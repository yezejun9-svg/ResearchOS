package evaluation

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func check(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if string(Bytes(want)) != string(Bytes(got)) {
		status = "FAIL"
	}
	fmt.Println("W10_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": "deterministic protocol assertion"})))
	if status != "PASS" {
		t.Fatalf("%s", id)
	}
}
func fixture(t *testing.T) (Manifest, []Result, map[string]string) {
	raw, e := os.ReadFile("../../spec/v2.0/examples/evaluation_smoke_cases.json")
	if e != nil {
		t.Fatal(e)
	}
	var f struct {
		Cases []struct {
			ID       string         `json:"id"`
			Input    map[string]any `json:"input"`
			Output   map[string]any `json:"simulated_provider_output"`
			Expected string         `json:"expected_handling"`
			Decision string         `json:"expected_decision"`
		} `json:"cases"`
	}
	if e = json.Unmarshal(raw, &f); e != nil {
		t.Fatal(e)
	}
	h := Digest(raw)
	m := Manifest{ProjectID: "dev-project", ExperimentID: "dev-experiment", RunID: "dev-run", Engine: Object{"name": "NATIVE", "version": "1", "config_hash": h}, DatasetHash: h, CandidateHash: h, BaselineHash: h, RubricHash: h}
	rows := []Result{}
	expected := map[string]string{}
	for _, c := range f.Cases {
		m.Expected = append(m.Expected, c.ID)
		expected[c.ID] = c.Expected
		if c.Output == nil {
			continue
		}
		hard := c.Input["hard_checks_passed"] == true && c.Input["evidence_present"] == true && c.Input["evidence_current"] == true
		r := Result{CaseID: c.ID, Hard: &hard, Reason: "frozen expected decision and deterministic conditions", Verdict: "FAIL"}
		if c.Output["selected"] == c.Decision && hard {
			r.Verdict = "PASS"
		}
		if v, ok := c.Output["score"].(float64); ok {
			r.Score = &v
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
		rows = append(rows, r)
	}
	return m, rows, expected
}
func TestProtocol(t *testing.T) {
	m, rows, expected := fixture(t)
	zero := 0
	raw := Bytes(rows)
	r, e := Normalize(m, m, raw, Digest(raw), &zero, 1)
	if e != nil {
		t.Fatal(e)
	}
	for _, v := range r["results"].([]Result) {
		got := v.Verdict
		if v.CaseID == "PF-11" && r["counts"].(Object)["duplicate_count"] == 1 && r["integrity_status"] == "INVALID" {
			got = "INVALID"
		}
		check(t, v.CaseID, expected[v.CaseID], got)
	}
	check(t, "C21-COUNTS", Object{"expected_count": 12, "observed_count": 11, "pass_count": 5, "fail_count": 4, "error_count": 1, "abstain_count": 1, "missing_count": 1, "duplicate_count": 1}, r["counts"])
	empty := m
	empty.Expected = nil
	_, e = Normalize(empty, empty, []byte("[]"), Digest([]byte("[]")), &zero, 0)
	check(t, "C21-ZERO", true, e != nil)
	for _, field := range []string{"config", "dataset", "candidate", "baseline", "rubric", "unknown", "raw"} {
		changed := m
		changed.Engine = Object{"name": "NATIVE", "version": "1", "config_hash": m.DatasetHash}
		x := append([]Result{}, rows[:10]...)
		wantRaw := Digest(Bytes(x))
		switch field {
		case "config":
			changed.Engine["config_hash"] = Digest([]byte("tamper"))
		case "dataset":
			changed.DatasetHash = Digest([]byte("tamper"))
		case "candidate":
			changed.CandidateHash = Digest([]byte("tamper"))
		case "baseline":
			changed.BaselineHash = Digest([]byte("tamper"))
		case "rubric":
			changed.RubricHash = Digest([]byte("tamper"))
		case "unknown":
			x = append(x, Result{CaseID: "unknown"})
			wantRaw = Digest(Bytes(x))
		case "raw":
			wantRaw = Digest([]byte("wrong"))
		}
		bad, e := Normalize(m, changed, Bytes(x), wantRaw, &zero, 1)
		if field != "unknown" && field != "raw" {
			check(t, "C21-TAMPER-"+field, true, e != nil && bad == nil)
			continue
		}
		if e != nil {
			t.Fatal(e)
		}
		check(t, "C21-TAMPER-"+field, "INVALID", bad["integrity_status"])
	}
	// A complete failed run is not a successful candidate, even with exit zero.
	stable := []Result{}
	hard := true
	for _, id := range m.Expected {
		stable = append(stable, Result{CaseID: id, Verdict: "PASS", Hard: &hard, Reason: "stable deterministic decision"})
	}
	sr, _ := Normalize(m, m, Bytes(stable), Digest(Bytes(stable)), &zero, 1)
	check(t, "C21-STABLE", 12, sr["counts"].(Object)["pass_count"])
	check(t, "C21-VALID", true, Validate(m, sr, Bytes(stable), Digest(Bytes(stable))) == nil)
	stable[0].Verdict = "FAIL"
	regressed, _ := Normalize(m, m, Bytes(stable), Digest(Bytes(stable)), &zero, 1)
	check(t, "C21-REGRESSION", []any{"COMPLETE", 1}, []any{regressed["integrity_status"], regressed["counts"].(Object)["fail_count"]})
	stable[0].Verdict = "PASS"
	no := false
	stable[0].Hard = &no
	score := 0.99
	stable[0].Score = &score
	high, _ := Normalize(m, m, Bytes(stable), Digest(Bytes(stable)), &zero, 1)
	check(t, "C21-HIGH-SCORE", "FAIL", high["results"].([]Result)[0].Verdict)
	exit := 7
	badExit, _ := Normalize(m, m, Bytes(stable), Digest(Bytes(stable)), &exit, 1)
	check(t, "C21-EXIT", 7, *badExit["exit_code"].(*int))
	sr["counts"].(Object)["pass_count"] = 0
	check(t, "C21-COUNT-TAMPER", true, Validate(m, sr, Bytes(stable), Digest(Bytes(stable))) != nil)
	if dir := os.Getenv("W10_EVIDENCE_DIR"); dir != "" {
		for name, v := range map[string]any{"protocol-report": r, "regressed-report": regressed, "high-score-report": high, "error-exit-report": badExit, "manifest": m, "raw-results": rows} {
			if e = os.WriteFile(filepath.Join(dir, name+".json"), Bytes(v), 0600); e != nil {
				t.Fatal(e)
			}
		}
	}
}

func TestRawIntegrity(t *testing.T) {
	m, rawRows, _ := fixture(t)
	raw := Bytes(rawRows)
	zero := 0
	report, e := Normalize(m, m, raw, Digest(raw), &zero, 1)
	if e != nil {
		t.Fatal(e)
	}
	report["integrity_status"] = "COMPLETE"
	report["counts"].(Object)["duplicate_count"] = 0
	check(t, "C21-REJECT-LAUNDERED-DUPLICATE", true, Validate(m, report, raw, Digest(raw)) != nil)
	hard := true
	complete := []Result{}
	for _, id := range m.Expected {
		complete = append(complete, Result{CaseID: id, Verdict: "PASS", Hard: &hard, Reason: "fixed"})
	}
	complete = append(complete, Result{CaseID: "unknown", Verdict: "PASS", Hard: &hard, Reason: "unknown"})
	raw = Bytes(complete)
	report, e = Normalize(m, m, raw, Digest(raw), &zero, 1)
	if e != nil {
		t.Fatal(e)
	}
	report["integrity_status"] = "COMPLETE"
	check(t, "C21-REJECT-LAUNDERED-UNKNOWN", true, Validate(m, report, raw, Digest(raw)) != nil)
	complete = complete[:len(complete)-1]
	raw = Bytes(complete)
	report, e = Normalize(m, m, raw, Digest(raw), &zero, 1)
	if e != nil {
		t.Fatal(e)
	}
	originalHash := Digest(raw)
	complete[0].Verdict = "ERROR"
	changed := Bytes(complete)
	check(t, "C21-REJECT-RAW-ROWS-MISMATCH", true, Validate(m, report, changed, originalHash) != nil)
	check(t, "C21-REJECT-REPORT-ROWS-MISMATCH", true, Validate(m, report, changed, Digest(changed)) != nil)
	_, e = Normalize(m, m, []byte(`[{"case_id":"x","case_id":"y"}]`), Digest([]byte(`[{"case_id":"x","case_id":"y"}]`)), &zero, 1)
	check(t, "C21-REJECT-AMBIGUOUS-JSON", true, e != nil)
}

func TestObservedManifestFence(t *testing.T) {
	m, _, _ := fixture(t)
	zero := 0
	hard := true
	rows := []Result{}
	for _, id := range m.Expected {
		rows = append(rows, Result{CaseID: id, Verdict: "PASS", Hard: &hard, Reason: "complete"})
	}
	raw := Bytes(rows)
	for _, field := range []string{"project", "experiment", "run", "engine", "config", "dataset", "candidate", "baseline", "rubric", "expected"} {
		observed := m
		observed.Engine = Object{"name": "NATIVE", "version": "1", "config_hash": m.DatasetHash}
		switch field {
		case "project":
			observed.ProjectID = "other"
		case "experiment":
			observed.ExperimentID = "other"
		case "run":
			observed.RunID = "other"
		case "engine":
			observed.Engine["version"] = "other"
		case "config":
			observed.Engine["config_hash"] = Digest([]byte("other"))
		case "dataset":
			observed.DatasetHash = Digest([]byte("other"))
		case "candidate":
			observed.CandidateHash = Digest([]byte("other"))
		case "baseline":
			observed.BaselineHash = Digest([]byte("other"))
		case "rubric":
			observed.RubricHash = Digest([]byte("other"))
		case "expected":
			observed.Expected = []string{"other"}
		}
		report, err := Normalize(m, observed, raw, Digest(raw), &zero, 1)
		check(t, "C21-OBSERVED-FENCE-"+field, true, err != nil && report == nil)
	}
}
