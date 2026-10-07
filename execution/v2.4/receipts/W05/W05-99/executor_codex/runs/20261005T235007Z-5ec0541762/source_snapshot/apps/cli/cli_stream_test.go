package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"
)

// This is an explicit HTTP protocol fixture, with no model/provider/runtime
// execution. Its independent state machine delays admission, run binding and
// cancellation confirmation so transport success cannot certify itself.
type cliStreamFixture struct {
	t           *testing.T
	server      *httptest.Server
	mu          sync.Mutex
	mode        string
	admitted    bool
	cancelled   bool
	taskReads   int
	sendCalls   int
	pages       int
	cancelCalls int
	events      []any
	phases      map[string]bool
	sendBodies  []string
	methods     []string
	signals     chan os.Signal
	sent        chan string
}

func newCLIStreamFixture(t *testing.T, mode string) *cliStreamFixture {
	f := &cliStreamFixture{t: t, mode: mode, events: []any{}, phases: map[string]bool{}, signals: make(chan os.Signal, 2), sent: make(chan string, 16)}
	f.server = httptest.NewServer(http.HandlerFunc(f.serve))
	t.Cleanup(f.server.Close)
	return f
}

func (f *cliStreamFixture) snapshot() map[string]any {
	var goal, run any
	if f.admitted {
		goal = "g1"
		if f.mode != "delayed" && f.mode != "cancel-pending" && f.mode != "cancel-no-run" && f.mode != "blocked" || f.taskReads >= 3 && f.mode != "cancel-no-run" {
			run = "r1"
		}
	}
	return map[string]any{"protocol_version": clientProtocol, "session_id": "s1", "project_id": "p1", "goal_id": goal,
		"active_run_id": run, "revision": 5 + len(f.events), "event_sequence": len(f.events), "earliest_event_sequence": 0,
		"core_build_id": "fixture-build", "writer": map[string]any{"client_id": "c1", "epoch": 1, "expires_at": time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)}}
}

func (f *cliStreamFixture) phase() string {
	switch f.mode {
	case "cancel", "cancel-pending", "cancel-unknown":
		if f.mode == "cancel-pending" && f.taskReads < 3 {
			return "PENDING"
		}
		if f.cancelled && f.mode != "cancel-unknown" {
			return "CANCELLED"
		}
		return "RUNNING"
	case "cancel-no-run", "blocked":
		return "PENDING"
	case "unknown":
		return "RECONCILING"
	case "failed":
		return "FAILED"
	case "delayed":
		if f.taskReads < 3 {
			return "PENDING"
		}
	}
	return "SETTLED"
}

func (f *cliStreamFixture) run() map[string]any {
	status := f.phase()
	settled := status == "SETTLED" || status == "FAILED" || status == "CANCELLED"
	if f.mode == "children" {
		settled = false
	}
	var at, cancel any
	if settled {
		at = "2026-10-05T12:00:00Z"
	}
	if status == "CANCELLED" {
		cancel = at
		at = nil
	}
	revision := 1
	if status == "CANCELLED" {
		revision = 2
	}
	return map[string]any{"project_id": "p1", "id": "r1", "task_id": "t1", "revision": revision,
		"status": status, "children_stopped": settled, "queue_empty": settled,
		"execution_report": "Fixture host execution report, no model used", "exit_code": 0, "result_artifact_ids": []any{"artifact-1"},
		"runtime_settled_at": at, "cancel_confirmed_at": cancel, "cancel_requested_at": cancel}
}

func fixtureEvent(sequence int, kind, run string, payload map[string]any) map[string]any {
	return map[string]any{"event_id": fmt.Sprintf("e-%d", sequence), "session_id": "s1", "sequence": sequence,
		"core_build_id": "fixture-build", "protocol_version": clientProtocol, "run_id": run,
		"command_id": nil, "domain_event_id": nil, "kind": kind, "payload": payload}
}

func (f *cliStreamFixture) appendState(run map[string]any) {
	payload := map[string]any{"run_id": run["id"], "status": run["status"], "revision": run["revision"],
		"children_stopped": run["children_stopped"], "queue_empty": run["queue_empty"],
		"cancel_requested_at": run["cancel_requested_at"], "cancel_confirmed_at": run["cancel_confirmed_at"], "settled_at": run["runtime_settled_at"]}
	f.events = append(f.events, fixtureEvent(len(f.events)+1, "RUN_STATE", run["id"].(string), payload))
}

func (f *cliStreamFixture) serve(w http.ResponseWriter, r *http.Request) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if r.Header.Get("Authorization") != "Bearer fixture-only" {
		http.Error(w, "unauthorized", 401)
		return
	}
	if r.Method == http.MethodGet {
		var body any
		switch r.URL.Path {
		case "/v1/projects/p1/goals/g1":
			ids := []any{"t1"}
			if f.mode == "ambiguous" {
				ids = append(ids, "other-task")
			}
			body = map[string]any{"id": "g1", "project_id": "p1", "task_ids": ids}
		case "/v1/projects/p1/tasks/t1":
			f.taskReads++
			var run any
			if f.phase() != "PENDING" {
				run = "r1"
			}
			status := "EXECUTION_REPORTED"
			if run == nil {
				status = "READY"
			}
			if f.mode == "blocked" {
				status = "BLOCKED"
			}
			if f.mode == "failed" {
				status = "FAILED"
			}
			if f.mode == "cancel-pending" && f.taskReads == 1 {
				f.signals <- os.Interrupt
			}
			body = map[string]any{"id": "t1", "project_id": "p1", "goal_id": "g1", "status": status, "active_run_id": run}
		case "/v1/projects/p1/runs/r1":
			run := f.run()
			if f.mode == "missing-report" {
				run["execution_report"] = nil
			}
			body = run
		default:
			http.NotFound(w, r)
			return
		}
		json.NewEncoder(w).Encode(body)
		return
	}
	raw, _ := io.ReadAll(r.Body)
	var env map[string]any
	if json.Unmarshal(raw, &env) != nil {
		http.Error(w, "invalid", 400)
		return
	}
	method, _ := env["method"].(string)
	f.methods = append(f.methods, method)
	payload := cliObject(env["payload"])
	status, result := "COMPLETED", map[string]any{}
	switch method {
	case "session.list":
		result = map[string]any{"items": []any{}, "next_cursor": nil}
	case "session.create", "session.get":
		result = f.snapshot()
	case "session.send":
		f.sendCalls++
		f.sendBodies = append(f.sendBodies, string(raw))
		f.admitted = true
		if f.sendCalls == 1 && (f.mode == "cancel" || f.mode == "cancel-unknown" || f.mode == "cancel-no-run") {
			f.signals <- os.Interrupt
		}
		select {
		case f.sent <- continuationString(payload, "text"):
		default:
		}
		if f.mode == "pending" && f.sendCalls < 3 {
			status = "ACKNOWLEDGED"
			if f.sendCalls == 2 {
				status = "IN_PROGRESS"
			}
		} else {
			result = map[string]any{"message_id": "m1", "run_id": nil, "queue_position": 0, "snapshot": f.snapshot()}
		}
	case "session.events":
		f.pages++
		if f.mode == "disconnect" {
			conn, _, _ := w.(http.Hijacker).Hijack()
			conn.Close()
			return
		}
		if f.mode == "cursor" {
			json.NewEncoder(w).Encode(map[string]any{"protocol_version": clientProtocol, "command_id": env["command_id"], "method": method, "session_id": "s1", "status": "REJECTED", "revision": 5, "error_code": "CURSOR_INVALID"})
			return
		}
		if f.mode == "paged" && !f.phases["prefix"] {
			f.phases["prefix"] = true
			for i := 0; i < 230; i++ {
				f.events = append(f.events, fixtureEvent(len(f.events)+1, "MESSAGE", "r1", map[string]any{"message_id": "response", "role": "ASSISTANT", "phase": "DELTA", "text": "中文 " + strconv.Itoa(i), "part_index": 0, "content_offset_utf8_bytes": i}))
			}
		}
		if f.mode == "delayed" && !f.phases["old"] {
			f.phases["old"] = true
			old := f.run()
			old["id"], old["status"], old["children_stopped"], old["queue_empty"], old["runtime_settled_at"] = "old-run", "SETTLED", true, true, "2026-10-05T11:00:00Z"
			f.appendState(old)
		}
		phase := f.phase()
		if phase != "PENDING" && !f.phases[phase] {
			f.phases[phase] = true
			f.appendState(f.run())
			if phase == "SETTLED" && f.mode != "missing-artifact" {
				f.events = append(f.events, fixtureEvent(len(f.events)+1, "ARTIFACT", "r1", map[string]any{"artifact_ref": map[string]any{"id": "artifact-1"}, "availability": "AVAILABLE"}))
			}
		}
		after, _ := cliInteger(payload["after_sequence"])
		start, end := int(after), len(f.events)
		if end > start+200 {
			end = start + 200
		}
		if start > len(f.events) {
			http.Error(w, "bad cursor", 400)
			return
		}
		result = map[string]any{"events": f.events[start:end], "next_sequence": end, "high_watermark": len(f.events), "has_more": end < len(f.events)}
		if f.mode == "foreign" && len(f.events) > 0 {
			f.events[0].(map[string]any)["session_id"] = "foreign"
		}
		if f.mode == "gap" && len(f.events) > 0 {
			f.events[0].(map[string]any)["sequence"] = 4
			result["high_watermark"], result["next_sequence"] = 4, 4
		}
		if f.mode == "stuck" {
			result = map[string]any{"events": []any{}, "next_sequence": 0, "high_watermark": 1, "has_more": true}
		}
	case "session.control":
		if payload["action"] != "CANCEL" || payload["target_id"] != "r1" || env["writer_epoch"] != float64(1) {
			http.Error(w, "wrong cancellation", 400)
			return
		}
		f.cancelCalls++
		f.cancelled = true
		status = "ACKNOWLEDGED"
	case "goal.start":
		json.NewEncoder(w).Encode(map[string]any{"protocol_version": clientProtocol, "command_id": env["command_id"], "method": method, "session_id": "s1", "status": "NOT_IMPLEMENTED", "revision": 5})
		return
	case "host.status":
		result = map[string]any{"host_state": "READY"}
	default:
		http.Error(w, "unknown method", 400)
		return
	}
	json.NewEncoder(w).Encode(map[string]any{"protocol_version": clientProtocol, "command_id": env["command_id"], "method": method,
		"session_id": "s1", "status": status, "revision": 5 + len(f.events), "result": result})
}

func (f *cliStreamFixture) runCLI() (map[string]any, int, []map[string]any) {
	c := &v2Context{clientID: "c1", credential: "fixture-only", projectID: "p1", commandID: "fixture-command", baseURL: f.server.URL}
	rows := []map[string]any{}
	options := cliFollowOptions{200 * time.Millisecond, time.Millisecond, 80 * time.Millisecond, f.signals, func(row map[string]any) { rows = append(rows, row) }}
	out, code := runCLIVerb("run", []string{"读取 中文 空格目录，修复并测试"}, c, cliConfig{WorkspaceRef: "ws-fixture", Model: "fixed-model"}, options)
	return out, code, rows
}

func TestW05CLIFollowActualPagesAndDelayedAdmission(t *testing.T) {
	for _, mode := range []string{"paged", "pending", "delayed"} {
		t.Run(mode, func(t *testing.T) {
			f := newCLIStreamFixture(t, mode)
			out, code, rows := f.runCLI()
			if code != 0 || out["status"] != "EXECUTION_REPORTED" || cliObject(out["execution"])["run_id"] != "r1" {
				t.Fatalf("code=%d out=%v", code, out)
			}
			if mode == "paged" && (len(rows) != 232 || f.pages < 2) {
				t.Fatalf("truncated events: %d pages=%d", len(rows), f.pages)
			}
			if mode == "pending" && (f.sendCalls != 3 || f.sendBodies[0] != f.sendBodies[1] || f.sendBodies[1] != f.sendBodies[2]) {
				t.Fatal("pending command changed envelope or exited before admission")
			}
			if mode == "delayed" && f.taskReads < 3 {
				t.Fatal("old terminal Run satisfied new task")
			}
			for _, row := range rows {
				if _, err := json.Marshal(row); err != nil {
					t.Fatal(err)
				}
			}
			t.Logf("FIXTURE mode=%s event_rows=%d event_pages=%d task_reads=%d send_calls=%d accepted=false", mode, len(rows), f.pages, f.taskReads, f.sendCalls)
		})
	}
}

func TestW05CLIFollowRefusesIncompleteExecution(t *testing.T) {
	for _, mode := range []string{"blocked", "children", "unknown", "foreign", "gap", "stuck", "disconnect", "cursor", "ambiguous", "missing-report", "missing-artifact", "failed"} {
		t.Run(mode, func(t *testing.T) {
			f := newCLIStreamFixture(t, mode)
			out, code, rows := f.runCLI()
			want := exitNotImplemented
			if mode == "failed" {
				want = exitFailed
			}
			if code != want || out["status"] == "EXECUTION_REPORTED" {
				t.Fatalf("code=%d out=%v", code, out)
			}
			if mode == "cursor" && (len(rows) != 1 || rows[0]["type"] != "session.snapshot") {
				t.Fatal("cursor failure did not recover actual snapshot")
			}
			if mode == "blocked" && out["reason"] != "TASK_BLOCKED" {
				t.Fatal(out)
			}
			if mode == "gap" && out["reason"] != "EVENT_SEQUENCE_GAP" {
				t.Fatal(out)
			}
			t.Logf("FIXTURE mode=%s exit=%d reason=%s", mode, code, out["reason"])
		})
	}
}

func TestW05CLICancelRequiresHostSettlement(t *testing.T) {
	for _, mode := range []string{"cancel", "cancel-pending", "cancel-unknown", "cancel-no-run"} {
		t.Run(mode, func(t *testing.T) {
			f := newCLIStreamFixture(t, mode)
			out, code, _ := f.runCLI()
			want := exitInterrupted
			if mode == "cancel-unknown" || mode == "cancel-no-run" {
				want = exitNotImplemented
			}
			if code != want {
				t.Fatalf("code=%d out=%v", code, out)
			}
			if mode != "cancel-no-run" && f.cancelCalls != 1 {
				t.Fatalf("actual cancel calls=%d out=%v", f.cancelCalls, out)
			}
			if mode == "cancel-pending" && f.taskReads < 3 {
				t.Fatal("pending Run cancelled without original task binding")
			}
			if mode == "cancel-no-run" && f.taskReads < 2 {
				t.Fatal("null Run caused immediate exit")
			}
			t.Logf("FIXTURE mode=%s actual_host_cancel=%d task_reads=%d exit=%d", mode, f.cancelCalls, f.taskReads, code)
		})
	}
}

func TestW05CLIEventReplayIntegrity(t *testing.T) {
	for _, mode := range []string{"exact", "changed", "nonadvancing"} {
		t.Run(mode, func(t *testing.T) {
			c := &v2Context{sessionID: "s1"}
			rows := 0
			f := &cliFlow{c: c, options: cliFollowOptions{emit: func(map[string]any) { rows++ }}}
			e := &cliExecution{build: "fixture-build", seen: map[int64][32]byte{}, runStates: map[string]map[string]any{}}
			// Round-trip through JSON has the exact transport number types.
			page := func(event map[string]any, next int, more bool) map[string]any {
				raw, _ := json.Marshal(map[string]any{"events": []any{event}, "next_sequence": next, "high_watermark": next, "has_more": more})
				var value map[string]any
				json.Unmarshal(raw, &value)
				return value
			}
			ev := fixtureEvent(1, "MESSAGE", "r1", map[string]any{"text": "真实事件"})
			if _, why := e.consume(f, page(ev, 1, false)); why != "" {
				t.Fatal(why)
			}
			if mode == "changed" {
				ev["payload"] = map[string]any{"text": "changed"}
			}
			_, why := e.consume(f, page(ev, 1, mode == "nonadvancing"))
			if (mode == "exact") != (why == "") || rows != 1 {
				t.Fatalf("mode=%s why=%s rows=%d", mode, why, rows)
			}
		})
	}
}

func TestW05CLIInteractiveBeforeEOFAndSlash(t *testing.T) {
	if os.Getenv("RESEARCHOS_TEST_STREAM_CHILD") == "1" {
		cliInteractive(nil)
		os.Exit(0)
	}
	f := newCLIStreamFixture(t, "settled")
	dir := t.TempDir()
	discoveryFile, configFile := filepath.Join(dir, "host.json"), filepath.Join(dir, "config.json")
	raw, _ := json.Marshal(discovery{URL: f.server.URL})
	os.WriteFile(discoveryFile, raw, 0600)
	raw, _ = json.Marshal(cliConfig{ProjectID: "p1", WorkspaceRef: "ws-fixture", Model: "fixed-model"})
	os.WriteFile(configFile, raw, 0600)
	cmd := exec.Command(os.Args[0], "-test.run=^TestW05CLIInteractiveBeforeEOFAndSlash$")
	cmd.Env = append(os.Environ(), "RESEARCHOS_TEST_STREAM_CHILD=1", "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile,
		"RESEARCHOS_CLI_CREDENTIAL=fixture-only", "RESEARCHOS_CLI_CLIENT_ID=c1")
	stdin, _ := cmd.StdinPipe()
	stdout, _ := cmd.StdoutPipe()
	var diagnostics bytes.Buffer
	cmd.Stderr = &diagnostics
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if cmd.ProcessState == nil {
			cmd.Process.Kill()
			cmd.Wait()
		}
	})
	io.WriteString(stdin, "读取 中文 空格目录\\\n修复并测试\n")
	select {
	case text := <-f.sent:
		if text != "读取 中文 空格目录\n修复并测试" {
			t.Fatalf("multiline changed: %q", text)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("interactive waited for EOF before dispatch")
	}
	scanner := bufio.NewScanner(stdout)
	readSummary := func() map[string]any {
		t.Helper()
		for scanner.Scan() {
			var row map[string]any
			if err := json.Unmarshal(scanner.Bytes(), &row); err != nil {
				t.Fatalf("stdout mixed logs: %s", scanner.Text())
			}
			if row["command"] != nil {
				return row
			}
		}
		t.Fatalf("missing summary: %v stderr=%s", scanner.Err(), diagnostics.String())
		return nil
	}
	if out := readSummary(); out["status"] != "EXECUTION_REPORTED" {
		t.Fatal(out)
	}
	// A slash command must use its actual handler, not become model input.
	io.WriteString(stdin, "/goal 保持原目标\n")
	if out := readSummary(); out["command"] != "/goal" || out["exit_code"] != float64(3) {
		t.Fatal(out)
	}
	stdin.Close()
	err := cmd.Wait()
	if exit, ok := err.(*exec.ExitError); !ok || exit.ExitCode() != 3 {
		t.Fatalf("expected honest unavailable Goal: %v", err)
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	if f.sendCalls != 1 || !strings.Contains(strings.Join(f.methods, ","), "goal.start") {
		t.Fatal(f.methods)
	}
	var saved cliConfig
	raw, _ = os.ReadFile(configFile)
	if json.Unmarshal(raw, &saved) != nil || saved.SessionID != "s1" || saved.WriterEpoch != 1 {
		t.Fatal("interactive context not saved")
	}
	t.Log("FIXTURE actual CLI child sent multiline Chinese before stdin EOF; slash goal reached typed host refusal; every stdout line parsed; session retained")
}
