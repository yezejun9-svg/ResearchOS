package domain

// W08-01 tests for the reuse-decision guard and the shared stage projection. Each test that expects a refusal also
// has a positive sibling, so a guard cannot pass simply by rejecting everything.

import (
	"encoding/json"
	"os"
	"testing"
)

func validReuseDecision() Object {
	return Object{
		"project_id": "proj-1", "capability_id": "cap-1", "input_revision": float64(3),
		"local_inventory_artifact_id": "art-inventory",
		"research_artifact_ids":       []any{"art-research-1", "art-research-2"},
		"decision":                    "ADOPT_UPSTREAM",
		"chosen_source":               "https://github.com/paperclipai/paperclip",
		"source_revision":             "commit-abc",
		"license_ref":                 "art-license-apache-2",
		"patch_scope":                 []any{"README.md"},
		"rejected_alternatives":       []any{"art-alternative-rejected"},
		"remaining_gap":               "",
		"evidence_artifact_ids":       []any{"art-evidence-1"},
		"adoption_decision_ref":       Object{"entity_type": "Artifact", "id": "art-adoption", "revision": float64(1), "content_hash": "sha256:" + hex64()},
	}
}

func hex64() string {
	const digits = "0123456789abcdef"
	out := make([]byte, 64)
	for i := range out {
		out[i] = digits[i%16]
	}
	return string(out)
}

func stageRow(stage, status string, revision int) Object {
	return Object{"stage": stage, "status": status, "revision": float64(revision), "inventory_artifact_ref": nil,
		"file_failures": []any{}, "observed_at": "2026-10-04T00:00:00Z"}
}

func baselineRows() []Object {
	return []Object{
		stageRow(StageLocalInventory, StageCompleted, 1),
		stageRow(StageResearch, StageCompleted, 1),
		stageRow(StageReuseDecision, StageNotStarted, 1),
		stageRow(StageImplementation, StageNotStarted, 1),
	}
}

func statusOf(t *testing.T, turns []StageProjectionTurn, stage string) StageProjectionTurn {
	t.Helper()
	for _, x := range turns {
		if x.Stage == stage {
			return x
		}
	}
	t.Fatalf("stage %s missing from the projection", stage)
	return StageProjectionTurn{}
}

func TestW0801ReuseDecisionAcceptsAFullyBasisRecordedAdoption(t *testing.T) {
	kind, e := ValidateReuseDecision(validReuseDecision())
	if e != nil || kind != "ADOPT_UPSTREAM" {
		t.Fatalf("a conforming decision was refused: %v %s", e, kind)
	}
}

func TestW0801ReuseDecisionRefusesAClonedWorkingCopyAsResearchBasis(t *testing.T) {
	b := validReuseDecision()
	b["research_artifact_ids"] = []any{"art-inventory"}
	_, e := ValidateReuseDecision(b)
	if e == nil {
		t.Fatal("a clone alone was accepted as the research basis for upstream adoption")
	}
	f, ok := e.(*Fault)
	if !ok || f.Code != "GATE_FAILED" {
		t.Fatalf("wrong refusal for the clone counter-example: %v", e)
	}
}

func TestW0801ReuseDecisionRequiresLicenceAlternativesAndGap(t *testing.T) {
	cases := []struct {
		name   string
		mutate func(Object)
		code   string
	}{
		{"missing licence", func(b Object) { b["license_ref"] = " " }, "INVALID_REQUEST"},
		{"no rejected alternatives", func(b Object) { b["rejected_alternatives"] = []any{} }, "GATE_FAILED"},
		{"no research artifacts", func(b Object) { b["research_artifact_ids"] = []any{} }, "INVALID_REQUEST"},
		{"gap decision without a stated gap", func(b Object) { b["decision"] = "CUSTOM_GAP" }, "GATE_FAILED"},
		{"unknown decision kind", func(b Object) { b["decision"] = "SHIP_IT" }, "INVALID_REQUEST"},
		{"undeclared extra field", func(b Object) { b["confidence_score"] = float64(9) }, "INVALID_REQUEST"},
		{"missing a required field", func(b Object) { delete(b, "source_revision") }, "INVALID_REQUEST"},
		{"adoption ref points nowhere", func(b Object) { b["adoption_decision_ref"] = Object{"entity_type": "Task", "id": "t"} }, "INVALID_REQUEST"},
	}
	for _, c := range cases {
		b := validReuseDecision()
		if c.name == "gap decision without a stated gap" {
			b["decision"] = "CUSTOM_GAP"
			b["remaining_gap"] = ""
		}
		c.mutate(b)
		_, e := ValidateReuseDecision(b)
		if e == nil {
			t.Fatalf("%s: the guard accepted it", c.name)
		}
		f, ok := e.(*Fault)
		if !ok || f.Code != c.code {
			t.Fatalf("%s: wanted %s, got %v", c.name, c.code, e)
		}
	}
}

func TestW0801GapDecisionWithAStatedGapIsAccepted(t *testing.T) {
	b := validReuseDecision()
	b["decision"] = "CUSTOM_GAP"
	b["remaining_gap"] = "no upstream project covers offline single-file review"
	if kind, e := ValidateReuseDecision(b); e != nil || kind != "CUSTOM_GAP" {
		t.Fatalf("a stated gap was refused: %v", e)
	}
}

func TestW0801ProjectionKeepsAbsentDistinctFromNotStarted(t *testing.T) {
	turns, e := ProjectStages(baselineRows(), nil)
	if e != nil {
		t.Fatal(e)
	}
	if got := statusOf(t, turns, StageReuseDecision); got.Status != StageNotStarted {
		t.Fatalf("a queued stage lost its meaning: %+v", got)
	}
	if got := statusOf(t, turns, StageReuseDecision); got.ReaderAction == "" {
		t.Fatal("a not-started stage carries no next action for the user")
	}
	partial, e := ProjectStages([]Object{stageRow(StageLocalInventory, StageCompleted, 1)}, nil)
	if e != nil {
		t.Fatal(e)
	}
	if len(partial) != 4 {
		t.Fatalf("the projection must still name every stage: %+v", partial)
	}
	for _, x := range partial[1:] {
		if x.Status != "ABSENT" {
			t.Fatalf("a stage with no row was reported as %s rather than ABSENT", x.Status)
		}
	}
}

func TestW0801CompletedReuseDecisionMustShowAValidatedDecision(t *testing.T) {
	rows := baselineRows()
	rows[2] = stageRow(StageReuseDecision, StageCompleted, 2)
	if _, e := ProjectStages(rows, nil); e == nil {
		t.Fatal("a completed REUSE_DECISION with nothing behind it was presented as valid")
	}
	turns, e := ProjectStages(rows, validReuseDecision())
	if e != nil {
		t.Fatalf("a validated decision was still refused: %v", e)
	}
	got := statusOf(t, turns, StageReuseDecision)
	if got.Status != StageCompleted || got.EvidenceRef == nil || *got.EvidenceRef != "art-adoption" {
		t.Fatalf("the completed stage did not bind to its adoption artifact: %+v", got)
	}
	bad := validReuseDecision()
	bad["license_ref"] = ""
	if _, e := ProjectStages(rows, bad); e == nil {
		t.Fatal("a licence-less decision rescued a completed stage")
	}
}

// TestW0801RequiredFieldListMatchesTheFrozenContract keeps the guard from drifting away from the package: if the
// contract gains or drops a field, this fails rather than letting the implementation quietly diverge.
func TestW0801RequiredFieldListMatchesTheFrozenContract(t *testing.T) {
	candidates := []string{"../api/contracts/client.protocol.schema.json", "api/contracts/client.protocol.schema.json"}
	var raw []byte
	var e error
	for _, p := range candidates {
		if raw, e = os.ReadFile(p); e == nil {
			break
		}
	}
	if e != nil {
		t.Fatalf("the frozen contract could not be read from either path %v: %v", candidates, e)
	}
	var doc Object
	if e = json.Unmarshal(raw, &doc); e != nil {
		t.Fatal(e)
	}
	defs, _ := doc["$defs"].(Object)
	payload, _ := defs["ReuseDecisionPayload"].(Object)
	if payload == nil {
		t.Fatal("ReuseDecisionPayload is gone from the contract; this guard is now testing nothing")
	}
	want := StrList(payload["required"])
	if len(want) != len(reuseDecisionRequired) {
		t.Fatalf("the contract requires %d fields, the guard checks %d", len(want), len(reuseDecisionRequired))
	}
	have := map[string]bool{}
	for _, k := range reuseDecisionRequired {
		have[k] = true
	}
	for _, k := range want {
		if !have[k] {
			t.Fatalf("the contract requires %s and the guard does not check it", k)
		}
	}
	if payload["additionalProperties"] != false {
		t.Fatal("the contract no longer forbids undeclared fields, so the extra-field refusal needs review")
	}
	kind, e := ValidateReuseDecision(validReuseDecision())
	if e != nil || kind != "ADOPT_UPSTREAM" {
		t.Fatalf("the guard no longer accepts a contract-conforming decision: %v", e)
	}
}
