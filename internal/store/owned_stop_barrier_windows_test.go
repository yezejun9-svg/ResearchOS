//go:build windows

package store

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"sort"
	"strings"
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

func ownedStopSchema24Fixture(t *testing.T) (string, *sql.DB, OwnedStopSubject) {
	t.Helper()
	path := filepath.Join(t.TempDir(), "schema24.sqlite")
	db, err := sql.Open("sqlite", ownedStopURI(path, "rwc"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = db.Close() })
	files, err := filepath.Glob(filepath.Join("..", "..", "migrations", "sqlite", "[0-9][0-9][0-9][0-9]_*.sql"))
	if err != nil || len(files) != 24 {
		t.Fatalf("exact schema24 source migration files required: %d %v", len(files), err)
	}
	sort.Strings(files)
	for i, file := range files {
		raw, e := os.ReadFile(file)
		if e != nil {
			t.Fatal(e)
		}
		if _, e = db.Exec(string(raw)); e != nil {
			t.Fatalf("fixture migration %s: %v", file, e)
		}
		if _, e = db.Exec(`INSERT INTO schema_migrations(version) VALUES(?)`, i+1); e != nil {
			t.Fatalf("fixture migration version %d: %v", i+1, e)
		}
	}
	subject := OwnedStopSubject{Project: "fixture-project", Run: "f3dcb996b2e43cf52cba874be7abfc70", Epoch: 1, DispatchKey: "705b11ec99044fef19e85f57e2d2b712", RequestKey: "bc269e772ada7e1bce54439fd080550c"}
	queries := []struct {
		sql  string
		args []any
	}{
		{`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,'Run',?,1,'{"status":"RUNNING"}')`, []any{subject.Project, subject.Run}},
		{`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES(?,?,?,?,'{}','fixture-hash','UNKNOWN','fixture-time','fixture-time')`, []any{subject.Project, subject.Run, subject.Epoch, subject.DispatchKey}},
		{`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?, 'old-model',1,'{"state":"CONFIRMED","payload":{"capability":"MODEL"}}')`, []any{subject.Project, subject.Run}},
		{`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES('fixture-principal',?,'host:managed-runtime-qualification',?,'fixture-hash',202,x'00','{}','fixture-time')`, []any{subject.Project, subject.RequestKey}},
	}
	for _, q := range queries {
		if _, err = db.Exec(q.sql, q.args...); err != nil {
			t.Fatalf("schema24 fixture insert %s: %v", q.sql, err)
		}
	}
	return path, db, subject
}

func TestOwnedStopSchema24SafetyRejectsUnresolvedEffectsAndOtherDispatches(t *testing.T) {
	for _, kind := range []string{"baseline", "prepared-effect", "started-effect", "unknown-effect", "other-prepared-dispatch", "other-running-run"} {
		t.Run(kind, func(t *testing.T) {
			path, db, subject := ownedStopSchema24Fixture(t)
			if strings.HasSuffix(kind, "effect") {
				state := strings.ToUpper(strings.TrimSuffix(kind, "-effect"))
				if _, err := db.Exec(`INSERT INTO resource_effects(project,run,effect_key,sequence,body) VALUES(?,?,?,1,?)`, subject.Project, subject.Run, kind, `{"state":"`+state+`","payload":{"capability":"MODEL"}}`); err != nil {
					t.Fatal(err)
				}
			} else if kind == "other-prepared-dispatch" {
				if _, err := db.Exec(`INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES(?,'other-run',1,'other-key','{}','hash','PREPARED','time','time')`, subject.Project); err != nil {
					t.Fatal(err)
				}
			} else if kind == "other-running-run" {
				if _, err := db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body) VALUES(?,'Run','other-run',1,'{"status":"RUNNING"}')`, subject.Project); err != nil {
					t.Fatal(err)
				}
			}
			barrier, err := AcquireOwnedStopBarrier(context.Background(), path)
			if err != nil {
				t.Fatal(err)
			}
			defer barrier.Close()
			snap, err := barrier.SafetySnapshot(context.Background(), subject)
			if err != nil {
				t.Fatal(err)
			}
			if kind == "baseline" && !snap.ExactOldSubjectSafe() {
				t.Fatalf("exact old RUNNING/UNKNOWN subject rejected: %+v", snap)
			}
			if kind != "baseline" && snap.ExactOldSubjectSafe() {
				t.Fatalf("unresolved %s accepted: %+v", kind, snap)
			}
		})
	}
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
