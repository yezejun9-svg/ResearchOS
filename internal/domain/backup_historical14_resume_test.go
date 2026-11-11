package domain

import (
    "context"
    "database/sql"
)

// Test-only schema14 behavior, copied from the pinned historical durability.go.
// The caller validates the exact restored schema14 before every invocation.
// Current production ResumeCheckpoint retains its native dispatch checks.
func (s *Service) upgradeHistorical14ResumeCheckpoint(ctx context.Context, token, project, runID, key string, expectedRevision int64) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return nil, e
	}
	p, e := resourcePrincipal(tx, token, project, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	if s.Contracts.Validate("Idempotency-Key", key) != nil {
		return nil, Fail(400, "INVALID_REQUEST", "resume key required")
	}
	hash := Hash([]any{runID, expectedRevision})
	var oldHash string
	var raw []byte
	e = tx.QueryRow("SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation='resumeCheckpoint' AND key=?", p.ID, project, key).Scan(&oldHash, &raw)
	if e == nil {
		if hash != oldHash {
			return nil, Fail(409, "IDEMPOTENCY_CONFLICT", "resume key changed")
		}
		return Decode(raw)
	}
	if e != sql.ErrNoRows {
		return nil, e
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	revision, _ := Num(run, "revision")
	if revision != expectedRevision {
		return nil, Fail(412, "STALE_REVISION", "run changed")
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return nil, e
	}
	if task["active_run_id"] != runID || task["status"] != "RUNNING" || goal["status"] != "ACTIVE" || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" {
		return nil, Fail(409, "STATE_CONFLICT", "stop state retains ownership without resume")
	}
	if Str(run, "checkpoint_artifact_id") == "" {
		return nil, Fail(422, "GATE_FAILED", "durable checkpoint required")
	}
	checkpoint, oldUse, e := s.artifactUse(tx, project, run, Str(run, "checkpoint_artifact_id"), false)
	if e != nil {
		return nil, e
	}
	observation, e := runtimeObservation(tx, project, run)
	if e != nil {
		return nil, e
	}
	if observation["children_stopped"] != true || observation["queue_empty"] != true {
		return nil, Fail(422, "GATE_FAILED", "old process tree not confirmed stopped")
	}
	if e = effectsReconciled(tx, project, runID); e != nil {
		return nil, e
	}
	// A refreshed context is not authorization to rewrite an in-flight input set.
	if Hash(run["input_refs"]) != Hash(task["input_refs"]) {
		return nil, Fail(412, "STALE_INPUT", "changed run inputs require explicit revalidation")
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	bundle, e := s.createContext(tx, p, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]})
	if e != nil {
		return nil, e
	}
	task, e = load(tx, project, "Task", Str(task, "id"))
	if e != nil {
		return nil, e
	}
	if e = s.taskContext(tx, project, task); e != nil {
		return nil, e
	}
	dependencies, e := s.dependencyVector(tx, project, task)
	if e != nil {
		return nil, e
	}
	if e = s.dependencyContext(tx, project, task, dependencies); e != nil {
		return nil, e
	}
	run["context_bundle_id"] = bundle["id"]
	lease, e := s.rebuildResourceSession(tx, project, p.ID, "CHECKPOINT_AND_CURRENT_CONTEXT", run)
	if e != nil {
		return nil, e
	}
	if _, e = s.runDependenciesCurrent(tx, project, task, run); e != nil {
		return nil, e
	}

	if e = s.carryCheckpoint(tx, project, p.ID, run, checkpoint, oldUse); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Run", run, p.ID, key, "RUN_CHANGED"); e != nil {
		return nil, e
	}
	out := Object{"run": run, "context": bundle, "lease_token": lease, "native_resume": false, "resume_mode": "CHECKPOINT_AND_CURRENT_CONTEXT"}
	if _, e = tx.Exec("INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'resumeCheckpoint',?,?,200,?,'{}',?)", p.ID, project, key, hash, Bytes(out), Now()); e != nil {
		return nil, e
	}
	return out, tx.Commit()
}
