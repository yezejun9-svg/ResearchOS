//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
	"errors"
	"time"
)

// LocalRuntimeQualificationRequest is a trusted managed-host request, never a
// new public client method. Every field is frozen before any model dispatch.
type LocalRuntimeQualificationRequest struct {
	RequestID         string `json:"request_id"`
	ProjectID         string `json:"project_id"`
	SessionID         string `json:"session_id"`
	ModelRef          string `json:"model_config_ref"`
	RuntimeID         string `json:"runtime_id"`
	TaskID            string `json:"task_id"`
	PlanHash          string `json:"plan_hash"`
	ProfileHash       string `json:"profile_hash"`
	AuthorizePurpose  string `json:"authorize_purpose"`
	PurposeSeconds    int    `json:"purpose_seconds"`
	OwnerHost         string `json:"owner_host"`
	OwnerPrincipal    string `json:"owner_principal"`
	OwnerRoot         string `json:"owner_root"`
	SessionHash       string `json:"session_hash"`
	ConfigurationHash string `json:"configuration_hash"`
	IssuedAt          string `json:"issued_at"`
	ExpiresAt         string `json:"expires_at"`
}

func (c *RuntimeCoordinator) localQualification(tx *sql.Tx, p Principal, request LocalRuntimeQualificationRequest) (Object, Object, error) {
	if request.RequestID == "" || request.AuthorizePurpose != "mu_turn" || request.PurposeSeconds < 1 || request.PurposeSeconds > 3600 || request.PlanHash == "" || request.ProfileHash == "" {
		return nil, nil, Fail(422, "GATE_FAILED", "explicit bounded local qualification request required")
	}
	candidate := RuntimeSetupCandidate{ProjectID: request.ProjectID, SessionID: request.SessionID, PrincipalID: p.ID, ModelRef: request.ModelRef}
	if _, e := c.service.runtimeSetupConfiguration(context.Background(), tx, p, candidate, c.config.ClientSchema, c.config.ConfigurationAuthority); e != nil {
		return nil, nil, e
	}
	runtime, profile, e := c.sessionModel(tx, request.ProjectID, request.ModelRef)
	if e != nil || runtime["id"] != request.RuntimeID {
		return nil, nil, Fail(412, "STALE_INPUT", "configured runtime differs from managed qualification request")
	}
	plan, digest, root, e := qualificationPlan(tx, request.ProjectID, request.TaskID, request.RuntimeID)
	ownerRoot, rootErr := currentAuthorityRoot(tx, p.ID)
	if e != nil || rootErr != nil || root != ownerRoot || digest != request.PlanHash || Hash(plan["profile_ref"]) != request.ProfileHash {
		return nil, nil, Fail(412, "STALE_INPUT", "managed qualification plan, profile or Owner changed")
	}
	config, _ := profile["model_config"].(map[string]any)
	if config["ref"] != request.ModelRef {
		return nil, nil, Fail(422, "GATE_FAILED", "exact configured local Mu profile required")
	}
	if e = validateLocalQualificationProfile(profile); e != nil {
		return nil, nil, e
	}
	if profile["coding_authorization"] != nil {
		var workspace string
		if e = tx.QueryRow(`SELECT workspace_ref FROM client_sessions WHERE id=? AND project_id=?`, request.SessionID, request.ProjectID).Scan(&workspace); e != nil {
			return nil, nil, e
		}
		if e = c.validateCodingWorkspace(context.Background(), tx, p.ID, request.ProjectID, request.SessionID, workspace, profile); e != nil {
			return nil, nil, e
		}
	}
	task, e := load(tx, request.ProjectID, "Task", request.TaskID)
	if e != nil || qualificationTaskHash(task) != plan["task_hash"] {
		return nil, nil, Fail(412, "STALE_INPUT", "qualification task inputs changed")
	}
	return runtime, task, nil
}

// ValidateLocalQualification is read-only and exposes no token or execution
// capability. The same checks run again under the sole scan lock before Begin.
func (c *RuntimeCoordinator) ValidateLocalQualification(ctx context.Context, ownerToken string, request LocalRuntimeQualificationRequest) error {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, ownerToken)
	if e != nil {
		return e
	}
	_, task, e := c.localQualification(tx, p, request)
	if e == nil {
		e = c.validateLocalConfirmation(ctx, tx, p, request)
	}
	if e == nil && task["status"] != "DRAFT" {
		return Fail(409, "STATE_CONFLICT", "qualification request was already consumed; no automatic retry")
	}
	return e
}

// ExecuteLocalQualification joins the single coordinator lifecycle. Scan does
// not claim qualification tasks, so a trusted explicit request must bridge
// Begin to RunAdmitted exactly once. Cancellation/recovery never relaunches it.
func (c *RuntimeCoordinator) ExecuteLocalQualification(ctx context.Context, ownerToken string, request LocalRuntimeQualificationRequest) (Object, error) {
	c.scanMu.Lock()
	unlock := true
	defer func() {
		if unlock {
			c.scanMu.Unlock()
		}
	}()
	if c.quiesced || !c.qualificationActive || c.qualificationRequest != request.RequestID {
		return nil, Fail(409, "RESOURCE_BLOCKED", "runtime intake is fenced")
	}
	if !c.startupComplete {
		if e := c.Recover(ctx); e != nil {
			return nil, e
		}
		c.startupComplete = true
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	p, e := authenticate(tx, ownerToken)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	_, task, e := c.localQualification(tx, p, request)
	if e != nil {
		tx.Rollback()
		return nil, e
	}
	if task["status"] != "DRAFT" {
		tx.Rollback()
		return nil, Fail(409, "STATE_CONFLICT", "qualification already consumed; no automatic retry")
	}
	var route RuntimeCoordinatorRoute
	for _, current := range c.runtimeRoutes() {
		if current.ProjectID == request.ProjectID && current.RuntimeID == request.RuntimeID {
			if route.RuntimeID != "" {
				tx.Rollback()
				return nil, errors.New("ambiguous qualification route")
			}
			route = current
		}
	}
	if route.RuntimeID == "" {
		tx.Rollback()
		return nil, Fail(503, "MODEL_UNAVAILABLE", "prepared route unavailable")
	}
	var active int
	e = tx.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.executor_principal_id')=? AND json_extract(body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')`, route.ProjectID, route.ExecutorID).Scan(&active)
	tx.Rollback()
	if e != nil {
		return nil, e
	}
	key := route.ProjectID + "/" + route.ExecutorID
	c.mu.Lock()
	busy := c.active[key]
	c.mu.Unlock()
	if active != 0 || busy {
		return nil, Fail(409, "STATE_CONFLICT", "executor has outstanding work; qualification not started")
	}
	if e = c.authority(ctx, route); e != nil {
		return nil, e
	}
	run, lease, e := c.beginManagedLocalQualification(ctx, ownerToken, request, route.ExecutorID)
	if e != nil {
		return nil, e
	}
	c.mu.Lock()
	c.active[key] = true
	c.mu.Unlock()
	c.workers.Add(1)
	c.scanMu.Unlock()
	unlock = false
	defer c.workers.Done()
	defer func() { c.mu.Lock(); delete(c.active, key); c.mu.Unlock() }()
	return run, c.RunAdmitted(ctx, route, run, lease)
}

func (c *RuntimeCoordinator) beginManagedLocalQualification(ctx context.Context, token string, request LocalRuntimeQualificationRequest, executor string) (Object, string, error) {
	s := c.service
	if e := s.Contracts.Validate("Id", request.RequestID); e != nil {
		return nil, "", e
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, "", e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, request.ProjectID, "OWNER")
	if e != nil {
		return nil, "", e
	}
	if _, _, e = c.localQualification(tx, p, request); e != nil {
		return nil, "", e
	}
	if e = c.validateLocalConfirmation(ctx, tx, p, request); e != nil {
		return nil, "", e
	}
	if e = localQualificationIdle(tx); e != nil {
		return nil, "", e
	}
	var prior string
	e = tx.QueryRow(`SELECT request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:managed-runtime-qualification' AND key=?`, p.ID, request.ProjectID, request.RequestID).Scan(&prior)
	if e == nil {
		return nil, "", Fail(409, "STATE_CONFLICT", "managed qualification request already consumed; no automatic replay")
	}
	if e != sql.ErrNoRows {
		return nil, "", e
	}
	// These are the same Owner, frozen plan, budget and claim gates used by the
	// public trusted Go BeginRuntimeQualification wrapper, in the same transaction
	// as the non-secret request-consumption receipt. No lease enters the receipt.
	run, lease, e := s.beginRuntimeQualification(tx, p, request.ProjectID, request.TaskID, request.RuntimeID, executor)
	if e != nil {
		return nil, "", e
	}
	// Recheck the wall-clock deadline after all claim gates; an expired claim is
	// rolled back together with consumption, even if earlier checks were slow.
	if e = validateLocalConfirmationTime(request); e != nil {
		return nil, "", e
	}
	_, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:managed-runtime-qualification',?,?,201,?,'{}',?)`, p.ID, request.ProjectID, request.RequestID, Hash(request), Bytes(Object{"request_hash": Hash(request), "run_ref": Ref(run, "Run"), "task_id": request.TaskID, "runtime_id": request.RuntimeID}), Now())
	if e != nil {
		return nil, "", e
	}
	return run, lease, tx.Commit()
}

// PreparedLocalQualification is for the privileged managed producer. It emits
// the current immutable identifiers and a short-lived private confirmation
// record without starting work or granting authority.
func (c *RuntimeCoordinator) PreparedLocalQualification(ctx context.Context, ownerToken string, candidate RuntimeSetupCandidate, seconds int) (LocalRuntimeQualificationRequest, error) {
	var request LocalRuntimeQualificationRequest
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return request, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, ownerToken)
	if e != nil {
		return request, e
	}
	record, e := c.service.runtimeSetupConfiguration(ctx, tx, p, candidate, c.config.ClientSchema, c.config.ConfigurationAuthority)
	if e != nil {
		return request, e
	}
	runtime, _, e := c.sessionModel(tx, candidate.ProjectID, candidate.ModelRef)
	if e != nil {
		return request, e
	}
	var taskID string
	if e = tx.QueryRow(`SELECT task FROM runtime_qualification_plans WHERE project=? AND runtime=?`, candidate.ProjectID, runtime["id"]).Scan(&taskID); e != nil {
		return request, e
	}
	plan, hash, _, e := qualificationPlan(tx, candidate.ProjectID, taskID, Str(runtime, "id"))
	if e != nil {
		return request, e
	}
	request = LocalRuntimeQualificationRequest{RequestID: ID(), ProjectID: candidate.ProjectID, SessionID: candidate.SessionID, ModelRef: candidate.ModelRef, RuntimeID: Str(runtime, "id"), TaskID: taskID, PlanHash: hash, ProfileHash: Hash(plan["profile_ref"]), AuthorizePurpose: "mu_turn", PurposeSeconds: seconds}
	request.OwnerHost, request.OwnerPrincipal, request.ConfigurationHash = record.Owner, p.ID, record.ConfigHash
	request.OwnerRoot, e = currentAuthorityRoot(tx, p.ID)
	if e != nil {
		return request, e
	}
	request.SessionHash, e = localConfirmationSessionHash(ctx, tx, request)
	if e != nil {
		return request, e
	}
	issued := time.Now().UTC()
	request.IssuedAt, request.ExpiresAt = issued.Format(time.RFC3339Nano), issued.Add(time.Minute).Format(time.RFC3339Nano)
	_, task, e := c.localQualification(tx, p, request)
	if e != nil {
		return request, e
	}
	if task["status"] != "DRAFT" {
		return request, Fail(409, "STATE_CONFLICT", "qualification already consumed; no automatic retry")
	}
	_, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:qualification-confirmation',?,?,200,?,'{}',?)`, p.ID, request.ProjectID, request.RequestID, Hash(request), Bytes(request), Now())
	if e != nil {
		return request, e
	}
	return request, tx.Commit()
}

// RecordLocalRuntimeAdministration seals provenance of a trusted local action;
// this is not an AcceptanceReceipt and confers no availability.
func (s *Service) RecordLocalRuntimeAdministration(ctx context.Context, token, project string, evidence Object) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return nil, e
	}
	if evidence["schema"] != "researchos.local-runtime-administration.v1" {
		return nil, Fail(422, "GATE_FAILED", "local administration evidence schema required")
	}
	if evidence["action"] == "EXPLICIT_QUALIFICATION_REQUEST" {
		child, root := Str(evidence, "verifier_principal"), Str(evidence, "service_root")
		actual, e := currentAuthorityRoot(tx, child)
		ownerRoot, ownerErr := currentAuthorityRoot(tx, p.ID)
		var parent string
		if e != nil || ownerErr != nil || actual != root || root == ownerRoot || root == child || !runtimeRoleAndGrant(tx, child, project, "VERIFIER") || tx.QueryRow(`SELECT parent FROM orchestration_identity WHERE principal=?`, child).Scan(&parent) != nil || parent != root {
			return nil, Fail(403, "FORBIDDEN", "explicit active independent verifier lineage required")
		}
		anchor := Object{"schema": "researchos.managed-verifier-lineage.v1", "principal": child, "root": root, "project_id": project, "registered_by": p.ID}
		var prior string
		e = tx.QueryRow(`SELECT request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:managed-verifier-lineage' AND key=?`, child, project, child).Scan(&prior)
		if e == sql.ErrNoRows {
			_, e = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,'host:managed-verifier-lineage',?,?,200,?,'{}',?)`, child, project, child, Hash(anchor), Bytes(anchor), Now())
		} else if e == nil && prior != Hash(anchor) {
			e = Fail(403, "FORBIDDEN", "managed verifier original lineage changed")
		}
		if e != nil {
			return nil, e
		}
	}
	a, e := s.serverArtifactMode(tx, project, p.ID, "MANIFEST", "LIVE", Bytes(evidence), Empty())
	if e != nil {
		return nil, e
	}
	return a, tx.Commit()
}

// LocalQualificationReview locates the exact observed LOG and current frozen
// references. The separate verifier must re-read them through its own API grant.
func (s *Service) LocalQualificationReview(ctx context.Context, token string, request LocalRuntimeQualificationRequest, runID string) (Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	if _, e = resourcePrincipal(tx, token, request.ProjectID, "OWNER"); e != nil {
		return nil, e
	}
	run, e := load(tx, request.ProjectID, "Run", runID)
	if e != nil {
		return nil, e
	}
	task, e := load(tx, request.ProjectID, "Task", request.TaskID)
	if e != nil {
		return nil, e
	}
	if run["task_id"] != request.TaskID || run["runtime_id"] != request.RuntimeID || run["status"] != "SETTLED" || task["status"] != "EXECUTION_REPORTED" || task["active_run_id"] != runID {
		return nil, Fail(409, "STATE_CONFLICT", "current settled qualification output required")
	}
	plan, hash, _, e := qualificationPlan(tx, request.ProjectID, request.TaskID, request.RuntimeID)
	if e != nil || hash != request.PlanHash || Hash(plan["profile_ref"]) != request.ProfileHash {
		return nil, Fail(412, "STALE_INPUT", "qualification review plan changed")
	}
	obs, e := runtimeObservation(tx, request.ProjectID, run)
	if e != nil {
		return nil, e
	}
	rows, e := tx.Query(`SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='LOG'`, request.ProjectID, runID)
	if e != nil {
		return nil, e
	}
	logs := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, e
		}
		o, err := Decode([]byte(raw))
		if err != nil {
			rows.Close()
			return nil, err
		}
		logs = append(logs, o)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	var logRef Object
	for _, log := range logs {
		ref := Ref(log, "Artifact")
		if s.runtimeReceipt(tx, request.ProjectID, run, ref, obs) == nil {
			if logRef != nil {
				return nil, errors.New("ambiguous qualification observation logs")
			}
			logRef = ref
		}
	}
	if logRef == nil {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "sealed original qualification observation missing")
	}
	mu, e := s.muTurnSnapshot(tx, request.ProjectID, task, run, task["acceptance_contract"].(map[string]any), obs)
	if e != nil {
		return nil, e
	}
	artifacts := Empty()
	for _, id := range Arr(task, "output_artifact_ids") {
		a, use, err := s.artifactUse(tx, request.ProjectID, run, id.(string), true)
		if err != nil {
			return nil, err
		}
		var raw []byte
		if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, request.ProjectID, use["storage_key"]).Scan(&raw); err != nil {
			return nil, err
		}
		if Digest(raw) != a["content_hash"] {
			return nil, Fail(422, "CONTENT_HASH_MISMATCH", "sealed result changed")
		}
		artifacts = append(artifacts, Object{"artifact": a, "use": use, "bytes": raw})
	}
	snapshot := Object{"task": task, "run": run, "mu_turn": mu, "artifacts": artifacts}
	status, reason := verifyMuTurn(snapshot)
	return Object{"task_ref": Ref(task, "Task"), "run_ref": Ref(run, "Run"), "profile_ref": plan["profile_ref"], "plan_hash": hash, "observation_ref": logRef, "executor_id": run["executor_principal_id"], "epoch": run["lease_epoch"], "verification_snapshot": snapshot, "verification_snapshot_hash": Hash(snapshot), "diagnostic_status": status, "diagnostic_reason": reason}, nil
}

// CheckLocalRuntimeQualification performs the existing deterministic algorithm
// on an immutable broker snapshot inside the separate verifier process. It has
// no database or side effects. The API acceptance authority recomputes it again
// against current authoritative rows, so this result cannot bypass acceptance.
func CheckLocalRuntimeQualification(snapshot Object) (string, string) {
	for _, value := range Arr(snapshot, "artifacts") {
		entry, ok := value.(map[string]any)
		if !ok {
			return "FAIL", "Malformed sealed result snapshot."
		}
		if encoded, ok := entry["bytes"].(string); ok {
			raw, e := base64.StdEncoding.DecodeString(encoded)
			if e != nil {
				return "FAIL", "Malformed sealed result bytes."
			}
			entry["bytes"] = raw
		}
		raw, ok := entry["bytes"].([]byte)
		a, _ := entry["artifact"].(map[string]any)
		size, e := Num(a, "byte_size")
		if !ok || e != nil || int64(len(raw)) != size || Digest(raw) != a["content_hash"] {
			return "FAIL", "Sealed result snapshot digest differs."
		}
	}
	return verifyMuTurn(snapshot)
}
