//go:build windows

package domain

import (
	"context"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func TestW07HealthBoundPartialEffectRemainsConfirmed(t *testing.T) {
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
	advance()
	for _, kind := range []string{"GITHUB"} {
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
		page := sources.Page{RawResponse: Bytes(Object{"fixture": "offline candidate", "kind": kind}), RawMediaType: "application/json", Complete: false, Failure: "page_timeout", HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}}
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
		if response["state"] != "CONFIRMED" {
			t.Fatal("committed partial receipt was downgraded", response)
		}
		tx, err = f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		durable, err := latestEffect(tx, f.project, Str(run.run, "id"), key)
		if err != nil || durable["state"] != "CONFIRMED" {
			t.Fatal("effect truth lost", durable, err)
		}
		stored, err := loadResearchWork(tx, f.project, id)
		if err != nil || stored.SourceReceipt == nil {
			t.Fatal("partial source receipt missing", err)
		}
		facts, err := f.s.researchSourceFacts(tx, f.project, stored)
		if err != nil || facts["page_complete"] != false {
			t.Fatal("partial facts unavailable", facts, err)
		}
		after, err := load(tx, f.project, "SourceCursor", Str(cursor, "id"))
		if err != nil || after["covered_until"] != nil {
			t.Fatal("partial cursor advanced", after, err)
		}
		tx.Rollback()
		emitH07Snapshot(t, f, "effect_confirmed", Object{"effect_key": key}, Object{"effect": durable, "facts": facts, "cursor": after})
		replay, err := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(run.run, "id"), key, Object{"logical_key": work.Key}, cost)
		if err != nil || replay["state"] != "CONFIRMED" || Hash(replay["receipt"]) != Hash(durable["receipt"]) {
			t.Fatal("same effect replay lost original receipt", replay, err)
		}
	}
}

func TestW07HealthFailureBeforeCommitStaysUnresolved(t *testing.T) {
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
	advance()
	for _, kind := range []string{"GITHUB"} {
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
		page := sources.Page{RawResponse: Bytes(Object{"fixture": "offline candidate", "kind": kind}), RawMediaType: "application/json", Complete: false, Failure: "page_timeout", HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}}
		if kind == "GITHUB" {
			to, _ := time.Parse(time.RFC3339Nano, Str(work.Parameters, "window_to"))
			page.Items = []sources.Item{{SourceID: "wrong-source", CanonicalURL: "https://github.com/researchos/research/releases/tag/v1", UpstreamID: "v1", PublishedAt: to.Add(-time.Minute), Body: []byte("Offline fixture release body; no measured improvement."), MediaType: "text/plain", Locator: "body"}}
		}
		coordinator := &RuntimeCoordinator{service: f.s}
		epoch, _ := Num(run.run, "lease_epoch")
		response, err := coordinator.captureResearchSource(context.Background(), RuntimeCoordinatorRoute{ProjectID: f.project}, RuntimeProviderRoute{SourceToken: rf.source, MeasurementMode: "FIXTURE"}, Str(run.run, "id"), epoch, rt.BridgeFrame{Key: key, Sequence: 1}, intent, work, config, cursor, sourceFixtureAdapter{page})
		if err == nil || response != nil {
			t.Fatal("invalid body unexpectedly committed", response, err)
		}
		tx, err = f.db.Begin()
		if err != nil {
			t.Fatal(err)
		}
		durable, err := latestEffect(tx, f.project, Str(run.run, "id"), key)
		workAfter, _ := loadResearchWork(tx, f.project, id)
		if err != nil || durable["state"] != "UNKNOWN" || workAfter.SourceReceipt != nil {
			t.Fatal("failed capture confirmed", durable, err)
		}
		tx.Rollback()
		emitH07Snapshot(t, f, "effect_unresolved", Object{"effect_key": key, "invalid_source_id": "wrong-source"}, Object{"effect": durable})
	}
}
