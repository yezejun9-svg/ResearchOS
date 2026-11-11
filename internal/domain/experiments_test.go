package domain

import (
	"context"
	"fmt"
	"testing"
)

func w10Assert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W10_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": "HTTP/SQLite/independent acceptance transaction"})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func experimentContract() Object {
	c := orchestrationContract()
	Arr(c, "checks")[0].(map[string]any)["command_key"] = "experiments.paired-mean-v1"
	Arr(c, "checks")[0].(map[string]any)["expected"] = `{"expected_case_ids":["s1","s2"]}`
	c["contract_hash"] = contractDigest(c)
	return c
}
func TestW10Experiment(t *testing.T) {
	for _, scenario := range []string{"positive", "negative", "null", "inconclusive", "stable"} {
		t.Run(scenario, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			contract := experimentContract()
			profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
			refs := []any{Ref(o.req, "Requirement")}
			b := Object{"cycle_id": nil, "scope": "PROJECT", "hypothesis": "candidate improves paired mean", "candidate_ref": refs[0], "baseline_refs": refs, "input_refs": refs, "metrics": []any{Object{"metric_id": "quality", "description": "paired arithmetic mean", "unit": "points", "operator": "GTE", "target": "2", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "attempt-limit", "sandbox-violation"}}, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"}
			x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), b)
			status, _, _ := f.request("POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": Digest([]byte("wrong"))})
			w10Assert(t, "A07-HASH-"+scenario, 422, status)
			x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": x["preregistration_hash"]})
			task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(o.goal, "id"))), Object{"goal_id": o.goal["id"], "title": "experiment " + scenario, "task_type": "paired-metric", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": refs, "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": "orchestration-problem", "candidate_id": scenario, "stop_policy": b["stop_policy"]})
			f.bundle(task)
			task = f.read("tasks", Str(task, "id"))
			task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "registered development experiment"})
			if e := f.s.BindExperimentTask(context.Background(), o.owner, f.project, Str(x, "id"), Str(task, "id")); e != nil {
				t.Fatal(e)
			}
			r := o.claim(task)
			var e error
			x, e = f.s.BeginExperiment(context.Background(), o.owner, f.project, Str(x, "id"), Str(r.run, "id"))
			if e != nil {
				t.Fatal(e)
			}
			w10Assert(t, "A07-REGISTER-FIRST-"+scenario, "RUNNING", x["status"])
			tx, _ := f.db.Begin()
			forged, _ := load(tx, f.project, "Experiment", Str(x, "id"))
			Arr(forged, "metrics")[0].(map[string]any)["target"] = "0"
			bump(forged)
			e = f.s.put(tx, "Experiment", forged)
			tx.Rollback()
			w10Assert(t, "A07-POSTHOC-"+scenario, true, e != nil)
			base, cand := []any{"1", "1"}, []any{"3", "3"}
			want := "IMPROVED"
			if scenario == "stable" {
				cand = []any{"1", "1"}
				want = "NO_IMPROVEMENT"
			}
			if scenario == "negative" {
				base = []any{"3", "3"}
				cand = []any{"1", "1"}
				want = "REGRESSED"
			}
			if scenario == "null" {
				cand = []any{nil, nil}
				want = "INCONCLUSIVE"
			}
			if scenario == "inconclusive" {
				base = []any{nil, nil}
				cand = []any{nil, nil}
				want = "INCONCLUSIVE"
			}
			raw := Object{"experiment_id": x["id"], "preregistration_hash": x["preregistration_hash"], "observations": []any{Object{"metric_id": "quality", "case_ids": []any{"s1", "s2"}, "baseline": base, "candidate": cand}}}
			results, outcome, e := recomputeExperiment(x, raw)
			if e != nil {
				t.Fatal(e)
			}
			raw["results"] = results
			raw["outcome"] = outcome
			a := o.report(r, Bytes(raw))
			request := o.acceptance(r, a)
			receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), request)
			w10Assert(t, "A07-VERIFIED-"+scenario, "PASS", receipt["verdict"])
			f.token = o.owner
			bad := Object{"run_ids": x["run_ids"], "results": results, "outcome": outcome, "acceptance_id": ID()}
			status, _, _ = f.request("POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), bad)
			w10Assert(t, "A07-NO-RECEIPT-"+scenario, 404, status)
			bad["acceptance_id"] = receipt["id"]
			tampered, _ := Decode(Bytes(bad))
			Arr(tampered, "results")[0].(map[string]any)["candidate"] = "999"
			status, _, _ = f.request("POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), tampered)
			w10Assert(t, "A07-METRIC-FORGE-"+scenario, 422, status)
			final := f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), bad)
			w10Assert(t, "A07-OUTCOME-"+scenario, want, final["outcome"])
			w10Assert(t, "A07-RECOMPUTE-"+scenario, results, final["results"])
		})
	}
}
