package evaluation

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func sampleSkillUp(t *testing.T) (SkillUpRun, []byte) {
	t.Helper()
	raw, err := os.ReadFile("testdata/skillup-native-result.json")
	if err != nil {
		t.Fatal(err)
	}
	eval, err := os.ReadFile("testdata/skillup-eval.yaml")
	if err != nil {
		t.Fatal(err)
	}
	evalHash := Digest(eval)
	h := Digest([]byte("fixture"))
	m := Manifest{ProjectID: "project-1", ExperimentID: "experiment-1", RunID: "run-1", Engine: Object{"name": "SKILL_UP", "version": SkillUpSourceRevision, "config_hash": evalHash}, DatasetHash: evalHash, CandidateHash: h, BaselineHash: h, RubricHash: h, Expected: []string{"must-contain-pass", "must-contain-fail", "rule-based-pass", "script-judge"}}
	binHash := "sha256:017e1ebee462402e6856b2db1ee796a817a9ec69f022b9930d2b1a6ac1452544"
	return SkillUpRun{Manifest: m, Variant: "with_skill", Iteration: 1, Attempt: 1, EngineName: "qoder-cli", ProviderName: "qoder", ModelName: "auto", FrozenEvalHash: evalHash, ObservedHash: evalHash, BinaryHash: binHash, ObservedBinaryHash: binHash}, raw
}

func TestSkillUpIterationArtifactSelection(t *testing.T) {
	_, raw := sampleSkillUp(t)
	root := t.TempDir()
	path := filepath.Join(root, "iteration-2")
	if err := os.Mkdir(path, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(path, "result.json"), raw, 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := ReadSkillUpResult(root, 1); err == nil {
		t.Fatal("used result from another iteration")
	}
	got, h, err := ReadSkillUpResult(root, 2)
	if err != nil || h != Digest(raw) || string(got) != string(raw) {
		t.Fatalf("iteration-2 result: %v", err)
	}
}

func TestSkillUpConfigRejectsUnauthorizedEgress(t *testing.T) {
	raw, err := os.ReadFile("testdata/skillup-eval.yaml")
	if err != nil {
		t.Fatal(err)
	}
	h, err := ValidateSkillUpConfig(raw, "qoder-cli", "qoder", "auto")
	if err != nil || h != Digest(raw) {
		t.Fatalf("fixed native config: %s %v", h, err)
	}
	for _, bad := range []string{
		string(raw) + "\nmcp:\n  servers:\n    - url: https://unapproved.example\n",
		strings.Replace(string(raw), "source: local_path", "source: git", 1),
		strings.Replace(string(raw), "path: .", "path: ../../outside", 1),
		strings.Replace(string(raw), "name: auto", "name: changed", 1),
		strings.Replace(string(raw), "type: none", "type: none\n  workspace_mount: /host", 1),
		string(raw) + "\nhooks:\n  exfiltrate: true\n",
	} {
		if _, err := ValidateSkillUpConfig([]byte(bad), "qoder-cli", "qoder", "auto"); err == nil {
			t.Fatalf("accepted unauthorized input: %s", bad)
		}
	}
}

func TestSkillUpNativeResultAndHardGate(t *testing.T) {
	s, raw := sampleSkillUp(t)
	exit := 1 // The fixed CLI exits nonzero when one native case fails.
	report, err := NormalizeSkillUp(s, raw, Digest(raw), &exit, 2000)
	if err != nil {
		t.Fatal(err)
	}
	if report["integrity_status"] != "COMPLETE" {
		t.Fatalf("status=%v", report["integrity_status"])
	}
	c := report["counts"].(Object)
	if c["pass_count"] != 3 || c["fail_count"] != 1 || c["observed_count"] != 4 {
		t.Fatalf("native counts=%v", c)
	}
	if err := ValidateSkillUp(s, report, raw, Digest(raw)); err != nil {
		t.Fatal(err)
	}
	if report["schema_version"] != "2.4.0" || report["dataset_split"] != "DEVELOPMENT" {
		t.Fatalf("scope=%v", report)
	}
	s.Variant = "without_skill"
	baseline, err := NormalizeSkillUp(s, raw, Digest(raw), &exit, 2000)
	if err != nil {
		t.Fatal(err)
	}
	if baseline["integrity_status"] != "INCOMPLETE" || baseline["counts"].(Object)["missing_count"] != 4 {
		t.Fatalf("collapsed with_skill into baseline: %v", baseline["counts"])
	}
}

func TestSkillUpRejectsMalformedNativeEvidence(t *testing.T) {
	s, base := sampleSkillUp(t)
	exit := 1
	decode := func() map[string]any {
		var o map[string]any
		if err := json.Unmarshal(base, &o); err != nil {
			t.Fatal(err)
		}
		return o
	}
	checks := []struct {
		name   string
		mutate func(map[string]any)
		want   string
	}{
		{"unknown case", func(o map[string]any) { o["case_results"].([]any)[0].(map[string]any)["case_id"] = "foreign-case" }, "INVALID"},
		{"duplicate case", func(o map[string]any) { rows := o["case_results"].([]any); o["case_results"] = append(rows, rows[0]) }, "INVALID"},
		{"skip", func(o map[string]any) {
			r := o["case_results"].([]any)[0].(map[string]any)
			r["status"] = "SKIP"
			r["grading"] = nil
		}, "COMPLETE"},
		{"missing", func(o map[string]any) { o["case_results"] = o["case_results"].([]any)[1:] }, "INCOMPLETE"},
		{"empty hard checks", func(o map[string]any) {
			r := o["case_results"].([]any)[0].(map[string]any)
			r["grading"].(map[string]any)["assertion_results"] = []any{}
		}, "INVALID"},
		{"model drift", func(o map[string]any) { o["requested_configuration"].(map[string]any)["model"] = "other" }, "ERROR"},
	}
	for _, tc := range checks {
		t.Run(tc.name, func(t *testing.T) {
			o := decode()
			tc.mutate(o)
			raw := Bytes(o)
			report, err := NormalizeSkillUp(s, raw, Digest(raw), &exit, 2000)
			if tc.want == "ERROR" {
				if err == nil {
					t.Fatal("accepted changed model")
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if report["integrity_status"] != tc.want {
				t.Fatalf("status=%v want=%s", report["integrity_status"], tc.want)
			}
			if err := ValidateSkillUp(s, report, raw, Digest(raw)); err == nil && tc.want != "COMPLETE" {
				t.Fatal("accepted invalid report")
			}
			if tc.name == "skip" {
				r := report["results"].([]Result)[0]
				if r.Verdict != "ERROR" {
					t.Fatalf("SKIP became %s", r.Verdict)
				}
			}
		})
	}
	s.ObservedHash = Digest([]byte("changed eval.yaml"))
	if _, err := NormalizeSkillUp(s, base, Digest(base), &exit, 2000); err == nil {
		t.Fatal("accepted changed input")
	}
	if report, err := NormalizeSkillUp(func() SkillUpRun { s, _ := sampleSkillUp(t); return s }(), base, Digest([]byte("wrong raw")), &exit, 2000); err != nil || report["integrity_status"] != "INVALID" {
		t.Fatalf("raw hash changed: %v %v", report, err)
	}
}
