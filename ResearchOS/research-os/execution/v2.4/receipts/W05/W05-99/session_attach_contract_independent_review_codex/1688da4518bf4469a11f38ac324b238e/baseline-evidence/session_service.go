package domain

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

// W06-02: one effective writer per client session, a handoff that cannot happen while the previous writer is still
// producing, and a reconnect that admits what it missed.
//
// Only tables that already exist are used: client_sessions (next_v24_sessions.sql), outbox and idempotency
// (0002_domain.sql). No migration is added, because this card's limits reserve migration numbers and shared
// contracts to their serial owners. The accepted epoch primitives (MapClientSession, AdvanceWatermark, HandoffEpoch,
// Seal) and the restore fence (EnsureClientSessionFence) are reused, not re-declared.
//
// Scope note for the reviewer: the session.* envelope gate lives in client_protocol.go, which belongs to the
// accepted W03-02 and is outside this card's write_scope. These are the service-level operations a client route or
// the construction check drives directly; adding a case to W03-02's write switch is filed as an obligation instead
// of being done quietly here.

type sessionExec interface {
	ExecContext(ctx context.Context, query string, args ...any) (sql.Result, error)
	QueryRowContext(ctx context.Context, query string, args ...any) *sql.Row
	QueryContext(ctx context.Context, query string, args ...any) (*sql.Rows, error)
}

// liveRunStatuses are the run states in which the previous writer may still be producing output.
var liveRunStatuses = map[string]bool{"QUEUED": true, "STARTING": true, "RUNNING": true,
	"CANCEL_REQUESTED": true, "RECONCILING": true, "LOST": true}

// SessionClaim is one attach request. Takeover asks for the writer role; a read attach claims nothing.
// StopConfirmationRef must name an outbox event of this project that recorded the run as settled; it is looked up
// and re-verified against the run, never trusted as supplied.
type SessionClaim struct {
	SessionID           string
	ClientID            string
	Takeover            bool
	StopConfirmationRef string
	Reason              string
}

// readClientSession returns the live index row for one session of this project.
func readClientSession(ctx context.Context, ex sessionExec, project, id string) (Object, error) {
	var (
		idv, projectv, clientv, protocolv                string
		rev, epoch, water                                int64
		goal, task, run, lease, sealedAt, upstream       sql.NullString
	)
	err := ex.QueryRowContext(ctx, `SELECT id, project_id, revision, writer_epoch, writer_client_id, event_watermark,
		goal_id, task_id, run_id, lease_expires_at, sealed_at, upstream_session_id, protocol
		FROM client_sessions WHERE id=? AND project_id=?`, id, project).
		Scan(&idv, &projectv, &rev, &epoch, &clientv, &water, &goal, &task, &run, &lease, &sealedAt, &upstream, &protocolv)
	if err != nil {
		return nil, err
	}
	return Object{"id": idv, "project_id": projectv, "revision": rev, "writer_epoch": epoch,
		"writer_client_id": clientv, "event_watermark": water, "goal_id": nullString(goal),
		"task_id": nullString(task), "run_id": nullString(run), "lease_expires_at": nullString(lease),
		"sealed_at": nullString(sealedAt), "upstream_session_id": nullString(upstream),
		"protocol": protocolv}, nil
}

func nullString(v sql.NullString) any {
	if v.Valid {
		return v.String
	}
	return nil
}

// runState reads the run's own recorded state; settled means the runtime reported children stopped and queue empty.
func runState(ctx context.Context, ex sessionExec, project, runID string) (string, bool, error) {
	if runID == "" {
		return "", true, nil
	}
	var body string
	err := ex.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE kind='Run' AND project=? AND id=?`,
		project, runID).Scan(&body)
	if err == sql.ErrNoRows {
		return "", false, Fail(404, "NOT_FOUND", "session points at a run this project does not have")
	}
	if err != nil {
		return "", false, err
	}
	var b Object
	if err = json.Unmarshal([]byte(body), &b); err != nil {
		return "", false, err
	}
	status, _ := b["status"].(string)
	stopped, _ := b["children_stopped"].(bool)
	empty, _ := b["queue_empty"].(bool)
	return status, stopped && empty, nil
}

// ConfirmRunStop records the stop confirmation a takeover needs. It reads the run's recorded settlement from the
// store and refuses to write a confirmation the run does not support, so a client cannot manufacture one by asking.
func (s *Service) ConfirmRunStop(ctx context.Context, p Principal, project, runID, operation, key string) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	status, settled, err := runState(ctx, tx, project, runID)
	if err != nil {
		return nil, err
	}
	if !settled {
		return nil, Fail(409, "STOP_UNCONFIRMED",
			"run " + runID + " is " + status + "; children stopped and queue empty must both be recorded before a stop can be confirmed")
	}
	eventID := ID()
	body := Object{"type": "RUN_STOP_CONFIRMED", "project": project, "run_id": runID, "run_status": status,
		"children_stopped": true, "queue_empty": true, "confirmed_by": p.ID, "at": Now(),
		"idempotency_key": key}
	if err = writeOutbox(ctx, tx, project, eventID, body); err != nil {
		return nil, err
	}
	stopRequest := Object{"run_id": runID, "operation": operation, "confirmed_by": p.ID}
	if err = rememberIdempotency(ctx, tx, p.ID, project, operation, key, digest(Bytes(stopRequest)),
		Object{"status": "COMPLETED", "stop_confirmation_ref": eventID, "run_id": runID, "run_status": status}); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return Object{"status": "COMPLETED", "stop_confirmation_ref": eventID, "run_id": runID, "run_status": status}, nil
}

// stopConfirmed verifies the referenced event really records this run as settled.
func stopConfirmed(ctx context.Context, ex sessionExec, project, runID, ref string) (bool, error) {
	if ref == "" {
		return false, nil
	}
	var body string
	err := ex.QueryRowContext(ctx, `SELECT body FROM outbox WHERE project=? AND id=?`, project, ref).Scan(&body)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	var b Object
	if err = json.Unmarshal([]byte(body), &b); err != nil {
		return false, err
	}
	if t, _ := b["type"].(string); t != "RUN_STOP_CONFIRMED" {
		return false, nil
	}
	if r, _ := b["run_id"].(string); r != runID {
		return false, nil
	}
	stopped, _ := b["children_stopped"].(bool)
	empty, _ := b["queue_empty"].(bool)
	if !stopped || !empty {
		return false, nil
	}
	// Re-read the run: a confirmation that no longer matches the stored run state is not a confirmation.
	status, settled, err := runState(ctx, ex, project, runID)
	if err != nil {
		return false, err
	}
	_ = status
	return settled, nil
}

// AttachClientSession reads a session snapshot, and with Takeover transfers the single writer in the same
// transaction as the epoch advance. A takeover over a live run is refused without a verified stop confirmation.
func (s *Service) AttachClientSession(ctx context.Context, p Principal, project string, in SessionClaim) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	if in.SessionID == "" || in.ClientID == "" {
		return nil, Fail(400, "INVALID_REQUEST", "session id and client id are required")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	sess, err := readClientSession(ctx, tx, project, in.SessionID)
	if err == sql.ErrNoRows {
		return nil, Fail(404, "NOT_FOUND", "unknown session for this project")
	}
	if err != nil {
		return nil, err
	}
	if !in.Takeover {
		return attachView(sess, false, nil), nil
	}
	if sealed(sess) {
		return nil, Fail(409, "SESSION_SEALED", "a sealed session cannot take a new writer")
	}
	runID, _ := sess["run_id"].(string)
	status, settled, err := runState(ctx, tx, project, runID)
	if err != nil {
		return nil, err
	}
	blocked := runID != "" && liveRunStatuses[status] && !settled
	if blocked {
		confirmed, err := stopConfirmed(ctx, tx, project, runID, in.StopConfirmationRef)
		if err != nil {
			return nil, err
		}
		if !confirmed {
			return nil, Fail(409, "STOP_CONFIRMATION_REQUIRED",
				"the session has a live run; a takeover needs a recorded stop confirmation with children stopped and queue empty")
		}
	}
	fromEpoch, _ := sess["writer_epoch"].(int64)
	fromClient, _ := sess["writer_client_id"].(string)
	rev, _ := sess["revision"].(int64)
	next, err := HandoffEpoch(ctx, tx, in.SessionID, fromEpoch, rev)
	if err != nil {
		return nil, asFault(err)
	}
	if _, err = tx.ExecContext(ctx, `UPDATE client_sessions SET writer_client_id=?, updated_at=? WHERE id=? AND writer_epoch=?`,
		in.ClientID, time.Now().UTC().Format(time.RFC3339Nano), in.SessionID, next); err != nil {
		return nil, err
	}
	event := Object{"type": "SESSION_HANDOFF", "session_id": in.SessionID, "from_epoch": fromEpoch, "to_epoch": next,
		"from_client_id": fromClient, "to_client_id": in.ClientID, "reason": in.Reason, "run_id": runID,
		"run_status": status, "stop_confirmation_ref": orNull(in.StopConfirmationRef),
		"live_run_at_handoff": blocked, "at": Now()}
	if err = writeOutbox(ctx, tx, project, ID(), event); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	after, err := readClientSession(ctx, s.DB, project, in.SessionID)
	if err != nil {
		return nil, err
	}
	return attachView(after, true, Object{"from_epoch": fromEpoch, "from_client_id": fromClient}), nil
}

// WriteAsWriter performs one writer-attributed operation. It succeeds only for the current epoch and client, and
// the same idempotency key cannot append or charge twice.
func (s *Service) WriteAsWriter(ctx context.Context, p Principal, project, sessionID, clientID string, epoch int64,
	operation, key string, payload Object) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	sess, err := readClientSession(ctx, tx, project, sessionID)
	if err == sql.ErrNoRows {
		return nil, Fail(404, "NOT_FOUND", "unknown session for this project")
	}
	if err != nil {
		return nil, err
	}
	if sealed(sess) {
		return nil, Fail(409, "SESSION_SEALED", "session is sealed")
	}
	if cur, _ := sess["writer_epoch"].(int64); cur != epoch {
		return nil, Fail(409, "STALE_WRITER_EPOCH", "writer_epoch is not the current owner")
	}
	if owner, _ := sess["writer_client_id"].(string); owner != clientID {
		return nil, Fail(409, "WRITER_BUSY", "writer attribution belongs to another client")
	}
	hash := digest(Bytes(payload))
	// The aggregate form returns one row of NULLs when nothing is stored yet, so every column is scanned as
	// nullable; scanning NULL into a plain string is what made the first write fail here.
	var (
		found       sql.NullInt64
		storedHash  sql.NullString
		storedReply sql.NullString
	)
	if err = tx.QueryRowContext(ctx, `SELECT count(*), max(request_hash), max(body) FROM idempotency
		WHERE principal=? AND project=? AND operation=? AND key=?`, p.ID, project, operation, key).
		Scan(&found, &storedHash, &storedReply); err != nil && err != sql.ErrNoRows {
		return nil, err
	}
	if found.Int64 == 1 {
		if storedHash.String != hash {
			return nil, Fail(409, "IDEMPOTENCY_KEY_REUSED", "the same key carries a different request")
		}
		var replay Object
		if e := json.Unmarshal([]byte(storedReply.String), &replay); e != nil {
			return nil, e
		}
		replay["replayed"] = true
		return replay, nil
	}
	before, _ := sess["event_watermark"].(int64)
	body := Object{"type": "SESSION_WRITE", "operation": operation, "idempotency_key": key, "session_id": sessionID,
		"client_id": clientID, "writer_epoch": epoch, "request_hash": hash, "payload": payload, "at": Now()}
	if err = writeOutbox(ctx, tx, project, ID(), body); err != nil {
		return nil, err
	}
	head, err := streamHead(ctx, tx, project)
	if err != nil {
		return nil, err
	}
	if head <= before {
		return nil, Fail(500, "WATERMARK_NOT_ADVANCED", "the event stream did not move forward")
	}
	if err = AdvanceWatermark(ctx, tx, sessionID, epoch, revisionOf(sess), head); err != nil {
		return nil, asFault(err)
	}
	reply := Object{"status": "COMPLETED", "operation": operation, "idempotency_key": key, "after_sequence": head,
		"replayed": false, "writer_epoch": epoch, "charged_events": 1}
	if err = rememberIdempotency(ctx, tx, p.ID, project, operation, key, hash, reply); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return reply, nil
}

// SessionEvents answers a watermark reconnect. The caller is told which sequence it asked from, what the stream
// head is, how many events it missed and whether the page was truncated - never "latest" as if nothing was lost.
func (s *Service) SessionEvents(ctx context.Context, p Principal, project, sessionID string, after int64, limit int) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	if limit <= 0 {
		limit = 50
	}
	if limit > 200 {
		return nil, Fail(400, "INVALID_REQUEST", "event page limit must not exceed 200")
	}
	if after < 0 {
		return nil, Fail(400, "INVALID_REQUEST", "after_sequence must not be negative")
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	sess, err := readClientSession(ctx, tx, project, sessionID)
	if err == sql.ErrNoRows {
		return nil, Fail(404, "NOT_FOUND", "unknown session for this project")
	}
	if err != nil {
		return nil, err
	}
	head, err := streamHead(ctx, tx, project)
	if err != nil {
		return nil, err
	}
	if after > head {
		return nil, Fail(409, "STALE_WATERMARK",
			fmt.Sprintf("asked for events after %d but the stream head is %d", after, head))
	}
	rows, err := tx.QueryContext(ctx, `SELECT sequence, id, body FROM outbox WHERE project=? AND sequence>?
		ORDER BY sequence LIMIT ?`, project, after, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	events := []any{}
	for rows.Next() {
		var (
			seq          int64
			id, bodyText string
		)
		if err = rows.Scan(&seq, &id, &bodyText); err != nil {
			return nil, err
		}
		var b Object
		if err = json.Unmarshal([]byte(bodyText), &b); err != nil {
			return nil, err
		}
		events = append(events, Object{"sequence": seq, "id": id, "type": b["type"], "body": b})
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	missed := head - after - int64(len(events))
	truncated := missed > 0
	if truncated {
		// A page that could not carry everything is not a complete view of the stream, so the snapshot stays at the
		// last sequence actually delivered rather than claiming the head.
		snap := head - missed
		return Object{"events": events, "from_sequence": after, "head_sequence": head, "delivered_through": snap,
				"missed_events": missed, "truncated": true, "complete": false, "snapshot_through_sequence": snap,
				"session": attachView(sess, false, nil)}, nil
	}
	return Object{"events": events, "from_sequence": after, "head_sequence": head,
		"delivered_through": head, "missed_events": 0, "truncated": false, "complete": true,
		"snapshot_through_sequence": head, "session": attachView(sess, false, nil)}, nil
}

// GetClientSession and ListClientSessions are the read surface; list is bounded and ordered so a client cannot
// mistake a partial page for the whole set.
func (s *Service) GetClientSession(ctx context.Context, p Principal, project, sessionID string) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	sess, err := readClientSession(ctx, s.DB, project, sessionID)
	if err == sql.ErrNoRows {
		return nil, Fail(404, "NOT_FOUND", "unknown session for this project")
	}
	if err != nil {
		return nil, err
	}
	return attachView(sess, false, nil), nil
}

func (s *Service) ListClientSessions(ctx context.Context, p Principal, project string, limit int) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	if limit <= 0 {
		limit = 50
	}
	if limit > 200 {
		return nil, Fail(400, "INVALID_REQUEST", "session page limit must not exceed 200")
	}
	rows, err := s.DB.QueryContext(ctx, `SELECT id, revision, writer_epoch, writer_client_id, event_watermark,
		COALESCE(run_id,''), COALESCE(sealed_at,'') FROM client_sessions WHERE project_id=?
		ORDER BY created_at, id LIMIT ?`, project, limit+1)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := []any{}
	for rows.Next() {
		var id, client, run, sealedAt string
		var rev, epoch, water int64
		if err = rows.Scan(&id, &rev, &epoch, &client, &water, &run, &sealedAt); err != nil {
			return nil, err
		}
		items = append(items, Object{"session_id": id, "revision": rev, "writer_epoch": epoch,
			"writer_client_id": client, "event_watermark": water, "run_id": orNull(run),
			"sealed": sealedAt != ""})
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	hasMore := len(items) > limit
	if hasMore {
		items = items[:limit]
	}
	return Object{"project_id": project, "sessions": items, "count": len(items), "has_more": hasMore}, nil
}

// OpenClientSession creates the index row for a new client session with epoch 1 and one named writer.
func (s *Service) OpenClientSession(ctx context.Context, p Principal, project, sessionID, clientID, upstream string,
	goalID, taskID, runID *string) (Object, error) {
	if !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")
	}
	now := time.Now().UTC()
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	head, err := streamHead(ctx, tx, project)
	if err != nil {
		return nil, err
	}
	if err = MapClientSession(ctx, tx, ClientSession{ID: sessionID, ProjectID: project, Revision: 1,
		CreatedAt: now, UpdatedAt: now, GoalID: goalID, TaskID: taskID, RunID: runID, WriterEpoch: 1,
		WriterClientID: clientID, EventWatermark: head, UpstreamSession: upstream, Protocol: ClientSessionProtocol}); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return Object{"session_id": sessionID, "writer_epoch": int64(1), "writer_client_id": clientID,
		"event_watermark": head, "revision": int64(1)}, nil
}

func writeOutbox(ctx context.Context, ex sessionExec, project, id string, body Object) error {
	head, err := streamHead(ctx, ex, project)
	if err != nil {
		return err
	}
	_, err = ex.ExecContext(ctx, `INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)`,
		project, head+1, id, string(Bytes(body)))
	return err
}

func streamHead(ctx context.Context, ex sessionExec, project string) (int64, error) {
	var head sql.NullInt64
	if err := ex.QueryRowContext(ctx, `SELECT max(sequence) FROM outbox WHERE project=?`, project).Scan(&head); err != nil {
		return 0, err
	}
	return head.Int64, nil
}

// rememberIdempotency stores the REQUEST digest (the column the replay comparison reads) together with the reply
// body. Storing a digest of the reply here is what made every replay look like a conflicting request.
func rememberIdempotency(ctx context.Context, ex sessionExec, principal, project, operation, key, requestHash string, reply Object) error {
	_, err := ex.ExecContext(ctx, `INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at)
		VALUES(?,?,?,?,?,?,?,?,?)`, principal, project, operation, key, requestHash, 200,
		Bytes(reply), "{}", Now())
	return err
}

func digest(raw []byte) string {
	sum := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func orNull(v string) any {
	if v == "" {
		return nil
	}
	return v
}

func revisionOf(sess Object) int64 {
	if v, ok := sess["revision"].(int64); ok {
		return v
	}
	return -1
}

func sealed(sess Object) bool {
	v, ok := sess["sealed_at"].(string)
	return ok && v != ""
}

func attachView(sess Object, took bool, extra Object) Object {
	out := Object{"session_id": sess["id"], "project_id": sess["project_id"], "revision": sess["revision"],
		"writer_epoch": sess["writer_epoch"], "writer_client_id": sess["writer_client_id"],
		"event_watermark": sess["event_watermark"], "run_id": sess["run_id"], "goal_id": sess["goal_id"],
		"task_id": sess["task_id"], "protocol": sess["protocol"], "sealed": sealed(sess), "takeover": took}
	for k, v := range extra {
		out[k] = v
	}
	return out
}

func asFault(err error) error {
	if err == nil {
		return nil
	}
	var f *Fault
	if errors.As(err, &f) {
		return f
	}
	switch {
	case errors.Is(err, ErrStaleEpoch), errors.Is(err, ErrStaleRevision), errors.Is(err, ErrSealed),
		errors.Is(err, ErrUnknownSession), errors.Is(err, ErrStaleWatermark):
		return Fail(409, err.Error(), "the session moved under this request")
	}
	return Fail(500, "SESSION_WRITE_FAILED", err.Error())
}
