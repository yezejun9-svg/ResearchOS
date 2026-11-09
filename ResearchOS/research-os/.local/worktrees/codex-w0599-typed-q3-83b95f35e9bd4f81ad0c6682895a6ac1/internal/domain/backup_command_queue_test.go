//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"testing"
)

func queueBackupFixture(t *testing.T) (*fixture, *ClientService, string, string) {
	f, svc, client, sid := queueClientFixture(t)
	for _, mode := range []string{"STEER", "FOLLOW_UP"} {
		reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "snapshot may predate a later send", "attachment_artifact_ids": Empty(), "delivery": mode}))
		if deref(reply.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(reply)))
		}
	}
	// Revocation is legitimate pre-backup workspace state; this fixture tests
	// queue evidence independently from the already-covered filesystem remap.
	if _, err := f.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','REVOKED') WHERE kind='WorkspaceBinding'`); err != nil {
		t.Fatal(err)
	}
	return f, svc, client, sid
}
func TestClientQueueBackupRestorePreservesHistoryAndFencesNoRun(t *testing.T) {
	f, _, _, sid := queueBackupFixture(t)
	key := backupTestKey(t)
	backup, manifest := backupTestCreate(t, f.s, key)
	if manifest.Inventory["command_queue_digest"] == nil {
		t.Fatal("queue not inventoried")
	}
	_, files, err := readBackup(backup, key)
	if err != nil || files["command-queue.json"] == nil {
		t.Fatal("portable queue sidecar absent", err)
	}
	destination := filepath.Join(t.TempDir(), "restore")
	report, err := RestoreBackup(context.Background(), backup, destination, backupOpt(t, f.s, key))
	if err != nil {
		t.Fatal(err)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report.Status)
	}
	db, err := store.Open(filepath.Join(destination, "state.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var unknown, receipts, runs int
	db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='UNKNOWN'`).Scan(&unknown)
	db.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE kind='RESTORE_UNKNOWN'`).Scan(&receipts)
	db.QueryRow(`SELECT count(*) FROM domain_objects WHERE kind='Run'`).Scan(&runs)
	if unknown != 2 || receipts != 2 || runs != 0 {
		t.Fatalf("unknown=%d receipt=%d invented Run=%d", unknown, receipts, runs)
	}
	var fence string
	var restored, explicit int
	db.QueryRow(`SELECT state,restore_fenced FROM client_queue_fences WHERE session_id=?`, sid).Scan(&fence, &restored)
	db.QueryRow(`SELECT resume_requires_explicit_user FROM client_sessions WHERE id=?`, sid).Scan(&explicit)
	if fence != "RECONCILING" || restored != 1 || explicit != 1 {
		t.Fatalf("fence=%s restored=%d explicit=%d", fence, restored, explicit)
	}
	restoredService := &Service{DB: db, Contracts: f.s.Contracts}
	again := filepath.Join(t.TempDir(), "rebackup")
	if _, err = restoredService.CreateBackup(context.Background(), again, key); err != nil {
		t.Fatal(err)
	}
	if _, err = RestoreBackup(context.Background(), again, filepath.Join(t.TempDir(), "restore-again"), backupOpt(t, restoredService, key)); err != nil {
		t.Fatal(err)
	}
}
func TestClientQueueBackupCorruptionFailsClosed(t *testing.T) {
	for _, kind := range []string{"content", "receipt", "foreign-session", "watermark", "orphan", "missing-table", "receipt-chain", "foreign-goal"} {
		t.Run(kind, func(t *testing.T) {
			f, _, _, _ := queueBackupFixture(t)
			switch kind {
			case "missing-table":
				if _, err := f.db.Exec(`DROP TABLE client_control_requests`); err != nil {
					t.Fatal(err)
				}
			case "foreign-goal":
				f.db.Exec(`UPDATE client_command_queue SET goal_id='foreign'`)
			case "receipt-chain":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					var generation, command string
					tx.QueryRow(`SELECT generation,command_id FROM client_command_queue LIMIT 1`).Scan(&generation, &command)
					return appendClientReceipt(tx, f.project, generation, command, "TEST", ID(), Object{"phase": "unknown"}, "missing-prior")
				})
			case "content":
				f.db.Exec(`UPDATE client_command_queue SET content='{}'`)
			case "receipt":
				sourceTx(t, f.db, func(tx *sql.Tx) error {
					var generation string
					tx.QueryRow(`SELECT generation FROM client_queue_fences`).Scan(&generation)
					_, err := tx.Exec(`INSERT INTO client_control_receipts(receipt_id,project,generation,kind,body,body_hash,created_at) VALUES(?,?,?,'TEST','{}','bad',?)`, ID(), f.project, generation, Now())
					return err
				})
			case "foreign-session":
				f.db.Exec(`UPDATE client_queue_fences SET session_id='foreign'`)
			case "watermark":
				f.db.Exec(`UPDATE client_queue_fences SET accepted_through=0`)
			case "orphan":
				f.db.Exec(`UPDATE client_command_queue SET task_id='foreign'`)
			}
			if err := validateBackupQueue(f.db); err == nil {
				t.Fatal("corruption accepted")
			}
			if _, err := f.s.CreateBackup(context.Background(), filepath.Join(t.TempDir(), "backup"), backupTestKey(t)); err == nil {
				t.Fatal("corrupt queue backed up")
			}
		})
	}
}
func TestClientQueueFreshNumberedSchema(t *testing.T) {
	f := setup(t)
	_, sqls, err := preparedUpgradeRelease("../..", 24)
	if err != nil || len(sqls) != 25 {
		t.Fatalf("exact installed schema24 release: %d %v", len(sqls), err)
	}
	want := len(sqls) - 1 // The final entry is the separately pinned additive SQL.
	rows, err := f.db.Query(`SELECT version FROM schema_migrations ORDER BY version`)
	if err != nil {
		t.Fatal(err)
	}
	count := 0
	for rows.Next() {
		count++
		var applied int
		if err = rows.Scan(&applied); err != nil || applied != count {
			rows.Close()
			t.Fatalf("noncontiguous installed migration %d: %d %v", count, applied, err)
		}
	}
	if err = rows.Err(); err != nil || count != want {
		rows.Close()
		t.Fatalf("installed migration count=%d want=%d %v", count, want, err)
	}
	rows.Close()
	var version int
	if err := f.db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&version); err != nil || version != want {
		t.Fatalf("migration=%d %v", version, err)
	}
	for _, table := range clientQueueTables {
		var n int
		if err := f.db.QueryRow(`SELECT count(*) FROM ` + table).Scan(&n); err != nil || n != 0 {
			t.Fatalf("fresh table %s %d %v", table, n, err)
		}
	}
	if raw, err := os.ReadFile("../../migrations/sqlite/0022_client_command_queue.sql"); err != nil || len(raw) == 0 {
		t.Fatal("numbered SQL absent", err)
	}
	configurationEvidenceSnapshot(t, f.db, "fresh-current24")
}

func TestClientQueueHistorical22NumberedSchema(t *testing.T) {
	root := queueUpgradeReleaseFixture(t, 22)
	_, sqls, err := upgradeQueueRelease(root, 22)
	if err != nil || len(sqls) != 23 {
		t.Fatalf("exact historical schema22 release: %d %v", len(sqls), err)
	}
	db, err := store.Open(filepath.Join(t.TempDir(), "numbered22.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	// Only fixed numbered001..022 are applied. This is not a matching startup
	// release: it intentionally lacks the separately installed session/fence.
	for i, raw := range sqls[:22] {
		if _, err = db.Exec(string(raw)); err != nil {
			t.Fatal(err)
		}
		if _, err = db.Exec(`INSERT INTO schema_migrations(version) VALUES(?)`, i+1); err != nil {
			t.Fatal(err)
		}
	}
	var version, count int
	if err = db.QueryRow(`SELECT max(version),count(*) FROM schema_migrations`).Scan(&version, &count); err != nil || version != 22 || count != 22 {
		t.Fatalf("historical migration=%d count=%d %v", version, count, err)
	}
	for _, table := range clientQueueTables {
		var n int
		if err := db.QueryRow(`SELECT count(*) FROM ` + table).Scan(&n); err != nil || n != 0 {
			t.Fatalf("fresh table %s %d %v", table, n, err)
		}
	}
	if raw, err := os.ReadFile(filepath.Join(root, "migrations/sqlite/0022_client_command_queue.sql")); err != nil || len(raw) == 0 {
		t.Fatal("numbered SQL absent", err)
	}
	if err = db.QueryRow(`SELECT count(*) FROM sqlite_master WHERE name IN ('host_model_configurations','host_model_config_heads','client_command_identities','client_sessions')`).Scan(&count); err != nil || count != 0 {
		t.Fatalf("historical22 contains later or additive schema: %d %v", count, err)
	}
	configurationEvidenceSnapshot(t, db, "historical-numbered22")
}

func TestClientQueueBackupAllPhasesAndPendingControl(t *testing.T) {
	f, svc, client, sid := queueBackupFixture(t)
	if _, err := f.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','ACTIVE') WHERE kind='WorkspaceBinding'`); err != nil {
		t.Fatal(err)
	}
	phases := []string{"ENQUEUED", "SENDING", "SDK_ACCEPTED", "CONSUMED", "DROP_REQUESTED", "DROPPED", "UNKNOWN"}
	for i := 2; i < len(phases); i++ {
		reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "phase fixture", "attachment_artifact_ids": Empty(), "delivery": "STEER"}))
		if deref(reply.Status) != "COMPLETED" {
			t.Fatal(string(Bytes(reply)))
		}
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		for i, phase := range phases {
			var generation, command string
			if err := tx.QueryRow(`SELECT generation,command_id FROM client_command_queue WHERE queue_sequence=?`, i+1).Scan(&generation, &command); err != nil {
				return err
			}
			if phase == "ENQUEUED" {
				continue
			}
			receipt := ID()
			if err := appendClientReceipt(tx, f.project, generation, command, "FIXTURE_PHASE", receipt, Object{"phase": phase}, nil); err != nil {
				return err
			}
			if _, err := tx.Exec(`UPDATE client_command_queue SET state=?,last_receipt_id=? WHERE command_id=?`, phase, receipt, command); err != nil {
				return err
			}
		}
		return nil
	})
	var goal string
	f.db.QueryRow(`SELECT goal_id FROM client_sessions WHERE id=?`, sid).Scan(&goal)
	control := queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "state fixture unresolved inputs"})
	reply, _ := goalCommand(t, f, svc, control)
	if deref(reply.Status) != "ACKNOWLEDGED" {
		t.Fatal(string(Bytes(reply)))
	}
	drain, err := f.s.RuntimeDrainSnapshot(context.Background())
	if err != nil || drain.UnresolvedCommands < 2 {
		t.Fatalf("pending noRun drain disappeared %+v %v", drain, err)
	}
	if _, err := f.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','REVOKED') WHERE kind='WorkspaceBinding'`); err != nil {
		t.Fatal(err)
	}
	key := backupTestKey(t)
	backup, _ := backupTestCreate(t, f.s, key)
	dest := filepath.Join(t.TempDir(), "restore")
	if _, err = RestoreBackup(context.Background(), backup, dest, backupOpt(t, f.s, key)); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(filepath.Join(dest, "state.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var consumed, dropped, unknown, pending int
	db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='CONSUMED'`).Scan(&consumed)
	db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='DROPPED'`).Scan(&dropped)
	db.QueryRow(`SELECT count(*) FROM client_command_queue WHERE state='UNKNOWN'`).Scan(&unknown)
	db.QueryRow(`SELECT count(*) FROM client_control_requests WHERE state='RECONCILING'`).Scan(&pending)
	if consumed != 1 || dropped != 2 || unknown != 4 || pending != 1 {
		t.Fatalf("restore terminal history consumed=%d dropped=%d unknown=%d controls=%d", consumed, dropped, unknown, pending)
	}
	if err = validateBackupQueue(db); err != nil {
		t.Fatal(err)
	}
}
func TestClientQueueBackupRequiresMatchingPortableSidecar(t *testing.T) {
	for _, mode := range []string{"missing", "disagreement"} {
		t.Run(mode, func(t *testing.T) {
			f, _, _, _ := queueBackupFixture(t)
			key := backupTestKey(t)
			backup, manifest := backupTestCreate(t, f.s, key)
			kept := []BackupFile{}
			for _, entry := range manifest.Files {
				if entry.Name != "command-queue.json" {
					kept = append(kept, entry)
					continue
				}
				if mode == "disagreement" {
					plain := Bytes(Object{"format": "RESEARCHOS_COMMAND_QUEUE_V1", "client_command_queue": Empty()})
					cipher, err := backupCipher(key)
					if err != nil {
						t.Fatal(err)
					}
					raw, err := backupEncrypt(cipher, manifest.ID, entry.Name, plain)
					if err != nil {
						t.Fatal(err)
					}
					if err = os.WriteFile(filepath.Join(backup, entry.Name+".enc"), raw, 0600); err != nil {
						t.Fatal(err)
					}
					entry.Hash = Digest(plain)
					entry.Size = len(plain)
					kept = append(kept, entry)
				}
			}
			manifest.Files = kept
			manifest.MAC = backupMAC(manifest, key)
			if err := os.WriteFile(filepath.Join(backup, "manifest.json"), Bytes(manifest), 0600); err != nil {
				t.Fatal(err)
			}
			if _, err := RestoreBackup(context.Background(), backup, filepath.Join(t.TempDir(), "restore"), backupOpt(t, f.s, key)); err == nil {
				t.Fatal("authenticated but incomplete/disagreeing queue sidecar accepted")
			}
		})
	}
}
func TestClientQueueFreshInstallRollsBackMissingAdditiveSchema(t *testing.T) {
	for _, mode := range []string{"missing", "corrupt"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			migrationDir := filepath.Join(root, "migrations")
			if err := os.Mkdir(migrationDir, 0700); err != nil {
				t.Fatal(err)
			}
			entries, err := os.ReadDir("../../migrations/sqlite")
			if err != nil {
				t.Fatal(err)
			}
			for _, entry := range entries {
				if entry.IsDir() || entry.Name() == "next_v24_sessions.sql" {
					continue
				}
				raw, err := os.ReadFile(filepath.Join("../../migrations/sqlite", entry.Name()))
				if err != nil {
					t.Fatal(err)
				}
				if err = os.WriteFile(filepath.Join(migrationDir, entry.Name()), raw, 0600); err != nil {
					t.Fatal(err)
				}
			}
			if mode == "corrupt" {
				if err = os.WriteFile(filepath.Join(migrationDir, "next_v24_sessions.sql"), []byte("CREATE TABLE partial_schema(id TEXT); invalid SQL;"), 0600); err != nil {
					t.Fatal(err)
				}
			}
			db, err := store.Open(filepath.Join(root, "state.sqlite"))
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			if err = store.Bootstrap(context.Background(), db, filepath.Join(migrationDir, "0001_bootstrap.sql")); err != nil {
				t.Fatal(err)
			}
			if _, err = New(db, "../../spec/v2.0/contracts", filepath.Join(migrationDir, "0002_domain.sql")); err == nil {
				t.Fatal("missing/corrupt additive schema accepted")
			}
			var version, tables int
			if err = db.QueryRow(`SELECT max(version) FROM schema_migrations`).Scan(&version); err != nil {
				t.Fatal(err)
			}
			if err = db.QueryRow(`SELECT count(*) FROM sqlite_master WHERE type='table' AND name IN ('client_command_queue','client_queue_fences','partial_schema')`).Scan(&tables); err != nil {
				t.Fatal(err)
			}
			if version != 1 || tables != 0 {
				t.Fatalf("partially installed numbered/additive migration: version=%d tables=%d", version, tables)
			}
		})
	}
}
