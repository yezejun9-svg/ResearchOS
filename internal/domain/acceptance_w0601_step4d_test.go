package domain

import (
	"context"
	"testing"
)

// W06-01 step-4 negatives, part D: an unresolved blocking conflict that appears between the two
// independent reads. Card action 2 names 未决冲突 explicitly, so the refusal needs a card-level id.
func TestW06Step4NegativesPartD(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}

	// Control first: with no conflict outstanding, the same transaction lands.
	ct := o.task("conflict-control", Empty(), Empty())
	cr := o.claim(ct)
	ca := o.report(cr, []byte(`{"result":"verified"}`))
	cb := o.acceptance(cr, ca)
	cReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(cr.task), cb)
	orchestrationAssert(t, "W06-01-NEG-CONFLICT-NONE-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED", 0},
		[]any{cReceipt["verdict"], Str(f.read("tasks", Str(ct, "id")), "status"), len(Arr(f.read("tasks", Str(ct, "id")), "blocking_conflict_ids"))}, cReceipt)

	// Now the conflict arrives after the first read.
	xt := o.task("conflict-between-reads", Empty(), Empty())
	xr := o.claim(xt)
	xa := o.report(xr, []byte(`{"result":"verified"}`))
	xb := o.acceptance(xr, xa)
	verifier := f.token
	prepared, e := f.s.prepareTaskAcceptance(context.Background(), verifier, f.project, xb)
	if e != nil {
		t.Fatal(e)
	}
	f.token = o.owner
	conflict := f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{
		"kind": "ARTIFACT", "subject_refs": []any{Ref(xa, "Artifact"), Ref(o.req, "Requirement")},
		"description": "blocking observation raised after the verifier took its first read",
		"blocks_refs": []any{Ref(xr.task, "Task")}})
	f.token = verifier
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	p, e := authenticate(tx, verifier)
	var finalErr error
	if e == nil {
		_, finalErr = f.s.acceptTask(tx, p, f.project, xb, prepared, ID())
	}
	tx.Rollback()
	before := countReceipts()
	fault, isFault := finalErr.(*Fault)
	statusCode := 0
	code, message := "", ""
	if isFault {
		statusCode, code, message = fault.Status, fault.Code, fault.Message
	}
	orchestrationAssert(t, "W06-01-NEG-CONFLICT-BETWEEN-READS-REFUSED", []any{409, "STATE_CONFLICT", "blocking conflict unresolved", 0},
		[]any{statusCode, code, message, countReceipts() - before},
		Object{"conflict_id": Str(conflict, "id"), "task_blocking_conflicts": Str(f.read("tasks", Str(xt, "id")), "blocking_conflict_ids"), "rejection": finalErr})

	// The submitted vector claiming no conflicts cannot overrule the server's own read either.
	claimClean, _ := Decode(Bytes(xb))
	claimClean["blocking_conflict_ids"] = Empty()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(xr.task), claimClean)
	orchestrationAssert(t, "W06-01-NEG-CONFLICT-EMPTY-CLAIM-REFUSED", []any{409, "STATE_CONFLICT", "blocking conflict unresolved", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before}, Object{"submitted_blocking_conflict_ids": claimClean["blocking_conflict_ids"], "rejection": reply})
}
