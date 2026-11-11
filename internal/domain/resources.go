package domain

import (
	"context"
	"database/sql"
	"strings"
	"time"
)

func init() {
	for _, op := range strings.Fields("createResourceRequest resolveResourceRequest getResourceRequest listResourceRequest getNoProgressRecord listNoProgressRecord") {
		implemented[op] = true
		resourceOperations[op] = true
	}
}

func resourceWriteLock(tx *sql.Tx) error {
	_, e := tx.Exec("UPDATE resource_write_lock SET value=value WHERE id=1")
	return e
}
func resourcePrincipal(tx *sql.Tx, token, project, role string) (Principal, error) {
	p, e := authenticate(tx, token)
	if e != nil {
		return p, e
	}
	if !p.HasRole(role) || !p.Allowed(project, "", "", false) {
		return p, Fail(403, "FORBIDDEN", "resource authority required")
	}
	return p, nil
}

func mergeUnique(a, b []any) []any {
	seen := map[string]bool{}
	out := Empty()
	for _, v := range append(append([]any{}, a...), b...) {
		k := Hash(v)
		if !seen[k] {
			seen[k] = true
			out = append(out, v)
		}
	}
	return out
}

func (s *Service) createResourceRequest(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if e := s.Contracts.Validate("CreateResourceRequest", b); e != nil {
		return nil, Fail(400, "INVALID_REQUEST", "invalid resource request")
	}
	if b["cost_known"] != (b["estimated_cost"] != nil) {
		return nil, Fail(422, "GATE_FAILED", "unknown cost must remain null")
	}
	key := Hash([]any{project, b["category"], b["account_ref"], b["reason_code"]})
	var raw string
	e := tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND json_extract(body,'$.dedup_key')=? AND json_extract(body,'$.status') IN ('OPEN','ACKNOWLEDGED')", project, key).Scan(&raw)
	var o Object
	if e == nil {
		o, e = Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
		for _, field := range []string{"blocked_task_ids", "continuable_task_ids", "completed_artifact_refs"} {
			o[field] = mergeUnique(Arr(o, field), Arr(b, field))
		}
		if b["requested_capability"] != o["requested_capability"] {
			o["requested_capability"] = Str(o, "requested_capability") + "; " + Str(b, "requested_capability")
		}
		if b["cost_known"] == false || Hash(o["estimated_cost"]) != Hash(b["estimated_cost"]) {
			o["cost_known"] = false
			o["estimated_cost"] = nil
		}
		// A request may be raised before the first durable checkpoint exists. Retain
		// the latest verified recovery reference instead of freezing that first null.
		if ref, ok := b["resume_checkpoint_ref"].(map[string]any); ok {
			if e = s.effective(tx, project, ref); e != nil {
				return nil, e
			}
			o["resume_checkpoint_ref"] = ref
		}
		o["summary"] = b["summary"]
		if e = bump(o); e != nil {
			return nil, e
		}
	} else if e == sql.ErrNoRows {
		o = Merge(Merge(Base(project), b), Object{"dedup_key": key, "status": "OPEN", "resolved_by": nil})
	} else {
		return nil, e
	}
	blocked := map[string]bool{}
	for _, v := range Arr(o, "blocked_task_ids") {
		blocked[v.(string)] = true
	}
	continuable := Empty()
	for _, v := range Arr(o, "continuable_task_ids") {
		if !blocked[v.(string)] {
			continuable = append(continuable, v)
		}
	}
	o["continuable_task_ids"] = continuable
	if e = s.put(tx, "ResourceRequest", o); e != nil {
		return nil, e
	}
	if e = s.resourceRequestNotice(tx, project, o, p.ID, ID()); e != nil {
		return nil, e
	}
	return o, nil
}

func (s *Service) resolveResourceRequest(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "ResourceRequest", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "OPEN" && o["status"] != "ACKNOWLEDGED" {
		return nil, Fail(409, "STATE_CONFLICT", "request already closed")
	}
	for _, v := range Arr(b, "resolution_evidence_refs") {
		if e = s.effective(tx, project, v.(map[string]any)); e != nil {
			return nil, e
		}
	}
	if e = s.applyResourceRecovery(tx, p, project, o, Arr(b, "resolution_evidence_refs")); e != nil {
		return nil, e
	}
	if _, e = tx.Exec("INSERT INTO resource_resolutions(request,project,body) VALUES(?,?,?)", id, project, string(Bytes(Merge(Merge(Object{}, b), Object{"actor": p.ID, "at": Now()})))); e != nil {
		return nil, e
	}
	o["status"] = "RESOLVED"
	o["resolved_by"] = p.ID
	if e = bump(o); e != nil {
		return nil, e
	}
	if e = s.put(tx, "ResourceRequest", o); e != nil {
		return nil, e
	}
	return o, nil
}

// AuthorizeFixtureResource records explicit OWNER permission and an observed,
// version-bound qualification fixture. It confers no LIVE runtime qualification.
func (s *Service) AuthorizeFixtureResource(ctx context.Context, token, project, runtime, purpose string, evidence Object, expires time.Time) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = resourceWriteLock(tx); e != nil {
		return e
	}
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return e
	}
	r, e := load(tx, project, "RuntimeRegistration", runtime)
	if e != nil {
		return e
	}
	var registered int
	if e = tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", project, runtime).Scan(&registered); e != nil {
		return e
	}
	a, e := version(tx, project, evidence)
	if e != nil {
		return e
	}
	if purpose == "" || !expires.After(time.Now()) || registered != 1 || r["measurement_mode"] != "FIXTURE" || evidence["entity_type"] != "Artifact" || a["measurement_mode"] != "FIXTURE" || a["evidence_kind"] != "OBSERVED" {
		return Fail(422, "GATE_FAILED", "current observed fixture qualification and registered fixture required")
	}
	grant := Object{"runtime_ref": Ref(r, "RuntimeRegistration"), "purpose": purpose, "evidence_ref": evidence, "expires_at": expires.UTC().Format(time.RFC3339Nano), "authorized_by": p.ID, "mode": "FIXTURE", "authorized_at": Now()}
	_, e = tx.Exec("INSERT INTO resource_route_grants(project,runtime,purpose,body) VALUES(?,?,?,?) ON CONFLICT(project,runtime,purpose) DO UPDATE SET body=excluded.body", project, runtime, purpose, string(Bytes(grant)))
	if e != nil {
		return e
	}
	return tx.Commit()
}

func (s *Service) qualifiedReplacement(tx *sql.Tx, project string, task, current, replacement Object) (Object, error) {
	if len(Arr(replacement, "qualification_ids")) > 0 {
		admission, e := s.currentRuntimeAdmission(tx, project, task, replacement, []any{"start", "context_rebuild"}, "replacement")
		if e != nil {
			return nil, e
		}
		if admission["mode"] != current["measurement_mode"] || replacement["platform"] != current["platform"] {
			return nil, Fail(422, "GATE_FAILED", "replacement provenance or platform differs")
		}
		return Object{"permission": admission["permission"], "admission": admission}, nil
	}
	var raw string
	e := tx.QueryRow("SELECT body FROM resource_route_grants WHERE project=? AND runtime=? AND purpose=?", project, replacement["id"], task["task_type"]).Scan(&raw)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "replacement lacks owner purpose authorization")
	}
	grant, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	expiry, e := time.Parse(time.RFC3339Nano, Str(grant, "expires_at"))
	if e != nil || !expiry.After(time.Now()) || Hash(grant["runtime_ref"]) != Hash(Ref(replacement, "RuntimeRegistration")) {
		return nil, Fail(422, "GATE_FAILED", "replacement qualification expired or changed")
	}
	var revoked int
	e = tx.QueryRow("SELECT revoked FROM auth_principals WHERE id=?", grant["authorized_by"]).Scan(&revoked)
	if e != nil || revoked != 0 {
		return nil, Fail(403, "FORBIDDEN", "resource authorization revoked")
	}
	if replacement["measurement_mode"] != "FIXTURE" || current["measurement_mode"] != "FIXTURE" || grant["mode"] != "FIXTURE" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "LIVE replacement requires W05 qualified purpose grant")
	}
	if replacement["status"] == "UNAVAILABLE" || replacement["status"] == "REVOKED" || replacement["platform"] != current["platform"] {
		return nil, Fail(422, "GATE_FAILED", "replacement unavailable or platform mismatch")
	}
	caps := map[string]bool{}
	for _, v := range Arr(replacement, "capabilities") {
		caps[v.(string)] = true
	}
	for _, v := range Arr(current, "capabilities") {
		if !caps[v.(string)] {
			return nil, Fail(422, "GATE_FAILED", "replacement capabilities not equivalent")
		}
	}
	if e = s.effective(tx, project, grant["evidence_ref"].(map[string]any)); e != nil {
		return nil, e
	}
	return grant, nil
}

// SwitchResource stays on the original Run and durable effect keys. A failed
// replacement is a local branch ResourceRequest, never a project-wide stop.
func (s *Service) SwitchResource(ctx context.Context, token, project, runID, replacementID string, request Object) (Object, error) {
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
	result, e := s.switchResource(tx, p, project, runID, replacementID, request)
	if e != nil {
		return nil, e
	}
	return result, tx.Commit()
}

// switchResource also serves the existing resource-resolution HTTP transaction.
// The caller owns commit, so failure resolving a request rolls back the switch.
func (s *Service) switchResource(tx *sql.Tx, p Principal, project, runID, replacementID string, request Object) (Object, error) {
	if !(p.HasRole("SCHEDULER") || p.HasRole("OWNER")) || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "resource authority required")
	}
	run, e := load(tx, project, "Run", runID)
	if e != nil {
		return nil, e
	}
	task, e := load(tx, project, "Task", Str(run, "task_id"))
	if e != nil {
		return nil, e
	}
	if task["active_run_id"] != run["id"] || runTerminal(run) || run["status"] == "CANCEL_REQUESTED" {
		return nil, Fail(409, "STATE_CONFLICT", "stopped or superseded run cannot switch")
	}
	current, e := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
	if e != nil {
		return nil, e
	}
	replacement, e := load(tx, project, "RuntimeRegistration", replacementID)
	if e != nil {
		return nil, e
	}
	grant, qualificationErr := s.qualifiedReplacement(tx, project, task, current, replacement)
	if qualificationErr != nil {
		request = Merge(Merge(Object{}, request), Object{"blocked_task_ids": mergeUnique(Arr(request, "blocked_task_ids"), []any{task["id"]})})
		o, e := s.createResourceRequest(tx, p, project, request)
		if e != nil {
			return nil, e
		}
		if e = s.event(tx, project, "ResourceRequest", o, p.ID, ID(), "RESOURCE_REQUESTED"); e != nil {
			return nil, e
		}
		return Object{"status": "BLOCKED", "request": o, "reason": qualificationErr.Error()}, nil
	}
	if e = s.taskContext(tx, project, task); e != nil {
		return nil, e
	}
	priorDispatch, dispatchErr := runtimeDispatch(tx, project, runID, run["lease_epoch"])
	if dispatchErr != nil && dispatchErr != sql.ErrNoRows {
		return nil, dispatchErr
	}
	native := dispatchErr == nil
	if native {
		if priorDispatch["manifest"].(map[string]any)["admission"].(map[string]any)["qualification_bootstrap"] == true {
			return nil, Fail(403, "FORBIDDEN", "qualification bootstrap cannot switch runtime")
		}
		observation, e := runtimeObservation(tx, project, run)
		if e != nil {
			return nil, e
		}
		if _, e = nativeDispatchProof(tx, project, run, observation); e != nil {
			return nil, e
		}
		if observation["children_stopped"] != true || observation["queue_empty"] != true || Str(run, "checkpoint_artifact_id") == "" {
			return nil, Fail(422, "GATE_FAILED", "stopped native execution and durable checkpoint required")
		}
		if grant["admission"] == nil {
			return nil, Fail(422, "GATE_FAILED", "native replacement requires current qualified admission")
		}
	}
	if run["status"] != "QUEUED" {
		observation, e := runtimeObservation(tx, project, run)
		if e != nil {
			return nil, e
		}
		if observation["children_stopped"] != true || observation["queue_empty"] != true {
			return nil, Fail(422, "GATE_FAILED", "prior execution must be reconciled before switching")
		}
	}
	if e = effectsReconciled(tx, project, runID); e != nil {
		return nil, e
	}
	var checkpoint, oldUse Object
	if id := Str(run, "checkpoint_artifact_id"); id != "" {
		checkpoint, oldUse, e = s.artifactUse(tx, project, run, id, false)
		if e != nil {
			return nil, e
		}
	}
	history := Object{"from_runtime_ref": Ref(current, "RuntimeRegistration"), "to_runtime_ref": Ref(replacement, "RuntimeRegistration"), "grant": grant, "run_id": runID, "task_id": task["id"], "acceptance_contract_hash": task["acceptance_contract"].(map[string]any)["contract_hash"], "context_bundle_id": task["context_bundle_id"], "checkpoint_artifact_id": run["checkpoint_artifact_id"], "at": Now(), "actor": p.ID}
	if _, e = tx.Exec("INSERT INTO resource_route_history(id,project,run,body) VALUES(?,?,?,?)", ID(), project, runID, string(Bytes(history))); e != nil {
		return nil, e
	}
	run["runtime_id"] = replacementID
	lease, e := s.rebuildResourceSession(tx, project, p.ID, "RESOURCE_SWITCH", run)
	if e != nil {
		return nil, e
	}
	if checkpoint != nil {
		if e = s.carryCheckpoint(tx, project, p.ID, run, checkpoint, oldUse); e != nil {
			return nil, e
		}
	}
	if native {
		admission := grant["admission"].(map[string]any)
		if e = s.reserveRuntimeLocalLaunch(tx, project, run, admission); e != nil {
			return nil, e
		}
		if e = s.prepareRuntimeDispatch(tx, project, task, run, admission); e != nil {
			return nil, e
		}
	}
	if e = s.event(tx, project, "Run", run, p.ID, ID(), "RUN_CHANGED"); e != nil {
		return nil, e
	}
	return Object{"status": "SWITCHED", "run": run, "evidence": history, "lease_token": lease, "native_resume": false, "resume_mode": "CHECKPOINT_AND_CURRENT_CONTEXT"}, nil
}
