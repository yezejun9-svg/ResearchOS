package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"strings"
	"unicode/utf8"
)

const clientQueueCapacity = 32

// The fence belongs to the original Task, including the interval before claim.
// It is never reopened by a lease transfer, restart or restore.
func ensureClientQueue(tx *sql.Tx, project, session, task string) error {
	_, err := tx.Exec(`INSERT INTO client_queue_fences(project,task_id,session_id,generation,state) VALUES(?,?,?,?,'OPEN') ON CONFLICT(project,task_id) DO NOTHING`, project, task, session, ID())
	return err
}

func (s *ClientService) enqueueClientMessage(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow, task Object, text, delivery string, attachments []string) (*Response, error) {
	if delivery != "STEER" && delivery != "FOLLOW_UP" {
		return NewTypedRejection(env, "INVALID_REQUEST", "unsupported delivery"), nil
	}
	if strings.TrimSpace(text) == "" || utf8.RuneCountInString(text) > 16384 {
		return NewTypedRejection(env, "CONTENT_TOO_LARGE", "message must contain 1 to 16384 characters"), nil
	}
	if task["status"] == "CANCELLED" || task["status"] == "ACCEPTED" || task["status"] == "FAILED" || clientTurnSettled(tx, sess.project, sess.sessionID, task) {
		return NewTypedRejection(env, "SESSION_BUSY", "an unsettled original task is required"), nil
	}
	p, err := clientPrincipal(ctx, tx, principal, sess.project, true)
	if err != nil {
		return clientFault(env, err)
	}
	// Custom Mu messages support text. Pin and retain every accepted attachment's
	// original version and bytes; binary conversion is rejected before acceptance.
	content := Object{"text": text, "attachments": Empty()}
	seen := map[string]bool{}
	for _, id := range attachments {
		if seen[id] {
			return NewTypedRejection(env, "INVALID_REQUEST", "duplicate attachment"), nil
		}
		seen[id] = true
		a, e := s.Domain.readObject(tx, p, sess.project, "Artifact", id)
		if e != nil {
			return clientFault(env, e)
		}
		if e = s.Domain.effective(tx, sess.project, Ref(a, "Artifact")); e != nil {
			return clientFault(env, e)
		}
		media := Str(a, "media_type")
		if !strings.HasPrefix(media, "text/") && media != "application/json" {
			return NewTypedRejection(env, "UNSUPPORTED_CONTENT", "queued attachments require UTF-8 text"), nil
		}
		var raw []byte
		if e = tx.QueryRowContext(ctx, "SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=?", sess.project, a["storage_key"]).Scan(&raw); e != nil {
			return nil, e
		}
		if !utf8.Valid(raw) || Digest(raw) != a["content_hash"] {
			return NewTypedRejection(env, "UNSUPPORTED_CONTENT", "attachment bytes are not verified UTF-8"), nil
		}
		content["attachments"] = append(Arr(content, "attachments"), Object{"ref": Ref(a, "Artifact"), "media_type": media, "text": string(raw)})
	}
	raw := Bytes(content)
	if len(raw) > 32*1024 {
		return NewTypedRejection(env, "CONTENT_TOO_LARGE", "queued content exceeds the bounded worker frame"), nil
	}
	if err = ensureClientQueue(tx, sess.project, sess.sessionID, Str(task, "id")); err != nil {
		return nil, err
	}
	var generation, state string
	var sequence int64
	var restore int
	if err = tx.QueryRowContext(ctx, `SELECT generation,state,accepted_through,restore_fenced FROM client_queue_fences WHERE project=? AND task_id=? AND session_id=?`, sess.project, task["id"], sess.sessionID).Scan(&generation, &state, &sequence, &restore); err != nil {
		return nil, err
	}
	if state != "OPEN" || restore != 0 {
		return NewTypedRejection(env, "SESSION_BUSY", "original worker queue is fenced"), nil
	}
	var count int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FROM client_command_queue WHERE generation=? AND state NOT IN ('CONSUMED','DROPPED')`, generation).Scan(&count); err != nil {
		return nil, err
	}
	if count >= clientQueueCapacity || sequence >= clientQueueCapacity {
		return NewTypedRejection(env, "RESOURCE_BLOCKED", "original worker queue capacity reached"), nil
	}
	if runID := Str(task, "active_run_id"); runID != "" {
		run, e := load(tx, sess.project, "Run", runID)
		if e != nil {
			return nil, e
		}
		if runTerminal(run) || run["status"] == "CANCEL_REQUESTED" || run["status"] == "RECONCILING" || run["status"] == "LOST" {
			return NewTypedRejection(env, "SESSION_BUSY", "original run cannot accept input"), nil
		}
	}
	sequence++
	messageID := ID()
	requestHash, err := env.ContentHash()
	if err != nil {
		return nil, err
	}
	if _, err = tx.ExecContext(ctx, `INSERT INTO client_command_queue(principal,project,command_id,session_id,task_id,goal_id,generation,queue_sequence,request_hash,message_id,accepted_writer_epoch,delivery,content,content_hash,state,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,'ENQUEUED',?)`, principal, sess.project, deref(env.CommandID), sess.sessionID, task["id"], task["goal_id"], generation, sequence, requestHash, messageID, sess.epoch, delivery, string(raw), Digest(raw), Now()); err != nil {
		return nil, err
	}
	if _, err = tx.ExecContext(ctx, `UPDATE client_queue_fences SET accepted_through=?,revision=revision+1 WHERE generation=?`, sequence, generation); err != nil {
		return nil, err
	}
	for _, part := range []Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0}, {"phase": "DELTA", "text": text, "content_offset_utf8_bytes": 0}, {"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(text))}} {
		part["message_id"], part["role"], part["part_index"] = messageID, "USER", 0
		if err = s.journal(ctx, tx, env, sess, "MESSAGE", part); err != nil {
			return nil, err
		}
		sess.revision++
		sess.watermark++
	}
	if err = s.Domain.sealSessionTranscript(ctx, tx, s.Doc, sess.project, sess.sessionID, principal); err != nil {
		return nil, err
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
	if err != nil {
		return nil, err
	}
	var run any
	if id := Str(task, "active_run_id"); id != "" {
		run = id
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(sess.revision), Result: Object{"message_id": messageID, "queue_position": sequence, "run_id": run, "snapshot": snap}}, nil
}

func clientPendingCommands(ctx context.Context, tx *sql.Tx, project, session string) ([]any, error) {
	rows, err := tx.QueryContext(ctx, `SELECT command_id FROM client_command_queue WHERE project=? AND session_id=? AND state NOT IN ('CONSUMED','DROPPED') UNION SELECT command_id FROM client_control_requests WHERE project=? AND session_id=? AND state<>'CONFIRMED' ORDER BY command_id`, project, session, project, session)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	ids := Empty()
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	return ids, rows.Err()
}

func clientQueueSettled(tx *sql.Tx, project, run string) error {
	installed, err := clientQueueInstalled(tx)
	if err != nil || !installed {
		return err
	}
	var n int
	err = tx.QueryRow(`SELECT count(*) FROM client_queue_fences f WHERE f.project=? AND f.run_id=? AND (f.state NOT IN ('SEALED','CANCEL_FENCED') OR f.restore_fenced<>0 OR f.accepted_through<>f.sealed_through OR EXISTS(SELECT 1 FROM client_command_queue q WHERE q.generation=f.generation AND q.state NOT IN ('CONSUMED','DROPPED')))`, project, run).Scan(&n)
	if err != nil {
		return err
	}
	if n != 0 {
		return Fail(409, "GATE_FAILED", "canonical command queue remains unsettled")
	}
	return nil
}

// Transition evidence is immutable. An identical receipt is safe to import
// again; conflicting evidence cannot overwrite the prior fact.
func appendClientReceipt(tx *sql.Tx, project, generation, command, kind, id string, body Object, previous any) error {
	raw := Bytes(body)
	digest := Digest(raw)
	var old string
	err := tx.QueryRow("SELECT body_hash FROM client_control_receipts WHERE receipt_id=?", id).Scan(&old)
	if err == nil {
		if old != digest {
			return Fail(409, "GATE_FAILED", "conflicting command receipt")
		}
		return nil
	}
	if err != sql.ErrNoRows {
		return err
	}
	_, err = tx.Exec(`INSERT INTO client_control_receipts(receipt_id,project,generation,command_id,kind,body,body_hash,previous_receipt_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)`, id, project, generation, command, kind, string(raw), digest, previous, Now())
	return err
}

func queueObject(raw string) (Object, error) {
	var o Object
	err := json.Unmarshal([]byte(raw), &o)
	return o, err
}

// Historical matching-program upgrade fixtures retain their pre-22 behavior.
func clientQueueInstalled(tx *sql.Tx) (bool, error) {
	var version int
	err := tx.QueryRow(`SELECT coalesce(max(version),0) FROM schema_migrations`).Scan(&version)
	return version >= 22, err
}
