package domain

import "testing"

func intentFixture(t *testing.T) (*fixture, Object, Object, Object) {
	f := contextFixture(t)
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": "帮我研究可验证的新方法，保留未知问题。", "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Owner submitted original statement", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	key, tag := ID(), testTag(req)
	body := Object{"action": "ACCEPT", "reason": "Owner confirms original statement", "source_validation_refs": Empty()}
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), key, tag, body)
	f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), key, tag, body)
	var gid, tid string
	if e := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); e != nil {
		t.Fatal(e)
	}
	return f, req, f.read("goals", gid), f.read("tasks", tid)
}
func TestIntentIntakeAtomicAndVisibleBlock(t *testing.T) {
	f, req, goal, task := intentFixture(t)
	if req["text"] != goal["original_intent"] || goal["status"] != "ACTIVE" || task["status"] != "BLOCKED" || task["task_type"] != "intent_planning" || task["context_bundle_id"] == nil {
		t.Fatalf("wrong intake: %s", Bytes(task))
	}
	for _, kind := range []string{"Goal", "Task", "ResourceRequest"} {
		var count int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?", f.project, kind).Scan(&count); e != nil || count != 1 {
			t.Fatalf("%s count=%d err=%v", kind, count, e)
		}
	}
	t.Log("I1-INTAKE: raw statement preserved; explicit accept replay creates one Goal/Task/ResourceRequest; blocked with real frozen contract and context")
}
func TestIntentPlannerCannotForgeOwnerSubmission(t *testing.T) {
	f := contextFixture(t)
	f.switchPrincipal("planning-model", []string{"PLANNER"})
	f.expect(403, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": "fabricated fact", "basis": "USER_STATED", "source_refs": Empty(), "rationale": "model", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	var count int
	f.db.QueryRow("SELECT count(*) FROM intent_plan_bindings").Scan(&count)
	if count != 0 {
		t.Fatal("unauthorized submission persisted")
	}
}
