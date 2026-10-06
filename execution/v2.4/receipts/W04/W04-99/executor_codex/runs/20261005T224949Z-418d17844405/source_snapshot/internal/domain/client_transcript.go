package domain

// The transcript is an immutable recovery copy of the MESSAGE journal. It is
// separate from the bounded Mu input history: there is no 32 KiB truncation here.
import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"sort"
	"unicode/utf8"
)

type sessionTranscript struct {
	messages, sequences []any
	through             int64
}

// replaySessionTranscript is shared by the writer and snapshot reader. It checks
// every byte offset and phase before either surface can claim complete recovery.
func replaySessionTranscript(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sessionID string) (*sessionTranscript, error) {
	var watermark int64
	if err := tx.QueryRowContext(ctx, `SELECT event_watermark FROM client_sessions WHERE id=? AND project_id=?`, sessionID, project).Scan(&watermark); err != nil {
		return nil, err
	}
	rows, err := tx.QueryContext(ctx, `SELECT body FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='MESSAGE' ORDER BY CAST(json_extract(body,'$.sequence') AS INTEGER)`, project, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := &sessionTranscript{messages: Empty(), sequences: Empty()}
	byID := map[string]*historyMessage{}
	ordered := []*historyMessage{}
	for rows.Next() {
		var raw string
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		if !utf8.ValidString(raw) {
			return nil, historyInvalid("transcript event UTF-8")
		}
		ev, err := DecodeEvent([]byte(raw))
		if err != nil || deref(ev.SessionID) != sessionID || ev.Sequence == nil || *ev.Sequence <= result.through || *ev.Sequence > watermark {
			return nil, historyInvalid("transcript envelope or watermark")
		}
		if err := ValidateEventPayload(doc, ev); err != nil {
			return nil, historyInvalid("transcript payload")
		}
		var p struct {
			ID     string  `json:"message_id"`
			Role   string  `json:"role"`
			Phase  string  `json:"phase"`
			Index  *int64  `json:"part_index"`
			Offset *int64  `json:"content_offset_utf8_bytes"`
			Text   *string `json:"text"`
		}
		if json.Unmarshal(ev.Payload, &p) != nil || p.ID == "" || p.Index == nil || *p.Index < 0 || *p.Index >= 64 || p.Offset == nil || *p.Offset < 0 || p.Text == nil || !utf8.ValidString(*p.Text) || (p.Role != "USER" && p.Role != "ASSISTANT" && p.Role != "SYSTEM") {
			return nil, historyInvalid("transcript message fields")
		}
		result.through = *ev.Sequence
		m := byID[p.ID]
		if m == nil {
			m = &historyMessage{id: p.ID, role: p.Role, runID: deref(ev.RunID), parts: map[int64]*historyPart{}}
			byID[p.ID], ordered = m, append(ordered, m)
		} else if m.role != p.Role || m.runID != deref(ev.RunID) {
			return nil, historyInvalid("transcript role or source run changed")
		}
		part := m.parts[*p.Index]
		if part == nil {
			part = &historyPart{}
			m.parts[*p.Index] = part
		}
		switch p.Phase {
		case "START":
			if part.started || *p.Offset != 0 || *p.Text != "" {
				return nil, historyInvalid("transcript START")
			}
			part.started, part.start = true, result.through
			if m.start == 0 {
				m.start = result.through
			}
		case "DELTA":
			if !part.started || part.ended || *p.Offset != int64(len(part.text)) || *p.Text == "" {
				return nil, historyInvalid("transcript DELTA byte offset or phase")
			}
			part.text += *p.Text
		case "END":
			if !part.started || part.ended || *p.Offset != int64(len(part.text)) || *p.Text != "" {
				return nil, historyInvalid("transcript END byte offset or phase")
			}
			part.ended, part.end, m.end = true, result.through, result.through
		default:
			return nil, historyInvalid("transcript phase")
		}
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	for _, m := range ordered {
		indices := make([]int64, 0, len(m.parts))
		for idx := range m.parts {
			indices = append(indices, idx)
		}
		sort.Slice(indices, func(i, j int) bool { return indices[i] < indices[j] })
		parts, complete := Empty(), true
		for i, idx := range indices {
			p := m.parts[idx]
			if idx != int64(i) || !p.started {
				return nil, historyInvalid("transcript missing part")
			}
			complete = complete && p.ended
			parts = append(parts, Object{"part_index": idx, "text": p.text, "complete": p.ended})
		}
		result.messages = append(result.messages, Object{"message_id": m.id, "role": m.role, "parts": parts, "complete": complete})
		result.sequences = append(result.sequences, Object{"message_id": m.id, "start_sequence": m.start, "end_sequence": m.end, "source_run_id": nilIfEmpty(m.runID)})
	}
	return result, nil
}

func nilIfEmpty(value string) any {
	if value == "" {
		return nil
	}
	return value
}

// Use the same provenance gates as clientHistoryArtifact. OBSERVED describes
// recorded roles and bytes; LIVE requires all assistant source runs to qualify.
func transcriptProvenance(ctx context.Context, tx *sql.Tx, project, sessionID string, transcript *sessionTranscript) ([]any, string, string, error) {
	refs, seen, allLive, basis := Empty(), map[string]bool{}, true, "ALL_ASSISTANT_RUNS_LIVE"
	sawAssistant := false
	for i, value := range transcript.messages {
		message := value.(Object)
		if message["complete"] != true {
			return nil, "", "", historyInvalid("unfinished transcript")
		}
		if message["role"] != "ASSISTANT" {
			continue
		}
		sawAssistant = true
		sequence := transcript.sequences[i].(Object)
		runID := Str(sequence, "source_run_id")
		if runID == "" {
			allLive, basis = false, "ASSISTANT_RUN_UNKNOWN"
			continue
		}
		if seen[runID] {
			continue
		}
		seen[runID] = true
		run, err := load(tx, project, "Run", runID)
		if historyMissing(err) {
			allLive, basis = false, "ASSISTANT_RUN_UNKNOWN"
			continue
		}
		if err != nil {
			return nil, "", "", err
		}
		refs = append(refs, Ref(run, "Run"))
		if run["status"] != "SETTLED" || Str(run, "runtime_settled_at") == "" {
			allLive, basis = false, "ASSISTANT_RUN_NOT_SETTLED"
		}
		var projected int
		if err := tx.QueryRowContext(ctx, `SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='RUN_STATE' AND json_extract(body,'$.payload.status')='SETTLED' AND CAST(json_extract(body,'$.sequence') AS INTEGER)<?`, project, sessionID, runID, sequence["start_sequence"]).Scan(&projected); err != nil {
			return nil, "", "", err
		}
		if projected == 0 {
			allLive, basis = false, "ASSISTANT_RUN_PROJECTION_UNKNOWN"
		}
		registration, err := load(tx, project, "RuntimeRegistration", Str(run, "runtime_id"))
		if historyMissing(err) {
			allLive, basis = false, "ASSISTANT_RUN_RUNTIME_UNKNOWN"
			continue
		}
		if err != nil {
			return nil, "", "", err
		}
		if registration["measurement_mode"] != "LIVE" {
			allLive, basis = false, "FIXTURE_OR_UNKNOWN_ASSISTANT_RUN"
		}
	}
	if !sawAssistant {
		allLive, basis = false, "USER_JOURNAL_ONLY"
	}
	mode := "FIXTURE"
	if allLive {
		mode = "LIVE"
	}
	return refs, mode, basis, nil
}

func (s *Service) sealSessionTranscript(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sessionID, principal string) error {
	transcript, err := replaySessionTranscript(ctx, tx, doc, project, sessionID)
	if err != nil {
		return err
	}
	if len(transcript.messages) == 0 {
		return nil
	}
	refs, mode, basis, err := transcriptProvenance(ctx, tx, project, sessionID, transcript)
	if err != nil {
		return err
	}
	body := Object{"schema": "researchos.session-transcript.v1", "origin": "SESSION_MESSAGE_JOURNAL", "project_id": project, "session_id": sessionID, "through_sequence": transcript.through, "messages": transcript.messages, "message_sequences": transcript.sequences, "source_run_refs": refs, "measurement_basis": basis, "observation_scope": "journal roles and bytes only; message claims are not verified facts"}
	artifact, err := s.serverArtifactMode(tx, project, principal, "REPORT", mode, Bytes(body), Empty())
	if err != nil {
		return err
	}
	_, err = tx.ExecContext(ctx, `UPDATE client_sessions SET transcript_artifact_id=? WHERE id=? AND project_id=?`, artifact["id"], sessionID, project)
	return err
}

func snapshotTranscriptRef(ctx context.Context, tx *sql.Tx, project, sessionID string, transcript *sessionTranscript) (any, error) {
	var id sql.NullString
	if err := tx.QueryRowContext(ctx, `SELECT transcript_artifact_id FROM client_sessions WHERE id=? AND project_id=?`, sessionID, project).Scan(&id); err != nil {
		return nil, err
	}
	if !id.Valid {
		if len(transcript.messages) > MaxSnapshotMessages {
			return nil, fmt.Errorf("%w: complete transcript unavailable", ErrSnapshotIncomplete)
		}
		return nil, nil
	}
	artifact, err := load(tx, project, "Artifact", id.String)
	if err != nil {
		return nil, err
	}
	if artifact["id"] != id.String || artifact["project_id"] != project || artifact["kind"] != "REPORT" || artifact["evidence_kind"] != "OBSERVED" || artifact["access_class"] != "PROJECT" || artifact["validity"] != "CURRENT" || Str(artifact, "sealed_at") == "" || artifact["run_id"] != nil {
		return nil, historyInvalid("transcript artifact scope or seal")
	}
	var raw []byte
	var storedHash string
	if err := tx.QueryRowContext(ctx, `SELECT bytes,content_hash FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, artifact["storage_key"]).Scan(&raw, &storedHash); err != nil {
		return nil, err
	}
	size, err := Num(artifact, "byte_size")
	if err != nil || size != int64(len(raw)) || storedHash != Digest(raw) || artifact["content_hash"] != Digest(raw) || !utf8.Valid(raw) {
		return nil, historyInvalid("transcript hash or size")
	}
	body, err := Decode(raw)
	if err != nil {
		return nil, err
	}
	through, err := Num(body, "through_sequence")
	if err != nil || through != transcript.through || body["schema"] != "researchos.session-transcript.v1" || body["origin"] != "SESSION_MESSAGE_JOURNAL" || body["project_id"] != project || body["session_id"] != sessionID || Hash(body["messages"]) != Hash(transcript.messages) || Hash(body["message_sequences"]) != Hash(transcript.sequences) {
		return nil, historyInvalid("transcript scope, watermark or journal changed")
	}
	return Ref(artifact, "Artifact"), nil
}
