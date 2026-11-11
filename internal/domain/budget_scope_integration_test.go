package domain

import (
	"context"
	"testing"
)

func TestW12ExperimentBudgetScopes(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	refs := []any{Ref(o.req, "Requirement")}
	body := Object{"cycle_id": nil, "scope": "PROJECT", "hypothesis": "scope intersection", "candidate_ref": refs[0], "baseline_refs": refs, "input_refs": refs, "metrics": []any{Object{"metric_id": "quality", "description": "paired arithmetic mean", "unit": "points", "operator": "GTE", "target": "2", "upper_target": nil, "mandatory": true}}, "acceptance_contract": experimentContract(), "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time"}}, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"}
	x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), body)
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": x["preregistration_hash"]})
	paths := []string{f.path("/experiments/" + Str(x, "id") + "/budget-policy"), f.path("/goals/" + Str(o.goal, "id") + "/budget-policy"), f.path("/budget-policy"), "/v1/policies/budget"}
	policies := []Object{}
	for i, cap := range []string{"2", "4", "6", "8"} {
		p := f.expect(200, "GET", paths[i], "", "", nil)
		policies = append(policies, f.expect(200, "PUT", paths[i], ID(), testTag(p), capBody(cap)))
	}
	task := o.task("intersect-experiment-budgets", Empty(), refs)
	if err := f.s.BindExperimentTask(context.Background(), o.owner, f.project, Str(x, "id"), Str(task, "id")); err != nil {
		t.Fatal(err)
	}
	r := o.claim(task)
	f.token = o.owner
	results := Empty()
	for i, scope := range []string{"EXPERIMENT", "GOAL", "PROJECT", "GLOBAL"} {
		// Select a different allowed leaf; every bound scope must still apply.
		leaf := policies[(i+1)%2]
		blocked := f.expect(422, "POST", f.path("/budget-ledger"), ID(), testTag(leaf), budgetRequest(r, Str(leaf, "id"), "RESERVE", ID(), dollars("2.01"), "UPPER_BOUND", nil))
		accepted := f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(leaf), budgetRequest(r, Str(leaf, "id"), "RESERVE", ID(), dollars("2"), "UPPER_BOUND", nil))
		results = append(results, Object{"limiting_scope": scope, "limiting_policy": policies[i], "submitted_policy_id": leaf["id"], "over_cap": blocked, "at_cap": accepted})
		policies[i] = f.expect(200, "PUT", paths[i], ID(), testTag(policies[i]), capBody("8"))
	}
	resourcesAssert(t, "W12-BUDGET-EXPERIMENT-SCOPES", 4, len(results), results)
}
