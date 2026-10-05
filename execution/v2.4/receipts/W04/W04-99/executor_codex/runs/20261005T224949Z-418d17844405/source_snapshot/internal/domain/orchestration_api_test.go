package domain

import (
	"strings"
	"testing"
)

func TestW06APIConstraints(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	budget := f.expect(200, "GET", f.path("/budget-policy"), "", "", nil)
	vectors := []struct {
		id, schema string
		value      any
	}{
		{"FLOAT-MONEY", "Money", Object{"amount": 1.2, "currency": "USD"}},
		{"CAP-ZERO", "BudgetPolicy", Merge(Merge(Object{}, budget), Object{"mode": "UNLIMITED_AMOUNT", "cap": Object{"amount": "0", "currency": "USD"}})},
		{"NAIVE-TIME", "UtcTime", "2026-09-29T20:00:00"},
		{"REVISION-ZERO", "BudgetPolicy", Merge(Merge(Object{}, budget), Object{"revision": 0})},
	}
	for _, v := range vectors {
		err := f.s.Contracts.Validate(v.schema, v.value)
		orchestrationAssert(t, "A03-01-"+v.id, true, err != nil, Object{"schema": v.schema, "input": v.value, "writes": 0})
	}
	encoded := Bytes(budget)
	decoded, e := Decode(encoded)
	if e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "A03-01-ROUNDTRIP", []any{Hash(budget), true, "UNLIMITED_AMOUNT"}, []any{Hash(decoded), decoded["cap"] == nil, decoded["mode"]}, Object{"serialized": string(encoded), "sha256": Digest(encoded)})
	task := o.task("http-contracts", Empty(), Empty())
	body := Object{"action": "SUBMIT", "reason": "cannot resubmit READY task"}
	stateBefore := f.read("tasks", Str(task, "id"))
	var before int
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&before)
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), body)
	var after int
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&after)
	orchestrationAssert(t, "A03-02-INVALID-STATE", []any{409, Hash(stateBefore), before}, []any{status, Hash(f.read("tasks", Str(task, "id"))), after}, Object{"request": body, "response": reply})
	status, reply, _ = f.request("GET", "/v1/projects/unknown-project/tasks/"+Str(task, "id"), "", "", nil)
	orchestrationAssert(t, "A03-02-PROJECT-ISOLATION", []any{404, false}, []any{status, strings.Contains(string(Bytes(reply)), Str(task, "title"))}, reply)
	state := f.expect(200, "GET", f.path("/state"), "", "", nil)
	key := ID()
	req := requirementBody()
	req["requirement_key"] = "HTTP-UNIQUE"
	created := f.expect(201, "POST", f.path("/requirements"), key, testTag(state), req)
	altered := Merge(Merge(Object{}, req), Object{"text": "different body same key"})
	status, reply, _ = f.request("POST", f.path("/requirements"), key, testTag(state), altered)
	orchestrationAssert(t, "A03-02-IDEMPOTENCY", 409, status, Object{"request": altered, "response": reply, "created": Ref(created, "Requirement")})
	status, reply, _ = f.request("POST", f.path("/requirements"), ID(), testTag(state), req)
	orchestrationAssert(t, "A03-02-STALE-REVISION", 412, status, reply)
	// HTTP request validation rejects a naive UTC frozen contract before writes.
	g := f.read("goals", Str(o.goal, "id"))
	contract := orchestrationContract()
	contract["frozen_at"] = "2026-09-29T20:00:00"
	taskBody := Object{"goal_id": g["id"], "title": "naive-http", "task_type": "fixture", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": contract, "origin_problem_id": "problem", "candidate_id": "candidate", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}}
	var taskCount int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Task'").Scan(&taskCount)
	status, reply, _ = f.request("POST", f.path("/tasks"), ID(), testTag(g), taskBody)
	var taskCountAfter int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Task'").Scan(&taskCountAfter)
	orchestrationAssert(t, "A03-01-HTTP-NO-WRITE", []any{400, taskCount}, []any{status, taskCountAfter}, Object{"request": taskBody, "response": reply})
}
