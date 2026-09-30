package main

import (
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
	"testing"
)

func TestW03PrivateOwnerBootstrap(t *testing.T) {
	dir := t.TempDir()
	db, e := store.Open(filepath.Join(dir, "domain.db"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	s, e := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	path := filepath.Join(dir, "private", "owner.json")
	if e = bootstrap(s, path); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	var o map[string]any
	if e = json.Unmarshal(raw, &o); e != nil {
		t.Fatal(e)
	}
	token := o["token"].(string)
	if len(token) != 64 {
		t.Fatal("weak token")
	}
	var hash string
	var roles string
	if e = db.QueryRow("SELECT token_hash FROM auth_credentials").Scan(&hash); e != nil {
		t.Fatal(e)
	}
	if hash != domain.Digest([]byte(token)) {
		t.Fatal("plaintext credential persisted")
	}
	db.QueryRow("SELECT roles FROM auth_principals").Scan(&roles)
	if roles != `["OWNER"]` {
		t.Fatal("bootstrap granted extra roles")
	}
	second := filepath.Join(dir, "private", "second.json")
	if e = bootstrap(s, second); e == nil {
		t.Fatal("second owner created")
	}
	if _, e = os.Stat(second); !os.IsNotExist(e) {
		t.Fatal("failed bootstrap left file")
	}
}

func TestLocalPrincipalCredentialAdministration(t *testing.T) {
	dir := t.TempDir()
	db, e := store.Open(filepath.Join(dir, "domain.db"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	s, e := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	definition := filepath.Join(dir, "principal.json")
	if e = os.WriteFile(definition, []byte(`{"ID":"independent-reviewer","Roles":["VERIFIER"],"Grants":[]}`), 0600); e != nil {
		t.Fatal(e)
	}
	credential := filepath.Join(dir, "private", "reviewer.json")
	if e = adminCredential(s, definition, "", credential); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(credential)
	if e != nil {
		t.Fatal(e)
	}
	value, e := domain.Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	token := domain.Str(value, "token")
	if len(token) != 64 || value["principal_id"] != "independent-reviewer" {
		t.Fatal("credential differs")
	}
	var stored string
	if e = db.QueryRow("SELECT token_hash FROM auth_credentials").Scan(&stored); e != nil || stored != domain.Digest([]byte(token)) {
		t.Fatal("plaintext or absent stored credential")
	}
	if e = adminCredential(s, "", "independent-reviewer", credential); e == nil {
		t.Fatal("existing credential overwritten")
	}
	if e = adminCredential(s, definition, "", filepath.Join(dir, "duplicate.json")); e == nil {
		t.Fatal("existing principal replaced")
	}
	if e = s.RevokePrincipal(context.Background(), "independent-reviewer"); e != nil {
		t.Fatal(e)
	}
	if e = adminCredential(s, "", "independent-reviewer", filepath.Join(dir, "revoked.json")); e == nil {
		t.Fatal("revoked principal renewed")
	}
	if e = os.WriteFile(definition, []byte(`{"ID":"new-reviewer","Roles":["VERIFIER"],"unexpected":true}`), 0600); e != nil {
		t.Fatal(e)
	}
	if e = adminCredential(s, definition, "", filepath.Join(dir, "unknown.json")); e == nil {
		t.Fatal("unknown principal field accepted")
	}
}
