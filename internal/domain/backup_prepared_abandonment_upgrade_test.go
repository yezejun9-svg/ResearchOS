package domain

import (
    "context"
    "database/sql"
    "os"
    "path/filepath"
    "reflect"
    "strings"
    "testing"

    "researchos.local/research-os/internal/store"
)

func preparedUpgradeTestRelease(t *testing.T, n int) string {
    t.Helper()
    root := configurationUpgradeReleaseFixture(t, 23)
    if n == 24 {
        raw, err := os.ReadFile("../../migrations/sqlite/0024_prepared_run_abandonment.sql")
        if err != nil { t.Fatal(err) }
        if err = os.WriteFile(filepath.Join(root, "migrations/sqlite/0024_prepared_run_abandonment.sql"), raw, 0600); err != nil { t.Fatal(err) }
    }
    if _, _, err := preparedUpgradeRelease(root, n); err != nil { t.Fatal(err) }
    return root
}

func preparedUpgradeTestDB(t *testing.T) (*sql.DB, []byte, preparedUpgradeSchemas) {
    t.Helper()
    ctx := context.Background()
    root := preparedUpgradeTestRelease(t, 24)
    _, sqls, err := preparedUpgradeRelease(root, 24)
    if err != nil { t.Fatal(err) }
    contracts, err := LoadContracts(filepath.Join(root, "spec/v2.0/contracts"))
    if err != nil { t.Fatal(err) }
    schemas, err := preparedUpgradeTemplate(ctx, sqls, contracts)
    if err != nil { t.Fatal(err) }
    db, err := store.Open(filepath.Join(t.TempDir(), "source23.sqlite"))
    if err != nil { t.Fatal(err) }
    t.Cleanup(func() { db.Close() })
    for i, raw := range sqls[:23] {
        if _, err = db.ExecContext(ctx, string(raw)); err != nil { t.Fatal(err) }
        if _, err = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil { t.Fatal(err) }
    }
    if _, err = db.ExecContext(ctx, string(sqls[24])); err != nil { t.Fatal(err) }
    if err = installClientSessionFence(ctx, db, false); err != nil { t.Fatal(err) }
    // These are storage-invariant fixtures, not domain acceptance fixtures.
    // Deliberately retain JSON spacing and a >2^53 decimal string.
    statements := []string{
        `INSERT INTO auth_principals(id,roles,can_create_project) VALUES('migration-fixture','["OWNER"]',1)`,
        `INSERT INTO auth_credentials(token_hash,principal,expires_at) VALUES('fixture-digest','migration-fixture','2099-01-01T00:00:00Z')`,
        `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Run','r',7,'{ "status": "QUEUED", "task_id":"t", "lease_epoch":1, "lease_token_hash":"fixture-only", "native_birth":"134359521876434319" }')`,
        `INSERT INTO domain_objects(project,kind,id,revision,body) VALUES('p','Task','t',9,'{"status":"RUNNING","active_run_id":"r"}')`,
        `INSERT INTO runtime_dispatches(project,run,epoch,dispatch_key,manifest,manifest_hash,state,prepared_at,updated_at) VALUES('p','r',1,'fixture-dispatch','{ "prepared": true }','fixture-manifest','PREPARED','fixture-time','fixture-time')`,
        `INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at,sealed) VALUES('fixture-blob','p','migration-fixture',x'0001fffe0000','fixture-content','2099-01-01T00:00:00Z',1)`,
    }
    for _, stmt := range statements { if _, err = db.Exec(stmt); err != nil { t.Fatal(err) } }
    return db, sqls[23], schemas
}

func TestPreparedUpgradeTypedRowsPreserveLosslessStorage(t *testing.T) {
    inputs := [][]any{
        {int64(9007199254740992)}, {int64(9007199254740993)},
        {"9007199254740993"}, {[]byte("9007199254740993")},
        {nil}, {""}, {[]byte{}}, {float64(1)}, {int64(1)},
        {"a", "bc"}, {"ab", "c"},
    }
    seen := map[string]bool{}
    for _, input := range inputs {
        h, err := preparedUpgradeRowHash(input)
        if err != nil || seen[h] { t.Fatalf("lossy/ambiguous typed row %T: %s %v", input[0], h, err) }
        seen[h] = true
    }
}

func TestPreparedUpgradeDDLOnlyPreservesQueuedRunCredentialsAndSealedBytes(t *testing.T) {
    db, raw, schemas := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    tx, err := db.Begin()
    if err != nil { t.Fatal(err) }
    defer tx.Rollback()
    if err = preparedUpgradeDDL(context.Background(), tx, raw, before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    if err = tx.Commit(); err != nil { t.Fatal(err) }
    after, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRowInvariant(before, after); err != nil { t.Fatal(err) }
    var run, task, dispatch string
    var revoked, proofs int
    for query, dest := range map[string]*string{
        `SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Run' AND id='r'`: &run,
        `SELECT json_extract(body,'$.status') FROM domain_objects WHERE kind='Task' AND id='t'`: &task,
        `SELECT state FROM runtime_dispatches WHERE run='r'`: &dispatch,
    } { if err = db.QueryRow(query).Scan(dest); err != nil { t.Fatal(err) } }
    if err = db.QueryRow("SELECT revoked FROM auth_credentials").Scan(&revoked); err != nil { t.Fatal(err) }
    if err = db.QueryRow("SELECT count(*) FROM runtime_prepared_abandonments").Scan(&proofs); err != nil { t.Fatal(err) }
    if run != "QUEUED" || task != "RUNNING" || dispatch != "PREPARED" || revoked != 0 || proofs != 0 {
        t.Fatalf("business mutation: %s/%s/%s credential=%d proofs=%d", run, task, dispatch, revoked, proofs)
    }
    var frozen int
    if err = db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND name IN ('runtime_dispatch_manifest_frozen','runtime_dispatch_no_delete','content_immutable','runtime_prepared_abandonments_immutable','runtime_prepared_abandonments_no_delete','runtime_dispatch_abandoned_no_update','runtime_prepared_abandonment_terminal_insert','runtime_prepared_abandoned_run_immutable','runtime_prepared_abandoned_task_no_restart')").Scan(&frozen); err != nil || frozen != 9 {
        t.Fatal("existing/new trigger inventory", frozen, err)
    }
    if _, err = db.Exec("UPDATE runtime_dispatches SET manifest='{}' WHERE run='r'"); err == nil {
        t.Fatal("existing immutable manifest trigger disabled")
    }
    // A proof cannot be inserted for the still-QUEUED tuple.
    if _, err = db.Exec("INSERT INTO runtime_prepared_abandonments VALUES('p','t','r','runtime',1,'fixture-dispatch','fixture-manifest','owner','proof','{}','FAILED_NOT_DISPATCHED_ACCOUNTING_UNKNOWN',0,'now')"); err == nil {
        t.Fatal("new terminal-state trigger failed")
    }
    unchanged, err := preparedUpgradeSnapshot(db)
    if err != nil || Hash(unchanged) != Hash(after) { t.Fatal("rejected writes changed rows", err) }
}

func TestPreparedUpgradeDDLRejectsAndRollsBack(t *testing.T) {
    for _, fault := range []string{"wrong-sql", "wrong-source-schema", "wrong-target-schema", "stale-business-baseline"} {
        t.Run(fault, func(t *testing.T) {
            db, raw, schemas := preparedUpgradeTestDB(t)
            before, err := preparedUpgradeSnapshot(db)
            if err != nil { t.Fatal(err) }
            supplied := before
            source, target := schemas.Source23, schemas.Original24
            expected := ""
            switch fault {
            case "wrong-sql": raw = append(append([]byte{}, raw...), '\n'); expected = "PREPARED_UPGRADE_SQL_HASH"
            case "wrong-source-schema": source = "wrong"; expected = "PREPARED_UPGRADE_SOURCE_SCHEMA"
            case "wrong-target-schema": target = "wrong"; expected = "PREPARED_UPGRADE_TARGET_SCHEMA"
            case "stale-business-baseline":
                supplied = preparedUpgradeRows{}
                for name, rows := range before { supplied[name] = rows }
                old := supplied["auth_credentials"]
                old.Rows = []string{"changed"}
                supplied["auth_credentials"] = old
                expected = "PREPARED_UPGRADE_BASELINE_CHANGED"
            }
            tx, err := db.Begin()
            if err != nil { t.Fatal(err) }
            err = preparedUpgradeDDL(context.Background(), tx, raw, supplied, source, target)
            if err == nil || !strings.Contains(err.Error(), expected) { _ = tx.Rollback(); t.Fatalf("wanted %s: %v", expected, err) }
            if err = tx.Rollback(); err != nil { t.Fatal(err) }
            after, err := preparedUpgradeSnapshot(db)
            if err != nil || Hash(before) != Hash(after) { t.Fatal("rollback changed rows", err) }
            schema, err := preparedUpgradeSchema(db)
            if err != nil || schema != schemas.Source23 { t.Fatal("rollback retained DDL", err) }
            if err = preparedUpgradeVersions(db, 23); err != nil { t.Fatal(err) }
        })
    }
}

func TestPreparedUpgradeRehearsalDDLProvesRollback(t *testing.T) {
    db, raw, schemas := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRehearseDDL(context.Background(), db, raw, before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    after, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRowInvariant(before, after); err != nil { t.Fatal(err) }
    if err = preparedUpgradeVersions(db, 24); err != nil { t.Fatal(err) }
}

func TestPreparedUpgradeReleaseRejectsMissingExtraAndChangedSQL(t *testing.T) {
    for _, fault := range []string{"missing24", "extra25", "changed24", "source-has24"} {
        t.Run(fault, func(t *testing.T) {
            root := preparedUpgradeTestRelease(t, 24)
            path := filepath.Join(root, "migrations/sqlite/0024_prepared_run_abandonment.sql")
            count := 24
            switch fault {
            case "missing24": if err := os.Remove(path); err != nil { t.Fatal(err) }
            case "extra25": if err := os.WriteFile(filepath.Join(root, "migrations/sqlite/0025_unreviewed.sql"), []byte("SELECT 1;"), 0600); err != nil { t.Fatal(err) }
            case "changed24": if err := os.WriteFile(path, []byte("CREATE TABLE unsafe(x);"), 0600); err != nil { t.Fatal(err) }
            case "source-has24": count = 23
            }
            if _, _, err := preparedUpgradeRelease(root, count); err == nil { t.Fatal("unreviewed inventory accepted") }
        })
    }
}

func TestPreparedUpgradeBusinessInvariantRejectsAnyOldRowMutation(t *testing.T) {
    db, raw, schemas := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRehearseDDL(context.Background(), db, raw, before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    after, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    for name, old := range before {
        if len(old.Rows) == 0 { continue }
        t.Run(name, func(t *testing.T) {
            changed := preparedUpgradeRows{}
            for key, value := range after { changed[key] = value }
            value := changed[name]
            value.Rows = append([]string{}, value.Rows...)
            for i, hash := range value.Rows {
                if hash == old.Rows[0] { value.Rows[i] = "changed-row"; break }
            }
            changed[name] = value
            if err := preparedUpgradeRowInvariant(before, changed); err == nil { t.Fatal("old row mutation accepted") }
        })
    }
    if !reflect.DeepEqual(before["auth_credentials"], after["auth_credentials"]) { t.Fatal("credential changed") }
}

func TestPreparedUpgradeBackupRecognizesOnlyExact24Schema(t *testing.T) {
    db, raw, schemas := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRehearseDDL(context.Background(), db, raw, before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    if present, err := backupConfigurationPresent(db); err != nil || !present { t.Fatal("valid24 refused", present, err) }
    if _, err = db.Exec("DROP TRIGGER runtime_prepared_abandonments_no_delete"); err != nil { t.Fatal(err) }
    if _, err = backupConfigurationPresent(db); err == nil || !strings.Contains(err.Error(), "BACKUP_PREPARED_ABANDONMENT_SCHEMA") { t.Fatal("altered24 accepted", err) }
}

func TestPreparedUpgradeBackupRejectsFuture25(t *testing.T) {
    db, raw, schemas := preparedUpgradeTestDB(t)
    before, err := preparedUpgradeSnapshot(db)
    if err != nil { t.Fatal(err) }
    if err = preparedUpgradeRehearseDDL(context.Background(), db, raw, before, schemas.Source23, schemas.Original24); err != nil { t.Fatal(err) }
    if _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(25)"); err != nil { t.Fatal(err) }
    if _, err = backupConfigurationPresent(db); err == nil || !strings.Contains(err.Error(), "BACKUP_CONFIGURATION_VERSION") { t.Fatal("future25 accepted", err) }
}
