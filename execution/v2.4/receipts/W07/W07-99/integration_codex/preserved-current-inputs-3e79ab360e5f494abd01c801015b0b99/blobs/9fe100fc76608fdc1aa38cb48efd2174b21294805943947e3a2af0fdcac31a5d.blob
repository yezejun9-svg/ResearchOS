package domain

import (
	"testing"
)

// W06-01 part H: the card action that says the final acceptance transaction re-checks side effects.
// The round-5 reviewer showed this branch is reachable inside this card's write_scope; these ids own it.
// An unresolved resource effect on the current epoch's run must stop acceptance, and reconciling the same
// effect key must let the identical request through - so the refusal can only be about reconciliation.
func TestW06Step4NegativesPartH(t *testing.T) {
	r := runtimeSetupMode(t, "FIXTURE")
	f := r.f
	output := r.seal([]byte(`{"result":"verified"}`))
	obs := r.observation("SETTLED", true)
	obs["artifacts"] = []any{Object{"path": "result.json", "content_hash": output["content_hash"], "byte_size": output["byte_size"]}}
	r.observe(obs)
	r.call("/report", r.report([]any{output["id"]}, 0), 200)
	f.switchPrincipal("runtime-independent-verifier", []string{"VERIFIER"})
	task := f.read("tasks", Str(r.task, "id"))
	r.task = task
	c := task["acceptance_contract"].(map[string]any)
	body := Object{"subject_ref": Ref(task, "Task"), "run_id": r.run["id"], "contract_hash": c["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": []any{Ref(output, "Artifact")}, "checks": []any{Object{"check_id": "json-result", "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": "orchestration.json-equals", "actual": "request independent verification", "exit_code": nil, "started_at": nil, "finished_at": nil}}, "verdict": "PASS", "executor_principal_ids": []any{r.executor}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": f.state()["policy_revision"], "measurement_mode": "FIXTURE", "reason": "frozen fixture qualification with an unreconciled effect"}

	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	unresolved := func() int {
		var n int
		if e := f.db.QueryRow(`SELECT count(*) FROM resource_effects x WHERE project=? AND run=? AND sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key) AND json_extract(body,'$.state') IN ('STARTED','UNKNOWN')`, f.project, Str(r.run, "id")).Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	appendEffect := func(state string) {
		tx, e := f.db.Begin()
		if e != nil {
			t.Fatal(e)
		}
		if e = effectAppend(tx, f.project, Str(r.run, "id"), "w0601-side-effect", Object{"state": state, "operation": "fixture-provider-call"}); e != nil {
			tx.Rollback()
			t.Fatal(e)
		}
		if e = tx.Commit(); e != nil {
			t.Fatal(e)
		}
	}

	// Baseline: nothing unresolved yet, so the same request shape would be accepted. Proving that here
	// would consume the acceptance, so the refusal is measured first and the control reuses the epoch
	// after reconciliation.
	appendEffect("UNKNOWN")
	orchestrationAssert(t, "W06-01-NEG-EFFECTS-SETUP-UNRESOLVED", 1, unresolved(), Object{"effect_key": "w0601-side-effect", "state": "UNKNOWN"})
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(task), body)
	orchestrationAssert(t, "W06-01-NEG-EFFECTS-UNRECONCILED-REFUSED", []any{409, "STATE_CONFLICT", "unknown effects require reconciliation; blind retry prohibited", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"guard": "acceptance.go:108 effectsReconciled", "refusal_string_owner": "durability.go:34", "task_status_after_refusal": Str(f.read("tasks", Str(task, "id")), "status")})

	// Reconciling the same effect key with a later resolved row lets the identical request land.
	appendEffect("DONE")
	orchestrationAssert(t, "W06-01-NEG-EFFECTS-CONTROL-RECONCILED", 0, unresolved(), Object{"effect_key": "w0601-side-effect", "latest_state": "DONE"})
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(task), body)
	orchestrationAssert(t, "W06-01-OUTPUT-EFFECTS-RECHECK-IS-INSIDE-THE-ACCEPTANCE-TRANSACTION", []any{"PASS", "ACCEPTED", 1},
		[]any{receipt["verdict"], Str(f.read("tasks", Str(task, "id")), "status"), countReceipts() - before},
		Object{"receipt_id": Str(receipt, "id"), "run_id": Str(receipt, "run_id"), "measurement_mode": receipt["measurement_mode"]})
}
