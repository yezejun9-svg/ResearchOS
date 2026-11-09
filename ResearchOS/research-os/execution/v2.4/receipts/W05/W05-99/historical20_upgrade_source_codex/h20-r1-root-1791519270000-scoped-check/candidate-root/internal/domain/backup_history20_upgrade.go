package domain

// History20SchemaUpgradePlan upgrades the exact numbered schema20 base into an
// isolated schema21 candidate. It does not install additive client sessions,
// qualify a release binary, perform cutover, or authorize a Product Owner.
import (
 "context"
 "database/sql"
 "fmt"
 "os"
 "path/filepath"
 "reflect"
 "strings"

 "researchos.local/research-os/internal/store"
)

const History20SchemaUpgradePlan = "schema20-to21-research-pending-windows-v1"
const upgradeHistory20SQLHash = "sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32"
var upgradeHistory20Tables = map[string]bool{"research_pending_windows": true}

func upgradeHistory20Release(root string, count int) (Object, [][]byte, error) {
	if count != 20 && count != 21 {
		return nil, nil, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	files, e := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql")) // release inputs are the numbered migrations only; unnumbered additive files (e.g. next_v24_sessions.sql) are applied through their own single-transaction path
	if e != nil || len(files) != count {
		return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS: require exact 1..%d", count)
	}
	manifest := Object{}
	sqls := make([][]byte, count)
	for i, file := range files {
		name := filepath.Base(file)
		if len(name) < 5 || name[:4] != fmt.Sprintf("%04d", i+1) {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS")
		}
		raw, e := os.ReadFile(file)
		expected := upgradeMigrationHashes[name]
		if name == "0021_research_pending_windows.sql" { expected = upgradeHistory20SQLHash }
		if e != nil || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_HASH: %s", name)
		}
		manifest["migrations/sqlite/"+name] = Digest(raw)
		sqls[i] = raw
	}
	for name, expected := range map[string]string{
		"domain.schema.json": "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
		"openapi.json":       "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
	} {
		raw, e := os.ReadFile(filepath.Join(root, "spec/v2.0/contracts", name))
		if e != nil || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("UPGRADE_CONTRACT_HASH: %s", name)
		}
		manifest["spec/v2.0/contracts/"+name] = expected
	}
	return manifest, sqls, nil
}

func upgradeHistory20Template(ctx context.Context, sqls [][]byte, contracts *Contracts) (string, string, error) {
	if len(sqls) != 21 {
		return "", "", fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	stage, e := os.MkdirTemp("", ".researchos-backup-stage-")
	if e != nil {
		return "", "", e
	}
	defer backupDiscard(stage)
	db, e := store.Open(filepath.Join(stage, "schema.sqlite"))
	if e != nil {
		return "", "", e
	}
	defer db.Close()
	for i, raw := range sqls[:20] {
		if _, e = db.ExecContext(ctx, string(raw)); e != nil {
			return "", "", e
		}
		if _, e = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
			return "", "", e
		}
	}
	before, e := backupSchema(db)
	if e != nil {
		return "", "", e
	}
	if _, e = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); e != nil {
		return "", "", e
	}
	if e = upgradeHistory20Migration(ctx, db, sqls[20]); e != nil {
		return "", "", e
	}
	after, e := backupSchema(db)
	return before, after, e
}

func upgradeHistory20Migration(ctx context.Context, db *sql.DB, raw []byte) error {
	if Digest(raw) != upgradeHistory20SQLHash {
		return fmt.Errorf("UPGRADE_MIGRATION_HASH")
	}
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(20)) {
		return fmt.Errorf("UPGRADE_SOURCE_VERSION")
	}
	before, e := upgradeRows(db)
	if e != nil {
		return e
	}
	tx, e := db.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if _, e = tx.ExecContext(ctx, string(raw)); e != nil {
		return e
	}
	if _, e = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(21)"); e != nil {
		return e
	}
	after, e := upgradeQueueRows(tx)
	if e != nil {
		return e
	}
	for table, rows := range before {
		if table == "schema_migrations" {
			continue
		}
		if Hash(rows) != Hash(after[table]) {
			return fmt.Errorf("UPGRADE_MIGRATION_MUTATED_HISTORY: %s", table)
		}
	}
	for table := range upgradeHistory20Tables {
		if rows, ok := after[table]; !ok || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_HISTORY20_PENDING_NOT_EMPTY: %s", table)
		}
	}
	for table := range after {
		if _, ok := before[table]; !ok && !upgradeHistory20Tables[table] {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE: %s", table)
		}
	}
	var integrity string
	if e = tx.QueryRowContext(ctx, "PRAGMA integrity_check").Scan(&integrity); e != nil || integrity != "ok" {
		return fmt.Errorf("UPGRADE_TARGET_INTEGRITY")
	}
	check, e := tx.QueryContext(ctx, "PRAGMA foreign_key_check")
	if e != nil {
		return e
	}
	bad := check.Next()
	e = check.Err()
	check.Close()
	if bad || e != nil {
		return fmt.Errorf("UPGRADE_TARGET_REFERENCE")
	}
	return tx.Commit()
}

func upgradeHistory20Local(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {
	report := RestoreReport{Started: Now(), Status: "FAILED"}
	if e := upgradePaths(&opt); e != nil {
		return report, e
	}
	sourceRelease, _, e := upgradeHistory20Release(opt.SourceRoot, 20)
	if e != nil {
		return report, e
	}
	targetRelease, sqls, e := upgradeHistory20Release(opt.TargetRoot, 21)
	if e != nil {
		return report, e
	}
	contracts, e := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if e != nil {
		return report, e
	}
	expectedSourceSchema, expectedTargetSchema, e := upgradeHistory20Template(ctx, sqls, contracts)
	if e != nil {
		return report, e
	}
	key, e := os.ReadFile(opt.KeyFile)
	if e != nil || len(key) != 32 {
		return report, fmt.Errorf("BACKUP_KEY_UNAVAILABLE")
	}
	defer clear(key)
	db, e := upgradeOpenExclusive(ctx, opt.Source)
	if e != nil {
		return report, e
	}
	defer db.Close() // The native source lock spans snapshot through publication.
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(20)) {
		return report, fmt.Errorf("UPGRADE_SOURCE_VERSION: require exact 1..20")
	}
	schema, e := backupSchema(db)
	if e != nil || schema != expectedSourceSchema {
		return report, fmt.Errorf("UPGRADE_SOURCE_SCHEMA")
	}
	guard := &upgradeQueueProtection{upgradeProtection: upgradeProtection{ctx: ctx, verifier: verifier}, contracts: contracts}
	if e = guard.refresh(db); e != nil {
		return report, e
	}
	// Reject any host-side protected storage before reading ordinary BLOB rows
	// for the logical inventory or creating a snapshot.
	original, e := upgradeRows(db)
	if e != nil {
		return report, e
	}
	workspaceIdentity, e := upgradeQueueWorkspaceIdentity(db, opt)
	if e != nil {
		return report, e
	}
	programHashes := Object{}
	for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
		raw, e := os.ReadFile(path)
		if e != nil {
			return report, e
		}
		programHashes[name] = Digest(raw)
	}
	host, e := os.Hostname()
	if e != nil || host == "" {
		return report, fmt.Errorf("UPGRADE_HOST_UNAVAILABLE")
	}
	plan := Object{"id": opt.Plan, "source_shape": "HISTORICAL20_NUMBERED_BASE_ONLY", "continuation": "SESSION_INSTALLATION_AND_21_TO24_NOT_IMPLEMENTED_BY_THIS_PLAN", "source_versions": versions, "target_versions": upgradeVersions(21),
		"source_schema_hash": schema, "target_schema_with_restore_fence_hash": expectedTargetSchema,
		"source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
		"migration_sql_hash": Digest(sqls[20]), "source_database_logical_hash": Hash(original),
		"source_release_manifest": sourceRelease, "target_release_manifest": targetRelease, "operational_row_manifest_hash": guard.operationalHash,
		"workspace_identity_manifest_hash": Hash(workspaceIdentity),
		"program_hashes":                   programHashes, "host_binding_hash": Hash(host), "service_summary_hash": guard.summaryHash,
		"source_path_hash": Hash(opt.Source), "target_path_hash": Hash(opt.Destination)}
	purpose := Object{"kind": "SAME_HOST_CONTROL_PLANE_UPGRADE", "scope": "SameHostExternalReferenceContinuityOnly",
		"plan": plan, "plan_hash": Hash(plan), "protected_reference_versions": guard.count,
		"protected_reference_digest": guard.referencesHash, "protected_payloads_included": false,
		"protected_payloads_revalidated": false, "recovery_dependency": "ORIGINAL_PROTECTED_SERVICE",
		"external_actions_dispatched": 0, "source_ownership": "SQLITE_EXCLUSIVE_UNTIL_TARGET_PUBLICATION",
		"cutover_requirement": "Keep original application and workers stopped until independent review and single-writer cutover; do not run both authorities."}
	policy := &backupPolicy{format: localUpgradeFormat, databaseName: "researchos.sqlite", purpose: purpose, validate: guard.refresh, allowProtected: guard.artifact}
	policy.preserveHistory20UpgradeWorkspaces = func(restored *sql.DB) error {
		if e := guard.refresh(restored); e != nil {
			return e
		}
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		identity, e := upgradeQueueWorkspaceIdentity(restored, opt)
		if e != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		return nil
	}
	policy.beforeRecovery = func(restored *sql.DB) error {
		rows, e := upgradeRows(restored)
		if e != nil || Hash(rows) != Hash(original) {
			return fmt.Errorf("UPGRADE_SNAPSHOT_HISTORY_MISMATCH")
		}
		return nil
	}
	policy.afterRecovery = func(restored *sql.DB) error {
		identity, err := upgradeQueueWorkspaceIdentity(restored, opt)
		if err != nil || Hash(identity) != Hash(workspaceIdentity) {
			return fmt.Errorf("UPGRADE_WORKSPACE_IDENTITY_CHANGED")
		}
		currentSchema, e := backupSchema(restored)
		if e != nil || currentSchema != expectedTargetSchema {
			return fmt.Errorf("UPGRADE_TARGET_SCHEMA")
		}
		rows, e := upgradeRows(restored)
		if e != nil {
			return e
		}
		if e = upgradeHistory20RecoveryInvariant(original, rows, opt.Destination, true); e != nil {
			return e
		}
		sourceNow, e := upgradeRows(db)
		if e != nil || Hash(sourceNow) != Hash(original) {
			return fmt.Errorf("UPGRADE_SOURCE_DRIFT")
		}
		// Release roots and binary files must not change during the operation.
		for _, entry := range []struct {
			root string
			n    int
			hash string
		}{
			{opt.SourceRoot, 20, Hash(sourceRelease)}, {opt.TargetRoot, 21, Hash(targetRelease)},
		} {
			current, _, err := upgradeHistory20Release(entry.root, entry.n)
			if err != nil || Hash(current) != entry.hash {
				return fmt.Errorf("UPGRADE_RELEASE_CHANGED")
			}
		}
		for name, path := range map[string]string{"source": opt.SourceProgram, "target": opt.TargetProgram} {
			raw, err := os.ReadFile(path)
			if err != nil || Digest(raw) != programHashes[name] {
				return fmt.Errorf("UPGRADE_PROGRAM_CHANGED")
			}
		}
		return ctx.Err()
	}
	svc := &Service{DB: db, Contracts: contracts}
	if _, e = svc.createBackupPolicy(ctx, opt.Snapshot, key, policy); e != nil {
		return report, e
	}
	return restoreBackupPolicy(ctx, opt.Snapshot, opt.Destination, RestoreOptions{
		Key: key, SupportedMigrations: versions, Contracts: contracts,
		Migration: func(ctx context.Context, target *sql.DB) error {
			// Recovery is checked before any numbered migration executes. The roots
			// still point inside the unpublished restore stage at this point.
			var sequence int
			var name, databasePath string
			if e := target.QueryRowContext(ctx, "PRAGMA database_list").Scan(&sequence, &name, &databasePath); e != nil { return e }
			recovered, e := upgradeRows(target)
			if e != nil { return e }
			if e = upgradeHistory20RecoveryInvariant(original, recovered, filepath.Dir(databasePath), false); e != nil { return e }
			return upgradeHistory20Migration(ctx, target, sqls[20])
		},
	}, policy)
}

func upgradeHistory20RecoveryInvariant(before, after upgradeData, destination string, migrated bool) error {
	active := map[string]Object{}
	projectRuns := map[string]int64{}
	oldObjects, newObjects := map[string]Object{}, map[string]Object{}
	for _, row := range before["domain_objects"] {
		oldObjects[upgradeObjectKey(row)] = row
		if row["kind"] == "Run" {
			body, e := Decode([]byte(Str(row, "body")))
			if e != nil {
				return e
			}
			if strings.Contains("|QUEUED|STARTING|RUNNING|CANCEL_REQUESTED|RECONCILING|LOST|", "|"+Str(body, "status")+"|") {
				active[upgradeObjectKey(row)] = body
				projectRuns[Str(row, "project")]++
			}
		}
	}
	for _, row := range after["domain_objects"] {
		newObjects[upgradeObjectKey(row)] = row
	}
	newEvents := map[string]bool{}
	for key, old := range oldObjects {
		current, ok := newObjects[key]
		if !ok {
			return fmt.Errorf("UPGRADE_CURRENT_OBJECT_LOST")
		}
		body, e := Decode([]byte(Str(current, "body")))
		if e != nil {
			return e
		}
		prior, e := Decode([]byte(Str(old, "body")))
		if e != nil {
			return e
		}
		if run, ok := active[key]; ok {
			status := "RECONCILING"
			if run["status"] == "CANCEL_REQUESTED" {
				status = "CANCEL_REQUESTED"
			}
			oldRev, _ := Num(prior, "revision")
			newRev, _ := Num(body, "revision")
			fields := []string{"status", "lease_token_hash", "lease_expires_at", "revision", "updated_at"}
			if newRev != oldRev+1 || body["status"] != status || body["lease_expires_at"] != "1970-01-01T00:00:00Z" || body["lease_token_hash"] == prior["lease_token_hash"] || Hash(upgradeWithout(body, fields...)) != Hash(upgradeWithout(prior, fields...)) {
				return fmt.Errorf("UPGRADE_RUN_FENCE_INVALID")
			}
		} else if old["kind"] == "ProjectState" && projectRuns[Str(old, "project")] != 0 {
			n := projectRuns[Str(old, "project")]
			for _, field := range []string{"revision", "event_sequence"} {
				a, _ := Num(prior, field)
				b, _ := Num(body, field)
				if b != a+n {
					return fmt.Errorf("UPGRADE_STATE_AUDIT_INVALID")
				}
			}
			if Hash(upgradeWithout(body, "revision", "updated_at", "event_sequence")) != Hash(upgradeWithout(prior, "revision", "updated_at", "event_sequence")) {
				return fmt.Errorf("UPGRADE_STATE_MUTATED")
			}
		} else if Hash(current) != Hash(old) {
			return fmt.Errorf("UPGRADE_CURRENT_OBJECT_MUTATED: %s", Str(old, "kind"))
		}
	}
	for key, row := range newObjects {
		if _, existed := oldObjects[key]; existed {
			continue
		}
		body, e := Decode([]byte(Str(row, "body")))
		if e != nil || row["kind"] != "EventEnvelope" || body["actor_id"] != "restore-local-admin" || body["event_type"] != "RUN_CHANGED" {
			return fmt.Errorf("UPGRADE_UNEXPECTED_NEW_OBJECT")
		}
		ref, ok := body["aggregate_ref"].(map[string]any)
		if !ok || active[Str(row, "project")+"/Run/"+Str(ref, "id")] == nil {
			return fmt.Errorf("UPGRADE_UNEXPECTED_AUDIT_EVENT")
		}
		newEvents[Str(row, "id")] = true
	}
	if len(newEvents) != len(active) {
		return fmt.Errorf("UPGRADE_AUDIT_EVENT_COUNT")
	}
	for table, old := range before {
		current, exists := after[table]
		if !exists {
			return fmt.Errorf("UPGRADE_TABLE_LOST")
		}
		switch table {
		case "domain_objects": // Checked by exact identity and restricted changes above.
		case "domain_versions", "domain_refs", "outbox", "event_state_snapshots":
			extra, e := upgradeExtra(old, current)
			if e != nil {
				return e
			}
			if (table == "domain_versions" && len(extra) != 3*len(active)) || ((table == "outbox" || table == "event_state_snapshots") && len(extra) != len(active)) {
				return fmt.Errorf("UPGRADE_AUDIT_HISTORY_COUNT")
			}
			for _, row := range extra {
				if table == "outbox" || table == "event_state_snapshots" {
					id := Str(row, "id")
					if table == "event_state_snapshots" {
						id = Str(row, "event_id")
					}
					if !newEvents[id] {
						return fmt.Errorf("UPGRADE_UNKNOWN_EVENT_HISTORY")
					}
				} else if !(row["kind"] == "Run" && active[upgradeObjectKey(row)] != nil) && !(row["kind"] == "ProjectState" && projectRuns[Str(row, "project")] > 0) && !(row["kind"] == "EventEnvelope" && newEvents[Str(row, "id")]) {
					return fmt.Errorf("UPGRADE_UNKNOWN_DOMAIN_HISTORY")
				}
			}
		case "resource_effects":
			if e := upgradeEffects(old, current); e != nil {
				return e
			}
		case "auth_credentials":
			expected := make([]Object, len(old))
			for i, row := range old {
				expected[i] = Merge(copyObject(row), Object{"revoked": int64(1)})
			}
			extra, e := upgradeExtra(expected, current)
			if e != nil || len(extra) != 0 {
				return fmt.Errorf("UPGRADE_CREDENTIAL_FENCE")
			}
		case "retrieval_roots":
			strip := func(rows []Object) []Object {
				result := make([]Object, len(rows))
				for i, row := range rows {
					result[i] = upgradeWithout(row, "path", "root_identity")
				}
				return result
			}
			extra, e := upgradeExtra(strip(old), strip(current))
			if e != nil || len(extra) != 0 {
				return fmt.Errorf("UPGRADE_SOURCE_ROOTS_CHANGED")
			}
			for _, row := range current {
				if !upgradeInside(destination, Str(row, "path")) || Str(row, "root_identity") == "" {
					return fmt.Errorf("UPGRADE_SOURCE_ROOT_NOT_RELOCATED")
				}
			}
		case "backup_restore_barriers":
			oldByKey := map[string]Object{}
			for _, row := range old {
				oldByKey[Str(row, "project")+"/Run/"+Str(row, "run")] = row
			}
			for _, row := range current {
				key := Str(row, "project") + "/Run/" + Str(row, "run")
				if active[key] != nil {
					if Str(row, "restored_at") == "" {
						return fmt.Errorf("UPGRADE_RESTORE_BARRIER")
					}
				} else if Hash(row) != Hash(oldByKey[key]) {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER_DRIFT")
				}
				delete(oldByKey, key)
			}
			if len(oldByKey) != 0 {
				return fmt.Errorf("UPGRADE_RESTORE_BARRIER_LOST")
			}
			for key := range active {
				found := false
				for _, row := range current {
					if Str(row, "project")+"/Run/"+Str(row, "run") == key {
						found = true
					}
				}
				if !found {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER_MISSING")
				}
			}
		case "schema_migrations":
			if !migrated {
				if Hash(old) != Hash(current) { return fmt.Errorf("UPGRADE_RECOVERY_CHANGED_MIGRATIONS") }
				continue
			}
			extra, e := upgradeExtra(old, current)
			seen := map[int64]bool{}
			for _, row := range extra {
				version, err := Num(row, "version")
				if err != nil || version != 21 || seen[version] {
					return fmt.Errorf("UPGRADE_MIGRATION_HISTORY")
				}
				seen[version] = true
			}
			if e != nil || len(seen) != 1 {
				return fmt.Errorf("UPGRADE_MIGRATION_HISTORY")
			}
		default:
			if Hash(old) != Hash(current) {
				return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE_CHANGE: %s", table)
			}
		}
	}
	for table, rows := range after {
		if _, exists := before[table]; exists {
			continue
		}
		if table == "backup_restore_barriers" {
			if len(rows) != len(active) {
				return fmt.Errorf("UPGRADE_RESTORE_BARRIER_COUNT")
			}
			for _, row := range rows {
				if active[Str(row, "project")+"/Run/"+Str(row, "run")] == nil || Str(row, "restored_at") == "" {
					return fmt.Errorf("UPGRADE_RESTORE_BARRIER")
				}
			}
		} else if !(migrated && upgradeHistory20Tables[table]) || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE")
		}
	}
	return nil
}

