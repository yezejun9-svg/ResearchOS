package domain

import (
	"context"
	"testing"
	"time"
)

const monitorStatement = "请持续监控当前项目，按现有配置定期生成研究报告，直到我暂停或取消。"

func monitorBrief(t *testing.T, f *fixture, req, task Object) GoalBrief {
	t.Helper()
	ctx := f.read("context-bundles", Str(task, "context_bundle_id"))
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	var policy Object
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	policy, err = load(tx, f.project, "RunPolicy", Str(profile, "run_policy_id"))
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	return monitorBriefCurrent(req, ctx, profile, policy)
}

func monitorBriefCurrent(req, ctx, profile, policy Object) GoalBrief {
	b := intentBriefFromContext(req, ctx, false)
	period, _ := Num(policy, "monitor_period_seconds")
	lookback, _ := Num(policy, "first_lookback_seconds")
	sources := []MonitorSource{}
	for _, raw := range Arr(profile, "source_configs") {
		config := raw.(map[string]any)
		sources = append(sources, MonitorSource{Str(config, "source_id"), Hash(config)})
	}
	b.Status, b.Title = "READY", "按现有配置持续研究"
	b.OpenQuestions = []PlanningQuestion{}
	b.Deliverables = []string{"每轮当前阶段证据及明确缺口"}
	b.Monitor = &MonitorPlan{Schema: "MonitorPlan/v1", ProfileRef: Ref(profile, "ProjectProfile"), RunPolicyRef: Ref(policy, "RunPolicy"), ContextTarget: Str(profile, "intent"), Sources: sources, PeriodSeconds: period, FirstLookbackSeconds: lookback, PagesPerSource: 2, ItemsPerPage: 10, MaxTasks: 16, WallTimeSeconds: 120, RequiredExperimentRefs: []Object{}, Exit: "OWNER_PAUSE_OR_CANCEL"}
	b.Nodes = []PlanningNode{{ID: "monitor", Title: "有限研究周期", Action: "research_monitor", Dependencies: []string{}, Inputs: []any{Ref(req, "Requirement")}, Outputs: []string{"cycle-report.json"}, Checks: []PlanningCheck{{"cycle-report", "research.cycle-report-v1", "current required stage evidence and explicit gaps"}}, WallTime: 120, MaxAttempts: 2}}
	return b
}

func acceptedMonitorFixture(t *testing.T) (*fixture, Object, *orchestrationFixture) {
	t.Helper()
	f, req, goal, task := intentFixture(t, monitorStatement)
	return acceptMonitorPlanningFixture(t, f, req, goal, task)
}

func acceptMonitorPlanningFixture(t *testing.T, f *fixture, req, goal, task Object, customize ...func(*GoalBrief)) (*fixture, Object, *orchestrationFixture) {
	t.Helper()
	brief := monitorBrief(t, f, req, task)
	for _, apply := range customize {
		apply(&brief)
	}
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "monitor planner fixture", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if err := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); err != nil {
		t.Fatal(err)
	}
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "RESUME", "reason": "bounded monitor fixture"})
	o := &orchestrationFixture{f: f, goal: goal, req: req, rt: rt, owner: f.token}
	run := o.claim(task)
	artifact := o.report(run, Bytes(brief))
	body := o.acceptance(run, artifact)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
	acceptIntentGoal(o, run, body)
	var gid string
	if err := f.db.QueryRow("SELECT compiled_goal FROM intent_plan_bindings WHERE project=? AND monitor_current=1", f.project).Scan(&gid); err != nil {
		t.Fatal(err)
	}
	return f, f.read("goals", gid), o
}

func TestResearchMonitorAcceptedPlanBinding(t *testing.T) {
	f, goal, _ := acceptedMonitorFixture(t)
	if goal["status"] != "ACTIVE" || len(Arr(goal, "task_ids")) != 0 {
		t.Fatal("monitor should be active awaiting finite cycle tasks")
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	meta, plan, err := f.s.monitorSnapshot(tx, f.project, Str(goal, "id"), true)
	tx.Rollback()
	if err != nil || plan == nil || meta == nil {
		t.Fatalf("accepted monitor unavailable: %v", err)
	}
	if err = f.s.RevokePrincipal(context.Background(), f.owner); err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	_, _, err = f.s.monitorSnapshot(tx, f.project, Str(goal, "id"), true)
	tx.Rollback()
	if err == nil {
		t.Fatal("revoked original Owner retained monitoring authority")
	}
	t.Log("I2-MONITOR: HTTP intent/planning Task/independent Task and Goal acceptance create one ACTIVE private monitor; current Owner revocation blocks reuse")
}

func TestResearchCycleBoundBeforeFirstTask(t *testing.T) {
	f, goal, o := acceptedMonitorFixture(t)
	f.token = o.owner
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	now := time.Now().UTC()
	cycle := f.expect(201, "POST", f.path("/research-cycles"), ID(), f.stateTag(), Object{"trigger": "USER", "profile_revision": profile["revision"], "window_from": now.Add(-time.Hour).Format(time.RFC3339Nano), "window_to": now.Format(time.RFC3339Nano)})
	var count int
	if err := f.db.QueryRow("SELECT count(*) FROM research_monitor_cycles WHERE project=? AND cycle=? AND goal=?", f.project, cycle["id"], goal["id"]).Scan(&count); err != nil || count != 1 {
		t.Fatalf("missing immediate binding: %d %v", count, err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=?", f.project).Scan(&count); err != nil || count != 0 {
		t.Fatalf("unexpected work: %d %v", count, err)
	}
	f.expect(422, "POST", f.path("/research-cycles/"+Str(cycle, "id")+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "no report yet"})
	probes := []string{
		"INSERT OR REPLACE INTO research_monitor_cycles SELECT * FROM research_monitor_cycles",
		"UPDATE research_monitor_cycles SET goal=goal",
		"DELETE FROM research_monitor_cycles",
	}
	for _, sql := range probes {
		if _, err := f.db.Exec(sql); err == nil {
			t.Fatalf("immutable mapping bypass: %s", sql)
		}
	}
	if _, err := f.db.Exec("UPDATE intent_plan_bindings SET monitor_current=0 WHERE project=? AND compiled_goal=?", f.project, goal["id"]); err != nil {
		t.Fatal(err)
	}
	f.expect(422, "POST", f.path("/research-cycles/"+Str(cycle, "id")+"/close"), ID(), testTag(cycle), Object{"requested_status": "BLOCKED", "outcome_summary": "retirement cannot erase binding"})
	t.Log("I2-CYCLE-BIND: create atomically binds zero-work cycle; public close denied before report and after monitor retirement; SQL replacement/update/delete rejected")
}

func TestResearchDriverCreatesOneFiniteCycleAndTruthfulMissingReport(t *testing.T) {
	f, goal, o := acceptedMonitorFixture(t)
	for i := 0; i < 2; i++ {
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
	var cycles int
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", f.project).Scan(&cycles); err != nil || cycles != 1 {
		t.Fatalf("duplicate cycles: %d %v", cycles, err)
	}
	var taskID, cycleID string
	if err := f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&taskID, &cycleID); err != nil {
		t.Fatal(err)
	}
	f.token = o.owner
	task := f.read("tasks", taskID)
	if task["goal_id"] != goal["id"] || task["status"] != "READY" {
		t.Fatal("finite cycle report was not materialized")
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	cycle, err := load(tx, f.project, "ResearchCycle", cycleID)
	if err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	if facts["cycle_outcome"] != "BLOCKED" || len(Arr(facts, "gaps")) < 3 {
		t.Fatal("missing sources became a successful report")
	}
	run := o.claim(task)
	artifact := o.report(run, Bytes(facts))
	body := o.acceptance(run, artifact)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
	tx, err = f.db.Begin()
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
	if f.read("research-cycles", cycleID)["status"] != "BLOCKED" || f.read("tasks", taskID)["status"] != "ACCEPTED" {
		t.Fatal("valid missing-data report acceptance must survive truthful cycle close")
	}
	t.Log("I2-CYCLE: repeated domain tick creates one finite cycle; source gaps computed from profile; actual fixture Task output independently accepted as BLOCKED report, not business success")
}
