package domain

// W08-01: one stage projection shared by project.bootstrap (init) and the Desktop workbench, plus the guard that
// decides whether a reuse decision may be recorded at all.
//
// The shapes here come from the frozen package rather than being invented: ReuseDecisionPayload in
// internal/api/contracts/client.protocol.schema.json declares 14 required fields, additionalProperties false and the
// decision enum below, and no code referenced it before this file. The stage constants and the NOT_STARTED row that
// project.bootstrap writes deliberately stay untouched: W05-03 recorded RESEARCH, REUSE_DECISION and IMPLEMENTATION as
// NOT_STARTED precisely so an absent row can never be read as "nothing left to do", and this file only ever derives
// status from evidence that actually exists - it never promotes a stage because time passed.

import (
	"fmt"
	"strings"
)

// reuseDecisions is the enum frozen in the client protocol schema.
var reuseDecisions = map[string]bool{"REUSE_LOCAL": true, "ADOPT_UPSTREAM": true, "ADAPT_UPSTREAM": true, "CUSTOM_GAP": true}

// reuseDecisionRequired lists the payload fields the contract demands. Kept as data so a re-issued schema that adds a
// field shows up as a comparison failure in tests rather than silently passing.
var reuseDecisionRequired = []string{"project_id", "capability_id", "input_revision", "local_inventory_artifact_id",
	"research_artifact_ids", "decision", "chosen_source", "source_revision", "license_ref", "patch_scope",
	"rejected_alternatives", "remaining_gap", "evidence_artifact_ids", "adoption_decision_ref"}

// ValidateReuseDecision refuses a decision the frozen contract or this card's counter-examples do not allow. It
// returns the decision kind it accepted so a caller can bind the stage promotion to the same value it checked.
func ValidateReuseDecision(b Object) (string, error) {
	for _, k := range reuseDecisionRequired {
		if _, ok := b[k]; !ok {
			return "", Fail(400, "INVALID_REQUEST", "reuse decision is missing "+k)
		}
	}
	// additionalProperties:false in the schema. An extra key here is how a caller quietly widens a contract, so it is
	// refused rather than ignored.
	for k := range b {
		known := false
		for _, r := range reuseDecisionRequired {
			if k == r {
				known = true
			}
		}
		if !known {
			return "", Fail(400, "INVALID_REQUEST", "reuse decision carries an undeclared field "+k)
		}
	}
	decision := Str(b, "decision")
	if !reuseDecisions[decision] {
		return "", Fail(400, "INVALID_REQUEST", "reuse decision kind is not one of REUSE_LOCAL|ADOPT_UPSTREAM|ADAPT_UPSTREAM|CUSTOM_GAP")
	}
	for _, k := range []string{"project_id", "capability_id", "local_inventory_artifact_id", "chosen_source", "source_revision", "license_ref"} {
		if strings.TrimSpace(Str(b, k)) == "" {
			return "", Fail(400, "INVALID_REQUEST", "reuse decision field "+k+" must not be empty")
		}
	}
	research := StrList(b["research_artifact_ids"])
	evidence := StrList(b["evidence_artifact_ids"])
	if len(research) == 0 || len(evidence) == 0 {
		return "", Fail(400, "INVALID_REQUEST", "a reuse decision needs at least one research artifact and one evidence artifact")
	}
	// The card's first named counter-example: cloning a repository and calling that adoption. A local inventory scan
	// is not research, so the inventory artifact may not double as the research basis for an upstream decision.
	if decision != "REUSE_LOCAL" && decision != "CUSTOM_GAP" {
		inventory := Str(b, "local_inventory_artifact_id")
		for _, r := range research {
			if r == inventory {
				return "", Fail(422, "GATE_FAILED", "a cloned working copy is not research evidence for upstream adoption")
			}
		}
	}
	// A gap decision has to say what is still missing; an empty string here is how "we found nothing" gets recorded as
	// a completed decision.
	if decision == "CUSTOM_GAP" && strings.TrimSpace(Str(b, "remaining_gap")) == "" {
		return "", Fail(422, "GATE_FAILED", "CUSTOM_GAP must state the remaining gap")
	}
	if decision != "CUSTOM_GAP" && len(StrList(b["rejected_alternatives"])) == 0 {
		return "", Fail(422, "GATE_FAILED", "a reuse decision must record the alternatives it rejected")
	}
	ref, ok := b["adoption_decision_ref"].(Object)
	if !ok || Str(ref, "entity_type") != "Artifact" || Str(ref, "id") == "" || Str(ref, "content_hash") == "" {
		return "", Fail(400, "INVALID_REQUEST", "adoption_decision_ref must be a VersionRef pointing at a sealed Artifact")
	}
	if n, isNum := b["input_revision"].(float64); !isNum || n < 1 {
		return "", Fail(400, "INVALID_REQUEST", "input_revision must be a positive integer")
	}
	return decision, nil
}

// StageProjectionTurn is one stage as init and Desktop are shown it. Absent is kept distinct from NotStarted so a
// reader can tell "this project never got a stage row" from "the stage is queued and nothing has been done in it".
type StageProjectionTurn struct {
	Stage        string
	Status       string
	EvidenceRef  *string
	DerivedFrom  string
	ReaderAction string
}

// ProjectStages derives the four-stage view from the stage rows project.bootstrap wrote plus the reuse decision that
// promoted REUSE_DECISION, if any. Inputs are the stored row bodies, not a live database handle, so the same function
// serves the CLI, the Desktop and the tests.
func ProjectStages(rows []Object, decision Object) ([]StageProjectionTurn, error) {
	byStage := map[string]Object{}
	for _, r := range rows {
		byStage[Str(r, "stage")] = r
	}
	known := []string{StageLocalInventory, StageResearch, StageReuseDecision, StageImplementation}
	out := make([]StageProjectionTurn, 0, len(known))
	for _, stage := range known {
		row, present := byStage[stage]
		if !present {
			out = append(out, StageProjectionTurn{Stage: stage, Status: "ABSENT",
				DerivedFrom:  "no stage row was ever written for this project",
				ReaderAction: "run project.bootstrap before reading reuse status"})
			continue
		}
		status := Str(row, "status")
		if status == "" {
			status = StageNotStarted
		}
		turn := StageProjectionTurn{Stage: stage, Status: status, EvidenceRef: optionalRef(row["inventory_artifact_ref"]),
			DerivedFrom:  "stored stage row revision " + fmt.Sprint(row["revision"]),
			ReaderAction: readerAction(stage, status)}
		if stage == StageReuseDecision {
			// A stored promotion is only reported when a decision that passes the guard backs it. This is what stops
			// "the row says COMPLETED" from being self-justifying after a manual database edit.
			if status == StageCompleted {
				if decision == nil {
					return nil, Fail(422, "GATE_FAILED", "REUSE_DECISION is recorded completed with no decision to show")
				}
				if _, e := ValidateReuseDecision(decision); e != nil {
					return nil, e
				}
				ref := decision["adoption_decision_ref"].(Object)
				turn.EvidenceRef = ptr(Str(ref, "id"))
				turn.DerivedFrom = "validated reuse decision " + Str(decision, "decision") + " over " +
					fmt.Sprint(len(StrList(decision["research_artifact_ids"]))) + " research artifacts"
			}
		}
		out = append(out, turn)
	}
	return out, nil
}

// readerAction keeps the projection actionable rather than merely decorative: every non-completed status names the
// next step, which is what the card means by a user-operable request.
func readerAction(stage, status string) string {
	switch status {
	case StageCompleted:
		return "nothing owed at this stage"
	case StagePartial:
		return "some sources or artifacts failed; re-read the gap reason before retrying"
	case StageFailed:
		return "this stage failed as a whole; inspect its file failures"
	case StageNotStarted:
		switch stage {
		case StageResearch:
			return "run a research cycle over the declared sources"
		case StageReuseDecision:
			return "record a reuse decision, or state the remaining gap"
		case StageImplementation:
			return "implement only what the reuse decision left open"
		}
		return "start this stage"
	}
	return "unrecognised stage status; treat as unknown rather than finished"
}

func optionalRef(v any) *string {
	s, ok := v.(string)
	if !ok || strings.TrimSpace(s) == "" {
		return nil
	}
	return ptr(s)
}

func ptr(s string) *string { return &s }

// StrList reads a JSON string array field without assuming the decoder's concrete type.
func StrList(v any) []string {
	out := []string{}
	switch a := v.(type) {
	case []any:
		for _, x := range a {
			if s, ok := x.(string); ok {
				out = append(out, s)
			}
		}
	case []string:
		out = append(out, a...)
	}
	return out
}
