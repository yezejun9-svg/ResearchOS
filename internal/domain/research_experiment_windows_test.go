//go:build windows

package domain

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"testing"
	"time"
)

func TestResearchOfflineNativeExperimentAndProgress(t *testing.T) {
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		t.Fatal("RESEARCHOS_GO required")
	}
	binary := filepath.Join(t.TempDir(), "native.exe")
	if out, err := exec.Command(goexe, "build", "-o", binary, "../../adapters/evaluation/cmd").CombinedOutput(); err != nil {
		t.Fatalf("native build: %v %s", err, out)
	}
	executable, err := os.ReadFile(binary)
	if err != nil {
		t.Fatal(err)
	}
	f := contextFixture(t)
	owner := f.token
	seal := func(kind string, raw []byte) Object {
		f.token = owner
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	}
	candidate := seal("CODE", []byte(`{"mode":"EVIDENCE_RULE_V1"}`))
	baseline := seal("CODE", []byte(`{"mode":"ALWAYS_ADOPT_V1"}`))
	tool := seal("CODE", executable)
	dataset := seal("DATASET", []byte(`{"cases":[{"id":"s1","input":{"evidence_present":true,"evidence_current":true,"hard_checks_passed":true,"measured_net_gain_positive":true},"expected_decision":"ADOPT"},{"id":"s2","input":{"evidence_present":false,"evidence_current":true,"hard_checks_passed":true,"measured_net_gain_positive":true},"expected_decision":"REJECT"}]}`))
	if err = f.s.RegisterNativeEvaluationTool(context.Background(), f.project, Str(tool, "content_hash")); err != nil {
		t.Fatal(err)
	}
	contract := experimentContract()
	Arr(contract, "checks")[0].(map[string]any)["expected"] = `{"expected_case_ids":["s1","s2"],"native_execution":true}`
	contract["contract_hash"] = contractDigest(contract)
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	template := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": nil, "scope": "PROJECT", "hypothesis": "evidence rule improves accuracy", "candidate_ref": Ref(candidate, "Artifact"), "baseline_refs": []any{Ref(baseline, "Artifact")}, "input_refs": []any{Ref(dataset, "Artifact"), Ref(tool, "Artifact")}, "metrics": []any{Object{"metric_id": "accuracy", "description": "paired accuracy", "unit": "ratio", "operator": "GTE", "target": "1", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "sandbox-violation"}}, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	template = f.expect(200, "POST", f.path("/experiments/"+Str(template, "id")+"/register"), ID(), testTag(template), Object{"expected_preregistration_hash": template["preregistration_hash"]})
	statement := "请持续监控当前项目，按现有配置定期生成研究报告，并运行已预注册实验，直到我暂停或取消。"
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": statement, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "explicit registered experiment monitor", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "confirmed", "source_validation_refs": Empty()})
	var gid, tid string
	if err = f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); err != nil {
		t.Fatal(err)
	}
	_, goal, o := acceptMonitorPlanningFixture(t, f, req, f.read("goals", gid), f.read("tasks", tid), func(b *GoalBrief) { b.Monitor.RequiredExperimentRefs = []Object{Ref(template, "Experiment")} })
	advance := func() {
		t.Helper()
		tx, e := f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		p, e := authenticate(tx, o.owner)
		if e == nil {
			e = f.s.advanceResearchProject(tx, p, f.project, time.Now().UTC())
		}
		if e == nil {
			e = tx.Commit()
		}
		tx.Rollback()
		if e != nil {
			t.Fatal(e)
		}
	}
	advance()
	if err = f.db.QueryRow("SELECT task,experiment FROM research_cycle_work WHERE project=? AND stage='experiment'", f.project).Scan(&tid, &gid); err != nil {
		t.Fatal(err)
	}
	f.token = o.owner
	task := f.read("tasks", tid)
	run := o.claim(task)
	run.call("/heartbeat", run.heartbeat(), 200)
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	work, err := loadResearchWork(tx, f.project, tid)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	frame := rt.BridgeFrame{Key: "experiment-" + work.Key, Sequence: 1}
	payload := Object{"logical_key": work.Key}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	c := &RuntimeCoordinator{service: f.s}
	_, _, err = c.researchExperimentGate(tx, f.project, run.task, run.run, frame, payload)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	intent, err := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(run.run, "id"), frame.Key, payload, Object{"policy_id": goal["budget_policy_id"], "run_id": run.run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": frame.Key, "provider_event_id": "prepare/" + frame.Key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": Now()})
	if err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	intent, err = f.s.beginEffectTx(tx, o.owner, f.project, Str(run.run, "id"), frame.Key)
	if err == nil {
		err = tx.Commit()
	}
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	p, err := authenticate(tx, o.owner)
	if err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	x, err := f.s.beginExperimentTx(tx, p, f.project, gid, Str(run.run, "id"))
	if err == nil {
		err = tx.Commit()
	}
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	record, err := f.s.ExecuteExperimentPair(context.Background(), f.token, f.project, gid, Str(run.run, "id"), run.heartbeat())
	if err != nil {
		t.Fatal(err)
	}
	epoch, _ := Num(run.run, "lease_epoch")
	response, err := c.reconcileResearchExperimentEffect(context.Background(), f.project, Str(run.run, "id"), epoch, frame, intent)
	if err != nil {
		t.Fatal(err)
	}
	if response["state"] != "CONFIRMED" || len(Arr(record, "sandbox_receipts")) != 2 {
		t.Fatal("paired native receipt missing")
	}
	if _, err = c.reconcileResearchExperimentEffect(context.Background(), f.project, Str(run.run, "id"), epoch, frame, intent); err != nil {
		t.Fatal(err)
	}
	obs := run.observation("SETTLED", true)
	obs["artifacts"] = record["runtime_artifacts"]
	run.observe(obs)
	run.call("/report", run.report(Arr(record, "artifact_ids"), 0), 200)
	f.token = o.owner
	run.task = f.read("tasks", tid)
	a := f.read("artifacts", Arr(record, "artifact_ids")[0].(string))
	body := o.acceptance(run, a)
	body["artifact_refs"] = record["artifact_refs"]
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
	advance()
	f.token = o.owner
	x = f.read("experiments", gid)
	if x["outcome"] != "IMPROVED" || x["acceptance_id"] == nil {
		t.Fatal("driver omitted independently accepted experiment")
	}
	var reportID, cycleID string
	if err = f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&reportID, &cycleID); err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	cycle, err := load(tx, f.project, "ResearchCycle", cycleID)
	if err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	report := o.claim(f.read("tasks", reportID))
	artifact := o.report(report, Bytes(facts))
	acceptance := o.acceptance(report, artifact)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(report.task), acceptance)
	advance()
	var resumes int
	if err = f.db.QueryRow("SELECT count(*) FROM resource_progress_resumes WHERE project=? AND json_extract(body,'$.new_progress_keys') IS NOT NULL", f.project).Scan(&resumes); err != nil || resumes != 1 {
		t.Fatalf("new accepted progress not recorded: %d %v", resumes, err)
	}
	// Distinct immutable Artifact IDs with identical bytes must produce one gain.
	duplicate := seal("CODE", []byte(`{"mode":"EVIDENCE_RULE_V1"}`))
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	originalKey, err := f.s.researchExperimentProgressKey(tx, f.project, x)
	if err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	copy := Merge(Object{}, x)
	copy["candidate_ref"] = Ref(duplicate, "Artifact")
	copy["hypothesis"] = "rewritten claim"
	copy["id"] = ID()
	copy["results"] = Empty()
	duplicateKey, err := f.s.researchExperimentProgressKey(tx, f.project, copy)
	tx.Rollback()
	if err != nil || duplicateKey != originalKey || originalKey == "" {
		t.Fatalf("content identity washed progress: %v", err)
	}
	t.Log("I2-NATIVE-EXPERIMENT-OFFLINE: approved preregistration cloned per cycle; real AppContainer candidate/baseline pair, original effect receipt replay, independent Task acceptance, driver result recording/report close and new progress audit; duplicate content IDs preserve progress key. No TCP listener or provider qualification claimed.")
}
