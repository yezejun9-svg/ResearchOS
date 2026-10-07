//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	rt "researchos.local/research-os/adapters/runtime"
)

func clientQueueCancelFactsReady(tx *sql.Tx, binding Object) (bool, error) {
	rows, err := tx.Query(`SELECT kind,body,body_hash FROM client_control_receipts WHERE project=? AND generation=? AND kind IN ('command.abort_observed','command.idle')`, binding["project_id"], binding["queue_generation"])
	if err != nil {
		return false, err
	}
	defer rows.Close()
	abort, idle := false, false
	for rows.Next() {
		var kind, body, hash string
		if err = rows.Scan(&kind, &body, &hash); err != nil {
			return false, err
		}
		value, err := Decode([]byte(body))
		if err != nil || Digest([]byte(body)) != hash {
			return false, historyInvalid("cancel receipt hash")
		}
		same := true
		for key, expected := range binding {
			if Hash(value[key]) != Hash(expected) {
				same = false
				break
			}
		}
		if !same || value["sdk_idle"] != true || value["sdk_queue_empty"] != true {
			continue
		}
		if kind == "command.abort_observed" {
			abort = true
		}
		if kind == "command.idle" && value["cancelled"] == true {
			idle = true
		}
	}
	return abort && idle, rows.Err()
}

// The pipe write and the canonical commit are different facts. This receipt is
// written only by the ACK owner after the actual initialization write succeeds.
func (c *RuntimeCoordinator) modelInitializationDelivered(ctx context.Context, project, run string, bridge *rt.Bridge) error {
	if !bridge.ModelInitializationDelivered() {
		return Fail(409, "GATE_FAILED", "model initialization not delivered")
	}
	j := bridge.Read()
	binding, _, _, err := c.queueBinding(ctx, project, run, j)
	if err != nil {
		return err
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var accepted string
	if err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind='command.accepted'`, fmt.Sprintf("%s:%d", j.DispatchKey, j.QueueInitSequence), project, binding["queue_generation"]).Scan(&accepted); err != nil {
		return err
	}
	value, err := Decode([]byte(accepted))
	if err != nil || value["initialized"] != true {
		return Fail(409, "GATE_FAILED", "canonical initialization missing")
	}
	body := Merge(Merge(Object{}, binding), Object{"initialization_sequence": j.QueueInitSequence, "delivered": true})
	if err = appendClientReceipt(tx, project, Str(binding, "queue_generation"), "", "command.initialize.delivered", j.DispatchKey+":initialize-delivered", body, nil); err != nil {
		return err
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) modelStreamBinding(ctx context.Context, route RuntimeCoordinatorRoute, run, lease string, epoch int64, bridge *rt.Bridge, frame rt.BridgeFrame, intent Object) (Object, error) {
	if !bridge.ModelInitializationDelivered() {
		return nil, Fail(409, "GATE_FAILED", "model stream requires delivered initialization")
	}
	tx, current, d, err := c.dispatchGate(ctx, route, run, lease, epoch)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	var generation, session, state string
	var restored int
	err = tx.QueryRow(`SELECT generation,session_id,state,restore_fenced FROM client_queue_fences WHERE project=? AND task_id=? AND run_id=? AND runtime_epoch=? AND dispatch_key=? AND manifest_hash=?`, route.ProjectID, current["task_id"], run, epoch, d["dispatch_key"], d["manifest_hash"]).Scan(&generation, &session, &state, &restored)
	if err != nil {
		return nil, err
	}
	if restored != 0 || state != "OPEN" {
		return nil, Fail(409, "STATE_CONFLICT", "model queue generation fenced")
	}
	j := bridge.Read()
	var raw string
	if err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind='command.initialize.delivered'`, j.DispatchKey+":initialize-delivered", route.ProjectID, generation).Scan(&raw); err != nil {
		return nil, err
	}
	delivered, err := Decode([]byte(raw))
	if err != nil || delivered["delivered"] != true || Hash(delivered["initialization_sequence"]) != Hash(j.QueueInitSequence) || Hash(delivered["process_identity"]) != Hash(d["identity"]) {
		return nil, Fail(409, "GATE_FAILED", "model initialization binding")
	}
	b := Object{"project_id": route.ProjectID, "session_id": session, "task_id": current["task_id"], "run_id": run, "runtime_epoch": epoch, "queue_generation": generation, "dispatch_key": d["dispatch_key"], "manifest_hash": d["manifest_hash"], "process_identity": d["identity"], "effect_sequence": frame.Sequence, "effect_key": frame.Key, "request_hash": intent["request_hash"]}
	b["stream_id"] = rt.ModelStreamID(b)
	return b, nil
}

// Every credit is backed by one SQLite commit. Tokens do not consume the
// independent control revision, and text_end deliberately creates no public END.
func (c *RuntimeCoordinator) commitModelObservation(ctx context.Context, route RuntimeCoordinatorRoute, run, lease string, epoch int64, obs rt.ModelStreamObservation) ([]string, int64, error) {
	f := obs.Frame
	b := Object(f.Binding)
	tx, current, d, err := c.dispatchGate(ctx, route, run, lease, epoch)
	if err != nil {
		return nil, 0, err
	}
	defer tx.Rollback()
	if b["project_id"] != route.ProjectID || b["run_id"] != run || b["task_id"] != current["task_id"] || Hash(b["runtime_epoch"]) != Hash(epoch) || b["dispatch_key"] != d["dispatch_key"] || b["manifest_hash"] != d["manifest_hash"] || Hash(b["process_identity"]) != Hash(d["identity"]) || rt.ModelStreamID(b) != b["stream_id"] {
		return nil, 0, Fail(409, "GATE_FAILED", "foreign model observation")
	}
	var state, session string
	var restored int
	err = tx.QueryRow(`SELECT state,session_id,restore_fenced FROM client_queue_fences WHERE project=? AND generation=? AND run_id=? AND runtime_epoch=?`, route.ProjectID, b["queue_generation"], run, epoch).Scan(&state, &session, &restored)
	if err != nil {
		return nil, 0, err
	}
	if state != "OPEN" || restored != 0 || session != b["session_id"] {
		return nil, 0, Fail(409, "STATE_CONFLICT", "model observation generation fenced")
	}
	intent, err := latestEffect(tx, route.ProjectID, run, Str(b, "effect_key"))
	if err != nil {
		return nil, 0, err
	}
	if intent["request_hash"] != b["request_hash"] || Hash(intent["epoch"]) != Hash(epoch) || (intent["state"] != "STARTED" && intent["state"] != "CONFIRMED") {
		return nil, 0, Fail(409, "GATE_FAILED", "model observation effect binding")
	}
	id := fmt.Sprintf("%s:observation:%d", b["stream_id"], f.Sequence)
	var old string
	err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind=?`, id, route.ProjectID, b["queue_generation"], modelObservationKind).Scan(&old)
	if err == nil {
		v, e := Decode([]byte(old))
		if e != nil || Hash(v["observation"]) != Hash(f) {
			return nil, 0, Fail(409, "GATE_FAILED", "changed model observation replay")
		}
		ids := []string{}
		for _, x := range Arr(v, "journal_event_ids") {
			s, ok := x.(string)
			if !ok {
				return nil, 0, Fail(409, "GATE_FAILED", "invalid observation IDs")
			}
			ids = append(ids, s)
		}
		wm, e := Num(v, "session_watermark")
		return ids, wm, e
	}
	if err != sql.ErrNoRows {
		return nil, 0, err
	}
	var previous string
	if f.Sequence > 1 {
		if err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind=?`, fmt.Sprintf("%s:observation:%d", b["stream_id"], f.Sequence-1), route.ProjectID, b["queue_generation"], modelObservationKind).Scan(&previous); err != nil {
			return nil, 0, err
		}
	}
	previousDigest := Digest(nil)
	previousOffset := int64(0)
	if previous != "" {
		v, e := Decode([]byte(previous))
		if e != nil {
			return nil, 0, e
		}
		prior, ok := v["observation"].(map[string]any)
		if !ok {
			return nil, 0, historyInvalid("prior observation shape")
		}
		pp, _ := prior["payload"].(map[string]any)
		if Hash(prior["binding"]) != Hash(b) || pp["event"] == "message_end" || Hash(pp["message_ordinal"]) != Hash(f.Payload["message_ordinal"]) {
			return nil, 0, historyInvalid("observation binding or terminal")
		}
		previousDigest = Str(prior, "digest")
		previousOffset, e = Num(prior, "offset")
		if e != nil {
			return nil, 0, e
		}
	}
	if f.Digest != Hash(Object{"previous": previousDigest, "payload": f.Payload}) || f.Offset != previousOffset+int64(len(Str(f.Payload, "text"))) {
		return nil, 0, historyInvalid("observation durable chain")
	}
	ordinal, e := Num(f.Payload, "message_ordinal")
	if e != nil || Str(b, "effect_key") != fmt.Sprintf("%s:%s:%d:model:%d", current["task_id"], run, epoch, ordinal) {
		return nil, 0, historyInvalid("observation original model ordinal")
	}
	var build string
	var revision, writer, watermark int64
	err = tx.QueryRow(`SELECT core_build_id,revision,writer_epoch,event_watermark FROM client_sessions WHERE id=? AND project_id=? AND task_id=? AND run_id=? AND sealed_at IS NULL`, session, route.ProjectID, current["task_id"], run).Scan(&build, &revision, &writer, &watermark)
	if err != nil {
		return nil, 0, err
	}
	payload := Object(f.Payload)
	part, err := Num(payload, "text_part")
	if err != nil {
		return nil, 0, err
	}
	message := modelPublicMessageID(b)
	// Reconstruct the current prefix from the durable public journal, never an
	// in-memory SDK cursor. This also makes duplicate replay independent of restarts.
	var starts, ends, offset, parts int64
	err = tx.QueryRow(`SELECT coalesce(sum(json_extract(body,'$.payload.phase')='START'),0),coalesce(sum(json_extract(body,'$.payload.phase')='END'),0),coalesce(sum(CASE WHEN json_extract(body,'$.payload.phase')='DELTA' THEN length(CAST(json_extract(body,'$.payload.text') AS BLOB)) ELSE 0 END),0) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.payload.message_id')=? AND json_extract(body,'$.payload.part_index')=? AND json_extract(body,'$.kind')='MESSAGE'`, route.ProjectID, session, message, part).Scan(&starts, &ends, &offset)
	if err != nil {
		return nil, 0, err
	}
	var stagedEnds int
	if err = tx.QueryRow(`SELECT count(*) FROM client_control_receipts WHERE project=? AND generation=? AND kind=? AND json_extract(body,'$.observation.binding.stream_id')=? AND json_extract(body,'$.observation.payload.event')='text_end' AND json_extract(body,'$.observation.payload.text_part')=?`, route.ProjectID, b["queue_generation"], modelObservationKind, b["stream_id"], part).Scan(&stagedEnds); err != nil {
		return nil, 0, err
	}
	if payload["event"] != "message_end" && stagedEnds != 0 {
		return nil, 0, historyInvalid("observation after staged text end")
	}
	if payload["event"] == "message_end" {
		var started, ended int
		if err = tx.QueryRow(`SELECT coalesce(sum(json_extract(body,'$.observation.payload.event')='text_start'),0),coalesce(sum(json_extract(body,'$.observation.payload.event')='text_end'),0) FROM client_control_receipts WHERE project=? AND generation=? AND kind=? AND json_extract(body,'$.observation.binding.stream_id')=?`, route.ProjectID, b["queue_generation"], modelObservationKind, b["stream_id"]).Scan(&started, &ended); err != nil {
			return nil, 0, err
		}
		if started != ended {
			return nil, 0, historyInvalid("message end before text parts closed")
		}
	}
	ids := []string{}
	emit := func(phase, text string) error {
		watermark++
		kind := "MESSAGE"
		ev := &SessionEvent{EventID: strptr(ID()), SessionID: &session, Sequence: &watermark, CoreBuildID: &build, ProtocolVersion: strptr(ProtocolV2), RunID: &run, Kind: &kind, Payload: Bytes(Object{"message_id": message, "role": "ASSISTANT", "phase": phase, "part_index": part, "content_offset_utf8_bytes": offset, "text": text})}
		if e := appendRuntimeMessageEvent(ctx, tx, c.config.ClientSchema, route.ProjectID, ev, writer, revision); e != nil {
			return e
		}
		ids = append(ids, *ev.EventID)
		return c.service.sealSessionTranscript(ctx, tx, c.config.ClientSchema, route.ProjectID, session, Str(current, "executor_principal_id"))
	}
	switch payload["event"] {
	case "text_start":
		if starts != 0 || ends != 0 {
			return nil, 0, Fail(409, "GATE_FAILED", "duplicate model text start")
		}
		if err = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.payload.message_id')=? AND json_extract(body,'$.payload.phase')='START'`, route.ProjectID, session, message).Scan(&parts); err != nil {
			return nil, 0, err
		}
		if part != parts {
			return nil, 0, Fail(409, "GATE_FAILED", "non-dense model text part")
		}
		err = emit("START", "")
	case "text_delta":
		if starts != 1 || ends != 0 {
			return nil, 0, Fail(409, "GATE_FAILED", "model delta phase")
		}
		err = emit("DELTA", Str(payload, "text"))
	case "text_end":
		if starts != 1 || ends != 0 {
			return nil, 0, Fail(409, "GATE_FAILED", "model text end phase")
		}
	case "message_end":
		if intent["state"] != "CONFIRMED" {
			return nil, 0, Fail(409, "GATE_FAILED", "model terminal effect not confirmed")
		}
	default:
		return nil, 0, Fail(409, "GATE_FAILED", "model observation event")
	}
	if err != nil {
		return nil, 0, err
	}
	receipt := Object{"version": 1, "observation": f, "journal_event_ids": ids, "session_watermark": watermark}
	raw := Bytes(receipt)
	if _, err = tx.Exec(`INSERT INTO client_control_receipts(receipt_id,project,generation,command_id,kind,body,body_hash,previous_receipt_id,created_at) VALUES(?,?,?,NULL,?,?,?,NULL,?)`, id, route.ProjectID, b["queue_generation"], modelObservationKind, string(raw), Digest(raw), Now()); err != nil {
		return nil, 0, err
	}
	if err = tx.Commit(); err != nil {
		return nil, 0, err
	}
	return ids, watermark, nil
}

func (c *RuntimeCoordinator) projectModelStreamEnds(tx *sql.Tx, project, session string, run Object) error {
	streams, _, err := c.service.modelStreamFinalEvidence(context.Background(), tx, project, run)
	if err != nil {
		return err
	}
	var build string
	var wm, revision, writer int64
	if err = tx.QueryRow(`SELECT core_build_id,event_watermark,revision,writer_epoch FROM client_sessions WHERE project_id=? AND id=? AND sealed_at IS NULL`, project, session).Scan(&build, &wm, &revision, &writer); err != nil {
		return err
	}
	for _, stream := range streams {
		for index, part := range stream.parts {
			message := modelPublicMessageID(stream.binding)
			var count int
			if err = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.payload.message_id')=? AND json_extract(body,'$.payload.part_index')=? AND json_extract(body,'$.payload.phase')='END'`, project, session, message, index).Scan(&count); err != nil {
				return err
			}
			if count == 1 {
				continue
			}
			if count != 0 {
				return historyInvalid("duplicate model public END")
			}
			wm++
			ev := &SessionEvent{EventID: strptr(ID()), SessionID: &session, Sequence: &wm, CoreBuildID: &build, ProtocolVersion: strptr(ProtocolV2), RunID: strptr(Str(run, "id")), Kind: strptr("MESSAGE"), Payload: Bytes(Object{"message_id": message, "role": "ASSISTANT", "phase": "END", "part_index": index, "content_offset_utf8_bytes": len(part.text), "text": ""})}
			if err = appendRuntimeMessageEvent(context.Background(), tx, c.config.ClientSchema, project, ev, writer, revision); err != nil {
				return err
			}
			if err = c.service.sealSessionTranscript(context.Background(), tx, c.config.ClientSchema, project, session, Str(run, "executor_principal_id")); err != nil {
				return err
			}
		}
	}
	return nil
}
