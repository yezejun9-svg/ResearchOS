package domain

import (
	"database/sql"
	"errors"
)

func (s *Service) researchStageSnapshot(tx *sql.Tx, project string, task Object) (Object, error) {
	w, err := loadResearchWork(tx, project, Str(task, "id"))
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	meta, _, err := s.monitorSnapshot(tx, project, Str(task, "goal_id"), true)
	if err != nil {
		return nil, err
	}
	if Hash(w.PlanRef) != Hash(meta["brief_ref"]) || Hash(w.InputRefs) != Hash(task["input_refs"]) {
		return nil, Fail(412, "STALE_INPUT", "research work inputs changed")
	}
	cycle, err := load(tx, project, "ResearchCycle", w.Cycle)
	if err != nil {
		return nil, err
	}
	if cycle["status"] != "RUNNING" {
		return nil, Fail(409, "STATE_CONFLICT", "research cycle is no longer active")
	}
	var expected Object
	switch w.Stage {
	case "delivery":
		expected, err = s.researchCycleFacts(tx, project, cycle)
	case "discovery":
		if w.SourceReceipt == nil {
			return nil, Fail(422, "GATE_FAILED", "real source capture receipt required")
		}
		if w.SourceReceipt["run_id"] != task["active_run_id"] {
			return nil, Fail(422, "GATE_FAILED", "source receipt belongs to a different run")
		}
		intent, e := latestEffect(tx, project, Str(w.SourceReceipt, "run_id"), Str(w.SourceReceipt, "effect_key"))
		if e != nil || intent["state"] != "CONFIRMED" {
			return nil, Fail(422, "GATE_FAILED", "source effect has not been durably confirmed")
		}
		expected, err = s.researchSourceFacts(tx, project, w)
	case "verification":
		expected, err = s.researchSupportFacts(tx, project, w)
	case "review":
		expected, err = s.researchReviewFacts(tx, project, w)
	default:
		return Object{"work": w.publicParameters(), "unavailable": "typed stage verifier unavailable"}, nil
	}
	if err != nil {
		return nil, err
	}
	return Object{"work": w.publicParameters(), "expected": expected}, nil
}

func verifyResearchStage(snap Object, command string) (string, string) {
	meta, _ := snap["research"].(map[string]any)
	if meta == nil {
		return "FAIL", "private current research work binding required"
	}
	work, _ := meta["work"].(map[string]any)
	want := map[string]string{"discovery": "research.source-page-v1", "delivery": "research.cycle-report-v1", "verification": "research.source-support-v1", "review": "research.candidate-review-v1", "follow_up": "research.follow-up-v1"}[Str(work, "stage")]
	if want != command {
		return "FAIL", "research command differs from bound stage"
	}
	expected, _ := meta["expected"].(map[string]any)
	if expected == nil {
		return "NOT_RUN", "current research stage capability is unavailable"
	}
	artifacts := Arr(snap, "artifacts")
	if len(artifacts) != 1 {
		return "FAIL", "one exact structured stage output required"
	}
	entry := artifacts[0].(map[string]any)
	actual, err := Decode(entry["bytes"].([]byte))
	if err != nil || Hash(actual) != Hash(expected) {
		return "FAIL", "stage output differs from current independently recomputed evidence"
	}
	return "PASS", "Exact source, stage receipts, costs and unresolved gaps recomputed from current durable evidence; no business improvement inferred."
}

func (s *Service) researchCycleFacts(tx *sql.Tx, project string, cycle Object) (Object, error) {
	profile, err := version(tx, project, cycle["profile_ref"].(map[string]any))
	if err != nil {
		return nil, err
	}
	current, err := singleton(tx, project, "ProjectProfile")
	if err != nil {
		return nil, err
	}
	if Hash(Ref(current, "ProjectProfile")) != Hash(cycle["profile_ref"]) {
		return nil, Fail(412, "STALE_INPUT", "research profile changed")
	}
	from, to, err := parseCycleWindow(Str(cycle, "window_from"), Str(cycle, "window_to"))
	if err != nil {
		return nil, err
	}
	coverage, err := s.researchCoverage(tx, project, profile, from, to)
	if err != nil {
		return nil, err
	}
	complete, progress := true, false
	gaps, stages, candidates, experiments, costs := Empty(), Empty(), Empty(), Empty(), Empty()
	for _, raw := range coverage {
		source := raw.(map[string]any)
		if source["status"] == "COMPLETE" {
			progress = true
		}
		if source["required"] == true && source["status"] != "COMPLETE" {
			complete = false
			gaps = append(gaps, Object{"code": "SOURCE_WINDOW_INCOMPLETE", "source_id": source["source_id"], "reason": source["gap_reason"]})
		}
	}
	rows, err := tx.Query("SELECT task,stage,source_receipt FROM research_cycle_work WHERE project=? AND cycle=? AND stage!='delivery' ORDER BY logical_key", project, cycle["id"])
	if err != nil {
		return nil, err
	}
	type row struct {
		task, stage string
		receipt     sql.NullString
	}
	work := []row{}
	for rows.Next() {
		var r row
		if err = rows.Scan(&r.task, &r.stage, &r.receipt); err != nil {
			rows.Close()
			return nil, err
		}
		work = append(work, r)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	for _, r := range work {
		task, err := load(tx, project, "Task", r.task)
		if err != nil {
			return nil, err
		}
		stage := Object{"task_ref": Ref(task, "Task"), "stage": r.stage, "status": task["status"], "acceptance_ref": nil}
		receipt, gate := s.researchAcceptedTask(tx, project, task)
		if gate == nil {
			stage["acceptance_ref"] = Ref(receipt, "AcceptanceReceipt")
		} else {
			var fault *Fault
			if !errors.As(gate, &fault) {
				return nil, gate
			}
			complete = false
			gaps = append(gaps, Object{"code": "STAGE_NOT_ACCEPTED", "task_id": task["id"], "reason": gate.Error()})
		}
		if r.receipt.Valid {
			w, err := loadResearchWork(tx, project, r.task)
			if err != nil {
				return nil, err
			}
			if _, err = s.researchSourceFacts(tx, project, w); err == nil {
				progress = true
			}
		}
		stages = append(stages, stage)
	}
	for _, id := range Arr(cycle, "candidate_evidence_ids") {
		ev, err := load(tx, project, "Evidence", id.(string))
		if err != nil {
			return nil, err
		}
		candidate := Object{"evidence_ref": Ref(ev, "Evidence"), "review": nil}
		review, gate := s.currentResearchReview(tx, project, Str(cycle, "id"), id.(string))
		if gate != nil {
			complete = false
			gaps = append(gaps, Object{"code": "CANDIDATE_REVIEW_REQUIRED", "evidence_id": id, "reason": "Current independent source review and disposition required"})
		} else {
			candidate["review"] = review
		}
		// The typed review binding is revalidated before it can populate this field.
		candidates = append(candidates, candidate)
	}
	for _, id := range Arr(cycle, "required_experiment_ids") {
		x, err := load(tx, project, "Experiment", id.(string))
		if err != nil {
			return nil, err
		}
		item := Object{"experiment_ref": Ref(x, "Experiment"), "status": x["status"], "outcome": x["outcome"], "acceptance_ref": nil}
		receipt, gate := s.experimentAcceptance(tx, project, x, Str(x, "acceptance_id"))
		if x["status"] == "COMPLETED" && gate == nil {
			progress = true
			item["acceptance_ref"] = Ref(receipt, "AcceptanceReceipt")
		} else {
			complete = false
			gaps = append(gaps, Object{"code": "EXPERIMENT_ACCEPTANCE_REQUIRED", "experiment_id": id, "reason": "Preregistered required experiment lacks current independent completion"})
		}
		experiments = append(experiments, item)
	}
	rows, err = tx.Query("SELECT l.body FROM domain_objects l JOIN domain_objects r ON r.project=l.project AND r.kind='Run' AND r.id=json_extract(l.body,'$.run_id') WHERE l.project=? AND l.kind='BudgetLedgerEntry' AND EXISTS(SELECT 1 FROM research_cycle_work w WHERE w.project=r.project AND w.cycle=? AND w.task=json_extract(r.body,'$.task_id') AND w.stage!='delivery') ORDER BY l.id", project, cycle["id"])
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return nil, err
		}
		cost, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		costs = append(costs, cost)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return nil, err
	}
	outcome := "COMPLETE"
	if !complete {
		outcome = "PARTIAL"
		if !progress {
			outcome = "BLOCKED"
		}
	}
	return Object{"type": "research.cycle-report.v1", "cycle_id": cycle["id"], "window_from": cycle["window_from"], "window_to": cycle["window_to"], "profile_ref": cycle["profile_ref"], "source_coverage": coverage, "stage_work": stages, "candidates": candidates, "experiments": experiments, "cost_entries": costs, "gaps": gaps, "cycle_outcome": outcome}, nil
}

func (s *Service) researchSourceFacts(tx *sql.Tx, project string, w *researchWork) (Object, error) {
	r := w.SourceReceipt
	if r == nil || r["project_id"] != project || r["task_id"] != w.Task {
		return nil, Fail(422, "GATE_FAILED", "bound source receipt unavailable")
	}
	run, err := load(tx, project, "Run", Str(r, "run_id"))
	if err != nil || run["task_id"] != w.Task {
		return nil, Fail(422, "GATE_FAILED", "source run binding unavailable")
	}
	intent, err := latestEffect(tx, project, Str(r, "run_id"), Str(r, "effect_key"))
	if err != nil || intent["request_hash"] != r["request_hash"] || intent["reservation_id"] != r["reservation_id"] || Hash(intent["epoch"]) != Hash(r["epoch"]) {
		return nil, Fail(422, "GATE_FAILED", "source receipt effect identity differs")
	}
	reservation, err := load(tx, project, "BudgetLedgerEntry", Str(r, "reservation_id"))
	if err != nil || reservation["run_id"] != r["run_id"] || reservation["provider_request_id"] != r["effect_key"] {
		return nil, Fail(422, "GATE_FAILED", "source receipt reservation differs")
	}
	for _, key := range []string{"cursor_before_ref", "cursor_after_ref"} {
		ref, ok := r[key].(map[string]any)
		if !ok || ref["entity_type"] != "SourceCursor" || ref["id"] != w.Parameters["cursor_id"] {
			return nil, Fail(422, "GATE_FAILED", "source receipt cursor binding differs")
		}
		cursor, e := version(tx, project, ref)
		if e != nil || cursor["source_id"] != w.SourceID || cursor["query_hash"] != w.Parameters["query_hash"] {
			return nil, Fail(422, "GATE_FAILED", "historical source cursor invalid")
		}
	}
	manifestRef, ok := r["manifest_ref"].(map[string]any)
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "source manifest required")
	}
	if err := s.effective(tx, project, manifestRef); err != nil {
		return nil, err
	}
	value, err := s.artifactJSON(tx, project, manifestRef)
	if err != nil {
		return nil, err
	}
	manifest, ok := value.(map[string]any)
	if !ok {
		return nil, Fail(422, "GATE_FAILED", "source manifest invalid")
	}
	for _, key := range []string{"source_id", "query_hash", "window_from", "window_to", "page_cursor_in"} {
		if manifest[key] != w.Parameters[key] {
			return nil, Fail(422, "GATE_FAILED", "source manifest differs from exact page work")
		}
	}
	return Object{"type": "research.source-page.v1", "cycle_id": w.Cycle, "logical_key": w.Key, "manifest_ref": manifestRef, "cursor_before_ref": r["cursor_before_ref"], "cursor_after_ref": r["cursor_after_ref"], "effect_key": r["effect_key"], "page_complete": manifest["complete"], "actual_cost": r["actual_cost"], "cost_basis": r["cost_basis"], "capture_environment": r["capture_environment"]}, nil
}
