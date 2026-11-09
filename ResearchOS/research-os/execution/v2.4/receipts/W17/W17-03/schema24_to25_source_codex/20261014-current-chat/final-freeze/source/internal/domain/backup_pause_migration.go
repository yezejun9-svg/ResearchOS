package domain

// The fixed24-to25 coordinator is separate from the accepted fixed23-to24
// path. None of these helpers accepts caller supplied versions or SQL hashes.
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

const PauseSchemaUpgradePlan = "schema24-to25-runtime-pause-v1"
const pauseMigrationReceiptName = "runtime-pause-schema-rehearsal.json"
const pauseMigrationReceiptSchema = "researchos.runtime-pause-schema-rehearsal.v1"
const pauseMigrationHandoffSchema = "researchos.public24-to25-backup-handoff.v1"

// SourceProgram is the preserved schema24 backup program; TargetProgram is
// the new control program. RehearsalProgram is a different target backup image.
// This leaves the old LocalUpgradeOptions signed representation unchanged.
type PauseSchemaUpgradeOptions struct {
	Upgrade              LocalUpgradeOptions `json:"upgrade"`
	RehearsalProgram     string              `json:"rehearsal_program"`
	HandoffBindingFile   string              `json:"handoff_binding_file"`
	HandoffBindingSHA256 string              `json:"handoff_binding_sha256"`
}

type pauseMigrationSchemas struct {
	Source24, Original25, Restored24, Restored25 string
}

type pauseMigrationReceipt struct {
	Schema                string                    `json:"schema"`
	Plan                  string                    `json:"plan"`
	Status                string                    `json:"status"`
	Options               PauseSchemaUpgradeOptions `json:"options"`
	OptionsHash           string                    `json:"options_sha256"`
	SourceProgramHash     string                    `json:"source_program_sha256"`
	TargetProgramHash     string                    `json:"target_program_sha256"`
	RehearsalProgramHash  string                    `json:"rehearsal_program_sha256"`
	SourceInventoryHash   string                    `json:"source_inventory_sha256"`
	TargetInventoryHash   string                    `json:"target_inventory_sha256"`
	SourceSchema          string                    `json:"source_schema_sha256"`
	TargetSchema          string                    `json:"target_schema_sha256"`
	RestoredSchema        string                    `json:"restored_schema24_sha256"`
	RestoredTargetSchema  string                    `json:"restored_schema25_sha256"`
	SQLHash               string                    `json:"sql_sha256"`
	OriginalRowsHash      string                    `json:"original_rows_sha256"`
	PostRestoreRowsHash   string                    `json:"post_restore_rows_sha256"`
	PostDDLRowsHash       string                    `json:"post_ddl_rows_sha256"`
	RestoreDelta          Object                    `json:"restore_delta"`
	BackupManifestHash    string                    `json:"backup_manifest_sha256"`
	BackupManifestBytes   int64                     `json:"backup_manifest_bytes"`
	HandoffBindingHash    string                    `json:"handoff_binding_sha256"`
	ProducerStdout        preparedHandoffFileRef    `json:"producer_stdout"`
	ProducerObservation   preparedHandoffFileRef    `json:"producer_observation"`
	OriginalUnchanged     bool                      `json:"original_unchanged"`
	RollbackVerified      bool                      `json:"rollback_verified"`
	ExistingRowsUnchanged bool                      `json:"existing_rows_unchanged"`
	NewPauseTablesEmpty   bool                      `json:"new_pause_tables_empty"`
	AutomaticPromotion    bool                      `json:"automatic_promotion"`
	ReleaseAuthority      string                    `json:"release_authority"`
	RestoreReport         RestoreReport             `json:"restore_report"`
}

func pauseMigrationRelease(root string, count int) (Object, [][]byte, error) {
	if count == 24 {
		return preparedUpgradeRelease(root, 24)
	}
	if count != 25 {
		return nil, nil, fmt.Errorf("PAUSE_UPGRADE_PLAN_UNSUPPORTED")
	}
	files, err := filepath.Glob(filepath.Join(root, "migrations/sqlite/0*.sql"))
	if err != nil || len(files) != 25 {
		return nil, nil, fmt.Errorf("PAUSE_UPGRADE_RELEASE_INVENTORY")
	}
	manifest, sqls := Object{}, make([][]byte, 26)
	for i, file := range files {
		name := filepath.Base(file)
		if len(name) < 6 || name[:5] != fmt.Sprintf("%04d_", i+1) {
			return nil, nil, fmt.Errorf("PAUSE_UPGRADE_RELEASE_INVENTORY")
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
		case "0025_runtime_pause_activations.sql":
			expected = pauseUpgradeSQLHash
		}
		raw, err := os.ReadFile(file)
		if err != nil || expected == "" || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("PAUSE_UPGRADE_RELEASE_HASH: %s", name)
		}
		manifest["migrations/sqlite/"+name], sqls[i] = expected, raw
	}
	for path, expected := range map[string]string{
		"spec/v2.0/contracts/domain.schema.json":             "sha256:b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847",
		"spec/v2.0/contracts/openapi.json":                   "sha256:f1edd7955a1d134a675c5558618756db809d82729f8eebe622a9bc2605a58920",
		"internal/api/contracts/client.protocol.schema.json": "sha256:8943fe363bcfda4a2c45231e54c266133ffccc8642c541724d93d2e56d3a9a9b",
		"internal/api/contracts/domain.schema.json":          "sha256:b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54",
		"migrations/sqlite/next_v24_sessions.sql":            upgradeQueueSessionHash,
	} {
		raw, err := os.ReadFile(filepath.Join(root, filepath.FromSlash(path)))
		if err != nil || Digest(raw) != expected {
			return nil, nil, fmt.Errorf("PAUSE_UPGRADE_RELEASE_MEMBER: %s", path)
		}
		manifest[path] = expected
		if path == "migrations/sqlite/next_v24_sessions.sql" {
			sqls[25] = raw
		}
	}
	return manifest, sqls, nil
}

func pauseMigrationRowsUnchanged(before, after preparedUpgradeRows) error {
	newTables := map[string]bool{}
	for _, name := range pauseTables {
		newTables[name] = true
		if _, exists := before[name]; exists {
			return fmt.Errorf("PAUSE_UPGRADE_TABLE_ALREADY_EXISTS: %s", name)
		}
		if table, exists := after[name]; !exists || len(table.Rows) != 0 {
			return fmt.Errorf("PAUSE_UPGRADE_NEW_TABLE_NOT_EMPTY: %s", name)
		}
	}
	for name, old := range before {
		current, exists := after[name]
		if !exists || !reflect.DeepEqual(old.Columns, current.Columns) {
			return fmt.Errorf("PAUSE_UPGRADE_OLD_TABLE_CHANGED: %s", name)
		}
		if name != "schema_migrations" {
			if !reflect.DeepEqual(old.Rows, current.Rows) {
				return fmt.Errorf("PAUSE_UPGRADE_OLD_ROWS_CHANGED: %s", name)
			}
			continue
		}
		counts := map[string]int{}
		for _, hash := range current.Rows {
			counts[hash]++
		}
		for _, hash := range old.Rows {
			counts[hash]--
			if counts[hash] < 0 {
				return fmt.Errorf("PAUSE_UPGRADE_MIGRATION_HISTORY_CHANGED")
			}
		}
		if len(current.Rows) != len(old.Rows)+1 {
			return fmt.Errorf("PAUSE_UPGRADE_MIGRATION_HISTORY_CHANGED")
		}
	}
	for name := range after {
		if _, exists := before[name]; !exists && !newTables[name] {
			return fmt.Errorf("PAUSE_UPGRADE_UNEXPECTED_TABLE: %s", name)
		}
	}
	return nil
}

func pauseMigrationDDL(ctx context.Context, tx *sql.Tx, raw []byte, before preparedUpgradeRows, sourceSchema, targetSchema string) error {
	if Digest(raw) != pauseUpgradeSQLHash {
		return fmt.Errorf("PAUSE_UPGRADE_SQL_HASH")
	}
	if err := preparedUpgradeVersions(tx, 24); err != nil {
		return err
	}
	schema, err := preparedUpgradeSchema(tx)
	if err != nil || schema != sourceSchema {
		return fmt.Errorf("PAUSE_UPGRADE_SOURCE_SCHEMA")
	}
	current, err := preparedUpgradeSnapshot(tx)
	if err != nil || Hash(current) != Hash(before) {
		return fmt.Errorf("PAUSE_UPGRADE_BASELINE_CHANGED")
	}
	for _, name := range pauseTables {
		if _, exists := current[name]; exists {
			return fmt.Errorf("PAUSE_UPGRADE_TABLE_ALREADY_EXISTS: %s", name)
		}
	}
	if _, err = tx.ExecContext(ctx, string(raw)); err != nil {
		return err
	}
	if _, err = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(25)"); err != nil {
		return err
	}
	after, err := preparedUpgradeSnapshot(tx)
	if err != nil {
		return err
	}
	if err = pauseMigrationRowsUnchanged(before, after); err != nil {
		return err
	}
	if err = preparedUpgradeVersions(tx, 25); err != nil {
		return err
	}
	schema, err = preparedUpgradeSchema(tx)
	if err != nil || schema != targetSchema {
		return fmt.Errorf("PAUSE_UPGRADE_TARGET_SCHEMA")
	}
	return preparedUpgradeIntegrity(ctx, tx)
}

func pauseMigrationTemplate(ctx context.Context, sqls [][]byte, contracts *Contracts) (pauseMigrationSchemas, error) {
	var result pauseMigrationSchemas
	if len(sqls) != 26 || Digest(sqls[24]) != pauseUpgradeSQLHash || Digest(sqls[25]) != upgradeQueueSessionHash {
		return result, fmt.Errorf("PAUSE_UPGRADE_TEMPLATE_INPUT")
	}
	stage, err := os.MkdirTemp("", ".researchos-backup-stage-")
	if err != nil {
		return result, err
	}
	defer backupDiscard(stage)
	db, err := store.Open(filepath.Join(stage, "template.sqlite"))
	if err != nil {
		return result, err
	}
	defer db.Close()
	for i, raw := range sqls[:24] {
		if _, err = db.ExecContext(ctx, string(raw)); err != nil {
			return result, err
		}
		if _, err = db.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", i+1); err != nil {
			return result, err
		}
	}
	if _, err = db.ExecContext(ctx, string(sqls[25])); err != nil {
		return result, err
	}
	if err = installClientSessionFence(ctx, db, false); err != nil {
		return result, err
	}
	if result.Source24, err = preparedUpgradeSchema(db); err != nil {
		return result, err
	}
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return result, err
	}
	if _, err = tx.ExecContext(ctx, string(sqls[24])); err == nil {
		result.Original25, err = preparedUpgradeSchema(tx)
	}
	rollbackErr := tx.Rollback()
	if err != nil {
		return result, err
	}
	if rollbackErr != nil {
		return result, rollbackErr
	}
	if _, err = (&Service{DB: db, Contracts: contracts}).backupFence(ctx); err != nil {
		return result, err
	}
	if result.Restored24, err = preparedUpgradeSchema(db); err != nil {
		return result, err
	}
	if _, err = db.ExecContext(ctx, string(sqls[24])); err != nil {
		return result, err
	}
	result.Restored25, err = preparedUpgradeSchema(db)
	return result, err
}

func pauseMigrationRehearseDDL(ctx context.Context, db *sql.DB, raw []byte, before preparedUpgradeRows, sourceSchema, targetSchema string) error {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	err = pauseMigrationDDL(ctx, tx, raw, before, sourceSchema, targetSchema)
	rollbackErr := tx.Rollback()
	if err != nil {
		return err
	}
	if rollbackErr != nil {
		return rollbackErr
	}
	rows, err := preparedUpgradeSnapshot(db)
	if err != nil || Hash(rows) != Hash(before) {
		return fmt.Errorf("PAUSE_UPGRADE_ROLLBACK_ROWS")
	}
	schema, err := preparedUpgradeSchema(db)
	if err != nil || schema != sourceSchema {
		return fmt.Errorf("PAUSE_UPGRADE_ROLLBACK_SCHEMA")
	}
	tx, err = db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = pauseMigrationDDL(ctx, tx, raw, before, sourceSchema, targetSchema); err != nil {
		return err
	}
	return tx.Commit()
}

func pauseMigrationPath(path string, existing bool) (string, error) {
	if strings.Contains(path, "#") {
		return "", fmt.Errorf("PAUSE_UPGRADE_AMBIGUOUS_URI_PATH")
	}
	return upgradePath(path, existing)
}
