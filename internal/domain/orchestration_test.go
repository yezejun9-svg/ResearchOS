package domain

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func orchestrationAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W06_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s mismatch", id)
	}
}

type orchestrationFixture struct {
	f             *fixture
	goal, req, rt Object
	owner         string
}

func orchestrationContract() Object {
	c := Object{"contract_revision": 1, "checks": []any{Object{"check_id": "json-result", "kind": "DETERMINISTIC", "required": true, "expected": `{"result":"verified"}`, "command_key": "orchestration.json-equals", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}}, "require_independent_verifier": true, "version_policy": "EXACT", "frozen_at": Now()}
	c["contract_hash"] = contractDigest(c)
	return c
}
func orchestrationSetup(t *testing.T) *orchestrationFixture {
	f := contextFixture(t)
	req := f.requirement()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "Orchestration development fixture", "original_intent": "Accept verified output before successor", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "development fixture"})
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "fixture observation producer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); e != nil {
		t.Fatal(e)
	}
	return &orchestrationFixture{f, goal, req, rt, f.token}
}
func (o *orchestrationFixture) task(title string, deps []any, inputs []any) Object {
	f := o.f
	f.token = o.owner
	o.goal = f.read("goals", Str(o.goal, "id"))
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(o.goal), Object{"goal_id": o.goal["id"], "title": title, "task_type": "json-verification", "stage": "verification", "dependency_task_ids": deps, "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": inputs, "acceptance_contract": orchestrationContract(), "origin_problem_id": "orchestration-problem", "candidate_id": title, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	return f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen checks and current bundle"})
}
func (o *orchestrationFixture) claim(task Object) *runtimeFixture {
	f := o.f
	f.token = o.owner
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		f.t.Fatal(e)
	}
	response := f.expect(201, "POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task), Object{"runtime_id": o.rt["id"], "executor_principal_id": executor, "context_bundle_id": task["context_bundle_id"]})
	r := &runtimeFixture{f: f, ownerToken: o.owner, executor: executor, lease: Str(response, "lease_token"), task: response["task"].(map[string]any), run: response["run"].(map[string]any), registration: o.rt}
	var e error
	f.token, e = f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		f.t.Fatal(e)
	}
	return r
}
func (o *orchestrationFixture) report(r *runtimeFixture, raw []byte) Object {
	f := o.f
	r.call("/heartbeat", r.heartbeat(), 200)
	executorToken := f.token
	f.token = o.owner
	tag := f.stateTag()
	f.token = executorToken
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	a := f.expect(201, "POST", f.path("/artifacts"), ID(), tag, Object{"run_id": r.run["id"], "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": r.task["input_refs"], "source_refs": Empty(), "produced_by": r.executor, "access_class": "PROJECT"})
	obs := r.observation("SETTLED", true)
	obs["artifacts"] = []any{Object{"path": "result.json", "content_hash": a["content_hash"], "byte_size": a["byte_size"]}}
	r.observe(obs)
	r.call("/report", r.report([]any{a["id"]}, 0), 200)
	f.token = o.owner
	r.task = f.read("tasks", Str(r.task, "id"))
	return a
}
func (o *orchestrationFixture) acceptance(r *runtimeFixture, a Object) Object {
	f := o.f
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	c := r.task["acceptance_contract"].(map[string]any)
	checks := Empty()
	for _, v := range Arr(c, "checks") {
		x := v.(map[string]any)
		checks = append(checks, Object{"check_id": x["check_id"], "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": x["command_key"], "actual": "request independent service computation", "exit_code": nil, "started_at": nil, "finished_at": nil})
	}
	return Object{"subject_ref": Ref(r.task, "Task"), "run_id": r.run["id"], "contract_hash": c["contract_hash"], "input_refs": r.task["input_refs"], "artifact_refs": []any{Ref(a, "Artifact")}, "checks": checks, "verdict": "PASS", "executor_principal_ids": []any{r.executor}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": f.state()["policy_revision"], "measurement_mode": "FIXTURE", "reason": "independent frozen computation"}
}
func TestW06DispatchAcceptance(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	first := o.task("first", Empty(), Empty())
	next := o.task("next", []any{first["id"]}, Empty())
	orchestrationAssert(t, "W06-G01-DAG", []any{"READY", "BLOCKED"}, []any{first["status"], next["status"]}, nil)
	r := o.claim(first)
	body := Object{"runtime_id": o.rt["id"], "executor_principal_id": r.executor, "context_bundle_id": first["context_bundle_id"]}
	f.token = o.owner
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(first, "id")+"/claim"), ID(), testTag(first), body)
	orchestrationAssert(t, "W06-G01-CAS", 412, status, reply)
	f.token, _ = f.s.IssueCredential(context.Background(), r.executor, time.Minute)
	a := o.report(r, []byte(`{"result":"verified"}`))
	next = f.read("tasks", Str(next, "id"))
	orchestrationAssert(t, "W06-G01-REPORT-ONLY", []any{"EXECUTION_REPORTED", "BLOCKED"}, []any{r.task["status"], next["status"]}, nil)
	b := o.acceptance(r, a)
	key := ID()
	tag := testTag(r.task)
	receipt := f.expect(201, "POST", f.path("/acceptances"), key, tag, b)
	f.expect(201, "POST", f.path("/acceptances"), key, tag, b)
	task := f.read("tasks", Str(first, "id"))
	next = f.read("tasks", Str(next, "id"))
	orchestrationAssert(t, "W06-G01-ATOMIC-ACCEPT", []any{"PASS", "ACCEPTED", "READY"}, []any{receipt["verdict"], task["status"], next["status"]}, Object{"receipt": receipt, "task": task, "successor": next})
}
