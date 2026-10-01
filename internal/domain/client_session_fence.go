package domain

import (
	"context"
	"database/sql"
)

type fenceExec interface {
	ExecContext(ctx context.Context, query string, args ...any) (sql.Result, error)
	QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
}

// EnsureClientSessionFence extends the restore barrier to v2.4 client sessions when the
// client_sessions table is present (it is absent on pre-W03 schemas): writer_epoch can
// never regress, and advancing the epoch of a session whose (project, run) is under a
// restore barrier requires the same fresh reconciliation evidence as Run leases.
// Open sessions with a run are seeded into the barriers so restored snapshots cannot
// silently re-handoff writers. Returns nil (no-op) when client_sessions does not exist.
func EnsureClientSessionFence(ctx context.Context, ex fenceExec) error {
	var present int
	row := ex.QueryRowContext(ctx, `SELECT count(*) FROM sqlite_master WHERE type='table' AND name='client_sessions'`)
	if err := row.Scan(&present); err != nil {
		return err
	}
	if present == 0 {
		return nil
	}
	if _, err := ex.ExecContext(ctx, `CREATE TABLE IF NOT EXISTS backup_restore_barriers(project TEXT NOT NULL,run TEXT NOT NULL,restored_at TEXT NOT NULL,PRIMARY KEY(project,run))`); err != nil {
		return err
	}
	if _, err := ex.ExecContext(ctx, `INSERT INTO backup_restore_barriers(project,run,restored_at)
		SELECT s.project_id, s.run_id, ? FROM client_sessions s
		WHERE s.sealed_at IS NULL AND s.run_id IS NOT NULL
		ON CONFLICT(project,run) DO UPDATE SET restored_at=excluded.restored_at`, Now()); err != nil {
		return err
	}
	if _, err := ex.ExecContext(ctx, `CREATE TRIGGER IF NOT EXISTS client_session_epoch_no_regression BEFORE UPDATE OF writer_epoch ON client_sessions
		WHEN NEW.writer_epoch < OLD.writer_epoch BEGIN SELECT RAISE(ABORT,'SESSION_EPOCH_REGRESSION'); END;`); err != nil {
		return err
	}
	_, err := ex.ExecContext(ctx, `CREATE TRIGGER IF NOT EXISTS client_session_require_fresh BEFORE UPDATE OF writer_epoch ON client_sessions
		WHEN NEW.writer_epoch > OLD.writer_epoch
		AND EXISTS(SELECT 1 FROM backup_restore_barriers b WHERE b.project=NEW.project_id AND b.run=NEW.run_id)
		AND NOT EXISTS(SELECT 1 FROM runtime_observations o WHERE o.project=NEW.project_id AND o.run=NEW.run_id AND o.epoch=OLD.writer_epoch
			AND o.observed_at > (SELECT max(b.restored_at) FROM backup_restore_barriers b WHERE b.project=NEW.project_id AND b.run=NEW.run_id))
		BEGIN SELECT RAISE(ABORT,'RESTORE_FRESH_RECONCILIATION_REQUIRED'); END;`)
	return err
}
