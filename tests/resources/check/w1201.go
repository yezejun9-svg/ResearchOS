package main

// The W12-01 qualification phases. Everything here is driven through the real HTTP handler over a
// real SQLite database: no assertion is satisfied by a value this program wrote itself into a field
// it also reads back, and every refusal is compared on both halves (Fault.Status and code).

import (
	"context"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"encoding/json"

	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/store"
)

type runGraph struct {
	goalID, taskID, runID, policyID string
	policyTag                       string
	origin, candidate               string
}

func num(o domain.Object, field string) int64 {
	v, e := domain.Num(o, field)
	if e != nil {
		return -1
	}
	return v
}

// defaultsPhase pins step 1: money is unlimited by default, and the retry and no-progress bounds
// stay finite anyway. An unbounded amount must never be read as an unbounded number of attempts.
func defaultsPhase(ctx context.Context, h *harness) {
	_, global, body := h.api(ctx, "GET", "/v1/policies/budget", "", "", nil)
	ok("W1201-GLOBAL-BUDGET-UNLIMITED",
		domain.Str(global, "mode") == "UNLIMITED_AMOUNT" && global["cap"] == nil, global, body)

	_, project, body := h.api(ctx, "GET", h.base+"/budget-policy", "", "", nil)
	ok("W1201-PROJECT-BUDGET-INHERITS-NULL-CAP", project["cap"] == nil, project, body)

	_, policy, body := h.api(ctx, "GET", h.base+"/run-policy", "", "", nil)
	ok("W1201-RUN-POLICY-BOUNDED-DEFAULTS",
		num(policy, "max_concurrency") == 2 &&
			num(policy, "same_failure_retry_limit") == 2 &&
			num(policy, "no_progress_iteration_limit") == 3, policy, body)

	// the two claims must hold together: this card's negative case is precisely "null money read as
	// null retries", so the finite bounds are asserted against the same project that has no cap
	ok("W1201-NULL-CAP-DOES-NOT-UNBOUNDED-RETRY",
		project["cap"] == nil && num(policy, "same_failure_retry_limit") == 2 &&
			num(policy, "no_progress_iteration_limit") == 3,
		domain.Object{"budget_cap": project["cap"], "retry": num(policy, "same_failure_retry_limit"),
			"no_progress": num(policy, "no_progress_iteration_limit")})
}

// orchestrationGraph builds the smallest real object graph that can carry a cost: requirement,
// goal, fixture runtime, task, frozen context bundle, submission and one admitted run.
func orchestrationGraph(ctx context.Context, h *harness) (*runGraph, error) {
	code, req, body := h.api(ctx, "POST", h.base+"/requirements", domain.ID(), h.stateTag(ctx), domain.Object{
		"requirement_key": "REQ-W1201", "text": "spend within the bound that was agreed",
		"basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "cost qualification fixture",
		"supersedes_id": nil, "acceptance_check_ids": domain.Empty()})
	if code != 201 {
		return nil, fmt.Errorf("requirement %d %s", code, body)
	}
	_, acceptedReq, body := h.api(ctx, "POST", h.base+"/requirements/"+domain.Str(req, "id")+"/actions",
		domain.ID(), tagOf(req), domain.Object{"action": "ACCEPT", "reason": "user stated fixture requirement",
			"source_validation_refs": domain.Empty()})
	if acceptedReq["id"] == nil {
		return nil, fmt.Errorf("requirement acceptance %s", body)
	}

	contract := domain.Object{"contract_revision": 1, "require_independent_verifier": true,
		"version_policy": "EXACT", "frozen_at": domain.Now(),
		"checks": []any{domain.Object{"check_id": "w1201-cost-check", "kind": "DETERMINISTIC",
			"required": true, "expected": "settled within bound", "command_key": "test.resources",
			"rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}}
	contract["contract_hash"] = contractDigest(contract)

	goalBody := domain.Object{"title": "w1201 cost qualification", "original_intent": "spend only what is bounded",
		"scope": "PROJECT", "requirement_refs": []any{domain.Ref(acceptedReq, "Requirement")},
		"problem_ids": []any{"p-w1201"}, "deliverables": []any{"settled ledger"}, "acceptance_contract": contract}
	code, goal, body := h.api(ctx, "POST", h.base+"/goals", domain.ID(), h.stateTag(ctx), goalBody)
	if code != 201 {
		return nil, fmt.Errorf("goal %d %s", code, body)
	}
	code, _, body = h.api(ctx, "POST", h.base+"/goals/"+domain.Str(goal, "id")+"/actions", domain.ID(),
		tagOf(goal), domain.Object{"action": "ACTIVATE", "reason": "cost qualification fixture"})
	if code != 200 {
		return nil, fmt.Errorf("goal activation %d %s", code, body)
	}

	code, runtime, body := h.api(ctx, "POST", h.base+"/runtimes", domain.ID(), h.stateTag(ctx), domain.Object{
		"name": "w1201 fixture runtime", "adapter": "fixture", "adapter_revision": "1",
		"capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE",
		"credential_ref": nil})
	if code != 201 {
		return nil, fmt.Errorf("runtime %d %s", code, body)
	}
	if e := h.svc.RegisterOrchestrationFixture(ctx, h.project, domain.Str(runtime, "id")); e != nil {
		return nil, fmt.Errorf("fixture registration %w", e)
	}

	_, goalNow, _ := h.api(ctx, "GET", h.base+"/goals/"+domain.Str(goal, "id"), "", "", nil)
	taskBody := domain.Object{"goal_id": domain.Str(goal, "id"), "title": "w1201 spend task",
		"task_type": "json-verification", "stage": "verification", "dependency_task_ids": domain.Empty(),
		"requirement_refs": []any{domain.Ref(acceptedReq, "Requirement")}, "input_refs": domain.Empty(),
		"acceptance_contract": contract, "origin_problem_id": "p-w1201", "candidate_id": "c-w1201",
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}}
	code, task, body := h.api(ctx, "POST", h.base+"/tasks", domain.ID(), tagOf(goalNow), taskBody)
	if code != 201 {
		return nil, fmt.Errorf("task %d %s", code, body)
	}

	state, _ := h.liveState(ctx)
	code, _, body = h.api(ctx, "POST", h.base+"/context-bundles", domain.ID(), tagOf(state), domain.Object{
		"task_id": domain.Str(task, "id"), "expected_project_state_revision": state["revision"]})
	if code != 201 {
		return nil, fmt.Errorf("context bundle %d %s", code, body)
	}
	_, taskSubmitted, _ := h.api(ctx, "GET", h.base+"/tasks/"+domain.Str(task, "id"), "", "", nil)
	code, _, body = h.api(ctx, "POST", h.base+"/tasks/"+domain.Str(task, "id")+"/actions", domain.ID(),
		tagOf(taskSubmitted), domain.Object{"action": "SUBMIT", "reason": "frozen bundle and contract"})
	if code != 200 {
		return nil, fmt.Errorf("task submit %d %s", code, body)
	}
	_, taskReady, _ := h.api(ctx, "GET", h.base+"/tasks/"+domain.Str(task, "id"), "", "", nil)

	executor := domain.ID()
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		return nil, fmt.Errorf("executor principal %w", e)
	}
	code, _, body = h.api(ctx, "POST", h.base+"/tasks/"+domain.Str(task, "id")+"/claim", domain.ID(),
		tagOf(taskReady), domain.Object{"runtime_id": domain.Str(runtime, "id"),
			"executor_principal_id": executor, "context_bundle_id": taskReady["context_bundle_id"]})
	if code != 201 {
		return nil, fmt.Errorf("claim %d %s", code, body)
	}

	var raw string
	if e := h.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=? ORDER BY rowid DESC LIMIT 1",
		h.project, domain.Str(task, "id")).Scan(&raw); e != nil {
		return nil, fmt.Errorf("run readback %w", e)
	}
	run := domain.Object{}
	if e := json.Unmarshal([]byte(raw), &run); e != nil {
		return nil, fmt.Errorf("run decode %w", e)
	}
	ok("W1201-RUN-ADMITTED", run["id"] != nil, run)

	_, policy, body := h.api(ctx, "GET", h.base+"/goals/"+domain.Str(goal, "id")+"/budget-policy", "", "", nil)
	if policy["id"] == nil {
		return nil, fmt.Errorf("goal budget policy %s", body)
	}
	return &runGraph{goalID: domain.Str(goal, "id"), taskID: domain.Str(task, "id"),
		runID: domain.Str(run, "id"), policyID: domain.Str(policy, "id"),
		policyTag: tagOf(policy), origin: "p-w1201", candidate: "c-w1201"}, nil
}

// ledgerPhase covers steps 2 and 3: reservation, unknown and settled costs stay in separate columns,
// a STRICT cap refuses a cost that cannot be bounded, and a late or repeated provider event is
// reconciled against the original run and idempotency key instead of being charged twice.
func ledgerPhase(ctx context.Context, h *harness, g *runGraph) {
	// one clock value is reused for the replay probe, because the ledger's idempotency compares the
	// whole request payload and a fresh occurred_at is a different request, not a repeated one
	holdAt := domain.Now()
	entry := func(op, request, basis string, money any, event string, reservation any, at string) domain.Object {
		return domain.Object{"policy_id": g.policyID, "run_id": g.runID, "operation": op,
			"money": money, "provider_request_id": request, "provider_event_id": event,
			"reservation_id": reservation, "cost_basis": basis, "occurred_at": at}
	}

	hold := entry("RESERVE", "req-held", "UPPER_BOUND", dollars("2.00"), "evt-held", nil, holdAt)
	code, reserve, body := h.ledger(ctx, g.policyTag, hold)
	ok("W1201-RESERVATION-ADMITTED", code == 201 && reserve["operation"] == "RESERVE", code, body)

	code, unknown, body := h.ledger(ctx, g.policyTag, entry("UNKNOWN", "req-unknown", "UNKNOWN", nil, "evt-unknown", nil, holdAt))
	ok("W1201-UNKNOWN-CARRIES-NO-INVENTED-AMOUNT",
		code == 201 && unknown["money"] == nil && domain.Str(unknown, "cost_basis") == "UNKNOWN", code, body)

	usage, e := h.svc.BudgetUsage(ctx, h.token, h.project, g.runID)
	if e != nil {
		ok("W1201-LEDGER-COLUMNS-SEPARATED", false, e)
		return
	}
	ok("W1201-LEDGER-COLUMNS-SEPARATED",
		countColumn(usage, "reserved", "req-held") == 1 &&
			countColumn(usage, "unknown", "req-unknown") == 1 &&
			countColumn(usage, "incurred", "req-held") == 0 && usage["in_flight_is_subset"] == true, usage)

	// the same provider event arriving twice must return the original entry, not a second charge
	code, replay, body := h.ledger(ctx, g.policyTag, entry("RESERVE", "req-held", "UPPER_BOUND", dollars("2.00"), "evt-held", nil, holdAt))
	ok("W1201-DUPLICATE-BILL-REPLAYS-ORIGINAL",
		code == 201 && domain.Str(replay, "id") == domain.Str(reserve, "id"), code, body)
	var rows int
	if e := h.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=?",
		h.project, "req-held").Scan(&rows); e != nil {
		rows = -1
	}
	ok("W1201-DUPLICATE-BILL-ADDS-NO-ROW", rows == 1, rows)

	// a strict cap may not be satisfied by a cost nobody bounded: unknown and estimate both refuse
	capped := domain.Object{"mode": "CAPPED", "cap": dollars("3.00"), "enforcement": "STRICT",
		"period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": domain.Now(),
		"unknown_cost_action": "BLOCK"}
	_, policyNow, _ := h.api(ctx, "GET", h.base+"/goals/"+g.goalID+"/budget-policy", "", "", nil)
	code, tightened, body := h.api(ctx, "PUT", h.base+"/goals/"+g.goalID+"/budget-policy", domain.ID(),
		tagOf(policyNow), capped)
	ok("W1201-STRICT-CAP-ACCEPTED-AS-POLICY", code == 200 && domain.Str(tightened, "enforcement") == "STRICT", code, body)
	tightenedTag := tagOf(tightened)

	code, _, body = h.ledger(ctx, tightenedTag, entry("UNKNOWN", "req-unknown-2", "UNKNOWN", nil, "evt-unknown-2", nil, holdAt))
	ok("W1201-STRICT-CAP-REFUSES-UNKNOWN-COST", code == 422 && strings.Contains(body, "GATE_FAILED"), code, body)

	code, _, body = h.ledger(ctx, tightenedTag, entry("RESERVE", "req-estimate", "ESTIMATE", dollars("1.00"), "evt-estimate", nil, holdAt))
	ok("W1201-STRICT-CAP-REFUSES-UNPROVEN-ESTIMATE", code == 422 && strings.Contains(body, "GATE_FAILED"), code, body)

	code, _, body = h.ledger(ctx, tightenedTag, entry("RECONCILE", "req-unknown", "ACTUAL", dollars("0.50"), "evt-unknown-settled", unknown["id"], holdAt))
	ok("W1201-UNKNOWN-RECONCILES-WHEN-PROVEN", code == 201, code, body)
	code, _, body = h.ledger(ctx, tightenedTag, entry("RESERVE", "req-over", "UPPER_BOUND", dollars("9.00"), "evt-over", nil, holdAt))
	ok("W1201-STRICT-CAP-REFUSES-OVER-CAP", code == 422 && strings.Contains(body, "budget exhausted"), code, body)

	// late settlement still binds the original run and request even after the cap tightened
	code, settled, body := h.ledger(ctx, tightenedTag, entry("COMMIT", "req-held", "ACTUAL", dollars("1.50"), "evt-held-commit", reserve["id"], holdAt))
	ok("W1201-LATE-USAGE-BINDS-ORIGINAL-RUN",
		code == 201 && domain.Str(settled, "run_id") == g.runID &&
			domain.Str(settled, "provider_request_id") == "req-held", code, body)

	code, _, body = h.ledger(ctx, tightenedTag, entry("COMMIT", "req-held", "ACTUAL", dollars("1.50"), "evt-held-second", reserve["id"], holdAt))
	ok("W1201-SETTLED-REQUEST-REFUSES-SECOND-COMMIT", code == 409 && strings.Contains(body, "already settled"), code, body)

	usage, e = h.svc.BudgetUsage(ctx, h.token, h.project, g.runID)
	if e != nil {
		ok("W1201-COLUMNS-RECOMPUTED-AFTER-SETTLEMENT", false, e)
		return
	}
	ok("W1201-COLUMNS-RECOMPUTED-AFTER-SETTLEMENT",
		countColumn(usage, "incurred", "req-held") == 1 && countColumn(usage, "reserved", "req-held") == 0, usage)
}

// restartPhase proves step 4 the way the card states it: the accounting lives in the store, so
// closing the process and reopening the same database cannot lose a failure fingerprint, and a new
// Goal carrying the same origin and candidate inherits the same record instead of starting clean.
func restartPhase(ctx context.Context, h *harness, g *runGraph) {
	_, before, _ := h.api(ctx, "GET", h.base+"/tasks/"+g.taskID, "", "", nil)
	record := domain.Str(before, "no_progress_record_id")
	var ledgerRows int
	if e := h.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'", h.project).Scan(&ledgerRows); e != nil {
		ledgerRows = -1
	}

	path := filepath.Join(h.dir, "w1201.sqlite")
	if e := h.db.Close(); e != nil {
		ok("W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART", false, e)
		return
	}
	db, e := store.Open(path)
	if e != nil {
		ok("W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART", false, e)
		return
	}
	reopened := &harness{db: db, dir: h.dir}
	reopened.svc, e = domain.New(db, filepath.Join(repoRoot(), "spec", "v2.0", "contracts"),
		filepath.Join(repoRoot(), "migrations", "sqlite", "0002_domain.sql"))
	if e != nil {
		_ = db.Close()
		ok("W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART", false, e)
		return
	}
	reopened.handler = reopened.svc.Handler()
	reopened.project = h.project
	reopened.base = h.base
	reopened.token, e = reopened.svc.IssueCredential(ctx, "w1201-owner", 15*time.Minute)
	if e != nil {
		_ = db.Close()
		ok("W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART", false, e)
		return
	}
	defer db.Close()

	_, after, body := reopened.api(ctx, "GET", reopened.base+"/tasks/"+g.taskID, "", "", nil)
	ok("W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART",
		domain.Str(after, "no_progress_record_id") == record && record != "", domain.Str(after, "no_progress_record_id"), body)

	var surviving int
	if e := db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'", reopened.project).Scan(&surviving); e != nil {
		surviving = -1
	}
	ok("W1201-LEDGER-SURVIVES-PROCESS-RESTART", surviving == ledgerRows && surviving > 0,
		domain.Object{"before": ledgerRows, "after": surviving})

	// a fresh Goal with the same origin and candidate is the "change the Goal to escape the failure
	// budget" case; the record must be inherited, not re-minted at zero
	code, childGoal, childBody := reopened.api(ctx, "POST", reopened.base+"/goals", domain.ID(),
		reopened.stateTag(ctx), domain.Object{"title": "second goal same origin",
			"original_intent": "spend only what is bounded", "scope": "PROJECT",
			"requirement_refs": after["requirement_refs"], "problem_ids": []any{g.origin},
			"deliverables": []any{"settled ledger"}, "acceptance_contract": after["acceptance_contract"]})
	if code != 201 {
		ok("W1201-NEW-GOAL-INHERITS-FAILURE-RECORD", false, childBody)
		return
	}
	reopenedTask := domain.Object{"goal_id": domain.Str(childGoal, "id"), "title": "same origin new goal",
		"task_type": "json-verification", "stage": "verification",
		"dependency_task_ids": domain.Empty(), "requirement_refs": after["requirement_refs"],
		"input_refs": domain.Empty(), "acceptance_contract": after["acceptance_contract"],
		"origin_problem_id": g.origin, "candidate_id": g.candidate,
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}}
	code, shared, body := reopened.api(ctx, "POST", reopened.base+"/tasks", domain.ID(), tagOf(childGoal), reopenedTask)
	ok("W1201-NEW-GOAL-INHERITS-FAILURE-RECORD",
		code == 201 && domain.Str(shared, "no_progress_record_id") == record,
		domain.Object{"record": record, "child": domain.Str(shared, "no_progress_record_id"), "detail": body})

	// the two disclosures this card cannot close, stated rather than dressed up as coverage
	skip("W1201-ATTEMPT-BOUND-HOLDS-ACROSS-RETRIES",
		"driving a task to its attempt limit needs the failed-run lifecycle (observation and report of a terminal run) that belongs to the accepted W05/W06 orchestration fixtures; the counter semantics themselves are asserted by the accepted C16-01 and C16-02 ids, which this program forwards to ops/ci/resources.py unchanged")
	skip("W1201-START-REFUSAL-NEEDS-NO-UNREACHABLE-BRANCH",
		"the only runtime that can reach a start without a provable bound is refused earlier: claimTaskMode (internal/domain/orchestration.go:347) rejects any claim whose runtime is not registered FIXTURE without a qualification, and reserveQualificationDispatch requires a positive max_cost, so a start-time refusal added to reserveFixtureDispatch would be unreachable dead code. Measured by reverting it in the W12-01 remediation (commits 5ae713ea and 15c429d6).")
}

// contractDigest mirrors the rule the service enforces at activation (orchestration.go): the hash
// covers every contract field except the hash itself. A goal cannot be activated without it, so the
// qualification has to compute it the same way rather than pin a value that the gate rejects.
func contractDigest(c domain.Object) string {
	v := domain.Object{}
	for k, x := range c {
		if k != "contract_hash" {
			v[k] = x
		}
	}
	return domain.Hash(v)
}

// countColumn counts the entries of one usage column that belong to a given provider request, so an
// assertion cannot be satisfied by the run's own unrelated fixture reservation.
func countColumn(usage domain.Object, column, request string) int {
	n := 0
	for _, v := range domain.Arr(usage, column) {
		entry, ok := v.(map[string]any)
		if ok && domain.Str(entry, "provider_request_id") == request {
			n++
		}
	}
	return n
}
