package domain

// Exact schema22 ->23 coordinator. Historical upgrade plans remain separate.
import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"researchos.local/research-os/internal/store"
	"strings"
)

const ConfigurationSchemaUpgradePlan = "schema22-to23-host-model-configuration-v1"
const upgradeConfigurationSQLHash = "sha256:07feef35d8d114f3d31aa99684ce85be9d2fafd2d5090a2c8548789b636cf794"

var upgradeConfigurationTables = map[string]bool{"client_command_identities": true, "host_model_configurations": true, "host_model_config_heads": true}

func upgradeConfigurationRelease(root string, count int) (Object, [][]byte, error) {
	if count != 22 && count != 23 {
		return nil, nil, fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	files, e := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
	if e != nil || len(files) != count {
		return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS: require exact 1..%d", count)
	}
	manifest := Object{}
	sqls := make([][]byte, count+1)
	for i, file := range files {
		name := filepath.Base(file)
		if len(name) < 5 || name[:4] != fmt.Sprintf("%04d", i+1) {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_MIGRATIONS")
		}
		expected := upgradeMigrationHashes[name]
		switch name {
		case "0021_research_pending_windows.sql":
			expected = "sha256:36d4e5c93aa1edcd7ca5aca922b3bea11d5739f307bd11c6834936adf5552f32"
		case "0022_client_command_queue.sql":
			expected = upgradeQueueSQLHash
		case "0023_host_model_configuration.sql":
			expected = upgradeConfigurationSQLHash
		}
		raw, e := os.ReadFile(file)
		if e != nil || expected == "" || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("UPGRADE_RELEASE_HASH: %s", name)
		}
		manifest["migrations/sqlite/"+name] = expected
		sqls[i] = raw
	}
	for path, expected := range map[string]string{
		"spec/v2.0/contracts/domain.schema.json":             "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
		"spec/v2.0/contracts/openapi.json":                   "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
		"internal/api/contracts/client.protocol.schema.json": "sha256:8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b",
		"internal/api/contracts/domain.schema.json":          "sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54",
	} {
		raw, e := os.ReadFile(filepath.Join(root, filepath.FromSlash(path)))
		if e != nil || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("UPGRADE_CONTRACT_HASH: %s", path)
		}
		manifest[path] = expected
	}
	raw, e := os.ReadFile(filepath.Join(root, "migrations/sqlite/next_v24_sessions.sql"))
	if e != nil || Digest(raw) != upgradeQueueSessionHash {
		return nil, nil, fmt.Errorf("UPGRADE_SESSION_SCHEMA_HASH")
	}
	manifest["migrations/sqlite/next_v24_sessions.sql"] = Digest(raw)
	sqls[count] = raw
	return manifest, sqls, nil
}

func upgradeConfigurationTemplate(ctx context.Context, sqls [][]byte, contracts *Contracts) (string, string, error) {
	if len(sqls) != 24 {
		return "", "", fmt.Errorf("UPGRADE_PLAN_UNSUPPORTED")
	}
	stage, e := os.MkdirTemp("", ".researchos-configuration-template-")
	if e != nil {
		return "", "", e
	}
	defer backupDiscard(stage)
	db, e := store.Open(filepath.Join(stage, "schema.sqlite"))
	if e != nil {
		return "", "", e
	}
	defer db.Close()
	for i, raw := range sqls[:22] {
		if _, e = db.ExecContext(ctx, string(raw)); e != nil {
			return "", "", e
		}
		if _, e = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); e != nil {
			return "", "", e
		}
	}
	if _, e = db.ExecContext(ctx, string(sqls[23])); e != nil {
		return "", "", e
	}
	if e = installClientSessionFence(ctx, db, false); e != nil {
		return "", "", e
	}
	before, e := backupSchema(db)
	if e != nil {
		return "", "", e
	}
	if _, e = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); e != nil {
		return "", "", e
	}
	if e = upgradeConfigurationMigration(ctx, db, sqls[22]); e != nil {
		return "", "", e
	}
	after, e := backupSchema(db)
	return before, after, e
}

func upgradeConfigurationMigration(ctx context.Context, db *sql.DB, raw []byte) error {
	if Digest(raw) != upgradeConfigurationSQLHash {
		return fmt.Errorf("UPGRADE_MIGRATION_HASH")
	}
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(22)) {
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
	if _, e = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(23)"); e != nil {
		return e
	}
	after, e := upgradeQueueRows(tx)
	if e != nil {
		return e
	}
	for table, rows := range before {
		if table != "schema_migrations" && Hash(rows) != Hash(after[table]) {
			return fmt.Errorf("UPGRADE_MIGRATION_MUTATED_HISTORY: %s", table)
		}
	}
	for table := range upgradeConfigurationTables {
		rows, ok := after[table]
		if !ok || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_CONFIGURATION_NOT_EMPTY")
		}
	}
	for table := range after {
		if _, ok := before[table]; !ok && !upgradeConfigurationTables[table] {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE")
		}
	}
	var integrity string
	if e = tx.QueryRowContext(ctx, "PRAGMA integrity_check").Scan(&integrity); e != nil || integrity != "ok" {
		return fmt.Errorf("UPGRADE_TARGET_INTEGRITY")
	}
	rows, e := tx.QueryContext(ctx, "PRAGMA foreign_key_check")
	if e != nil {
		return e
	}
	bad := rows.Next()
	e = rows.Err()
	rows.Close()
	if bad || e != nil {
		return fmt.Errorf("UPGRADE_TARGET_REFERENCE")
	}
	return tx.Commit()
}

func upgradeConfigurationLocal(ctx context.Context, opt LocalUpgradeOptions, verifier upgradeVerifier) (RestoreReport, error) {
	report := RestoreReport{Started: Now(), Status: "FAILED"}
	if e := upgradePaths(&opt); e != nil {
		return report, e
	}
	sourceRelease, _, e := upgradeConfigurationRelease(opt.SourceRoot, 22)
	if e != nil {
		return report, e
	}
	targetRelease, sqls, e := upgradeConfigurationRelease(opt.TargetRoot, 23)
	if e != nil {
		return report, e
	}
	contracts, e := LoadContracts(filepath.Join(opt.TargetRoot, "spec/v2.0/contracts"))
	if e != nil {
		return report, e
	}
	expectedSourceSchema, expectedTargetSchema, e := upgradeConfigurationTemplate(ctx, sqls, contracts)
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
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(22)) {
		return report, fmt.Errorf("UPGRADE_SOURCE_VERSION: require exact 1..22")
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
	plan := Object{"id": opt.Plan, "source_versions": versions, "target_versions": upgradeVersions(23),
		"source_schema_hash": schema, "target_schema_with_restore_fence_hash": expectedTargetSchema,
		"source_release_hash": Hash(sourceRelease), "target_release_hash": Hash(targetRelease),
		"migration_sql_hash": Digest(sqls[22]), "source_database_logical_hash": Hash(original),
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
	policy.preserveConfigurationUpgradeWorkspaces = func(restored *sql.DB) error {
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
		if e = upgradeConfigurationRecoveryInvariant(original, rows, opt.Destination); e != nil {
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
			{opt.SourceRoot, 22, Hash(sourceRelease)}, {opt.TargetRoot, 23, Hash(targetRelease)},
		} {
			current, _, err := upgradeConfigurationRelease(entry.root, entry.n)
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
			return upgradeConfigurationMigration(ctx, target, sqls[22])
		},
	}, policy)
}

// Recompute the exact existing restore transformation. A new receipt is not
// permission to change the original admission, response, generation or epoch.
func configurationQueueRecoveryInvariant(before, after upgradeData) error {
	index := func(rows []Object, keys ...string) (map[string]Object, error) {
		result := map[string]Object{}
		for _, r := range rows {
			parts := []any{}
			for _, k := range keys {
				parts = append(parts, r[k])
			}
			key := Hash(parts)
			if result[key] != nil {
				return nil, fmt.Errorf("UPGRADE_DUPLICATE_IDENTITY")
			}
			result[key] = r
		}
		return result, nil
	}
	receipts, err := index(after["client_control_receipts"], "receipt_id")
	if err != nil {
		return err
	}
	extras, err := upgradeExtra(before["client_control_receipts"], after["client_control_receipts"])
	if err != nil {
		return err
	}
	newIDs := map[string]bool{}
	for _, r := range extras {
		newIDs[Str(r, "receipt_id")] = true
	}
	unknown := map[string]bool{}
	resume := map[string]bool{}
	queue, err := index(after["client_command_queue"], "principal", "project", "command_id")
	if err != nil {
		return err
	}
	if len(queue) != len(before["client_command_queue"]) {
		return fmt.Errorf("UPGRADE_QUEUE_COUNT")
	}
	for _, old := range before["client_command_queue"] {
		key := Hash([]any{old["principal"], old["project"], old["command_id"]})
		current := queue[key]
		if current == nil {
			return fmt.Errorf("UPGRADE_QUEUE_LOST")
		}
		expected := copyObject(old)
		if old["state"] != "CONSUMED" && old["state"] != "DROPPED" {
			rev, e := Num(old, "revision")
			if e != nil {
				return e
			}
			id := Str(current, "last_receipt_id")
			r := receipts[Hash([]any{id})]
			body := Object{"prior_state": old["state"], "reason": "SNAPSHOT_MAY_PREDATE_SEND"}
			if !newIDs[id] || r == nil || r["kind"] != "RESTORE_UNKNOWN" || r["project"] != old["project"] || r["generation"] != old["generation"] || r["command_id"] != old["command_id"] || Hash(r["previous_receipt_id"]) != Hash(old["last_receipt_id"]) || Str(r, "body") != string(Bytes(body)) || r["body_hash"] != Digest(Bytes(body)) || Str(r, "created_at") == "" {
				return fmt.Errorf("UPGRADE_QUEUE_RESTORE_RECEIPT")
			}
			delete(newIDs, id)
			expected["state"] = "UNKNOWN"
			expected["revision"] = rev + 1
			expected["last_receipt_id"] = id
			unknown[Str(old, "generation")] = true
		}
		if Hash(expected) != Hash(current) {
			return fmt.Errorf("UPGRADE_QUEUE_IDENTITY_CHANGED")
		}
	}
	if len(newIDs) != 0 {
		return fmt.Errorf("UPGRADE_EXTRA_CONTROL_RECEIPT")
	}
	fences, err := index(after["client_queue_fences"], "project", "task_id")
	if err != nil {
		return err
	}
	if len(fences) != len(before["client_queue_fences"]) {
		return fmt.Errorf("UPGRADE_FENCE_COUNT")
	}
	for _, old := range before["client_queue_fences"] {
		expected := copyObject(old)
		if old["state"] != "SEALED" || unknown[Str(old, "generation")] {
			rev, e := Num(old, "revision")
			if e != nil {
				return e
			}
			expected["revision"] = rev + 1
			expected["restore_fenced"] = int64(1)
			if old["state"] != "CANCEL_FENCED" {
				expected["state"] = "RECONCILING"
			}
		}
		if Hash(expected) != Hash(fences[Hash([]any{old["project"], old["task_id"]})]) {
			return fmt.Errorf("UPGRADE_QUEUE_FENCE_CHANGED")
		}
		if expected["restore_fenced"] == int64(1) {
			resume[Str(old, "session_id")] = true
		}
	}
	controls, err := index(after["client_control_requests"], "principal", "project", "command_id")
	if err != nil {
		return err
	}
	if len(controls) != len(before["client_control_requests"]) {
		return fmt.Errorf("UPGRADE_CONTROL_COUNT")
	}
	for _, old := range before["client_control_requests"] {
		expected := copyObject(old)
		if old["state"] != "CONFIRMED" {
			expected["state"] = "RECONCILING"
			resume[Str(old, "session_id")] = true
		}
		if Hash(expected) != Hash(controls[Hash([]any{old["principal"], old["project"], old["command_id"]})]) {
			return fmt.Errorf("UPGRADE_CONTROL_CHANGED")
		}
	}
	sessions, err := index(after["client_sessions"], "id")
	if err != nil {
		return err
	}
	if len(sessions) != len(before["client_sessions"]) {
		return fmt.Errorf("UPGRADE_SESSION_COUNT")
	}
	for _, old := range before["client_sessions"] {
		expected := copyObject(old)
		if resume[Str(old, "id")] {
			expected["resume_requires_explicit_user"] = int64(1)
		}
		if Hash(expected) != Hash(sessions[Hash([]any{old["id"]})]) {
			return fmt.Errorf("UPGRADE_SESSION_CHANGED")
		}
	}
	return nil
}

func upgradeConfigurationRecoveryInvariant(before, after upgradeData, destination string) error {
	if e := configurationQueueRecoveryInvariant(before, after); e != nil {
		return e
	}
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
		case "client_sessions", "client_queue_fences", "client_command_queue", "client_control_requests", "client_control_receipts": // Validated independently above.
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
			extra, e := upgradeExtra(old, current)
			seen := map[int64]bool{}
			for _, row := range extra {
				version, err := Num(row, "version")
				if err != nil || version != 23 || seen[version] {
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
		} else if !upgradeConfigurationTables[table] || len(rows) != 0 {
			return fmt.Errorf("UPGRADE_UNEXPECTED_TABLE")
		}
	}
	return nil
}
