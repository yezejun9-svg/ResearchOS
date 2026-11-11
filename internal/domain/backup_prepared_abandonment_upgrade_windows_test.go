//go:build windows

package domain

import (
    "context"
    "encoding/json"
    "os"
    "path/filepath"
    "strings"
    "testing"

    runtimeadapter "researchos.local/research-os/adapters/runtime"
    "researchos.local/research-os/internal/recoveryauthority"
    "researchos.local/research-os/internal/store"
)

func preparedUpgradePublicFixture(t *testing.T) (LocalUpgradeOptions, *fixture, Object) {
    t.Helper()
    opt, f := configurationUpgradeFixture(t)
    raw, err := os.ReadFile("../../migrations/sqlite/0023_host_model_configuration.sql")
    if err != nil { t.Fatal(err) }
    if err = upgradeConfigurationMigration(context.Background(), f.db, raw); err != nil { t.Fatal(err) }
    opt.SourceRoot, opt.TargetRoot = preparedUpgradeTestRelease(t, 23), preparedUpgradeTestRelease(t, 24)
    opt.Plan = PreparedAbandonmentSchemaUpgradePlan
    req := f.requirement()
    goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "schema-only original preservation", "original_intent": "test restore separation", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
    goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "test fixture"})
    rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "schema-upgrade fixture only", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
    if err = f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); err != nil { t.Fatal(err) }
    orchestration := &orchestrationFixture{f, goal, req, rt, f.token}
    run := orchestration.claim(orchestration.task("prepared-schema-upgrade", Empty(), Empty()))
    f.token = orchestration.owner
    return opt, f, run.run
}

func TestPreparedUpgradeEncryptedRehearsalKeepsOriginalQueuedAndCredentials(t *testing.T) {
    opt, f, run := preparedUpgradePublicFixture(t)
    before, err := preparedUpgradeSnapshot(f.db)
    if err != nil { t.Fatal(err) }
    beforeSchema, err := preparedUpgradeSchema(f.db)
    if err != nil { t.Fatal(err) }
    if err = f.db.Close(); err != nil { t.Fatal(err) }
    report, err := UpgradeLocal(context.Background(), opt)
    if err != nil || report.Status != "RESTORED_RECONCILIATION_REQUIRED" { t.Fatal(report, err) }
    original, err := store.Open(opt.Source)
    if err != nil { t.Fatal(err) }
    defer original.Close()
    originalAfter, err := preparedUpgradeSnapshot(original)
    if err != nil || Hash(originalAfter) != Hash(before) { t.Fatal("original rows changed", err) }
    originalSchema, err := preparedUpgradeSchema(original)
    if err != nil || originalSchema != beforeSchema { t.Fatal("original schema changed", err) }
    if err = preparedUpgradeVersions(original, 23); err != nil { t.Fatal(err) }
    var originalStatus string
    if err = original.QueryRow("SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Run' AND id=?", run["id"]).Scan(&originalStatus); err != nil || originalStatus != "QUEUED" { t.Fatal(originalStatus, err) }
    copyDB, err := store.Open(filepath.Join(opt.Destination, "researchos.sqlite"))
    if err != nil { t.Fatal(err) }
    defer copyDB.Close()
    if err = preparedUpgradeVersions(copyDB, 24); err != nil { t.Fatal(err) }
    var restoredStatus string
    var liveCredentials, proofs int
    if err = copyDB.QueryRow("SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Run' AND id=?", run["id"]).Scan(&restoredStatus); err != nil || restoredStatus != "RECONCILING" { t.Fatal(restoredStatus, err) }
    if err = copyDB.QueryRow("SELECT count(*) FROM auth_credentials WHERE revoked=0").Scan(&liveCredentials); err != nil || liveCredentials != 0 { t.Fatal(liveCredentials, err) }
    if err = copyDB.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments").Scan(&proofs); err != nil || proofs != 0 { t.Fatal(proofs, err) }
    var receipt preparedUpgradeRehearsalReceipt
    raw, err := os.ReadFile(filepath.Join(opt.Destination, preparedUpgradeReceiptName))
    if err != nil || json.Unmarshal(raw, &receipt) != nil { t.Fatal("receipt", err) }
    if !receipt.RollbackVerified || !receipt.ExistingRowsUnchanged || !receipt.OriginalUnchanged ||
        receipt.OriginalRowsHash != Hash(before) || receipt.PostRestoreRowsHash == receipt.OriginalRowsHash ||
        receipt.RestoreDelta["auth_credentials"] == nil || receipt.RestoreDelta["domain_objects"] == nil ||
        receipt.ReleaseAuthority != "RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY" {
        t.Fatal("restore and DDL evidence conflated", string(raw))
    }
    afterDDL, err := preparedUpgradeSnapshot(copyDB)
    if err != nil || Hash(afterDDL) != receipt.PostDDLRowsHash { t.Fatal("published copy differs from checked DDL", err) }
    manifestRaw, err := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
    if err != nil || Digest(manifestRaw) != receipt.BackupManifestHash { t.Fatal("backup pin", err) }
    if _, err = os.Stat(filepath.Join(opt.Snapshot, "state.sqlite")); !os.IsNotExist(err) { t.Fatal("plaintext snapshot published") }
    key, err := os.ReadFile(opt.KeyFile)
    if err != nil { t.Fatal(err) }
    defer clear(key)
    _, decrypted, err := readBackupPolicy(opt.Snapshot, key, &backupPolicy{format: localUpgradeFormat, purpose: receipt.BackupPurpose})
    if err != nil || len(decrypted["state.sqlite"]) == 0 { t.Fatal("complete encrypted matching backup", err) }
    for _, raw := range decrypted { clear(raw) }
}

func TestPreparedUpgradeRehearsalRequiresCurrentDataRootLease(t *testing.T) {
    opt, f, _ := preparedUpgradePublicFixture(t)
    if err := f.db.Close(); err != nil { t.Fatal(err) }
    held, err := runtimeadapter.AcquireDataRootLease(filepath.Dir(opt.Source))
    if err != nil { t.Fatal(err) }
    defer held.Close()
    if _, err = UpgradeLocal(context.Background(), opt); err == nil { t.Fatal("competing data-root owner accepted") }
    if _, err = os.Stat(opt.Snapshot); !os.IsNotExist(err) { t.Fatal("backup created without data-root ownership") }
}

func TestPreparedUpgradeOriginalRequiresOpaquePurposeToken(t *testing.T) {
    db, _, _ := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    result, err := ExecutePreparedAbandonmentSchemaUpgrade(context.Background(), db, recoveryauthority.MigrationToken{}, "", LocalUpgradeOptions{Plan: PreparedAbandonmentSchemaUpgradePlan})
    if err == nil || result["committed"] != false { t.Fatal("zero native token accepted") }
    after, err := preparedUpgradeSnapshot(db)
    if err != nil || Hash(before) != Hash(after) { t.Fatal("denied original operation changed rows", err) }
}

func TestPreparedUpgradeNormalStartupStillRequiresPrebackup(t *testing.T) {
    db, _, _ := preparedUpgradeTestDB(t)
    target := preparedUpgradeTestRelease(t, 24)
    files, err := filepath.Glob(filepath.Join(target, "migrations/sqlite/0*.sql"))
    if err != nil { t.Fatal(err) }
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    err = CheckMigrationSafety(db, files)
    if err == nil || !strings.Contains(err.Error(), "MIGRATION_PREBACKUP_REQUIRED") { t.Fatal("normal populated startup bypass", err) }
    after, err := preparedUpgradeSnapshot(db)
    if err != nil || Hash(before) != Hash(after) { t.Fatal("startup guard changed rows", err) }
}

func TestPreparedUpgradeNormalBackupAfterExact24(t *testing.T) {
    opt, f, _ := preparedUpgradePublicFixture(t)
    _, sqls, err := preparedUpgradeRelease(opt.TargetRoot, 24)
    if err != nil { t.Fatal(err) }
    schemas, err := preparedUpgradeTemplate(context.Background(), sqls, f.s.Contracts)
    if err != nil { t.Fatal(err) }
    before, err := preparedUpgradeSnapshot(f.db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRehearseDDL(context.Background(), f.db, sqls[23], before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    afterDDL, err := preparedUpgradeSnapshot(f.db)
    if err != nil { t.Fatal(err) }
    bindings, err := workspaceBackupBindings(f.db)
    if err != nil || len(bindings) != 1 { t.Fatal("public fixture workspace", len(bindings), err) }
    key, err := os.ReadFile(opt.KeyFile)
    if err != nil { t.Fatal(err) }
    defer clear(key)
    destination := filepath.Join(t.TempDir(), "normal24-backup")
    manifest, err := f.s.CreateBackupWithWorkspaces(context.Background(), destination, key, queueUpgradeWorkspace{bindings[0].RealPath})
    if err != nil { t.Fatal("normal current24 backup", err) }
    if manifest.Format != "RESEARCHOS_BACKUP_V1" || Hash(manifest.Migrations) != Hash(upgradeVersions(24)) || manifest.SchemaHash != schemas.Original24 {
        t.Fatal("wrong normal backup contract", manifest)
    }
    _, files, err := readBackupPolicy(destination, key, nil)
    if err != nil || len(files["state.sqlite"]) == 0 || len(files["portable.json"]) == 0 { t.Fatal("normal backup unreadable", err) }
    for _, raw := range files { clear(raw) }
    afterBackup, err := preparedUpgradeSnapshot(f.db)
    if err != nil || Hash(afterBackup) != Hash(afterDDL) { t.Fatal("normal backup changed business rows", err) }
}

