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
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
)

type CodexRPCOptions struct {
	Executable string
	Descriptor CodexDescriptor
	NormalHome string
}

// Only the trusted Go test constructor accepts an in-memory qualification
// fixture. The production constructor never has a qualifier in Slice B1.
type CodexQualificationProvider interface {
	Ensure(context.Context, CodexTurnEvidence) error
}
type CodexQualificationFunc func(context.Context, CodexTurnEvidence) error

func (f CodexQualificationFunc) Ensure(ctx context.Context, e CodexTurnEvidence) error {
	return f(ctx, e)
}

type codexRPC struct {
	options   CodexRPCOptions
	qualifier CodexQualificationProvider
	// Go-only fake executable tests may replace the executable argv, never
	// the fixed production policy builder or its canonical identity.
	fixtureArgs []string
	fixtureEnv  []string
}

func NewCodexRPC(options CodexRPCOptions) (CodexDriver, error) {
	if !filepath.IsAbs(options.Executable) || strings.ToLower(filepath.Ext(options.Executable)) != ".exe" ||
		!strings.HasPrefix(options.Descriptor.ExecutableHash, "sha256:") || len(options.Descriptor.ExecutableHash) != 71 ||
		!filepath.IsAbs(options.NormalHome) || strings.ContainsAny(options.NormalHome, ";\x00\r\n") ||
		!strings.EqualFold(filepath.Clean(options.NormalHome), filepath.Clean(os.Getenv("USERPROFILE"))) {
		return nil, errors.New("CODEX_RPC_COMPOSITION_INVALID")
	}
	options.Descriptor.NativeTransport = CodexRPCTransport
	return &codexRPC{options: options}, nil
}

func NewCodexRPCForTrustedGoTest(options CodexRPCOptions, provider CodexQualificationProvider) (CodexDriver, error) {
	if provider == nil {
		return nil, errors.New("CODEX_RPC_TEST_QUALIFIER_REQUIRED")
	}
	d, err := NewCodexRPC(options)
	if err != nil {
		return nil, err
	}
	d.(*codexRPC).qualifier = provider
	return d, nil
}

func (d *codexRPC) Descriptor() CodexDescriptor { return d.options.Descriptor }
func (d *codexRPC) ReadinessSnapshot() CodexReadiness {
	return CodexReadiness{State: "PREPARATION_READY", PolicyIdentity: CodexRPCPolicyIdentity(d.options.Descriptor.ExecutableHash)}
}
func (d *codexRPC) readiness() CodexReadiness {
	return EvaluateCodexReadiness(d.Descriptor(), d.ReadinessSnapshot(), CodexRPCPolicyIdentity(d.options.Descriptor.ExecutableHash))
}

type rpcRun struct {
	mu           sync.Mutex
	cancel       context.CancelFunc
	done         chan struct{}
	result       CodexResult
	err          error
	cancelled    bool
	turnIntent   bool
	guardFailure error
}

func (r *rpcRun) Cancel() {
	r.cancel()
	r.mu.Lock()
	r.cancelled = true
	r.mu.Unlock()
}
func (r *rpcRun) Wait(ctx context.Context) (CodexResult, error) {
	select {
	case <-r.done:
		r.mu.Lock()
		defer r.mu.Unlock()
		value := r.result
		value.Stdout = bytes.Clone(value.Stdout)
		value.Stderr = bytes.Clone(value.Stderr)
		return value, r.err
	case <-ctx.Done():
		return CodexResult{}, ctx.Err()
	}
}

func rpcNonce() (string, error) {
	var raw [16]byte
	if _, err := rand.Read(raw[:]); err != nil {
		return "", err
	}
	return "researchos-readonly-" + hex.EncodeToString(raw[:]), nil
}

var rpcPeekNamedPipe = windows.NewLazySystemDLL("kernel32.dll").NewProc("PeekNamedPipe")

func rpcPendingBytes(pipe *os.File) (uint32, error) {
	var available uint32
	ok, _, err := rpcPeekNamedPipe.Call(pipe.Fd(), 0, 0, 0, uintptr(unsafe.Pointer(&available)), 0)
	if ok == 0 {
		return 0, err
	}
	return available, nil
}

const (
	rpcJobActiveProcessLimit = 16
	rpcProcessCommitLimit    = uintptr(1 << 30)
	rpcJobCommitLimit        = uintptr(2 << 30)
	rpcJobLimitFlags         = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
		windows.JOB_OBJECT_LIMIT_ACTIVE_PROCESS |
		windows.JOB_OBJECT_LIMIT_PROCESS_MEMORY |
		windows.JOB_OBJECT_LIMIT_JOB_MEMORY
)

type rpcJobBudget struct {
	LimitFlags         uint32  `json:"limit_flags"`
	ActiveProcessLimit uint32  `json:"active_process_limit"`
	ProcessCommitBytes uintptr `json:"process_commit_bytes"`
	JobCommitBytes     uintptr `json:"job_commit_bytes"`
}

func rpcApplyJobBudget(job windows.Handle) (rpcJobBudget, error) {
	requested := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	requested.BasicLimitInformation.LimitFlags = rpcJobLimitFlags
	requested.BasicLimitInformation.ActiveProcessLimit = rpcJobActiveProcessLimit
	requested.ProcessMemoryLimit = rpcProcessCommitLimit
	requested.JobMemoryLimit = rpcJobCommitLimit
	if _, err := windows.SetInformationJobObject(job, windows.JobObjectExtendedLimitInformation,
		uintptr(unsafe.Pointer(&requested)), uint32(unsafe.Sizeof(requested))); err != nil {
		return rpcJobBudget{}, errors.New("CODEX_RPC_JOB_BUDGET_SET_FAILED")
	}
	actual := windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION{}
	if err := windows.QueryInformationJobObject(job, windows.JobObjectExtendedLimitInformation,
		uintptr(unsafe.Pointer(&actual)), uint32(unsafe.Sizeof(actual)), nil); err != nil {
		return rpcJobBudget{}, errors.New("CODEX_RPC_JOB_BUDGET_QUERY_FAILED")
	}
	if actual.BasicLimitInformation.LimitFlags != rpcJobLimitFlags ||
		actual.BasicLimitInformation.ActiveProcessLimit != rpcJobActiveProcessLimit ||
		actual.ProcessMemoryLimit != rpcProcessCommitLimit || actual.JobMemoryLimit != rpcJobCommitLimit {
		return rpcJobBudget{}, errors.New("CODEX_RPC_JOB_BUDGET_MISMATCH")
	}
	return rpcJobBudget{actual.BasicLimitInformation.LimitFlags, actual.BasicLimitInformation.ActiveProcessLimit,
		actual.ProcessMemoryLimit, actual.JobMemoryLimit}, nil
}

func rpcPersistJobBudget(directory, jobName, source, sourceBindingHash string, budget rpcJobBudget) error {
	file, err := os.OpenFile(filepath.Join(directory, "native-rpc-job-limits.json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return errors.New("CODEX_RPC_JOB_BUDGET_PERSIST_FAILED")
	}
	record := struct {
		Job, Source, SourceBindingHash, AppliedAtUTC string
		Requested, Queried                           rpcJobBudget
	}{jobName, source, sourceBindingHash, time.Now().UTC().Format(time.RFC3339Nano),
		rpcJobBudget{rpcJobLimitFlags, rpcJobActiveProcessLimit, rpcProcessCommitLimit, rpcJobCommitLimit}, budget}
	raw, _ := json.Marshal(record)
	n, writeErr := file.Write(append(raw, '\n'))
	if writeErr == nil && n != len(raw)+1 {
		writeErr = io.ErrShortWrite
	}
	if writeErr == nil {
		writeErr = file.Sync()
	}
	closeErr := file.Close()
	if writeErr != nil || closeErr != nil {
		return errors.New("CODEX_RPC_JOB_BUDGET_PERSIST_FAILED")
	}
	return nil
}

type rpcCaptureReader struct {
	pipe *os.File
	file *os.File
	raw  *bytes.Buffer
}

var errRPCCaptureLimit = errors.New("CODEX_RPC_CAPTURE_LIMIT")

func (c *rpcCaptureReader) Read(dst []byte) (int, error) {
	remaining := rpcCaptureLimit - c.raw.Len()
	if remaining <= 0 {
		return 0, errRPCCaptureLimit
	}
	if len(dst) > remaining {
		dst = dst[:remaining]
	}
	n, err := c.pipe.Read(dst)
	if n > 0 {
		c.raw.Write(dst[:n])
		written, writeErr := c.file.Write(dst[:n])
		if writeErr == nil && written != n {
			writeErr = io.ErrShortWrite
		}
		if writeErr == nil {
			writeErr = c.file.Sync()
		}
		if writeErr != nil {
			return 0, errors.New("CODEX_RPC_CAPTURE_PERSIST_FAILED")
		}
	}
	return n, err
}

func (d *codexRPC) Start(ctx context.Context, in CodexLaunch, cb CodexCallbacks) (CodexHandle, error) {
	if gate := d.readiness(); gate.State != "PREPARATION_READY" {
		return nil, errors.New(gate.Reason)
	}
	if !filepath.IsAbs(in.Workspace) || !filepath.IsAbs(in.Directory) || in.SourceBindingHash == "" ||
		in.TaskID == "" || in.RunID == "" || strings.TrimSpace(in.Prompt) == "" || len(in.Prompt) > 65536 ||
		in.Timeout <= 0 || in.Timeout > 15*time.Minute || cb.BeforeResume == nil || cb.BeforeModelTurn == nil || cb.Event == nil {
		return nil, errors.New("CODEX_RPC_LAUNCH_INVALID")
	}
	epoch, err := strconv.ParseInt(in.Epoch, 10, 64)
	if err != nil || epoch <= 0 || strconv.FormatInt(epoch, 10) != in.Epoch {
		return nil, errors.New("CODEX_EPOCH_INVALID")
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	binary, err := os.Open(d.options.Executable)
	if err != nil {
		return nil, errors.New("CODEX_EXECUTABLE_UNAVAILABLE")
	}
	hash := sha256.New()
	_, hashErr := io.Copy(hash, binary)
	closeErr := binary.Close()
	if hashErr != nil || closeErr != nil || "sha256:"+hex.EncodeToString(hash.Sum(nil)) != d.options.Descriptor.ExecutableHash {
		return nil, errors.New("CODEX_EXECUTABLE_CHANGED")
	}
	profile, err := rpcNonce()
	if err != nil {
		return nil, errors.New("CODEX_RPC_NONCE_UNAVAILABLE")
	}
	cwd := filepath.Join(in.Directory, "cwd")
	input, err := codexExecutionInput(in.Workspace, cwd, in.Prompt)
	if err != nil {
		return nil, err
	}
	if err = os.Mkdir(in.Directory, 0700); err != nil {
		return nil, err
	}
	if _, err = PrivateDirectory(in.Directory); err != nil {
		return nil, err
	}
	if err = os.Mkdir(cwd, 0700); err != nil {
		return nil, err
	}
	if err = os.WriteFile(filepath.Join(cwd, ".researchos-codex-root"), []byte("researchos-codex-owned-root-v1\n"), 0600); err != nil {
		return nil, err
	}
	stdinR, stdinW, err := os.Pipe()
	if err != nil {
		return nil, err
	}
	captureR, captureW, err := os.Pipe()
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		return nil, err
	}
	// Duplicate the write HANDLE into the same kernel pipe: stdout and stderr
	// have one ordered byte stream and exactly one reader.
	var stderrHandle windows.Handle
	err = windows.DuplicateHandle(windows.CurrentProcess(), windows.Handle(captureW.Fd()), windows.CurrentProcess(), &stderrHandle, 0, true, windows.DUPLICATE_SAME_ACCESS)
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		captureR.Close()
		captureW.Close()
		return nil, err
	}
	stderrW := os.NewFile(uintptr(stderrHandle), "rpc-same-capture-stderr")
	closeAll := func() { stdinR.Close(); stdinW.Close(); captureR.Close(); captureW.Close(); stderrW.Close() }
	jobName := "researchos-codex-rpc-" + strings.TrimPrefix(Hash([]byte(in.RunID+"/"+in.Epoch)), "sha256:")
	job, err := newJob(jobName)
	if err != nil {
		closeAll()
		return nil, err
	}
	budget, err := rpcApplyJobBudget(job)
	if err != nil {
		closeJob(job)
		closeAll()
		return nil, err
	}
	if err = rpcPersistJobBudget(in.Directory, jobName, in.Workspace, in.SourceBindingHash, budget); err != nil {
		closeJob(job)
		closeAll()
		return nil, err
	}
	args := codexRPCArguments(profile, in.Workspace)
	if d.fixtureArgs != nil {
		args = append([]string(nil), d.fixtureArgs...)
	}
	env := Environment("")
	if d.fixtureArgs != nil {
		env = append(env, d.fixtureEnv...)
	}
	for _, entry := range env {
		if strings.HasPrefix(strings.ToUpper(entry), "CODEX_HOME=") {
			closeJob(job)
			closeAll()
			return nil, errors.New("CODEX_HOME_INHERITED")
		}
	}
	captureFile, err := os.OpenFile(filepath.Join(in.Directory, "native-rpc-capture.raw"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		closeJob(job)
		closeAll()
		return nil, errors.New("CODEX_RPC_CAPTURE_PERSIST_FAILED")
	}
	proc, err := launchWithCallback(job, Command{Executable: d.options.Executable, Args: args, Directory: cwd}, env, stdinR, captureW, stderrW,
		func(p *process) error {
			if gate := d.readiness(); gate.State != "PREPARATION_READY" {
				return errors.New(gate.Reason)
			}
			return cb.BeforeResume(CodexIdentity{PID: p.pid, Created: p.created, Job: jobName})
		})
	if err != nil {
		captureFile.Close()
		closeJob(job)
		closeAll()
		return nil, err
	}
	stdinR.Close()
	captureW.Close()
	stderrW.Close()
	child, cancel := context.WithTimeout(ctx, in.Timeout)
	run := &rpcRun{cancel: cancel, done: make(chan struct{})}
	go d.run(child, cancel, run, proc, job, jobName, stdinW, captureR, captureFile, in, input, profile, cwd, cb)
	return run, nil
}

func (d *codexRPC) run(ctx context.Context, cancel context.CancelFunc, r *rpcRun, p *process, job windows.Handle, jobName string,
	stdinW, captureR, captureFile *os.File, in CodexLaunch, input []byte, profile, cwd string, cb CodexCallbacks) {
	result := CodexResult{State: "UNKNOWN", ExitCode: -1, Identity: CodexIdentity{PID: p.pid, Created: p.created, Job: jobName}}
	var raw bytes.Buffer
	var failure error
	var reader *bufio.Reader
	stopWatch := make(chan struct{})
	go func() {
		select {
		case <-ctx.Done():
			_ = killJob(job)
			_ = stdinW.Close()
		case <-stopWatch:
		}
	}()
	defer func() {
		close(stopWatch)
		cancel()
		_ = killJob(job)
		deadline := time.Now().Add(5 * time.Second)
		for time.Now().Before(deadline) {
			exited, code, e := p.exited()
			ids, je := jobPIDs(job)
			if e == nil && je == nil && exited && len(ids) == 0 {
				result.Stopped = true
				result.ExitCode = code
				break
			}
			time.Sleep(20 * time.Millisecond)
		}
		if reader != nil && result.Stopped {
			if result.State == "COMPLETED" {
				for {
					line, drainErr := reader.ReadSlice('\n')
					if len(line) != 0 {
						if drainErr != nil || rpcTerminalFrame(bytes.TrimSuffix(line, []byte{'\n'}), result.ThreadID) != nil {
							failure = errors.New("CODEX_RPC_TERMINAL_TRAILING_BYTES")
						}
					}
					if drainErr == io.EOF {
						result.StreamsDrained = true
						break
					}
					if drainErr != nil {
						if failure == nil {
							failure = errors.New("CODEX_RPC_TERMINAL_DRAIN_FAILED")
						}
						break
					}
				}
			} else {
				_, drainErr := io.Copy(io.Discard, reader)
				result.StreamsDrained = drainErr == nil
				if drainErr != nil && failure == nil {
					failure = errors.New("CODEX_RPC_TERMINAL_DRAIN_FAILED")
				}
			}
		}
		stdinW.Close()
		captureR.Close()
		if err := captureFile.Sync(); err != nil && failure == nil {
			failure = errors.New("CODEX_RPC_CAPTURE_PERSIST_FAILED")
		}
		if err := captureFile.Close(); err != nil && failure == nil {
			failure = errors.New("CODEX_RPC_CAPTURE_PERSIST_FAILED")
		}
		p.close()
		closeJob(job)
		result.Stdout = bytes.Clone(raw.Bytes())
		result.CleanupComplete = result.Stopped && result.StreamsDrained
		if !result.CleanupComplete || failure != nil {
			result.State = "UNKNOWN"
		}
		if failure != nil {
			result.Failure = failure.Error()
		}
		receipt, receiptErr := os.OpenFile(filepath.Join(in.Directory, "native-rpc-terminal.json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if receiptErr == nil {
			projection := struct {
				State, Failure, ThreadID                 string
				CaptureBytes                             int
				Stopped, StreamsDrained, CleanupComplete bool
			}{result.State, result.Failure, result.ThreadID, raw.Len(), result.Stopped, result.StreamsDrained, result.CleanupComplete}
			encoded, _ := json.Marshal(projection)
			_, receiptErr = receipt.Write(append(encoded, '\n'))
			if receiptErr == nil {
				receiptErr = receipt.Sync()
			}
			closeErr := receipt.Close()
			if receiptErr == nil {
				receiptErr = closeErr
			}
		}
		if receiptErr != nil {
			result.State = "UNKNOWN"
			result.Failure = "CODEX_RPC_RECEIPT_FAILED"
		}
		r.mu.Lock()
		r.result, r.err = result, nil
		r.mu.Unlock()
		close(r.done)
	}()
	prepCtx, prepCancel := context.WithTimeout(ctx, rpcPreparationSeconds*time.Second)
	defer prepCancel()
	stopRead := make(chan struct{})
	watchDone := make(chan struct{})
	var stopReadOnce sync.Once
	defer stopReadOnce.Do(func() { close(stopRead) })
	go func() {
		defer close(watchDone)
		select {
		case <-prepCtx.Done():
			_ = killJob(job)
			_ = stdinW.Close()
		case <-stopRead:
		}
	}()
	captureSource := &rpcCaptureReader{pipe: captureR, file: captureFile, raw: &raw}
	reader = bufio.NewReaderSize(captureSource, rpcFrameLimit+1)
	read := func() (map[string]any, error) {
		line, err := reader.ReadSlice('\n')
		if err != nil {
			if errors.Is(err, errRPCCaptureLimit) {
				return nil, err
			}
			if strings.Contains(err.Error(), "CODEX_RPC_CAPTURE_PERSIST_FAILED") {
				return nil, err
			}
			return nil, errors.New("CODEX_RPC_FRAME_TRUNCATED")
		}
		return rpcFrame(bytes.TrimSuffix(line, []byte{'\n'}))
	}
	write := func(frame []byte) error {
		if len(frame) > rpcFrameLimit {
			return errors.New("CODEX_RPC_REQUEST_LIMIT")
		}
		n, err := stdinW.Write(frame)
		if err != nil || n != len(frame) {
			return errors.New("CODEX_RPC_WRITE_UNCERTAIN")
		}
		return nil
	}
	if failure = write(rpcInitialize()); failure != nil {
		return
	}
	var frame map[string]any
	frame, failure = read()
	if failure != nil {
		return
	}
	if id, ok := rpcResponseID(frame); !ok || id != 1 || frame["error"] != nil || frame["result"] == nil {
		failure = errors.New("CODEX_RPC_INITIALIZE_FAILED")
		return
	}
	if failure = write(rpcInitialized()); failure != nil {
		return
	}
	if failure = write(rpcThreadStart(cwd, in.Workspace, profile)); failure != nil {
		return
	}
	threadID := ""
	started := false
	startedID := ""
	for !started || threadID == "" {
		frame, failure = read()
		if failure != nil {
			return
		}
		if id, ok := rpcResponseID(frame); ok {
			if id != 2 || threadID != "" {
				failure = errors.New("CODEX_RPC_DUPLICATE_RESPONSE")
				return
			}
			threadID, failure = rpcThreadEvidence(frame, profile, cwd, in.Workspace)
			if failure != nil {
				return
			}
		} else if frame["method"] == "thread/started" && !started {
			params, ok := frame["params"].(map[string]any)
			thread, tok := params["thread"].(map[string]any)
			if !ok || !tok || thread["id"] == "" {
				failure = errors.New("CODEX_RPC_NOTIFICATION_INVALID")
				return
			}
			startedID, _ = thread["id"].(string)
			started = true
		} else {
			failure = errors.New("CODEX_RPC_UNEXPECTED_STARTUP_FRAME")
			return
		}
	}
	if startedID != threadID {
		failure = errors.New("CODEX_RPC_NOTIFICATION_THREAD_MISMATCH")
		return
	}
	if reader.Buffered() != 0 {
		failure = errors.New("CODEX_RPC_STARTUP_TRAILING_BYTES")
		return
	}
	if pending, peekErr := rpcPendingBytes(captureR); peekErr != nil || pending != 0 {
		failure = errors.New("CODEX_RPC_STARTUP_TRAILING_BYTES")
		return
	}
	stopReadOnce.Do(func() { close(stopRead) })
	<-watchDone
	prepCancel()
	guardStop := make(chan struct{})
	guardDone := make(chan struct{})
	var stopGuardOnce sync.Once
	stopGuard := func() { stopGuardOnce.Do(func() { close(guardStop); <-guardDone }) }
	defer stopGuard()
	go func() {
		defer close(guardDone)
		tick := time.NewTicker(5 * time.Millisecond)
		defer tick.Stop()
		for {
			select {
			case <-guardStop:
				return
			case <-ctx.Done():
				return
			case <-tick.C:
				pending, peekErr := rpcPendingBytes(captureR)
				exited, _, exitErr := p.exited()
				if peekErr != nil || pending != 0 || exitErr != nil || exited {
					r.mu.Lock()
					if r.guardFailure == nil {
						r.guardFailure = errors.New("CODEX_RPC_PRETURN_PIPE_DIRTY")
					}
					r.mu.Unlock()
					// The main protocol reader is parked during callbacks.
					// Persist bytes already visible in the pipe before a
					// hard stop can discard their diagnostic evidence.
					if pending > 0 && peekErr == nil {
						_, _ = io.CopyN(io.Discard, captureSource, int64(pending))
					}
					cancel()
					return
				}
			}
		}
	}()
	evidence := CodexTurnEvidence{PolicyIdentity: CodexRPCPolicyIdentity(d.options.Descriptor.ExecutableHash),
		RenderedConfigSHA256: codexRPCConfigHash(profile, cwd, in.Workspace), SourceBindingHash: in.SourceBindingHash,
		ProfileNonce: profile, ThreadID: threadID, TaskID: in.TaskID, RunID: in.RunID, Epoch: in.Epoch,
		Process: result.Identity, CaptureBytes: int64(raw.Len())}
	if d.qualifier == nil {
		failure = errors.New("QUALIFICATION_REQUIRED")
		return
	}
	if failure = d.qualifier.Ensure(ctx, evidence); failure != nil {
		return
	}
	r.mu.Lock()
	guardFailure := r.guardFailure
	r.mu.Unlock()
	if guardFailure != nil {
		failure = errors.New("CODEX_RPC_PRETURN_PIPE_DIRTY")
		return
	}
	if ctx.Err() != nil {
		failure = errors.New("CODEX_RPC_TURN_FENCE_CLOSED")
		return
	}
	if gate := d.readiness(); gate.State != "PREPARATION_READY" {
		failure = errors.New(gate.Reason)
		return
	}
	if failure = cb.BeforeModelTurn(evidence); failure != nil {
		return
	}
	r.mu.Lock()
	guardFailure = r.guardFailure
	r.mu.Unlock()
	if guardFailure != nil {
		failure = errors.New("CODEX_RPC_PRETURN_PIPE_DIRTY")
		return
	}
	if ctx.Err() != nil {
		failure = errors.New("CODEX_RPC_TURN_FENCE_CLOSED")
		return
	}
	r.mu.Lock()
	if r.cancelled || ctx.Err() != nil || r.turnIntent {
		r.mu.Unlock()
		failure = errors.New("CODEX_RPC_TURN_FENCE_CLOSED")
		return
	}
	r.turnIntent = true
	r.mu.Unlock()
	intent, err := os.OpenFile(filepath.Join(in.Directory, "native-turn-write-intent.json"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		failure = errors.New("CODEX_RPC_TURN_INTENT_UNCERTAIN")
		return
	}
	intentRaw, _ := json.Marshal(evidence)
	_, err = intent.Write(intentRaw)
	if err == nil {
		err = intent.Sync()
	}
	closeErr := intent.Close()
	if err != nil || closeErr != nil {
		failure = errors.New("CODEX_RPC_TURN_INTENT_UNCERTAIN")
		return
	}
	stopGuard()
	r.mu.Lock()
	pending, peekErr := rpcPendingBytes(captureR)
	exited, _, exitErr := p.exited()
	if r.cancelled || ctx.Err() != nil || r.guardFailure != nil || reader.Buffered() != 0 ||
		peekErr != nil || pending != 0 || exitErr != nil || exited {
		r.mu.Unlock()
		failure = errors.New("CODEX_RPC_TURN_FENCE_CLOSED")
		return
	}
	// Cancel invokes context cancellation before acquiring this lock, so the
	// overall Job watcher can still stop a blocked stdin write.
	failure = write(rpcTurnStart(threadID, input))
	r.mu.Unlock()
	if failure != nil {
		return
	}
	result.ThreadID = threadID
	completed := false
	acknowledged := false
	startedTurn := false
	turnID := ""
	eventTurnID := ""
	eventCount := 0
	activeItems := map[string]string{}
	seenItems := map[string]bool{}
	finalAssistant := false
	for !completed {
		frame, failure = read()
		if failure != nil {
			return
		}
		eventCount++
		if eventCount > 4096 {
			failure = errors.New("CODEX_RPC_EVENT_LIMIT")
			return
		}
		if id, ok := rpcResponseID(frame); ok {
			if id != 3 || acknowledged || frame["error"] != nil || frame["result"] == nil {
				failure = errors.New("CODEX_RPC_TURN_RESPONSE_INVALID")
				return
			}
			response, ok := frame["result"].(map[string]any)
			if !ok {
				failure = errors.New("CODEX_RPC_TURN_RESPONSE_INVALID")
				return
			}
			turn, ok := response["turn"].(map[string]any)
			if !ok {
				failure = errors.New("CODEX_RPC_TURN_RESPONSE_INVALID")
				return
			}
			turnID, ok = turn["id"].(string)
			if !ok || turnID == "" || len(turnID) > 256 || (eventTurnID != "" && eventTurnID != turnID) {
				failure = errors.New("CODEX_RPC_TURN_ID_MISMATCH")
				return
			}
			acknowledged = true
			continue
		}
		method, ok := frame["method"].(string)
		if !ok {
			failure = errors.New("CODEX_RPC_SERVER_REQUEST")
			return
		}
		params, ok := frame["params"].(map[string]any)
		if !ok || params["threadId"] != threadID {
			failure = errors.New("CODEX_RPC_EVENT_THREAD_MISMATCH")
			return
		}
		if method == "thread/status/changed" {
			status, _ := params["status"].(map[string]any)
			if status["type"] != "active" && status["type"] != "idle" {
				failure = errors.New("CODEX_RPC_THREAD_STATUS_INVALID")
				return
			}
			continue
		}
		candidate, _ := params["turnId"].(string)
		if method == "turn/started" || method == "turn/completed" {
			turn, tok := params["turn"].(map[string]any)
			if !tok {
				failure = errors.New("CODEX_RPC_TURN_EVENT_INVALID")
				return
			}
			candidate, _ = turn["id"].(string)
		}
		if candidate == "" || len(candidate) > 256 || (turnID != "" && candidate != turnID) ||
			(eventTurnID != "" && candidate != eventTurnID) {
			failure = errors.New("CODEX_RPC_EVENT_TURN_MISMATCH")
			return
		}
		eventTurnID = candidate
		switch method {
		case "turn/started":
			if startedTurn {
				failure = errors.New("CODEX_RPC_DUPLICATE_TURN_START")
				return
			}
			startedTurn = true
		case "thread/tokenUsage/updated":
			if !startedTurn {
				failure = errors.New("CODEX_RPC_EVENT_BEFORE_TURN")
				return
			}
		case "item/started":
			if !startedTurn {
				failure = errors.New("CODEX_RPC_EVENT_BEFORE_TURN")
				return
			}
			item, _ := params["item"].(map[string]any)
			itemID, _ := item["id"].(string)
			itemType, _ := item["type"].(string)
			if itemID == "" || len(itemID) > 256 || seenItems[itemID] ||
				(itemType != "agentMessage" && itemType != "reasoning" && itemType != "commandExecution") {
				failure = errors.New("CODEX_RPC_UNEXPECTED_ITEM")
				return
			}
			seenItems[itemID] = true
			activeItems[itemID] = itemType
			if itemType == "commandExecution" {
				if failure = cb.Event(CodexEvent{Kind: "TOOL_EVENT", ToolID: itemID, ToolName: itemType, ToolPhase: "started", NativeID: itemID}); failure != nil {
					return
				}
			}
		case "item/agentMessage/delta", "item/reasoning/summaryTextDelta",
			"item/reasoning/summaryPartAdded", "item/reasoning/textDelta",
			"item/commandExecution/outputDelta":
			if !startedTurn {
				failure = errors.New("CODEX_RPC_EVENT_BEFORE_TURN")
				return
			}
			itemID, _ := params["itemId"].(string)
			expectedType := "reasoning"
			if method == "item/agentMessage/delta" {
				expectedType = "agentMessage"
			}
			if method == "item/commandExecution/outputDelta" {
				expectedType = "commandExecution"
			}
			if itemID == "" || activeItems[itemID] != expectedType {
				failure = errors.New("CODEX_RPC_ITEM_ID_MISMATCH")
				return
			}
			if method == "item/agentMessage/delta" {
				if _, ok := params["delta"].(string); !ok {
					failure = errors.New("CODEX_RPC_DELTA_INVALID")
					return
				}
			}
		case "item/completed":
			if !startedTurn {
				failure = errors.New("CODEX_RPC_EVENT_BEFORE_TURN")
				return
			}
			item, _ := params["item"].(map[string]any)
			itemID, _ := item["id"].(string)
			itemType, _ := item["type"].(string)
			if itemID == "" || activeItems[itemID] != itemType {
				failure = errors.New("CODEX_RPC_ITEM_ID_MISMATCH")
				return
			}
			delete(activeItems, itemID)
			if itemType == "agentMessage" {
				text, ok := item["text"].(string)
				if !ok || strings.TrimSpace(text) == "" {
					failure = errors.New("CODEX_RPC_ASSISTANT_INVALID")
					return
				}
				result.Assistant = text
				finalAssistant = true
				if failure = cb.Event(CodexEvent{Kind: "ASSISTANT_MESSAGE", Text: text, NativeID: itemID}); failure != nil {
					return
				}
			} else if itemType == "commandExecution" && (item["status"] != "completed" || item["exitCode"] != json.Number("0")) {
				failure = errors.New("CODEX_RPC_TOOL_FAILED")
				return
			} else if itemType == "commandExecution" {
				if failure = cb.Event(CodexEvent{Kind: "TOOL_EVENT", ToolID: itemID, ToolName: itemType, ToolPhase: "completed", NativeID: itemID}); failure != nil {
					return
				}
			} else if itemType != "reasoning" {
				failure = errors.New("CODEX_RPC_UNEXPECTED_ITEM")
				return
			}
		case "turn/completed":
			turn, _ := params["turn"].(map[string]any)
			status, _ := turn["status"].(string)
			if !acknowledged || !startedTurn || status != "completed" || len(activeItems) != 0 || !finalAssistant {
				failure = errors.New("CODEX_RPC_TURN_NOT_COMPLETED")
				return
			}
			completed = true
		default:
			failure = errors.New("CODEX_RPC_UNEXPECTED_EVENT")
			return
		}
	}
	result.State = "COMPLETED"
}
