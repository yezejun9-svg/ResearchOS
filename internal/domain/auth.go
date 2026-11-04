package domain

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"time"
)

type Principal struct {
	ID               string
	DeviceID         string
	Roles            []string
	CanCreateProject bool
	Grants           []Grant
}
type Grant struct {
	ProjectID  string
	TaskID     string
	RunID      string
	Restricted bool
}

// ProvisionPrincipal is a trusted local administrative interface; it is never exposed by HTTP.
func (s *Service) ProvisionPrincipal(ctx context.Context, p Principal) error {
	if e := s.Contracts.Validate("Id", p.ID); e != nil {
		return e
	}
	for _, r := range p.Roles {
		if !safeRole(r) {
			return Fail(400, "INVALID_REQUEST", "unknown role")
		}
	}
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if _, e = tx.Exec("INSERT INTO auth_principals(id,roles,can_create_project) VALUES(?,?,?)", p.ID, string(Bytes(p.Roles)), p.CanCreateProject); e != nil {
		return e
	}
	for _, g := range p.Grants {
		if _, e = tx.Exec("INSERT INTO auth_grants(principal,project,task,run,restricted) VALUES(?,?,?,?,?)", p.ID, g.ProjectID, g.TaskID, g.RunID, g.Restricted); e != nil {
			return e
		}
	}
	return tx.Commit()
}
func (s *Service) IssueCredential(ctx context.Context, principal string, ttl time.Duration) (string, error) {
	if ttl <= 0 || ttl > 15*time.Minute {
		return "", Fail(400, "INVALID_REQUEST", "credential TTL must be at most 15 minutes")
	}
	var b [32]byte
	if _, e := rand.Read(b[:]); e != nil {
		return "", e
	}
	token := hex.EncodeToString(b[:])
	_, e := s.DB.ExecContext(ctx, "INSERT INTO auth_credentials(token_hash,principal,expires_at) VALUES(?,?,?)", Digest([]byte(token)), principal, time.Now().UTC().Add(ttl).Format(time.RFC3339Nano))
	return token, e
}
func (s *Service) RevokePrincipal(ctx context.Context, id string) error {
	_, e := s.DB.ExecContext(ctx, "UPDATE auth_principals SET revoked=1 WHERE id=?", id)
	return e
}
func authenticate(tx *sql.Tx, token string) (Principal, error) {
	p, _, err := authenticateWithCredential(tx, token)
	return p, err
}

func authenticateWithCredential(tx *sql.Tx, token string) (Principal, authenticatedCredential, error) {
	var p Principal
	hash := Digest([]byte(token))
	var roles, expires string
	e := tx.QueryRow("SELECT p.id,p.roles,p.can_create_project,c.expires_at FROM auth_credentials c JOIN auth_principals p ON p.id=c.principal WHERE c.token_hash=? AND c.revoked=0 AND p.revoked=0", hash).Scan(&p.ID, &roles, &p.CanCreateProject, &expires)
	if e != nil {
		return p, authenticatedCredential{}, Fail(401, "UNAUTHENTICATED", "valid credential required")
	}
	t, e := time.Parse(time.RFC3339Nano, expires)
	if e != nil || !time.Now().Before(t) {
		return p, authenticatedCredential{}, Fail(401, "UNAUTHENTICATED", "credential expired")
	}
	if e = json.Unmarshal([]byte(roles), &p.Roles); e != nil {
		return p, authenticatedCredential{}, e
	}
	rows, e := tx.Query("SELECT project,task,run,restricted FROM auth_grants WHERE principal=?", p.ID)
	if e != nil {
		return p, authenticatedCredential{}, e
	}
	defer rows.Close()
	for rows.Next() {
		var g Grant
		if e = rows.Scan(&g.ProjectID, &g.TaskID, &g.RunID, &g.Restricted); e != nil {
			return p, authenticatedCredential{}, e
		}
		p.Grants = append(p.Grants, g)
	}
	if e = rows.Err(); e != nil {
		return p, authenticatedCredential{}, e
	}
	rows.Close()
	if e = constrainRemotePrincipal(tx, &p); e != nil {
		return p, authenticatedCredential{}, e
	}
	return p, authenticatedCredential{principal: p.ID, hash: hash, expiresAt: t}, nil
}
func (p Principal) HasRole(want string) bool {
	for _, r := range p.Roles {
		if r == want {
			return true
		}
	}
	return false
}
func (p Principal) Allowed(project, task, run string, restricted bool) bool {
	for _, g := range p.Grants {
		if g.ProjectID != project || restricted && !g.Restricted {
			continue
		}
		if g.TaskID != "" && g.TaskID != task {
			continue
		}
		if g.RunID != "" && g.RunID != run {
			continue
		}
		return true
	}
	return false
}
