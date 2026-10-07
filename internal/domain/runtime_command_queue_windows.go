//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	rt "researchos.local/research-os/adapters/runtime"
	"strings"
	"sync"
	"time"
)

func bindClientRunQueue(tx *sql.Tx, project string, run Object) (bool, error) {
	installed, err := clientQueueInstalled(tx)
	if err != nil || !installed {
		return false, err
	}
	var session string
	err = tx.QueryRow(`SELECT id FROM client_sessions WHERE project_id=? AND task_id=?`, project, run["task_id"]).Scan(&session)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if err = ensureClientQueue(tx, project, session, Str(run, "task_id")); err != nil {
		return false, err
	}
	d, err := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
	if err != nil {
		return false, err
	}
	result, err := tx.Exec(`UPDATE client_queue_fences SET run_id=?,runtime_epoch=?,dispatch_key=?,manifest_hash=?,revision=revision+1 WHERE project=? AND task_id=? AND state='OPEN' AND restore_fenced=0 AND (run_id IS NULL OR (run_id=? AND runtime_epoch=?))`, run["id"], run["lease_epoch"], d["dispatch_key"], d["manifest_hash"], project, run["task_id"], run["id"], run["lease_epoch"])
	if err != nil {
		return false, err
	}
	n, err := result.RowsAffected()
	if err != nil {
		return false, err
	}
	if n != 1 {
		return false, Fail(409, "STATE_CONFLICT", "queue generation is fenced")
	}
	return true, nil
}

func unknownClientRunQueue(tx *sql.Tx, project, run, reason string) error {
	rows, err := tx.Query(`SELECT generation,command_id,state,last_receipt_id FROM client_command_queue WHERE generation IN (SELECT generation FROM client_queue_fences WHERE project=? AND run_id=?) AND state IN ('SENDING','SDK_ACCEPTED','DROP_REQUESTED')`, project, run)
	if err != nil {
		return err
	}
	entries := []Object{}
	for rows.Next() {
		var generation, command, state string
		var prior sql.NullString
		if err = rows.Scan(&generation, &command, &state, &prior); err != nil {
			rows.Close()
			return err
		}
		var previous any
		if prior.Valid {
			previous = prior.String
		}
		entries = append(entries, Object{"generation": generation, "command": command, "state": state, "previous": previous})
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, entry := range entries {
		id := ID()
		if err = appendClientReceipt(tx, project, Str(entry, "generation"), Str(entry, "command"), "TRANSPORT_UNKNOWN", id, Object{"prior_state": entry["state"], "reason": reason}, entry["previous"]); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE client_command_queue SET state='UNKNOWN',revision=revision+1,last_receipt_id=? WHERE generation=? AND command_id=?`, id, entry["generation"], entry["command"]); err != nil {
			return err
		}
	}
	_, err = tx.Exec(`UPDATE client_queue_fences SET state=CASE WHEN state='CANCEL_FENCED' THEN state ELSE 'RECONCILING' END,revision=revision+1 WHERE project=? AND run_id=? AND state<>'SEALED'`, project, run)
	return err
}

func (c *RuntimeCoordinator) recoverClientQueue(ctx context.Context, project, run string, epoch int64, j rt.BridgeJournal) error {
	if !j.QueueRequired {
		return nil
	}
	binding, _, _, err := c.queueBinding(ctx, project, run, j)
	if err != nil {
		return err
	}
	if Hash(binding["runtime_epoch"]) != Hash(epoch) {
		return Fail(409, "GATE_FAILED", "old queue recovery epoch")
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	dispatch, err := runtimeDispatch(tx, project, run, epoch)
	if err != nil {
		return err
	}
	if Hash(dispatch["identity"]) != Hash(binding["process_identity"]) || dispatch["manifest_hash"] != j.ManifestHash || dispatch["dispatch_key"] != j.DispatchKey {
		return Fail(409, "GATE_FAILED", "foreign recovered worker")
	}
	var last int64
	initialized := false
	for _, frame := range j.CommandReceipts {
		if frame.Sequence <= last || frame.Sequence > j.Frames {
			return Fail(409, "GATE_FAILED", "recovery command sequence")
		}
		last = frame.Sequence
		payload, e := Decode(frame.Payload)
		if e != nil {
			return e
		}
		for key, value := range binding {
			if Hash(value) != Hash(payload[key]) {
				return Fail(409, "GATE_FAILED", "recovered command binding")
			}
		}
		if frame.Type == "command.accepted" && payload["initialized"] == true {
			initialized = true
		} else if !initialized {
			return Fail(409, "GATE_FAILED", "recovered command before initialization")
		}
		id := fmt.Sprintf("%s:%d", j.DispatchKey, frame.Sequence)
		var old string
		e = tx.QueryRow(`SELECT body_hash FROM client_control_receipts WHERE receipt_id=?`, id).Scan(&old)
		if e == nil {
			if old != Digest(Bytes(payload)) {
				return Fail(409, "GATE_FAILED", "conflicting recovered receipt")
			}
			continue
		}
		if e != sql.ErrNoRows {
			return e
		}
		command := Str(payload, "command_id")
		var previous any
		if command != "" {
			var state, message, hash string
			var seq int64
			var prior sql.NullString
			e = tx.QueryRow(`SELECT state,message_id,content_hash,queue_sequence,last_receipt_id FROM client_command_queue WHERE generation=? AND command_id=?`, binding["queue_generation"], command).Scan(&state, &message, &hash, &seq, &prior)
			if e != nil {
				return e
			}
			if message != payload["message_id"] || hash != payload["content_hash"] || Hash(seq) != Hash(payload["queue_sequence"]) {
				return Fail(409, "GATE_FAILED", "recovered command content")
			}
			if prior.Valid {
				previous = prior.String
			}
			next := state
			if frame.Type == "command.consumed" && state != "DROPPED" {
				next = "CONSUMED"
			}
			if frame.Type == "command.cleared" && state != "CONSUMED" && j.Cancelled && j.QueueCancelIdle && j.Receipt.Stopped {
				next = "DROPPED"
			}
			if frame.Type == "command.accepted" && state != "CONSUMED" && state != "DROPPED" {
				next = "UNKNOWN"
			}
			if _, e = tx.Exec(`UPDATE client_command_queue SET state=?,revision=revision+1,last_receipt_id=? WHERE generation=? AND command_id=?`, next, id, binding["queue_generation"], command); e != nil {
				return e
			}
		}
		if e = appendClientReceipt(tx, project, Str(binding, "queue_generation"), command, frame.Type, id, payload, previous); e != nil {
			return e
		}
	}
	var pending int
	if err = tx.QueryRow(`SELECT count(*) FROM client_command_queue WHERE generation=? AND state NOT IN ('CONSUMED','DROPPED')`, binding["queue_generation"]).Scan(&pending); err != nil {
		return err
	}
	if pending == 0 && j.Receipt.Stopped && (j.QueueSealed || j.Cancelled && j.QueueCancelIdle) {
		state := "SEALED"
		if j.Cancelled {
			state = "CANCEL_FENCED"
		}
		// A restored future remains fenced even with old snapshot receipts.
		if _, err = tx.Exec(`UPDATE client_queue_fences SET state=?,sealed_through=accepted_through,revision=revision+1 WHERE generation=? AND restore_fenced=0 AND (state<>? OR sealed_through<>accepted_through)`, state, binding["queue_generation"], state); err != nil {
			return err
		}
	}
	return tx.Commit()
}

func (c *RuntimeCoordinator) queueBinding(ctx context.Context, project, run string, j rt.BridgeJournal) (Object, string, int64, error) {
	var generation, state, session, task string
	var epoch, through int64
	err := c.service.DB.QueryRowContext(ctx, `SELECT generation,state,session_id,task_id,runtime_epoch,accepted_through FROM client_queue_fences WHERE project=? AND run_id=?`, project, run).Scan(&generation, &state, &session, &task, &epoch, &through)
	if err != nil {
		return nil, "", 0, err
	}
	return Object{"project_id": project, "session_id": session, "task_id": task, "run_id": run, "runtime_epoch": epoch, "queue_generation": generation, "dispatch_key": j.DispatchKey, "manifest_hash": j.ManifestHash, "process_identity": runtimeNativeIdentity(j.Identity)}, state, through, nil
}

func (c *RuntimeCoordinator) deliverClientQueue(ctx context.Context, route RuntimeCoordinatorRoute, run string, bridge *rt.Bridge, initialized *time.Time, cancelSent *time.Time) error {
	j := bridge.Read()
	if !j.QueueRequired || !j.ContextReady {
		return nil
	}
	binding, state, through, err := c.queueBinding(ctx, route.ProjectID, run, j)
	if err != nil {
		return err
	}
	if initialized.IsZero() {
		if err = bridge.Control(ctx, Object{"type": "command.deliver", "binding": binding, "initialize": true, "command": nil}); err != nil {
			return err
		}
		*initialized = time.Now()
		return nil
	}
	if j.QueueInitSequence == 0 || j.Acknowledged < j.QueueInitSequence {
		if time.Since(*initialized) > 5*time.Second {
			return Fail(409, "GATE_FAILED", "queue initialization ACK timeout")
		}
		return nil
	}
	if state == "CANCEL_FENCED" {
		if cancelSent.IsZero() {
			*cancelSent = time.Now()
			return bridge.Control(ctx, Object{"type": "command.clear_abort", "binding": binding})
		}
		if time.Since(*cancelSent) > 2*time.Second {
			bridge.Cancel("canonical cancellation process fallback")
		}
		return nil
	}
	if state == "RECONCILING" {
		return Fail(409, "STATE_CONFLICT", "queue is reconciling")
	}
	if state == "SEALED" {
		return nil
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	rows, err := tx.Query(`SELECT command_id,message_id,queue_sequence,content,content_hash,delivery FROM client_command_queue WHERE generation=? AND state='ENQUEUED' ORDER BY queue_sequence`, binding["queue_generation"])
	if err != nil {
		return err
	}
	commands := []Object{}
	for rows.Next() {
		var id, message, content, hash, delivery string
		var seq int64
		if err = rows.Scan(&id, &message, &seq, &content, &hash, &delivery); err != nil {
			rows.Close()
			return err
		}
		commands = append(commands, Object{"command_id": id, "message_id": message, "queue_sequence": seq, "content": content, "content_hash": hash, "delivery": delivery})
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, cmd := range commands {
		id := ID()
		if err = appendClientReceipt(tx, route.ProjectID, Str(binding, "queue_generation"), Str(cmd, "command_id"), "SENDING", id, Merge(Merge(Object{}, binding), Object{"command": cmd}), nil); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE client_command_queue SET state='SENDING',revision=revision+1,last_receipt_id=? WHERE generation=? AND command_id=? AND state='ENQUEUED'`, id, binding["queue_generation"], cmd["command_id"]); err != nil {
			return err
		}
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	for _, cmd := range commands {
		if err = bridge.Control(ctx, Object{"type": "command.deliver", "binding": binding, "command": cmd}); err != nil {
			return err
		}
	}
	if state == "SEALING" {
		return bridge.Control(ctx, Object{"type": "command.prepare_seal", "binding": binding, "through": through})
	}
	return nil
}

func (c *RuntimeCoordinator) ingestClientQueueFrame(ctx context.Context, route RuntimeCoordinatorRoute, run string, bridge *rt.Bridge, frame rt.BridgeFrame) error {
	payload, err := Decode(frame.Payload)
	if err != nil {
		return err
	}
	binding, _, _, err := c.queueBinding(ctx, route.ProjectID, run, bridge.Read())
	if err != nil {
		return err
	}
	for key, value := range binding {
		if Hash(payload[key]) != Hash(value) {
			return Fail(409, "GATE_FAILED", "foreign command receipt binding")
		}
	}
	tx, err := c.service.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var fence string
	var through int64
	if err = tx.QueryRow(`SELECT state,accepted_through FROM client_queue_fences WHERE generation=?`, binding["queue_generation"]).Scan(&fence, &through); err != nil {
		return err
	}
	receiptID := fmt.Sprintf("%s:%d", bridge.Read().DispatchKey, frame.Sequence)
	command := Str(payload, "command_id")
	var previous any
	if command != "" {
		var message, hash, state string
		var seq int64
		var prior sql.NullString
		err = tx.QueryRow(`SELECT message_id,content_hash,state,queue_sequence,last_receipt_id FROM client_command_queue WHERE generation=? AND command_id=?`, binding["queue_generation"], command).Scan(&message, &hash, &state, &seq, &prior)
		if err != nil {
			return err
		}
		if payload["message_id"] != message || payload["content_hash"] != hash || Hash(payload["queue_sequence"]) != Hash(seq) {
			return Fail(409, "GATE_FAILED", "command receipt content mismatch")
		}
		if prior.Valid {
			previous = prior.String
		}
		next := state
		switch frame.Type {
		case "command.accepted":
			if state == "SENDING" || state == "UNKNOWN" {
				next = "SDK_ACCEPTED"
			} else if state != "SDK_ACCEPTED" && state != "CONSUMED" && state != "DROP_REQUESTED" {
				return Fail(409, "GATE_FAILED", "unexpected SDK acceptance")
			}
		case "command.consumed":
			if state == "SENDING" || state == "SDK_ACCEPTED" || state == "UNKNOWN" || state == "DROP_REQUESTED" {
				next = "CONSUMED"
			} else if state != "CONSUMED" {
				return Fail(409, "GATE_FAILED", "unexpected SDK consumption")
			}
		case "command.cleared":
			if fence != "CANCEL_FENCED" || state == "CONSUMED" {
				return Fail(409, "GATE_FAILED", "invalid clear receipt")
			}
			next = "DROP_REQUESTED"
		default:
			return Fail(409, "GATE_FAILED", "unexpected per-command receipt")
		}
		if err = appendClientReceipt(tx, route.ProjectID, Str(binding, "queue_generation"), command, frame.Type, receiptID, payload, previous); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE client_command_queue SET state=?,revision=revision+1,last_receipt_id=? WHERE generation=? AND command_id=?`, next, receiptID, binding["queue_generation"], command); err != nil {
			return err
		}
	} else {
		if err = appendClientReceipt(tx, route.ProjectID, Str(binding, "queue_generation"), "", frame.Type, receiptID, payload, nil); err != nil {
			return err
		}
	}
	action := ""
	if frame.Type == "command.idle" || frame.Type == "command.abort_observed" && fence == "CANCEL_FENCED" {
		if payload["sdk_idle"] != true || payload["sdk_queue_empty"] != true {
			return Fail(409, "GATE_FAILED", "SDK idle proof missing")
		}
		if fence == "CANCEL_FENCED" {
			if frame.Type == "command.idle" && payload["cancelled"] != true || !bridge.Read().QueueCancelIdle {
				return tx.Commit()
			}
			// Agent idle and the awaited abort completion can arrive in either
			// order. Do not kill the worker before both original SDK facts commit.
			settled, e := clientQueueCancelFactsReady(tx, binding)
			if e != nil {
				return e
			}
			if !settled {
				return tx.Commit()
			}
			// Only entries with exact clear evidence can be dropped; UNKNOWN remains.
			if _, err = tx.Exec(`UPDATE client_command_queue SET state='DROPPED',revision=revision+1 WHERE generation=? AND state='DROP_REQUESTED' AND last_receipt_id IN (SELECT receipt_id FROM client_control_receipts WHERE kind='command.cleared')`, binding["queue_generation"]); err != nil {
				return err
			}
			var pending int
			if err = tx.QueryRow(`SELECT count(*) FROM client_command_queue WHERE generation=? AND state NOT IN ('CONSUMED','DROPPED')`, binding["queue_generation"]).Scan(&pending); err != nil {
				return err
			}
			if pending == 0 {
				_, err = tx.Exec(`UPDATE client_queue_fences SET sealed_through=accepted_through,revision=revision+1 WHERE generation=?`, binding["queue_generation"])
				action = "cancel"
			}
		} else if fence == "OPEN" {
			_, err = tx.Exec(`UPDATE client_queue_fences SET state='SEALING',revision=revision+1 WHERE generation=? AND state='OPEN'`, binding["queue_generation"])
			action = "prepare"
		} else if fence == "SEALING" && Hash(payload["through"]) == Hash(through) {
			var pending int
			if err = tx.QueryRow(`SELECT count(*) FROM client_command_queue WHERE generation=? AND state NOT IN ('CONSUMED','DROPPED')`, binding["queue_generation"]).Scan(&pending); err != nil {
				return err
			}
			if pending == 0 {
				_, err = tx.Exec(`UPDATE client_queue_fences SET state='SEALED',sealed_through=accepted_through,revision=revision+1 WHERE generation=?`, binding["queue_generation"])
				action = "commit"
			}
		}
	}
	if err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	switch action {
	case "prepare":
		c.boundary("queue_sealing", binding)
		return bridge.Control(ctx, Object{"type": "command.prepare_seal", "binding": binding, "through": through})
	case "commit":
		return bridge.Control(ctx, Object{"type": "command.commit_seal", "binding": binding, "through": through})
	case "cancel":
		bridge.Cancel("SDK clear, abort and idle reconciled")
	}
	return nil
}

// Effects may block on a model/tool. Only this flow owns ACK order; a bounded
// result pump lets the same coordinator receive SDK receipts and send controls.
func (c *RuntimeCoordinator) runCommandBridge(ctx, brokerCtx context.Context, route RuntimeCoordinatorRoute, run, lease string, epoch int64, locator string, bridge *rt.Bridge, mutation *sync.Mutex) error {
	type completion struct {
		seq      int64
		response any
		err      error
	}
	results := make(chan completion, 32)
	ready := map[int64]completion{}
	inflight := 0
	next := int64(1)
	frames := bridge.Frames()
	tick := time.NewTicker(40 * time.Millisecond)
	defer tick.Stop()
	var initialized time.Time
	var cancelSent time.Time
	var deferredError error
	for frames != nil || inflight > 0 {
		select {
		case observation := <-bridge.ModelObservations():
			ids, watermark, err := c.commitModelObservation(ctx, route, run, lease, epoch, observation)
			if err != nil {
				return err
			}
			if err = bridge.CreditModelObservation(ctx, observation, ids, watermark); err != nil {
				return err
			}
		case frame, ok := <-frames:
			if !ok {
				frames = nil
				continue
			}
			if frame.Type == "effect.request" {
				if inflight >= 16 {
					return Fail(409, "GATE_FAILED", "effect concurrency exceeds bound")
				}
				inflight++
				go func(f rt.BridgeFrame) {
					r, e := c.brokerEffect(brokerCtx, route, run, lease, epoch, bridge, f)
					results <- completion{f.Sequence, r, e}
				}(frame)
			} else {
				var response any
				var err error
				if strings.HasPrefix(frame.Type, "command.") {
					err = c.ingestClientQueueFrame(ctx, route, run, bridge, frame)
					if err == nil && frame.Type == "command.accepted" {
						payload, e := Decode(frame.Payload)
						if e != nil {
							return e
						}
						if payload["initialized"] == true {
							response = Object{"sequence": frame.Sequence, "key": "command.initialize", "state": "CONFIRMED", "payload": Object{}}
						}
					}
				}
				if frame.Type == "checkpoint" {
					mutation.Lock()
					response, err = c.checkpoint(ctx, route, run, lease, epoch, locator, bridge, frame)
					mutation.Unlock()
				}
				if err != nil {
					return err
				}
				ready[frame.Sequence] = completion{seq: frame.Sequence, response: response}
			}
		case done := <-results:
			inflight--
			if done.err != nil {
				var fenced int
				if err := c.service.DB.QueryRowContext(ctx, `SELECT count(*) FROM client_queue_fences WHERE project=? AND run_id=? AND state='CANCEL_FENCED'`, route.ProjectID, run).Scan(&fenced); err != nil || fenced != 1 {
					return done.err
				}
				deferredError = done.err
			}
			ready[done.seq] = done
		case <-tick.C:
			if err := c.deliverClientQueue(ctx, route, run, bridge, &initialized, &cancelSent); err != nil {
				return err
			}
		case <-ctx.Done():
			return ctx.Err()
		}
		for {
			done, ok := ready[next]
			if !ok {
				break
			}
			if err := bridge.Acknowledge(ctx, next, done.response); err != nil {
				return err
			}
			if next == bridge.Read().QueueInitSequence && bridge.ModelInitializationDelivered() {
				if err := c.modelInitializationDelivered(ctx, route.ProjectID, run, bridge); err != nil {
					return err
				}
			}
			delete(ready, next)
			next++
		}
	}
	if len(ready) != 0 {
		return Fail(409, "GATE_FAILED", "protocol receipt gap")
	}
	return deferredError
}
