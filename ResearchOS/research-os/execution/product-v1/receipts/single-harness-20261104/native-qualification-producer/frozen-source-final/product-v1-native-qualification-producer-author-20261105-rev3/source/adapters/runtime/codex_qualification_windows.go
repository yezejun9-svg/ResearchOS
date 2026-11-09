//go:build windows

package runtime

import (
	"bufio"
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"golang.org/x/sys/windows"
	"researchos.local/research-os/internal/qualificationprobe"
)

// Only actual Host composition may supply these installed source/build facts.
// No request decoder, environment override, PASS boolean, receipt path, or
// arbitrary qualification provider is accepted by this constructor.
type CodexNativeQualificationOptions struct {
	ApprovedRoot        string
	SyntheticSource     string
	ShippedHelper       string
	ShippedHelperSHA256 string
	HostBuildSHA256     string
}
type nativeQualificationObservation struct {
	TaskID, RunID, Epoch, SourceBindingHash, Source, Directory                                 string
	NativeHash, HelperHash, HostBuildHash, TemplateHash, EnvironmentHash, NormalHome, HostBoot string
	RenderedArgvHash                                                                           string
	ReceiptPath                                                                                string
	PreflightNoChild                                                                           bool
	Until                                                                                      time.Time
	Capture                                                                                    qualificationCapture
}
type nativeQualifier struct {
	mu          sync.Mutex
	state       string
	used        bool
	options     CodexNativeQualificationOptions
	rpc         *codexRPC
	boot        string
	observation nativeQualificationObservation
}
type qualifiedRPC struct {
	rpc *codexRPC
	q   *nativeQualifier
}

// This is a scope fact for Host/domain admission, never a readiness or
// qualification grant. Arbitrary CodexDriver implementations cannot supply it.
func CodexNativeQualificationSource(driver CodexDriver) (string, bool) {
	d, ok := driver.(*qualifiedRPC)
	if !ok || d == nil || d.q == nil || d.q.options.SyntheticSource == "" {
		return "", false
	}
	return d.q.options.SyntheticSource, true
}

type qualifiedHandle struct {
	mu                 sync.Mutex
	cancel             context.CancelFunc
	delegate           CodexHandle
	delegateAttempted  bool
	q                  *nativeQualifier
	launch             CodexLaunch
	done               chan struct{}
	result             CodexResult
	err                error
	preparationFailure *CodexPreparationFailure
}

// A value-only projection of a terminal preparation failure. The only mint
// path is the private wrapper handle after its goroutine has ended; serialized
// reports or caller-created CodexHandle implementations cannot obtain it.
type CodexPreparationFailure struct {
	Reason                                                          string
	QualificationReceiptPath                                        string
	QualificationPID                                                uint32
	NoQualificationChild                                            bool
	QualificationJobZero                                            bool
	StreamsDrained                                                  bool
	CleanupComplete                                                 bool
	NoModelDelegation                                               bool
	TaskID, RunID, Epoch, SourceBindingHash, TemplateHash, HostBoot string
}

func CodexPreparationFailureForHandle(handle CodexHandle) (CodexPreparationFailure, bool) {
	h, ok := handle.(*qualifiedHandle)
	if !ok || h == nil {
		return CodexPreparationFailure{}, false
	}
	select {
	case <-h.done:
	default:
		return CodexPreparationFailure{}, false
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.delegateAttempted || h.delegate != nil || h.preparationFailure == nil || h.err == nil || h.q == nil {
		return CodexPreparationFailure{}, false
	}
	f := *h.preparationFailure
	if !knownQualificationFailure(f.Reason) || !f.NoModelDelegation || f.TaskID != h.launch.TaskID || f.RunID != h.launch.RunID || f.Epoch != h.launch.Epoch || f.SourceBindingHash != h.launch.SourceBindingHash ||
		f.TemplateHash != CodexRPCPolicyIdentity(h.q.rpc.options.Descriptor.ExecutableHash).RequestedConfigSHA256 || f.HostBoot != h.q.boot ||
		!(f.NoQualificationChild && f.QualificationPID == 0 || f.QualificationPID != 0 && f.QualificationJobZero && f.StreamsDrained && f.CleanupComplete) {
		return CodexPreparationFailure{}, false
	}
	return f, true
}
func knownQualificationFailure(reason string) bool {
	switch reason {
	case "QUALIFICATION_REQUIRED", "QUALIFICATION_SCOPE_MISMATCH", "QUALIFICATION_BOOTSTRAP_BLOCKED", "QUALIFICATION_POLICY_VIOLATION", "QUALIFICATION_CONTROL_INVALID", "QUALIFICATION_INCOMPLETE", "QUALIFICATION_IDENTITY_CHANGED", "QUALIFICATION_CLEANUP_UNKNOWN", "QUALIFICATION_RECEIPT_UNCERTAIN", "QUALIFICATION_CANCELLED_BEFORE_RPC", "QUALIFICATION_TIME_BUDGET_EXHAUSTED", "QUALIFICATION_TEMPLATE_CHANGED":
		return true
	}
	return false
}
func preparationFailure(reason string, obs nativeQualificationObservation) *CodexPreparationFailure {
	return &CodexPreparationFailure{Reason: reason, QualificationReceiptPath: obs.ReceiptPath, QualificationPID: obs.Capture.PID, NoQualificationChild: obs.PreflightNoChild, QualificationJobZero: obs.Capture.JobZero, StreamsDrained: obs.Capture.StreamsDrained, CleanupComplete: obs.Capture.CleanupComplete, NoModelDelegation: true, TaskID: obs.TaskID, RunID: obs.RunID, Epoch: obs.Epoch, SourceBindingHash: obs.SourceBindingHash, TemplateHash: obs.TemplateHash, HostBoot: obs.HostBoot}
}

func NewCodexRPCWithNativeQualification(options CodexRPCOptions, scope CodexNativeQualificationOptions) (CodexDriver, error) {
	if options.Descriptor.Version != "0.166.0" || !filepath.IsAbs(scope.ApprovedRoot) || !filepath.IsAbs(scope.SyntheticSource) || !filepath.IsAbs(scope.ShippedHelper) ||
		filepath.Clean(scope.ApprovedRoot) != scope.ApprovedRoot || filepath.Clean(scope.SyntheticSource) != scope.SyntheticSource || filepath.Clean(scope.ShippedHelper) != scope.ShippedHelper ||
		!strings.EqualFold(scope.SyntheticSource, filepath.Join(scope.ApprovedRoot, "S")) || !strings.EqualFold(scope.ShippedHelper, filepath.Join(scope.SyntheticSource, "qualification-helper.exe")) ||
		!qualificationSHA(scope.ShippedHelperSHA256) || !qualificationSHA(scope.HostBuildSHA256) {
		return nil, errors.New("QUALIFICATION_REQUIRED")
	}
	d, err := NewCodexRPC(options)
	if err != nil {
		return nil, err
	}
	var nonce [16]byte
	if _, err = rand.Read(nonce[:]); err != nil {
		return nil, errors.New("QUALIFICATION_BOOT_UNAVAILABLE")
	}
	q := &nativeQualifier{state: "NOT_STARTED", options: scope, rpc: d.(*codexRPC), boot: hex.EncodeToString(nonce[:])}
	q.rpc.qualifier = q
	return &qualifiedRPC{rpc: q.rpc, q: q}, nil
}
func qualificationSHA(s string) bool {
	if len(s) != 71 || !strings.HasPrefix(s, "sha256:") {
		return false
	}
	_, err := hex.DecodeString(s[7:])
	return err == nil
}
func (d *qualifiedRPC) Descriptor() CodexDescriptor       { return d.rpc.Descriptor() }
func (d *qualifiedRPC) ReadinessSnapshot() CodexReadiness { return d.rpc.ReadinessSnapshot() }
func (h *qualifiedHandle) Cancel() {
	h.mu.Lock()
	delegate := h.delegate
	h.mu.Unlock()
	h.cancel()
	if delegate != nil {
		delegate.Cancel()
	}
}
func (h *qualifiedHandle) Wait(ctx context.Context) (CodexResult, error) {
	select {
	case <-h.done:
		h.mu.Lock()
		defer h.mu.Unlock()
		return h.result, h.err
	case <-ctx.Done():
		return CodexResult{}, ctx.Err()
	}
}

// Mirror B1's pure launch gate before consuming the one-shot qualification.
// B1 still validates again immediately before its own child is created.
func validateQualificationLaunch(in CodexLaunch, cb CodexCallbacks) error {
	if !filepath.IsAbs(in.Workspace) || !filepath.IsAbs(in.Directory) || in.SourceBindingHash == "" ||
		in.TaskID == "" || in.RunID == "" || strings.TrimSpace(in.Prompt) == "" || len(in.Prompt) > 65536 ||
		in.Timeout <= 0 || in.Timeout > 15*time.Minute || cb.BeforeResume == nil || cb.BeforeModelTurn == nil || cb.Event == nil {
		return errors.New("CODEX_RPC_LAUNCH_INVALID")
	}
	epoch, err := strconv.ParseInt(in.Epoch, 10, 64)
	if err != nil || epoch <= 0 || strconv.FormatInt(epoch, 10) != in.Epoch {
		return errors.New("CODEX_EPOCH_INVALID")
	}
	_, err = codexExecutionInput(in.Workspace, filepath.Join(in.Directory, "cwd"), in.Prompt)
	return err
}

func (d *qualifiedRPC) Start(ctx context.Context, in CodexLaunch, cb CodexCallbacks) (CodexHandle, error) {
	if d.rpc.readiness().State != "PREPARATION_READY" {
		return nil, errors.New("QUALIFICATION_REQUIRED")
	}
	if err := validateQualificationLaunch(in, cb); err != nil {
		return nil, err
	}
	if !strings.EqualFold(filepath.Clean(in.Workspace), d.q.options.SyntheticSource) || ctx.Err() != nil {
		return nil, errors.New("QUALIFICATION_SCOPE_MISMATCH")
	}
	if _, err := os.Lstat(in.Directory); !errors.Is(err, os.ErrNotExist) {
		return nil, errors.New("QUALIFICATION_LAUNCH_DIRECTORY_PRECREATED")
	}
	d.q.mu.Lock()
	if d.q.state != "NOT_STARTED" {
		d.q.mu.Unlock()
		return nil, errors.New("QUALIFICATION_ATTEMPT_CONSUMED")
	}
	d.q.state = "RUNNING"
	d.q.mu.Unlock()
	child, cancel := context.WithCancel(ctx)
	h := &qualifiedHandle{cancel: cancel, done: make(chan struct{}), q: d.q, launch: in}
	go func() {
		defer close(h.done)
		defer cancel()
		deadline := time.Now().Add(in.Timeout)
		prepBudget := 60 * time.Second
		if in.Timeout < prepBudget {
			prepBudget = in.Timeout
		}
		prepCtx, prepCancel := context.WithTimeout(child, prepBudget)
		obs, err := d.q.ensureLaunch(prepCtx, in)
		prepCancel()
		if err != nil {
			h.mu.Lock()
			h.result = CodexResult{State: "FAILED", Failure: err.Error(), Stopped: obs.Capture.JobZero, StreamsDrained: obs.Capture.StreamsDrained, CleanupComplete: obs.Capture.CleanupComplete}
			h.err = err
			h.preparationFailure = preparationFailure(err.Error(), obs)
			h.mu.Unlock()
			return
		}
		if child.Err() != nil {
			h.mu.Lock()
			h.err = child.Err()
			h.preparationFailure = preparationFailure("QUALIFICATION_CANCELLED_BEFORE_RPC", obs)
			h.mu.Unlock()
			return
		}
		remaining := time.Until(deadline)
		if remaining <= 0 {
			h.mu.Lock()
			h.err = errors.New("QUALIFICATION_TIME_BUDGET_EXHAUSTED")
			h.preparationFailure = preparationFailure("QUALIFICATION_TIME_BUDGET_EXHAUSTED", obs)
			h.mu.Unlock()
			return
		}
		in.Timeout = remaining
		h.mu.Lock()
		h.delegateAttempted = true
		h.mu.Unlock()
		delegate, err := d.rpc.Start(child, in, cb)
		if err != nil {
			h.mu.Lock()
			h.err = err
			h.mu.Unlock()
			return
		}
		h.mu.Lock()
		h.delegate = delegate
		h.mu.Unlock()
		if child.Err() != nil {
			delegate.Cancel()
		}
		result, err := delegate.Wait(context.Background())
		h.mu.Lock()
		h.result, h.err = result, err
		h.mu.Unlock()
	}()
	return h, nil
}

func (q *nativeQualifier) Ensure(ctx context.Context, e CodexTurnEvidence) error {
	q.mu.Lock()
	defer q.mu.Unlock()
	o := q.observation
	if q.state != "OBSERVED_PASS" || q.used {
		return errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	q.used = true
	if ctx.Err() != nil || time.Now().After(o.Until) || o.HostBoot != q.boot ||
		e.TaskID != o.TaskID || e.RunID != o.RunID || e.Epoch != o.Epoch || e.SourceBindingHash != o.SourceBindingHash ||
		e.PolicyIdentity != CodexRPCPolicyIdentity(o.NativeHash) || e.Process.PID == 0 || e.Process.Created <= 0 || e.Process.Job == "" ||
		e.ProfileNonce == "" || e.ThreadID == "" || e.RenderedConfigSHA256 != codexRPCConfigHash(e.ProfileNonce, filepath.Join(o.Directory, "cwd"), o.Source) ||
		q.rpc.options.Descriptor.ExecutableHash != o.NativeHash || q.options.ShippedHelperSHA256 != o.HelperHash || q.options.HostBuildSHA256 != o.HostBuildHash ||
		CodexRPCPolicyIdentity(o.NativeHash).RequestedConfigSHA256 != o.TemplateHash || Hash(mustJSON(Environment(""))) != o.EnvironmentHash ||
		!strings.EqualFold(q.rpc.options.NormalHome, o.NormalHome) || !strings.EqualFold(q.options.SyntheticSource, o.Source) || !strings.EqualFold(q.options.ApprovedRoot, filepath.Dir(o.Source)) {
		return errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	if exactReal(o.Source) != nil || exactReal(q.options.ShippedHelper) != nil {
		return errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	if digest, err := fileDigest(q.options.ShippedHelper); err != nil || digest != o.HelperHash {
		return errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	if digest, err := fileDigest(q.rpc.options.Executable); err != nil || digest != o.NativeHash {
		return errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	return nil
}
func mustJSON(v any) []byte { raw, _ := json.Marshal(v); return raw }
func fileDigest(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	h := sha256.New()
	_, e := io.Copy(h, f)
	c := f.Close()
	if e != nil || c != nil {
		return "", errors.Join(e, c)
	}
	return "sha256:" + hex.EncodeToString(h.Sum(nil)), nil
}
func exactReal(path string) error {
	for current := filepath.Clean(path); ; current = filepath.Dir(current) {
		name, e := windows.UTF16PtrFromString(current)
		if e != nil {
			return errors.New("QUALIFICATION_REPARSE_OR_MISSING")
		}
		attributes, e := windows.GetFileAttributes(name)
		if e != nil || attributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0 {
			return errors.New("QUALIFICATION_REPARSE_OR_MISSING")
		}
		parent := filepath.Dir(current)
		if parent == current {
			break
		}
	}
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(path)) {
		return errors.New("QUALIFICATION_REPARSE_OR_MISSING")
	}
	return nil
}
func createFixed(path string, raw []byte) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	n, e := f.Write(raw)
	if e == nil && n != len(raw) {
		e = io.ErrShortWrite
	}
	syncErr := f.Sync()
	closeErr := f.Close()
	return errors.Join(e, syncErr, closeErr)
}
func hostWriteControl(path string, expected []byte) error {
	f, err := os.OpenFile(path, os.O_RDWR, 0)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err = f.WriteAt(bytes.Repeat([]byte{'C'}, len(expected)), 0); err != nil {
		return err
	}
	if err = f.Sync(); err != nil {
		return err
	}
	if _, err = f.WriteAt(expected, 0); err != nil {
		return err
	}
	if err = f.Sync(); err != nil {
		return err
	}
	raw, err := os.ReadFile(path)
	if err != nil || !bytes.Equal(raw, expected) {
		return errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	return nil
}

func hostCreateControl(path string) error {
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	_, writeErr := f.Write([]byte("researchos-host-create-control-v1\n"))
	syncErr := f.Sync()
	closeErr := f.Close()
	removeErr := os.Remove(path)
	if err := errors.Join(writeErr, syncErr, closeErr, removeErr); err != nil {
		return err
	}
	if _, err := os.Lstat(path); !errors.Is(err, os.ErrNotExist) {
		return errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	return nil
}

type qualificationListener struct {
	listener              *net.TCPListener
	nonce                 string
	mu                    sync.Mutex
	pre, post, unexpected int
	done                  chan struct{}
}

func startQualificationListener(nonce string) (*qualificationListener, error) {
	l, err := net.ListenTCP("tcp4", &net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: 0})
	if err != nil {
		return nil, err
	}
	q := &qualificationListener{listener: l, nonce: nonce, done: make(chan struct{})}
	go q.serve()
	return q, nil
}
func (q *qualificationListener) serve() {
	defer close(q.done)
	for {
		c, err := q.listener.AcceptTCP()
		if err != nil {
			return
		}
		func() {
			defer c.Close()
			_ = c.SetDeadline(time.Now().Add(time.Second))
			line, err := bufio.NewReaderSize(io.LimitReader(c, 129), 128).ReadString('\n')
			q.mu.Lock()
			switch {
			case err == nil && len(line) <= 128 && line == q.nonce+":pre\n":
				q.pre++
			case err == nil && len(line) <= 128 && line == q.nonce+":post\n":
				q.post++
			default:
				q.unexpected++
			}
			q.mu.Unlock()
			if err == nil {
				_, _ = c.Write([]byte("OK\n"))
			}
		}()
	}
}
func (q *qualificationListener) control(phase string) error {
	c, err := net.DialTimeout("tcp4", q.listener.Addr().String(), time.Second)
	if err != nil {
		return err
	}
	defer c.Close()
	_ = c.SetDeadline(time.Now().Add(time.Second))
	if _, err = c.Write([]byte(q.nonce + ":" + phase + "\n")); err != nil {
		return err
	}
	var reply [3]byte
	if _, err = io.ReadFull(c, reply[:]); err != nil || string(reply[:]) != "OK\n" {
		return errors.New("QUALIFICATION_LISTENER_CONTROL_INVALID")
	}
	return nil
}
func (q *qualificationListener) closeAndCheck() (bool, error) {
	q.listener.Close()
	<-q.done
	q.mu.Lock()
	defer q.mu.Unlock()
	if q.unexpected != 0 {
		return true, errors.New("QUALIFICATION_POLICY_VIOLATION")
	}
	if q.pre != 1 || q.post != 1 {
		return false, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	return false, nil
}

func qualificationArguments(nonce, source, working, helper, encoded string) ([]string, error) {
	args := codexRPCArguments(nonce, source)
	if len(args) < 3 || args[len(args)-3] != "app-server" || args[len(args)-2] != "--listen" || args[len(args)-1] != "stdio://" {
		return nil, errors.New("QUALIFICATION_TEMPLATE_CHANGED")
	}
	args = append(args[:len(args)-3], "sandbox", "--include-managed-config", "--permission-profile", nonce, "-C", working, "--", helper, "--plan-v1", encoded)
	return args, nil
}

func qualificationReasonRank(reason string) int {
	switch reason {
	case "":
		return 0
	case "QUALIFICATION_POLICY_VIOLATION":
		return 6
	case "QUALIFICATION_IDENTITY_CHANGED":
		return 5
	case "QUALIFICATION_CLEANUP_UNKNOWN":
		return 4
	case "QUALIFICATION_CONTROL_INVALID":
		return 3
	case "QUALIFICATION_INCOMPLETE":
		return 2
	default:
		return 1
	}
}

func qualificationPreferredReason(current, next string) string {
	if qualificationReasonRank(next) > qualificationReasonRank(current) {
		return next
	}
	return current
}

func evaluateQualificationCase(name string, result qualificationprobe.Event, expectedDigest string, expectedBytes int) string {
	switch name {
	case "source_read":
		if !result.Opened || result.Errno != 0 || result.Digest != expectedDigest || result.Bytes != expectedBytes {
			return "QUALIFICATION_CONTROL_INVALID"
		}
	case "loopback_connect":
		if result.Opened {
			return "QUALIFICATION_POLICY_VIOLATION"
		}
		if result.Errno != 10013 {
			return "QUALIFICATION_INCOMPLETE"
		}
	default:
		if result.Opened {
			return "QUALIFICATION_POLICY_VIOLATION"
		}
		if result.Errno != 5 {
			return "QUALIFICATION_INCOMPLETE"
		}
	}
	return ""
}

func (q *nativeQualifier) ensureLaunch(ctx context.Context, in CodexLaunch) (obs nativeQualificationObservation, err error) {
	defer func() {
		q.mu.Lock()
		defer q.mu.Unlock()
		if err != nil {
			q.state = "FAILED"
			if !obs.Capture.JobZero && obs.Capture.PID != 0 {
				q.state = "UNKNOWN"
			}
		} else {
			q.observation = obs
			q.state = "OBSERVED_PASS"
		}
	}()
	o := q.options
	source := o.SyntheticSource
	root := o.ApprovedRoot
	obs = nativeQualificationObservation{TaskID: in.TaskID, RunID: in.RunID, Epoch: in.Epoch, SourceBindingHash: in.SourceBindingHash, Source: source, Directory: in.Directory, NativeHash: q.rpc.options.Descriptor.ExecutableHash, HelperHash: o.ShippedHelperSHA256, HostBuildHash: o.HostBuildSHA256, TemplateHash: CodexRPCPolicyIdentity(q.rpc.options.Descriptor.ExecutableHash).RequestedConfigSHA256, EnvironmentHash: Hash(mustJSON(Environment(""))), NormalHome: q.rpc.options.NormalHome, HostBoot: q.boot, PreflightNoChild: true}
	receipt := qualificationReceiptContext{TaskID: obs.TaskID, RunID: obs.RunID, Epoch: obs.Epoch, SourceBindingHash: obs.SourceBindingHash, Source: source, NativeHash: obs.NativeHash, HelperHash: obs.HelperHash, HostBuildHash: obs.HostBuildHash, TemplateHash: obs.TemplateHash, EnvironmentHash: obs.EnvironmentHash, NormalHome: obs.NormalHome, HostBoot: obs.HostBoot, ExpectedCases: qualificationprobe.FixedCases()}
	if ctx.Err() != nil || in.SourceBindingHash == "" || in.TaskID == "" || in.RunID == "" || in.Epoch == "" || !strings.EqualFold(in.Workspace, source) || !strings.EqualFold(filepath.Dir(source), root) || !strings.EqualFold(q.rpc.options.NormalHome, os.Getenv("USERPROFILE")) {
		return obs, errors.New("QUALIFICATION_SCOPE_MISMATCH")
	}
	if exactReal(root) != nil || exactReal(source) != nil || exactReal(o.ShippedHelper) != nil {
		return obs, errors.New("QUALIFICATION_SCOPE_MISMATCH")
	}
	if _, e := PrivateDirectory(root); e != nil {
		return obs, errors.New("QUALIFICATION_SCOPE_MISMATCH")
	}
	receiptDir := filepath.Join(root, "receipts")
	if e := os.Mkdir(receiptDir, 0700); e != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	if _, e := PrivateDirectory(receiptDir); e != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	receiptPath := filepath.Join(receiptDir, strings.TrimPrefix(Hash([]byte(in.RunID+"/"+in.Epoch)), "sha256:")+".json")
	obs.ReceiptPath = receiptPath
	persisted := false
	defer func() {
		if !persisted {
			reason := "QUALIFICATION_INCOMPLETE"
			if err != nil {
				reason = err.Error()
			}
			if e := persistQualificationCapture(receiptPath, obs.Capture, reason, receipt); e != nil {
				err = errors.New("QUALIFICATION_RECEIPT_UNCERTAIN")
			}
		}
	}()
	nativeHash, e := fileDigest(q.rpc.options.Executable)
	if e != nil || nativeHash != obs.NativeHash {
		return obs, errors.New("QUALIFICATION_IDENTITY_CHANGED")
	}
	helperHash, e := fileDigest(o.ShippedHelper)
	if e != nil || helperHash != o.ShippedHelperSHA256 {
		return obs, errors.New("QUALIFICATION_BOOTSTRAP_BLOCKED")
	}
	working, denied := filepath.Join(root, "QW"), filepath.Join(root, "D")
	receipt.Working, receipt.Denied = working, denied
	for _, dir := range []string{working, denied} {
		if e = os.Mkdir(dir, 0700); e != nil {
			return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
		}
		if _, e = PrivateDirectory(dir); e != nil {
			return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
		}
		if exactReal(dir) != nil {
			return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
		}
	}
	allow := []byte("researchos-qualification-allow-v1\n")
	writeS := []byte("researchos-qualification-source-write-v1\n")
	writeW := []byte("researchos-qualification-working-write-v1\n")
	deniedRaw := []byte("researchos-qualification-denied-v1\n")
	for path, raw := range map[string][]byte{filepath.Join(source, "allow.txt"): allow, filepath.Join(source, "write-existing.txt"): writeS, filepath.Join(working, "write-existing.txt"): writeW, filepath.Join(denied, "denied.txt"): deniedRaw, filepath.Join(working, ".researchos-codex-root"): []byte("researchos-codex-owned-root-v1\n")} {
		if e = createFixed(path, raw); e != nil {
			return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
		}
	}
	fixtureFiles := []string{filepath.Join(source, "allow.txt"), filepath.Join(source, "write-existing.txt"), filepath.Join(working, "write-existing.txt"), filepath.Join(denied, "denied.txt"), filepath.Join(working, ".researchos-codex-root")}
	for _, path := range fixtureFiles {
		if exactReal(path) != nil {
			return obs, errors.New("QUALIFICATION_SCOPE_MISMATCH")
		}
	}
	if _, e = os.Lstat(filepath.Join(source, "create-denied.txt")); !errors.Is(e, os.ErrNotExist) {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	if _, e = os.Lstat(filepath.Join(working, "create-denied.txt")); !errors.Is(e, os.ErrNotExist) {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	if err = hostWriteControl(filepath.Join(source, "write-existing.txt"), writeS); err != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	if err = hostWriteControl(filepath.Join(working, "write-existing.txt"), writeW); err != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	for _, path := range []string{filepath.Join(source, "create-denied.txt"), filepath.Join(working, "create-denied.txt")} {
		if err = hostCreateControl(path); err != nil {
			return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
		}
	}
	if raw, e := os.ReadFile(filepath.Join(denied, "denied.txt")); e != nil || !bytes.Equal(raw, deniedRaw) {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	if raw, e := os.ReadFile(filepath.Join(source, "allow.txt")); e != nil || !bytes.Equal(raw, allow) {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	listener, e := startQualificationListener(q.boot)
	if e != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	listenerClosed := false
	defer func() {
		if !listenerClosed {
			listener.listener.Close()
			<-listener.done
		}
	}()
	if e = listener.control("pre"); e != nil {
		return obs, errors.New("QUALIFICATION_CONTROL_INVALID")
	}
	receipt.PreControlsComplete = true
	nonce, e := rpcNonce()
	if e != nil {
		return obs, errors.New("QUALIFICATION_BOOTSTRAP_BLOCKED")
	}
	plan := qualificationprobe.Plan{Schema: qualificationprobe.Schema, Source: source, Working: working, Denied: denied, Nonce: nonce, Port: uint16(listener.listener.Addr().(*net.TCPAddr).Port), Cases: qualificationprobe.FixedCases()}
	receipt.LoopbackPort = plan.Port
	encoded, e := qualificationprobe.Encode(plan)
	if e != nil {
		return obs, errors.New("QUALIFICATION_SCOPE_MISMATCH")
	}
	receipt.Nonce, receipt.PlanHash, receipt.PlanEncoded = nonce, Hash([]byte(encoded)), encoded
	args, e := qualificationArguments(nonce, source, working, o.ShippedHelper, encoded)
	if e != nil {
		return obs, e
	}
	obs.RenderedArgvHash = Hash(mustJSON(args))
	receipt.RenderedArgvHash = obs.RenderedArgvHash
	receipt.RenderedArgv = append([]string(nil), args...)
	obs.PreflightNoChild = false
	obs.Capture = collectQualification(ctx, q.rpc.options.Executable, args, Environment(""), working, qualificationJobName(in.RunID, in.Epoch, nonce), receiptPath)
	reason := ""
	record := func(next string) {
		if next == "" {
			return
		}
		receipt.FindingCodes = append(receipt.FindingCodes, next)
		reason = qualificationPreferredReason(reason, next)
	}
	record(qualificationCaptureReason(obs.Capture))
	if e = listener.control("post"); e != nil {
		record("QUALIFICATION_CONTROL_INVALID")
	}
	unexpected, listenerErr := listener.closeAndCheck()
	if unexpected {
		record("QUALIFICATION_POLICY_VIOLATION")
	} else if listenerErr != nil {
		record("QUALIFICATION_CONTROL_INVALID")
	}
	listenerClosed = true
	if raw, e := os.ReadFile(filepath.Join(source, "allow.txt")); e != nil || !bytes.Equal(raw, allow) {
		record("QUALIFICATION_CONTROL_INVALID")
	}
	if raw, e := os.ReadFile(filepath.Join(denied, "denied.txt")); e != nil || !bytes.Equal(raw, deniedRaw) {
		record("QUALIFICATION_CONTROL_INVALID")
	}
	if raw, e := os.ReadFile(filepath.Join(working, ".researchos-codex-root")); e != nil || string(raw) != "researchos-codex-owned-root-v1\n" {
		record("QUALIFICATION_CONTROL_INVALID")
	}
	for _, control := range []struct {
		path     string
		expected []byte
	}{{filepath.Join(source, "write-existing.txt"), writeS}, {filepath.Join(working, "write-existing.txt"), writeW}} {
		path, expected := control.path, control.expected
		if raw, e := os.ReadFile(path); e != nil || !bytes.Equal(raw, expected) || hostWriteControl(path, expected) != nil {
			record("QUALIFICATION_CONTROL_INVALID")
		}
	}
	for _, path := range []string{filepath.Join(source, "create-denied.txt"), filepath.Join(working, "create-denied.txt")} {
		if _, e := os.Lstat(path); e == nil {
			record("QUALIFICATION_POLICY_VIOLATION")
		} else if !errors.Is(e, os.ErrNotExist) {
			record("QUALIFICATION_CONTROL_INVALID")
		}
		if e := hostCreateControl(path); e != nil {
			record("QUALIFICATION_CONTROL_INVALID")
		}
	}
	if exactReal(source) != nil || exactReal(working) != nil || exactReal(denied) != nil || exactReal(o.ShippedHelper) != nil {
		record("QUALIFICATION_IDENTITY_CHANGED")
	}
	for _, path := range fixtureFiles {
		if exactReal(path) != nil {
			record("QUALIFICATION_IDENTITY_CHANGED")
		}
	}
	if digest, e := fileDigest(q.rpc.options.Executable); e != nil || digest != obs.NativeHash {
		record("QUALIFICATION_IDENTITY_CHANGED")
	}
	if digest, e := fileDigest(o.ShippedHelper); e != nil || digest != o.ShippedHelperSHA256 {
		record("QUALIFICATION_IDENTITY_CHANGED")
	}
	if len(obs.Capture.Stderr.raw) != 0 {
		record("QUALIFICATION_INCOMPLETE")
	}
	results, parseErr := qualificationprobe.ParseTranscript(obs.Capture.Stdout.raw)
	if parseErr != nil {
		record("QUALIFICATION_INCOMPLETE")
	} else {
		receipt.ObservedCaseBitmap = qualificationprobe.CompleteBitmap
		digest := Hash(allow)
		for _, name := range qualificationprobe.Cases {
			result := results[name]
			receipt.CaseResults = append(receipt.CaseResults, qualificationCaseOutcome{Name: name, Opened: result.Opened, Errno: result.Errno, Digest: result.Digest, Bytes: result.Bytes})
			record(evaluateQualificationCase(name, result, digest, len(allow)))
		}
	}
	receipt.PostControlsComplete = reason == ""
	if e = persistQualificationCapture(receiptPath, obs.Capture, reason, receipt); e != nil {
		return obs, errors.New("QUALIFICATION_RECEIPT_UNCERTAIN")
	}
	persisted = true
	if reason != "" {
		return obs, errors.New(reason)
	}
	obs.Until = time.Now().Add(2 * time.Minute)
	return obs, nil
}
