package domain

import (
	"database/sql"
	"time"
)

// Checkpoint recovery rebuilds a session; it is not a qualified native resume.
// Archive the former binding before clearing it so the first heartbeat may bind
// the replacement process while all callbacks using the old lease are fenced.
func (s *Service) rebuildResourceSession(tx *sql.Tx, project, actor, reason string, run Object) (string, error) {
	epoch, e := Num(run, "lease_epoch")
	if e != nil || epoch == 1<<63-1 {
		return "", Fail(409, "STATE_CONFLICT", "lease epoch exhausted")
	}
	history := Object{"kind": "SESSION_REBUILT", "reason": reason, "native_resume": false, "run_id": run["id"], "runtime_id": run["runtime_id"], "previous_external_run_id": run["external_run_id"], "previous_lease_epoch": epoch, "next_lease_epoch": epoch + 1, "checkpoint_artifact_id": run["checkpoint_artifact_id"], "actor": actor, "at": Now()}
	if _, e = tx.Exec("INSERT INTO resource_route_history(id,project,run,body) VALUES(?,?,?,?)", ID(), project, run["id"], string(Bytes(history))); e != nil {
		return "", e
	}
	lease := ID() + ID()
	Merge(run, Object{"external_run_id": nil, "lease_epoch": epoch + 1, "lease_token_hash": Digest([]byte(lease)), "lease_expires_at": time.Now().UTC().Add(90 * time.Second).Format(time.RFC3339Nano), "status": "QUEUED", "heartbeat_at": nil, "children_stopped": nil, "queue_empty": nil, "runtime_settled_at": nil})
	if e = bump(run); e != nil {
		return "", e
	}
	return lease, s.put(tx, "Run", run)
}
