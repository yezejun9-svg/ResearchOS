package domain

import (
	"os"
	"testing"

	"researchos.local/research-os/adapters/evaluation"
)

func TestW1002NativeSkillUpReportMeetsFrozenContract(t *testing.T) {
	c, err := LoadContracts("../../spec/v2.0/contracts")
	if err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile("../../adapters/evaluation/testdata/skillup-native-result.json")
	if err != nil {
		t.Fatal(err)
	}
	eval, err := os.ReadFile("../../adapters/evaluation/testdata/skillup-eval.yaml")
	if err != nil {
		t.Fatal(err)
	}
	evalHash, err := evaluation.ValidateSkillUpConfig(eval, "qoder-cli", "qoder", "auto")
	if err != nil {
		t.Fatal(err)
	}
	h := evaluation.Digest([]byte("fixture"))
	m := evaluation.Manifest{ProjectID: "project-1", ExperimentID: "experiment-1", RunID: "run-1", Engine: Object{"name": "SKILL_UP", "version": "7f1ff9b8e2d7c654728de526867f2f7e7b78ea51", "config_hash": evalHash}, DatasetHash: evalHash, CandidateHash: h, BaselineHash: h, RubricHash: h, Expected: []string{"must-contain-pass", "must-contain-fail", "rule-based-pass", "script-judge"}}
	binHash := "sha256:017e1ebee462402e6856b2db1ee796a817a9ec69f022b9930d2b1a6ac1452544"
	s := evaluation.SkillUpRun{Manifest: m, Variant: "with_skill", Iteration: 1, Attempt: 1, EngineName: "qoder-cli", ProviderName: "qoder", ModelName: "auto", FrozenEvalHash: evalHash, ObservedHash: evalHash, BinaryHash: binHash, ObservedBinaryHash: binHash}
	exit := 1
	report, err := evaluation.NormalizeSkillUp(s, raw, evaluation.Digest(raw), &exit, 2000)
	if err != nil {
		t.Fatal(err)
	}
	if err := evaluation.ValidateSkillUp(s, report, raw, evaluation.Digest(raw)); err != nil {
		t.Fatal(err)
	}
	if err := c.Validate("EvaluationReport", report); err != nil {
		t.Fatalf("native result cannot enter v2.4 schema: %v", err)
	}
}
