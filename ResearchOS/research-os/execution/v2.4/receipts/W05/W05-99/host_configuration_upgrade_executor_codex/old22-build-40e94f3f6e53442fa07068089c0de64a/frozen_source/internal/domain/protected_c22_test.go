//go:build windows

package domain

import (
	"bufio"
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	dbstore "researchos.local/research-os/internal/store"
	sandbox "researchos.local/research-os/ops/experiment_sandbox"
)

const c22Marker = "fixture_holdout_private_marker"

func c22Assert(t *testing.T, id string, want, actual any, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(actual) {
		status = "FAIL"
	}
	fmt.Println("C22_ASSERTION " + string(Bytes(Object{"assertion_id": id, "status": status, "expected": want, "actual": actual, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func c22Save(t *testing.T, name string, v any) {
	t.Helper()
	dir := os.Getenv("RESEARCHOS_C22_EVIDENCE")
	if dir == "" {
		return
	}
	if e := os.WriteFile(filepath.Join(dir, name), Bytes(v), 0600); e != nil {
		t.Fatal(e)
	}
}
func c22Native(t *testing.T, private string, paths []any, operands []any, phase string) Object {
	t.Helper()
	root := t.TempDir()
	input := filepath.Join(root, "input")
	output := filepath.Join(root, "output")
	for _, p := range []string{input, output} {
		if e := os.Mkdir(p, 0700); e != nil {
			t.Fatal(e)
		}
	}
	goBin := os.Getenv("RESEARCHOS_GO")
	if goBin == "" {
		t.Fatal("RESEARCHOS_GO is required")
	}
	native := filepath.Join(input, "candidate.exe")
	cmd := exec.Command(goBin, "build", "-o", native, "../../ops/protected_fixture")
	cmd.Env = append(os.Environ(), "GOTOOLCHAIN=local", "GOENV=off")
	if raw, e := cmd.CombinedOutput(); e != nil {
		t.Fatalf("build fixture: %v %s", e, raw)
	}
	binary, e := os.ReadFile(native)
	if e != nil {
		t.Fatal(e)
	}
	body := Object{"question": Object{"operands": operands}, "private_directory": private, "probes": paths}
	requestPath := filepath.Join(input, "question.json")
	if e := os.WriteFile(requestPath, Bytes(body), 0600); e != nil {
		t.Fatal(e)
	}
	c22Save(t, phase+"-native-input.json", Object{"binary_sha256": Digest(binary), "binary_bytes": len(binary), "question_request": body, "question_request_sha256": Digest(Bytes(body)), "input_files": []any{"candidate.exe", "question.json"}, "stdin": "NONE", "environment": "existing sandbox fixed minimal environment", "previous_feedback": "NONE"})
	resultPath := filepath.Join(output, "result.json")
	r, e := sandbox.Run(context.Background(), sandbox.Command{Executable: native, Args: []string{requestPath, resultPath}, InputDirectory: input, OutputDirectory: output, Timeout: 10 * time.Second})
	c22Save(t, phase+"-native-receipt.json", r)
	if e != nil {
		t.Fatalf("native boundary unavailable; no retry: %v", e)
	}
	c22Assert(t, phase+"-native-exit", []any{0, true, false, 0}, []any{r.ExitCode, r.Stopped, r.TimedOut, len(r.Capabilities)}, Object{"sid": r.SID, "pid": r.PID})
	raw, e := os.ReadFile(resultPath)
	if e != nil {
		t.Fatal(e)
	}
	v, e := Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	c22Save(t, phase+"-native-output.json", v)
	c22Assert(t, phase+"-native-identity", true, r.SID != "" && r.PID != 0 && Hash(v["pid"]) == Hash(r.PID), Object{"sid": r.SID, "receipt_pid": r.PID, "child_pid": v["pid"]})
	for _, value := range Arr(v, "probes") {
		p := value.(map[string]any)
		c22Assert(t, phase+"-os-deny-"+Str(p, "name"), []any{5, 0, 5, 0}, []any{p["read_code"], p["read_bytes"], p["write_code"], p["written_bytes"]}, p)
	}
	c22Assert(t, phase+"-os-list-deny", []any{5, 0}, []any{v["list_code"], v["listed_entries"]}, v["list_error"])
	c22Assert(t, phase+"-single-input", []any{[]any{"candidate.exe", "question.json"}, Hash(body), false}, []any{v["input_files"], Hash(json.RawMessage(Str(v, "input_raw"))), bytes.Contains(raw, []byte(c22Marker))}, Object{"input_hash": Hash(body), "no_labels_or_previous_feedback": true})
	return v
}

func TestProtectedC22VerticalSlice(t *testing.T) {
	f := contextFixture(t)
	private := filepath.Join(t.TempDir(), "private")
	store, e := protectedstore.NewCanary(private)
	if e != nil {
		t.Fatal(e)
	}
	defer store.Close()
	f.s.Protected = store
	p := Principal{ID: "c22-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
		t.Fatal(e)
	}
	f.token, e = f.s.IssueCredential(context.Background(), p.ID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	blob, e := store.CreateCanary(context.Background(), f.project, "application/json", Bytes(Object{"marker": c22Marker, "expected": 7, "kind": "labels"}))
	if e != nil {
		t.Fatal(e)
	}
	a, e := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, blob.Ticket, protectedMetadata())
	if e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(private, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	c22Assert(t, "vertical-host-positive", true, bytes.Contains(raw, []byte(c22Marker)), Object{"path": path, "sha256": Digest(raw), "exists": true})
	c22Native(t, private, []any{Object{"name": "labels", "path": path}}, []any{2, 5}, "vertical")
	server, _ := fixtureHTTPServer(t, f.s.Handler())
	defer server.Close()
	f.switchPrincipal("c22-executor", []string{"EXECUTOR"})
	req, _ := http.NewRequest("GET", server.URL+f.path("/artifacts/"+Str(a, "id")+"/content"), nil)
	req.Header.Set("Authorization", "Bearer "+f.token)
	resp, e := server.Client().Do(req)
	if e != nil {
		t.Fatal(e)
	}
	raw, e = io.ReadAll(resp.Body)
	resp.Body.Close()
	if e != nil {
		t.Fatal(e)
	}
	c22Assert(t, "vertical-http-deny", []any{404, false}, []any{resp.StatusCode, bytes.Contains(raw, []byte(c22Marker))}, Object{"transport": "host-issued actual loopback HTTP under candidate credential", "response": string(raw)})
}

type c22ControlConfig struct {
	DB, Private, Log string
	Provider         bool
}

// This fixture-only subprocess exposes the existing Service.Handler unchanged.
// Its stdin only controls test shutdown; there is no new administration route.
func TestProtectedC22ControlPlaneProcess(t *testing.T) {
	path := os.Getenv("RESEARCHOS_C22_CONTROL_CONFIG")
	if path == "" {
		return
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	var config c22ControlConfig
	if e = json.Unmarshal(raw, &config); e != nil {
		t.Fatal(e)
	}
	db, e := dbstore.Open(config.DB)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	private, e := protectedstore.OpenCanary(config.Private)
	if e != nil {
		t.Fatal(e)
	}
	defer private.Close()
	if config.Provider {
		s.Protected = private
	}
	logs, e := os.Create(config.Log)
	if e != nil {
		t.Fatal(e)
	}
	defer logs.Close()
	server := httptest.NewUnstartedServer(s.Handler())
	server.Config.ErrorLog = log.New(logs, "", 0)
	server.Start()
	defer server.Close()
	fmt.Println("C22_CONTROL_READY " + string(Bytes(Object{"pid": os.Getpid(), "url": server.URL, "database": config.DB, "private": config.Private, "provider": config.Provider})))
	if _, e = io.Copy(io.Discard, os.Stdin); e != nil {
		t.Fatal(e)
	}
}

type c22Control struct {
	url     string
	pid     int
	command *exec.Cmd
	stdin   io.WriteCloser
	stdout  *bufio.Reader
	stderr  bytes.Buffer
	phase   string
}

func c22StartControl(t *testing.T, config c22ControlConfig, phase string) *c22Control {
	t.Helper()
	file := filepath.Join(t.TempDir(), "control.json")
	if e := os.WriteFile(file, Bytes(config), 0600); e != nil {
		t.Fatal(e)
	}
	executable, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	c := &c22Control{phase: phase}
	c.command = exec.Command(executable, "-test.run=^TestProtectedC22ControlPlaneProcess$", "-test.count=1")
	c.command.Env = append(os.Environ(), "RESEARCHOS_C22_CONTROL_CONFIG="+file)
	c.command.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	c.command.Stderr = &c.stderr
	c.stdin, e = c.command.StdinPipe()
	if e != nil {
		t.Fatal(e)
	}
	stdout, e := c.command.StdoutPipe()
	if e != nil {
		t.Fatal(e)
	}
	c.stdout = bufio.NewReader(stdout)
	if e = c.command.Start(); e != nil {
		t.Fatal(e)
	}
	line := make(chan string, 1)
	go func() { text, _ := c.stdout.ReadString('\n'); line <- text }()
	var text string
	select {
	case text = <-line:
	case <-time.After(20 * time.Second):
		c.command.Process.Kill()
		t.Fatal("control-plane startup timed out")
	}
	if !strings.HasPrefix(text, "C22_CONTROL_READY ") {
		c.stdin.Close()
		c.command.Wait()
		t.Fatalf("control startup: %s %s", text, c.stderr.String())
	}
	ready, e := Decode([]byte(strings.TrimPrefix(text, "C22_CONTROL_READY ")))
	if e != nil {
		t.Fatal(e)
	}
	pid, e := Num(ready, "pid")
	if e != nil {
		t.Fatal(e)
	}
	c.pid = int(pid)
	c.url = Str(ready, "url")
	c22Save(t, phase+"-control-ready.json", ready)
	t.Cleanup(func() {
		if c.command != nil {
			c.stop(t)
		}
	})
	return c
}
func (c *c22Control) stop(t *testing.T) {
	t.Helper()
	if c.command == nil {
		return
	}
	c.stdin.Close()
	raw, _ := io.ReadAll(c.stdout)
	e := c.command.Wait()
	c22Save(t, c.phase+"-control-exit.json", Object{"pid": c.pid, "stdout": string(raw), "stderr": c.stderr.String(), "error": fmt.Sprint(e), "exit_code": c.command.ProcessState.ExitCode()})
	c.command = nil
	if e != nil {
		t.Fatalf("control exit: %v %s", e, c.stderr.String())
	}
}

type c22Audit struct {
	t                                                     *testing.T
	file                                                  *os.File
	url, phase, role, audience, principal, token, project string
	count                                                 int
	responses                                             []string
}

func (a *c22Audit) record(o Object) {
	a.t.Helper()
	if _, e := fmt.Fprintln(a.file, string(Bytes(o))); e != nil {
		a.t.Fatal(e)
	}
}
func (a *c22Audit) request(method, path, key, tag string, body any) (int, []byte, http.Header) {
	a.t.Helper()
	var raw []byte
	if b, ok := body.([]byte); ok {
		raw = b
	} else if body != nil {
		raw = Bytes(body)
	}
	req, e := http.NewRequest(method, a.url+"/v1/projects/"+a.project+path, bytes.NewReader(raw))
	if e != nil {
		a.t.Fatal(e)
	}
	req.Header.Set("Authorization", "Bearer "+a.token)
	if key != "" {
		req.Header.Set("Idempotency-Key", key)
	}
	if tag != "" {
		req.Header.Set("If-Match", tag)
	}
	dumpReq, e := http.NewRequest(method, req.URL.String(), bytes.NewReader(raw))
	if e != nil {
		a.t.Fatal(e)
	}
	dumpReq.Header = req.Header.Clone()
	dumpReq.Header.Set("Authorization", "Bearer [REDACTED]")
	dump, e := httputil.DumpRequestOut(dumpReq, true)
	if e != nil {
		a.t.Fatal(e)
	}
	started := Now()
	response, e := (&http.Client{Timeout: 10 * time.Second}).Do(req)
	if e != nil {
		a.t.Fatal(e)
	}
	defer response.Body.Close()
	data, e := io.ReadAll(response.Body)
	if e != nil {
		a.t.Fatal(e)
	}
	response.Body = io.NopCloser(bytes.NewReader(data))
	wire, e := httputil.DumpResponse(response, true)
	if e != nil {
		a.t.Fatal(e)
	}
	a.count++
	a.record(Object{"record_type": "http", "request_id": a.count, "phase": a.phase, "audience": a.audience, "role": a.role, "principal_id": a.principal, "transport": "HOST_ISSUED_REAL_LOOPBACK_HTTP", "method": method, "path": req.URL.RequestURI(), "status": response.StatusCode, "started_at": started, "finished_at": Now(), "raw_request": string(dump), "raw_response": string(wire), "response_body": string(data), "credential": "REDACTED"})
	if a.audience == "CANDIDATE" {
		a.responses = append(a.responses, string(wire))
	}
	return response.StatusCode, data, response.Header
}
func (a *c22Audit) obj(method, path, key, tag string, body any, status int) Object {
	a.t.Helper()
	code, raw, _ := a.request(method, path, key, tag, body)
	if code != status {
		a.t.Fatalf("%s %s HTTP %d want %d: %s", method, path, code, status, raw)
	}
	o, e := Decode(raw)
	if e != nil {
		a.t.Fatal(e)
	}
	return o
}
func c22Token(t *testing.T, f *fixture, id string, roles []string, restricted bool) string {
	t.Helper()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: id, Roles: roles, Grants: []Grant{{ProjectID: f.project, Restricted: restricted}}}); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), id, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return token
}
func c22DBPath(t *testing.T, db *sql.DB) string {
	t.Helper()
	var seq int
	var name, path string
	if e := db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	return path
}
func c22Open(t *testing.T, path string) (*sql.DB, *Service) {
	t.Helper()
	db, e := dbstore.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		db.Close()
		t.Fatal(e)
	}
	return db, s
}

func TestW17C22ProtectedIsolation(t *testing.T) {
	f := contextFixture(t)
	root := t.TempDir()
	privatePath := filepath.Join(root, "private")
	private, e := protectedstore.NewCanary(privatePath)
	if e != nil {
		t.Fatal(e)
	}
	defer private.Close()
	f.s.Protected = private
	tokens := map[string]string{}
	roles := map[string][]string{"executor": {"EXECUTOR"}, "planner": {"PLANNER"}, "verifier": {"VERIFIER"}, "owner": {"OWNER", "PLANNER", "EXECUTOR"}, "unrestricted-verifier": {"VERIFIER"}, "unrestricted-owner": {"OWNER"}, "revoked-verifier": {"VERIFIER"}}
	for id, rs := range roles {
		restricted := id == "verifier" || id == "owner" || id == "revoked-verifier"
		tokens[id] = c22Token(t, f, "c22-"+id, rs, restricted)
	}
	f.token = tokens["owner"]
	f.owner = "c22-owner"
	// Full inputs and labels remain only in the host store. Each child receives
	// one question and negative-probe paths, never this batch or its answers.
	batch := []any{Object{"operands": []any{2, 5}}, Object{"operands": []any{8, 9}}}
	expected := []any{7, 17}
	privateValues := map[string]any{"inputs": Object{"marker": c22Marker, "questions": batch}, "labels": Object{"marker": c22Marker, "expected": expected, "weights": []any{1, 1}}, "details": Object{"marker": c22Marker, "feedback": "private per-case results"}, "logs": Object{"marker": c22Marker, "trace": "private evaluation trace"}, "baseline": Object{"marker": c22Marker, "rule": "ALWAYS_ZERO", "expected": expected}}
	artifacts := map[string]Object{}
	blobs := map[string]protectedstore.Blob{}
	probes := Empty()
	hostHashes := map[string]string{}
	privateNames := map[string]string{}
	for _, name := range []string{"inputs", "labels", "details", "logs", "baseline"} {
		blob, err := private.CreateCanary(context.Background(), f.project, "application/json", Bytes(privateValues[name]))
		if err != nil {
			t.Fatal(err)
		}
		blobs[name] = blob
		artifact, err := f.s.RegisterProtectedArtifact(context.Background(), f.token, f.project, blob.Ticket, protectedMetadata())
		if err != nil {
			t.Fatal(err)
		}
		artifacts[name] = artifact
		path := filepath.Join(privatePath, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		hostHashes[path] = Digest(raw)
		privateNames[path] = name
		probes = append(probes, Object{"name": name, "path": path})
		c22Assert(t, "host-positive-"+name, true, bytes.Contains(raw, []byte(c22Marker)), Object{"path": path, "sha256": Digest(raw), "artifact_ref": Ref(artifact, "Artifact"), "host_exists_and_readable": true})
	}
	database := c22DBPath(t, f.db)
	probes = append(probes, Object{"name": "authority-db", "path": database})
	req := f.requirement()
	task := f.task(req, []any{Ref(artifacts["inputs"], "Artifact")}, "c22-protected-context")
	bundle := f.bundle(task)
	development := f.artifact(Object{"public_development": "separate synthetic development fixture"}, Empty())
	decisionBody := w11Body(f, req)
	decisionBody["mode"] = "BOUNDED_AUTO"
	qbody := Object{"scope": decisionBody["scope"], "dataset_artifact_ref": Ref(development, "Artifact"), "holdout_artifact_ref": Ref(artifacts["inputs"], "Artifact"), "thresholds_hash": Digest(Bytes(privateValues["labels"])), "thresholds_frozen_at": Now(), "total_case_count": 3, "holdout_case_count": 2, "label_basis": "OBJECTIVE", "measurement_mode": "FIXTURE", "jev_called": false, "expires_at": nil}
	f.token = tokens["verifier"]
	q := f.expect(201, "POST", f.path("/qualifications"), ID(), f.stateTag(), qbody)
	f.token = tokens["owner"]
	materialized := filepath.Join(root, "forbidden-context")
	_, e = f.s.MaterializeTaskContext(context.Background(), tokens["owner"], f.project, Str(task, "id"), materialized)
	_, statErr := os.Stat(materialized)
	c22Assert(t, "protected-context-not-materialized", []any{true, true}, []any{e != nil, os.IsNotExist(statErr)}, fmt.Sprint(e))
	if _, e = f.s.CreateBackup(context.Background(), filepath.Join(root, "backup"), bytes.Repeat([]byte{1}, 32)); e == nil || !strings.Contains(e.Error(), "PROTECTED_BACKUP_REQUIRES_W17") {
		t.Fatalf("protected backup must fail closed: %v", e)
	}
	c22Assert(t, "protected-backup-engine-deny", true, true, fmt.Sprint(e))
	_, backupStat := os.Stat(filepath.Join(root, "backup"))
	c22Assert(t, "protected-backup-not-published", true, os.IsNotExist(backupStat), Object{"destination": filepath.Join(root, "backup")})
	c22Save(t, "host-positive-controls.json", Object{"private_hashes": hostHashes, "artifact_refs": artifacts, "database": database, "private_store": privatePath, "qualification": q, "task_ref": Ref(task, "Task"), "bundle_ref": Ref(bundle, "ContextBundle")})
	if e = f.db.Close(); e != nil {
		t.Fatal(e)
	}
	out := os.Getenv("RESEARCHOS_C22_EVIDENCE")
	if out == "" {
		out = t.TempDir()
	}
	auditFile, e := os.Create(filepath.Join(out, "audit.jsonl"))
	if e != nil {
		t.Fatal(e)
	}
	defer auditFile.Close()
	a := &c22Audit{t: t, file: auditFile, project: f.project}
	pids := []int{}
	nativeRuns := 0
	writeDenials, scoreDenials := 0, 0
	var publicReport Object
	summary := protectedstore.SafeSummary{Schema: "researchos.protected-summary.v1", Status: "EXECUTION_REPORTED", MaximumMode: "ADVISORY"}
	for _, phase := range []string{"before-restart", "after-restart"} {
		control := c22StartControl(t, c22ControlConfig{DB: database, Private: privatePath, Log: filepath.Join(out, phase+"-service.log"), Provider: true}, phase)
		pids = append(pids, control.pid)
		a.url = control.url
		a.phase = phase
		if phase == "before-restart" {
			a.role = "revoked-verifier"
			a.principal = "c22-revoked-verifier"
			a.token = tokens["revoked-verifier"]
			a.audience = "AUTHORIZED_CONTROL"
			code, raw, h := a.request("GET", "/artifacts/"+Str(artifacts["inputs"], "id")+"/content", "", "", nil)
			c22Assert(t, "revocation-before-positive", []any{200, artifacts["inputs"]["content_hash"], "no-store"}, []any{code, Digest(raw), h.Get("Cache-Control")}, Object{"principal_id": a.principal})
		}
		// Verify both authorized roles against every exact registered object and
		// body, with no-store headers; host-only full evidence is labelled.
		for _, role := range []string{"owner", "verifier"} {
			a.role = role
			a.principal = "c22-" + role
			a.token = tokens[role]
			a.audience = "AUTHORIZED_CONTROL"
			for _, name := range []string{"inputs", "labels", "details", "logs", "baseline"} {
				artifact := artifacts[name]
				got := a.obj("GET", "/artifacts/"+Str(artifact, "id"), "", "", nil, 200)
				code, raw, h := a.request("GET", "/artifacts/"+Str(artifact, "id")+"/content", "", "", nil)
				c22Assert(t, phase+"-authorized-"+role+"-"+name, []any{200, artifact["content_hash"], true, "no-store", "VERIFIER_ONLY"}, []any{code, Digest(raw), bytes.Contains(raw, []byte(c22Marker)), h.Get("Cache-Control"), got["access_class"]}, Object{"artifact_ref": Ref(got, "Artifact"), "principal_id": a.principal, "content_disposition": h.Get("Content-Disposition")})
			}
		}
		for _, role := range []string{"executor", "planner", "unrestricted-verifier", "unrestricted-owner"} {
			a.role = role
			a.principal = "c22-" + role
			a.token = tokens[role]
			a.audience = "CANDIDATE"
			state := a.obj("GET", "/state", "", "", nil, 200)
			for _, name := range []string{"inputs", "labels", "details", "logs", "baseline"} {
				for _, suffix := range []string{"", "/content"} {
					a.obj("GET", "/artifacts/"+Str(artifacts[name], "id")+suffix, "", "", nil, 404)
				}
			}
			for _, route := range []string{"/artifacts", "/events", "/context-bundles", "/qualifications"} {
				a.obj("GET", route, "", "", nil, 200)
			}
			a.obj("GET", "/context-bundles/"+Str(bundle, "id"), "", "", nil, 404)
			// Preview and export use the frozen content endpoint; no dedicated
			// backup/export HTTP route exists. Also probe guessed routes explicitly.
			for _, route := range []string{"/artifacts/" + Str(artifacts["inputs"], "id") + "/preview", "/artifacts/" + Str(artifacts["inputs"], "id") + "/export", "/backups", "/backup", "/logs"} {
				a.obj("GET", route, "", "", nil, 404)
			}
			if role == "executor" || role == "planner" {
				code, raw, _ := a.request("POST", "/search", ID(), "", Object{"query": c22Marker, "snapshot_ids": []any{artifacts["inputs"]["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
				c22Assert(t, phase+"-search-"+role, true, code >= 400 && !bytes.Contains(raw, []byte(c22Marker)), Object{"status": code, "response": string(raw)})
				code, raw, _ = a.request("POST", "/context-bundles", ID(), testTag(state), Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]})
				c22Assert(t, phase+"-context-build-"+role, true, code >= 400 && !bytes.Contains(raw, []byte(c22Marker)), Object{"status": code, "response": string(raw)})
				code, raw, _ = a.request("POST", "/qualifications", ID(), testTag(state), qbody)
				c22Assert(t, phase+"-forged-qualification-"+role, true, code >= 400, Object{"status": code, "response": string(raw)})
				for _, field := range []string{"weights", "labels", "baseline"} {
					changed := Bytes(Object{"changed_criterion": field, "new_value": "candidate-selected"})
					status, raw, _ := a.request("POST", "/content", ID(), "", changed)
					if status == 201 {
						upload, err := Decode(raw)
						if err != nil {
							t.Fatal(err)
						}
						seal := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(changed), "input_refs": []any{Ref(artifacts["labels"], "Artifact"), Ref(artifacts["baseline"], "Artifact")}, "source_refs": Empty(), "produced_by": a.principal, "access_class": "PROJECT"}
						status, raw, _ = a.request("POST", "/artifacts", ID(), testTag(state), seal)
					}
					c22Assert(t, phase+"-criterion-submit-"+role+"-"+field, true, status == 403, Object{"status": status, "response": string(raw)})
					writeDenials++
				}
				resultBody := Object{"requested_maximum_mode": "BOUNDED_AUTO", "critical_false_accept_count": 0, "false_accept_rate": 0, "false_reject_rate": 0, "abstain_rate": 0, "test_receipt_refs": []any{Ref(development, "Artifact")}, "acceptance_id": ID()}
				code, raw, _ = a.request("POST", "/qualifications/"+Str(q, "id")+"/result", ID(), testTag(q), resultBody)
				c22Assert(t, phase+"-self-score-"+role, true, code == 403 || code == 404, Object{"status": code, "response": string(raw)})
				scoreDenials++
			}
		}
		// Run a composed two-item fixture. The trusted host reads the private
		// batch, invokes one new AppContainer per question, stores raw results
		// privately and gives the next child no result or feedback from prior IO.
		raw, err := private.Read(context.Background(), blobs["inputs"])
		if err != nil {
			t.Fatal(err)
		}
		inputBody, err := Decode(raw)
		if err != nil {
			t.Fatal(err)
		}
		phaseProbes := append(Empty(), probes...)
		for i, question := range Arr(inputBody, "questions") {
			value := question.(map[string]any)
			name := fmt.Sprintf("%s-case-%d", phase, i+1)
			result := c22Native(t, privatePath, phaseProbes, Arr(value, "operands"), name)
			nativeRuns++
			privateResult := Object{"marker": c22Marker, "case_index": i, "candidate_result": result["result"], "expected": expected[i], "phase": phase, "candidate_observation": result}
			blob, err := private.CreateCanary(context.Background(), f.project, "application/json", Bytes(privateResult))
			if err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(privatePath, strings.TrimPrefix(blob.Ticket, "ps1:")+".bin")
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			hostHashes[path] = Digest(raw)
			privateNames[path] = "result-" + name
			c22Assert(t, "host-positive-result-"+name, true, bytes.Contains(raw, []byte(c22Marker)), Object{"path": path, "sha256": Digest(raw), "exists": true})
			probes = append(probes, Object{"name": "result-" + name, "path": path})
			db, host := c22Open(t, database)
			host.Protected = private
			metadata := protectedMetadata()
			metadata["input_refs"] = []any{Ref(artifacts["inputs"], "Artifact"), Ref(artifacts["labels"], "Artifact")}
			detail, err := host.RegisterProtectedArtifact(context.Background(), tokens["verifier"], f.project, blob.Ticket, metadata)
			db.Close()
			if err != nil {
				t.Fatal(err)
			}
			a.record(Object{"record_type": "private_result", "phase": phase, "name": name, "artifact_ref": Ref(detail, "Artifact"), "lineage": metadata["input_refs"], "content_sha256": detail["content_hash"], "private_path": path})
			for _, role := range []string{"owner", "verifier", "executor", "planner"} {
				a.role = role
				a.principal = "c22-" + role
				a.token = tokens[role]
				if role == "owner" || role == "verifier" {
					a.audience = "AUTHORIZED_CONTROL"
					got := a.obj("GET", "/artifacts/"+Str(detail, "id"), "", "", nil, 200)
					code, body, h := a.request("GET", "/artifacts/"+Str(detail, "id")+"/content", "", "", nil)
					c22Assert(t, name+"-raw-result-authorized-"+role, []any{200, detail["content_hash"], "no-store", metadata["input_refs"]}, []any{code, Digest(body), h.Get("Cache-Control"), got["input_refs"]}, Object{"artifact_ref": Ref(got, "Artifact"), "principal_id": a.principal})
				} else {
					a.audience = "CANDIDATE"
					a.obj("GET", "/artifacts/"+Str(detail, "id"), "", "", nil, 404)
					a.obj("GET", "/artifacts/"+Str(detail, "id")+"/content", "", "", nil, 404)
				}
			}
			if phase == "before-restart" {
				summary.Total++
				if Hash(result["result"]) == Hash(expected[i]) {
					summary.Correct++
				} else {
					summary.FalseReject++
				}
			}
		}
		a.audience = "AUTHORIZED_CONTROL"
		a.role = "owner"
		a.principal = "c22-owner"
		a.token = tokens["owner"]
		// Even a restricted owner cannot feed protected lineage to the public
		// sealing route, or convert caller-supplied scores into qualification.
		state := a.obj("GET", "/state", "", "", nil, 200)
		publicBytes := []byte(`{"attempt":"declassify"}`)
		upload := a.obj("POST", "/content", ID(), "", publicBytes, 201)
		seal := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(publicBytes), "input_refs": []any{Ref(artifacts["inputs"], "Artifact")}, "source_refs": Empty(), "produced_by": "c22-owner", "access_class": "PROJECT"}
		a.obj("POST", "/artifacts", ID(), testTag(state), seal, 403)
		writeDenials++
		if publicReport == nil {
			if err := summary.Validate(); err != nil {
				t.Fatal(err)
			}
			raw := Bytes(summary)
			upload := a.obj("POST", "/content", ID(), "", raw, 201)
			publicBody := Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": upload["content_hash"], "storage_key": upload["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": "c22-owner", "access_class": "PROJECT"}
			publicReport = a.obj("POST", "/artifacts", ID(), testTag(state), publicBody, 201)
			a.record(Object{"record_type": "public_summary", "source": "trusted fixture host computed counts; not production declassification authority", "artifact_ref": Ref(publicReport, "Artifact"), "summary": summary})
		}
		for _, role := range []string{"executor", "planner"} {
			a.audience = "CANDIDATE"
			a.role = role
			a.principal = "c22-" + role
			a.token = tokens[role]
			code, raw, _ := a.request("GET", "/artifacts/"+Str(publicReport, "id")+"/content", "", "", nil)
			parsed, err := protectedstore.ParseSafeSummary(raw)
			c22Assert(t, phase+"-public-summary-"+role, []any{200, true, Hash(summary), false}, []any{code, err == nil, Hash(parsed), bytes.Contains(raw, []byte(c22Marker))}, Object{"artifact_ref": Ref(publicReport, "Artifact"), "body": string(raw)})
		}
		a.audience = "AUTHORIZED_CONTROL"
		a.role = "verifier"
		a.principal = "c22-verifier"
		a.token = tokens["verifier"]
		resultBody := Object{"requested_maximum_mode": "BOUNDED_AUTO", "critical_false_accept_count": 0, "false_accept_rate": 0, "false_reject_rate": 0, "abstain_rate": 0, "test_receipt_refs": []any{Ref(development, "Artifact")}, "acceptance_id": ID()}
		a.obj("POST", "/qualifications/"+Str(q, "id")+"/result", ID(), testTag(q), resultBody, 503)
		scoreDenials++
		current := a.obj("GET", "/qualifications/"+Str(q, "id"), "", "", nil, 200)
		c22Assert(t, phase+"-no-auto", []any{"DRAFT", "ADVISORY", false, nil}, []any{current["status"], current["maximum_mode"], current["jev_called"], current["acceptance_id"]}, current)
		a.role = "owner"
		a.principal = "c22-owner"
		a.token = tokens["owner"]
		state = a.obj("GET", "/state", "", "", nil, 200)
		a.obj("POST", "/decisions", ID(), testTag(state), decisionBody, 503)
		if phase == "after-restart" {
			a.token = tokens["revoked-verifier"]
			a.role = "revoked-verifier"
			a.principal = "c22-revoked-verifier"
			a.audience = "CANDIDATE"
			a.obj("GET", "/artifacts/"+Str(artifacts["inputs"], "id")+"/content", "", "", nil, 401)
		}
		control.stop(t)
		if phase == "before-restart" {
			db, service := c22Open(t, database)
			if err = service.RevokePrincipal(context.Background(), "c22-revoked-verifier"); err != nil {
				t.Fatal(err)
			}
			db.Close()
		}
	}
	// Missing provider is a third fresh process, never an in-memory object swap.
	missing := c22StartControl(t, c22ControlConfig{DB: database, Private: privatePath, Log: filepath.Join(out, "missing-provider-service.log"), Provider: false}, "missing-provider")
	a.url = missing.url
	a.phase = "missing-provider"
	a.role = "verifier"
	a.principal = "c22-verifier"
	a.token = tokens["verifier"]
	a.audience = "AUTHORIZED_CONTROL"
	a.obj("GET", "/artifacts/"+Str(artifacts["inputs"], "id")+"/content", "", "", nil, 503)
	current := a.obj("GET", "/qualifications/"+Str(q, "id"), "", "", nil, 200)
	c22Assert(t, "missing-provider-advisory", []any{"DRAFT", "ADVISORY", nil}, []any{current["status"], current["maximum_mode"], current["acceptance_id"]}, nil)
	missing.stop(t)
	if e = summary.Validate(); e != nil {
		t.Fatal(e)
	}
	c22Save(t, "public-report.json", summary)
	unsafeSummary := append(Bytes(summary)[:len(Bytes(summary))-1], []byte(`,"labels":"forged self score"}`)...)
	_, e = protectedstore.ParseSafeSummary(unsafeSummary)
	c22Assert(t, "summary-free-text-refused", true, e != nil, nil)
	badSummary := summary
	badSummary.MaximumMode = "BOUNDED_AUTO"
	c22Assert(t, "summary-auto-refused", true, badSummary.Validate() != nil, nil)
	if e = private.Ready(context.Background(), "LIVE"); e == nil {
		t.Fatal("CanaryStore granted LIVE")
	}
	c22Assert(t, "canary-live-closed", true, true, fmt.Sprint(e))
	boundary, e := private.Boundary(context.Background())
	if e != nil {
		t.Fatal(e)
	}
	c22Assert(t, "canary-missing-formal-isolation", []any{"CANARY_ONLY", false, true}, []any{boundary.Mode, boundary.IndependentIdentity, boundary.UnrestrictedSameUserCanRead}, boundary)
	leaks := 0
	for _, response := range a.responses {
		if strings.Contains(response, c22Marker) {
			leaks++
		}
	}
	for _, phase := range []string{"before-restart", "after-restart", "missing-provider"} {
		raw, err := os.ReadFile(filepath.Join(out, phase+"-service.log"))
		if err != nil {
			t.Fatal(err)
		}
		a.record(Object{"record_type": "service_log", "phase": phase, "body": string(raw)})
		if bytes.Contains(raw, []byte(c22Marker)) {
			leaks++
		}
	}
	for path, hash := range hostHashes {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		c22Assert(t, "private-unchanged-"+privateNames[path], hash, Digest(raw), Object{"path": path})
	}
	db, service := c22Open(t, database)
	defer db.Close()
	service.Protected = private
	var cached int
	if e = db.QueryRow("SELECT count(*) FROM idempotency WHERE instr(CAST(body AS TEXT),?)>0", c22Marker).Scan(&cached); e != nil {
		t.Fatal(e)
	}
	var uploaded int
	if e = db.QueryRow("SELECT count(*) FROM uploaded_content WHERE instr(CAST(bytes AS TEXT),?)>0", c22Marker).Scan(&uploaded); e != nil {
		t.Fatal(e)
	}
	var business int
	if e = db.QueryRow("SELECT count(*) FROM domain_objects WHERE instr(body,?)>0", c22Marker).Scan(&business); e != nil {
		t.Fatal(e)
	}
	var eventLeaks int
	if e = db.QueryRow("SELECT count(*) FROM outbox WHERE instr(body,?)>0", c22Marker).Scan(&eventLeaks); e != nil {
		t.Fatal(e)
	}
	c22Save(t, "sqlite-readback.json", Object{"cache_marker_rows": cached, "uploaded_marker_rows": uploaded, "domain_marker_rows": business, "event_marker_rows": eventLeaks, "database": database, "qualification_id": q["id"], "classification": "VERIFIER_ONLY"})
	c22Assert(t, "C22-01", []any{0, 0, 0, 0, 0, true}, []any{leaks, cached, uploaded, business, eventLeaks, len(a.responses) > 0}, Object{"candidate_http_responses": len(a.responses), "native_runs": nativeRuns, "marker": c22Marker})
	c22Assert(t, "C22-02", []any{int64(2), int64(2), "ADVISORY", false}, []any{summary.Total, summary.Correct, summary.MaximumMode, bytes.Contains(Bytes(summary), []byte(c22Marker))}, Object{"single_question_runs": nativeRuns, "public_report": summary, "feedback_to_candidates": false})
	c22Assert(t, "C22-03", []any{9, 14, 6}, []any{len(hostHashes), writeDenials, scoreDenials}, Object{"private_files_unchanged": len(hostHashes), "os_write_denied": true, "project_derivation_denied": true, "self_score_denied": true, "authorized_verifier_owner_body_reads": "exact hashes, protected lineage and no-store recorded above"})
	c22Assert(t, "C22-04", []any{true, true, "ADVISORY"}, []any{len(pids) == 2 && pids[0] != pids[1] && pids[0] != os.Getpid() && pids[1] != os.Getpid(), missing.pid != pids[0] && missing.pid != pids[1], current["maximum_mode"]}, Object{"control_pids": pids, "missing_provider_pid": missing.pid, "parent_pid": os.Getpid(), "same_database": database, "same_private_store": privatePath, "revocation_persisted": true})
	c22Save(t, "scan-summary.json", Object{"http_count": a.count, "candidate_responses": len(a.responses), "marker_leaks": leaks, "native_runs": nativeRuns, "control_pids": pids, "qualification_maximum_mode": "ADVISORY", "formal_live": false, "scope": "Synthetic CanaryStore fixture; host HTTP and AppContainer OS probes are distinct evidence layers."})
}
