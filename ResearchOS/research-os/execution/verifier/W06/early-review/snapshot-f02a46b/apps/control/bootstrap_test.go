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
