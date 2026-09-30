//go:build windows

package protectedstore

import (
	"context"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/svc"
	"golang.org/x/sys/windows/svc/mgr"
)

const CanaryServiceName = "ResearchOSVerifierCanary"
const canaryPipe = `\\.\pipe\ResearchOSVerifierCanary-v1`
const pipeClientRights = windows.FILE_READ_DATA | windows.FILE_WRITE_DATA | windows.SYNCHRONIZE

// Windows also checks FILE_READ_ATTRIBUTES when opening the client endpoint.
// Do not grant FILE_CREATE_PIPE_INSTANCE (0x4) through generic write access.
const pipeClientACL = "0x100083"

var brokerFiles = []string{"input.canary", "label.canary", "detail.canary", "log.canary"}

// CanaryInstallRoot is fixed, not accepted from an IPC request or environment.
func CanaryInstallRoot() (string, error) {
	root, e := windows.KnownFolderPath(windows.FOLDERID_ProgramData, 0)
	if e != nil {
		return "", ErrUnavailable
	}
	return filepath.Join(root, CanaryServiceName), nil
}

func brokerSummary() (SafeSummary, *CanaryStore, error) {
	root, e := CanaryInstallRoot()
	if e != nil {
		return SafeSummary{}, nil, e
	}
	private := filepath.Join(root, "data", "private")
	store, e := OpenCanary(private)
	if e != nil {
		if _, stat := os.Stat(private); !os.IsNotExist(stat) {
			return SafeSummary{}, nil, ErrBoundary
		}
		store, e = NewCanary(private)
		if e != nil {
			return SafeSummary{}, nil, e
		}
		for _, name := range brokerFiles {
			if e = store.createFile(name, []byte("SYNTHETIC_SERVICE_CANARY_"+name)); e != nil {
				store.Close()
				return SafeSummary{}, nil, e
			}
		}
	}
	for _, name := range brokerFiles {
		body, err := store.readFile(name, 1024)
		if err != nil || string(body) != "SYNTHETIC_SERVICE_CANARY_"+name {
			store.Close()
			return SafeSummary{}, nil, ErrIntegrity
		}
	}
	return SafeSummary{Schema: "researchos.protected-summary.v1", Status: "EXECUTION_REPORTED", Total: 4, Correct: 4, MaximumMode: "ADVISORY"}, store, nil
}

// RunCanaryService is the fixed installed verifier service. Its public pipe
// accepts no filename, provider URL, credential, threshold or evaluation case.
func RunCanaryService(readerSID string) error {
	interactive, e := svc.IsWindowsService()
	if e != nil || !interactive {
		return ErrIsolation
	}
	account, _, _, e := windows.LookupSID("", `NT SERVICE\`+CanaryServiceName)
	user, err := windows.GetCurrentProcessToken().GetTokenUser()
	if e != nil || err != nil || user.User.Sid.String() != account.String() {
		return ErrIsolation
	}
	reader, e := windows.StringToSid(readerSID)
	if e != nil || !reader.IsValid() || readerSID == account.String() || !strings.HasPrefix(readerSID, "S-1-5-21-") {
		return ErrBoundary
	}
	root, e := CanaryInstallRoot()
	exe, err := os.Executable()
	if e != nil || err != nil || !strings.EqualFold(exe, filepath.Join(root, "broker.exe")) {
		return ErrBoundary
	}
	return svc.Run(CanaryServiceName, &canaryService{readerSID: readerSID})
}

type canaryService struct{ readerSID string }

func (s *canaryService) Execute(_ []string, requests <-chan svc.ChangeRequest, changes chan<- svc.Status) (bool, uint32) {
	changes <- svc.Status{State: svc.StartPending}
	summary, store, e := brokerSummary()
	if e != nil {
		return true, 1
	}
	defer store.Close()
	boundary, e := store.Boundary(context.Background())
	if e != nil || summary.Validate() != nil {
		return true, 2
	}
	// Explicit data read/write permissions avoid FILE_CREATE_PIPE_INSTANCE. A
	// different server instance cannot be created with the reader's pipe rights.
	sd, e := windows.SecurityDescriptorFromString("D:P(A;;FA;;;" + boundary.OwnerSID + ")(A;;" + pipeClientACL + ";;;" + s.readerSID + ")")
	if e != nil {
		return true, 3
	}
	sa := windows.SecurityAttributes{Length: uint32(unsafe.Sizeof(windows.SecurityAttributes{})), SecurityDescriptor: sd}
	name, _ := windows.UTF16PtrFromString(canaryPipe)
	h, e := windows.CreateNamedPipe(name, windows.PIPE_ACCESS_DUPLEX|windows.FILE_FLAG_FIRST_PIPE_INSTANCE, windows.PIPE_TYPE_MESSAGE|windows.PIPE_READMODE_MESSAGE|windows.PIPE_NOWAIT|windows.PIPE_REJECT_REMOTE_CLIENTS, 1, 4096, 64, 0, &sa)
	if e != nil {
		return true, 4
	}
	defer windows.CloseHandle(h)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	engine := newFrozenEngine(ctx, store, protectedGenerator(), serviceCallFactory(store))
	configuration, e := newConfigPipe(boundary.OwnerSID)
	if e != nil {
		return true, 8
	}
	defer windows.CloseHandle(configuration)
	done := make(chan struct{})
	configured := make(chan struct{})
	go func() { defer close(done); serveCanaryPipe(ctx, h, summary, store, engine) }()
	go func() { defer close(configured); serveConfigPipe(ctx, configuration, engine) }()
	stop := func() { cancel(); <-done; <-configured; engine.wait() }
	defer stop()
	current := svc.Status{State: svc.Running, Accepts: svc.AcceptStop | svc.AcceptShutdown}
	changes <- current
	for request := range requests {
		switch request.Cmd {
		case svc.Interrogate:
			changes <- current
		case svc.Stop, svc.Shutdown:
			changes <- svc.Status{State: svc.StopPending}
			return false, 0
		case svc.Cmd(128):
			// Only the installer administrator receives SERVICE_USER_DEFINED_CONTROL.
			// Refuse before changing any state once formal data exists. This is
			// deployment rollback, never deletion of unique protected evidence.
			engine.mu.Lock()
			entries, err := os.ReadDir(store.root)
			allowed := map[string]bool{serviceCredentialFile: true}
			for _, name := range brokerFiles {
				allowed[name] = true
			}
			canErase := err == nil && !privateExists(store, runMarkerFile)
			for _, entry := range entries {
				if entry.IsDir() || !allowed[entry.Name()] {
					canErase = false
				}
			}
			if !canErase {
				engine.mu.Unlock()
				continue
			}
			cancel()
			engine.mu.Unlock()
			changes <- svc.Status{State: svc.StopPending}
			stop()
			if _, e := store.Boundary(context.Background()); e != nil {
				return true, 5
			}
			store.Close()
			for _, entry := range entries {
				if e := os.Remove(filepath.Join(store.root, entry.Name())); e != nil {
					return true, 6
				}
			}
			if e := os.Remove(store.root); e != nil {
				return true, 7
			}
			return false, 0
		}
	}
	return false, 0
}

func waitBroker(ctx context.Context) bool {
	select {
	case <-ctx.Done():
		return false
	case <-time.After(25 * time.Millisecond):
		return true
	}
}
func pipeReadFrame(ctx context.Context, h windows.Handle, timeout time.Duration) (string, error) {
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) && ctx.Err() == nil {
		var n uint32
		buffer := make([]byte, 64)
		e := windows.ReadFile(h, buffer, &n, nil)
		if e == nil && n > 0 {
			return string(buffer[:n]), nil
		}
		if e != nil && !errors.Is(e, windows.ERROR_NO_DATA) {
			return "", ErrUnavailable
		}
		if !waitBroker(ctx) {
			break
		}
	}
	return "", ErrUnavailable
}
func serveCanaryPipe(ctx context.Context, h windows.Handle, summary SafeSummary, store *CanaryStore, engines ...*frozenEngine) {
	for ctx.Err() == nil {
		e := windows.ConnectNamedPipe(h, nil)
		if e != nil && !errors.Is(e, windows.ERROR_PIPE_CONNECTED) {
			if !errors.Is(e, windows.ERROR_PIPE_LISTENING) {
				windows.DisconnectNamedPipe(h)
			}
			if !waitBroker(ctx) {
				return
			}
			continue
		}
		request, err := pipeReadFrame(ctx, h, 2*time.Second)
		if err == nil && (request == "summary-v1" || (len(engines) == 1 && (request == "start-frozen-run" || request == "status" || request == "aggregate"))) {
			// Recheck every file before returning an aggregate; ACL/body drift never
			// returns the last successful startup aggregate.
			valid := true
			for _, name := range brokerFiles {
				b, e := store.readFile(name, 1024)
				if e != nil || string(b) != "SYNTHETIC_SERVICE_CANARY_"+name {
					valid = false
					break
				}
			}
			current := summary
			if !valid {
				current = SafeSummary{Schema: "researchos.protected-summary.v1", Status: "BLOCKED", MaximumMode: "ADVISORY"}
			} else if request != "summary-v1" {
				if request == "start-frozen-run" {
					current = engines[0].start()
				} else {
					current = engines[0].snapshot()
				}
			}
			body, _ := json.Marshal(current)
			var written uint32
			if windows.WriteFile(h, body, &written, nil) == nil && written == uint32(len(body)) {
				pipeReadFrame(ctx, h, 2*time.Second)
			}
		}
		windows.DisconnectNamedPipe(h)
	}
}

// ProbeCanaryService verifies that SCM's running, expected virtual-account
// service owns the connected pipe. It returns only a validated fixed aggregate.
func ProbeCanaryService() (SafeSummary, error) {
	return queryServiceSummary("summary-v1")
}

// QueryFrozenService exposes only the frozen start/status/aggregate vocabulary.
// A status response during RUNNING contains no changing counters or key rows.
func QueryFrozenService(command string) (SafeSummary, error) {
	if command != "start-frozen-run" && command != "status" && command != "aggregate" {
		return SafeSummary{}, ErrBoundary
	}
	summary, e := queryServiceSummary(command)
	if e == nil && summary.Frozen == nil {
		return SafeSummary{}, ErrIntegrity
	}
	return summary, e
}
func queryServiceSummary(command string) (SafeSummary, error) {
	deadline := time.Now().Add(3 * time.Second)
	type result struct {
		summary SafeSummary
		err     error
	}
	done := make(chan result, 1)
	go func() { summary, e := probeServiceSummary(deadline, command); done <- result{summary, e} }()
	timer := time.NewTimer(time.Until(deadline))
	defer timer.Stop()
	select {
	case value := <-done:
		return value.summary, value.err
	case <-timer.C:
		return SafeSummary{}, ErrUnavailable
	}
}

func connectServicePipe(pipeName string) (*os.File, *mgr.Service, uint32, error) {
	scm, e := windows.OpenSCManager(nil, nil, windows.SC_MANAGER_CONNECT)
	if e != nil {
		return nil, nil, 0, ErrUnavailable
	}
	m := &mgr.Mgr{Handle: scm}
	defer m.Disconnect()
	h, e := windows.OpenService(m.Handle, windows.StringToUTF16Ptr(CanaryServiceName), windows.SERVICE_QUERY_STATUS|windows.SERVICE_QUERY_CONFIG)
	if e != nil {
		return nil, nil, 0, ErrUnavailable
	}
	s := &mgr.Service{Name: CanaryServiceName, Handle: h}
	ok := false
	defer func() {
		if !ok {
			s.Close()
		}
	}()
	config, e := s.Config()
	if e != nil || !strings.EqualFold(config.ServiceStartName, `NT SERVICE\`+CanaryServiceName) {
		return nil, nil, 0, ErrIsolation
	}
	root, err := CanaryInstallRoot()
	if err != nil || !strings.HasPrefix(strings.ToLower(config.BinaryPathName), strings.ToLower(`"`+filepath.Join(root, "broker.exe")+`" --service --reader-sid S-1-5-21-`)) {
		return nil, nil, 0, ErrBoundary
	}
	status, e := s.Query()
	if e != nil || status.State != svc.Running || status.ProcessId == 0 {
		return nil, nil, 0, ErrUnavailable
	}
	pipe, e := windows.CreateFile(windows.StringToUTF16Ptr(pipeName), pipeClientRights, 0, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OVERLAPPED|windows.SECURITY_SQOS_PRESENT|windows.SECURITY_IDENTIFICATION, 0)
	if e != nil {
		return nil, nil, 0, ErrUnavailable
	}
	file := os.NewFile(uintptr(pipe), "canary-summary-pipe")
	var pid uint32
	if windows.GetNamedPipeServerProcessId(pipe, &pid) != nil || pid != status.ProcessId {
		file.Close()
		return nil, nil, 0, ErrIsolation
	}
	ok = true
	return file, s, pid, nil
}
func probeServiceSummary(deadline time.Time, command string) (SafeSummary, error) {
	file, s, pid, e := connectServicePipe(canaryPipe)
	if e != nil {
		return SafeSummary{}, e
	}
	defer file.Close()
	defer s.Close()
	summary, e := requestServiceSummary(file, deadline, command)
	if e != nil {
		return SafeSummary{}, e
	}
	after, e := s.Query()
	if e != nil || after.ProcessId != pid || after.State != svc.Running {
		return SafeSummary{}, ErrIsolation
	}
	if summary.Frozen != nil {
		root, e := CanaryInstallRoot()
		if e != nil {
			return SafeSummary{}, e
		}
		raw, e := os.ReadFile(filepath.Join(root, "broker.exe"))
		if e != nil || Digest(raw) != summary.Frozen.BinaryHash {
			return SafeSummary{}, ErrIntegrity
		}
	}
	return summary, nil
}

func requestCanarySummary(file *os.File, deadline time.Time) (SafeSummary, error) {
	return requestServiceSummary(file, deadline, "summary-v1")
}
func requestServiceSummary(file *os.File, deadline time.Time, command string) (SafeSummary, error) {
	// Overlapped pipe handles are integrated with Go's Windows poller. One
	// absolute deadline covers request, response and acknowledgement; timeout
	// cancels the native operation even if the server never sends any bytes.
	if file.SetDeadline(deadline) != nil {
		return SafeSummary{}, ErrUnavailable
	}
	if _, e := file.Write([]byte(command)); e != nil {
		return SafeSummary{}, ErrUnavailable
	}
	buffer := make([]byte, 4096)
	n, e := file.Read(buffer)
	if e != nil {
		return SafeSummary{}, ErrUnavailable
	}
	summary, e := ParseSafeSummary(buffer[:n])
	if e != nil {
		return SafeSummary{}, e
	}
	if _, e = file.Write([]byte("ack")); e != nil {
		return SafeSummary{}, ErrUnavailable
	}
	return summary, nil
}
