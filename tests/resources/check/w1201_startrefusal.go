package main

// startRefusalPhase closes B-01 of the W12-01 round-1 review. The receipt had excused step 2's
// "refused at START" with the claim that a start-time refusal is unreachable through any public
// path. That statement was measured false: a fresh claim of a second task in the same Goal is a
// start, its reservation runs through reserveFixtureDispatch -> appendBudget -> the Goal's budget
// chain, and the unresolved-cost gate there refuses it before any Run row exists. This phase drives
// only the service's own HTTP handler, asserts the refusal by name, proves no Run was written, and
// puts the same claim back through the gate once the liability is settled.

import (
	"context"
	"strings"

	"researchos.local/research-os/internal/domain"
)

// startRefusalGraph is a submitted, claimable task inside the Goal the first run already belongs to,
// so the budget chain under test is exactly the one the unresolved liability sits in.
func submittedTaskInGoal(ctx context.Context, h *harness, g *runGraph, label string) (string, bool) {
	_, task1, _ := h.api(ctx, "GET", h.base+"/tasks/"+g.taskID, "", "", nil)
	if task1["id"] == nil {
		ok("W1201-START-REFUSAL-SECOND-TASK-CREATED", false, "task readback for "+label)
		return "", false
	}
	_, goal, _ := h.api(ctx, "GET", h.base+"/goals/"+g.goalID, "", "", nil)
	code, task, body := h.api(ctx, "POST", h.base+"/tasks", domain.ID(), tagOf(goal), domain.Object{
		"goal_id": g.goalID, "title": "w1201 start refusal " + label, "task_type": "json-verification",
		"stage": "verification", "dependency_task_ids": domain.Empty(),
		"requirement_refs": task1["requirement_refs"], "input_refs": domain.Empty(),
		"acceptance_contract": task1["acceptance_contract"], "origin_problem_id": g.origin,
		"candidate_id": g.candidate + "-" + label, "stop_policy": task1["stop_policy"]})
	if code != 201 {
		ok("W1201-START-REFUSAL-SECOND-TASK-CREATED", false, domain.Object{"code": code, "body": body})
		return "", false
	}
	id := domain.Str(task, "id")

	state, _ := h.liveState(ctx)
	code, _, body = h.api(ctx, "POST", h.base+"/context-bundles", domain.ID(), tagOf(state), domain.Object{
		"task_id": id, "expected_project_state_revision": state["revision"]})
	if code != 201 {
		ok("W1201-START-REFUSAL-SECOND-TASK-CREATED", false, domain.Object{"bundle": code, "body": body})
		return "", false
	}
	_, submitted, _ := h.api(ctx, "GET", h.base+"/tasks/"+id, "", "", nil)
	code, _, body = h.api(ctx, "POST", h.base+"/tasks/"+id+"/actions", domain.ID(), tagOf(submitted),
		domain.Object{"action": "SUBMIT", "reason": "start-time cost qualification probe"})
	if code != 200 {
		ok("W1201-START-REFUSAL-SECOND-TASK-CREATED", false, domain.Object{"submit": code, "body": body})
		return "", false
	}
	ok("W1201-START-REFUSAL-SECOND-TASK-CREATED", true, id)
	return id, true
}

func runRowsFor(ctx context.Context, h *harness, taskID string) int {
	var n int
	if e := h.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?",
		h.project, taskID).Scan(&n); e != nil {
		return -1
	}
	return n
}

// claimTask is the "start". It returns the reply pair and the run rows that exist afterwards.
func claimTask(ctx context.Context, h *harness, g *runGraph, taskID string) (int, string, int) {
	_, ready, _ := h.api(ctx, "GET", h.base+"/tasks/"+taskID, "", "", nil)
	executor := domain.ID()
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		return 0, e.Error(), runRowsFor(ctx, h, taskID)
	}
	code, _, body := h.api(ctx, "POST", h.base+"/tasks/"+taskID+"/claim", domain.ID(), tagOf(ready),
		domain.Object{"runtime_id": g.runtimeID, "executor_principal_id": executor,
			"context_bundle_id": ready["context_bundle_id"]})
	return code, body, runRowsFor(ctx, h, taskID)
}

func startRefusalPhase(ctx context.Context, h *harness, g *runGraph) {
	at := domain.Now()

	// the policy as it was before this phase, so the phase can hand ledgerPhase the same state it
	// would otherwise have seen; nothing here may depend on what an earlier phase left behind
	_, policyBefore, _ := h.api(ctx, "GET", h.base+"/goals/"+g.goalID+"/budget-policy", "", "", nil)
	if policyBefore["id"] == nil {
		ok("W1201-START-REFUSAL-POLICY-READABLE", false, "no goal budget policy")
		return
	}
	ok("W1201-START-REFUSAL-POLICY-READABLE", true, domain.Object{"mode": policyBefore["mode"],
		"enforcement": policyBefore["enforcement"], "unknown_cost_action": policyBefore["unknown_cost_action"]})
	beforeTag := tagOf(policyBefore)

	// 1. an unresolved liability enters while the policy still cannot bound anything
	code, unknown, body := h.ledger(ctx, beforeTag, domain.Object{"policy_id": g.policyID, "run_id": g.runID,
		"operation": "UNKNOWN", "money": nil, "provider_request_id": "startref-unknown",
		"provider_event_id": "startref-unknown-evt", "reservation_id": nil, "cost_basis": "UNKNOWN",
		"occurred_at": at})
	ok("W1201-START-REFUSAL-LIABILITY-PLANTED", code == 201 && unknown["money"] == nil, code, body)
	if code != 201 {
		return
	}

	// 2. the same Goal tightens to a strict cap that blocks unknown cost
	capped := domain.Object{"mode": "CAPPED", "cap": dollars("100.00"), "enforcement": "STRICT",
		"period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": at,
		"unknown_cost_action": "BLOCK"}
	code, tightened, body := h.api(ctx, "PUT", h.base+"/goals/"+g.goalID+"/budget-policy", domain.ID(), beforeTag, capped)
	ok("W1201-START-REFUSAL-CAP-TIGHTENED", code == 200 && domain.Str(tightened, "enforcement") == "STRICT", code, body)
	if code != 200 {
		return
	}
	tightenedTag := tagOf(tightened)

	// 3. the start itself: a second task of the same Goal, no history of its own, refused at claim
	taskID, built := submittedTaskInGoal(ctx, h, g, "claim")
	if !built {
		return
	}
	code, rbody, runs := claimTask(ctx, h, g, taskID)
	ok("W1201-START-REFUSAL-AT-CLAIM",
		code == 422 && strings.Contains(rbody, "unresolved cost prevents bounded admission") && runs == 0,
		domain.Object{"claim_code": code, "run_rows": runs, "body": rbody})
	note("startref-claim", code, rbody)
	if code != 422 {
		return
	}

	// 4. settle exactly what was unresolved, change nothing else, and the identical start is admitted.
	// Without this the refusal above could have been any 422 on any rule.
	code, _, body = h.ledger(ctx, tightenedTag, domain.Object{"policy_id": g.policyID, "run_id": g.runID,
		"operation": "RECONCILE", "money": dollars("0.50"), "provider_request_id": "startref-unknown",
		"provider_event_id": "startref-unknown-settled", "reservation_id": unknown["id"],
		"cost_basis": "ACTUAL", "occurred_at": at})
	ok("W1201-START-REFUSAL-CONTROL-LIABILITY-SETTLED", code == 201, code, body)
	if code != 201 {
		return
	}
	code, rbody, runs = claimTask(ctx, h, g, taskID)
	ok("W1201-START-REFUSAL-CONTROLED-BY-SETTLEMENT", code == 201 && runs == 1,
		domain.Object{"claim_code": code, "run_rows": runs, "body": rbody})
	note("startref-control", code, rbody)

	// 5. leave the Goal policy and ledger as ledgerPhase expects to find them
	restore := domain.Object{"mode": policyBefore["mode"], "cap": policyBefore["cap"],
		"enforcement": policyBefore["enforcement"], "period": policyBefore["period"],
		"timezone": policyBefore["timezone"], "effective_from": policyBefore["effective_from"],
		"unknown_cost_action": policyBefore["unknown_cost_action"]}
	code, back, body := h.api(ctx, "PUT", h.base+"/goals/"+g.goalID+"/budget-policy", domain.ID(),
		etagOfLatestPolicy(ctx, h, g), restore)
	ok("W1201-START-REFUSAL-POLICY-RESTORED", code == 200 &&
		domain.Str(back, "mode") == domain.Str(policyBefore, "mode") &&
		domain.Str(back, "enforcement") == domain.Str(policyBefore, "enforcement"),
		domain.Object{"code": code, "mode": domain.Str(back, "mode"), "body": body})
	g.policyTag = tagOf(back)
}

// etagOfLatestPolicy reads the policy fresh, because the control claim above may have moved the
// ledger and a stale If-Match would turn a passing restore into a false failure.
func etagOfLatestPolicy(ctx context.Context, h *harness, g *runGraph) string {
	_, p, _ := h.api(ctx, "GET", h.base+"/goals/"+g.goalID+"/budget-policy", "", "", nil)
	return tagOf(p)
}
