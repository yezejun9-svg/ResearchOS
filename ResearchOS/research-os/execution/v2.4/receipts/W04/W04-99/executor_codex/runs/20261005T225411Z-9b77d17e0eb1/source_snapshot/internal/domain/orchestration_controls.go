package domain

import "database/sql"

func (s *Service) controlTask(tx *sql.Tx, p Principal, project string, t, b Object, cid string) (Object, error) {
	action := Str(b, "action")
	status := Str(t, "status")
	if status == "ACCEPTED" || status == "CANCELLED" || status == "NEEDS_REVALIDATION" || status == "DEFERRED_NO_PROGRESS" {
		return nil, Fail(409, "STATE_CONFLICT", "task cannot be paused or cancelled in this state")
	}
	if _, e := tx.Exec("INSERT INTO orchestration_task_controls(project,task,action,reason,requested_at) VALUES(?,?,?,?,?) ON CONFLICT(project,task) DO UPDATE SET action=excluded.action,reason=excluded.reason,requested_at=excluded.requested_at", project, t["id"], action, b["reason"], Now()); e != nil {
		return nil, e
	}
	unresolved := false
	if id := Str(t, "active_run_id"); id != "" {
		r, e := load(tx, project, "Run", id)
		if e != nil {
			return nil, e
		}
		unresolved = !runTerminal(r)
		if unresolved && r["status"] != "CANCEL_REQUESTED" {
			// Unknown reconciliation is retained; a cancellation request does not prove stopping.
			if r["status"] != "RECONCILING" && r["status"] != "LOST" {
				r["status"] = "CANCEL_REQUESTED"
			}
			r["cancel_requested_at"] = Now()
			if e = bump(r); e != nil {
				return nil, e
			}
			if e = s.put(tx, "Run", r); e != nil {
				return nil, e
			}
			if e = s.event(tx, project, "Run", r, p.ID, cid, "RUN_CHANGED"); e != nil {
				return nil, e
			}
		}
	}
	t["status"] = "BLOCKED"
	if action == "CANCEL" && !unresolved {
		t["status"] = "CANCELLED"
	}
	if e := bump(t); e != nil {
		return nil, e
	}
	return t, s.put(tx, "Task", t)
}
