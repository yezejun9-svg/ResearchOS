//go:build windows

package store

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"sort"
	"testing"
)

func TestOpenQualificationMaintenanceExistingSchema24Only(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "researchos.sqlite")
	if _, err := OpenQualificationMaintenance(context.Background(), path); err == nil {
		t.Fatal("absent database must not be created")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("absent database changed: %v", err)
	}
	db, err := sql.Open("sqlite", ownedStopURI(path, "rwc"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		t.Fatal(err)
	}
	files, err := filepath.Glob(filepath.Join("..", "..", "migrations", "sqlite", "[0-9][0-9][0-9][0-9]_*.sql"))
	if err != nil || len(files) != 24 {
		t.Fatalf("migration fixture unavailable: %d %v", len(files), err)
	}
	sort.Strings(files)
	for i, file := range files {
		raw, readErr := os.ReadFile(file)
		if readErr != nil {
			t.Fatal(readErr)
		}
		if _, err = db.Exec(string(raw)); err != nil {
			t.Fatalf("migration %s: %v", file, err)
		}
		if _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil {
			t.Fatal(err)
		}
	}
	session, err := os.ReadFile(filepath.Join("..", "..", "migrations", "sqlite", "next_v24_sessions.sql"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(session)); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(`CREATE TABLE IF NOT EXISTS backup_restore_barriers(project TEXT NOT NULL,run TEXT NOT NULL,restored_at TEXT NOT NULL,PRIMARY KEY(project,run))`); err != nil {
		t.Fatal(err)
	}
	var tables int
	if err = db.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'`).Scan(&tables); err != nil {
		t.Fatal(err)
	}
	if tables != 87 {
		t.Fatalf("fixture expected 87 application tables, got %d", tables)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	opened, err := OpenQualificationMaintenance(context.Background(), path)
	if err != nil {
		t.Fatal(err)
	}
	selectors := QualificationResidualSelectors{Project: "p", Run: "r", Operation: "op", Principal: "owner",
		UploadKey: "upload", EventID: "event", Epoch: 1, EventSequence: 1,
		ArtifactID: "artifact", ImpactLinkID: "link", StateID: "state", RunRevision: 2, StateRevision: 2,
		ObservationHash: "observation"}
	ctx := context.Background()
	base, err := opened.BeginTx(ctx, &sql.TxOptions{ReadOnly: true})
	if err != nil {
		t.Fatal(err)
	}
	protectedBefore, err := QualificationMaintenanceProtectedCensus(ctx, base)
	if err != nil {
		t.Fatal(err)
	}
	residualBefore, err := QualificationMaintenanceResidualCensus(ctx, base, selectors)
	if err != nil {
		t.Fatal(err)
	}
	if err = base.Rollback(); err != nil {
		t.Fatal(err)
	}
	check := func(sqlText string, wantResidualChange, wantProtectedChange bool) {
		t.Helper()
		tx, err := opened.BeginTx(ctx, nil)
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback()
		if _, err = tx.Exec(sqlText); err != nil {
			t.Fatal(err)
		}
		p, err := QualificationMaintenanceProtectedCensus(ctx, tx)
		if err != nil {
			t.Fatal(err)
		}
		r, err := QualificationMaintenanceResidualCensus(ctx, tx, selectors)
		if err != nil {
			t.Fatal(err)
		}
		if (p != protectedBefore) != wantProtectedChange || (r != residualBefore) != wantResidualChange {
			t.Fatalf("census delta mismatch: protected=%t residual=%t", p != protectedBefore, r != residualBefore)
		}
	}
	check(`INSERT INTO outbox(project,sequence,id,body) VALUES('p',1,'event','{}')`, false, false)
	check(`INSERT INTO outbox(project,sequence,id,body) VALUES('p',2,'unrelated','{}')`, true, false)
	check(`INSERT INTO auth_principals(id,roles) VALUES('outsider','[]')`, false, true)
	if err := opened.Close(); err != nil {
		t.Fatal(err)
	}
}
