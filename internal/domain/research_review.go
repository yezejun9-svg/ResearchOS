package domain

import "database/sql"

func (s *Service) currentResearchReview(tx *sql.Tx, project, cycle, evidence string) (Object, error) {
	var taskRaw, receiptRaw, reviewer, supportRaw, outcome, target, reason, missing, revisit string
	err := tx.QueryRow("SELECT review_task_ref,acceptance_ref,reviewer_id,origin_summary_json,outcome,context_target,reason,coalesce(missing_evidence,''),coalesce(revisit_trigger,'') FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND evidence_id=? AND reviewer_id IS NOT NULL AND review_task_ref IS NOT NULL AND acceptance_ref IS NOT NULL", project, cycle, evidence).Scan(&taskRaw, &receiptRaw, &reviewer, &supportRaw, &outcome, &target, &reason, &missing, &revisit)
	if err != nil {
		return nil, err
	}
	taskRef, err := Decode([]byte(taskRaw))
	if err != nil {
		return nil, err
	}
	task, err := load(tx, project, "Task", Str(taskRef, "id"))
	if err != nil {
		return nil, err
	}
	if Hash(Ref(task, "Task")) != Hash(taskRef) {
		return nil, Fail(412, "STALE_INPUT", "review task changed")
	}
	receipt, err := s.researchAcceptedTask(tx, project, task)
	if err != nil {
		return nil, err
	}
	if string(Bytes(Ref(receipt, "AcceptanceReceipt"))) != receiptRaw || receipt["verifier_principal_id"] != reviewer {
		return nil, Fail(422, "GATE_FAILED", "review acceptance identity changed")
	}
	w, err := loadResearchWork(tx, project, Str(task, "id"))
	if err != nil {
		return nil, err
	}
	if w.Stage != "review" || w.Cycle != cycle || w.EvidenceID != evidence {
		return nil, Fail(422, "GATE_FAILED", "review work binding differs")
	}
	facts, err := s.researchReviewFacts(tx, project, w)
	if err != nil {
		return nil, err
	}
	if string(Bytes(facts["support"])) != supportRaw || facts["outcome"] != outcome || facts["context_target"] != target || facts["reason"] != reason || facts["missing_evidence"] != missing || facts["revisit_trigger"] != revisit {
		return nil, Fail(412, "STALE_INPUT", "review facts are no longer current")
	}
	return Merge(facts, Object{"acceptance_ref": Ref(receipt, "AcceptanceReceipt")}), nil
}

// This stage checks captured bytes and reviewed origin support. It does not
// change Evidence.verification_status or convert unreviewed origin into truth.
func (s *Service) researchSupportFacts(tx *sql.Tx, project string, w *researchWork) (Object, error) {
	ev, err := load(tx, project, "Evidence", w.EvidenceID)
	if err != nil {
		return nil, err
	}
	if ev["validity"] != "CURRENT" {
		return nil, Fail(412, "STALE_INPUT", "research evidence changed")
	}
	ref, ok := ev["snapshot_artifact_ref"].(map[string]any)
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "sealed source snapshot required")
	}
	if err = s.effective(tx, project, ref); err != nil {
		return nil, err
	}
	snapshot, err := version(tx, project, ref)
	if err != nil {
		return nil, err
	}
	if err = s.requireCurrentArtifactBody(tx, project, snapshot); err != nil {
		return nil, err
	}
	sourceTask, err := researchCandidateSourceTask(tx, project, w)
	if err != nil {
		return nil, err
	}
	source, err := load(tx, project, "Task", sourceTask)
	if err != nil {
		return nil, err
	}
	receipt, err := s.researchAcceptedTask(tx, project, source)
	if err != nil {
		return nil, err
	}
	meta, _, err := s.monitorSnapshot(tx, project, Str(source, "goal_id"), true)
	if err != nil {
		return nil, err
	}
	owner := meta["owner_principal"].(Principal)
	origin, root := "UNKNOWN", ""
	if ev["evidence_kind"] == "OBSERVED" && ev["stance"] == "SUPPORT" && s.evidenceBodyCurrent(tx, owner, project, ev) {
		if id, e := s.originRoot(tx, owner, project, w.EvidenceID); e == nil {
			r, e := load(tx, project, "Evidence", id)
			if e == nil && r["validity"] == "CURRENT" && s.evidenceBodyCurrent(tx, owner, project, r) {
				origin, root = "CONFIRMED", id
			}
		}
	}
	count := 0
	roots := Empty()
	if root != "" {
		count = 1
		roots = append(roots, root)
	}
	return Object{"type": "research.source-support.v1", "cycle_id": w.Cycle, "evidence_ref": Ref(ev, "Evidence"), "snapshot_ref": ref, "source_acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "origin_relation": origin, "independent_root_ids": roots, "independent_observed_count": count, "verification_status": ev["verification_status"], "assessment": "Sealed snapshot integrity and current reviewed origin only; source claim truth and project improvement are not inferred."}, nil
}

func (s *Service) researchReviewFacts(tx *sql.Tx, project string, w *researchWork) (Object, error) {
	support, err := s.researchSupportFacts(tx, project, w)
	if err != nil {
		return nil, err
	}
	var verificationID string
	if err = tx.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND stage='verification' AND evidence_id=?", project, w.Cycle, w.EvidenceID).Scan(&verificationID); err != nil {
		return nil, err
	}
	verification, err := load(tx, project, "Task", verificationID)
	if err != nil {
		return nil, err
	}
	receipt, err := s.researchAcceptedTask(tx, project, verification)
	if err != nil {
		return nil, err
	}
	cycle, err := load(tx, project, "ResearchCycle", w.Cycle)
	if err != nil {
		return nil, err
	}
	profile, err := version(tx, project, cycle["profile_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	return Object{"type": "research.candidate-review.v1", "cycle_id": w.Cycle, "evidence_ref": support["evidence_ref"], "profile_ref": cycle["profile_ref"], "context_target": profile["intent"], "support": support, "verification_acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "outcome": "INCONCLUSIVE", "reason": "Captured source and support were inspected; no independently accepted project improvement is established.", "missing_evidence": "A preregistered project-specific comparison and current independent assessment are required before recommending adoption.", "revisit_trigger": "New current independent evidence or an accepted required experiment result."}, nil
}

func (s *Service) sealResearchReview(tx *sql.Tx, project string, w *researchWork, task Object) error {
	receipt, err := s.researchAcceptedTask(tx, project, task)
	if err != nil {
		return err
	}
	facts, err := s.researchReviewFacts(tx, project, w)
	if err != nil {
		return err
	}
	var raw string
	err = tx.QueryRow("SELECT acceptance_ref FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND evidence_id=?", project, w.Cycle, w.EvidenceID).Scan(&raw)
	if err == nil {
		if raw != string(Bytes(Ref(receipt, "AcceptanceReceipt"))) {
			return Fail(409, "STATE_CONFLICT", "candidate review already bound differently")
		}
		return nil
	}
	if err != sql.ErrNoRows {
		return err
	}
	profileRef := facts["profile_ref"].(map[string]any)
	_, err = tx.Exec("INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,missing_evidence,revisit_trigger,origin_summary_json,created_at,reviewer_id,review_task_ref,acceptance_ref) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", project, w.Cycle, w.EvidenceID, profileRef["revision"], facts["context_target"], facts["outcome"], facts["reason"], facts["missing_evidence"], facts["revisit_trigger"], string(Bytes(facts["support"])), Now(), receipt["verifier_principal_id"], string(Bytes(Ref(task, "Task"))), string(Bytes(Ref(receipt, "AcceptanceReceipt"))))
	return err
}

func (s *Service) advanceResearchCandidates(tx *sql.Tx, owner Principal, project string, meta Object, plan *MonitorPlan, cycle Object) (bool, error) {
	ready := true
	for _, raw := range Arr(cycle, "candidate_evidence_ids") {
		id := raw.(string)
		ev, err := load(tx, project, "Evidence", id)
		if err != nil {
			return false, err
		}
		params := Object{"evidence_id": id}
		key := stringsDigest(Hash([]any{"verification", meta["brief_ref"], Ref(ev, "Evidence")}))
		sourceTask, err := researchCandidateSourceTask(tx, project, &researchWork{Cycle: Str(cycle, "id"), EvidenceID: id})
		if err != nil {
			return false, err
		}
		verification, err := s.materializeResearchWork(tx, owner, project, meta, plan, cycle, "verification", key, params, []any{sourceTask}, []any{Ref(ev, "Evidence"), ev["snapshot_artifact_ref"]})
		if err != nil {
			return false, err
		}
		if verification["status"] != "ACCEPTED" {
			if verification["status"] != "BLOCKED" && verification["status"] != "FAILED" && verification["status"] != "DEFERRED_NO_PROGRESS" {
				ready = false
			}
			continue
		}
		if _, err = s.researchAcceptedTask(tx, project, verification); err != nil {
			return false, err
		}
		key = stringsDigest(Hash([]any{"review", meta["brief_ref"], Ref(ev, "Evidence")}))
		review, err := s.materializeResearchWork(tx, owner, project, meta, plan, cycle, "review", key, params, []any{verification["id"]}, []any{Ref(ev, "Evidence"), ev["snapshot_artifact_ref"]})
		if err != nil {
			return false, err
		}
		if review["status"] == "ACCEPTED" {
			w, err := loadResearchWork(tx, project, Str(review, "id"))
			if err != nil {
				return false, err
			}
			if err = s.sealResearchReview(tx, project, w, review); err != nil {
				return false, err
			}
		} else if review["status"] != "BLOCKED" && review["status"] != "FAILED" && review["status"] != "DEFERRED_NO_PROGRESS" {
			ready = false
		}
	}
	return ready, nil
}

func researchCandidateSourceTask(tx *sql.Tx, project string, w *researchWork) (string, error) {
	var err error
	var sourceTask string
	if err = tx.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND stage='discovery' AND source_receipt IS NOT NULL AND EXISTS(SELECT 1 FROM domain_objects a JOIN uploaded_content u ON u.project=a.project AND u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.project=research_cycle_work.project AND a.kind='Artifact' AND a.id=json_extract(research_cycle_work.source_receipt,'$.manifest_ref.id') AND EXISTS(SELECT 1 FROM json_each(CAST(u.bytes AS TEXT),'$.evidence_refs') WHERE json_extract(value,'$.id')=?)) ORDER BY created_at LIMIT 1", project, w.Cycle, w.EvidenceID).Scan(&sourceTask); err != nil {
		return "", Fail(422, "GATE_FAILED", "candidate lacks this cycle's bound source capture")
	}
	return sourceTask, nil
}
