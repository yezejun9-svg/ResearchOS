package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"testing"
)

// These assertions exercise the administrative backup/restore implementation
// against native SQLite files. The business records are public test fixtures.
func TestW1801BackupContract(t *testing.T) {
	ctx := context.Background()
	o := orchestrationSetup(t)
	f := o.f
	failed := o.claim(o.task("retain-one-failed-attempt", Empty(), Empty()))
	failed.observe(failed.observation("FAILED", false))
	failed.call("/report", failed.report(Empty(), 0), 200)
	f.token = o.owner
	failedTask := f.read("tasks", Str(failed.task, "id"))
	progressID := Str(failedTask, "no_progress_record_id")

	active := o.claim(o.task("retain-cost-reservation", Empty(), Empty()))
	f.token = o.owner
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	intent, err := f.s.PrepareEffect(ctx, o.owner, f.project, Str(active.run, "id"), "w1801-cost-fixture",
		Object{"fixture": "unsettled cost, no provider call"},
		budgetRequest(active, Str(policy, "id"), "RESERVE", "w1801-cost-fixture", dollars("2.50"), "UPPER_BOUND", nil))
	if err != nil {
		t.Fatal(err)
	}
	if err = f.s.ProvisionPrincipal(ctx, Principal{ID: "w1801-restricted-verifier", Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(failedTask, "id"), Restricted: true}}}); err != nil {
		t.Fatal(err)
	}
	ownerToken := o.owner
	key := backupTestKey(t)
	beforeState := w1801Authority(t, f.db, f.project, progressID, Str(intent, "reservation_id"))
	beforeRows := w1801Rows(t, f.db, f.project)
	beforeGrant := w1801Grant(t, f.db, "w1801-restricted-verifier")
	if beforeState["failure_count"] != int64(1) || beforeState["cost"] != "2.50" || beforeGrant["restricted"] != int64(1) {
		t.Fatalf("production fixture did not establish failure, cost and restricted grant: %v %v", beforeState, beforeGrant)
	}

	var seq int
	var dbName, dbPath string
	if err = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &dbName, &dbPath); err != nil {
		t.Fatal(err)
	}
	if _, err = f.db.Exec("CREATE TABLE backup_w1801_wal_probe(a INTEGER NOT NULL,b INTEGER NOT NULL); INSERT INTO backup_w1801_wal_probe VALUES(0,0)"); err != nil {
		t.Fatal(err)
	}
	if _, err = f.db.Exec("PRAGMA wal_checkpoint(TRUNCATE)"); err != nil {
		t.Fatal(err)
	}
	writer, err := store.Open(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	defer writer.Close()
	if _, err = writer.Exec("PRAGMA wal_autocheckpoint=0"); err != nil {
		t.Fatal(err)
	}
	if _, err = writer.Exec("UPDATE backup_w1801_wal_probe SET a=7,b=7"); err != nil {
		t.Fatal(err)
	}
	wal, err := os.Stat(dbPath + "-wal")
	if err != nil || wal.Size() == 0 {
		t.Fatalf("committed WAL fixture absent: %v", err)
	}
	// A literal copy of the main file omits the newly committed WAL row.
	mainBytes, err := os.ReadFile(dbPath)
	if err != nil {
		t.Fatal(err)
	}
	barePath := filepath.Join(t.TempDir(), "bare.sqlite")
	if err = os.WriteFile(barePath, mainBytes, 0600); err != nil {
		t.Fatal(err)
	}
	bare, err := store.Open(barePath)
	if err != nil {
		t.Fatal(err)
	}
	var bareA, bareB int
	if err = bare.QueryRow("SELECT a,b FROM backup_w1801_wal_probe").Scan(&bareA, &bareB); err != nil {
		bare.Close()
		t.Fatal(err)
	}
	bare.Close()

	keyFile := filepath.Join(t.TempDir(), "separate.key")
	if err = os.WriteFile(keyFile, key, 0600); err != nil {
		t.Fatal(err)
	}
	pack := filepath.Join(t.TempDir(), "encrypted-backup")
	var manifest BackupManifest
	if err = json.Unmarshal(w1801BackupCLI(t, "create", "--db", dbPath, "--out", pack, "--key-file", keyFile), &manifest); err != nil {
		t.Fatal(err)
	}
	verified, _, err := readBackup(pack, key)
	if err != nil || verified.ID != manifest.ID {
		t.Fatalf("encrypted manifest verification failed: %v", err)
	}
	target := filepath.Join(t.TempDir(), "restored")
	var report RestoreReport
	if err = json.Unmarshal(w1801BackupCLI(t, "restore", "--backup", pack, "--out", target, "--key-file", keyFile), &report); err != nil {
		t.Fatal(err)
	}
	restored, err := store.Open(filepath.Join(target, "state.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	var restoredA, restoredB int
	if err = restored.QueryRow("SELECT a,b FROM backup_w1801_wal_probe").Scan(&restoredA, &restoredB); err != nil {
		t.Fatal(err)
	}
	backupAssert(t, "W18-01-WAL-OMISSION", true,
		bareA == 0 && bareB == 0 && restoredA == 7 && restoredB == 7,
		Object{"bare_main_file": []int{bareA, bareB}, "restored_snapshot": []int{restoredA, restoredB}, "wal_bytes_at_snapshot": wal.Size()})

	afterState := w1801Authority(t, restored, f.project, progressID, Str(intent, "reservation_id"))
	afterRows := w1801Rows(t, restored, f.project)
	backupAssert(t, "W18-01-STATE-REVISIONS", beforeRows, afterRows,
		Object{"kinds": []string{"Goal", "Task", "NoProgressRecord", "BudgetLedgerEntry", "BudgetPolicy", "ProjectProfile"}})
	backupAssert(t, "W18-01-COST-FAILURE", beforeState, afterState,
		Object{"failed_task_id": failedTask["id"], "reservation_id": intent["reservation_id"]})
	backupAssert(t, "W18-01-AUTHORIZATION", beforeGrant,
		w1801Grant(t, restored, "w1801-restricted-verifier"), Object{"principal_id": "w1801-restricted-verifier"})
	var restoredCursor int64
	if err = restored.QueryRow("SELECT coalesce(max(sequence),0) FROM outbox").Scan(&restoredCursor); err != nil {
		t.Fatal(err)
	}
	snapshotCursor, cursorErr := Num(manifest.Inventory, "max_event_sequence")
	if cursorErr != nil {
		t.Fatal(cursorErr)
	}
	backupAssert(t, "W18-01-MANIFEST-CURSOR", true,
		manifest.Inventory["max_event_sequence"] == report.Before["max_event_sequence"] &&
			restoredCursor >= snapshotCursor &&
			manifest.Inventory["entity_revision_digest"] == report.Before["entity_revision_digest"],
		Object{"snapshot_cursor": manifest.Inventory["max_event_sequence"], "restored_cursor": restoredCursor, "snapshot_database_sha256": w1801FileHash(t, pack, "state.sqlite.enc")})

	materialExposed := false
	entries, err := os.ReadDir(pack)
	if err != nil {
		t.Fatal(err)
	}
	for _, entry := range entries {
		raw, readErr := os.ReadFile(filepath.Join(pack, entry.Name()))
		if readErr != nil {
			t.Fatal(readErr)
		}
		materialExposed = materialExposed || bytes.Contains(raw, []byte(ownerToken)) || bytes.Contains(raw, key)
	}
	backupAssert(t, "W18-01-NO-PLAINTEXT-CREDENTIAL", false, materialExposed,
		Object{"encrypted_file_count": len(manifest.Files), "key_stored_separately": true})

	// Migration operates on an unpublished restoration copy. A failed SQL trial
	// must not change the source or consume the last good encrypted package.
	manifestHash := w1801FileHash(t, pack, "manifest.json")
	allSourceBefore, err := upgradeRows(f.db)
	if err != nil {
		t.Fatal(err)
	}
	negative := filepath.Join(t.TempDir(), "failed-trial")
	options := backupOpt(t, f.s, key)
	options.Migration = func(_ context.Context, copy *sql.DB) error {
		if _, e := copy.Exec("CREATE TABLE w1801_partial_migration(x)"); e != nil {
			return e
		}
		return errors.New("public fixture migration failure")
	}
	_, err = RestoreBackup(ctx, pack, negative, options)
	_, targetStatErr := os.Stat(negative)
	var sourcePartial int
	if sourceErr := f.db.QueryRow("SELECT count(*) FROM sqlite_master WHERE name='w1801_partial_migration'").Scan(&sourcePartial); sourceErr != nil {
		t.Fatal(sourceErr)
	}
	backupAssert(t, "W18-01-MIGRATION-ROLLBACK", true,
		err != nil && os.IsNotExist(targetStatErr) && sourcePartial == 0 && manifestHash == w1801FileHash(t, pack, "manifest.json"),
		Object{"failed_copy_published": !os.IsNotExist(targetStatErr), "source_mutated": sourcePartial != 0, "stable_package_hash": manifestHash})
	allSourceAfter, err := upgradeRows(f.db)
	if err != nil {
		t.Fatal(err)
	}
	backupAssert(t, "W18-01-SOURCE-STABLE", Hash(allSourceBefore), Hash(allSourceAfter),
		Object{"source_db": "fixture native SQLite file; original remains open", "tables_compared": len(allSourceBefore)})
	backupEvidence(t, "w1801-snapshot-report.json", Object{"manifest": manifest, "report": report,
		"encrypted_database_hash":  w1801FileHash(t, pack, "state.sqlite.enc"),
		"key_or_token_in_evidence": false, "scope": "native Windows SQLite/WAL; fixture business rows; no external provider"})
}

func w1801Rows(t *testing.T, db *sql.DB, project string) Object {
	t.Helper()
	out := Object{}
	for _, kind := range []string{"Goal", "Task", "NoProgressRecord", "BudgetLedgerEntry", "BudgetPolicy", "ProjectProfile"} {
		rows, err := db.Query("SELECT body FROM domain_objects WHERE project=? AND kind=? ORDER BY id", project, kind)
		if err != nil {
			t.Fatal(err)
		}
		values := []any{}
		for rows.Next() {
			var raw string
			if err = rows.Scan(&raw); err != nil {
				rows.Close()
				t.Fatal(err)
			}
			values = append(values, raw)
		}
		if err = rows.Err(); err != nil {
			rows.Close()
			t.Fatal(err)
		}
		rows.Close()
		out[kind] = Object{"count": len(values), "digest": Hash(values)}
	}
	return out
}

func w1801Authority(t *testing.T, db *sql.DB, project, progressID, reservationID string) Object {
	t.Helper()
	var failure int64
	if err := db.QueryRow("SELECT json_extract(body,'$.same_failure_count') FROM domain_objects WHERE project=? AND kind='NoProgressRecord' AND id=?", project, progressID).Scan(&failure); err != nil {
		t.Fatal(err)
	}
	var cost string
	if err := db.QueryRow("SELECT json_extract(body,'$.money.amount') FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND id=?", project, reservationID).Scan(&cost); err != nil {
		t.Fatal(err)
	}
	var policyRevision int64
	if err := db.QueryRow("SELECT json_extract(body,'$.policy_revision') FROM domain_objects WHERE project=? AND kind='ProjectState'", project).Scan(&policyRevision); err != nil {
		t.Fatal(err)
	}
	return Object{"failure_count": failure, "cost": cost, "policy_revision": policyRevision}
}

func w1801Grant(t *testing.T, db *sql.DB, id string) Object {
	t.Helper()
	var roles, project, task, run string
	var create, revoked, restricted int64
	if err := db.QueryRow(`SELECT p.roles,p.can_create_project,p.revoked,g.project,g.task,g.run,g.restricted
		FROM auth_principals p JOIN auth_grants g ON g.principal=p.id WHERE p.id=?`, id).
		Scan(&roles, &create, &revoked, &project, &task, &run, &restricted); err != nil {
		t.Fatal(err)
	}
	return Object{"roles": roles, "can_create_project": create, "revoked": revoked, "project": project, "task": task, "run": run, "restricted": restricted}
}

func w1801FileHash(t *testing.T, dir, name string) string {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(dir, name))
	if err != nil {
		t.Fatal(err)
	}
	return Digest(raw)
}

func w1801BackupCLI(t *testing.T, args ...string) []byte {
	t.Helper()
	goExe := os.Getenv("RESEARCHOS_GO")
	if goExe == "" {
		var err error
		goExe, err = exec.LookPath("go")
		if err != nil {
			t.Fatal("RESEARCHOS_GO required for production backup CLI test")
		}
	}
	cmd := exec.Command(goExe, append([]string{"run", "./ops/backup"}, args...)...)
	cmd.Dir = "../.."
	raw, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("backup CLI %s failed: %v; output=%s", args[0], err, raw)
	}
	return raw
}
