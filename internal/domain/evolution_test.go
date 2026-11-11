//go:build windows

package domain

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/evaluation/evolution"
	"researchos.local/research-os/ops/supervisor"
	"testing"
	"time"
)

type evolutionFixture struct {
	o                 *orchestrationFixture
	x, experiment     Object
	owner, release    string
	stable, candidate []byte
}

func evoAssert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W16_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": "actual public fixture HTTP, SQLite, AppContainer and independent Task acceptance", "scope": evolution.Scope})))
	if status != "PASS" {
		t.Fatal(id)
	}
}
func evoContract(phase string) Object {
	checks := Empty()
	if phase == "REGRESSION" {
		checks = append(checks, Object{"check_id": "paired", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(Object{"expected_case_ids": evolutionIDs()})), "command_key": "experiments.paired-mean-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
	}
	key := "evolution.regression-v1"
	if phase == "CANARY" {
		key = "evolution.canary-v1"
	}
	checks = append(checks, Object{"check_id": "evolution", "kind": "DETERMINISTIC", "required": true, "expected": string(Bytes(evolutionExpected(phase))), "command_key": key, "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
	c := Object{"contract_revision": 1, "checks": checks, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}
func evoSetup(t *testing.T, variant string) *evolutionFixture {
	return evoSetupMode(t, variant, false)
}

func evoSetupMode(t *testing.T, variant string, releaseMechanism bool) *evolutionFixture {
	t.Helper()
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("RESEARCHOS_GO required")
	}
	build := func(mode string) []byte {
		path := filepath.Join(t.TempDir(), mode+".exe")
		c := exec.Command(goexe, "build", "-ldflags", "-X main.variant="+mode, "-o", path, "../../ops/canary/fixture")
		out, e := c.CombinedOutput()
		if e != nil {
			t.Fatalf("native build: %v %s", e, out)
		}
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	stable, candidate := build("stable"), build(variant)
	o := orchestrationSetup(t)
	f := o.f
	seal := func(kind string, raw []byte) Object {
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	}
	s := seal("CODE", stable)
	c := seal("CODE", candidate)
	suite := seal("DATASET", evolution.Bytes(evolution.Suite()))
	manifest := seal("REPORT", Bytes(Object{"paths": []any{"ops/canary/fixture/main.go"}}))
	rollback := seal("REPORT", Bytes(Object{"restore": "W18 encrypted snapshot to isolated copy; stable exact hash", "scope": evolution.Scope}))
	f.switchPrincipal("fixture-independent-release", []string{"RELEASE_SERVICE", "SCHEDULER"})
	release := f.token
	f.token = o.owner
	supervisorID := ID()
	register := f.s.RegisterEvolutionFixture
	if releaseMechanism {
		register = f.s.RegisterEvolutionReleaseFixture
	}
	if e := register(context.Background(), f.project, supervisorID, "fixture-independent-release", t.TempDir(), Ref(s, "Artifact"), Ref(suite, "Artifact"), Ref(rollback, "Artifact")); e != nil {
		t.Fatal(e)
	}
	source, e := os.ReadFile("../../ops/canary/fixture/main.go")
	if e != nil {
		t.Fatal(e)
	}
	if e = f.s.RegisterEvolutionBuild(context.Background(), f.project, Ref(c, "Artifact"), Ref(manifest, "Artifact"), Digest(source)); e != nil {
		t.Fatal(e)
	}
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	contract := evoContract("REGRESSION")
	stop := Object{"wall_time_seconds": 120, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "required-regression", "sandbox-boundary"}}
	experiment := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": nil, "scope": "SYSTEM", "hypothesis": "fixed required behavior and independent measurable improvement", "candidate_ref": Ref(c, "Artifact"), "baseline_refs": []any{Ref(s, "Artifact")}, "input_refs": []any{Ref(suite, "Artifact"), Ref(manifest, "Artifact"), Ref(rollback, "Artifact")}, "metrics": []any{Object{"metric_id": "correctness", "description": "same frozen cases", "unit": "ratio", "operator": "GTE", "target": "0.75", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	experiment = f.expect(200, "POST", f.path("/experiments/"+Str(experiment, "id")+"/register"), ID(), testTag(experiment), Object{"expected_preregistration_hash": experiment["preregistration_hash"]})
	x := f.expect(201, "POST", f.path("/system-candidates"), ID(), f.stateTag(), Object{"scope": "SYSTEM", "candidate_artifact_ref": Ref(c, "Artifact"), "stable_artifact_ref": Ref(s, "Artifact"), "isolated_workspace_id": ID(), "baseline_suite_ref": Ref(suite, "Artifact"), "baseline_policy_hash": Digest(evolution.Bytes(evolution.Policy())), "changed_paths_manifest_ref": Ref(manifest, "Artifact"), "experiment_id": experiment["id"], "migration_plan_ref": nil, "rollback_plan_ref": Ref(rollback, "Artifact"), "independent_supervisor_id": supervisorID})
	x, e = f.s.IsolateEvolutionFixture(context.Background(), o.owner, f.project, Str(x, "id"))
	if e != nil {
		t.Fatal(e)
	}
	v := &evolutionFixture{o, x, experiment, o.owner, release, stable, candidate}
	v.action("START_EVALUATION", nil, 200)
	return v
}
func (e *evolutionFixture) action(action string, receipt any, status int) Object {
	f := e.o.f
	f.token = e.release
	b := Object{"action": action, "regression_acceptance_id": receipt, "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": nil, "reason": "bounded explicit fixture action"}
	if action == "START_CANARY" {
		b["observation_deadline"] = time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano)
	}
	result := f.expect(status, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(e.x), b)
	if status == 200 {
		e.x = result
	}
	return result
}
func (e *evolutionFixture) run(phase string) (*runtimeFixture, Object, Object) {
	o, f := e.o, e.o.f
	f.token = e.owner
	c := evoContract(phase)
	if phase == "REGRESSION" {
		c = e.experiment["acceptance_contract"].(map[string]any)
	}
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(o.goal, "id"))), Object{"goal_id": o.goal["id"], "title": "evolution " + phase, "task_type": "system-candidate", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": evolutionInputs(e.x), "acceptance_contract": c, "origin_problem_id": "orchestration-problem", "candidate_id": e.x["id"], "stop_policy": e.experiment["stop_policy"]})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen system comparison"})
	if err := f.s.BindEvolutionTask(context.Background(), e.owner, f.project, Str(e.x, "id"), Str(task, "id"), phase); err != nil {
		f.t.Fatal(err)
	}
	if phase == "REGRESSION" {
		if err := f.s.BindExperimentTask(context.Background(), e.owner, f.project, Str(e.experiment, "id"), Str(task, "id")); err != nil {
			f.t.Fatal(err)
		}
	}
	r := o.claim(task)
	if phase == "REGRESSION" {
		var err error
		e.experiment, err = f.s.BeginExperiment(context.Background(), e.owner, f.project, Str(e.experiment, "id"), Str(r.run, "id"))
		if err != nil {
			f.t.Fatal(err)
		}
	}
	r.call("/heartbeat", r.heartbeat(), 200)
	record, err := f.s.ExecuteEvolutionFixture(context.Background(), f.token, e.release, f.project, Str(e.x, "id"), Str(r.run, "id"), r.heartbeat())
	if err != nil {
		f.t.Fatal(err)
	}
	obs := r.observation("SETTLED", true)
	obs["artifacts"] = record["runtime_artifacts"]
	r.observe(obs)
	r.call("/report", r.report([]any{record["artifact_id"]}, 0), 200)
	f.token = e.owner
	r.task = f.read("tasks", Str(task, "id"))
	a := f.read("artifacts", Str(record, "artifact_id"))
	request := o.acceptance(r, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), request)
	if phase == "REGRESSION" {
		f.token = e.owner
		ob := record["observation"].(map[string]any)
		e.experiment = f.expect(200, "POST", f.path("/experiments/"+Str(e.experiment, "id")+"/result"), ID(), testTag(e.experiment), Object{"run_ids": e.experiment["run_ids"], "results": ob["results"], "outcome": ob["outcome"], "acceptance_id": receipt["id"]})
	}
	f.token = e.owner
	e.x = f.read("system-candidates", Str(e.x, "id"))
	if dir := os.Getenv("W16_EVIDENCE_DIR"); dir != "" {
		if err = os.WriteFile(filepath.Join(dir, Str(e.x, "id")+"-"+phase+".json"), Bytes(Object{"execution": record, "acceptance": receipt, "candidate": e.x, "experiment": e.experiment}), 0600); err != nil {
			f.t.Fatal(err)
		}
	}
	return r, record, receipt
}
func TestW16C09(t *testing.T) {
	e := evoSetup(t, "regression")
	_, r, a := e.run("REGRESSION")
	evoAssert(t, "C09-REQUIRED", false, r["required_passed"])
	e.action("START_CANARY", a["id"], 200)
	evoAssert(t, "C09-01", "REJECTED", e.x["status"])
	e.assertStable("C09-02")
}
func TestW16C12(t *testing.T) {
	e := evoSetup(t, "degrade")
	_, r, a := e.run("REGRESSION")
	evoAssert(t, "C12-ADMITTED", true, r["improved"])
	e.action("START_CANARY", a["id"], 200)
	_, record, _ := e.run("CANARY")
	evoAssert(t, "C12-01", true, record["observed_regression"])
	evoAssert(t, "C12-02", "FROZEN", e.x["status"])
	e.action("PROMOTE", nil, 409)
	e.action("START_CANARY", a["id"], 409)
	var raw string
	if err := e.o.f.db.QueryRow("SELECT body FROM evolution_journal WHERE project=? AND candidate=? AND event='ROLLBACK_STARTED'", e.o.f.project, e.x["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	j, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	evoAssert(t, "C12-03", true, j["observed_regression"] == true && j["self_score_authority"] == "NONE" && record["baseline_hash"] != record["candidate_hash"] && record["restore"] != nil && record["stable_health"] != nil)
	e.save("C12-rollback-trigger", j)
	e.assertStable("C12-STABLE")
}

func (e *evolutionFixture) save(name string, value any) {
	if dir := os.Getenv("W16_EVIDENCE_DIR"); dir != "" {
		if err := os.WriteFile(filepath.Join(dir, Str(e.x, "id")+"-"+name+".json"), Bytes(value), 0600); err != nil {
			e.o.f.t.Fatal(err)
		}
	}
}
func (e *evolutionFixture) assertStable(id string) {
	f := e.o.f
	var active, state string
	if err := f.db.QueryRow("SELECT active_hash,state FROM evolution_slots WHERE project=?", f.project).Scan(&active, &state); err != nil {
		f.t.Fatal(err)
	}
	health := supervisor.Invoke(context.Background(), e.stable, "HEALTH", nil)
	result, err := supervisor.Verify(health, Digest(e.stable))
	if err != nil {
		f.t.Fatal(err)
	}
	task := e.o.task("unrelated-after-candidate", Empty(), Empty())
	r := e.o.claim(task)
	a := e.o.report(r, []byte(`{"result":"verified"}`))
	req := e.o.acceptance(r, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), req)
	evoAssert(f.t, id, true, active == Digest(e.stable) && state == "STABLE" && result.RequiredPassed && receipt["verdict"] == "PASS")
	e.save(id, Object{"stable_health": health, "active_hash": active, "slot_state": state, "unrelated_task_acceptance": receipt})
}
func TestW16C10(t *testing.T) {
	e := evoSetup(t, "gate_tamper")
	r, record, a := e.run("REGRESSION")
	f := e.o.f
	pair, err := decodePair(record["pair"])
	if err != nil {
		t.Fatal(err)
	}
	denied := true
	for _, row := range pair.CandidateResult.Rows {
		if len(row.WriteDenied) != 4 {
			denied = false
		}
		for _, v := range row.WriteDenied {
			denied = denied && v
		}
	}
	f.token = e.owner
	baseline := Hash(evolutionPlan(e.x))
	attacks := []string{"evaluation/evolution/required-tests.json", "evaluation/evolution/labels.json", "ops/supervisor/permissions.json", "ops/supervisor/fixture_windows.go"}
	for _, path := range attacks {
		manifest := f.artifact(Object{"paths": []any{path}}, Empty())
		err = f.s.RegisterEvolutionBuild(context.Background(), f.project, e.x["candidate_artifact_ref"].(map[string]any), Ref(manifest, "Artifact"), Digest([]byte(path)))
		if err == nil {
			t.Fatalf("accepted forbidden build path %s", path)
		}
	}
	evoAssert(t, "C10-01", true, denied && pair.StablePreserved && baseline == Hash(evolutionPlan(f.read("system-candidates", Str(e.x, "id")))))
	artifact := f.read("artifacts", Str(record, "artifact_id"))
	req := e.o.acceptance(r, artifact)
	f.token, err = f.s.IssueCredential(context.Background(), r.executor, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	forged := f.expect(403, "POST", f.path("/acceptances"), ID(), testTag(r.task), req)
	f.token = e.owner
	body := Object{"action": "START_CANARY", "regression_acceptance_id": a["id"], "canary_acceptance_id": nil, "rollback_verified_receipt_id": nil, "observation_deadline": time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), "reason": "candidate author self release"}
	self := f.expect(403, "POST", f.path("/system-candidates/"+Str(e.x, "id")+"/actions"), ID(), testTag(e.x), body)
	evoAssert(t, "C10-02", true, forged != nil && self != nil)
	// The existing independent change workflow holds a rule research proposal;
	// it cannot edit SystemCandidate, host policy or apply its own acceptance.
	f.switchPrincipal("fixture-independent-rule-author", []string{"OWNER", "PLANNER", "EXECUTOR"})
	oldOwner := f.owner
	f.owner = "fixture-independent-rule-author"
	samples := f.artifact(Object{"purpose": "future rule research only; not used to evaluate current candidate", "cases": []any{Object{"id": "new-independent-rule-sample", "a": 2, "b": 4, "expected": 6}}}, Empty())
	value := f.artifact("Independently review a future rule revision; preserve old suite and new separate samples", []any{e.x["baseline_suite_ref"], record["artifact_ref"], Ref(samples, "Artifact")})
	state := f.state()
	proposal := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{"title": "Independent evolution rule research", "reason": "separate old-suite results and independent new samples required", "base_state_revision": state["revision"], "edits": []any{Object{"target_ref": Ref(e.o.req, "Requirement"), "field": "text", "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": "future rule requirements only"}}, "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"retain current host baseline"}})
	evoAssert(t, "C10-03", true, proposal["acceptance_id"] == nil && proposal["applied_state_revision"] == nil && baseline == Hash(evolutionPlan(f.read("system-candidates", Str(e.x, "id")))))
	e.save("C10-attacks", Object{"forged_acceptance": forged, "self_release": self, "rule_proposal": proposal, "rule_proposal_author": f.owner, "independent_samples": samples, "baseline_plan_hash": baseline, "protected_hashes": pair.ProtectedHashes, "native_write_denied": denied})
	f.owner = oldOwner
	e.action("FREEZE", nil, 200)
}
func TestW16C20(t *testing.T) {
	e := evoSetup(t, "rubric_only")
	private := prepareC20Private(t, e)
	_, record, a := e.run("REGRESSION")
	pair, err := decodePair(record["pair"])
	if err != nil {
		t.Fatal(err)
	}
	e.action("START_CANARY", a["id"], 200)
	evoAssert(t, "C20-01", true, record["improved"] == false && record["holdout_proof_hash"] == private.proof["content_hash"] && e.x["status"] == "REJECTED")
	e.save("C20-promotion-rejection", e.x)
	evoAssert(t, "C20-02", true, pair.BaselineResult.Rows[0].SelfScore < pair.CandidateResult.Rows[0].SelfScore && pair.BaselineResult.Rows[0].Rubric != pair.CandidateResult.Rows[0].Rubric && Hash(pair.BaselineResult.Values) == Hash(pair.CandidateResult.Values) && pair.Baseline.InputHash == pair.Candidate.InputHash && pair.SuiteHash == record["suite_hash"])
	evoAssert(t, "C20-03", true, record["improved"] == false && e.experiment["outcome"] == "NO_IMPROVEMENT" && private.verdict.OutcomesEqual && !private.verdict.Gain)
	c20PrivateConclude(t, e, private, record)
	private.verifyReopened(t, e)
	e.save("C20-conclusion", Object{"quality_improved": false, "real_world_gain": "NOT_ESTABLISHED", "private_fixture_holdout": "FROZEN_AND_VERIFIED", "formal_live_holdout": "NOT_RUN", "fixture_outcomes_unchanged": true, "private_proof_hash": private.proof["content_hash"], "old_rubric": pair.BaselineResult.Rows[0].Rubric, "new_rubric": pair.CandidateResult.Rows[0].Rubric, "model_revision": "NONE", "experiment_outcome": e.experiment["outcome"], "project_closed": false, "scope": evolution.Scope})
}
func TestW16A16Partial(t *testing.T) {
	for _, variant := range []string{"canary_startup_failure", "canary_hang"} {
		t.Run(variant, func(t *testing.T) {
			e := evoSetup(t, variant)
			_, _, a := e.run("REGRESSION")
			e.action("START_CANARY", a["id"], 200)
			_, record, _ := e.run("CANARY")
			evoAssert(t, "A16-PARTIAL-"+variant, true, record["observed_regression"] == true && e.x["status"] == "FROZEN" && record["restore"] != nil)
			e.assertStable("A16-PARTIAL-STABLE-" + variant)
		})
	}
}
