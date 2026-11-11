package domain

import (
	"context"
	"strings"
	"testing"
	"time"
)

func researchTick(t *testing.T, f *fixture, token string) {
	t.Helper()
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	p, err := authenticate(tx, token)
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

func TestResearchMonitorPauseResumeCancelAndDrift(t *testing.T) {
	for _, mode := range []string{"pause-resume-cancel", "profile-drift", "cancel-unknown"} {
		t.Run(mode, func(t *testing.T) {
			f, goal, o := acceptedMonitorFixture(t)
			researchTick(t, f, o.owner)
			var taskID, cycleID string
			if err := f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&taskID, &cycleID); err != nil {
				t.Fatal(err)
			}
			f.token = o.owner
			goal = f.read("goals", Str(goal, "id"))
			if mode == "pause-resume-cancel" {
				goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "PAUSE", "reason": "owner pause"})
				researchTick(t, f, o.owner)
				if f.read("tasks", taskID)["status"] != "BLOCKED" {
					t.Fatal("pause did not block finite work")
				}
				goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "RESUME", "reason": "owner resumes"})
				researchTick(t, f, o.owner)
				if f.read("tasks", taskID)["status"] != "READY" {
					t.Fatal("monitor did not resume its own hold")
				}
				f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "CANCEL", "reason": "owner cancels"})
			} else if mode == "profile-drift" {
				// Simulate an already committed profile revision; this tests the coordinator
				// gate, not the independent change-proposal workflow.
				tx, err := f.db.Begin()
				if err != nil {
					t.Fatal(err)
				}
				profile, err := singleton(tx, f.project, "ProjectProfile")
				if err == nil {
					profile["intent"] = "changed target requiring new approval"
					err = bump(profile)
				}
				if err == nil {
					err = f.s.put(tx, "ProjectProfile", profile)
				}
				alternateRef := Ref(profile, "ProjectProfile")
				if err == nil {
					profile["intent"] = "another current target"
					err = bump(profile)
				}
				if err == nil {
					err = f.s.put(tx, "ProjectProfile", profile)
				}
				if err == nil {
					err = tx.Commit()
				}
				tx.Rollback()
				if err != nil {
					t.Fatal(err)
				}
				// Keeping a stale ref while RUNNING remains forbidden. Switching to
				// another historical ref during cancellation is forbidden as well.
				for _, status := range []string{"RUNNING", "CANCELLED"} {
					tx, err = f.db.Begin()
					if err != nil {
						t.Fatal(err)
					}
					original, e := load(tx, f.project, "ResearchCycle", cycleID)
					if e == nil {
						original["status"] = status
						if status == "CANCELLED" {
							original["profile_ref"] = alternateRef
							original["closed_at"] = Now()
						}
						e = bump(original)
					}
					if e == nil {
						e = f.s.put(tx, "ResearchCycle", original)
					}
					tx.Rollback()
					if e == nil {
						t.Fatalf("historical ref guard bypass: %s", status)
					}
				}
			} else {
				run := o.claim(f.read("tasks", taskID))
				run.call("/heartbeat", run.heartbeat(), 200)
				key := ID()
				_, err := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(run.run, "id"), key, Object{"fixture": "unknown"}, Object{"policy_id": goal["budget_policy_id"], "run_id": run.run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": Now()})
				if err != nil {
					t.Fatal(err)
				}
				if _, err = f.s.BeginEffect(context.Background(), o.owner, f.project, Str(run.run, "id"), key); err != nil {
					t.Fatal(err)
				}
				if err = f.s.ObserveEffect(context.Background(), f.project, Str(run.run, "id"), key, "UNKNOWN", Object{"reason": "offline unresolved outcome"}); err != nil {
					t.Fatal(err)
				}
				f.token = o.owner
				f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "CANCEL", "reason": "cancel unresolved work"})
				researchTick(t, f, o.owner)
				if f.read("runs", Str(run.run, "id"))["status"] != "CANCEL_REQUESTED" {
					t.Fatal("cancel request was rolled back")
				}
				if f.read("research-cycles", cycleID)["status"] != "RUNNING" {
					t.Fatal("unresolved cycle closed")
				}
				var current int
				if err = f.db.QueryRow("SELECT monitor_current FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, goal["id"]).Scan(&current); err != nil || current != 1 {
					t.Fatal("unknown effect lost original ownership")
				}
				return
			}
			researchTick(t, f, o.owner)
			cycle := f.read("research-cycles", cycleID)
			if cycle["status"] != "CANCELLED" {
				t.Fatal("safe terminal cycle not cancelled")
			}
			if mode == "profile-drift" && (!strings.Contains(Str(cycle, "outcome_summary"), "prior=") || !strings.Contains(Str(cycle, "outcome_summary"), "current=")) {
				t.Fatal("drift lost both profile refs")
			}
			var current, count int
			if err := f.db.QueryRow("SELECT monitor_current FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, goal["id"]).Scan(&current); err != nil || current != 0 {
				t.Fatal("retired monitor remained current")
			}
			researchTick(t, f, o.owner)
			if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", f.project).Scan(&count); err != nil || count != 1 {
				t.Fatal("retired monitor created another cycle")
			}
		})
	}
	t.Log("I2-LIFECYCLE: Owner pause/resume clears only monitor hold; safe cancel/drift retires original binding; unresolved effect preserves RUNNING cycle and commits cancel request")
}

func TestResearchNoProgressPersistsAcrossAcceptedReports(t *testing.T) {
	f, goal, o := acceptedMonitorFixture(t)
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	policy, err := f.s.effectiveRetryPolicy(tx, f.project)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	limit, _ := Num(policy, "no_progress_iteration_limit")
	for i := int64(0); i < limit; i++ {
		f.token = o.owner
		profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
		now := time.Now().UTC()
		cycle := f.expect(201, "POST", f.path("/research-cycles"), ID(), f.stateTag(), Object{"trigger": "USER", "profile_revision": profile["revision"], "window_from": now.Add(-time.Hour).Format(time.RFC3339Nano), "window_to": now.Format(time.RFC3339Nano)})
		researchTick(t, f, o.owner)
		var taskID string
		if err = f.db.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND stage='delivery'", f.project, cycle["id"]).Scan(&taskID); err != nil {
			t.Fatal(err)
		}
		tx, err = f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
		tx.Rollback()
		if err != nil {
			t.Fatal(err)
		}
		run := o.claim(f.read("tasks", taskID))
		artifact := o.report(run, Bytes(facts))
		body := o.acceptance(run, artifact)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), body)
		researchTick(t, f, o.owner)
		if f.read("tasks", taskID)["status"] != "ACCEPTED" {
			t.Fatal("no-progress must preserve correct report acceptance")
		}
	}
	var progressID string
	if err = f.db.QueryRow("SELECT monitor_progress_id FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, goal["id"]).Scan(&progressID); err != nil {
		t.Fatal(err)
	}
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	n, err := load(tx, f.project, "NoProgressRecord", progressID)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	count, _ := Num(n, "no_progress_iterations")
	if count != limit || n["status"] != "DEFERRED_NO_PROGRESS" {
		t.Fatalf("cross-cycle progress reset: %v", n)
	}
	researchTick(t, f, o.owner)
	var cycles int64
	if err = f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", f.project).Scan(&cycles); err != nil || cycles != limit {
		t.Fatal("deferred monitor created additional cycle")
	}
	t.Log("I2-NOPROGRESS: distinct cycles and independently accepted report Runs count against one stable record; finite limit defers next cycle and preserves accepted reports")
}

func TestResearchRecompiledSameIntentKeepsNoProgress(t *testing.T) {
	f, oldGoal, o := acceptedMonitorFixture(t)
	f.token = o.owner
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	now := time.Now().UTC()
	cycle := f.expect(201, "POST", f.path("/research-cycles"), ID(), f.stateTag(), Object{
		"trigger": "USER", "profile_revision": profile["revision"],
		"window_from": now.Add(-time.Hour).Format(time.RFC3339Nano), "window_to": now.Format(time.RFC3339Nano)})
	researchTick(t, f, o.owner)
	var reportID string
	if err := f.db.QueryRow("SELECT task FROM research_cycle_work WHERE project=? AND cycle=? AND stage='delivery'", f.project, cycle["id"]).Scan(&reportID); err != nil {
		t.Fatal(err)
	}
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	facts, err := f.s.researchCycleFacts(tx, f.project, cycle, nil)
	tx.Rollback()
	if err != nil {
		t.Fatal(err)
	}
	run := o.claim(f.read("tasks", reportID))
	artifact := o.report(run, Bytes(facts))
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), o.acceptance(run, artifact))
	researchTick(t, f, o.owner)
	if f.read("research-cycles", Str(cycle, "id"))["status"] != "BLOCKED" {
		t.Fatal("the independently accepted no-progress report did not close")
	}
	var oldProgressID string
	if err = f.db.QueryRow("SELECT monitor_progress_id FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, oldGoal["id"]).Scan(&oldProgressID); err != nil {
		t.Fatal(err)
	}
	oldProgress := f.read("no-progress-records", oldProgressID)
	count, _ := Num(oldProgress, "no_progress_iterations")
	if count != 1 {
		t.Fatalf("the first accepted report did not count against the monitor: %v", oldProgress)
	}
	f.token = o.owner
	oldGoal = f.read("goals", Str(oldGoal, "id"))
	f.expect(200, "POST", f.path("/goals/"+Str(oldGoal, "id")+"/actions"), ID(), testTag(oldGoal), Object{"action": "CANCEL", "reason": "Owner retires this monitor"})
	researchTick(t, f, o.owner)
	var current int
	if err = f.db.QueryRow("SELECT monitor_current FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, oldGoal["id"]).Scan(&current); err != nil || current != 0 {
		t.Fatalf("cancelled monitor still current: %d %v", current, err)
	}
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{
		"requirement_key": "INTENT-" + ID(), "text": monitorStatement, "basis": "USER_STATED",
		"source_refs": Empty(), "rationale": "Owner explicitly reauthorizes the same project monitoring intent",
		"supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{
		"action": "ACCEPT", "reason": "same current problem and profile", "source_validation_refs": Empty()})
	var planningGoalID, planningTaskID string
	if err = f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&planningGoalID, &planningTaskID); err != nil {
		t.Fatal(err)
	}
	_, newGoal, _ := acceptMonitorPlanningFixture(t, f, req, f.read("goals", planningGoalID), f.read("tasks", planningTaskID))
	if newGoal["id"] == oldGoal["id"] {
		t.Fatal("the second monitor did not compile a distinct Goal")
	}
	var newProgressID string
	if err = f.db.QueryRow("SELECT monitor_progress_id FROM intent_plan_bindings WHERE project=? AND compiled_goal=?", f.project, newGoal["id"]).Scan(&newProgressID); err != nil {
		t.Fatal(err)
	}
	if newProgressID != oldProgressID {
		t.Fatalf("same intent and source inputs escaped no-progress through a new Goal: %s -> %s", oldProgressID, newProgressID)
	}
	reused := f.read("no-progress-records", newProgressID)
	reusedCount, _ := Num(reused, "no_progress_iterations")
	if reusedCount != count || reused["key_hash"] != oldProgress["key_hash"] {
		t.Fatalf("recompilation reset progress: before=%v after=%v", oldProgress, reused)
	}
	t.Log("I2-RECOMPILE-NO-RESET: a distinct Owner-approved Goal for the same project problem and inputs retains the original accepted report count and NoProgressRecord")
}
