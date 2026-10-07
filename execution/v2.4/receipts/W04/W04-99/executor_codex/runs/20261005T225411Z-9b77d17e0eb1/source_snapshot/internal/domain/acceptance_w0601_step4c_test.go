package domain

import (
	"context"
	"testing"
	"time"
)

// W06-01 step-4 negatives, part C: the re-checks the round-1 review found unfalsified - verifier
// visibility over the subject, the use-qualification basis the receipt claims, and the settled
// current epoch binding. Each refusal is paired with a control on the same run.
func TestW06Step4NegativesPartC(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	runStatus := func(runID string) string {
		var s string
		if e := f.db.QueryRow("SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='Run' AND id=?", f.project, runID).Scan(&s); e != nil {
			t.Fatal(e)
		}
		return s
	}
	copyBody := func(b Object) Object {
		c, _ := Decode(Bytes(b))
		return c
	}

	// Verifier visibility and task ownership: a VERIFIER whose only grant is pinned to a different task.
	vis := o.task("visibility-ownership", Empty(), Empty())
	vr := o.claim(vis)
	va := o.report(vr, []byte(`{"result":"verified"}`))
	vb := o.acceptance(vr, va)
	other := o.task("visibility-other-task", Empty(), Empty())
	scoped := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: scoped, Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(other, "id")}}}); e != nil {
		t.Fatal(e)
	}
	var e error
	f.token, e = f.s.IssueCredential(context.Background(), scoped, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(vr.task), vb)
	orchestrationAssert(t, "W06-01-NEG-VISIBILITY-TASK-SCOPED-VERIFIER-REFUSED", []any{404, "NOT_FOUND", "project or object unavailable", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"mechanism": "fail-closed 404 rather than 403: a verifier whose grant is pinned to another task is not told the subject exists", "verifier_principal_id": scoped, "grant_pinned_to_task": Str(other, "id"), "subject_task": Str(vr.task, "id"), "rejection": reply})
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	vReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(vr.task), vb)
	orchestrationAssert(t, "W06-01-NEG-VISIBILITY-PROJECT-VERIFIER-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED"},
		[]any{vReceipt["verdict"], Str(f.read("tasks", Str(vis, "id")), "status")},
		Object{"accepting_verifier": vReceipt["verifier_principal_id"]})

	// Use qualification: the receipt may not claim a basis the service does not implement.
	qt := o.task("qualification-basis", Empty(), Empty())
	qr := o.claim(qt)
	qa := o.report(qr, []byte(`{"result":"verified"}`))
	qb := o.acceptance(qr, qa)
	basisClaim := copyBody(qb)
	basisClaim["independence_basis"] = "MODEL_RUBRIC"
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(qr.task), basisClaim)
	orchestrationAssert(t, "W06-01-NEG-QUALIFICATION-BASIS-REFUSED", []any{400, "INVALID_REQUEST", "request violates CreateAcceptanceRequest schema", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"layer_that_refuses": "the frozen request schema, before acceptance.go:180 can be reached over HTTP", "submitted_basis": basisClaim["independence_basis"], "rejection": reply})
	qualClaim := copyBody(qb)
	qualClaim["qualification_ids"] = []any{"invented-qualification"}
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(qr.task), qualClaim)
	orchestrationAssert(t, "W06-01-NEG-QUALIFICATION-IDS-REFUSED", []any{422, "GATE_FAILED", "only deterministic service verification is implemented", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before}, Object{"submitted_qualification_ids": qualClaim["qualification_ids"]})
	qReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(qr.task), qb)
	orchestrationAssert(t, "W06-01-NEG-QUALIFICATION-DETERMINISTIC-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED", "DETERMINISTIC_SERVICE", 0},
		[]any{qReceipt["verdict"], Str(f.read("tasks", Str(qt, "id")), "status"), Str(qReceipt, "independence_basis"), len(Arr(qReceipt, "qualification_ids"))}, qReceipt)

	// The settled current epoch binding: a run that is no longer SETTLED cannot be accepted.
	et := o.task("epoch-settled", Empty(), Empty())
	er := o.claim(et)
	ea := o.report(er, []byte(`{"result":"verified"}`))
	eb := o.acceptance(er, ea)
	settledBefore := runStatus(Str(er.run, "id"))
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status','RUNNING') WHERE project=? AND kind='Run' AND id=?", f.project, Str(er.run, "id")); e != nil {
		t.Fatal(e)
	}
	before = countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(er.task), eb)
	orchestrationAssert(t, "W06-01-NEG-EPOCH-NOT-SETTLED-REFUSED", []any{422, "GATE_FAILED", "settled current epoch and exact output/context binding required", "RUNNING", 0},
		[]any{status, reply["code"], reply["message"], runStatus(Str(er.run, "id")), countReceipts() - before},
		Object{"status_before_injection": settledBefore, "rejection": reply})
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.status',?) WHERE project=? AND kind='Run' AND id=?", settledBefore, f.project, Str(er.run, "id")); e != nil {
		t.Fatal(e)
	}
	eReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(er.task), eb)
	orchestrationAssert(t, "W06-01-NEG-EPOCH-RESTORED-CONTROL-ACCEPTED", []any{"PASS", "ACCEPTED", settledBefore},
		[]any{eReceipt["verdict"], Str(f.read("tasks", Str(et, "id")), "status"), runStatus(Str(er.run, "id"))},
		Object{"run_id": eReceipt["run_id"]})
}
