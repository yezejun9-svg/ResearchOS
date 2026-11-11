package domain

import (
	"context"
	"database/sql"
	"time"
)

func latestEffect(tx *sql.Tx, project, run, key string) (Object, error) {
	var raw string
	e := tx.QueryRow("SELECT body FROM resource_effects WHERE project=? AND run=? AND effect_key=? ORDER BY sequence DESC LIMIT 1", project, run, key).Scan(&raw)
	if e != nil {
		return nil, e
	}
	return Decode([]byte(raw))
}
func effectAppend(tx *sql.Tx, project, run, key string, o Object) error {
	var seq int64
	if e := tx.QueryRow("SELECT coalesce(max(sequence),0)+1 FROM resource_effects WHERE project=? AND run=? AND effect_key=?", project, run, key).Scan(&seq); e != nil {
		return e
	}
	o["sequence"] = seq
	o["observed_at"] = Now()
	_, e := tx.Exec("INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,?,?)", project, run, key, seq, string(Bytes(o)))
	return e
}
func effectsReconciled(tx *sql.Tx, project, run string) error {
	var unresolved int
	e := tx.QueryRow(`SELECT count(*) FROM resource_effects x WHERE project=? AND run=? AND sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('STARTED','UNKNOWN')`, project, run).Scan(&unresolved)
	if e != nil {
		return e
	}
	if unresolved != 0 {
		return Fail(409, "STATE_CONFLICT", "unknown effects require reconciliation; blind retry prohibited")
	}
	return nil
}

// PrepareEffect persists intent and cost admission in one transaction before
// any provider request. The sole scheduler owns this; a worker cannot enqueue.
func (s *Service) PrepareEffect(ctx context.Context, token, project, runID, key string, payload, cost Object) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	result, e := s.prepareEffectTx(tx, token, project, runID, key, payload, cost)
	if e != nil {
		return nil, e
	}
	return result, tx.Commit()
}
func (s *Service) prepareEffectTx(tx *sql.Tx, token, project, runID, key string, payload, cost Object) (Object, error) {
	if e := resourceWriteLock(tx); e != nil {
		return nil, e
	}
	p, e := resourcePrincipal(tx, token, project, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	if s.Contracts.Validate("Idempotency-Key", key) != nil {
		return nil, Fail(400, "INVALID_REQUEST", "stable effect key required")
	}
	digest := Hash([]any{payload, cost})
	prior, e := latestEffect(tx, project, runID, key)
	if e == nil {
		if prior["request_hash"] != digest {
			return nil, Fail(409, "IDEMPOTENCY_CONFLICT", "effect key payload changed")
		}
		return prior, nil
	}
	if e != sql.ErrNoRows {
		return nil, e
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	if e = qualificationEffectBlocked(tx, project, task); e != nil {
		if e = qualificationModelEffectAllowed(tx, project, task, payload); e != nil {
			return nil, e
		}
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return nil, e
	}
	if task["active_run_id"] != runID || goal["status"] != "ACTIVE" || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" {
		return nil, Fail(409, "STATE_CONFLICT", "run is not permitted new effects")
	}
	if e = s.taskContextForRun(tx, project, run); e != nil {
		return nil, e
	}
	if e = effectsReconciled(tx, project, runID); e != nil {
		return nil, e
	}
	if cost["run_id"] != runID || cost["provider_request_id"] != key || cost["reservation_id"] != nil || (cost["operation"] != "RESERVE" && cost["operation"] != "UNKNOWN") {
		return nil, Fail(422, "GATE_FAILED", "effect must bind a new reservation")
	}
	if e = s.Contracts.Validate("CostEntryRequest", cost); e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "invalid cost request")
	}
	ledger, e := s.appendBudget(tx, project, cost)
	if e != nil {
		return nil, e
	}
	o := Object{"project_id": project, "goal_id": goal["id"], "task_id": task["id"], "run_id": runID, "key": key, "request_hash": digest, "payload": payload, "reservation_id": ledger["id"], "state": "PREPARED", "epoch": run["lease_epoch"], "context_bundle_id": task["context_bundle_id"], "checkpoint_artifact_id": run["checkpoint_artifact_id"], "receipt": nil}
	if e = effectAppend(tx, project, runID, key, o); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Run", run, p.ID, ID(), "RUN_CHANGED"); e != nil {
		return nil, e
	}
	return o, nil
}

// BeginEffect is an atomic one-time dispatch fence. A lost acknowledgement is
// STARTED/UNKNOWN until trusted reconciliation, even when retries remain.
func (s *Service) BeginEffect(ctx context.Context, token, project, runID, key string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	result, e := s.beginEffectTx(tx, token, project, runID, key)
	if e != nil {
		return nil, e
	}
	return result, tx.Commit()
}
func (s *Service) beginEffectTx(tx *sql.Tx, token, project, runID, key string) (Object, error) {
	if e := resourceWriteLock(tx); e != nil {
		return nil, e
	}
	_, e := resourcePrincipal(tx, token, project, "SCHEDULER")
	if e != nil {
		return nil, e
	}
	o, e := latestEffect(tx, project, runID, key)
	if e != nil {
		return nil, e
	}
	if o["state"] != "PREPARED" {
		return nil, Fail(409, "STATE_CONFLICT", "already dispatched; query provider before recovery")
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	if e = qualificationEffectBlocked(tx, project, task); e != nil {
		payload, _ := o["payload"].(map[string]any)
		if e = qualificationModelEffectAllowed(tx, project, task, payload); e != nil {
			return nil, e
		}
	}
	goal, e := load(tx, project, "Goal", Str(task, "goal_id"))
	if e != nil {
		return nil, e
	}
	if goal["status"] != "ACTIVE" || task["status"] != "RUNNING" || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || task["active_run_id"] != runID {
		return nil, Fail(409, "STATE_CONFLICT", "run stopped or superseded")
	}
	expiry, e := time.Parse(time.RFC3339Nano, Str(run, "lease_expires_at"))
	if e != nil || !expiry.After(time.Now()) {
		return nil, Fail(409, "LEASE_EXPIRED", "expired lease cannot start effect")
	}
	if e = s.taskContextForRun(tx, project, run); e != nil {
		return nil, e
	}
	ledger, e := load(tx, project, "BudgetLedgerEntry", Str(o, "reservation_id"))
	if e != nil {
		return nil, e
	}
	var lastCost string
	if e = tx.QueryRow("SELECT json_extract(body,'$.operation') FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.provider_request_id')=? ORDER BY rowid DESC LIMIT 1", project, runID, key).Scan(&lastCost); e != nil {
		return nil, e
	}
	if lastCost != "RESERVE" && lastCost != "UNKNOWN" {
		return nil, Fail(409, "STATE_CONFLICT", "settled or released cost cannot authorize a new effect")
	}
	chain, _, e := runBudgetScopes(tx, project, runID)
	if e != nil {
		return nil, e
	}
	for _, policy := range chain {
		if policy["mode"] != "CAPPED" {
			continue
		}
		if ledger["money"] == nil {
			if policy["enforcement"] == "STRICT" || policy["unknown_cost_action"] == "BLOCK" {
				return nil, Fail(422, "GATE_FAILED", "current policy cannot bound prepared effect")
			}
			continue
		}
		if policy["enforcement"] == "STRICT" && ledger["cost_basis"] != "UPPER_BOUND" {
			return nil, Fail(422, "GATE_FAILED", "current policy cannot bound prepared effect")
		}
		cap := policy["cap"].(map[string]any)
		used, unknown, e := budgetExposure(tx, policy, Str(cap, "currency"))
		if e != nil {
			return nil, e
		}
		limit, _ := moneyAmount(cap)
		if unknown && (policy["enforcement"] == "STRICT" || policy["unknown_cost_action"] == "BLOCK") || used.Cmp(limit) > 0 {
			return nil, Fail(422, "GATE_FAILED", "tightened policy blocks unissued effect")
		}
	}
	o["state"] = "STARTED"
	o["epoch"] = run["lease_epoch"]
	if e = effectAppend(tx, project, runID, key, o); e != nil {
		return nil, e
	}
	return o, nil
}

// ObserveEffect is the trusted worker/provider reconciliation boundary, like
// ObserveRuntime. No public HTTP endpoint accepts invented provider outcomes.
func (s *Service) ObserveEffect(ctx context.Context, project, runID, key, state string, receipt Object) error {
	if (state != "CONFIRMED" && state != "UNKNOWN" && state != "NOT_APPLIED") || len(receipt) == 0 {
		return Fail(400, "INVALID_REQUEST", "trusted outcome and receipt required")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	o, e := latestEffect(tx, project, runID, key)
	if e != nil {
		return e
	}
	if o["state"] == state && Hash(o["receipt"]) == Hash(receipt) {
		return nil
	}
	if o["state"] == "CONFIRMED" || o["state"] == "NOT_APPLIED" || o["state"] == "PREPARED" {
		return Fail(409, "STATE_CONFLICT", "effect outcome cannot be rewritten")
	}
	o["state"] = state
	o["receipt"] = receipt
	if e = effectAppend(tx, project, runID, key, o); e != nil {
		return e
	}
	return tx.Commit()
}

// ResumeCheckpoint rebuilds current context after trusted process/effect
// reconciliation. It retains Run identity and all provider keys, rotating only
// the execution lease so old callbacks cannot change the resumed run.
func (s *Service) ResumeCheckpoint(ctx context.Context, token, project, runID, key string, expectedRevision int64) (Object, error) {
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
	priorDispatch, dispatchErr := runtimeDispatch(tx, project, runID, run["lease_epoch"])
	if dispatchErr != nil && dispatchErr != sql.ErrNoRows {
		return nil, dispatchErr
	}
	native := dispatchErr == nil
	if native {
		if priorDispatch["manifest"].(map[string]any)["admission"].(map[string]any)["qualification_bootstrap"] == true {
			return nil, Fail(403, "FORBIDDEN", "qualification bootstrap cannot resume")
		}
		if _, e = nativeDispatchProof(tx, project, run, observation); e != nil {
			return nil, e
		}
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
	runtime, e := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
	if e != nil {
		return nil, e
	}
	var admission Object
	if native || runtime["measurement_mode"] != "FIXTURE" {
		admission, e = s.currentRuntimeAdmission(tx, project, task, runtime, []any{"start", "context_rebuild"}, "checkpoint_resume")
		if e != nil {
			return nil, e
		}
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
	if native {
		if e = s.reserveRuntimeLocalLaunch(tx, project, run, admission); e != nil {
			return nil, e
		}
		if e = s.prepareRuntimeDispatch(tx, project, task, run, admission); e != nil {
			return nil, e
		}
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
