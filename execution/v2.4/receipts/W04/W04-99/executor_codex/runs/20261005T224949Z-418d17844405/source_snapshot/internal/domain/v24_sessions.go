package domain

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// ClientSession is the v2.4 authoritative index row mapping one client session to
// this-domain project/goal/task/run plus the upstream worker session log, watermark
// and lease attribution. Business truth remains in the existing tables.
type ClientSession struct {
	ID              string
	ProjectID       string
	Revision        int64
	CreatedAt       time.Time
	UpdatedAt       time.Time
	GoalID          *string
	TaskID          *string
	RunID           *string
	WriterEpoch     int64
	WriterClientID  string
	LeaseExpiresAt  *time.Time
	EventWatermark  int64
	UpstreamSession string
	UpstreamLogID   *string
	UpstreamLogHash *string
	WorkspaceRef    *string
	Title           *string
	ModelConfigRef  *string
	CoreBuildID     *string
	ResumeExplicit  int
	SealedAt        *time.Time
	ArchivedAt      *time.Time
	Protocol        string
}

var (
	ErrStaleEpoch      = errors.New("STALE_WRITER_EPOCH")
	ErrStaleRevision   = errors.New("STALE_REVISION")
	ErrUnknownProtocol = errors.New("UNKNOWN_PROTOCOL")
	ErrBadLogHash      = errors.New("BAD_UPSTREAM_LOG_HASH")
	ErrSealed          = errors.New("SESSION_SEALED")
	ErrUnknownSession  = errors.New("UNKNOWN_SESSION")
	ErrStaleWatermark  = errors.New("STALE_WATERMARK")
	ErrUnknownProject  = errors.New("UNKNOWN_PROJECT")
	ErrMissingWriter   = errors.New("MISSING_WRITER_ATTRIBUTION")
)

const ClientSessionProtocol = "researchos-client/2"

func fmtTime(t *time.Time) any {
	if t == nil {
		return nil
	}
	return t.UTC().Format(time.RFC3339Nano)
}

func validLogHash(h *string) bool {
	if h == nil {
		return true
	}
	if len(*h) != 71 || (*h)[:7] != "sha256:" {
		return false
	}
	for _, r := range (*h)[7:] {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f')) {
			return false
		}
	}
	return true
}

// MapClientSession inserts the mapping inside the caller's transaction; the project
// must already exist in domain_objects (existence checked in the same transaction).
func MapClientSession(ctx context.Context, tx *sql.Tx, s ClientSession) error {
	if s.Protocol != ClientSessionProtocol {
		return ErrUnknownProtocol
	}
	if !validLogHash(s.UpstreamLogHash) {
		return ErrBadLogHash
	}
	if s.WriterClientID == "" {
		return ErrMissingWriter
	}
	if s.UpstreamSession == "" {
		return fmt.Errorf("MISSING_NATIVE_SESSION_REF")
	}
	if s.Revision < 1 || s.WriterEpoch < 1 || s.EventWatermark < 0 {
		return fmt.Errorf("INVALID_SESSION_FIELDS")
	}
	var n int
	if err := tx.QueryRowContext(ctx, `SELECT count(DISTINCT id) FROM domain_objects WHERE kind IN ('Project','ProjectProfile') AND id=?`, s.ProjectID).Scan(&n); err != nil {
		return err
	}
	if n != 1 {
		return ErrUnknownProject
	}
	_, err := tx.ExecContext(ctx, `INSERT INTO client_sessions
		(id, project_id, revision, created_at, updated_at, goal_id, task_id, run_id,
		 writer_epoch, writer_client_id, lease_expires_at, event_watermark,
		 upstream_session_id, upstream_log_hash, upstream_log_id, workspace_ref, title,
		 model_config_ref, core_build_id, resume_requires_explicit_user, sealed_at, archived_at, protocol)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
		s.ID, s.ProjectID, s.Revision, s.CreatedAt.UTC().Format(time.RFC3339Nano), s.UpdatedAt.UTC().Format(time.RFC3339Nano),
		s.GoalID, s.TaskID, s.RunID, s.WriterEpoch, s.WriterClientID, fmtTime(s.LeaseExpiresAt), s.EventWatermark,
		s.UpstreamSession, s.UpstreamLogHash, s.UpstreamLogID, s.WorkspaceRef, s.Title,
		s.ModelConfigRef, s.CoreBuildID, s.ResumeExplicit, fmtTime(s.SealedAt), fmtTime(s.ArchivedAt), s.Protocol)
	return err
}

// AdvanceWatermark moves forward only, under the current writer epoch and the caller's
// expected revision; single-step and multi-step advances are both valid (22 §161).
func AdvanceWatermark(ctx context.Context, tx *sql.Tx, id string, epoch, expectedRevision, watermark int64) error {
	var cur int64
	var curEpoch, rev int64
	var sealed sql.NullString
	err := tx.QueryRowContext(ctx, `SELECT event_watermark, writer_epoch, revision, sealed_at FROM client_sessions WHERE id=?`, id).Scan(&cur, &curEpoch, &rev, &sealed)
	if err == sql.ErrNoRows {
		return ErrUnknownSession
	}
	if err != nil {
		return err
	}
	if sealed.Valid {
		return ErrSealed
	}
	if rev != expectedRevision {
		return ErrStaleRevision
	}
	if epoch != curEpoch {
		return ErrStaleEpoch
	}
	if watermark <= cur {
		return ErrStaleWatermark
	}
	res, err := tx.ExecContext(ctx, `UPDATE client_sessions
		SET event_watermark=?, revision=revision+1, updated_at=?
		WHERE id=? AND writer_epoch=? AND revision=? AND sealed_at IS NULL AND event_watermark=?`,
		watermark, time.Now().UTC().Format(time.RFC3339Nano), id, curEpoch, expectedRevision, cur)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n != 1 {
		return ErrStaleEpoch
	}
	return nil
}

// HandoffEpoch transfers the single writer; epoch advances by exactly one.
func HandoffEpoch(ctx context.Context, tx *sql.Tx, id string, fromEpoch int64, expectedRevision int64) (int64, error) {
	var curEpoch, rev int64
	var sealed sql.NullString
	if err := tx.QueryRowContext(ctx, `SELECT writer_epoch, revision, sealed_at FROM client_sessions WHERE id=?`, id).Scan(&curEpoch, &rev, &sealed); err == sql.ErrNoRows {
		return 0, ErrUnknownSession
	} else if err != nil {
		return 0, err
	}
	if sealed.Valid {
		return 0, ErrSealed
	}
	if rev != expectedRevision {
		return 0, ErrStaleRevision
	}
	res, err := tx.ExecContext(ctx, `UPDATE client_sessions
		SET writer_epoch=writer_epoch+1, revision=revision+1, updated_at=?
		WHERE id=? AND writer_epoch=? AND sealed_at IS NULL`,
		time.Now().UTC().Format(time.RFC3339Nano), id, fromEpoch)
	if err != nil {
		return 0, err
	}
	if n, _ := res.RowsAffected(); n != 1 {
		return 0, ErrStaleEpoch
	}
	return fromEpoch + 1, nil
}

// Seal closes the session for writes; sealed sessions report ErrSealed distinctly.
func Seal(ctx context.Context, tx *sql.Tx, id string, epoch int64, expectedRevision int64) error {
	var curEpoch, rev int64
	var sealed sql.NullString
	err := tx.QueryRowContext(ctx, `SELECT writer_epoch, revision, sealed_at FROM client_sessions WHERE id=?`, id).Scan(&curEpoch, &rev, &sealed)
	if err == sql.ErrNoRows {
		return ErrUnknownSession
	}
	if err != nil {
		return err
	}
	if sealed.Valid {
		return ErrSealed
	}
	if rev != expectedRevision {
		return ErrStaleRevision
	}
	res, err := tx.ExecContext(ctx, `UPDATE client_sessions SET sealed_at=?, revision=revision+1, updated_at=?
		WHERE id=? AND writer_epoch=? AND sealed_at IS NULL`,
		time.Now().UTC().Format(time.RFC3339Nano), time.Now().UTC().Format(time.RFC3339Nano), id, epoch)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n != 1 {
		return ErrStaleEpoch
	}
	return nil
}
