"""Pure-IO Source derivation; never imports or runs the Go candidate."""
import difflib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
source = Path(r"D:\作品集\ResearchOS\research-os\internal\domain\runtime_qualification.go")
out = Path(__file__).resolve().parent
original = source.read_text(encoding="utf-8")

anchor = '''func qualificationTaskHash(t Object) string {
	return Hash([]any{t["goal_id"], t["task_type"], t["input_refs"], t["requirement_refs"], t["context_bundle_id"], t["dependency_task_ids"], t["acceptance_contract"], t["stop_policy"]})
}
'''
helper = anchor + '''
// qualificationUnlimitedPolicies is the explicit default-policy exception to
// the LIVE upper-bound reservation. It never admits a CAPPED ancestor, even an
// accounting-only one, and never reinterprets unknown cost as zero.
func qualificationUnlimitedPolicies(policies []Object) error {
	if len(policies) == 0 {
		return Fail(422, "GATE_FAILED", "active budget ancestry required")
	}
	for _, p := range policies {
		if p["mode"] != "UNLIMITED_AMOUNT" || p["cap"] != nil || p["unknown_cost_action"] != "ALLOW_AND_RECORD" {
			return Fail(422, "GATE_FAILED", "LIVE unknown cost requires unlimited active ancestry")
		}
	}
	return nil
}

func qualificationUnlimitedGoal(tx *sql.Tx, project, goalID string) error {
	goal, e := load(tx, project, "Goal", goalID)
	if e != nil {
		return e
	}
	policies, e := budgetChain(tx, project, Str(goal, "budget_policy_id"))
	if e != nil {
		return e
	}
	return qualificationUnlimitedPolicies(policies)
}
'''

old_register = '''	if r["measurement_mode"] == "LIVE" {
		cost, err := moneyAmount(profileBody["max_cost"])
		if err != nil || cost.Sign() <= 0 || Str(profileBody["max_cost"].(map[string]any), "currency") == "" {
			return Fail(422, "GATE_FAILED", "LIVE qualification needs positive frozen cost bound")
		}
	}
'''
new_register = '''	if r["measurement_mode"] == "LIVE" {
		maxCost, declared := profileBody["max_cost"]
		if !declared {
			return Fail(422, "GATE_FAILED", "LIVE qualification cost basis must be declared")
		}
		if maxCost == nil {
			if e = qualificationUnlimitedGoal(tx, project, Str(t, "goal_id")); e != nil {
				return e
			}
		} else {
			cost, err := moneyAmount(maxCost)
			if err != nil || cost.Sign() <= 0 || Str(maxCost.(map[string]any), "currency") == "" {
				return Fail(422, "GATE_FAILED", "LIVE qualification needs positive frozen cost bound")
			}
		}
	}
'''

old_reserve = '''	cost, e := moneyAmount(profileBody["max_cost"])
	if e != nil || cost.Sign() <= 0 {
		return Fail(422, "GATE_FAILED", "LIVE qualification cost bound missing")
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": profileBody["max_cost"], "provider_request_id": "qualification-dispatch/" + Str(run, "id"), "provider_event_id": "qualification-dispatch/" + Str(run, "id"), "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
	return e
'''
new_reserve = '''	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return e
	}
	requestID := "qualification-dispatch/" + Str(run, "id")
	if profileBody["max_cost"] == nil {
		if runtime["measurement_mode"] != "LIVE" {
			return Fail(422, "GATE_FAILED", "LIVE unknown cost path required")
		}
		policies, _, err := runBudgetScopes(tx, project, Str(run, "id"))
		if err != nil {
			return err
		}
		if err = qualificationUnlimitedPolicies(policies); err != nil {
			return err
		}
		_, err = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": requestID, "provider_event_id": requestID, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": Now()})
		return err
	}
	cost, e := moneyAmount(profileBody["max_cost"])
	if e != nil || cost.Sign() <= 0 {
		return Fail(422, "GATE_FAILED", "LIVE qualification cost bound missing")
	}
	_, e = s.appendBudget(tx, project, Object{"policy_id": goal["budget_policy_id"], "run_id": run["id"], "operation": "RESERVE", "money": profileBody["max_cost"], "provider_request_id": requestID, "provider_event_id": requestID, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
	return e
'''

replacements = ((anchor, helper), (old_register, new_register),
                (old_reserve, new_reserve))
updated = original
counts = [updated.count(old) for old, _ in replacements]
if counts != [1, 1, 1]:
    print(f"SOURCE_DRIFT: replacement counts={counts}")
    raise SystemExit(0)
for old, new in replacements:
    updated = updated.replace(old, new, 1)
name = "runtime_qualification.unlimited.proposed.go"
with (out / name).open("xb") as target:
    target.write(updated.encode("utf-8"))
diff = "".join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True),
                                    fromfile="a/internal/domain/runtime_qualification.go",
                                    tofile="b/internal/domain/runtime_qualification.go"))
with (out / "runtime_qualification.unlimited.patch").open("xb") as target:
    target.write(diff.encode("utf-8"))
print(f"SOURCE_DERIVED counts={counts} bytes={len(updated.encode('utf-8'))}")
