package domain

import (
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
	if status == "FAIL" {
		t.Fatalf("an operator the contract does not define was recorded as a measured shortfall")
	}
	if status != "INCONCLUSIVE" {
		t.Fatalf("got %q; an unevaluable metric must be INCONCLUSIVE, which is what MetricResult.status allows", status)
	}
	w09Assertion(t, "W1001-METRIC-VERDICT-CANNOT-BE-IMPLIED-BY-AN-UNEVALUABLE-GATE", Object{
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
	if passing != "PASS" || failing != "FAIL" {
		t.Fatalf("controlling the unevaluable case must not disturb the evaluable ones: %q / %q", passing, failing)
	}
	w09Assertion(t, "W1001-EVALUABLE-METRIC-STILL-PASSES", Object{"operator": "LT", "candidate": "42",
		"target": "50", "status": passing})
	w09Assertion(t, "W1001-EVALUABLE-METRIC-STILL-FAILS", Object{"operator": "LT", "candidate": "77",
		"target": "50", "status": failing})

	between, e := metricStatus(w1001Metric("BETWEEN", "10", "50"), w1001Result("42"))
	if e != nil || between != "PASS" {
		t.Fatalf("the two-sided operator regressed: %q %v", between, e)
	}
	w09Assertion(t, "W1001-BETWEEN-OPERATOR-EVALUATES-BOTH-ENDS", Object{"operator": "BETWEEN",
		"lower": "10", "upper": "50", "candidate": "42", "status": between})
}

func TestW1001ZeroSampleAndAbsentArmsAreDistinguished(t *testing.T) {
	// Both of these are currently one INCONCLUSIVE at the metric level, which the frozen
	// MetricResult.status enum permits and nothing finer. The rows record that rather than pretending
	// the classes are separable here: the separable five-class taxonomy lives on
	// EvaluationCaseResult.verdict, and wiring that through is the rest of this card.
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
	if zeroStatus != "INCONCLUSIVE" || absentStatus != "INCONCLUSIVE" {
		t.Fatalf("the metric level collapsed differently than the enum allows: %q / %q", zeroStatus, absentStatus)
	}
	w09Assertion(t, "W1001-ZERO-SAMPLE_AND_ABSENT_ARM_ARE_BOTH_INCONCLUSIVE_AT_METRIC_LEVEL", Object{
		"zero_sample_status": zeroStatus, "absent_baseline_status": absentStatus,
		"where_the_classes_are_separate": "EvaluationCaseResult.verdict = PASS|FAIL|ERROR|ABSTAIN|MISSING, " +
			"which this card has to wire through the experiment path"})
}
