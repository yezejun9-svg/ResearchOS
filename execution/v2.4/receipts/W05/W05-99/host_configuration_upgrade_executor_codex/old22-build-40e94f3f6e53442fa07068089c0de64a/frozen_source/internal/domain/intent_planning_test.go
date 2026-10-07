package domain

import (
	"context"
	"testing"
)

func intentFixture(t *testing.T, statement ...string) (*fixture, Object, Object, Object) {
	f := contextFixture(t)
	raw := "帮我研究可验证的新方法，保留未知问题。"
	if len(statement) > 0 {
		raw = statement[0]
	}
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": raw, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Owner submitted original statement", "supersedes_id": nil, "acceptance_check_ids": Empty()})
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

func intentBrief(f *fixture, req, task Object, ready bool) GoalBrief {
	ctx := f.read("context-bundles", Str(task, "context_bundle_id"))
	return intentBriefFromContext(req, ctx, ready)
}
func intentBriefFromContext(req, ctx Object, ready bool) GoalBrief {
	var budget Object
	for _, v := range Arr(ctx, "version_vector") {
		r := v.(map[string]any)
		if r["entity_type"] == "BudgetPolicy" {
			budget = r
		}
	}
	b := GoalBrief{Schema: "GoalBrief/v1", ProjectID: Str(req, "project_id"), RawIntentRef: Ref(req, "Requirement"), RawIntentHash: Digest([]byte(Str(req, "text"))), ContextRef: Ref(ctx, "ContextBundle"), VersionVector: Arr(ctx, "version_vector"), Revision: 1, Status: "NEEDS_INPUT", Title: "用户明确指定的 JSON 交付", Facts: []PlanningFact{{Str(req, "text"), "USER_STATED", []any{Ref(req, "Requirement")}}}, Scope: []string{"按用户给出的 JSON 字面量生成报告"}, Exclusions: []string{"不执行外部系统修改"}, Deliverables: []string{"两份独立检查的 JSON 报告"}, Nodes: []PlanningNode{}, BudgetPolicyRef: budget, FailureExits: []string{"input changed", "no progress", "resource unavailable"}, OpenQuestions: []PlanningQuestion{}, CapabilityGaps: []PlanningGap{}}
	if ready {
		b.Status = "READY"
		b.Nodes = []PlanningNode{{ID: "first", Title: "第一份报告", Action: "json_report", Dependencies: []string{}, Inputs: []any{Ref(req, "Requirement")}, Outputs: []string{"result.json"}, Checks: []PlanningCheck{{"first-check", "orchestration.json-equals", `{"result":"verified"}`}}, WallTime: 60, MaxAttempts: 2}, {ID: "second", Title: "依赖第一份的第二份报告", Action: "json_report", Dependencies: []string{"first"}, Inputs: []any{Ref(req, "Requirement")}, Outputs: []string{"result.json"}, Checks: []PlanningCheck{{"second-check", "orchestration.json-equals", `{"result":"verified"}`}}, WallTime: 60, MaxAttempts: 2}}
	} else {
		b.OpenQuestions = []PlanningQuestion{{"success", "要研究哪个方向，如何判断业务成功？", []string{}, true}}
	}
	return b
}

func intentReport(t *testing.T, ready bool) (*orchestrationFixture, *runtimeFixture, Object, Object) {
	statement := "帮我研究可验证的新方法。"
	if ready {
		statement = `请按先后顺序生成两份 {"result":"verified"} JSON 报告。`
	}
	f, req, goal, task := intentFixture(t, statement)
	brief := intentBrief(f, req, task, ready)
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "intent fixture output producer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); e != nil {
		t.Fatal(e)
	}
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "explicit development fixture"})
	o := &orchestrationFixture{f: f, goal: goal, req: req, rt: rt, owner: f.token}
	r := o.claim(task)
	artifact := o.report(r, Bytes(brief))
	request := o.acceptance(r, artifact)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), request)
	return o, r, artifact, request
}

func acceptIntentGoal(o *orchestrationFixture, r *runtimeFixture, b Object) Object {
	f := o.f
	g := f.read("goals", Str(o.goal, "id"))
	task := f.read("tasks", Str(r.task, "id"))
	body, _ := Decode(Bytes(b))
	body["subject_ref"] = Ref(g, "Goal")
	body["run_id"] = nil
	body["input_refs"] = []any{Ref(o.req, "Requirement"), Ref(task, "Task")}
	body["contract_hash"] = g["acceptance_contract"].(map[string]any)["contract_hash"]
	key, tag := ID(), testTag(g)
	receipt := f.expect(201, "POST", f.path("/acceptances"), key, tag, body)
	f.expect(201, "POST", f.path("/acceptances"), key, tag, body)
	return receipt
}

func TestIntentAcceptedBriefCompilesExactBusinessDAG(t *testing.T) {
	o, r, a, b := intentReport(t, true)
	f := o.f
	var before int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Goal'").Scan(&before)
	if before != 1 {
		t.Fatal("Task acceptance alone compiled a business goal")
	}
	receipt := acceptIntentGoal(o, r, b)
	var goalID, mappingRaw string
	if e := f.db.QueryRow("SELECT compiled_goal,node_mapping FROM intent_plan_bindings WHERE project=?", f.project).Scan(&goalID, &mappingRaw); e != nil {
		t.Fatal(e)
	}
	mapping, _ := Decode([]byte(mappingRaw))
	first := f.read("tasks", Str(mapping, "first"))
	second := f.read("tasks", Str(mapping, "second"))
	business := f.read("goals", goalID)
	planning := f.read("goals", Str(o.goal, "id"))
	if first["status"] != "READY" || second["status"] != "BLOCKED" || business["status"] != "ACTIVE" || planning["status"] != "ACCEPTED" || Hash(second["dependency_task_ids"]) != Hash([]any{first["id"]}) {
		t.Fatalf("wrong business DAG: %s %s", Bytes(first), Bytes(second))
	}
	if Hash(first["requirement_refs"]) != Hash([]any{Ref(o.req, "Requirement")}) {
		t.Fatal("proposal facts replaced Owner authority")
	}
	for _, input := range []any{Ref(a, "Artifact"), Ref(receipt, "AcceptanceReceipt")} {
		found := false
		for _, ref := range Arr(first, "input_refs") {
			found = found || Hash(ref) == Hash(input)
		}
		if !found {
			t.Fatal("missing accepted planning cross-Goal provenance")
		}
	}
	var goals, tasks int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Goal'").Scan(&goals)
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Task'").Scan(&tasks)
	if goals != 2 || tasks != 3 {
		t.Fatal("replay duplicated compiled objects")
	}
	t.Logf("I1-COMPILE: planning=%s brief=%s receipt=%s business=%s map=%s", planning["id"], a["id"], receipt["id"], business["id"], mappingRaw)
}

func TestIntentUnknownBusinessChoiceCreatesVisibleRequest(t *testing.T) {
	o, r, _, b := intentReport(t, false)
	acceptIntentGoal(o, r, b)
	f := o.f
	var goals, questions int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Goal'").Scan(&goals)
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='ResourceRequest' AND json_extract(body,'$.category')='BUSINESS_CHOICE'").Scan(&questions)
	if goals != 1 || questions != 1 {
		t.Fatalf("invented business branch or missing question: goals=%d questions=%d", goals, questions)
	}
	t.Log("I1-UNKNOWN: valid NEEDS_INPUT proposal accepted; one BUSINESS_CHOICE; no invented business Goal")
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
