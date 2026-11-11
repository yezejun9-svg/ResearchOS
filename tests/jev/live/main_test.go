package main

import (
	"encoding/json"
	"os"
	"researchos.local/research-os/adapters/decision"
	"testing"
)

func TestDevelopmentObjectiveLabels(t *testing.T) {
	raw, e := os.ReadFile("../../../evaluation/development/jev/dataset.json")
	if e != nil {
		t.Fatal(e)
	}
	var data dataset
	if e = decision.Strict(raw, &data); e != nil {
		t.Fatal(e)
	}
	if len(data.Cases) != 60 || data.HoldoutCount != 0 || data.Authority != "NONE" || data.Split != "DEVELOPMENT_ONLY" {
		t.Fatal("development scope differs")
	}
	counts := map[string]int{}
	ids := map[string]bool{}
	for _, c := range data.Cases {
		if e = validateCase(c); e != nil {
			t.Fatalf("%s: %v", c.ID, e)
		}
		if ids[c.ID] {
			t.Fatal("duplicate case")
		}
		ids[c.ID] = true
		counts[c.Scope.Language+":"+c.Expected]++
	}
	for _, key := range []string{"zh:ACCEPT", "zh:REJECT", "zh-en:ACCEPT", "zh-en:REJECT"} {
		if counts[key] != 15 {
			t.Fatalf("unexpected label count %s", key)
		}
	}
	c := data.Cases[0]
	c.Expected = "REJECT"
	if validateCase(c) == nil {
		t.Fatal("forged label accepted")
	}
	c = data.Cases[0]
	c.ID = "../../../escape"
	if validateCase(c) == nil {
		t.Fatal("unsafe output identity accepted")
	}
	var manifest struct {
		DatasetHash string `json:"dataset_sha256"`
	}
	manifestRaw, e := os.ReadFile("../../../evaluation/development/jev/manifest.json")
	if e != nil {
		t.Fatal(e)
	}
	// Only the hash is needed; the manifest's other declarations are checked above.
	if e = json.Unmarshal(manifestRaw, &manifest); e != nil {
		t.Fatal(e)
	}
	if manifest.DatasetHash != decision.Digest(raw) {
		t.Fatal("frozen dataset hash mismatch")
	}
	var families struct {
		DatasetHash string `json:"dataset_sha256"`
		Cases       map[string]struct {
			Family      string `json:"source_family"`
			Group       string `json:"paraphrase_group"`
			Independent bool   `json:"independent_source"`
		} `json:"cases"`
	}
	familyRaw, e := os.ReadFile("../../../evaluation/development/jev/source_families.json")
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(familyRaw, &families); e != nil {
		t.Fatal(e)
	}
	if families.DatasetHash != decision.Digest(raw) || len(families.Cases) != 60 {
		t.Fatal("family map not bound to complete development dataset")
	}
	groups := map[string]int{}
	for _, c := range data.Cases {
		family, ok := families.Cases[c.ID]
		if !ok || family.Family != "synthetic-six-checks-template-v1" || family.Independent {
			t.Fatal("missing or overstated source independence")
		}
		groups[family.Group]++
	}
	if len(groups) != 30 {
		t.Fatal("paired-language groups differ")
	}
	for _, n := range groups {
		if n != 2 {
			t.Fatal("paraphrase group must preserve both language variants")
		}
	}
	c = data.Cases[0]
	r := data.Rubric
	envelope := decision.Envelope{MeasurementMode: "LIVE", JevCalled: true, Request: decision.Request{Model: c.Scope.ModelRevision, State: c.State, Questions: r.Questions}, Binding: decision.Binding{ProjectID: "W11-development", InputHash: decision.Digest(decision.Encode(c.State)), RubricHash: decision.Digest(decision.Encode(r)), Scope: c.Scope}}
	if !matchesCase(envelope, c, r) || matchesCase(envelope, data.Cases[1], r) {
		t.Fatal("reanalysis must reject another case's response")
	}
	envelope.MeasurementMode = "FIXTURE"
	if matchesCase(envelope, c, r) {
		t.Fatal("fixture cannot become a reanalysed live response")
	}
}
