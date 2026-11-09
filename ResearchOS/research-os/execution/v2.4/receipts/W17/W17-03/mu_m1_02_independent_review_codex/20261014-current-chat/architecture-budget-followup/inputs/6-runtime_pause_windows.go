//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"golang.org/x/sys/windows"
	"io"
	"os"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"strconv"
	"strings"
	"time"
)

func (c *RuntimeCoordinator) recordPauseCapability(ctx context.Context, project, run string, bridge *rt.Bridge) error {
	j := bridge.Read()
	if j.PauseProtocol != rt.PauseProtocol {
		return nil
	}
	if j.QueueInitSequence == 0 || j.Acknowledged < j.QueueInitSequence {
		return Fail(409, "GATE_FAILED", "pause capability before initialization ACK")
	}
	binding, _, _, err := c.queueBinding(ctx, project, run, j)
	if err != nil {
		return err
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	body := Merge(binding, Object{"pause_protocol": rt.PauseProtocol, "original_input_hash": j.InputHash, "initialization_sequence": j.QueueInitSequence})
	if err = appendClientReceipt(tx, project, Str(binding, "queue_generation"), "", "HOST_PAUSE_CAPABILITY", j.DispatchKey+":pause-capability", body, nil); err != nil {
		return err
	}
	if err = c.confirmResumeInitialization(tx, project, run, binding); err != nil {
		return err
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) deliverRuntimePause(ctx context.Context, project, run string, binding Object, bridge *rt.Bridge) (bool, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return true, err
	}
	intent, err := pauseIntent(tx, project, run, binding["runtime_epoch"])
	tx.Rollback()
	if err != nil {
		return true, err
	}
	if intent == nil || intent["state"] == "RESUMED" {
		return false, nil
	}
	if intent["state"] == "CANCELLED" {
		return true, nil
	}
	if intent["dispatch_key"] != binding["dispatch_key"] || intent["manifest_hash"] != binding["manifest_hash"] || intent["process_identity_hash"] != Hash(binding["process_identity"]) {
		return true, Fail(409, "GATE_FAILED", "pause dispatch changed")
	}
	if !bridge.Read().PauseRequested {
		if intent["state"] != "PAUSE_REQUESTED" {
			return true, Fail(409, "STATE_CONFLICT", "pause process state ambiguous")
		}
		return true, bridge.Control(ctx, Object{"type": "command.pause", "version": rt.PauseProtocol, "pause_id": intent["pause_id"], "binding": binding})
	}
	return true, nil
}

// The SDK validated its own tree before emitting the frame. Core additionally
// proves that every frozen command belongs to the canonical queue and that no
// accepted command has disappeared from the snapshot.
func validatePauseQueue(tx *sql.Tx, intent, snapshot Object) error {
	commands := Arr(snapshot, "commands")
	if len(commands) > 32 {
		return Fail(409, "GATE_FAILED", "pause command limit")
	}
	queue, _ := snapshot["queue_state"].(map[string]any)
	if queue == nil || queue["command_ledger_hash"] != Hash(commands) {
		return Fail(409, "GATE_FAILED", "pause ledger hash")
	}
	seen := map[string]bool{}
	var cut int64
	for _, v := range commands {
		entry, ok := v.(map[string]any)
		if !ok {
			return Fail(409, "GATE_FAILED", "pause command entry")
		}
		details, _ := entry["details"].(map[string]any)
		id := Str(details, "command_id")
		seq, err := Num(details, "queue_sequence")
		if err != nil || id == "" || seen[id] || details["queue_generation"] != intent["generation"] {
			return Fail(409, "GATE_FAILED", "pause command identity")
		}
		seen[id] = true
		if seq > cut {
			cut = seq
		}
		frozen, err := Decode([]byte(Str(entry, "frozen")))
		if err != nil {
			return err
		}
		var state, message, content, hash, delivery string
		var storedSeq int64
		err = tx.QueryRow(`SELECT state,message_id,content,content_hash,delivery,queue_sequence FROM client_command_queue WHERE generation=? AND command_id=?`, intent["generation"], id).Scan(&state, &message, &content, &hash, &delivery, &storedSeq)
		if err != nil {
			return err
		}
		if storedSeq != seq || entry["message_id"] != message || details["content_hash"] != hash || frozen["command_id"] != id || frozen["message_id"] != message || frozen["content"] != content || frozen["content_hash"] != hash || frozen["delivery"] != delivery || Hash(frozen["queue_sequence"]) != Hash(seq) {
			return Fail(409, "GATE_FAILED", "pause canonical command mismatch")
		}
		if state != entry["state"] || state != "SDK_ACCEPTED" && state != "CONSUMED" && state != "DROPPED" {
			return Fail(409, "GATE_FAILED", "pause command outcome unresolved")
		}
	}
	if Hash(cut) != Hash(queue["queue_cut"]) {
		return Fail(409, "GATE_FAILED", "pause queue cut")
	}
	rows, err := tx.Query(`SELECT command_id,state,queue_sequence FROM client_command_queue WHERE generation=? AND state<>'ENQUEUED'`, intent["generation"])
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var id, state string
		var seq int64
		if err = rows.Scan(&id, &state, &seq); err != nil {
			return err
		}
		if !seen[id] || seq > cut {
			return Fail(409, "GATE_FAILED", "pause omits canonical accepted command")
		}
	}
	return rows.Err()
}

// A purpose is constructed by the Host call site, never by the worker. The
// ordinary dispatch path has no purpose and keeps its strict lifecycle gate.
type runtimePauseGatePurpose struct {
	kind, pauseID, effectKey, requestHash string
}

func pauseDispatchPurposeGate(tx *sql.Tx, project string, task, run, dispatch Object, purpose *runtimePauseGatePurpose) (Object, error) {
	if task["status"] != "BLOCKED" || purpose == nil {
		return nil, nil
	}
	if task["active_run_id"] != run["id"] || run["status"] != "RUNNING" || run["cancel_requested_at"] != nil ||
		run["executor_principal_id"] == nil || run["runtime_id"] == nil {
		return nil, Fail(409, "STATE_CONFLICT", "current pause lifecycle required")
	}
	goal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, err
	}
	if goal["status"] != "ACTIVE" {
		return nil, Fail(409, "STATE_CONFLICT", "current pause goal inactive")
	}
	intent, err := pauseIntent(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil {
		return nil, err
	}
	if intent == nil || intent["project"] != project || intent["task"] != task["id"] || intent["run"] != run["id"] ||
		Hash(intent["epoch"]) != Hash(run["lease_epoch"]) || intent["runtime"] != run["runtime_id"] ||
		intent["dispatch_key"] != dispatch["dispatch_key"] || intent["manifest_hash"] != dispatch["manifest_hash"] ||
		intent["process_identity_hash"] != Hash(dispatch["identity"]) || Str(intent, "pause_id") == "" {
		return nil, Fail(409, "GATE_FAILED", "current pause dispatch binding changed")
	}
	witness, err := requiredPauseReceipt(tx, intent, "STATE_TRANSITION")
	if err != nil {
		return nil, err
	}
	if witness["state"] != intent["state"] || Hash(witness["revision"]) != Hash(intent["revision"]) || witness["intent_hash"] != Hash(intent) {
		return nil, Fail(409, "GATE_FAILED", "current pause witness changed")
	}
	if _, err = freshPauseActor(tx, Str(intent, "principal"), project, Str(task, "id"), Str(run, "id")); err != nil {
		return nil, err
	}
	var state, session, generation, key, manifestHash, identity string
	var epoch int64
	var restored int
	if err = tx.QueryRow(`SELECT state,session_id,generation,dispatch_key,manifest_hash,process_identity,runtime_epoch,restore_fenced FROM client_queue_fences WHERE project=? AND task_id=? AND run_id=?`, project, task["id"], run["id"]).Scan(&state, &session, &generation, &key, &manifestHash, &identity, &epoch, &restored); err != nil {
		return nil, err
	}
	process, err := Decode([]byte(identity))
	if err != nil || state != "OPEN" || restored != 0 || session != intent["session_id"] || generation != intent["generation"] ||
		Hash(epoch) != Hash(intent["epoch"]) || key != dispatch["dispatch_key"] || manifestHash != dispatch["manifest_hash"] || Hash(process) != Hash(dispatch["identity"]) {
		return nil, Fail(409, "GATE_FAILED", "current pause queue binding changed")
	}
	var control string
	if err = tx.QueryRow(`SELECT action FROM orchestration_task_controls WHERE project=? AND task=?`, project, task["id"]).Scan(&control); err != nil || control != "PAUSE" {
		return nil, Fail(409, "STATE_CONFLICT", "current pause control ended")
	}
	switch purpose.kind {
	case "checkpoint", "heartbeat":
		if purpose.pauseID == "" || purpose.pauseID != intent["pause_id"] ||
			(intent["state"] != "PAUSE_REQUESTED" && !(purpose.kind == "heartbeat" && intent["state"] == "CHECKPOINT_SEALED")) {
			return nil, Fail(409, "STATE_CONFLICT", "current pause checkpoint phase ended")
		}
	case "effect-read", "effect-start", "effect-observe", "effect-continue", "effect-finish":
		if intent["state"] != "PAUSE_REQUESTED" || purpose.effectKey == "" {
			return nil, Fail(409, "STATE_CONFLICT", "current pause effect phase ended")
		}
		effect, effectErr := latestEffect(tx, project, Str(run, "id"), purpose.effectKey)
		if effectErr != nil || Hash(effect["epoch"]) != Hash(run["lease_epoch"]) ||
			(purpose.requestHash != "" && effect["request_hash"] != purpose.requestHash) || effect["state"] == "UNKNOWN" {
			return nil, Fail(409, "GATE_FAILED", "current pause effect binding changed")
		}
		admitted, cutoffErr := pauseEffectInCutoff(tx, intent, effect, purpose.kind == "effect-start")
		if cutoffErr != nil {
			return nil, cutoffErr
		}
		if !admitted || (purpose.kind == "effect-observe" && effect["state"] != "STARTED" && effect["state"] != "CONFIRMED") ||
			(purpose.kind == "effect-continue" && effect["state"] != "STARTED") ||
			(purpose.kind == "effect-finish" && effect["state"] != "CONFIRMED" && effect["state"] != "NOT_APPLIED") {
			return nil, Fail(409, "STATE_CONFLICT", "effect is outside original pause cutoff")
		}
	default:
		return nil, Fail(409, "GATE_FAILED", "unknown pause dispatch purpose")
	}
	return intent, nil
}

func (c *RuntimeCoordinator) pauseCheckpoint(ctx context.Context, route RuntimeCoordinatorRoute, runID, lease string, epoch int64, key string, bridge *rt.Bridge, frame rt.BridgeFrame) (Object, error) {
	j := bridge.Read()
	cp := j.Checkpoint
	if cp == nil || cp.Version != rt.PauseProtocol || cp.PauseID != j.PauseID || j.CheckpointSequence != frame.Sequence {
		return nil, Fail(409, "GATE_FAILED", "captured pause checkpoint required")
	}
	raw, err := bridge.CheckpointBytes()
	if err != nil {
		return nil, err
	}
	snapshot, err := Decode(raw)
	if err != nil {
		return nil, err
	}
	tx, run, dispatch, err := c.dispatchGate(ctx, route, runID, lease, epoch, runtimePauseGatePurpose{kind: "checkpoint", pauseID: cp.PauseID})
	if err != nil {
		return nil, err
	}
	intent, err := pauseIntent(tx, route.ProjectID, runID, epoch)
	if err == nil && (intent == nil || intent["state"] != "PAUSE_REQUESTED" || intent["pause_id"] != cp.PauseID || intent["original_input_hash"] != cp.InputHash || intent["process_identity_hash"] != Hash(dispatch["identity"])) {
		err = Fail(409, "GATE_FAILED", "pause checkpoint intent mismatch")
	}
	if err == nil {
		err = validatePauseQueue(tx, intent, snapshot)
	}
	tx.Rollback()
	if err != nil {
		return nil, err
	}
	fact := Object{"version": rt.PauseProtocol, "project_id": route.ProjectID, "run_id": runID, "epoch": epoch, "manifest_hash": dispatch["manifest_hash"], "dispatch_key": dispatch["dispatch_key"], "sequence": frame.Sequence, "content_hash": Digest(raw), "payload_locator": "checkpoint.sealed.json", "byte_size": len(raw), "metadata": cp}
	factRaw := Bytes(fact)
	if len(factRaw) > 64*1024 {
		return nil, Fail(409, "GATE_FAILED", "pause metadata bound")
	}
	if err = writeRuntimeFact(filepath.Join(bridge.Directory(), fmt.Sprintf("checkpoint-%d.json", frame.Sequence)), factRaw); err != nil {
		return nil, err
	}
	c.boundary("checkpoint_durable", fact)
	artifact, err := c.sealOutput(ctx, route, runID, key+"-checkpoint-"+strconv.FormatInt(frame.Sequence, 10), raw, j, "CHECKPOINT")
	if err != nil {
		return nil, err
	}
	if err = c.heartbeat(ctx, route, runID, lease, epoch, key, Str(artifact, "id"), runtimePauseGatePurpose{kind: "heartbeat", pauseID: cp.PauseID}); err != nil {
		return nil, err
	}
	tx, err = c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, err
	}
	intent, err = pauseIntent(tx, route.ProjectID, runID, epoch)
	if err != nil {
		return nil, err
	}
	if intent == nil || intent["state"] != "PAUSE_REQUESTED" || intent["pause_id"] != cp.PauseID {
		return nil, Fail(409, "STATE_CONFLICT", "pause superseded before seal")
	}
	_, use, err := c.service.artifactUse(tx, route.ProjectID, run, Str(artifact, "id"), false)
	if err != nil {
		return nil, err
	}
	if artifact["content_hash"] != cp.ContentHash || Digest(raw) != cp.ContentHash || Hash(artifact["byte_size"]) != Hash(cp.Bytes) {
		return nil, Fail(409, "GATE_FAILED", "sealed checkpoint bytes mismatch")
	}
	if _, err = pauseCAS(tx, intent, "CHECKPOINT_SEALED", Object{"checkpoint_sequence": frame.Sequence, "checkpoint_artifact": artifact["id"], "checkpoint_use_receipt_hash": use["receipt_hash"], "checkpoint_use_principal": use["principal_id"], "checkpoint_hash": cp.ContentHash, "checkpoint_bytes": cp.Bytes, "native_session_ref": run["external_run_id"], "sdk_session_id": cp.SDKSessionID, "queue_cut": cp.QueueCut, "command_ledger_hash": cp.CommandLedgerHash, "sdk_watermarks_json": string(cp.SDKWatermarks), "model_calls": cp.ModelCalls, "tool_calls": cp.ToolCalls, "journal_checkpoint_hash": Digest(factRaw)}); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return Object{"pause_seal": rt.CheckpointSeal{Version: rt.PauseProtocol, Type: "checkpoint.sealed", PauseID: cp.PauseID, Binding: cp.Binding, Sequence: frame.Sequence, ContentHash: cp.ContentHash, CheckpointArtifactID: Str(artifact, "id"), CheckpointUseReceiptHash: Str(use, "receipt_hash"), CheckpointUsePrincipal: Str(use, "principal_id"), JournalCheckpointHash: Digest(factRaw)}}, nil
}

func (c *RuntimeCoordinator) confirmRuntimePause(ctx context.Context, project, runID string, epoch int64, j rt.BridgeJournal) error {
	if j.PauseProtocol != rt.PauseProtocol {
		return nil
	}
	observation, err := j.Observation()
	if err != nil {
		return err
	}
	if j.State != "PAUSED" || !j.Paused || j.CheckpointSeal == nil || j.Checkpoint == nil {
		return Fail(409, "GATE_FAILED", "native pause proof incomplete")
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return err
	}
	intent, err := pauseIntent(tx, project, runID, epoch)
	if err != nil {
		return err
	}
	if intent == nil {
		return Fail(409, "GATE_FAILED", "pause intent missing")
	}
	if intent["state"] == "PAUSED_CONFIRMED" || intent["state"] == "RESUME_PREPARED" || intent["state"] == "RESUMED" {
		return nil
	}
	if intent["state"] != "CHECKPOINT_SEALED" {
		return Fail(409, "STATE_CONFLICT", "pause cancelled or unresolved")
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return err
	}
	if Hash(run["lease_epoch"]) != Hash(epoch) || run["status"] == "CANCEL_REQUESTED" {
		return Fail(409, "STATE_CONFLICT", "pause epoch no longer current")
	}
	if _, err = nativeDispatchProof(tx, project, run, observation); err != nil {
		return err
	}
	if err = pauseEffectsSettled(tx, project, runID); err != nil {
		return err
	}
	seal := j.CheckpointSeal
	if intent["checkpoint_artifact"] != seal.CheckpointArtifactID || intent["checkpoint_hash"] != seal.ContentHash || intent["checkpoint_use_receipt_hash"] != seal.CheckpointUseReceiptHash || intent["checkpoint_use_principal"] != seal.CheckpointUsePrincipal || intent["journal_checkpoint_hash"] != seal.JournalCheckpointHash {
		return Fail(409, "GATE_FAILED", "pause seal proof mismatch")
	}
	if err = appendPauseReceipt(tx, intent, "NATIVE_STOPPED", Object{"observation": observation, "observation_hash": Hash(observation), "seal": seal}); err != nil {
		return err
	}
	if _, err = pauseCAS(tx, intent, "PAUSED_CONFIRMED", nil); err != nil {
		return err
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) confirmResumeInitialization(tx *sql.Tx, project, run string, binding Object) error {
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		return err
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_checkpoint_activations WHERE project=? AND run=? AND epoch=?`, project, run, binding["runtime_epoch"])
	if err != nil || len(rows) == 0 {
		return err
	}
	a := rows[0]
	intent, err := pauseIntent(tx, project, run, a["previous_epoch"])
	if err != nil {
		return err
	}
	if intent["state"] == "RESUMED" {
		return nil
	}
	if intent["state"] != "RESUME_PREPARED" || a["dispatch_key"] != binding["dispatch_key"] || a["manifest_hash"] != binding["manifest_hash"] {
		return Fail(409, "GATE_FAILED", "resume initialization binding")
	}
	_, err = pauseCAS(tx, intent, "RESUMED", nil)
	return err
}

func (c *RuntimeCoordinator) pauseActivationInputs(tx *sql.Tx, project string, run, request Object, inputs map[string][]byte) error {
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		return err
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_checkpoint_activations WHERE project=? AND run=? AND epoch=?`, project, run["id"], run["lease_epoch"])
	if err != nil || len(rows) == 0 {
		return err
	}
	a := rows[0]
	intent, err := pauseIntent(tx, project, Str(run, "id"), a["previous_epoch"])
	if err != nil {
		return err
	}
	if intent["state"] != "RESUME_PREPARED" {
		return Fail(409, "STATE_CONFLICT", "resume activation is not launchable")
	}
	_, use, err := c.service.artifactUse(tx, project, run, Str(a, "checkpoint_artifact"), false)
	if err != nil {
		return err
	}
	if use["receipt_hash"] != a["carry_use_receipt_hash"] || use["principal_id"] != a["carry_use_principal"] {
		return Fail(409, "GATE_FAILED", "resume carry proof changed")
	}
	raw := inputs["checkpoint.json"]
	if len(raw) == 0 || len(raw) > rt.MaxPauseCheckpointBytes || Digest(raw) != a["checkpoint_hash"] {
		return Fail(409, "GATE_FAILED", "resume captured bytes mismatch")
	}
	inputs[rt.PauseCheckpointFilename] = raw
	delete(inputs, "checkpoint.json")
	request["pause_activation"] = Object{"version": runtimePauseProtocol, "previous_epoch": a["previous_epoch"], "new_epoch": a["epoch"], "checkpoint_hash": a["checkpoint_hash"], "checkpoint_artifact_id": a["checkpoint_artifact"], "checkpoint_use_receipt_hash": a["checkpoint_use_receipt_hash"], "checkpoint_use_principal": a["checkpoint_use_principal"], "carry_use_receipt_hash": a["carry_use_receipt_hash"], "original_input_hash": a["original_input_hash"]}
	return nil
}

// preparePausedSuccessor is called only by the sole coordinator under scanMu.
// Its transaction consumes explicit user authority and never creates a new Run.
func (c *RuntimeCoordinator) preparePausedSuccessor(ctx context.Context, route RuntimeCoordinatorRoute) (Object, string, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return nil, "", err
	}
	defer tx.Rollback()
	if err = resourceWriteLock(tx); err != nil {
		return nil, "", err
	}
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		return nil, "", err
	}
	prepared, lease, err := c.recoverPreparedPauseLease(tx, route)
	if err != nil {
		return nil, "", err
	}
	if prepared != nil {
		if err = tx.Commit(); err != nil {
			return nil, "", err
		}
		return prepared, lease, nil
	}
	rows, err := configurationBackupRows(tx, `SELECT p.* FROM runtime_pause_intents p JOIN domain_objects r ON r.project=p.project AND r.kind='Run' AND r.id=p.run WHERE p.project=? AND p.runtime=? AND p.state='PAUSED_CONFIRMED' AND json_extract(r.body,'$.executor_principal_id')=? AND EXISTS(SELECT 1 FROM runtime_pause_receipts x WHERE x.project=p.project AND x.pause_id=p.pause_id AND x.kind='RESUME_REQUESTED' AND NOT EXISTS(SELECT 1 FROM runtime_pause_receipts f WHERE f.project=x.project AND f.pause_id=x.pause_id AND f.kind='RESUME_REJECTED' AND json_extract(f.body,'$.request_key')=json_extract(x.body,'$.request_key'))) ORDER BY p.created_at LIMIT 1`, route.ProjectID, route.RuntimeID, route.ExecutorID)
	if err != nil || len(rows) == 0 {
		return nil, "", err
	}
	intent := rows[0]
	var raw string
	if err = tx.QueryRow(`SELECT body FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='RESUME_REQUESTED' ORDER BY sequence DESC LIMIT 1`, route.ProjectID, intent["pause_id"]).Scan(&raw); err != nil {
		return nil, "", err
	}
	request, err := Decode([]byte(raw))
	if err != nil {
		return nil, "", err
	}
	actor, err := freshPauseActor(tx, Str(request, "principal"), route.ProjectID, Str(intent, "task"), Str(intent, "run"))
	if err != nil {
		if e := appendPauseReceipt(tx, intent, "RESUME_REJECTED", Object{"request_key": request["request_key"], "reason": "current actor authority unavailable"}); e != nil {
			return nil, "", e
		}
		if e := tx.Commit(); e != nil {
			return nil, "", e
		}
		return nil, "", err
	}
	run, err := load(tx, route.ProjectID, "Run", Str(intent, "run"))
	if err != nil {
		return nil, "", err
	}
	task, err := load(tx, route.ProjectID, "Task", Str(intent, "task"))
	if err != nil {
		return nil, "", err
	}
	if Hash(run["lease_epoch"]) != Hash(intent["epoch"]) || run["status"] != "RUNNING" || task["status"] != "BLOCKED" || task["active_run_id"] != run["id"] || Hash(request["task_revision"]) != Hash(task["revision"]) || Hash(request["pause_revision"]) != Hash(intent["revision"]) || request["checkpoint_hash"] != intent["checkpoint_hash"] {
		return nil, "", Fail(409, "STATE_CONFLICT", "resume request no longer current")
	}
	if err = c.sessionTaskRoute(tx, route.ProjectID, task, route.RuntimeID); err != nil {
		return nil, "", err
	}
	if err = pauseEffectsSettled(tx, route.ProjectID, Str(run, "id")); err != nil {
		return nil, "", err
	}
	oldDispatch, err := runtimeDispatch(tx, route.ProjectID, Str(run, "id"), intent["epoch"])
	if err != nil {
		return nil, "", err
	}
	admission, err := c.sealedPauseAdmission(tx, route, task, run, oldDispatch, intent, request)
	if err != nil {
		return nil, "", err
	}
	var stop string
	if err = tx.QueryRow(`SELECT body FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind='NATIVE_STOPPED'`, route.ProjectID, intent["pause_id"]).Scan(&stop); err != nil {
		return nil, "", err
	}
	proof, err := Decode([]byte(stop))
	if err != nil {
		return nil, "", err
	}
	observation, _ := proof["observation"].(map[string]any)
	if _, err = nativeDispatchProof(tx, route.ProjectID, run, observation); err != nil {
		return nil, "", err
	}
	artifact, oldUse, err := c.service.artifactUse(tx, route.ProjectID, run, Str(intent, "checkpoint_artifact"), false)
	if err != nil {
		return nil, "", err
	}
	var fence string
	var fenced int64
	var queueEpoch int64
	if err = tx.QueryRow(`SELECT state,restore_fenced,runtime_epoch FROM client_queue_fences WHERE generation=? AND dispatch_key=? AND manifest_hash=?`, intent["generation"], intent["dispatch_key"], intent["manifest_hash"]).Scan(&fence, &fenced, &queueEpoch); err != nil {
		return nil, "", err
	}
	if fence != "OPEN" || fenced != 0 || Hash(queueEpoch) != Hash(intent["epoch"]) {
		return nil, "", Fail(409, "STATE_CONFLICT", "resume queue fenced")
	}
	oldEpoch, _ := Num(intent, "epoch")
	newEpoch := oldEpoch + 1
	lease = ID() + ID()
	if _, err = pauseCAS(tx, intent, "RESUME_PREPARED", Object{"successor_epoch": newEpoch}); err != nil {
		return nil, "", err
	}
	Merge(run, Object{"lease_epoch": newEpoch, "lease_token_hash": Digest([]byte(lease)), "lease_expires_at": time.Now().UTC().Add(90 * time.Second).Format(time.RFC3339Nano), "external_run_id": nil, "status": "QUEUED", "heartbeat_at": nil, "children_stopped": nil, "queue_empty": nil, "runtime_settled_at": nil})
	if err = bump(run); err != nil {
		return nil, "", err
	}
	if err = c.service.put(tx, "Run", run); err != nil {
		return nil, "", err
	}
	if err = c.service.reserveRuntimeLocalLaunch(tx, route.ProjectID, run, admission); err != nil {
		return nil, "", err
	}
	if err = c.service.carryCheckpoint(tx, route.ProjectID, actor.ID, run, artifact, oldUse); err != nil {
		return nil, "", err
	}
	_, use, err := c.service.artifactUse(tx, route.ProjectID, run, Str(artifact, "id"), false)
	if err != nil {
		return nil, "", err
	}
	if err = c.service.prepareRuntimeDispatch(tx, route.ProjectID, task, run, admission); err != nil {
		return nil, "", err
	}
	dispatch, err := runtimeDispatch(tx, route.ProjectID, Str(run, "id"), newEpoch)
	if err != nil {
		return nil, "", err
	}
	_, err = tx.Exec(`INSERT INTO runtime_checkpoint_activations(project,run,epoch,previous_epoch,pause_id,task,session_id,generation,principal,request_key,request_hash,dispatch_key,manifest_hash,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,carry_use_receipt_hash,carry_use_principal,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,created_at) SELECT project,run,successor_epoch,epoch,pause_id,task,session_id,generation,?,?,?,?,?,checkpoint_artifact,checkpoint_hash,checkpoint_use_receipt_hash,checkpoint_use_principal,?,?,original_input_hash,native_session_ref,sdk_session_id,queue_cut,model_calls,tool_calls,? FROM runtime_pause_intents WHERE project=? AND pause_id=?`, actor.ID, request["request_key"], request["request_hash"], dispatch["dispatch_key"], dispatch["manifest_hash"], use["receipt_hash"], use["principal_id"], Now(), route.ProjectID, intent["pause_id"])
	if err != nil {
		return nil, "", err
	}
	result, err := tx.Exec(`UPDATE client_queue_fences SET runtime_epoch=?,dispatch_key=?,manifest_hash=?,process_identity='{}',revision=revision+1 WHERE generation=? AND runtime_epoch=? AND dispatch_key=? AND state='OPEN' AND restore_fenced=0`, newEpoch, dispatch["dispatch_key"], dispatch["manifest_hash"], intent["generation"], oldEpoch, intent["dispatch_key"])
	if err != nil {
		return nil, "", err
	}
	n, err := result.RowsAffected()
	if err != nil {
		return nil, "", err
	}
	if n != 1 {
		return nil, "", Fail(409, "STATE_CONFLICT", "resume queue CAS lost")
	}
	if err = appendPauseReceipt(tx, intent, "RESUME_CONSUMED", Object{"request_key": request["request_key"], "epoch": newEpoch, "dispatch_key": dispatch["dispatch_key"]}); err != nil {
		return nil, "", err
	}
	task["status"] = "RUNNING"
	if err = bump(task); err != nil {
		return nil, "", err
	}
	if err = c.service.put(tx, "Task", task); err != nil {
		return nil, "", err
	}
	if _, err = tx.Exec(`DELETE FROM orchestration_task_controls WHERE project=? AND task=? AND action='PAUSE'`, route.ProjectID, task["id"]); err != nil {
		return nil, "", err
	}
	if err = c.service.event(tx, route.ProjectID, "Run", run, actor.ID, ID(), "RUN_CHANGED"); err != nil {
		return nil, "", err
	}
	if err = tx.Commit(); err != nil {
		return nil, "", err
	}
	return run, lease, nil
}

// JSON roundtrip is used only for metadata, never for checkpoint payload bytes.
func pauseSealResponse(value any) (rt.CheckpointSeal, bool) {
	o, ok := value.(Object)
	if !ok {
		return rt.CheckpointSeal{}, false
	}
	v, ok := o["pause_seal"]
	if !ok {
		return rt.CheckpointSeal{}, false
	}
	if seal, ok := v.(rt.CheckpointSeal); ok {
		return seal, true
	}
	var seal rt.CheckpointSeal
	err := json.Unmarshal(Bytes(v), &seal)
	return seal, err == nil
}

// Offline recovery uses Windows no-reparse/final-handle semantics. The only
// payload location is the bridge's trusted captured file, never sandbox output.
func readRuntimePauseFile(path string, limit int64) ([]byte, error) {
	actual, err := filepath.EvalSymlinks(path)
	if err != nil || !strings.EqualFold(filepath.Clean(actual), filepath.Clean(path)) {
		return nil, errors.New("pause recovery reparse rejected")
	}
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	h, err := windows.CreateFile(p, windows.GENERIC_READ, windows.FILE_SHARE_READ, nil, windows.OPEN_EXISTING, windows.FILE_FLAG_OPEN_REPARSE_POINT, 0)
	if err != nil {
		return nil, err
	}
	file := os.NewFile(uintptr(h), path)
	defer file.Close()
	final := make([]uint16, 32768)
	n, err := windows.GetFinalPathNameByHandle(h, &final[0], uint32(len(final)), 0)
	if err != nil || n >= uint32(len(final)) || !strings.EqualFold(strings.TrimPrefix(windows.UTF16ToString(final[:n]), `\\?\`), strings.TrimPrefix(filepath.Clean(path), `\\?\`)) {
		return nil, errors.New("pause recovery opened path differs")
	}
	var info windows.ByHandleFileInformation
	if err = windows.GetFileInformationByHandle(h, &info); err != nil || info.FileAttributes&(windows.FILE_ATTRIBUTE_REPARSE_POINT|windows.FILE_ATTRIBUTE_DIRECTORY) != 0 {
		return nil, errors.New("pause recovery regular file required")
	}
	stat, err := file.Stat()
	if err != nil || !stat.Mode().IsRegular() || stat.Size() <= 0 || stat.Size() > limit {
		return nil, errors.New("pause recovery file size invalid")
	}
	raw, err := io.ReadAll(io.LimitReader(file, limit+1))
	if err != nil || int64(len(raw)) != stat.Size() || int64(len(raw)) > limit {
		return nil, errors.New("pause recovery bounded read failed")
	}
	return raw, nil
}

func (c *RuntimeCoordinator) recoverPauseCheckpoint(tx *sql.Tx, project, runID, directory string, epoch int64, dispatch, fact Object, factRaw []byte) (Object, error) {
	if len(factRaw) > 64*1024 || fact["payload_locator"] != "checkpoint.sealed.json" {
		return nil, Fail(409, "GATE_FAILED", "pause recovery metadata locator")
	}
	raw, err := readRuntimePauseFile(filepath.Join(directory, "checkpoint.sealed.json"), rt.MaxPauseCheckpointBytes)
	if err != nil {
		return nil, err
	}
	if fact["content_hash"] != Digest(raw) || Hash(fact["byte_size"]) != Hash(len(raw)) {
		return nil, Fail(409, "GATE_FAILED", "pause recovered content mismatch")
	}
	var cp rt.PauseCheckpoint
	if err = json.Unmarshal(Bytes(fact["metadata"]), &cp); err != nil {
		return nil, err
	}
	intent, err := pauseIntent(tx, project, runID, epoch)
	if err != nil {
		return nil, err
	}
	if intent == nil || intent["pause_id"] != cp.PauseID || cp.Version != rt.PauseProtocol || cp.ContentHash != Digest(raw) || cp.Bytes != int64(len(raw)) || intent["original_input_hash"] != cp.InputHash || intent["process_identity_hash"] != Hash(dispatch["identity"]) {
		return nil, Fail(409, "GATE_FAILED", "pause recovered original binding")
	}
	snapshot, err := Decode(raw)
	if err != nil {
		return nil, err
	}
	if intent["state"] == "PAUSE_REQUESTED" {
		if err = validatePauseQueue(tx, intent, snapshot); err != nil {
			return nil, err
		}
	}
	artifact, err := c.recoverArtifact(tx, project, dispatch, raw, "CHECKPOINT")
	if err != nil {
		return nil, err
	}
	if intent["state"] == "PAUSE_REQUESTED" {
		manifest := dispatch["manifest"].(map[string]any)
		var useRaw string
		if err = tx.QueryRow(`SELECT body FROM artifact_uses WHERE project=? AND artifact=? AND run=? AND epoch=? AND principal=?`, project, artifact["id"], runID, epoch, manifest["executor_principal_id"]).Scan(&useRaw); err != nil {
			return nil, err
		}
		use, err := Decode([]byte(useRaw))
		if err != nil {
			return nil, err
		}
		_, err = pauseCAS(tx, intent, "CHECKPOINT_SEALED", Object{"checkpoint_sequence": fact["sequence"], "checkpoint_artifact": artifact["id"], "checkpoint_use_receipt_hash": use["receipt_hash"], "checkpoint_use_principal": use["principal_id"], "checkpoint_hash": cp.ContentHash, "checkpoint_bytes": cp.Bytes, "native_session_ref": dispatch["dispatch_key"], "sdk_session_id": cp.SDKSessionID, "queue_cut": cp.QueueCut, "command_ledger_hash": cp.CommandLedgerHash, "sdk_watermarks_json": string(cp.SDKWatermarks), "model_calls": cp.ModelCalls, "tool_calls": cp.ToolCalls, "journal_checkpoint_hash": Digest(factRaw)})
		if err != nil {
			return nil, err
		}
	} else if Str(intent, "checkpoint_hash") != "" && (intent["checkpoint_hash"] != cp.ContentHash || intent["checkpoint_artifact"] != artifact["id"] || intent["journal_checkpoint_hash"] != Digest(factRaw)) {
		return nil, Fail(409, "GATE_FAILED", "pause recovery conflicts with frozen seal")
	}
	return artifact, nil
}

// sealedPauseAdmission is a fixed internal proof category, authorized separately
// from general RuntimeRegistration.supports_resume. It cannot be client-selected.
func (c *RuntimeCoordinator) sealedPauseAdmission(tx *sql.Tx, route RuntimeCoordinatorRoute, task, run, dispatch, intent, request Object) (Object, error) {
	if intent == nil || intent["state"] != "PAUSED_CONFIRMED" || task["task_type"] != "mu_turn" || task["status"] != "BLOCKED" || run["status"] != "RUNNING" || task["active_run_id"] != run["id"] || Str(request, "request_key") == "" || Str(request, "request_hash") == "" || Hash(request["pause_revision"]) != Hash(intent["revision"]) || request["checkpoint_hash"] != intent["checkpoint_hash"] {
		return nil, Fail(409, "GATE_FAILED", "required sealed pause request missing")
	}
	if _, err := freshPauseActor(tx, Str(request, "principal"), route.ProjectID, Str(task, "id"), Str(run, "id")); err != nil {
		return nil, err
	}
	goal, err := load(tx, route.ProjectID, "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, err
	}
	if goal["status"] != "ACTIVE" || run["cancel_requested_at"] != nil {
		return nil, Fail(409, "STATE_CONFLICT", "sealed pause Goal or Run fenced")
	}
	if _, _, err := c.service.requiredSealedPauseProof(tx, route.ProjectID, run, intent); err != nil {
		return nil, err
	}
	prior, _ := dispatch["manifest"].(map[string]any)
	old, _ := prior["admission"].(map[string]any)
	if old == nil || old["qualification_bootstrap"] == true || old["legacy_fixture"] == true || len(Arr(old, "qualification_ids")) != 1 {
		return nil, Fail(409, "GATE_FAILED", "sealed pause requires full runtime qualification")
	}
	admission, err := c.service.currentDispatchAdmission(tx, route.ProjectID, task, run, dispatch, "sealed-pause-activation")
	if err != nil {
		return nil, err
	}
	if admission["qualification_bootstrap"] == true || admission["legacy_fixture"] == true || len(Arr(admission, "qualification_ids")) != 1 {
		return nil, Fail(409, "GATE_FAILED", "sealed pause qualification missing")
	}
	admission["sealed_pause_activation"] = Object{"pause_id": intent["pause_id"], "previous_epoch": intent["epoch"], "checkpoint_hash": intent["checkpoint_hash"]}
	return admission, nil
}

func requiredPauseReceipt(tx *sql.Tx, intent Object, kind string) (Object, error) {
	var raw, hash string
	if err := tx.QueryRow(`SELECT body,body_hash FROM runtime_pause_receipts WHERE project=? AND pause_id=? AND kind=? ORDER BY sequence DESC LIMIT 1`, intent["project"], intent["pause_id"], kind).Scan(&raw, &hash); err != nil {
		return nil, Fail(409, "GATE_FAILED", "required pause receipt missing: "+kind)
	}
	body, err := Decode([]byte(raw))
	if err != nil || Hash(body) != hash || body["project"] != intent["project"] || body["pause_id"] != intent["pause_id"] || body["kind"] != kind {
		return nil, Fail(409, "GATE_FAILED", "required pause receipt binding changed")
	}
	return body, nil
}

func (s *Service) requiredSealedPauseProof(tx *sql.Tx, project string, run, intent Object) (Object, Object, error) {
	fail := func(message string) (Object, Object, error) { return nil, nil, Fail(409, "GATE_FAILED", message) }
	installed, err := pauseInstalled(tx)
	if err != nil {
		return nil, nil, err
	}
	if !installed || intent == nil || intent["project"] != project || intent["run"] != run["id"] || intent["task"] != run["task_id"] || intent["state"] == "CANCELLED" || intent["state"] == "RECONCILING" {
		return fail("required sealed pause intent missing")
	}
	witness, err := requiredPauseReceipt(tx, intent, "STATE_TRANSITION")
	if err != nil {
		return nil, nil, err
	}
	if witness["state"] != intent["state"] || Hash(witness["revision"]) != Hash(intent["revision"]) || witness["intent_hash"] != Hash(intent) {
		return fail("required current pause witness changed")
	}
	d, err := runtimeDispatch(tx, project, Str(run, "id"), intent["epoch"])
	if err != nil {
		return nil, nil, err
	}
	if d["dispatch_key"] != intent["dispatch_key"] || d["manifest_hash"] != intent["manifest_hash"] || Hash(d["identity"]) != intent["process_identity_hash"] {
		return fail("required old pause dispatch changed")
	}
	binding := Object{"project_id": project, "run_id": run["id"], "task_id": run["task_id"], "session_id": intent["session_id"], "runtime_epoch": intent["epoch"], "queue_generation": intent["generation"], "dispatch_key": d["dispatch_key"], "manifest_hash": d["manifest_hash"], "process_identity": d["identity"]}
	var raw, hash string
	if err = tx.QueryRow(`SELECT body,body_hash FROM client_control_receipts WHERE generation=? AND receipt_id=? AND kind='HOST_PAUSE_CAPABILITY'`, intent["generation"], Str(d, "dispatch_key")+":pause-capability").Scan(&raw, &hash); err != nil {
		return fail("required old pause capability missing")
	}
	cap, err := Decode([]byte(raw))
	if err != nil || Hash(cap) != hash || cap["pause_protocol"] != runtimePauseProtocol || strings.TrimPrefix(Str(cap, "original_input_hash"), "sha256:") != intent["original_input_hash"] {
		return fail("required pause capability hash/input changed")
	}
	for k, v := range binding {
		if Hash(cap[k]) != Hash(v) {
			return fail("required pause capability binding changed")
		}
	}
	seq, err := Num(cap, "initialization_sequence")
	if err != nil || seq <= 0 {
		return fail("required initialization ACK missing")
	}
	if err = tx.QueryRow(`SELECT body,body_hash FROM client_control_receipts WHERE generation=? AND receipt_id=? AND kind='command.accepted'`, intent["generation"], fmt.Sprintf("%s:%d", d["dispatch_key"], seq)).Scan(&raw, &hash); err != nil {
		return fail("required initialization receipt missing")
	}
	init, err := Decode([]byte(raw))
	if err != nil || Hash(init) != hash || init["initialized"] != true {
		return fail("required initialization receipt invalid")
	}
	for k, v := range binding {
		if Hash(init[k]) != Hash(v) {
			return fail("required initialization binding changed")
		}
	}
	stop, err := requiredPauseReceipt(tx, intent, "NATIVE_STOPPED")
	if err != nil {
		return nil, nil, err
	}
	obs, _ := stop["observation"].(map[string]any)
	if obs == nil || stop["observation_hash"] != Hash(obs) || obs["state"] != "PAUSED" || obs["children_stopped"] != true || obs["streams_drained"] != true || obs["cleanup_complete"] != true {
		return fail("required native pause stop incomplete")
	}
	oldRun := Merge(Object{}, run)
	oldRun["lease_epoch"] = intent["epoch"]
	manifest := d["manifest"].(map[string]any)
	oldRun["executor_principal_id"] = manifest["executor_principal_id"]
	if _, err = nativeDispatchProof(tx, project, oldRun, obs); err != nil {
		return nil, nil, err
	}
	var seal rt.CheckpointSeal
	if err = json.Unmarshal(Bytes(stop["seal"]), &seal); err != nil || seal.Version != runtimePauseProtocol || seal.PauseID != intent["pause_id"] || Hash(seal.Binding) != Hash(binding) || Hash(seal.Sequence) != Hash(intent["checkpoint_sequence"]) || seal.ContentHash != intent["checkpoint_hash"] || seal.CheckpointArtifactID != intent["checkpoint_artifact"] || seal.CheckpointUseReceiptHash != intent["checkpoint_use_receipt_hash"] || seal.CheckpointUsePrincipal != intent["checkpoint_use_principal"] || seal.JournalCheckpointHash != intent["journal_checkpoint_hash"] {
		return fail("required typed checkpoint ACK changed")
	}
	artifact, use, err := s.artifactUse(tx, project, oldRun, Str(intent, "checkpoint_artifact"), false)
	if err != nil {
		return nil, nil, err
	}
	if artifact["kind"] != "CHECKPOINT" || artifact["content_hash"] != intent["checkpoint_hash"] || Hash(artifact["byte_size"]) != Hash(intent["checkpoint_bytes"]) || use["receipt_hash"] != intent["checkpoint_use_receipt_hash"] || use["principal_id"] != intent["checkpoint_use_principal"] {
		return fail("required old checkpoint use changed")
	}
	var content []byte
	if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, project, use["storage_key"]).Scan(&content); err != nil {
		return nil, nil, err
	}
	if len(content) == 0 || len(content) > rt.MaxPauseCheckpointBytes || Digest(content) != intent["checkpoint_hash"] {
		return fail("required sealed pause bytes changed")
	}
	snapshot, err := Decode(content)
	if err != nil {
		return nil, nil, err
	}
	counts, _ := snapshot["counts"].(map[string]any)
	queue, _ := snapshot["queue_state"].(map[string]any)
	sdk, _ := snapshot["sdk"].(map[string]any)
	payload, _ := sdk["payload"].(map[string]any)
	sb, _ := payload["binding"].(map[string]any)
	if snapshot["version"] != runtimePauseProtocol || snapshot["pause_id"] != intent["pause_id"] || Hash(snapshot["binding"]) != Hash(binding) || snapshot["input_hash"] != intent["original_input_hash"] || sb["inputHash"] != intent["original_input_hash"] || sb["sessionId"] != intent["sdk_session_id"] || Hash(sb["leaseEpoch"]) != Hash(intent["epoch"]) || Hash(counts["model_calls"]) != Hash(intent["model_calls"]) || Hash(counts["tool_calls"]) != Hash(intent["tool_calls"]) || Hash(queue["queue_cut"]) != Hash(intent["queue_cut"]) || queue["command_ledger_hash"] != intent["command_ledger_hash"] || Hash(Arr(snapshot, "commands")) != intent["command_ledger_hash"] {
		return fail("required SDK pause snapshot binding changed")
	}
	watermarks, err := Decode([]byte(Str(intent, "sdk_watermarks_json")))
	if err != nil || Hash(watermarks) != Hash(queue["sdk_watermarks"]) {
		return fail("required SDK watermarks changed")
	}
	return artifact, use, nil
}

func (s *Service) pauseActivationGate(tx *sql.Tx, project string, run, dispatch Object) error {
	return s.pauseActivationGateWithCurrentPause(tx, project, run, dispatch, nil)
}

func (s *Service) pauseActivationGateWithCurrentPause(tx *sql.Tx, project string, run, dispatch, currentPause Object) error {
	manifest, _ := dispatch["manifest"].(map[string]any)
	admission, _ := manifest["admission"].(map[string]any)
	marker, _ := admission["sealed_pause_activation"].(map[string]any)
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		if err == nil && marker != nil {
			return Fail(409, "GATE_FAILED", "required activation schema missing")
		}
		return err
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_checkpoint_activations WHERE project=? AND run=? AND epoch=?`, project, run["id"], run["lease_epoch"])
	if err != nil {
		return err
	}
	if len(rows) == 0 {
		var required int
		if err = tx.QueryRow(`SELECT count(*) FROM runtime_pause_intents WHERE project=? AND run=? AND successor_epoch=?`, project, run["id"], run["lease_epoch"]).Scan(&required); err != nil {
			return err
		}
		if marker != nil || required != 0 {
			return Fail(409, "GATE_FAILED", "required immutable activation missing")
		}
		return err
	}
	a := rows[0]
	intent, err := pauseIntent(tx, project, Str(run, "id"), a["previous_epoch"])
	if err != nil {
		return err
	}
	if intent == nil || (intent["state"] != "RESUME_PREPARED" && intent["state"] != "RESUMED") || a["dispatch_key"] != dispatch["dispatch_key"] || a["manifest_hash"] != dispatch["manifest_hash"] {
		return Fail(409, "STATE_CONFLICT", "pause activation authority ended")
	}
	if marker == nil || marker["pause_id"] != a["pause_id"] || Hash(marker["previous_epoch"]) != Hash(a["previous_epoch"]) || marker["checkpoint_hash"] != a["checkpoint_hash"] || admission["qualification_bootstrap"] == true || admission["legacy_fixture"] == true || len(Arr(admission, "qualification_ids")) != 1 {
		return Fail(409, "GATE_FAILED", "required activation manifest marker missing")
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return err
	}
	goal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return err
	}
	if (task["status"] != "RUNNING" && (task["status"] != "BLOCKED" || currentPause == nil)) || task["active_run_id"] != run["id"] || goal["status"] != "ACTIVE" || run["cancel_requested_at"] != nil || (run["status"] != "QUEUED" && run["status"] != "STARTING" && run["status"] != "RUNNING") {
		return Fail(409, "STATE_CONFLICT", "required activation lifecycle fenced")
	}
	oldEpoch, _ := Num(a, "previous_epoch")
	newEpoch, _ := Num(a, "epoch")
	if newEpoch != oldEpoch+1 || Hash(run["lease_epoch"]) != Hash(newEpoch) || a["project"] != project || a["run"] != run["id"] || a["task"] != run["task_id"] || Hash(intent["successor_epoch"]) != Hash(newEpoch) {
		return Fail(409, "GATE_FAILED", "required successor identity changed")
	}
	for _, k := range []string{"pause_id", "task", "session_id", "generation", "checkpoint_artifact", "checkpoint_hash", "checkpoint_use_receipt_hash", "checkpoint_use_principal", "original_input_hash", "native_session_ref", "sdk_session_id", "queue_cut", "model_calls", "tool_calls"} {
		if Hash(a[k]) != Hash(intent[k]) {
			return Fail(409, "GATE_FAILED", "required activation original binding changed")
		}
	}
	if _, err = freshPauseActor(tx, Str(a, "principal"), project, Str(run, "task_id"), Str(run, "id")); err != nil {
		return err
	}
	if _, _, err = s.requiredSealedPauseProof(tx, project, run, intent); err != nil {
		return err
	}
	request, err := requiredPauseReceipt(tx, intent, "RESUME_REQUESTED")
	if err != nil {
		return err
	}
	if request["principal"] != a["principal"] || request["request_key"] != a["request_key"] || request["request_hash"] != a["request_hash"] || request["checkpoint_hash"] != a["checkpoint_hash"] {
		return Fail(409, "GATE_FAILED", "required activation request changed")
	}
	consumed, err := requiredPauseReceipt(tx, intent, "RESUME_CONSUMED")
	if err != nil {
		return err
	}
	if consumed["request_key"] != a["request_key"] || Hash(consumed["epoch"]) != Hash(a["epoch"]) || consumed["dispatch_key"] != a["dispatch_key"] {
		return Fail(409, "GATE_FAILED", "required activation consumption changed")
	}
	_, use, err := s.artifactUse(tx, project, run, Str(a, "checkpoint_artifact"), false)
	if err != nil {
		return err
	}
	if use["receipt_hash"] != a["carry_use_receipt_hash"] || use["principal_id"] != a["carry_use_principal"] {
		return Fail(409, "GATE_FAILED", "required activation carried use changed")
	}
	var raw string
	if err = tx.QueryRow(`SELECT body FROM resource_checkpoint_carries WHERE project=? AND run=? AND epoch=?`, project, run["id"], a["epoch"]).Scan(&raw); err != nil {
		return err
	}
	carry, err := Decode([]byte(raw))
	if err != nil {
		return err
	}
	ref, _ := carry["artifact_ref"].(map[string]any)
	if carry["actor"] != a["principal"] || carry["from_use_receipt_hash"] != a["checkpoint_use_receipt_hash"] || Hash(carry["from_epoch"]) != Hash(a["previous_epoch"]) || Hash(carry["to_epoch"]) != Hash(a["epoch"]) || carry["new_upload_key"] != use["storage_key"] || ref["id"] != a["checkpoint_artifact"] || ref["content_hash"] != a["checkpoint_hash"] {
		return Fail(409, "GATE_FAILED", "required activation carry changed")
	}
	var state string
	var restored int
	var epoch int64
	var key, mh string
	if err = tx.QueryRow(`SELECT state,restore_fenced,runtime_epoch,dispatch_key,manifest_hash FROM client_queue_fences WHERE project=? AND generation=? AND task_id=? AND run_id=? AND session_id=?`, project, a["generation"], a["task"], run["id"], a["session_id"]).Scan(&state, &restored, &epoch, &key, &mh); err != nil {
		return err
	}
	if restored != 0 || state == "CANCEL_FENCED" || state == "RECONCILING" || Hash(epoch) != Hash(a["epoch"]) || key != a["dispatch_key"] || mh != a["manifest_hash"] {
		return Fail(409, "GATE_FAILED", "required activation queue fenced")
	}
	return nil
}

func (c *RuntimeCoordinator) unstartedPauseActivation(tx *sql.Tx, project, runID string, epoch any) (Object, Object, error) {
	ok, err := pauseInstalled(tx)
	if err != nil || !ok {
		return nil, nil, err
	}
	rows, err := configurationBackupRows(tx, `SELECT * FROM runtime_checkpoint_activations WHERE project=? AND run=? AND epoch=?`, project, runID, epoch)
	if err != nil || len(rows) == 0 {
		return nil, nil, err
	}
	a := rows[0]
	intent, err := pauseIntent(tx, project, runID, a["previous_epoch"])
	if err != nil {
		return nil, nil, err
	}
	if intent == nil || intent["state"] != "RESUME_PREPARED" {
		return nil, nil, nil
	}
	run, err := load(tx, project, "Run", runID)
	if err != nil {
		return nil, nil, err
	}
	if Hash(run["lease_epoch"]) != Hash(epoch) || run["status"] != "QUEUED" {
		return nil, nil, nil
	}
	d, err := runtimeDispatch(tx, project, runID, epoch)
	if err != nil {
		return nil, nil, err
	}
	if d["state"] != "PREPARED" || d["worker"] != "" || d["journal_locator"] != "" || Hash(d["identity"]) != Hash(Object{}) || d["dispatch_key"] != a["dispatch_key"] || d["manifest_hash"] != a["manifest_hash"] {
		return nil, nil, nil
	}
	if !filepath.IsLocal(Str(d, "dispatch_key")) {
		return nil, nil, Fail(409, "GATE_FAILED", "invalid prepared pause locator")
	}
	if _, e := os.Lstat(filepath.Join(c.config.DataRoot, "runtime-dispatches", Str(d, "dispatch_key"))); e == nil {
		return nil, nil, nil
	} else if !os.IsNotExist(e) {
		return nil, nil, e
	}
	var effects int
	if err = tx.QueryRow(`SELECT count(*) FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.epoch')=?`, project, runID, epoch).Scan(&effects); err != nil {
		return nil, nil, err
	}
	if effects != 0 {
		return nil, nil, nil
	}
	var fence string
	var fenced int
	if err = tx.QueryRow(`SELECT state,restore_fenced FROM client_queue_fences WHERE generation=? AND runtime_epoch=? AND dispatch_key=? AND manifest_hash=?`, a["generation"], epoch, a["dispatch_key"], a["manifest_hash"]).Scan(&fence, &fenced); err != nil {
		return nil, nil, err
	}
	if fence != "OPEN" || fenced != 0 {
		return nil, nil, nil
	}
	task, err := load(tx, project, "Task", Str(run, "task_id"))
	if err != nil {
		return nil, nil, err
	}
	if task["active_run_id"] != runID || task["status"] != "RUNNING" {
		return nil, nil, nil
	}
	return a, run, nil
}

func (c *RuntimeCoordinator) isUnstartedPauseActivation(ctx context.Context, project, run string, epoch any) (bool, error) {
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return false, err
	}
	defer tx.Rollback()
	a, _, err := c.unstartedPauseActivation(tx, project, run, epoch)
	return a != nil, err
}

func (c *RuntimeCoordinator) recoverPreparedPauseLease(tx *sql.Tx, route RuntimeCoordinatorRoute) (Object, string, error) {
	rows, err := configurationBackupRows(tx, `SELECT a.run,a.epoch FROM runtime_checkpoint_activations a JOIN runtime_pause_intents p ON p.project=a.project AND p.pause_id=a.pause_id JOIN domain_objects r ON r.project=a.project AND r.kind='Run' AND r.id=a.run WHERE a.project=? AND p.runtime=? AND p.state='RESUME_PREPARED' AND json_extract(r.body,'$.executor_principal_id')=?`, route.ProjectID, route.RuntimeID, route.ExecutorID)
	if err != nil {
		return nil, "", err
	}
	for _, row := range rows {
		a, run, err := c.unstartedPauseActivation(tx, route.ProjectID, Str(row, "run"), row["epoch"])
		if err != nil {
			return nil, "", err
		}
		if a == nil {
			continue
		}
		d, err := runtimeDispatch(tx, route.ProjectID, Str(run, "id"), run["lease_epoch"])
		if err != nil {
			return nil, "", err
		}
		if err = c.service.pauseActivationGate(tx, route.ProjectID, run, d); err != nil {
			return nil, "", err
		}
		task, err := load(tx, route.ProjectID, "Task", Str(run, "task_id"))
		if err != nil {
			return nil, "", err
		}
		if err = c.sessionTaskRoute(tx, route.ProjectID, task, route.RuntimeID); err != nil {
			return nil, "", err
		}
		if _, err = c.service.currentDispatchAdmission(tx, route.ProjectID, task, run, d, "resume-prepared"); err != nil {
			return nil, "", err
		}
		lease := ID() + ID()
		run["lease_token_hash"], run["lease_expires_at"] = Digest([]byte(lease)), time.Now().UTC().Add(90*time.Second).Format(time.RFC3339Nano)
		if err = bump(run); err != nil {
			return nil, "", err
		}
		if err = c.service.put(tx, "Run", run); err != nil {
			return nil, "", err
		}
		intent, err := pauseIntent(tx, route.ProjectID, Str(run, "id"), a["previous_epoch"])
		if err != nil {
			return nil, "", err
		}
		if err = appendPauseReceipt(tx, intent, "PREPARED_LEASE_REPLACED", Object{"epoch": run["lease_epoch"], "dispatch_key": d["dispatch_key"], "run_revision": run["revision"], "reason": "exact unstarted activation, no journal or effects"}); err != nil {
			return nil, "", err
		}
		return run, lease, nil
	}
	return nil, "", nil
}
