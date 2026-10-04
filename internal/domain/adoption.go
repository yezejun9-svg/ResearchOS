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
	"context"
	"database/sql"
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
				// The card's third counter-example as a reader sees it: a completed reuse decision may not be presented
				// when the research stage never produced a row. A blocked network is recorded as RESEARCH_BLOCKED or
				// coverage PARTIAL, and neither entitles the projection to show a decision that skipped the reuse gate.
				if s := researchStatusName(byStage); s != StageCompleted && s != StagePartial {
					return nil, Fail(422, "GATE_FAILED", "REUSE_DECISION is presented as completed while RESEARCH is "+s)
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

// researchStatusName names the RESEARCH state the reader is looking at, keeping "no row was ever written" distinct
// from a row that exists and says NOT_STARTED, so a refusal states which of the two it refuses.
func researchStatusName(byStage map[string]Object) string {
	row, present := byStage[StageResearch]
	if !present {
		return "ABSENT"
	}
	if s := Str(row, "status"); s != "" {
		return s
	}
	return StageNotStarted
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

// ReuseJevGate is the J01 gate "judge before reusing": it reads a decision receipt produced by the existing Jev
// protocol and returns the score a reader may show, or refuses. A score is only ever returned for a signal whose
// jev_called is true, because "显示分数却未调用Jev" is one of this card's named counter-examples. A hard failure
// outranks any score, which is the 高分硬失败 case: the highest-scoring candidate is still refused.
//
// The fields read here are the ones the accepted decision writer actually stores (status, selected, signals with
// value/jev_called, deterministic_results, missing_evidence), so a receipt that was never written by that path cannot
// satisfy the gate by shape alone.
func ReuseJevGate(receipt Object) (float64, error) {
	if receipt == nil {
		return 0, Fail(422, "GATE_FAILED", "a reuse score requires a decision receipt; no Jev call was made")
	}
	for _, k := range []string{"status", "selected", "signals"} {
		if _, ok := receipt[k]; !ok {
			return 0, Fail(400, "INVALID_REQUEST", "decision receipt is missing "+k)
		}
	}
	if Str(receipt, "status") != "DECIDED" {
		return 0, Fail(422, "GATE_FAILED", "decision receipt is "+Str(receipt, "status")+"; only a DECIDED receipt may ground a reuse decision")
	}
	if strings.TrimSpace(Str(receipt, "selected")) == "" {
		return 0, Fail(422, "GATE_FAILED", "decision receipt measured no action, so there is no candidate to adopt")
	}
	// Hard failures are re-derived here rather than trusted from the receipt's own rationale string, so a receipt that
	// was hand-edited to say DECIDED still cannot pass a failing deterministic check.
	if len(Arr(receipt, "missing_evidence")) > 0 {
		return 0, Fail(422, "GATE_FAILED", "the reuse decision is missing evidence")
	}
	for _, v := range Arr(receipt, "deterministic_results") {
		check, ok := v.(map[string]any)
		if !ok {
			return 0, Fail(400, "INVALID_REQUEST", "deterministic_results must be objects")
		}
		if check["status"] != "PASS" && check["status"] != "NOT_APPLICABLE" {
			return 0, Fail(422, "GATE_FAILED", "a deterministic check failed, which no score can outweigh: "+Str(check, "check_id"))
		}
	}
	best := 0.0
	found := false
	for _, v := range Arr(receipt, "signals") {
		signal, ok := v.(map[string]any)
		if !ok {
			return 0, Fail(400, "INVALID_REQUEST", "signals must be objects")
		}
		called, _ := signal["jev_called"].(bool)
		value, isNum := signal["value"].(float64)
		// A value with no Jev call behind it is the fabricated-score case; it is refused even when other signals are
		// legitimate, because the reader would be showing a number that nothing produced.
		if !called && isNum {
			return 0, Fail(422, "GATE_FAILED", "a signal presents score "+fmt.Sprint(value)+" without jev_called")
		}
		if called && isNum && (!found || value > best) {
			best, found = value, true
		}
	}
	if !found {
		return 0, Fail(422, "GATE_FAILED", "no qualified candidate: the receipt carries no score produced by a Jev call")
	}
	return best, nil
}

// RecordReuseDecision is the only way a reuse decision becomes durable. mode is transport metadata (FIXTURE during
// construction, LIVE only against a qualified provider) and deliberately not part of the payload, because the frozen
// ReuseDecisionPayload forbids undeclared fields.
func (s *Service) RecordReuseDecision(ctx context.Context, token, project string, b Object, mode string) (Object, error) {
	if mode != "FIXTURE" && mode != "LIVE" {
		return nil, Fail(400, "INVALID_REQUEST", "measurement_mode for a reuse decision must be FIXTURE or LIVE")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	out, e := s.recordReuseDecision(ctx, tx, p, project, b, mode)
	if e != nil {
		return nil, e
	}
	return out, tx.Commit()
}

func (s *Service) recordReuseDecision(ctx context.Context, tx *sql.Tx, p Principal, project string, b Object, mode string) (Object, error) {
	decision, e := ValidateReuseDecision(b)
	if e != nil {
		return nil, e
	}
	if Str(b, "project_id") != project {
		return nil, Fail(403, "FORBIDDEN", "reuse decision is bound to a different project")
	}
	// Every cited artifact has to exist and be visible in this project. Without this a decision could name plausible
	// ids that point at nothing, which would let a completed stage rest on an invented basis.
	cited := append([]string{Str(b, "local_inventory_artifact_id")}, StrList(b["research_artifact_ids"])...)
	cited = append(cited, StrList(b["evidence_artifact_ids"])...)
	refs := []any{}
	for _, id := range cited {
		o, e := s.readObject(tx, p, project, "Artifact", id)
		if e != nil {
			return nil, e
		}
		refs = append(refs, Ref(o, "Artifact"))
	}
	ref := b["adoption_decision_ref"].(Object)
	if e := s.effective(tx, project, ref); e != nil {
		return nil, e
	}
	upload, e := s.upload(tx, p, project, Bytes(b))
	if e != nil {
		return nil, e
	}
	sealed, e := s.seal(tx, p, project, Object{"run_id": nil, "kind": "MANIFEST", "evidence_kind": "GENERATED",
		"measurement_mode": mode, "content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": upload["byte_size"],
		"input_refs": refs, "source_refs": Empty(), "produced_by": p.ID, "access_class": "PROJECT"})
	if e != nil {
		return nil, e
	}
	// Promotion writes the stage row and nothing else: a decision may not quietly mark research or implementation
	// finished, because each of those stages has its own evidence path.
	id := "stage-" + project + "-" + strings.ToLower(StageReuseDecision)
	rev, e := s.nextRevision(ctx, tx, project, KindBootstrapStage, id)
	if e != nil {
		return nil, e
	}
	stage := Object{"id": id, "project_id": project, "stage": StageReuseDecision, "status": StageCompleted,
		"inventory_artifact_ref": sealed["id"], "file_failures": Empty(), "observed_at": Now(), "revision": rev}
	if e := s.putOpaque(ctx, tx, project, KindBootstrapStage, id, stage); e != nil {
		return nil, e
	}
	return Object{"decision": decision, "adoption_artifact": Ref(sealed, "Artifact"), "stage": stage}, nil
}
