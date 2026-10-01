package domain

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// ClientSession is the v2.4 authoritative index row mapping one client session to
// this-domain project/goal/task/run plus the upstream worker session log and the
// event watermark. Business truth remains in the existing tables; this maps to it.
type ClientSession struct {
	ID               string
	ProjectID        string
	Revision         int64
	CreatedAt        time.Time
	UpdatedAt        time.Time
	GoalID           *string
	TaskID           *string
	RunID            *string
	WriterEpoch      int64
	EventWatermark   int64
	UpstreamSession  *string
	UpstreamLogID    *string
	UpstreamLogHash  *string
	SealedAt         *time.Time
	Protocol         string
}

var (
	ErrStaleEpoch      = errors.New("STALE_WRITER_EPOCH")
	ErrUnknownProtocol = errors.New("UNKNOWN_PROTOCOL")
	ErrBadLogHash      = errors.New("BAD_UPSTREAM_LOG_HASH")
	ErrSealed          = errors.New("SESSION_SEALED")
)

const clientProtocolV2 = "researchos-client/2"

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

// MapClientSession inserts the mapping inside the caller's transaction so that the
// business write and the index share one atomic commit.
func MapClientSession(ctx context.Context, tx *sql.Tx, s ClientSession) error {
	if s.Protocol != clientProtocolV2 {
		return ErrUnknownProtocol
	}
	if !validLogHash(s.UpstreamLogHash) {
		return ErrBadLogHash
	}
	if s.Revision < 1 || s.WriterEpoch < 1 || s.EventWatermark < 0 {
		return fmt.Errorf("INVALID_SESSION_FIELDS")
	}
	_, err := tx.ExecContext(ctx, `INSERT INTO client_sessions
		(id, project_id, revision, created_at, updated_at, goal_id, task_id, run_id,
		 writer_epoch, event_watermark, upstream_session_id, upstream_log_hash, upstream_log_id, sealed_at, protocol)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
		s.ID, s.ProjectID, s.Revision, s.CreatedAt.UTC().Format(time.RFC3339Nano), s.UpdatedAt.UTC().Format(time.RFC3339Nano),
		s.GoalID, s.TaskID, s.RunID, s.WriterEpoch, s.EventWatermark, s.UpstreamSession, s.UpstreamLogHash, s.UpstreamLogID,
		s.SealedAt, s.Protocol)
	return err
}

// AdvanceWatermark moves the event watermark forward only, under the current writer epoch.
func AdvanceWatermark(ctx context.Context, tx *sql.Tx, id string, epoch, watermark int64) error {
	res, err := tx.ExecContext(ctx, `UPDATE client_sessions
		SET event_watermark=?, revision=revision+1, updated_at=?
		WHERE id=? AND writer_epoch=? AND event_watermark<? AND sealed_at IS NULL`,
		watermark, time.Now().UTC().Format(time.RFC3339Nano), id, epoch, watermark-1)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n != 1 {
		return ErrStaleEpoch
	}
	return nil
}

// HandoffEpoch transfers the single writer: epoch must advance exactly by one and the
// session must be open. Old epochs stop being writable by construction.
func HandoffEpoch(ctx context.Context, tx *sql.Tx, id string, fromEpoch int64) (int64, error) {
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

// Seal marks the session closed; sealed sessions reject further writes.
func Seal(ctx context.Context, tx *sql.Tx, id string, epoch int64) error {
	res, err := tx.ExecContext(ctx, `UPDATE client_sessions SET sealed_at=?, revision=revision+1, updated_at=?
		WHERE id=? AND writer_epoch=? AND sealed_at IS NULL`,
		time.Now().UTC().Format(time.RFC3339Nano), time.Now().UTC().Format(time.RFC3339Nano), id, epoch)
	if err != nil {
		return err
	}
	if n, _ := res.RowsAffected(); n != 1 {
		return ErrSealed
	}
	return nil
}
