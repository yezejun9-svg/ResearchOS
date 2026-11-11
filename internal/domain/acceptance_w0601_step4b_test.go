package domain

import (
	"context"
	"testing"
)

// W06-01 step-4 negatives, part B: a required hard gate that cannot be run, and a state change that
// lands between the two independent reads. Both must refuse a PASS rather than be papered over.
func TestW06Step4NegativesPartB(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	rowsByCheck := func(checks []any) map[string]Object {
		m := map[string]Object{}
		for _, v := range checks {
			x := v.(map[string]any)
			m[Str(x, "check_id")] = x
		}
		return m
	}

	// A frozen contract with a second required gate whose command_key no deterministic handler serves.
	contract := orchestrationContract()
	second := Object{"check_id": "gate-unrunnable", "kind": "DETERMINISTIC", "required": true, "expected": `{"result":"verified"}`,
		"command_key": "orchestration.gate-unrunnable-v24", "rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}
	contract["checks"] = append(Arr(contract, "checks"), second)
	contract["contract_hash"] = contractDigest(contract)

	f.token = o.owner
	goal := f.read("goals", Str(o.goal, "id"))
	gt := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "gate-missing", "task_type": "json-verification", "stage": "verification",
		"dependency_task_ids": Empty(), "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": Empty(), "acceptance_contract": contract,
		"origin_problem_id": "orchestration-problem", "candidate_id": "gate-missing", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(gt)
	gt = f.read("tasks", Str(gt, "id"))
	gt = f.expect(200, "POST", f.path("/tasks/"+Str(gt, "id")+"/actions"), ID(), testTag(gt), Object{"action": "SUBMIT", "reason": "frozen contract with an unrunnable required gate"})
	frozen := f.read("tasks", Str(gt, "id"))["acceptance_contract"].(map[string]any)
	allRequired := true
	for _, v := range Arr(frozen, "checks") {
		if v.(map[string]any)["required"] != true {
			allRequired = false
		}
	}
	orchestrationAssert(t, "W06-01-NEG-GATE-CONTRACT-FROZE-TWO-REQUIRED-CHECKS", []any{2, true, Str(contract, "contract_hash")},
		[]any{len(Arr(frozen, "checks")), allRequired, Str(frozen, "contract_hash")}, Object{"frozen_contract": frozen})

	gr := o.claim(gt)
	ga := o.report(gr, []byte(`{"result":"verified"}`))
	gb := o.acceptance(gr, ga)
	gp, e := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, gb)
	if e != nil {
		t.Fatal(e)
	}
	gRows := rowsByCheck(gp.checks)
	orchestrationAssert(t, "W06-01-NEG-GATE-UNRUNNABLE-COMPUTES-NOT-RUN-AND-BLOCKS", []any{"BLOCKED", "PASS", "NOT_RUN", nil},
		[]any{gp.verdict, gRows["json-result"]["status"], gRows["gate-unrunnable"]["status"], gRows["gate-unrunnable"]["exit_code"]},
		Object{"runnable_row": gRows["json-result"], "unrunnable_row": gRows["gate-unrunnable"]})

	// A submitted vector that omits the second required gate cannot stand in for it.
	dropped := Object{}
	for k, v := range gb {
		dropped[k] = v
	}
	kept := []any{}
	for _, v := range Arr(dropped, "checks") {
		if Str(v.(map[string]any), "check_id") == "json-result" {
			kept = append(kept, v)
		}
	}
	dropped["checks"] = kept
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(gr.task), dropped)
	orchestrationAssert(t, "W06-01-NEG-GATE-MISSING-ROW-REFUSED", []any{422, "GATE_FAILED", "all frozen checks required", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before}, Object{"submitted_check_ids": []any{"json-result"}, "rejection": reply})

	// Reporting the unrunnable gate as PASS is refused; only the honest BLOCKED verdict lands.
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(gr.task), gb)
	orchestrationAssert(t, "W06-01-NEG-GATE-PASS-VERDICT-REFUSED", []any{422, "GATE_FAILED", "requested verdict differs from independently computed checks", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before}, reply)
	gb["verdict"] = "BLOCKED"
	gReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(gr.task), gb)
	gRecRows := rowsByCheck(Arr(gReceipt, "checks"))
	orchestrationAssert(t, "W06-01-NEG-GATE-BLOCKED-VERDICT-LANDS-UNRUNNABLE-RECORDED", []any{"BLOCKED", "BLOCKED", "NOT_RUN", nil},
		[]any{gReceipt["verdict"], Str(f.read("tasks", Str(gt, "id")), "status"), gRecRows["gate-unrunnable"]["status"], gRecRows["gate-unrunnable"]["exit_code"]},
		Object{"task": f.read("tasks", Str(gt, "id")), "unrunnable_row": gRecRows["gate-unrunnable"]})

	// State moving between the two reads: the policy revision changes after the first snapshot.
	pc := o.task("recheck-policy", Empty(), Empty())
	pr := o.claim(pc)
	pa := o.report(pr, []byte(`{"result":"verified"}`))
	pb := o.acceptance(pr, pa)
	prepared, e := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, pb)
	if e != nil {
		t.Fatal(e)
	}
	cur, e := Num(f.state(), "policy_revision")
	if e != nil {
		t.Fatal(e)
	}
	next := cur + 1
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.policy_revision',?) WHERE project=? AND kind='ProjectState'", next, f.project); e != nil {
		t.Fatal(e)
	}
	verifier := f.token
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	p, e := authenticate(tx, verifier)
	var finalErr error
	if e == nil {
		_, finalErr = f.s.acceptTask(tx, p, f.project, pb, prepared, ID())
	}
	tx.Rollback()
	before = countReceipts()
	fault, isFault := finalErr.(*Fault)
	statusCode := 0
	code, message := "", ""
	if isFault {
		statusCode, code, message = fault.Status, fault.Code, fault.Message
	}
	orchestrationAssert(t, "W06-01-NEG-RECHECK-POLICY-MOVED-REFUSED", []any{412, "STALE_INPUT", "context policy changed", 0},
		[]any{statusCode, code, message, countReceipts() - before},
		Object{"guard_hit": "the re-validated task context refuses before the acceptance-level policy revision comparison", "policy_revision_at_first_read": prepared.snapshot["policy_revision"], "policy_revision_now": f.state()["policy_revision"], "rejection": finalErr})

	// Control: restore the revision the acceptance claimed and the same transaction lands.
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.policy_revision',?) WHERE project=? AND kind='ProjectState'", cur, f.project); e != nil {
		t.Fatal(e)
	}
	pReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(pr.task), pb)
	restored, e := Num(f.state(), "policy_revision")
	if e != nil {
		t.Fatal(e)
	}
	atFirstRead, e := Num(prepared.snapshot, "policy_revision")
	if e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-01-NEG-RECHECK-POLICY-RESTORED-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED", true, true},
		[]any{pReceipt["verdict"], Str(f.read("tasks", Str(pc, "id")), "status"), restored == cur, restored == atFirstRead},
		Object{"restored_policy_revision": restored, "policy_revision_at_first_read": atFirstRead, "bumped_value": next})
}
