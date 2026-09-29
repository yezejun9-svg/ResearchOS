package domain

import (
	"context"
	"database/sql"
	"strings"
	"time"
)

var runtimeOperations = map[string]bool{}

func init() {
	for _, id := range strings.Fields("registerRuntime getRuntimeRegistration listRuntimeRegistration getRun listRun heartbeatRun reportRun cancelRun acknowledgeRunCancellation reconcileRun") {
		runtimeOperations[id] = true
		implemented[id] = true
	}
}

// BeginRuntimeQualification is a trusted local construction/qualification entry, not claimTask.
// It deliberately rejects normal tasks and creates no READY scheduling authority.
func (s *Service) BeginRuntimeQualification(ctx context.Context, token, project, taskID, runtimeID, executor string) (Object, string, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, "", e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, "", e
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) {
		return nil, "", Fail(403, "FORBIDDEN", "qualification requires local owner")
	}
	task, e := load(tx, project, "Task", taskID)
	if e != nil {
		return nil, "", e
	}
	if task["task_type"] != "runtime_qualification" || task["status"] != "DRAFT" || len(Arr(task, "dependency_task_ids")) != 0 {
		return nil, "", Fail(409, "STATE_CONFLICT", "only dependency-free DRAFT runtime_qualification tasks are admitted here")
	}
	if e = s.taskContext(tx, project, task); e != nil {
		return nil, "", e
	}
	rt, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return nil, "", e
	}
	if rt["status"] == "REVOKED" || rt["status"] == "UNAVAILABLE" {
		return nil, "", Fail(409, "STATE_CONFLICT", "runtime unavailable")
	}
	var roles string
	var revoked int
	if e = tx.QueryRow("SELECT roles,revoked FROM auth_principals WHERE id=?", executor).Scan(&roles, &revoked); e != nil || revoked != 0 || !strings.Contains(roles, `"EXECUTOR"`) {
		return nil, "", Fail(403, "FORBIDDEN", "executor principal unavailable")
	}
	var epoch int64
	if e = tx.QueryRow("SELECT coalesce(max(CAST(json_extract(body,'$.lease_epoch') AS INTEGER)),0)+1 FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?", project, taskID).Scan(&epoch); e != nil {
		return nil, "", e
	}
	lease := ID() + ID()
	r := Merge(Base(project), Object{"task_id": taskID, "runtime_id": runtimeID, "executor_principal_id": executor, "attempt": epoch, "status": "QUEUED", "input_refs": task["input_refs"], "context_bundle_id": task["context_bundle_id"], "external_run_id": nil, "workspace_snapshot_id": ID(), "lease_token_hash": Digest([]byte(lease)), "lease_expires_at": time.Now().UTC().Add(90 * time.Second).Format(time.RFC3339Nano), "heartbeat_at": nil, "checkpoint_artifact_id": nil, "result_artifact_ids": Empty(), "execution_report": nil, "exit_code": nil, "runtime_settled_at": nil, "cancel_requested_at": nil, "cancel_confirmed_at": nil, "children_stopped": nil, "queue_empty": nil, "started_at": nil, "ended_at": nil, "lease_epoch": epoch})
	if e = s.put(tx, "Run", r); e != nil {
		return nil, "", e
	}
	if _, e = tx.Exec("INSERT INTO auth_grants(principal,project,task,run) VALUES(?,?,?,?)", executor, project, taskID, r["id"]); e != nil {
		return nil, "", e
	}
	if e = bump(task); e != nil {
		return nil, "", e
	}
	task["active_run_id"] = r["id"]
	task["assigned_principal_id"] = executor
	if e = s.put(tx, "Task", task); e != nil {
		return nil, "", e
	}
	if e = s.event(tx, project, "Run", r, p.ID, ID(), "RUN_CHANGED"); e != nil {
		return nil, "", e
	}
	return r, lease, tx.Commit()
}

// ObserveRuntime is only called by the trusted worker bridge. There is no HTTP write endpoint.
// An old epoch observation is retained for reconciliation but cannot change current Run state.
func (s *Service) ObserveRuntime(ctx context.Context, project, runID string, epoch int64, observation Object) error {
	if epoch < 1 {
		return Fail(400, "INVALID_REQUEST", "invalid epoch")
	}
	spec, _ := observation["spec"].(map[string]any)
	n, e := Num(spec, "epoch")
	if e != nil || n != epoch || spec["run_id"] != runID {
		return Fail(422, "GATE_FAILED", "observation identity mismatch")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	r, e := load(tx, project, "Run", runID)
	if e != nil {
		return e
	}
	if spec["task_id"] != r["task_id"] {
		return Fail(422, "GATE_FAILED", "observation task mismatch")
	}
	_, e = tx.Exec("INSERT OR IGNORE INTO runtime_observations(project,run,epoch,receipt_hash,body,observed_at) VALUES(?,?,?,?,?,?)", project, runID, epoch, Hash(observation), string(Bytes(observation)), Now())
	if e != nil {
		return e
	}
	return tx.Commit()
}
func runtimeObservation(tx *sql.Tx, project string, r Object) (Object, error) {
	var raw string
	e := tx.QueryRow("SELECT body FROM runtime_observations WHERE project=? AND run=? AND epoch=? ORDER BY observed_at DESC LIMIT 1", project, r["id"], r["lease_epoch"]).Scan(&raw)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "trusted runtime observation required")
	}
	return Decode([]byte(raw))
}
func currentRun(tx *sql.Tx, p Principal, project, id string) (Object, error) {
	r, e := load(tx, project, "Run", id)
	if e != nil {
		return nil, e
	}
	if !p.Allowed(project, Str(r, "task_id"), id, false) {
		return nil, Fail(404, "NOT_FOUND", "run unavailable")
	}
	return r, nil
}
func runTerminal(r Object) bool {
	return r["status"] == "SETTLED" || r["status"] == "FAILED" || r["status"] == "CANCELLED"
}
func runtimeLease(p Principal, r, b Object) error {
	epoch, e := Num(b, "lease_epoch")
	current, _ := Num(r, "lease_epoch")
	expires, te := time.Parse(time.RFC3339Nano, Str(r, "lease_expires_at"))
	if p.ID != r["executor_principal_id"] || e != nil || epoch != current || Digest([]byte(Str(b, "lease_token"))) != r["lease_token_hash"] || te != nil || !time.Now().Before(expires) {
		return Fail(409, "LEASE_EXPIRED", "run lease no longer current")
	}
	return nil
}
func (s *Service) runtimeOperation(tx *sql.Tx, p Principal, project, id string, b Object, op string) (Object, string, int, error) {
	if op == "registerRuntime" {
		r := Merge(Base(project), b)
		Merge(r, Object{"status": "REGISTERED", "qualification_ids": Empty(), "health_checked_at": nil, "supports_resume": false, "resume_evidence_ref": nil})
		return r, "RuntimeRegistration", 201, s.put(tx, "RuntimeRegistration", r)
	}
	r, e := currentRun(tx, p, project, id)
	if e != nil {
		return nil, "", 0, e
	}
	if op != "cancelRun" && op != "reconcileRun" {
		if e = runtimeLease(p, r, b); e != nil {
			return nil, "", 0, e
		}
	}
	if runTerminal(r) {
		return nil, "", 0, Fail(409, "STATE_CONFLICT", "run already terminal")
	}
	switch op {
	case "heartbeatRun":
		if r["status"] == "CANCEL_REQUESTED" || r["status"] == "RECONCILING" || r["status"] == "LOST" {
			return nil, "", 0, Fail(409, "STATE_CONFLICT", "run requires reconciliation")
		}
		if old := Str(r, "external_run_id"); old != "" && old != Str(b, "external_run_id") {
			return nil, "", 0, Fail(409, "STATE_CONFLICT", "external identity changed")
		}
		r["heartbeat_at"] = Now()
		r["lease_expires_at"] = time.Now().UTC().Add(90 * time.Second).Format(time.RFC3339Nano)
		r["external_run_id"] = b["external_run_id"]
		r["checkpoint_artifact_id"] = b["checkpoint_artifact_id"]
		r["status"] = "RUNNING"
		if r["started_at"] == nil {
			r["started_at"] = Now()
		}
	case "cancelRun":
		r["status"] = "CANCEL_REQUESTED"
		r["cancel_requested_at"] = Now()
	case "reportRun":
		o, err := runtimeObservation(tx, project, r)
		if err != nil {
			return nil, "", 0, err
		}
		protocol, _ := o["protocol"].(map[string]any)
		if o["state"] != "SETTLED" && o["state"] != "FAILED" || o["children_stopped"] != true || o["queue_empty"] != true || Str(o, "ended") == "" || Hash(o["exit_code"]) != Hash(b["exit_code"]) {
			return nil, "", 0, Fail(422, "GATE_FAILED", "settled process tree and complete receipt required")
		}
		if r["status"] == "CANCEL_REQUESTED" {
			return nil, "", 0, Fail(409, "STATE_CONFLICT", "cancellation requires acknowledgement")
		}
		for _, v := range Arr(b, "result_artifact_ids") {
			a, err := load(tx, project, "Artifact", v.(string))
			if err != nil || a["run_id"] != id || a["produced_by"] != p.ID {
				return nil, "", 0, Fail(422, "GATE_FAILED", "result must be sealed by this run")
			}
		}
		status := "FAILED"
		manifestOK := len(Arr(o, "artifacts")) > 0
		for _, v := range Arr(o, "artifacts") {
			item, ok := v.(map[string]any)
			if !ok {
				manifestOK = false
				break
			}
			found := false
			for _, id := range Arr(b, "result_artifact_ids") {
				a, err := load(tx, project, "Artifact", id.(string))
				if err == nil && a["content_hash"] == item["content_hash"] && Hash(a["byte_size"]) == Hash(item["byte_size"]) {
					found = true
				}
			}
			if !found {
				manifestOK = false
			}
		}
		if o["state"] == "SETTLED" && protocol["settled"] == true && manifestOK {
			status = "SETTLED"
		}
		Merge(r, Object{"status": status, "execution_report": b["execution_report"], "exit_code": b["exit_code"], "result_artifact_ids": b["result_artifact_ids"], "checkpoint_artifact_id": b["checkpoint_artifact_id"], "runtime_settled_at": Now(), "children_stopped": true, "queue_empty": true, "ended_at": Now()})
		task, err := load(tx, project, "Task", Str(r, "task_id"))
		if err != nil {
			return nil, "", 0, err
		}
		if task["active_run_id"] != id {
			return nil, "", 0, Fail(409, "STATE_CONFLICT", "run no longer owns task")
		}
		if status == "SETTLED" {
			if e = bump(task); e != nil {
				return nil, "", 0, e
			}
			task["status"] = "EXECUTION_REPORTED"
			task["output_artifact_ids"] = b["result_artifact_ids"]
			if e = s.put(tx, "Task", task); e != nil {
				return nil, "", 0, e
			}
		}
	case "acknowledgeRunCancellation":
		o, err := runtimeObservation(tx, project, r)
		if err != nil {
			return nil, "", 0, err
		}
		if r["status"] != "CANCEL_REQUESTED" || o["state"] != "CANCELLED" || o["children_stopped"] != true || o["queue_empty"] != true {
			return nil, "", 0, Fail(422, "GATE_FAILED", "cancellation is not confirmed")
		}
		if e = s.runtimeReceipt(tx, project, r, b["receipt_artifact_ref"], o); e != nil {
			return nil, "", 0, e
		}
		Merge(r, Object{"status": "CANCELLED", "children_stopped": true, "queue_empty": true, "cancel_confirmed_at": Now(), "ended_at": Now()})
	case "reconcileRun":
		o, err := runtimeObservation(tx, project, r)
		if err != nil {
			return nil, "", 0, err
		}
		if e = s.runtimeReceipt(tx, project, r, b["receipt_artifact_ref"], o); e != nil {
			return nil, "", 0, e
		}
		// UNKNOWN or missing process is never evidence of a settled side effect.
		r["status"] = "RECONCILING"
		r["children_stopped"] = o["children_stopped"]
		r["queue_empty"] = o["queue_empty"]
	default:
		return nil, "", 0, Fail(503, "RESOURCE_UNAVAILABLE", "runtime operation unavailable")
	}
	if e = bump(r); e != nil {
		return nil, "", 0, e
	}
	return r, "Run", 200, s.put(tx, "Run", r)
}
func (s *Service) runtimeReceipt(tx *sql.Tx, project string, r Object, value any, o Object) error {
	ref, ok := value.(map[string]any)
	if !ok {
		return Fail(422, "GATE_FAILED", "receipt reference required")
	}
	a, e := version(tx, project, ref)
	if e != nil || ref["entity_type"] != "Artifact" || a["run_id"] != r["id"] {
		return Fail(422, "GATE_FAILED", "receipt run mismatch")
	}
	var b []byte
	if e = tx.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", project, a["storage_key"]).Scan(&b); e != nil {
		return e
	}
	record, e := Decode(b)
	if e != nil || Hash(record) != Hash(o) {
		return Fail(422, "GATE_FAILED", "receipt differs from trusted observation")
	}
	return nil
}

// Scope checks are tied to current persisted Run relationships, never only a caller-supplied id.
func (s *Service) runtimeScope(tx *sql.Tx, p Principal, project, id, op string, b Object) bool {
	if op == "getTask" {
		task, e := load(tx, project, "Task", id)
		return e == nil && p.Allowed(project, id, Str(task, "active_run_id"), false)
	}
	if op == "getRun" || runtimeOperations[op] && op != "registerRuntime" && op != "listRun" && op != "listRuntimeRegistration" && op != "getRuntimeRegistration" {
		_, e := currentRun(tx, p, project, id)
		return e == nil
	}
	if op == "uploadContent" {
		_, e := activeExecutorRun(tx, p, project)
		return e == nil
	}
	if op == "sealArtifact" {
		r, e := currentRun(tx, p, project, Str(b, "run_id"))
		return e == nil && r["executor_principal_id"] == p.ID && !runTerminal(r)
	}
	if op == "getArtifact" || op == "getArtifactContent" {
		a, e := load(tx, project, "Artifact", id)
		if e != nil {
			return false
		}
		_, e = currentRun(tx, p, project, Str(a, "run_id"))
		return e == nil
	}
	return false
}
func activeExecutorRun(tx *sql.Tx, p Principal, project string) (Object, error) {
	var count int
	if e := tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.executor_principal_id')=? AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST')", project, p.ID).Scan(&count); e != nil || count != 1 {
		return nil, Fail(403, "FORBIDDEN", "upload requires one unambiguous active run")
	}
	var raw string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.executor_principal_id')=? AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED','RECONCILING','LOST') ORDER BY json_extract(body,'$.created_at') DESC LIMIT 1", project, p.ID).Scan(&raw)
	if e != nil {
		return nil, Fail(403, "FORBIDDEN", "no scoped active run")
	}
	r, e := Decode([]byte(raw))
	if e != nil || !p.Allowed(project, Str(r, "task_id"), Str(r, "id"), false) {
		return nil, Fail(403, "FORBIDDEN", "active run scope denied")
	}
	if e = validExecutorRun(tx, p, project, r); e != nil {
		return nil, e
	}
	return r, nil
}
func validExecutorRun(tx *sql.Tx, p Principal, project string, r Object) error {
	expires, e := time.Parse(time.RFC3339Nano, Str(r, "lease_expires_at"))
	task, te := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil || te != nil || !time.Now().Before(expires) || r["executor_principal_id"] != p.ID || task["active_run_id"] != r["id"] {
		return Fail(409, "LEASE_EXPIRED", "run is not current")
	}
	return nil
}
func (s *Service) runtimeUpload(tx *sql.Tx, p Principal, project string, b []byte) (Object, error) {
	r, e := activeExecutorRun(tx, p, project)
	if e != nil {
		return nil, e
	}
	o, e := s.upload(tx, p, project, b)
	if e != nil {
		return nil, e
	}
	_, e = tx.Exec("INSERT INTO runtime_uploads(storage_key,project,run,epoch) VALUES(?,?,?,?)", o["storage_key"], project, r["id"], r["lease_epoch"])
	return o, e
}
func (s *Service) runtimeSeal(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	r, e := currentRun(tx, p, project, Str(b, "run_id"))
	if e != nil {
		return nil, e
	}
	if e = validExecutorRun(tx, p, project, r); e != nil {
		return nil, e
	}
	var count int
	if e = tx.QueryRow("SELECT count(*) FROM runtime_uploads WHERE storage_key=? AND project=? AND run=? AND epoch=?", b["storage_key"], project, r["id"], r["lease_epoch"]).Scan(&count); e != nil {
		return nil, e
	}
	if count != 1 || r["executor_principal_id"] != p.ID || runTerminal(r) {
		return nil, Fail(403, "FORBIDDEN", "upload is not bound to current run")
	}
	return s.seal(tx, p, project, b)
}
