package domain

import (
	"context"
	"database/sql"
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
	profile, summary, err := s.validateResearchCandidateReview(tx, p, project, cycle, evidenceID, target, outcome, reason, missing, revisit)
	if err != nil {
		return nil, err
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

// Shared write/close validation. The authenticated caller and all source reads
// belong to the same transaction; this does not create independent review.
func (s *Service) validateResearchCandidateReview(tx *sql.Tx, p Principal, project string, cycle Object, evidenceID, target, outcome, reason, missing, revisit string) (Object, Object, error) {
	if !strings.Contains(" REJECT WATCH INCONCLUSIVE ADOPT ", " "+outcome+" ") || strings.TrimSpace(reason) == "" {
		return nil, nil, Fail(400, "INVALID_REQUEST", "candidate outcome and reason required")
	}
	if (outcome == "WATCH" || outcome == "INCONCLUSIVE") && (strings.TrimSpace(missing) == "" || strings.TrimSpace(revisit) == "") {
		return nil, nil, Fail(422, "GATE_FAILED", "watch and inconclusive results need a gap and revisit trigger")
	}
	found := false
	for _, id := range Arr(cycle, "candidate_evidence_ids") {
		if id == evidenceID {
			found = true
		}
	}
	if !found {
		return nil, nil, Fail(422, "GATE_FAILED", "evidence is not a cycle candidate")
	}
	profile, err := version(tx, project, cycle["profile_ref"].(map[string]any))
	if err != nil {
		return nil, nil, err
	}
	current, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, nil, err
	}
	if Hash(Ref(current, "ProjectProfile")) != Hash(cycle["profile_ref"]) {
		return nil, nil, Fail(412, "STALE_INPUT", "project background changed")
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
		return nil, nil, Fail(422, "GATE_FAILED", "candidate target is absent from frozen project context")
	}
	evidence, err := s.readObject(tx, p, project, "Evidence", evidenceID)
	if err != nil {
		return nil, nil, err
	}
	if evidence["validity"] != "CURRENT" || evidence["evidence_kind"] != "OBSERVED" {
		return nil, nil, Fail(422, "GATE_FAILED", "current observed candidate evidence required")
	}
	// Candidate references must be emitted by the existing W07 page adapter.
	var count int
	if err = tx.QueryRow("SELECT count(*) FROM source_pages WHERE project=? AND EXISTS (SELECT 1 FROM json_each(source_pages.item_refs_json) WHERE value=?)", project, evidenceID).Scan(&count); err != nil {
		return nil, nil, err
	}
	if count == 0 {
		return nil, nil, Fail(422, "GATE_FAILED", "candidate has no durable source page")
	}
	ref, ok := evidence["snapshot_artifact_ref"].(map[string]any)
	if !ok || ref["entity_type"] != "Artifact" {
		return nil, nil, Fail(422, "GATE_FAILED", "candidate source snapshot required")
	}
	if err = s.effective(tx, project, ref); err != nil {
		return nil, nil, err
	}
	snapshot, err := s.readObject(tx, p, project, "Artifact", Str(ref, "id"))
	if err != nil {
		return nil, nil, err
	}
	var body []byte
	if err = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, snapshot["storage_key"]).Scan(&body); err != nil {
		return nil, nil, err
	}
	size, sizeErr := Num(snapshot, "byte_size")
	if sizeErr != nil || size != int64(len(body)) || Digest(body) != snapshot["content_hash"] {
		return nil, nil, Fail(422, "CONTENT_HASH_MISMATCH", "candidate source snapshot bytes differ from seal")
	}
	// W09 support is recomputed from current source permissions and origin roots;
	// the persisted annotation's origin_summary is not current authority.
	summary, err := s.evidenceSupportSummary(tx, p, project, []string{evidenceID})
	if err != nil {
		return nil, nil, err
	}
	if outcome == "ADOPT" {
		if summary["independent_observed_count"] == 0 || len(Arr(cycle, "required_experiment_ids")) == 0 {
			return nil, nil, Fail(422, "GATE_FAILED", "adoption recommendation needs reviewed source and required experiment")
		}
		for _, raw := range Arr(cycle, "required_experiment_ids") {
			experiment, e := load(tx, project, "Experiment", raw.(string))
			if e != nil {
				return nil, nil, e
			}
			if experiment["cycle_id"] != cycle["id"] || experiment["status"] != "COMPLETED" || experiment["outcome"] != "IMPROVED" || experiment["acceptance_id"] == nil {
				return nil, nil, Fail(422, "GATE_FAILED", "adoption recommendation requires independently accepted improvement")
			}
			if _, e = s.experimentAcceptance(tx, project, experiment, Str(experiment, "acceptance_id")); e != nil {
				return nil, nil, e
			}
		}
	}
	return profile, summary, nil
}

func (s *Service) currentManualResearchReview(tx *sql.Tx, p Principal, project string, cycle Object, evidenceID string) (Object, error) {
	var revision int64
	var target, outcome, reason, missing, revisit, created string
	err := tx.QueryRow("SELECT profile_revision,context_target,outcome,reason,coalesce(missing_evidence,''),coalesce(revisit_trigger,''),created_at FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND evidence_id=? AND reviewer_id IS NULL AND review_task_ref IS NULL AND acceptance_ref IS NULL", project, cycle["id"], evidenceID).Scan(&revision, &target, &outcome, &reason, &missing, &revisit, &created)
	if err != nil {
		return nil, err
	}
	if outcome != "REJECT" && outcome != "WATCH" && outcome != "INCONCLUSIVE" {
		return nil, Fail(422, "GATE_FAILED", "only negative manual dispositions can be revalidated")
	}
	profile, summary, err := s.validateResearchCandidateReview(tx, p, project, cycle, evidenceID, target, outcome, reason, missing, revisit)
	if err != nil {
		return nil, err
	}
	currentRevision, err := Num(profile, "revision")
	if err != nil || revision != currentRevision {
		return nil, Fail(412, "STALE_INPUT", "manual disposition profile changed")
	}
	return Object{"status": "MANUAL_REVALIDATED", "project_id": project, "cycle_id": cycle["id"], "evidence_id": evidenceID,
		"profile_revision": revision, "context_target": target, "outcome": outcome, "reason": reason,
		"missing_evidence": missing, "revisit_trigger": revisit, "origin_summary": summary, "created_at": created,
		"acceptance_ref": nil, "independent_review": false, "authority": false}, nil
}
