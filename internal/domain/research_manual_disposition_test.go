package domain

import (
	"context"
	"testing"
	"time"
)

// Counterfactual rows are inserted once inside a rolled-back transaction. No
// immutable review, source-page, binding or receipt is updated or deleted.
func TestW08ManualDispositionCurrentBoundary(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	evidence := r.capture(t, "GITHUB", true)[0]
	r.capture(t, "PAPER", false)
	r.capture(t, "X", false)
	r.checkpoint(t, []any{evidence["id"]}, Empty())
	outsider := Principal{ID: ID(), Roles: []string{"SCHEDULER"}, Grants: []Grant{}}
	if err := r.f.s.ProvisionPrincipal(context.Background(), outsider); err != nil {
		t.Fatal(err)
	}
	outsiderToken, err := r.f.s.IssueCredential(context.Background(), outsider.ID, time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"REJECT", "WATCH", "INCONCLUSIVE", "nil-actor", "stale-profile", "stored-profile-revision", "unknown-target", "blank-reason", "blank-gap", "blank-revisit", "ADOPT", "stale-evidence", "simulated-evidence", "stale-snapshot", "snapshot-ref-hash", "snapshot-byte-hash", "snapshot-byte-size", "no-project-grant", "restricted-snapshot", "missing-durable-page"} {
		t.Run(name, func(t *testing.T) {
			f := r.f
			tx, err := f.db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			p, err := authenticate(tx, r.scheduler)
			if err != nil {
				t.Fatal(err)
			}
			cycle, err := load(tx, f.project, "ResearchCycle", Str(r.cycle, "id"))
			if err != nil {
				t.Fatal(err)
			}
			profile, err := singleton(tx, f.project, "ProjectProfile")
			if err != nil {
				t.Fatal(err)
			}
			ev, err := load(tx, f.project, "Evidence", Str(evidence, "id"))
			if err != nil {
				t.Fatal(err)
			}
			persist := func(kind string, obj Object) {
				t.Helper()
				if e := bump(obj); e != nil {
					t.Fatal(e)
				}
				if e := f.s.put(tx, kind, obj); e != nil {
					t.Fatal(e)
				}
			}
			outcome, target, reason, missing, revisit := "REJECT", Str(profile, "intent"), "No measured improvement", "measurement missing", "new measurement"
			revision := profile["revision"]
			actor := &p
			pass := name == "REJECT" || name == "WATCH" || name == "INCONCLUSIVE"
			switch name {
			case "WATCH", "INCONCLUSIVE", "ADOPT":
				outcome = name
			case "nil-actor":
				actor = nil
			case "stale-profile":
				profile["intent"] = "changed intent"
				persist("ProjectProfile", profile)
			case "stored-profile-revision":
				revision = 999
			case "unknown-target":
				target = "absent target"
			case "blank-reason":
				reason = " "
			case "blank-gap":
				outcome, missing = "WATCH", " "
			case "blank-revisit":
				outcome, revisit = "INCONCLUSIVE", " "
			case "stale-evidence":
				ev["validity"] = "STALE"
				persist("Evidence", ev)
			case "simulated-evidence":
				ev["evidence_kind"] = "SIMULATED"
				persist("Evidence", ev)
			case "no-project-grant":
				p, err = authenticate(tx, outsiderToken)
				if err != nil {
					t.Fatal(err)
				}
			case "snapshot-ref-hash":
				ev["snapshot_artifact_ref"].(map[string]any)["content_hash"] = Digest([]byte("wrong ref"))
				// Deliberately corrupt a fixture projection; the ordinary write API
				// rejects this reference before persistence.
				if _, e := tx.Exec("UPDATE domain_objects SET body=? WHERE project=? AND kind='Evidence' AND id=?", string(Bytes(ev)), f.project, ev["id"]); e != nil {
					t.Fatal(e)
				}
			case "stale-snapshot", "snapshot-byte-hash", "snapshot-byte-size", "restricted-snapshot":
				a, e := load(tx, f.project, "Artifact", Str(ev["snapshot_artifact_ref"].(map[string]any), "id"))
				if e != nil {
					t.Fatal(e)
				}
				switch name {
				case "stale-snapshot":
					a["validity"] = "STALE"
				case "snapshot-byte-hash":
					a["content_hash"] = Digest([]byte("wrong sealed metadata"))
				case "snapshot-byte-size":
					a["byte_size"] = 1
				case "restricted-snapshot":
					a["access_class"] = "VERIFIER_ONLY"
				}
				if name == "stale-snapshot" {
					persist("Artifact", a)
				} else {
					// New counterfactual metadata, leaving the original seal intact.
					a["id"], a["revision"], a["kind"] = ID(), 1, "REPORT"
					if e := f.s.put(tx, "Artifact", a); e != nil {
						t.Fatal(e)
					}
				}
				ev["snapshot_artifact_ref"] = Ref(a, "Artifact")
				persist("Evidence", ev)
			case "missing-durable-page":
				ev["id"], ev["revision"] = ID(), 1
				ev["canonical_url"] = "https://github.com/researchos/research/releases/tag/unpaged-fixture"
				if e := f.s.put(tx, "Evidence", ev); e != nil {
					t.Fatal(e)
				}
				cycle["candidate_evidence_ids"] = []any{ev["id"]}
				persist("ResearchCycle", cycle)
			}
			// Deliberately stale cached support must never create authority/progress.
			_, err = tx.Exec("INSERT INTO research_candidate_reviews(project,cycle_id,evidence_id,profile_revision,context_target,outcome,reason,missing_evidence,revisit_trigger,origin_summary_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", f.project, cycle["id"], ev["id"], revision, target, outcome, reason, missing, revisit, `{"independent_observed_count":99}`, Now())
			if err != nil {
				t.Fatal(err)
			}
			facts, err := f.s.researchCycleFacts(tx, f.project, cycle, actor)
			if pass {
				if err != nil || facts["cycle_outcome"] != "COMPLETE" {
					t.Fatalf("negative manual close unavailable: %v %v", facts, err)
				}
				review := Arr(facts, "candidates")[0].(map[string]any)["review"].(map[string]any)
				if review["status"] != "MANUAL_REVALIDATED" || review["acceptance_ref"] != nil || review["authority"] != false || review["independent_review"] != false || review["support"] != nil {
					t.Fatalf("manual annotation gained authority: %v", review)
				}
				summary := review["origin_summary"].(map[string]any)
				if summary["independent_observed_count"] != 0 {
					t.Fatalf("cached support trusted: %v", summary)
				}
				keys, e := f.s.researchProgressKeys(tx, f.project, facts)
				if e != nil || len(keys) != 0 {
					t.Fatalf("manual annotation generated progress: %v %v", keys, e)
				}
			} else if err == nil && facts["cycle_outcome"] == "COMPLETE" {
				t.Fatalf("invalid current input admitted: %v", facts)
			}
			if name != "nil-actor" {
				_, closeErr := f.s.closeResearchCycle(tx, p, f.project, Str(cycle, "id"), Object{"requested_status": "COMPLETE", "outcome_summary": "bounded manual disposition fixture"})
				if (closeErr == nil) != pass {
					t.Fatalf("close gate disagrees: pass=%v err=%v", pass, closeErr)
				}
			}
			var minted int
			if err := tx.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind IN ('Task','AcceptanceReceipt','Decision','Release')", f.project).Scan(&minted); err != nil || minted != 0 {
				t.Fatalf("manual close minted authority: %d %v", minted, err)
			}
			t.Logf("W08 manual boundary %s: pass=%v; current tx checks; no authority or progress minted", name, pass)
		})
	}
	t.Run("monitor-binding-before-work-and-after-retirement", func(t *testing.T) {
		f := r.f
		f.token = r.owner
		req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": monitorStatement, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Explicit fixture monitor", "supersedes_id": nil, "acceptance_check_ids": Empty()})
		req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "Owner confirms monitor", "source_validation_refs": Empty()})
		var goalID, taskID string
		if err := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&goalID, &taskID); err != nil {
			t.Fatal(err)
		}
		_, goal, _ := acceptMonitorPlanningFixture(t, f, req, f.read("goals", goalID), f.read("tasks", taskID))
		_, err := f.s.ReviewResearchCandidate(context.Background(), r.owner, f.project, Str(r.cycle, "id"), Str(evidence, "id"), "fixture", "REJECT", "No improvement", "", "")
		if err != nil {
			t.Fatal(err)
		}
		tx, err := f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		defer tx.Rollback()
		p, err := authenticate(tx, r.scheduler)
		if err != nil {
			t.Fatal(err)
		}
		meta, plan, err := f.s.monitorSnapshot(tx, f.project, Str(goal, "id"), true)
		if err != nil {
			t.Fatal(err)
		}
		// A work relation alone must also prevent manual completion. The real
		// planning Task has no accepted research-stage receipt.
		if _, err = tx.Exec("SAVEPOINT work_only"); err != nil {
			t.Fatal(err)
		}
		if _, err = tx.Exec("INSERT INTO research_cycle_work(project,cycle,logical_key,plan_ref,stage,task,input_refs,input_hash,parameters,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", f.project, r.cycle["id"], "work-only-boundary", string(Bytes(meta["brief_ref"])), "delivery", taskID, "[]", Hash(Empty()), "{}", Now()); err != nil {
			t.Fatal(err)
		}
		if facts, e := f.s.researchCycleFacts(tx, f.project, r.cycle, &p); e == nil && facts["cycle_outcome"] == "COMPLETE" {
			t.Fatal("work-only cycle downgraded to manual")
		}
		if _, e := f.s.closeResearchCycle(tx, p, f.project, Str(r.cycle, "id"), Object{"requested_status": "COMPLETE", "outcome_summary": "must not bypass work binding"}); e == nil {
			t.Fatal("work-only close bypassed gate")
		}
		if _, err = tx.Exec("ROLLBACK TO work_only"); err != nil {
			t.Fatal(err)
		}
		if _, err = tx.Exec("RELEASE work_only"); err != nil {
			t.Fatal(err)
		}
		t.Log("W08 work-only fence: unaccepted real planning Task prevents manual completion")
		if err = bindResearchMonitorCycle(tx, f.project, r.cycle, meta, plan); err != nil {
			t.Fatal(err)
		}
		var count int
		if err = tx.QueryRow("SELECT count(*) FROM research_cycle_work WHERE project=? AND cycle=?", f.project, r.cycle["id"]).Scan(&count); err != nil || count != 0 {
			t.Fatalf("expected zero work: %d %v", count, err)
		}
		for _, retired := range []bool{false, true} {
			if retired {
				if _, err = tx.Exec("UPDATE intent_plan_bindings SET monitor_current=0 WHERE project=? AND compiled_goal=?", f.project, goal["id"]); err != nil {
					t.Fatal(err)
				}
			}
			facts, e := f.s.researchCycleFacts(tx, f.project, r.cycle, &p)
			if e != nil {
				t.Fatal(e)
			}
			if facts["cycle_outcome"] == "COMPLETE" || Arr(facts, "candidates")[0].(map[string]any)["review"] != nil {
				t.Fatalf("monitor downgraded to manual: retired=%v %v", retired, facts)
			}
			if _, e = f.s.closeResearchCycle(tx, p, f.project, Str(r.cycle, "id"), Object{"requested_status": "COMPLETE", "outcome_summary": "must not bypass monitor"}); e == nil {
				t.Fatal("monitor close bypassed independent report")
			}
			t.Logf("W08 monitor fence: zero work; retired=%v; manual annotation rejected", retired)
		}
	})
}
