//go:build windows

package host

import (
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	_ "modernc.org/sqlite"
	"researchos.local/research-os/internal/auth"
)

func TestOwnedCoreStopPublicIdentitySameSIDOwnerAndSchema(t *testing.T) {
	root := t.TempDir()
	hostDir := filepath.Join(root, "host")
	if err := os.Mkdir(hostDir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := privateDir(hostDir); err != nil {
		t.Fatal(err)
	}
	identity, err := auth.Current()
	if err != nil {
		t.Fatal(err)
	}
	state := hostState{Version: 1, PrincipalRef: identity.Ref, PrincipalID: "owner-fixture", HostInstanceID: "host-fixture"}
	raw, err := json.Marshal(state)
	if err != nil {
		t.Fatal(err)
	}
	statePath := filepath.Join(hostDir, stateFile)
	if err = os.WriteFile(statePath, raw, 0600); err != nil {
		t.Fatal(err)
	}
	if err = privateFile(statePath); err != nil {
		t.Fatal(err)
	}
	db, err := sql.Open("sqlite", filepath.Join(root, "researchos.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err = db.Exec(`CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY);CREATE TABLE auth_principals(id TEXT PRIMARY KEY,roles TEXT,revoked INTEGER);CREATE TABLE orchestration_identity(principal TEXT PRIMARY KEY,root TEXT)`); err != nil {
		t.Fatal(err)
	}
	for i := 1; i <= 24; i++ {
		if _, err = db.Exec(`INSERT INTO schema_migrations VALUES(?)`, i); err != nil {
			t.Fatal(err)
		}
	}
	if _, err = db.Exec(`INSERT INTO auth_principals VALUES('owner-fixture','["OWNER"]',0);INSERT INTO orchestration_identity VALUES('owner-fixture','root-fixture')`); err != nil {
		t.Fatal(err)
	}
	public, err := ReadOwnedCoreStopPublicIdentity(context.Background(), root)
	if err != nil {
		t.Fatal(err)
	}
	if public.OwnerID != "owner-fixture" || public.OwnerRoot != "root-fixture" || public.HostID != "host-fixture" || public.SchemaVersion != 24 || public.DatabaseIndex == 0 || public.SID == "" {
		t.Fatalf("incomplete public authority: %+v", public)
	}
	if _, err = db.Exec(`UPDATE auth_principals SET revoked=1`); err != nil {
		t.Fatal(err)
	}
	if _, err = ReadOwnedCoreStopPublicIdentity(context.Background(), root); err == nil {
		t.Fatal("revoked owner accepted")
	}
}
