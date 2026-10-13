package domain

import (
	"database/sql"
	_ "embed"
	"encoding/json"
	"fmt"
	"sort"
	"sync"
)

// This is the new storage contract only. A populated original schema24 database
// still requires matching-program backup and a separate reviewed upgrade entry.
const pauseUpgradeSQLHash = "sha256:6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0"

//go:embed contracts/runtime_pause_activations.sql
var backupPauseSQL []byte

var pauseTables = []string{"runtime_pause_intents", "runtime_checkpoint_activations", "runtime_pause_receipts"}
var pauseSchemaOnce sync.Once
var pauseSchemaExpected []Object
var pauseSchemaError error

const pauseSchemaQuery = `SELECT type,name,tbl_name,sql FROM sqlite_master
WHERE tbl_name IN ('runtime_pause_intents','runtime_checkpoint_activations','runtime_pause_receipts')
OR name LIKE 'runtime_pause_%' OR name LIKE 'runtime_checkpoint_activation_%'
ORDER BY type,name`

func backupPauseSchema(db *sql.DB) error {
	if err := preparedUpgradeVersions(db, 25); err != nil {
		return err
	}
	pauseSchemaOnce.Do(func() {
		if Digest(backupPauseSQL) != pauseUpgradeSQLHash {
			pauseSchemaError = fmt.Errorf("BACKUP_PAUSE_SQL_HASH")
			return
		}
		template, err := sql.Open("sqlite", ":memory:")
		if err != nil {
			pauseSchemaError = err
			return
		}
		defer template.Close()
		template.SetMaxOpenConns(1)
		_, err = template.Exec(`CREATE TABLE runtime_dispatches(project TEXT,run TEXT,epoch INTEGER,PRIMARY KEY(project,run,epoch));
CREATE TABLE client_queue_fences(generation TEXT PRIMARY KEY,state TEXT,restore_fenced INTEGER);
CREATE TABLE domain_objects(project TEXT,kind TEXT,id TEXT,body TEXT);`)
		if err == nil {
			_, err = template.Exec(string(backupPauseSQL))
		}
		if err == nil {
			pauseSchemaExpected, err = configurationBackupRows(template, pauseSchemaQuery)
		}
		pauseSchemaError = err
	})
	if pauseSchemaError != nil {
		return pauseSchemaError
	}
	actual, err := configurationBackupRows(db, pauseSchemaQuery)
	if err != nil {
		return err
	}
	if Hash(actual) != Hash(pauseSchemaExpected) {
		return fmt.Errorf("BACKUP_PAUSE_SCHEMA")
	}
	return nil
}

func backupPausePresent(db *sql.DB) (bool, error) {
	versions, err := backupMigrations(db)
	if err != nil {
		return false, err
	}
	if len(versions) == 0 || len(versions) > 25 {
		return false, fmt.Errorf("BACKUP_PAUSE_VERSION")
	}
	for i, version := range versions {
		if version != i+1 {
			return false, fmt.Errorf("BACKUP_PAUSE_VERSION")
		}
	}
	if len(versions) < 25 {
		rows, err := configurationBackupRows(db, pauseSchemaQuery)
		if err != nil {
			return false, err
		}
		if len(rows) != 0 {
			return false, fmt.Errorf("BACKUP_PAUSE_PREMATURE_SCHEMA")
		}
		return false, nil
	}
	if err := backupPauseSchema(db); err != nil {
		return false, err
	}
	return true, nil
}

func backupPauseState(db *sql.DB) (Object, error) {
	present, err := backupPausePresent(db)
	if err != nil || !present {
		return nil, err
	}
	state := Object{"format": "RESEARCHOS_RUNTIME_PAUSE_V1"}
	for _, table := range pauseTables {
		rows, err := configurationBackupRows(db, "SELECT * FROM "+table)
		if err != nil {
			return nil, err
		}
		sort.Slice(rows, func(i, j int) bool { return Hash(rows[i]) < Hash(rows[j]) })
		state[table] = rows
	}
	return state, nil
}

func validateBackupPause(db *sql.DB) error {
	state, err := backupPauseState(db)
	if err != nil || state == nil {
		return err
	}
	queries := []string{
		`SELECT count(*) FROM runtime_pause_intents p WHERE
NOT EXISTS(SELECT 1 FROM domain_objects t WHERE t.project=p.project AND t.kind='Task' AND t.id=p.task)
OR NOT EXISTS(SELECT 1 FROM domain_objects r WHERE r.project=p.project AND r.kind='Run' AND r.id=p.run AND json_extract(r.body,'$.task_id')=p.task AND json_extract(r.body,'$.lease_epoch')>=p.epoch)
OR NOT EXISTS(SELECT 1 FROM client_sessions s WHERE s.project_id=p.project AND s.id=p.session_id)
OR NOT EXISTS(SELECT 1 FROM client_queue_fences f WHERE f.project=p.project AND f.task_id=p.task AND f.session_id=p.session_id AND f.generation=p.generation)
OR NOT EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=p.project AND d.run=p.run AND d.epoch=p.epoch AND d.dispatch_key=p.dispatch_key AND d.manifest_hash=p.manifest_hash)
OR NOT EXISTS(SELECT 1 FROM auth_principals a WHERE a.id=p.principal)`,
		`SELECT count(*) FROM runtime_pause_intents p WHERE p.checkpoint_hash IS NOT NULL AND
(NOT EXISTS(SELECT 1 FROM artifact_uses u JOIN uploaded_content c ON c.storage_key=u.storage_key
 WHERE u.project=p.project AND u.artifact=p.checkpoint_artifact AND u.run=p.run AND u.epoch=p.epoch
 AND u.principal=p.checkpoint_use_principal AND u.receipt_hash=p.checkpoint_use_receipt_hash
 AND c.project=p.project AND c.sealed=1 AND c.content_hash=p.checkpoint_hash AND length(c.bytes)=p.checkpoint_bytes)
 OR p.queue_cut>(SELECT f.accepted_through FROM client_queue_fences f WHERE f.generation=p.generation))`,
		`SELECT count(*) FROM runtime_checkpoint_activations a WHERE
NOT EXISTS(SELECT 1 FROM runtime_pause_intents p WHERE p.project=a.project AND p.pause_id=a.pause_id
 AND p.task=a.task AND p.run=a.run AND p.epoch=a.previous_epoch AND p.successor_epoch=a.epoch
 AND p.session_id=a.session_id AND p.generation=a.generation AND p.checkpoint_artifact=a.checkpoint_artifact
 AND p.checkpoint_hash=a.checkpoint_hash AND p.checkpoint_use_receipt_hash=a.checkpoint_use_receipt_hash
 AND p.checkpoint_use_principal=a.checkpoint_use_principal AND p.original_input_hash=a.original_input_hash
 AND p.native_session_ref=a.native_session_ref AND p.sdk_session_id=a.sdk_session_id AND p.queue_cut=a.queue_cut
 AND p.model_calls=a.model_calls AND p.tool_calls=a.tool_calls)
OR NOT EXISTS(SELECT 1 FROM runtime_dispatches d WHERE d.project=a.project AND d.run=a.run AND d.epoch=a.epoch AND d.dispatch_key=a.dispatch_key AND d.manifest_hash=a.manifest_hash)
OR NOT EXISTS(SELECT 1 FROM auth_principals p WHERE p.id=a.principal)
OR NOT EXISTS(SELECT 1 FROM auth_principals p WHERE p.id=a.carry_use_principal)
OR NOT EXISTS(SELECT 1 FROM artifact_uses u WHERE u.project=a.project AND u.artifact=a.checkpoint_artifact AND u.run=a.run AND u.epoch=a.epoch AND u.receipt_hash=a.carry_use_receipt_hash AND u.principal=a.carry_use_principal)
OR NOT EXISTS(SELECT 1 FROM resource_checkpoint_carries c JOIN artifact_uses u
 ON u.project=c.project AND u.run=c.run AND u.epoch=c.epoch AND u.artifact=a.checkpoint_artifact
 AND u.receipt_hash=a.carry_use_receipt_hash AND u.principal=a.carry_use_principal
 WHERE c.project=a.project AND c.run=a.run AND c.epoch=a.epoch
 AND json_extract(c.body,'$.actor')=a.principal
 AND json_extract(c.body,'$.artifact_ref.entity_type')='Artifact'
 AND json_extract(c.body,'$.artifact_ref.id')=a.checkpoint_artifact
 AND json_extract(c.body,'$.artifact_ref.content_hash')=a.checkpoint_hash
 AND json_extract(c.body,'$.new_upload_key')=u.storage_key
 AND json_extract(c.body,'$.reason')='CHECKPOINT_CARRY_NOT_NEW_RESULT'
 AND json_extract(c.body,'$.from_use_receipt_hash')=a.checkpoint_use_receipt_hash
 AND json_extract(c.body,'$.from_epoch')=a.previous_epoch AND json_extract(c.body,'$.to_epoch')=a.epoch)`,
		`SELECT count(*) FROM runtime_pause_intents p WHERE p.state IN ('RESUME_PREPARED','RESUMED') AND
NOT EXISTS(SELECT 1 FROM runtime_checkpoint_activations a WHERE a.project=p.project AND a.pause_id=p.pause_id AND a.run=p.run AND a.epoch=p.successor_epoch)`,
		`SELECT count(*) FROM runtime_pause_receipts r WHERE
NOT EXISTS(SELECT 1 FROM runtime_pause_intents p WHERE p.project=r.project AND p.pause_id=r.pause_id)
OR (r.sequence=1 AND r.previous_receipt_hash IS NOT NULL)
OR (r.sequence>1 AND NOT EXISTS(SELECT 1 FROM runtime_pause_receipts p WHERE p.project=r.project AND p.pause_id=r.pause_id AND p.sequence=r.sequence-1 AND p.body_hash=r.previous_receipt_hash))`,
	}
	for _, query := range queries {
		var count int
		if err := db.QueryRow(query).Scan(&count); err != nil {
			return err
		}
		if count != 0 {
			return fmt.Errorf("BACKUP_PAUSE_BINDING: %d invalid rows", count)
		}
	}
	witnesses := map[string]Object{}
	for _, receipt := range state["runtime_pause_receipts"].([]Object) {
		var body Object
		if json.Unmarshal([]byte(Str(receipt, "body")), &body) != nil || Hash(body) != Str(receipt, "body_hash") {
			return fmt.Errorf("BACKUP_PAUSE_RECEIPT_HASH")
		}
		if Str(body, "project") != Str(receipt, "project") || Str(body, "pause_id") != Str(receipt, "pause_id") || Str(body, "kind") != Str(receipt, "kind") || Hash(body["sequence"]) != Hash(receipt["sequence"]) {
			return fmt.Errorf("BACKUP_PAUSE_RECEIPT_IDENTITY")
		}
		if Str(body, "kind") == "STATE_TRANSITION" {
			key := Hash([]any{body["project"], body["pause_id"], body["revision"]})
			if _, exists := witnesses[key]; exists {
				return fmt.Errorf("BACKUP_PAUSE_DUPLICATE_WITNESS")
			}
			witnesses[key] = body
		}
	}
	for _, intent := range state["runtime_pause_intents"].([]Object) {
		// Backup observes a committed transaction: every current state must have
		// a witness of the complete stored projection. A revision trigger alone
		// does not prove the future Core's expected-state CAS or native stop.
		witness := witnesses[Hash([]any{intent["project"], intent["pause_id"], intent["revision"]})]
		if witness == nil || Str(witness, "state") != Str(intent, "state") || Str(witness, "intent_hash") != Hash(intent) {
			return fmt.Errorf("BACKUP_PAUSE_STATE_WITNESS")
		}
		var identity string
		if err := db.QueryRow(`SELECT identity FROM runtime_dispatches WHERE project=? AND run=? AND epoch=?`, intent["project"], intent["run"], intent["epoch"]).Scan(&identity); err != nil {
			return err
		}
		var value Object
		if json.Unmarshal([]byte(identity), &value) != nil || Hash(value) != Str(intent, "process_identity_hash") {
			return fmt.Errorf("BACKUP_PAUSE_PROCESS_IDENTITY")
		}
		if Str(intent, "checkpoint_hash") != "" {
			if err := backupPauseUse(db, intent["project"], intent["run"], intent["epoch"],
				intent["checkpoint_artifact"], intent["checkpoint_hash"], intent["checkpoint_use_receipt_hash"], Str(intent, "checkpoint_use_principal")); err != nil {
				return err
			}
		}
	}
	for _, activation := range state["runtime_checkpoint_activations"].([]Object) {
		if err := backupPauseUse(db, activation["project"], activation["run"], activation["epoch"],
			activation["checkpoint_artifact"], activation["checkpoint_hash"], activation["carry_use_receipt_hash"], Str(activation, "carry_use_principal")); err != nil {
			return err
		}
	}
	return nil
}

// A matching hash column alone is insufficient: retain the sealed bytes and
// recompute the existing artifact-use receipt with its original binding.
func backupPauseUse(db *sql.DB, project, run, epoch, artifact, contentHash, receiptHash any, expectedPrincipal string) error {
	rows, err := db.Query(`SELECT u.principal,u.storage_key,u.body,c.bytes FROM artifact_uses u
JOIN uploaded_content c ON c.storage_key=u.storage_key
JOIN domain_objects a ON a.project=u.project AND a.kind='Artifact' AND a.id=u.artifact
WHERE u.project=? AND u.run=? AND u.epoch=? AND u.artifact=? AND u.receipt_hash=?
AND c.project=u.project AND c.principal=u.principal AND c.sealed=1 AND c.content_hash=?
AND json_extract(a.body,'$.kind')='CHECKPOINT' AND json_extract(a.body,'$.content_hash')=?`,
		project, run, epoch, artifact, receiptHash, contentHash, contentHash)
	if err != nil {
		return err
	}
	defer rows.Close()
	count := 0
	for rows.Next() {
		var principal, storage, raw string
		var content []byte
		if err := rows.Scan(&principal, &storage, &raw, &content); err != nil {
			return err
		}
		count++
		var use Object
		if json.Unmarshal([]byte(raw), &use) != nil || Receipt(use) != receiptHash || use["receipt_hash"] != receiptHash ||
			use["project_id"] != project || use["run_id"] != run || use["principal_id"] != principal || use["storage_key"] != storage ||
			Hash(use["lease_epoch"]) != Hash(epoch) || use["content_hash"] != contentHash || Digest(content) != contentHash ||
			(expectedPrincipal != "" && principal != expectedPrincipal) {
			return fmt.Errorf("BACKUP_PAUSE_USE_PROOF")
		}
		artifactRef, ok := use["artifact_ref"].(map[string]any)
		byteCount, sizeErr := Num(use, "byte_size")
		if !ok || artifactRef["id"] != artifact || artifactRef["entity_type"] != "Artifact" || artifactRef["content_hash"] != contentHash || sizeErr != nil || byteCount != int64(len(content)) {
			return fmt.Errorf("BACKUP_PAUSE_USE_CONTENT")
		}
	}
	if err := rows.Err(); err != nil {
		return err
	}
	if count != 1 {
		return fmt.Errorf("BACKUP_PAUSE_USE_CARDINALITY")
	}
	return nil
}
