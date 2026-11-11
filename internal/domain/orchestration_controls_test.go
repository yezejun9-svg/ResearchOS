package domain

import (
	"testing"
)

func TestW06TaskControls(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("pause-ready", Empty(), Empty())
	pause := f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "PAUSE", "reason": "owner waits for input"})
	var reason string
	if e := f.db.QueryRow("SELECT reason FROM orchestration_task_controls WHERE project=? AND task=?", f.project, task["id"]).Scan(&reason); e != nil {
		t.Fatal(e)
	}
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(pause), Object{"action": "RESUME", "reason": "input restored"})
	orchestrationAssert(t, "W06-G01-PAUSE-RESUME", []any{"BLOCKED", "owner waits for input", "READY"}, []any{pause["status"], reason, task["status"]}, nil)
	r := o.claim(task)
	executorToken := f.token
	f.token = o.owner
	running := f.read("tasks", Str(task, "id"))
	pause = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(running), Object{"action": "PAUSE", "reason": "stop before resuming"})
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(pause), Object{"action": "RESUME", "reason": "unsafe early resume"})
	run := f.read("runs", Str(r.run, "id"))
	orchestrationAssert(t, "W06-G01-PAUSE-STOP-FENCE", []any{"BLOCKED", "CANCEL_REQUESTED", 409}, []any{pause["status"], run["status"], status}, reply)
	f.token = executorToken
	r.run = run
	observation := r.observation("CANCELLED", false)
	r.observe(observation)
	raw := Bytes(observation)
	f.token = o.owner
	tag := f.stateTag()
	f.token = executorToken
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	receipt := f.expect(201, "POST", f.path("/artifacts"), ID(), tag, Object{"run_id": r.run["id"], "kind": "LOG", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": r.executor, "access_class": "PROJECT"})
	r.call("/cancel-ack", Object{"lease_token": r.lease, "lease_epoch": r.run["lease_epoch"], "children_stopped": true, "queue_empty": true, "receipt_artifact_ref": Ref(receipt, "Artifact")}, 200)
	f.token = o.owner
	paused := f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(paused), Object{"action": "RESUME", "reason": "trusted stop confirmed"})
	cancelled := f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "CANCEL", "reason": "owner cancels settled task"})
	status, _, _ = f.request("POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(cancelled), Object{"action": "RESUME", "reason": "cannot revive terminal cancellation"})
	orchestrationAssert(t, "W06-G01-CONFIRMED-RESUME-CANCEL", []any{"BLOCKED", "READY", "CANCELLED", 409}, []any{paused["status"], task["status"], cancelled["status"], status}, nil)
}

func TestW06NoProgress(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("same-candidate", Empty(), Empty())
	original := task
	statuses := Empty()
	for i := 0; i < 3; i++ {
		r := o.claim(task)
		obs := r.observation("FAILED", false)
		obs["artifacts"] = Empty()
		r.observe(obs)
		r.call("/report", r.report(Empty(), 0), 200)
		f.token = o.owner
		task = f.read("tasks", Str(task, "id"))
		statuses = append(statuses, task["status"])
		if i < 2 {
			task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "bounded same failure retry"})
		}
	}
	var raw string
	f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='NoProgressRecord' AND id=?", task["no_progress_record_id"]).Scan(&raw)
	n, _ := Decode([]byte(raw))
	orchestrationAssert(t, "W06-G01-NO-PROGRESS-BOUNDS", []any{[]any{"FAILED", "FAILED", "DEFERRED_NO_PROGRESS"}, 3, 3}, []any{statuses, n["same_failure_count"], n["no_progress_iterations"]}, n)
	body := Object{}
	for _, k := range []string{"goal_id", "task_type", "stage", "dependency_task_ids", "requirement_refs", "input_refs", "acceptance_contract", "stop_policy"} {
		body[k] = original[k]
	}
	body["title"] = "renamed but same cause"
	body["origin_problem_id"] = n["origin_problem_id"]
	body["candidate_id"] = n["candidate_id"]
	goal := f.read("goals", Str(o.goal, "id"))
	renamed := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), body)
	f.bundle(renamed)
	renamed = f.read("tasks", Str(renamed, "id"))
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(renamed, "id")+"/actions"), ID(), testTag(renamed), Object{"action": "SUBMIT", "reason": "rename should not reset"})
	orchestrationAssert(t, "W06-G01-NO-PROGRESS-RENAME", []any{true, 409}, []any{renamed["no_progress_record_id"] == task["no_progress_record_id"], status}, reply)
	alternate := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "new goal same failed candidate", "original_intent": "verify stable retry origin", "scope": "PROJECT", "requirement_refs": []any{Ref(o.req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
	alternate = f.expect(200, "POST", f.path("/goals/"+Str(alternate, "id")+"/actions"), ID(), testTag(alternate), Object{"action": "ACTIVATE", "reason": "separate goal cannot reset cause"})
	body["goal_id"] = alternate["id"]
	other := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(alternate), body)
	f.bundle(other)
	other = f.read("tasks", Str(other, "id"))
	status, reply, _ = f.request("POST", f.path("/tasks/"+Str(other, "id")+"/actions"), ID(), testTag(other), Object{"action": "SUBMIT", "reason": "new goal and session cannot reset cause"})
	orchestrationAssert(t, "W06-G01-NO-PROGRESS-NEW-GOAL", []any{true, 409}, []any{other["no_progress_record_id"] == task["no_progress_record_id"], status}, reply)

}
