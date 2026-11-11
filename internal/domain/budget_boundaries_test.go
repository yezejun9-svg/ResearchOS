package domain

import (
	"context"
	"researchos.local/research-os/internal/store"
	"sort"
	"sync"
	"testing"
	"time"
)

func TestW12BudgetConnections(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("two-sqlite-connections", Empty(), Empty()))
	f.token = o.owner
	path := f.path("/goals/" + Str(o.goal, "id") + "/budget-policy")
	policy := f.expect(200, "GET", path, "", "", nil)
	policy = f.expect(200, "PUT", path, ID(), testTag(policy), capBody("2.00"))
	var index int
	var name, dbPath string
	if e := f.db.QueryRow("PRAGMA database_list").Scan(&index, &name, &dbPath); e != nil {
		t.Fatal(e)
	}
	db, e := store.Open(dbPath)
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	other := &fixture{s: s, h: s.Handler(), token: o.owner, owner: f.owner, project: f.project, db: db, t: t}
	resourceHTTP(other)
	ch := make(chan int, 2)
	var wg sync.WaitGroup
	for _, client := range []*fixture{f, other} {
		wg.Add(1)
		go func(client *fixture) {
			defer wg.Done()
			code, _, _ := client.request("POST", client.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RESERVE", ID(), dollars("2.00"), "UPPER_BOUND", nil))
			ch <- code
		}(client)
	}
	wg.Wait()
	close(ch)
	codes := []int{}
	for code := range ch {
		codes = append(codes, code)
	}
	sort.Ints(codes)
	resourcesAssert(t, "W12-BUDGET-SQLITE-CONNECTIONS", []int{201, 422}, codes, Object{"sqlite_connections": 2, "same_database": true, "reservation_upper_bounds": []string{"2.00", "2.00"}, "cap": "2.00"})
}

func TestW12BudgetPrecisionAndModes(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("precision-and-modes", Empty(), Empty()))
	f.token = o.owner
	path := f.path("/goals/" + Str(o.goal, "id") + "/budget-policy")
	policy := f.expect(200, "GET", path, "", "", nil)
	policy = f.expect(200, "PUT", path, ID(), testTag(policy), capBody("0.3000000000000000001"))
	for _, amount := range []string{"0.1000000000000000001", "0.2"} {
		f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RESERVE", ID(), dollars(amount), "UPPER_BOUND", nil))
	}
	f.expect(422, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RESERVE", ID(), dollars("0.0000000000000000001"), "UPPER_BOUND", nil))
	estimated := capBody("10")
	estimated["enforcement"] = "ESTIMATED"
	estimated["unknown_cost_action"] = "ALLOW_AND_RECORD"
	policy = f.expect(200, "PUT", path, ID(), testTag(policy), estimated)
	f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "UNKNOWN", "unknown-estimated", nil, "UNKNOWN", nil))
	f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RESERVE", "estimated-known", dollars("1"), "ESTIMATE", nil))
	usage, e := f.s.BudgetUsage(context.Background(), o.owner, f.project, Str(r.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	future := capBody("0")
	future["effective_from"] = time.Now().UTC().Add(time.Hour).Format(time.RFC3339Nano)
	policy = f.expect(200, "PUT", path, ID(), testTag(policy), future)
	f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, Str(policy, "id"), "RESERVE", "prior-effective-policy", dollars("1"), "UPPER_BOUND", nil))
	resourcesAssert(t, "W12-BUDGET-DECIMAL-MODES", []any{1, 1, true}, []any{len(Arr(usage, "unknown")), len(Arr(usage, "estimated")), Arr(usage, "unknown")[0].(map[string]any)["money"] == nil}, Object{"projection": usage, "future_policy": policy, "decimal_boundary": "0.1000000000000000001 + 0.2 accepted; extra 0.0000000000000000001 rejected"})
}

func TestW12PreparedEffectFences(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("prepared-tighten", Empty(), Empty()))
	resourceCheckpoint(r, Object{"step": "not yet sent"})
	f.token = o.owner
	path := f.path("/goals/" + Str(o.goal, "id") + "/budget-policy")
	policy := f.expect(200, "GET", path, "", "", nil)
	key := "prepared-effect-tightening-key"
	cost := budgetRequest(r, Str(policy, "id"), "RESERVE", key, dollars("8"), "UPPER_BOUND", nil)
	intent, e := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key, Object{"operation": "bounded local fixture"}, cost)
	if e != nil {
		t.Fatal(e)
	}
	policy = f.expect(200, "PUT", path, ID(), testTag(policy), capBody("5"))
	_, e = f.s.BeginEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key)
	if e == nil {
		t.Fatal("prepared effect issued after cap tightening")
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	after, e := latestEffect(tx, f.project, Str(r.run, "id"), key)
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	resourcesAssert(t, "W12-PREPARED-TIGHTEN-FENCE", "PREPARED", after["state"], Object{"intent": intent, "tightened_policy": policy, "provider_calls": 0})
}

func TestW12CancelRetainsAccounting(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("cancel-unknown", Empty(), Empty()))
	resourceCheckpoint(r, Object{"step": "in-flight effect"})
	f.token = o.owner
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	key := "cancelled-unknown-provider-key"
	cost := budgetRequest(r, Str(policy, "id"), "UNKNOWN", key, nil, "UNKNOWN", nil)
	intent, e := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key, Object{"operation": "external unknown"}, cost)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.s.BeginEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key); e != nil {
		t.Fatal(e)
	}
	r.run = f.expect(200, "POST", f.path("/runs/"+Str(r.run, "id")+"/cancel"), ID(), testTag(r.run), Object{"reason": "user stop cannot erase issued liabilities"})
	if e = f.s.ObserveEffect(context.Background(), f.project, Str(r.run, "id"), key, "UNKNOWN", Object{"reason": "provider cannot confirm termination"}); e != nil {
		t.Fatal(e)
	}
	usage, e := f.s.BudgetUsage(context.Background(), o.owner, f.project, Str(r.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	revision, _ := Num(r.run, "revision")
	_, resumeErr := f.s.ResumeCheckpoint(context.Background(), o.owner, f.project, Str(r.run, "id"), "cancel-resume-not-allowed", revision)
	late := budgetRequest(r, Str(policy, "id"), "RECONCILE", key, dollars("2.75"), "ACTUAL", intent["reservation_id"])
	settled := f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), late)
	after, e := f.s.BudgetUsage(context.Background(), o.owner, f.project, Str(r.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	resourcesAssert(t, "W12-CANCEL-UNKNOWN-INFLIGHT", []any{"CANCEL_REQUESTED", 1, true, true, 1}, []any{r.run["status"], len(Arr(usage, "unknown")), len(Arr(usage, "in_flight")) >= 1, resumeErr != nil, len(Arr(after, "incurred"))}, Object{"before_late_usage": usage, "late_original_run": settled, "after_late_usage": after, "external_effect": "UNKNOWN_RETAINED"})
}
