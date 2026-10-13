//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"

	"researchos.local/research-os/internal/recoveryauthority"
)

// No original-root operation is available through caller JSON alone.
// The native leaf owns the purpose-separated signature, accepted release anchor,
// actual Windows peer/self/root/DB identities, lifetime and held DataRootLease.
func ExecutePauseSchemaUpgrade(ctx context.Context, db *sql.DB, token recoveryauthority.MigrationToken, ownerToken string, pauseOpt PauseSchemaUpgradeOptions) (result Object, err error) {
	opt := pauseOpt.Upgrade
	result = Object{"plan": PauseSchemaUpgradePlan, "status": "DENIED_BEFORE_DDL",
		"committed": false, "automatic_retry": false, "original_restore_called": false,
		"abandonment_performed": false, "provider_requests": nil, "financial_closed": false}
	binding, err := token.Binding()
	if err != nil {
		return result, err
	}
	if binding.PlanID != PauseSchemaUpgradePlan || opt.Plan != binding.PlanID ||
		binding.SQLSHA256 != pauseUpgradeSQLHash {
		return result, fmt.Errorf("PAUSE_UPGRADE_NATIVE_PLAN")
	}
	optionsRaw, err := json.Marshal(pauseOpt)
	if err != nil || Digest(optionsRaw) != binding.OptionsSHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_NATIVE_OPTIONS")
	}
	if err = token.Check(binding); err != nil {
		return result, err
	}
	if db == nil || db.Stats().MaxOpenConnections != 1 {
		return result, fmt.Errorf("PAUSE_UPGRADE_SINGLE_CONNECTION_REQUIRED")
	}
	if err = pauseMigrationPaths(&pauseOpt, true); err != nil {
		return result, err
	}
	if !reflect.DeepEqual(opt, pauseOpt.Upgrade) {
		return result, fmt.Errorf("PAUSE_UPGRADE_CANONICAL_PATHS_REQUIRED")
	}
	// Do not run upgradePaths here: these are reviewed EXISTING backup and
	// rehearsal outputs, not fresh destinations. Reject aliases before reading.
	for _, path := range []string{opt.Source, opt.SourceRoot, opt.TargetRoot, opt.SourceProgram, opt.TargetProgram, opt.KeyFile, opt.Snapshot, opt.Destination} {
		resolved, pathErr := pauseMigrationPath(path, true)
		if pathErr != nil || !filepath.IsAbs(path) || !strings.EqualFold(filepath.Clean(path), resolved) {
			return result, fmt.Errorf("PAUSE_UPGRADE_REVIEWED_PATH_CHANGED")
		}
	}
	for _, path := range []string{opt.KeyFile, opt.Snapshot, opt.Destination} {
		parent := path
		if path == opt.KeyFile {
			parent = filepath.Dir(path)
		}
		if upgradeInside(filepath.Dir(opt.Source), parent) || upgradeInside(parent, filepath.Dir(opt.Source)) {
			return result, fmt.Errorf("PAUSE_UPGRADE_OUTPUT_OVERLAP")
		}
	}
	if !strings.EqualFold(filepath.Clean(binding.Root), filepath.Dir(opt.Source)) ||
		!strings.EqualFold(filepath.Clean(binding.Database), filepath.Clean(opt.Source)) {
		return result, fmt.Errorf("PAUSE_UPGRADE_NATIVE_DATABASE")
	}
	dbs, err := db.QueryContext(ctx, "PRAGMA database_list")
	if err != nil {
		return result, err
	}
	mainPath, databaseCount := "", 0
	for dbs.Next() {
		var sequence int
		var name, path string
		if err = dbs.Scan(&sequence, &name, &path); err != nil {
			dbs.Close()
			return result, err
		}
		if name != "temp" {
			databaseCount++
		}
		if name == "main" {
			mainPath = path
		}
	}
	err = dbs.Err()
	dbs.Close()
	if err != nil || databaseCount != 1 || !strings.EqualFold(filepath.Clean(mainPath), filepath.Clean(opt.Source)) {
		return result, fmt.Errorf("PAUSE_UPGRADE_CONNECTION_IDENTITY")
	}
	var temporaryObjects int
	if err = db.QueryRowContext(ctx, "SELECT count(*) FROM sqlite_temp_master").Scan(&temporaryObjects); err != nil || temporaryObjects != 0 {
		return result, fmt.Errorf("PAUSE_UPGRADE_TEMP_SCHEMA_PROHIBITED")
	}
	// Retained EXCLUSIVE SQLite ownership is separate from the native lease.
	// This no-op transaction establishes it without restore/recovery changes.
	if _, err = db.ExecContext(ctx, "PRAGMA busy_timeout=250; PRAGMA locking_mode=EXCLUSIVE; BEGIN EXCLUSIVE; ROLLBACK;"); err != nil {
		return result, fmt.Errorf("PAUSE_UPGRADE_SOURCE_NOT_OFFLINE: %w", err)
	}
	sourceRelease, _, err := pauseMigrationRelease(opt.SourceRoot, 24)
	if err != nil || Hash(sourceRelease) != binding.SourceInventorySHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_SOURCE_RELEASE_ANCHOR")
	}
	targetRelease, sqls, err := pauseMigrationRelease(opt.TargetRoot, 25)
	if err != nil || Hash(targetRelease) != binding.TargetInventorySHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_TARGET_RELEASE_ANCHOR")
	}
	for relative, digest := range sourceRelease {
		if err = preparedUpgradeRequireFilePin(token, "source-inventory:"+relative,
			filepath.Join(opt.SourceRoot, filepath.FromSlash(relative)), digest.(string)); err != nil {
			return result, err
		}
	}
	for relative, digest := range targetRelease {
		if err = preparedUpgradeRequireFilePin(token, "target-inventory:"+relative,
			filepath.Join(opt.TargetRoot, filepath.FromSlash(relative)), digest.(string)); err != nil {
			return result, err
		}
	}
	programs, err := pauseMigrationProgramHashes(pauseOpt, true)
	sourceProgram, targetProgram := programs.Source, programs.Control
	if err != nil || sourceProgram != binding.SourceReleaseSHA256 || targetProgram != binding.TargetReleaseSHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_NATIVE_PROGRAM_ANCHOR")
	}
	handoff, err := pauseHandoffCheck(pauseOpt, programs)
	if err != nil {
		return result, err
	}
	for _, pin := range []struct{ role, path, hash string }{
		{"target-rehearsal-program", pauseOpt.RehearsalProgram, programs.Rehearsal},
		{"handoff-binding", pauseOpt.HandoffBindingFile, pauseOpt.HandoffBindingSHA256},
		{"backup-producer-stdout", handoff.ProducerStdout.Path, handoff.ProducerStdout.SHA256},
		{"backup-producer-observation", handoff.ProducerObservation.Path, handoff.ProducerObservation.SHA256},
		{"source-program", opt.SourceProgram, sourceProgram},
		{"target-program", opt.TargetProgram, targetProgram},
		{"migration-sql", filepath.Join(opt.TargetRoot, "migrations/sqlite/0025_runtime_pause_activations.sql"), pauseUpgradeSQLHash},
	} {
		if err = preparedUpgradeRequireFilePin(token, pin.role, pin.path, pin.hash); err != nil {
			return result, err
		}
	}
	contracts, err := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if err != nil {
		return result, err
	}
	schemas, err := pauseMigrationTemplate(ctx, sqls, contracts)
	if err != nil {
		return result, err
	}
	if schemas.Source24 != binding.SourceSchemaSHA256 || schemas.Original25 != binding.TargetSchemaSHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_NATIVE_SCHEMA_ANCHOR")
	}
	guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: preparedUpgradeConcreteVerifier()}, contracts: contracts}
	if err = guard.refresh(db); err != nil {
		return result, err
	}
	backupRaw, err := preparedUpgradeReadPin(binding.Backup, filepath.Join(opt.Snapshot, "manifest.json"), "encrypted-backup-manifest")
	if err != nil {
		return result, err
	}
	rehearsalRaw, err := preparedUpgradeReadPin(binding.Rehearsal, filepath.Join(opt.Destination, pauseMigrationReceiptName), "isolated-restore-rehearsal")
	if err != nil {
		return result, err
	}
	var rehearsal pauseMigrationReceipt
	if err = pauseMigrationDecode(rehearsalRaw, &rehearsal); err != nil {
		return result, err
	}
	if rehearsal.Schema != pauseMigrationReceiptSchema ||
		rehearsal.Plan != binding.PlanID || rehearsal.Status != "ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED" ||
		!rehearsal.RollbackVerified || !rehearsal.OriginalUnchanged || !rehearsal.ExistingRowsUnchanged || !rehearsal.NewPauseTablesEmpty ||
		rehearsal.AutomaticPromotion || !reflect.DeepEqual(rehearsal.Options, pauseOpt) || rehearsal.OptionsHash != binding.OptionsSHA256 ||
		rehearsal.RehearsalProgramHash != programs.Rehearsal || rehearsal.HandoffBindingHash != pauseOpt.HandoffBindingSHA256 ||
		rehearsal.ProducerStdout != handoff.ProducerStdout || rehearsal.ProducerObservation != handoff.ProducerObservation ||
		rehearsal.SourceProgramHash != sourceProgram || rehearsal.TargetProgramHash != targetProgram ||
		rehearsal.SourceInventoryHash != Hash(sourceRelease) || rehearsal.TargetInventoryHash != Hash(targetRelease) ||
		rehearsal.SQLHash != pauseUpgradeSQLHash || rehearsal.SourceSchema != schemas.Source24 || rehearsal.TargetSchema != schemas.Original25 ||
		rehearsal.RestoredSchema != schemas.Restored24 || rehearsal.RestoredTargetSchema != schemas.Restored25 ||
		rehearsal.OriginalRowsHash != binding.OriginalRowsSHA256 ||
		rehearsal.BackupManifestHash != Digest(backupRaw) || rehearsal.BackupManifestBytes != int64(len(backupRaw)) ||
		rehearsal.RestoreReport.Status != "RESTORED_RECONCILIATION_REQUIRED" ||
		!backupConfigurationHash.MatchString(rehearsal.PostRestoreRowsHash) || !backupConfigurationHash.MatchString(rehearsal.PostDDLRowsHash) ||
		rehearsal.RestoreDelta == nil || rehearsal.ReleaseAuthority != "RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY" {
		return result, fmt.Errorf("PAUSE_UPGRADE_REHEARSAL_BINDING")
	}
	key, err := os.ReadFile(opt.KeyFile)
	if err != nil || len(key) != 32 {
		return result, fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	manifest, files, err := readBackup(opt.Snapshot, key)
	if err != nil {
		return result, err
	}
	defer func() {
		for _, raw := range files {
			clear(raw)
		}
	}()
	if !reflect.DeepEqual(manifest.Migrations, upgradeVersions(24)) || manifest.SchemaHash != schemas.Source24 ||
		manifest.ID != rehearsal.RestoreReport.BackupID || len(manifest.Purpose) != 0 || manifest.Format != "RESEARCHOS_BACKUP_V1" || manifest.ID != handoff.BackupID {
		return result, fmt.Errorf("PAUSE_UPGRADE_BACKUP_BINDING")
	}
	for _, file := range manifest.Files {
		path := filepath.Join(opt.Snapshot, file.Name+".enc")
		encrypted, readErr := os.ReadFile(path)
		if readErr != nil {
			return result, readErr
		}
		if err = token.RequirePin(recoveryauthority.RawPin{Role: "encrypted-backup-payload:" + file.Name + ".enc",
			Path: path, SHA256: Digest(encrypted), Bytes: int64(len(encrypted))}); err != nil {
			return result, err
		}
	}
	if err = token.Check(binding); err != nil {
		return result, err
	}
	if err = preparedUpgradeVersions(db, 24); err != nil {
		return result, err
	}
	original, err := preparedUpgradeSnapshot(db)
	if err != nil || Hash(original) != binding.OriginalRowsSHA256 {
		return result, fmt.Errorf("PAUSE_UPGRADE_ORIGINAL_DRIFT")
	}
	schema, err := preparedUpgradeSchema(db)
	if err != nil || schema != schemas.Source24 {
		return result, fmt.Errorf("PAUSE_UPGRADE_SOURCE_SCHEMA")
	}
	if err = token.Check(binding); err != nil {
		return result, err
	}
	// An existing intent is a recovery boundary, never an automatic retry.
	receiptDir := opt.Destination + ".original-schema25"
	if _, err = upgradePath(receiptDir, false); err != nil {
		return result, err
	}
	if err = os.Mkdir(receiptDir, 0700); err != nil {
		return result, err
	}
	result["receipt_directory"] = receiptDir
	intent := Object{"schema": "researchos.runtime-pause-schema-migration-intent.v1", "binding": binding,
		"created_at": Now(), "status": "PREPARED_NOT_COMMITTED", "automatic_retry": false,
		"original_rows_sha256": Hash(original), "source_schema_sha256": schema}
	if err = backupWrite(filepath.Join(receiptDir, "migration-intent.json"), Bytes(intent)); err != nil {
		return result, err
	}
	// The native caller also records the result. A durable intent without a
	// final receipt requires inspection of schema/version, not replay.
	defer func() {
		result["finished_at"] = Now()
		if err != nil && result["committed"] == false && result["status"] != "COMMIT_OUTCOME_UNKNOWN" {
			result["status"] = "NOT_COMMITTED"
		}
		if err != nil {
			result["error"] = err.Error()
		}
		writeErr := backupWrite(filepath.Join(receiptDir, "migration-result.json"), Bytes(result))
		if writeErr != nil {
			result["receipt_persistence_error"] = writeErr.Error()
			if err == nil {
				err = fmt.Errorf("PAUSE_UPGRADE_RESULT_PERSISTENCE: %w", writeErr)
			}
		}
	}()
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return result, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return result, err
	}
	owner, err := authenticate(tx, ownerToken)
	if err != nil {
		return result, err
	}
	if !owner.HasRole("OWNER") || !owner.Allowed(binding.ProjectID, "", "", false) {
		return result, Fail(403, "FORBIDDEN", "current project Owner required")
	}
	root, err := authorityRoot(tx, owner.ID)
	if err != nil || root != owner.ID || root != binding.OwnerRoot {
		return result, Fail(403, "FORBIDDEN", "direct local Root Owner required")
	}
	if err = token.Begin(binding); err != nil {
		return result, err
	}
	commitAttempted := false
	defer func() { _ = tx.Rollback(); token.Finish(commitAttempted) }()
	result["status"] = "TRANSACTION_OPEN"
	if err = pauseMigrationDDL(ctx, tx, sqls[24], original, schemas.Source24, schemas.Original25); err != nil {
		result["status"] = "ROLLED_BACK_BEFORE_COMMIT"
		return result, err
	}
	if err = token.Check(binding); err != nil {
		return result, err
	}
	// Recheck public pins before commit; the SQL used above is the already
	// verified immutable byte slice, never reloaded from a mutable path.
	a, _, pinErr := pauseMigrationRelease(opt.SourceRoot, 24)
	if pinErr != nil || Hash(a) != Hash(sourceRelease) {
		return result, fmt.Errorf("PAUSE_UPGRADE_RELEASE_CHANGED")
	}
	b, _, pinErr := pauseMigrationRelease(opt.TargetRoot, 25)
	if pinErr != nil || Hash(b) != Hash(targetRelease) {
		return result, fmt.Errorf("PAUSE_UPGRADE_RELEASE_CHANGED")
	}
	currentPrograms, pinErr := pauseMigrationProgramHashes(pauseOpt, true)
	if pinErr != nil || currentPrograms != programs {
		return result, fmt.Errorf("PAUSE_UPGRADE_PROGRAM_CHANGED")
	}
	currentHandoff, pinErr := pauseHandoffCheck(pauseOpt, programs)
	if pinErr != nil || !reflect.DeepEqual(currentHandoff, handoff) {
		return result, fmt.Errorf("PAUSE_UPGRADE_HANDOFF_CHANGED")
	}
	if pinErr = pauseHandoffVerifyBackup(pauseOpt, key, handoff); pinErr != nil {
		return result, pinErr
	}
	if _, pinErr = preparedUpgradeReadPin(binding.Backup, filepath.Join(opt.Snapshot, "manifest.json"), "encrypted-backup-manifest"); pinErr != nil {
		return result, pinErr
	}
	if _, pinErr = preparedUpgradeReadPin(binding.Rehearsal, filepath.Join(opt.Destination, pauseMigrationReceiptName), "isolated-restore-rehearsal"); pinErr != nil {
		return result, pinErr
	}
	after, err := preparedUpgradeSnapshot(tx)
	if err != nil {
		return result, err
	}
	result["before_rows_sha256"], result["after_rows_sha256"] = Hash(original), Hash(after)
	result["source_schema_sha256"], result["target_schema_sha256"] = schemas.Source24, schemas.Original25
	result["existing_business_rows_unchanged"], result["new_pause_tables_empty"] = true, true
	result["migration_only_adds_version"] = 25
	// A Commit error can have an uncertain durable outcome. Consume the token
	// conservatively and leave the immutable intent for independent inspection.
	commitAttempted = true
	result["status"] = "COMMIT_OUTCOME_UNKNOWN"
	if err = tx.Commit(); err != nil {
		return result, err
	}
	result["status"], result["committed"] = "SCHEMA25_COMMITTED_ORIGINAL_BUSINESS_ROWS_UNCHANGED", true
	result["binding"] = binding
	return result, nil
}
