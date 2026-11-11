package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"
)

// W10-01 begins with the verdict taxonomy itself, because the card's own counter-example is about an
// outcome being implied by something that never evaluated. metricStatus had no default branch: an
// operator outside the frozen MetricSpec enum fell out of the switch with pass still false and was
// returned as FAIL, which is a measured shortfall recorded for a gate that did not run.
//
// The two control rows are what make the new row mean something. A change that returned INCONCLUSIVE
// for everything would satisfy the fix row on its own, so both directions of a valid operator are
// asserted here as well.

// w1001Assert compares rather than declares: the W09 emitter it replaced prints PASS unconditionally and
// relies on a preceding t.Fatalf, so a row could go quiet instead of red. Here the expectation is an
// argument, and a mismatch is a FAIL line on stdout plus a test failure.
func w1001Assert(t *testing.T, id string, want, got any, evidence Object) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	line, e := json.Marshal(Object{"assertion_id": id, "expected": want, "actual": got, "status": status,
		"evidence": evidence})
	if e != nil {
		t.Fatal(e)
	}
	fmt.Println("W10_ASSERTION " + string(line))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}

// w1001ClaimProbe re-claims without t.Fatal-ing on a non-2xx, because some of this card's rows are about
// the refusal itself.
func w1001ClaimProbe(t *testing.T, o *orchestrationFixture, task Object) (int, Object) {
	t.Helper()
	f := o.f
	f.token = o.owner
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		t.Fatal(e)
	}
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task),
		Object{"runtime_id": o.rt["id"], "executor_principal_id": executor,
			"context_bundle_id": task["context_bundle_id"]})
	return status, reply
}

func w1001Metric(operator, target, upper any) Object {
	m := Object{"operator": operator, "target": target, "upper_target": upper, "metric_id": "latency_ms",
		"unit": "ms", "hard_gate": true}
	return m
}

func w1001Result(candidate string) Object {
	return Object{"sample_count": 12, "baseline": "40", "candidate": candidate, "measurement_status": "OK"}
}

func TestW1001UnrecognisedOperatorCannotBeReportedAsFail(t *testing.T) {
	status, err := metricStatus(w1001Metric("NOT_A_FROZEN_OPERATOR", "50", nil), w1001Result("42"))
	if err != nil {
		t.Fatalf("the classifier refused instead of grading: %v", err)
	}
	// The comparison itself decides the verdict. An earlier version of this test aborted here when the
	// status was FAIL, which meant the mutation that reintroduced that fallthrough reddened the test but
	// never emitted the row, so the row could not be shown to be the thing that catches it.
	w1001Assert(t, "W1001-METRIC-VERDICT-CANNOT-BE-IMPLIED-BY-AN-UNEVALUABLE-GATE", "INCONCLUSIVE", status, Object{
		"operator": "NOT_A_FROZEN_OPERATOR", "status": status,
		"before_this_card": "FAIL", "frozen_operators": []string{"LT", "LTE", "EQ", "GTE", "GT", "BETWEEN"},
		"why_not_a_new_class": "MetricResult.status is a closed enum of PASS|FAIL|INCONCLUSIVE|NOT_RUN, so the " +
			"class has to come from inside it; a new class would need the contract owner"})
}

func TestW1001RecognisedOperatorsStillGradeBothWays(t *testing.T) {
	passing, e := metricStatus(w1001Metric("LT", "50", nil), w1001Result("42"))
	if e != nil {
		t.Fatal(e)
	}
	failing, e := metricStatus(w1001Metric("LT", "50", nil), w1001Result("77"))
	if e != nil {
		t.Fatal(e)
	}
	// Same reason as above: the two comparison rows below are what must catch a gate that always passes,
	// so nothing may abort before them.
	w1001Assert(t, "W1001-EVALUABLE-METRIC-STILL-PASSES", "PASS", passing, Object{"operator": "LT", "candidate": "42",
		"target": "50", "status": passing})
	w1001Assert(t, "W1001-EVALUABLE-METRIC-STILL-FAILS", "FAIL", failing, Object{"operator": "LT", "candidate": "77",
		"target": "50", "status": failing})

	// Round-1 blocker P1/P2: the guard that used to sit here asserted exactly the predicate the row below
	// compares, so a broken two-sided operator aborted the test instead of reporting FAIL - and the single
	// in-range candidate (42 inside 10 to 50) could not tell an upper-bound check from no upper-bound check
	// at all. Both legs now get their own row, each with a candidate where the two legs disagree.
	between, eBetween := metricStatus(w1001Metric("BETWEEN", "10", "50"), w1001Result("42"))
	belowLower, e := metricStatus(w1001Metric("BETWEEN", "10", "50"), w1001Result("5"))
	aboveUpper, eUpper := metricStatus(w1001Metric("BETWEEN", "10", "50"), w1001Result("77"))
	w1001Assert(t, "W1001-BETWEEN-IN-RANGE-PASSES", "PASS", between, Object{"operator": "BETWEEN",
		"lower": "10", "upper": "50", "candidate": "42", "status": between, "error": fmt.Sprint(eBetween)})
	w1001Assert(t, "W1001-BETWEEN-BELOW-LOWER-END-FAILS", "FAIL", belowLower, Object{"operator": "BETWEEN",
		"lower": "10", "upper": "50", "candidate": "5", "status": belowLower, "error": fmt.Sprint(e)})
	w1001Assert(t, "W1001-BETWEEN-ABOVE-UPPER-END-FAILS", "FAIL", aboveUpper, Object{"operator": "BETWEEN",
		"lower": "10", "upper": "50", "candidate": "77", "status": aboveUpper, "error": fmt.Sprint(eUpper)})
}

func TestW1001ZeroSampleAndAbsentArmsAreDistinguished(t *testing.T) {
	// Both of these are currently one INCONCLUSIVE at the metric level, which the frozen
	// MetricResult.status enum permits and nothing finer. The rows record that rather than pretending
	// the classes are separable here: the five-class taxonomy lives on EvaluationCaseResult.verdict,
	// and this card's tests show how far that distinction actually travels (see
	// TestW1001TheFiveCaseClassesAreRetainedButNotCarriedIntoThePairedObservation).
	zero := Object{"sample_count": 0, "baseline": "40", "candidate": "42", "measurement_status": "OK"}
	absent := Object{"sample_count": 12, "baseline": nil, "candidate": "42", "measurement_status": "OK"}
	zeroStatus, e := metricStatus(w1001Metric("LT", "50", nil), zero)
	if e != nil {
		t.Fatal(e)
	}
	absentStatus, e := metricStatus(w1001Metric("LT", "50", nil), absent)
	if e != nil {
		t.Fatal(e)
	}
	// Round-1 blocker P2: this guard asserted the same predicate as the row below, so a metric level that
	// stopped collapsing both classes would abort rather than report FAIL on the named row.
	w1001Assert(t, "W1001-ZERO-SAMPLE_AND_ABSENT_ARM_ARE_BOTH_INCONCLUSIVE_AT_METRIC_LEVEL",
		[]any{"INCONCLUSIVE", "INCONCLUSIVE"}, []any{zeroStatus, absentStatus}, Object{
			"zero_sample_status": zeroStatus, "absent_baseline_status": absentStatus,
			"where_the_classes_are_separate": "EvaluationCaseResult.verdict = PASS|FAIL|ERROR|ABSTAIN|MISSING"})
}

// w1001Setup builds a registered experiment with taskCount bound tasks. Tasks are bound while the
// experiment is still REGISTERED because BindExperimentTask refuses any later status, which is what makes
// a second retained run reachable at all: the same task cannot be re-claimed after it reports (the claim
// gate requires READY), so attempts come from separate bound tasks.
func w1001Setup(t *testing.T, attempts int64, taskCount int) (*orchestrationFixture, Object, []Object) {
	t.Helper()
	o := orchestrationSetup(t)
	f := o.f
	contract := experimentContract()
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	refs := []any{Ref(o.req, "Requirement")}
	stop := Object{"wall_time_seconds": 60, "max_attempts": attempts, "max_parallel_runs": 1,
		"stop_conditions": []any{"wall-time", "attempt-limit", "sandbox-violation"}}
	b := Object{"cycle_id": nil, "scope": "PROJECT", "hypothesis": "candidate improves paired mean",
		"candidate_ref": refs[0], "baseline_refs": refs, "input_refs": refs,
		"metrics": []any{Object{"metric_id": "quality", "description": "paired arithmetic mean", "unit": "points",
			"operator": "GTE", "target": "2", "upper_target": nil, "mandatory": true}},
		"acceptance_contract": contract, "stop_policy": stop,
		"budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"}
	x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), b)
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x),
		Object{"expected_preregistration_hash": x["preregistration_hash"]})
	tasks := []Object{}
	for i := 0; i < taskCount; i++ {
		task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(o.goal, "id"))),
			Object{"goal_id": o.goal["id"], "title": fmt.Sprintf("w1001 retention attempt %d", i+1),
				"task_type": "paired-metric", "stage": "verification", "dependency_task_ids": Empty(),
				"requirement_refs": refs, "input_refs": refs, "acceptance_contract": contract,
				"origin_problem_id": "orchestration-problem", "candidate_id": fmt.Sprintf("retention-%d", i+1),
				"stop_policy": stop})
		f.bundle(task)
		task = f.read("tasks", Str(task, "id"))
		task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task),
			Object{"action": "SUBMIT", "reason": "registered development experiment"})
		if e := f.s.BindExperimentTask(context.Background(), o.owner, f.project, Str(x, "id"), Str(task, "id")); e != nil {
			t.Fatal(e)
		}
		tasks = append(tasks, task)
	}
	return o, x, tasks
}

func w1001RawFor(x Object, cases int) Object {
	base, cand, ids := []any{}, []any{}, []any{}
	for i := 1; i <= cases; i++ {
		base = append(base, "1")
		cand = append(cand, "3")
		ids = append(ids, fmt.Sprintf("s%d", i))
	}
	return Object{"experiment_id": x["id"], "preregistration_hash": x["preregistration_hash"],
		"observations": []any{Object{"metric_id": "quality", "case_ids": ids, "baseline": base, "candidate": cand}}}
}

func TestW1001ARetriedTaskCannotBeReclaimedAfterReporting(t *testing.T) {
	// Recorded because it is the reason the two-run construction below needs two bound tasks: the claim
	// gate only accepts READY, and reporting leaves the task EXECUTION_REPORTED. This is the product
	// refusing, not a fixture limitation, so it gets a row rather than a workaround.
	o, x, tasks := w1001Setup(t, 2, 1)
	f := o.f
	r1 := o.claim(tasks[0])
	x, e := f.s.BeginExperiment(context.Background(), o.owner, f.project, Str(x, "id"), Str(r1.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	o.report(r1, Bytes(w1001RawFor(x, 2)))
	f.token = o.owner
	after := f.read("tasks", Str(tasks[0], "id"))
	status, reply := w1001ClaimProbe(t, o, after)
	if status != 409 {
		t.Fatalf("a reported task was claimable again: status=%d reply=%v", status, reply)
	}
	w1001Assert(t, "W1001-REPORTED-TASK-CANNOT-BE-RECLAIMED-SO-ATTEMPTS-NEED-SEPARATE-BINDS",
		[]any{409, "STATE_CONFLICT", "only READY tasks can be claimed", "EXECUTION_REPORTED"},
		[]any{status, reply["code"], reply["message"], after["status"]},
		Object{"refusal": reply, "task": after, "retained_run_ids_after_attempt_one": Arr(x, "run_ids")})
}

func TestW1001DeletingARetainedRunIsRefused(t *testing.T) {
	o, x, tasks := w1001Setup(t, 2, 2)
	f := o.f
	r1 := o.claim(tasks[0])
	x, e := f.s.BeginExperiment(context.Background(), o.owner, f.project, Str(x, "id"), Str(r1.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	if len(Arr(x, "run_ids")) != 1 {
		t.Fatalf("first attempt registered %v", Arr(x, "run_ids"))
	}
	o.report(r1, Bytes(w1001RawFor(x, 2)))
	r2 := o.claim(tasks[1])
	x, e = f.s.BeginExperiment(context.Background(), o.owner, f.project, Str(x, "id"), Str(r2.run, "id"))
	if e != nil {
		t.Fatalf("second bound task could not begin a second retained run: %v", e)
	}
	retained := Arr(x, "run_ids")
	// Round-1 blocker P2: the duplicate guard used to sit ABOVE this row and assert the same length, which
	// made the row unreportable-FAIL. It now sits below, where it still protects the retained[0] index the
	// counterexample builds on but no longer preempts the comparison.
	w1001Assert(t, "W1001-TWO-ATTEMPTS-PRODUCE-TWO-RETAINED-RUN-IDS", 2, len(Arr(x, "run_ids")),
		Object{"max_attempts": 2, "second_run_id": Str(r2.run, "id")})
	if len(retained) != 2 {
		t.Fatalf("attempt limit is 2 but retained runs are %v", retained)
	}

	raw := w1001RawFor(x, 2)
	results, outcome, e := recomputeExperiment(x, raw)
	if e != nil {
		t.Fatal(e)
	}
	raw["results"], raw["outcome"] = results, outcome
	a := o.report(r2, Bytes(raw))
	f.token = o.owner
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r2.task), o.acceptance(r2, a))
	f.token = o.owner
	dropped := Object{"run_ids": []any{retained[0]}, "results": results, "outcome": outcome,
		"acceptance_id": receipt["id"]}
	status, reply, _ := f.request("POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), dropped)
	// Round-1 major P4: the guard that used to sit here credited M02 to an abort instead of to a row, so the
	// matrix could only claim an absence. With it gone the row itself goes FAIL when the retention gate stops
	// deciding, which is what "caught by a named assertion" is supposed to mean.
	w1001Assert(t, "W1001-DELETING-A-RETAINED-RUN-IS-REFUSED-BY-THE-RETENTION-GATE",
		[]any{422, "GATE_FAILED", "all runs must be retained"},
		[]any{status, reply["code"], reply["message"]},
		Object{"refusal": reply, "submitted_run_ids": dropped["run_ids"], "frozen_run_ids": retained})

	still := f.read("experiments", Str(x, "id"))
	w1001Assert(t, "W1001-RETENTION-REFUSAL-CHANGED-NO-STATE",
		[]any{"RUNNING", 2, nil, 0},
		[]any{still["status"], len(Arr(still, "run_ids")), still["outcome"], len(Arr(still, "results"))},
		Object{"experiment_after_refusal": still})

	full := Object{"run_ids": retained, "results": results, "outcome": outcome, "acceptance_id": receipt["id"]}
	final := f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(still), full)
	w1001Assert(t, "W1001-SAME-EXPERIMENT-STILL-ACCEPTS-THE-FULL-RETAINED-SET",
		[]any{"COMPLETED", 2, outcome},
		[]any{final["status"], len(Arr(final, "run_ids")), final["outcome"]},
		Object{"final": final, "why": "the refusal above was the retention gate, not a dead experiment"})
}
