package domain

import (
	"context"
	"database/sql"
	"fmt"
)

// An ordinary backup/restore must not imply adoption of this prepared addon.
// This guard applies to all existing backup policies, even when the table is empty.
func rejectPreparedNativeOriginBackup(db *sql.DB) error {
	present, err := nativeOriginSchemaState(context.Background(), db)
	if err != nil {
		return err
	}
	if present {
		return fmt.Errorf("PREPARED_NATIVE_WRITER_ORIGINS_UNSUPPORTED")
	}
	return nil
}

// Historical fixture validation is deliberately independent of live Host maps,
// current credentials and expiry. Its result grants no current authorization.
func ValidateClientNativeWriterOriginHistory(ctx context.Context, db *sql.DB, doc *SchemaDoc) (string, error) {
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return "", err
	}
	defer tx.Rollback()
	root, err := nativeOriginHistoryTx(ctx, tx, doc)
	if err != nil {
		return "", err
	}
	if root == "" {
		return "", fmt.Errorf("NATIVE_CREATE_UNSUPPORTED")
	}
	if err = tx.Commit(); err != nil {
		return "", err
	}
	return root, nil
}
