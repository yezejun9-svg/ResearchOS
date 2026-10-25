package domain

// Public-backup handoff is an isolated, same-host rehearsal. The Root-supplied
// observation pins are provenance inputs, not credentials or execution proof.
// The old program has already created an ordinary public backup. This program
// never executes that old binary and must itself equal the distinct target.
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

const preparedPublicHandoffSchema = "researchos.public23-to24-backup-handoff.v1"
const preparedPublicHandoffReceiptName = "prepared-abandonment-public-backup-handoff.json"

type PreparedBackupHandoffOptions struct {
    Upgrade LocalUpgradeOptions
    BindingFile string
    BindingSHA256 string
}

type preparedHandoffFileRef struct {
    Path string `json:"path"`
    SHA256 string `json:"sha256"`
    Bytes int64 `json:"bytes"`
}

// All digests in this contract include the "sha256:" prefix. Root must review
// the original observation independently before constructing and pinning this
// binding. Reading a JSON declaration does not authenticate its claims.
type preparedBackupHandoffBinding struct {
    Schema string `json:"schema"`
    SourceDatabase string `json:"source_database"`
    BackupDirectory string `json:"backup_directory"`
    SourceProgramSHA256 string `json:"source_program_sha256"`
    TargetProgramSHA256 string `json:"target_program_sha256"`
    BackupManifestSHA256 string `json:"backup_manifest_sha256"`
    BackupManifestBytes int64 `json:"backup_manifest_bytes"`
    BackupID string `json:"backup_id"`
    SourceBackupOperation string `json:"source_backup_operation"`
    ObservedBackupExit *int `json:"observed_backup_exit"`
    ProducerStdout preparedHandoffFileRef `json:"producer_stdout"`
    ProducerObservation preparedHandoffFileRef `json:"producer_observation"`
}

func preparedHandoffDigest(value string) bool {
    if len(value) != 71 || !strings.HasPrefix(value, "sha256:") { return false }
    for _, c := range value[7:] {
        if !(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f') { return false }
    }
    return true
}

func preparedHandoffReadRef(ref preparedHandoffFileRef) ([]byte, error) {
    if !preparedHandoffDigest(ref.SHA256) || ref.Bytes <= 0 || ref.Bytes > 128*1024*1024 {
        return nil, fmt.Errorf("PREPARED_HANDOFF_EVIDENCE_PIN")
    }
    path, err := upgradePath(ref.Path, true)
    if err != nil { return nil, err }
    info, err := os.Stat(path)
    if err != nil || !info.Mode().IsRegular() || info.Size() != ref.Bytes {
        return nil, fmt.Errorf("PREPARED_HANDOFF_EVIDENCE_FILE")
    }
    raw, err := os.ReadFile(path)
    if err != nil || int64(len(raw)) != ref.Bytes || Digest(raw) != ref.SHA256 {
        return nil, fmt.Errorf("PREPARED_HANDOFF_EVIDENCE_CHANGED")
    }
    return raw, nil
}

func preparedHandoffMetadata(b preparedBackupHandoffBinding, source, target string, manifest, stdout BackupManifest) error {
    if b.Schema != preparedPublicHandoffSchema || b.SourceBackupOperation != "create" ||
       b.ObservedBackupExit == nil || *b.ObservedBackupExit != 0 {
        return fmt.Errorf("PREPARED_HANDOFF_OBSERVATION_REQUIRED")
    }
    if !preparedHandoffDigest(source) || !preparedHandoffDigest(target) ||
       source == target || source != b.SourceProgramSHA256 || target != b.TargetProgramSHA256 {
        return fmt.Errorf("PREPARED_HANDOFF_DISTINCT_PROGRAM_PINS")
    }
    if b.BackupID == "" || manifest.ID != b.BackupID || manifest.Format != "RESEARCHOS_BACKUP_V1" ||
       len(manifest.Purpose) != 0 || Hash(manifest.Migrations) != Hash(upgradeVersions(23)) {
        return fmt.Errorf("PREPARED_HANDOFF_BACKUP_IDENTITY")
    }
    if Hash(manifest) != Hash(stdout) {
        return fmt.Errorf("PREPARED_HANDOFF_PRODUCER_STDOUT_MISMATCH")
    }
    return nil
}

func preparedHandoffCheck(opt LocalUpgradeOptions, handoff PreparedBackupHandoffOptions) (preparedBackupHandoffBinding, error) {
    var b preparedBackupHandoffBinding
    if !preparedHandoffDigest(handoff.BindingSHA256) { return b, fmt.Errorf("PREPARED_HANDOFF_BINDING_PIN_REQUIRED") }
    raw, err := os.ReadFile(handoff.BindingFile)
    if err != nil || Digest(raw) != handoff.BindingSHA256 { return b, fmt.Errorf("PREPARED_HANDOFF_BINDING_CHANGED") }
    dec := json.NewDecoder(bytes.NewReader(raw)); dec.DisallowUnknownFields()
    if err = dec.Decode(&b); err != nil { return b, err }
    if err = dec.Decode(new(any)); err != io.EOF { return b, fmt.Errorf("PREPARED_HANDOFF_BINDING_TRAILING_DATA") }
    sourcePath, err := upgradePath(b.SourceDatabase, true)
    if err != nil || !strings.EqualFold(sourcePath, opt.Source) { return b, fmt.Errorf("PREPARED_HANDOFF_SOURCE_PATH") }
    backupPath, err := upgradePath(b.BackupDirectory, true)
    if err != nil || !strings.EqualFold(backupPath, opt.Snapshot) { return b, fmt.Errorf("PREPARED_HANDOFF_BACKUP_PATH") }
    source, target, err := preparedUpgradeProgramHashes(opt, true)
    if err != nil { return b, err }
    rawManifest, err := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
    if err != nil || !preparedHandoffDigest(b.BackupManifestSHA256) ||
       int64(len(rawManifest)) != b.BackupManifestBytes || Digest(rawManifest) != b.BackupManifestSHA256 {
        return b, fmt.Errorf("PREPARED_HANDOFF_MANIFEST_CHANGED")
    }
    var manifest, stdout BackupManifest
    if err = json.Unmarshal(rawManifest, &manifest); err != nil { return b, err }
    rawStdout, err := preparedHandoffReadRef(b.ProducerStdout)
    if err != nil { return b, err }
    if err = json.Unmarshal(rawStdout, &stdout); err != nil { return b, err }
    if _, err = preparedHandoffReadRef(b.ProducerObservation); err != nil { return b, err }
    return b, preparedHandoffMetadata(b, source, target, manifest, stdout)
}

// Snapshot is existing here; every other path/alias/overlap constraint remains
// the same as upgradePaths. No dummy nonexistent output is used to bypass it.
func preparedHandoffPaths(opt *LocalUpgradeOptions, handoff *PreparedBackupHandoffOptions) error {
    for _, p := range []*string{&opt.Source, &opt.Snapshot, &opt.KeyFile, &opt.SourceRoot, &opt.TargetRoot, &opt.SourceProgram, &opt.TargetProgram, &handoff.BindingFile} {
        v, err := upgradePath(*p, true)
        if err != nil { return err }
        *p = v
    }
    destination, err := upgradePath(opt.Destination, false)
    if err != nil { return err }
    opt.Destination = destination
    dirs := []string{filepath.Dir(opt.Source), filepath.Dir(opt.KeyFile), opt.Snapshot, opt.Destination}
    for i, a := range dirs {
        for _, b := range dirs[i+1:] {
            if upgradeInside(a, b) || upgradeInside(b, a) { return fmt.Errorf("UPGRADE_PATH_OVERLAP") }
        }
    }
    var infos []os.FileInfo
    for _, path := range []string{opt.Source, opt.KeyFile, opt.SourceProgram, opt.TargetProgram, handoff.BindingFile} {
        info, err := os.Stat(path)
        if err != nil || !info.Mode().IsRegular() { return fmt.Errorf("UPGRADE_REGULAR_FILE_REQUIRED") }
        infos = append(infos, info)
    }
    for i, a := range infos {
        for _, b := range infos[i+1:] {
            if os.SameFile(a, b) { return fmt.Errorf("UPGRADE_FILE_ALIAS") }
        }
    }
    for _, path := range []string{opt.Snapshot, opt.SourceRoot, opt.TargetRoot} {
        info, err := os.Stat(path)
        if err != nil || !info.IsDir() { return fmt.Errorf("PREPARED_HANDOFF_DIRECTORY_REQUIRED") }
    }
    return nil
}

func preparedHandoffVerifyBackup(opt LocalUpgradeOptions, key []byte, b preparedBackupHandoffBinding) error {
    manifest, files, err := readBackup(opt.Snapshot, key)
    defer func() { for _, raw := range files { clear(raw) } }()
    if err != nil { return err }
    if manifest.ID != b.BackupID || Hash(manifest.Migrations) != Hash(upgradeVersions(23)) {
        return fmt.Errorf("PREPARED_HANDOFF_BACKUP_IDENTITY")
    }
    return nil
}

// Separate public entry point. Its report is not a Native MigrationToken and
// the receipt filename is intentionally not the original-apply receipt name.
func UpgradePreparedAbandonmentBackup(ctx context.Context, handoff PreparedBackupHandoffOptions) (RestoreReport, error) {
    return RestoreReport{Status: "FAILED"}, fmt.Errorf("UPGRADE_SOURCE_LEASE_REQUIRED")
}


func upgradePreparedAbandonmentBackup(ctx context.Context, handoff PreparedBackupHandoffOptions, verifier upgradeVerifier) (report RestoreReport, err error) {
    opt := handoff.Upgrade
    report = RestoreReport{Started: Now(), Status: "FAILED"}
    if opt.Plan != PreparedAbandonmentSchemaUpgradePlan { return report, fmt.Errorf("PREPARED_UPGRADE_PLAN_UNSUPPORTED") }
    if err := preparedHandoffPaths(&opt, &handoff); err != nil { return report, err }
    if opt.sourceLease != nil {
        if err := opt.sourceLease.Check(filepath.Dir(opt.Source), opt.Source); err != nil { return report, err }
    }
    lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source), opt.Source, opt.sourceLease)
    if err != nil { return report, err }
    defer func() {
        if closeErr := lease.Close(); closeErr != nil && err == nil { err = closeErr }
    }()
    sourceRelease, _, err := preparedUpgradeRelease(opt.SourceRoot, 23)
    if err != nil { return report, err }
    targetRelease, sqls, err := preparedUpgradeRelease(opt.TargetRoot, 24)
    if err != nil { return report, err }
    sourceProgram, targetProgram, err := preparedUpgradeProgramHashes(opt, true)
    if err != nil { return report, err }
    binding, err := preparedHandoffCheck(opt, handoff)
    if err != nil { return report, err }
    contracts, err := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
    if err != nil { return report, err }
    schemas, err := preparedUpgradeTemplate(ctx, sqls, contracts)
    if err != nil { return report, err }
    key, err := os.ReadFile(opt.KeyFile)
    if err != nil || len(key) != 32 { return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE") }
    defer clear(key)
    if err = preparedHandoffVerifyBackup(opt, key, binding); err != nil { return report, err }
    db, err := upgradeOpenExclusive(ctx, opt.Source)
    if err != nil { return report, err }
    defer db.Close()
    if err = preparedUpgradeVersions(db, 23); err != nil { return report, err }
    schema, err := preparedUpgradeSchema(db)
    if err != nil { return report, err }
    sourceSchema, targetSchema := schema, schemas.Original24
    if schema == schemas.Restored23 {
        targetSchema = schemas.Restored24
    } else if schema != schemas.Source23 {
        return report, fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA")
    }
    guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: verifier}, contracts: contracts}
    if err = guard.refresh(db); err != nil { return report, err }
    original, err := preparedUpgradeSnapshot(db)
    if err != nil { return report, err }
    originalRecoveryRows, err := upgradeRows(db)
    if err != nil { return report, err }
    workspace, err := upgradeQueueWorkspaceIdentity(db, opt)
    if err != nil { return report, err }
    optionsRaw, err := json.Marshal(opt)
    if err != nil { return report, err }
    receipt := preparedUpgradeRehearsalReceipt{
        Schema: "researchos.prepared-abandonment-public-backup-rehearsal.v1", Plan: opt.Plan, Status: "IN_PROGRESS",
        Options: opt, OptionsHash: Digest(optionsRaw), SourceProgramHash: sourceProgram, TargetProgramHash: targetProgram,
        SourceInventoryHash: Hash(sourceRelease), TargetInventoryHash: Hash(targetRelease),
        SourceSchema: sourceSchema, TargetSchema: targetSchema, RestoredSchema: schemas.Restored23,
        RestoredTargetSchema: schemas.Restored24, SQLHash: preparedUpgradeSQLHash, OriginalRowsHash: Hash(original),
        ReleaseAuthority: "RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY",
    }
    plan := Object{"id": opt.Plan, "source_versions": upgradeVersions(23), "target_versions": upgradeVersions(24),
        "source_schema_hash": sourceSchema, "original_target_schema_hash": targetSchema,
        "restored_target_schema_hash": schemas.Restored24, "source_database_logical_hash": Hash(original),
        "source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
        "source_program_hash": sourceProgram, "target_program_hash": targetProgram, "migration_sql_hash": preparedUpgradeSQLHash,
        "options_hash": receipt.OptionsHash}
    purpose := Object{"kind": "SAME_HOST_PUBLIC23_TO24_BACKUP_HANDOFF", "scope": "IsolatedRestoreOnly",
        "plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
        "protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
        "protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
        "external_actions_dispatched": 0, "automatic_promotion": false, "original_business_mutation": false}
    purpose["source_provenance"] = "EXTERNALLY_REVIEWED_OBSERVATION_INPUT_NOT_JSON_AUTHORITY"
    purpose["handoff_binding_sha256"] = handoff.BindingSHA256
    purpose["producer_observation"] = binding.ProducerObservation
    purpose["producer_stdout"] = binding.ProducerStdout
    purpose["existing_public_backup_consumed"] = true
    purpose["old_program_executed_by_target"] = false
    receipt.BackupPurpose = purpose
    // Retain ordinary public backup MAC/portable/queue/protected-artifact gates.
    // This private flag only permits fixed same-host preservation and late DDL.
    policy := &backupPolicy{format: "RESEARCHOS_BACKUP_V1", databaseName: "researchos.sqlite",
        validate: guard.refresh, publicPreparedAbandonmentHandoff: true}
    checkSource := func() error {
        if err := lease.Check(); err != nil { return err }
        current, err := preparedUpgradeSnapshot(db)
        if err != nil || Hash(current) != Hash(original) { return fmt.Errorf("PREPARED_UPGRADE_SOURCE_DRIFT") }
        currentSchema, err := preparedUpgradeSchema(db)
        if err != nil || currentSchema != sourceSchema { return fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA_DRIFT") }
        a, _, err := preparedUpgradeRelease(opt.SourceRoot, 23)
        if err != nil || Hash(a) != Hash(sourceRelease) { return fmt.Errorf("PREPARED_UPGRADE_RELEASE_CHANGED") }
        b, _, err := preparedUpgradeRelease(opt.TargetRoot, 24)
        if err != nil || Hash(b) != Hash(targetRelease) { return fmt.Errorf("PREPARED_UPGRADE_RELEASE_CHANGED") }
        x, y, err := preparedUpgradeProgramHashes(opt, true)
        if err != nil || x != sourceProgram || y != targetProgram { return fmt.Errorf("PREPARED_UPGRADE_PROGRAM_CHANGED") }
        currentBinding, err := preparedHandoffCheck(opt, handoff)
        if err != nil || Hash(currentBinding) != Hash(binding) { return fmt.Errorf("PREPARED_HANDOFF_INPUT_CHANGED") }
        if err = preparedHandoffVerifyBackup(opt, key, binding); err != nil { return err }
        return ctx.Err()
    }
    checkSnapshot := func(restored *sql.DB) error {
        if err := guard.refresh(restored); err != nil { return err }
        rows, err := preparedUpgradeSnapshot(restored)
        if err != nil || Hash(rows) != Hash(original) { return fmt.Errorf("PREPARED_UPGRADE_SNAPSHOT_HISTORY") }
        identity, err := upgradeQueueWorkspaceIdentity(restored, opt)
        if err != nil || Hash(identity) != Hash(workspace) { return fmt.Errorf("PREPARED_UPGRADE_WORKSPACE_CHANGED") }
        return checkSource()
    }
    policy.preservePreparedAbandonmentUpgradeWorkspaces = checkSnapshot
    policy.beforeRecovery = checkSnapshot
    // This hook runs AFTER ordinary relocation, backupFence, acceptance checks
    // and source-path publication. Its baseline includes every restore effect.
    policy.afterRecovery = func(restored *sql.DB) error {
        if err := checkSource(); err != nil { return err }
        schema, err := preparedUpgradeSchema(restored)
        if err != nil || schema != schemas.Restored23 { return fmt.Errorf("PREPARED_UPGRADE_RESTORED_SCHEMA") }
        recoveryRows, err := upgradeRows(restored)
        if err != nil { return err }
        if err = preparedUpgradeRecoveryInvariant(originalRecoveryRows, recoveryRows, opt.Destination); err != nil { return err }
        baseline, err := preparedUpgradeSnapshot(restored)
        if err != nil { return err }
        receipt.PostRestoreRowsHash = Hash(baseline)
        receipt.RestoreDelta = preparedUpgradeDelta(original, baseline)
        if err = preparedUpgradeRehearseDDL(ctx, restored, sqls[23], baseline, schemas.Restored23, schemas.Restored24); err != nil { return err }
        after, err := preparedUpgradeSnapshot(restored)
        if err != nil { return err }
        receipt.PostDDLRowsHash = Hash(after)
        receipt.RollbackVerified, receipt.ExistingRowsUnchanged, receipt.NewProofTableEmpty = true, true, true
        return checkSource()
    }
    // Consume the already-observed old-program output. Never recreate it.
    // The beforeRecovery hook rejects stale/mixed snapshots before late DDL.
    // No skipRecovery and no migration callback in generic RestoreOptions.
    report, err = restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination,
        RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(23), Contracts: contracts}, policy)
    if err != nil { return report, err }
    if err = checkSource(); err != nil { return report, err }
    rawManifest, err := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
    if err != nil { return report, err }
    if Digest(rawManifest) != binding.BackupManifestSHA256 || int64(len(rawManifest)) != binding.BackupManifestBytes {
        return report, fmt.Errorf("PREPARED_HANDOFF_MANIFEST_CHANGED")
    }
    receipt.BackupManifestHash, receipt.BackupManifestBytes = Digest(rawManifest), int64(len(rawManifest))
    receipt.Status, receipt.OriginalUnchanged, receipt.RestoreReport = "ISOLATED_PUBLIC_BACKUP_HANDOFF_COMPLETE_ORIGINAL_UNCHANGED", true, report
    if err = backupWrite(filepath.Join(opt.Destination, preparedPublicHandoffReceiptName), Bytes(receipt)); err != nil { return report, err }
    report.Recovery["local_upgrade"] = purpose
    report.Recovery["source_provenance_authority"] = "EXTERNAL_INDEPENDENT_REVIEW_REQUIRED"
    report.Recovery["prepared_abandonment_public_backup_handoff_receipt"] = Object{"path": filepath.Join(opt.Destination, preparedPublicHandoffReceiptName), "sha256": Digest(Bytes(receipt))}
    return report, nil
}
