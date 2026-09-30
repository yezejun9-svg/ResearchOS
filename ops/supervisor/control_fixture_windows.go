//go:build windows

package supervisor

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"

	"golang.org/x/sys/windows"
	rt "researchos.local/research-os/adapters/runtime"
)

const drainHandleEnv = "RESEARCHOS_DRAIN_BOOTSTRAP_HANDLE"

// DrainBootstrap travels only over an explicitly inherited anonymous pipe.
// The environment contains a handle number, never a key or authority flag.
// This proves same-user fixture mechanics, not an SCM security boundary.
type DrainBootstrap struct {
	Pipe     string
	Root     string
	Key      []byte
	Peer     ProcessIdentity
	Token    string
	Epoch    uint64
	Listener string
}

func ReadInheritedDrainBootstrap(root string) (*DrainBootstrap, error) {
	v := os.Getenv(drainHandleEnv)
	_ = os.Unsetenv(drainHandleEnv)
	if v == "" {
		return nil, nil
	}
	n, e := strconv.ParseUint(v, 10, 64)
	if e != nil || n == 0 {
		return nil, errors.New("invalid inherited drain handle")
	}
	h := windows.Handle(n)
	if kind, err := windows.GetFileType(h); err != nil || kind != windows.FILE_TYPE_PIPE {
		return nil, errors.New("drain bootstrap must be an inherited pipe")
	}
	if e = windows.SetHandleInformation(h, windows.HANDLE_FLAG_INHERIT, 0); e != nil {
		return nil, e
	}
	f := os.NewFile(uintptr(h), "private-drain-bootstrap")
	defer f.Close()
	var boot DrainBootstrap
	if e = json.NewDecoder(io.LimitReader(f, 8192)).Decode(&boot); e != nil {
		return nil, e
	}
	if !validDrainPipeName(boot.Pipe) || boot.Root != root || len(boot.Key) != 32 || boot.Token == "" || boot.Epoch == 0 || boot.Listener == "" {
		return nil, errors.New("drain bootstrap binding invalid")
	}
	if alive, err := (NativeFixtureDriver{}).Alive(boot.Peer); err != nil || !alive {
		return nil, errors.New("drain supervisor identity unavailable")
	}
	return &boot, nil
}

// ControlFixtureDriver implements the existing engine's driver and barrier.
// It owns no research scheduler. Loss of its in-memory inherited capability
// requires manual reconciliation; reopening the journal never repeats stop.
type ControlFixtureDriver struct {
	Journal                                    *ReleaseJournal
	WorkDir, WebDir, Listen, CoordinatorConfig string
	Output                                     io.Writer
	boot                                       *DrainBootstrap
	process                                    ProcessIdentity
	frame                                      DrainFrame
}

func (d *ControlFixtureDriver) Start(image, token, data string) (ProcessIdentity, error) {
	if d.Journal == nil {
		return ProcessIdentity{}, errors.New("supervisor journal required")
	}
	s := d.Journal.State()
	if (s.Phase != "STARTING" && s.Phase != "SWITCHED") || s.PID != 0 || s.Data != data || token == "" {
		return ProcessIdentity{}, errors.New("durable unstarted slot required")
	}
	lease, e := rt.AcquireDataRootLease(data)
	if e != nil {
		return ProcessIdentity{}, e
	}
	if e = lease.Close(); e != nil {
		return ProcessIdentity{}, e
	}
	actual, digest, e := exactImage(image)
	if e != nil || digest != s.Active {
		return ProcessIdentity{}, errors.New("control image differs from durable slot")
	}
	peer, e := ObserveProcess(uint32(os.Getpid()))
	if e != nil {
		return ProcessIdentity{}, e
	}
	name, e := NewDrainPipeName()
	if e != nil {
		return ProcessIdentity{}, e
	}
	boot := &DrainBootstrap{Pipe: name, Root: filepath.Clean(data), Key: make([]byte, 32), Peer: peer, Token: token, Epoch: s.Epoch, Listener: d.Listen}
	if _, e = rand.Read(boot.Key); e != nil {
		return ProcessIdentity{}, e
	}
	r, w, e := os.Pipe()
	if e != nil {
		return ProcessIdentity{}, e
	}
	defer r.Close()
	defer w.Close()
	if e = windows.SetHandleInformation(windows.Handle(r.Fd()), windows.HANDLE_FLAG_INHERIT, windows.HANDLE_FLAG_INHERIT); e != nil {
		return ProcessIdentity{}, e
	}
	args := []string{}
	if d.CoordinatorConfig != "" {
		args = append(args, "--runtime-coordinator-config", d.CoordinatorConfig)
	}
	cmd := exec.Command(actual, args...)
	cmd.Dir = d.WorkDir
	for _, v := range os.Environ() {
		name, _, _ := strings.Cut(v, "=")
		if strings.EqualFold(name, drainHandleEnv) || strings.EqualFold(name, "RESEARCHOS_DATA_DIR") || strings.EqualFold(name, "RESEARCHOS_WEB_DIR") || strings.EqualFold(name, "RESEARCHOS_LISTEN") {
			continue
		}
		cmd.Env = append(cmd.Env, v)
	}
	cmd.Env = append(cmd.Env, drainHandleEnv+"="+strconv.FormatUint(uint64(r.Fd()), 10), "RESEARCHOS_DATA_DIR="+data, "RESEARCHOS_WEB_DIR="+d.WebDir, "RESEARCHOS_LISTEN="+d.Listen)
	cmd.Stdout, cmd.Stderr = d.Output, d.Output
	cmd.SysProcAttr = &windows.SysProcAttr{CreationFlags: windows.CREATE_NEW_PROCESS_GROUP | windows.CREATE_NO_WINDOW, AdditionalInheritedHandles: []syscall.Handle{syscall.Handle(r.Fd())}}
	if e = cmd.Start(); e != nil {
		return ProcessIdentity{}, e
	}
	go func() { _ = cmd.Wait() }()
	p, e := ObserveProcess(uint32(cmd.Process.Pid))
	if e != nil {
		return ProcessIdentity{}, e
	}
	d.boot, d.process, d.frame = boot, p, DrainFrame{}
	if e = json.NewEncoder(w).Encode(boot); e != nil {
		return p, e
	}
	return p, nil
}

func (d *ControlFixtureDriver) Alive(p ProcessIdentity) (bool, error) {
	return (NativeFixtureDriver{}).Alive(p)
}

func (d *ControlFixtureDriver) connection(p ProcessIdentity) (*os.File, error) {
	if d.boot == nil || p != d.process || processIn(d.Journal.State()) != p || d.Journal.State().Data != d.boot.Root {
		return nil, errors.New("original inherited capability and durable identity required")
	}
	c, e := DialDrainPipe(d.boot.Pipe, p)
	if e != nil {
		return nil, e
	}
	if e = c.SetDeadline(time.Now().Add(5 * time.Second)); e != nil {
		c.Close()
		return nil, e
	}
	return c, nil
}

func (d *ControlFixtureDriver) send(c *os.File, frame DrainFrame) error {
	f, e := DrainFrameSign(d.boot.Key, frame)
	if e != nil {
		return e
	}
	return WriteDrainFrame(c, f)
}

func (d *ControlFixtureDriver) read(c *os.File, frame DrainFrame) (DrainFrame, error) {
	r, e := ReadDrainFrame(c)
	if e != nil {
		return r, e
	}
	if !DrainFrameValid(d.boot.Key, r) || r.Operation != frame.Operation || r.Epoch != frame.Epoch || r.Root != frame.Root || r.Nonce != frame.Nonce {
		return r, errors.New("control reply binding changed")
	}
	return r, nil
}

func (d *ControlFixtureDriver) Drain(ctx context.Context, p ProcessIdentity, operation string) (string, error) {
	s := d.Journal.State()
	if ctx.Err() != nil {
		return "", ctx.Err()
	}
	if s.Phase != "PREPARED" || s.Operation != operation || processIn(s) != p {
		return "", errors.New("prepared control binding required")
	}
	c, e := d.connection(p)
	if e != nil {
		return "", e
	}
	defer c.Close()
	var nonce [32]byte
	if _, e = rand.Read(nonce[:]); e != nil {
		return "", e
	}
	f := DrainFrame{Kind: "QUIESCE", Operation: operation, Epoch: s.Epoch, Root: s.Data, Nonce: hex.EncodeToString(nonce[:])}
	s.Phase = "DRAIN_UNKNOWN"
	s.DrainNonce = f.Nonce
	if e = d.Journal.Append(s); e != nil {
		return "", e
	}
	d.frame = f
	if e = d.send(c, f); e != nil {
		return "", e
	}
	r, e := d.read(c, f)
	if e != nil {
		return "", e
	}
	if r.Kind == "BUSY" && r.State == "STABLE" {
		s.Phase = "PREPARED"
		if e = d.Journal.Append(s); e != nil {
			return "", e
		}
		return "", errors.New("control busy; stable retained")
	}
	if r.Kind != "QUIESCED" || r.State != "QUIESCED" || !validDigest(r.Receipt) {
		return "", errors.New("control drain outcome unknown")
	}
	d.frame.Receipt = r.Receipt
	return r.Receipt, nil
}

func (d *ControlFixtureDriver) Stop(p ProcessIdentity) error {
	s := d.Journal.State()
	if s.Phase != "DRAINED" || processIn(s) != p || d.frame.Receipt != s.DrainReceipt || d.frame.Nonce != s.DrainNonce || !validDigest(s.DrainReceipt) {
		return errors.New("durable drained receipt required; stop not repeated")
	}
	h, e := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION|windows.SYNCHRONIZE, false, p.PID)
	if e != nil {
		return e
	}
	defer windows.CloseHandle(h)
	var created, exit, kernel, user windows.Filetime
	if e = windows.GetProcessTimes(h, &created, &exit, &kernel, &user); e != nil || created.Nanoseconds() != p.CreatedNS {
		return errors.New("control creation identity changed")
	}
	if digest, e := processImageDigest(h); e != nil || digest != p.ImageSHA256 {
		return errors.New("control image changed before normal exit")
	}
	c, e := d.connection(p)
	if e != nil {
		return e
	}
	defer c.Close()
	s.Phase = "EXIT_UNKNOWN"
	if e = d.Journal.Append(s); e != nil {
		return e
	}
	f := d.frame
	f.Kind = "COMMIT_EXIT"
	if e = d.send(c, f); e != nil {
		return e
	}
	r, e := d.read(c, f)
	if e != nil {
		return e
	}
	if r.Kind != "COMMIT_READY" || r.State != "QUIESCED" || r.Receipt != f.Receipt {
		return errors.New("commit outcome unknown")
	}
	f.Kind = "EXIT_ACK"
	if e = d.send(c, f); e != nil {
		return e
	}
	wait, e := windows.WaitForSingleObject(h, 15000)
	if e != nil || wait != windows.WAIT_OBJECT_0 {
		return fmt.Errorf("normal exit not observed: %d %v", wait, e)
	}
	var code uint32
	if e = windows.GetExitCodeProcess(h, &code); e != nil || code != 0 {
		return fmt.Errorf("control exit was not clean: %d %v", code, e)
	}
	lease, e := rt.AcquireDataRootLease(s.Data)
	if e != nil {
		return e
	}
	return lease.Close()
}

func (d *ControlFixtureDriver) Ready(ctx context.Context, p ProcessIdentity, token string) error {
	if d.boot == nil || p != d.process || token != d.boot.Token || d.Listen != d.boot.Listener {
		return errors.New("original child startup capability required")
	}
	s := d.Journal.State()
	// Bootstrap calls Ready while its durable slot is still STARTING/PID=0.
	// Only this read-only proof accepts that window; mutation connections retain
	// their complete journal-process identity requirement.
	starting := (s.Phase == "STARTING" || s.Phase == "SWITCHED") && s.PID == 0
	if (!starting && processIn(s) != p) || s.Data != d.boot.Root || s.Epoch != d.boot.Epoch || s.Active != p.ImageSHA256 {
		return errors.New("control startup slot binding changed")
	}
	client := &http.Client{Timeout: time.Second}
	deadline := time.Now().Add(10 * time.Second)
	if end, ok := ctx.Deadline(); ok && end.Before(deadline) {
		deadline = end
	}
	for time.Now().Before(deadline) && ctx.Err() == nil {
		alive, e := d.Alive(p)
		if e != nil || !alive {
			return errors.New("control not alive")
		}
		c, e := dialDrainPipeUntil(d.boot.Pipe, p, deadline)
		if e != nil {
			return fmt.Errorf("private control readiness unavailable: %w", e)
		}
		if e = c.SetDeadline(deadline); e != nil {
			c.Close()
			return e
		}
		var nonce [32]byte
		if _, e = rand.Read(nonce[:]); e != nil {
			c.Close()
			return e
		}
		frame := DrainFrame{Kind: "READY", Operation: token, Epoch: d.boot.Epoch, Root: d.boot.Root, Nonce: hex.EncodeToString(nonce[:])}
		if e = d.send(c, frame); e != nil {
			c.Close()
			return e
		}
		reply, e := d.read(c, frame)
		c.Close()
		if e != nil {
			return e
		}
		if reply.Kind == "BUSY" && reply.State == "STARTING" {
			time.Sleep(25 * time.Millisecond)
			continue
		}
		r := reply.Readiness
		if reply.Kind != "READY" || reply.State != "READY" || r == nil || r.Process != p || r.Listener != d.Listen || !r.LeaseHeld || !r.StartupComplete {
			return errors.New("private control readiness binding changed")
		}
		req, e := http.NewRequestWithContext(ctx, http.MethodGet, "http://"+d.Listen+"/healthz", nil)
		if e != nil {
			return e
		}
		res, e := client.Do(req)
		if e == nil {
			res.Body.Close()
			if res.StatusCode == http.StatusOK {
				if alive, e = d.Alive(p); e != nil || !alive {
					return errors.New("ready control exited")
				}
				return nil
			}
		}
		time.Sleep(25 * time.Millisecond)
	}
	return errors.New("control readiness unavailable")
}

func (d *ControlFixtureDriver) Compatible(context.Context, ReleaseState) error {
	return errors.New("actual control rollback requires a separately qualified restore")
}
