package domain

import (
	"bufio"
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type fixture struct {
	s                     *Service
	h                     http.Handler
	token, owner, project string
	db                    *sql.DB
	t                     *testing.T
}

// Connect before sending any fixture business request. Windows loopback can
// transiently reject a newly opened listener; never replay a submitted request.
func fixtureConnect(t *testing.T, server *httptest.Server) net.Conn {
	t.Helper()
	var last error
	for attempt := 1; attempt <= 3; attempt++ {
		conn, err := net.DialTimeout("tcp", server.Listener.Addr().String(), 2*time.Second)
		if err == nil {
			return conn
		}
		last = err
		t.Logf("fixture connection attempt %d failed: %v", attempt, err)
	}
	t.Fatalf("fixture listener unavailable after three connection attempts: %v", last)
	return nil
}

func fixtureHTTPProbe(client *http.Client, url string) (Object, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	probe, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
	response, err := client.Do(probe)
	entry := Object{"url": url, "status": nil, "error": nil}
	if err == nil {
		entry["status"] = response.StatusCode
		_, err = io.Copy(io.Discard, response.Body)
		response.Body.Close()
	}
	if err != nil {
		entry["error"] = err.Error()
	}
	return entry, err
}

// A child process cannot replace its parent's provider URL. Only its read-only
// probe may retry; the subsequent effect request remains single-shot.
func fixtureHTTPReady(t *testing.T, client *http.Client, url string) {
	t.Helper()
	for attempt := 1; attempt <= 3; attempt++ {
		entry, err := fixtureHTTPProbe(client, url)
		if err == nil {
			if entry["status"] != 404 {
				t.Fatalf("unexpected fixture readiness response: %v", entry)
			}
			return
		}
		t.Logf("fixture read-only probe %d: %v", attempt, err)
	}
	t.Fatal("fixture provider unavailable after three read-only probes")
}

// Windows can bind a loopback port that remains unreachable. Retry startup on
// fresh listeners before handing the URL to a caller; never replay business IO.
func fixtureHTTPServer(t *testing.T, handler http.Handler) (*httptest.Server, []any) {
	t.Helper()
	readiness := Empty()
	for attempt := 0; attempt < 3; attempt++ {
		server := httptest.NewServer(handler)
		url := server.URL + "/__researchos_fixture_readiness__"
		entry, err := fixtureHTTPProbe(server.Client(), url)
		entry["attempt"] = attempt + 1
		readiness = append(readiness, entry)
		if err == nil {
			if entry["status"] != 404 {
				server.Close()
				t.Fatalf("unexpected fixture readiness response: %v", entry)
			}
			return server, readiness
		}
		server.Close()
		t.Logf("fixture startup attempt %d failed before business IO: %v", attempt+1, err)
		if attempt == 2 {
			t.Fatalf("fixture unavailable after three fresh listeners: %v", err)
		}
	}
	return nil, readiness
}

func TestFixtureHTTPStartupRecovery(t *testing.T) {
	var probes, business atomic.Int32
	server, attempts := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			if probes.Add(1) == 1 {
				conn, _, err := w.(http.Hijacker).Hijack()
				if err == nil {
					conn.Close()
				}
				return
			}
			w.WriteHeader(404)
			return
		}
		business.Add(1)
		w.WriteHeader(200)
	}))
	defer server.Close()
	if len(attempts) != 2 || attempts[0].(map[string]any)["url"] == attempts[1].(map[string]any)["url"] || business.Load() != 0 {
		t.Fatalf("startup must replace only the failed listener before business IO: %v", attempts)
	}
	response, err := server.Client().Post(server.URL, "text/plain", strings.NewReader("single effect"))
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if response.StatusCode != 200 || business.Load() != 1 {
		t.Fatal("business request was not single-shot")
	}
}

func setup(t *testing.T) *fixture {
	return setupWithConstructor(t, New)
}

func setupWithConstructor(t *testing.T, construct func(*sql.DB, string, string) (*Service, error)) *fixture {
	t.Helper()
	db, e := store.Open(filepath.Join(t.TempDir(), "domain.sqlite"))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	s, e := construct(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	p := Principal{ID: "fixture-owner", Roles: []string{"OWNER"}, CanCreateProject: true}
	if e = s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	token, e := s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return &fixture{s: s, h: s.Handler(), token: token, owner: p.ID, db: db, t: t}
}
func (f *fixture) request(method, path, key, etag string, body any) (int, Object, http.Header) {
	f.t.Helper()
	var raw []byte
	if body != nil {
		switch v := body.(type) {
		case []byte:
			raw = v
		default:
			raw = Bytes(v)
		}
	}
	r := httptest.NewRequest(method, path, bytes.NewReader(raw))
	r.Header.Set("Authorization", "Bearer "+f.token)
	if key != "" {
		r.Header.Set("Idempotency-Key", key)
	}
	if etag != "" {
		r.Header.Set("If-Match", etag)
	}
	w := httptest.NewRecorder()
	f.h.ServeHTTP(w, r)
	w09ExportHTTP(f.t, method, path, key, etag, raw, w.Code, w.Body.Bytes(), w.Header().Get("ETag"), w.Header().Get("Content-Type"))
	var o Object
	json.Unmarshal(w.Body.Bytes(), &o)
	return w.Code, o, w.Header()
}
func (f *fixture) expect(status int, method, path, key, etag string, b any) Object {
	f.t.Helper()
	got, o, _ := f.request(method, path, key, etag, b)
	if got != status {
		f.t.Fatalf("%s %s: status %d want %d body %s", method, path, got, status, Bytes(o))
	}
	return o
}
func projectBody() Object {
	return Object{"name": "ResearchOS fixture", "intent": "verify foundation", "facts": Empty(), "accepted_scope": []any{"fixture"}, "constraints": Empty(), "source_configs": Empty(), "source_document_refs": Empty(), "read_snapshot_ids": Empty()}
}
func (f *fixture) createProject() Object {
	o := f.expect(201, "POST", "/v1/projects", ID(), "", projectBody())
	f.project = Str(o, "project_id")
	return o
}
func (f *fixture) path(s string) string { return "/v1/projects/" + f.project + s }
func (f *fixture) stateTag() string {
	return testTag(f.expect(200, "GET", f.path("/state"), "", "", nil))
}
func requirementBody() Object {
	return Object{"requirement_key": "REQ-1", "text": "persist fixture evidence", "basis": "USER_STATED", "source_refs": Empty(), "rationale": "explicit synthetic fixture", "supersedes_id": nil, "acceptance_check_ids": Empty()}
}
func (f *fixture) requirement() Object {
	o := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), requirementBody())
	return f.expect(200, "POST", f.path("/requirements/"+Str(o, "id")+"/actions"), ID(), testTag(o), Object{"action": "ACCEPT", "reason": "explicit fixture requirement", "source_validation_refs": Empty()})
}
func TestW03SchemaMigrationDefaults(t *testing.T) {
	f := setup(t)
	p := f.createProject()
	if p["project_id"] != p["id"] {
		t.Fatal("project identity mismatch")
	}
	for _, url := range []string{"/v1/policies/budget", f.path("/budget-policy")} {
		o := f.expect(200, "GET", url, "", "", nil)
		if o["cap"] != nil || o["mode"] != "UNLIMITED_AMOUNT" {
			t.Fatal(o)
		}
	}
	o := f.expect(200, "GET", f.path("/run-policy"), "", "", nil)
	if testNum(o, "max_concurrency") != 2 || testNum(o, "lease_seconds") != 90 {
		t.Fatal(o)
	}
	var count int
	migrations, err := filepath.Glob("../../migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql")
	if err != nil || len(migrations) == 0 {
		t.Fatal("missing migrations", err)
	}
	if e := f.db.QueryRow("SELECT count(*) FROM schema_migrations").Scan(&count); e != nil || count != len(migrations) {
		t.Fatal(count, e)
	}
	for _, migration := range migrations {
		var recorded int
		if err := f.db.QueryRow("SELECT count(*) FROM schema_migrations WHERE version=CAST(? AS INTEGER)", filepath.Base(migration)[:4]).Scan(&recorded); err != nil || recorded != 1 {
			t.Fatal("unrecorded migration", migration, err)
		}
	}
	if _, e := New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); e != nil {
		t.Fatal(e)
	}
	f.expect(400, "POST", "/v1/projects", ID(), "", []byte(`{"name":"a","name":"b"}`))
	b := projectBody()
	b["unexpected"] = true
	f.expect(400, "POST", "/v1/projects", ID(), "", b)
	if e := f.s.Contracts.Validate("UtcTime", "2026-02-30T00:00:00Z"); e == nil {
		t.Fatal("invalid date accepted")
	}
	if e := f.s.Contracts.Validate("Money", Object{"amount": 1.2, "currency": "USD"}); e == nil {
		t.Fatal("numeric amount accepted")
	}
	if e := f.s.Contracts.Validate("Money", Object{"amount": "12.50", "currency": "USD"}); e != nil {
		t.Fatal(e)
	}
}
func TestW03PreconditionReplayAuthorization(t *testing.T) {
	f := setup(t)
	f.createProject()
	b := requirementBody()
	f.expect(428, "POST", f.path("/requirements"), "", f.stateTag(), b)
	for _, key := range []string{strings.Repeat("k", 15), strings.Repeat("k", 161)} {
		f.expect(400, "POST", f.path("/requirements"), key, f.stateTag(), b)
	}
	f.expect(428, "POST", f.path("/requirements"), ID(), "", b)
	tag := f.stateTag()
	key := ID()
	first := f.expect(201, "POST", f.path("/requirements"), key, tag, b)
	status, replayed, h := f.request("POST", f.path("/requirements"), key, tag, b)
	if status != 201 || h.Get("Idempotency-Replayed") != "true" || Hash(first) != Hash(replayed) {
		t.Fatal(status, replayed, h)
	}
	f.expect(409, "POST", f.path("/requirements"), key, f.stateTag(), b)
	f.expect(412, "POST", f.path("/requirements"), ID(), tag, b)
	f.expect(400, "POST", f.path("/requirements"), ID(), "W/"+f.stateTag(), b)
	if e := f.s.RevokePrincipal(context.Background(), f.owner); e != nil {
		t.Fatal(e)
	}
	f.expect(401, "POST", f.path("/requirements"), key, tag, b)
}
func TestW03ConcurrentWriteOutboxRollback(t *testing.T) {
	f := setup(t)
	f.createProject()
	tag := f.stateTag()
	var wg sync.WaitGroup
	codes := make(chan int, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			status, _, _ := f.request("POST", f.path("/requirements"), ID(), tag, requirementBody())
			codes <- status
		}()
	}
	wg.Wait()
	close(codes)
	counts := map[int]int{}
	for c := range codes {
		counts[c]++
	}
	if counts[201] != 1 || counts[412] != 1 {
		t.Fatal(counts)
	}
	events, e := f.s.PendingEvents(context.Background(), f.project)
	if e != nil || len(events) != 2 {
		t.Fatal(len(events), e)
	}
	if testNum(events[1], "sequence") != 2 || events[0]["id"] == events[1]["id"] {
		t.Fatal(events)
	}
	if e = f.s.AcknowledgeEvent(context.Background(), f.project, Str(events[0], "id")); e != nil {
		t.Fatal(e)
	}
	if e = f.s.AcknowledgeEvent(context.Background(), f.project, Str(events[0], "id")); e != nil {
		t.Fatal(e)
	}
	bad := requirementBody()
	bad["source_refs"] = []any{Object{"entity_type": "Artifact", "id": "missing", "revision": 1, "content_hash": nil}}
	f.expect(422, "POST", f.path("/requirements"), ID(), f.stateTag(), bad)
	events, e = f.s.PendingEvents(context.Background(), f.project)
	if e != nil || len(events) != 1 {
		t.Fatal(events, e)
	}
	var n int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Requirement'").Scan(&n)
	if n != 1 {
		t.Fatal("partial business write", n)
	}
}
func TestW03ReferenceIsolationAndHistoricalHash(t *testing.T) {
	f := setup(t)
	f.createProject()
	a := f.requirement()
	projectA := f.project
	f.createProject()
	b := requirementBody()
	b["source_refs"] = []any{Ref(a, "Requirement")}
	f.expect(422, "POST", f.path("/requirements"), ID(), f.stateTag(), b)
	f.project = projectA
	b["source_refs"] = []any{Object{"entity_type": "Requirement", "id": a["id"], "revision": 1, "content_hash": nil}}
	f.expect(412, "POST", f.path("/requirements"), ID(), f.stateTag(), b)
	var n int
	f.db.QueryRow("SELECT count(*) FROM domain_refs WHERE target_kind='Requirement'").Scan(&n)
	if n == 0 {
		t.Fatal("no typed references")
	}
	if _, e := f.db.Exec("UPDATE domain_versions SET body='{}'"); e == nil {
		t.Fatal("immutable history overwritten")
	}
	if _, e := f.db.Exec("INSERT INTO domain_refs(project,kind,id,revision,field,target_project,target_kind,target_id,target_revision) VALUES('x','Task','x',1,'test','other','Goal','missing',1)"); e == nil {
		t.Fatal("foreign reference accepted")
	}
}
func TestW03ContentSealAccessAndImmutability(t *testing.T) {
	f := setup(t)
	f.createProject()
	f.expect(403, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{})
	p := Principal{ID: "fixture-executor", Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	owner := f.token
	f.token = token
	upload := f.expect(201, "POST", f.path("/content"), ID(), "", []byte("actual immutable bytes"))
	b := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "text/plain", "byte_size": upload["byte_size"], "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"}
	f.expect(422, "POST", f.path("/artifacts"), ID(), f.stateTag(), MergeCopy(b, Object{"byte_size": 1}))
	artifact := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), b)
	req := httptest.NewRequest("GET", f.path("/artifacts/"+Str(artifact, "id")+"/content"), nil)
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	f.h.ServeHTTP(w, req)
	if w.Code != 200 || w.Body.String() != "actual immutable bytes" || w.Header().Get("Digest") == "" || w.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatal(w.Code, w.Body.String(), w.Header())
	}
	if _, e = f.db.Exec("UPDATE uploaded_content SET bytes='different' WHERE storage_key=?", upload["storage_key"]); e == nil {
		t.Fatal("sealed bytes overwritten")
	}
	f.expect(403, "POST", f.path("/artifacts"), ID(), f.stateTag(), MergeCopy(b, Object{"access_class": "VERIFIER_ONLY"}))
	f.token = owner
	f.createProject()
	f.expect(404, "GET", f.path("/artifacts/"+Str(artifact, "id")), "", "", nil)
}

func TestW13AuthenticatedPrincipalHeader(t *testing.T) {
	f := setup(t)
	status, _, headers := f.request("GET", "/v1/projects", "", "", nil)
	if status != 200 || headers.Get("X-ResearchOS-Principal-ID") != f.owner {
		t.Fatal("authenticated caller identity unavailable", status, headers)
	}
	f.token = "invalid-credential"
	status, _, headers = f.request("GET", "/v1/projects", "", "", nil)
	if status != 401 || headers.Get("X-ResearchOS-Principal-ID") != "" {
		t.Fatal("unauthenticated response exposes identity", status, headers)
	}
}
func MergeCopy(o, b Object) Object {
	n := Object{}
	for k, v := range o {
		n[k] = v
	}
	return Merge(n, b)
}
func TestW03DeferredContractAndScope(t *testing.T) {
	f := setup(t)
	f.createProject()
	f.expect(400, "POST", f.path("/research-cycles"), ID(), f.stateTag(), Object{})
	p := Principal{ID: "reader", Roles: []string{"READER"}, Grants: []Grant{{ProjectID: f.project}}}
	f.s.ProvisionPrincipal(context.Background(), p)
	f.token, _ = f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	f.expect(403, "POST", f.path("/requirements"), ID(), f.stateTag(), requirementBody())
	f.expect(404, "GET", "/v1/projects/other/state", "", "", nil)
	for _, op := range f.s.Contracts.Operations {
		if op.Owner == "" {
			t.Fatal("unmapped", op)
		}
	}
}
func TestW03CursorSnapshotAndReceipt(t *testing.T) {
	f := setup(t)
	f.createProject()
	f.requirement()
	p := f.expect(200, "GET", f.path("/events?limit=1"), "", "", nil)
	cursor := Str(p, "next_cursor")
	if cursor == "" {
		t.Fatal("missing continuation")
	}
	f.requirement()
	page := f.expect(200, "GET", f.path("/events?limit=1&cursor="+cursor), "", "", nil)
	if page["snapshot_event_sequence"] != p["snapshot_event_sequence"] {
		t.Fatal("moving snapshot")
	}
	event := Arr(page, "items")[0].(map[string]any)
	if Receipt(event) != event["receipt_hash"] {
		t.Fatal("receipt hash mismatch")
	}
	f.createProject()
	f.expect(400, "GET", f.path("/events?cursor="+cursor), "", "", nil)
}

func TestW03GoalTaskDraftAndRefusals(t *testing.T) {
	f := setup(t)
	f.createProject()
	req := f.requirement()
	contract := Object{"contract_hash": Digest([]byte("fixture contract")), "contract_revision": 1, "checks": []any{Object{"check_id": "fixture-check", "kind": "DETERMINISTIC", "required": true, "expected": "actual evidence persists", "command_key": "test.domain", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "fixture goal", "original_intent": "persist actual records", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"origin-problem"}, "deliverables": []any{"fixture record"}, "acceptance_contract": contract})
	body := Object{"goal_id": goal["id"], "title": "fixture task", "task_type": "fixture", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": contract, "origin_problem_id": "origin-problem", "candidate_id": "candidate-one", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no effective progress"}}}
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), body)
	if task["context_bundle_id"] != nil || task["status"] != "DRAFT" || task["no_progress_record_id"] == nil {
		t.Fatal(task)
	}
	goal = f.expect(200, "GET", f.path("/goals/"+Str(goal, "id")), "", "", nil)
	second := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), body)
	if second["no_progress_record_id"] != task["no_progress_record_id"] {
		t.Fatal("counter reset")
	}
	actionURL := f.path("/tasks/" + Str(task, "id") + "/actions")
	f.expect(409, "POST", actionURL, ID(), testTag(task), Object{"action": "SUBMIT", "reason": "goal is not active"})
	f.expect(400, "POST", actionURL, ID(), testTag(task), Object{"action": "ACCEPTED", "reason": "forged completion"})
	cancelled := f.expect(200, "POST", actionURL, ID(), testTag(task), Object{"action": "CANCEL", "reason": "fixture cancellation"})
	f.expect(409, "POST", actionURL, ID(), testTag(cancelled), Object{"action": "RESUME", "reason": "illegal retry"})
}

func TestW03RestrictedMetadataPositiveAndNegative(t *testing.T) {
	f := setup(t)
	f.createProject()
	project := f.project
	// Synthetic metadata only: no formal holdout, labels or protected bytes exist in this fixture.
	a := Merge(Base(project), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "SIMULATED", "validity": "CURRENT", "measurement_mode": "FIXTURE", "content_hash": Digest(nil), "storage_key": "unbound-synthetic-metadata", "media_type": "application/json", "byte_size": 0, "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "sealed_at": Now(), "access_class": "VERIFIER_ONLY"})
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	if e = f.s.put(tx, "Artifact", a); e != nil {
		t.Fatal(e)
	}
	if e = f.s.event(tx, project, "Artifact", a, f.owner, ID(), "PROJECT_UPDATED"); e != nil {
		t.Fatal(e)
	}
	if e = tx.Commit(); e != nil {
		t.Fatal(e)
	}
	for _, role := range []string{"EXECUTOR", "PLANNER", "VERIFIER", "OWNER"} {
		p := Principal{ID: "restricted-fixture-" + role, Roles: []string{role}, Grants: []Grant{{ProjectID: project, Restricted: role == "VERIFIER" || role == "OWNER"}}}
		if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
			t.Fatal(e)
		}
		f.token, e = f.s.IssueCredential(context.Background(), p.ID, time.Minute)
		if e != nil {
			t.Fatal(e)
		}
		want := 404
		if p.Grants[0].Restricted {
			want = 200
		}
		f.expect(want, "GET", f.path("/artifacts/"+Str(a, "id")), "", "", nil)
		page := f.expect(200, "GET", f.path("/artifacts"), "", "", nil)
		if (len(Arr(page, "items")) == 1) != p.Grants[0].Restricted {
			t.Fatal(role, "artifact disclosure")
		}
		events := f.expect(200, "GET", f.path("/events"), "", "", nil)
		for _, v := range Arr(events, "items") {
			ev := v.(map[string]any)
			ref := ev["aggregate_ref"].(map[string]any)
			if ref["id"] == a["id"] && !p.Grants[0].Restricted {
				t.Fatal(role, "event disclosure")
			}
		}
		contentCode := 404
		if p.Grants[0].Restricted {
			contentCode = 503
		}
		f.expect(contentCode, "GET", f.path("/artifacts/"+Str(a, "id")+"/content"), "", "", nil)
		if role == "EXECUTOR" || role == "VERIFIER" {
			upload := f.expect(201, "POST", f.path("/content"), ID(), "", []byte("synthetic derivative"))
			b := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "text/plain", "byte_size": upload["byte_size"], "input_refs": []any{Ref(a, "Artifact")}, "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"}
			f.expect(403, "POST", f.path("/artifacts"), ID(), f.stateTag(), b)
			if role == "VERIFIER" {
				b["input_refs"] = Empty()
				b["access_class"] = "VERIFIER_ONLY"
				f.expect(503, "POST", f.path("/artifacts"), ID(), f.stateTag(), b)
			}
		}
	}
}

func TestW03OperationCoverage(t *testing.T) {
	f := setup(t)
	raw, e := os.ReadFile("../../contracts/operation_coverage.json")
	if e != nil {
		t.Fatal(e)
	}
	var manifest struct {
		Operations []struct {
			ID                   string `json:"operation_id"`
			Method, Path, Status string
			Owner                string `json:"owner_task"`
		}
	}
	if e = json.Unmarshal(raw, &manifest); e != nil {
		t.Fatal(e)
	}
	if len(manifest.Operations) != len(f.s.Contracts.Operations) || len(f.s.Contracts.Entities) != 31 {
		t.Fatal("incomplete contract inventory")
	}
	actual := map[string]Operation{}
	for _, op := range f.s.Contracts.Operations {
		actual[op.ID] = op
	}
	for _, entry := range manifest.Operations {
		op, ok := actual[entry.ID]
		if !ok || op.Method != entry.Method || op.Path != entry.Path || op.Owner != entry.Owner || op.Implemented != (entry.Status == "IMPLEMENTED_CORE") {
			t.Fatal("coverage drift", entry, op)
		}
	}
}

func testTag(o Object) string {
	v, e := ETag(o)
	if e != nil {
		panic(e)
	}
	return v
}
func testNum(o Object, k string) int64 {
	v, e := Num(o, k)
	if e != nil {
		panic(e)
	}
	return v
}

func TestW03ExactIntegerOverflow(t *testing.T) {
	for _, text := range []string{"1e21", "9223372036854775808", "-9223372036854775809", "1.5"} {
		if _, e := Num(Object{"n": json.Number(text)}, "n"); e == nil {
			t.Fatal("invalid integer silently converted", text)
		}
	}
	for text, want := range map[string]int64{"1e3": 1000, "1.0": 1} {
		o, e := Decode([]byte(`{"n":` + text + `}`))
		if e != nil {
			t.Fatal(e)
		}
		got, e := Num(o, "n")
		if e != nil || got != want {
			t.Fatal(text, got, e)
		}
	}
	if n, e := Num(Object{"n": json.Number("9223372036854775807")}, "n"); e != nil || n != 1<<63-1 {
		t.Fatal("exact integer parser lost signed maximum", n, e)
	}
	if _, e := Decode([]byte(`{"n":9223372036854775807}`)); e == nil {
		t.Fatal("canonical boundary accepted a lossy integer")
	}
	f := setup(t)
	f.createProject()
	p := Principal{ID: "overflow-fixture", Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	f.token, _ = f.s.IssueCredential(context.Background(), p.ID, time.Minute)
	upload := f.expect(201, "POST", f.path("/content"), ID(), "", []byte{})
	body := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "text/plain", "byte_size": json.Number("1e21"), "input_refs": Empty(), "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"}
	if e := f.s.Contracts.Validate("CreateArtifactRequest", body); e != nil {
		t.Fatal("fixture should be schema-valid", e)
	}
	before := f.stateTag()
	f.expect(400, "POST", f.path("/artifacts"), ID(), before, body)
	if after := f.stateTag(); after != before {
		t.Fatal("overflow changed state", before, after)
	}
	var count int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Artifact'").Scan(&count)
	if count != 0 {
		t.Fatal("overflow persisted artifact")
	}
	body["byte_size"] = json.Number("0e0")
	f.expect(201, "POST", f.path("/artifacts"), ID(), before, body)
}

func TestW03CursorQueryBinding(t *testing.T) {
	f := setup(t)
	f.createProject()
	f.requirement()
	page := f.expect(200, "GET", f.path("/events?limit=1&after_sequence=0"), "", "", nil)
	cursor := Str(page, "next_cursor")
	if cursor == "" {
		t.Fatal("fixture needs cursor")
	}
	next := f.expect(200, "GET", f.path("/events?cursor="+cursor+"&after_sequence=0&limit=1"), "", "", nil)
	if len(Arr(next, "items")) != 1 {
		t.Fatal("same normalized query did not resume")
	}
	f.expect(400, "GET", f.path("/events?limit=1&after_sequence=100&cursor="+cursor), "", "", nil)
}

func TestW03SlowBodyDoesNotBlockDatabase(t *testing.T) {
	f := setup(t)
	f.createProject()
	reading := make(chan struct{})
	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if e := store.Ready(r.Context(), f.db); e != nil {
			http.Error(w, "database unavailable", 503)
			return
		}
		w.WriteHeader(200)
	})
	mux.Handle("/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Fixture-Slow") == "true" {
			r.Body = &notifyReadBody{ReadCloser: r.Body, started: reading}
		}
		f.h.ServeHTTP(w, r)
	}))
	server := httptest.NewServer(mux)
	defer server.Close()
	conn := fixtureConnect(t, server)
	defer conn.Close()
	// Establish the independent reader before timing database responsiveness.
	readConn := fixtureConnect(t, server)
	defer readConn.Close()
	reader := bufio.NewReader(readConn)
	conn.SetDeadline(time.Now().Add(BodyReadTimeout + 3*time.Second))
	_, e := fmt.Fprintf(conn, "POST /v1/projects HTTP/1.1\r\nHost: fixture\r\nAuthorization: Bearer %s\r\nIdempotency-Key: %s\r\nX-Fixture-Slow: true\r\nContent-Length: 1000\r\n\r\n{", f.token, ID())
	if e != nil {
		t.Fatal(e)
	}
	select {
	case <-reading:
	case <-time.After(time.Second):
		t.Fatal("slow body never read")
	}
	for _, path := range []string{f.path("/state"), "/healthz"} {
		req, _ := http.NewRequest("GET", server.URL+path, nil)
		req.Header.Set("Authorization", "Bearer "+f.token)
		if e := readConn.SetDeadline(time.Now().Add(time.Second)); e != nil {
			t.Fatal(e)
		}
		if e := req.Write(readConn); e != nil {
			t.Fatal("independent read request failed", path, e)
		}
		response, e := http.ReadResponse(reader, req)
		if e != nil {
			t.Fatal("stalled body blocked independent read", path, e)
		}
		_, e = io.Copy(io.Discard, response.Body)
		response.Body.Close()
		if e != nil {
			t.Fatal("independent read body failed", path, e)
		}
		if response.StatusCode != 200 {
			t.Fatal(path, response.StatusCode)
		}
	}
	response, e := http.ReadResponse(bufio.NewReader(conn), nil)
	if e != nil {
		t.Fatal("body deadline failed to return bounded response", e)
	}
	defer response.Body.Close()
	if response.StatusCode != 400 {
		t.Fatal("stalled body not rejected", response.StatusCode)
	}
}

type notifyReadBody struct {
	io.ReadCloser
	started chan struct{}
	once    sync.Once
}

func (b *notifyReadBody) Read(p []byte) (int, error) {
	b.once.Do(func() { close(b.started) })
	return b.ReadCloser.Read(p)
}
