package domain

import "testing"

func TestW06GoalPause(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	first := o.task("goal-pause-running", Empty(), Empty())
	second := o.task("goal-pause-ready", Empty(), Empty())
	r := o.claim(first)
	f.token = o.owner
	goal := f.read("goals", Str(o.goal, "id"))
	paused := f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "PAUSE", "reason": "stop new dispatch"})
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(second, "id")+"/claim"), ID(), testTag(second), Object{"runtime_id": o.rt["id"], "executor_principal_id": r.executor, "context_bundle_id": second["context_bundle_id"]})
	running := f.read("runs", Str(r.run, "id"))
	f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(paused), Object{"action": "RESUME", "reason": "resume dispatch"})
	next := o.claim(second)
	orchestrationAssert(t, "W06-G01-GOAL-PAUSE-DISPATCH", []any{"PAUSED", 409, "QUEUED", nil, "RUNNING"}, []any{paused["status"], status, running["status"], running["cancel_confirmed_at"], next.task["status"]}, Object{"rejection": reply, "existing_run_not_claimed_stopped": true})
}
