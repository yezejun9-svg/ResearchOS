//go:build windows

package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"researchos.local/research-os/adapters/protectedstore"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
)

var controlBuildOnce sync.Once
var controlBinary []byte
var controlSource string
var controlBuildError error

func controlNativeBuild(t *testing.T) ([]byte, string) {
	t.Helper()
	controlBuildOnce.Do(func() {
		goexe := os.Getenv("RESEARCHOS_GO")
		if goexe == "" {
			controlBuildError = fmt.Errorf("RESEARCHOS_GO required")
			return
		}
		files := map[string]string{}
		for _, dir := range []string{"../../apps/control", "../../internal", "../../adapters", "../../evaluation", "../../ops"} {
			if err := filepath.WalkDir(dir, func(path string, entry os.DirEntry, err error) error {
				if err != nil {
					return err
				}
				if !entry.IsDir() && strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go") {
					raw, e := os.ReadFile(path)
					if e != nil {
						return e
					}
					files[filepath.ToSlash(path)] = Digest(raw)
				}
				return nil
			}); err != nil {
				controlBuildError = err
				return
			}
		}
		for _, path := range []string{"../../go.mod", "../../go.sum"} {
			raw, err := os.ReadFile(path)
			if err != nil {
				controlBuildError = err
				return
			}
			files[path] = Digest(raw)
		}
		controlSource = Hash(files)
		if dir := os.Getenv("W16_CONTROL_EVIDENCE_DIR"); dir != "" {
			if err := os.WriteFile(filepath.Join(dir, "control-source-files.json"), Bytes(files), 0600); err != nil {
				controlBuildError = err
				return
			}
		}
		path := filepath.Join(t.TempDir(), "control.exe")
		cmd := exec.Command(goexe, "build", "-o", path, "../../apps/control")
		if raw, err := cmd.CombinedOutput(); err != nil {
			controlBuildError = fmt.Errorf("native control build: %w %s", err, raw)
			return
		}
		controlBinary, controlBuildError = os.ReadFile(path)
	})
	if controlBuildError != nil {
		t.Fatal(controlBuildError)
	}
	return controlBinary, controlSource
}

func controlAssert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W16_CONTROL_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "scope": "REAL_CONTROL_EXE_OFFLINE_API_FIXTURE", "provider_calls": 0, "os_service_qualified": false})))
	if status != "PASS" {
		t.Fatal(id)
	}
}

func controlSnapshotFixture(t *testing.T) (evolution.ControlBundle, evolution.ControlSuite, evolution.ControlInputs, evolution.ControlLabels) {
	t.Helper()
	r := researchSetup(t, false)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	file := filepath.Join(t.TempDir(), "frozen.sqlite")
	if _, err := r.f.db.Exec("VACUUM INTO ?", file); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}
	root, err := filepath.Abs("../..")
	if err != nil {
		t.Fatal(err)
	}
	bundle, err := PrepareEvolutionControlBundle(context.Background(), raw, root, r.f.project, Str(r.cycle, "id"))
	if err != nil {
		t.Fatal(err)
	}
	if err = validateEvolutionControlBundle(context.Background(), bundle); err != nil {
		t.Fatal(err)
	}
	path := "/v1/projects/" + r.f.project + "/research-cycles/" + Str(r.cycle, "id")
	read := evolution.ControlStep{Method: "GET", Path: path, Authenticated: true}
	close := evolution.ControlStep{Method: "POST", Path: path + "/close", Authenticated: true, Body: Bytes(Object{"requested_status": "COMPLETE", "outcome_summary": "frozen public coverage gate"}), ETag: testTag(r.cycle), IdempotencyKey: "public-control-close"}
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
	errorBody := func(code, message string, current any) json.RawMessage {
		return Bytes(Object{"code": code, "message": message, "retryable": false, "current_revision": current, "details": Empty()})
	}
	suite := evolution.ControlSuite{Inputs: evolution.ControlInputs{Revision: evolution.ControlPublicRevision, Binding: bundle.Binding, Cases: []evolution.ControlCase{
		{ID: "public-control-read-cycle", Steps: []evolution.ControlStep{read}},
		{ID: "public-control-refuse-false-complete", Steps: []evolution.ControlStep{close, read}},
	}}, Labels: evolution.ControlLabels{Revision: evolution.ControlPublicRevision, Binding: bundle.Binding, Labels: []evolution.ControlLabel{
		{ID: "public-control-read-cycle", Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 200, Headers: headers(true, testTag(r.cycle)), Body: Bytes(r.cycle)}}},
		{ID: "public-control-refuse-false-complete", Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 422, Headers: headers(true, ""), Body: errorBody("GATE_FAILED", "requested cycle status differs from verified coverage and experiments: BLOCKED", nil)}, {Status: 200, Headers: headers(true, testTag(r.cycle)), Body: Bytes(r.cycle)}}},
	}}}
	noAuth := read
	noAuth.Authenticated = false
	stale := close
	stale.ETag = "\"r999999\""
	stale.IdempotencyKey = "private-control-stale"
	stale.Body = Bytes(Object{"requested_status": "COMPLETE", "outcome_summary": "frozen private stale revision"})
	nonce := ID()
	inputs := evolution.ControlInputs{Revision: evolution.ControlPrivateRevision, Binding: bundle.Binding, Cases: []evolution.ControlCase{{ID: "private-control-" + nonce + "-auth", Steps: []evolution.ControlStep{noAuth}}, {ID: "private-control-" + nonce + "-stale", Steps: []evolution.ControlStep{stale, read}}}}
	labels := evolution.ControlLabels{Revision: evolution.ControlPrivateRevision, Binding: bundle.Binding, Labels: []evolution.ControlLabel{
		{ID: inputs.Cases[0].ID, Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 401, Headers: headers(false, ""), Body: errorBody("UNAUTHENTICATED", "Bearer credential required", nil)}}},
		{ID: inputs.Cases[1].ID, Required: true, Unchanged: true, Results: []evolution.ControlHTTPResult{{Status: 412, Headers: headers(true, testTag(r.cycle)), Body: errorBody("STALE_REVISION", "aggregate changed", r.cycle["revision"])}, {Status: 200, Headers: headers(true, testTag(r.cycle)), Body: Bytes(r.cycle)}}},
	}}
	if err = evolution.ValidateControlDataset(suite.Inputs, suite.Labels); err != nil {
		t.Fatal(err)
	}
	if err = evolution.ValidateControlDataset(inputs, labels); err != nil {
		t.Fatal(err)
	}
	if dir := os.Getenv("W16_CONTROL_EVIDENCE_DIR"); dir != "" {
		for name, value := range map[string]any{"public-bundle": bundle, "public-suite": suite} {
			if err = os.WriteFile(filepath.Join(dir, t.Name()+"-"+name+".json"), evolution.Bytes(value), 0600); err != nil {
				t.Fatal(err)
			}
		}
	}
	return bundle, suite, inputs, labels
}

func TestW16ControlReplayNative(t *testing.T) {
	binary, source := controlNativeBuild(t)
	ordinary := filepath.Join(t.TempDir(), "control.exe")
	if err := os.WriteFile(ordinary, binary, 0700); err != nil {
		t.Fatal(err)
	}
	refusal, refusalErr := exec.Command(ordinary, "--fixture-control-replay", filepath.Join(t.TempDir(), "absent-request.json")).CombinedOutput()
	controlAssert(t, "REAL-EXE-NON-APPCONTAINER-REFUSED", true, refusalErr != nil && strings.Contains(string(refusal), "requires AppContainer"))
	bundle, suite, _, _ := controlSnapshotFixture(t)
	plan := Digest([]byte("reviewed-control-protocol-baseline"))
	suiteHash := Digest(evolution.Bytes(suite))
	proof, err := supervisor.EvaluateControl(context.Background(), binary, binary, source, source, bundle, suite.Inputs, Digest(evolution.Bytes(suite.Labels)), plan, suiteHash)
	if err != nil {
		t.Fatal(err)
	}
	v, err := supervisor.CheckControl(proof, suite.Inputs, suite.Labels, plan, Digest(binary), Digest(binary), source, source, suiteHash)
	if err != nil {
		t.Fatal(err)
	}
	controlAssert(t, "SAME-CONTROL-REAL-API-CORRECT", []int{2, 2}, []int{v.BaselineCorrect, v.CandidateCorrect})
	controlAssert(t, "SAME-CONTROL-NO-GAIN", true, v.OutcomesEqual && !v.Gain && v.RequiredPassed)
	for _, mutation := range []string{"exe", "protocol", "snapshot", "source", "calculator", "receipt"} {
		var changed supervisor.ControlProof
		if err = evolution.StrictControlJSON(Bytes(proof), &changed); err != nil {
			t.Fatal(err)
		}
		switch mutation {
		case "exe":
			changed.CandidateHash = Digest([]byte("another executable"))
		case "protocol":
			changed.Binding.Protocol = "private-r2-fixture-v1"
		case "snapshot":
			changed.Binding.AuthorityGeneration = Digest([]byte("later generation"))
		case "source":
			changed.CandidateSourceHash = Digest([]byte("unreviewed source"))
		case "calculator":
			changed.Profile = evolution.HoldoutRevision
		case "receipt":
			changed.Pairs[0].Candidate.Receipt.CleanupComplete = false
		}
		_, err = supervisor.CheckControl(changed, suite.Inputs, suite.Labels, plan, Digest(binary), Digest(binary), source, source, suiteHash)
		controlAssert(t, "PROOF-REFUSES-"+mutation, true, err != nil)
	}
	if dir := os.Getenv("W16_CONTROL_EVIDENCE_DIR"); dir != "" {
		if err = os.WriteFile(filepath.Join(dir, "public-control-native-proof.json"), Bytes(proof), 0600); err != nil {
			t.Fatal(err)
		}
	}
}

func controlExperimentSetup(t *testing.T) (*evolutionFixture, evolution.ControlInputs, evolution.ControlLabels) {
	t.Helper()
	binary, source := controlNativeBuild(t)
	bundle, suite, inputs, labels := controlSnapshotFixture(t)
	o := orchestrationSetup(t)
	f := o.f
	seal := func(kind string, raw []byte) Object {
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	}
	code := seal("CODE", binary)
	public := seal("DATASET", evolution.Bytes(suite))
	snapshot := seal("DATASET", evolution.Bytes(bundle))
	manifest := seal("REPORT", Bytes(Object{"paths": []any{"internal/domain/research.go"}}))
	rollback := seal("REPORT", Bytes(Object{"scope": evolution.ControlProfile, "rollback": "no-gain retains original stable; no switch"}))
	f.switchPrincipal("control-independent-release", []string{"RELEASE_SERVICE", "SCHEDULER"})
	release := f.token
	f.token = o.owner
	supervisorID := ID()
	if err := f.s.RegisterEvolutionControlFixture(context.Background(), f.project, supervisorID, "control-independent-release", t.TempDir(), Ref(code, "Artifact"), Ref(public, "Artifact"), Ref(rollback, "Artifact"), Ref(snapshot, "Artifact"), source); err != nil {
		t.Fatal(err)
	}
	if err := f.s.RegisterEvolutionBuild(context.Background(), f.project, Ref(code, "Artifact"), Ref(manifest, "Artifact"), source); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, f.project)
	if err != nil {
		t.Fatal(err)
	}
	ids, err := f.s.evolutionHostCaseIDs(tx, f.project, h)
	if err != nil {
		t.Fatal(err)
	}
	tx.Rollback()
	contract := Object{"contract_revision": 1, "checks": []any{
		Object{"check_id": "paired", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(Object{"expected_case_ids": ids})), "command_key": "experiments.paired-mean-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil},
		Object{"check_id": "control", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(evolutionHostExpected(h, "REGRESSION"))), "command_key": "evolution.regression-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil},
	}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	contract["contract_hash"] = contractDigest(contract)
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	stop := Object{"wall_time_seconds": 120, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "required-regression", "sandbox-boundary"}}
	experiment := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": nil, "scope": "SYSTEM", "hypothesis": "Exact new control protocol baseline has no business gain", "candidate_ref": Ref(code, "Artifact"), "baseline_refs": []any{Ref(code, "Artifact")}, "input_refs": []any{Ref(public, "Artifact"), Ref(manifest, "Artifact"), Ref(rollback, "Artifact")}, "metrics": []any{Object{"metric_id": "correctness", "description": "frozen real domain API gates", "unit": "ratio", "operator": "GTE", "target": "1", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	experiment = f.expect(200, "POST", f.path("/experiments/"+Str(experiment, "id")+"/register"), ID(), testTag(experiment), Object{"expected_preregistration_hash": experiment["preregistration_hash"]})
	x := f.expect(201, "POST", f.path("/system-candidates"), ID(), f.stateTag(), Object{"scope": "SYSTEM", "candidate_artifact_ref": Ref(code, "Artifact"), "stable_artifact_ref": Ref(code, "Artifact"), "isolated_workspace_id": ID(), "baseline_suite_ref": Ref(public, "Artifact"), "baseline_policy_hash": h["policy_hash"], "changed_paths_manifest_ref": Ref(manifest, "Artifact"), "experiment_id": experiment["id"], "migration_plan_ref": nil, "rollback_plan_ref": Ref(rollback, "Artifact"), "independent_supervisor_id": supervisorID})
	x, err = f.s.IsolateEvolutionFixture(context.Background(), o.owner, f.project, Str(x, "id"))
	if err != nil {
		t.Fatal(err)
	}
	e := &evolutionFixture{o: o, x: x, experiment: experiment, owner: o.owner, release: release, stable: binary, candidate: binary}
	e.action("START_EVALUATION", nil, 200)
	return e, inputs, labels
}

func TestW16ControlBusinessNoGain(t *testing.T) {
	e, inputs, labels := controlExperimentSetup(t)
	f := e.o.f
	privateRoot := filepath.Join(t.TempDir(), "private-control")
	if root := os.Getenv("W16_CONTROL_PROTECTED_EVIDENCE_DIR"); root != "" {
		privateRoot = root
	}
	store, err := protectedstore.NewCanary(privateRoot)
	if err != nil {
		t.Fatal(err)
	}
	defer store.Close()
	f.s.Protected = store
	verifier := Principal{ID: "control-current-independent-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, Restricted: true}}}
	if err = f.s.ProvisionPrincipal(context.Background(), verifier); err != nil {
		t.Fatal(err)
	}
	token, err := f.s.IssueCredential(context.Background(), verifier.ID, 10*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	register := func(raw []byte) Object {
		blob, err := store.CreateCanary(context.Background(), f.project, "application/json", raw)
		if err != nil {
			t.Fatal(err)
		}
		a, err := f.s.RegisterProtectedArtifact(context.Background(), token, f.project, blob.Ticket, Object{"run_id": nil, "kind": "DATASET", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "input_refs": Empty(), "source_refs": Empty()})
		if err != nil {
			t.Fatal(err)
		}
		return a
	}
	i, l := register(evolution.Bytes(inputs)), register(evolution.Bytes(labels))
	if err = f.s.RegisterEvolutionHoldoutFixture(context.Background(), token, f.project, Str(e.x, "id"), Ref(i, "Artifact"), Ref(l, "Artifact")); err != nil {
		t.Fatal(err)
	}
	private, err := f.s.EvaluateEvolutionHoldoutFixture(context.Background(), token, f.project, Str(e.x, "id"))
	if err != nil {
		t.Fatal(err)
	}
	summary := private["summary"].(map[string]any)
	controlAssert(t, "PRIVATE-CONTROL-SAME-BUILD-NO-GAIN", true, summary["gain"] == false && summary["outcomes_equal"] == true && Hash(summary["candidate_correct"]) == Hash(2))
	f.token = e.owner
	_, record, receipt := e.run("REGRESSION")
	controlAssert(t, "NORMAL-TASK-RUN-EXPERIMENT-ACCEPTANCE", true, receipt["verdict"] == "PASS" && record["evaluation_profile"] == evolution.ControlProfile && record["required_passed"] == true && record["improved"] == false)
	e.action("START_CANARY", receipt["id"], 200)
	controlAssert(t, "NO-GAIN-CANDIDATE-REJECTED", "REJECTED", e.x["status"])
	var active, state string
	var effects, operations int
	if err = f.db.QueryRow("SELECT active_hash,state FROM evolution_slots WHERE project=?", f.project).Scan(&active, &state); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT count(*) FROM resource_effects WHERE project=?", f.project).Scan(&effects); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT count(*) FROM evolution_release_operations WHERE project=?", f.project).Scan(&operations); err != nil {
		t.Fatal(err)
	}
	controlAssert(t, "STABLE-RETAINED-NO-SWITCH-EFFECT", true, active == Digest(e.stable) && state == "STABLE" && effects == 0 && operations == 0)
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	frozen, present, err := evolutionHoldoutEntry(tx, f.project, Str(e.x, "id"), "HOLDOUT_FROZEN")
	if err != nil || !present {
		t.Fatal(err)
	}
	evaluated, present, err := evolutionHoldoutEntry(tx, f.project, Str(e.x, "id"), "HOLDOUT_EVALUATED")
	if err != nil || !present {
		t.Fatal(err)
	}
	h, err := evolutionHost(tx, f.project)
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range []string{"revision", "protocol", "control_binding", "stable_source_hash"} {
		changed := copyObject(frozen)
		changed[key] = "private-r2-fixture-v1"
		_, _, err = f.s.controlHoldoutVerdict(context.Background(), tx, f.project, e.x, h, changed, evaluated)
		controlAssert(t, "CURRENT-PROOF-REFUSES-"+key, true, err != nil)
	}
	_, proofRaw, err := f.s.evolutionPrivateBytes(context.Background(), tx, f.project, evaluated["proof_ref"].(map[string]any))
	if err != nil {
		t.Fatal(err)
	}
	var proof supervisor.ControlProof
	if err = evolution.StrictControlJSON(proofRaw, &proof); err != nil {
		t.Fatal(err)
	}
	controlAssert(t, "PRIVATE-REAL-CONTROL-INVOCATIONS", 2, len(proof.Pairs))
	controlAssert(t, "PRIVATE-RAW-IS-VERIFIER-ONLY", private["proof_sha256"], Digest(proofRaw))
	tx.Rollback()
	if err = f.s.RevokePrincipal(context.Background(), verifier.ID); err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	_, _, err = f.s.evolutionHoldoutVerdict(context.Background(), tx, f.project, e.x)
	controlAssert(t, "CURRENT-VERIFIER-REVOCATION-REFUSED", true, err != nil)
	err = f.s.evolutionRecordValid(tx, f.project, e.x, record)
	controlAssert(t, "CURRENT-REGRESSION-REUSE-REVOKED", true, err != nil)
	tx.Rollback()
	if dir := os.Getenv("W16_CONTROL_EVIDENCE_DIR"); dir != "" {
		safe := Object{"execution": record, "acceptance": receipt, "candidate": e.x, "experiment": e.experiment, "private_summary": summary, "private_proof_hash": Digest(proofRaw), "private_proof_ref": evaluated["proof_ref"], "private_raw_published": false, "active_hash": active, "slot_state": state, "switch_effect_count": effects, "release_operation_count": operations}
		if err = os.WriteFile(filepath.Join(dir, "control-business-no-gain.json"), Bytes(safe), 0600); err != nil {
			t.Fatal(err)
		}
	}
}
