package domain

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func impactReject(t *testing.T, id string, actual int, expected ...int) {
	t.Helper()
	pass := false
	for _, status := range expected {
		pass = pass || actual == status
	}
	fmt.Println("W04_ANALYZE_ASSERTION " + string(Bytes(Object{"id": id, "expected": expected, "actual": actual, "status": map[bool]string{true: "PASS", false: "FAIL"}[pass]})))
	if !pass {
		t.Fatalf("%s: status %d, expected %v", id, actual, expected)
	}
}

func impactTask(o *orchestrationFixture, inputs []any) Object {
	f := o.f
	f.token = o.owner
	o.goal = f.read("goals", Str(o.goal, "id"))
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(o.goal), Object{
		"goal_id": o.goal["id"], "title": "Review a frozen change impact", "task_type": "impact_review", "stage": "verification",
		"dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": inputs,
		"acceptance_contract": orchestrationContract(), "origin_problem_id": "orchestration-problem", "candidate_id": "impact-review",
		"stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}},
	})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	return f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen impact review"})
}

func impactSetup(t *testing.T) (*orchestrationFixture, Object, Object, Object, Object) {
	o := orchestrationSetup(t)
	f := o.f
	value := f.artifact("revised requirement", Empty())
	// A normal task with frozen edit inputs exists before the proposal. Its Run
	// can then report the proposal ID and immutable contract hash exactly.
	inputs := []any{Ref(o.req, "Requirement"), Ref(value, "Artifact")}
	task := impactTask(o, inputs)
	extra := f.artifact(Object{"independent": true}, Empty())
	downstream := o.task("semantic-downstream", Empty(), Empty())
	f.link(Ref(downstream, "Task"), Ref(extra, "Artifact"))
	state := f.state()
	proposal := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{
		"title": "Revise requirement", "reason": "fixture impact review", "base_state_revision": state["revision"],
		"edits":           []any{Object{"target_ref": Ref(o.req, "Requirement"), "field": "text", "proposed_value_artifact_ref": Ref(value, "Artifact"), "reason": "explicit revision"}},
		"migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"submit a checked reversal"},
	})
	return o, proposal, task, extra, downstream
}

func impactRun(o *orchestrationFixture, proposal, task Object, additional, conflicts []any) *runtimeFixture {
	r := o.claim(task)
	report := Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": additional, "conflict_ids": conflicts, "reason": "reviewed explicit dependency effects"}
	o.report(r, Bytes(report))
	return r
}

func impactAnalyze(o *orchestrationFixture, proposal Object, r *runtimeFixture, additional, conflicts []any) Object {
	f := o.f
	f.token = o.owner
	return f.expect(200, "POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), Object{
		"semantic_review_run_id": r.run["id"], "additional_impacted_refs": additional, "conflict_ids": conflicts,
	})
}

func impactAcceptanceRequest(f *fixture, proposal Object) Object {
	return Object{"subject_ref": Ref(proposal, "ChangeProposal"), "run_id": nil, "contract_hash": changeHash(proposal),
		"input_refs": []any{Ref(proposal, "ChangeProposal")}, "artifact_refs": Empty(),
		"checks":  []any{Object{"check_id": "client-not-authoritative", "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": nil, "actual": "server must recompute", "exit_code": nil, "started_at": nil, "finished_at": nil}},
		"verdict": "BLOCKED", "executor_principal_ids": Empty(), "independence_basis": "DETERMINISTIC_SERVICE",
		"blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": f.state()["policy_revision"],
		"measurement_mode": "FIXTURE", "reason": "recheck current authority"}
}

func TestW04AnalyzeHTTPAcceptanceApply(t *testing.T) {
	o, proposal, task, extra, downstream := impactSetup(t)
	f := o.f
	// The review adds an artifact dependency and its downstream Task.
	r := impactRun(o, proposal, task, []any{Ref(extra, "Artifact")}, Empty())
	analyzed := impactAnalyze(o, proposal, r, []any{Ref(extra, "Artifact")}, Empty())
	if analyzed["semantic_review_run_id"] != r.run["id"] || len(Arr(analyzed, "impacted_refs")) == 0 || len(Arr(analyzed, "impact_link_ids")) == 0 {
		t.Fatal("semantic impact not retained", analyzed)
	}
	for _, value := range Arr(proposal, "impacted_refs") {
		old := value.(map[string]any)
		retained := false
		for _, value := range Arr(analyzed, "impacted_refs") {
			current := value.(map[string]any)
			retained = retained || old["entity_type"] == current["entity_type"] && old["id"] == current["id"]
		}
		if !retained {
			t.Fatal("deterministic impact disappeared", old)
		}
	}
	if !hasExactRef(Arr(analyzed, "impacted_refs"), Ref(downstream, "Task")) {
		t.Fatal("downstream closure missing", analyzed)
	}
	receipt := f.accept(analyzed)
	if receipt["verdict"] != "PASS" {
		t.Fatal(receipt)
	}
	f.token = o.owner
	applied := f.expect(200, "POST", f.path("/change-proposals/"+Str(analyzed, "id")+"/apply"), ID(), testTag(analyzed), Object{"acceptance_id": receipt["id"], "expected_project_state_revision": f.state()["revision"]})
	if applied["status"] != "APPLIED" || f.read("tasks", Str(downstream, "id"))["status"] != "NEEDS_REVALIDATION" {
		t.Fatal("independently accepted impact was not applied", applied)
	}
}

func TestW04AnalyzeRejectsUnsettledAndForeignRun(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := o.claim(task)
	f.token = o.owner
	body := Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": Empty()}
	status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), body)
	impactReject(t, "unsettled-run", status, 422)
	foreign := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: foreign, Roles: []string{"PLANNER"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), foreign, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f.token = token
	status, _, _ = f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), body)
	impactReject(t, "unsettled-run-other-caller", status, 422)
	// A real Run in a second project cannot be loaded through this proposal's
	// project scope, even when the caller has access to both projects.
	f.token = o.owner
	originalProject := f.project
	f.createProject()
	foreignReq := f.requirement()
	foreignGoal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{
		"title": "Foreign review fixture", "original_intent": "foreign project", "scope": "PROJECT", "requirement_refs": []any{Ref(foreignReq, "Requirement")},
		"problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"report"}, "acceptance_contract": orchestrationContract(),
	})
	foreignGoal = f.expect(200, "POST", f.path("/goals/"+Str(foreignGoal, "id")+"/actions"), ID(), testTag(foreignGoal), Object{"action": "ACTIVATE", "reason": "fixture"})
	foreignRuntime := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "foreign fixture", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(foreignRuntime, "id")); e != nil {
		t.Fatal(e)
	}
	foreignOrchestration := &orchestrationFixture{f: f, goal: foreignGoal, req: foreignReq, rt: foreignRuntime, owner: o.owner}
	foreignTask := foreignOrchestration.task("foreign-run", Empty(), Empty())
	foreignRun := foreignOrchestration.claim(foreignTask)
	f.project = originalProject
	f.token = o.owner
	body["semantic_review_run_id"] = foreignRun.run["id"]
	status, _, _ = f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), body)
	impactReject(t, "foreign-project-run", status, 404)
}

func TestW04AnalyzeReportBindingAndTamper(t *testing.T) {
	t.Run("wrong proposal", func(t *testing.T) {
		o, proposal, task, _, _ := impactSetup(t)
		f := o.f
		r := impactRun(o, proposal, task, Empty(), Empty())
		state := f.state()
		other := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{
			"title": "Another proposal", "reason": "same edit, different proposal identity", "base_state_revision": state["revision"],
			"edits": proposal["edits"], "migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"checked reversal"},
		})
		status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(other, "id")+"/analyze"), ID(), testTag(other), Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": Empty()})
		impactReject(t, "wrong-proposal-report", status, 422)
	})
	t.Run("forged sealed report", func(t *testing.T) {
		o, proposal, task, _, _ := impactSetup(t)
		f := o.f
		r := o.claim(task)
		o.report(r, Bytes(Object{"proposal_id": proposal["id"], "change_contract_hash": "sha256:forged", "additional_impacted_refs": Empty(), "conflict_ids": Empty(), "reason": "forged contract"}))
		status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": Empty()})
		impactReject(t, "forged-sealed-report", status, 422)
	})
}

func TestW04AnalyzeRejectsStaleEditInputs(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := impactRun(o, proposal, task, Empty(), Empty())
	newValue := f.artifact("newer requirement", Empty())
	state := f.state()
	newer := f.expect(201, "POST", f.path("/change-proposals"), ID(), testTag(state), Object{
		"title": "Newer requirement", "reason": "invalidate old review input", "base_state_revision": state["revision"],
		"edits":           []any{Object{"target_ref": Ref(o.req, "Requirement"), "field": "text", "proposed_value_artifact_ref": Ref(newValue, "Artifact"), "reason": "new version"}},
		"migration_steps": Empty(), "test_check_ids": changeChecks, "rollback_steps": []any{"checked reversal"},
	})
	f.apply(newer)
	status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": Empty()})
	impactReject(t, "stale-edit-inputs", status, 409, 412, 422)
}

func TestW04AnalyzeRejectsUnrelatedConflict(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := o.claim(task)
	executorToken := f.token
	f.token = o.owner
	a := f.artifact(Object{"unrelated": 1}, Empty())
	b := f.artifact(Object{"unrelated": 2}, Empty())
	conflict := f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{
		"kind": "ARTIFACT", "subject_refs": []any{Ref(a, "Artifact"), Ref(b, "Artifact")},
		"description": "unrelated artifact disagreement", "blocks_refs": Empty(),
	})
	f.token = executorToken
	o.report(r, Bytes(Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": Empty(), "conflict_ids": []any{conflict["id"]}, "reason": "claim unrelated conflict"}))
	f.token = o.owner
	status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": []any{conflict["id"]}})
	impactReject(t, "unrelated-conflict", status, 422)
}

func TestW04AnalyzeRejectsForeignReference(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	originalProject := f.project
	f.createProject()
	foreign := f.requirement()
	f.project = originalProject
	r := impactRun(o, proposal, task, []any{Ref(foreign, "Requirement")}, Empty())
	status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(proposal, "id")+"/analyze"), ID(), testTag(proposal), Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": []any{Ref(foreign, "Requirement")}, "conflict_ids": Empty()})
	impactReject(t, "foreign-impact-reference", status, 404, 422)
}

func TestW04AnalyzeConflictStaysOpen(t *testing.T) {
	o, proposal, task, extra, _ := impactSetup(t)
	f := o.f
	r := o.claim(task)
	executorToken := f.token
	f.token = o.owner
	conflict := f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{
		"kind": "ARTIFACT", "subject_refs": []any{Ref(extra, "Artifact"), Ref(o.req, "Requirement")},
		"description": "review found contradictory impact", "blocks_refs": []any{Ref(task, "Task")},
	})
	report := Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": []any{Ref(extra, "Artifact")}, "conflict_ids": []any{conflict["id"]}, "reason": "unresolved contradictory impact"}
	f.token = executorToken
	o.report(r, Bytes(report))
	analyzed := impactAnalyze(o, proposal, r, []any{Ref(extra, "Artifact")}, []any{conflict["id"]})
	if analyzed["status"] != "BLOCKED" || f.read("conflicts", Str(conflict, "id"))["status"] != "OPEN" {
		t.Fatal("review conflict did not remain open", analyzed)
	}
	status, _, _ := f.request("POST", f.path("/change-proposals/"+Str(analyzed, "id")+"/apply"), ID(), testTag(analyzed), Object{"acceptance_id": ID(), "expected_project_state_revision": f.state()["revision"]})
	impactReject(t, "blocked-review-apply", status, 409)
	if f.read("conflicts", Str(conflict, "id"))["status"] != "OPEN" {
		t.Fatal("blocked review resolved conflict")
	}
}

func TestW04AnalyzeCASReplayAndRevokedVerifier(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := impactRun(o, proposal, task, Empty(), Empty())
	path := f.path("/change-proposals/" + Str(proposal, "id") + "/analyze")
	body := Object{"semantic_review_run_id": r.run["id"], "additional_impacted_refs": Empty(), "conflict_ids": Empty()}
	key := ID()
	status, first, _ := f.request("POST", path, key, testTag(proposal), body)
	if status != 200 {
		t.Fatalf("initial analysis failed: %d %s", status, Bytes(first))
	}
	status, replay, _ := f.request("POST", path, key, testTag(proposal), body)
	if status != 200 || Hash(replay) != Hash(first) {
		t.Fatalf("idempotency replay changed: %d", status)
	}
	status, _, _ = f.request("POST", path, ID(), testTag(proposal), body)
	impactReject(t, "stale-if-match", status, 412)
	status, _, _ = f.request("POST", path, ID(), "", body)
	impactReject(t, "missing-if-match", status, 428)
	f.switchPrincipal("impact-reader", []string{"READER"})
	status, _, _ = f.request("POST", path, ID(), testTag(first), body)
	impactReject(t, "reader-role", status, 403)
	f.token = o.owner
	receipt := f.accept(first)
	if e := f.s.RevokePrincipal(context.Background(), Str(receipt, "verifier_principal_id")); e != nil {
		t.Fatal(e)
	}
	f.token = o.owner
	status, _, _ = f.request("POST", f.path("/change-proposals/"+Str(first, "id")+"/apply"), ID(), testTag(first), Object{"acceptance_id": receipt["id"], "expected_project_state_revision": f.state()["revision"]})
	impactReject(t, "revoked-verifier-at-apply", status, 403)
}

func TestW04AnalyzeRevokedExecutorBeforeAcceptance(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := impactRun(o, proposal, task, Empty(), Empty())
	analyzed := impactAnalyze(o, proposal, r, Empty(), Empty())
	if e := f.s.RevokePrincipal(context.Background(), r.executor); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("impact-independent-verifier", []string{"VERIFIER"})
	body := impactAcceptanceRequest(f, analyzed)
	status, _, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(analyzed), body)
	impactReject(t, "revoked-executor-at-accept", status, 403)
}

func TestW04AnalyzeExecutorAliasCannotAccept(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := impactRun(o, proposal, task, Empty(), Empty())
	analyzed := impactAnalyze(o, proposal, r, Empty(), Empty())
	alias := "impact-executor-alias"
	f.switchPrincipal(alias, []string{"VERIFIER"})
	if e := f.s.RegisterExecutionIdentity(context.Background(), alias, r.executor); e != nil {
		t.Fatal(e)
	}
	body := impactAcceptanceRequest(f, analyzed)
	status, _, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(analyzed), body)
	impactReject(t, "executor-alias-self-accept", status, 403)
}

func TestW04AnalyzeContinuesAfterFormalResolution(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	r := o.claim(task)
	executorToken := f.token
	f.token = o.owner
	rubric := f.artifact(Object{"rubric": "explicit fixture decision"}, Empty())
	d1 := f.decision(o.req, rubric, nil, "A")
	d2 := f.decision(o.req, rubric, d1["id"], "B")
	conflict := f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{
		"kind": "REVISION", "subject_refs": []any{Ref(d1, "DecisionReceipt"), Ref(d2, "DecisionReceipt")},
		"description": "choose one decision generation", "blocks_refs": Empty(),
	})
	f.token = executorToken
	o.report(r, Bytes(Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": []any{Ref(d2, "DecisionReceipt")}, "conflict_ids": []any{conflict["id"]}, "reason": "decision conflict affects requirement"}))
	blocked := impactAnalyze(o, proposal, r, []any{Ref(d2, "DecisionReceipt")}, []any{conflict["id"]})
	if blocked["status"] != "BLOCKED" {
		t.Fatal(blocked)
	}
	// A separate integration Task and independently accepted change formally
	// resolve the conflict. The blocked proposal itself does not do so.
	integration := f.task(o.req, Empty(), "integration")
	f.bundle(integration)
	integration = f.read("tasks", Str(integration, "id"))
	formal := f.apply(f.proposal([]any{Ref(d2, "DecisionReceipt")}, Ref(integration, "Task")))
	if formal["status"] != "APPLIED" || f.read("conflicts", Str(conflict, "id"))["status"] != "RESOLVED" {
		t.Fatal("formal resolution failed", formal)
	}
	f.token = o.owner
	continuationTask := impactTask(o, reviewInputs(blocked))
	continuationRun := o.claim(continuationTask)
	o.report(continuationRun, Bytes(Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": Empty(), "conflict_ids": Empty(), "reason": "resolved conflict rechecked; prior impact retained", "previous_review_run_id": r.run["id"]}))
	continued := impactAnalyze(o, blocked, continuationRun, Empty(), Empty())
	if continued["status"] != "IMPACT_ANALYZED" || !hasExactRef(Arr(continued, "impacted_refs"), Ref(d2, "DecisionReceipt")) || len(Arr(continued, "impact_link_ids")) < len(Arr(blocked, "impact_link_ids")) {
		t.Fatal("continuation dropped prior impact", continued)
	}
	receipt := f.accept(continued)
	f.token = o.owner
	applied := f.expect(200, "POST", f.path("/change-proposals/"+Str(continued, "id")+"/apply"), ID(), testTag(continued), Object{"acceptance_id": receipt["id"], "expected_project_state_revision": f.state()["revision"]})
	if applied["status"] != "APPLIED" {
		t.Fatal(applied)
	}
}

func TestW04AnalyzeRepeatAddsImpact(t *testing.T) {
	o, proposal, task, _, _ := impactSetup(t)
	f := o.f
	firstRun := impactRun(o, proposal, task, Empty(), Empty())
	first := impactAnalyze(o, proposal, firstRun, Empty(), Empty())
	f.token = o.owner
	extra := f.artifact(Object{"later_review": true}, Empty())
	secondTask := impactTask(o, reviewInputs(first))
	secondRun := o.claim(secondTask)
	o.report(secondRun, Bytes(Object{"proposal_id": proposal["id"], "change_contract_hash": changeHash(proposal), "additional_impacted_refs": []any{Ref(extra, "Artifact")}, "conflict_ids": Empty(), "reason": "second review added an effect", "previous_review_run_id": firstRun.run["id"]}))
	second := impactAnalyze(o, first, secondRun, []any{Ref(extra, "Artifact")}, Empty())
	if second["status"] != "IMPACT_ANALYZED" || !hasExactRef(Arr(second, "impacted_refs"), Ref(extra, "Artifact")) || len(Arr(second, "impacted_refs")) < len(Arr(first, "impacted_refs")) {
		t.Fatal("repeat analysis removed or missed an impact", second)
	}
	receipt := f.accept(second)
	f.token = o.owner
	if applied := f.expect(200, "POST", f.path("/change-proposals/"+Str(second, "id")+"/apply"), ID(), testTag(second), Object{"acceptance_id": receipt["id"], "expected_project_state_revision": f.state()["revision"]}); applied["status"] != "APPLIED" {
		t.Fatal(applied)
	}
}
