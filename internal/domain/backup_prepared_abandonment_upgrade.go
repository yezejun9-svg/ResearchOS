package domain

// A fixed additive upgrade. Restoration is confined to a rehearsal copy.
// Original-root DDL is exposed only through the separate native MigrationToken.
import (
    "bytes"
    "context"
    "database/sql"
    _ "embed"
    "encoding/binary"
    "encoding/json"
    "fmt"
    "math"
    "os"
    "path/filepath"
    "reflect"
    "sort"
    "strconv"
    "strings"
    "sync"

    "researchos.local/research-os/internal/store"
    "researchos.local/research-os/adapters/protectedstore"
)

const PreparedAbandonmentSchemaUpgradePlan = "schema23-to24-prepared-abandonment-v1"
const preparedUpgradeSQLHash = "sha256:1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098"
const preparedUpgradeProofTable = "runtime_prepared_abandonments"
const preparedUpgradeReceiptName = "prepared-abandonment-rehearsal.json"

type preparedUpgradeSchemas struct {
    Source23 string
    Original24 string
    Restored23 string
    Restored24 string
}

type preparedUpgradeTable struct {
    Columns []string `json:"columns"`
    Rows []string `json:"row_digests"`
}
type preparedUpgradeRows map[string]preparedUpgradeTable
type preparedUpgradeQuery interface {
    Query(string, ...any) (*sql.Rows, error)
    QueryRow(string, ...any) *sql.Row
}

type preparedUpgradeRehearsalReceipt struct {
    Schema string `json:"schema"`
    Plan string `json:"plan"`
    Status string `json:"status"`
    Options LocalUpgradeOptions `json:"options"`
    OptionsHash string `json:"options_sha256"`
    SourceProgramHash string `json:"source_program_sha256"`
    TargetProgramHash string `json:"target_program_sha256"`
    SourceInventoryHash string `json:"source_inventory_sha256"`
    TargetInventoryHash string `json:"target_inventory_sha256"`
    SourceSchema string `json:"source_schema_sha256"`
    TargetSchema string `json:"target_schema_sha256"`
    RestoredSchema string `json:"restored_schema23_sha256"`
    RestoredTargetSchema string `json:"restored_schema24_sha256"`
    SQLHash string `json:"sql_sha256"`
    OriginalRowsHash string `json:"original_rows_sha256"`
    PostRestoreRowsHash string `json:"post_restore_rows_sha256"`
    PostDDLRowsHash string `json:"post_ddl_rows_sha256"`
    BackupManifestHash string `json:"backup_manifest_sha256"`
    BackupManifestBytes int64 `json:"backup_manifest_bytes"`
    BackupPurpose Object `json:"backup_purpose"`
    RestoreDelta Object `json:"restore_row_delta"`
    RestoreReport RestoreReport `json:"restore_report"`
    RollbackVerified bool `json:"rollback_verified"`
    OriginalUnchanged bool `json:"original_unchanged"`
    ExistingRowsUnchanged bool `json:"existing_rows_unchanged_by_ddl"`
    NewProofTableEmpty bool `json:"new_proof_table_empty"`
    ReleaseAuthority string `json:"release_authority"`
    AutomaticPromotion bool `json:"automatic_promotion"`
}

// Preserve the exact 1..23 inventory and add only the pinned 0024 at target24.
// Existing upgradeConfigurationRelease and its 22->23 semantics are untouched.
func preparedUpgradeRelease(root string, count int) (Object, [][]byte, error) {
    if count != 23 && count != 24 {
        return nil, nil, fmt.Errorf("PREPARED_UPGRADE_PLAN_UNSUPPORTED")
    }
    files, err := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
    if err != nil || len(files) != count {
        return nil, nil, fmt.Errorf("PREPARED_UPGRADE_RELEASE_INVENTORY")
    }
    manifest := Object{}
    sqls := make([][]byte, count+1)
    for i, file := range files {
        name := filepath.Base(file)
        if len(name) < 6 || name[:5] != fmt.Sprintf("%04d_", i+1) {
            return nil, nil, fmt.Errorf("PREPARED_UPGRADE_RELEASE_INVENTORY")
        }
        expected := upgradeMigrationHashes[name]
        switch name {
        case "0021_research_pending_windows.sql":
            expected = "sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32"
        case "0022_client_command_queue.sql":
            expected = upgradeQueueSQLHash
        case "0023_host_model_configuration.sql":
            expected = upgradeConfigurationSQLHash
        case "0024_prepared_run_abandonment.sql":
            expected = preparedUpgradeSQLHash
        }
        raw, err := os.ReadFile(file)
        if err != nil || expected == "" || Digest(raw) != expected {
            return nil, nil, fmt.Errorf("PREPARED_UPGRADE_RELEASE_HASH: %s", name)
        }
        manifest["migrations/sqlite/"+name] = expected
        sqls[i] = raw
    }
    for path, expected := range map[string]string{
        "spec/v2.0/contracts/domain.schema.json": "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
        "spec/v2.0/contracts/openapi.json": "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
        "internal/api/contracts/client.protocol.schema.json": "sha256:8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b",
        "internal/api/contracts/domain.schema.json": "sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54",
    } {
        raw, err := os.ReadFile(filepath.Join(root, filepath.FromSlash(path)))
        if err != nil || Digest(raw) != expected {
            return nil, nil, fmt.Errorf("PREPARED_UPGRADE_CONTRACT_HASH: %s", path)
        }
        manifest[path] = expected
    }
    raw, err := os.ReadFile(filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql"))
    if err != nil || Digest(raw) != upgradeQueueSessionHash {
        return nil, nil, fmt.Errorf("PREPARED_UPGRADE_ADDITIVE_HASH")
    }
    manifest["migrations/sqlite/next_v24_sessions.sql"] = Digest(raw)
    sqls[count] = raw
    return manifest, sqls, nil
}

func preparedUpgradeVersions(q preparedUpgradeQuery, n int) error {
    rows, err := q.Query("SELECT version,typeof(version) FROM schema_migrations ORDER BY version")
    if err != nil { return err }
    defer rows.Close()
    seen := 0
    for rows.Next() {
        var version int
        var typ string
        if err = rows.Scan(&version, &typ); err != nil { return err }
        seen++
        if version != seen || typ != "integer" || seen > n {
            return fmt.Errorf("PREPARED_UPGRADE_MIGRATION_INVENTORY")
        }
    }
    if err = rows.Err(); err != nil { return err }
    if seen != n { return fmt.Errorf("PREPARED_UPGRADE_MIGRATION_INVENTORY") }
    return nil
}

func preparedUpgradeSchema(q preparedUpgradeQuery) (string, error) {
    rows, err := q.Query("SELECT type,name,tbl_name,coalesce(sql,'') FROM sqlite_master ORDER BY type,name")
    if err != nil { return "", err }
    defer rows.Close()
    all := []any{}
    for rows.Next() {
        var kind, name, table, raw string
        if err = rows.Scan(&kind, &name, &table, &raw); err != nil { return "", err }
        all = append(all, []any{kind, name, table, raw})
    }
    return Hash(all), rows.Err()
}

// Row hashes encode SQL storage types and lossless values, including raw TEXT,
// BLOB bytes, int64 decimal and float64 bits. No JSON number round trip occurs.
func preparedUpgradeRowHash(values []any) (string, error) {
    var buf bytes.Buffer
    for _, value := range values {
        var typ byte
        var raw []byte
        switch v := value.(type) {
        case nil: typ = 'N'
        case int64: typ, raw = 'I', []byte(strconv.FormatInt(v, 10))
        case float64:
            typ, raw = 'F', make([]byte, 8)
            binary.BigEndian.PutUint64(raw, math.Float64bits(v))
        case string: typ, raw = 'T', []byte(v)
        case []byte: typ, raw = 'B', v
        default: return "", fmt.Errorf("PREPARED_UPGRADE_SQL_STORAGE_TYPE: %T", value)
        }
        buf.WriteByte(typ)
        var size [8]byte
        binary.BigEndian.PutUint64(size[:], uint64(len(raw)))
        buf.Write(size[:])
        buf.Write(raw)
    }
    return Digest(buf.Bytes()), nil
}

func preparedUpgradeSnapshot(q preparedUpgradeQuery) (preparedUpgradeRows, error) {
    rows, err := q.Query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    if err != nil { return nil, err }
    names := []string{}
    for rows.Next() {
        var name string
        if err = rows.Scan(&name); err != nil { rows.Close(); return nil, err }
        names = append(names, name)
    }
    err = rows.Err()
    rows.Close()
    if err != nil { return nil, err }
    result := preparedUpgradeRows{}
    for _, name := range names {
        rows, err = q.Query("SELECT * FROM \""+strings.ReplaceAll(name, "\"", "\"\"")+"\"")
        if err != nil { return nil, err }
        cols, err := rows.Columns()
        if err != nil { rows.Close(); return nil, err }
        // Strip declared-column type hints so the SQLite driver returns the
        // actual storage class rather than parsing a declared date/bool type.
        rows.Close()
        projections := make([]string, len(cols))
        for i, col := range cols {
            projections[i] = "CASE WHEN 1 THEN \""+strings.ReplaceAll(col, "\"", "\"\"")+"\" END"
        }
        rows, err = q.Query("SELECT "+strings.Join(projections, ",")+" FROM \""+strings.ReplaceAll(name, "\"", "\"\"")+"\"")
        if err != nil { return nil, err }
        table := preparedUpgradeTable{Columns: cols, Rows: []string{}}
        for rows.Next() {
            values := make([]any, len(cols))
            pointers := make([]any, len(cols))
            for i := range values { pointers[i] = &values[i] }
            if err = rows.Scan(pointers...); err != nil { rows.Close(); return nil, err }
            digest, err := preparedUpgradeRowHash(values)
            if err != nil { rows.Close(); return nil, err }
            table.Rows = append(table.Rows, digest)
        }
        err = rows.Err()
        rows.Close()
        if err != nil { return nil, err }
        sort.Strings(table.Rows)
        result[name] = table
    }
    return result, nil
}

func preparedUpgradeRowInvariant(before, after preparedUpgradeRows) error {
    if _, exists := before[preparedUpgradeProofTable]; exists {
        return fmt.Errorf("PREPARED_UPGRADE_PROOF_TABLE_ALREADY_EXISTS")
    }
    for name, old := range before {
        current, exists := after[name]
        if !exists || !reflect.DeepEqual(old.Columns, current.Columns) {
            return fmt.Errorf("PREPARED_UPGRADE_TABLE_CHANGED: %s", name)
        }
        if name == "schema_migrations" {
            counts := map[string]int{}
            for _, h := range current.Rows { counts[h]++ }
            for _, h := range old.Rows {
                counts[h]--
                if counts[h] < 0 { return fmt.Errorf("PREPARED_UPGRADE_MIGRATION_HISTORY_CHANGED") }
            }
            // Version24 is checked separately; applied_at must not cause any
            // old migration row to be rewritten.
            if len(current.Rows) != len(old.Rows)+1 {
                return fmt.Errorf("PREPARED_UPGRADE_MIGRATION_HISTORY_CHANGED")
            }
        } else if !reflect.DeepEqual(old.Rows, current.Rows) {
            return fmt.Errorf("PREPARED_UPGRADE_BUSINESS_ROWS_CHANGED: %s", name)
        }
    }
    for name, table := range after {
        if _, exists := before[name]; exists { continue }
        if name != preparedUpgradeProofTable || len(table.Rows) != 0 {
            return fmt.Errorf("PREPARED_UPGRADE_UNEXPECTED_TABLE: %s", name)
        }
    }
    if table, exists := after[preparedUpgradeProofTable]; !exists || len(table.Rows) != 0 {
        return fmt.Errorf("PREPARED_UPGRADE_PROOF_TABLE_NOT_EMPTY")
    }
    return nil
}

func preparedUpgradeIntegrity(ctx context.Context, tx *sql.Tx) error {
    var integrity string
    if err := tx.QueryRowContext(ctx, "PRAGMA integrity_check").Scan(&integrity); err != nil || integrity != "ok" {
        return fmt.Errorf("PREPARED_UPGRADE_INTEGRITY")
    }
    rows, err := tx.QueryContext(ctx, "PRAGMA foreign_key_check")
    if err != nil { return err }
    bad := rows.Next()
    err = rows.Err()
    rows.Close()
    if bad || err != nil { return fmt.Errorf("PREPARED_UPGRADE_FOREIGN_KEY") }
    return nil
}

// The caller owns commit/rollback. Every check occurs inside this transaction,
// including target schema/triggers, exact old row multisets and migration24.
func preparedUpgradeDDL(ctx context.Context, tx *sql.Tx, raw []byte, before preparedUpgradeRows, sourceSchema, targetSchema string) error {
    if Digest(raw) != preparedUpgradeSQLHash { return fmt.Errorf("PREPARED_UPGRADE_SQL_HASH") }
    if err := preparedUpgradeVersions(tx, 23); err != nil { return err }
    schema, err := preparedUpgradeSchema(tx)
    if err != nil || schema != sourceSchema { return fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA") }
    current, err := preparedUpgradeSnapshot(tx)
    if err != nil || Hash(current) != Hash(before) { return fmt.Errorf("PREPARED_UPGRADE_BASELINE_CHANGED") }
    if _, err = tx.ExecContext(ctx, string(raw)); err != nil { return err }
    if _, err = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(24)"); err != nil { return err }
    after, err := preparedUpgradeSnapshot(tx)
    if err != nil { return err }
    if err = preparedUpgradeRowInvariant(before, after); err != nil { return err }
    if err = preparedUpgradeVersions(tx, 24); err != nil { return err }
    schema, err = preparedUpgradeSchema(tx)
    if err != nil || schema != targetSchema { return fmt.Errorf("PREPARED_UPGRADE_TARGET_SCHEMA") }
    return preparedUpgradeIntegrity(ctx, tx)
}

func preparedUpgradeTemplate(ctx context.Context, sqls [][]byte, contracts *Contracts) (preparedUpgradeSchemas, error) {
    var result preparedUpgradeSchemas
    if len(sqls) != 25 || Digest(sqls[23]) != preparedUpgradeSQLHash || Digest(sqls[24]) != upgradeQueueSessionHash {
        return result, fmt.Errorf("PREPARED_UPGRADE_TEMPLATE_INPUT")
    }
    stage, err := os.MkdirTemp("", ".researchos-backup-stage-")
    if err != nil { return result, err }
    defer backupDiscard(stage)
    db, err := store.Open(filepath.Join(stage, "template.sqlite"))
    if err != nil { return result, err }
    defer db.Close()
    for i, raw := range sqls[:23] {
        if _, err = db.ExecContext(ctx, string(raw)); err != nil { return result, err }
        if _, err = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil { return result, err }
    }
    if _, err = db.ExecContext(ctx, string(sqls[24])); err != nil { return result, err }
    if err = installClientSessionFence(ctx, db, false); err != nil { return result, err }
    if result.Source23, err = preparedUpgradeSchema(db); err != nil { return result, err }
    tx, err := db.BeginTx(ctx, nil)
    if err != nil { return result, err }
    if _, err = tx.ExecContext(ctx, string(sqls[23])); err == nil {
        result.Original24, err = preparedUpgradeSchema(tx)
    }
    rollbackErr := tx.Rollback()
    if err != nil { return result, err }
    if rollbackErr != nil { return result, rollbackErr }
    // This template is disposable; backupFence is never called on the original.
    if _, err = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); err != nil { return result, err }
    if result.Restored23, err = preparedUpgradeSchema(db); err != nil { return result, err }
    if _, err = db.ExecContext(ctx, string(sqls[23])); err != nil { return result, err }
    result.Restored24, err = preparedUpgradeSchema(db)
    return result, err
}

func preparedUpgradeDelta(before, after preparedUpgradeRows) Object {
    result := Object{}
    names := map[string]bool{}
    for name := range before { names[name] = true }
    for name := range after { names[name] = true }
    for name := range names {
        a, aok := before[name]
        b, bok := after[name]
        if aok == bok && reflect.DeepEqual(a, b) { continue }
        oldCounts, newCounts := map[string]int{}, map[string]int{}
        for _, h := range a.Rows { oldCounts[h]++ }
        for _, h := range b.Rows { newCounts[h]++ }
        removed, added := []string{}, []string{}
        for h, n := range oldCounts { for i := newCounts[h]; i < n; i++ { removed = append(removed, h) } }
        for h, n := range newCounts { for i := oldCounts[h]; i < n; i++ { added = append(added, h) } }
        sort.Strings(removed)
        sort.Strings(added)
        result[name] = Object{"before_columns": a.Columns, "after_columns": b.Columns, "before_present": aok, "after_present": bok,
            "before_rows": len(a.Rows), "after_rows": len(b.Rows), "removed_row_digests": removed, "added_row_digests": added}
    }
    return result
}

// Reuse the established exact restore transformation for all business tables.
// No numbered migration belongs to recovery: schema_migrations must remain23.
func preparedUpgradeRecoveryInvariant(before, after upgradeData, destination string) error {
    if Hash(before["schema_migrations"]) != Hash(after["schema_migrations"]) {
        return fmt.Errorf("PREPARED_UPGRADE_RECOVERY_CHANGED_MIGRATIONS")
    }
    a, b := upgradeData{}, upgradeData{}
    for name, rows := range before { if name != "schema_migrations" { a[name] = rows } }
    for name, rows := range after { if name != "schema_migrations" { b[name] = rows } }
    return upgradeConfigurationRecoveryInvariant(a, b, destination)
}

func preparedUpgradeRehearseDDL(ctx context.Context, db *sql.DB, raw []byte, before preparedUpgradeRows, sourceSchema, targetSchema string) error {
    tx, err := db.BeginTx(ctx, nil)
    if err != nil { return err }
    err = preparedUpgradeDDL(ctx, tx, raw, before, sourceSchema, targetSchema)
    rollbackErr := tx.Rollback()
    if err != nil { return err }
    if rollbackErr != nil { return rollbackErr }
    rows, err := preparedUpgradeSnapshot(db)
    if err != nil || Hash(rows) != Hash(before) { return fmt.Errorf("PREPARED_UPGRADE_ROLLBACK_ROWS") }
    schema, err := preparedUpgradeSchema(db)
    if err != nil || schema != sourceSchema { return fmt.Errorf("PREPARED_UPGRADE_ROLLBACK_SCHEMA") }
    tx, err = db.BeginTx(ctx, nil)
    if err != nil { return err }
    defer tx.Rollback()
    if err = preparedUpgradeDDL(ctx, tx, raw, before, sourceSchema, targetSchema); err != nil { return err }
    return tx.Commit()
}

func preparedUpgradeProgramHashes(opt LocalUpgradeOptions, currentIsTarget bool) (string, string, error) {
    source, err := os.ReadFile(opt.SourceProgram)
    if err != nil { return "", "", err }
    target, err := os.ReadFile(opt.TargetProgram)
    if err != nil { return "", "", err }
    program, err := os.Executable()
    if err != nil { return "", "", err }
    current, err := os.ReadFile(program)
    if err != nil { return "", "", err }
    want := Digest(source)
    if currentIsTarget { want = Digest(target) }
    if Digest(current) != want { return "", "", fmt.Errorf("PREPARED_UPGRADE_MATCHING_PROGRAM_REQUIRED") }
    return Digest(source), Digest(target), nil
}

func upgradePreparedAbandonmentLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (report RestoreReport, err error) {
    report = RestoreReport{Started: Now(), Status: "FAILED"}
    if opt.Plan != PreparedAbandonmentSchemaUpgradePlan { return report, fmt.Errorf("PREPARED_UPGRADE_PLAN_UNSUPPORTED") }
    if err := upgradePaths(&opt); err != nil { return report, err }
    lease, err := acquirePreparedUpgradeRootLease(filepath.Dir(opt.Source))
    if err != nil { return report, err }
    defer func() {
        if closeErr := lease.Close(); closeErr != nil && err == nil { err = closeErr }
    }()
    sourceRelease, _, err := preparedUpgradeRelease(opt.SourceRoot, 23)
    if err != nil { return report, err }
    targetRelease, sqls, err := preparedUpgradeRelease(opt.TargetRoot, 24)
    if err != nil { return report, err }
    sourceProgram, targetProgram, err := preparedUpgradeProgramHashes(opt, false)
    if err != nil { return report, err }
    contracts, err := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
    if err != nil { return report, err }
    schemas, err := preparedUpgradeTemplate(ctx, sqls, contracts)
    if err != nil { return report, err }
    key, err := os.ReadFile(opt.KeyFile)
    if err != nil || len(key) != 32 { return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE") }
    defer clear(key)
    db, err := upgradeOpenExclusive(ctx, opt.Source)
    if err != nil { return report, err }
    defer db.Close()
    if err = preparedUpgradeVersions(db, 23); err != nil { return report, err }
    schema, err := preparedUpgradeSchema(db)
    if err != nil || schema != schemas.Source23 { return report, fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA") }
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
        Schema: "researchos.prepared-abandonment-schema-rehearsal.v1", Plan: opt.Plan, Status: "IN_PROGRESS",
        Options: opt, OptionsHash: Digest(optionsRaw), SourceProgramHash: sourceProgram, TargetProgramHash: targetProgram,
        SourceInventoryHash: Hash(sourceRelease), TargetInventoryHash: Hash(targetRelease),
        SourceSchema: schemas.Source23, TargetSchema: schemas.Original24, RestoredSchema: schemas.Restored23,
        RestoredTargetSchema: schemas.Restored24, SQLHash: preparedUpgradeSQLHash, OriginalRowsHash: Hash(original),
        ReleaseAuthority: "RECORDED_PROGRAM_PINS_REQUIRE_SEPARATE_NATIVE_APPLY_AUTHORITY",
    }
    plan := Object{"id": opt.Plan, "source_versions": upgradeVersions(23), "target_versions": upgradeVersions(24),
        "source_schema_hash": schemas.Source23, "original_target_schema_hash": schemas.Original24,
        "restored_target_schema_hash": schemas.Restored24, "source_database_logical_hash": Hash(original),
        "source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
        "source_program_hash": sourceProgram, "target_program_hash": targetProgram, "migration_sql_hash": preparedUpgradeSQLHash,
        "options_hash": receipt.OptionsHash}
    purpose := Object{"kind": "SAME_HOST_PREPARED_ABANDONMENT_SCHEMA_REHEARSAL", "scope": "IsolatedRestoreOnly",
        "plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
        "protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
        "protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
        "external_actions_dispatched": 0, "automatic_promotion": false, "original_business_mutation": false}
    receipt.BackupPurpose = purpose
    policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose,
        validate: guard.refresh, allowProtected: guard.artifact}
    checkSource := func() error {
        if err := lease.Check(); err != nil { return err }
        current, err := preparedUpgradeSnapshot(db)
        if err != nil || Hash(current) != Hash(original) { return fmt.Errorf("PREPARED_UPGRADE_SOURCE_DRIFT") }
        currentSchema, err := preparedUpgradeSchema(db)
        if err != nil || currentSchema != schemas.Source23 { return fmt.Errorf("PREPARED_UPGRADE_SOURCE_SCHEMA_DRIFT") }
        a, _, err := preparedUpgradeRelease(opt.SourceRoot, 23)
        if err != nil || Hash(a) != Hash(sourceRelease) { return fmt.Errorf("PREPARED_UPGRADE_RELEASE_CHANGED") }
        b, _, err := preparedUpgradeRelease(opt.TargetRoot, 24)
        if err != nil || Hash(b) != Hash(targetRelease) { return fmt.Errorf("PREPARED_UPGRADE_RELEASE_CHANGED") }
        x, y, err := preparedUpgradeProgramHashes(opt, false)
        if err != nil || x != sourceProgram || y != targetProgram { return fmt.Errorf("PREPARED_UPGRADE_PROGRAM_CHANGED") }
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
    if _, err = (&Service{DB: db, Contracts: contracts}).createBackupPolicy(ctx, opt.Snapshot, key, policy); err != nil { return report, err }
    // No skipRecovery and no migration callback in generic RestoreOptions.
    report, err = restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination,
        RestoreOptions{Key: key, SupportedMigrations: upgradeVersions(23), Contracts: contracts}, policy)
    if err != nil { return report, err }
    if err = checkSource(); err != nil { return report, err }
    rawManifest, err := os.ReadFile(filepath.Join(opt.Snapshot, "manifest.json"))
    if err != nil { return report, err }
    receipt.BackupManifestHash, receipt.BackupManifestBytes = Digest(rawManifest), int64(len(rawManifest))
    receipt.Status, receipt.OriginalUnchanged, receipt.RestoreReport = "ISOLATED_REHEARSAL_COMPLETE_ORIGINAL_UNCHANGED", true, report
    if err = backupWrite(filepath.Join(opt.Destination, preparedUpgradeReceiptName), Bytes(receipt)); err != nil { return report, err }
    report.Recovery["prepared_abandonment_rehearsal_receipt"] = Object{"path": filepath.Join(opt.Destination, preparedUpgradeReceiptName), "sha256": Digest(Bytes(receipt))}
    return report, nil
}

func preparedUpgradeConcreteVerifier() upgradeVerifier {
    return upgradeVerifier{
        provider: &protectedstore.FrozenProvider{},
        summary: func(ctx context.Context) (protectedstore.SafeSummary, error) {
            if err := ctx.Err(); err != nil { return protectedstore.SafeSummary{}, err }
            return protectedstore.QueryFrozenService("aggregate")
        },
    }
}

// Package-local mirror is byte-identical to the release 0024 SQL. Its digest is
// checked before building the expected schema; database rows cannot redefine it.
//go:embed contracts/prepared_run_abandonment.sql
var backupPreparedAbandonmentSQL []byte

var backupPreparedAbandonmentSchemaOnce sync.Once
var backupPreparedAbandonmentExpected []Object
var backupPreparedAbandonmentSchemaError error

const preparedUpgradeSchemaObjects = `SELECT type,name,tbl_name,sql FROM sqlite_master
WHERE tbl_name='runtime_prepared_abandonments'
OR name IN ('runtime_dispatch_abandoned_no_update','runtime_prepared_abandonment_terminal_insert',
'runtime_prepared_abandoned_run_immutable','runtime_prepared_abandoned_task_no_restart')
ORDER BY type,name`

// Current24 is additive; the existing config/queue validators still run.
// This validates exactly the table, autoindexes and six triggers from SQL24.
func backupPreparedAbandonmentSchema(db *sql.DB) error {
    if err := preparedUpgradeVersions(db, 24); err != nil { return err }
    backupPreparedAbandonmentSchemaOnce.Do(func() {
        if Digest(backupPreparedAbandonmentSQL) != preparedUpgradeSQLHash {
            backupPreparedAbandonmentSchemaError = fmt.Errorf("BACKUP_PREPARED_ABANDONMENT_SQL_HASH")
            return
        }
        expected, err := sql.Open("sqlite", ":memory:")
        if err != nil { backupPreparedAbandonmentSchemaError = err; return }
        defer expected.Close()
        expected.SetMaxOpenConns(1)
        // Only dependencies for parsing trigger bodies; these stubs are excluded
        // from the fingerprint. No stored business row enters this template.
        _, err = expected.Exec("CREATE TABLE runtime_dispatches(project TEXT,run TEXT,epoch INTEGER,state TEXT,worker TEXT,journal_locator TEXT,identity TEXT,observation_sequence INTEGER,observation_hash TEXT,PRIMARY KEY(project,run,epoch)); CREATE TABLE domain_objects(project TEXT,kind TEXT,id TEXT,body TEXT);")
        if err == nil { _, err = expected.Exec(string(backupPreparedAbandonmentSQL)) }
        if err == nil { backupPreparedAbandonmentExpected, err = configurationBackupRows(expected, preparedUpgradeSchemaObjects) }
        backupPreparedAbandonmentSchemaError = err
    })
    if backupPreparedAbandonmentSchemaError != nil { return backupPreparedAbandonmentSchemaError }
    current, err := configurationBackupRows(db, preparedUpgradeSchemaObjects)
    if err != nil { return err }
    if Hash(current) != Hash(backupPreparedAbandonmentExpected) {
        return fmt.Errorf("BACKUP_PREPARED_ABANDONMENT_SCHEMA")
    }
    return nil
}
