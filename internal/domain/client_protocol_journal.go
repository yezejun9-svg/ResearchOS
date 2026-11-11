package domain

// Durable session-event boundary for researchos-client/2 (W03-02).
//
// One command transaction writes business state AND the journal row, so a replayed
// command can never produce a second event: the journal sequence is issued from the
// session watermark (forward-only CAS through AdvanceWatermark), the event id is the
// outbox primary key, and any commit failure rolls both back. Gap detection and
// snapshot recovery use the same watermark the writers advance, so client and server
// cannot disagree about what "caught up" means.

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
)

const (
	// MaxEventPage bounds one session.events page; larger asks return has_more.
	MaxEventPage = 200
	// MaxSnapshotMessages is SessionSnapshot.messages maxItems.
	MaxSnapshotMessages = 200
)

var (
	ErrSnapshotIncomplete = errors.New("SNAPSHOT_SOURCE_INCOMPLETE")
	ErrStreamWithoutStart = errors.New("MESSAGE_STREAM_WITHOUT_START")
)

// ClientEventPage is the typed session.events result body (schema ReadEventsResult).
type ClientEventPage struct {
	Events        []SessionEvent `json:"events"`
	NextSequence  int64          `json:"next_sequence"`
	HighWatermark int64          `json:"high_watermark"`
	HasMore       bool           `json:"has_more"`
}

// AppendSessionEvent journals one typed event inside the caller's transaction.
// epoch/expectedRevision are the writer's own claim: the same CAS rules as every other
// write apply, so a stale writer or a stale snapshot cannot emit.
func AppendSessionEvent(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project string, ev *SessionEvent, epoch, expectedRevision int64) error {
	return appendSessionEvent(ctx, tx, doc, project, ev, epoch, expectedRevision, false)
}

// Only the runtime stream commit path uses this private watermark-only variant.
func appendRuntimeMessageEvent(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project string, ev *SessionEvent, epoch, expectedRevision int64) error {
	if ev == nil || ev.Kind == nil || *ev.Kind != "MESSAGE" || ev.RunID == nil || *ev.RunID == "" {
		return fmt.Errorf("runtime MESSAGE identity required")
	}
	return appendSessionEvent(ctx, tx, doc, project, ev, epoch, expectedRevision, true)
}

func appendSessionEvent(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project string, ev *SessionEvent, epoch, expectedRevision int64, runtimeMessage bool) error {
	if ev == nil || ev.SessionID == nil || ev.Kind == nil || ev.Sequence == nil {
		return fmt.Errorf("UNtyped_EVENT")
	}
	if err := ValidateEventPayload(doc, ev); err != nil {
		return err
	}
	var wm, curRev, curEpoch int64
	var sealed sql.NullString
	err := tx.QueryRowContext(ctx,
		`SELECT event_watermark, revision, writer_epoch, sealed_at FROM client_sessions WHERE id=? AND project_id=?`,
		*ev.SessionID, project).Scan(&wm, &curRev, &curEpoch, &sealed)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return ErrUnknownSession
		}
		return err
	}
	if sealed.Valid {
		return ErrSealed
	}
	// Unified numbering rule: exactly watermark+1. Reuse (<=) and holes (>) are both
	// rejected here instead of being repaired later.
	if want := wm + 1; *ev.Sequence != want {
		return fmt.Errorf("%w: got %d want %d", ErrEventSequence, *ev.Sequence, want)
	}
	if *ev.Kind == "MESSAGE" {
		var p struct {
			MessageID *string `json:"message_id"`
			Phase     *string `json:"phase"`
		}
		if err := json.Unmarshal(ev.Payload, &p); err != nil {
			return err
		}
		if p.MessageID != nil && p.Phase != nil && *p.Phase != "START" {
			var n int
			if err := tx.QueryRowContext(ctx,
				`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=?
				 AND json_extract(body,'$.kind')='MESSAGE'
				 AND json_extract(body,'$.payload.message_id')=?
				 AND json_extract(body,'$.payload.phase')='START'`,
				project, *ev.SessionID, *p.MessageID).Scan(&n); err != nil {
				return err
			}
			if n == 0 {
				return ErrStreamWithoutStart
			}
		}
	}
	body, err := json.Marshal(ev)
	if err != nil {
		return err
	}
	// Both mutations (journal row + watermark CAS) are one unit: a savepoint means a failed
	// watermark compare leaves no orphan event even if the caller later commits.
	if _, err := tx.ExecContext(ctx, `SAVEPOINT client_event`); err != nil {
		return err
	}
	if err := appendEventRows(ctx, tx, project, ev, body, epoch, expectedRevision, runtimeMessage); err != nil {
		if _, rbErr := tx.ExecContext(ctx, `ROLLBACK TO client_event`); rbErr != nil {
			return errors.Join(err, rbErr)
		}
		if _, relErr := tx.ExecContext(ctx, `RELEASE client_event`); relErr != nil {
			return errors.Join(err, relErr)
		}
		return err
	}
	_, err = tx.ExecContext(ctx, `RELEASE client_event`)
	return err
}

func appendEventRows(ctx context.Context, tx *sql.Tx, project string, ev *SessionEvent, body []byte, epoch, expectedRevision int64, runtimeMessage bool) error {
	var next int64
	if err := tx.QueryRowContext(ctx, `SELECT COALESCE(MAX(sequence),0)+1 FROM outbox WHERE project=?`, project).Scan(&next); err != nil {
		return err
	}
	if _, err := tx.ExecContext(ctx, `INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)`,
		project, next, *ev.EventID, string(body)); err != nil {
		return err
	}
	if runtimeMessage {
		return advanceRuntimeMessageWatermark(ctx, tx, project, *ev.SessionID, epoch, expectedRevision, *ev.Sequence-1, *ev.Sequence)
	}
	// Watermark advance is the same forward-only, epoch-guarded CAS every other write uses.
	return AdvanceWatermark(ctx, tx, *ev.SessionID, epoch, expectedRevision, *ev.Sequence)
}

// ReadSessionEvents returns the typed journal tail after afterSequence, or
// ErrResyncRequired when the client claims a position the session never had.
func ReadSessionEvents(ctx context.Context, tx *sql.Tx, project, sessionID string, afterSequence, limit int64) (*ClientEventPage, error) {
	var wm int64
	if err := tx.QueryRowContext(ctx, `SELECT event_watermark FROM client_sessions WHERE id=? AND project_id=?`,
		sessionID, project).Scan(&wm); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, ErrUnknownSession
		}
		return nil, err
	}
	if afterSequence > wm {
		return nil, ErrResyncRequired
	}
	if limit <= 0 || limit > MaxEventPage {
		limit = MaxEventPage
	}
	rows, err := tx.QueryContext(ctx,
		`SELECT body FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=?
		 AND json_extract(body,'$.sequence') > ?
		 ORDER BY json_extract(body,'$.sequence') ASC LIMIT ?`,
		project, sessionID, afterSequence, limit+1)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	page := &ClientEventPage{Events: []SessionEvent{}, HighWatermark: wm}
	var got int64
	var last int64
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		got++
		if got > limit {
			page.HasMore = true
			break
		}
		var ev SessionEvent
		if err := json.Unmarshal([]byte(raw), &ev); err != nil {
			return nil, err
		}
		if ev.Sequence == nil {
			return nil, fmt.Errorf("UNtyped_EVENT")
		}
		last = *ev.Sequence
		page.Events = append(page.Events, ev)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	// With more rows pending the client continues from the last delivered sequence;
	// otherwise it is caught up and next_sequence equals the watermark.
	if page.HasMore {
		page.NextSequence = last
	} else {
		page.NextSequence = wm
	}
	return page, nil
}

// DetectEventGaps reports per-session sequence holes. Because append happens inside the
// business transaction, a hole means an aborted commit or external tampering, so
// qualification asserts this stays empty.
func DetectEventGaps(ctx context.Context, tx *sql.Tx, project, sessionID string) ([]int64, error) {
	rows, err := tx.QueryContext(ctx,
		`SELECT json_extract(body,'$.sequence') FROM outbox
		 WHERE project=? AND json_extract(body,'$.session_id')=? ORDER BY 1 ASC`, project, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var seen []int64
	for rows.Next() {
		var s int64
		if err := rows.Scan(&s); err != nil {
			return nil, err
		}
		seen = append(seen, s)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	var missing []int64
	for i, s := range seen {
		if s != int64(i+1) {
			missing = append(missing, int64(i+1))
		}
	}
	return missing, nil
}

// runStatusMap / goalStatusMap translate existing domain lifecycle values into the
// published snapshot enums; anything unmapped answers null instead of inventing state.
var runStatusMap = map[string]string{
	"QUEUED": "QUEUED", "STARTING": "STARTING", "RUNNING": "RUNNING",
	"CANCEL_REQUESTED": "CANCEL_REQUESTED", "SETTLED": "SETTLED", "COMPLETED": "SETTLED",
	"FAILED": "FAILED", "CANCELLED": "CANCELLED", "LOST": "LOST", "RECONCILING": "RECONCILING",
}

var goalStatusMap = map[string]string{
	"DRAFT": "DRAFT", "ACTIVE": "ACTIVE", "PAUSED": "PAUSED", "VERIFYING": "VERIFYING",
	"ACCEPTED": "ACCEPTED", "BLOCKED": "BLOCKED", "CANCELLED": "CANCELLED",
	"NEEDS_REVALIDATION": "NEEDS_REVALIDATION",
}

// BuildSessionSnapshot assembles the typed SessionSnapshot for one session from the
// authoritative index row plus the durable journal. Fields whose producing subsystem is
// a later card are emitted as schema-legal nulls/empties; a missing non-null source
// (workspace, model config, core build, native session) fails closed instead of
// fabricating a value.
func BuildSessionSnapshot(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sessionID string) (map[string]any, error) {
	var (
		revision, wm, epoch                     int64
		createdAt, updatedAt                    string
		writerClient                            string
		goalID, taskID, runID                   sql.NullString
		leaseExpires, workspaceRef, title       sql.NullString
		modelConfigRef, coreBuildID, archivedAt sql.NullString
		resumeExplicit                          int
	)
	err := tx.QueryRowContext(ctx, `SELECT revision, event_watermark, writer_epoch, created_at, updated_at,
		goal_id, task_id, run_id, lease_expires_at, workspace_ref, title, model_config_ref, core_build_id,
		archived_at, resume_requires_explicit_user, writer_client_id, upstream_session_id
		FROM client_sessions WHERE id=? AND project_id=?`, sessionID, project).
		Scan(&revision, &wm, &epoch, &createdAt, &updatedAt, &goalID, &taskID, &runID,
			&leaseExpires, &workspaceRef, &title, &modelConfigRef, &coreBuildID,
			&archivedAt, &resumeExplicit, &writerClient, new(sql.NullString))
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrUnknownSession
	}
	if err != nil {
		return nil, err
	}
	var upstream string
	if err := tx.QueryRowContext(ctx, `SELECT upstream_session_id FROM client_sessions WHERE id=?`, sessionID).Scan(&upstream); err != nil {
		return nil, err
	}
	for name, v := range map[string]string{"workspace_ref": workspaceRef.String, "model_config_ref": modelConfigRef.String,
		"core_build_id": coreBuildID.String, "native_session_ref": upstream} {
		if v == "" {
			return nil, fmt.Errorf("%w:%s", ErrSnapshotIncomplete, name)
		}
	}
	transcript, err := replaySessionTranscript(ctx, tx, doc, project, sessionID)
	if err != nil {
		return nil, err
	}
	transcriptRef, err := snapshotTranscriptRef(ctx, tx, project, sessionID, transcript)
	if err != nil {
		return nil, err
	}
	messages := transcript.messages
	hasEarlier := len(messages) > MaxSnapshotMessages
	start := 0
	if hasEarlier {
		start = len(messages) - MaxSnapshotMessages
		messages = messages[start:]
	}
	earliest := int64(0)
	if len(messages) > 0 {
		earliest, _ = Num(transcript.sequences[start].(Object), "start_sequence")
	}
	writer := any(nil)
	if leaseExpires.Valid {
		writer = map[string]any{"client_id": writerClient, "epoch": epoch, "expires_at": leaseExpires.String}
	}
	permissions, err := snapshotPermissions(ctx, tx, doc, project, sessionID)
	if err != nil {
		return nil, err
	}
	pending, err := clientPendingCommands(ctx, tx, project, sessionID)
	if err != nil {
		return nil, err
	}
	snap := map[string]any{
		"session_id":                    sessionID,
		"project_id":                    project,
		"workspace_ref":                 workspaceRef.String,
		"native_session_ref":            upstream,
		"core_build_id":                 coreBuildID.String,
		"protocol_version":              ProtocolV2,
		"revision":                      revision,
		"title":                         title.String,
		"archived_at":                   nullable(archivedAt),
		"created_at":                    createdAt,
		"updated_at":                    updatedAt,
		"model_config_ref":              modelConfigRef.String,
		"goal_id":                       nullable(goalID),
		"active_run_id":                 nullable(runID),
		"run_status":                    mappedStatus(ctx, tx, runID, runStatusMap),
		"goal_status":                   mappedStatus(ctx, tx, goalID, goalStatusMap),
		"writer":                        writer,
		"event_sequence":                wm,
		"earliest_event_sequence":       earliest,
		"checkpoint_artifact_ref":       nil,
		"pending_command_ids":           pending,
		"pending_permissions":           permissions,
		"resume_requires_explicit_user": resumeExplicit == 1,
		"messages":                      messages,
		"transcript_artifact_ref":       transcriptRef,
		"has_earlier_messages":          hasEarlier,
	}
	if doc != nil {
		if err := doc.ValidateDef("SessionSnapshot", normalizeNumbers(snap)); err != nil {
			return nil, fmt.Errorf("SNAPSHOT_SCHEMA:%v", err)
		}
	}
	return snap, nil
}

func nullable(s sql.NullString) any {
	if s.Valid {
		return s.String
	}
	return nil
}

func mappedStatus(ctx context.Context, tx *sql.Tx, ref sql.NullString, table map[string]string) any {
	if !ref.Valid {
		return nil
	}
	var body string
	if err := tx.QueryRowContext(ctx, `SELECT body FROM domain_objects WHERE id=? LIMIT 1`, ref.String).Scan(&body); err != nil {
		return nil
	}
	var m map[string]any
	if json.Unmarshal([]byte(body), &m) != nil {
		return nil
	}
	s, ok := m["status"].(string)
	if !ok {
		return nil
	}
	if mapped, ok := table[s]; ok {
		return mapped
	}
	return nil
}

// normalizeNumbers round-trips through JSON so int64/string Go types become the same
// generic tree the schema validator sees for a fixture.
func normalizeNumbers(m map[string]any) map[string]any {
	b, _ := json.Marshal(m)
	var out map[string]any
	json.Unmarshal(b, &out)
	return out
}
