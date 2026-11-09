package domain

// A Mu worker starts a fresh SDK session for each turn. This file copies the
// complete prior USER/ASSISTANT conversation from the durable session journal
// into one bounded, sealed input artifact before the next USER event is written.
// OBSERVED means the journal recorded these roles and bytes; it does not assert
// that any claim in the conversation is true.

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strings"
	"unicode/utf8"
)

const maxClientHistoryBytes = 32 << 10

type historyPart struct {
	started, ended bool
	text           string
	start, end     int64
}

type historyMessage struct {
	id, role, runID string
	start, end      int64
	parts           map[int64]*historyPart
}

func historyInvalid(reason string) error {
	return Fail(422, "GATE_FAILED", "session message history is incomplete or invalid: "+reason)
}

func historyMissing(err error) bool {
	var fault *Fault
	return errors.As(err, &fault) && fault.Code == "NOT_FOUND"
}

// clientHistoryArtifact is called inside session.send's existing SQLite
// transaction. A nil artifact means there were no prior USER/ASSISTANT messages.
func (s *ClientService) clientHistoryArtifact(ctx context.Context, tx *sql.Tx, p Principal, project, sessionID string, beforeSequence int64) (Object, error) {
	rows, err := tx.QueryContext(ctx, `SELECT body FROM outbox WHERE project=?
		AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='MESSAGE'
		AND CAST(json_extract(body,'$.sequence') AS INTEGER)<=?
		ORDER BY CAST(json_extract(body,'$.sequence') AS INTEGER) ASC`, project, sessionID, beforeSequence)
	if err != nil {
		return nil, err
	}
	byID := map[string]*historyMessage{}
	ordered := []*historyMessage{}
	var lastSequence int64
	var totalText int
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			break
		}
		if !utf8.ValidString(raw) {
			err = historyInvalid("event is not UTF-8")
			break
		}
		var ev *SessionEvent
		ev, err = DecodeEvent([]byte(raw))
		if err != nil || ev.SessionID == nil || *ev.SessionID != sessionID || ev.Kind == nil || *ev.Kind != "MESSAGE" || ev.Sequence == nil || *ev.Sequence <= lastSequence || *ev.Sequence > beforeSequence {
			err = historyInvalid("event envelope or sequence")
			break
		}
		if err = ValidateEventPayload(s.Doc, ev); err != nil {
			err = historyInvalid("event payload")
			break
		}
		lastSequence = *ev.Sequence
		var body struct {
			MessageID string `json:"message_id"`
			Role      string `json:"role"`
			Phase     string `json:"phase"`
			PartIndex int64  `json:"part_index"`
			Offset    int64  `json:"content_offset_utf8_bytes"`
			Text      string `json:"text"`
		}
		if err = json.Unmarshal(ev.Payload, &body); err != nil {
			err = historyInvalid("event payload JSON")
			break
		}
		if body.Role == "SYSTEM" {
			continue
		}
		if body.Role != "USER" && body.Role != "ASSISTANT" {
			err = historyInvalid("unexpected role")
			break
		}
		if body.MessageID == "" || body.PartIndex < 0 || body.Offset < 0 || !utf8.ValidString(body.Text) {
			err = historyInvalid("message fields")
			break
		}
		runID := ""
		if ev.RunID != nil {
			runID = *ev.RunID
		}
		if body.Role == "ASSISTANT" && runID == "" {
			err = historyInvalid("assistant has no source run")
			break
		}
		m := byID[body.MessageID]
		if m == nil {
			m = &historyMessage{id: body.MessageID, role: body.Role, runID: runID, parts: map[int64]*historyPart{}}
			byID[body.MessageID] = m
			ordered = append(ordered, m)
		} else if m.role != body.Role || m.runID != runID {
			err = historyInvalid("message role or source run changed")
			break
		}
		part := m.parts[body.PartIndex]
		if part == nil {
			part = &historyPart{}
			m.parts[body.PartIndex] = part
		}
		switch body.Phase {
		case "START":
			if part.started || body.Offset != 0 || body.Text != "" {
				err = historyInvalid("duplicate or malformed START")
			} else {
				part.started, part.start = true, *ev.Sequence
				if m.start == 0 {
					m.start = *ev.Sequence
				}
			}
		case "DELTA":
			if !part.started || part.ended || body.Offset != int64(len([]byte(part.text))) || body.Text == "" {
				err = historyInvalid("DELTA byte offset or phase")
			} else {
				part.text += body.Text
				totalText += len([]byte(body.Text))
				if totalText > maxClientHistoryBytes {
					err = Fail(413, "CONTENT_TOO_LARGE", "complete session history exceeds 32 KiB; rebuild context explicitly")
				}
			}
		case "END":
			if !part.started || part.ended || body.Offset != int64(len([]byte(part.text))) || body.Text != "" {
				err = historyInvalid("END byte offset or phase")
			} else {
				part.ended, part.end = true, *ev.Sequence
				m.end = *ev.Sequence
			}
		default:
			err = historyInvalid("unknown phase")
		}
		if err != nil {
			break
		}
	}
	if err == nil {
		err = rows.Err()
	}
	closeErr := rows.Close()
	if err != nil {
		return nil, err
	}
	if closeErr != nil {
		return nil, closeErr
	}
	if len(ordered) == 0 {
		return nil, nil
	}
	sdkOrder := map[string]int{}
	sdkGroup := map[string]string{}
	anchors := map[string]int64{}
	for _, m := range ordered {
		if m.role != "ASSISTANT" || !strings.HasPrefix(m.id, "model-stream-") {
			continue
		}
		if _, done := anchors[m.runID]; done {
			continue
		}
		run, e := load(tx, project, "Run", m.runID)
		if e != nil {
			return nil, e
		}
		_, positions, e := s.Domain.modelStreamFinalEvidence(ctx, tx, project, run)
		if e != nil {
			return nil, e
		}
		anchor := m.start
		for _, candidate := range ordered {
			if _, ok := positions[candidate.id]; ok && candidate.start < anchor {
				anchor = candidate.start
			}
		}
		anchors[m.runID] = anchor
		for id, pos := range positions {
			sdkOrder[id] = pos
			sdkGroup[id] = m.runID
		}
	}
	sort.SliceStable(ordered, func(i, j int) bool {
		a, b := ordered[i], ordered[j]
		ga, gb := sdkGroup[a.id], sdkGroup[b.id]
		if ga != "" && ga == gb {
			return sdkOrder[a.id] < sdkOrder[b.id]
		}
		ka, kb := a.start, b.start
		if ga != "" {
			ka = anchors[ga]
		}
		if gb != "" {
			kb = anchors[gb]
		}
		return ka < kb
	})
	messages := make([]any, 0, len(ordered))
	runRefs := Empty()
	seenRuns := map[string]bool{}
	allLive := true
	basis := "ALL_ASSISTANT_RUNS_LIVE"
	var previousEnd int64
	previousGroup := ""
	for _, m := range ordered {
		if (m.start <= previousEnd && (sdkGroup[m.id] == "" || sdkGroup[m.id] != previousGroup)) || m.end <= m.start || len(m.parts) == 0 {
			return nil, historyInvalid("overlapping or unfinished messages")
		}
		indices := make([]int64, 0, len(m.parts))
		for idx := range m.parts {
			indices = append(indices, idx)
		}
		sort.Slice(indices, func(i, j int) bool { return indices[i] < indices[j] })
		text := ""
		for i, idx := range indices {
			part := m.parts[idx]
			if idx != int64(i) || !part.started || !part.ended || part.end <= part.start {
				return nil, historyInvalid("part missing START or END")
			}
			text += part.text
		}
		if text == "" {
			return nil, historyInvalid("empty complete message")
		}
		previousEnd = m.end
		previousGroup = sdkGroup[m.id]
		messages = append(messages, Object{"message_id": m.id, "role": m.role, "text": text,
			"start_sequence": m.start, "end_sequence": m.end})
		if m.role != "ASSISTANT" || seenRuns[m.runID] {
			continue
		}
		seenRuns[m.runID] = true
		run, loadErr := load(tx, project, "Run", m.runID)
		if loadErr != nil {
			if historyMissing(loadErr) {
				return nil, historyInvalid("assistant source run missing")
			}
			return nil, loadErr
		}
		runRefs = append(runRefs, Ref(run, "Run"))
		if run["status"] != "SETTLED" || Str(run, "runtime_settled_at") == "" {
			allLive, basis = false, "ASSISTANT_RUN_NOT_SETTLED"
		}
		var projected int
		if queryErr := tx.QueryRowContext(ctx, `SELECT count(*) FROM outbox WHERE project=?
			AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=?
			AND json_extract(body,'$.kind')='RUN_STATE'
			AND json_extract(body,'$.payload.status')='SETTLED'
			AND CAST(json_extract(body,'$.sequence') AS INTEGER)<?`, project, sessionID, m.runID, m.start).Scan(&projected); queryErr != nil {
			return nil, queryErr
		}
		if sdkGroup[m.id] != "" {
			projected = 1
		}
		if projected == 0 {
			allLive, basis = false, "ASSISTANT_RUN_PROJECTION_UNKNOWN"
		}
		runtimeID := Str(run, "runtime_id")
		if runtimeID == "" {
			allLive, basis = false, "ASSISTANT_RUN_RUNTIME_UNKNOWN"
			continue
		}
		registration, loadErr := load(tx, project, "RuntimeRegistration", runtimeID)
		if historyMissing(loadErr) {
			allLive, basis = false, "ASSISTANT_RUN_RUNTIME_UNKNOWN"
			continue
		}
		if loadErr != nil {
			return nil, loadErr
		}
		if registration["measurement_mode"] != "LIVE" {
			allLive, basis = false, "FIXTURE_OR_UNKNOWN_ASSISTANT_RUN"
		}
	}
	if len(runRefs) == 0 {
		allLive, basis = false, "USER_JOURNAL_ONLY"
	}
	mode := "FIXTURE"
	if allLive {
		mode = "LIVE"
	}
	manifest := Object{"schema": "researchos.session-history.v1", "origin": "SESSION_MESSAGE_JOURNAL",
		"session_id": sessionID, "before_sequence": beforeSequence, "messages": messages,
		"source_run_refs": runRefs, "measurement_basis": basis,
		"observation_scope": "journal roles and bytes only; message claims are not verified facts"}
	raw := Bytes(manifest)
	if len(raw) > maxClientHistoryBytes {
		return nil, Fail(413, "CONTENT_TOO_LARGE", fmt.Sprintf("complete session history is %d bytes, above 32 KiB; rebuild context explicitly", len(raw)))
	}
	return s.Domain.serverArtifactMode(tx, project, p.ID, "REPORT", mode, raw, Empty())
}
