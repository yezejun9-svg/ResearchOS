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
	mu         sync.Mutex
	cancel     context.CancelFunc
	done       chan struct{}
	result     CodexResult
	err        error
	cancelled  bool
	turnIntent bool
}

func (r *rpcRun) Cancel() {
	r.mu.Lock()
	r.cancelled = true
	r.mu.Unlock()
	r.cancel()
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
	proc, err := launchWithCallback(job, Command{Executable: d.options.Executable, Args: args, Directory: cwd}, env, stdinR, captureW, stderrW,
		func(p *process) error {
			if gate := d.readiness(); gate.State != "PREPARATION_READY" {
				return errors.New(gate.Reason)
			}
			return cb.BeforeResume(CodexIdentity{PID: p.pid, Created: p.created, Job: jobName})
		})
	if err != nil {
		closeJob(job)
		closeAll()
		return nil, err
	}
	stdinR.Close()
	captureW.Close()
	stderrW.Close()
	child, cancel := context.WithTimeout(ctx, in.Timeout)
	run := &rpcRun{cancel: cancel, done: make(chan struct{})}
	go d.run(child, cancel, run, proc, job, jobName, stdinW, captureR, in, input, profile, cwd, cb)
	return run, nil
}

func (d *codexRPC) run(ctx context.Context, cancel context.CancelFunc, r *rpcRun, p *process, job windows.Handle, jobName string,
	stdinW, captureR *os.File, in CodexLaunch, input []byte, profile, cwd string, cb CodexCallbacks) {
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
			left := int64(rpcCaptureLimit - raw.Len())
			if left >= 0 {
				tail, drainErr := io.ReadAll(io.LimitReader(reader, left+1))
				if int64(len(tail)) <= left && drainErr == nil {
					raw.Write(tail)
					result.StreamsDrained = true
				} else if left > 0 {
					raw.Write(tail[:left])
				}
			}
		}
		stdinW.Close()
		captureR.Close()
		p.close()
		closeJob(job)
		result.Stdout = bytes.Clone(raw.Bytes())
		result.CleanupComplete = result.Stopped && result.StreamsDrained
		if !result.CleanupComplete {
			result.State = "UNKNOWN"
		}
		if failure != nil {
			result.Failure = failure.Error()
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
	reader = bufio.NewReaderSize(captureR, rpcFrameLimit+1)
	read := func() (map[string]any, error) {
		line, err := reader.ReadSlice('\n')
		if raw.Len()+len(line) > rpcCaptureLimit {
			return nil, errors.New("CODEX_RPC_CAPTURE_LIMIT")
		}
		raw.Write(line)
		if err != nil {
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
	stopReadOnce.Do(func() { close(stopRead) })
	<-watchDone
	prepCancel()
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
	if gate := d.readiness(); gate.State != "PREPARATION_READY" {
		failure = errors.New(gate.Reason)
		return
	}
	if failure = cb.BeforeModelTurn(evidence); failure != nil {
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
	if failure = write(rpcTurnStart(threadID, input)); failure != nil {
		return
	}
	result.ThreadID = threadID
	completed := false
	for !completed {
		frame, failure = read()
		if failure != nil {
			return
		}
		if id, ok := rpcResponseID(frame); ok {
			if id != 3 || frame["error"] != nil {
				failure = errors.New("CODEX_RPC_TURN_RESPONSE_INVALID")
				return
			}
			continue
		}
		method, ok := frame["method"].(string)
		if !ok {
			failure = errors.New("CODEX_RPC_SERVER_REQUEST")
			return
		}
		switch method {
		case "turn/started", "item/started", "thread/tokenUsage/updated":
		case "item/completed":
			params, _ := frame["params"].(map[string]any)
			item, _ := params["item"].(map[string]any)
			if item["type"] == "agentMessage" {
				text, _ := item["text"].(string)
				result.Assistant = text
				if failure = cb.Event(CodexEvent{Kind: "ASSISTANT", Text: text}); failure != nil {
					return
				}
			} else if item["type"] == "commandExecution" && item["status"] != "completed" {
				failure = errors.New("CODEX_RPC_TOOL_FAILED")
				return
			}
		case "turn/completed":
			params, _ := frame["params"].(map[string]any)
			turn, _ := params["turn"].(map[string]any)
			status, _ := turn["status"].(string)
			if status != "completed" || turn["threadId"] != threadID {
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
