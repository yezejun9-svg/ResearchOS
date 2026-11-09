package domain

import "database/sql"

func (s *Service) advanceResearchExperiments(tx *sql.Tx, owner Principal, project string, meta Object, plan *MonitorPlan, cycle Object) (bool, error) {
	ready := true
	for _, templateRef := range plan.RequiredExperimentRefs {
		key := stringsDigest(Hash([]any{"experiment", meta["brief_ref"], templateRef}))
		var taskID string
		err := tx.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND logical_key=?", project, cycle["id"], key).Scan(&taskID)
		var task, x Object
		if err == sql.ErrNoRows {
			capacity, e := researchStageCapacity(tx, project, Str(cycle, "id"), plan)
			if e != nil {
				return false, e
			}
			if !capacity {
				continue
			}
			template, err := version(tx, project, templateRef)
			if err != nil {
				return false, err
			}
			if template["status"] != "REGISTERED" {
				return false, Fail(422, "GATE_FAILED", "approved experiment template is no longer registered")
			}
			if err = s.experimentCurrent(tx, project, template); err != nil {
				return false, err
			}
			body := experimentPlan(template)
			body["cycle_id"] = cycle["id"]
			x, err = s.createExperiment(tx, project, body)
			if err != nil {
				return false, err
			}
			x, err = s.registerExperiment(tx, project, Str(x, "id"), Object{"expected_preregistration_hash": x["preregistration_hash"]})
			if err != nil {
				return false, err
			}
			inputs := mergeUnique([]any{x["candidate_ref"]}, mergeUnique(Arr(x, "baseline_refs"), Arr(x, "input_refs")))
			task, err = s.materializeResearchWork(tx, owner, project, meta, plan, cycle, "experiment", key, Object{"experiment_id": x["id"], "template_ref": templateRef, "preregistration_hash": x["preregistration_hash"]}, Empty(), inputs)
			if err != nil {
				return false, err
			}
			if err = experimentTaskInputs(x, task); err != nil {
				return false, err
			}
			if _, err = tx.Exec("INSERT INTO experiment_tasks(project,experiment,task,bound_at) VALUES(?,?,?,?)", project, x["id"], task["id"], Now()); err != nil {
				return false, err
			}
			cycle, err = s.checkpointResearchCycle(tx, project, Str(cycle, "id"), Object{"candidate_evidence_ids": cycle["candidate_evidence_ids"], "required_experiment_ids": mergeUnique(Arr(cycle, "required_experiment_ids"), []any{x["id"]}), "decision_ids": cycle["decision_ids"], "follow_up_task_ids": cycle["follow_up_task_ids"], "checkpoint_artifact_id": cycle["checkpoint_artifact_id"]})
			if err != nil {
				return false, err
			}
		} else if err != nil {
			return false, err
		} else {
			task, err = load(tx, project, "Task", taskID)
			if err != nil {
				return false, err
			}
			w, err := loadResearchWork(tx, project, taskID)
			if err != nil {
				return false, err
			}
			x, err = load(tx, project, "Experiment", w.Experiment)
			if err != nil {
				return false, err
			}
		}
		if task["status"] == "ACCEPTED" && x["status"] == "RUNNING" {
			receipt, err := s.researchAcceptedTask(tx, project, task)
			if err != nil {
				return false, err
			}
			var raw string
			if err = tx.QueryRow("SELECT body FROM experiment_executions WHERE project=? AND experiment=? AND run=? AND state='RECORDED'", project, x["id"], task["active_run_id"]).Scan(&raw); err != nil {
				return false, err
			}
			execution, err := Decode([]byte(raw))
			if err != nil {
				return false, err
			}
			observed := execution["observation"].(map[string]any)
			x, err = s.recordExperimentResult(tx, project, Str(x, "id"), Object{"run_ids": x["run_ids"], "acceptance_id": receipt["id"], "results": observed["results"], "outcome": observed["outcome"]})
			if err != nil {
				return false, err
			}
			if err = s.event(tx, project, "Experiment", x, owner.ID, ID(), "PROJECT_UPDATED"); err != nil {
				return false, err
			}
		} else if task["status"] != "ACCEPTED" && task["status"] != "BLOCKED" && task["status"] != "FAILED" && task["status"] != "DEFERRED_NO_PROGRESS" {
			ready = false
		}
	}
	return ready, nil
}
