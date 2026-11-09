package domain

import (
	"context"
	"database/sql"
	"time"
)

// RecoverExpiredRuns retains ownership when the side effect outcome is unknown.
// It neither dispatches nor creates another Run. A worker must reconcile first.
func (s *Service) RecoverExpiredRuns(ctx context.Context, token, project string) ([]Object, error) {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		return nil, e
	}
	if !p.HasRole("SCHEDULER") || !p.Allowed(project, "", "", false) {
		return nil, Fail(403, "FORBIDDEN", "current scheduler authority required")
	}
	rows, e := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.status') IN ('QUEUED','STARTING','RUNNING','CANCEL_REQUESTED')", project)
	if e != nil {
		return nil, e
	}
	runs := []Object{}
	for rows.Next() {
		var raw string
		if e = rows.Scan(&raw); e != nil {
			rows.Close()
			return nil, e
		}
		r, e := Decode([]byte(raw))
		if e != nil {
			rows.Close()
			return nil, e
		}
		expiry, e := time.Parse(time.RFC3339Nano, Str(r, "lease_expires_at"))
		if e != nil {
			rows.Close()
			return nil, e
		}
		if !time.Now().Before(expiry) {
			runs = append(runs, r)
		}
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	for _, r := range runs {
		r["status"] = "RECONCILING"
		if e = bump(r); e != nil {
			return nil, e
		}
		if e = s.put(tx, "Run", r); e != nil {
			return nil, e
		}
		if e = s.event(tx, project, "Run", r, p.ID, ID(), "RUN_CHANGED"); e != nil {
			return nil, e
		}
	}
	return runs, tx.Commit()
}

func (s *Service) taskFailed(tx *sql.Tx, project string, t Object, reason string) error {
	n, e := load(tx, project, "NoProgressRecord", Str(t, "no_progress_record_id"))
	if e != nil {
		return e
	}
	if _, e = tx.Exec("INSERT INTO orchestration_failures(project,key_hash,reason_hash,count) VALUES(?,?,?,1) ON CONFLICT(project,key_hash,reason_hash) DO UPDATE SET count=count+1", project, n["key_hash"], Digest([]byte(reason))); e != nil {
		return e
	}
	var count int64
	if e = tx.QueryRow("SELECT count FROM orchestration_failures WHERE project=? AND key_hash=? AND reason_hash=?", project, n["key_hash"], Digest([]byte(reason))).Scan(&count); e != nil {
		return e
	}
	iterations, _ := Num(n, "no_progress_iterations")
	iterations++
	n["same_failure_count"] = count
	n["no_progress_iterations"] = iterations
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return e
	}
	policy, e := load(tx, project, "RunPolicy", Str(profile, "run_policy_id"))
	if e != nil {
		return e
	}
	retryLimit, _ := Num(policy, "same_failure_retry_limit")
	iterationLimit, _ := Num(policy, "no_progress_iteration_limit")
	t["status"] = "FAILED"
	if count > retryLimit || iterations >= iterationLimit {
		n["status"] = "DEFERRED_NO_PROGRESS"
		t["status"] = "DEFERRED_NO_PROGRESS"
	}
	if e = bump(n); e != nil {
		return e
	}
	return s.put(tx, "NoProgressRecord", n)
}

func (s *Service) runtimeTaskTerminal(tx *sql.Tx, p Principal, project string, r Object, cid string) error {
	if r["status"] != "FAILED" && r["status"] != "CANCELLED" {
		return nil
	}
	t, e := load(tx, project, "Task", Str(r, "task_id"))
	if e != nil {
		return e
	}
	if t["task_type"] == "runtime_qualification" || (t["status"] != "RUNNING" && t["status"] != "BLOCKED") {
		return nil
	}
	if t["active_run_id"] != r["id"] {
		return Fail(409, "STATE_CONFLICT", "old run cannot change task")
	}
	if r["status"] == "FAILED" {
		if e = s.taskFailed(tx, project, t, "runtime execution failed"); e != nil {
			return e
		}
	} else {
		t["status"] = "CANCELLED"
		var action string
		e = tx.QueryRow("SELECT action FROM orchestration_task_controls WHERE project=? AND task=?", project, t["id"]).Scan(&action)
		if e != nil && e != sql.ErrNoRows {
			return e
		}
		if action == "PAUSE" {
			t["status"] = "BLOCKED"
		}
	}
	if e = bump(t); e != nil {
		return e
	}
	if e = s.put(tx, "Task", t); e != nil {
		return e
	}
	return s.event(tx, project, "Task", t, p.ID, cid, "TASK_CHANGED")
}
