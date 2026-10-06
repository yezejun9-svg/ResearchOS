package domain

import "database/sql"

func init() { implemented["advanceNoProgress"] = true; resourceOperations["advanceNoProgress"] = true }

func (s *Service) advanceNoProgress(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	n, e := load(tx, project, "NoProgressRecord", id)
	if e != nil {
		return nil, e
	}
	run, e := load(tx, project, "Run", Str(b, "run_id"))
	if e != nil {
		return nil, e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	if task["no_progress_record_id"] != id || task["active_run_id"] != run["id"] || !runTerminal(run) {
		return nil, Fail(409, "STATE_CONFLICT", "completed matching iteration required")
	}
	if len(Arr(b, "new_evidence_refs")) > 0 {
		if Str(b, "resume_reason") == "" {
			return nil, Fail(422, "GATE_FAILED", "new evidence requires explicit resume reason")
		}
		inputs := map[string]bool{}
		for _, v := range Arr(run, "input_refs") {
			inputs[Hash(v)] = true
		}
		for _, v := range Arr(b, "new_evidence_refs") {
			ref := v.(map[string]any)
			if inputs[Hash(ref)] {
				return nil, Fail(422, "GATE_FAILED", "existing inputs cannot reset progress")
			}
			if e = s.effective(tx, project, ref); e != nil {
				return nil, e
			}
		}
		// Keep the old origin counter permanently. New versioned input creates its
		// own key through W06 progressForInputs/createTask, with this reason retained.
		record := Merge(Merge(Object{}, b), Object{"actor": p.ID, "at": Now(), "prior_counts": Object{"same_failure_count": n["same_failure_count"], "no_progress_iterations": n["no_progress_iterations"]}})
		if _, e = tx.Exec("INSERT INTO resource_progress_resumes(id,project,record,body) VALUES(?,?,?,?)", ID(), project, id, string(Bytes(record))); e != nil {
			return nil, e
		}
		if e = s.refreshRetainedProgress(tx, project, n); e != nil {
			return nil, e
		}
		n["resume_conditions"] = mergeUnique(Arr(n, "resume_conditions"), []any{"New input version required: " + Str(b, "resume_reason")})
		if e = bump(n); e != nil {
			return nil, e
		}
		return n, s.put(tx, "NoProgressRecord", n)
	}
	if len(Arr(b, "metric_results")) > 0 {
		return nil, Fail(422, "GATE_FAILED", "metric progress requires independently verified experiment results")
	}
	var counted int
	if e = tx.QueryRow("SELECT count(*) FROM resource_progress_runs WHERE project=? AND run=?", project, run["id"]).Scan(&counted); e != nil {
		return nil, e
	}
	if counted != 0 {
		return n, nil
	}
	reason := Str(b, "failure_signature")
	if reason == "" {
		reason = "complete iteration produced no new effective evidence"
	}
	if e = s.taskFailed(tx, project, task, reason); e != nil {
		return nil, e
	}
	if e = bump(task); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Task", task); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED"); e != nil {
		return nil, e
	}
	return load(tx, project, "NoProgressRecord", id)
}
