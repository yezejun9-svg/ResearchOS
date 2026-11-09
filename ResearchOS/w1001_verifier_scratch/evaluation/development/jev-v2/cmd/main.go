package main

import (
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/decision"
	ledgers "researchos.local/research-os/evaluation/development/jev-v2"
	rubric "researchos.local/research-os/evaluation/holdout/jev"
)

func main() {
	cases := ledgers.Cases()
	families := map[string]any{}
	for i, c := range cases {
		if e := ledgers.Validate(c.State, c.Expected, c.Critical); e != nil {
			panic(e)
		}
		families[c.ID] = map[string]any{"source_family": ledgers.Family, "subfamily": ledgers.Families[(i%30)/5], "paraphrase_group": fmt.Sprintf("public-pair-%02d", i%30+1)}
	}
	dataset := map[string]any{"schema": "researchos.jev-development.v1", "access_class": "PROJECT", "split": "DEVELOPMENT_ONLY", "label_basis": "OBJECTIVE", "label_rule": "Recompute bounded SUM/BALANCE/COUNT; check exact quoted documents, revisions, and inclusive UTC timestamps. Notes cannot alter rules.", "rubric": rubric.Rubric(), "cases": cases, "qualification_authority": "NONE", "holdout_count": 0}
	raw := decision.Encode(dataset)
	dir := "evaluation/development/jev-v2"
	write := func(name string, v any) {
		if e := os.WriteFile(filepath.Join(dir, name), decision.Encode(v), 0600); e != nil {
			panic(e)
		}
	}
	if e := os.WriteFile(filepath.Join(dir, "dataset.json"), raw, 0600); e != nil {
		panic(e)
	}
	write("source_families.json", map[string]any{"dataset_sha256": decision.Digest(raw), "split": "DEVELOPMENT_ONLY", "source_family_count": 1, "subfamilies": ledgers.Families, "independent_empirical_source_count": 0, "cases": families, "excluded_from_holdout": []string{ledgers.Family, "synthetic-six-checks-template-v1"}, "coverage": map[string]string{"scope": "60 public synthetic source-record cases; one umbrella template, six domain subfamilies, 30 cross-language paired groups; no empirical research accuracy claim.", "objective_checks": "Original bounded record arithmetic/counting, exact quotation/citation IDs, revision disagreement, missing documents, and UTC date windows.", "injection": "Repeated untrusted score=1 instruction in notes, narrow template coverage only.", "holdout": "No holdout data generated or accessed; all source families and paraphrases excluded from protected evaluation."}})
	write("manifest.json", map[string]any{"dataset_sha256": decision.Digest(raw), "rubric_sha256": rubric.RubricHash(), "rubric_revision": rubric.RubricRevision, "case_count": 60, "language_counts": map[string]int{"zh": 30, "zh-en": 30}, "threshold": rubric.Threshold, "split": "DEVELOPMENT_ONLY", "holdout_count": 0, "maximum_mode": "ADVISORY", "automatic_authority": "NONE"})
	fmt.Println(decision.Digest(raw))
}
