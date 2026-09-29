package domain

import (
	"database/sql"
	"fmt"
	"time"
)

func binding() Object {
	return Object{"route": "THIN_CORE", "upstream_project_id": nil, "upstream_goal_id": nil, "upstream_task_id": nil}
}
func (s *Service) policy(tx *sql.Tx, kind, project, scope, id, parent string) (Object, error) {
	o := Base(project)
	if project == "" {
		o["project_id"] = nil
	}
	o["scope_type"] = scope
	o["scope_id"] = id
	o["parent_policy_id"] = nil
	if parent != "" {
		o["parent_policy_id"] = parent
	}
	if kind == "BudgetPolicy" {
		Merge(o, Object{"mode": "UNLIMITED_AMOUNT", "cap": nil, "enforcement": "ACCOUNTING_ONLY", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": Now(), "unknown_cost_action": "ALLOW_AND_RECORD"})
	} else {
		Merge(o, Object{"max_concurrency": 2, "max_queue": 100, "monitor_period_seconds": 21600, "first_lookback_seconds": 604800, "max_active_cycles_per_project": 1, "coalesce_missed_triggers": true, "same_failure_retry_limit": 2, "no_progress_iteration_limit": 3, "heartbeat_seconds": 15, "lease_seconds": 90, "log_retention_days": 30, "timezone": "Asia/Shanghai"})
	}
	return o, s.put(tx, kind, o)
}
func (s *Service) createProject(tx *sql.Tx, p Principal, b Object) (Object, error) {
	if !p.CanCreateProject {
		return nil, Fail(403, "FORBIDDEN", "project creation is not granted")
	}
	// Imported documents/snapshots require an explicit import workflow, never implicit cross-project references.
	if len(Arr(b, "source_document_refs")) > 0 || len(Arr(b, "read_snapshot_ids")) > 0 {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "explicit import requires W04")
	}
	for _, f := range Arr(b, "facts") {
		if len(Arr(f.(map[string]any), "source_refs")) > 0 {
			return nil, Fail(503, "RESOURCE_UNAVAILABLE", "fact imports require W04")
		}
	}
	globals := map[string]Object{}
	for _, k := range []string{"BudgetPolicy", "RunPolicy"} {
		g, e := singleton(tx, "", k)
		if e != nil {
			if f, ok := e.(*Fault); !ok || f.Status != 404 {
				return nil, e
			}
			g, e = s.policy(tx, k, "", "GLOBAL", "global", "")
			if e != nil {
				return nil, e
			}
		}
		globals[k] = g
	}
	project := ID()
	policies := map[string]Object{}
	for _, k := range []string{"BudgetPolicy", "RunPolicy"} {
		o, e := s.policy(tx, k, project, "PROJECT", project, Str(globals[k], "id"))
		if e != nil {
			return nil, e
		}
		policies[k] = o
	}
	profile := Merge(Base(project), b)
	profile["id"] = project
	Merge(profile, Object{"stage": "IDEA", "open_problem_ids": Empty(), "budget_policy_id": policies["BudgetPolicy"]["id"], "run_policy_id": policies["RunPolicy"]["id"], "scope_grants": []any{Object{"resource_type": "PROJECT", "resource_id": project, "actions": []any{"READ", "WRITE"}}}})
	if e := s.put(tx, "ProjectProfile", profile); e != nil {
		return nil, e
	}
	state := Merge(Base(project), Object{"profile_revision": 1, "current_requirement_refs": Empty(), "current_decision_refs": Empty(), "active_goal_ids": Empty(), "active_cycle_id": nil, "blocking_conflict_ids": Empty(), "pending_change_ids": Empty(), "latest_release_id": nil, "event_sequence": 0, "policy_revision": 1, "binding": binding()})
	if e := s.put(tx, "ProjectState", state); e != nil {
		return nil, e
	}
	seen := map[string]bool{}
	for _, v := range Arr(b, "source_configs") {
		source := v.(map[string]any)
		sid := Str(source, "source_id")
		if seen[sid] {
			return nil, Fail(400, "INVALID_REQUEST", "duplicate source ID")
		}
		seen[sid] = true
		cursor := Merge(Base(project), Object{"source_id": sid, "query_hash": Hash(source["query"]), "opaque_cursor": nil, "covered_until": nil, "last_success_at": nil, "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": nil})
		if e := s.put(tx, "SourceCursor", cursor); e != nil {
			return nil, e
		}
	}
	_, e := tx.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", p.ID, project)
	return profile, e
}
func (s *Service) createRequirement(tx *sql.Tx, project string, b Object) (Object, error) {
	o := Merge(Base(project), b)
	o["status"] = "PROPOSED"
	return o, s.put(tx, "Requirement", o)
}
func (s *Service) actRequirement(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "Requirement", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "PROPOSED" || b["action"] != "ACCEPT" {
		return nil, Fail(409, "STATE_CONFLICT", "requirement change requires W04 impact workflow")
	}
	if o["basis"] == "ASSUMED" || o["basis"] == "PROPOSED" {
		return nil, Fail(422, "GATE_FAILED", "proposed or assumed requirements need explicit validation through W04")
	}
	if o["basis"] == "OBSERVED" && len(Arr(b, "source_validation_refs")) == 0 {
		return nil, Fail(422, "GATE_FAILED", "observed requirement needs validation evidence")
	}
	// Validation refs become part of the immutable new version provenance.
	refs := Arr(o, "source_refs")
	refs = append(refs, Arr(b, "source_validation_refs")...)
	o["source_refs"] = refs
	bump(o)
	o["status"] = "ACCEPTED"
	if e = s.put(tx, "Requirement", o); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	bump(state)
	state["current_requirement_refs"] = append(Arr(state, "current_requirement_refs"), Ref(o, "Requirement"))
	return o, s.put(tx, "ProjectState", state)
}
func (s *Service) acceptedRequirements(tx *sql.Tx, project string, refs []any) error {
	for _, v := range refs {
		r := v.(map[string]any)
		if r["entity_type"] != "Requirement" {
			return Fail(422, "GATE_FAILED", "requirement reference type required")
		}
		o, e := load(tx, project, "Requirement", Str(r, "id"))
		if e != nil {
			return Fail(422, "GATE_FAILED", "requirement unavailable")
		}
		if o["status"] != "ACCEPTED" {
			return Fail(422, "GATE_FAILED", "requirement not accepted")
		}
	}
	return nil
}
func (s *Service) createGoal(tx *sql.Tx, project string, b Object) (Object, error) {
	if e := s.acceptedRequirements(tx, project, Arr(b, "requirement_refs")); e != nil {
		return nil, e
	}
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return nil, e
	}
	o := Merge(Base(project), b)
	budget, e := s.policy(tx, "BudgetPolicy", project, "GOAL", Str(o, "id"), Str(profile, "budget_policy_id"))
	if e != nil {
		return nil, e
	}
	Merge(o, Object{"status": "DRAFT", "task_ids": Empty(), "budget_policy_id": budget["id"], "outcome": nil, "acceptance_id": nil, "binding": binding()})
	return o, s.put(tx, "Goal", o)
}
func (s *Service) createTask(tx *sql.Tx, project string, b Object) (Object, error) {
	goal, e := load(tx, project, "Goal", Str(b, "goal_id"))
	if e != nil {
		return nil, e
	}
	if goal["status"] != "DRAFT" && goal["status"] != "ACTIVE" {
		return nil, Fail(409, "STATE_CONFLICT", "goal is not accepting tasks")
	}
	found := false
	for _, v := range Arr(goal, "problem_ids") {
		if v == b["origin_problem_id"] {
			found = true
		}
	}
	if !found {
		return nil, Fail(422, "GATE_FAILED", "origin problem must belong to goal")
	}
	if e = s.acceptedRequirements(tx, project, Arr(b, "requirement_refs")); e != nil {
		return nil, e
	}
	inputHash := Hash(b["input_refs"])
	key := Hash([]any{b["origin_problem_id"], b["candidate_id"], inputHash})
	var raw string
	e = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='NoProgressRecord' AND json_extract(body,'$.key_hash')=?", project, key).Scan(&raw)
	var n Object
	if e == sql.ErrNoRows {
		n = Merge(Base(project), Object{"origin_problem_id": b["origin_problem_id"], "candidate_id": b["candidate_id"], "input_hash": inputHash, "key_hash": key, "same_failure_count": 0, "no_progress_iterations": 0, "best_accepted_artifact_ref": nil, "last_effective_progress_at": nil, "resume_conditions": []any{"New effective evidence, changed input, or restored resource required after deferral."}, "status": "ACTIVE"})
		if e = s.put(tx, "NoProgressRecord", n); e != nil {
			return nil, e
		}
	} else if e != nil {
		return nil, e
	} else {
		n, e = Decode([]byte(raw))
		if e != nil {
			return nil, e
		}
	}
	o := Base(project)
	for k, v := range b {
		if k != "origin_problem_id" && k != "candidate_id" {
			o[k] = v
		}
	}
	Merge(o, Object{"status": "DRAFT", "context_bundle_id": nil, "assigned_principal_id": nil, "active_run_id": nil, "output_artifact_ids": Empty(), "acceptance_id": nil, "blocking_conflict_ids": Empty(), "no_progress_record_id": n["id"], "binding": binding()})
	if e = s.put(tx, "Task", o); e != nil {
		return nil, e
	}
	bump(goal)
	goal["task_ids"] = append(Arr(goal, "task_ids"), o["id"])
	return o, s.put(tx, "Goal", goal)
}
func (s *Service) actTask(tx *sql.Tx, project, id string, b Object) (Object, error) {
	o, e := load(tx, project, "Task", id)
	if e != nil {
		return nil, e
	}
	if o["status"] != "DRAFT" {
		return nil, Fail(409, "STATE_CONFLICT", "task transition requires W06")
	}
	switch b["action"] {
	case "CANCEL":
		o["status"] = "CANCELLED"
	case "PAUSE":
		o["status"] = "BLOCKED"
	case "SUBMIT":
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "context and admission gate require W04/W06")
	default:
		return nil, Fail(409, "STATE_CONFLICT", "illegal task transition")
	}
	bump(o)
	return o, s.put(tx, "Task", o)
}
func (s *Service) upload(tx *sql.Tx, p Principal, project string, b []byte) (Object, error) {
	key := ID()
	expiry := time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano)
	h := Digest(b)
	_, e := tx.Exec("INSERT INTO uploaded_content(storage_key,project,principal,bytes,content_hash,expires_at) VALUES(?,?,?,?,?,?)", key, project, p.ID, b, h, expiry)
	return Object{"storage_key": key, "content_hash": h, "byte_size": len(b), "expires_at": expiry}, e
}
func (s *Service) seal(tx *sql.Tx, p Principal, project string, b Object) (Object, error) {
	if b["produced_by"] != p.ID {
		return nil, Fail(403, "FORBIDDEN", "producer must be authenticated principal")
	}
	if b["access_class"] == "VERIFIER_ONLY" {
		return nil, Fail(503, "RESOURCE_UNAVAILABLE", "protected content store requires W17 qualification")
	}
	if b["run_id"] != nil {
		r, e := load(tx, project, "Run", Str(b, "run_id"))
		if e != nil {
			return nil, Fail(422, "GATE_FAILED", "run unavailable")
		}
		if !p.Allowed(project, Str(r, "task_id"), Str(r, "id"), false) {
			return nil, Fail(403, "FORBIDDEN", "run scope denied")
		}
	}
	for _, key := range []string{"input_refs", "source_refs"} {
		for _, v := range Arr(b, key) {
			r := v.(map[string]any)
			if r["entity_type"] == "Artifact" {
				a, e := load(tx, project, "Artifact", Str(r, "id"))
				if e != nil {
					return nil, Fail(422, "GATE_FAILED", "source unavailable")
				}
				if a["access_class"] == "VERIFIER_ONLY" {
					return nil, Fail(403, "FORBIDDEN", "restricted derivation cannot be declassified")
				}
			}
		}
	}
	var content []byte
	var hash, owner, expires string
	e := tx.QueryRow("SELECT bytes,content_hash,principal,expires_at FROM uploaded_content WHERE project=? AND storage_key=?", project, b["storage_key"]).Scan(&content, &hash, &owner, &expires)
	if e != nil {
		return nil, Fail(422, "GATE_FAILED", "upload unavailable")
	}
	if owner != p.ID {
		return nil, Fail(403, "FORBIDDEN", "upload belongs to another principal")
	}
	expiry, e := time.Parse(time.RFC3339Nano, expires)
	if e != nil || time.Now().After(expiry) {
		return nil, Fail(422, "GATE_FAILED", "upload expired")
	}
	if hash != Digest(content) || b["content_hash"] != hash || Num(b, "byte_size") != int64(len(content)) {
		return nil, Fail(422, "CONTENT_HASH_MISMATCH", "content hash or size mismatch")
	}
	if b["kind"] == "TEST_RESULT" {
		if report, e := Decode(content); e == nil && report["schema_version"] == "2.0.0" {
			name := "EvaluationReport"
			if report["report_artifact_ref"] != nil {
				name = "EvaluationSummary"
			}
			if e = s.Contracts.Validate(name, report); e != nil {
				return nil, Fail(422, "GATE_FAILED", "evaluation schema mismatch")
			}
			if report["project_id"] != project {
				return nil, Fail(422, "GATE_FAILED", "evaluation project mismatch")
			}
			return nil, Fail(503, "RESOURCE_UNAVAILABLE", "evaluation execution and independent summary publication require W10/W17")
		}
	}
	o := Merge(Base(project), b)
	Merge(o, Object{"validity": "CURRENT", "sealed_at": Now()})
	if e = s.put(tx, "Artifact", o); e != nil {
		return nil, e
	}
	_, e = tx.Exec("UPDATE uploaded_content SET sealed=1 WHERE storage_key=?", b["storage_key"])
	return o, e
}
func ETag(o Object) string { return fmt.Sprintf("\"r%d\"", Num(o, "revision")) }
