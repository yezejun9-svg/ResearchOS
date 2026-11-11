package domain

import (
	"fmt"
	"sync"
	"testing"
)

func resourcesAssert(t *testing.T, id string, want, got, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W12_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status != "PASS" {
		t.Fatalf("%s mismatch", id)
	}
}
func dollars(s string) Object { return Object{"amount": s, "currency": "USD"} }
func budgetRequest(r *runtimeFixture, policy, op, request string, money any, basis string, reservation any) Object {
	return Object{"policy_id": policy, "run_id": r.run["id"], "operation": op, "money": money, "provider_request_id": request, "provider_event_id": ID(), "reservation_id": reservation, "cost_basis": basis, "occurred_at": Now()}
}
func capBody(amount string) Object {
	return Object{"mode": "CAPPED", "cap": dollars(amount), "enforcement": "STRICT", "period": "LIFETIME", "timezone": "Asia/Shanghai", "effective_from": Now(), "unknown_cost_action": "BLOCK"}
}
func TestW12Budget(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	task := o.task("budget", Empty(), Empty())
	r := o.claim(task)
	f.token = o.owner
	goalPath := f.path("/goals/" + Str(o.goal, "id") + "/budget-policy")
	policy := f.expect(200, "GET", goalPath, "", "", nil)
	pid := Str(policy, "id")
	initial := f.expect(200, "GET", f.path("/budget-policy"), "", "", nil)
	add := func(op, request string, money any, basis string, reservation any) Object {
		return f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, pid, op, request, money, basis, reservation))
	}
	unknown := add("UNKNOWN", "unknown-one", nil, "UNKNOWN", nil)
	resourcesAssert(t, "C13-01", true, initial["mode"] == "UNLIMITED_AMOUNT" && initial["cap"] == nil && unknown["money"] == nil && unknown["cost_basis"] == "UNKNOWN", Object{"policy": initial, "ledger": unknown})
	add("RECONCILE", "unknown-one", dollars("6.00"), "ACTUAL", unknown["id"])
	reserve := add("RESERVE", "already-inflight", dollars("2.00"), "UPPER_BOUND", nil)
	policy = f.expect(200, "PUT", goalPath, ID(), testTag(policy), capBody("20.00"))
	initial = f.expect(200, "PUT", f.path("/budget-policy"), ID(), testTag(initial), capBody("10.00"))
	var wg sync.WaitGroup
	codes := make(chan int, 2)
	for range 2 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			code, _, _ := f.request("POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, pid, "RESERVE", ID(), dollars("2.00"), "UPPER_BOUND", nil))
			codes <- code
		}()
	}
	wg.Wait()
	close(codes)
	passed, blocked := 0, 0
	for c := range codes {
		if c == 201 {
			passed++
		}
		if c == 422 {
			blocked++
		}
	}
	resourcesAssert(t, "C14-01", []int{1, 1}, []int{passed, blocked}, Object{"parent_policy": initial, "child_policy": policy, "prior_reserved": reserve})
	outcomes := []int{}
	for _, b := range []Object{budgetRequest(r, pid, "UNKNOWN", ID(), nil, "UNKNOWN", nil), budgetRequest(r, pid, "RESERVE", ID(), Object{"amount": "0", "currency": "EUR"}, "UPPER_BOUND", nil), budgetRequest(r, pid, "RESERVE", ID(), dollars("0"), "ESTIMATE", nil)} {
		code, _, _ := f.request("POST", f.path("/budget-ledger"), ID(), testTag(policy), b)
		outcomes = append(outcomes, code)
	}
	resourcesAssert(t, "C14-02", []int{422, 422, 422}, outcomes, nil)
	initial = f.expect(200, "PUT", f.path("/budget-policy"), ID(), testTag(initial), capBody("1.00"))
	f.expect(422, "POST", f.path("/budget-ledger"), ID(), testTag(policy), budgetRequest(r, pid, "RESERVE", ID(), dollars("0.01"), "UPPER_BOUND", nil))
	// Stop request retains all reservations and permits late final accounting.
	r.run = f.expect(200, "POST", f.path("/runs/"+Str(r.run, "id")+"/cancel"), ID(), testTag(r.run), Object{"reason": "late cost test"})
	late := add("COMMIT", "already-inflight", dollars("2.50"), "ACTUAL", reserve["id"])
	resourcesAssert(t, "C14-03", true, late["run_id"] == r.run["id"] && late["money"].(map[string]any)["amount"] == "2.50" && initial["cap"].(map[string]any)["amount"] == "1.00", Object{"late": late, "run": r.run})
	b := budgetRequest(r, pid, "COMMIT", "already-inflight", dollars("2.50"), "ACTUAL", reserve["id"])
	b["provider_event_id"] = late["provider_event_id"]
	b["occurred_at"] = late["occurred_at"]
	duplicate := f.expect(201, "POST", f.path("/budget-ledger"), ID(), testTag(policy), b)
	b["money"] = dollars("3")
	f.expect(409, "POST", f.path("/budget-ledger"), ID(), testTag(policy), b)
	resourcesAssert(t, "W12-BUDGET-REPLAY", late["id"], duplicate["id"], nil)
}

func TestW12BudgetSettlementChain(t *testing.T) {
	for _, scenario := range []string{"unknown-alias", "late-correction"} {
		t.Run(scenario, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			resourceHTTP(f)
			r := o.claim(o.task(scenario, Empty(), Empty()))
			f.token = o.owner
			path := f.path("/goals/" + Str(o.goal, "id") + "/budget-policy")
			policy := f.expect(200, "GET", path, "", "", nil)
			policy = f.expect(200, "PUT", path, ID(), testTag(policy), capBody("10.00"))
			pid := Str(policy, "id")
			body := func(op, amount string, reservation any) Object {
				var money any = dollars(amount)
				basis := "ACTUAL"
				if op == "RESERVE" {
					basis = "UPPER_BOUND"
				}
				if op == "UNKNOWN" {
					money = nil
					basis = "UNKNOWN"
				}
				return budgetRequest(r, pid, op, "original-request", money, basis, reservation)
			}
			add := func(status int, b Object) Object {
				return f.expect(status, "POST", f.path("/budget-ledger"), ID(), testTag(policy), b)
			}
			reserve := add(201, body("RESERVE", "6", nil))
			var unknown Object
			if scenario == "unknown-alias" {
				unknown = add(201, body("UNKNOWN", "", reserve["id"]))
			}
			committed := add(201, body("COMMIT", "6", reserve["id"]))
			if scenario == "unknown-alias" {
				add(422, body("COMMIT", "0", unknown["id"]))
				add(409, body("COMMIT", "0", reserve["id"]))
				add(409, body("UNKNOWN", "", reserve["id"]))
				extra := body("RESERVE", "10", nil)
				extra["provider_request_id"] = "new-request"
				add(422, extra)
				resourcesAssert(t, "W12-BUDGET-ALIAS-FENCE", true, true, Object{"root": reserve, "unknown": unknown, "committed": committed, "alias_commit_status": 422, "second_commit_status": 409, "new_reserve_status": 422})
			} else {
				correctionBody := body("RECONCILE", "7", reserve["id"])
				corrected := add(201, correctionBody)
				replayed := add(201, correctionBody)
				extra := body("RESERVE", "4", nil)
				extra["provider_request_id"] = "new-request"
				add(422, extra)
				extra = body("RESERVE", "3", nil)
				extra["provider_request_id"] = "allowed-request"
				add(201, extra)
				var history int
				if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')='original-request'").Scan(&history); e != nil {
					t.Fatal(e)
				}
				resourcesAssert(t, "W12-BUDGET-LATE-CORRECTION", []any{3, true}, []any{history, corrected["id"] == replayed["id"]}, Object{"original_commit": committed, "late_correction": corrected, "new_four_status": 422, "new_three_status": 201})
			}
		})
	}
}
