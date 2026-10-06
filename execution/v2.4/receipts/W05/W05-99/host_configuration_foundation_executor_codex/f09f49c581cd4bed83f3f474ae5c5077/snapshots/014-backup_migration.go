package domain

import (
	"database/sql"
	"fmt"
	"path/filepath"
	"strconv"
)

// CheckMigrationSafety is the startup hook proposed for Service.New. Existing
// populated authority must first be backed up using its matching program, then
// migrated and verified in an isolated RestoreBackup copy. No environment flag
// or operator assertion silently authorizes an in-place migration.
func CheckMigrationSafety(db *sql.DB, files []string) error {
	var exists int
	if e := db.QueryRow("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='domain_objects'").Scan(&exists); e != nil {
		return e
	}
	if exists == 0 {
		return nil
	}
	var count int
	if e := db.QueryRow("SELECT count(*) FROM domain_objects").Scan(&count); e != nil {
		return e
	}
	if count == 0 {
		return nil
	}
	for _, file := range files {
		base := filepath.Base(file)
		if len(base) < 4 {
			return fmt.Errorf("MIGRATION_FILENAME_INVALID")
		}
		v, e := strconv.Atoi(base[:4])
		if e != nil {
			return e
		}
		var applied int
		if e = db.QueryRow("SELECT count(*) FROM schema_migrations WHERE version=?", v).Scan(&applied); e != nil {
			return e
		}
		if applied == 0 {
			return fmt.Errorf("MIGRATION_PREBACKUP_REQUIRED: back up with matching program and verify an isolated restore before migration %d", v)
		}
	}
	return nil
}
