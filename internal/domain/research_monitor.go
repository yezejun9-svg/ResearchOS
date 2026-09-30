package domain

import (
	"database/sql"
	"strings"
)

func researchContract(command string) Object {
	c := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "research-stage", "kind": "DETERMINISTIC", "required": true, "expected": "current required stage evidence and explicit gaps", "command_key": command, "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}

func (s *Service) compileMonitorPlan(tx *sql.Tx, owner Principal, project string, b *GoalBrief, meta, planningGoal, briefRef, receipt Object) error {
	if err := verifyMonitorPlan(b.Monitor, meta); err != nil {
		return Fail(422, "GATE_FAILED", err.Error())
	}
	var existing string
	err := tx.QueryRow("SELECT compiled_goal FROM intent_plan_bindings WHERE project=? AND monitor_current=1", project).Scan(&existing)
	if err == nil {
		task, e := load(tx, project, "Task", Arr(planningGoal, "task_ids")[0].(string))
		if e != nil {
			return e
		}
		return s.intentResource(tx, owner, project, task, "BUSINESS_CHOICE", "MONITOR_ALREADY_BOUND", "项目已有监控目标；需明确停止并完成对账后选择替代计划，不能并行扩大监控授权。", []any{briefRef})
	}
	if err != sql.ErrNoRows {
		return err
	}
	profile := meta["profile"].(map[string]any)
	// Correlation IDs and report/cycle versions do not define a new strategy.
	inputs := []any{profile["intent"], profile["accepted_scope"], profile["constraints"], profile["source_configs"]}
	inputHash := Hash(inputs)
	origin := "monitor-" + strings.TrimPrefix(Hash([]any{profile["intent"], profile["accepted_scope"]}), "sha256:")[:32]
	candidate := "monitor-current-sources"
	key := Hash([]any{origin, candidate, inputHash})
	var raw string
	err = tx.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='NoProgressRecord' AND json_extract(body,'$.key_hash')=?", project, key).Scan(&raw)
	var progress Object
	if err == sql.ErrNoRows {
		progress = Merge(Base(project), Object{"origin_problem_id": origin, "candidate_id": candidate, "input_hash": inputHash, "key_hash": key, "same_failure_count": 0, "no_progress_iterations": 0, "best_accepted_artifact_ref": nil, "last_effective_progress_at": nil, "resume_conditions": Empty(), "status": "ACTIVE"})
		err = s.put(tx, "NoProgressRecord", progress)
	} else if err == nil {
		progress, err = Decode([]byte(raw))
	}
	if err != nil {
		return err
	}
	req := meta["requirement"].(map[string]any)
	goal, err := s.createGoal(tx, project, Object{"title": "持续研究当前项目", "original_intent": req["text"], "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{origin}, "deliverables": []any{"每个有限窗口的真实来源、独立阶段证据、研究结论和明确缺口；周期结束不代表长期监控完成"}, "acceptance_contract": researchContract("research.cycle-report-v1")})
	if err != nil {
		return err
	}
	goal, err = s.actGoal(tx, project, Str(goal, "id"), Object{"action": "ACTIVATE", "reason": "Explicit Owner monitoring intent and independently accepted bounded MonitorPlan"})
	if err != nil {
		return err
	}
	_, err = tx.Exec("UPDATE intent_plan_bindings SET compiled_goal=?,node_mapping='{}',plan_kind='MONITOR',monitor_current=1,monitor_started_at=?,monitor_progress_id=? WHERE project=? AND requirement=? AND compiled_goal IS NULL", goal["id"], Now(), progress["id"], project, req["id"])
	if err != nil {
		return err
	}
	for _, ref := range []any{briefRef, Ref(receipt, "AcceptanceReceipt")} {
		if _, err = s.impactLink(tx, project, Object{"from_ref": Ref(goal, "Goal"), "to_ref": ref, "relation": "DEPENDS_ON", "basis": "DETERMINISTIC", "evidence_refs": []any{briefRef}}); err != nil {
			return err
		}
	}
	return s.event(tx, project, "Goal", goal, owner.ID, ID(), "PROJECT_UPDATED")
}

// monitorSnapshot is shared by materialization, effects, stage acceptance and
// close. A stored binding is not current execution authority.
func (s *Service) monitorSnapshot(tx *sql.Tx, project, goalID string, active bool) (Object, *MonitorPlan, error) {
	var actor, planningTask, briefRaw, receiptRaw, progress, started string
	err := tx.QueryRow("SELECT actor,planning_task,brief_ref,acceptance_ref,monitor_progress_id,monitor_started_at FROM intent_plan_bindings WHERE project=? AND compiled_goal=? AND plan_kind='MONITOR' AND monitor_current=1", project, goalID).Scan(&actor, &planningTask, &briefRaw, &receiptRaw, &progress, &started)
	if err != nil {
		return nil, nil, Fail(422, "GATE_FAILED", "current explicit monitor binding required")
	}
	owner, err := s.planningOwner(tx, project, actor)
	if err != nil {
		return nil, nil, err
	}
	goal, err := load(tx, project, "Goal", goalID)
	if err != nil {
		return nil, nil, err
	}
	if active && goal["status"] != "ACTIVE" {
		return nil, nil, Fail(409, "STATE_CONFLICT", "monitor does not permit new work")
	}
	task, err := load(tx, project, "Task", planningTask)
	if err != nil {
		return nil, nil, err
	}
	if _, err = s.researchAcceptedTask(tx, project, task); err != nil {
		return nil, nil, err
	}
	meta, err := s.planningSnapshot(tx, project, task)
	if err != nil {
		return nil, nil, err
	}
	briefRef, err := Decode([]byte(briefRaw))
	if err != nil {
		return nil, nil, err
	}
	receiptRef, err := Decode([]byte(receiptRaw))
	if err != nil {
		return nil, nil, err
	}
	for _, ref := range []Object{briefRef, receiptRef} {
		if err = s.effective(tx, project, ref); err != nil {
			return nil, nil, err
		}
	}
	receipt, err := version(tx, project, receiptRef)
	if err != nil {
		return nil, nil, err
	}
	planGoal, err := load(tx, project, "Goal", Str(task, "goal_id"))
	if err != nil {
		return nil, nil, err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, nil, err
	}
	if planGoal["status"] != "ACCEPTED" || planGoal["acceptance_id"] != receipt["id"] || receipt["verdict"] != "PASS" || receipt["receipt_hash"] != Receipt(receipt) || Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) || len(Arr(receipt, "artifact_refs")) != 1 || Hash(Arr(receipt, "artifact_refs")[0]) != Hash(briefRef) {
		return nil, nil, Fail(422, "GATE_FAILED", "monitor proposal acceptance is no longer current")
	}
	if _, err = intentPrincipal(tx, project, Str(receipt, "verifier_principal_id"), "VERIFIER"); err != nil {
		return nil, nil, err
	}
	if err = retentionIndependent(tx, task, receipt); err != nil {
		return nil, nil, err
	}
	value, err := s.artifactJSON(tx, project, briefRef)
	if err != nil {
		return nil, nil, err
	}
	b, err := parseGoalBrief(Bytes(value))
	if err == nil {
		err = verifyPlanningProvenance(b, meta)
	}
	if err == nil {
		err = verifyMonitorPlan(b.Monitor, meta)
	}
	if err != nil {
		return nil, nil, Fail(422, "GATE_FAILED", err.Error())
	}
	meta["goal"], meta["brief_ref"], meta["acceptance_ref"], meta["progress_record_id"], meta["monitor_started_at"] = goal, briefRef, receiptRef, progress, started
	meta["owner_principal"] = owner
	return meta, b.Monitor, nil
}

func (s *Service) researchAcceptedTask(tx *sql.Tx, project string, task Object) (Object, error) {
	if task["status"] != "ACCEPTED" {
		return nil, Fail(409, "STATE_CONFLICT", "research stage needs independent acceptance")
	}
	if err := s.acceptedTaskBinding(tx, project, task); err != nil {
		return nil, err
	}
	if err := s.taskContext(tx, project, task); err != nil {
		return nil, err
	}
	receipt, err := load(tx, project, "AcceptanceReceipt", Str(task, "acceptance_id"))
	if err != nil {
		return nil, err
	}
	if _, err = intentPrincipal(tx, project, Str(receipt, "verifier_principal_id"), "VERIFIER"); err != nil {
		return nil, err
	}
	if err = retentionIndependent(tx, task, receipt); err != nil {
		return nil, err
	}
	state, err := singleton(tx, project, "ProjectState")
	if err != nil {
		return nil, err
	}
	if Hash(receipt["policy_revision"]) != Hash(state["policy_revision"]) {
		return nil, Fail(412, "STALE_INPUT", "research verifier policy changed")
	}
	run, err := load(tx, project, "Run", Str(receipt, "run_id"))
	if err != nil {
		return nil, err
	}
	if err = effectsReconciled(tx, project, Str(run, "id")); err != nil {
		return nil, err
	}
	if _, err = s.runDependenciesCurrent(tx, project, task, run); err != nil {
		return nil, err
	}
	dispatch, err := runtimeDispatch(tx, project, Str(run, "id"), run["lease_epoch"])
	if err == nil {
		observation, e := runtimeObservation(tx, project, run)
		if e != nil {
			return nil, e
		}
		if _, e = nativeDispatchProof(tx, project, run, observation); e != nil {
			return nil, e
		}
		if _, e = s.currentDispatchAdmission(tx, project, task, run, dispatch, "accept"); e != nil {
			return nil, e
		}
	} else if err != sql.ErrNoRows || receipt["measurement_mode"] != "FIXTURE" {
		return nil, Fail(422, "GATE_FAILED", "current native research stage proof required")
	}
	return receipt, nil
}
