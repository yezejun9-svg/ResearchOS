package domain

import "testing"

// W06-01: the final acceptance transaction must write ACCEPTED, release the
// successor and append the outbox event in ONE service transaction, and a stale
// precondition must not be able to slip through it.
func TestW06AcceptanceTransactionAndStalePrecondition(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("w0601-tx", Empty(), Empty())
	next := o.task("w0601-tx-next", []any{task["id"]}, Empty())
	r := o.claim(task)
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	var outboxBefore, receiptsBefore int
	if e := f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&outboxBefore); e != nil {
		t.Fatal(e)
	}
	if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&receiptsBefore); e != nil {
		t.Fatal(e)
	}
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	orchestrationAssert(t, "W06-01-TX-ACCEPTED-201", 201, status, reply)
	st := Str(f.read("tasks", Str(task, "id")), "status")
	nst := Str(f.read("tasks", Str(next, "id")), "status")
	orchestrationAssert(t, "W06-01-TX-NO-LONGER-REPORTED", true, st != "EXECUTION_REPORTED", st)
	orchestrationAssert(t, "W06-01-TX-SUCCESSOR-RELEASED", "READY", nst, nst)
	var outboxAfter, receiptsAfter int
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&outboxAfter)
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&receiptsAfter)
	orchestrationAssert(t, "W06-01-TX-OUTBOX-APPENDED", true, outboxAfter > outboxBefore, []any{outboxBefore, outboxAfter})
	orchestrationAssert(t, "W06-01-TX-RECEIPT-PERSISTED", true, receiptsAfter > receiptsBefore, []any{receiptsBefore, receiptsAfter})
	// The precondition tag captured before the transaction is stale once the
	// acceptance has landed: replaying it must be refused, not double-accepted.
	stale := testTag(r.task)
	replay, replayReply, _ := f.request("POST", f.path("/acceptances"), ID(), stale, b)
	orchestrationAssert(t, "W06-01-TX-STALE-PRECONDITION-REFUSED", true, replay != 201, []any{stale, replay, replayReply})
	var afterReplay int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&afterReplay)
	orchestrationAssert(t, "W06-01-TX-STALE-REPLAY-NO-SECOND-RECEIPT", receiptsAfter, afterReplay, []any{receiptsAfter, afterReplay})
}
