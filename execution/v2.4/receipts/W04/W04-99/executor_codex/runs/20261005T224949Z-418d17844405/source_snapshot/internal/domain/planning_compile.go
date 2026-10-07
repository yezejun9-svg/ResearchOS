package domain

import (
	"database/sql"
	"fmt"
)

// compileIntentPlan runs only after current, independently verified planning
// Goal acceptance, in the same transaction. Generated identifiers are never used
// as authority IDs; durable logical mappings make acceptance replay harmless.
func (s *Service) compileIntentPlan(tx *sql.Tx, project string, snap, receipt Object) error {
	b, meta, e := planningRaw(snap)
	if e != nil {
		return e
	}
	if e = verifyPlanningProvenance(b, meta); e != nil {
		return e
	}
	if e = verifyPlanningQuestions(b); e != nil {
		return e
	}
	ordered, e := planningOrder(b, meta)
	if e != nil {
		return e
	}
	req := meta["requirement"].(map[string]any)
	planningGoal := snap["goal"].(map[string]any)
	var prior sql.NullString
	if e = tx.QueryRow("SELECT compiled_goal FROM intent_plan_bindings WHERE project=? AND requirement=? AND planning_goal=?", project, req["id"], planningGoal["id"]).Scan(&prior); e != nil {
		return e
	}
	if prior.Valid {
		return nil
	}
	owner, e := s.planningOwner(tx, project, Str(meta, "owner"))
	if e != nil {
		return e
	}
	artifactRef := Arr(snap, "artifact_refs")[0]
	refs := []any{Ref(req, "Requirement"), artifactRef, Ref(receipt, "AcceptanceReceipt")}
	if _, e = tx.Exec("UPDATE intent_plan_bindings SET brief_ref=?,acceptance_ref=? WHERE project=? AND requirement=?", string(Bytes(artifactRef)), string(Bytes(Ref(receipt, "AcceptanceReceipt"))), project, req["id"]); e != nil {
		return e
	}
	planningTask := Arr(snap, "tasks")[0].(map[string]any)
	if b.Status == "NEEDS_INPUT" {
		for _, q := range b.OpenQuestions {
			if q.Blocking {
				if e = s.intentResource(tx, owner, project, planningTask, "BUSINESS_CHOICE", "INTENT_QUESTION:"+q.ID, fmt.Sprintf("已接受规划提案仍需用户选择：%s；选项：%s。答复须保存为关联原意图/提案的新 USER_STATED Requirement 并显式接受；不得将资源请求状态当成答案。", q.Question, Bytes(q.Options)), []any{artifactRef}); e != nil {
					return e
				}
			}
		}
		for _, gap := range b.CapabilityGaps {
			if e = s.intentResource(tx, owner, project, planningTask, "PERMISSION", "INTENT_CAPABILITY:"+gap.Node+":"+gap.Capability, "规划提案缺少可执行/可验证能力："+gap.Reason, []any{artifactRef}); e != nil {
				return e
			}
		}
		return nil
	}
	if b.Monitor != nil {
		return s.compileMonitorPlan(tx, owner, project, b, meta, planningGoal, artifactRef.(map[string]any), receipt)
	}
	for _, n := range ordered {
		if !planningNodeSupported(n, meta) {
			return Fail(422, "GATE_FAILED", "unsupported business node cannot be compiled")
		}
	}
	goalContract := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "compiled-deliverables", "kind": "DETERMINISTIC", "required": true, "expected": "Every exact compiled deliverable Task has current independent acceptance against its Owner-grounded checks.", "command_key": "planning.compiled-deliverables-v1", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	goalContract["contract_hash"] = contractDigest(goalContract)
	literal, count, _ := planningJSONAuthorization(meta)
	goal, e := s.createGoal(tx, project, Object{"title": "交付用户明确指定的 JSON 报告", "original_intent": req["text"], "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": planningGoal["problem_ids"], "deliverables": []any{fmt.Sprintf("%d 份独立校验且逐字面量匹配的 JSON 报告：%s", count, literal)}, "acceptance_contract": goalContract})
	if e != nil {
		return e
	}
	mapping := Object{}
	for _, n := range ordered {
		checks := Empty()
		for _, check := range n.Checks {
			checks = append(checks, Object{"check_id": check.ID, "kind": "DETERMINISTIC", "required": true, "expected": check.Expected, "command_key": check.Command, "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil})
		}
		contract := Object{"contract_revision": 1, "checks": checks, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
		contract["contract_hash"] = contractDigest(contract)
		deps := Empty()
		for _, logical := range n.Dependencies {
			deps = append(deps, mapping[logical])
		}
		inputRefs := mergeUnique(append(Empty(), refs...), n.Inputs)
		task, e := s.createTask(tx, project, Object{"goal_id": goal["id"], "title": n.Title, "task_type": "json_report", "stage": "delivery", "dependency_task_ids": deps, "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": inputRefs, "acceptance_contract": contract, "origin_problem_id": Arr(planningGoal, "problem_ids")[0], "candidate_id": "intent-node-" + Str(req, "id") + "-" + n.ID, "stop_policy": Object{"wall_time_seconds": n.WallTime, "max_attempts": n.MaxAttempts, "max_parallel_runs": 1, "stop_conditions": toAnyStrings(b.FailureExits)}})
		if e != nil {
			return e
		}
		mapping[n.ID] = task["id"]
	}
	if _, e = s.actGoal(tx, project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Compile current independently accepted bounded intent plan"}); e != nil {
		return e
	}
	for _, n := range ordered {
		taskID := mapping[n.ID].(string)
		state, e := singleton(tx, project, "ProjectState")
		if e != nil {
			return e
		}
		if _, e = s.createContext(tx, owner, project, Object{"task_id": taskID, "expected_project_state_revision": state["revision"]}); e != nil {
			return e
		}
		task, e := load(tx, project, "Task", taskID)
		if e != nil {
			return e
		}
		task, e = s.orchestrateTask(tx, project, task, Object{"action": "SUBMIT"})
		if e != nil {
			return e
		}
		if e = s.event(tx, project, "Task", task, owner.ID, ID(), "TASK_CHANGED"); e != nil {
			return e
		}
	}
	goal, e = load(tx, project, "Goal", Str(goal, "id"))
	if e != nil {
		return e
	}
	for _, ref := range []any{artifactRef, Ref(receipt, "AcceptanceReceipt")} {
		if _, e = s.impactLink(tx, project, Object{"from_ref": Ref(goal, "Goal"), "to_ref": ref, "relation": "DEPENDS_ON", "basis": "DETERMINISTIC", "evidence_refs": []any{artifactRef}}); e != nil {
			return e
		}
	}
	if _, e = tx.Exec("UPDATE intent_plan_bindings SET compiled_goal=?,node_mapping=? WHERE project=? AND requirement=? AND compiled_goal IS NULL", goal["id"], string(Bytes(mapping)), project, req["id"]); e != nil {
		return e
	}
	goal, e = load(tx, project, "Goal", Str(goal, "id"))
	if e != nil {
		return e
	}
	return s.event(tx, project, "Goal", goal, owner.ID, ID(), "PROJECT_UPDATED")
}

func toAnyStrings(values []string) []any {
	result := Empty()
	for _, v := range values {
		result = append(result, v)
	}
	return result
}

func (s *Service) compiledPlanningSnapshot(tx *sql.Tx, project string, goal Object) (Object, error) {
	var kind string
	if err := tx.QueryRow("SELECT plan_kind FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", project, goal["id"]).Scan(&kind); err != nil && err != sql.ErrNoRows {
		return nil, err
	}
	if kind == "MONITOR" {
		meta, _, err := s.monitorSnapshot(tx, project, Str(goal, "id"), true)
		return meta, err
	}
	var planningGoal, briefRaw, receiptRaw, mappingRaw string
	e := tx.QueryRow("SELECT planning_goal,brief_ref,acceptance_ref,node_mapping FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", project, goal["id"]).Scan(&planningGoal, &briefRaw, &receiptRaw, &mappingRaw)
	if e == sql.ErrNoRows {
		return nil, nil
	}
	if e != nil {
		return nil, e
	}
	brief, e := Decode([]byte(briefRaw))
	if e != nil {
		return nil, e
	}
	receiptRef, e := Decode([]byte(receiptRaw))
	if e != nil {
		return nil, e
	}
	mapping, e := Decode([]byte(mappingRaw))
	if e != nil {
		return nil, e
	}
	for _, ref := range []Object{brief, receiptRef} {
		if e = s.effective(tx, project, ref); e != nil {
			return nil, e
		}
	}
	plan, e := load(tx, project, "Goal", planningGoal)
	if e != nil {
		return nil, e
	}
	accepted, e := version(tx, project, receiptRef)
	if e != nil {
		return nil, e
	}
	if plan["status"] != "ACCEPTED" || plan["acceptance_id"] != accepted["id"] || accepted["verdict"] != "PASS" || accepted["receipt_hash"] != Receipt(accepted) {
		return nil, Fail(422, "GATE_FAILED", "compiled plan acceptance no longer current")
	}
	ids := map[string]bool{}
	for _, v := range mapping {
		id, ok := v.(string)
		if !ok || ids[id] {
			return nil, Fail(422, "GATE_FAILED", "compiled node mapping invalid")
		}
		ids[id] = true
	}
	if len(ids) != len(Arr(goal, "task_ids")) {
		return nil, Fail(422, "GATE_FAILED", "compiled goal task set changed")
	}
	for _, v := range Arr(goal, "task_ids") {
		if !ids[v.(string)] {
			return nil, Fail(422, "GATE_FAILED", "compiled goal contains an unbound task")
		}
	}
	return Object{"planning_goal": plan, "brief_ref": brief, "acceptance": accepted, "node_mapping": mapping}, nil
}
