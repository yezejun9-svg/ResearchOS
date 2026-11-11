package domain

import (
	"context"
	"database/sql"
	"fmt"
	"reflect"
)

// This ordered list is the entire additional plan. A caller cannot choose an
// intermediate version, append SQL, or provide its own migration manifest.
var upgradeFinalMigrations = []string{
	"0014_remote_access.sql", "0015_evolution_fixture.sql",
	"0016_runtime_qualification.sql", "0017_runtime_dispatch.sql",
	"0018_intent_planning.sql", "0019_evolution_release_operations.sql",
	"0020_research_cycle_work.sql",
}

var upgradeFinalTables = map[string]bool{
	// SQLite creates this empty table for 0015's first AUTOINCREMENT table.
	"sqlite_sequence":   true,
	"remote_challenges": true, "remote_devices": true, "remote_refresh": true,
	"remote_replays": true, "remote_audit": true,
	"evolution_hosts": true, "evolution_builds": true, "evolution_candidates": true,
	"evolution_tasks": true, "evolution_executions": true, "evolution_journal": true,
	"evolution_slots": true, "runtime_bindings": true,
	"runtime_qualification_plans": true, "runtime_qualification_runs": true,
	"runtime_qualification_approvals": true, "runtime_dispatches": true,
	"intent_plan_bindings": true, "evolution_release_operations": true,
	"research_monitor_cycles": true, "research_cycle_work": true,
}

func upgradeFinalSQLManifest() Object {
	manifest := Object{}
	for _, name := range upgradeFinalMigrations {
		manifest[name] = upgradeMigrationHashes[name]
	}
	return manifest
}

// 0020 adds exactly three nullable columns to existing legacy manual reviews.
// They must remain NULL: migration cannot manufacture reviewer authority or an
// acceptance. Everything else in each old row remains byte-for-byte identical.
func upgradeFinalProjection(before, after upgradeData) (upgradeData, error) {
	projected := upgradeData{}
	for table, rows := range after {
		projected[table] = rows
	}
	for table := range upgradeFinalTables {
		if rows, exists := after[table]; !exists || len(rows) != 0 {
			return nil, fmt.Errorf("UPGRADE_NEW_TABLE_NOT_EMPTY: %s", table)
		}
		if _, existed := before[table]; existed {
			return nil, fmt.Errorf("UPGRADE_NEW_TABLE_ALREADY_EXISTS: %s", table)
		}
	}
	rows, exists := after["research_candidate_reviews"]
	if !exists {
		return nil, fmt.Errorf("UPGRADE_TABLE_LOST")
	}
	projected["research_candidate_reviews"] = make([]Object, len(rows))
	for i, row := range rows {
		for _, col := range []string{"reviewer_id", "review_task_ref", "acceptance_ref"} {
			if value, exists := row[col]; !exists || value != nil {
				return nil, fmt.Errorf("UPGRADE_LEGACY_REVIEW_AUTHORITY")
			}
		}
		projected["research_candidate_reviews"][i] = upgradeWithout(row, "reviewer_id", "review_task_ref", "acceptance_ref")
	}
	// SQL column addition changes row sorting hashes. Compare multisets before
	// adopting the original order for the common recovery invariant.
	extra, e := upgradeExtra(before["research_candidate_reviews"], projected["research_candidate_reviews"])
	if e != nil || len(extra) != 0 {
		return nil, fmt.Errorf("UPGRADE_LEGACY_REVIEW_MUTATED")
	}
	projected["research_candidate_reviews"] = before["research_candidate_reviews"]
	return projected, nil
}

func upgradeFinalMigration(ctx context.Context, db *sql.DB, sqls [][]byte) error {
	if len(sqls) != len(upgradeFinalMigrations) {
		return fmt.Errorf("UPGRADE_MIGRATION_HASH")
	}
	for i, name := range upgradeFinalMigrations {
		if Digest(sqls[i]) != upgradeMigrationHashes[name] {
			return fmt.Errorf("UPGRADE_MIGRATION_HASH: %s", name)
		}
	}
	versions, e := backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(13)) {
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
	for i, raw := range sqls {
		if _, e = tx.ExecContext(ctx, string(raw)); e != nil {
			return e
		}
		if _, e = tx.ExecContext(ctx, "INSERT INTO schema_migrations(version) VALUES(?)", 14+i); e != nil {
			return e
		}
	}
	if e = tx.Commit(); e != nil {
		return e
	}
	after, e := upgradeRows(db)
	if e != nil {
		return e
	}
	projected, e := upgradeFinalProjection(before, after)
	if e != nil {
		return e
	}
	for table, rows := range before {
		if table != "schema_migrations" && Hash(rows) != Hash(projected[table]) {
			return fmt.Errorf("UPGRADE_MIGRATION_MUTATED_HISTORY: %s", table)
		}
	}
	versions, e = backupMigrations(db)
	if e != nil || !reflect.DeepEqual(versions, upgradeVersions(20)) {
		return fmt.Errorf("UPGRADE_TARGET_VERSION")
	}
	return nil
}
