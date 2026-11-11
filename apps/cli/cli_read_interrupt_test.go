package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"
)

const readInterruptCredential = "SYNTHETIC_READ_STATUS_CREDENTIAL"

func readInterruptSnapshot() map[string]any {
	return map[string]any{
		"session_id": "read-session", "project_id": "read-project", "workspace_ref": "read-workspace",
		"native_session_ref": "read-native", "core_build_id": "read-build", "protocol_version": clientProtocol,
		"revision": 1, "title": "Read-only status", "archived_at": nil,
		"created_at": "2026-10-06T12:00:00Z", "updated_at": "2026-10-06T12:00:00Z",
		"model_config_ref": "read-model", "goal_id": "read-goal", "active_run_id": nil,
		"run_status": nil, "goal_status": "ACTIVE", "writer": nil, "event_sequence": 0,
		"earliest_event_sequence": 0, "checkpoint_artifact_ref": nil, "pending_command_ids": []any{},
		"pending_permissions": []any{}, "messages": []any{}, "resume_requires_explicit_user": false,
		"transcript_artifact_ref": nil, "has_earlier_messages": false,
	}
}

func readInterruptHostStatus() map[string]any {
	return map[string]any{
		"host_instance_id": "read-host", "core_build_id": "read-build", "protocol_versions": []any{clientProtocol},
		"host_state": "READY", "client_id": "read-client", "authenticated_principal_ref": "read-principal",
		"config_revision": 0, "model_configurations": []any{}, "credentials": []any{}, "workspaces": []any{},
		"supported_methods": []any{"host.status", "session.get"}, "operating_mode": "LOCAL_USER_HOST",
	}
}

// A public loopback fixture exercises actual HTTP cancellation. It makes no
// claim about native Host qualification, model execution, or formal acceptance.
type readInterruptHost struct {
	server    *httptest.Server
	started   chan struct{}
	cancelled chan struct{}
	once      sync.Once
	mu        sync.Mutex
	requests  []string
}

func newReadInterruptHost(t *testing.T, stage, fault string) *readInterruptHost {
	t.Helper()
	doc, err := cliProtocolDocument()
	if err != nil {
		t.Fatal(err)
	}
	if err = doc.ValidateDef("HostStatusResult", readInterruptHostStatus()); err != nil {
		t.Fatal("fixture HostStatusResult is invalid", err)
	}
	if err = doc.ValidateDef("SessionSnapshot", readInterruptSnapshot()); err != nil {
		t.Fatal("fixture SessionSnapshot is invalid", err)
	}
	h := &readInterruptHost{started: make(chan struct{}), cancelled: make(chan struct{})}
	h.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer "+readInterruptCredential {
			t.Error("read credential transport changed")
			w.WriteHeader(http.StatusForbidden)
			return
		}
		request := r.Method + " " + r.URL.RequestURI()
		var envelope map[string]any
		if r.Method == http.MethodPost && r.URL.Path == v2CommandPath {
			if json.NewDecoder(r.Body).Decode(&envelope) != nil || envelope["client_id"] != "read-client" || envelope["protocol_version"] != clientProtocol {
				t.Error("invalid public read request envelope")
				w.WriteHeader(http.StatusBadRequest)
				return
			}
			method, _ := envelope["method"].(string)
			if method != "host.status" && method != "session.get" {
				t.Error("status sent a write or execution request", method)
				w.WriteHeader(http.StatusForbidden)
				return
			}
			request = method
		}
		h.mu.Lock()
		h.requests = append(h.requests, request)
		h.mu.Unlock()
		block := stage == "typed-header" && request == "session.get" ||
			stage == "host-header" && request == "host.status" ||
			stage == "typed-body" && request == "session.get" ||
			stage == "goal" && strings.Contains(r.URL.Path, "/goals/") ||
			stage == "tasks" && strings.HasSuffix(r.URL.Path, "/tasks") ||
			stage == "run" && strings.Contains(r.URL.Path, "/runs/") ||
			stage == "bundle" && strings.Contains(r.URL.Path, "/context-bundles/")
		if stage == "goal-error-body" && strings.Contains(r.URL.Path, "/goals/") {
			w.WriteHeader(http.StatusUnauthorized)
			w.(http.Flusher).Flush()
			block = true
		}
		if block {
			if stage == "typed-body" {
				w.WriteHeader(http.StatusOK)
				w.Write([]byte("{\"protocol_version\":"))
				w.(http.Flusher).Flush()
			}
			h.once.Do(func() { close(h.started) })
			select {
			case <-r.Context().Done():
				close(h.cancelled)
			case <-time.After(4 * time.Second):
				t.Error("blocked read request did not receive context cancellation")
			}
			return
		}
		if envelope != nil {
			if fault == "401" || fault == "503" {
				status := http.StatusUnauthorized
				if fault == "503" {
					status = http.StatusServiceUnavailable
				}
				w.WriteHeader(status)
				w.Write([]byte(readInterruptCredential))
				return
			}
			if fault == "malformed" {
				w.Write([]byte("not-json"))
				return
			}
			result := readInterruptHostStatus()
			if request == "session.get" {
				result = readInterruptSnapshot()
			}
			reply := map[string]any{"protocol_version": clientProtocol, "command_id": envelope["command_id"],
				"method": envelope["method"], "status": "COMPLETED", "session_id": "read-session", "result": result,
				"revision": 1, "error_code": nil, "error": nil}
			if err := doc.ValidateDef("CommandResponse", reply); err != nil {
				t.Error("fixture CommandResponse is invalid", err)
				w.WriteHeader(http.StatusInternalServerError)
				return
			}
			if fault == "identity" {
				reply["command_id"] = "foreign-command"
			}
			json.NewEncoder(w).Encode(reply)
			return
		}
		if r.Method != http.MethodGet {
			t.Error("unexpected non-read request", request)
			w.WriteHeader(http.StatusForbidden)
			return
		}
		switch {
		case strings.Contains(r.URL.Path, "/goals/"):
			json.NewEncoder(w).Encode(map[string]any{"id": "read-goal", "project_id": "read-project", "task_ids": []any{"read-task"}, "status": "ACTIVE", "intent": "Read continuation"})
		case strings.HasSuffix(r.URL.Path, "/tasks"):
			var run, bundle any
			if stage == "run" || stage == "bundle" {
				run = "read-run"
			}
			if stage == "bundle" {
				bundle = "read-bundle"
			}
			json.NewEncoder(w).Encode(map[string]any{"items": []any{map[string]any{"id": "read-task", "project_id": "read-project", "goal_id": "read-goal", "title": "Read task", "status": "READY", "active_run_id": run, "context_bundle_id": bundle}}, "next_cursor": nil})
		case strings.Contains(r.URL.Path, "/runs/"):
			json.NewEncoder(w).Encode(map[string]any{"id": "read-run", "project_id": "read-project", "task_id": "read-task", "status": "SETTLED"})
		default:
			t.Error("unexpected continuation request", request)
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	t.Cleanup(h.server.Close)
	return h
}

func (h *readInterruptHost) context() *v2Context {
	return &v2Context{baseURL: h.server.URL, clientID: "read-client", commandID: "read-command",
		credential: readInterruptCredential, projectID: "read-project", sessionID: "read-session", revision: 1, epoch: 7}
}

func waitReadInterruptFact(t *testing.T, fact <-chan struct{}, label string) {
	t.Helper()
	select {
	case <-fact:
	case <-time.After(3 * time.Second):
		t.Fatal("missing actual read fact:", label)
	}
}

func assertReadInterruptOnly(t *testing.T, out map[string]any, code int, c *v2Context) {
	t.Helper()
	if code != exitInterrupted || out["status"] != "INTERRUPTED_READ_ONLY" || out["reason"] != "READ_INTERRUPTED" {
		t.Fatal("read interrupt outcome", code, out)
	}
	if out["execution"] != nil || out["admission_command_id"] != "" || c.epoch != 7 || c.revision != 1 {
		t.Fatal("read interrupt claimed execution or changed writer identity", out, c.epoch, c.revision)
	}
	for _, request := range c.requestLog {
		if request == "session.control" || request == "session.send" || request == "goal.start" {
			t.Fatal("read interrupt sent execution/control request", c.requestLog)
		}
	}
	raw, _ := json.Marshal(out)
	if strings.Contains(string(raw), readInterruptCredential) {
		t.Fatal("credential entered read report")
	}
}

func TestCLIReadStatusInterruptCancelsAllRequestPhases(t *testing.T) {
	for _, stage := range []string{"typed-header", "host-header", "typed-body", "goal", "tasks", "run", "bundle"} {
		t.Run(stage, func(t *testing.T) {
			h := newReadInterruptHost(t, stage, "")
			c := h.context()
			signals := make(chan os.Signal, 2)
			done := make(chan struct{})
			var out map[string]any
			var code int
			go func() {
				out, code = runCLIVerb("status", nil, c, cliConfig{}, cliFollowOptions{timeout: 5 * time.Second, poll: time.Millisecond, cancelTimeout: time.Second, interrupts: signals})
				close(done)
			}()
			waitReadInterruptFact(t, h.started, "public HTTP request reached "+stage)
			signals <- os.Interrupt
			waitReadInterruptFact(t, h.cancelled, "server received context cancellation")
			waitReadInterruptFact(t, done, "read flow returned after cancellation")
			assertReadInterruptOnly(t, out, code, c)
			t.Logf("actual HTTP cancellation stage=%s requests=%v", stage, c.requestLog)
		})
	}
}

func readProcessFlags(cmd *exec.Cmd, flags uint64) {
	cmd.SysProcAttr = &syscall.SysProcAttr{}
	fields := reflect.ValueOf(cmd.SysProcAttr).Elem()
	if field := fields.FieldByName("CreationFlags"); field.IsValid() {
		field.SetUint(flags)
	}
	if field := fields.FieldByName("HideWindow"); field.IsValid() {
		field.SetBool(true)
	}
}

func readNativeHelper(t *testing.T) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, os.Getenv("RESEARCHOS_READ_TEST_BINARY"), "status", "--project", "read-project", "--session", "read-session", "--expected-revision", "1", "--writer-epoch", "7")
	// This helper already owns a private console. The CLI inherits it and
	// creates a separate group; CREATE_NEW_CONSOLE is deliberately absent.
	readProcessFlags(cmd, 0x200)
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	if err := cmd.Start(); err != nil {
		t.Fatal("actual CLI child start", err)
	}
	waited := false
	defer func() {
		if !waited {
			cmd.Process.Kill()
			cmd.Wait()
		}
	}()
	if os.Getenv("RESEARCHOS_READ_TEST_SIGNAL") == "1" {
		line, err := bufio.NewReader(os.Stdin).ReadString('\n')
		if err != nil || line != "interrupt\n" {
			t.Fatal("missing HTTP barrier instruction", err)
		}
		ps := fmt.Sprintf("Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class ReadSignal { [DllImport(\"kernel32.dll\", SetLastError=true)] public static extern bool FreeConsole(); [DllImport(\"kernel32.dll\", SetLastError=true)] public static extern bool AttachConsole(uint pid); [DllImport(\"kernel32.dll\", SetLastError=true)] public static extern bool GenerateConsoleCtrlEvent(uint signal,uint group); }'; [ReadSignal]::FreeConsole() | Out-Null; if (-not [ReadSignal]::AttachConsole(%d)) { Write-Output ('ATTACH_ERROR:' + [Runtime.InteropServices.Marshal]::GetLastWin32Error()); exit 1 }; if (-not [ReadSignal]::GenerateConsoleCtrlEvent(1,%d)) { Write-Output ('SIGNAL_ERROR:' + [Runtime.InteropServices.Marshal]::GetLastWin32Error()); exit 2 }; Write-Output 'ACTUAL_CTRL_BREAK_SENT'", cmd.Process.Pid, cmd.Process.Pid)
		sender := exec.CommandContext(ctx, "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps)
		readProcessFlags(sender, 0x08000000)
		actual, err := sender.CombinedOutput()
		if err != nil || !strings.Contains(string(actual), "ACTUAL_CTRL_BREAK_SENT") {
			t.Fatal("actual console signal failed", err, string(actual))
		}
		t.Logf("actual CTRL_BREAK sender exit0 child_pid=%d output=%s", cmd.Process.Pid, strings.TrimSpace(string(actual)))
	}
	err := cmd.Wait()
	waited = true
	code := 0
	if err != nil {
		var ok bool
		var exit *exec.ExitError
		exit, ok = err.(*exec.ExitError)
		if !ok {
			t.Fatal("CLI child wait", err)
		}
		code = exit.ExitCode()
	}
	var report map[string]any
	if json.Unmarshal(bytes.TrimSpace(stdout.Bytes()), &report) != nil {
		t.Fatal("actual CLI stdout is not one JSON report", stdout.String(), stderr.String())
	}
	if os.Getenv("RESEARCHOS_READ_TEST_SIGNAL") == "1" {
		if code != exitInterrupted || report["status"] != "INTERRUPTED_READ_ONLY" || report["reason"] != "READ_INTERRUPTED" {
			t.Fatal("actual CLI interrupt result", code, report, stderr.String())
		}
	} else if code != exitCompleted || report["status"] != "COMPLETED" {
		t.Fatal("actual CLI typed successful control failed", code, report, stderr.String())
	}
	if report["execution"] != nil || report["admission_command_id"] != "" || strings.Contains(stdout.String()+stderr.String(), readInterruptCredential) {
		t.Fatal("actual CLI leaked credential or claimed execution", report)
	}
	witness, _ := json.Marshal(map[string]any{"child_pid": cmd.Process.Pid, "actual_exit": code, "report": report})
	fmt.Println("NATIVE_READ_WITNESS " + string(witness))
}

func TestCLIReadStatusActualWindowsConsoleSignal(t *testing.T) {
	if os.Getenv("RESEARCHOS_READ_TEST_HELPER") == "1" {
		readNativeHelper(t)
		return
	}
	if runtime.GOOS != "windows" {
		t.Skip("actual Windows console signal requires Windows")
	}
	goTool := os.Getenv("RESEARCHOS_GO")
	if goTool == "" {
		t.Fatal("RESEARCHOS_GO must bind the actual Go toolchain")
	}
	repo, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	binary := filepath.Join(t.TempDir(), "researchos-cli.exe")
	build := exec.Command(goTool, "build", "-o", binary, "./apps/cli")
	build.Dir = repo
	if raw, err := build.CombinedOutput(); err != nil {
		t.Fatal("actual CLI build", err, string(raw))
	}
	compiled, err := os.ReadFile(binary)
	if err != nil {
		t.Fatal(err)
	}
	t.Logf("actual compiled CLI sha256=%x bytes=%d", sha256.Sum256(compiled), len(compiled))
	for _, stage := range []string{"success", "typed-header", "host-header", "goal"} {
		t.Run(stage, func(t *testing.T) {
			blockedStage := stage
			if stage == "success" {
				blockedStage = ""
			}
			h := newReadInterruptHost(t, blockedStage, "")
			dir := t.TempDir()
			discoveryFile, configFile := filepath.Join(dir, "discovery.json"), filepath.Join(dir, "config.json")
			discoveryRaw, _ := json.Marshal(discovery{URL: h.server.URL, PID: os.Getpid(), DataDir: dir, StartedAt: time.Now().UTC().Format(time.RFC3339Nano)})
			if err := os.WriteFile(discoveryFile, discoveryRaw, 0600); err != nil {
				t.Fatal(err)
			}
			cfg := cliConfig{ProjectID: "read-project", SessionID: "read-session", Revision: 1, WriterEpoch: 7, UpdatedBy: "read-client"}
			cfgRaw, _ := json.MarshalIndent(cfg, "", " ")
			if err := os.WriteFile(configFile, append(cfgRaw, '\n'), 0600); err != nil {
				t.Fatal(err)
			}
			configBefore, _ := os.ReadFile(configFile)
			ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestCLIReadStatusActualWindowsConsoleSignal$", "-test.v")
			// A private, hidden console avoids assumptions about the invoking
			// PTY. The CLI launched inside uses only CREATE_NEW_PROCESS_GROUP.
			readProcessFlags(cmd, 0x10)
			for _, env := range os.Environ() {
				if !strings.HasPrefix(env, "RESEARCHOS_CLI_") && !strings.HasPrefix(env, "RESEARCHOS_READ_TEST_") {
					cmd.Env = append(cmd.Env, env)
				}
			}
			signal := "1"
			if stage == "success" {
				signal = "0"
			}
			cmd.Env = append(cmd.Env, "RESEARCHOS_READ_TEST_HELPER=1", "RESEARCHOS_READ_TEST_SIGNAL="+signal,
				"RESEARCHOS_READ_TEST_BINARY="+binary, "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile,
				"RESEARCHOS_CLI_CREDENTIAL="+readInterruptCredential, "RESEARCHOS_CLI_CLIENT_ID=read-client")
			stdin, err := cmd.StdinPipe()
			if err != nil {
				t.Fatal(err)
			}
			var stdout, stderr bytes.Buffer
			cmd.Stdout, cmd.Stderr = &stdout, &stderr
			if err = cmd.Start(); err != nil {
				t.Fatal("hidden console helper start", err)
			}
			waited := false
			defer func() {
				if !waited {
					cmd.Process.Kill()
					cmd.Wait()
				}
			}()
			if stage != "success" {
				waitReadInterruptFact(t, h.started, "compiled CLI HTTP barrier "+stage)
				if _, err = stdin.Write([]byte("interrupt\n")); err != nil {
					t.Fatal("signal barrier pipe", err)
				}
				waitReadInterruptFact(t, h.cancelled, "compiled CLI request context cancellation")
			}
			stdin.Close()
			err = cmd.Wait()
			waited = true
			if err != nil || !strings.Contains(stdout.String(), "NATIVE_READ_WITNESS ") {
				t.Fatal("hidden console helper witness missing", err, stdout.String(), stderr.String())
			}
			t.Logf("actual hidden-console stage=%s witness=%s", stage, strings.TrimSpace(stdout.String()))
			configAfter, _ := os.ReadFile(configFile)
			if !bytes.Equal(configBefore, configAfter) {
				t.Fatal("read-only compiled CLI changed existing recovery config")
			}
			h.mu.Lock()
			requests := append([]string(nil), h.requests...)
			h.mu.Unlock()
			for _, request := range requests {
				if request == "session.control" || request == "session.send" || request == "goal.start" {
					t.Fatal("actual CLI read sent a write", requests)
				}
			}
			t.Logf("actual hidden-console stage=%s requests=%v config_bytes_unchanged=true", stage, requests)
		})
	}
}

func TestCLIReadStatusNoSignalAndFaultControls(t *testing.T) {
	for _, mode := range []string{"nil", "closed", "unsupported", "identity", "malformed", "401", "503"} {
		t.Run(mode, func(t *testing.T) {
			h := newReadInterruptHost(t, "", mode)
			c := h.context()
			var signals chan os.Signal
			if mode == "closed" || mode == "unsupported" {
				signals = make(chan os.Signal, 1)
				if mode == "closed" {
					close(signals)
				} else {
					signals <- syscall.Signal(42)
				}
			}
			out, code := runCLIVerb("status", nil, c, cliConfig{}, cliFollowOptions{timeout: 3 * time.Second, poll: time.Millisecond, cancelTimeout: time.Second, interrupts: signals})
			want := exitCompleted
			switch mode {
			case "identity", "malformed", "503":
				want = exitFailed
			case "401":
				want = exitNotImplemented
			}
			if code != want || out["status"] == "INTERRUPTED_READ_ONLY" || out["reason"] == "READ_INTERRUPTED" {
				t.Fatal("fault or absent signal was mislabeled", mode, code, out)
			}
			raw, _ := json.Marshal(out)
			if strings.Contains(string(raw), readInterruptCredential) || out["execution"] != nil || out["admission_command_id"] != "" {
				t.Fatal("read fault leaked credential or claimed execution", out)
			}
		})
	}
}

func TestCLIReadInterruptObserverJoinsAndIgnoresLateSignals(t *testing.T) {
	for i := 0; i < 24; i++ {
		ctx, cancel := context.WithCancel(context.Background())
		signals := make(chan os.Signal, 2)
		guard := observeCLIReadInterrupt(signals, cancel)
		signals <- syscall.SIGTERM
		signals <- os.Interrupt
		waitReadInterruptFact(t, ctx.Done(), "registered signal cancelled request context")
		if !guard.finish() || !guard.finish() {
			t.Fatal("accepted interrupt fact was lost")
		}
		select {
		case <-guard.done:
		default:
			t.Fatal("interrupt observer still running after finish")
		}
		cancel()
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	signals := make(chan os.Signal, 1)
	guard := observeCLIReadInterrupt(signals, cancel)
	if guard.finish() {
		t.Fatal("unsignaled read was interrupted")
	}
	signals <- os.Interrupt
	if guard.finish() || guard.observed() || ctx.Err() != nil {
		t.Fatal("late signal changed already finalized outcome")
	}
}

func TestCLIReadStatusProtocolFaultRetainsOutcome(t *testing.T) {
	h := newReadInterruptHost(t, "", "identity")
	c := h.context()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	signals := make(chan os.Signal, 1)
	guard := observeCLIReadInterrupt(signals, cancel)
	f := &cliFlow{c: c, budget: ctx, base: c.commandID, readInterrupt: guard}
	_, reason, code := f.call("host.status", map[string]any{}, true)
	if code != exitFailed || reason != "REPLY_IDENTITY_MISMATCH" {
		t.Fatal("strict protocol fault changed", reason, code)
	}
	if guard.finish() {
		t.Fatal("protocol failure invented an interrupt")
	}
	signals <- os.Interrupt
	if guard.finish() || guard.observed() {
		t.Fatal("late signal masked terminal protocol failure")
	}
}

func TestCLIReadStatusDeadlineWithoutSignalIsNotInterrupt(t *testing.T) {
	for _, stage := range []string{"typed-header", "typed-body", "goal"} {
		t.Run(stage, func(t *testing.T) {
			h := newReadInterruptHost(t, stage, "")
			c := h.context()
			done := make(chan struct{})
			var out map[string]any
			var code int
			go func() {
				out, code = runCLIVerb("status", nil, c, cliConfig{}, cliFollowOptions{timeout: time.Second, poll: time.Millisecond, cancelTimeout: time.Second})
				close(done)
			}()
			waitReadInterruptFact(t, h.started, "deadline control reached blocked HTTP request")
			waitReadInterruptFact(t, h.cancelled, "deadline cancelled actual request without a signal")
			waitReadInterruptFact(t, done, "deadline read returned")
			if code != exitFailed || out["status"] != "REJECTED" || out["reason"] == "READ_INTERRUPTED" || out["execution"] != nil || out["admission_command_id"] != "" {
				t.Fatal("deadline invented interrupt or execution", code, out)
			}
		})
	}
}

func TestCLIReadStatusAcceptedReplyThenSignalBeforeFinalization(t *testing.T) {
	for _, fault := range []string{"", "identity", "malformed", "401", "503"} {
		t.Run("reply-"+fault, func(t *testing.T) {
			h := newReadInterruptHost(t, "", fault)
			c := h.context()
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			signals := make(chan os.Signal, 1)
			guard := observeCLIReadInterrupt(signals, cancel)
			defer guard.finish()
			f := &cliFlow{c: c, budget: ctx, base: c.commandID, readInterrupt: guard}
			_, reason, code := f.call("host.status", map[string]any{}, true)
			originalCode, originalReason := code, reason
			// f.call has returned and its original result has been accepted.
			// The context barrier proves observation before finalization.
			signals <- os.Interrupt
			waitReadInterruptFact(t, ctx.Done(), "signal observed after accepted reply and before finish")
			code, reason = f.finishReadResult(code, reason)
			if fault == "" {
				if originalCode != exitCompleted || code != exitInterrupted || reason != "READ_INTERRUPTED" {
					t.Fatal("valid read did not retain pre-finalization interrupt", originalCode, code, reason)
				}
			} else if originalCode == exitCompleted || code != originalCode || reason != originalReason {
				t.Fatal("accepted failure masked by later signal", originalCode, originalReason, code, reason)
			}
			if len(c.requestLog) != 1 || c.requestLog[0] != "host.status" || !guard.observed() {
				t.Fatal("ordering control replayed a request or lost signal", c.requestLog)
			}
		})
	}
}

type readInterruptRoundTrip func(*http.Request) (*http.Response, error)

func (r readInterruptRoundTrip) RoundTrip(req *http.Request) (*http.Response, error) {
	return r(req)
}

type readInterruptCausalBody struct {
	reader   *bytes.Reader
	terminal error
	trigger  func()
	once     sync.Once
}

func (b *readInterruptCausalBody) Read(p []byte) (int, error) {
	n, err := b.reader.Read(p)
	if b.reader.Len() == 0 {
		b.once.Do(b.trigger)
		if b.terminal != nil {
			err = b.terminal
		}
	}
	return n, err
}

func (b *readInterruptCausalBody) Close() error { return nil }

type readInterruptObservedBody struct {
	io.ReadCloser
	started chan struct{}
	once    sync.Once
}

func (b *readInterruptObservedBody) Read(p []byte) (int, error) {
	b.once.Do(func() { close(b.started) })
	return b.ReadCloser.Read(p)
}

func TestCLIReadStatusActualIOCauseRetainsNonCancellationFailures(t *testing.T) {
	for _, mode := range []string{"oversize", "unexpected-eof", "connection-error", "cancelled-do", "cancelled-body"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			signals := make(chan os.Signal, 1)
			guard := observeCLIReadInterrupt(signals, cancel)
			defer guard.finish()
			trigger := func() {
				signals <- os.Interrupt
				waitReadInterruptFact(t, ctx.Done(), "actual I/O boundary observed signal")
			}
			original := http.DefaultTransport
			defer func() { http.DefaultTransport = original }()
			http.DefaultTransport = readInterruptRoundTrip(func(req *http.Request) (*http.Response, error) {
				if mode == "connection-error" || mode == "cancelled-do" {
					trigger()
					if mode == "cancelled-do" {
						return nil, fmt.Errorf("request I/O: %w", context.Canceled)
					}
					return nil, errors.New("SYNTHETIC_CONNECTION_REFUSAL")
				}
				body := []byte("incomplete")
				terminal := error(io.ErrUnexpectedEOF)
				if mode == "oversize" {
					body, terminal = bytes.Repeat([]byte("x"), (1<<20)+1), nil
				} else if mode == "cancelled-body" {
					terminal = fmt.Errorf("body I/O: %w", context.Canceled)
				}
				return &http.Response{StatusCode: http.StatusOK, Header: make(http.Header), Request: req,
					Body: &readInterruptCausalBody{reader: bytes.NewReader(body), terminal: terminal, trigger: trigger}}, nil
			})
			c := &v2Context{baseURL: "http://causal-boundary.invalid", clientID: "read-client", commandID: "read-causal-command", credential: readInterruptCredential}
			f := &cliFlow{c: c, budget: ctx, base: c.commandID, readInterrupt: guard}
			_, reason, code := f.call("host.status", map[string]any{}, true)
			code, reason = f.finishReadResult(code, reason)
			if strings.HasPrefix(mode, "cancelled-") {
				if code != exitInterrupted || reason != "READ_INTERRUPTED" {
					t.Fatal("actual wrapped cancellation cause was lost", mode, code, reason)
				}
			} else if code != exitFailed || reason == "READ_INTERRUPTED" {
				t.Fatal("non-cancellation I/O failure masked by signal", mode, code, reason)
			}
			if !guard.observed() || ctx.Err() != context.Canceled || len(c.requestLog) != 1 {
				t.Fatal("counterexample did not observe real synchronization or repeated I/O")
			}
			t.Logf("I/O boundary mode=%s actual_signal_observed=true result=%d reason=%s", mode, code, reason)
		})
	}
}

func TestCLIReadStatusHTTPContinuationFailurePrecedesBodyCancellation(t *testing.T) {
	h := newReadInterruptHost(t, "goal-error-body", "")
	c := h.context()
	clientRead := make(chan struct{})
	original := http.DefaultTransport
	defer func() { http.DefaultTransport = original }()
	http.DefaultTransport = readInterruptRoundTrip(func(req *http.Request) (*http.Response, error) {
		resp, err := original.RoundTrip(req)
		if err == nil && strings.Contains(req.URL.Path, "/goals/") && resp.StatusCode == http.StatusUnauthorized {
			resp.Body = &readInterruptObservedBody{ReadCloser: resp.Body, started: clientRead}
		}
		return resp, err
	})
	signals := make(chan os.Signal, 1)
	done := make(chan struct{})
	var out map[string]any
	var code int
	go func() {
		out, code = runCLIVerb("status", nil, c, cliConfig{}, cliFollowOptions{timeout: 5 * time.Second, interrupts: signals})
		close(done)
	}()
	waitReadInterruptFact(t, h.started, "continuation non200 headers flushed")
	waitReadInterruptFact(t, clientRead, "actual client accepted non200 headers before body read")
	signals <- os.Interrupt
	waitReadInterruptFact(t, h.cancelled, "non200 response body actually cancelled")
	waitReadInterruptFact(t, done, "read finished with preserved HTTP terminal outcome")
	if code != exitFailed || out["status"] != "REJECTED" || out["reason"] != "CONTINUATION_READ_FAILED" || out["execution"] != nil || out["admission_command_id"] != "" {
		t.Fatal("known non200 continuation headers masked by body cancellation", code, out)
	}
}
