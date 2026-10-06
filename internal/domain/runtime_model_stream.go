package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strconv"
	"strings"
	"unicode/utf16"
	"unicode/utf8"
)

const modelStreamMaxRaw = 2 * 1024 * 1024
const modelStreamMaxSecretLanes = 4096

const modelObservationKind = "MODEL_STREAM_OBSERVATION_V1"

func modelPublicMessageID(binding Object) string {
	return "model-stream-" + strings.TrimPrefix(Str(binding, "stream_id"), "sha256:")
}

type modelStreamQuery interface {
	Query(string, ...any) (*sql.Rows, error)
	QueryRow(string, ...any) *sql.Row
}
type modelObservedPart struct {
	index int64
	text  string
	ended bool
}
type modelObservedStream struct {
	binding                              Object
	sequence, offset, watermark, ordinal int64
	digest                               string
	parts                                []*modelObservedPart
	ended                                bool
	eventIDs                             []string
}

func modelExactKeys(value Object, keys ...string) bool {
	if len(value) != len(keys) {
		return false
	}
	for _, key := range keys {
		if _, ok := value[key]; !ok {
			return false
		}
	}
	return true
}

// Reconstruct host observations without granting authority to any REPORT label.
// Both normal finalization and portable restore call this same readonly verifier.
func modelStreamEvidence(db modelStreamQuery, project, run string) ([]*modelObservedStream, error) {
	rows, err := db.Query(`SELECT receipt_id,project,generation,command_id,body,body_hash,previous_receipt_id FROM client_control_receipts WHERE kind=? AND (?='' OR project=?) AND (?='' OR json_extract(body,'$.observation.binding.run_id')=?) ORDER BY rowid`, modelObservationKind, project, project, run, run)
	if err != nil {
		return nil, err
	}
	entries := []Object{}
	for rows.Next() {
		var id, p, g, body, hash string
		var command, previous sql.NullString
		if err = rows.Scan(&id, &p, &g, &command, &body, &hash, &previous); err != nil {
			break
		}
		if command.Valid || previous.Valid || Digest([]byte(body)) != hash {
			err = historyInvalid("model receipt columns or hash")
			break
		}
		v, e := Decode([]byte(body))
		if e != nil {
			err = e
			break
		}
		entries = append(entries, Object{"id": id, "project": p, "generation": g, "value": v})
		if len(entries) > 262144*32 {
			err = historyInvalid("model receipt global bound")
			break
		}
	}
	if err == nil {
		err = rows.Err()
	}
	rows.Close()
	if err != nil {
		return nil, err
	}
	ordered := []*modelObservedStream{}
	byID := map[string]*modelObservedStream{}
	workers := map[string]int{}
	seenEvents := map[string]bool{}
	for _, entry := range entries {
		v := entry["value"].(Object)
		f, ok := v["observation"].(map[string]any)
		if !ok || !modelExactKeys(v, "version", "observation", "journal_event_ids", "session_watermark") || Hash(v["version"]) != Hash(1) || !modelExactKeys(f, "version", "type", "binding", "sequence", "offset", "digest", "payload") || f["version"] != "MODEL_SSE_V1" || f["type"] != "stream.observe" {
			return nil, historyInvalid("model receipt shape")
		}
		b, ok := f["binding"].(map[string]any)
		if !ok || !modelExactKeys(b, "project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity", "effect_sequence", "effect_key", "request_hash", "stream_id") {
			return nil, historyInvalid("model binding shape")
		}
		copy := Merge(Object{}, b)
		delete(copy, "stream_id")
		id := Str(b, "stream_id")
		if id != Hash(copy) || b["project_id"] != entry["project"] || b["queue_generation"] != entry["generation"] {
			return nil, historyInvalid("model stream identity")
		}
		p, ok := f["payload"].(map[string]any)
		if !ok || !modelExactKeys(p, "event", "message_ordinal", "text_part", "sdk_content_index", "text") {
			return nil, historyInvalid("model observation payload")
		}
		seq, e1 := Num(f, "sequence")
		off, e2 := Num(f, "offset")
		wm, e3 := Num(v, "session_watermark")
		ordinal, e4 := Num(p, "message_ordinal")
		part, e5 := Num(p, "text_part")
		index, e6 := Num(p, "sdk_content_index")
		text, validText := p["text"].(string)
		if e1 != nil || e2 != nil || e3 != nil || e4 != nil || e5 != nil || e6 != nil || seq < 1 || off < 0 || off > modelStreamMaxRaw || wm < 0 || ordinal < 1 || ordinal > 32 || part < 0 || part >= 64 || index < 0 || index >= 4096 || !validText || !utf8.ValidString(text) || len(text) > 8192 || utf8.RuneCountInString(text) > 16384 || entry["id"] != fmt.Sprintf("%s:observation:%d", id, seq) {
			return nil, historyInvalid("model observation bounds")
		}
		worker := Hash([]any{b["dispatch_key"], b["process_identity"]})
		workers[worker]++
		if workers[worker] > 262144 {
			return nil, historyInvalid("model worker record bound")
		}
		stream := byID[id]
		if stream == nil {
			if seq != 1 {
				return nil, historyInvalid("model first observation gap")
			}
			stream = &modelObservedStream{binding: b, digest: Digest(nil), ordinal: ordinal}
			byID[id] = stream
			ordered = append(ordered, stream)
			if err = modelStreamAuthority(db, b); err != nil {
				return nil, err
			}
		}
		if Hash(stream.binding) != Hash(b) || stream.ended || stream.ordinal != ordinal || seq != stream.sequence+1 || off != stream.offset+int64(len(text)) || wm < stream.watermark || f["digest"] != Hash(Object{"previous": stream.digest, "payload": p}) {
			return nil, historyInvalid("model observation chain or watermark")
		}
		ids, ok := v["journal_event_ids"].([]any)
		if !ok {
			return nil, historyInvalid("model event refs")
		}
		phase := ""
		offset := int64(0)
		switch p["event"] {
		case "text_start":
			if text != "" || part != int64(len(stream.parts)) {
				return nil, historyInvalid("model dense text start")
			}
			stream.parts = append(stream.parts, &modelObservedPart{index: index})
			phase = "START"
		case "text_delta", "text_end":
			if part >= int64(len(stream.parts)) || stream.parts[part].ended || stream.parts[part].index != index {
				return nil, historyInvalid("model text phase")
			}
			q := stream.parts[part]
			offset = int64(len(q.text))
			if p["event"] == "text_delta" {
				if text == "" {
					return nil, historyInvalid("empty model delta")
				}
				q.text += text
				phase = "DELTA"
			} else {
				if text != "" {
					return nil, historyInvalid("model end text")
				}
				q.ended = true
			}
		case "message_end":
			if text != "" || part != 0 || index != 0 {
				return nil, historyInvalid("model terminal shape")
			}
			for _, q := range stream.parts {
				if !q.ended {
					return nil, historyInvalid("model terminal has open part")
				}
			}
			stream.ended = true
		default:
			return nil, historyInvalid("model observation phase")
		}
		if phase == "" && len(ids) != 0 || phase != "" && len(ids) != 1 {
			return nil, historyInvalid("model public event count")
		}
		for _, rawID := range ids {
			eventID, ok := rawID.(string)
			if !ok || eventID == "" || seenEvents[eventID] {
				return nil, historyInvalid("model reused public event")
			}
			seenEvents[eventID] = true
			var raw string
			if err = db.QueryRow(`SELECT body FROM outbox WHERE project=? AND id=?`, b["project_id"], eventID).Scan(&raw); err != nil {
				return nil, err
			}
			ev, e := DecodeEvent([]byte(raw))
			if e != nil || ev.EventID == nil || *ev.EventID != eventID || ev.SessionID == nil || *ev.SessionID != b["session_id"] || ev.RunID == nil || *ev.RunID != b["run_id"] || ev.Sequence == nil || *ev.Sequence != wm || ev.Kind == nil || *ev.Kind != "MESSAGE" {
				return nil, historyInvalid("model public event identity")
			}
			expected := Object{"message_id": modelPublicMessageID(b), "role": "ASSISTANT", "phase": phase, "part_index": part, "content_offset_utf8_bytes": offset, "text": text}
			actual, e := Decode(ev.Payload)
			if e != nil || Hash(actual) != Hash(expected) {
				return nil, historyInvalid("model public prefix differs from observation")
			}
			stream.eventIDs = append(stream.eventIDs, eventID)
		}
		stream.sequence, stream.offset, stream.watermark, stream.digest = seq, off, wm, Str(f, "digest")
	}
	return ordered, nil
}

func modelStreamAuthority(db modelStreamQuery, b Object) error {
	var session, task, run, key, manifest, identity string
	var epoch int64
	err := db.QueryRow(`SELECT f.session_id,f.task_id,f.run_id,f.runtime_epoch,d.dispatch_key,d.manifest_hash,d.identity FROM client_queue_fences f JOIN runtime_dispatches d ON d.project=f.project AND d.run=f.run_id AND d.epoch=f.runtime_epoch WHERE f.project=? AND f.generation=?`, b["project_id"], b["queue_generation"]).Scan(&session, &task, &run, &epoch, &key, &manifest, &identity)
	if err != nil {
		return err
	}
	native, e := Decode([]byte(identity))
	if e != nil || session != b["session_id"] || task != b["task_id"] || run != b["run_id"] || Hash(epoch) != Hash(b["runtime_epoch"]) || key != b["dispatch_key"] || manifest != b["manifest_hash"] || Hash(native) != Hash(b["process_identity"]) {
		return historyInvalid("model generation or process binding")
	}
	var delivered, accepted string
	if err = db.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind='command.initialize.delivered'`, key+":initialize-delivered", b["project_id"], b["queue_generation"]).Scan(&delivered); err != nil {
		return err
	}
	value, e := Decode([]byte(delivered))
	if e != nil || value["delivered"] != true {
		return historyInvalid("model delivery receipt")
	}
	seq, e := Num(value, "initialization_sequence")
	effectSeq, ee := Num(b, "effect_sequence")
	if e != nil || ee != nil || seq < 1 || effectSeq <= seq {
		return historyInvalid("model initialization sequence")
	}
	for _, k := range []string{"project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity"} {
		if Hash(value[k]) != Hash(b[k]) {
			return historyInvalid("model delivered initialization binding")
		}
	}
	if err = db.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND kind='command.accepted'`, fmt.Sprintf("%s:%d", key, seq), b["project_id"], b["queue_generation"]).Scan(&accepted); err != nil {
		return err
	}
	a, e := Decode([]byte(accepted))
	if e != nil || a["initialized"] != true {
		return historyInvalid("model canonical initialization")
	}
	for _, k := range []string{"project_id", "session_id", "task_id", "run_id", "runtime_epoch", "queue_generation", "dispatch_key", "manifest_hash", "process_identity"} {
		if Hash(a[k]) != Hash(b[k]) {
			return historyInvalid("model accepted initialization binding")
		}
	}
	var effect string
	if err = db.QueryRow(`SELECT body FROM resource_effects WHERE project=? AND run=? AND effect_key=? ORDER BY sequence DESC LIMIT 1`, b["project_id"], b["run_id"], b["effect_key"]).Scan(&effect); err != nil {
		return err
	}
	intent, e := Decode([]byte(effect))
	if e != nil || intent["request_hash"] != b["request_hash"] || Hash(intent["epoch"]) != Hash(b["runtime_epoch"]) {
		return historyInvalid("model effect binding")
	}
	request, ok := intent["payload"].(map[string]any)
	if !ok || request["capability"] != "MODEL" {
		return historyInvalid("model effect capability")
	}
	return nil
}

func validateModelStreamBackup(db *sql.DB) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err = validateProviderInventory(tx, "", ""); err != nil {
		return err
	}
	streams, err := modelStreamEvidence(tx, "", "")
	if err != nil {
		return err
	}
	verified := map[string]bool{}
	for _, stream := range streams {
		if len(stream.parts) == 0 {
			continue
		}
		project, session := Str(stream.binding, "project_id"), Str(stream.binding, "session_id")
		var artifactID string
		if err = tx.QueryRow(`SELECT transcript_artifact_id FROM client_sessions WHERE project_id=? AND id=?`, project, session).Scan(&artifactID); err != nil {
			return err
		}
		a, err := load(tx, project, "Artifact", artifactID)
		if err != nil {
			return err
		}
		if a["kind"] != "REPORT" || a["evidence_kind"] != "OBSERVED" || a["run_id"] != nil || Str(a, "sealed_at") == "" {
			return historyInvalid("model transcript seal")
		}
		var raw []byte
		var hash string
		if err = tx.QueryRow(`SELECT bytes,content_hash FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, a["storage_key"]).Scan(&raw, &hash); err != nil {
			return err
		}
		if hash != Digest(raw) || a["content_hash"] != hash || Hash(a["byte_size"]) != Hash(len(raw)) {
			return historyInvalid("model transcript bytes")
		}
		body, err := Decode(raw)
		if err != nil {
			return err
		}
		if body["schema"] != "researchos.session-transcript.v1" || body["session_id"] != session || body["project_id"] != project {
			return historyInvalid("model transcript identity")
		}
		found := false
		publicComplete := false
		for _, value := range Arr(body, "messages") {
			m, ok := value.(map[string]any)
			if !ok {
				return historyInvalid("model transcript message")
			}
			if m["message_id"] != modelPublicMessageID(stream.binding) {
				continue
			}
			if found || m["role"] != "ASSISTANT" || len(Arr(m, "parts")) != len(stream.parts) {
				return historyInvalid("model transcript membership")
			}
			found = true
			complete := true
			for index, value := range Arr(m, "parts") {
				part, ok := value.(map[string]any)
				if !ok || part["text"] != stream.parts[index].text || Hash(part["part_index"]) != Hash(index) {
					return historyInvalid("model transcript prefix")
				}
				var ends int
				if err = tx.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.payload.message_id')=? AND json_extract(body,'$.payload.part_index')=? AND json_extract(body,'$.payload.phase')='END' AND json_extract(body,'$.payload.content_offset_utf8_bytes')=? AND json_extract(body,'$.payload.text')=''`, project, session, stream.binding["run_id"], m["message_id"], index, len(stream.parts[index].text)).Scan(&ends); err != nil {
					return err
				}
				if ends > 1 || part["complete"] != (ends == 1) {
					return historyInvalid("model transcript END witness")
				}
				complete = complete && ends == 1
				publicComplete = publicComplete || ends == 1
			}
			if m["complete"] != complete {
				return historyInvalid("model transcript completeness")
			}
			if !complete && (body["complete"] != false || a["measurement_mode"] == "LIVE") {
				return historyInvalid("partial model transcript promoted")
			}
		}
		if !found {
			return historyInvalid("model transcript omitted prefix")
		}
		runID := Str(stream.binding, "run_id")
		if publicComplete && !verified[runID] {
			run, err := load(tx, project, "Run", runID)
			if err != nil {
				return err
			}
			if _, _, err = (&Service{}).modelStreamFinalEvidence(context.Background(), tx, project, run); err != nil {
				return err
			}
			verified[runID] = true
		}
	}
	return nil
}

func (s *Service) modelStreamAcceptanceSnapshot(tx *sql.Tx, project string, run Object) (Object, error) {
	installed, err := clientQueueInstalled(tx)
	if err != nil || !installed {
		return nil, err
	}
	streams, order, err := s.modelStreamFinalEvidence(context.Background(), tx, project, run)
	if err != nil || len(streams) == 0 {
		return nil, err
	}
	bindings := Empty()
	for _, stream := range streams {
		bindings = append(bindings, stream.binding)
	}
	rows, err := tx.Query(`SELECT q.command_id,q.message_id,q.queue_sequence,q.content,q.content_hash,q.state,r.body,r.body_hash FROM client_command_queue q JOIN client_control_receipts r ON r.receipt_id=q.last_receipt_id AND r.project=q.project AND r.generation=q.generation AND r.command_id=q.command_id WHERE q.project=? AND q.generation=? AND q.state='CONSUMED' AND r.kind='command.consumed' ORDER BY q.queue_sequence`, project, streams[0].binding["queue_generation"])
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	commands := Empty()
	for rows.Next() {
		var id, message, content, hash, state, body, bodyHash string
		var seq int64
		if err = rows.Scan(&id, &message, &seq, &content, &hash, &state, &body, &bodyHash); err != nil {
			return nil, err
		}
		if Digest([]byte(body)) != bodyHash || Digest([]byte(content)) != hash {
			return nil, historyInvalid("canonical command receipt hash")
		}
		receipt, e := Decode([]byte(body))
		if e != nil {
			return nil, e
		}
		commands = append(commands, Object{"command_id": id, "message_id": message, "queue_sequence": seq, "content": content, "content_hash": hash, "state": state, "consumption": receipt, "consumption_hash": bodyHash, "sdk_position": order[message]})
	}
	if err = rows.Err(); err != nil {
		return nil, err
	}
	return Object{"bindings": bindings, "commands": commands}, nil
}

// This proof starts at canonical dispatch/effect rows. A publicly sealed REPORT
// with the same vocabulary cannot create stream authority or public END events.
func (s *Service) modelStreamFinalEvidence(ctx context.Context, tx *sql.Tx, project string, run Object) ([]*modelObservedStream, map[string]int, error) {
	if _, err := validateProviderInventory(tx, project, Str(run, "id")); err != nil {
		return nil, nil, err
	}
	streams, err := modelStreamEvidence(tx, project, Str(run, "id"))
	if err != nil || len(streams) == 0 {
		return streams, nil, err
	}
	if run["status"] != "SETTLED" || Str(run, "runtime_settled_at") == "" || run["children_stopped"] != true || run["queue_empty"] != true {
		return nil, nil, historyInvalid("model run not settled")
	}
	observation, err := runtimeObservation(tx, project, run)
	if err != nil {
		return nil, nil, err
	}
	dispatch, err := nativeDispatchProof(tx, project, run, observation)
	if err != nil {
		return nil, nil, err
	}
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	profile, _ := admission["profile"].(map[string]any)
	config, _ := profile["model_config"].(map[string]any)
	if err = validateRuntimeModelConfig(profile); err != nil {
		return nil, nil, err
	}
	outputs := Arr(observation, "artifacts")
	if len(outputs) != 1 || len(Arr(run, "result_artifact_ids")) != 1 {
		return nil, nil, historyInvalid("model result output membership")
	}
	aID, ok := Arr(run, "result_artifact_ids")[0].(string)
	if !ok {
		return nil, nil, historyInvalid("model result reference")
	}
	a, err := load(tx, project, "Artifact", aID)
	if err != nil {
		return nil, nil, err
	}
	output, ok := outputs[0].(map[string]any)
	if !ok || a["run_id"] != run["id"] || a["produced_by"] != run["executor_principal_id"] || Str(a, "sealed_at") == "" || a["content_hash"] != output["content_hash"] || Hash(a["byte_size"]) != Hash(output["byte_size"]) {
		return nil, nil, historyInvalid("model output differs from native artifact")
	}
	var raw []byte
	var stored string
	if err = tx.QueryRowContext(ctx, `SELECT bytes,content_hash FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, a["storage_key"]).Scan(&raw, &stored); err != nil {
		return nil, nil, err
	}
	if Digest(raw) != a["content_hash"] || stored != a["content_hash"] {
		return nil, nil, historyInvalid("model sealed output changed")
	}
	result, err := Decode(raw)
	if err != nil || result["task_id"] != run["task_id"] || result["run_id"] != run["id"] || Hash(result["epoch"]) != Hash(run["lease_epoch"]) || result["model_ref"] != config["ref"] || result["model"] != config["model"] || result["actual_cost"] != nil || result["sdk_cost_is_placeholder"] != true {
		return nil, nil, historyInvalid("model SDK result identity")
	}
	order := map[string]int{}
	ordinal := 0
	used := map[string]bool{}
	messages := Arr(result, "messages")
	// Prior history is an immutable input to this run and precedes its own prompt.
	current := false
	for pos, item := range messages {
		m, ok := item.(map[string]any)
		if !ok {
			return nil, nil, historyInvalid("model SDK message")
		}
		if m["role"] == "user" {
			text, valid := muText(m["content"])
			if valid {
				p, e := Decode([]byte(text))
				if e == nil && p["run_id"] == run["id"] && p["task_id"] == run["task_id"] {
					if current {
						return nil, nil, historyInvalid("duplicate model prompt")
					}
					current = true
				}
			}
			continue
		}
		if !current {
			continue
		}
		if m["role"] == "custom" {
			if m["customType"] != "researchos.command.v1" {
				return nil, nil, historyInvalid("unbound SDK custom message")
			}
			details, ok := m["details"].(map[string]any)
			if !ok || !modelExactKeys(details, "command_id", "queue_generation", "queue_sequence", "content_hash") {
				return nil, nil, historyInvalid("model command details")
			}
			command := Str(details, "command_id")
			if used[command] {
				return nil, nil, historyInvalid("duplicate SDK command")
			}
			used[command] = true
			var id, content, hash, state, receiptID string
			var sequence int64
			err = tx.QueryRow(`SELECT message_id,content,content_hash,state,queue_sequence,last_receipt_id FROM client_command_queue WHERE project=? AND generation=? AND command_id=?`, project, details["queue_generation"], command).Scan(&id, &content, &hash, &state, &sequence, &receiptID)
			if err != nil {
				return nil, nil, err
			}
			if state != "CONSUMED" || hash != Digest([]byte(content)) || details["content_hash"] != hash || Hash(sequence) != Hash(details["queue_sequence"]) {
				return nil, nil, historyInvalid("SDK command not canonically consumed")
			}
			var rec string
			if err = tx.QueryRow(`SELECT body FROM client_control_receipts WHERE receipt_id=? AND project=? AND generation=? AND command_id=? AND kind='command.consumed'`, receiptID, project, details["queue_generation"], command).Scan(&rec); err != nil {
				return nil, nil, err
			}
			receipt, e := Decode([]byte(rec))
			if e != nil || receipt["message_id"] != id || receipt["content_hash"] != hash || receipt["run_id"] != run["id"] {
				return nil, nil, historyInvalid("SDK consumption receipt binding")
			}
			parsed, e := Decode([]byte(content))
			if e != nil {
				return nil, nil, e
			}
			parts := []any{Object{"type": "text", "text": parsed["text"]}}
			for _, v := range Arr(parsed, "attachments") {
				attachment, ok := v.(map[string]any)
				if !ok {
					return nil, nil, historyInvalid("command attachment")
				}
				parts = append(parts, Object{"type": "text", "text": attachment["text"]})
			}
			if Hash(parts) != Hash(m["content"]) {
				return nil, nil, historyInvalid("SDK consumed command bytes")
			}
			order[id] = pos
			continue
		}
		if m["role"] != "assistant" {
			continue
		}
		ordinal++
		if ordinal > len(streams) {
			return nil, nil, historyInvalid("SDK assistant lacks model observation")
		}
		stream := streams[ordinal-1]
		if stream.ordinal != int64(ordinal) || !stream.ended {
			return nil, nil, historyInvalid("model observations incomplete")
		}
		intent, e := latestEffect(tx, project, Str(run, "id"), Str(stream.binding, "effect_key"))
		if e != nil {
			return nil, nil, e
		}
		receipt, _ := intent["receipt"].(map[string]any)
		response, _ := receipt["payload"].(map[string]any)
		responseRaw := Str(response, "body")
		if intent["state"] != "CONFIRMED" || receipt["state"] != "CONFIRMED" || receipt["model_transport"] != true || receipt["actual_cost"] != nil || receipt["run_id"] != run["id"] || Hash(receipt["epoch"]) != Hash(run["lease_epoch"]) || receipt["key"] != stream.binding["effect_key"] || receipt["receipt_id"] != Digest([]byte(responseRaw)) || response["content_type"] != "text/event-stream" || Hash(response["status"]) != Hash(200) || len(responseRaw) > modelStreamMaxRaw || !completeRuntimeModelSSE([]byte(responseRaw)) {
			return nil, nil, historyInvalid("model confirmed SSE receipt")
		}
		expected, e := providerResponse(config, responseRaw)
		actual, ae := muSDKAssistant(m)
		if e != nil || ae != nil || Hash(actual) != Hash(expected) || m["model"] != config["model"] || m["provider"] != config["provider"] || m["api"] != config["api"] || m["errorMessage"] != nil {
			return nil, nil, historyInvalid("SDK differs from original confirmed SSE")
		}
		if policy, _ := providerPolicy(config); policy {
			request, _ := intent["payload"].(map[string]any)
			payload, _ := request["payload"].(map[string]any)
			body, _ := payload["body"].(map[string]any)
			if e = verifyProviderReasoning(responseRaw, m); e != nil {
				return nil, nil, e
			}
			if e = verifyProviderWireHistory(Arr(body, "messages"), messages[:pos], providerOriginalCWD(dispatch)); e != nil {
				return nil, nil, e
			}
		}
		content := Arr(m, "content")
		text := ""
		for _, part := range stream.parts {
			if !part.ended || part.index >= int64(len(content)) {
				return nil, nil, historyInvalid("model part incomplete")
			}
			sdkPart, ok := content[part.index].(map[string]any)
			if !ok || sdkPart["type"] != "text" || sdkPart["text"] != part.text {
				return nil, nil, historyInvalid("model prefix differs from SDK part")
			}
			text += part.text
		}
		if text != expected.Text {
			return nil, nil, historyInvalid("model prefix differs from original SSE")
		}
		order[modelPublicMessageID(stream.binding)] = pos
	}
	if !current || ordinal != len(streams) {
		return nil, nil, historyInvalid("model prompt or assistant omitted")
	}
	// Admission is not consumption. Every queue member for this generation must
	// be accounted for by an actual SDK custom message before executable history.
	var count int
	if err = tx.QueryRow(`SELECT count(*) FROM client_command_queue WHERE project=? AND generation=? AND state='CONSUMED'`, project, streams[0].binding["queue_generation"]).Scan(&count); err != nil {
		return nil, nil, err
	}
	if count != len(used) {
		return nil, nil, historyInvalid("SDK omitted consumed command")
	}
	return streams, order, nil
}

// modelSSEQuarantine keeps original bytes while validating complete SSE events.
// No caller may forward bytes other than the returned safe prefix. Suspect
// decoded suffixes hold whole events, including JSON-escaped credentials.
type modelSSEQuarantine struct {
	raw                                   []byte
	scan, lineStart, eventStart, released int
	secrets                               []string
	tails                                 map[string]string
	done, data, failed                    bool
	detailKind                            string
	tools                                 map[string]*modelSSEToolStrings
	toolCount                             int
	jsonPending                           map[string]bool
}

func newModelSSEQuarantine(secrets ...string) (*modelSSEQuarantine, error) {
	q := &modelSSEQuarantine{tails: map[string]string{}, tools: map[string]*modelSSEToolStrings{}, jsonPending: map[string]bool{}}
	for _, s := range secrets {
		if s == "" {
			continue
		}
		if len(s) > modelStreamMaxRaw || !utf8.ValidString(s) {
			return nil, errors.New("invalid credential quarantine bound")
		}
		q.secrets = append(q.secrets, s)
	}
	return q, nil
}

func (q *modelSSEQuarantine) reject() ([]byte, error) {
	q.failed = true
	// Do not include provider bytes or secret material in diagnostics/evidence.
	return nil, errors.New("model SSE quarantine rejected response")
}

func (q *modelSSEQuarantine) inspect(lane, value string) bool {
	if len(q.secrets) == 0 {
		return true
	}
	joined := q.tails[lane] + value
	for _, secret := range q.secrets {
		if strings.Contains(joined, secret) {
			return false
		}
	}
	keep := ""
	for _, secret := range q.secrets {
		for n := min(len(secret)-1, len(joined)); n > len(keep); n-- {
			if strings.HasSuffix(joined, secret[:n]) {
				keep = secret[:n]
				break
			}
		}
	}
	if keep == "" {
		delete(q.tails, lane)
	} else {
		if _, exists := q.tails[lane]; !exists && len(q.tails) >= modelStreamMaxSecretLanes {
			return false
		}
		q.tails[lane] = keep
	}
	return true
}

func (q *modelSSEQuarantine) inspectJSON(value any, path string, depth int) bool {
	if depth > 64 {
		return false
	}
	switch v := value.(type) {
	case string:
		for _, secret := range q.secrets {
			if strings.Contains(v, secret) {
				return false
			}
		}
		// Only fields concatenated by the provider parser carry suffix state.
		// Stable metadata such as response ID must not hold every later event.
		for _, suffix := range []string{"/content", "/arguments", "/input"} {
			if strings.HasSuffix(path, suffix) {
				return q.inspect(path, v)
			}
		}
		return true
	case []any:
		for i, item := range v {
			if !q.inspectJSON(item, path+"/"+strconv.Itoa(i), depth+1) {
				return false
			}
		}
	case map[string]any:
		keys := make([]string, 0, len(v))
		for k := range v {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			for _, secret := range q.secrets {
				if strings.Contains(k, secret) {
					return false
				}
			}
			if !q.inspectJSON(v[k], path+"/"+strings.ReplaceAll(strings.ReplaceAll(k, "~", "~0"), "/", "~1"), depth+1) {
				return false
			}
			// Also join content lanes independently of array order/index changes.
			if k == "content" || k == "arguments" || k == "input" {
				if s, ok := v[k].(string); ok && !q.inspect("semantic:"+k, s) {
					return false
				}
			}
		}
	}
	return true
}

// Tool arguments have a second JSON-string decoding layer in parseStreamingJson.
// Decode string tokens incrementally, holding only possible secret suffixes and
// incomplete escape code units. No whole argument or stream buffer is added.
type modelSSEToolStrings struct {
	lane    string
	indexed bool
	quoted  bool
	escape  string
	high    uint16
}

func (q *modelSSEQuarantine) inspectToolJSON(tool *modelSSEToolStrings, value string) bool {
	emit := func(r rune) bool { return q.inspect(tool.lane, string(r)) }
	for i := 0; i < len(value); i++ {
		c := value[i]
		if !tool.quoted {
			if c == '"' {
				tool.quoted = true
				delete(q.tails, tool.lane)
			}
			continue
		}
		if tool.escape != "" {
			tool.escape += string(c)
			if len(tool.escape) == 2 && c != 'u' {
				if tool.high != 0 {
					if !emit(utf8.RuneError) {
						return false
					}
					tool.high = 0
				}
				decoded := ""
				switch c {
				case '"', '\\', '/':
					decoded = string(c)
				case 'b':
					decoded = "\b"
				case 'f':
					decoded = "\f"
				case 'n':
					decoded = "\n"
				case 'r':
					decoded = "\r"
				case 't':
					decoded = "\t"
				default:
					return false
				}
				if !q.inspect(tool.lane, decoded) {
					return false
				}
				tool.escape = ""
			} else if len(tool.escape) == 6 {
				n, err := strconv.ParseUint(tool.escape[2:], 16, 16)
				if err != nil {
					return false
				}
				u := uint16(n)
				tool.escape = ""
				if tool.high != 0 {
					if u >= 0xdc00 && u <= 0xdfff {
						if !emit(utf16.DecodeRune(rune(tool.high), rune(u))) {
							return false
						}
						tool.high = 0
						continue
					}
					if !emit(utf8.RuneError) {
						return false
					}
					tool.high = 0
				}
				if u >= 0xd800 && u <= 0xdbff {
					tool.high = u
				} else if u >= 0xdc00 && u <= 0xdfff {
					if !emit(utf8.RuneError) {
						return false
					}
				} else if !emit(rune(u)) {
					return false
				}
			}
			continue
		}
		if c == '\\' {
			tool.escape = "\\"
			continue
		}
		if tool.high != 0 {
			if !emit(utf8.RuneError) {
				return false
			}
			tool.high = 0
		}
		if c == '"' {
			tool.quoted = false
			delete(q.tails, tool.lane)
			continue
		}
		if c < 0x20 || !q.inspect(tool.lane, string([]byte{c})) {
			return false
		}
	}
	if tool.escape != "" || tool.high != 0 {
		q.jsonPending[tool.lane] = true
	} else {
		delete(q.jsonPending, tool.lane)
	}
	return true
}

func (q *modelSSEQuarantine) inspectSDKTools(delta map[string]any) bool {
	calls, _ := delta["tool_calls"].([]any)
	for _, raw := range calls {
		call, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		index, indexed := call["index"].(float64)
		// SDK Map keys use SameValueZero: JSON numbers are binary64 and both
		// signed zeros select the same accumulated tool-argument stream.
		if index == 0 {
			index = 0
		}
		indexKey := "index:" + strconv.FormatFloat(index, 'g', -1, 64)
		id, _ := call["id"].(string)
		var tool *modelSSEToolStrings
		if indexed {
			tool = q.tools[indexKey]
		}
		if tool == nil && id != "" {
			tool = q.tools["id:"+id]
		}
		if tool == nil {
			if q.toolCount >= modelStreamMaxSecretLanes {
				return false
			}
			tool = &modelSSEToolStrings{lane: "sdk:tool-json:" + strconv.Itoa(q.toolCount), indexed: indexed}
			q.toolCount++
			if indexed {
				q.tools[indexKey] = tool
			}
		} else if indexed && !tool.indexed {
			q.tools[indexKey] = tool
			tool.indexed = true
		}
		if id != "" {
			q.tools["id:"+id] = tool
		}
		if len(q.tools) > modelStreamMaxSecretLanes {
			return false
		}
		function, _ := call["function"].(map[string]any)
		if arguments, ok := function["arguments"].(string); ok && arguments != "" {
			if !q.inspectToolJSON(tool, arguments) {
				return false
			}
		}
	}
	return true
}

// Match the fixed openai-completions SDK, which selects the first choice and
// appends the first non-empty alias to one thinking block. Wire field names and
// reasoning detail indices are not independent semantic string identities.
func (q *modelSSEQuarantine) inspectSDKStrings(object map[string]any) bool {
	choices, _ := object["choices"].([]any)
	if len(choices) == 0 {
		return true
	}
	choice, _ := choices[0].(map[string]any)
	delta, _ := choice["delta"].(map[string]any)
	if !q.inspectSDKTools(delta) {
		return false
	}
	for _, key := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
		if text, ok := delta[key].(string); ok && text != "" {
			if !q.inspect("sdk:thinking", text) {
				return false
			}
			break
		}
	}
	details, _ := delta["reasoning_details"].([]any)
	for _, raw := range details {
		detail, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		valid := true
		for _, key := range []string{"id", "format", "index"} {
			value, exists := detail[key]
			if !exists || key == "id" && value == nil {
				continue
			}
			if key == "index" {
				_, ok = value.(float64)
			} else {
				_, ok = value.(string)
			}
			valid = valid && ok
		}
		if !valid {
			continue
		}
		kind, _ := detail["type"].(string)
		field := ""
		switch kind {
		case "reasoning.text":
			field = "text"
			if signature, exists := detail["signature"]; exists && signature != nil {
				if _, ok := signature.(string); !ok {
					continue
				}
			}
		case "reasoning.summary":
			field = "summary"
		case "reasoning.encrypted":
			field = "data"
		default:
			continue
		}
		text, ok := detail[field].(string)
		if !ok {
			continue
		}
		// Invalid details are ignored by the SDK. Valid encrypted or differing
		// types terminate the previous merge, including across event boundaries.
		if kind != q.detailKind || kind == "reasoning.encrypted" {
			delete(q.tails, "sdk:reasoning-detail")
		}
		q.detailKind = kind
		if kind != "reasoning.encrypted" && !q.inspect("sdk:reasoning-detail", text) {
			return false
		}
	}
	return true
}

func (q *modelSSEQuarantine) event(raw []byte) bool {
	if !utf8.Valid(raw) {
		return false
	}
	for _, secret := range q.secrets {
		if bytes.Contains(raw, []byte(secret)) {
			return false
		}
	}
	data := []string{}
	for _, line := range strings.Split(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\n") {
		if strings.HasPrefix(line, "data:") {
			data = append(data, strings.TrimPrefix(strings.TrimPrefix(line, "data:"), " "))
		}
	}
	if len(data) == 0 {
		return true
	}
	if q.done {
		return false
	}
	payload := strings.Join(data, "\n")
	if payload == "[DONE]" {
		q.done = true
		return true
	}
	var object map[string]any
	if json.Unmarshal([]byte(payload), &object) != nil || object == nil || !q.inspectJSON(object, "", 0) || !q.inspectSDKStrings(object) {
		return false
	}
	q.data = true
	return true
}

func (q *modelSSEQuarantine) Feed(chunk []byte) ([]byte, error) {
	if q.failed || len(q.raw)+len(chunk) > modelStreamMaxRaw {
		return q.reject()
	}
	q.raw = append(q.raw, chunk...)
	through := q.released
	for q.scan < len(q.raw) {
		i := q.scan
		q.scan++
		if q.raw[i] != '\n' {
			continue
		}
		empty := i == q.lineStart || (i == q.lineStart+1 && q.raw[q.lineStart] == '\r')
		q.lineStart = i + 1
		if !empty {
			continue
		}
		if !q.event(q.raw[q.eventStart : i+1]) {
			return q.reject()
		}
		q.eventStart = i + 1
		if !q.done && len(q.tails) == 0 && len(q.jsonPending) == 0 {
			through = i + 1
		}
	}
	// A returned prefix always consists of complete valid events. If a later
	// event in the same read rejects, none of this read is forwarded.
	ready := append([]byte(nil), q.raw[q.released:through]...)
	q.released = through
	return ready, nil
}

// Finish validates original EOF. The caller must durably confirm the original
// resource effect before forwarding this withheld terminal suffix to the SDK.
func (q *modelSSEQuarantine) Finish() ([]byte, []byte, error) {
	if q.failed || !q.done || !q.data || len(q.jsonPending) != 0 || q.eventStart != len(q.raw) || !completeRuntimeModelSSE(q.raw) {
		_, err := q.reject()
		return nil, nil, err
	}
	for _, secret := range q.secrets {
		if bytes.Contains(q.raw, []byte(secret)) {
			_, err := q.reject()
			return nil, nil, err
		}
	}
	return append([]byte(nil), q.raw...), append([]byte(nil), q.raw[q.released:]...), nil
}
