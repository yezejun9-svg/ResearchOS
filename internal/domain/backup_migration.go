package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// Existing authority requires matching-program backup and isolated migration.
// This is a read-only domain guard; store.Open may already have selected WAL.
func CheckMigrationSafety(db *sql.DB, files []string) error {
	applied, e := checkMigrationInventory(db, files)
	if e != nil {
		return e
	}
	populated, e := migrationAuthorityPresent(db)
	if e != nil {
		return e
	}
	if !populated {
		return nil
	}
	if applied != len(files) {
		return fmt.Errorf("MIGRATION_PREBACKUP_REQUIRED: back up with matching program and verify an isolated restore before migration %d", applied+1)
	}
	raw, e := os.ReadFile(filepath.Join(filepath.Dir(files[0]), "next_v24_sessions.sql"))
	if e != nil || Digest(raw) != upgradeQueueSessionHash {
		return fmt.Errorf("MIGRATION_ADDITIVE_SOURCE")
	}
	expected, e := sql.Open("sqlite", ":memory:")
	if e != nil {
		return e
	}
	defer expected.Close()
	expected.SetMaxOpenConns(1)
	if _, e = expected.Exec(string(raw)); e != nil {
		return e
	}
	if e = installClientSessionFence(context.Background(), expected, false); e != nil {
		return e
	}
	want, e := migrationSessionSchema(expected)
	if e != nil {
		return e
	}
	got, e := migrationSessionSchema(db)
	if e != nil {
		return e
	}
	if Hash(got) != Hash(want) {
		return fmt.Errorf("MIGRATION_PREBACKUP_REQUIRED: additive session schema or fence differs")
	}
	return nil
}

func checkMigrationInventory(db *sql.DB, files []string) (int, error) {
	if len(files) == 0 || len(files) > 24 {
		return 0, fmt.Errorf("MIGRATION_SOURCE_INVENTORY")
	}
	for i, file := range files {
		base := filepath.Base(file)
		if len(base) < 6 || base[4] != '_' {
			return 0, fmt.Errorf("MIGRATION_FILENAME_INVALID")
		}
		v, e := strconv.Atoi(base[:4])
		if e != nil || v != i+1 {
			return 0, fmt.Errorf("MIGRATION_SOURCE_INVENTORY")
		}
	}
	var exists int
	if e := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations'").Scan(&exists); e != nil {
		return 0, e
	}
	if exists == 0 {
		return 0, fmt.Errorf("MIGRATION_BOOTSTRAP_REQUIRED")
	}
	rows, e := db.Query("SELECT version,typeof(version) FROM schema_migrations ORDER BY version")
	if e != nil {
		return 0, e
	}
	defer rows.Close()
	n := 0
	for rows.Next() {
		var v int
		var kind string
		if e = rows.Scan(&v, &kind); e != nil {
			return 0, e
		}
		n++
		if kind != "integer" || v != n || v > len(files) {
			return 0, fmt.Errorf("MIGRATION_UNSUPPORTED_OR_GAPPED_VERSION")
		}
	}
	if e = rows.Err(); e != nil {
		return 0, e
	}
	if n == 0 {
		return 0, fmt.Errorf("MIGRATION_BOOTSTRAP_REQUIRED")
	}
	return n, nil
}

func migrationAuthorityPresent(db *sql.DB) (bool, error) {
	rows, e := db.Query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
	if e != nil {
		return false, e
	}
	names := []string{}
	for rows.Next() {
		var name string
		if e = rows.Scan(&name); e != nil {
			rows.Close()
			return false, e
		}
		names = append(names, name)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return false, e
	}
	for _, name := range names {
		if name == "schema_migrations" {
			continue
		}
		query := `SELECT count(*) FROM "` + strings.ReplaceAll(name, `"`, `""`) + `"`
		// Only the exact source-defined mutex seed is structural, not authority.
		if name == "resource_write_lock" {
			query += " WHERE id<>1 OR value<>0"
		}
		var n int
		if e = db.QueryRow(query).Scan(&n); e != nil {
			return false, e
		}
		if n != 0 {
			return true, nil
		}
	}
	return false, nil
}

func migrationSessionSchema(db *sql.DB) ([]Object, error) {
	rows, e := db.Query(`SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name IN ('client_sessions','backup_restore_barriers') AND sql IS NOT NULL ORDER BY type,name`)
	if e != nil {
		return nil, e
	}
	defer rows.Close()
	result := []Object{}
	for rows.Next() {
		var typ, name, table, raw string
		if e = rows.Scan(&typ, &name, &table, &raw); e != nil {
			return nil, e
		}
		result = append(result, Object{"type": typ, "name": name, "table": table, "sql": raw})
	}
	return result, rows.Err()
}
