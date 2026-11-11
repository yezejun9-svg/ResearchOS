package domain

import (
	"context"
	"database/sql"
	"strings"
)

func init() { implemented["claimTask"] = true; implemented["actOnGoal"] = true }

// RegisterOrchestrationFixture is a trusted, local DEVELOPMENT_ONLY entry.
// It cannot qualify a LIVE runtime or turn it AVAILABLE.
func (s *Service) RegisterOrchestrationFixture(ctx context.Context, project, runtime string) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	r, e := load(tx, project, "RuntimeRegistration", runtime)
	if e != nil {
		return e
	}
	if r["measurement_mode"] != "FIXTURE" {
		return Fail(422, "GATE_FAILED", "fixture registration requires FIXTURE runtime")
	}
	_, e = tx.Exec("INSERT INTO orchestration_fixtures(project,runtime) VALUES(?,?)", project, runtime)
	if e != nil {
		return e
	}
	return tx.Commit()
}

// RegisterExecutionIdentity binds an alias or delegated child to its authority root.
// Only the local principal provisioner may call this, before the identity executes.
// This is application separation, not W17 protected execution isolation.
func (s *Service) RegisterExecutionIdentity(ctx context.Context, principal, parent string) error {
	tx, e := s.DB.BeginTx(ctx, nil)
	if e != nil {
		return e
	}
	defer tx.Rollback()
	if principal == parent {
		return Fail(422, "GATE_FAILED", "identity cannot parent itself")
	}
	var used int
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.executor_principal_id')=?", principal).Scan(&used); e != nil {
		return e
	}
	if used != 0 {
		return Fail(409, "STATE_CONFLICT", "identity lineage must precede execution")
	}
	root := parent
	e = tx.QueryRow("SELECT root FROM orchestration_identity WHERE principal=?", parent).Scan(&root)
	if e != nil && e != sql.ErrNoRows {
		return e
	}
	if e == sql.ErrNoRows {
		if _, e = tx.Exec("INSERT INTO orchestration_identity(principal,root,parent) VALUES(?,?,NULL)", parent, parent); e != nil {
			return e
		}
	}
	if root == principal {
		return Fail(422, "GATE_FAILED", "identity cycle")
	}
	_, e = tx.Exec("INSERT INTO orchestration_identity(principal,root,parent) VALUES(?,?,?)", principal, root, parent)
	if e != nil {
		return e
	}
	return tx.Commit()
}

func authorityRoot(tx *sql.Tx, id string) (string, error) {
	root := id
	e := tx.QueryRow("SELECT root FROM orchestration_identity WHERE principal=?", id).Scan(&root)
	if e == sql.ErrNoRows {
		return id, nil
	}
	return root, e
}

// currentAuthorityRoot proves current authority lineage, not inherited roles or
// grants. Legacy direct principals need not have an orchestration row. Managed
// verifier children are explicitly anchored by their trusted installation and
// may never fall back to that legacy direct-identity rule after row deletion.
func currentAuthorityRoot(tx *sql.Tx, id string) (string, error) {
	denied := func() (string, error) {
		return "", Fail(403, "FORBIDDEN", "authority principal or registered lineage is missing, revoked or changed")
	}
	if id == "" {
		return denied()
	}
	var anchorHash, anchorRaw, anchorProject string
	var anchors int
	if e := tx.QueryRow(`SELECT count(*) FROM idempotency WHERE principal=? AND operation='host:managed-verifier-lineage' AND key=?`, id, id).Scan(&anchors); e != nil {
		return "", e
	}
	if anchors > 1 {
		return denied()
	}
	err := tx.QueryRow(`SELECT project,request_hash,body FROM idempotency WHERE principal=? AND operation='host:managed-verifier-lineage' AND key=?`, id, id).Scan(&anchorProject, &anchorHash, &anchorRaw)
	var anchor Object
	if err == nil {
		anchor, err = Decode([]byte(anchorRaw))
		if err != nil || Hash(anchor) != anchorHash || anchor["schema"] != "researchos.managed-verifier-lineage.v1" || anchor["principal"] != id || Str(anchor, "root") == "" || anchorProject == "" || anchor["project_id"] != anchorProject || Str(anchor, "registered_by") == "" {
			return denied()
		}
	} else if err != sql.ErrNoRows {
		return "", err
	}
	var root string
	var parent sql.NullString
	err = tx.QueryRow(`SELECT root,parent FROM orchestration_identity WHERE principal=?`, id).Scan(&root, &parent)
	if err == sql.ErrNoRows {
		var revoked int
		if anchor != nil || tx.QueryRow(`SELECT revoked FROM auth_principals WHERE id=?`, id).Scan(&revoked) != nil || revoked != 0 {
			return denied()
		}
		return id, nil
	}
	if err != nil {
		return "", err
	}
	if root == "" || (anchor != nil && (anchor["root"] != root || !parent.Valid || parent.String != root)) {
		return denied()
	}
	seen := map[string]bool{}
	for current := id; ; {
		if current == "" || seen[current] || len(seen) >= 256 {
			return denied()
		}
		seen[current] = true
		var revoked int
		if tx.QueryRow(`SELECT revoked FROM auth_principals WHERE id=?`, current).Scan(&revoked) != nil || revoked != 0 {
			return denied()
		}
		var actualRoot string
		var actualParent sql.NullString
		if tx.QueryRow(`SELECT root,parent FROM orchestration_identity WHERE principal=?`, current).Scan(&actualRoot, &actualParent) != nil || actualRoot != root {
			return denied()
		}
		if !actualParent.Valid {
			if current != root {
				return denied()
			}
			return root, nil
		}
		if current == root {
			return denied()
		}
		current = actualParent.String
	}
}

func contractDigest(c Object) string {
	v := Object{}
	for k, x := range c {
		if k != "contract_hash" {
			v[k] = x
		}
	}
	return Hash(v)
}

func freezeTaskContract(tx *sql.Tx, project string, task Object) error {
	c := task["acceptance_contract"].(map[string]any)
	if c["contract_hash"] != contractDigest(c) || c["require_independent_verifier"] != true || c["version_policy"] != "EXACT" {
		return Fail(422, "GATE_FAILED", "exact independent contract hash required")
	}
	required := 0
	ids := map[string]bool{}
	for _, v := range Arr(c, "checks") {
		check := v.(map[string]any)
		id := Str(check, "check_id")
		if ids[id] {
			return Fail(422, "GATE_FAILED", "duplicate frozen check")
		}
		ids[id] = true
		if check["required"] == true {
			required++
		}
	}
	if required == 0 {
		return Fail(422, "GATE_FAILED", "at least one mandatory acceptance check required")
	}
	var old string
	e := tx.QueryRow("SELECT contract FROM orchestration_contracts WHERE project=? AND task=?", project, task["id"]).Scan(&old)
	if e == nil {
		c0, _ := Decode([]byte(old))
		if Hash(c0) != Hash(c) {
			return Fail(422, "GATE_FAILED", "acceptance contract cannot change after submission")
		}
		return nil
	}
	if e != sql.ErrNoRows {
		return e
	}
	_, e = tx.Exec("INSERT INTO orchestration_contracts(project,task,contract,frozen_at) VALUES(?,?,?,?)", project, task["id"], string(Bytes(c)), Now())
	return e
}

func (s *Service) dependenciesReady(tx *sql.Tx, project string, task Object) (bool, error) {
	visiting := map[string]bool{}
	visited := map[string]bool{}
	var visit func(Object) error
	visit = func(t Object) error {
		id := Str(t, "id")
		if visiting[id] {
			return Fail(422, "GATE_FAILED", "task dependency cycle")
		}
		if visited[id] {
			return nil
		}
		visiting[id] = true
		seen := map[string]bool{}
		for _, v := range Arr(t, "dependency_task_ids") {
			d, ok := v.(string)
			if !ok || seen[d] {
				return Fail(422, "GATE_FAILED", "invalid or duplicate dependency")
			}
			seen[d] = true
			n, e := load(tx, project, "Task", d)
			if e != nil {
				return e
			}
			if n["goal_id"] != task["goal_id"] {
				return Fail(422, "GATE_FAILED", "dependency must belong to same goal")
			}
			if e = visit(n); e != nil {
				return e
			}
		}
		delete(visiting, id)
		visited[id] = true
		return nil
	}
	if e := visit(task); e != nil {
		return false, e
	}
	for _, v := range Arr(task, "dependency_task_ids") {
		d, e := load(tx, project, "Task", v.(string))
		if e != nil {
			return false, e
		}
		if d["status"] != "ACCEPTED" {
			return false, nil
		}
		if e = s.acceptedTaskBinding(tx, project, d); e != nil {
			return false, e
		}
	}
	return true, nil
}

func (s *Service) actGoal(tx *sql.Tx, project, id string, b Object) (Object, error) {
	g, e := load(tx, project, "Goal", id)
	if e != nil {
		return nil, e
	}
	action := Str(b, "action")
	status := Str(g, "status")
	switch {
	case action == "ACTIVATE" && status == "DRAFT", action == "RESUME" && status == "PAUSED":
		g["status"] = "ACTIVE"
	case action == "PAUSE" && status == "ACTIVE":
		g["status"] = "PAUSED"
	case action == "CANCEL" && (status == "DRAFT" || status == "ACTIVE" || status == "PAUSED"):
		g["status"] = "CANCELLED"
		if e = s.cancelGoalQueueTasks(tx, project, id); e != nil {
			return nil, e
		}
	default:
		return nil, Fail(409, "STATE_CONFLICT", "illegal goal transition")
	}
	if g["status"] == "ACTIVE" {
		if e = freezeGoalContract(tx, project, g); e != nil {
			return nil, e
		}
	}
	if e = bump(g); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Goal", g); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	ids := Empty()
	for _, v := range Arr(state, "active_goal_ids") {
		if v != id {
			ids = append(ids, v)
		}
	}
	if g["status"] == "ACTIVE" {
		ids = append(ids, id)
	}
	state["active_goal_ids"] = ids
	if e = bump(state); e != nil {
		return nil, e
	}
	return g, s.put(tx, "ProjectState", state)
}

func (s *Service) orchestrateTask(tx *sql.Tx, project string, t, b Object) (Object, error) {
	action, status := Str(b, "action"), Str(t, "status")
	if action == "SUBMIT" && status != "DRAFT" || action == "RESUME" && status != "BLOCKED" && status != "FAILED" {
		return nil, Fail(409, "STATE_CONFLICT", "task not eligible for submission")
	}
	if action != "SUBMIT" && action != "RESUME" {
		return nil, Fail(409, "STATE_CONFLICT", "active task requires settled cancellation before transition")
	}
	var active int
	if e := tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=? AND json_extract(body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')", project, t["id"]).Scan(&active); e != nil {
		return nil, e
	}
	if active != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "unresolved execution retains ownership")
	}
	g, e := load(tx, project, "Goal", Str(t, "goal_id"))
	if e != nil {
		return nil, e
	}
	if g["status"] != "ACTIVE" {
		return nil, Fail(409, "STATE_CONFLICT", "goal must be active")
	}
	if e = freezeTaskContract(tx, project, t); e != nil {
		return nil, e
	}
	ready, e := s.dependenciesReady(tx, project, t)
	if e != nil {
		return nil, e
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, e
	}
	n, e := s.progressForInputs(tx, project, t)
	if e != nil {
		return nil, e
	}
	if n["status"] == "DEFERRED_NO_PROGRESS" {
		return nil, Fail(409, "STATE_CONFLICT", "unchanged no-progress key remains deferred")
	}
	if action == "RESUME" {
		if _, e = tx.Exec("DELETE FROM orchestration_task_controls WHERE project=? AND task=?", project, t["id"]); e != nil {
			return nil, e
		}
	}
	if e = s.admitResourceQueue(tx, project, Str(t, "id")); e != nil {
		return nil, e
	}
	t["status"] = "BLOCKED"
	if ready && len(Arr(t, "blocking_conflict_ids")) == 0 {
		t["status"] = "READY"
	}
	if action == "RESUME" && Str(t, "active_run_id") != "" && len(Arr(t, "output_artifact_ids")) > 0 {
		run, e := load(tx, project, "Run", Str(t, "active_run_id"))
		if e != nil {
			return nil, e
		}
		if run["status"] == "SETTLED" {
			t["status"] = "EXECUTION_REPORTED"
		}
	}
	if e = bump(t); e != nil {
		return nil, e
	}
	return t, s.put(tx, "Task", t)
}

func (s *Service) claimTask(tx *sql.Tx, p Principal, project, id string, b Object, cid string) (Object, error) {
	return s.claimTaskMode(tx, p, project, id, b, cid, false)
}

func (s *Service) claimTaskMode(tx *sql.Tx, p Principal, project, id string, b Object, cid string, qualificationBootstrap bool) (Object, error) {
	t, e := load(tx, project, "Task", id)
	if e != nil {
		return nil, e
	}
	installed, e := clientQueueInstalled(tx)
	if e != nil {
		return nil, e
	}
	if installed {
		var queueFenced int
		if e = tx.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE project=? AND task_id=? AND (state<>'OPEN' OR restore_fenced<>0 OR run_id IS NOT NULL)`, project, id).Scan(&queueFenced); e != nil {
			return nil, e
		}
		if queueFenced != 0 {
			return nil, Fail(409, "STATE_CONFLICT", "original command queue cannot be redispatched")
		}
	}
	if t["status"] != "READY" {
		return nil, Fail(409, "STATE_CONFLICT", "only READY tasks can be claimed")
	}
	g, e := load(tx, project, "Goal", Str(t, "goal_id"))
	if e != nil {
		return nil, e
	}
	if g["status"] != "ACTIVE" {
		return nil, Fail(409, "STATE_CONFLICT", "goal is not active")
	}
	ready, e := s.dependenciesReady(tx, project, t)
	if e != nil {
		return nil, e
	}
	if !ready {
		return nil, Fail(409, "STATE_CONFLICT", "dependencies are not accepted")
	}
	if t["context_bundle_id"] != b["context_bundle_id"] {
		return nil, Fail(412, "STALE_INPUT", "context changed")
	}
	if e = s.taskContext(tx, project, t); e != nil {
		return nil, e
	}
	if e = freezeTaskContract(tx, project, t); e != nil {
		return nil, e
	}
	state, e := singleton(tx, project, "ProjectState")
	if e != nil {
		return nil, e
	}
	if len(Arr(t, "blocking_conflict_ids"))+len(Arr(state, "blocking_conflict_ids")) != 0 {
		return nil, Fail(409, "STATE_CONFLICT", "blocking conflict unresolved")
	}
	rt, e := load(tx, project, "RuntimeRegistration", Str(b, "runtime_id"))
	if e != nil {
		return nil, e
	}
	var fixture int
	e = tx.QueryRow("SELECT count(*) FROM orchestration_fixtures WHERE project=? AND runtime=?", project, rt["id"]).Scan(&fixture)
	if e != nil {
		return nil, e
	}
	var admission Object
	if !qualificationBootstrap && (fixture != 1 || rt["measurement_mode"] != "FIXTURE" || len(Arr(rt, "qualification_ids")) != 0) {
		admission, e = s.currentRuntimeAdmission(tx, project, t, rt, []any{"start"}, "claim")
		if e != nil {
			return nil, e
		}
		if !runtimeExecutorAllowed(tx, Str(b, "executor_principal_id"), project, id) {
			return nil, Fail(403, "FORBIDDEN", "current executor project/task grant required")
		}
	}
	if rt["status"] == "REVOKED" || rt["status"] == "UNAVAILABLE" {
		return nil, Fail(409, "STATE_CONFLICT", "runtime unavailable")
	}
	var roles string
	var revoked int
	if e = tx.QueryRow("SELECT roles,revoked FROM auth_principals WHERE id=?", b["executor_principal_id"]).Scan(&roles, &revoked); e != nil || revoked != 0 || !strings.Contains(roles, `"EXECUTOR"`) {
		return nil, Fail(403, "FORBIDDEN", "executor unavailable")
	}
	profile, e := singleton(tx, project, "ProjectProfile")
	if e != nil {
		return nil, e
	}
	policy, e := load(tx, project, "RunPolicy", Str(profile, "run_policy_id"))
	if e != nil {
		return nil, e
	}
	limit, _ := Num(policy, "max_concurrency")
	var active int64
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.status') NOT IN ('SETTLED','FAILED','CANCELLED')", project).Scan(&active); e != nil {
		return nil, e
	}
	if active >= limit {
		return nil, Fail(409, "STATE_CONFLICT", "project concurrency exhausted")
	}
	n, e := load(tx, project, "NoProgressRecord", Str(t, "no_progress_record_id"))
	if e != nil {
		return nil, e
	}
	if n["status"] == "DEFERRED_NO_PROGRESS" {
		return nil, Fail(409, "STATE_CONFLICT", "no-progress key deferred")
	}
	var attempts int64
	if e = tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?", project, t["id"]).Scan(&attempts); e != nil {
		return nil, e
	}
	maxAttempts, _ := Num(t["stop_policy"].(map[string]any), "max_attempts")
	if attempts >= maxAttempts {
		return nil, Fail(409, "STATE_CONFLICT", "task attempt limit reached")
	}
	dependencies, e := s.dependencyVector(tx, project, t)
	if e != nil {
		return nil, e
	}
	if e = s.dependencyContext(tx, project, t, dependencies); e != nil {
		return nil, e
	}
	if e = s.admitGlobalConcurrency(tx); e != nil {
		return nil, e
	}
	r, lease, e := s.createRuntimeRun(tx, project, t, Str(rt, "id"), Str(b, "executor_principal_id"))
	if e != nil {
		return nil, e
	}
	if qualificationBootstrap {
		if rt["measurement_mode"] == "FIXTURE" {
			if e = s.reserveFixtureDispatch(tx, project, r); e != nil {
				return nil, e
			}
		} else if e = s.reserveQualificationDispatch(tx, project, r, rt); e != nil {
			return nil, e
		}
	} else if admission != nil {
		if e = s.reserveRuntimeLocalLaunch(tx, project, r, admission); e != nil {
			return nil, e
		}
	} else {
		if e = s.reserveFixtureDispatch(tx, project, r); e != nil {
			return nil, e
		}
	}
	if _, e = tx.Exec("INSERT INTO orchestration_run_dependencies(project,run,snapshot) VALUES(?,?,?)", project, r["id"], string(Bytes(Object{"refs": dependencies}))); e != nil {
		return nil, e
	}
	t["status"] = "RUNNING"
	if e = bump(t); e != nil {
		return nil, e
	}
	if e = s.put(tx, "Task", t); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Run", r, p.ID, cid, "RUN_CHANGED"); e != nil {
		return nil, e
	}
	if e = s.event(tx, project, "Task", t, p.ID, cid, "TASK_CHANGED"); e != nil {
		return nil, e
	}
	if admission != nil {
		if e = s.prepareRuntimeDispatch(tx, project, t, r, admission); e != nil {
			return nil, e
		}
	}
	return Object{"task": t, "run": r, "lease_token": lease}, nil
}

func taskTransition(old, next Object) bool {
	from, to := Str(old, "status"), Str(next, "status")
	if from == to {
		return true
	}
	if to == "NEEDS_REVALIDATION" && from != "CANCELLED" {
		return true
	}
	switch from {
	case "NEEDS_REVALIDATION":
		return to == "DRAFT"
	case "DRAFT":
		return to == "READY" || to == "BLOCKED" || to == "CANCELLED" || to == "EXECUTION_REPORTED" && old["task_type"] == "runtime_qualification"
	case "READY":
		return to == "RUNNING" || to == "BLOCKED" || to == "CANCELLED"
	case "BLOCKED", "FAILED":
		return to == "READY" || to == "BLOCKED" || to == "CANCELLED" || to == "EXECUTION_REPORTED"
	case "RUNNING":
		return to == "BLOCKED" || to == "EXECUTION_REPORTED" || to == "FAILED" || to == "DEFERRED_NO_PROGRESS" || to == "CANCELLED"
	case "EXECUTION_REPORTED", "VERIFYING":
		return to == "CANCELLED" || to == "ACCEPTED" || to == "FAILED" || to == "BLOCKED" || to == "DEFERRED_NO_PROGRESS"
	}
	return false
}
