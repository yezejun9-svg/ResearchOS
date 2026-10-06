package evaluation

import "testing"

func TestNativeProviderStatus(t *testing.T) {
	m, _, _ := fixture(t)
	m.Expected = []string{"one"}
	zero := 0
	for _, c := range []struct {
		output     Object
		verdict    string
		duplicates int
	}{
		{Object{"selected": "ADOPT"}, "PASS", 0},
		{Object{"selected": "REJECT"}, "FAIL", 0},
		{Object{"selected": "ADOPT", "provider_error": "timeout"}, "ERROR", 0},
		{Object{"selected": "ADOPT", "abstain": true}, "ABSTAIN", 0},
		{Object{"selected": "ADOPT", "abstain": true, "provider_error": "timeout"}, "ERROR", 0},
		{Object{"selected": "ADOPT", "abstain": true, "provider_error": "timeout", "duplicate_case_id": "one"}, "ERROR", 1},
	} {
		input := Object{"evidence_present": true, "evidence_current": true, "hard_checks_passed": true}
		rows, err := Execute(Bytes(Dataset{Cases: []Case{{ID: "one", Input: input, Output: c.output, Expected: "ADOPT"}}}), Bytes(Program{Mode: "PROTOCOL_FIXTURE"}))
		if err != nil || len(rows) != 1+c.duplicates || rows[0].Verdict != c.verdict {
			t.Fatalf("provider status lost: %s %v", Bytes(rows), err)
		}
		raw := Bytes(rows)
		report, err := Normalize(m, m, raw, Digest(raw), &zero, 0)
		key := map[string]string{"PASS": "pass_count", "FAIL": "fail_count", "ERROR": "error_count", "ABSTAIN": "abstain_count"}[c.verdict]
		if err != nil || report["results"].([]Result)[0].Verdict != c.verdict || report["counts"].(Object)[key] != 1 || report["counts"].(Object)["duplicate_count"] != c.duplicates {
			t.Fatalf("normalized provider status/count lost: %s %v", Bytes(report), err)
		}
	}
	check(t, "C21-NATIVE-PROVIDER-STATUS", true, true)
}
