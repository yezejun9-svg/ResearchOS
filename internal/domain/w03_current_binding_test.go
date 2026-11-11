package domain

import (
	"context"
	"fmt"
	"testing"

	"researchos.local/research-os/adapters/evaluation"
)

func w03CurrentFixture(t *testing.T) *fixture {
	t.Helper()
	f := setup(t)
	w03ReopenCurrent(t, f)
	return f
}

func w03ReopenCurrent(t *testing.T, f *fixture) {
	t.Helper()
	s, err := NewCurrentMu(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if err != nil {
		t.Fatal(err)
	}
	f.s, f.h = s, s.Handler()
}

func w03Copy(t *testing.T, o Object) Object {
	t.Helper()
	x, err := Decode(Bytes(o))
	if err != nil {
		t.Fatal(err)
	}
	return x
}

func w03GoalBody(req Object, title string) Object {
	return Object{"title": title, "original_intent": "current domain regression", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"w03-problem"}, "deliverables": []any{"fixture evidence"}, "acceptance_contract": orchestrationContract()}
}

func w03TaskBody(goal, req Object, title string) Object {
	return Object{"goal_id": goal["id"], "title": title, "task_type": "fixture", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": orchestrationContract(), "origin_problem_id": "w03-problem", "candidate_id": title, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}}
}

func w03GoalTask(f *fixture, req Object, title string) (Object, Object) {
	f.t.Helper()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), w03GoalBody(req, title))
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), w03TaskBody(goal, req, title))
	return f.read("goals", Str(goal, "id")), task
}

func w03AssertStoredRoute(t *testing.T, f *fixture, kind string, o Object, route string) {
	t.Helper()
	if Str(o["binding"].(map[string]any), "route") != route {
		t.Fatalf("%s HTTP route: %v", kind, o["binding"])
	}
	var raw string
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND id=?", f.project, kind, o["id"]).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	stored, err := Decode([]byte(raw))
	if err != nil || Hash(stored["binding"]) != Hash(o["binding"]) {
		t.Fatalf("%s persisted binding differs: %v", kind, err)
	}
	if err := f.s.Contracts.Validate(kind, stored); err != nil {
		t.Fatalf("%s persisted schema: %v", kind, err)
	}
	t.Logf("W03 current-binding HTTP/SQLite %s route=%s revision=%v", kind, route, stored["revision"])
}

func TestW03CurrentMuHTTPPersistenceAndInheritance(t *testing.T) {
	// No environment value can choose the installed host's fixed route.
	t.Setenv("RESEARCHOS_ROUTE", "PAPERCLIP")
	t.Setenv("RESEARCHOS_SCHEMA_VERSION", "2.0.0")
	f := w03CurrentFixture(t)
	body := projectBody()
	body["binding"] = Object{"route": "PI_COMPOSE"}
	f.expect(400, "POST", "/v1/projects", ID(), "", body)
	f.createProject()
	req := f.requirement()
	badGoal := w03GoalBody(req, "injected")
	badGoal["binding"] = Object{"route": "THIN_CORE"}
	f.expect(400, "POST", f.path("/goals"), ID(), f.stateTag(), badGoal)
	goal, task := w03GoalTask(f, req, "current")
	badTask := w03TaskBody(goal, req, "injected")
	badTask["binding"] = Object{"route": "GAP_ONLY_COMPOSE"}
	f.expect(400, "POST", f.path("/tasks"), ID(), testTag(goal), badTask)
	for kind, o := range map[string]Object{"ProjectState": f.state(), "Goal": goal, "Task": task} {
		w03AssertStoredRoute(t, f, kind, o, "MU_FORK")
	}
	before := Hash(f.state())
	w03ReopenCurrent(t, f)
	if Hash(f.state()) != before {
		t.Fatal("restart changed existing ProjectState")
	}
	cancelled := f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "CANCEL", "reason": "fixture complete"})
	w03AssertStoredRoute(t, f, "Task", cancelled, "MU_FORK")
	for _, path := range []string{"/goals", "/tasks"} {
		page := f.expect(200, "GET", f.path(path), "", "", nil)
		if len(Arr(page, "items")) != 1 {
			t.Fatalf("route injection created a second object: %s %v", path, page)
		}
	}
}

func TestW03LegacyContinuationAndMixedPages(t *testing.T) {
	f := setup(t)
	f.createProject()
	req := f.requirement()
	oldGoal, oldTask := w03GoalTask(f, req, "legacy")
	before := Hash(f.state())
	w03ReopenCurrent(t, f)
	if Hash(f.state()) != before {
		t.Fatal("current constructor rewrote legacy project")
	}
	goal, task := w03GoalTask(f, req, "continued")
	for kind, o := range map[string]Object{"ProjectState": f.state(), "Goal": goal, "Task": task} {
		w03AssertStoredRoute(t, f, kind, o, "THIN_CORE")
	}
	// Isolated imported-history fixture: a valid current object can coexist
	// with valid legacy objects. There is no user route-changing API involved.
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	for kind, original := range map[string]Object{"Goal": oldGoal, "Task": oldTask} {
		o, err := load(tx, f.project, kind, Str(original, "id"))
		if err != nil {
			t.Fatal(err)
		}
		o["binding"].(map[string]any)["route"] = "MU_FORK"
		if err = bump(o); err != nil {
			t.Fatal(err)
		}
		if err = f.s.put(tx, kind, o); err != nil {
			t.Fatal(err)
		}
	}
	if err = tx.Commit(); err != nil {
		t.Fatal(err)
	}
	for kind, path := range map[string]string{"Goal": "/goals", "Task": "/tasks"} {
		page := f.expect(200, "GET", f.path(path), "", "", nil)
		routes := map[string]bool{}
		for _, item := range Arr(page, "items") {
			routes[Str(item.(map[string]any)["binding"].(map[string]any), "route")] = true
		}
		if !routes["MU_FORK"] || !routes["THIN_CORE"] {
			t.Fatalf("mixed page lost an item: %v", routes)
		}
		mutations := []func(Object){
			func(x Object) { x["unknown_outer"] = true },
			func(x Object) { delete(x, "next_cursor") },
			func(x Object) { x["snapshot_event_sequence"] = -1 },
			func(x Object) { Arr(x, "items")[0].(map[string]any)["unknown_inner"] = true },
			func(x Object) { delete(Arr(x, "items")[0].(map[string]any), "binding") },
			func(x Object) { Arr(x, "items")[0].(map[string]any)["binding"].(map[string]any)["route"] = "UNKNOWN" },
		}
		for i, mutate := range mutations {
			x := w03Copy(t, page)
			mutate(x)
			if f.s.Contracts.Validate(kind+"Page", x) == nil {
				t.Fatalf("%sPage accepted malformed mutation %d", kind, i)
			}
		}
	}
	// New children inherit the authoritative Goal, including imported current
	// Goal bindings in a legacy project; the host default never overrides it.
	currentGoal := f.read("goals", Str(oldGoal, "id"))
	child := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(currentGoal), w03TaskBody(currentGoal, req, "inherited-current"))
	w03AssertStoredRoute(t, f, "Task", child, "MU_FORK")
}

func TestW03CurrentBindingStrictValidation(t *testing.T) {
	f := w03CurrentFixture(t)
	f.createProject()
	req := f.requirement()
	goal, task := w03GoalTask(f, req, "strict")
	for kind, sample := range map[string]Object{"ProjectState": f.state(), "Goal": goal, "Task": task} {
		for _, route := range []string{"THIN_CORE", "PAPERCLIP", "MU_FORK", "PI_COMPOSE", "GAP_ONLY_COMPOSE"} {
			x := w03Copy(t, sample)
			x["binding"].(map[string]any)["route"] = route
			if err := f.s.Contracts.Validate(kind, x); err != nil {
				t.Fatalf("recognized %s %s rejected: %v", kind, route, err)
			}
		}
		for i, mutate := range []func(Object){
			func(x Object) { delete(x, "binding") },
			func(x Object) { x["binding"] = nil },
			func(x Object) { delete(x["binding"].(map[string]any), "route") },
			func(x Object) { x["binding"].(map[string]any)["route"] = "UNKNOWN" },
			func(x Object) { x["binding"].(map[string]any)["upstream_project_id"] = "" },
			func(x Object) { x["binding"].(map[string]any)["new_authority"] = true },
			func(x Object) { x["revision"] = 0 },
			func(x Object) { x["created_at"] = "2026-02-30T00:00:00Z" },
		} {
			x := w03Copy(t, sample)
			mutate(x)
			if f.s.Contracts.Validate(kind, x) == nil {
				t.Fatalf("%s mutation %d bypassed strict current/legacy selection", kind, i)
			}
		}
	}
}

func TestW03CurrentTaskClaimResponse(t *testing.T) {
	f := w03CurrentFixture(t)
	f.createProject()
	f.owner = "w03-current-author"
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	req := f.requirement()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "current claim", "original_intent": "current response schema", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"fixture"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "development fixture"})
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "current claim fixture", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if err := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); err != nil {
		t.Fatal(err)
	}
	o := &orchestrationFixture{f, goal, req, rt, f.token}
	r := o.claim(o.task("w03-current-claim", Empty(), Empty()))
	w03AssertStoredRoute(t, f, "Task", r.task, "MU_FORK")
	response := Object{"task": r.task, "run": r.run, "lease_token": r.lease}
	if err := f.s.Contracts.Validate("TaskClaimResponse", response); err != nil {
		t.Fatal(err)
	}
	for i, mutate := range []func(Object){
		func(x Object) { delete(x, "lease_token") },
		func(x Object) { x["lease_token"] = "" },
		func(x Object) { x["unknown_outer"] = true },
		func(x Object) { x["run"].(map[string]any)["unknown_run"] = true },
		func(x Object) { x["task"].(map[string]any)["binding"].(map[string]any)["route"] = "UNKNOWN" },
	} {
		x := w03Copy(t, response)
		mutate(x)
		if f.s.Contracts.Validate("TaskClaimResponse", x) == nil {
			t.Fatalf("claim response mutation %d bypassed original envelope", i)
		}
	}
	// No report, acceptance, protected service or formal W06 gate is invoked.
}

func TestW03CurrentEvaluationArtifactGuard(t *testing.T) {
	f := w03CurrentFixture(t)
	f.createProject()
	var artifactsBefore int
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact'", f.project).Scan(&artifactsBefore); err != nil {
		t.Fatal(err)
	}
	executor := "w03-evaluation-fixture"
	f.switchPrincipal(executor, []string{"EXECUTOR"})
	_, report := evaluationReportContractFixture(t)
	report["schema_version"] = "2.4.0"
	report["project_id"] = f.project
	if err := f.s.Contracts.Validate("EvaluationReport", report); err != nil {
		t.Fatal(err)
	}
	summary := evaluation.Summary(report, Ref(Object{"id": "report", "revision": 1, "content_hash": Hash(report)}, "Artifact"))
	if err := f.s.Contracts.Validate("EvaluationSummary", summary); err != nil || summary["schema_version"] != "2.4.0" {
		t.Fatalf("current summary did not preserve validated report: %v", err)
	}
	invalid := w03Copy(t, summary)
	delete(invalid, "rubric_hash")
	foreign := w03Copy(t, summary)
	foreign["project_id"] = "other-project"
	legacy := w03Copy(t, report)
	legacy["schema_version"] = "2.0.0"
	for i, tc := range []struct {
		content Object
		status  int
	}{{report, 503}, {summary, 503}, {invalid, 422}, {foreign, 422}, {legacy, 503}} {
		raw := Bytes(tc.content)
		u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
		f.expect(tc.status, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "TEST_RESULT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": executor, "access_class": "PROJECT"})
		var sealed, artifacts int
		if err := f.db.QueryRow("SELECT sealed FROM uploaded_content WHERE storage_key=?", u["storage_key"]).Scan(&sealed); err != nil {
			t.Fatal(err)
		}
		if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact'", f.project).Scan(&artifacts); err != nil {
			t.Fatal(err)
		}
		if sealed != 0 || artifacts != artifactsBefore {
			t.Fatalf("guard %d created partial sealed output", i)
		}
	}
	for _, version := range []any{nil, "3.0.0", 2.4} {
		x := w03Copy(t, summary)
		x["schema_version"] = version
		if f.s.Contracts.Validate("EvaluationSummary", x) == nil {
			t.Fatal("unknown summary version accepted", fmt.Sprint(version))
		}
	}
}
