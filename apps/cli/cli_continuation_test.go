package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/api"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

type continuationFixture struct {
	db         *sql.DB
	svc        *domain.Service
	server     *httptest.Server
	c          *v2Context
	goal, task domain.Object
	snapshot   map[string]any
}

func newContinuationFixture(t *testing.T) *continuationFixture {
	t.Helper()
	ctx := context.Background()
	db, err := store.Open(filepath.Join(t.TempDir(), "continuation.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(raw)); err != nil {
		t.Fatal(err)
	}
	if err = svc.ProvisionPrincipal(ctx, domain.Principal{ID: "continuation-owner", Roles: []string{"OWNER", "PLANNER", "SCHEDULER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	token, err := svc.IssueCredential(ctx, "continuation-owner", 10*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	f := &continuationFixture{db: db, svc: svc, c: &v2Context{clientID: "continuation-cli", credential: token, commandID: "continuation-create"}}
	var configuredRef string
	f.server = httptest.NewServer(api.HandlerWithConfigurationHost(db, t.TempDir(), svc, cliSessionBindingFixture{configuredRef: &configuredRef}, "", nil, nil, cliConfigurationMetadataFixture{"continuation-owner"}))
	t.Cleanup(f.server.Close)
	f.c.baseURL = f.server.URL
	profile := f.call(t, "POST", "/v1/projects", domain.Object{"name": "Recovered original project", "intent": "Preserve original work", "facts": domain.Empty(), "accepted_scope": []any{"fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}, 201)
	f.c.projectID = profile["project_id"].(string)
	pid := f.c.projectID
	binding := domain.WorkspaceBinding{AuthorizedRef: "ws-continuation", DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &pid, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "continuation-owner", ClientID: f.c.clientID, HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, err = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, binding.AuthorizedRef, string(domain.Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	configuredRef = cliConfigureSessionFixture(t, f.c)
	steps, _, _ := verbSteps("run", []string{"Continue the original research"}, f.c, cliConfig{ProjectID: pid, WorkspaceRef: binding.AuthorizedRef, Model: configuredRef})
	for _, step := range steps {
		f.c.commandID = domain.ID()
		if reply, why, code := v2Call(f.c, step.method, step.payload); code != 0 {
			t.Fatalf("setup %s: %s %v", step.method, why, reply)
		}
	}
	f.c.commandID = domain.ID()
	f.refresh(t)
	f.goal = f.call(t, "GET", "/v1/projects/"+pid+"/goals/"+f.snapshot["goal_id"].(string), nil, 200)
	tasks := f.call(t, "GET", "/v1/projects/"+pid+"/tasks", nil, 200)["items"].([]any)
	f.task = tasks[0].(map[string]any)
	return f
}

func (f *continuationFixture) call(t *testing.T, method, path string, body domain.Object, status int) domain.Object {
	t.Helper()
	var input io.Reader
	if body != nil {
		input = bytes.NewReader(domain.Bytes(body))
	}
	req, err := http.NewRequest(method, f.server.URL+path, input)
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Authorization", "Bearer "+f.c.credential)
	if method != "GET" {
		req.Header.Set("Idempotency-Key", domain.ID())
		if body != nil && f.c.projectID != "" {
			var revision int64
			var err error
			if strings.HasSuffix(path, "/tasks") {
				err = f.db.QueryRow("SELECT revision FROM domain_objects WHERE project=? AND kind='Goal' AND id=?", f.c.projectID, body["goal_id"]).Scan(&revision)
			} else if strings.Contains(path, "/tasks/") {
				parts := strings.Split(path, "/")
				err = f.db.QueryRow("SELECT revision FROM domain_objects WHERE project=? AND kind='Task' AND id=?", f.c.projectID, parts[len(parts)-2]).Scan(&revision)
			} else {
				err = f.db.QueryRow("SELECT revision FROM domain_objects WHERE project=? AND kind='ProjectState'", f.c.projectID).Scan(&revision)
			}
			if err != nil {
				t.Fatal(err)
			}
			req.Header.Set("If-Match", fmt.Sprintf("\"r%d\"", revision))
		}
	}
	resp, err := f.server.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	if err != nil || resp.StatusCode != status {
		t.Fatalf("%s %s: %d %s %v", method, path, resp.StatusCode, raw, err)
	}
	var out domain.Object
	if err = json.Unmarshal(raw, &out); err != nil {
		t.Fatal(err)
	}
	return out
}

func (f *continuationFixture) refresh(t *testing.T) {
	t.Helper()
	reply, why, code := v2Call(f.c, "session.get", map[string]any{})
	if code != 0 {
		t.Fatalf("snapshot %s %v", why, reply)
	}
	f.snapshot = reply["result"].(map[string]any)
	if nested, ok := f.snapshot["snapshot"].(map[string]any); ok {
		f.snapshot = nested
	}
}

func (f *continuationFixture) stateDigest(t *testing.T) string {
	t.Helper()
	rows, err := f.db.Query("SELECT body FROM domain_objects ORDER BY project,kind,id")
	if err != nil {
		t.Fatal(err)
	}
	var bodies []string
	for rows.Next() {
		var body string
		if err = rows.Scan(&body); err != nil {
			t.Fatal(err)
		}
		bodies = append(bodies, body)
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	rows.Close()
	// The authority for effects and dispatches also includes relational tables.
	for _, table := range []string{"resource_effects", "runtime_dispatches", "outbox"} {
		var count int64
		if err := f.db.QueryRow("SELECT count(*) FROM " + table).Scan(&count); err != nil {
			t.Fatal(err)
		}
		bodies = append(bodies, fmt.Sprintf("%s:%d", table, count))
	}
	return domain.Hash(bodies)
}

func (f *continuationFixture) claimTask(t *testing.T) domain.Object {
	t.Helper()
	// These writes prepare a real development fixture before the read-only probe.
	rt := f.call(t, "POST", "/v1/projects/"+f.c.projectID+"/runtimes", domain.Object{"name": "continuation fixture runtime", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil}, 201)
	if err := f.svc.RegisterOrchestrationFixture(context.Background(), f.c.projectID, rt["id"].(string)); err != nil {
		t.Fatal(err)
	}
	task := f.addTask(t)
	var revision int64
	if err := f.db.QueryRow("SELECT revision FROM domain_objects WHERE project=? AND kind='ProjectState'", f.c.projectID).Scan(&revision); err != nil {
		t.Fatal(err)
	}
	bundle := f.call(t, "POST", "/v1/projects/"+f.c.projectID+"/context-bundles", domain.Object{"task_id": task["id"], "expected_project_state_revision": revision}, 201)
	base := "/v1/projects/" + f.c.projectID + "/tasks/" + task["id"].(string)
	f.call(t, "POST", base+"/actions", domain.Object{"action": "SUBMIT", "reason": "fixture setup"}, 200)
	executor := domain.ID()
	if err := f.svc.ProvisionPrincipal(context.Background(), domain.Principal{ID: executor, Roles: []string{"EXECUTOR"}}); err != nil {
		t.Fatal(err)
	}
	return f.call(t, "POST", base+"/claim", domain.Object{"runtime_id": rt["id"], "executor_principal_id": executor, "context_bundle_id": bundle["id"]}, 201)
}

func TestW18ContinuationActiveRunAndTerminalTasks(t *testing.T) {
	f := newContinuationFixture(t)
	claimed := f.claimTask(t)
	task := claimed["task"].(map[string]any)
	out := f.project(t, "ACTIVE_RUN", "UNIQUE")
	if out["next_step"].(map[string]any)["task_id"] != task["id"] {
		t.Fatal(out)
	}
	// Corrupt only the restored Run's task binding and prove fail-closed behavior.
	run := claimed["run"].(map[string]any)
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.task_id',?) WHERE kind='Run' AND id=?", f.task["id"], run["id"]); err != nil {
		t.Fatal(err)
	}
	if _, why, code := cliReadContinuation(f.c, f.snapshot); code == 0 || why != "CONTINUATION_SCOPE_MISMATCH" {
		t.Fatalf("run mismatch %s %d", why, code)
	}
	// Accepted and cancelled restored tasks are terminal regardless of saved refs.
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',CASE WHEN id=? THEN 'ACCEPTED' ELSE 'CANCELLED' END) WHERE kind='Task' AND project=?", f.task["id"], f.c.projectID); err != nil {
		t.Fatal(err)
	}
	out = f.project(t, "", "NONE")
	if len(out["unfinished_tasks"].([]any)) != 0 || out["next_step"] != nil {
		t.Fatal(out)
	}
}

func TestW18ContinuationTerminalRunDoesNotHideActive(t *testing.T) {
	for _, terminal := range []string{"SETTLED", "FAILED", "CANCELLED"} {
		t.Run(terminal, func(t *testing.T) {
			f := newContinuationFixture(t)
			claimed := f.claimTask(t)
			task := claimed["task"].(map[string]any)
			run := claimed["run"].(map[string]any)
			// API-created/claimed entities are given restored terminal state
			// before the real API read; this is not LIVE runtime settlement.
			taskStatus := map[string]string{"SETTLED": "EXECUTION_REPORTED", "FAILED": "FAILED", "CANCELLED": "BLOCKED"}[terminal]
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',?,'$.children_stopped',json('true'),'$.queue_empty',json('true'),'$.ended_at',?) WHERE kind='Run' AND id=?", terminal, domain.Now(), run["id"]); err != nil {
				t.Fatal(err)
			}
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',?) WHERE kind='Task' AND id=?", taskStatus, task["id"]); err != nil {
				t.Fatal(err)
			}
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','CANCELLED') WHERE kind='Task' AND id=?", f.task["id"]); err != nil {
				t.Fatal(err)
			}
			out := f.project(t, "CONTEXT_BUNDLE", "UNIQUE")
			if len(out["unfinished_tasks"].([]any)) != 1 {
				t.Fatal("terminal Run hid its unaccepted Task")
			}
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.context_bundle_id',NULL) WHERE kind='Task' AND id=?", task["id"]); err != nil {
				t.Fatal(err)
			}
			f.project(t, "ONLY_UNFINISHED_TASK", "UNIQUE")
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.context_bundle_id',?) WHERE kind='Task' AND id=?", task["context_bundle_id"], task["id"]); err != nil {
				t.Fatal(err)
			}
			current := f.claimTask(t)
			currentTask := current["task"].(map[string]any)
			currentRun := current["run"].(map[string]any)
			if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','RUNNING') WHERE kind='Run' AND id=?", currentRun["id"]); err != nil {
				t.Fatal(err)
			}
			out = f.project(t, "ACTIVE_RUN", "UNIQUE")
			if out["next_step"].(map[string]any)["task_id"] != currentTask["id"] || len(out["unfinished_tasks"].([]any)) != 2 {
				t.Fatalf("terminal history obscured current Run: %v", out)
			}
		})
	}
}

func TestW18ContinuationRunStatusClassification(t *testing.T) {
	f := newContinuationFixture(t)
	first := f.claimTask(t)
	run := first["run"].(map[string]any)
	for _, status := range []string{"QUEUED", "STARTING", "RUNNING", "CANCEL_REQUESTED", "LOST", "RECONCILING"} {
		if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',?) WHERE kind='Run' AND id=?", status, run["id"]); err != nil {
			t.Fatal(err)
		}
		f.project(t, "ACTIVE_RUN", "UNIQUE")
	}
	second := f.claimTask(t)
	secondRun := second["run"].(map[string]any)
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','RUNNING') WHERE kind='Run' AND id IN (?,?)", run["id"], secondRun["id"]); err != nil {
		t.Fatal(err)
	}
	out := f.project(t, "", "AMBIGUOUS")
	if out["next_step"] != nil {
		t.Fatal("two active Runs were arbitrarily ordered")
	}
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','UNKNOWN_RESTORED_STATUS') WHERE kind='Run' AND id=?", run["id"]); err != nil {
		t.Fatal(err)
	}
	before := f.stateDigest(t)
	out, why, code := cliReadContinuation(f.c, f.snapshot)
	// The real API rejects persisted unknown enums during response validation.
	if code == 0 || out["status"] != "UNAVAILABLE" || why != "CONTINUATION_HTTP_500" {
		t.Fatalf("unknown persisted Run status was not refused: %s %d %v", why, code, out)
	}
	if before != f.stateDigest(t) {
		t.Fatal("unknown Run status probe mutated product state")
	}
	t.Log(string(domain.Bytes(out)))
}

func TestW18ContinuationRealTaskPagination(t *testing.T) {
	f := newContinuationFixture(t)
	for i := 0; i < 100; i++ {
		f.addTask(t)
	}
	start := len(f.c.requestLog)
	out := f.project(t, "CONTEXT_BUNDLE", "UNIQUE")
	if len(out["unfinished_tasks"].([]any)) != 101 {
		t.Fatal("pagination lost unfinished tasks")
	}
	pages := 0
	for _, request := range f.c.requestLog[start:] {
		if strings.Contains(request, "/tasks?limit=100") {
			pages++
		}
	}
	if pages != 2 {
		t.Fatalf("task pages=%d", pages)
	}
}

func (f *continuationFixture) project(t *testing.T, source, selection string) map[string]any {
	t.Helper()
	before := f.stateDigest(t)
	start := len(f.c.requestLog)
	out, why, code := cliReadContinuation(f.c, f.snapshot)
	if code != 0 || why != "" || out["status"] != "AVAILABLE" || out["selection"] != selection {
		t.Fatalf("continuation: %s %d %v", why, code, out)
	}
	if source != "" && out["next_step"].(map[string]any)["source"] != source {
		t.Fatalf("wrong source: %v", out)
	}
	if out["session_id"] != f.c.sessionID || out["goal_id"] != f.goal["id"] || out["event_watermark"] != f.snapshot["event_sequence"] {
		t.Fatalf("original context lost: %v", out)
	}
	for _, request := range f.c.requestLog[start:] {
		if !strings.HasPrefix(request, "GET /v1/projects/"+f.c.projectID+"/") {
			t.Fatal(request)
		}
	}
	if before != f.stateDigest(t) {
		t.Fatal("projection changed domain objects including Tasks, Runs, costs or effects")
	}
	t.Log(string(domain.Bytes(out)))
	return out
}

func TestW18ContinuationOriginalContextReadOnly(t *testing.T) {
	f := newContinuationFixture(t)
	out := f.project(t, "CONTEXT_BUNDLE", "UNIQUE")
	if out["goal"].(map[string]any)["original_intent"] != f.goal["original_intent"] || out["next_step"].(map[string]any)["task_id"] != f.task["id"] {
		t.Fatal("lost original intent or pending task")
	}
	// Simulate a restored task with no saved bundle; it is only a pending item.
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.context_bundle_id',NULL) WHERE kind='Task' AND id=?", f.task["id"]); err != nil {
		t.Fatal(err)
	}
	f.project(t, "ONLY_UNFINISHED_TASK", "UNIQUE")
	// Reconstruct the saved continuation through the real ContextBundle API.
	var revision int64
	if err := f.db.QueryRow("SELECT revision FROM domain_objects WHERE project=? AND kind='ProjectState'", f.c.projectID).Scan(&revision); err != nil {
		t.Fatal(err)
	}
	f.call(t, "POST", "/v1/projects/"+f.c.projectID+"/context-bundles", domain.Object{"task_id": f.task["id"], "expected_project_state_revision": revision}, 201)
	f.project(t, "CONTEXT_BUNDLE", "UNIQUE")
}

func (f *continuationFixture) addTask(t *testing.T) domain.Object {
	t.Helper()
	body := domain.Object{}
	for _, key := range []string{"goal_id", "title", "task_type", "stage", "dependency_task_ids", "requirement_refs", "input_refs", "acceptance_contract", "stop_policy"} {
		body[key] = f.task[key]
	}
	body["origin_problem_id"] = f.goal["problem_ids"].([]any)[0]
	body["candidate_id"] = domain.ID()
	return f.call(t, "POST", "/v1/projects/"+f.c.projectID+"/tasks", body, 201)
}

func TestW18ContinuationAmbiguityAndCompleteness(t *testing.T) {
	f := newContinuationFixture(t)
	f.addTask(t)
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.context_bundle_id',NULL) WHERE kind='Task' AND id=?", f.task["id"]); err != nil {
		t.Fatal(err)
	}
	out := f.project(t, "", "AMBIGUOUS")
	if out["next_step"] != nil || len(out["unfinished_tasks"].([]any)) != 2 {
		t.Fatal(out)
	}
	// A damaged persisted membership must not silently lose work.
	if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.task_ids',json(?)) WHERE kind='Goal' AND id=?", string(domain.Bytes([]any{f.task["id"], "missing-task"})), f.goal["id"]); err != nil {
		t.Fatal(err)
	}
	_, why, code := cliReadContinuation(f.c, f.snapshot)
	if code == 0 || why != "CONTINUATION_INCOMPLETE_GOAL_TASKS" {
		t.Fatalf("missing membership accepted: %s %d", why, code)
	}
}

func TestW18ContinuationAuthorizationAndNoGoal(t *testing.T) {
	f := newContinuationFixture(t)
	count := len(f.c.requestLog)
	if out, _, code := cliReadContinuation(f.c, map[string]any{}); out != nil || code != 0 || count != len(f.c.requestLog) {
		t.Fatal("legacy status queried without a goal")
	}
	if err := f.svc.ProvisionPrincipal(context.Background(), domain.Principal{ID: "no-project", Roles: []string{"OWNER"}}); err != nil {
		t.Fatal(err)
	}
	token, err := f.svc.IssueCredential(context.Background(), "no-project", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	f.c.credential = token
	out, why, code := cliReadContinuation(f.c, f.snapshot)
	if code == 0 || why != "CONTINUATION_HTTP_404" || out["status"] != "UNAVAILABLE" || out["goal"] != nil {
		t.Fatalf("unauthorized continuation: %v %s", out, why)
	}
}

func TestW18ContinuationStatusProcess(t *testing.T) {
	if os.Getenv("RESEARCHOS_TEST_CONTINUATION_CHILD") == "1" {
		cliHostCommand("status", nil)
		return
	}
	f := newContinuationFixture(t)
	dir := t.TempDir()
	discoveryPath, configPath := filepath.Join(dir, "host.json"), filepath.Join(dir, "config.json")
	if err := os.WriteFile(discoveryPath, domain.Bytes(discovery{URL: f.server.URL}), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(configPath, domain.Bytes(cliConfig{ProjectID: f.c.projectID, SessionID: f.c.sessionID}), 0600); err != nil {
		t.Fatal(err)
	}
	run := func(wantCode int) map[string]any {
		t.Helper()
		ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
		defer cancel()
		cmd := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestW18ContinuationStatusProcess$")
		cmd.Env = append(os.Environ(), "RESEARCHOS_TEST_CONTINUATION_CHILD=1", "RESEARCHOS_CLI_DISCOVERY="+discoveryPath, "RESEARCHOS_CLI_CONFIG="+configPath, "RESEARCHOS_CLI_CREDENTIAL="+f.c.credential, "RESEARCHOS_CLI_CLIENT_ID="+f.c.clientID)
		raw, err := cmd.CombinedOutput()
		code := 0
		if err != nil {
			if exit, ok := err.(*exec.ExitError); ok {
				code = exit.ExitCode()
			} else {
				t.Fatal(err)
			}
		}
		if code != wantCode {
			t.Fatalf("exit=%d want=%d %s", code, wantCode, raw)
		}
		var out map[string]any
		if json.Unmarshal(bytes.Split(raw, []byte("\n"))[0], &out) != nil {
			t.Fatalf("bad JSONL: %s", raw)
		}
		t.Log(string(bytes.Split(raw, []byte("\n"))[0]))
		return out
	}
	before := f.stateDigest(t)
	out := run(0)
	operations := out["operations"].([]any)
	if len(operations) != 2 || operations[0].(map[string]any)["method"] != "session.get" || operations[1].(map[string]any)["method"] != "host.status" || out["continuation"].(map[string]any)["selection"] != "UNIQUE" {
		t.Fatal(out)
	}
	if before != f.stateDigest(t) {
		t.Fatal("status mutated product objects")
	}
	// Session snapshot still exists, but its original Goal cannot be read.
	if _, err := f.db.Exec("UPDATE client_sessions SET goal_id='missing-original-goal' WHERE id=?", f.c.sessionID); err != nil {
		t.Fatal(err)
	}
	out = run(exitFailed)
	if out["continuation"].(map[string]any)["status"] != "UNAVAILABLE" || out["reason"] != "CONTINUATION_HTTP_404" {
		t.Fatal(fmt.Sprint(out))
	}
}

// Fault-injected transport tests exercise limits; product recovery evidence is
// supplied separately by the real API/SQLite and CLI-process tests above.
func TestW18ContinuationTransportLimits(t *testing.T) {
	for _, mode := range []string{"oversize", "page-limit", "redirect", "timeout", "cross-project", "unknown-run-status"} {
		t.Run(mode, func(t *testing.T) {
			requests := 0
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				requests++
				switch mode {
				case "oversize":
					io.WriteString(w, strings.Repeat(" ", continuationReadLimit+1))
					return
				case "redirect":
					w.Header().Set("Location", "/credential-sink")
					w.WriteHeader(http.StatusTemporaryRedirect)
					return
				case "timeout":
					<-r.Context().Done()
					return
				}
				if strings.Contains(r.URL.Path, "/goals/") {
					project := "project-original"
					if mode == "cross-project" {
						project = "different-project"
					}
					ids := []any{}
					if mode == "unknown-run-status" {
						ids = []any{"task-original"}
					}
					json.NewEncoder(w).Encode(map[string]any{"id": "goal-original", "project_id": project, "task_ids": ids})
					return
				}
				if mode == "unknown-run-status" {
					if strings.Contains(r.URL.Path, "/runs/") {
						json.NewEncoder(w).Encode(map[string]any{"id": "run-original", "project_id": "project-original", "task_id": "task-original", "status": "UNKNOWN_HOST_STATUS"})
					} else {
						json.NewEncoder(w).Encode(map[string]any{"items": []any{map[string]any{"id": "task-original", "project_id": "project-original", "goal_id": "goal-original", "status": "RUNNING", "active_run_id": "run-original"}}, "next_cursor": nil})
					}
					return
				}
				json.NewEncoder(w).Encode(map[string]any{"items": []any{}, "next_cursor": fmt.Sprintf("cursor-%d", requests)})
			}))
			defer server.Close()
			c := &v2Context{baseURL: server.URL, credential: "transport-fixture", projectID: "project-original", sessionID: "session-original"}
			start := time.Now()
			out, reason, code := cliReadContinuation(c, map[string]any{"goal_id": "goal-original", "project_id": c.projectID, "session_id": c.sessionID, "event_sequence": 3})
			want := map[string]string{"oversize": "CONTINUATION_RESPONSE_TOO_LARGE", "page-limit": "CONTINUATION_PAGE_LIMIT", "redirect": "CONTINUATION_HTTP_307", "timeout": "CONTINUATION_READ_FAILED", "cross-project": "CONTINUATION_SCOPE_MISMATCH", "unknown-run-status": "CONTINUATION_INVALID_RUN_STATUS"}[mode]
			if code == 0 || out["status"] != "UNAVAILABLE" || reason != want {
				t.Fatalf("%s %d %v", reason, code, out)
			}
			if mode == "page-limit" && requests != 11 {
				t.Fatalf("unbounded page requests=%d", requests)
			}
			if mode == "redirect" && requests != 1 {
				t.Fatal("followed a credential-bearing redirect")
			}
			if mode == "timeout" && time.Since(start) > 10*time.Second {
				t.Fatal("exceeded whole-read budget")
			}
		})
	}
}
