package store

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"
)

func TestOwnedStopOnlineBackupWALAndLogicalCAS(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "source", "owned.sqlite")
	if err := os.Mkdir(filepath.Dir(source), 0700); err != nil {
		t.Fatal(err)
	}
	db, err := sql.Open("sqlite", ownedStopURI(source, "rwc"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if _, err = db.Exec(`PRAGMA journal_mode=WAL; CREATE TABLE records(k TEXT PRIMARY KEY,b BLOB); INSERT INTO records VALUES('a',x'00ff')`); err != nil {
		t.Fatal(err)
	}
	backup := filepath.Join(root, "private-backup.sqlite")
	base, digest, err := OnlineOwnedStopBackup(context.Background(), source, backup)
	if err != nil {
		t.Fatal(err)
	}
	if digest == "" || base.QuickCheck != "ok" || base.Rows != 1 {
		t.Fatalf("incomplete backup: %+v %q", base, digest)
	}
	if _, _, err = OnlineOwnedStopBackup(context.Background(), source, backup); err == nil {
		t.Fatal("backup overwritten")
	}
	if _, err = db.Exec(`INSERT INTO records VALUES('b',x'0100')`); err != nil {
		t.Fatal(err)
	}
	b, err := AcquireOwnedStopBarrier(context.Background(), source)
	if err != nil {
		t.Fatal(err)
	}
	defer b.Close()
	now, err := b.Census(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if now.SHA256 == base.SHA256 || now.Rows != 2 {
		t.Fatal("committed WAL drift not seen by barrier")
	}
}
