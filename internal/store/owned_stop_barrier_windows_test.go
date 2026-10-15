//go:build windows

package store

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func ownedStopFixtureDB(t *testing.T) (string, *sql.DB) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "owned.sqlite")
	db, err := sql.Open("sqlite", ownedStopURI(path, "rwc"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	if _, err = db.Exec(`PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; CREATE TABLE ledger(id TEXT PRIMARY KEY, payload BLOB NOT NULL); INSERT INTO ledger VALUES('one',x'0001ff')`); err != nil {
		t.Fatal(err)
	}
	return path, db
}

func TestOwnedStopBarrierNativeQueryOnlyAndReservedWriter(t *testing.T) {
	path, db := ownedStopFixtureDB(t)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	b, err := AcquireOwnedStopBarrier(ctx, path)
	if err != nil {
		t.Fatal(err)
	}
	defer b.Close()
	before, err := b.Census(ctx)
	if err != nil {
		t.Fatal(err)
	}
	for _, stmt := range []string{
		`INSERT INTO ledger VALUES('bad',x'ff')`, `UPDATE ledger SET payload=x'11'`,
		`DELETE FROM ledger`, `CREATE TABLE injection(id INTEGER)`, `DROP TABLE ledger`,
	} {
		if _, err = b.conn.ExecContext(ctx, stmt); err == nil {
			t.Fatalf("SQLite query_only permitted %q", stmt)
		}
	}
	other, err := sql.Open("sqlite", ownedStopURI(path, "rw"))
	if err != nil {
		t.Fatal(err)
	}
	defer other.Close()
	start := time.Now()
	if _, err = other.ExecContext(ctx, `INSERT INTO ledger VALUES('blocked',x'01')`); err == nil {
		t.Fatal("writer reservation lost after query_only")
	}
	if time.Since(start) < 50*time.Millisecond {
		t.Log("writer returned busy without waiting, lock still verified")
	}
	var count int
	if err = db.QueryRow(`SELECT count(*) FROM ledger`).Scan(&count); err != nil || count != 1 {
		t.Fatalf("product rows changed: %d %v", count, err)
	}
	after, err := b.Census(ctx)
	if err != nil || after.SHA256 != before.SHA256 {
		t.Fatalf("barrier changed rows: %v %v", after, err)
	}
	if err = b.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err = other.Exec(`INSERT INTO ledger VALUES('after',x'02')`); err != nil {
		t.Fatalf("ROLLBACK did not release lock: %v", err)
	}
}

func TestOwnedStopBarrierIncludesCommitWhileWaiting(t *testing.T) {
	path, db := ownedStopFixtureDB(t)
	core, err := db.Conn(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	defer core.Close()
	if _, err = core.ExecContext(context.Background(), "BEGIN IMMEDIATE"); err != nil {
		t.Fatal(err)
	}
	if _, err = core.ExecContext(context.Background(), `INSERT INTO ledger VALUES('late',x'03')`); err != nil {
		t.Fatal(err)
	}
	got := make(chan *OwnedStopBarrier, 1)
	errs := make(chan error, 1)
	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
		defer cancel()
		b, e := AcquireOwnedStopBarrier(ctx, path)
		if e != nil {
			errs <- e
		} else {
			got <- b
		}
	}()
	time.Sleep(100 * time.Millisecond)
	if _, err = core.ExecContext(context.Background(), "COMMIT"); err != nil {
		t.Fatal(err)
	}
	select {
	case err = <-errs:
		t.Fatal(err)
	case b := <-got:
		defer b.Close()
		c, e := b.Census(context.Background())
		if e != nil || c.Rows != 2 {
			t.Fatalf("late committed row omitted: %+v %v", c, e)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("barrier acquisition timed out")
	}
}

func TestOwnedStopBarrierMissingFileNoCreate(t *testing.T) {
	path := filepath.Join(t.TempDir(), "missing.sqlite")
	if b, err := AcquireOwnedStopBarrier(context.Background(), path); err == nil || b != nil {
		t.Fatal("missing source accepted")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("missing file was created: %v", err)
	}
}
