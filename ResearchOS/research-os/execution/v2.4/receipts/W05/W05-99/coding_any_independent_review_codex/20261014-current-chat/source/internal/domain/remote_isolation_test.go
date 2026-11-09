package domain

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"
)

const c02Private = "fixture_b_private_marker"
const c02Own = "fixture_a_authorized_material"
const c02Shared = "fixture_explicit_shared_knowledge"

type c02Audit struct {
	t                      *testing.T
	f                      *fixture
	file                   *os.File
	server                 *httptest.Server
	logs                   bytes.Buffer
	audience, role, action string
	responses, materials   []string
	requests, denials      int
	assertions             map[string]bool
}

func (a *c02Audit) record(o Object) {
	a.t.Helper()
	if _, e := fmt.Fprintln(a.file, string(Bytes(o))); e != nil {
		a.t.Fatal(e)
	}
}
func (a *c02Audit) assert(id string, expected, actual any) {
	a.t.Helper()
	status := "PASS"
	if a.assertions[id] || Hash(expected) != Hash(actual) {
		status = "FAIL"
	}
	a.assertions[id] = true
	o := Object{"record_type": "assertion", "assertion_id": id, "expected": expected, "actual": actual, "status": status, "mode": "FIXTURE"}
	a.record(o)
	fmt.Println("W17_C02_ASSERTION " + string(Bytes(o)))
	if status != "PASS" {
		a.t.Fatalf("C02 assertion failed: %s", id)
	}
}

// Every fixture helper request crosses a real loopback connection. The recorder
// here only adapts the existing test helpers to that HTTP client, not the app.
func c02Start(t *testing.T) *c02Audit {
	t.Helper()
	out := os.Getenv("W17_C02_EVIDENCE_DIR")
	if out == "" {
		out = t.TempDir()
	}
	if e := os.MkdirAll(out, 0700); e != nil {
		t.Fatal(e)
	}
	file, e := os.Create(filepath.Join(out, "audit.jsonl"))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { file.Close() })
	f := setup(t)
	a := &c02Audit{t: t, f: f, file: file, audience: "SETUP", role: "ADMIN", assertions: map[string]bool{}}
	server, ready := fixtureHTTPServer(t, f.s.Handler())
	a.server = server
	server.Config.ErrorLog = log.New(&a.logs, "", 0)
	t.Cleanup(server.Close)
	a.record(Object{"record_type": "listener", "transport": "REAL_LOOPBACK_HTTP", "url": server.URL, "readiness": ready})
	f.h = http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		raw, e := io.ReadAll(r.Body)
		if e != nil {
			t.Fatal(e)
		}
		req, e := http.NewRequest(r.Method, server.URL+r.URL.RequestURI(), bytes.NewReader(raw))
		if e != nil {
			t.Fatal(e)
		}
		req.Header = r.Header.Clone()
		redacted := req.Clone(context.Background())
		redacted.Header = req.Header.Clone()
		redacted.Header.Set("Authorization", "Bearer [REDACTED]")
		requestDump, e := httputil.DumpRequestOut(redacted, true)
		if e != nil {
			t.Fatal(e)
		}
		started := time.Now()
		response, e := server.Client().Do(req)
		if e != nil {
			t.Fatal(e)
		}
		defer response.Body.Close()
		body, e := io.ReadAll(response.Body)
		if e != nil {
			t.Fatal(e)
		}
		response.Body = io.NopCloser(bytes.NewReader(body))
		responseDump, e := httputil.DumpResponse(response, true)
		if e != nil {
			t.Fatal(e)
		}
		a.requests++
		if response.StatusCode == 403 || response.StatusCode == 404 {
			a.denials++
		}
		if a.audience == "A" {
			a.responses = append(a.responses, string(responseDump))
		}
		a.record(Object{"record_type": "http", "request_id": a.requests, "audience": a.audience, "role": a.role, "action": a.action, "method": r.Method, "path": r.URL.RequestURI(), "started_at": started.UTC().Format(time.RFC3339Nano), "finished_at": Now(), "elapsed_milliseconds": time.Since(started).Milliseconds(), "status": response.StatusCode, "raw_request": string(requestDump), "raw_response": string(responseDump), "response_body": string(body), "credential": "REDACTED"})
		for key, values := range response.Header {
			for _, value := range values {
				w.Header().Add(key, value)
			}
		}
		w.WriteHeader(response.StatusCode)
		w.Write(body)
	})
	return a
}

func c02Principal(t *testing.T, f *fixture, id, project string, roles []string) string {
	t.Helper()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: id, Roles: roles, Grants: []Grant{{ProjectID: project}}}); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), id, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return token
}
func (a *c02Audit) use(project, token, audience, role string) {
	a.f.project = project
	a.f.token = token
	a.audience = audience
	a.role = role
}
func (a *c02Audit) content(project, id string, status int) string {
	a.t.Helper()
	w := httptest.NewRecorder()
	r := httptest.NewRequest("GET", "/v1/projects/"+project+"/artifacts/"+id+"/content", nil)
	r.Header.Set("Authorization", "Bearer "+a.f.token)
	a.f.h.ServeHTTP(w, r)
	if w.Code != status {
		a.t.Fatalf("content status %d want %d: %s", w.Code, status, w.Body.String())
	}
	return w.Body.String()
}
func (a *c02Audit) search(project string, ids []any, query string, status int) Object {
	a.t.Helper()
	state := a.f.state()
	return a.f.expect(status, "POST", "/v1/projects/"+project+"/search", ID(), "", Object{"query": query, "snapshot_ids": ids, "limit": 20, "expected_state_revision": state["revision"]})
}
func c02Status(e error) int {
	if e == nil {
		return 200
	}
	if f, ok := e.(*Fault); ok {
		return f.Status
	}
	return 500
}

// Explicit sharing uses the existing trusted Owner import operation: only the
// selected public common directory is registered separately into A and B.
// Scope text documents provenance; registration and project-local copies are
// the authority, and this fixture adds no sharing schema or global grant.
func TestW17C02ProjectIsolation(t *testing.T) {
	a := c02Start(t)
	f := a.f
	ctx := context.Background()
	a.action = "create-same-name-projects"
	projectA := Str(f.createProject(), "project_id")
	projectB := Str(f.createProject(), "project_id")
	roles := []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}
	ownerA := c02Principal(t, f, "c02-owner-a", projectA, roles)
	ownerB := c02Principal(t, f, "c02-owner-b", projectB, roles)
	rootA, rootB, sharedRoot := t.TempDir(), t.TempDir(), t.TempDir()
	for path, body := range map[string]string{filepath.Join(rootA, "same-document.txt"): "Same study notes\n" + c02Own, filepath.Join(rootB, "same-document.txt"): "Same study notes\n" + c02Private} {
		if e := os.WriteFile(path, []byte(body), 0600); e != nil {
			t.Fatal(e)
		}
	}
	shared := Object{"knowledge": c02Shared, "source": "fixture://explicit-common-knowledge/shared-v1", "source_version": "1", "authorized_project_ids": []any{projectA, projectB}, "shared_knowledge_scope": []any{"fixture_project_a", "fixture_project_b"}}
	sharedRaw := Bytes(shared)
	if e := os.WriteFile(filepath.Join(sharedRoot, "shared.json"), sharedRaw, 0600); e != nil {
		t.Fatal(e)
	}
	type projectData struct {
		task, bundle, snapshot, shared Object
		root, common                   string
	}
	data := map[string]projectData{}
	for _, p := range []struct{ id, token, owner, root, audience string }{{projectA, ownerA, "c02-owner-a", rootA, "A"}, {projectB, ownerB, "c02-owner-b", rootB, "B_CONTROL"}} {
		a.use(p.id, p.token, p.audience, "OWNER")
		f.owner = p.owner
		a.action = "authorized-owner-import"
		root, e := f.s.RegisterLocalRoot(ctx, p.token, p.id, p.root)
		if e != nil {
			t.Fatal(e)
		}
		common, e := f.s.RegisterLocalRoot(ctx, p.token, p.id, sharedRoot)
		if e != nil {
			t.Fatal(e)
		}
		snapshot, e := f.s.CaptureLocalSnapshot(ctx, p.token, p.id, root, "same-document.txt")
		if e != nil {
			t.Fatal(e)
		}
		imported, e := f.s.CaptureLocalSnapshot(ctx, p.token, p.id, common, "shared.json")
		if e != nil {
			t.Fatal(e)
		}
		a.record(Object{"record_type": "trusted_local_import", "project_id": p.id, "principal_id": p.owner, "operations": []string{"RegisterLocalRoot", "CaptureLocalSnapshot"}, "common_root_id": common, "snapshot_ref": Ref(imported, "Artifact"), "source": shared["source"], "source_version": shared["source_version"], "authorized_project_ids": shared["authorized_project_ids"], "content_hash": Digest(sharedRaw), "status": 201})
		req := f.requirement()
		task := f.task(req, []any{Ref(snapshot, "Artifact"), Ref(imported, "Artifact")}, "same-task")
		bundle := f.bundle(task)
		data[p.id] = projectData{task, bundle, snapshot, imported, root, common}
	}
	pa, pb := data[projectA], data[projectB]
	a.use(projectB, ownerB, "B_CONTROL", "OWNER")
	a.action = "positive-private-marker-control"
	bBody := a.content(projectB, Str(pb.snapshot, "id"), 200)
	bHits := a.search(projectB, []any{pb.snapshot["id"]}, c02Private, 200)
	a.assert("W17-C02-SETUP-POSITIVE", []any{true, true, true, true}, []any{strings.Contains(bBody, c02Private), len(Arr(bHits, "hits")) > 0, pa.task["title"] == pb.task["title"], pa.snapshot["id"] != pb.snapshot["id"]})
	a.use(projectA, ownerA, "A", "OWNER")
	a.action = "shared-import-authority-negative"
	_, wrongProject := f.s.CaptureLocalSnapshot(ctx, ownerA, projectB, pb.common, "shared.json")
	_, wrongRoot := f.s.CaptureLocalSnapshot(ctx, ownerA, projectA, pb.common, "shared.json")
	_, outside := f.s.CaptureLocalSnapshot(ctx, ownerA, projectA, pa.root, filepath.Join(rootB, "same-document.txt"))
	_, traversal := f.s.CaptureLocalSnapshot(ctx, ownerA, projectA, pa.root, "../"+filepath.Base(rootB)+"/same-document.txt")
	a.record(Object{"record_type": "trusted_local_negative", "authority": "A-only Owner", "wrong_project_status": c02Status(wrongProject), "foreign_root_status": c02Status(wrongRoot), "absolute_B_path_status": c02Status(outside), "traversal_status": c02Status(traversal)})
	a.assert("W17-C02-SHARED-IMPORT-BOUNDARY", []any{403, 404, true, true}, []any{c02Status(wrongProject), c02Status(wrongRoot), pa.shared["id"] != pb.shared["id"], pa.shared["content_hash"] == pb.shared["content_hash"]})
	a.assert("W17-C02-PATH-DENIALS", []int{422, 422}, []int{c02Status(outside), c02Status(traversal)})
	before := c02ProjectDigest(t, f, projectB)
	for _, role := range []string{"READER", "PLANNER", "EXECUTOR"} {
		token := c02Principal(t, f, "c02-a-"+strings.ToLower(role), projectA, []string{role})
		a.use(projectA, token, "A", role)
		a.action = "A-positive-state-ID-list-download"
		state := f.state()
		task := f.read("tasks", Str(pa.task, "id"))
		artifact := f.read("artifacts", Str(pa.snapshot, "id"))
		projects := f.expect(200, "GET", "/v1/projects", "", "", nil)
		tasks := f.expect(200, "GET", f.path("/tasks"), "", "", nil)
		own := a.content(projectA, Str(pa.snapshot, "id"), 200)
		a.assert("W17-C02-"+role+"-A-POSITIVES", []any{projectA, pa.task["id"], pa.snapshot["id"], 1, true, true}, []any{state["project_id"], task["id"], artifact["id"], len(Arr(projects, "items")), len(Arr(tasks, "items")) > 0, strings.Contains(own, c02Own)})
		a.action = "B-known-ID-and-path-denials"
		denialsBefore := a.denials
		for _, path := range []string{"/v1/projects/" + projectB + "/state", "/v1/projects/" + projectB + "/tasks", "/v1/projects/" + projectB + "/tasks/" + Str(pb.task, "id"), "/v1/projects/" + projectB + "/artifacts/" + Str(pb.snapshot, "id"), "/v1/projects/" + projectB + "/context-bundles/" + Str(pb.bundle, "id"), f.path("/tasks/" + Str(pb.task, "id")), f.path("/artifacts/" + Str(pb.snapshot, "id")), f.path("/context-bundles/" + Str(pb.bundle, "id"))} {
			f.expect(404, "GET", path, "", "", nil)
		}
		a.content(projectB, Str(pb.snapshot, "id"), 404)
		a.content(projectA, Str(pb.snapshot, "id"), 404)
		a.search(projectB, []any{pb.snapshot["id"]}, c02Private, 404)
		a.search(projectA, []any{pb.snapshot["id"]}, c02Private, 404)
		state = f.state()
		f.expect(400, "POST", f.path("/search"), ID(), "", Object{"query": c02Private, "snapshot_ids": []any{pa.snapshot["id"]}, "limit": 20, "expected_state_revision": state["revision"], "path": filepath.Join(rootB, "same-document.txt")})
		a.assert("W17-C02-"+role+"-B-DENIALS", 12, a.denials-denialsBefore)
		a.action = "authorized-fulltext-and-shared-provenance"
		ownHits := a.search(projectA, []any{pa.snapshot["id"], pa.shared["id"]}, c02Own, 200)
		privateHits := a.search(projectA, []any{pa.snapshot["id"], pa.shared["id"]}, c02Private, 200)
		sharedHits := a.search(projectA, []any{pa.snapshot["id"], pa.shared["id"]}, c02Shared, 200)
		sharedBody := a.content(projectA, Str(pa.shared, "id"), 200)
		decoded, e := Decode([]byte(sharedBody))
		if e != nil {
			t.Fatal(e)
		}
		a.assert("W17-C02-"+role+"-SEARCH-SHARED", []any{true, 0, true, Hash(shared)}, []any{len(Arr(ownHits, "hits")) > 0, len(Arr(privateHits, "hits")), len(Arr(sharedHits, "hits")) > 0, Hash(decoded)})
		a.action = "context-build-read-and-materialize"
		state = f.state()
		createStatus := 403
		if role == "PLANNER" {
			createStatus = 201
		}
		f.expect(createStatus, "POST", f.path("/context-bundles"), ID(), testTag(state), Object{"task_id": pa.task["id"], "expected_project_state_revision": state["revision"]})
		task = f.read("tasks", Str(pa.task, "id"))
		bundle := f.read("context-bundles", Str(task, "context_bundle_id"))
		state = f.state()
		denyStatus := 403
		if role == "PLANNER" {
			denyStatus = 404
		}
		f.expect(denyStatus, "POST", f.path("/context-bundles"), ID(), testTag(state), Object{"task_id": pb.task["id"], "expected_project_state_revision": state["revision"]})
		folder := filepath.Join(t.TempDir(), "context")
		manifest, e := f.s.MaterializeTaskContext(ctx, token, projectA, Str(pa.task, "id"), folder)
		if e != nil {
			t.Fatal(e)
		}
		local := c02Materialized(t, a, folder, role)
		_, foreign := f.s.MaterializeTaskContext(ctx, token, projectB, Str(pb.task, "id"), filepath.Join(t.TempDir(), "forbidden"))
		a.record(Object{"record_type": "materialize", "audience": "A", "role": role, "manifest": manifest, "foreign_project_status": c02Status(foreign)})
		a.assert("W17-C02-"+role+"-CONTEXT", []any{true, true, true, true, 404}, []any{containsSnapshot(Arr(bundle, "authorized_snapshot_ids"), Str(pa.snapshot, "id")), containsSnapshot(Arr(bundle, "authorized_snapshot_ids"), Str(pa.shared, "id")), strings.Contains(local, c02Own), strings.Contains(local, c02Shared), c02Status(foreign)})
		a.action = "shared-read-does-not-grant-B"
		f.expect(404, "GET", "/v1/projects/"+projectB+"/state", "", "", nil)
		a.content(projectB, Str(pb.shared, "id"), 404)
		a.content(projectB, Str(pb.snapshot, "id"), 404)
		var count int
		if e = f.db.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=?", "c02-a-"+strings.ToLower(role), projectB).Scan(&count); e != nil {
			t.Fatal(e)
		}
		a.assert("W17-C02-"+role+"-SHARED-NO-GRANT", 0, count)
	}
	readback := c02Readback(t, f, projectA, projectB)
	a.record(Object{"record_type": "sqlite_readback", "data": readback, "B_business_hash_before": before, "B_business_hash_after": c02ProjectDigest(t, f, projectB)})
	a.assert("W17-C02-SQLITE-SCOPE", []any{before, 0, 6}, []any{c02ProjectDigest(t, f, projectB), readback["cross_project_references"], readback["role_grant_checks"]})
	responseLeaks, materialLeaks := 0, 0
	for _, raw := range a.responses {
		if strings.Contains(raw, c02Private) {
			responseLeaks++
		}
	}
	for _, raw := range a.materials {
		if strings.Contains(raw, c02Private) {
			materialLeaks++
		}
	}
	a.server.Close()
	logText := a.logs.String()
	a.record(Object{"record_type": "service_log", "audience": "A", "body": logText, "scope": "httptest real HTTP server ErrorLog; application handler emits no request-body logging"})
	a.assert("W17-C02-LOG-SCAN", false, strings.Contains(logText, c02Private))
	a.assert("C02-01", []any{0, 0, true, true}, []any{responseLeaks, materialLeaks, len(a.responses) > 0, len(a.materials) > 0})
	a.assert("C02-02", []any{true, true, 3}, []any{pa.shared["project_id"] == projectA, pb.shared["project_id"] == projectB, readback["A_only_role_principals"]})
	a.record(Object{"record_type": "scan_report", "private_marker": c02Private, "A_http_responses_scanned": len(a.responses), "A_materialized_files_scanned": len(a.materials), "A_response_leaks": responseLeaks, "A_material_leaks": materialLeaks, "service_log_leaks": strings.Count(logText, c02Private), "total_HTTP_requests": a.requests, "forbidden_or_not_found_responses": a.denials, "request_inputs_excluded": "Caller-supplied marker in negative search requests is input, not a returned secret. B_CONTROL positive responses are separately labelled and excluded."})
}

func c02Materialized(t *testing.T, a *c02Audit, root, role string) string {
	t.Helper()
	all := ""
	e := filepath.WalkDir(root, func(path string, d os.DirEntry, e error) error {
		if e != nil {
			return e
		}
		if d.IsDir() {
			return nil
		}
		raw, e := os.ReadFile(path)
		if e != nil {
			return e
		}
		rel, e := filepath.Rel(root, path)
		if e != nil {
			return e
		}
		a.materials = append(a.materials, string(raw))
		all += string(raw)
		a.record(Object{"record_type": "materialized_file", "audience": "A", "role": role, "path": filepath.ToSlash(rel), "sha256": Digest(raw), "body": string(raw)})
		return nil
	})
	if e != nil {
		t.Fatal(e)
	}
	return all
}
func c02ProjectDigest(t *testing.T, f *fixture, project string) string {
	t.Helper()
	values := []string{}
	for _, table := range []string{"domain_objects", "domain_versions", "uploaded_content", "retrieval_roots", "retrieval_snapshots", "retrieval_index"} {
		rows, e := f.db.Query("SELECT * FROM "+table+" WHERE project=?", project)
		if e != nil {
			t.Fatal(e)
		}
		cols, e := rows.Columns()
		if e != nil {
			t.Fatal(e)
		}
		for rows.Next() {
			v := make([]any, len(cols))
			p := make([]any, len(cols))
			for i := range v {
				p[i] = &v[i]
			}
			if e = rows.Scan(p...); e != nil {
				t.Fatal(e)
			}
			values = append(values, table+string(Bytes(v)))
		}
		if e = rows.Err(); e != nil {
			t.Fatal(e)
		}
		rows.Close()
	}
	sort.Strings(values)
	return Hash(values)
}
func c02Readback(t *testing.T, f *fixture, projectA, projectB string) Object {
	t.Helper()
	o := Object{"cross_project_references": 0, "role_grant_checks": 0, "A_only_role_principals": 0, "roles": Empty(), "shared_imports": Empty()}
	var cross int
	if e := f.db.QueryRow("SELECT count(*) FROM domain_refs WHERE project IN (?,?) AND target_project NOT IN (project,'')", projectA, projectB).Scan(&cross); e != nil {
		t.Fatal(e)
	}
	o["cross_project_references"] = cross
	for _, role := range []string{"READER", "PLANNER", "EXECUTOR"} {
		id := "c02-a-" + strings.ToLower(role)
		var raw string
		var grantedA, grantedB int
		if e := f.db.QueryRow("SELECT roles FROM auth_principals WHERE id=?", id).Scan(&raw); e != nil {
			t.Fatal(e)
		}
		var roles []string
		if e := json.Unmarshal([]byte(raw), &roles); e != nil {
			t.Fatal(e)
		}
		if e := f.db.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=? AND task='' AND run='' AND restricted=0", id, projectA).Scan(&grantedA); e != nil {
			t.Fatal(e)
		}
		if e := f.db.QueryRow("SELECT count(*) FROM auth_grants WHERE principal=? AND project=?", id, projectB).Scan(&grantedB); e != nil {
			t.Fatal(e)
		}
		if Hash(roles) != Hash([]string{role}) || grantedA != 1 || grantedB != 0 {
			t.Fatal("unexpected C02 grant")
		}
		o["roles"] = append(Arr(o, "roles"), Object{"principal_id": id, "roles": roles, "A_grants": grantedA, "B_grants": grantedB})
	}
	o["role_grant_checks"] = 6
	o["A_only_role_principals"] = 3
	rows, e := f.db.Query("SELECT project,artifact_id,root_id,relative_path,content_hash,status FROM retrieval_snapshots WHERE relative_path='shared.json' ORDER BY project")
	if e != nil {
		t.Fatal(e)
	}
	defer rows.Close()
	for rows.Next() {
		var project, id, root, path, hash, status string
		if e = rows.Scan(&project, &id, &root, &path, &hash, &status); e != nil {
			t.Fatal(e)
		}
		o["shared_imports"] = append(Arr(o, "shared_imports"), Object{"project_id": project, "artifact_id": id, "root_id": root, "relative_path": path, "content_hash": hash, "status": status})
	}
	if e = rows.Err(); e != nil {
		t.Fatal(e)
	}
	return o
}
