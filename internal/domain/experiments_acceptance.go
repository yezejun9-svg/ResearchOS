package domain

import (
	"fmt"
	"math/big"
	"strings"
)

// paired-mean-v1 is a narrow deterministic rubric: paired decimal arrays, arithmetic
// means rounded to eight decimal places. Unknown observations remain null.
func mean(values []any) (any, error) {
	if len(values) == 0 {
		return nil, nil
	}
	sum := new(big.Rat)
	for _, v := range values {
		if v == nil {
			return nil, nil
		}
		s, ok := v.(string)
		if !ok {
			return nil, fmt.Errorf("decimal string required")
		}
		n, ok := new(big.Rat).SetString(s)
		if !ok {
			return nil, fmt.Errorf("invalid decimal")
		}
		sum.Add(sum, n)
	}
	sum.Quo(sum, big.NewRat(int64(len(values)), 1))
	v := strings.TrimRight(strings.TrimRight(sum.FloatString(8), "0"), ".")
	if v == "-0" {
		v = "0"
	}
	return v, nil
}
func recomputeExperiment(x, raw Object) ([]any, string, error) {
	ids, e := experimentCaseIDs(x)
	if e != nil {
		return nil, "", e
	}

	observations := map[string]Object{}
	for _, v := range Arr(raw, "observations") {
		o, ok := v.(map[string]any)
		if !ok {
			return nil, "", fmt.Errorf("observation object required")
		}
		id := Str(o, "metric_id")
		if observations[id] != nil {
			return nil, "", fmt.Errorf("duplicate metric observation")
		}
		observations[id] = o
	}
	if len(observations) != len(Arr(x, "metrics")) {
		return nil, "", fmt.Errorf("all metrics required")
	}
	results := Empty()
	missing, failed, better, worse := false, false, false, false
	for _, v := range Arr(x, "metrics") {
		m := v.(map[string]any)
		o := observations[Str(m, "metric_id")]
		if o == nil {
			return nil, "", fmt.Errorf("unknown or absent metric")
		}
		base, cand := Arr(o, "baseline"), Arr(o, "candidate")
		if len(base) != len(cand) || len(base) != len(ids) || Hash(o["case_ids"]) != Hash(ids) {
			return nil, "", fmt.Errorf("paired observation denominator mismatch")
		}
		b, e := mean(base)
		if e != nil {
			return nil, "", e
		}
		c, e := mean(cand)
		if e != nil {
			return nil, "", e
		}
		r := Object{"metric_id": m["metric_id"], "baseline": b, "candidate": c, "sample_count": len(base), "evidence_refs": Empty()}
		status, e := metricStatus(m, r)
		if e != nil {
			return nil, "", e
		}
		r["status"] = status
		results = append(results, r)
		if m["mandatory"] == true {
			missing = missing || status == "INCONCLUSIVE"
			failed = failed || status == "FAIL"
		}
		if b != nil && c != nil {
			bv, _ := new(big.Rat).SetString(b.(string))
			cv, _ := new(big.Rat).SetString(c.(string))
			cmp := cv.Cmp(bv)
			if m["operator"] == "LT" || m["operator"] == "LTE" {
				cmp = -cmp
			}
			if m["operator"] == "EQ" || m["operator"] == "BETWEEN" {
				bs := Object{"baseline": b, "candidate": b, "sample_count": len(base)}
				previous, _ := metricStatus(m, bs)
				cmp = 0
				if previous == "FAIL" && status == "PASS" {
					cmp = 1
				}
				if previous == "PASS" && status == "FAIL" {
					cmp = -1
				}
			}
			better = better || cmp > 0
			worse = worse || cmp < 0
		}
	}
	outcome := "NO_IMPROVEMENT"
	if missing {
		outcome = "INCONCLUSIVE"
	} else if worse {
		outcome = "REGRESSED"
	} else if better && !failed {
		outcome = "IMPROVED"
	}
	return results, outcome, nil
}
func (s *Service) verifyExperimentObservation(snap Object) (string, string) {
	task := snap["task"].(map[string]any)
	var text string
	if e := s.DB.QueryRow("SELECT d.body FROM experiment_tasks et JOIN domain_objects d ON d.project=et.project AND d.kind='Experiment' AND d.id=et.experiment WHERE et.project=? AND et.task=?", task["project_id"], task["id"]).Scan(&text); e != nil {
		return "FAIL", "no registered experiment binding"
	}
	x, e := Decode([]byte(text))
	if e != nil {
		return "FAIL", e.Error()
	}
	artifacts := Arr(snap, "artifacts")
	if len(artifacts) != 1 {
		return "FAIL", "one paired observation artifact required"
	}
	raw, e := Decode(artifacts[0].(map[string]any)["bytes"].([]byte))
	if e != nil {
		return "FAIL", e.Error()
	}
	if raw["experiment_id"] != x["id"] || raw["preregistration_hash"] != x["preregistration_hash"] || x["status"] != "RUNNING" || Hash(x["acceptance_contract"]) != Hash(task["acceptance_contract"]) {
		return "FAIL", "frozen experiment binding mismatch"
	}
	results, outcome, e := recomputeExperiment(x, raw)
	if e != nil {
		return "FAIL", e.Error()
	}
	if Hash(results) != Hash(raw["results"]) || outcome != raw["outcome"] {
		return "FAIL", "independent paired means/outcome differ from submitted results"
	}
	return "PASS", string(Bytes(Object{"results": results, "outcome": outcome, "preregistration_hash": x["preregistration_hash"]}))
}

func experimentCaseIDs(x Object) ([]any, error) {
	c, ok := x["acceptance_contract"].(map[string]any)
	if !ok {
		return nil, fmt.Errorf("contract required")
	}
	var ids []any
	for _, v := range Arr(c, "checks") {
		check, ok := v.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("check required")
		}
		if check["command_key"] != "experiments.paired-mean-v1" {
			continue
		}
		if ids != nil {
			return nil, fmt.Errorf("one mean check required")
		}
		config, e := Decode([]byte(Str(check, "expected")))
		if e != nil {
			return nil, e
		}
		ids = Arr(config, "expected_case_ids")
	}
	if len(ids) == 0 {
		return nil, fmt.Errorf("frozen expected cases required")
	}
	seen := map[string]bool{}
	for _, v := range ids {
		id, ok := v.(string)
		if !ok || id == "" || seen[id] {
			return nil, fmt.Errorf("unique expected IDs required")
		}
		seen[id] = true
	}
	return ids, nil
}
