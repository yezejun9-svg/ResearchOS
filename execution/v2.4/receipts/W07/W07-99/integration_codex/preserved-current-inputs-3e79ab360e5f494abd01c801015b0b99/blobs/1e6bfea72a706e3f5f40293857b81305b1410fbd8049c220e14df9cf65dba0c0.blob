package domain

import (
	"context"
	"database/sql"
	"time"
)

// AuthorizeRuntimePurpose is a trusted local Owner action. It authorizes a
// qualified immutable profile for one task purpose, never a URL or command.
func (s *Service) AuthorizeRuntimePurpose(ctx context.Context, token, project, runtimeID, purpose string, expires time.Time) error {
	if purpose == "" || !expires.After(time.Now()) {
		return Fail(422, "GATE_FAILED", "bounded owner purpose required")
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	p, e := resourcePrincipal(tx, token, project, "OWNER")
	if e != nil {
		return e
	}
	runtime, e := load(tx, project, "RuntimeRegistration", runtimeID)
	if e != nil {
		return e
	}
	admission, e := s.currentRuntimeAdmission(tx, project, nil, runtime, []any{"start"}, "authorize")
	if e != nil {
		return e
	}
	if admission["legacy_fixture"] == true {
		return Fail(422, "GATE_FAILED", "qualified immutable profile required")
	}
	qualificationExpiry, e := time.Parse(time.RFC3339Nano, Str(admission, "expires_at"))
	if e != nil || expires.After(qualificationExpiry) {
		return Fail(422, "GATE_FAILED", "purpose cannot outlive qualification")
	}
	grant := Object{"runtime_id": runtimeID, "profile_hash": admission["profile_hash"], "technical_hash": admission["technical_hash"], "qualification_hash": Hash(runtime["qualification_ids"]), "purpose": purpose, "authorized_by": p.ID, "authorized_at": Now(), "expires_at": expires.UTC().Format(time.RFC3339Nano), "mode": admission["mode"]}
	_, e = tx.Exec("INSERT INTO resource_route_grants(project,runtime,purpose,body) VALUES(?,?,?,?) ON CONFLICT(project,runtime,purpose) DO UPDATE SET body=excluded.body", project, runtimeID, purpose, string(Bytes(grant)))
	if e != nil {
		return e
	}
	return tx.Commit()
}

func (s *Service) currentRuntimePurpose(tx *sql.Tx, project string, task, runtime, profileRef Object) (Object, error) {
	var raw string
	if e := tx.QueryRow("SELECT body FROM resource_route_grants WHERE project=? AND runtime=? AND purpose=?", project, runtime["id"], task["task_type"]).Scan(&raw); e != nil {
		return nil, Fail(403, "FORBIDDEN", "current owner purpose permission required")
	}
	grant, e := Decode([]byte(raw))
	if e != nil {
		return nil, e
	}
	expiry, e := time.Parse(time.RFC3339Nano, Str(grant, "expires_at"))
	if e != nil || !expiry.After(time.Now()) || grant["profile_hash"] != Hash(profileRef) || grant["technical_hash"] != runtimeTechnicalHash(runtime) || grant["qualification_hash"] != Hash(runtime["qualification_ids"]) || grant["purpose"] != task["task_type"] || grant["runtime_id"] != runtime["id"] || grant["mode"] != runtime["measurement_mode"] {
		return nil, Fail(412, "STALE_INPUT", "runtime purpose permission expired or changed")
	}
	if !runtimeRoleAndGrant(tx, Str(grant, "authorized_by"), project, "OWNER") {
		return nil, Fail(403, "FORBIDDEN", "purpose owner role or project grant revoked")
	}
	return grant, nil
}
