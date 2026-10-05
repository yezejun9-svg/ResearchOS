package api

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// Only the host binding port is a fixture. HTTP validation, authentication,
// transaction, Goal/Task/Context, idempotency and events are the production code.
// This fixture deliberately grants no LIVE runtime qualification.
type sessionBindingFixture struct{}

func (sessionBindingFixture) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, _, model string) error {
	if model != "model-test" {
		return domain.Fail(422, "MODEL_UNAVAILABLE", "unknown fixture model binding")
	}
	return nil
}
func (sessionBindingFixture) AdmitTurn(_ context.Context, _ *sql.Tx, _, _ string, _ domain.Object) error {
	return domain.Fail(503, "RESOURCE_UNAVAILABLE", "no qualified runtime in this HTTP fixture")
}

type sessionHTTPFixture struct {
	db                        *sql.DB
	svc                       *domain.Service
	server                    *httptest.Server
	token, project, workspace string
}

func newSessionHTTPFixture(t *testing.T) *sessionHTTPFixture {
	t.Helper()
	ctx := context.Background()
	db, err := store.Open(filepath.Join(t.TempDir(), "sessions.sqlite"))
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
	if err = domain.EnsureClientSessionFence(ctx, db); err != nil {
		t.Fatal(err)
	}
	if err = svc.ProvisionPrincipal(ctx, domain.Principal{ID: "session-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	token, err := svc.IssueCredential(ctx, "session-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	f := &sessionHTTPFixture{db: db, svc: svc, token: token, workspace: "workspace-test"}
	f.server = httptest.NewServer(HandlerWithClientRuntime(db, t.TempDir(), svc, sessionBindingFixture{}))
	t.Cleanup(f.server.Close)
	profile := domain.Object{"name": "Session HTTP fixture", "intent": "One finite message", "facts": domain.Empty(), "accepted_scope": []any{"session fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	request, _ := http.NewRequest("POST", f.server.URL+"/v1/projects", bytes.NewReader(domain.Bytes(profile)))
	request.Header.Set("Authorization", "Bearer "+token)
	request.Header.Set("Idempotency-Key", domain.ID())
	resp, err := f.server.Client().Do(request)
	if err != nil {
		t.Fatal(err)
	}
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()
	if resp.StatusCode != 201 {
		t.Fatalf("create project: %d %s", resp.StatusCode, body)
	}
	var project domain.Object
	if err = json.Unmarshal(body, &project); err != nil {
		t.Fatal(err)
	}
	f.project = project["project_id"].(string)
	// Existing workspace-authority fact; no filesystem chooser is exercised here.
	binding := domain.WorkspaceBinding{AuthorizedRef: f.workspace, DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "session-owner", ClientID: "client-one", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, err = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, f.workspace, string(domain.Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	return f
}
func (f *sessionHTTPFixture) call(t *testing.T, token string, env domain.Object) domain.Object {
	t.Helper()
	req, _ := http.NewRequest("POST", f.server.URL+"/v2/command", bytes.NewReader(domain.Bytes(env)))
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := f.server.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	var out domain.Object
	if err = json.Unmarshal(raw, &out); err != nil {
		t.Fatalf("%s: %v", raw, err)
	}
	if resp.StatusCode >= 500 {
		t.Fatalf("server failure: %d %s", resp.StatusCode, raw)
	}
	return out
}
func (f *sessionHTTPFixture) envelope(method, key string, payload domain.Object) domain.Object {
	return domain.Object{"protocol_version": domain.ProtocolV2, "command_id": key, "client_id": "client-one", "project_id": f.project, "session_id": nil, "expected_revision": nil, "writer_epoch": nil, "method": method, "payload": payload}
}
func sessionResult(t *testing.T, r domain.Object) domain.Object {
	t.Helper()
	if r["status"] != "COMPLETED" {
		t.Fatalf("unexpected response %s", domain.Bytes(r))
	}
	return r["result"].(map[string]any)
}
func (f *sessionHTTPFixture) create(t *testing.T, key string) domain.Object {
	return sessionResult(t, f.call(t, f.token, f.envelope("session.create", key, domain.Object{"workspace_ref": f.workspace, "model_config_ref": "model-test", "title": "Finite turn"})))
}

func TestW14SessionHTTPCreateSendEventsAndReplay(t *testing.T) {
	f := newSessionHTTPFixture(t)
	snap := f.create(t, "create-one")
	sid := snap["session_id"]
	if again := f.create(t, "create-one"); again["session_id"] != sid {
		t.Fatal("create replay minted another session")
	}
	list := sessionResult(t, f.call(t, f.token, f.envelope("session.list", "list-one", domain.Object{"cursor": nil, "limit": 20})))
	if len(list["items"].([]any)) != 1 {
		t.Fatal(list)
	}
	env := f.envelope("session.send", "send-one", domain.Object{"text": "请只完成这一轮回答。", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	env["session_id"] = sid
	env["expected_revision"] = snap["revision"]
	env["writer_epoch"] = snap["writer"].(map[string]any)["epoch"]
	sent := f.call(t, f.token, env)
	result := sessionResult(t, sent)
	if result["run_id"] != nil {
		t.Fatal("unqualified turn fabricated a run")
	}
	if replay := f.call(t, f.token, env); !bytes.Equal(domain.Bytes(replay), domain.Bytes(sent)) {
		t.Fatal("send replay changed response")
	}
	var count int
	var taskBody string
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", f.project).Scan(&count); err != nil || count != 1 {
		t.Fatalf("task count %d %v", count, err)
	}
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Task'", f.project).Scan(&taskBody); err != nil {
		t.Fatal(err)
	}
	var task domain.Object
	json.Unmarshal([]byte(taskBody), &task)
	if task["status"] != "BLOCKED" || task["task_type"] != "mu_turn" || task["context_bundle_id"] == nil {
		t.Fatalf("task not real bounded blocked work: %s", taskBody)
	}
	eventsEnv := f.envelope("session.events", "events-one", domain.Object{"after_sequence": 0, "limit": 20})
	eventsEnv["session_id"] = sid
	events := sessionResult(t, f.call(t, f.token, eventsEnv))["events"].([]any)
	if len(events) != 4 {
		t.Fatalf("want MESSAGE START/DELTA/END and blocked ERROR, got %s", domain.Bytes(events))
	}
	if events[1].(map[string]any)["payload"].(map[string]any)["text"] != "请只完成这一轮回答。" || events[3].(map[string]any)["kind"] != "ERROR" {
		t.Fatal(events)
	}
	get := f.envelope("session.get", "get-one", domain.Object{})
	get["session_id"] = sid
	after := sessionResult(t, f.call(t, f.token, get))
	if after["active_run_id"] != nil || len(after["messages"].([]any)) != 1 {
		t.Fatal(after)
	}
	// A v1 write after the typed messages must use the same authoritative outbox
	// sequence, rather than colliding with its independently numbered session tail.
	stateReq, _ := http.NewRequest("GET", f.server.URL+"/v1/projects/"+f.project+"/state", nil)
	stateReq.Header.Set("Authorization", "Bearer "+f.token)
	stateResp, err := f.server.Client().Do(stateReq)
	if err != nil {
		t.Fatal(err)
	}
	io.Copy(io.Discard, stateResp.Body)
	stateResp.Body.Close()
	entry := domain.Object{"requirement_key": "INTERLEAVED-HTTP", "text": "ordinary v1 event after typed events", "basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "outbox interleaving witness", "supersedes_id": nil, "acceptance_check_ids": domain.Empty()}
	writeReq, _ := http.NewRequest("POST", f.server.URL+"/v1/projects/"+f.project+"/requirements", bytes.NewReader(domain.Bytes(entry)))
	writeReq.Header.Set("Authorization", "Bearer "+f.token)
	writeReq.Header.Set("Idempotency-Key", domain.ID())
	writeReq.Header.Set("If-Match", stateResp.Header.Get("ETag"))
	writeResp, err := f.server.Client().Do(writeReq)
	if err != nil {
		t.Fatal(err)
	}
	writeRaw, _ := io.ReadAll(writeResp.Body)
	writeResp.Body.Close()
	if writeResp.StatusCode != http.StatusCreated {
		t.Fatalf("interleaved v1 write: %d %s", writeResp.StatusCode, writeRaw)
	}
	var max, unique, total, stateSequence int64
	if err = f.db.QueryRow("SELECT MAX(sequence),count(DISTINCT sequence),count(*) FROM outbox WHERE project=?", f.project).Scan(&max, &unique, &total); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT json_extract(body,'$.event_sequence') FROM domain_objects WHERE project=? AND kind='ProjectState'", f.project).Scan(&stateSequence); err != nil {
		t.Fatal(err)
	}
	if max != total || unique != total || stateSequence != max {
		t.Fatalf("shared sequence max=%d unique=%d count=%d state=%d", max, unique, total, stateSequence)
	}
}

func TestW14SessionHTTPAuthorityAndFrozenRequest(t *testing.T) {
	f := newSessionHTTPFixture(t)
	snap := f.create(t, "create-authority")
	base := func(key string) domain.Object {
		e := f.envelope("session.send", key, domain.Object{"text": "hello", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
		e["session_id"] = snap["session_id"]
		e["expected_revision"] = 1
		e["writer_epoch"] = 1
		return e
	}
	cases := []struct {
		name, code string
		mutate     func(domain.Object)
	}{
		{"epoch", "STALE_WRITER_EPOCH", func(e domain.Object) { e["writer_epoch"] = 2 }},
		{"revision", "VERSION_CONFLICT", func(e domain.Object) { e["expected_revision"] = 2 }},
		{"writer", "WRITER_BUSY", func(e domain.Object) { e["client_id"] = "other-client" }},
		{"project", "FORBIDDEN", func(e domain.Object) { e["project_id"] = "different-project" }},
		{"queue", "INVALID_REQUEST", func(e domain.Object) { e["payload"].(map[string]any)["delivery"] = "QUEUE" }},
		{"extra", "INVALID_REQUEST", func(e domain.Object) { e["payload"].(map[string]any)["runtime_id"] = "forged" }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			e := base("bad-" + tc.name)
			tc.mutate(e)
			r := f.call(t, f.token, e)
			if r["error_code"] != tc.code {
				t.Fatalf("want %s got %s", tc.code, domain.Bytes(r))
			}
		})
	}
	ctx := context.Background()
	if err := f.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "other-owner", Roles: []string{"OWNER"}, Grants: []domain.Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	other, err := f.svc.IssueCredential(ctx, "other-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	if r := f.call(t, other, base("other-principal")); r["error_code"] != "FORBIDDEN" {
		t.Fatal(r)
	}
	list := sessionResult(t, f.call(t, other, f.envelope("session.list", "other-list", domain.Object{"cursor": nil, "limit": 20})))
	if len(list["items"].([]any)) != 0 {
		t.Fatal("other principal can list private sessions")
	}
	var count int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Task'", f.project).Scan(&count)
	if count != 0 {
		t.Fatal("rejections created tasks")
	}
}

func TestW14SessionWriterLeaseHandoff(t *testing.T) {
	f := newSessionHTTPFixture(t)
	snapshot := f.create(t, "lease-create")
	if _, err := f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), snapshot["session_id"]); err != nil {
		t.Fatal(err)
	}
	send := f.envelope("session.send", "expired-send", domain.Object{"text": "finite message", "attachment_artifact_ids": domain.Empty(), "delivery": "NORMAL"})
	send["session_id"] = snapshot["session_id"]
	send["expected_revision"] = 1
	send["writer_epoch"] = 1
	if r := f.call(t, f.token, send); r["error_code"] != "LEASE_EXPIRED" {
		t.Fatal(r)
	}
	take := f.envelope("session.attach", "take-writer", domain.Object{"after_sequence": 0, "request_write_owner": true})
	take["session_id"] = snapshot["session_id"]
	take["client_id"] = "client-two"
	take["expected_revision"] = 1
	if r := f.call(t, f.token, take); r["status"] != "ACKNOWLEDGED" {
		t.Fatal(r)
	}
	get := f.envelope("session.get", "lease-get", domain.Object{})
	get["session_id"] = snapshot["session_id"]
	get["client_id"] = "client-two"
	after := sessionResult(t, f.call(t, f.token, get))
	writer := after["writer"].(map[string]any)
	expiry, err := time.Parse(time.RFC3339Nano, writer["expires_at"].(string))
	if err != nil || !expiry.After(time.Now()) || writer["epoch"] != float64(2) {
		t.Fatal(writer)
	}
	send["command_id"] = "fresh-send"
	send["client_id"] = "client-two"
	send["expected_revision"] = after["revision"]
	send["writer_epoch"] = writer["epoch"]
	sessionResult(t, f.call(t, f.token, send))
	var previous string
	if err = f.db.QueryRow("SELECT json_extract(body,'$.payload.previous_client_id') FROM outbox WHERE project=? AND json_extract(body,'$.kind')='CLIENT_HANDOFF'", f.project).Scan(&previous); err != nil || previous != "client-one" {
		t.Fatalf("handoff attribution %s %v", previous, err)
	}
}
