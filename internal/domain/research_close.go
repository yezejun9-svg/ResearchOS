package domain

import (
	"database/sql"
	"sort"
)

func (s *Service) researchExperimentProgressKey(tx *sql.Tx, project string, x Object) (string, error) {
	roles := []any{}
	for _, refs := range [][]any{{x["candidate_ref"]}, Arr(x, "baseline_refs"), Arr(x, "input_refs")} {
		hashes := []string{}
		for _, raw := range refs {
			ref := raw.(map[string]any)
			if err := s.effective(tx, project, ref); err != nil {
				return "", err
			}
			// Executable pairs use sealed artifacts. Unsupported domain-object semantics
			// cannot establish new progress merely by acquiring another ID or revision.
			if ref["entity_type"] != "Artifact" {
				return "", nil
			}
			artifact, err := version(tx, project, ref)
			if err != nil {
				return "", err
			}
			hashes = append(hashes, Str(artifact, "content_hash"))
		}
		sort.Strings(hashes)
		roles = append(roles, hashes)
	}
	// Hypothesis prose, sample values and all run/cycle/object IDs are deliberately
	// absent: a repeated improvement of identical content is still the same gain.
	return Hash([]any{"accepted-improvement", roles, x["metrics"], x["measurement_mode"]}), nil
}

func (s *Service) researchProgressKeys(tx *sql.Tx, project string, facts Object) ([]any, error) {
	keys := Empty()
	for _, raw := range Arr(facts, "candidates") {
		candidate := raw.(map[string]any)
		review, _ := candidate["review"].(map[string]any)
		if review == nil {
			continue
		}
		support, _ := review["support"].(map[string]any)
		if support == nil || support["origin_relation"] != "CONFIRMED" {
			continue
		}
		for _, rootID := range Arr(support, "independent_root_ids") {
			root, err := load(tx, project, "Evidence", rootID.(string))
			if err != nil {
				return nil, err
			}
			snapshot, _ := root["snapshot_artifact_ref"].(map[string]any)
			if snapshot == nil {
				continue
			}
			if err = s.effective(tx, project, snapshot); err != nil {
				return nil, err
			}
			keys = mergeUnique(keys, []any{Hash([]any{"reviewed-origin", root["canonical_url"], root["upstream_revision"], snapshot["content_hash"]})})
		}
	}
	for _, raw := range Arr(facts, "experiments") {
		item := raw.(map[string]any)
		if item["outcome"] != "IMPROVED" || item["acceptance_ref"] == nil {
			continue
		}
		ref := item["experiment_ref"].(map[string]any)
		x, err := version(tx, project, ref)
		if err != nil {
			return nil, err
		}
		if _, err = s.experimentAcceptance(tx, project, x, Str(x, "acceptance_id")); err != nil {
			return nil, err
		}
		key, err := s.researchExperimentProgressKey(tx, project, x)
		if err != nil {
			return nil, err
		}
		if key != "" {
			keys = mergeUnique(keys, []any{key})
		}
	}
	return keys, nil
}

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
	_, err := s.researchAcceptedTask(tx, project, task)
	if err != nil {
		return err
	}
	facts, err := s.researchCycleFacts(tx, project, cycle, &owner)
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
	cycle, err = s.closeResearchCycle(tx, owner, project, Str(cycle, "id"), Object{"requested_status": facts["cycle_outcome"], "outcome_summary": "Current independently accepted cycle report " + Str(artifact, "id") + "; gaps and unknown cost retained."})
	if err != nil {
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
	keys, err := s.researchProgressKeys(tx, project, facts)
	if err != nil {
		return err
	}
	newKeys := Empty()
	for _, key := range keys {
		var prior int
		if err = tx.QueryRow("SELECT count(*) FROM resource_progress_runs WHERE project=? AND record=? AND EXISTS(SELECT 1 FROM json_each(resource_progress_runs.body,'$.progress_keys') WHERE value=?)", project, n["id"], key).Scan(&prior); err != nil {
			return err
		}
		if prior == 0 {
			newKeys = append(newKeys, key)
		}
	}
	if _, err = tx.Exec("INSERT INTO resource_progress_runs(project,run,record,body) VALUES(?,?,?,?)", project, task["active_run_id"], n["id"], string(Bytes(Object{"cycle_id": facts["cycle_id"], "report_acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "cycle_outcome": facts["cycle_outcome"], "progress_keys": keys, "at": Now()}))); err != nil {
		return err
	}
	if len(newKeys) > 0 {
		if _, err = tx.Exec("INSERT INTO resource_progress_resumes(id,project,record,body) VALUES(?,?,?,?)", ID(), project, n["id"], string(Bytes(Object{"reason": "Current independently accepted new origin support or measured improvement", "new_progress_keys": newKeys, "prior_counts": Object{"same_failure_count": n["same_failure_count"], "no_progress_iterations": n["no_progress_iterations"]}, "report_acceptance_ref": Ref(receipt, "AcceptanceReceipt"), "at": Now()}))); err != nil {
			return err
		}
		n["no_progress_iterations"], n["same_failure_count"], n["last_effective_progress_at"], n["status"] = 0, 0, Now(), "ACTIVE"
		if err = bump(n); err != nil {
			return err
		}
		return s.put(tx, "NoProgressRecord", n)
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
