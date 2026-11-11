//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/internal/store"
	"researchos.local/research-os/ops/supervisor"
)

func currentControlBuild(t *testing.T, root, work string) (string, []byte, evolution.ControlSourceProvenance) {
	t.Helper()
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("RESEARCHOS_GO required")
	}
	path := filepath.Join(work, "control.exe")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	cmd := exec.CommandContext(ctx, goexe, "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", path, "./apps/control")
	cmd.Dir = root
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	fixed := map[string]string{"GOENV": "off", "GOTOOLCHAIN": "local", "GOWORK": "off", "GOFLAGS": "-mod=readonly", "CGO_ENABLED": "0", "GOOS": "windows", "GOARCH": "amd64", "GOAMD64": "v1", "GOPROXY": "off", "GOSUMDB": "off", "GOEXPERIMENT": ""}
	for _, v := range os.Environ() {
		k, _, _ := strings.Cut(v, "=")
		k = strings.ToUpper(k)
		if _, ok := fixed[k]; !ok && k != "GOROOT" {
			cmd.Env = append(cmd.Env, v)
		}
	}
	for k, v := range fixed {
		cmd.Env = append(cmd.Env, k+"="+v)
	}
	if raw, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("fixed control build: %v %s", err, raw)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	p, err := supervisor.ControlBuildProvenance(raw, root)
	if err != nil {
		t.Fatal(err)
	}
	return path, raw, p
}

func currentControlResearch(t *testing.T, root, data string) *researchFixture {
	t.Helper()
	if err := os.MkdirAll(data, 0700); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(data, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(context.Background(), db, filepath.Join(root, "migrations/sqlite/0001_bootstrap.sql")); err != nil {
		t.Fatal(err)
	}
	service, err := New(db, filepath.Join(root, "spec/v2.0/contracts"), filepath.Join(root, "migrations/sqlite/0002_domain.sql"))
	if err != nil {
		t.Fatal(err)
	}
	owner := Principal{ID: "current-control-owner", Roles: []string{"OWNER", "PLANNER", "SCHEDULER", "EXECUTOR"}, CanCreateProject: true}
	if err = service.ProvisionPrincipal(context.Background(), owner); err != nil {
		t.Fatal(err)
	}
	token, err := service.IssueCredential(context.Background(), owner.ID, 15*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	f := &fixture{s: service, h: service.Handler(), token: token, owner: owner.ID, db: db, t: t}
	ids := map[string]string{"GITHUB": ID(), "PAPER": ID()}
	body := projectBody()
	body["intent"] = "Bounded current authority proof for ResearchOS cycle coverage"
	body["source_configs"] = []any{Object{"source_id": ids["GITHUB"], "kind": "GITHUB", "required": true, "enabled": true, "query": "repo:researchos/research", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil}, Object{"source_id": ids["PAPER"], "kind": "PAPER", "required": true, "enabled": true, "query": "research agents", "allowed_origins": []any{"https://arxiv.org", "https://export.arxiv.org"}, "credential_ref": nil}}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", body)
	f.project = Str(p, "project_id")
	r := &researchFixture{f: f, owner: token, ids: ids}
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	return r
}

func currentControlSuites(binding evolution.ControlBinding, project string, cycle Object) (evolution.ControlSuite, evolution.ControlInputs, evolution.ControlLabels) {
	path := "/v1/projects/" + project + "/research-cycles/" + Str(cycle, "id")
	read := evolution.ControlStep{Method: "GET", Path: path, Authenticated: true}
	close := evolution.ControlStep{Method: "POST", Path: path + "/close", Authenticated: true, Body: Bytes(Object{"requested_status": "COMPLETE", "outcome_summary": "current public coverage gate"}), ETag: testTag(cycle), IdempotencyKey: "current-public-close"}
	headers := func(auth bool, etag string) map[string]string {
		h := map[string]string{"Content-Type": "application/json", "Cache-Control": "no-store"}
		if auth {
			h["X-ResearchOS-Principal-ID"] = evolution.ControlPrincipal
		}
		if etag != "" {
			h["ETag"] = etag
		}
		return h
	}
	failure := func(code, message string, current any) json.RawMessage {
		return Bytes(Object{"code": code, "message": message, "retryable": false, "current_revision": current, "details": Empty()})
	}
	suite := evolution.ControlSuite{Inputs: evolution.ControlInputs{Revision: evolution.ControlPublicRevision, Binding: binding, Cases: []evolution.ControlCase{{ID: "public-control-current-read", Steps: []evolution.ControlStep{read}}, {ID: "public-control-current-no-false-complete", Steps: []evolution.ControlStep{close, read}}}}, Labels: evolution.ControlLabels{Revision: evolution.ControlPublicRevision, Binding: binding, Labels: []evolution.ControlLabel{{ID: "public-control-current-read", Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 200, Headers: headers(true, testTag(cycle)), Body: Bytes(cycle)}}}, {ID: "public-control-current-no-false-complete", Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 422, Headers: headers(true, ""), Body: failure("GATE_FAILED", "requested cycle status differs from verified coverage and experiments: BLOCKED", nil)}, {Status: 200, Headers: headers(true, testTag(cycle)), Body: Bytes(cycle)}}}}}}
	noAuth := read
	noAuth.Authenticated = false
	stale := close
	stale.ETag = "\"r999999\""
	stale.IdempotencyKey = "current-private-stale"
	stale.Body = Bytes(Object{"requested_status": "COMPLETE", "outcome_summary": "current private stale revision"})
	nonce := ID()
	inputs := evolution.ControlInputs{Revision: evolution.ControlPrivateRevision, Binding: binding, Cases: []evolution.ControlCase{{ID: "private-control-current-" + nonce + "-auth", Steps: []evolution.ControlStep{noAuth}}, {ID: "private-control-current-" + nonce + "-stale", Steps: []evolution.ControlStep{stale, read}}}}
	labels := evolution.ControlLabels{Revision: evolution.ControlPrivateRevision, Binding: binding, Labels: []evolution.ControlLabel{{ID: inputs.Cases[0].ID, Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 401, Headers: headers(false, ""), Body: failure("UNAUTHENTICATED", "Bearer credential required", nil)}}}, {ID: inputs.Cases[1].ID, Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 412, Headers: headers(true, testTag(cycle)), Body: failure("STALE_REVISION", "aggregate changed", cycle["revision"])}, {Status: 200, Headers: headers(true, testTag(cycle)), Body: Bytes(cycle)}}}}}
	return suite, inputs, labels
}

func TestControlCurrentActualOwnerNoGain(t *testing.T) {
	if os.Getenv("W16_CURRENT_NATIVE") != "1" {
		t.Skip("explicit bounded current-control native invocation required")
	}
	ctx := context.Background()
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	work := os.Getenv("W16_CURRENT_WORK_DIR")
	if work == "" {
		work = t.TempDir()
	} else {
		work = filepath.Clean(work)
		if err = os.Mkdir(work, 0700); err != nil {
			t.Fatal(err)
		}
	}
	data := filepath.Join(work, "data")
	image, binary, provenance := currentControlBuild(t, root, work)
	evidence := os.Getenv("W16_CURRENT_EVIDENCE_DIR")
	writeEvidence := func(name string, value any) {
		t.Helper()
		if evidence != "" {
			if err := os.WriteFile(filepath.Join(evidence, name), Bytes(value), 0600); err != nil {
				t.Fatal(err)
			}
		}
	}
	writeEvidence("actual-build.json", Object{"binary_hash": Digest(binary), "image_path": image, "source_provenance": provenance, "fixture_work": work})
	r := currentControlResearch(t, root, data)
	f := r.f
	ownerToken := r.owner
	privateRoot := os.Getenv("W16_CURRENT_PROTECTED_DIR")
	if privateRoot == "" {
		privateRoot = filepath.Join(work, "private")
	}
	privateRoot = filepath.Clean(privateRoot)
	writeEvidence("private-locators.json", Object{"database": filepath.Join(data, "researchos.sqlite"), "canary_store": privateRoot, "scope": "SYNTHETIC_FIXTURE_ONLY", "os_independent_identity": false})
	private, err := protectedstore.NewCanary(privateRoot)
	if err != nil {
		t.Fatal(err)
	}
	defer private.Close()
	f.s.Protected = private
	provision := func(id string, roles []string, restricted bool) string {
		t.Helper()
		if err := f.s.ProvisionPrincipal(ctx, Principal{ID: id, Roles: roles, Grants: []Grant{{ProjectID: f.project, Restricted: restricted}}}); err != nil {
			t.Fatal(err)
		}
		token, err := f.s.IssueCredential(ctx, id, 15*time.Minute)
		if err != nil {
			t.Fatal(err)
		}
		return token
	}
	releaseID, verifierID, executorID := "current-control-release", "current-control-verifier", "current-control-executor"
	releaseToken := provision(releaseID, []string{"RELEASE_SERVICE", "SCHEDULER"}, false)
	verifierToken := provision(verifierID, []string{"VERIFIER"}, true)
	executorToken := provision(executorID, []string{"EXECUTOR"}, false)
	requirement := f.requirement()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "Current control API comparison", "original_intent": "Accept native API evidence under unchanged authority", "scope": "PROJECT", "requirement_refs": []any{Ref(requirement, "Requirement")}, "problem_ids": []any{"current-control-proof"}, "deliverables": []any{"verified control API observation"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "bounded current authority fixture"})
	runtime := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "current control fixture observation", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if err = f.s.RegisterOrchestrationFixture(ctx, f.project, Str(runtime, "id")); err != nil {
		t.Fatal(err)
	}
	seal := func(kind string, raw []byte) Object {
		t.Helper()
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	}
	code := seal("CODE", binary)
	prov := seal("REPORT", evolution.Bytes(evolution.ControlBuildProvenance{Schema: evolution.ControlCurrentProfile, Stable: provenance, Candidate: provenance}))
	manifest := seal("REPORT", Bytes(Object{"paths": []any{"internal/domain/research.go"}}))
	rollback := seal("REPORT", Bytes(Object{"scope": evolution.ControlCurrentProfile, "rollback": "no-gain retains same actual stable owner; no switch"}))
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	address := listener.Addr().String()
	listener.Close()
	journal, err := supervisor.OpenReleaseJournal(filepath.Join(work, "release-state"))
	if err != nil {
		t.Fatal(err)
	}
	defer journal.Close()
	log, err := os.Create(filepath.Join(work, "control.log"))
	if err != nil {
		t.Fatal(err)
	}
	defer log.Close()
	driver := &supervisor.ControlFixtureDriver{Journal: journal, WorkDir: root, WebDir: filepath.Join(root, "apps/web"), Listen: address, FixtureStore: privateRoot, Output: log}
	engine, err := supervisor.NewReleaseEngine(journal, driver, driver, func(supervisor.ReleaseAdmission) error { return fmt.Errorf("CURRENT_PROFILE_RELEASE_CLOSED") })
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		state := journal.State()
		if state.PID != 0 {
			stopCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			stopErr := driver.ShutdownFixture(stopCtx)
			cancel()
			if stopErr != nil {
				_ = (supervisor.NativeFixtureDriver{}).Stop(supervisor.ProcessIdentity{PID: state.PID, CreatedNS: state.CreatedNS, ImageSHA256: state.ImageSHA256})
				t.Logf("disposable current fixture cleanup only: %v", stopErr)
			}
		}
		if t.Failed() {
			log.Sync()
			raw, _ := os.ReadFile(log.Name())
			t.Logf("actual control log: %s", raw)
		}
	}()
	if err = engine.BootstrapFixture(ctx, image, data); err != nil {
		t.Fatal(err)
	}
	endpoint, _ := url.Parse("http://" + address)
	f.h = httputil.NewSingleHostReverseProxy(endpoint)
	phases := []any{}
	phase := func(req evolution.ControlCurrentRequest) evolution.ControlCurrentReply {
		t.Helper()
		state := journal.State()
		phaseCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
		defer cancel()
		reply, e := driver.Private(phaseCtx, "CURRENT_CONTROL", supervisor.ReleasePrivateMessage{Snapshot: &state, Request: evolution.Bytes(req)})
		if e != nil {
			phases = append(phases, Object{"phase": req.Phase, "error": e.Error()})
			writeEvidence("phases.json", phases)
			t.Fatalf("current %s: %v", req.Phase, e)
		}
		var result evolution.ControlCurrentReply
		if e = evolution.StrictControlJSON(reply.Result, &result); e != nil {
			t.Fatal(e)
		}
		fmt.Println("W16_CURRENT_PHASE " + string(evolution.Bytes(result)))
		phases = append(phases, result)
		writeEvidence("phases.json", phases)
		return result
	}
	sample := phase(evolution.ControlCurrentRequest{Phase: "SAMPLE", ProjectID: f.project, CycleID: Str(r.cycle, "id"), OwnerToken: ownerToken, StableRef: Ref(code, "Artifact"), CandidateRef: Ref(code, "Artifact"), ProvenanceRef: Ref(prov, "Artifact")})
	if sample.Binding == nil || !sample.OwnerMatches || sample.OSQualified {
		t.Fatal("actual owner sample binding absent")
	}
	suite, inputs, labels := currentControlSuites(*sample.Binding, f.project, r.cycle)
	public := seal("DATASET", evolution.Bytes(suite))
	supervisorID := ID()
	hostRoot := t.TempDir()
	if os.Getenv("W16_CURRENT_WORK_DIR") != "" {
		hostRoot, err = os.MkdirTemp("", "researchos-current-eval-")
		if err != nil {
			t.Fatal(err)
		}
	}
	writeEvidence("private-locators.json", Object{"database": filepath.Join(data, "researchos.sqlite"), "canary_store": privateRoot, "evaluation_root": hostRoot, "scope": "SYNTHETIC_FIXTURE_ONLY", "os_independent_identity": false})
	phase(evolution.ControlCurrentRequest{Phase: "REGISTER", SessionID: sample.SessionID, SupervisorID: supervisorID, ReleasePrincipal: releaseID, HostRoot: hostRoot, SuiteRef: Ref(public, "Artifact"), RollbackRef: Ref(rollback, "Artifact"), ManifestRef: Ref(manifest, "Artifact")})
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	host, err := evolutionHost(tx, f.project)
	if err != nil {
		t.Fatal(err)
	}
	caseIDs, err := f.s.evolutionHostCaseIDs(tx, f.project, host)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	contract := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "paired", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(Object{"expected_case_ids": caseIDs})), "command_key": "experiments.paired-mean-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}, Object{"check_id": "control", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(evolutionHostExpected(host, "REGRESSION"))), "command_key": "evolution.regression-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	contract["contract_hash"] = contractDigest(contract)
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	stop := Object{"wall_time_seconds": 120, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "required-regression", "sandbox-boundary"}}
	experiment := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": nil, "scope": "SYSTEM", "hypothesis": "Same current control executable has no positive business gain", "candidate_ref": Ref(code, "Artifact"), "baseline_refs": []any{Ref(code, "Artifact")}, "input_refs": []any{Ref(public, "Artifact"), Ref(manifest, "Artifact"), Ref(rollback, "Artifact")}, "metrics": []any{Object{"metric_id": "correctness", "description": "native current domain API gates", "unit": "ratio", "operator": "GTE", "target": "1", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	experiment = f.expect(200, "POST", f.path("/experiments/"+Str(experiment, "id")+"/register"), ID(), testTag(experiment), Object{"expected_preregistration_hash": experiment["preregistration_hash"]})
	candidate := f.expect(201, "POST", f.path("/system-candidates"), ID(), f.stateTag(), Object{"scope": "SYSTEM", "candidate_artifact_ref": Ref(code, "Artifact"), "stable_artifact_ref": Ref(code, "Artifact"), "isolated_workspace_id": ID(), "baseline_suite_ref": Ref(public, "Artifact"), "baseline_policy_hash": host["policy_hash"], "changed_paths_manifest_ref": Ref(manifest, "Artifact"), "experiment_id": experiment["id"], "migration_plan_ref": nil, "rollback_plan_ref": Ref(rollback, "Artifact"), "independent_supervisor_id": supervisorID})
	candidate, err = f.s.IsolateEvolutionFixture(ctx, ownerToken, f.project, Str(candidate, "id"))
	if err != nil {
		t.Fatal(err)
	}
	f.token = releaseToken
	candidate = f.expect(200, "POST", f.path("/system-candidates/"+Str(candidate, "id")+"/actions"), ID(), testTag(candidate), Object{"action": "START_EVALUATION", "reason": "bounded current proof", "regression_acceptance_id": nil, "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": nil})
	f.token = ownerToken
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "current control regression", "task_type": "system-candidate", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(requirement, "Requirement")}, "input_refs": evolutionInputs(candidate), "acceptance_contract": contract, "origin_problem_id": "current-control-proof", "candidate_id": candidate["id"], "stop_policy": stop})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen current control contract"})
	if err = f.s.BindEvolutionTask(ctx, ownerToken, f.project, Str(candidate, "id"), Str(task, "id"), "REGRESSION"); err != nil {
		t.Fatal(err)
	}
	if err = f.s.BindExperimentTask(ctx, ownerToken, f.project, Str(experiment, "id"), Str(task, "id")); err != nil {
		t.Fatal(err)
	}
	claim := f.expect(201, "POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task), Object{"runtime_id": runtime["id"], "executor_principal_id": executorID, "context_bundle_id": task["context_bundle_id"]})
	run := &runtimeFixture{f: f, ownerToken: ownerToken, executor: executorID, lease: Str(claim, "lease_token"), task: claim["task"].(map[string]any), run: claim["run"].(map[string]any), registration: runtime}
	experiment, err = f.s.BeginExperiment(ctx, ownerToken, f.project, Str(experiment, "id"), Str(run.run, "id"))
	if err != nil {
		t.Fatal(err)
	}
	registerPrivate := func(raw []byte) Object {
		t.Helper()
		blob, e := private.CreateCanary(ctx, f.project, "application/json", raw)
		if e != nil {
			t.Fatal(e)
		}
		artifact, e := f.s.RegisterProtectedArtifact(ctx, verifierToken, f.project, blob.Ticket, Object{"run_id": nil, "kind": "DATASET", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "input_refs": Empty(), "source_refs": Empty()})
		if e != nil {
			t.Fatal(e)
		}
		return artifact
	}
	inputArtifact, labelArtifact := registerPrivate(evolution.Bytes(inputs)), registerPrivate(evolution.Bytes(labels))
	if err = f.s.RegisterEvolutionHoldoutFixture(ctx, verifierToken, f.project, Str(candidate, "id"), Ref(inputArtifact, "Artifact"), Ref(labelArtifact, "Artifact")); err != nil {
		t.Fatal(err)
	}
	f.token = executorToken
	run.call("/heartbeat", run.heartbeat(), 200)
	frozen := phase(evolution.ControlCurrentRequest{Phase: "FREEZE", SessionID: sample.SessionID, VerifierToken: verifierToken, CandidateID: Str(candidate, "id"), TaskID: Str(task, "id"), RunID: Str(run.run, "id")})
	if os.Getenv("W16_CURRENT_SETUP_ONLY") == "1" {
		t.Log("setup-only diagnostic complete; EVALUATE not invoked")
		return
	}
	evaluated := phase(evolution.ControlCurrentRequest{Phase: "EVALUATE", SessionID: sample.SessionID, VerifierToken: verifierToken, WorkerToken: executorToken, ReleaseToken: releaseToken, Lease: run.heartbeat()})
	if evaluated.ObservationRef == nil {
		t.Fatal("native result reference absent")
	}
	run.refresh()
	run.call("/report", run.report([]any{evaluated.ObservationRef["id"]}, 0), 200)
	f.token = verifierToken
	run.task = f.read("tasks", Str(task, "id"))
	checks := Empty()
	for _, v := range Arr(contract, "checks") {
		check := v.(map[string]any)
		checks = append(checks, Object{"check_id": check["check_id"], "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": check["command_key"], "actual": "request server independent computation", "exit_code": nil, "started_at": nil, "finished_at": nil})
	}
	acceptance := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), Object{"subject_ref": Ref(run.task, "Task"), "run_id": run.run["id"], "contract_hash": contract["contract_hash"], "input_refs": run.task["input_refs"], "artifact_refs": []any{evaluated.ObservationRef}, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{executorID}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": f.state()["policy_revision"], "measurement_mode": "FIXTURE", "reason": "independent current authority computation"})
	var executionRaw string
	if err = f.db.QueryRow("SELECT body FROM evolution_executions WHERE project=? AND candidate=? AND phase='REGRESSION'", f.project, candidate["id"]).Scan(&executionRaw); err != nil {
		t.Fatal(err)
	}
	execution, err := Decode([]byte(executionRaw))
	if err != nil {
		t.Fatal(err)
	}
	observation := execution["observation"].(map[string]any)
	f.token = ownerToken
	experiment = f.read("experiments", Str(experiment, "id"))
	experiment = f.expect(200, "POST", f.path("/experiments/"+Str(experiment, "id")+"/result"), ID(), testTag(experiment), Object{"run_ids": experiment["run_ids"], "results": observation["results"], "outcome": observation["outcome"], "acceptance_id": acceptance["id"]})
	f.token = releaseToken
	candidate = f.read("system-candidates", Str(candidate, "id"))
	candidate = f.expect(200, "POST", f.path("/system-candidates/"+Str(candidate, "id")+"/actions"), ID(), testTag(candidate), Object{"action": "START_CANARY", "reason": "normal no-gain gate must reject", "regression_acceptance_id": acceptance["id"], "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": time.Now().UTC().Add(time.Minute).Format(time.RFC3339Nano)})
	sealed := phase(evolution.ControlCurrentRequest{Phase: "SEAL", SessionID: sample.SessionID, VerifierToken: verifierToken, AcceptanceID: Str(acceptance, "id")})
	repeated := phase(evolution.ControlCurrentRequest{Phase: "EVALUATE", SessionID: sample.SessionID, VerifierToken: verifierToken})
	if !sealed.Current || sealed.OSQualified || !sealed.OwnerMatches || candidate["status"] != "REJECTED" || execution["improved"] != false || Hash(repeated.ObservationRef) != Hash(evaluated.ObservationRef) {
		t.Fatal("current no-gain boundary failed")
	}
	var reserved, recorded int
	if err = f.db.QueryRow("SELECT count(*) FROM evolution_journal WHERE project=? AND candidate=? AND event=?", f.project, candidate["id"], controlCurrentReserved).Scan(&reserved); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT count(*) FROM evolution_journal WHERE project=? AND candidate=? AND event=?", f.project, candidate["id"], controlCurrentRecorded).Scan(&recorded); err != nil {
		t.Fatal(err)
	}
	if reserved != 1 || recorded != 1 {
		t.Fatal("evaluation replayed")
	}
	state := journal.State()
	summary := Object{"profile": evolution.ControlCurrentProfile, "sample": sample, "frozen": frozen, "sealed": sealed, "acceptance": acceptance, "candidate": candidate, "experiment": experiment, "execution_hash": execution["receipt_hash"], "native_owner": Object{"pid": state.PID, "created_ns": state.CreatedNS, "image_hash": state.ImageSHA256, "data_root": state.Data}, "source_provenance": provenance, "normal_gate": "REJECTED", "host_phase": state.Phase, "reservation_count": reserved, "completion_count": recorded, "provider_calls": 0, "os_service_qualified": false, "normal_release_authorized": false}
	fmt.Println("W16_CURRENT_NATIVE_ASSERTION " + string(Bytes(Object{"current": sealed.Current, "owner_matches": sealed.OwnerMatches, "normal_gate": candidate["status"], "host_phase": state.Phase, "reservation_count": reserved, "completion_count": recorded, "proof_hash": sealed.ProofHash, "g1_hash": sealed.G1Hash})))
	if evidence := os.Getenv("W16_CURRENT_EVIDENCE_DIR"); evidence != "" {
		if err = os.WriteFile(filepath.Join(evidence, "current-control-native.json"), Bytes(summary), 0600); err != nil {
			t.Fatal(err)
		}
	}
}
