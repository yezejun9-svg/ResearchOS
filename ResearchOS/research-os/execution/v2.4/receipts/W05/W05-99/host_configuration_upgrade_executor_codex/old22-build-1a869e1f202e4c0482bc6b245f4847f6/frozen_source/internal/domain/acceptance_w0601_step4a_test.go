package domain

import (
	"bytes"
	"context"
	"testing"
)

// W06-01 step-4 negatives, part A: an executor signing its own acceptance, a stale input vector,
// and a high Jev score standing over a failing required check. Each refusal is paired with a
// control on the same bytes so it can only fire for the reason its id names.
func TestW06Step4NegativesPartA(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}

	// Self-approval. The executor is given VERIFIER roles and a project grant, so the refusal cannot
	// be about missing credentials: only the shared authority root can be what stops it.
	sa := o.task("self-approval", Empty(), Empty())
	saNext := o.task("self-approval-next", []any{sa["id"]}, Empty())
	sr := o.claim(sa)
	saArt := o.report(sr, []byte(`{"result":"verified"}`))
	sb := o.acceptance(sr, saArt)
	if _, e := f.db.Exec("UPDATE auth_principals SET roles='[\"EXECUTOR\",\"VERIFIER\"]' WHERE id=?", sr.executor); e != nil {
		t.Fatal(e)
	}
	if _, e := f.db.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", sr.executor, f.project); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal(sr.executor, []string{"VERIFIER"})
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(sr.task), sb)
	orchestrationAssert(t, "W06-01-NEG-SELF-APPROVAL-REFUSED", []any{403, "FORBIDDEN", "executor, alias or delegated authority cannot accept own output", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"executor_principal_id": sr.executor, "roles_granted": true, "project_granted": true})
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	sReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(sr.task), sb)
	orchestrationAssert(t, "W06-01-NEG-SELF-APPROVAL-VERIFIER-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED", "READY"},
		[]any{sReceipt["verdict"], Str(f.read("tasks", Str(sa, "id")), "status"), Str(f.read("tasks", Str(saNext, "id")), "status")},
		Object{"verifier_principal_id": sReceipt["verifier_principal_id"], "executor_principal_id": sr.executor})

	// Stale input vector. The task, run, contract and artifacts are all current; only the submitted
	// input vector names a different version, so the refusal cannot be blamed on anything else.
	st := o.task("stale-input", Empty(), Empty())
	stNext := o.task("stale-input-next", []any{st["id"]}, Empty())
	tr := o.claim(st)
	ta := o.report(tr, []byte(`{"result":"verified"}`))
	tb := o.acceptance(tr, ta)
	currentVector := tb["input_refs"]
	tb["input_refs"] = []any{Ref(o.req, "Requirement")}
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(tr.task), tb)
	orchestrationAssert(t, "W06-01-NEG-STALE-INPUT-REFUSED", []any{412, "STALE_INPUT", "acceptance input vector mismatch", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"submitted_vector": tb["input_refs"], "task_vector": Str(f.read("tasks", Str(st, "id")), "input_refs")})
	tb["input_refs"] = currentVector
	tReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(tr.task), tb)
	orchestrationAssert(t, "W06-01-NEG-STALE-INPUT-CURRENT-VECTOR-CONTROL", []any{"PASS", "ACCEPTED", "READY"},
		[]any{tReceipt["verdict"], Str(f.read("tasks", Str(st, "id")), "status"), Str(f.read("tasks", Str(stNext, "id")), "status")},
		Object{"restored_vector": currentVector})

	// High score over a failing check. The report carries the frozen marker AND Jev_score 100.
	scoreRaw := []byte(`{"result":"verified","Jev_score":100,"grade":"A"}`)
	sc := o.task("high-score", Empty(), Empty())
	scNext := o.task("high-score-next", []any{sc["id"]}, Empty())
	cr := o.claim(sc)
	ca := o.report(cr, scoreRaw)
	cb := o.acceptance(cr, ca)
	cp, e := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, cb)
	if e != nil {
		t.Fatal(e)
	}
	cRow := cp.checks[0].(Object)
	orchestrationAssert(t, "W06-01-NEG-SCORE-COMPUTED-FAIL", []any{true, "FAIL", "FAIL", 1},
		[]any{bytes.Contains(scoreRaw, []byte(`"Jev_score":100`)), cp.verdict, cRow["status"], cRow["exit_code"]},
		Object{"report_bytes": string(scoreRaw), "check": cRow})
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(cr.task), cb)
	orchestrationAssert(t, "W06-01-NEG-SCORE-PASS-VERDICT-REFUSED", []any{422, "GATE_FAILED", "requested verdict differs from independently computed checks", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before}, reply)
	cb["verdict"] = "FAIL"
	scReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(cr.task), cb)
	scRow := Arr(scReceipt, "checks")[0].(map[string]any)
	orchestrationAssert(t, "W06-01-NEG-SCORE-OBSERVED-NOT-DECISIVE", []any{"FAIL", "FAIL", 1, true, "FAILED", "BLOCKED"},
		[]any{scReceipt["verdict"], scRow["status"], scRow["exit_code"], bytes.Contains(Bytes(scReceipt), []byte("Jev_score")), Str(f.read("tasks", Str(sc, "id")), "status"), Str(f.read("tasks", Str(scNext, "id")), "status")},
		Object{"receipt_check_actual": scRow["actual"], "report_bytes": string(scoreRaw)})
}
