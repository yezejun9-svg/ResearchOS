package domain

import (
	"testing"

	"researchos.local/research-os/adapters/evaluation"
)

func evaluationReportContractFixture(t *testing.T) (*Contracts, Object) {
	t.Helper()
	c, err := LoadContracts("../../spec/v2.0/contracts")
	if err != nil {
		t.Fatal(err)
	}
	hash := evaluation.Digest([]byte("development-contract-fixture"))
	m := evaluation.Manifest{ProjectID: "project", ExperimentID: "experiment", RunID: "run", Engine: Object{"name": "NATIVE", "version": "1", "config_hash": hash}, DatasetHash: hash, CandidateHash: hash, BaselineHash: hash, RubricHash: hash, Expected: []string{"case-1"}}
	hard, exit := true, 0
	raw := evaluation.Bytes([]evaluation.Result{{CaseID: "case-1", Verdict: "PASS", Hard: &hard, Reason: "deterministic development case"}})
	report, err := evaluation.Normalize(m, m, raw, evaluation.Digest(raw), &exit, 1)
	if err != nil {
		t.Fatal(err)
	}
	return c, report
}

func TestW1002ReportContractVersions(t *testing.T) {
	c, report := evaluationReportContractFixture(t)
	if err := c.Validate("EvaluationReport", report); err != nil {
		t.Fatalf("legacy NATIVE compatibility: %v", err)
	}
	report["engine"].(map[string]any)["name"] = "SKILL_UP"
	if c.Validate("EvaluationReport", report) == nil {
		t.Fatal("v2.0 must not admit a new engine under an old version")
	}
	report["schema_version"] = "2.4.0"
	if err := c.Validate("EvaluationReport", report); err != nil {
		t.Fatalf("frozen v2.4 SKILL_UP report: %v", err)
	}
	report["engine"].(map[string]any)["name"] = "UNQUALIFIED_ENGINE"
	if c.Validate("EvaluationReport", report) == nil {
		t.Fatal("v2.4 must reject unknown engines")
	}
	report["engine"].(map[string]any)["name"] = "SKILL_UP"
	report["unpublished_field"] = true
	if c.Validate("EvaluationReport", report) == nil {
		t.Fatal("v2.4 must reject unknown report fields")
	}
}

func TestW1002ReportContractProtectedSplit(t *testing.T) {
	c, report := evaluationReportContractFixture(t)
	report["schema_version"] = "2.4.0"
	report["engine"].(map[string]any)["name"] = "SKILL_UP"
	report["dataset_split"] = "HOLDOUT"
	if c.Validate("EvaluationReport", report) == nil {
		t.Fatal("formal split cannot be a PROJECT artifact")
	}
	report["access_class"] = "VERIFIER_ONLY"
	if err := c.Validate("EvaluationReport", report); err != nil {
		t.Fatal(err)
	}
	// Shape validation confers no access or evaluation authority. No holdout
	// labels or protected files are opened by this development-only test.
}
