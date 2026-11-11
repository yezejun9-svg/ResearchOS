package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"path/filepath"
	"reflect"
	"testing"
	"time"

	"researchos.local/research-os/internal/store"
)

func commandAuthFixture(t *testing.T) (*sql.DB, *Service, *ClientService, string) {
	t.Helper()
	db, err := store.Open(filepath.Join(t.TempDir(), "auth.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	s, err := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	if err = s.ProvisionPrincipal(context.Background(), Principal{ID: "command-owner", Roles: []string{"OWNER"}, CanCreateProject: true, Grants: []Grant{{ProjectID: "auth-project", Restricted: true}}}); err != nil {
		t.Fatal(err)
	}
	token, err := s.IssueCredential(context.Background(), "command-owner", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	return db, s, &ClientService{Domain: s}, token
}

func TestCommandAuthContextBindsTransactionServiceAndPrincipal(t *testing.T) {
	db, _, service, token := commandAuthFixture(t)
	legacy, err := AuthenticateToken(context.Background(), db, token)
	if err != nil {
		t.Fatal(err)
	}
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	ctx, principal, err := AuthenticateCommandTx(context.Background(), tx, token, service)
	if err != nil || !reflect.DeepEqual(principal, legacy) {
		t.Fatalf("ordinary credential compatibility: %v", err)
	}
	facts, ok := commandCredentialFromContext(ctx, tx, service, principal.ID)
	if !ok || facts.principal != principal.ID || facts.hash != Digest([]byte(token)) || facts.hash == token || !facts.expiresAt.After(time.Now()) {
		t.Fatal("context did not bind real credential facts")
	}
	for _, tc := range []struct {
		name      string
		ctx       context.Context
		tx        *sql.Tx
		svc       *ClientService
		principal string
	}{
		{"different-tx", ctx, &sql.Tx{}, service, principal.ID},
		{"different-service", ctx, tx, &ClientService{Domain: service.Domain}, principal.ID},
		{"different-principal", ctx, tx, service, "another-owner"},
		{"nil-context", nil, tx, service, principal.ID},
		{"nil-tx", ctx, nil, service, principal.ID},
		{"nil-service", ctx, tx, nil, principal.ID},
		{"no-context", context.Background(), tx, service, principal.ID},
		{"caller-key", context.WithValue(context.Background(), "commandCredentialKey", true), tx, service, principal.ID},
		{"zero-value", context.WithValue(context.Background(), commandCredentialKey{}, commandCredentialContext{}), tx, service, principal.ID},
	} {
		t.Run(tc.name, func(t *testing.T) {
			if _, ok := commandCredentialFromContext(tc.ctx, tc.tx, tc.svc, tc.principal); ok {
				t.Fatal("foreign/empty context acquired authenticated facts")
			}
		})
	}
	raw, err := json.Marshal(facts)
	if err != nil || string(raw) != "{}" {
		t.Fatal("credential facts became a public wire value")
	}
}

func TestCommandAuthContextRejectsInvalidCredentialState(t *testing.T) {
	for _, name := range []string{"missing", "unknown", "revoked-credential", "expired", "bad-expiry", "revoked-principal"} {
		t.Run(name, func(t *testing.T) {
			db, _, service, token := commandAuthFixture(t)
			switch name {
			case "missing":
				token = ""
			case "unknown":
				token = "not-a-real-credential"
			case "revoked-credential":
				if _, e := db.Exec(`UPDATE auth_credentials SET revoked=1`); e != nil {
					t.Fatal(e)
				}
			case "expired":
				if _, e := db.Exec(`UPDATE auth_credentials SET expires_at='2000-01-01T00:00:00Z'`); e != nil {
					t.Fatal(e)
				}
			case "bad-expiry":
				if _, e := db.Exec(`UPDATE auth_credentials SET expires_at='not-time'`); e != nil {
					t.Fatal(e)
				}
			case "revoked-principal":
				if _, e := db.Exec(`UPDATE auth_principals SET revoked=1`); e != nil {
					t.Fatal(e)
				}
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			ctx, p, e := AuthenticateCommandTx(context.Background(), tx, token, service)
			if e == nil || ctx != nil || p.ID != "" {
				t.Fatal("invalid credential produced context")
			}
		})
	}
}

func TestCommandAuthContextReadsUncommittedCallerTransaction(t *testing.T) {
	for _, name := range []string{"credential-revocation", "principal-revocation", "grant-removal"} {
		t.Run(name, func(t *testing.T) {
			db, _, service, token := commandAuthFixture(t)
			tx, err := db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			query := `UPDATE auth_credentials SET revoked=1`
			if name == "principal-revocation" {
				query = `UPDATE auth_principals SET revoked=1`
			}
			if name == "grant-removal" {
				query = `DELETE FROM auth_grants`
			}
			if _, err = tx.Exec(query); err != nil {
				t.Fatal(err)
			}
			ctx, p, err := AuthenticateCommandTx(context.Background(), tx, token, service)
			if name == "grant-removal" {
				if err != nil || ctx == nil || p.Allowed("auth-project", "", "", false) {
					t.Fatalf("uncommitted grant change was ignored: %v", err)
				}
			} else if err == nil || ctx != nil {
				t.Fatal("uncommitted revocation was ignored")
			}
			if err = tx.Rollback(); err != nil {
				t.Fatal(err)
			}
			legacy, err := AuthenticateToken(context.Background(), db, token)
			if err != nil || !legacy.Allowed("auth-project", "", "", true) {
				t.Fatalf("auth helper committed caller changes: %v", err)
			}
		})
	}
}

func TestCommandAuthContextKeepsRemoteConstraints(t *testing.T) {
	for _, name := range []string{"active", "owner-grant-removed", "owner-revoked", "owner-role-removed", "device-revoked"} {
		t.Run(name, func(t *testing.T) {
			db, s, service, _ := commandAuthFixture(t)
			if e := s.ProvisionPrincipal(context.Background(), Principal{ID: "paired-device", Roles: []string{"OWNER"}, CanCreateProject: true, Grants: []Grant{{ProjectID: "auth-project", Restricted: true}}}); e != nil {
				t.Fatal(e)
			}
			if _, e := db.Exec(`INSERT INTO remote_devices(id,owner,body) VALUES('paired-device','command-owner',?)`, string(Bytes(Object{"status": "ACTIVE", "role": "READER"}))); e != nil {
				t.Fatal(e)
			}
			token, e := s.IssueCredential(context.Background(), "paired-device", time.Minute)
			if e != nil {
				t.Fatal(e)
			}
			switch name {
			case "owner-grant-removed":
				_, e = db.Exec(`DELETE FROM auth_grants WHERE principal='command-owner'`)
			case "owner-revoked":
				_, e = db.Exec(`UPDATE auth_principals SET revoked=1 WHERE id='command-owner'`)
			case "owner-role-removed":
				_, e = db.Exec(`UPDATE auth_principals SET roles='["READER"]' WHERE id='command-owner'`)
			case "device-revoked":
				_, e = db.Exec(`UPDATE remote_devices SET body='{"status":"REVOKED","role":"READER"}'`)
			}
			if e != nil {
				t.Fatal(e)
			}
			tx, e := db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			defer tx.Rollback()
			ctx, p, e := AuthenticateCommandTx(context.Background(), tx, token, service)
			if name == "active" || name == "owner-grant-removed" {
				if e != nil || ctx == nil || p.DeviceID != "paired-device" || p.CanCreateProject || !reflect.DeepEqual(p.Roles, []string{"READER"}) || p.Allowed("auth-project", "", "", true) {
					t.Fatalf("remote restrictions changed: %v", e)
				}
				if p.Allowed("auth-project", "", "", false) != (name == "active") {
					t.Fatal("owner/device grants were not intersected")
				}
			} else if e == nil || ctx != nil {
				t.Fatal("unavailable remote authority authenticated")
			}
		})
	}
}
