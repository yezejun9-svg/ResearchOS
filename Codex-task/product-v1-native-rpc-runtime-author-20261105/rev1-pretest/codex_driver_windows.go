//go:build windows

package runtime

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"golang.org/x/sys/windows"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
	"unicode/utf8"
)

// CodexCLIOptions is only supplied by the Host composition root, never decoded
// from a task/request. PermissionOverrides are Host-fixed TOML overrides.
type CodexCLIOptions struct {
	Executable          string
	Descriptor          CodexDescriptor
	PermissionOverrides []string
}
type codexCLI struct {
	options     CodexCLIOptions
	fixtureArgs []string
	fixtureEnv  []string
	readiness   CodexReadinessProvider
}

func NewCodexCLI(options CodexCLIOptions) (CodexDriver, error) {
	if !filepath.IsAbs(options.Executable) || strings.ToLower(filepath.Ext(options.Executable)) != ".exe" ||
		!strings.HasPrefix(options.Descriptor.ExecutableHash, "sha256:") || len(options.Descriptor.ExecutableHash) != 71 {
		return nil, errors.New("CODEX_EXECUTABLE_INVALID")
	}
	if len(options.PermissionOverrides) != 0 {
		return nil, errors.New("CODEX_POLICY_OVERRIDE_FORBIDDEN")
	}
	options.Descriptor.NativeTransport = CodexExecTransport
	return &codexCLI{options: options}, nil
}
func (d *codexCLI) Descriptor() CodexDescriptor { return d.options.Descriptor }

// Only trusted Go composition can inject a fixture provider. NewCodexCLI and
// the actual Host composition always remain UNVERIFIED in Slice A.
func NewCodexCLIForTrustedGoTest(options CodexCLIOptions, provider CodexReadinessProvider) (CodexDriver, error) {
	if provider == nil {
		return nil, errors.New("CODEX_TEST_PROVIDER_REQUIRED")
	}
	driver, err := NewCodexCLI(options)
	if err != nil {
		return nil, err
	}
	driver.(*codexCLI).readiness = provider
	return driver, nil
}
func (d *codexCLI) ReadinessSnapshot() CodexReadiness {
	if d.readiness != nil {
		return d.readiness.Snapshot()
	}
	return CodexReadiness{State: "UNVERIFIED", Reason: "PERMISSION_PROFILE_UNVERIFIED", PolicyIdentity: CodexRequestedPolicyIdentity(d.options.Descriptor.ExecutableHash)}
}
func (d *codexCLI) evaluatedReadiness() CodexReadiness {
	return EvaluateCodexReadiness(d.Descriptor(), d.ReadinessSnapshot(), CodexRequestedPolicyIdentity(d.options.Descriptor.ExecutableHash))
}
func (d *codexCLI) arguments(cwd, source string) []string {
	return codexRequestedArguments(cwd, source)
}

const codexExecutionInputLimit = 1 << 20

// codexExecutionInput adds execution-only Host metadata. The canonical user
// request and launch authority remain unchanged; JSON keeps user content from
// becoming another source-context field. This grants no additional access.
func codexExecutionInput(workspace, cwd, prompt string) ([]byte, error) {
	if !utf8.ValidString(workspace) || !utf8.ValidString(cwd) {
		return nil, errors.New("CODEX_SOURCE_CONTEXT_INVALID")
	}
	context := struct {
		SourceWorkspace         string `json:"source_workspace"`
		ProcessWorkingDirectory string `json:"process_working_directory"`
		Access                  string `json:"access"`
		Instructions            string `json:"instructions"`
	}{
		SourceWorkspace:         workspace,
		ProcessWorkingDirectory: cwd,
		Access:                  "READ_ONLY",
		Instructions: "Use source_workspace as the source project root and resolve project-relative paths there. " +
			"process_working_directory is a separate Host-owned working directory, not the source project. " +
			"The existing read-only permission profile and native platform policy still govern access; this context grants no additional permissions.",
	}
	input := struct {
		Schema        string `json:"schema"`
		SourceContext any    `json:"source_context"`
		UserRequest   string `json:"user_request"`
	}{Schema: "researchos.codex-source-context.v1", SourceContext: context, UserRequest: prompt}
	raw, err := json.Marshal(input)
	if err != nil {
		return nil, err
	}
	if len(raw) > codexExecutionInputLimit {
		return nil, errors.New("CODEX_EXECUTION_INPUT_LIMIT")
	}
	return raw, nil
}

type codexRun struct {
	mu              sync.Mutex
	cancel          context.CancelFunc
	done            chan struct{}
	result          CodexResult
	requestedCancel bool
	err             error
}

func (r *codexRun) Cancel() { r.mu.Lock(); r.requestedCancel = true; r.mu.Unlock(); r.cancel() }
func (r *codexRun) Wait(ctx context.Context) (CodexResult, error) {
	select {
	case <-r.done:
		r.mu.Lock()
		defer r.mu.Unlock()
		v := r.result
		v.Stdout = bytes.Clone(v.Stdout)
		v.Stderr = bytes.Clone(v.Stderr)
		return v, r.err
	case <-ctx.Done():
		return CodexResult{}, ctx.Err()
	}
}
func (d *codexCLI) Start(ctx context.Context, in CodexLaunch, cb CodexCallbacks) (CodexHandle, error) {
	if gate := d.evaluatedReadiness(); gate.State != "READY" {
		return nil, errors.New(gate.Reason)
	}
	if !d.options.Descriptor.ConfigurationControlled {
		return nil, errors.New("CONFIG_INHERITANCE_UNVERIFIED")
	}
	if !filepath.IsAbs(in.Workspace) || !filepath.IsAbs(in.Directory) || in.TaskID == "" || in.RunID == "" ||
		!utf8.ValidString(in.Prompt) || strings.TrimSpace(in.Prompt) == "" || len(in.Prompt) > 65536 || strings.ContainsRune(in.Prompt, 0) ||
		in.Timeout <= 0 || in.Timeout > 15*time.Minute || cb.BeforeResume == nil || cb.Event == nil {
		return nil, errors.New("CODEX_LAUNCH_INVALID")
	}
	epoch, err := strconv.ParseInt(in.Epoch, 10, 64)
	if err != nil || epoch <= 0 || strconv.FormatInt(epoch, 10) != in.Epoch {
		return nil, errors.New("CODEX_EPOCH_INVALID")
	}
	if err = ctx.Err(); err != nil {
		return nil, err
	}
	cwd := filepath.Join(in.Directory, "cwd")
	executionInput, err := codexExecutionInput(in.Workspace, cwd, in.Prompt)
	if err != nil {
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
	if err = os.Mkdir(in.Directory, 0700); err != nil {
		return nil, err
	}
	if _, err = PrivateDirectory(in.Directory); err != nil {
		return nil, err
	}
	stdinR, stdinW, err := os.Pipe()
	if err != nil {
		return nil, err
	}
	stdoutR, stdoutW, err := os.Pipe()
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		return nil, err
	}
	stderrR, stderrW, err := os.Pipe()
	if err != nil {
		stdinR.Close()
		stdinW.Close()
		stdoutR.Close()
		stdoutW.Close()
		return nil, err
	}
	closeAll := func() {
		for _, f := range []*os.File{stdinR, stdinW, stdoutR, stdoutW, stderrR, stderrW} {
			f.Close()
		}
	}
	jobName := "researchos-codex-" + strings.TrimPrefix(Hash([]byte(in.RunID+"/"+in.Epoch)), "sha256:")
	job, err := newJob(jobName)
	if err != nil {
		closeAll()
		return nil, err
	}
	if err = os.Mkdir(cwd, 0700); err != nil {
		closeJob(job)
		closeAll()
		return nil, err
	}
	if err = os.WriteFile(filepath.Join(cwd, ".researchos-codex-root"), []byte("researchos-codex-owned-root-v1\n"), 0600); err != nil {
		closeJob(job)
		closeAll()
		return nil, err
	}
	args := d.arguments(cwd, in.Workspace)
	env := Environment("")
	if d.fixtureArgs != nil {
		args = append([]string(nil), d.fixtureArgs...)
		env = append(env, d.fixtureEnv...)
	}
	proc, err := launchWithCallback(job, Command{Executable: d.options.Executable, Args: args, Directory: cwd}, env, stdinR, stdoutW, stderrW,
		func(p *process) error {
			if gate := d.evaluatedReadiness(); gate.State != "READY" {
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
	stdoutW.Close()
	stderrW.Close()
	child, cancel := context.WithTimeout(ctx, in.Timeout)
	r := &codexRun{cancel: cancel, done: make(chan struct{})}
	go d.run(child, cancel, r, proc, job, jobName, stdinW, stdoutR, stderrR, in, executionInput, cb)
	return r, nil
}

type codexStreamResult struct {
	raw []byte
	err error
}

func (d *codexCLI) run(ctx context.Context, cancel context.CancelFunc, r *codexRun, p *process, job windows.Handle, jobName string, stdinW, stdoutR, stderrR *os.File, in CodexLaunch, executionInput []byte, cb CodexCallbacks) {

	var eventMu sync.Mutex
	eventCount := 0
	emit := func(e CodexEvent) error {
		eventMu.Lock()
		defer eventMu.Unlock()
		eventCount++
		if eventCount > 4096 {
			return errors.New("CODEX_EVENT_LIMIT")
		}
		return cb.Event(e)
	}
	stdoutDone := make(chan codexStreamResult, 1)
	stderrDone := make(chan codexStreamResult, 1)
	go func() {
		var raw bytes.Buffer
		scanner := bufio.NewScanner(stdoutR)
		scanner.Buffer(make([]byte, 4096), 1<<20)
		var protocolErr error
		for scanner.Scan() {
			line := bytes.Clone(scanner.Bytes())
			if raw.Len()+len(line)+1 > 4<<20 {
				protocolErr = errors.New("CODEX_OUTPUT_LIMIT")
				cancel()
				break
			}
			raw.Write(line)
			raw.WriteByte('\n')
			if !utf8.Valid(line) {
				protocolErr = errors.New("CODEX_INVALID_UTF8")
				cancel()
				break
			}
			event, err := codexEvent(line)
			if err != nil {
				protocolErr = err
				cancel()
				break
			}
			if event != nil {
				if err = emit(*event); err != nil {
					protocolErr = err
					cancel()
					break
				}
			}
		}
		protocolErr = errors.Join(protocolErr, scanner.Err())
		if protocolErr != nil {
			cancel()
		}
		stdoutDone <- codexStreamResult{raw: raw.Bytes(), err: protocolErr}
	}()
	go func() {
		var raw bytes.Buffer
		scanner := bufio.NewScanner(stderrR)
		scanner.Buffer(make([]byte, 4096), 1<<20)
		var streamErr error
		for scanner.Scan() {
			line := bytes.Clone(scanner.Bytes())
			if raw.Len()+len(line)+1 > 4<<20 {
				streamErr = errors.New("CODEX_STDERR_LIMIT")
				cancel()
				break
			}
			raw.Write(line)
			raw.WriteByte('\n')
			diagnostic := Redact(line)
			if len(diagnostic) > 4096 {
				diagnostic = diagnostic[:4096]
			}
			lower := strings.ToLower(string(diagnostic))
			if strings.Contains(lower, "access_token") || strings.Contains(lower, "refresh_token") || strings.Contains(lower, "api_key") {
				diagnostic = []byte("[credential-bearing diagnostic omitted]")
			}
			if err := emit(CodexEvent{Kind: "LOG", Text: strings.ToValidUTF8(string(diagnostic), "?")}); err != nil {
				streamErr = err
				cancel()
				break
			}
		}
		streamErr = errors.Join(streamErr, scanner.Err())
		if streamErr != nil {
			cancel()
		}
		stderrDone <- codexStreamResult{raw: raw.Bytes(), err: streamErr}
	}()
	inputDone := make(chan error, 1)
	go func() {
		_, err := stdinW.Write(executionInput)
		closeErr := stdinW.Close()
		inputDone <- errors.Join(err, closeErr)
	}()
	result := CodexResult{Identity: CodexIdentity{PID: p.pid, Created: p.created, Job: jobName}, State: "UNKNOWN", ExitCode: -1}
	var lifecycleErr error
	var stopDeadline time.Time
	killed := false
	ticker := time.NewTicker(20 * time.Millisecond)
	defer ticker.Stop()
	for {
		exited, code, inspectErr := p.exited()
		if exited {
			result.ExitCode = code
		}
		ids, jobErr := jobPIDs(job)
		lifecycleErr = errors.Join(lifecycleErr, inspectErr, jobErr)
		// Kill descendants on parent exit too: a child retaining a pipe must not
		// bypass timeout/cleanup ownership by outliving the parent.
		if !killed && (exited || ctx.Err() != nil || inspectErr != nil || jobErr != nil) {
			lifecycleErr = errors.Join(lifecycleErr, killJob(job))
			killed = true
			stopDeadline = time.Now().Add(5 * time.Second)
		}
		if killed && inspectErr == nil && jobErr == nil && exited && len(ids) == 0 {
			result.Stopped = true
			break
		}
		if killed && time.Now().After(stopDeadline) {
			lifecycleErr = errors.Join(lifecycleErr, errors.New("CODEX_JOB_STOP_UNCONFIRMED"))
			break
		}
		<-ticker.C
	}
	closeJob(job)
	p.close()
	stdinW.Close()
	drainDeadline := time.NewTimer(5 * time.Second)
	var out, errStream codexStreamResult
	haveOut, haveErr := false, false
	for !haveOut || !haveErr {
		select {
		case v := <-stdoutDone:
			out = v
			haveOut = true
		case v := <-stderrDone:
			errStream = v
			haveErr = true
		case <-drainDeadline.C:
			stdoutR.Close()
			stderrR.Close()
			lifecycleErr = errors.Join(lifecycleErr, errors.New("CODEX_STREAM_DRAIN_UNCONFIRMED"))
			if !haveOut {
				out = <-stdoutDone
				haveOut = true
			}
			if !haveErr {
				errStream = <-stderrDone
				haveErr = true
			}
		}
	}
	drainDeadline.Stop()
	stdoutR.Close()
	stderrR.Close()
	result.Stdout = bytes.Clone(out.raw)
	result.Stderr = bytes.Clone(errStream.raw)
	result.StreamsDrained = out.err == nil && errStream.err == nil
	result.CleanupComplete = result.Stopped && result.StreamsDrained && lifecycleErr == nil
	r.mu.Lock()
	requestedCancel := r.requestedCancel
	r.mu.Unlock()
	protocol := ParseStreams(out.raw, errStream.raw, result.ExitCode)
	threadID, threadValid := codexThreadIdentity(out.raw)
	result.ThreadID = threadID
	for _, line := range bytes.Split(out.raw, []byte("\n")) {
		var row map[string]any
		if json.Unmarshal(line, &row) == nil && row["type"] == "item.completed" {
			item, _ := row["item"].(map[string]any)
			if item["type"] == "agent_message" {
				if value, ok := item["text"].(string); ok {
					result.Assistant = value
				}
			}
		}
	}
	switch {
	case !result.CleanupComplete:
		result.State = "UNKNOWN"
		result.Failure = "CODEX_CLEANUP_OR_PROTOCOL_UNCONFIRMED"
	case requestedCancel:
		result.State = "CANCELLED"
	case errors.Is(ctx.Err(), context.DeadlineExceeded):
		result.State = "FAILED"
		result.Failure = "CODEX_TIMEOUT"
	case result.ExitCode != 0:
		result.State = "FAILED"
		result.Failure = "CODEX_EXECUTOR_EXIT"
	case !threadValid:
		result.State = "UNKNOWN"
		result.Failure = "CODEX_THREAD_IDENTITY_INVALID"
	case !protocol.Settled:
		result.State = "UNKNOWN"
		result.Failure = "CODEX_TERMINAL_PROTOCOL_MISSING"
	default:
		result.State = "COMPLETED"
	}
	// Await the one owned stdin writer after the Job is stopped.
	select {
	case <-inputDone:
	case <-time.After(time.Second):
		lifecycleErr = errors.Join(lifecycleErr, errors.New("CODEX_INPUT_CLOSE_UNCONFIRMED"))
		result.State = "UNKNOWN"
		result.CleanupComplete = false
	}
	if err := save(filepath.Join(in.Directory, "codex-receipt.json"), result); err != nil {
		lifecycleErr = errors.Join(lifecycleErr, err)
		result.State = "UNKNOWN"
	}
	cancel()
	r.mu.Lock()
	r.result = result
	r.err = lifecycleErr
	r.mu.Unlock()
	close(r.done)
}
func codexEvent(raw []byte) (*CodexEvent, error) {
	var row map[string]any
	if json.Unmarshal(raw, &row) != nil {
		return nil, errors.New("CODEX_INVALID_JSONL")
	}
	kind, _ := row["type"].(string)
	if kind == "" {
		return nil, errors.New("CODEX_EVENT_TYPE_MISSING")
	}
	if kind == "error" || kind == "turn.failed" {
		return &CodexEvent{Kind: "LOG", Text: "Codex reported an execution error"}, nil
	}
	if kind != "item.started" && kind != "item.updated" && kind != "item.completed" {
		return nil, nil
	}
	item, ok := row["item"].(map[string]any)
	if !ok {
		return nil, errors.New("CODEX_ITEM_MISSING")
	}
	itemKind, _ := item["type"].(string)
	id, _ := item["id"].(string)
	if itemKind == "agent_message" && kind == "item.completed" {
		value, ok := item["text"].(string)
		if !ok || len(value) > 1<<20 {
			return nil, errors.New("CODEX_MESSAGE_INVALID")
		}
		return &CodexEvent{Kind: "ASSISTANT_MESSAGE", Text: value, NativeID: id}, nil
	}
	if itemKind == "command_execution" || itemKind == "mcp_tool_call" || itemKind == "web_search" || itemKind == "file_change" {
		phase := "STARTED"
		if kind == "item.completed" {
			phase = "COMPLETED"
			if status, _ := item["status"].(string); status == "failed" {
				phase = "FAILED"
			}
			if code, ok := item["exit_code"].(float64); ok && code != 0 {
				phase = "FAILED"
			}
		}
		summary, _ := item["command"].(string)
		if len(summary) > 4096 {
			summary = summary[:4096]
		}
		return &CodexEvent{Kind: "TOOL_EVENT", ToolID: id, ToolName: itemKind, ToolPhase: phase, Text: string(Redact([]byte(summary))), NativeID: id}, nil
	}
	return nil, nil
}

// codexThreadIdentity binds this ephemeral native turn to one declared thread.
// It deliberately does not change the older ParseStreams/Mu contract. Replayed
// declarations of the same identity are idempotent; a later writer cannot
// replace the first identity or retroactively bind an earlier message/turn.
func codexThreadIdentity(stdout []byte) (string, bool) {
	thread := ""
	for _, line := range bytes.Split(stdout, []byte("\n")) {
		if len(bytes.TrimSpace(line)) == 0 {
			continue
		}
		var row map[string]any
		if !utf8.Valid(line) || json.Unmarshal(line, &row) != nil {
			return "", false
		}
		kind, _ := row["type"].(string)
		if kind == "thread.started" {
			id, ok := row["thread_id"].(string)
			if !ok || id == "" || strings.TrimSpace(id) != id || utf8.RuneCountInString(id) > 256 {
				return "", false
			}
			for _, r := range id {
				if unicode.IsControl(r) {
					return "", false
				}
			}
			if thread != "" && id != thread {
				return "", false
			}
			thread = id
		} else {
			if (strings.HasPrefix(kind, "item.") || strings.HasPrefix(kind, "turn.")) && thread == "" {
				return "", false
			}
			if value, exists := row["thread_id"]; exists && value != thread {
				return "", false
			}
		}
	}
	return thread, thread != ""
}
