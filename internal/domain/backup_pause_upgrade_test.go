package domain

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"researchos.local/research-os/internal/store"
)

func pauseStorageExec(t *testing.T, db *sql.DB, query string, args ...any) {
	t.Helper()
	if _, err := db.Exec(query, args...); err != nil {
		t.Fatal(err)
	}
}

func pauseStorageSeed(t *testing.T) *sql.DB {
	t.Helper()
	db, _ := configurationDB(t, 25, true)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Run','r',1,'{"status":"RUNNING","task_id":"t","lease_epoch":1}')`)
	pauseStorageExec(t, db, `INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES('p','r',1,'d1','{}','m1','OBSERVED','now','now')`)
	pauseStorageExec(t, db, `INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES('p','t','s','g','OPEN')`)
	pauseStorageExec(t, db, `INSERT INTO runtime_pause_intents(project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,state,created_at,updated_at)
VALUES('p','pause','t','r',1,'s','g','actor','pause-command','request','runtime','d1','m1','identity','input','PAUSE_REQUESTED','now','now')`)
	return db
}

func pauseStorageSeal(t *testing.T, db *sql.DB) {
	t.Helper()
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='CHECKPOINT_SEALED',revision=revision+1,
checkpoint_sequence=6,checkpoint_artifact='a',checkpoint_use_receipt_hash='use1',checkpoint_use_principal='executor',
checkpoint_hash='content',checkpoint_bytes=123,native_session_ref='native',sdk_session_id='sdk',queue_cut=0,
command_ledger_hash='ledger',sdk_watermarks_json='{}',model_calls=1,tool_calls=2,journal_checkpoint_hash='journal',updated_at='sealed'
WHERE project='p' AND pause_id='pause'`)
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=revision+1 WHERE project='p' AND pause_id='pause'`)
}

func TestPauseStorageSchemaAndLegacyBackup(t *testing.T) {
	raw, err := os.ReadFile("../../migrations/sqlite/0025_runtime_pause_activations.sql")
	if err != nil || Digest(raw) != pauseUpgradeSQLHash || Digest(raw) != Digest(backupPauseSQL) {
		t.Fatal("migration/embed/hash mismatch", err)
	}
	for _, version := range []int{22, 23, 24, 25} {
		db, _ := configurationDB(t, version, true)
		if err := validateBackupHostConfiguration(db); err != nil {
			t.Fatalf("host configuration schema%d: %v", version, err)
		}
		if err := validateBackupPause(db); err != nil {
			t.Fatalf("pause schema%d: %v", version, err)
		}
		state, err := backupPauseState(db)
		if err != nil || (state != nil) != (version == 25) {
			t.Fatalf("wrong version projection %d: %v", version, err)
		}
		if version == 25 && backupPreparedAbandonmentSchema(db) == nil {
			t.Fatal("old exact24 upgrade gate weakened")
		}
	}
}

func TestPauseStorageIsolated24To25Rehearsal(t *testing.T) {
	source, _ := configurationDB(t, 24, true)
	pauseStorageExec(t, source, `INSERT INTO auth_principals(id,roles,can_create_project) VALUES('retained-owner','["OWNER"]',1)`)
	pauseStorageExec(t, source, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Task','history',9,'{ "failure_count":9007199254740993, "status":"FAILED" }')`)
	before, err := preparedUpgradeSnapshot(source)
	if err != nil {
		t.Fatal(err)
	}
	copyPath := filepath.Join(t.TempDir(), "isolated25.sqlite")
	pauseStorageExec(t, source, "VACUUM INTO ?", copyPath)
	copyDB, err := store.Open(copyPath)
	if err != nil {
		t.Fatal(err)
	}
	defer copyDB.Close()
	tx, err := copyDB.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if _, err = tx.Exec(string(backupPauseSQL)); err != nil {
		t.Fatal(err)
	}
	if _, err = tx.Exec("INSERT INTO schema_migrations(version) VALUES(25)"); err != nil {
		t.Fatal(err)
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	afterSource, err := preparedUpgradeSnapshot(source)
	if err != nil || !reflect.DeepEqual(before, afterSource) {
		t.Fatal("source database changed", err)
	}
	afterCopy, err := preparedUpgradeSnapshot(copyDB)
	if err != nil {
		t.Fatal(err)
	}
	for name, rows := range before {
		if name != "schema_migrations" && !reflect.DeepEqual(rows, afterCopy[name]) {
			t.Fatalf("existing storage changed: %s", name)
		}
	}
	if err := backupPauseSchema(copyDB); err != nil {
		t.Fatal(err)
	}
	// Source authority cannot be upgraded by simply opening a newer release.
	files, err := filepath.Glob("../../migrations/sqlite/[0-9][0-9][0-9][0-9]_*.sql")
	if err != nil {
		t.Fatal(err)
	}
	if err := CheckMigrationSafety(source, files); err == nil || !strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED") {
		t.Fatalf("populated original24 opened for automatic migration: %v", err)
	}
}

func TestPauseStorageSnapshotAndCancelFences(t *testing.T) {
	db := pauseStorageSeed(t)
	for _, query := range []string{
		`UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=2`,
		`UPDATE runtime_pause_intents SET epoch=2,revision=2`,
		`UPDATE runtime_pause_intents SET revision=3`,
		`DELETE FROM runtime_pause_intents`,
	} {
		if _, err := db.Exec(query); err == nil {
			t.Fatalf("invalid original pause mutation accepted: %s", query)
		}
	}
	pauseStorageSeal(t, db)
	for _, field := range []string{"model_calls=0", "checkpoint_hash='other'", "sdk_watermarks_json='{" + `"cleared":true` + "}'", "checkpoint_use_principal='other'", "journal_checkpoint_hash='other'"} {
		if _, err := db.Exec(`UPDATE runtime_pause_intents SET revision=revision+1,` + field); err == nil {
			t.Fatalf("sealed state mutated: %s", field)
		}
	}
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='CANCELLED',revision=revision+1`)
	if _, err := db.Exec(`UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=revision+1`); err == nil {
		t.Fatal("cancelled pause resurrected")
	}
}

func TestPauseStorageSuccessorAndReceiptCAS(t *testing.T) {
	db := pauseStorageSeed(t)
	pauseStorageSeal(t, db)
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='RESUME_PREPARED',successor_epoch=2,revision=revision+1`)
	pauseStorageExec(t, db, `INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES('p','r',2,'d2','{}','m2','PREPARED','now','now')`)
	activation := `INSERT INTO runtime_checkpoint_activations(project,run,epoch,previous_epoch,pause_id,task,session_id,generation,principal,request_key,request_hash,dispatch_key,manifest_hash,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,carry_use_receipt_hash,carry_use_principal,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,created_at)
VALUES('p','r',2,1,'pause','t','s','g','actor','resume-command','resume-request','d2','m2','a','content','use1','executor','use2','executor','input','native','sdk',0,1,2,'now')`
	pauseStorageExec(t, db, activation)
	if _, err := db.Exec(activation); err == nil {
		t.Fatal("second successor accepted")
	}
	if _, err := db.Exec(`UPDATE runtime_checkpoint_activations SET model_calls=0`); err == nil {
		t.Fatal("activation counter reset")
	}
	for sequence := 1; sequence <= 2; sequence++ {
		body := Object{"project": "p", "pause_id": "pause", "kind": "OBSERVED", "sequence": sequence}
		var previous any
		if sequence == 2 {
			previous = Hash(Object{"project": "p", "pause_id": "pause", "kind": "OBSERVED", "sequence": 1})
		}
		pauseStorageExec(t, db, `INSERT INTO runtime_pause_receipts(receipt_id,project,pause_id,sequence,kind,body,body_hash,previous_receipt_hash,created_at) VALUES(?,'p','pause',?,'OBSERVED',?,?,?,'now')`, string(rune('a'+sequence)), sequence, string(Bytes(body)), Hash(body), previous)
	}
	if _, err := db.Exec(`INSERT INTO runtime_pause_receipts(receipt_id,project,pause_id,sequence,kind,body,body_hash,previous_receipt_hash,created_at) VALUES('gap','p','pause',4,'OBSERVED','{}','gap-hash','wrong','now')`); err == nil {
		t.Fatal("receipt gap accepted")
	}
	for _, query := range []string{`UPDATE runtime_pause_receipts SET body='{}'`, `DELETE FROM runtime_pause_receipts`} {
		if _, err := db.Exec(query); err == nil {
			t.Fatal("append-only receipt changed")
		}
	}
	// Storage constraints cannot certify fake artifact references as backup proof.
	if err := validateBackupPause(db); err == nil {
		t.Fatal("unbound synthetic checkpoint passed backup integrity")
	}
}

func TestPauseStorageRejectsSchemaDrift(t *testing.T) {
	db, _ := configurationDB(t, 25, true)
	pauseStorageExec(t, db, `DROP TRIGGER runtime_pause_snapshot_frozen`)
	if err := backupPauseSchema(db); err == nil {
		t.Fatal("weakened schema fingerprint accepted")
	}
	old, _ := configurationDB(t, 24, true)
	pauseStorageExec(t, old, string(backupPauseSQL))
	if _, err := backupPauseState(old); err == nil {
		t.Fatal("unversioned pause schema accepted")
	}
}

func TestPauseStorageSealedUseProof(t *testing.T) {
	db, _ := configurationDB(t, 25, true)
	content := []byte(`{"session":"original-sdk","leaseEpoch":1,"followUp":["retained"]}`)
	contentHash := Digest(content)
	use := Object{"project_id": "p", "run_id": "r", "lease_epoch": 1, "principal_id": "executor",
		"storage_key": "checkpoint-upload", "content_hash": contentHash, "byte_size": len(content),
		"artifact_ref": Object{"entity_type": "Artifact", "id": "a", "content_hash": contentHash, "revision": 1}}
	use["receipt_hash"] = Receipt(use)
	pauseStorageExec(t, db, `INSERT INTO auth_principals(id,roles,can_create_project) VALUES('executor','["EXECUTOR"]',0)`)
	pauseStorageExec(t, db, `INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES('checkpoint-upload','p','executor',?,?,'2099-01-01T00:00:00Z',1)`, content, contentHash)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Artifact','a',1,?)`, string(Bytes(Object{"kind": "CHECKPOINT", "content_hash": contentHash})))
	pauseStorageExec(t, db, `INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES('p','a','r',1,'executor','checkpoint-upload',?,?)`, use["receipt_hash"], string(Bytes(use)))
	if err := backupPauseUse(db, "p", "r", int64(1), "a", contentHash, use["receipt_hash"], "executor"); err != nil {
		t.Fatal("bound original use rejected", err)
	}
	if err := backupPauseUse(db, "p", "r", int64(2), "a", contentHash, use["receipt_hash"], "executor"); err == nil {
		t.Fatal("old checkpoint relabelled as new epoch")
	}
	if err := backupPauseUse(db, "p", "r", int64(1), "a", contentHash, use["receipt_hash"], "another-principal"); err == nil {
		t.Fatal("wrong contribution principal accepted")
	}
	configurationBackupMutation(t, db, `UPDATE uploaded_content SET bytes=? WHERE storage_key='checkpoint-upload'`, []byte(strings.Repeat("x", len(content))))
	if err := backupPauseUse(db, "p", "r", int64(1), "a", contentHash, use["receipt_hash"], "executor"); err == nil {
		t.Fatal("stored hash columns hid corrupted same-size checkpoint bytes")
	}
}

// Positive history and rejection regressions adapted from the independent review.
func pauseStorageValidHistory(t *testing.T) (*sql.DB, string, string) {
	db, _ := configurationDB(t, 25, true)
	pauseStorageExec(t, db, `INSERT INTO auth_principals(id,roles) VALUES('actor','["OWNER"]'),('executor','["EXECUTOR"]'),('other-executor','["EXECUTOR"]')`)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Task','t',1,'{}'),('p','Run','r',1,'{"status":"RUNNING","task_id":"t","lease_epoch":2,"executor_principal_id":"executor"}')`)
	pauseStorageExec(t, db, `INSERT INTO client_sessions(id,project_id,revision,created_at,updated_at,task_id,run_id,writer_epoch,writer_client_id,event_watermark,upstream_session_id) VALUES('s','p',1,'now','now','t','r',1,'client',0,'native')`)
	pauseStorageExec(t, db, `INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES('p','t','s','g','OPEN')`)
	pauseStorageExec(t, db, `INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,identity,prepared_at,updated_at) VALUES('p','r',1,'d1','{}','m1','OBSERVED','{}','now','now'),('p','r',2,'d2','{}','m2','PREPARED','{}','now','now')`)
	pauseStorageExec(t, db, `INSERT INTO runtime_pause_intents(project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,state,created_at,updated_at) VALUES('p','pause','t','r',1,'s','g','actor','pause-command','request','runtime','d1','m1',?,'input','PAUSE_REQUESTED','now','now')`, Hash(Object{}))
	content := []byte(`{"session":"sdk","leaseEpoch":1}`)
	contentHash := Digest(content)
	pauseStorageExec(t, db, `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Artifact','a',1,?)`, string(Bytes(Object{"kind": "CHECKPOINT", "content_hash": contentHash})))
	hashes := []string{}
	for i, principal := range []string{"executor", "other-executor"} {
		storage := []string{"old-upload", "new-upload"}[i]
		use := Object{"project_id": "p", "run_id": "r", "lease_epoch": i + 1, "principal_id": principal, "storage_key": storage, "content_hash": contentHash, "byte_size": len(content), "artifact_ref": Object{"entity_type": "Artifact", "id": "a", "content_hash": contentHash, "revision": 1}}
		use["receipt_hash"] = Receipt(use)
		hashes = append(hashes, Str(use, "receipt_hash"))
		pauseStorageExec(t, db, `INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES(?,'p',?,?,?,'2099-01-01T00:00:00Z',1)`, storage, principal, content, contentHash)
		pauseStorageExec(t, db, `INSERT INTO artifact_uses(project,artifact,run,epoch,principal,storage_key,receipt_hash,body) VALUES('p','a','r',?,?,?,?,?)`, i+1, principal, storage, use["receipt_hash"], string(Bytes(use)))
	}
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='CHECKPOINT_SEALED',revision=revision+1,checkpoint_sequence=1,checkpoint_artifact='a',checkpoint_use_receipt_hash=?,checkpoint_use_principal='executor',checkpoint_hash=?,checkpoint_bytes=?,native_session_ref='native',sdk_session_id='sdk',queue_cut=0,command_ledger_hash='ledger',sdk_watermarks_json='{}',model_calls=1,tool_calls=2,journal_checkpoint_hash='journal'`, hashes[0], contentHash, len(content))
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='PAUSED_CONFIRMED',revision=revision+1`)
	pauseStorageWitness(t, db)
	if err := validateBackupPause(db); err != nil {
		t.Fatal("valid paused fixture", err)
	}
	return db, hashes[0], hashes[1]
}

func pauseStorageActivate(t *testing.T, db *sql.DB, oldUse, newUse, actor string) error {
	pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET state='RESUME_PREPARED',successor_epoch=2,revision=revision+1`)
	pauseStorageExec(t, db, `INSERT INTO resource_checkpoint_carries(project,run,epoch,body) VALUES('p','r',2,?)`, string(Bytes(Object{"actor": "actor", "artifact_ref": Object{"entity_type": "Artifact", "id": "a", "content_hash": pauseStorageCheckpointHash(t, db)}, "from_use_receipt_hash": oldUse, "from_epoch": 1, "to_epoch": 2, "new_upload_key": "new-upload", "reason": "CHECKPOINT_CARRY_NOT_NEW_RESULT"})))
	_, err := db.Exec(`INSERT INTO runtime_checkpoint_activations(project,run,epoch,previous_epoch,pause_id,task,session_id,generation,principal,request_key,request_hash,dispatch_key,manifest_hash,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,carry_use_receipt_hash,carry_use_principal,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,created_at)
 SELECT project,run,2,epoch,pause_id,task,session_id,generation,?,'resume-command','resume-request','d2','m2',checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,?,'other-executor',original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,'now' FROM runtime_pause_intents`, actor, newUse)
	if err == nil {
		pauseStorageWitness(t, db)
	}
	return err
}

func pauseStorageCheckpointHash(t *testing.T, db *sql.DB) string {
	t.Helper()
	var hash string
	if err := db.QueryRow(`SELECT checkpoint_hash FROM runtime_pause_intents WHERE pause_id='pause'`).Scan(&hash); err != nil {
		t.Fatal(err)
	}
	return hash
}

func pauseStorageWitness(t *testing.T, db *sql.DB) {
	t.Helper()
	rows, err := configurationBackupRows(db, `SELECT * FROM runtime_pause_intents WHERE project='p' AND pause_id='pause'`)
	if err != nil || len(rows) != 1 {
		t.Fatal(rows, err)
	}
	intent := rows[0]
	var count int
	if err := db.QueryRow(`SELECT count(*) FROM runtime_pause_receipts WHERE project='p' AND pause_id='pause'`).Scan(&count); err != nil {
		t.Fatal(err)
	}
	var previous any
	if count > 0 {
		var hash string
		if err := db.QueryRow(`SELECT body_hash FROM runtime_pause_receipts WHERE project='p' AND pause_id='pause' AND sequence=?`, count).Scan(&hash); err != nil {
			t.Fatal(err)
		}
		previous = hash
	}
	body := Object{"project": "p", "pause_id": "pause", "kind": "STATE_TRANSITION", "sequence": count + 1, "state": intent["state"], "revision": intent["revision"], "intent_hash": Hash(intent)}
	pauseStorageExec(t, db, `INSERT INTO runtime_pause_receipts(receipt_id,project,pause_id,sequence,kind,body,body_hash,previous_receipt_hash,created_at) VALUES(?,'p','pause',?,'STATE_TRANSITION',?,?,?,'now')`, fmt.Sprintf("witness-%d", count+1), count+1, string(Bytes(body)), Hash(body), previous)
}

func TestPauseStorageCancelRequestedRejectsSuccessor(t *testing.T) {
	db, oldUse, newUse := pauseStorageValidHistory(t)
	pauseStorageExec(t, db, `UPDATE domain_objects SET body=json_set(body,'$.status','CANCEL_REQUESTED') WHERE kind='Run'`)
	if err := pauseStorageActivate(t, db, oldUse, newUse, "actor"); err == nil {
		t.Fatal("cancel-requested execution acquired successor")
	}
}

func TestPauseStorageActivationAndCarryProvenance(t *testing.T) {
	for _, mutation := range []string{"", "missing-actor", "carry-actor", "carry-upload", "carry-artifact", "carry-hash", "carry-principal", "upload-principal"} {
		name := mutation
		if name == "" {
			name = "valid"
		}
		t.Run(name, func(t *testing.T) {
			db, oldUse, newUse := pauseStorageValidHistory(t)
			actor := "actor"
			if mutation == "missing-actor" {
				actor = "absent"
			}
			if err := pauseStorageActivate(t, db, oldUse, newUse, actor); err != nil {
				t.Fatal(err)
			}
			switch mutation {
			case "carry-actor":
				pauseStorageExec(t, db, `UPDATE resource_checkpoint_carries SET body=json_set(body,'$.actor','absent')`)
			case "carry-upload":
				pauseStorageExec(t, db, `UPDATE resource_checkpoint_carries SET body=json_set(body,'$.new_upload_key','absent')`)
			case "carry-artifact":
				pauseStorageExec(t, db, `UPDATE resource_checkpoint_carries SET body=json_set(body,'$.artifact_ref.id','absent')`)
			case "carry-hash":
				pauseStorageExec(t, db, `UPDATE resource_checkpoint_carries SET body=json_set(body,'$.artifact_ref.content_hash','wrong')`)
			case "carry-principal":
				configurationBackupMutation(t, db, `UPDATE artifact_uses SET principal='executor' WHERE epoch=2`)
			case "upload-principal":
				configurationBackupMutation(t, db, `UPDATE uploaded_content SET principal='executor' WHERE storage_key='new-upload'`)
			}
			err := validateBackupPause(db)
			if mutation == "" && err != nil {
				t.Fatal("valid historical carry rejected", err)
			}
			if mutation != "" && err == nil {
				t.Fatal("invalid provenance accepted", mutation)
			}
		})
	}
}

func TestPauseStorageCurrentStateWitnessRequired(t *testing.T) {
	for _, mutation := range []string{"missing", "stale", "intent-hash", "state", "sequence"} {
		t.Run(mutation, func(t *testing.T) {
			db, _, _ := pauseStorageValidHistory(t)
			if mutation == "missing" {
				configurationBackupMutation(t, db, `DELETE FROM runtime_pause_receipts`)
			}
			if mutation == "stale" {
				pauseStorageExec(t, db, `UPDATE runtime_pause_intents SET revision=revision+1,updated_at='later'`)
			}
			if mutation == "intent-hash" || mutation == "state" || mutation == "sequence" {
				rows, err := configurationBackupRows(db, `SELECT * FROM runtime_pause_receipts WHERE sequence=1`)
				if err != nil {
					t.Fatal(err)
				}
				var body Object
				if err := json.Unmarshal([]byte(Str(rows[0], "body")), &body); err != nil {
					t.Fatal(err)
				}
				if mutation == "intent-hash" {
					body["intent_hash"] = "wrong"
				}
				if mutation == "state" {
					body["state"] = "PAUSE_REQUESTED"
				}
				if mutation == "sequence" {
					body["sequence"] = 7
				}
				configurationBackupMutation(t, db, `UPDATE runtime_pause_receipts SET body=?,body_hash=? WHERE sequence=1`, string(Bytes(body)), Hash(body))
			}
			if err := validateBackupPause(db); err == nil {
				t.Fatal("missing or mismatched state witness accepted", mutation)
			}
		})
	}
}
