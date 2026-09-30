package evaluation

import (
	"encoding/json"
	"errors"
	"time"
)

type Dataset struct {
	Cases []Case `json:"cases"`
}
type Case struct {
	ID       string `json:"id"`
	Input    Object `json:"input"`
	Output   Object `json:"simulated_provider_output"`
	Expected string `json:"expected_decision"`
}
type Program struct {
	Mode string `json:"mode"`
}

// Execute is the narrow NATIVE development runner. It executes deterministic
// policies; it never claims to call or qualify a model.
func Execute(datasetBytes, programBytes []byte) ([]Result, error) {
	var d Dataset
	var p Program
	if e := json.Unmarshal(datasetBytes, &d); e != nil {
		return nil, e
	}
	if e := json.Unmarshal(programBytes, &p); e != nil {
		return nil, e
	}
	if len(d.Cases) == 0 {
		return nil, errors.New("zero cases")
	}
	if p.Mode != "EVIDENCE_RULE_V1" && p.Mode != "ALWAYS_ADOPT_V1" && p.Mode != "PROTOCOL_FIXTURE" {
		return nil, errors.New("unsupported frozen native program")
	}
	rows := []Result{}
	seen := map[string]bool{}
	for _, c := range d.Cases {
		if c.ID == "" || seen[c.ID] {
			return nil, errors.New("duplicate/empty input ID")
		}
		seen[c.ID] = true
		if c.Expected != "ADOPT" && c.Expected != "REJECT" {
			return nil, errors.New("missing independent development label")
		}
		start := time.Now()
		selected := "ADOPT"
		valid := c.Input["evidence_present"] == true && c.Input["evidence_current"] == true && c.Input["hard_checks_passed"] == true && c.Input["measured_net_gain_positive"] == true
		if p.Mode == "EVIDENCE_RULE_V1" && !valid {
			selected = "REJECT"
		}
		hard := selected != "ADOPT" || valid
		r := Result{CaseID: c.ID, Verdict: "FAIL", Hard: &hard, Reason: "deterministic development label and adoption gates"}
		if p.Mode == "PROTOCOL_FIXTURE" {
			if c.Output == nil {
				continue
			}
			selected, _ = c.Output["selected"].(string)
			hard = c.Input["hard_checks_passed"] == true && c.Input["evidence_present"] == true && c.Input["evidence_current"] == true
			r.Hard = &hard
			if score, ok := c.Output["score"].(float64); ok {
				r.Score = &score
			}
			if c.Output["abstain"] == true {
				r.Verdict = "ABSTAIN"
				r.Hard = nil
			}
			if c.Output["provider_error"] != nil {
				r.Verdict = "ERROR"
				r.Hard = nil
			}
			if c.Output["duplicate_case_id"] != nil {
				r.Verdict = "PASS"
				rows = append(rows, r)
			}
		}
		if selected == c.Expected && hard {
			r.Verdict = "PASS"
		}
		latency := time.Since(start).Milliseconds()
		r.Latency = &latency
		rows = append(rows, r)
	}
	return rows, nil
}
