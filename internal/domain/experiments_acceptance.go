package domain

import (
	"encoding/json"
	"fmt"
	"math/big"
	"researchos.local/research-os/adapters/evaluation"
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

	raw, e := experimentObservation(Arr(snap, "artifacts"))
	if e != nil {
		return "FAIL", e.Error()
	}
	if nativeExperiment(x) {
		if e = s.verifyNativeExperiment(x, snap, raw); e != nil {
			return "FAIL", e.Error()
		}
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

func experimentObservation(artifacts []any) (Object, error) {
	var found Object
	for _, v := range artifacts {
		entry, ok := v.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("artifact entry required")
		}
		raw, ok := entry["bytes"].([]byte)
		if !ok {
			return nil, fmt.Errorf("artifact bytes required")
		}
		o, e := Decode(raw)
		if e != nil {
			continue
		}
		if _, ok := o["observations"]; !ok {
			continue
		}
		if found != nil {
			return nil, fmt.Errorf("ambiguous paired observation artifact")
		}
		found = o
	}
	if found == nil {
		return nil, fmt.Errorf("paired observation artifact required")
	}
	return found, nil
}
func nativeExperiment(x Object) bool {
	for _, v := range Arr(x["acceptance_contract"].(map[string]any), "checks") {
		c := v.(map[string]any)
		if c["command_key"] == "experiments.paired-mean-v1" {
			config, e := Decode([]byte(Str(c, "expected")))
			if e == nil {
				return config["native_execution"] == true
			}
		}
	}
	return false
}
func (s *Service) verifyNativeExperiment(x, snap, observation Object) error {
	r := snap["run"].(map[string]any)
	var body, receiptHash, state string
	if e := s.DB.QueryRow("SELECT body,receipt_hash,state FROM experiment_executions WHERE project=? AND experiment=? AND run=? AND epoch=?", x["project_id"], x["id"], r["id"], r["lease_epoch"]).Scan(&body, &receiptHash, &state); e != nil {
		return fmt.Errorf("actual native execution receipt unavailable")
	}
	record, e := Decode([]byte(body))
	if e != nil {
		return e
	}
	if state != "RECORDED" || record["receipt_hash"] != receiptHash || receiptHash != Receipt(record) || Hash(record["observation"]) != Hash(observation) || record["preregistration_hash"] != x["preregistration_hash"] || Hash(record["artifact_refs"]) != Hash(snap["artifact_refs"]) {
		return fmt.Errorf("native receipt/observation/artifact binding mismatch")
	}
	var manifest evaluation.Manifest
	if e = json.Unmarshal(Bytes(record["manifest"]), &manifest); e != nil {
		return e
	}
	if manifest.ProjectID != x["project_id"] || manifest.Engine["name"] != "NATIVE" || manifest.Engine["version"] != "1" || manifest.Engine["config_hash"] != Hash(x["acceptance_contract"]) || manifest.RubricHash != Hash(x["acceptance_contract"]) || manifest.ExperimentID != x["id"] || manifest.RunID != r["id"] || manifest.CandidateHash != x["candidate_ref"].(map[string]any)["content_hash"] || manifest.BaselineHash != Arr(x, "baseline_refs")[0].(map[string]any)["content_hash"] {
		return fmt.Errorf("native manifest version mismatch")
	}

	expectedIDs, err := experimentCaseIDs(x)
	if err != nil || Hash(expectedIDs) != Hash(manifest.Expected) {
		return fmt.Errorf("native expected case binding mismatch")
	}
	var datasetBound bool
	for _, v := range Arr(x, "input_refs") {
		if v.(map[string]any)["content_hash"] == manifest.DatasetHash {
			datasetBound = true
		}
	}
	if !datasetBound {
		return fmt.Errorf("native dataset binding mismatch")
	}
	if len(Arr(record, "reports")) != 2 || len(Arr(record, "raw_exports")) != 2 || len(Arr(record, "raw_hashes")) != 2 || len(Arr(record, "sandbox_receipts")) != 2 {
		return fmt.Errorf("complete baseline and candidate receipts required")
	}
	for i, v := range Arr(record, "reports") {
		report := v.(map[string]any)
		if e = evaluation.Validate(manifest, report, []byte(Arr(record, "raw_exports")[i].(string)), Arr(record, "raw_hashes")[i].(string)); e != nil {
			return e
		}
		receipt := Arr(record, "sandbox_receipts")[i].(map[string]any)
		exit, _ := Num(receipt, "exit_code")
		if exit != 0 || receipt["children_stopped"] != true || receipt["timed_out"] != false || len(Arr(receipt, "capabilities")) != 0 {
			return fmt.Errorf("native sandbox did not finish within frozen bounds")
		}
	}
	return nil
}
