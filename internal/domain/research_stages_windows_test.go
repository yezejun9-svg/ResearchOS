//go:build windows

package domain

import (
	"context"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestResearchOfflineCandidateStagesCurrentReceipts(t *testing.T) {
	rf := researchSetup(t, false)
	f := rf.f
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": monitorStatement, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "bounded stage fixture", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "confirmed", "source_validation_refs": Empty()})
	var gid, tid string
	if err := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); err != nil {
		t.Fatal(err)
	}
	_, goal, o := acceptMonitorPlanningFixture(t, f, req, f.read("goals", gid), f.read("tasks", tid))
	advance := func() {
		t.Helper()
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		p, err := authenticate(tx, o.owner)
		if err == nil {
			err = f.s.advanceResearchProject(tx, p, f.project, time.Now().UTC())
		}
		if err == nil {
			err = tx.Commit()
		}
		tx.Rollback()
		if err != nil {
			t.Fatal(err)
		}
	}
	accept := func(task Object, facts Object) {
		t.Helper()
		r := o.claim(task)
		artifact := o.report(r, Bytes(facts))
		body := o.acceptance(r, artifact)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), body)
	}
	advance()
	for _, kind := range []string{"GITHUB", "PAPER"} {
		var id string
		if err := f.db.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND stage='discovery' AND source_id=?", f.project, rf.ids[kind]).Scan(&id); err != nil {
			t.Fatal(err)
		}
		f.token = o.owner
		task := f.read("tasks", id)
		run := o.claim(task)
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		work, err := loadResearchWork(tx, f.project, id)
		tx.Rollback()
		if err != nil {
			t.Fatal(err)
		}
		config, cursor, err := f.s.sourceConfig(context.Background(), rf.source, f.project, Str(work.Parameters, "cursor_id"))
		if err != nil {
			t.Fatal(err)
		}
		key := "source-" + work.Key
		cost := Object{"policy_id": goal["budget_policy_id"], "run_id": run.run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": run.run["created_at"]}
		intent, err := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(run.run, "id"), key, Object{"logical_key": work.Key}, cost)
		if err != nil {
			t.Fatal(err)
		}
		tx, err = f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		intent, err = f.s.beginEffectTx(tx, o.owner, f.project, Str(run.run, "id"), key)
		if err == nil {
			err = tx.Commit()
		}
		tx.Rollback()
		if err != nil {
			t.Fatal(err)
		}
		endpoint := map[string]string{"GITHUB": "https://api.github.com/repos/researchos/research/releases", "PAPER": "https://export.arxiv.org/api/query"}[kind]
		page := sources.Page{RawResponse: Bytes(Object{"fixture": "offline candidate", "kind": kind}), RawMediaType: "application/json", Complete: true, HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}}
		if kind == "GITHUB" {
			to, _ := time.Parse(time.RFC3339Nano, Str(work.Parameters, "window_to"))
			page.Items = []sources.Item{{SourceID: rf.ids[kind], CanonicalURL: "https://github.com/researchos/research/releases/tag/v1", UpstreamID: "v1", PublishedAt: to.Add(-time.Minute), Body: []byte("Offline fixture release body; no measured improvement."), MediaType: "text/plain", Locator: "body"}}
		}
		coordinator := &RuntimeCoordinator{service: f.s}
		epoch, _ := Num(run.run, "lease_epoch")
		response, err := coordinator.captureResearchSource(context.Background(), RuntimeCoordinatorRoute{ProjectID: f.project}, RuntimeProviderRoute{SourceToken: rf.source, MeasurementMode: "FIXTURE"}, Str(run.run, "id"), epoch, rt.BridgeFrame{Key: key, Sequence: 1}, intent, work, config, cursor, sourceFixtureAdapter{page})
		if err != nil {
			t.Fatal(err)
		}
		artifact := o.report(run, Bytes(response["payload"]))
		body := o.acceptance(run, artifact)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
	}
	for _, stage := range []string{"verification", "review"} {
		advance()
		f.token = o.owner
		var id string
		if err := f.db.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND stage=?", f.project, stage).Scan(&id); err != nil {
			t.Fatal(err)
		}
		task := f.read("tasks", id)
		if task["status"] == "BLOCKED" {
			f.bundle(task)
			task = f.read("tasks", id)
			task = f.expect(200, "POST", f.path("/tasks/"+id+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "current accepted dependency"})
		}
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		snapshot, err := f.s.researchStageSnapshot(tx, f.project, task)
		tx.Rollback()
		if err != nil {
			t.Fatal(err)
		}
		accept(task, snapshot["expected"].(map[string]any))
	}
	advance()
	f.token = o.owner
	var reportID, cycleID string
	if err := f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&reportID, &cycleID); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	cycle, err := load(tx, f.project, "ResearchCycle", cycleID)
	if err != nil {
		t.Fatal(err)
	}
	facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	candidates := Arr(facts, "candidates")
	if len(candidates) != 1 || candidates[0].(map[string]any)["review"] == nil {
		t.Fatal("current independent candidate disposition missing")
	}
	accept(f.read("tasks", reportID), facts)
	advance()
	f.token = o.owner
	if f.read("research-cycles", cycleID)["status"] != "PARTIAL" {
		t.Fatal("missing X became complete")
	}
	t.Log("I2-OFFLINE-STAGES: real source transaction -> accepted capture -> accepted sealed-snapshot/origin verification -> accepted INCONCLUSIVE disposition -> current bound review -> accepted PARTIAL cycle close; no external IO or live semantic claim")
}

func TestResearchTaskBoundAndPublicCloseGate(t *testing.T) {
	rf := researchSetup(t, false)
	f := rf.f
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": monitorStatement, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "bounded stage fixture", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "confirmed", "source_validation_refs": Empty()})
	var gid, tid string
	if err := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); err != nil {
		t.Fatal(err)
	}
	_, _, o := acceptMonitorPlanningFixture(t, f, req, f.read("goals", gid), f.read("tasks", tid), func(b *GoalBrief) { b.Monitor.MaxTasks = 1 })
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	p, err := authenticate(tx, o.owner)
	if err == nil {
		err = f.s.advanceResearchProject(tx, p, f.project, time.Now().UTC())
	}
	if err == nil {
		err = tx.Commit()
	}
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	var taskID, cycleID string
	if err = f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&taskID, &cycleID); err != nil {
		t.Fatal(err)
	}
	var count int
	if err = f.db.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=?", f.project).Scan(&count); err != nil || count != 1 {
		t.Fatalf("max tasks=1 must retain one report, got %d %v", count, err)
	}
	f.token = o.owner
	cycle := f.read("research-cycles", cycleID)
	f.expect(409, "POST", f.path("/research-cycles/"+cycleID+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "report still READY"})
	task := f.read("tasks", taskID)
	failed := o.claim(task)
	failed.call("/heartbeat", failed.heartbeat(), 200)
	observation := failed.observation("FAILED", true)
	observation["exit_code"] = 1
	failed.observe(observation)
	failed.call("/report", failed.report(Empty(), 1), 200)
	f.token = o.owner
	f.expect(409, "POST", f.path("/research-cycles/"+cycleID+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "report FAILED"})
	task = f.read("tasks", taskID)
	task = f.expect(200, "POST", f.path("/tasks/"+taskID+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "one permitted current retry"})
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	if facts["cycle_outcome"] != "BLOCKED" || len(Arr(facts, "gaps")) < 3 {
		t.Fatal("finite bound must retain all source gaps")
	}
	origin, _ := facts["origin"].(map[string]any)
	continuation, _ := facts["continuation"].(map[string]any)
	if origin == nil || origin["goal_id"] != task["goal_id"] || origin["owner_instruction"] == "" || origin["accepted_plan_ref"] == nil ||
		origin["plan_acceptance_ref"] == nil || len(Arr(origin, "requirement_refs")) == 0 ||
		continuation == nil || continuation["mode"] != "ACCEPTED_MONITOR_PLAN" ||
		continuation["next_window_from"] != cycle["window_to"] || len(Arr(continuation, "next_review_conditions")) == 0 {
		t.Fatalf("accepted report omitted monitor origin or finite next-review conditions: %v %v", origin, continuation)
	}
	run := o.claim(task)
	artifact := o.report(run, Bytes(facts))
	f.token = o.owner
	f.expect(409, "POST", f.path("/research-cycles/"+cycleID+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "execution report has no independent acceptance"})
	body := o.acceptance(run, artifact)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
	f.token = o.owner
	f.expect(200, "POST", f.path("/research-cycles/"+cycleID+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "current independently accepted report"})
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	closed, err := load(tx, f.project, "ResearchCycle", cycleID)
	if err == nil {
		var after Object
		after, err = f.s.researchCycleFacts(tx, f.project, closed, nil)
		if err == nil && Hash(after) != Hash(facts) {
			t.Fatal("accepted report facts changed merely because the cycle closed")
		}
	}
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	f.expect(409, "POST", f.path("/research-cycles/"+cycleID+"/close"), ID(), testTag(f.read("research-cycles", cycleID)), Object{"requested_status": "BLOCKED", "outcome_summary": "repeat close"})
	if err = f.db.QueryRow("SELECT count(*) FROM resource_progress_runs WHERE project=? AND run=?", f.project, run.run["id"]).Scan(&count); err != nil || count != 1 {
		t.Fatalf("close must count exact original iteration once: %d %v", count, err)
	}
	t.Log("I2-BOUNDS/CLOSE: MaxTasks=1 with 3 configured sources preserves one truthful BLOCKED report; public READY/FAILED/EXECUTION_REPORTED-without-receipt close rejected; exact accepted public close counts one stable monitor iteration")
}
