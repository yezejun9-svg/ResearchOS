//go:build windows

package domain

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
)

func TestW10NativePair(t *testing.T) {
	goexe := os.Getenv("RESEARCHOS_GO")
	if goexe == "" {
		goexe = filepath.Join(os.Getenv("GOROOT"), "bin", "go.exe")
	}
	if goexe == "bin\\go.exe" {
		t.Fatal("RESEARCHOS_GO or GOROOT required")
	}
	binary := filepath.Join(t.TempDir(), "native.exe")
	cmd := exec.Command(goexe, "build", "-o", binary, "../../adapters/evaluation/cmd")
	if out, e := cmd.CombinedOutput(); e != nil {
		t.Fatalf("build native: %v %s", e, out)
	}
	executable, e := os.ReadFile(binary)
	if e != nil {
		t.Fatal(e)
	}
	o := orchestrationSetup(t)
	f := o.f
	seal := func(kind string, raw []byte) Object {
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/octet-stream", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	}
	candidate := seal("CODE", []byte(`{"mode":"EVIDENCE_RULE_V1"}`))
	baseline := seal("CODE", []byte(`{"mode":"ALWAYS_ADOPT_V1"}`))
	tool := seal("CODE", executable)
	data := seal("DATASET", []byte(`{"cases":[{"id":"s1","input":{"evidence_present":true,"evidence_current":true,"hard_checks_passed":true,"measured_net_gain_positive":true},"expected_decision":"ADOPT"},{"id":"s2","input":{"evidence_present":false,"evidence_current":true,"hard_checks_passed":true,"measured_net_gain_positive":true},"expected_decision":"REJECT"}]}`))
	if e = f.s.RegisterNativeEvaluationTool(context.Background(), f.project, Str(tool, "content_hash")); e != nil {
		t.Fatal(e)
	}
	contract := experimentContract()
	Arr(contract, "checks")[0].(map[string]any)["expected"] = `{"expected_case_ids":["s1","s2"],"native_execution":true}`
	contract["contract_hash"] = contractDigest(contract)
	refs := []any{Ref(candidate, "Artifact"), Ref(baseline, "Artifact"), Ref(data, "Artifact"), Ref(tool, "Artifact")}
	stop := Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "sandbox-violation"}}
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": nil, "scope": "PROJECT", "hypothesis": "evidence rule improves accuracy", "candidate_ref": refs[0], "baseline_refs": []any{refs[1]}, "input_refs": []any{refs[2], refs[3]}, "metrics": []any{Object{"metric_id": "accuracy", "description": "paired accuracy", "unit": "ratio", "operator": "GTE", "target": "1", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": x["preregistration_hash"]})
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(o.goal, "id"))), Object{"goal_id": o.goal["id"], "title": "native paired experiment", "task_type": "paired-metric", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": "orchestration-problem", "candidate_id": "native", "stop_policy": stop})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen native pair"})
	if e = f.s.BindExperimentTask(context.Background(), o.owner, f.project, Str(x, "id"), Str(task, "id")); e != nil {
		t.Fatal(e)
	}
	r := o.claim(task)
	x, e = f.s.BeginExperiment(context.Background(), o.owner, f.project, Str(x, "id"), Str(r.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	r.call("/heartbeat", r.heartbeat(), 200)
	record, e := f.s.ExecuteExperimentPair(context.Background(), f.token, f.project, Str(x, "id"), Str(r.run, "id"), r.heartbeat())
	if e != nil {
		t.Fatal(e)
	}
	w10Assert(t, "A07-NATIVE-RECORDED", "RECORDED", record["state"])
	w10Assert(t, "A07-NATIVE-PAIRED", 2, len(Arr(record, "sandbox_receipts")))
	_, e = f.s.ExecuteExperimentPair(context.Background(), f.token, f.project, Str(x, "id"), Str(r.run, "id"), r.heartbeat())
	w10Assert(t, "A07-NATIVE-NO-REPLAY", true, e != nil)
	obs := r.observation("SETTLED", true)
	obs["artifacts"] = record["runtime_artifacts"]
	r.observe(obs)
	r.call("/report", r.report(Arr(record, "artifact_ids"), 0), 200)
	f.token = o.owner
	r.task = f.read("tasks", Str(task, "id"))
	a := f.read("artifacts", Arr(record, "artifact_ids")[0].(string))
	request := o.acceptance(r, a)
	request["artifact_refs"] = record["artifact_refs"]
	acceptance := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), request)
	w10Assert(t, "A07-NATIVE-INDEPENDENT", "PASS", acceptance["verdict"])
	f.token = o.owner
	result := record["observation"].(map[string]any)
	final := f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), Object{"run_ids": x["run_ids"], "results": result["results"], "outcome": result["outcome"], "acceptance_id": acceptance["id"]})
	w10Assert(t, "A07-NATIVE-IMPROVED", "IMPROVED", final["outcome"])
	if dir := os.Getenv("W10_EVIDENCE_DIR"); dir != "" {
		for name, v := range map[string]any{"native-execution": record, "native-acceptance": acceptance, "native-experiment": final} {
			if e = os.WriteFile(filepath.Join(dir, name+".json"), Bytes(v), 0600); e != nil {
				t.Fatal(e)
			}
		}
	}
}
