package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

type pauseBackupHandoffBinding struct {
	Schema                 string                 `json:"schema"`
	SourceDatabase         string                 `json:"source_database"`
	BackupDirectory        string                 `json:"backup_directory"`
	SourceProgramSHA256    string                 `json:"source_program_sha256"`
	TargetProgramSHA256    string                 `json:"target_program_sha256"`
	RehearsalProgramSHA256 string                 `json:"rehearsal_program_sha256"`
	BackupManifestSHA256   string                 `json:"backup_manifest_sha256"`
	BackupManifestBytes    int64                  `json:"backup_manifest_bytes"`
	BackupID               string                 `json:"backup_id"`
	SourceBackupOperation  string                 `json:"source_backup_operation"`
	ObservedBackupExit     *int                   `json:"observed_backup_exit"`
	ProducerStdout         preparedHandoffFileRef `json:"producer_stdout"`
	ProducerObservation    preparedHandoffFileRef `json:"producer_observation"`
}

type pauseMigrationPrograms struct{ Source, Control, Rehearsal string }

func pauseMigrationDecode(raw []byte, out any) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(out); err != nil {
		return err
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return fmt.Errorf("PAUSE_UPGRADE_TRAILING_DATA")
	}
	return nil
}

func pauseMigrationProgramHashes(opt PauseSchemaUpgradeOptions, currentIsControl bool) (pauseMigrationPrograms, error) {
	var result pauseMigrationPrograms
	for path, dest := range map[string]*string{
		opt.Upgrade.SourceProgram: &result.Source,
		opt.Upgrade.TargetProgram: &result.Control,
		opt.RehearsalProgram:      &result.Rehearsal,
	} {
		raw, err := os.ReadFile(path)
		if err != nil {
			return result, err
		}
		*dest = Digest(raw)
	}
	if result.Source == "" || result.Control == "" || result.Rehearsal == "" || result.Source == result.Control || result.Source == result.Rehearsal || result.Control == result.Rehearsal {
		return result, fmt.Errorf("PAUSE_UPGRADE_DISTINCT_PROGRAMS_REQUIRED")
	}
	program, err := os.Executable()
	if err != nil {
		return result, err
	}
	raw, err := os.ReadFile(program)
	if err != nil {
		return result, err
	}
	want := result.Rehearsal
	if currentIsControl {
		want = result.Control
	}
	if Digest(raw) != want {
		return result, fmt.Errorf("PAUSE_UPGRADE_MATCHING_PROGRAM_REQUIRED")
	}
	return result, nil
}

func pauseMigrationPaths(opt *PauseSchemaUpgradeOptions, existingDestination bool) error {
	u := &opt.Upgrade
	if u.Plan != PauseSchemaUpgradePlan {
		return fmt.Errorf("PAUSE_UPGRADE_PLAN_UNSUPPORTED")
	}
	// Check aliases before normalizing them away. This also requires the
	// explicitly bound staging parent to exist before any filesystem staging.
	if _, err := pauseMigrationStageParent(*opt, filepath.Dir(u.Destination)); err != nil {
		return err
	}
	for _, p := range []*string{&u.Source, &u.Snapshot, &u.KeyFile, &u.SourceRoot, &u.TargetRoot, &u.SourceProgram, &u.TargetProgram, &opt.RehearsalProgram, &opt.HandoffBindingFile} {
		path, err := pauseMigrationPath(*p, true)
		if err != nil {
			return err
		}
		*p = path
	}
	destination, err := pauseMigrationPath(u.Destination, existingDestination)
	if err != nil {
		return err
	}
	u.Destination = destination
	dirs := []string{filepath.Dir(u.Source), filepath.Dir(u.KeyFile), u.Snapshot, u.Destination}
	for i, a := range dirs {
		for _, b := range dirs[i+1:] {
			if upgradeInside(a, b) || upgradeInside(b, a) {
				return fmt.Errorf("PAUSE_UPGRADE_PATH_OVERLAP")
			}
		}
	}
	var infos []os.FileInfo
	for _, path := range []string{u.Source, u.KeyFile, u.SourceProgram, u.TargetProgram, opt.RehearsalProgram, opt.HandoffBindingFile} {
		info, err := os.Stat(path)
		if err != nil || !info.Mode().IsRegular() {
			return fmt.Errorf("PAUSE_UPGRADE_REGULAR_FILE_REQUIRED")
		}
		for _, old := range infos {
			if os.SameFile(old, info) {
				return fmt.Errorf("PAUSE_UPGRADE_FILE_ALIAS")
			}
		}
		infos = append(infos, info)
	}
	for _, path := range []string{u.Snapshot, u.SourceRoot, u.TargetRoot} {
		info, err := os.Stat(path)
		if err != nil || !info.IsDir() {
			return fmt.Errorf("PAUSE_UPGRADE_DIRECTORY_REQUIRED")
		}
	}
	return nil
}

func pauseHandoffMetadata(b pauseBackupHandoffBinding, programs pauseMigrationPrograms, manifest, stdout BackupManifest) error {
	if b.Schema != pauseMigrationHandoffSchema || b.SourceBackupOperation != "create" || b.ObservedBackupExit == nil || *b.ObservedBackupExit != 0 {
		return fmt.Errorf("PAUSE_HANDOFF_OBSERVATION_REQUIRED")
	}
	if !preparedHandoffDigest(programs.Source) || !preparedHandoffDigest(programs.Control) || !preparedHandoffDigest(programs.Rehearsal) ||
		programs.Source == programs.Control || programs.Source == programs.Rehearsal || programs.Control == programs.Rehearsal ||
		b.SourceProgramSHA256 != programs.Source || b.TargetProgramSHA256 != programs.Control || b.RehearsalProgramSHA256 != programs.Rehearsal {
		return fmt.Errorf("PAUSE_HANDOFF_PROGRAM_PINS")
	}
	if b.BackupID == "" || b.BackupID != manifest.ID || manifest.Format != "RESEARCHOS_BACKUP_V1" || len(manifest.Purpose) != 0 || Hash(manifest.Migrations) != Hash(upgradeVersions(24)) {
		return fmt.Errorf("PAUSE_HANDOFF_BACKUP_IDENTITY")
	}
	if Hash(manifest) != Hash(stdout) {
		return fmt.Errorf("PAUSE_HANDOFF_PRODUCER_STDOUT_MISMATCH")
	}
	return nil
}

// Public observation bytes are evidence only. The native issuer must review
// them independently before pinning this binding in a separately signed grant.
func pauseHandoffCheck(opt PauseSchemaUpgradeOptions, programs pauseMigrationPrograms) (pauseBackupHandoffBinding, error) {
	var binding pauseBackupHandoffBinding
	if !preparedHandoffDigest(opt.HandoffBindingSHA256) {
		return binding, fmt.Errorf("PAUSE_HANDOFF_BINDING_PIN_REQUIRED")
	}
	raw, err := os.ReadFile(opt.HandoffBindingFile)
	if err != nil || Digest(raw) != opt.HandoffBindingSHA256 {
		return binding, fmt.Errorf("PAUSE_HANDOFF_BINDING_CHANGED")
	}
	if err = pauseMigrationDecode(raw, &binding); err != nil {
		return binding, err
	}
	for observed, want := range map[string]string{binding.SourceDatabase: opt.Upgrade.Source, binding.BackupDirectory: opt.Upgrade.Snapshot} {
		path, err := pauseMigrationPath(observed, true)
		if err != nil || !strings.EqualFold(path, want) {
			return binding, fmt.Errorf("PAUSE_HANDOFF_SOURCE_OR_BACKUP_PATH")
		}
	}
	manifestRaw, err := os.ReadFile(filepath.Join(opt.Upgrade.Snapshot, "manifest.json"))
	if err != nil || !preparedHandoffDigest(binding.BackupManifestSHA256) || Digest(manifestRaw) != binding.BackupManifestSHA256 || int64(len(manifestRaw)) != binding.BackupManifestBytes {
		return binding, fmt.Errorf("PAUSE_HANDOFF_MANIFEST_CHANGED")
	}
	var manifest, stdout BackupManifest
	if err = pauseMigrationDecode(manifestRaw, &manifest); err != nil {
		return binding, err
	}
	for _, pin := range []preparedHandoffFileRef{binding.ProducerStdout, binding.ProducerObservation} {
		if _, err = pauseMigrationPath(pin.Path, true); err != nil {
			return binding, err
		}
		bytes, readErr := preparedHandoffReadRef(pin)
		if readErr != nil {
			return binding, readErr
		}
		if pin == binding.ProducerStdout {
			if err = pauseMigrationDecode(bytes, &stdout); err != nil {
				return binding, err
			}
		}
	}
	return binding, pauseHandoffMetadata(binding, programs, manifest, stdout)
}

func pauseHandoffVerifyBackup(opt PauseSchemaUpgradeOptions, key []byte, b pauseBackupHandoffBinding) error {
	manifest, files, err := readBackup(opt.Upgrade.Snapshot, key)
	defer func() {
		for _, raw := range files {
			clear(raw)
		}
	}()
	if err != nil {
		return err
	}
	if manifest.ID != b.BackupID || Hash(manifest.Migrations) != Hash(upgradeVersions(24)) {
		return fmt.Errorf("PAUSE_HANDOFF_BACKUP_IDENTITY")
	}
	return nil
}

func UpgradePauseSchemaBackup(ctx context.Context, opt PauseSchemaUpgradeOptions) (RestoreReport, error) {
	return upgradePauseSchemaBackup(ctx, opt, preparedUpgradeConcreteVerifier())
}

func upgradePauseSchemaBackup(ctx context.Context, opt PauseSchemaUpgradeOptions, verifier upgradeVerifier) (report RestoreReport, err error) {
	report = RestoreReport{Started: Now(), Status: "FAILED"}
	if err = pauseMigrationPaths(&opt, false); err != nil {
		return report, err
	}
	u := opt.Upgrade
	lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(u.Source))
	if err != nil {
		return report, err
	}
	defer func() {
		if closeErr := lease.Close(); closeErr != nil && err == nil {
			err = closeErr
		}
	}()
	sourceRelease, _, err := pauseMigrationRelease(u.SourceRoot, 24)
	if err != nil {
		return report, err
	}
	targetRelease, sqls, err := pauseMigrationRelease(u.TargetRoot, 25)
	if err != nil {
		return report, err
	}
	programs, err := pauseMigrationProgramHashes(opt, false)
	if err != nil {
		return report, err
	}
	binding, err := pauseHandoffCheck(opt, programs)
	if err != nil {
		return report, err
	}
	contracts, err := LoadContracts(filepath.Join(u.TargetRoot, "spec/v2.0/contracts"))
	if err != nil {
		return report, err
	}
	schemas, err := pauseMigrationTemplate(ctx, opt, filepath.Dir(u.Destination), sqls, contracts)
	if err != nil {
		return report, err
	}
	key, err := os.ReadFile(u.KeyFile)
	if err != nil || len(key) != 32 {
		return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	if err = pauseHandoffVerifyBackup(opt, key, binding); err != nil {
		return report, err
	}
	db, err := upgradeOpenExclusive(ctx, u.Source)
	if err != nil {
		return report, err
	}
	defer db.Close()
	if err = preparedUpgradeVersions(db, 24); err != nil {
		return report, err
	}
	schema, err := preparedUpgradeSchema(db)
	if err != nil || schema != schemas.Source24 {
		return report, fmt.Errorf("PAUSE_UPGRADE_SOURCE_SCHEMA")
	}
	guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: verifier}, contracts: contracts}
	if err = guard.refresh(db); err != nil {
		return report, err
	}
	original, err := preparedUpgradeSnapshot(db)
	if err != nil {
		return report, err
	}
	originalRecovery, err := upgradeRows(db)
	if err != nil {
		return report, err
	}
	workspace, err := upgradeQueueWorkspaceIdentity(db, u)
	if err != nil {
		return report, err
	}
	optionsRaw, err := json.Marshal(opt)
	if err != nil {
		return report, err
	}
	receipt := pauseMigrationReceipt{
		Schema: pauseMigrationReceiptSchema, Plan: PauseSchemaUpgradePlan, Status: "IN_PROGRESS", Options: opt,
		OptionsHash: Digest(optionsRaw), SourceProgramHash: programs.Source, TargetProgramHash: programs.Control, RehearsalProgramHash: programs.Rehearsal,
		SourceInventoryHash: Hash(sourceRelease), TargetInventoryHash: Hash(targetRelease),
		SourceSchema: schemas.Source24, TargetSchema: schemas.Original25, RestoredSchema: schemas.Restored24, RestoredTargetSchema: schemas.Restored25,
		SQLHash: pauseUpgradeSQLHash, OriginalRowsHash: Hash(original), HandoffBindingHash: opt.HandoffBindingSHA256,
		ProducerStdout: binding.ProducerStdout, ProducerObservation: binding.ProducerObservation,
		ReleaseAuthority: "RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY",
	}
	checkSource := func() error {
		if err := lease.Check(); err != nil {
			return err
		}
		rows, err := preparedUpgradeSnapshot(db)
		if err != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("PAUSE_UPGRADE_SOURCE_DRIFT")
		}
		currentSchema, err := preparedUpgradeSchema(db)
		if err != nil || currentSchema != schemas.Source24 {
			return fmt.Errorf("PAUSE_UPGRADE_SOURCE_SCHEMA_DRIFT")
		}
		for _, entry := range []struct {
			root  string
			count int
			hash  string
		}{{u.SourceRoot, 24, Hash(sourceRelease)}, {u.TargetRoot, 25, Hash(targetRelease)}} {
			current, _, err := pauseMigrationRelease(entry.root, entry.count)
			if err != nil || Hash(current) != entry.hash {
				return fmt.Errorf("PAUSE_UPGRADE_RELEASE_CHANGED")
			}
		}
		currentPrograms, err := pauseMigrationProgramHashes(opt, false)
		if err != nil || currentPrograms != programs {
			return fmt.Errorf("PAUSE_UPGRADE_PROGRAM_CHANGED")
		}
		currentBinding, err := pauseHandoffCheck(opt, programs)
		if err != nil || Hash(currentBinding) != Hash(binding) {
			return fmt.Errorf("PAUSE_HANDOFF_INPUT_CHANGED")
		}
		if err = pauseHandoffVerifyBackup(opt, key, binding); err != nil {
			return err
		}
		return ctx.Err()
	}
	checkSnapshot := func(restored *sql.DB) error {
		if err := guard.refresh(restored); err != nil {
			return err
		}
		rows, err := preparedUpgradeSnapshot(restored)
		if err != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("PAUSE_UPGRADE_SNAPSHOT_HISTORY")
		}
		identity, err := upgradeQueueWorkspaceIdentity(restored, u)
		if err != nil || Hash(identity) != Hash(workspace) {
			return fmt.Errorf("PAUSE_UPGRADE_WORKSPACE_CHANGED")
		}
		return checkSource()
	}
	policy := &backupPolicy{format: "RESEARCHOS_BACKUP_V1", databaseName: "researchos.sqlite", validate: guard.refresh,
		publicPauseUpgradeHandoff: true, preservePauseUpgradeWorkspaces: checkSnapshot, beforeRecovery: checkSnapshot}
	policy.afterRecovery = func(restored *sql.DB) error {
		if err := checkSource(); err != nil {
			return err
		}
		schema, err := preparedUpgradeSchema(restored)
		if err != nil || schema != schemas.Restored24 {
			return fmt.Errorf("PAUSE_UPGRADE_RESTORED_SCHEMA")
		}
		recoveryRows, err := upgradeRows(restored)
		if err != nil {
			return err
		}
		if err = preparedUpgradeRecoveryInvariant(originalRecovery, recoveryRows, u.Destination); err != nil {
			return err
		}
		baseline, err := preparedUpgradeSnapshot(restored)
		if err != nil {
			return err
		}
		receipt.PostRestoreRowsHash, receipt.RestoreDelta = Hash(baseline), preparedUpgradeDelta(original, baseline)
		if err = pauseMigrationRehearseDDL(ctx, restored, sqls[24], baseline, schemas.Restored24, schemas.Restored25); err != nil {
			return err
		}
		after, err := preparedUpgradeSnapshot(restored)
		if err != nil {
			return err
		}
		receipt.PostDDLRowsHash = Hash(after)
		receipt.RollbackVerified, receipt.ExistingRowsUnchanged, receipt.NewPauseTablesEmpty = true, true, true
		return checkSource()
	}
	// This consumes the old producer's complete ordinary backup without
	// executing the old program, replacing its output, or skipping recovery.
	report, err = restoreBackupPolicy(ctx, u.Snapshot, u.Destination,
		RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(24), Contracts: contracts}, policy)
	if err != nil {
		return report, err
	}
	if err = checkSource(); err != nil {
		return report, err
	}
	manifestRaw, err := os.ReadFile(filepath.Join(u.Snapshot, "manifest.json"))
	if err != nil || Digest(manifestRaw) != binding.BackupManifestSHA256 || int64(len(manifestRaw)) != binding.BackupManifestBytes {
		return report, fmt.Errorf("PAUSE_HANDOFF_MANIFEST_CHANGED")
	}
	receipt.BackupManifestHash, receipt.BackupManifestBytes = Digest(manifestRaw), int64(len(manifestRaw))
	receipt.Status, receipt.OriginalUnchanged, receipt.RestoreReport = "ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED", true, report
	if err = backupWrite(filepath.Join(u.Destination, pauseMigrationReceiptName), Bytes(receipt)); err != nil {
		return report, err
	}
	report.Recovery["runtime_pause_rehearsal_receipt"] = Object{"path": filepath.Join(u.Destination, pauseMigrationReceiptName), "sha256": Digest(Bytes(receipt))}
	return report, nil
}
