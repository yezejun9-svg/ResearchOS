package domain

import (
	"context"
	"database/sql"
	"encoding/json"
)

func (s *Service) cancelGoalQueueTasks(tx *sql.Tx, project, goal string) error {
	rows, err := tx.Query(`SELECT body FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=?`, project, goal)
	if err != nil {
		return err
	}
	tasks := []Object{}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return err
		}
		task, e := queueObject(raw)
		if e != nil {
			rows.Close()
			return e
		}
		tasks = append(tasks, task)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, task := range tasks {
		if err = fenceClientTask(tx, project, Str(task, "id")); err != nil {
			return err
		}
		if task["status"] != "CANCELLED" && task["status"] != "ACCEPTED" {
			if _, err = s.controlTask(tx, Principal{ID: "goal-control"}, project, task, Object{"action": "CANCEL", "reason": "Goal cancelled"}, ID()); err != nil {
				return err
			}
		}
	}
	return nil
}

func fenceClientTask(tx *sql.Tx, project, task string) error {
	if err := cancelTaskPauses(tx, project, task); err != nil {
		return err
	}
	installed, err := clientQueueInstalled(tx)
	if err != nil || !installed {
		return err
	}
	var session string
	err = tx.QueryRow(`SELECT id FROM client_sessions WHERE project_id=? AND task_id=?`, project, task).Scan(&session)
	if err == sql.ErrNoRows {
		return nil
	}
	if err != nil {
		return err
	}
	if err = ensureClientQueue(tx, project, session, task); err != nil {
		return err
	}
	var generation string
	if err = tx.QueryRow(`SELECT generation FROM client_queue_fences WHERE project=? AND task_id=?`, project, task).Scan(&generation); err != nil {
		return err
	}
	if _, err = tx.Exec(`UPDATE client_queue_fences SET state='CANCEL_FENCED',revision=revision+1 WHERE generation=? AND state<>'SEALED'`, generation); err != nil {
		return err
	}
	rows, err := tx.Query(`SELECT command_id,state,last_receipt_id FROM client_command_queue WHERE generation=? AND state IN ('ENQUEUED','SENDING','SDK_ACCEPTED')`, generation)
	if err != nil {
		return err
	}
	type entry struct {
		id, state string
		prior     sql.NullString
	}
	entries := []entry{}
	for rows.Next() {
		var item entry
		if err = rows.Scan(&item.id, &item.state, &item.prior); err != nil {
			rows.Close()
			return err
		}
		entries = append(entries, item)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, item := range entries {
		next := "DROP_REQUESTED"
		if item.state == "ENQUEUED" {
			next = "DROPPED"
		}
		receipt := ID()
		var previous any
		if item.prior.Valid {
			previous = item.prior.String
		}
		if err = appendClientReceipt(tx, project, generation, item.id, "CANCEL_FENCE", receipt, Object{"task_id": task, "from": item.state, "to": next}, previous); err != nil {
			return err
		}
		if _, err = tx.Exec(`UPDATE client_command_queue SET state=?,revision=revision+1,last_receipt_id=? WHERE generation=? AND command_id=?`, next, receipt, generation, item.id); err != nil {
			return err
		}
	}
	_, err = tx.Exec(`UPDATE client_sessions SET resume_requires_explicit_user=1 WHERE id=?`, session)
	return err
}

func (s *ClientService) cancelClientTarget(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow, target string) (*Response, error) {
	p, err := clientPrincipal(ctx, tx, principal, sess.project, true)
	if err != nil {
		return clientFault(env, err)
	}
	var goal, task sql.NullString
	if err = tx.QueryRow(`SELECT goal_id,task_id FROM client_sessions WHERE id=? AND project_id=?`, sess.sessionID, sess.project).Scan(&goal, &task); err != nil {
		return nil, err
	}
	ids := []string{}
	if target == goal.String && goal.Valid {
		rows, e := tx.Query(`SELECT id FROM domain_objects WHERE project=? AND kind='Task' AND json_extract(body,'$.goal_id')=? ORDER BY id`, sess.project, target)
		if e != nil {
			return nil, e
		}
		for rows.Next() {
			var id string
			if e = rows.Scan(&id); e != nil {
				rows.Close()
				return nil, e
			}
			ids = append(ids, id)
		}
		e = rows.Err()
		rows.Close()
		if e != nil {
			return nil, e
		}
		g, e := load(tx, sess.project, "Goal", target)
		if e != nil {
			return nil, e
		}
		if g["status"] != "CANCELLED" {
			g["status"] = "CANCELLED"
			if e = bump(g); e != nil {
				return nil, e
			}
			if e = s.Domain.put(tx, "Goal", g); e != nil {
				return nil, e
			}
		}
	} else if target == sess.runID && target != "" {
		r, e := load(tx, sess.project, "Run", target)
		if e != nil {
			return nil, e
		}
		taskID := Str(r, "task_id")
		if task.Valid && task.String != taskID {
			return NewTypedRejection(env, "NOT_FOUND", "run no longer belongs to session task"), nil
		}
		ids = append(ids, taskID)
	} else {
		return NewTypedRejection(env, "NOT_FOUND", "cancel target is not this session's Goal or Run"), nil
	}
	if len(ids) == 0 {
		return NewTypedRejection(env, "NOT_FOUND", "cancel target has no owned tasks"), nil
	}
	for _, id := range ids {
		t, e := load(tx, sess.project, "Task", id)
		if e != nil {
			return nil, e
		}
		if e = fenceClientTask(tx, sess.project, id); e != nil {
			return nil, e
		}
		if t["status"] != "CANCELLED" && t["status"] != "ACCEPTED" {
			if _, e = s.Domain.controlTask(tx, p, sess.project, t, Object{"action": "CANCEL", "reason": "Authenticated client cancellation"}, deref(env.CommandID)); e != nil {
				return clientFault(env, e)
			}
		}
		if runID := Str(t, "active_run_id"); runID != "" {
			r, e := load(tx, sess.project, "Run", runID)
			if e != nil {
				return nil, e
			}
			if r["status"] == "CANCEL_REQUESTED" {
				if e = s.journal(ctx, tx, env, sess, "RUN_STATE", Object{"run_id": runID, "status": r["status"], "revision": r["revision"], "cancel_requested_at": r["cancel_requested_at"], "cancel_confirmed_at": r["cancel_confirmed_at"], "settled_at": r["runtime_settled_at"], "children_stopped": r["children_stopped"], "queue_empty": r["queue_empty"]}); e != nil {
					return nil, e
				}
				sess.revision++
				sess.watermark++
			}
		}
	}
	hash, err := env.ContentHash()
	if err != nil {
		return nil, err
	}
	control := "ctrl-" + deref(env.CommandID)
	if _, err = tx.Exec(`INSERT INTO client_control_requests(principal,project,command_id,session_id,control_request_id,request_hash,target_id,task_ids,state,created_at) VALUES(?,?,?,?,?,?,?,?,'REQUESTED',?)`, principal, sess.project, deref(env.CommandID), sess.sessionID, control, hash, target, string(Bytes(ids)), Now()); err != nil {
		return nil, err
	}
	result, err := s.finalizeClientCancel(ctx, tx, env, principal, sess)
	if err != nil {
		return nil, err
	}
	if result != nil {
		return result, nil
	}
	return &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("ACKNOWLEDGED"), SessionID: env.SessionID, Revision: revPtr(sess.revision), Result: Object{"accepted_at": Now(), "operation_id": "op-" + deref(env.CommandID), "after_sequence": sess.watermark, "related_resource_ref": nil}}, nil
}

// The original ACK is retained in the control row. Only the same command hash
// can advance its replay result to COMPLETED after canonical settlement.
func (s *ClientService) finalizeClientCancel(ctx context.Context, tx *sql.Tx, env *Envelope, principal string, sess *clientSessionRow) (*Response, error) {
	var tasks, target, control, state string
	err := tx.QueryRow(`SELECT task_ids,target_id,control_request_id,state FROM client_control_requests WHERE principal=? AND project=? AND command_id=?`, principal, deref(env.ProjectID), deref(env.CommandID)).Scan(&tasks, &target, &control, &state)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	if state == "CONFIRMED" || state == "RECONCILING" {
		return nil, nil
	}
	var ids []string
	if err = json.Unmarshal([]byte(tasks), &ids); err != nil {
		return nil, err
	}
	for _, id := range ids {
		task, e := load(tx, deref(env.ProjectID), "Task", id)
		if e != nil {
			return nil, e
		}
		if run := Str(task, "active_run_id"); run != "" {
			r, e := load(tx, deref(env.ProjectID), "Run", run)
			if e != nil {
				return nil, e
			}
			if !runTerminal(r) || r["children_stopped"] != true || r["queue_empty"] != true || effectsReconciled(tx, deref(env.ProjectID), run) != nil || clientQueueSettled(tx, deref(env.ProjectID), run) != nil {
				return nil, nil
			}
			if r["status"] == "CANCELLED" && Str(r, "cancel_confirmed_at") == "" {
				return nil, nil
			}
		} else {
			var dispatches int
			if e = tx.QueryRow(`SELECT (SELECT count(*) FROM runtime_dispatches WHERE project=? AND json_extract(manifest,'$.task_id')=?)+(SELECT count(*) FROM domain_objects WHERE kind='Run' AND project=? AND json_extract(body,'$.task_id')=?)`, deref(env.ProjectID), id, deref(env.ProjectID), id).Scan(&dispatches); e != nil {
				return nil, e
			}
			if dispatches != 0 || task["status"] != "CANCELLED" {
				return nil, nil
			}
			var pending int
			if e = tx.QueryRow(`SELECT count(*) FROM client_command_queue WHERE project=? AND task_id=? AND state NOT IN ('CONSUMED','DROPPED')`, deref(env.ProjectID), id).Scan(&pending); e != nil {
				return nil, e
			}
			var restored int
			if e = tx.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE project=? AND task_id=? AND restore_fenced<>0`, deref(env.ProjectID), id).Scan(&restored); e != nil {
				return nil, e
			}
			if pending != 0 || restored != 0 {
				return nil, nil
			}
			if _, e = tx.Exec(`UPDATE client_queue_fences SET sealed_through=accepted_through WHERE project=? AND task_id=? AND state='CANCEL_FENCED' AND restore_fenced=0`, deref(env.ProjectID), id); e != nil {
				return nil, e
			}
		}
	}
	if sess == nil {
		sess, err = loadClientSession(ctx, tx, deref(env.SessionID), deref(env.ProjectID))
		if err != nil {
			return nil, err
		}
	}
	// Hide the pending ID only in the same transaction as the final receipt.
	if _, err = tx.Exec(`UPDATE client_control_requests SET state='CONFIRMED' WHERE principal=? AND project=? AND command_id=?`, principal, sess.project, deref(env.CommandID)); err != nil {
		return nil, err
	}
	snap, err := BuildSessionSnapshot(ctx, tx, s.Doc, sess.project, sess.sessionID)
	if err != nil {
		return nil, err
	}
	response := &Response{ProtocolVersion: strptr(ProtocolV2), CommandID: env.CommandID, Method: env.Method, Status: strptr("COMPLETED"), SessionID: env.SessionID, Revision: revPtr(sess.revision), Result: Object{"action": "CANCEL", "target_id": target, "control_request_id": control, "settled": true, "children_stopped": true, "queue_empty": true, "snapshot": snap}}
	_, err = tx.Exec(`UPDATE client_control_requests SET final_response=? WHERE principal=? AND project=? AND command_id=?`, string(Bytes(response)), principal, sess.project, deref(env.CommandID))
	return response, err
}
