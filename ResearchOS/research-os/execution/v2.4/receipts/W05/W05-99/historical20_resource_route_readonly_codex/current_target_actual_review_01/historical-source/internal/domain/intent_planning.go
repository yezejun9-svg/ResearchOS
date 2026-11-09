package domain

import (
	"database/sql"
	"strings"
)

// This binding is created only at the authenticated Owner submission boundary.
// A model-created requirement or an INTENT prefix alone never grants authority.
func (s *Service) registerIntentSubmission(tx *sql.Tx, p Principal, project string, req Object) error {
	if !strings.HasPrefix(Str(req, "requirement_key"), "INTENT-") {
		return nil
	}
	if !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) || req["basis"] != "USER_STATED" || req["supersedes_id"] != nil || len(Arr(req, "source_refs")) != 0 {
		return Fail(403, "FORBIDDEN", "intent submission requires an authenticated Owner and original user statement")
	}
	submission := strings.TrimPrefix(Str(req, "requirement_key"), "INTENT-")
	if submission == "" || len(submission) > 80 {
		return Fail(422, "GATE_FAILED", "invalid intent submission identity")
	}
	var previous string
	err := tx.QueryRow("SELECT requirement FROM intent_plan_bindings WHERE project=? AND submission=?", project, submission).Scan(&previous)
	if err == nil {
		return Fail(409, "STATE_CONFLICT", "intent submission already exists; replay the original idempotency key")
	}
	if err != sql.ErrNoRows {
		return err
	}
	_, err = tx.Exec("INSERT INTO intent_plan_bindings(project,requirement,submission,actor,raw_hash) VALUES(?,?,?,?,?)", project, req["id"], submission, p.ID, Digest([]byte(Str(req, "text"))))
	return err
}

func (s *Service) acceptIntentRequirement(tx *sql.Tx, p Principal, project, id string, b Object) (Object, error) {
	var actor, rawHash string
	var accepted sql.NullInt64
	err := tx.QueryRow("SELECT actor,raw_hash,accepted_revision FROM intent_plan_bindings WHERE project=? AND requirement=?", project, id).Scan(&actor, &rawHash, &accepted)
	if err == sql.ErrNoRows {
		return s.actRequirement(tx, project, id, b)
	}
	if err != nil {
		return nil, err
	}
	if accepted.Valid || b["action"] != "ACCEPT" {
		return nil, Fail(409, "STATE_CONFLICT", "intent bootstrap requires its first explicit ACCEPT")
	}
	req, err := load(tx, project, "Requirement", id)
	if err != nil {
		return nil, err
	}
	if p.ID != actor || !p.HasRole("OWNER") || !p.Allowed(project, "", "", false) || rawHash != Digest([]byte(Str(req, "text"))) || req["basis"] != "USER_STATED" {
		return nil, Fail(403, "FORBIDDEN", "intent acceptance requires the submitting Owner and unchanged raw statement")
	}
	req, err = s.actRequirement(tx, project, id, b)
	if err != nil {
		return nil, err
	}
	if err = s.bootstrapIntent(tx, p, project, req); err != nil {
		return nil, err
	}
	return req, nil
}

func planningContract() Object {
	checks := Empty()
	for _, key := range []string{"planning.provenance-v1", "planning.dag-capabilities-v1", "planning.open-questions-v1"} {
		checks = append(checks, Object{"check_id": key, "kind": "DETERMINISTIC", "required": true, "expected": "GoalBrief/v1: exact provenance, bounded proposal DAG and explicit unresolved questions; proposal acceptance is not business acceptance", "command_key": key, "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
	}
	c := Object{"contract_revision": 1, "checks": checks, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}

func (s *Service) bootstrapIntent(tx *sql.Tx, p Principal, project string, req Object) error {
	contract := planningContract()
	problem := ID()
	refs := []any{Ref(req, "Requirement")}
	goal, err := s.createGoal(tx, project, Object{"title": "规划：" + Str(req, "text"), "original_intent": Str(req, "text"), "scope": "PROJECT", "requirement_refs": refs, "problem_ids": []any{problem}, "deliverables": []any{"有来源的 GoalBrief/v1 提案，含明确问题、能力缺口、DAG 与失败出口；不代表业务目标完成"}, "acceptance_contract": contract})
	if err != nil {
		return err
	}
	task, err := s.createTask(tx, project, Object{"goal_id": goal["id"], "title": "将原始意图整理为可审查的 GoalBrief", "task_type": "intent_planning", "stage": "review", "dependency_task_ids": Empty(), "requirement_refs": refs, "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": problem, "candidate_id": req["id"], "stop_policy": Object{"wall_time_seconds": 300, "max_attempts": 2, "max_parallel_runs": 1, "stop_conditions": []any{"missing qualified planner", "unresolved business choice", "input drift", "no progress"}}})
	if err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE intent_plan_bindings SET accepted_revision=?,planning_goal=?,planning_task=? WHERE project=? AND requirement=? AND accepted_revision IS NULL", req["revision"], goal["id"], task["id"], project, req["id"]); err != nil {
		return err
	}
	if _, err = s.actGoal(tx, project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Owner explicitly accepted original intent; bounded planning only"}); err != nil {
		return err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return err
	}
	if _, err = s.createContext(tx, p, project, Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]}); err != nil {
		return err
	}
	task, err = load(tx, project, "Task", Str(task, "id"))
	if err != nil {
		return err
	}
	task, err = s.orchestrateTask(tx, project, task, Object{"action": "SUBMIT"})
	if err != nil {
		return err
	}
	// Only the sole runtime coordinator can establish a current qualified route.
	task["status"] = "BLOCKED"
	if err = bump(task); err != nil {
		return err
	}
	if err = s.put(tx, "Task", task); err != nil {
		return err
	}
	if err = s.intentResource(tx, p, project, task, "PERMISSION", "INTENT_PLANNER_UNAVAILABLE", "等待已通过当前资格、用途权限及独立验收条件的规划运行器；原始想法已保存。", Empty()); err != nil {
		return err
	}
	goal, err = load(tx, project, "Goal", Str(goal, "id"))
	if err != nil {
		return err
	}
	if err = s.event(tx, project, "Goal", goal, p.ID, ID(), "PROJECT_UPDATED"); err != nil {
		return err
	}
	return s.event(tx, project, "Task", task, p.ID, ID(), "TASK_CHANGED")
}

func (s *Service) intentResource(tx *sql.Tx, p Principal, project string, task Object, category, code, summary string, artifacts []any) error {
	blocked := []any{task["id"]}
	if task["status"] == "ACCEPTED" {
		blocked = Empty()
	}
	request, err := s.createResourceRequest(tx, project, Object{"category": category, "account_ref": nil, "reason_code": code + ":" + Str(task, "id"), "summary": summary, "blocked_task_ids": blocked, "continuable_task_ids": Empty(), "completed_artifact_refs": artifacts, "requested_capability": Str(task, "task_type"), "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil})
	if err != nil {
		return err
	}
	return s.event(tx, project, "ResourceRequest", request, p.ID, ID(), "RESOURCE_REQUESTED")
}
