//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"time"
)

func localConfirmationSessionHash(ctx context.Context, tx *sql.Tx, r LocalRuntimeQualificationRequest) (string, error) {
	s, e := loadClientSession(ctx, tx, r.SessionID, r.ProjectID)
	if e != nil {
		return "", e
	}
	if s.sealed || s.archived {
		return "", Fail(409, "STATE_CONFLICT", "current open session required")
	}
	return Hash(Object{"id": s.sessionID, "project": s.project, "revision": s.revision, "writer_epoch": s.epoch, "writer": s.writerClientID, "run": s.runID}), nil
}

// Called in the very transaction which claims the Run and consumes the request.
// The immutable private row is intent provenance, not an execution queue.
func validateLocalConfirmationTime(r LocalRuntimeQualificationRequest) error {
	bad := func() error {
		return Fail(412, "STALE_INPUT", "local confirmation expired or its original Host, Owner, session or configuration changed")
	}
	issued, e := time.Parse(time.RFC3339Nano, r.IssuedAt)
	if e != nil {
		return bad()
	}
	expires, e := time.Parse(time.RFC3339Nano, r.ExpiresAt)
	if e != nil {
		return bad()
	}
	now := time.Now().UTC()
	if issued.After(now) || !expires.After(now) || !expires.After(issued) || expires.Sub(issued) > time.Minute {
		return bad()
	}
	return nil
}

func (c *RuntimeCoordinator) validateLocalConfirmation(ctx context.Context, tx *sql.Tx, p Principal, r LocalRuntimeQualificationRequest) error {
	bad := func() error { return Fail(412, "STALE_INPUT", "original qualification confirmation binding changed") }
	root, e := currentAuthorityRoot(tx, p.ID)
	if e != nil || root != r.OwnerRoot || r.OwnerPrincipal != p.ID {
		return bad()
	}
	record, e := c.service.runtimeSetupConfiguration(ctx, tx, p, RuntimeSetupCandidate{ProjectID: r.ProjectID, SessionID: r.SessionID, PrincipalID: p.ID, ModelRef: r.ModelRef}, c.config.ClientSchema, c.config.ConfigurationAuthority)
	if e != nil {
		return e
	}
	if record.Owner != r.OwnerHost || record.ConfigHash != r.ConfigurationHash {
		return bad()
	}
	session, e := localConfirmationSessionHash(ctx, tx, r)
	if e != nil || session != r.SessionHash {
		return bad()
	}
	var hash, body string
	if e = tx.QueryRow(`SELECT request_hash,body FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-confirmation' AND key=?`, p.ID, r.ProjectID, r.RequestID).Scan(&hash, &body); e != nil {
		return bad()
	}
	var original LocalRuntimeQualificationRequest
	if json.Unmarshal([]byte(body), &original) != nil || hash != Hash(r) || Hash(original) != hash {
		return bad()
	}
	return validateLocalConfirmationTime(r)
}

// LoadLocalConfirmation resolves only a previously prepared exact request.
// No caller may replace its session, model, expiry or planned purpose.
func (c *RuntimeCoordinator) LoadLocalConfirmation(ctx context.Context, token, project, id, digest string) (LocalRuntimeQualificationRequest, error) {
	var r LocalRuntimeQualificationRequest
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return r, e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return r, e
	}
	var body, hash string
	e = tx.QueryRow(`SELECT body,request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-confirmation' AND key=?`, p.ID, project, id).Scan(&body, &hash)
	if e != nil || hash != digest || json.Unmarshal([]byte(body), &r) != nil || Hash(r) != hash {
		return r, Fail(412, "STALE_INPUT", "exact original private confirmation required")
	}
	return r, c.validateLocalConfirmation(ctx, tx, p, r)
}

// STATUS remains readable after expiry or a lost reply and never executes.
func (c *RuntimeCoordinator) LocalQualificationStatus(ctx context.Context, token, project, id, digest string) (Object, error) {
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return nil, e
	}
	var body, hash string
	e = tx.QueryRow(`SELECT body,request_hash FROM idempotency WHERE principal=? AND project=? AND operation='host:qualification-confirmation' AND key=?`, p.ID, project, id).Scan(&body, &hash)
	var request LocalRuntimeQualificationRequest
	if e != nil || hash != digest || json.Unmarshal([]byte(body), &request) != nil || Hash(request) != hash {
		return nil, Fail(404, "NOT_FOUND", "original qualification confirmation unavailable")
	}
	root, e := currentAuthorityRoot(tx, p.ID)
	if e != nil || root != request.OwnerRoot {
		return nil, Fail(403, "FORBIDDEN", "original Owner authority unavailable")
	}
	metadata, e := c.config.ConfigurationAuthority.ConfigurationMetadata(ctx, p.ID, "", nil)
	if e != nil || metadata.OwnerHost != request.OwnerHost {
		return nil, Fail(403, "FORBIDDEN", "original Host unavailable")
	}
	out := Object{"request_id": id, "request_hash": hash, "expires_at": request.ExpiresAt, "state": "AWAITING_CONFIRMATION", "consumed": false}
	expires, e := time.Parse(time.RFC3339Nano, request.ExpiresAt)
	if e != nil || !expires.After(time.Now()) {
		out["state"] = "EXPIRED"
	}
	var consumed string
	e = tx.QueryRow(`SELECT body FROM idempotency WHERE principal=? AND project=? AND operation='host:managed-runtime-qualification' AND key=?`, p.ID, project, id).Scan(&consumed)
	if e == sql.ErrNoRows {
		return out, nil
	}
	if e != nil {
		return nil, e
	}
	row, e := Decode([]byte(consumed))
	if e != nil {
		return nil, e
	}
	ref, ok := row["run_ref"].(map[string]any)
	if !ok {
		return nil, Fail(409, "STATE_CONFLICT", "consumed qualification evidence incomplete")
	}
	out["consumed"], out["state"], out["run_ref"] = true, "UNRESOLVED", ref
	run, e := load(tx, project, "Run", Str(ref, "id"))
	if e != nil {
		return out, nil
	}
	out["run_status"] = run["status"]
	if run["status"] == "SETTLED" {
		out["state"] = "EXECUTION_SETTLED"
	}
	runtime, e := load(tx, project, "RuntimeRegistration", request.RuntimeID)
	if e != nil {
		return nil, e
	}
	out["runtime_status"] = runtime["status"]
	// Current evidence and purpose are revalidated, not inferred from a historical
	// AVAILABLE string or from the privileged process's last stdout response.
	if _, e = c.service.currentRuntimeAdmission(tx, project, nil, runtime, []any{"start"}, "session.send"); e == nil {
		if profile, _, err := c.service.currentRuntimeBinding(tx, project, runtime); err == nil {
			if _, e = c.service.currentRuntimePurpose(tx, project, Object{"task_type": "mu_turn"}, runtime, profile); e == nil {
				out["state"] = "QUALIFIED_PURPOSE_AUTHORIZED"
			}
		}
	}
	return out, nil
}

// A settled UNKNOWN-cost ledger is left byte-for-byte intact: it is not an
// unknown external effect. Only original effect/dispatch state resolves that.
func localQualificationIdle(tx *sql.Tx) error {
	for _, query := range []string{
		`SELECT count(*) FROM domain_objects WHERE kind='Run' AND coalesce(json_extract(body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED')`,
		`SELECT count(*) FROM resource_effects x WHERE sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')`,
		`SELECT count(*) FROM runtime_dispatches WHERE state IN ('PREPARED','STARTED','UNKNOWN')`,
	} {
		var n int
		if e := tx.QueryRow(query).Scan(&n); e != nil {
			return e
		}
		if n != 0 {
			return Fail(409, "RESOURCE_BLOCKED", "host has an active Run or unresolved external effect; qualification not started")
		}
	}
	return nil
}

// Offline preparation never enters Scan, advances READY Tasks, or launches a
// worker. This is shared by the private producer and managed startup consumer.
func (c *RuntimeCoordinator) PrepareLocalRuntimeOffline(ctx context.Context) error {
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if c.quiesced || c.qualificationActive {
		return Fail(409, "RESOURCE_BLOCKED", "host runtime is busy")
	}
	if c.config.PrepareLocalRuntime != nil {
		return c.config.PrepareLocalRuntime(ctx, c)
	}
	return nil
}

// BeginLocalQualificationWindow fences ALL routes before checking global idle.
// It stays active through independent acceptance and purpose authorization.
func (c *RuntimeCoordinator) BeginLocalQualificationWindow(ctx context.Context, id string) error {
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if c.quiesced || c.qualificationActive {
		return Fail(409, "RESOURCE_BLOCKED", "host runtime is already fenced")
	}
	previousIntakeClosed := c.intakeClosed.Load()
	c.intakeClosed.Store(true)
	success := false
	defer func() {
		if !success && !c.config.ManagedStartupHold {
			c.intakeClosed.Store(previousIntakeClosed)
		}
	}()
	if !c.startupComplete {
		if e := c.Recover(ctx); e != nil {
			previousIntakeClosed = true
			return e
		}
		c.startupComplete = true
	}
	c.mu.Lock()
	busy := len(c.active) > 0
	c.mu.Unlock()
	if busy {
		return Fail(409, "RESOURCE_BLOCKED", "host has active workers")
	}
	tx, e := c.service.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if e = localQualificationIdle(tx); e != nil {
		return e
	}
	c.qualificationActive, c.qualificationRequest = true, id
	c.config.ManagedStartupHold = false
	success = true
	return nil
}

func (c *RuntimeCoordinator) EndLocalQualificationWindow(ctx context.Context) error {
	c.scanMu.Lock()
	defer c.scanMu.Unlock()
	if !c.qualificationActive || c.quiesced {
		return Fail(409, "STATE_CONFLICT", "no active managed qualification window to settle")
	}
	fenced, e := c.managedQualificationUnsettled(ctx)
	if e != nil || fenced {
		return Fail(409, "RESOURCE_BLOCKED", "managed qualification remains unresolved; dispatch stays fenced and is never replayed")
	}
	c.qualificationActive = false
	c.qualificationRequest = ""
	c.config.ManagedStartupHold = false
	c.intakeClosed.Store(false)
	return nil
}

// Durable business rows restore the fence after a claim/crash. No file or
// manager journal can reset a consumed request, a Run, or an UNKNOWN effect.
func (c *RuntimeCoordinator) managedQualificationUnsettled(ctx context.Context) (bool, error) {
	var n int
	e := c.service.DB.QueryRowContext(ctx, `SELECT count(*) FROM idempotency i LEFT JOIN domain_objects r ON r.project=i.project AND r.kind='Run' AND r.id=json_extract(i.body,'$.run_ref.id') WHERE i.operation='host:managed-runtime-qualification' AND (r.id IS NULL OR coalesce(json_extract(r.body,'$.status'),'UNKNOWN') NOT IN ('SETTLED','FAILED','CANCELLED') OR EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=i.project AND d.run=r.id AND d.state IN ('PREPARED','STARTED','UNKNOWN')) OR EXISTS(SELECT 1 FROM resource_effects x WHERE x.project=i.project AND x.run=r.id AND x.sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(x.body,'$.state') IN ('PREPARED','STARTED','UNKNOWN')))`).Scan(&n)
	return n != 0, e
}
