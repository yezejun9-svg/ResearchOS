//go:build windows

package supervisor

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"

	_ "modernc.org/sqlite"
)

func TestReleaseOperationSQLTransitions(t *testing.T) {
	db, e := sql.Open("sqlite", ":memory:")
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	b, e := os.ReadFile(filepath.Join("..", "..", "migrations", "sqlite", "0019_evolution_release_operations.sql"))
	if e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(string(b)); e != nil {
		t.Fatal(e)
	}
	admission := releaseHash("admission")
	reject := func(label, query string, args ...any) {
		t.Helper()
		if _, err := db.Exec(query, args...); err == nil {
			t.Fatalf("%s accepted", label)
		}
	}
	reject("direct PROJECTED insertion", `INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status,receipt_digest,projection_revision) VALUES('p2','c2','PROMOTE','terminal',1,?,'e2','PROJECTED',?,1)`, admission, releaseHash("raw"))
	reject("fractional epoch", `INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES('p2','c2','PROMOTE','fractional',0.5,?,'e2','PREPARED')`, admission)
	insert := `INSERT INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES('project','candidate','START_CANARY','operation',1,?, 'effect','PREPARED')`
	if _, e = db.Exec(insert, admission); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(insert, admission); e == nil {
		t.Fatal("duplicate operation accepted")
	}
	reject("REPLACE primary identity", `INSERT OR REPLACE INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES('project','candidate','START_CANARY','replacement',1,?,'replacement-effect','PREPARED')`, admission)
	reject("REPLACE operation ID", `INSERT OR REPLACE INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES('p2','c2','PROMOTE','operation',1,?,'e2','PREPARED')`, admission)
	reject("REPLACE effect key", `INSERT OR REPLACE INTO evolution_release_operations(project,candidate,action,operation_id,expected_epoch,admission_hash,effect_key,status) VALUES('p2','c2','PROMOTE','another',1,?,'effect','PREPARED')`, admission)
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='OBSERVED',receipt_digest=?`, releaseHash("raw")); e == nil {
		t.Fatal("PREPARED skipped dispatch")
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET admission_hash=?`, releaseHash("forged")); e == nil {
		t.Fatal("admission replaced")
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='DISPATCHED'`); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='FAILED'`); e == nil {
		t.Fatal("uncertain dispatch marked failed")
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='OBSERVED'`); e == nil {
		t.Fatal("raw receipt omitted")
	}
	receipt := releaseHash("raw")
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='OBSERVED',receipt_digest=?`, receipt); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET receipt_digest=?`, releaseHash("alternate")); e == nil {
		t.Fatal("sealed receipt replaced")
	}
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='PROJECTED'`); e == nil {
		t.Fatal("projection revision omitted")
	}
	reject("fractional projection revision", `UPDATE evolution_release_operations SET status='PROJECTED',projection_revision=0.5`)
	if _, e = db.Exec(`UPDATE evolution_release_operations SET status='PROJECTED',projection_revision=1`); e != nil {
		t.Fatal(e)
	}
	if _, e = db.Exec(`DELETE FROM evolution_release_operations`); e == nil {
		t.Fatal("release operation deleted")
	}
	var status, gotReceipt string
	var revision int
	if e = db.QueryRow(`SELECT status,receipt_digest,projection_revision FROM evolution_release_operations`).Scan(&status, &gotReceipt, &revision); e != nil || status != "PROJECTED" || gotReceipt != receipt || revision != 1 {
		t.Fatalf("unexpected final operation: %s %s %d %v", status, gotReceipt, revision, e)
	}
}
