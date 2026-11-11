//go:build windows

package domain

import (
	"context"
	"database/sql"
	rt "researchos.local/research-os/adapters/runtime"
)

func (c *RuntimeCoordinator) researchExperimentGate(tx *sql.Tx, project string, task, run Object, frame rt.BridgeFrame, payload Object) (*researchWork, Object, error) {
	w, err := loadResearchWork(tx, project, Str(task, "id"))
	if err != nil {
		return nil, nil, err
	}
	if w.Stage != "experiment" || w.Experiment == "" || frame.Key != "experiment-"+w.Key || Hash(payload) != Hash(Object{"logical_key": w.Key}) || task["active_run_id"] != run["id"] {
		return nil, nil, Fail(403, "FORBIDDEN", "exact research experiment work required")
	}
	meta, _, err := c.service.monitorSnapshot(tx, project, Str(task, "goal_id"), true)
	if err != nil {
		return nil, nil, err
	}
	if Hash(w.PlanRef) != Hash(meta["brief_ref"]) || Hash(w.InputRefs) != Hash(task["input_refs"]) {
		return nil, nil, Fail(412, "STALE_INPUT", "experiment work inputs changed")
	}
	x, err := load(tx, project, "Experiment", w.Experiment)
	if err != nil {
		return nil, nil, err
	}
	if x["cycle_id"] != w.Cycle || x["preregistration_hash"] != w.Parameters["preregistration_hash"] || Hash(x["acceptance_contract"]) != Hash(task["acceptance_contract"]) {
		return nil, nil, Fail(422, "GATE_FAILED", "experiment preregistration binding differs")
	}
	if err = c.service.experimentCurrent(tx, project, x); err != nil {
		return nil, nil, err
	}
	if x["measurement_mode"] != "FIXTURE" || !nativeExperiment(x) {
		return nil, nil, Fail(503, "RESOURCE_UNAVAILABLE", "current native experiment capability unavailable")
	}
	return w, x, nil
}

func (c *RuntimeCoordinator) brokerResearchExperiment(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, frame rt.BridgeFrame, payload, intent Object) (Object, error) {
	tx, run, dispatch, err := c.dispatchGate(ctx, route, runID, lease, epoch)
	if err != nil {
		return nil, err
	}
	if _, err = c.providerRoute(tx, route, run, dispatch, frame); err != nil {
		tx.Rollback()
		return nil, err
	}
	task, err := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
	if err != nil {
		tx.Rollback()
		return nil, err
	}
	w, x, err := c.researchExperimentGate(tx, route.ProjectID, task, run, frame, payload)
	if err != nil {
		tx.Rollback()
		return nil, err
	}
	p, err := resourcePrincipal(tx, c.schedulerCredential(route.ProjectID), route.ProjectID, "SCHEDULER")
	if err != nil {
		tx.Rollback()
		return nil, err
	}
	if x["status"] == "REGISTERED" {
		if _, err = c.service.beginExperimentTx(tx, p, route.ProjectID, w.Experiment, runID); err != nil {
			tx.Rollback()
			return nil, err
		}
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	_, err = c.service.ExecuteExperimentPair(ctx, route.ExecutorToken, route.ProjectID, w.Experiment, runID, Object{"lease_token": lease, "lease_epoch": epoch})
	if err != nil {
		c.service.ObserveEffect(context.Background(), route.ProjectID, runID, frame.Key, "UNKNOWN", Object{"reason": "native paired execution requires original receipt reconciliation"})
		return nil, err
	}
	return c.reconcileResearchExperimentEffect(context.Background(), route.ProjectID, runID, epoch, frame, intent)
}

func (c *RuntimeCoordinator) reconcileResearchExperimentEffect(ctx context.Context, project, runID string, epoch int64, frame rt.BridgeFrame, intent Object) (Object, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, err
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return nil, err
	}
	w, err := loadResearchWork(tx, project, Str(run, "task_id"))
	if err != nil {
		return nil, err
	}
	original, err := latestEffect(tx, project, runID, frame.Key)
	if err != nil {
		return nil, err
	}
	if w.Stage != "experiment" || frame.Key != "experiment-"+w.Key || original["request_hash"] != intent["request_hash"] || original["reservation_id"] != intent["reservation_id"] || Hash(original["epoch"]) != Hash(epoch) {
		return nil, Fail(422, "GATE_FAILED", "experiment receipt differs from original effect")
	}
	if original["state"] == "CONFIRMED" {
		receipt := original["receipt"].(map[string]any)
		return Object{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": receipt["payload"]}, nil
	}
	if original["state"] != "STARTED" && original["state"] != "UNKNOWN" {
		return nil, Fail(409, "STATE_CONFLICT", "experiment effect cannot be rewritten")
	}
	var raw, receiptHash string
	if err = tx.QueryRow("SELECT body,receipt_hash FROM experiment_executions WHERE project=? AND experiment=? AND run=? AND epoch=? AND state='RECORDED'", project, w.Experiment, runID, epoch).Scan(&raw, &receiptHash); err != nil {
		return nil, Fail(409, "STATE_CONFLICT", "native execution receipt unavailable; repeat prohibited")
	}
	record, err := Decode([]byte(raw))
	if err != nil || record["receipt_hash"] != receiptHash || Receipt(record) != receiptHash || record["preregistration_hash"] != w.Parameters["preregistration_hash"] {
		return nil, Fail(422, "GATE_FAILED", "native execution receipt invalid")
	}
	ledger, err := load(tx, project, "BudgetLedgerEntry", Str(intent, "reservation_id"))
	if err != nil {
		return nil, err
	}
	if _, err = c.service.appendBudget(tx, project, Object{"policy_id": ledger["policy_id"], "run_id": runID, "operation": "UNKNOWN", "money": nil, "provider_request_id": frame.Key, "provider_event_id": "experiment/" + receiptHash, "reservation_id": intent["reservation_id"], "cost_basis": "UNKNOWN", "occurred_at": Now()}); err != nil {
		return nil, err
	}
	receipt := Object{"receipt_id": receiptHash, "key": frame.Key, "run_id": runID, "epoch": epoch, "state": "CONFIRMED", "actual_cost": nil, "cost_basis": "UNKNOWN", "payload": record["observation"]}
	original["state"], original["receipt"] = "CONFIRMED", receipt
	if err = effectAppend(tx, project, runID, frame.Key, original); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return Object{"sequence": frame.Sequence, "key": frame.Key, "state": "CONFIRMED", "payload": record["observation"]}, nil
}
