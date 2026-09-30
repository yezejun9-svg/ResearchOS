package domain

import "database/sql"

func researchCycleSettled(tx *sql.Tx, project, cycle string) error {
	rows, err := tx.Query("SELECT r.body FROM domain_objects r JOIN research_cycle_work w ON w.project=r.project AND w.task=json_extract(r.body,'$.task_id') WHERE r.project=? AND r.kind='Run' AND w.cycle=?", project, cycle)
	if err != nil {
		return err
	}
	runs := []Object{}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return err
		}
		run, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return e
		}
		runs = append(runs, run)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, run := range runs {
		if !runTerminal(run) {
			return Fail(409, "STATE_CONFLICT", "cycle has an unsettled run")
		}
		if err = effectsReconciled(tx, project, Str(run, "id")); err != nil {
			return err
		}
	}
	return nil
}

func (s *Service) closeReportedResearchCycle(tx *sql.Tx, owner Principal, project string, meta, cycle, task Object) error {
	receipt, err := s.researchAcceptedTask(tx, project, task)
	if err != nil {
		return err
	}
	facts, err := s.researchCycleFacts(tx, project, cycle)
	if err != nil {
		return err
	}
	outputs := Arr(task, "output_artifact_ids")
	if len(outputs) != 1 {
		return Fail(422, "GATE_FAILED", "one accepted cycle report required")
	}
	artifact, err := load(tx, project, "Artifact", outputs[0].(string))
	if err != nil {
		return err
	}
	actual, err := s.artifactJSON(tx, project, Ref(artifact, "Artifact"))
	if err != nil {
		return err
	}
	if Hash(actual) != Hash(facts) {
		return Fail(412, "STALE_INPUT", "accepted report differs from current cycle evidence")
	}
	b := Object{"candidate_evidence_ids": cycle["candidate_evidence_ids"], "required_experiment_ids": cycle["required_experiment_ids"], "decision_ids": cycle["decision_ids"], "follow_up_task_ids": cycle["follow_up_task_ids"], "checkpoint_artifact_id": artifact["id"]}
	cycle, err = s.checkpointResearchCycle(tx, project, Str(cycle, "id"), b)
	if err != nil {
		return err
	}
	cycle, err = s.closeResearchCycle(tx, project, Str(cycle, "id"), Object{"requested_status": facts["cycle_outcome"], "outcome_summary": "Current independently accepted cycle report " + Str(artifact, "id") + "; gaps and unknown cost retained."})
	if err != nil {
		return err
	}
	if err = s.recordResearchIteration(tx, project, meta, task, receipt, facts); err != nil {
		return err
	}
	return s.event(tx, project, "ResearchCycle", cycle, owner.ID, ID(), "PROJECT_UPDATED")
}

// Report acceptance is preserved when an iteration discovers no new qualified
// evidence. One stable monitor record counts each original report Run once.
func (s *Service) recordResearchIteration(tx *sql.Tx, project string, meta, task, receipt, facts Object) error {
	var counted int
	if err := tx.QueryRow("SELECT count(*) FROM resource_progress_runs WHERE project=? AND run=?", project, task["active_run_id"]).Scan(&counted); err != nil {
		return err
	}
	if counted != 0 {
		return nil
	}
	n, err := load(tx, project, "NoProgressRecord", Str(meta, "progress_record_id"))
	if err != nil {
		return err
	}
	// Discovery count is not research improvement. Stage reviews/experiments must
	// supply independently current new evidence before a later iteration resumes.
	if _, err = tx.Exec("INSERT INTO resource_progress_runs(project,run,record,body) VALUES(?,?,?,?)", project, task["active_run_id"], n["id"], string(Bytes(Object{"cycle_id": facts["cycle_id"], "report_acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "cycle_outcome": facts["cycle_outcome"], "at": Now()}))); err != nil {
		return err
	}
	iterations, _ := Num(n, "no_progress_iterations")
	iterations++
	n["no_progress_iterations"] = iterations
	policy, err := s.effectiveRetryPolicy(tx, project)
	if err != nil {
		return err
	}
	limit, _ := Num(policy, "no_progress_iteration_limit")
	if iterations >= limit {
		n["status"] = "DEFERRED_NO_PROGRESS"
	}
	if err = bump(n); err != nil {
		return err
	}
	return s.put(tx, "NoProgressRecord", n)
}
