package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// This is an explicit HTTP protocol fixture, with no model/provider/runtime
// execution. Its independent state machine delays admission, run binding and
// cancellation confirmation so transport success cannot certify itself.
type cliStreamFixture struct {
	t                *testing.T
	server           *httptest.Server
	mu               sync.Mutex
	mode             string
	admitted         bool
	cancelled        bool
	taskReads        int
	sendCalls        int
	pages            int
	cancelCalls      int
	cancelOperations int
	cancelCommand    string
	cancelBody       string
	cancelHash       [32]byte
	cancelTarget     string
	events           []any
	phases           map[string]bool
	sendBodies       []string
	methods          []string
	signals          chan os.Signal
	sent             chan string
	goalEnabled      bool
	goalDraft        bool
	goalBodies       []string
	goalMutate       func(map[string]any)
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
	var goalStatus any
	if f.admitted {
		goalStatus = "ACTIVE"
		if f.goalDraft {
			goalStatus, run = "DRAFT", nil
		}
	}
	return map[string]any{"protocol_version": clientProtocol, "session_id": "s1", "project_id": "p1", "goal_id": goal,
		"workspace_ref": "ws-fixture", "native_session_ref": "native-fixture", "title": "中文 Goal", "archived_at": nil,
		"created_at": "2026-10-05T12:00:00Z", "updated_at": "2026-10-05T12:00:00Z", "model_config_ref": "fixed-model",
		"goal_status": goalStatus, "run_status": nil, "checkpoint_artifact_ref": nil, "pending_command_ids": []any{},
		"pending_permissions": []any{}, "resume_requires_explicit_user": false, "messages": []any{}, "transcript_artifact_ref": nil, "has_earlier_messages": false,
		"active_run_id": run, "revision": 5 + len(f.events), "event_sequence": len(f.events), "earliest_event_sequence": 0,
		"core_build_id": "fixture-build", "writer": map[string]any{"client_id": "c1", "epoch": 1, "expires_at": time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano)}}
}

func (f *cliStreamFixture) phase() string {
	switch f.mode {
	case "cancel", "cancel-pending", "cancel-unknown", "pending-cancel":
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
	case "session.attach":
		result = map[string]any{"snapshot": f.snapshot(), "write_owner_acquired": payload["request_write_owner"] == true}
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
			result = cliProtocolPendingFixture(env["command_id"])
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
			json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "REJECTED", nil, "CURSOR_INVALID", 5))
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
				f.events = append(f.events, fixtureEvent(len(f.events)+1, "ARTIFACT", "r1", map[string]any{"artifact_ref": map[string]any{"entity_type": "Artifact", "id": "artifact-1", "revision": 1, "content_hash": "sha256:" + strings.Repeat("a", 64)}, "availability": "AVAILABLE"}))
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
		if payload["action"] != "CANCEL" || env["session_id"] != "s1" || env["project_id"] != "p1" || env["writer_epoch"] != float64(1) || !f.admitted {
			http.Error(w, "wrong cancellation", 400)
			return
		}
		f.cancelCalls++
		if f.cancelOperations == 0 {
			f.cancelTarget = "g1"
			if run := f.snapshot()["active_run_id"]; run != nil {
				f.cancelTarget = run.(string)
			}
			if payload["target_id"] != f.cancelTarget || env["expected_revision"] != float64(5+len(f.events)) {
				http.Error(w, "wrong original target or revision", 409)
				return
			}
			f.cancelCommand, _ = env["command_id"].(string)
			if f.cancelCommand == "" {
				http.Error(w, "missing identity", 400)
				return
			}
			f.cancelBody, f.cancelHash = string(raw), sha256.Sum256(raw)
			f.cancelOperations++
		} else if env["command_id"] != f.cancelCommand || string(raw) != f.cancelBody || sha256.Sum256(raw) != f.cancelHash {
			http.Error(w, "changed cancellation replay", 409)
			return
		}
		status = "ACKNOWLEDGED"
		result = cliProtocolPendingFixture(env["command_id"])
		if f.cancelCalls >= 2 && f.mode != "cancel-unknown" {
			f.cancelled, status = true, "COMPLETED"
			result = map[string]any{"action": payload["action"], "target_id": payload["target_id"], "control_request_id": "control-fixture", "snapshot": f.snapshot(), "settled": true, "children_stopped": true, "queue_empty": true}
		}
	case "goal.start":
		if f.goalEnabled {
			f.goalBodies = append(f.goalBodies, string(raw))
			f.admitted = true
			f.goalDraft = payload["start_as_draft"] == true || f.mode == "unexpected-draft"
			if len(f.goalBodies) == 1 && (f.mode == "cancel" || f.mode == "cancel-unknown" || f.mode == "cancel-no-run" || f.mode == "pending-cancel") {
				f.signals <- os.Interrupt
			}
			if (f.mode == "pending" || f.mode == "pending-cancel") && len(f.goalBodies) < 3 {
				status = "ACKNOWLEDGED"
				result = cliProtocolPendingFixture(env["command_id"])
			} else {
				snap := f.snapshot()
				result = map[string]any{"goal_id": "g1", "goal_revision": 37, "goal_status": snap["goal_status"], "snapshot": snap}
			}
			reply := cliProtocolReplyFixture(env, status, result, "", 37)
			if f.goalMutate != nil {
				f.goalMutate(reply)
			}
			json.NewEncoder(w).Encode(reply)
			return
		}
		json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "REJECTED", nil, "NOT_IMPLEMENTED", 5))
		return
	case "host.status":
		result = cliProtocolHostFixture(env["client_id"])
	default:
		http.Error(w, "unknown method", 400)
		return
	}
	reply := cliProtocolReplyFixture(env, status, result, "", 5+len(f.events))
	if method == "session.create" {
		reply["session_id"] = "s1"
	}
	json.NewEncoder(w).Encode(reply)
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
			if mode == "cancel-unknown" {
				want = exitNotImplemented
			}
			if code != want {
				t.Fatalf("code=%d out=%v", code, out)
			}
			f.assertCancellation(t)
			t.Logf("FIXTURE mode=%s actual_host_cancel=%d task_reads=%d exit=%d", mode, f.cancelCalls, f.taskReads, code)
		})
	}
}

func (f *cliStreamFixture) assertCancellation(t *testing.T) {
	t.Helper()
	if f.cancelOperations != 1 || f.cancelCalls < 2 || f.cancelCommand == "" || sha256.Sum256([]byte(f.cancelBody)) != f.cancelHash {
		t.Fatal("cancellation must replay one exact original operation", f.cancelOperations, f.cancelCalls)
	}
	want := "r1"
	if f.mode == "cancel-pending" || f.mode == "cancel-no-run" {
		want = "g1"
	}
	if f.cancelTarget != want {
		t.Fatal("original admitted cancellation target", f.cancelTarget, want)
	}
	if f.mode == "cancel-unknown" {
		if f.cancelled || f.run()["children_stopped"] == true || f.run()["queue_empty"] == true {
			t.Fatal("unknown cancellation was falsely settled")
		}
	} else if !f.cancelled {
		t.Fatal("no host-confirmed settlement")
	}
	if f.mode == "cancel-no-run" && (f.snapshot()["active_run_id"] != nil || len(f.events) != 0 || f.taskReads == 0) {
		t.Fatal("noRun cancellation fabricated a Run")
	}
	t.Logf("FIXTURE cancellation target=%s operations=%d attempts=%d exact_request_sha256=%x settled=%t", f.cancelTarget, f.cancelOperations, f.cancelCalls, f.cancelHash, f.cancelled)
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

func (f *cliStreamFixture) runGoal(name string, args []string, existing bool) (map[string]any, int, *v2Context) {
	f.goalEnabled = true
	c := &v2Context{clientID: "c1", credential: "fixture-only", projectID: "p1", commandID: "goal-fixture-command", baseURL: f.server.URL, revision: 91, epoch: 99}
	if existing {
		c.sessionID = "s1"
	}
	options := cliFollowOptions{600 * time.Millisecond, time.Millisecond, 120 * time.Millisecond, f.signals, func(map[string]any) {}}
	out, code := runCLIVerb(name, args, c, cliConfig{}, options)
	return out, code, c
}

func TestW05CLIGoalAdoptionAndAliases(t *testing.T) {
	for _, name := range []string{"goal", "go", "/goal"} {
		for _, existing := range []bool{false, true} {
			t.Run(fmt.Sprintf("%s/existing=%t", name, existing), func(t *testing.T) {
				f := newCLIStreamFixture(t, "paged")
				out, code, c := f.runGoal(name, []string{"修复真实目标"}, existing)
				if code != 0 || out["status"] != "EXECUTION_REPORTED" || c.sessionID != "s1" || c.epoch != 1 || c.revision == 37 || len(f.goalBodies) != 1 || f.pages < 2 {
					t.Fatalf("out=%v context=%+v", out, c)
				}
				var env map[string]any
				json.Unmarshal([]byte(f.goalBodies[0]), &env)
				if existing {
					if f.methods[0] != "session.get" || env["expected_revision"] != float64(5) || env["writer_epoch"] != float64(1) {
						t.Fatal(env, f.methods)
					}
				} else if env["session_id"] != nil || env["expected_revision"] != nil || env["writer_epoch"] != nil {
					t.Fatal(env)
				}
				if out["admission_command_id"] != env["command_id"] || cliObject(out["goal"])["goal_revision"] != float64(37) {
					t.Fatal(out)
				}
				for _, method := range f.methods {
					if method == "session.send" || method == "session.create" {
						t.Fatal(f.methods)
					}
				}
				t.Setenv("RESEARCHOS_CLI_CONFIG", filepath.Join(t.TempDir(), "saved.json"))
				cfg := cliConfig{}
				if err := saveCLIContext(c, &cfg); err != nil {
					t.Fatal(err)
				}
				saved, err := readConfig()
				if err != nil || saved.SessionID != "s1" || saved.Revision != c.revision || saved.WriterEpoch != 1 {
					t.Fatal(saved, err)
				}
			})
		}
	}
}

func TestW05CLIGoalDraftAndExecutionOutcomes(t *testing.T) {
	cases := []struct {
		mode  string
		draft bool
		want  int
	}{
		{"draft", true, 0}, {"unexpected-draft", false, 3}, {"pending", false, 0}, {"delayed", false, 0},
		{"blocked", false, 3}, {"failed", false, 1}, {"missing-report", false, 3}, {"missing-artifact", false, 3}, {"children", false, 3},
		{"cancel-pending", false, 130}, {"pending-cancel", false, 130}, {"cancel-unknown", false, 3}, {"cancel-no-run", false, 130},
	}
	for _, tc := range cases {
		t.Run(tc.mode, func(t *testing.T) {
			f := newCLIStreamFixture(t, tc.mode)
			args := []string{"原始 Goal"}
			if tc.draft {
				args = append(args, "--draft")
			}
			out, code, c := f.runGoal("goal", args, false)
			if code != tc.want || c.sessionID != "s1" || c.epoch != 1 {
				t.Fatalf("code=%d out=%v context=%+v", code, out, c)
			}
			if tc.draft {
				if out["status"] != "GOAL_DRAFT_CREATED" || cliObject(out["execution"])["status"] != "NOT_STARTED" || cliObject(out["execution"])["independent_acceptance"] != "NOT_EVALUATED" || f.pages != 0 || f.taskReads != 0 || len(f.methods) != 1 {
					t.Fatal(out, f.methods)
				}
			}
			if strings.HasPrefix(tc.mode, "pending") {
				if len(f.goalBodies) != 3 || f.goalBodies[0] != f.goalBodies[1] || f.goalBodies[1] != f.goalBodies[2] {
					t.Fatal("pending Goal changed envelope", f.goalBodies)
				}
			}
			if strings.Contains(tc.mode, "cancel") {
				f.assertCancellation(t)
			}
			if tc.mode == "delayed" && f.taskReads < 3 {
				t.Fatal("old terminal satisfied Goal")
			}
			if code != 0 && out["admission_command_id"] == "" {
				t.Fatal(out)
			}
		})
	}
}

func TestW05CLIGoalRejectsBeforeContextAdoption(t *testing.T) {
	mutations := map[string]func(map[string]any){
		"missing_snapshot":          func(r map[string]any) { delete(cliObject(r["result"]), "snapshot") },
		"invalid_goal":              func(r map[string]any) { cliObject(r["result"])["goal_id"] = "" },
		"fraction_revision":         func(r map[string]any) { cliObject(r["result"])["goal_revision"] = 1.5 },
		"unknown_status":            func(r map[string]any) { cliObject(r["result"])["goal_status"] = "COMPLETED" },
		"status_mismatch":           func(r map[string]any) { cliObject(r["result"])["goal_status"] = "ACCEPTED" },
		"goal_mismatch":             func(r map[string]any) { cliSnapshot(r)["goal_id"] = "other-goal" },
		"project_mismatch":          func(r map[string]any) { cliSnapshot(r)["project_id"] = "other-project" },
		"session_mismatch":          func(r map[string]any) { r["session_id"] = "other-session" },
		"explicit_session_mismatch": func(r map[string]any) { cliSnapshot(r)["session_id"] = "other-session" },
		"missing_native":            func(r map[string]any) { delete(cliSnapshot(r), "native_session_ref") },
		"protocol_mismatch":         func(r map[string]any) { cliSnapshot(r)["protocol_version"] = "other" },
		"writer_other":              func(r map[string]any) { cliObject(cliSnapshot(r)["writer"])["client_id"] = "other-client" },
		"writer_absent":             func(r map[string]any) { cliSnapshot(r)["writer"] = nil },
		"fraction_epoch":            func(r map[string]any) { cliObject(cliSnapshot(r)["writer"])["epoch"] = 1.5 },
	}
	for name, mutate := range mutations {
		t.Run(name, func(t *testing.T) {
			f := newCLIStreamFixture(t, "settled")
			f.goalMutate = mutate
			existing := name == "explicit_session_mismatch"
			out, code, c := f.runGoal("goal", []string{"原 Goal"}, existing)
			expectedSession, expectedRevision, expectedEpoch := "", int64(91), int64(99)
			if existing {
				expectedSession, expectedRevision, expectedEpoch = "s1", 5, 1
			}
			if code == 0 || c.sessionID != expectedSession || c.revision != expectedRevision || c.epoch != expectedEpoch || f.pages != 0 {
				t.Fatalf("malformed result adopted: %v context=%+v", out, c)
			}
		})
	}
}

func TestW05CLIGoalInterruptBeforeAdmission(t *testing.T) {
	f := newCLIStreamFixture(t, "settled")
	f.signals <- os.Interrupt
	out, code, _ := f.runGoal("goal", []string{"do not admit"}, false)
	if code != 130 || len(f.goalBodies) != 0 || out["reason"] != "CANCELLED_BEFORE_ADMISSION" {
		t.Fatal(out)
	}
}

func TestW05CLIInteractiveGoalJSONL(t *testing.T) {
	if os.Getenv("RESEARCHOS_TEST_GOAL_CHILD") == "1" {
		cliInteractive(nil)
		os.Exit(0)
	}
	f := newCLIStreamFixture(t, "settled")
	f.goalEnabled = true
	dir := t.TempDir()
	discoveryFile, configFile := filepath.Join(dir, "host.json"), filepath.Join(dir, "config.json")
	raw, _ := json.Marshal(discovery{URL: f.server.URL})
	os.WriteFile(discoveryFile, raw, 0600)
	raw, _ = json.Marshal(cliConfig{ProjectID: "p1", WorkspaceRef: "ws-fixture", Model: "fixed-model"})
	os.WriteFile(configFile, raw, 0600)
	cmd := exec.Command(os.Args[0], "-test.run=^TestW05CLIInteractiveGoalJSONL$")
	cmd.Env = append(os.Environ(), "RESEARCHOS_TEST_GOAL_CHILD=1", "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile, "RESEARCHOS_CLI_CREDENTIAL=fixture-only", "RESEARCHOS_CLI_CLIENT_ID=c1")
	cmd.Stdin = strings.NewReader("/goal 修复 中文目标\n")
	var out, diagnostics bytes.Buffer
	cmd.Stdout = &out
	cmd.Stderr = &diagnostics
	if err := cmd.Run(); err != nil {
		t.Fatal(err, out.String(), diagnostics.String())
	}
	scanner := bufio.NewScanner(&out)
	summary := false
	events := 0
	for scanner.Scan() {
		var row map[string]any
		if json.Unmarshal(scanner.Bytes(), &row) != nil {
			t.Fatal("nonJSON stdout", scanner.Text())
		}
		if row["type"] == "session.event" {
			events++
		}
		if row["command"] == "/goal" {
			summary = row["status"] == "EXECUTION_REPORTED" && row["exit_code"] == float64(0)
		}
	}
	if !summary || events != 2 {
		t.Fatal("missing Goal follow output", out.String())
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	if len(f.goalBodies) != 1 || f.sendCalls != 0 {
		t.Fatal(f.methods)
	}
	var saved cliConfig
	raw, _ = os.ReadFile(configFile)
	json.Unmarshal(raw, &saved)
	if saved.SessionID != "s1" || saved.WriterEpoch != 1 {
		t.Fatal(saved)
	}
}

// Only these composition tests resolve a project Goal binding. The embedded
// fixture still refuses admission because it has no LIVE runtime.
type cliGoalBindingFixture struct{ cliSessionBindingFixture }

func (cliGoalBindingFixture) ResolveGoalBinding(_ context.Context, _ *sql.Tx, _, _, _ string) (string, string, error) {
	return "ws-cli", "model-cli-fixture", nil
}

type cliRealGoalFixture struct {
	t      *testing.T
	db     *sql.DB
	server *httptest.Server
	token  string
	pid    string
	mu     sync.Mutex
	goals  [][]byte
}

func newCLIRealGoalFixture(t *testing.T) *cliRealGoalFixture {
	t.Helper()
	f := &cliRealGoalFixture{t: t}
	ctx := context.Background()
	var err error
	f.db, err = store.Open(filepath.Join(t.TempDir(), "real-goal.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { f.db.Close() })
	if err = store.Bootstrap(ctx, f.db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.db.Exec(string(raw)); err != nil {
		t.Fatal(err)
	}
	if err = svc.ProvisionPrincipal(ctx, domain.Principal{ID: "cli-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	f.token, err = svc.IssueCredential(ctx, "cli-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	handler := api.HandlerWithClientRuntime(f.db, t.TempDir(), svc, cliGoalBindingFixture{})
	f.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == v2CommandPath {
			raw, readErr := io.ReadAll(r.Body)
			if readErr != nil {
				t.Error(readErr)
				http.Error(w, "read failed", 500)
				return
			}
			var env map[string]any
			if json.Unmarshal(raw, &env) == nil && env["method"] == "goal.start" {
				f.mu.Lock()
				f.goals = append(f.goals, bytes.Clone(raw))
				f.mu.Unlock()
			}
			r.Body = io.NopCloser(bytes.NewReader(raw))
		}
		handler.ServeHTTP(w, r)
	}))
	t.Cleanup(f.server.Close)
	profile := domain.Object{"name": "CLI Goal composition fixture", "intent": "one finite Goal", "facts": domain.Empty(), "accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	req, err := http.NewRequest("POST", f.server.URL+"/v1/projects", bytes.NewReader(domain.Bytes(profile)))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Authorization", "Bearer "+f.token)
	req.Header.Set("Idempotency-Key", domain.ID())
	resp, err := f.server.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	body, err := io.ReadAll(resp.Body)
	resp.Body.Close()
	if err != nil || resp.StatusCode != 201 {
		t.Fatalf("project status=%d body=%s err=%v", resp.StatusCode, body, err)
	}
	var project domain.Object
	if err = json.Unmarshal(body, &project); err != nil {
		t.Fatal(err)
	}
	f.pid = project["project_id"].(string)
	binding := domain.WorkspaceBinding{AuthorizedRef: "ws-cli", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.pid, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "cli-owner", ClientID: "cli-client", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, err = f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, "ws-cli", string(domain.Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	return f
}

func (f *cliRealGoalFixture) context(command string) *v2Context {
	return &v2Context{clientID: "cli-client", credential: f.token, projectID: f.pid, commandID: command, baseURL: f.server.URL}
}

func (f *cliRealGoalFixture) goalEnvelope() []byte {
	f.mu.Lock()
	defer f.mu.Unlock()
	if len(f.goals) != 1 {
		f.t.Fatalf("actual goal.start count=%d", len(f.goals))
	}
	return bytes.Clone(f.goals[0])
}

func (f *cliRealGoalFixture) count(query string, args ...any) int {
	f.t.Helper()
	var n int
	if err := f.db.QueryRow(query, args...).Scan(&n); err != nil {
		f.t.Fatal(err)
	}
	return n
}

func (f *cliRealGoalFixture) canonicalCounts() (requirements, goals, tasks, runs, effects, dispatches int) {
	for i, kind := range []string{"Requirement", "Goal", "Task", "Run"} {
		n := f.count("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?", f.pid, kind)
		switch i {
		case 0:
			requirements = n
		case 1:
			goals = n
		case 2:
			tasks = n
		case 3:
			runs = n
		}
	}
	effects = f.count("SELECT count(*) FROM resource_effects WHERE project=?", f.pid)
	dispatches = f.count("SELECT count(*) FROM runtime_dispatches WHERE project=?", f.pid)
	return
}

func (f *cliRealGoalFixture) postEnvelope(raw []byte) (int, map[string]any) {
	f.t.Helper()
	req, err := http.NewRequest("POST", f.server.URL+v2CommandPath, bytes.NewReader(raw))
	if err != nil {
		f.t.Fatal(err)
	}
	req.Header.Set("Authorization", "Bearer "+f.token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := f.server.Client().Do(req)
	if err != nil {
		f.t.Fatal(err)
	}
	body, err := io.ReadAll(resp.Body)
	resp.Body.Close()
	if err != nil {
		f.t.Fatal(err)
	}
	var reply map[string]any
	if err := json.Unmarshal(body, &reply); err != nil {
		f.t.Fatalf("HTTP %d untyped body=%s: %v", resp.StatusCode, body, err)
	}
	return resp.StatusCode, reply
}

func (f *cliRealGoalFixture) runGoal(c *v2Context, objective string, draft bool) (map[string]any, int) {
	args := []string{objective}
	if draft {
		args = append(args, "--draft")
	}
	return runCLIVerb("goal", args, c, cliConfig{}, cliFollowOptions{time.Second, time.Millisecond, 100 * time.Millisecond, nil, func(map[string]any) {}})
}

func TestW05CLIRealLocalGoalDraftBindingFixture(t *testing.T) {
	f := newCLIRealGoalFixture(t)
	c := f.context("real-goal-draft")
	out, code := f.runGoal(c, "保存真实草稿目标", true)
	if code != 0 || out["status"] != "GOAL_DRAFT_CREATED" || cliObject(out["execution"])["status"] != "NOT_STARTED" || cliObject(out["execution"])["independent_acceptance"] != "NOT_EVALUATED" {
		t.Fatalf("code=%d out=%v", code, out)
	}
	var sent map[string]any
	if err := json.Unmarshal(f.goalEnvelope(), &sent); err != nil {
		t.Fatal(err)
	}
	if sent["session_id"] != nil || sent["expected_revision"] != nil || sent["writer_epoch"] != nil {
		t.Fatalf("project-level envelope claimed session writer: %v", sent)
	}
	goal := cliObject(out["goal"])
	if c.sessionID == "" || c.revision < 1 || c.epoch != 1 || goal["goal_status"] != "DRAFT" || out["session_id"] != c.sessionID {
		t.Fatalf("CLI lost typed session: %v %+v", out, c)
	}
	operations := out["operations"].([]map[string]any)
	result := cliObject(operations[0]["result"])
	doc, err := cliProtocolDocument()
	if err != nil || doc.ValidateDef("StartGoalResult", result) != nil {
		t.Fatalf("actual draft result did not validate: %v %v", result, err)
	}
	snapshot := cliObject(result["snapshot"])
	if snapshot["session_id"] != c.sessionID || snapshot["revision"] != float64(c.revision) || cliObject(snapshot["writer"])["epoch"] != float64(c.epoch) {
		t.Fatalf("CLI context differs from typed snapshot: %v %+v", snapshot, c)
	}
	if reqs, goals, tasks, runs, effects, dispatches := f.canonicalCounts(); reqs != 1 || goals != 1 || tasks != 0 || runs != 0 || effects != 0 || dispatches != 0 {
		t.Fatalf("draft counts=%d/%d/%d/%d/%d/%d", reqs, goals, tasks, runs, effects, dispatches)
	}
	var goalBody string
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Goal'", f.pid).Scan(&goalBody); err != nil {
		t.Fatal(err)
	}
	var canonical map[string]any
	if err := json.Unmarshal([]byte(goalBody), &canonical); err != nil {
		t.Fatal(err)
	}
	if canonical["id"] != goal["goal_id"] || len(canonical["requirement_refs"].([]any)) != 1 {
		t.Fatalf("goal requirement association missing: %v", canonical)
	}
	if f.count("SELECT count(*) FROM client_sessions WHERE id=? AND project_id=? AND goal_id=?", c.sessionID, f.pid, goal["goal_id"]) != 1 {
		t.Fatal("typed snapshot session not canonical")
	}
	t.Logf("REAL_LOCAL_BINDING_FIXTURE draft session=%s goal=%s revision=%d epoch=%d", c.sessionID, goal["goal_id"], c.revision, c.epoch)
}

func TestW05CLIRealLocalGoalBlockedAndReplayBindingFixture(t *testing.T) {
	f := newCLIRealGoalFixture(t)
	c := f.context("real-goal-blocked")
	out, code := f.runGoal(c, "解释真实有限目标", false)
	goal := cliObject(out["goal"])
	if code != exitNotImplemented || out["status"] == "EXECUTION_REPORTED" || c.sessionID == "" || c.epoch != 1 || goal["goal_status"] != "ACTIVE" {
		t.Fatalf("blocked code=%d out=%v context=%+v", code, out, c)
	}
	if reqs, goals, tasks, runs, effects, dispatches := f.canonicalCounts(); reqs != 1 || goals != 1 || tasks != 1 || runs != 0 || effects != 0 || dispatches != 0 {
		t.Fatalf("blocked counts=%d/%d/%d/%d/%d/%d", reqs, goals, tasks, runs, effects, dispatches)
	}
	var goalBody, taskBody string
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Goal'", f.pid).Scan(&goalBody); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Task'", f.pid).Scan(&taskBody); err != nil {
		t.Fatal(err)
	}
	var canonicalGoal, canonicalTask map[string]any
	if err := json.Unmarshal([]byte(goalBody), &canonicalGoal); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal([]byte(taskBody), &canonicalTask); err != nil {
		t.Fatal(err)
	}
	if canonicalGoal["id"] != goal["goal_id"] || canonicalTask["goal_id"] != goal["goal_id"] || canonicalTask["status"] != "BLOCKED" || len(canonicalGoal["task_ids"].([]any)) != 1 {
		t.Fatalf("canonical Goal/Task mismatch: %v %v", canonicalGoal, canonicalTask)
	}
	t.Setenv("RESEARCHOS_CLI_CONFIG", filepath.Join(t.TempDir(), "blocked-context.json"))
	cfg := cliConfig{}
	if savedCode := cliFlowSummary(out, code, c, &cfg); savedCode != exitNotImplemented {
		t.Fatalf("blocked summary code=%d", savedCode)
	}
	saved, err := readConfig()
	if err != nil || saved.SessionID != c.sessionID || saved.WriterEpoch != c.epoch || saved.Revision != c.revision {
		t.Fatalf("blocked session not saved: %+v %v", saved, err)
	}
	original := f.goalEnvelope()
	status, first := f.postEnvelope(original)
	if status != 200 || first["status"] != "COMPLETED" || cliObject(first["result"])["goal_id"] != goal["goal_id"] || cliSnapshot(first)["session_id"] != c.sessionID {
		t.Fatalf("original envelope replay: HTTP=%d %v", status, first)
	}
	if first["session_id"] != nil {
		t.Fatalf("project-level typed reply must have null session: %v", first)
	}
	operations := out["operations"].([]map[string]any)
	if !reflect.DeepEqual(cliObject(operations[0]["result"]), cliObject(first["result"])) {
		t.Fatalf("idempotent replay changed the original CLI result: original=%v replay=%v", operations[0]["result"], first["result"])
	}
	status, replay := f.postEnvelope(original)
	if status != 200 || !reflect.DeepEqual(first, replay) {
		t.Fatalf("identical envelope changed typed result: HTTP=%d first=%v replay=%v", status, first, replay)
	}
	if doc, err := cliProtocolDocument(); err != nil || doc.ValidateDef("StartGoalResult", cliObject(first["result"])) != nil {
		t.Fatalf("actual replay is not a typed Goal result: %v %v", first, err)
	}
	var changed map[string]any
	if err := json.Unmarshal(original, &changed); err != nil {
		t.Fatal(err)
	}
	cliObject(changed["payload"])["objective"] = "不同的目标"
	changedRaw, err := json.Marshal(changed)
	if err != nil {
		t.Fatal(err)
	}
	status, refused := f.postEnvelope(changedRaw)
	if status != http.StatusConflict || cliObject(refused["error"])["code"] != "COMMAND_ID_CONFLICT" {
		t.Fatalf("changed payload reused command: HTTP=%d %v", status, refused)
	}
	for _, tc := range []struct {
		name     string
		revision int64
		epoch    int64
		wantCode string
	}{
		{"stale_revision", c.revision - 1, c.epoch, "VERSION_CONFLICT"},
		{"stale_writer", c.revision, c.epoch + 1, "STALE_WRITER_EPOCH"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var env map[string]any
			if err := json.Unmarshal(original, &env); err != nil {
				t.Fatal(err)
			}
			env["command_id"] = "real-goal-" + tc.name
			env["session_id"] = c.sessionID
			env["expected_revision"] = tc.revision
			env["writer_epoch"] = tc.epoch
			raw, err := json.Marshal(env)
			if err != nil {
				t.Fatal(err)
			}
			status, reply := f.postEnvelope(raw)
			code := continuationString(cliObject(reply["error"]), "code")
			if code == "" {
				code = continuationString(reply, "error_code")
			}
			if status < 400 && reply["status"] != "REJECTED" || code != tc.wantCode {
				t.Fatalf("stale command passed or wrong typed refusal: HTTP=%d code=%s reply=%v", status, code, reply)
			}
			if reqs, goals, tasks, runs, effects, dispatches := f.canonicalCounts(); reqs != 1 || goals != 1 || tasks != 1 || runs != 0 || effects != 0 || dispatches != 0 {
				t.Fatalf("stale command changed business state: %d/%d/%d/%d/%d/%d", reqs, goals, tasks, runs, effects, dispatches)
			}
		})
	}
	if reqs, goals, tasks, runs, effects, dispatches := f.canonicalCounts(); reqs != 1 || goals != 1 || tasks != 1 || runs != 0 || effects != 0 || dispatches != 0 {
		t.Fatalf("replay changed canonical counts=%d/%d/%d/%d/%d/%d", reqs, goals, tasks, runs, effects, dispatches)
	}
	// A second CLI Goal refreshes through the real session.get before the new write.
	c.commandID = "real-goal-new-command"
	second, secondCode := f.runGoal(c, "解释真实有限目标", false)
	if secondCode == 0 || c.sessionID != saved.SessionID || len(c.requestLog) < 3 || c.requestLog[len(c.requestLog)-2] != "session.get" || c.requestLog[len(c.requestLog)-1] != "goal.start" {
		t.Fatalf("existing Goal did not refresh/refuse: code=%d out=%v log=%v", secondCode, second, c.requestLog)
	}
	if reqs, goals, tasks, runs, effects, dispatches := f.canonicalCounts(); reqs != 1 || goals != 1 || tasks != 1 || runs != 0 || effects != 0 || dispatches != 0 {
		t.Fatalf("new ID duplicated Goal: %d/%d/%d/%d/%d/%d", reqs, goals, tasks, runs, effects, dispatches)
	}
	t.Logf("REAL_LOCAL_BINDING_FIXTURE blocked code=%d goal=%s task=%s session=%s new_command_code=%d", code, goal["goal_id"], canonicalTask["id"], c.sessionID, secondCode)
}

// FIXTURE_PROTOCOL: these are schema-complete transport records, not real host
// attachment completion or runtime qualification.
func cliProtocolPendingFixture(command any) map[string]any {
	return map[string]any{"accepted_at": "2026-10-05T12:00:00Z", "operation_id": command, "after_sequence": 0, "related_resource_ref": nil}
}
func cliProtocolHostFixture(client any) map[string]any {
	return map[string]any{"host_instance_id": "fixture-host", "core_build_id": "fixture-build", "protocol_versions": []any{clientProtocol}, "host_state": "READY", "client_id": client, "authenticated_principal_ref": "fixture-principal", "config_revision": 0, "model_configurations": []any{}, "credentials": []any{}, "workspaces": []any{}, "supported_methods": []any{"host.status"}, "operating_mode": "LOCAL_USER_HOST"}
}
func cliProtocolReplyFixture(env map[string]any, status string, result any, code string, revision any) map[string]any {
	reply := map[string]any{"protocol_version": clientProtocol, "command_id": env["command_id"], "method": env["method"], "session_id": env["session_id"], "revision": revision, "status": status, "error_code": nil, "error": nil, "result": result}
	if code != "" {
		reply["error_code"] = code
		reply["error"] = map[string]any{"code": code, "message": "Synthetic protocol refusal", "retryable": false, "recovery": "STOP_AND_REPORT", "current_revision": nil, "current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": "fixture-correlation"}
	}
	return reply
}

// cliProtocolProcess executes the freshly built production CLI. Its owned
// evidence contains every request, stdout/stderr, argv and the exact local bytes.
func cliProtocolProcess(t *testing.T, serverURL string, cfg cliConfig, stdin string, args ...string) (int, []byte, []byte, []byte) {
	t.Helper()
	binary := os.Getenv("RESEARCHOS_CLI_PROTOCOL_BINARY")
	evidence := os.Getenv("RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR")
	if binary == "" || evidence == "" {
		t.Fatal("compiled CLI and owned evidence directory are required")
	}
	dir := filepath.Join(evidence, strings.NewReplacer("/", "_", "\\", "_").Replace(t.Name()))
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	configFile, discoveryFile := filepath.Join(dir, "config.json"), filepath.Join(dir, "discovery.json")
	initial, _ := json.MarshalIndent(cfg, "", "  ")
	if err := os.WriteFile(configFile, initial, 0600); err != nil {
		t.Fatal(err)
	}
	discovery, _ := json.Marshal(map[string]any{"url": serverURL})
	if err := os.WriteFile(discoveryFile, discovery, 0600); err != nil {
		t.Fatal(err)
	}
	timeout, stop := context.WithTimeout(context.Background(), 15*time.Second)
	defer stop()
	cmd := exec.CommandContext(timeout, binary, args...)
	cmd.Stdin = strings.NewReader(stdin)
	// Explicit same-purpose fixture credentials, never a native credential bridge.
	cmd.Env = append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discoveryFile, "RESEARCHOS_CLI_CONFIG="+configFile, "RESEARCHOS_CLI_CREDENTIAL=fixture-only", "RESEARCHOS_CLI_CLIENT_ID="+cliEnv("RESEARCHOS_CLI_PROTOCOL_CLIENT", "c1"))
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	started := time.Now().UTC()
	err := cmd.Run()
	ended := time.Now().UTC()
	code := 0
	if err != nil {
		if e, ok := err.(*exec.ExitError); ok {
			code = e.ExitCode()
		} else {
			t.Fatal(err)
		}
	}
	after, readErr := os.ReadFile(configFile)
	if readErr != nil {
		t.Fatal(readErr)
	}
	for name, body := range map[string][]byte{"stdout.jsonl": stdout.Bytes(), "stderr.txt": stderr.Bytes(), "config.before.json": initial, "config.after.json": after} {
		if e := os.WriteFile(filepath.Join(dir, name), body, 0600); e != nil {
			t.Fatal(e)
		}
	}
	invocation, _ := json.MarshalIndent(map[string]any{"actualargv": cmd.Args, "cwd": func() string { s, _ := os.Getwd(); return s }(), "started_at": started, "ended_at": ended, "exit_code": code, "measurement_mode": "FIXTURE_PROTOCOL", "timeout": timeout.Err() != nil}, "", "  ")
	if err := os.WriteFile(filepath.Join(dir, "invocation.json"), invocation, 0600); err != nil {
		t.Fatal(err)
	}
	if timeout.Err() != nil {
		t.Fatal("compiled CLI timed out", string(stdout.Bytes()), string(stderr.Bytes()))
	}
	return code, stdout.Bytes(), initial, after
}

func TestCLIProtocolStrictResponse(t *testing.T) {
	t.Run("full-method-results", func(t *testing.T) {
		methods := []string{"host.status", "host.configure", "project.bootstrap", "session.list", "session.create", "session.get", "session.attach", "session.send", "session.control", "session.events", "session.handoff", "goal.start", "provider.models", "provider.probe", "workspace.register", "workspace.list", "workspace.tree", "workspace.read", "workspace.diff", "workspace.write", "artifact.import", "session.update", "permission.respond"}
		for _, method := range methods {
			t.Run(method, func(t *testing.T) {
				server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					var env map[string]any
					json.NewDecoder(r.Body).Decode(&env)
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "COMPLETED", map[string]any{"method_confirmed": method}, "", nil))
				}))
				defer server.Close()
				c := &v2Context{clientID: "c1", credential: "fixture-only", projectID: "p1", sessionID: "s1", revision: 1, epoch: 1, commandID: "method-gate", baseURL: server.URL}
				payload := map[string]any{}
				for _, key := range v2Contract[method].required {
					payload[key] = nil
				}
				if method == "session.attach" {
					payload["request_write_owner"] = false
				}
				before := *c
				_, why, code := v2Call(c, method, payload)
				if code != 1 || why != "INVALID_REPLY_SCHEMA" || c.sessionID != before.sessionID || c.revision != before.revision || c.epoch != before.epoch {
					t.Fatalf("generic strict=false result gate: %d %s %+v", code, why, c)
				}
			})
		}
	})
	// Each case exercises raw bytes through the compiled CLI, not a decoder call.
	cases := []string{"valid-null", "valid-zero", "protocol", "command", "method", "client", "missing-revision", "missing-session", "foreign-session", "fraction", "near-integer", "large-exact", "overflow", "duplicate", "escaped-duplicate", "nested-duplicate", "invalid-utf8", "surrogate", "trailing-value", "unknown-key", "top-in-progress", "top-not-implemented", "missing-result-field", "ack-empty", "ack-snapshot", "ack-null", "rejected-no-error", "error-code-mismatch", "snapshot-project", "snapshot-session", "snapshot-revision", "snapshot-missing-writer", "snapshot-fraction-epoch", "invalid-last-reply"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			var mu sync.Mutex
			requests := []json.RawMessage{}
			scoped := strings.HasPrefix(name, "snapshot-") || name == "invalid-last-reply"
			fixture := &cliStreamFixture{}
			handler := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				raw, _ := io.ReadAll(r.Body)
				mu.Lock()
				requests = append(requests, append(json.RawMessage(nil), raw...))
				mu.Unlock()
				var env map[string]any
				json.Unmarshal(raw, &env)
				result := cliProtocolHostFixture("c1")
				var rev any = nil
				if env["method"] == "session.get" {
					result = fixture.snapshot()
					rev = result["revision"]
				}
				reply := cliProtocolReplyFixture(env, "COMPLETED", result, "", rev)
				mutate := env["method"] == "host.status" && !strings.HasPrefix(name, "snapshot-") || env["method"] == "session.get" && strings.HasPrefix(name, "snapshot-")
				if mutate {
					switch name {
					case "valid-zero":
						reply["revision"] = 0 // Null or >=1 only: explicit zero is malformed.
					case "protocol":
						reply["protocol_version"] = "wrong"
					case "command":
						reply["command_id"] = "foreign"
					case "method":
						reply["method"] = "session.list"
					case "client":
						result["client_id"] = "foreign"
					case "missing-revision":
						delete(reply, "revision")
					case "missing-session":
						delete(reply, "session_id")
					case "foreign-session":
						reply["session_id"] = "foreign"
					case "fraction":
						result["config_revision"] = 1.5
					case "near-integer":
						result["config_revision"] = json.Number("1.0000000000000001")
					case "large-exact":
						result["config_revision"] = json.Number("9007199254740992")
					case "overflow":
						reply["revision"] = json.Number("9223372036854775808")
					case "unknown-key":
						reply["extra"] = true
					case "top-in-progress":
						reply["status"] = "IN_PROGRESS"
					case "top-not-implemented":
						reply["status"] = "NOT_IMPLEMENTED"
					case "missing-result-field":
						delete(result, "credentials")
					case "ack-empty":
						reply["status"] = "ACKNOWLEDGED"
						reply["result"] = map[string]any{}
					case "ack-snapshot":
						reply["status"] = "ACKNOWLEDGED"
						reply["result"] = fixture.snapshot()
					case "ack-null":
						reply["status"] = "ACKNOWLEDGED"
						reply["result"] = nil
					case "rejected-no-error":
						reply["status"] = "REJECTED"
						reply["result"] = nil
					case "error-code-mismatch":
						reply = cliProtocolReplyFixture(env, "REJECTED", nil, "FORBIDDEN", nil)
						cliObject(reply["error"])["code"] = "NOT_FOUND"
					case "snapshot-project":
						result["project_id"] = "other"
					case "snapshot-session":
						result["session_id"] = "other"
					case "snapshot-revision":
						reply["revision"] = 99
					case "snapshot-missing-writer":
						delete(result, "writer")
					case "snapshot-fraction-epoch":
						cliObject(result["writer"])["epoch"] = json.Number("1.0000000000000001")
					case "invalid-last-reply":
						delete(result, "host_state")
					}
				}
				encoded, _ := json.Marshal(reply)
				if mutate {
					switch name {
					case "duplicate":
						encoded = bytes.Replace(encoded, []byte(`"status":"COMPLETED"`), []byte(`"status":"COMPLETED","status":"COMPLETED"`), 1)
					case "escaped-duplicate":
						encoded = bytes.Replace(encoded, []byte(`"status":"COMPLETED"`), []byte(`"status":"COMPLETED","\u0073tatus":"COMPLETED"`), 1)
					case "nested-duplicate":
						encoded = bytes.Replace(encoded, []byte(`"host_state":"READY"`), []byte(`"host_state":"READY","host_state":"READY"`), 1)
					case "invalid-utf8":
						encoded = bytes.Replace(encoded, []byte("READY"), []byte{0xff}, 1)
					case "surrogate":
						encoded = bytes.Replace(encoded, []byte(`"fixture-host"`), []byte(`"\ud800"`), 1)
					case "trailing-value":
						encoded = append(encoded, []byte(` {}`)...)
					}
				}
				w.Write(encoded)
			}))
			defer handler.Close()
			cfg := cliConfig{ProjectID: "p1"}
			if scoped {
				cfg.SessionID = "s1"
				cfg.Revision = 5
				cfg.WriterEpoch = 1
			}
			code, out, before, after := cliProtocolProcess(t, handler.URL, cfg, "", "status")
			mu.Lock()
			record, _ := json.MarshalIndent(requests, "", "  ")
			mu.Unlock()
			dir := filepath.Join(os.Getenv("RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR"), strings.ReplaceAll(t.Name(), "/", "_"))
			os.WriteFile(filepath.Join(dir, "requests.json"), record, 0600)
			expected := exitFailed
			if name == "valid-null" || name == "large-exact" {
				expected = 0
			}
			if code != expected {
				t.Fatalf("exit=%d expected=%d output=%s", code, expected, out)
			}
			if !bytes.Equal(before, after) {
				t.Fatalf("invalid or unchanged reply altered local bytes: %s", out)
			}
		})
	}
}

func TestCLIProtocolAttachCompletionBarrier(t *testing.T) {
	cases := []string{"ack-then-completed", "permanent-ack", "ack-then-conflict", "ack-cancel", "false-acquired", "foreign-writer", "expired-writer", "caller-epoch-not-authority", "readonly-attach", "typed-cancel-ack"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			var bodies [][]byte
			fixture := &cliStreamFixture{}
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				raw, _ := io.ReadAll(r.Body)
				bodies = append(bodies, append([]byte(nil), raw...))
				var env map[string]any
				json.Unmarshal(raw, &env)
				if env["method"] == "session.control" {
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "ACKNOWLEDGED", cliProtocolPendingFixture(env["command_id"]), "", 6))
					return
				}
				if name == "ack-then-conflict" && len(bodies) > 1 {
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "REJECTED", nil, "VERSION_CONFLICT", 5))
					return
				}
				if name == "permanent-ack" || name == "ack-cancel" || len(bodies) == 1 && name == "ack-then-completed" || len(bodies) == 1 && name == "ack-then-conflict" {
					json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "ACKNOWLEDGED", cliProtocolPendingFixture(env["command_id"]), "", 6))
					return
				}
				snap := fixture.snapshot()
				snap["revision"] = 6
				cliObject(snap["writer"])["epoch"] = 2
				if name == "foreign-writer" {
					cliObject(snap["writer"])["client_id"] = "foreign"
				}
				if name == "expired-writer" {
					cliObject(snap["writer"])["expires_at"] = "2020-01-01T00:00:00Z"
				}
				result := map[string]any{"snapshot": snap, "write_owner_acquired": name != "false-acquired" && name != "readonly-attach"}
				json.NewEncoder(w).Encode(cliProtocolReplyFixture(env, "COMPLETED", result, "", 6))
			}))
			defer server.Close()
			c := &v2Context{clientID: "c1", credential: "fixture-only", projectID: "p1", sessionID: "s1", revision: 5, epoch: 91, commandID: "attach-case", baseURL: server.URL}
			budget, cancel := context.WithTimeout(context.Background(), 400*time.Millisecond)
			defer cancel()
			signals := make(chan os.Signal, 1)
			if name == "ack-cancel" {
				signals <- os.Interrupt
			}
			f := &cliFlow{c: c, budget: budget, base: c.commandID, options: cliFollowOptions{timeout: time.Second, poll: 10 * time.Millisecond, cancelTimeout: 200 * time.Millisecond, interrupts: signals}}
			method := "session.attach"
			payload := map[string]any{"after_sequence": 0, "request_write_owner": name != "readonly-attach"}
			if name == "typed-cancel-ack" {
				method = "session.control"
				payload = map[string]any{"action": "CANCEL", "target_id": "r1", "reason": "fixture"}
			}
			_, reason, code := f.call(method, payload, true)
			success := name == "ack-then-completed" || name == "caller-epoch-not-authority" || name == "readonly-attach"
			if success {
				if code != 0 || c.epoch != 2 || c.revision != 6 {
					t.Fatalf("not adopted: %d %s %+v", code, reason, c)
				}
			} else {
				if code == 0 || c.epoch != 91 || c.revision != 5 {
					t.Fatalf("pending/invalid adopted: %d %s %+v", code, reason, c)
				}
			}
			if len(bodies) == 0 {
				t.Fatal("no actual attach request")
			}
			for _, raw := range bodies[1:] {
				if !bytes.Equal(raw, bodies[0]) {
					t.Fatal("pending changed original command/CAS")
				}
			}
			var first map[string]any
			json.Unmarshal(bodies[0], &first)
			if method == "session.attach" && name != "readonly-attach" && first["writer_epoch"] != nil {
				t.Fatal("local claimed epoch leaked into acquisition")
			}
			t.Logf("PROTOCOL_CONTROL name=%s requests=%d exit=%d reason=%s", name, len(bodies), code, reason)
		})
	}
}

func TestCLIProtocolExitClassification(t *testing.T) {
	for _, name := range []string{"NOT_IMPLEMENTED", "FORBIDDEN", "MODEL_UNAVAILABLE", "INVALID_REQUEST", "INTERNAL_ERROR", "illegal-top", "http503", "http403", "legal-ack"} {
		t.Run(name, func(t *testing.T) {
			calls := 0
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				calls++
				var env map[string]any
				json.NewDecoder(r.Body).Decode(&env)
				if name == "http503" {
					http.Error(w, "synthetic", 503)
					return
				}
				if name == "http403" {
					http.Error(w, "synthetic", 403)
					return
				}
				reply := cliProtocolReplyFixture(env, "REJECTED", nil, name, nil)
				if name == "illegal-top" {
					reply = cliProtocolReplyFixture(env, "NOT_IMPLEMENTED", nil, "", nil)
				}
				if name == "legal-ack" {
					reply = cliProtocolReplyFixture(env, "COMPLETED", cliProtocolHostFixture("c1"), "", nil)
					if calls == 1 {
						reply = cliProtocolReplyFixture(env, "ACKNOWLEDGED", cliProtocolPendingFixture(env["command_id"]), "", nil)
					}
				}
				json.NewEncoder(w).Encode(reply)
			}))
			defer server.Close()
			expected := 3
			switch name {
			case "INVALID_REQUEST":
				expected = 2
			case "INTERNAL_ERROR", "illegal-top", "http503":
				expected = 1
			case "legal-ack":
				expected = 0
			}
			code, out, before, after := cliProtocolProcess(t, server.URL, cliConfig{}, "", "status")
			if code != expected || !bytes.Equal(before, after) {
				t.Fatalf("exit=%d expected=%d out=%s", code, expected, out)
			}
			if name == "NOT_IMPLEMENTED" && !bytes.Contains(out, []byte("HOST_REJECTED:NOT_IMPLEMENTED")) {
				t.Fatal(string(out))
			}
			if name == "legal-ack" && calls != 2 {
				t.Fatal("ACK not replayed", calls)
			}
		})
	}
}

// Each negative is delivered to a compiled CLI before any send may occur. A
// pending create remains the same command; later typed pending refusal bounds
// the fixture without introducing a product timeout or completion shortcut.
func cliProtocolCreateNegativeControls(t *testing.T) {
	names := []string{"ack", "foreign", "expired", "null-writer", "missing-writer", "wrong-project", "wrong-sid", "wrong-revision", "fraction-revision", "overflow-revision", "near-epoch", "fraction-epoch", "unknown-key", "duplicate"}
	for _, name := range names {
		t.Run("create-"+name, func(t *testing.T) {
			f := &cliStreamFixture{}
			var mu sync.Mutex
			requests := [][]byte{}
			responses := [][]byte{}
			creates, attaches, sends := 0, 0, 0
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				raw, _ := io.ReadAll(r.Body)
				var env map[string]any
				json.Unmarshal(raw, &env)
				mu.Lock()
				defer mu.Unlock()
				requests = append(requests, append([]byte(nil), raw...))
				var reply map[string]any
				switch env["method"] {
				case "session.list":
					reply = cliProtocolReplyFixture(env, "COMPLETED", map[string]any{"items": []any{}, "next_cursor": nil}, "", nil)
				case "session.create":
					creates++
					snap := f.snapshot()
					reply = cliProtocolReplyFixture(env, "COMPLETED", snap, "", 5)
					reply["session_id"] = "s1"
					switch name {
					case "ack":
						if creates == 1 {
							reply = cliProtocolReplyFixture(env, "ACKNOWLEDGED", cliProtocolPendingFixture(env["command_id"]), "", nil)
						} else {
							reply = cliProtocolReplyFixture(env, "REJECTED", nil, "COMMAND_PENDING", nil)
						}
					case "foreign":
						cliObject(snap["writer"])["client_id"] = "foreign"
					case "expired":
						cliObject(snap["writer"])["expires_at"] = "2020-01-01T00:00:00Z"
					case "null-writer":
						snap["writer"] = nil
					case "missing-writer":
						delete(snap, "writer")
					case "wrong-project":
						snap["project_id"] = "other"
					case "wrong-sid":
						reply["session_id"] = "other"
					case "wrong-revision":
						reply["revision"] = 6
					case "fraction-revision":
						reply["revision"] = json.Number("5.0000000000000001")
					case "overflow-revision":
						reply["revision"] = json.Number("9223372036854775808")
					case "near-epoch":
						cliObject(snap["writer"])["epoch"] = json.Number("1.0000000000000001")
					case "fraction-epoch":
						cliObject(snap["writer"])["epoch"] = 1.5
					case "unknown-key":
						snap["unverified_lease"] = true
					}
				case "session.attach":
					attaches++
					reply = cliProtocolReplyFixture(env, "REJECTED", nil, "WRITER_BUSY", 5)
				case "session.send":
					sends++
					reply = cliProtocolReplyFixture(env, "REJECTED", nil, "INTERNAL_ERROR", nil)
				default:
					reply = cliProtocolReplyFixture(env, "REJECTED", nil, "NOT_IMPLEMENTED", nil)
				}
				encoded, _ := json.Marshal(reply)
				if name == "duplicate" && env["method"] == "session.create" {
					encoded = bytes.Replace(encoded, []byte(`"revision":5`), []byte(`"revision":5,"revision":5`), 1)
				}
				responses = append(responses, append([]byte(nil), encoded...))
				w.Write(encoded)
			}))
			defer server.Close()
			code, out, before, after := cliProtocolProcess(t, server.URL, cliConfig{ProjectID: "p1", WorkspaceRef: "ws-fixture", Model: "model-fixture"}, "must not send\n")
			expected := 1
			if name == "ack" || name == "foreign" || name == "expired" || name == "null-writer" {
				expected = 3
			}
			mu.Lock()
			defer mu.Unlock()
			dir := filepath.Join(os.Getenv("RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR"), strings.ReplaceAll(t.Name(), "/", "_"))
			raw, _ := json.MarshalIndent(map[string]any{"requests_base64": requests, "responses_base64": responses}, "", "  ")
			os.WriteFile(filepath.Join(dir, "wire.json"), raw, 0600)
			if code != expected || sends != 0 {
				t.Fatalf("create negative %s exit=%d send=%d output=%s", name, code, sends, out)
			}
			wantAttach := 0
			if name == "null-writer" {
				wantAttach = 1
			}
			if attaches != wantAttach {
				t.Fatal("hidden acquisition", attaches)
			}
			if expected == 1 || name == "ack" {
				if !bytes.Equal(before, after) {
					t.Fatal("invalid create adopted local bytes")
				}
			}
			if name == "ack" {
				if creates != 2 {
					t.Fatal("pending replay count", creates)
				}
				var originals [][]byte
				for _, raw := range requests {
					var env map[string]any
					json.Unmarshal(raw, &env)
					if env["method"] == "session.create" {
						originals = append(originals, raw)
					}
				}
				if !bytes.Equal(originals[0], originals[1]) {
					t.Fatal("pending create changed original envelope")
				}
			}
		})
	}
}

func cliProtocolTwoMultilineTurns(t *testing.T) {
	binary := os.Getenv("RESEARCHOS_CLI_PROTOCOL_BINARY")
	root := os.Getenv("RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR")
	if binary == "" || root == "" {
		t.Fatal("compiled CLI/evidence required")
	}
	dir := filepath.Join(root, strings.ReplaceAll(t.Name(), "/", "_"))
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	first, second := newCLIStreamFixture(t, "settled"), newCLIStreamFixture(t, "settled")
	active, sendCount, createCount := first, 0, 0
	var lock sync.Mutex
	var requests, responses [][]byte
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		lock.Lock()
		defer lock.Unlock()
		raw, _ := io.ReadAll(r.Body)
		requests = append(requests, append([]byte(nil), raw...))
		var env map[string]any
		json.Unmarshal(raw, &env)
		if env["method"] == "session.create" {
			createCount++
		}
		if env["method"] == "session.send" {
			sendCount++
			if sendCount == 2 {
				second.events = append([]any(nil), first.events...)
				active = second
			}
		}
		clone := r.Clone(r.Context())
		urlCopy := *r.URL
		clone.URL = &urlCopy
		if active == second {
			clone.URL.Path = strings.NewReplacer("/g2", "/g1", "/t2", "/t1", "/r2", "/r1").Replace(clone.URL.Path)
		}
		clone.Body = io.NopCloser(bytes.NewReader(raw))
		rec := httptest.NewRecorder()
		active.serve(rec, clone)
		body := rec.Body.Bytes()
		if active == second {
			body = []byte(strings.NewReplacer(`"g1"`, `"g2"`, `"t1"`, `"t2"`, `"r1"`, `"r2"`, `"artifact-1"`, `"artifact-2"`).Replace(string(body)))
		}
		responses = append(responses, append([]byte(nil), body...))
		w.WriteHeader(rec.Code)
		w.Write(body)
	}))
	defer server.Close()
	cfg := cliConfig{ProjectID: "p1", WorkspaceRef: "ws-fixture", Model: "fixed-model"}
	initial, _ := json.Marshal(cfg)
	config, discovery := filepath.Join(dir, "config.json"), filepath.Join(dir, "discovery.json")
	os.WriteFile(config, initial, 0600)
	raw, _ := json.Marshal(map[string]any{"url": server.URL})
	os.WriteFile(discovery, raw, 0600)
	budget, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	cmd := exec.CommandContext(budget, binary)
	cmd.Env = append(os.Environ(), "RESEARCHOS_CLI_CONFIG="+config, "RESEARCHOS_CLI_DISCOVERY="+discovery, "RESEARCHOS_CLI_CLIENT_ID=c1", "RESEARCHOS_CLI_CREDENTIAL=fixture-only")
	stdin, err := cmd.StdinPipe()
	if err != nil {
		t.Fatal(err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	if err := cmd.Start(); err != nil {
		t.Fatal(err)
	}
	records := make(chan map[string]any, 128)
	scanDone := make(chan struct{})
	var output bytes.Buffer
	go func() {
		defer close(scanDone)
		defer close(records)
		scan := bufio.NewScanner(stdout)
		scan.Buffer(make([]byte, 4096), 2<<20)
		for scan.Scan() {
			line := append([]byte(nil), scan.Bytes()...)
			output.Write(line)
			output.WriteByte('\n')
			var v map[string]any
			if json.Unmarshal(line, &v) == nil {
				records <- v
			}
		}
	}()
	waited := false
	defer func() {
		if !waited {
			_ = cmd.Process.Kill()
			_ = cmd.Wait()
			<-scanDone
		}
		lock.Lock()
		defer lock.Unlock()
		wire, _ := json.MarshalIndent(map[string]any{"requests_base64": requests, "responses_base64": responses}, "", "  ")
		exit := -1
		if cmd.ProcessState != nil {
			exit = cmd.ProcessState.ExitCode()
		}
		invocation, _ := json.MarshalIndent(map[string]any{"actualargv": cmd.Args, "exit_code": exit, "mode": "FIXTURE_PROTOCOL_NOT_MODEL", "driver_failed": t.Failed()}, "", "  ")
		for name, body := range map[string][]byte{"stdout.jsonl": output.Bytes(), "stderr.txt": stderr.Bytes(), "wire.json": wire, "actual-process.json": invocation} {
			os.WriteFile(filepath.Join(dir, name), body, 0600)
		}
	}()
	completed := 0
	for _, input := range []string{"first \\\nquestion\n", "second \\\nquestion\n"} {
		if _, err := io.WriteString(stdin, input); err != nil {
			t.Fatal(err)
		}
		waiting := true
		for waiting {
			select {
			case row, open := <-records:
				if !open {
					t.Fatal("CLI ended before second logical input", output.String(), stderr.String())
				}
				if row["command"] == "run" {
					if row["exit_code"] != float64(0) || row["status"] != "EXECUTION_REPORTED" {
						t.Fatal("fixture turn not reported", row)
					}
					completed++
					waiting = false
				}
			case <-budget.Done():
				t.Fatal("no completion before EOF", completed)
			}
		}
	}
	stdin.Close()
	err = cmd.Wait()
	<-scanDone
	waited = true
	code := 0
	if err != nil {
		if e, ok := err.(*exec.ExitError); ok {
			code = e.ExitCode()
		} else {
			t.Fatal(err)
		}
	}
	lock.Lock()
	defer lock.Unlock()
	wire, _ := json.MarshalIndent(map[string]any{"requests_base64": requests, "responses_base64": responses}, "", "  ")
	invocation, _ := json.MarshalIndent(map[string]any{"actualargv": cmd.Args, "cwd": func() string { s, _ := os.Getwd(); return s }(), "exit_code": code, "completed_before_EOF": completed, "mode": "FIXTURE_PROTOCOL_NOT_MODEL"}, "", "  ")
	for name, body := range map[string][]byte{"stdout.jsonl": output.Bytes(), "stderr.txt": stderr.Bytes(), "wire.json": wire, "invocation.json": invocation, "config.before.json": initial} {
		os.WriteFile(filepath.Join(dir, name), body, 0600)
	}
	saved, _ := os.ReadFile(config)
	os.WriteFile(filepath.Join(dir, "config.after.json"), saved, 0600)
	if code != 0 || createCount != 1 || sendCount != 2 || completed != 2 {
		t.Fatal("logical input counts", code, createCount, sendCount, completed)
	}
	var sends []map[string]any
	for _, raw := range requests {
		var env map[string]any
		json.Unmarshal(raw, &env)
		if env["method"] == "session.attach" {
			t.Fatal("redundant acquire after valid own create")
		}
		if env["method"] == "session.send" {
			sends = append(sends, env)
		}
	}
	if len(sends) != 2 || sends[0]["command_id"] == sends[1]["command_id"] || cliObject(sends[0]["payload"])["text"] != "first \nquestion" || cliObject(sends[1]["payload"])["text"] != "second \nquestion" {
		t.Fatal("multiline original identity/text", sends)
	}
}
