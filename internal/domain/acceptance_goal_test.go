package domain

import "testing"

func TestW06GoalAcceptance(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	r := o.claim(o.task("goal-deliverable", Empty(), Empty()))
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	g := f.read("goals", Str(o.goal, "id"))
	gc := g["acceptance_contract"].(map[string]any)
	goalRequest, _ := Decode(Bytes(b))
	goalRequest["subject_ref"] = Ref(g, "Goal")
	goalRequest["run_id"] = nil
	goalRequest["contract_hash"] = gc["contract_hash"]
	goalRequest["input_refs"] = []any{Ref(o.req, "Requirement"), Ref(r.task, "Task")}
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(g), goalRequest)
	orchestrationAssert(t, "W06-G01-GOAL-UNACCEPTED-TASK", 409, status, reply)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	accepted := f.read("tasks", Str(r.task, "id"))
	goalRequest["input_refs"] = []any{Ref(o.req, "Requirement"), Ref(accepted, "Task")}
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(g), goalRequest)
	goal := f.read("goals", Str(g, "id"))
	state := f.state()
	orchestrationAssert(t, "W06-G01-GOAL-ATOMIC-ACCEPT", []any{"PASS", "ACCEPTED", 0}, []any{receipt["verdict"], goal["status"], len(Arr(state, "active_goal_ids"))}, Object{"receipt": receipt, "goal": goal})
}

func TestW06AdmissionRubric(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("admission", Empty(), Empty())
	live := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "unqualified LIVE runtime", "adapter": "codex-cli", "adapter_revision": "fixture-not-qualified", "capabilities": Empty(), "platform": "windows-amd64", "measurement_mode": "LIVE", "credential_ref": nil})
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/claim"), ID(), testTag(task), Object{"runtime_id": live["id"], "executor_principal_id": f.owner, "context_bundle_id": task["context_bundle_id"]})
	orchestrationAssert(t, "W06-G01-LIVE-ADMISSION-CLOSED", 503, status, reply)
	// A required model rubric remains unavailable; no declared score/qualification
	// or deterministic substitute can make the mandatory check PASS.
	c := orchestrationContract()
	check := Arr(c, "checks")[0].(map[string]any)
	check["kind"] = "MODEL_RUBRIC"
	check["command_key"] = nil
	c["contract_hash"] = contractDigest(c)
	body := Object{}
	for _, k := range []string{"goal_id", "task_type", "stage", "dependency_task_ids", "requirement_refs", "input_refs", "stop_policy"} {
		body[k] = task[k]
	}
	body["title"] = "model rubric fail closed"
	body["acceptance_contract"] = c
	body["origin_problem_id"] = "orchestration-problem"
	body["candidate_id"] = "model-rubric"
	goal := f.read("goals", Str(o.goal, "id"))
	model := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), body)
	f.bundle(model)
	model = f.read("tasks", Str(model, "id"))
	model = f.expect(200, "POST", f.path("/tasks/"+Str(model, "id")+"/actions"), ID(), testTag(model), Object{"action": "SUBMIT", "reason": "prove unavailable qualified model gate"})
	r := o.claim(model)
	a := o.report(r, []byte(`{"result":"verified"}`))
	request := o.acceptance(r, a)
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), request)
	orchestrationAssert(t, "W06-G01-RUBRIC-NO-SUBSTITUTE", 422, status, reply)
	request["verdict"] = "BLOCKED"
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), request)
	orchestrationAssert(t, "W06-G01-RUBRIC-BLOCKED", []any{"BLOCKED", "NOT_RUN"}, []any{receipt["verdict"], Arr(receipt, "checks")[0].(map[string]any)["status"]}, receipt)
}
