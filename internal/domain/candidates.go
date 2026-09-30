package domain

import (
	"context"
	"strings"
)

// ReviewResearchCandidate records a project-scoped disposition. Source origin
// counting comes from W09, so a repost or an unknown chain adds no support.
func (s *Service) ReviewResearchCandidate(ctx context.Context, token, project, cycleID, evidenceID, target, outcome, reason, missing, revisit string) (Object, error) {
	if !strings.Contains(" REJECT WATCH INCONCLUSIVE ADOPT ", " "+outcome+" ") || strings.TrimSpace(reason) == "" {
		return nil, Fail(400, "INVALID_REQUEST", "candidate outcome and reason required")
	}
	if (outcome == "WATCH" || outcome == "INCONCLUSIVE") && (strings.TrimSpace(missing) == "" || strings.TrimSpace(revisit) == "") {
		return nil, Fail(422, "GATE_FAILED", "watch and inconclusive results need a gap and revisit trigger")
	}
	// This existing W09 service verifies current reviewed roots. It never infers
	// independence from matching text or a caller-supplied independence_key.
	summary, err := s.EvidenceSupportSummary(ctx, token, project, []string{evidenceID})
	if err != nil {
		return nil, err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	p, err := authenticate(tx, token)
	if err != nil {
		return nil, err
	}
	if !(p.HasRole("OWNER") || p.HasRole("PLANNER") || p.HasRole("VERIFIER")) || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "project reviewer required")
	}
	cycle, err := load(tx, project, "ResearchCycle", cycleID)
	if err != nil {
		return nil, err
	}
	if cycle["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "cycle is closed")
	}
	found := false
	for _, id := range Arr(cycle, "candidate_evidence_ids") {
		if id == evidenceID {
			found = true
		}
	}
	if !found {
		return nil, Fail(422, "GATE_FAILED", "evidence is not a cycle candidate")
	}
	profile, err := version(tx, project, cycle["profile_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	current, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if current["revision"] != profile["revision"] {
		return nil, Fail(412, "STALE_INPUT", "project background changed")
	}
	matched := target != "" && target == profile["intent"]
	for _, field := range []string{"open_problem_ids", "accepted_scope", "constraints"} {
		for _, item := range Arr(profile, field) {
			if item == target {
				matched = true
			}
		}
	}
	if !matched {
		return nil, Fail(422, "GATE_FAILED", "candidate target is absent from frozen project context")
	}
	evidence, err := load(tx, project, "Evidence", evidenceID)
	if err != nil {
		return nil, err
	}
	if evidence["validity"] != "CURRENT" || evidence["evidence_kind"] != "OBSERVED" {
		return nil, Fail(422, "GATE_FAILED", "current observed candidate evidence required")
	}
	// Candidate references must be emitted by the existing W07 page adapter.
	var count int
	if err = tx.QueryRow("SELECT count(*) FROM source_pages WHERE project=? AND EXISTS (SELECT 1 FROM json_each(source_pages.item_refs_json) WHERE value=?)", project, evidenceID).Scan(&count); err != nil {
		return nil, err
	}
	if count == 0 {
		return nil, Fail(422, "GATE_FAILED", "candidate has no durable source page")
	}
	if outcome == "ADOPT" {
		if summary["independent_observed_count"] == 0 || len(Arr(cycle, "required_experiment_ids")) == 0 {
			return nil, Fail(422, "GATE_FAILED", "adoption recommendation needs reviewed source and required experiment")
		}
		for _, raw := range Arr(cycle, "required_experiment_ids") {
			experiment, e := load(tx, project, "Experiment", raw.(string))
			if e != nil {
				return nil, e
			}
			if experiment["cycle_id"] != cycleID || experiment["status"] != "COMPLETED" || experiment["outcome"] != "IMPROVED" || experiment["acceptance_id"] == nil {
				return nil, Fail(422, "GATE_FAILED", "adoption recommendation requires independently accepted improvement")
			}
			if _, e = s.experimentAcceptance(tx, project, experiment, Str(experiment, "acceptance_id")); e != nil {
				return nil, e
			}
		}
	}
	review := Object{"project_id": project, "cycle_id": cycleID, "evidence_id": evidenceID, "profile_revision": profile["revision"],
		"context_target": target, "outcome": outcome, "reason": reason, "missing_evidence": nil, "revisit_trigger": nil,
		"origin_summary": summary, "created_at": Now()}
	if missing != "" {
		review["missing_evidence"] = missing
	}
	if revisit != "" {
		review["revisit_trigger"] = revisit
	}
	_, err = tx.Exec("INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,missing_evidence,revisit_trigger,origin_summary_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
		project, cycleID, evidenceID, profile["revision"], target, outcome, reason, review["missing_evidence"], review["revisit_trigger"], string(Bytes(summary)), review["created_at"])
	if err != nil {
		return nil, err
	}
	return review, tx.Commit()
}
