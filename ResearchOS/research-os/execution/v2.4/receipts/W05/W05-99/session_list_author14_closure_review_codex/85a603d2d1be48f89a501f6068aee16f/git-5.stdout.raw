package api

import (
	"bytes"
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

// Only the host binding port is a fixture. HTTP validation, authentication,
// transaction, Goal/Task/Context, idempotency and events are the production code.
// This fixture deliberately grants no LIVE runtime qualification.
type sessionBindingFixture struct{ model string }

func (p *sessionBindingFixture) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, _, model string) error {
	if model != p.model {
		return domain.Fail(422, "MODEL_UNAVAILABLE", "unknown fixture model binding")
	}
	return nil
}
func (*sessionBindingFixture) AdmitTurn(_ context.Context, _ *sql.Tx, _, _ string, _ domain.Object) error {
	return domain.Fail(503, "RESOURCE_UNAVAILABLE", "no qualified runtime in this HTTP fixture")
}

// SYNTHETIC metadata port, common-platform transaction/HTTP fixture only.
// Real local SID/Host composition has separate Windows tests.
type sessionConfigurationFixture struct{}

func (sessionConfigurationFixture) ConfigurationMetadata(_ context.Context, principal, _ string, credential *string) (domain.ClientConfigurationMetadata, error) {
	if principal != "session-owner" || credential != nil {
		return domain.ClientConfigurationMetadata{}, domain.Fail(403, "FORBIDDEN", "synthetic metadata scope")
	}
	return domain.ClientConfigurationMetadata{OwnerHost: "host-123456789abc", Principal: principal}, nil
}

type sessionHTTPFixture struct {
	db                        *sql.DB
	svc                       *domain.Service
	server                    *httptest.Server
	token, project, workspace string
	model                     string
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
	runtimePort := &sessionBindingFixture{}
	f.server = httptest.NewServer(HandlerWithConfigurationHost(db, t.TempDir(), svc, runtimePort, "host-123456789abc", nil, nil, sessionConfigurationFixture{}))
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
	configure := f.envelope("host.configure", "configure-original", domain.Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})
	configure["project_id"] = nil
	f.model = sessionResult(t, f.call(t, f.token, configure))["model_config_ref"].(string)
	runtimePort.model = f.model
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
	return sessionResult(t, f.call(t, f.token, f.envelope("session.create", key, domain.Object{"workspace_ref": f.workspace, "model_config_ref": f.model, "title": "Finite turn"})))
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

// Session-list identity controls use the production API, transaction and SQLite.
// Only the two existing metadata/runtime ports are SYNTHETIC; no runtime starts.
type sessionListFixture struct {
	*sessionHTTPFixture
	dir, dbPath string
	calls       int
}
type sessionListRows struct {
	Schema  []string            `json:"schema"`
	Columns map[string][]string `json:"columns"`
	Tables  map[string][]string `json:"tables"`
}

func sessionListSave(t *testing.T, dir, name string, raw []byte) {
	t.Helper()
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	f, err := os.OpenFile(filepath.Join(dir, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.Write(raw); err != nil {
		f.Close()
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}
func sessionListJSON(t *testing.T, dir, name string, v any) {
	t.Helper()
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	sessionListSave(t, dir, name, b)
}
func sessionListDigest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func (f *sessionListFixture) request(t *testing.T, method, path, token string, raw []byte) (int, []byte) {
	t.Helper()
	f.calls++
	if f.calls > 16 {
		t.Fatal("registered per-leaf HTTP cap exhausted")
	}
	stem := fmt.Sprintf("http-%02d", f.calls)
	// Retain the actual bytes before handing them to the production decoder.
	sessionListSave(t, f.dir, stem+".request.raw", raw)
	sessionListJSON(t, f.dir, stem+".request.json", domain.Object{"method": method, "path": path, "bytes": len(raw), "sha256": sessionListDigest(raw), "authorization": "OMITTED_SYNTHETIC_TOKEN"})
	req, e := http.NewRequest(method, f.server.URL+path, bytes.NewReader(raw))
	if e != nil {
		t.Fatal(e)
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	if path == "/v1/projects" {
		req.Header.Set("Idempotency-Key", domain.ID())
	}
	resp, e := f.server.Client().Do(req)
	if e != nil {
		t.Fatal(e)
	}
	body, e := io.ReadAll(resp.Body)
	resp.Body.Close()
	if e != nil {
		t.Fatal(e)
	}
	sessionListSave(t, f.dir, stem+".response.raw", body)
	sessionListJSON(t, f.dir, stem+".response.json", domain.Object{"status": resp.StatusCode, "headers": resp.Header, "bytes": len(body), "sha256": sessionListDigest(body)})
	return resp.StatusCode, body
}
func (f *sessionListFixture) command(t *testing.T, token string, env domain.Object) (int, []byte) {
	t.Helper()
	return f.request(t, "POST", "/v2/command", token, domain.Bytes(env))
}
func sessionListServiceResponse(t *testing.T, env domain.Object, status int, raw []byte, wantStatus, code string) domain.Object {
	t.Helper()
	if status != 200 && status != 403 {
		t.Fatalf("service HTTP status=%d body=%s", status, raw)
	}
	var body domain.Object
	if e := json.Unmarshal(raw, &body); e != nil {
		t.Fatal(e)
	}
	doc, e := ClientProtocolDocument()
	if e != nil {
		t.Fatal(e)
	}
	if e = doc.ValidateDef("CommandResponse", body); e != nil {
		t.Fatalf("full response schema: %v %s", e, raw)
	}
	var res domain.Response
	if e = json.Unmarshal(raw, &res); e != nil {
		t.Fatal(e)
	}
	if e = domain.ValidateResultAgainstMethod(env["method"].(string), &res, doc); e != nil {
		t.Fatal(e)
	}
	if body["command_id"] != env["command_id"] || body["method"] != env["method"] || body["protocol_version"] != domain.ProtocolV2 || body["status"] != wantStatus {
		t.Fatalf("response identity/status: %s", raw)
	}
	if env["method"] != "session.create" && !reflect.DeepEqual(body["session_id"], env["session_id"]) {
		t.Fatalf("original context lost: %s", raw)
	}
	if code != "" && body["error_code"] != code {
		t.Fatalf("wanted %s: %s", code, raw)
	}
	if env["method"] == "session.list" && body["revision"] != nil {
		t.Fatal("list invented session revision")
	}
	return body
}
func sessionListShortResponse(t *testing.T, env domain.Object, status int, raw []byte, want int, code string) {
	t.Helper()
	if status != want {
		t.Fatalf("transport status=%d want=%d %s", status, want, raw)
	}
	var b domain.Object
	if e := json.Unmarshal(raw, &b); e != nil {
		t.Fatal(e)
	}
	// Existing writeTypedError is a separate short transport wrapper, not /2 CommandResponse.
	if len(b) != 1 {
		t.Fatalf("unexpected transport wrapper: %s", raw)
	}
	er, ok := b["error"].(map[string]any)
	if !ok || len(er) != 4 || er["code"] != code || er["retryable"] != false {
		t.Fatalf("short wrapper: %s", raw)
	}
	if msg, ok := er["message"].(string); !ok || msg == "" {
		t.Fatal("missing transport message")
	}
	wantCorrelation := env["command_id"]
	// DecodeEnvelope returns nil for an unknown root key; serve preserves its existing short wrapper.
	if code == "INVALID_REQUEST" {
		wantCorrelation = "unparsed-command"
	}
	if er["correlation_id"] != wantCorrelation {
		t.Fatalf("transport correlation=%v want=%v", er["correlation_id"], wantCorrelation)
	}
}
func newSessionListFixture(t *testing.T) *sessionListFixture {
	t.Helper()
	root := os.Getenv("RESEARCHOS_SESSION_LIST_EVIDENCE")
	if root == "" {
		root = t.TempDir()
	}
	dir := filepath.Join(root, strings.ReplaceAll(t.Name(), "/", "__"))
	if e := os.MkdirAll(dir, 0700); e != nil {
		t.Fatal(e)
	}
	dbPath := filepath.Join(t.TempDir(), "session-list.sqlite")
	db, e := store.Open(dbPath)
	if e != nil {
		t.Fatal(e)
	}
	f := &sessionListFixture{sessionHTTPFixture: &sessionHTTPFixture{db: db, workspace: "list-workspace"}, dir: dir, dbPath: dbPath}
	t.Cleanup(func() { f.closeEvidence(t) })
	ctx := context.Background()
	if e = store.Bootstrap(ctx, db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	f.svc, e = domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	if e = f.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "session-owner", Roles: []string{"OWNER"}, CanCreateProject: true}); e != nil {
		t.Fatal(e)
	}
	f.token, e = f.svc.IssueCredential(ctx, "session-owner", time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	runtimePort := &sessionBindingFixture{}
	f.server = httptest.NewServer(HandlerWithConfigurationHost(db, t.TempDir(), f.svc, runtimePort, "host-123456789abc", nil, nil, sessionConfigurationFixture{}))
	f.project = f.newProject(t)
	binding := domain.WorkspaceBinding{AuthorizedRef: f.workspace, DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "session-owner", ClientID: "client-one", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
	if _, e = db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, f.workspace, string(domain.Bytes(binding))); e != nil {
		t.Fatal(e)
	}
	env := f.envelope("host.configure", "list-configure", domain.Object{"config_revision": 1, "provider_id": "fixture-provider", "base_url": "https://fixture.invalid/v1", "model_id": "fixture-model", "credential_ref": nil})
	env["project_id"] = nil
	status, raw := f.command(t, f.token, env)
	body := sessionListServiceResponse(t, env, status, raw, "COMPLETED", "")
	f.model = body["result"].(map[string]any)["model_config_ref"].(string)
	runtimePort.model = f.model
	return f
}
func (f *sessionListFixture) newProject(t *testing.T) string {
	t.Helper()
	profile := domain.Object{"name": "Session list HTTP fixture", "intent": "Read session identities", "facts": domain.Empty(), "accepted_scope": []any{"session list fixture"}, "constraints": domain.Empty(), "source_configs": domain.Empty(), "source_document_refs": domain.Empty(), "read_snapshot_ids": domain.Empty()}
	status, raw := f.request(t, "POST", "/v1/projects", f.token, domain.Bytes(profile))
	if status != 201 {
		t.Fatalf("project %d %s", status, raw)
	}
	var out domain.Object
	if e := json.Unmarshal(raw, &out); e != nil {
		t.Fatal(e)
	}
	return out["project_id"].(string)
}
func (f *sessionListFixture) createSession(t *testing.T, key string) string {
	t.Helper()
	env := f.envelope("session.create", key, domain.Object{"workspace_ref": f.workspace, "model_config_ref": f.model, "title": "Read context fixture"})
	status, raw := f.command(t, f.token, env)
	body := sessionListServiceResponse(t, env, status, raw, "COMPLETED", "")
	return body["result"].(map[string]any)["session_id"].(string)
}
func (f *sessionListFixture) secondPrincipal(t *testing.T, granted bool) string {
	t.Helper()
	p := domain.Principal{ID: "list-reader", Roles: []string{"READER"}}
	if granted {
		p.Grants = []domain.Grant{{ProjectID: f.project}}
	}
	if e := f.svc.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	token, e := f.svc.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return token
}
func sessionListQuote(s string) string { return `"` + strings.ReplaceAll(s, `"`, `""`) + `"` }
func sessionListScanStrings(t *testing.T, db *sql.DB, query string) []string {
	t.Helper()
	rs, e := db.Query(query)
	if e != nil {
		t.Fatal(e)
	}
	defer rs.Close()
	cols, e := rs.Columns()
	if e != nil {
		t.Fatal(e)
	}
	out := []string{}
	for rs.Next() {
		vals := make([]any, len(cols))
		ptrs := make([]any, len(cols))
		for i := range vals {
			ptrs[i] = &vals[i]
		}
		if e = rs.Scan(ptrs...); e != nil {
			t.Fatal(e)
		}
		b, e := json.Marshal(vals)
		if e != nil {
			t.Fatal(e)
		}
		out = append(out, string(b))
	}
	if e = rs.Err(); e != nil {
		t.Fatal(e)
	}
	sort.Strings(out)
	return out
}
func sessionListCaptureRows(t *testing.T, db *sql.DB) sessionListRows {
	t.Helper()
	v := sessionListRows{Schema: sessionListScanStrings(t, db, "SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name"), Columns: map[string][]string{}, Tables: map[string][]string{}}
	rs, e := db.Query("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")
	if e != nil {
		t.Fatal(e)
	}
	names := []string{}
	for rs.Next() {
		var n string
		if e = rs.Scan(&n); e != nil {
			t.Fatal(e)
		}
		names = append(names, n)
	}
	if e = rs.Err(); e != nil {
		t.Fatal(e)
	}
	rs.Close()
	for _, n := range names {
		v.Columns[n] = sessionListScanStrings(t, db, "PRAGMA table_xinfo("+sessionListQuote(n)+")")
		cr, e := db.Query("PRAGMA table_xinfo(" + sessionListQuote(n) + ")")
		if e != nil {
			t.Fatal(e)
		}
		columns := []string{}
		for cr.Next() {
			var cid, nn, pk, hidden int
			var name, typ string
			var def any
			if e = cr.Scan(&cid, &name, &typ, &nn, &def, &pk, &hidden); e != nil {
				t.Fatal(e)
			}
			columns = append(columns, name)
		}
		if e = cr.Err(); e != nil {
			t.Fatal(e)
		}
		cr.Close()
		expr := []string{}
		for _, c := range columns {
			q := sessionListQuote(c)
			expr = append(expr, "typeof("+q+")", q)
		}
		rows, e := db.Query("SELECT " + strings.Join(expr, ",") + " FROM " + sessionListQuote(n))
		if e != nil {
			t.Fatal(e)
		}
		out := []string{}
		for rows.Next() {
			vals := make([]any, len(expr))
			ptrs := make([]any, len(vals))
			for i := range vals {
				ptrs[i] = &vals[i]
			}
			if e = rows.Scan(ptrs...); e != nil {
				t.Fatal(e)
			}
			cells := []any{}
			for i := 0; i < len(vals); i += 2 {
				typ := fmt.Sprint(vals[i])
				var raw string
				switch x := vals[i+1].(type) {
				case nil:
					raw = ""
				case string:
					raw = base64.StdEncoding.EncodeToString([]byte(x))
				case []byte:
					raw = base64.StdEncoding.EncodeToString(x)
				case int64:
					raw = strconv.FormatInt(x, 10)
				case float64:
					raw = strconv.FormatFloat(x, 'g', -1, 64)
				default:
					t.Fatalf("unhandled SQLite value %T", x)
				}
				cells = append(cells, []string{typ, raw})
			}
			out = append(out, string(domain.Bytes(cells)))
		}
		if e = rows.Err(); e != nil {
			t.Fatal(e)
		}
		rows.Close()
		sort.Strings(out)
		v.Tables[n] = out
	}
	return v
}
func sessionListDelta(t *testing.T, before, after sessionListRows, added bool) {
	t.Helper()
	if !reflect.DeepEqual(before.Schema, after.Schema) || !reflect.DeepEqual(before.Columns, after.Columns) || len(before.Tables) != len(after.Tables) {
		t.Fatal("schema changed during session.list")
	}
	for n, rows := range before.Tables {
		next := after.Tables[n]
		if added && (n == "idempotency" || n == "client_command_identities") {
			if len(next) != len(rows)+1 {
				t.Fatalf("%s row delta %d -> %d", n, len(rows), len(next))
			}
			counts := map[string]int{}
			for _, s := range next {
				counts[s]++
			}
			for _, s := range rows {
				counts[s]--
				if counts[s] < 0 {
					t.Fatalf("%s changed original row", n)
				}
			}
		} else if !reflect.DeepEqual(rows, next) {
			t.Fatalf("unexpected row multiset change in %s", n)
		}
	}
}
func (f *sessionListFixture) journal(t *testing.T, principal string, env domain.Object, original, response []byte) {
	t.Helper()
	decoded, e := domain.DecodeEnvelope(original)
	if e != nil {
		t.Fatal(e)
	}
	hash, e := decoded.ContentHash()
	if e != nil {
		t.Fatal(e)
	}
	var storedHash, body, headers, created, protocol, project, method, operation, ih string
	var status int
	e = f.db.QueryRow(`SELECT request_hash,status,body,headers,created_at FROM idempotency WHERE principal=? AND project=? AND operation=? AND key=?`, principal, env["project_id"], "v2:session.list", env["command_id"]).Scan(&storedHash, &status, &body, &headers, &created)
	if e != nil {
		t.Fatal(e)
	}
	var h map[string]any
	if e = json.Unmarshal([]byte(headers), &h); e != nil {
		t.Fatal(e)
	}
	encoded, ok := h["raw_envelope_base64"].(string)
	if !ok {
		t.Fatal("missing original private request")
	}
	b, e := base64.StdEncoding.Strict().DecodeString(encoded)
	if e != nil || !bytes.Equal(b, original) || storedHash != hash || status != 0 || created == "" {
		t.Fatal("journal original binding differs")
	}
	var stored, out any
	if e = json.Unmarshal([]byte(body), &stored); e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(response, &out); e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(stored, out) {
		t.Fatal("HTTP response differs from committed journal")
	}
	e = f.db.QueryRow(`SELECT protocol,project,method,operation,request_hash FROM client_command_identities WHERE principal=? AND command_id=?`, principal, env["command_id"]).Scan(&protocol, &project, &method, &operation, &ih)
	if e != nil {
		t.Fatal(e)
	}
	if protocol != domain.ProtocolV2 || project != env["project_id"] || method != "session.list" || operation != "v2:session.list" || ih != hash {
		t.Fatal("global identity differs from original request")
	}
	sessionListJSON(t, f.dir, fmt.Sprintf("journal-%02d.json", f.calls), domain.Object{"principal": principal, "project": project, "command_id": env["command_id"], "request_hash": hash, "status": status, "body": body, "headers": headers, "created_at": created, "protocol": protocol, "method": method, "operation": operation})
}

// readonlyCopyOpen is only for a fully closed, standalone evidence copy.
// URL.Path escapes spaces, non-ASCII characters and URI metacharacters.
func readonlyCopyOpen(path string) (*sql.DB, error) {
	absolute, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	uriPath := filepath.ToSlash(absolute)
	if !strings.HasPrefix(uriPath, "/") {
		uriPath = "/" + uriPath
	}
	u := url.URL{Scheme: "file", Path: uriPath}
	u.RawQuery = url.Values{"mode": {"ro"}, "immutable": {"1"}}.Encode()
	db, err := sql.Open("sqlite", u.String())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	if err = db.Ping(); err != nil {
		if closeErr := db.Close(); closeErr != nil {
			return nil, fmt.Errorf("open readonly copy: %v; close: %w", err, closeErr)
		}
		return nil, err
	}
	return db, nil
}

func (f *sessionListFixture) closeEvidence(t *testing.T) {
	t.Helper()
	if f.server != nil {
		f.server.Close()
	}
	if f.db == nil {
		return
	}
	open := sessionListCaptureRows(t, f.db)
	sessionListJSON(t, f.dir, "post-open.rows.json", open)
	fileHashes := func() map[string]any {
		out := map[string]any{}
		for _, s := range []string{"", "-wal", "-shm"} {
			b, e := os.ReadFile(f.dbPath + s)
			if os.IsNotExist(e) {
				out[s] = nil
			} else if e != nil {
				t.Error(e)
			} else {
				out[s] = domain.Object{"bytes": len(b), "sha256": sessionListDigest(b)}
			}
		}
		return out
	}
	sidecarsAbsent := func(path, receipt string) bool {
		facts := domain.Object{}
		absent := true
		for _, suffix := range []string{"-wal", "-shm"} {
			_, err := os.Lstat(path + suffix)
			if os.IsNotExist(err) {
				facts[suffix] = domain.Object{"exists": false, "error": nil}
			} else if err != nil {
				facts[suffix] = domain.Object{"exists": nil, "error": err.Error()}
				absent = false
				t.Error(err)
			} else {
				facts[suffix] = domain.Object{"exists": true, "error": nil}
				absent = false
				t.Errorf("standalone closed evidence has sidecar %s", path+suffix)
			}
		}
		sessionListJSON(t, f.dir, receipt, facts)
		return absent
	}
	sessionListJSON(t, f.dir, "before-close.files.json", fileHashes())
	if e := f.db.Close(); e != nil {
		t.Error(e)
		return
	}
	sessionListJSON(t, f.dir, "closed-original.files.json", fileHashes())
	if !sidecarsAbsent(f.dbPath, "closed-original.sidecars.json") {
		return
	}
	raw, e := os.ReadFile(f.dbPath)
	if e != nil {
		t.Error(e)
		return
	}
	// sessionListSave uses O_EXCL: never reuse an earlier evidence copy.
	sessionListSave(t, f.dir, "closed.sqlite", raw)
	closedPath := filepath.Join(f.dir, "closed.sqlite")
	if !sidecarsAbsent(closedPath, "closed-copy.before.sidecars.json") {
		return
	}
	db, e := readonlyCopyOpen(closedPath)
	if e != nil {
		t.Error(e)
		sidecarsAbsent(closedPath, "closed-copy.after.sidecars.json")
		return
	}
	var closed sessionListRows
	copySidecarsAbsent := false
	func() {
		defer func() {
			if e := db.Close(); e != nil {
				t.Error(e)
			}
			copySidecarsAbsent = sidecarsAbsent(closedPath, "closed-copy.after.sidecars.json")
		}()
		closed = sessionListCaptureRows(t, db)
	}()
	sessionListJSON(t, f.dir, "closed.rows.json", closed)
	equal := reflect.DeepEqual(open, closed)
	after, e := os.ReadFile(closedPath)
	if e != nil {
		t.Error(e)
	}
	byteEqual := bytes.Equal(raw, after)
	sessionListJSON(t, f.dir, "closed-proof.json", domain.Object{"all_table_schema_multisets_equal": equal, "closed_copy_bytes_unchanged_by_read": byteEqual, "closed_copy_sha256": sessionListDigest(after), "closed_copy_sidecars_absent": copySidecarsAbsent, "HTTP_calls_including_setup": f.calls, "SDK_worker_model_external_paid": 0, "fixture_ports": "SYNTHETIC_METADATA_AND_BINDING_ONLY", "case_failed": t.Failed()})
	if !equal || !byteEqual || !copySidecarsAbsent {
		t.Error("closed SQLite evidence drift")
	}
}

func TestSessionListHTTPOriginalContextIdentity(t *testing.T) {
	names := []string{"NullContext", "OwnedContext", "ContextNotResultFilter", "ExactReplayAfterCommit", "ChangedPayloadConflict", "ChangedSIDConflict", "CrossProjectContext", "ForeignPrincipalContext", "ForeignPrincipalNullList", "UnknownContext", "ProjectGrantDenied", "CrossProjectCursor", "CrossPrincipalCursor", "MalformedRequest"}
	for _, name := range names {
		if !t.Run(name, func(t *testing.T) {
			f := newSessionListFixture(t)
			ids := []string{f.createSession(t, "list-create-a"), f.createSession(t, "list-create-b")}
			sort.Strings(ids)
			env := f.envelope("session.list", "list-original", domain.Object{"cursor": nil, "limit": 20})
			env["session_id"] = ids[1]
			token, principal := f.token, "session-owner"
			httpWant, wantStatus, code := 200, "COMPLETED", ""
			added := true
			short := false
			switch name {
			case "NullContext":
				env["session_id"] = nil
			case "OwnedContext":
				env["client_id"] = "same-principal-readonly-client"
			case "ContextNotResultFilter":
				env["payload"].(domain.Object)["limit"] = 1
			case "ForeignPrincipalContext":
				token = f.secondPrincipal(t, true)
				principal = "list-reader"
				wantStatus, code = "REJECTED", "FORBIDDEN"
			case "ForeignPrincipalNullList":
				token = f.secondPrincipal(t, true)
				principal = "list-reader"
				env["session_id"] = nil
			case "UnknownContext":
				env["session_id"] = "never-created-session"
				wantStatus, code = "REJECTED", "NOT_FOUND"
			case "ProjectGrantDenied":
				token = f.secondPrincipal(t, false)
				principal = "list-reader"
				httpWant, wantStatus, code, added = 403, "REJECTED", "FORBIDDEN", false
			case "CrossProjectContext":
				env["project_id"] = f.newProject(t)
				wantStatus, code = "REJECTED", "NOT_FOUND"
			case "CrossProjectCursor", "CrossPrincipalCursor":
				ce := f.envelope("session.list", "cursor-source", domain.Object{"cursor": nil, "limit": 1})
				cs, cr := f.command(t, f.token, ce)
				cb := sessionListServiceResponse(t, ce, cs, cr, "COMPLETED", "")
				cursor := cb["result"].(map[string]any)["next_cursor"]
				if cursor == nil {
					t.Fatal("real cursor prerequisite missing")
				}
				if name == "CrossProjectCursor" {
					f.project = f.newProject(t)
					f.workspace = "list-workspace-b"
					binding := domain.WorkspaceBinding{AuthorizedRef: f.workspace, DisplayName: "fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: domain.WorkspaceActive, PrincipalID: "session-owner", ClientID: "client-one", HostPrincipalRef: "fixture-local-user", CreatedAt: domain.Now()}
					if _, e := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, domain.KindWorkspaceBinding, f.workspace, string(domain.Bytes(binding))); e != nil {
						t.Fatal(e)
					}
					env["session_id"] = f.createSession(t, "project-b-session")
					env["project_id"] = f.project
				} else {
					token = f.secondPrincipal(t, true)
					principal = "list-reader"
					env["session_id"] = nil
				}
				env["payload"].(domain.Object)["cursor"] = cursor
				wantStatus, code = "REJECTED", "CURSOR_INVALID"
			case "MalformedRequest":
				env["unknown_context_override"] = "not-authority"
				httpWant, code, added, short = 400, "INVALID_REQUEST", false, true
			}
			// Fixture mutations and cursor preparation are complete before this baseline.
			before := sessionListCaptureRows(t, f.db)
			sessionListJSON(t, f.dir, "target.before.rows.json", before)
			original := domain.Bytes(env)
			status, raw := f.request(t, "POST", "/v2/command", token, original)
			if status != httpWant {
				t.Fatalf("target HTTP=%d want=%d %s", status, httpWant, raw)
			}
			var body domain.Object
			if short {
				sessionListShortResponse(t, env, status, raw, httpWant, code)
			} else {
				body = sessionListServiceResponse(t, env, status, raw, wantStatus, code)
			}
			after := sessionListCaptureRows(t, f.db)
			sessionListJSON(t, f.dir, "target.after.rows.json", after)
			sessionListDelta(t, before, after, added)
			if added {
				f.journal(t, principal, env, original, raw)
			}
			if wantStatus == "COMPLETED" && !short {
				items := body["result"].(map[string]any)["items"].([]any)
				switch name {
				case "ForeignPrincipalNullList":
					if len(items) != 0 {
						t.Fatal("foreign principal saw private session")
					}
				case "ContextNotResultFilter":
					if len(items) != 1 || items[0].(map[string]any)["session_id"] != ids[0] || body["session_id"] != ids[1] {
						t.Fatal("context adopted result scope or filtered list")
					}
				default:
					if len(items) != 2 {
						t.Fatalf("own list item count=%d", len(items))
					}
					for i, item := range items {
						if item.(map[string]any)["session_id"] != ids[i] {
							t.Fatal("list ordering or ownership differs")
						}
					}
				}
			}
			if name == "ExactReplayAfterCommit" || name == "ChangedPayloadConflict" || name == "ChangedSIDConflict" {
				if name == "ChangedPayloadConflict" {
					env["payload"].(domain.Object)["limit"] = 1
				}
				if name == "ChangedSIDConflict" {
					env["session_id"] = ids[0]
				}
				nextRaw := original
				if name != "ExactReplayAfterCommit" {
					nextRaw = domain.Bytes(env)
					origEnv, e := domain.DecodeEnvelope(original)
					if e != nil {
						t.Fatal(e)
					}
					nextEnv, e := domain.DecodeEnvelope(nextRaw)
					if e != nil {
						t.Fatal(e)
					}
					a, e := origEnv.ContentHash()
					if e != nil {
						t.Fatal(e)
					}
					b, e := nextEnv.ContentHash()
					if e != nil || a == b {
						t.Fatal("changed request did not change semantic content hash")
					}
				}
				status2, raw2 := f.request(t, "POST", "/v2/command", token, nextRaw)
				if name == "ExactReplayAfterCommit" {
					sessionListServiceResponse(t, env, status2, raw2, "COMPLETED", "")
					if status2 != status || !bytes.Equal(raw, raw2) {
						t.Fatal("committed original replay changed wire bytes")
					}
				} else {
					sessionListShortResponse(t, env, status2, raw2, 409, "COMMAND_ID_CONFLICT")
				}
				replay := sessionListCaptureRows(t, f.db)
				sessionListJSON(t, f.dir, "replay.after.rows.json", replay)
				sessionListDelta(t, after, replay, false)
			}
			sessionListJSON(t, f.dir, "assertions.json", domain.Object{"case": name, "target_HTTP": status, "original_request_sha256": sessionListDigest(original), "original_request_bytes": len(original), "wire": "FULL_SERVICE_SCHEMA_EXCEPT_L05_L06_CONFLICT_AND_L14_SHORT_TRANSPORT", "all_assertions_reached": true, "HTTP_calls_including_setup": f.calls})
		}) {
			return
		}
	}
}
