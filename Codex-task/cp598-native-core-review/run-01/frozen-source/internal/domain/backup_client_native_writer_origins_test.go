package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"researchos.local/research-os/internal/store"
)

func TestPreparedNativeOriginOrdinaryBackupAlwaysUnsupported(t *testing.T) {
	for _, rows := range []bool{false, true} {
		name := "empty"
		if rows {
			name = "populated"
		}
		t.Run(name, func(t *testing.T) {
			f := newNativeOriginFixture(t, true)
			if rows {
				if _, e := f.execute(t, f.create(t, "backup-native"), fixtureNativeRef()); e != nil {
					t.Fatal(e)
				}
			}
			called := false
			e := backupIntegrityPolicy(f.db, &backupPolicy{validate: func(_ *sql.DB) error { called = true; return nil }})
			if e == nil || !strings.Contains(e.Error(), "UNSUPPORTED") || called {
				t.Fatalf("prepared addon bypassed ordinary backup gate: %v", e)
			}
		})
	}
	f := newNativeOriginFixture(t, false)
	if e := rejectPreparedNativeOriginBackup(f.db); e != nil {
		t.Fatal("ordinary no-addon guard changed", e)
	}
}

func TestPreparedNativeOriginHistoricalSnapshotDoesNotRestoreAuthority(t *testing.T) {
	f := newNativeOriginFixture(t, true)
	if _, e := f.execute(t, f.create(t, "snapshot-native"), fixtureNativeRef()); e != nil {
		t.Fatal(e)
	}
	root, e := ValidateClientNativeWriterOriginHistory(context.Background(), f.db, f.client.Doc)
	if e != nil {
		t.Fatal(e)
	}
	var path string
	var seq int
	var name string
	if e = f.db.QueryRow(`SELECT seq,name,file FROM pragma_database_list WHERE name='main'`).Scan(&seq, &name, &path); e != nil {
		t.Fatal(e)
	}
	if _, e = f.db.Exec(`PRAGMA wal_checkpoint(FULL)`); e != nil {
		t.Fatal(e)
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	copyPath := filepath.Join(t.TempDir(), "historical.sqlite")
	if e = os.WriteFile(copyPath, raw, 0600); e != nil {
		t.Fatal(e)
	}
	copyDB, e := store.Open(copyPath)
	if e != nil {
		t.Fatal(e)
	}
	defer copyDB.Close()
	again, e := ValidateClientNativeWriterOriginHistory(context.Background(), copyDB, f.client.Doc)
	if e != nil || again != root {
		t.Fatalf("historical snapshot differs: %v", e)
	}
	if e = rejectPreparedNativeOriginBackup(copyDB); e == nil || !strings.Contains(e.Error(), "UNSUPPORTED") {
		t.Fatal("historical copy became adopted production backup")
	}
	// No live Host map or Native authority was consulted by either inventory.
	f.client.NativeCreateAuthority = nil
	if r, err := f.execute(t, f.create(t, "cold-new-create"), fixtureNativeRef()); err == nil && deref(r.Status) == "COMPLETED" {
		t.Fatal("history inventory recreated current Native authority")
	}
}
