package domain

import (
	"context"
	"testing"
	"time"
)

// W06-01 part F: the guards the round-3 review proved reachable but unowned.
// F1 the acceptance-level policy-revision comparison (acceptance.go:146) on a stale CLAIM, which is a
// different case from the state move that part B refused at the task-context layer.
// F2 the snapshot equality between the two reads (acceptance.go:348) via a run field no earlier clause
// inspects, so the refusal can only come from the equality test itself.
// F3 the verifier-visibility gate (acceptance.go:14) at service level, where the HTTP layer's earlier
// 404 cannot mask it.
// F4 output isolation (acceptance.go:208) with an evidence_kind the frozen schema actually accepts, so
// the attempt tests access_class rather than the enum.
func TestW06Step4NegativesPartF(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}

	// F1: the claim carries a policy revision the project state does not have.
	p1 := o.task("stale-policy-claim", Empty(), Empty())
	p1r := o.claim(p1)
	p1a := o.report(p1r, []byte(`{"result":"verified"}`))
	p1b := o.acceptance(p1r, p1a)
	claimed := p1b["policy_revision"]
	real := f.state()["policy_revision"]
	cur, ce := Num(f.state(), "policy_revision")
	if ce != nil {
		t.Fatal(ce)
	}
	mutated, _ := Decode(Bytes(p1b))
	mutated["policy_revision"] = cur + 1
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(p1r.task), mutated)
	orchestrationAssert(t, "W06-01-NEG-POLICY-CLAIM-STALE-REFUSED-BY-ACCEPTANCE-GUARD", []any{412, "STALE_INPUT", "policy revision changed", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"claimed_policy_revision": mutated["policy_revision"], "claim_in_accepted_request": claimed, "project_state_value": real, "rejection": reply})
	p1Receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(p1r.task), p1b)
	orchestrationAssert(t, "W06-01-NEG-POLICY-CLAIM-CURRENT-CONTROL-LANDS", []any{"PASS", "ACCEPTED"},
		[]any{p1Receipt["verdict"], Str(f.read("tasks", Str(p1, "id")), "status")}, p1Receipt)

	// F2: a run field that no earlier clause reads moves between the two reads.
	p2 := o.task("snapshot-drift", Empty(), Empty())
	p2r := o.claim(p2)
	p2a := o.report(p2r, []byte(`{"result":"verified"}`))
	p2b := o.acceptance(p2r, p2a)
	verifier := f.token
	prepared, e := f.s.prepareTaskAcceptance(context.Background(), verifier, f.project, p2b)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.heartbeat_at',?) WHERE project=? AND kind='Run' AND id=?", "2026-01-02T03:04:05Z", f.project, Str(p2r.run, "id")); e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	p, e := authenticate(tx, verifier)
	var finalErr error
	if e == nil {
		_, finalErr = f.s.acceptTask(tx, p, f.project, p2b, prepared, ID())
	}
	tx.Rollback()
	before = countReceipts()
	fault, isFault := finalErr.(*Fault)
	code, message := "", ""
	if isFault {
		code, message = fault.Code, fault.Message
	}
	statusCode := 0
	if isFault {
		statusCode = fault.Status
	}
	orchestrationAssert(t, "W06-01-NEG-SNAPSHOT-DRIFT-REFUSED-BY-EQUALITY-TEST", []any{412, "STALE_INPUT", "inputs changed during independent verification", 0},
		[]any{statusCode, code, message, countReceipts() - before},
		Object{"injected_field": "heartbeat_at", "not_inspected_by_any_earlier_clause": true, "rejection": finalErr})

	// F3: visibility decided by acceptanceSnapshot itself, with the earlier HTTP 404 out of the way.
	p3 := o.task("visibility-service-level", Empty(), Empty())
	p3r := o.claim(p3)
	p3a := o.report(p3r, []byte(`{"result":"verified"}`))
	p3b := o.acceptance(p3r, p3a)
	other := o.task("visibility-pinned-to-other-task", Empty(), Empty())
	scoped := ID()
	if e = f.s.ProvisionPrincipal(context.Background(), Principal{ID: scoped, Roles: []string{"VERIFIER"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(other, "id")}}}); e != nil {
		t.Fatal(e)
	}
	tok, cerr := f.s.IssueCredential(context.Background(), scoped, 15*time.Minute)
	if cerr != nil {
		t.Fatal(cerr)
	}
	tx2, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	sp, se := authenticate(tx2, tok)
	snapCode, snapMessage := 0, ""
	if se == nil {
		_, ve := f.s.acceptanceSnapshot(tx2, sp, f.project, p3b)
		if vf, ok := ve.(*Fault); ok {
			snapCode, snapMessage = vf.Status, vf.Message
		} else if ve != nil {
			snapMessage = ve.Error()
		}
	}
	tx2.Rollback()
	orchestrationAssert(t, "W06-01-NEG-VERIFIER-GRANT-SERVICE-LEVEL-REFUSED", []any{403, "current independent verifier grant required"},
		[]any{snapCode, snapMessage},
		Object{"guard_reached": "acceptance.go:11 - the grant scope decides before the visibility clause at :14, which is why :14 has no card-level id", "authenticate_error": se, "principal": scoped, "grant_pinned_to_task": Str(other, "id")})

	// F4: isolation with a schema-legal evidence_kind, so the refusal is about access_class.
	p4 := o.task("isolation-legal-evidence-kind", Empty(), Empty())
	p4r := o.claim(p4)
	p4a := o.report(p4r, []byte(`{"result":"verified"}`))
	raw := []byte(`{"verifier_only":"side observation"}`)
	f.token = o.owner
	tag := f.stateTag()
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	verifierToken := f.token
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	cStatus, created, _ := f.request("POST", f.path("/artifacts"), ID(), tag, Object{
		"run_id": p4r.run["id"], "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json",
		"byte_size": len(raw), "input_refs": p4r.task["input_refs"], "source_refs": Empty(),
		"produced_by": "orchestration-independent-verifier", "access_class": "VERIFIER_ONLY"})
	rStatus := 0
	var rReply Object
	if cStatus == 201 {
		etok, ee := f.s.IssueCredential(context.Background(), p4r.executor, 15*time.Minute)
		if ee != nil {
			t.Fatal(ee)
		}
		f.token = etok
		p4r.refresh()
		rStatus, rReply, _ = f.request("POST", f.path("/runs/"+Str(p4r.run, "id")+"/report"), ID(), testTag(p4r.run), Object{
			"lease_token": p4r.lease, "lease_epoch": p4r.run["lease_epoch"], "runtime_settled": true,
			"execution_report": "both artifacts declared", "exit_code": 0,
			"result_artifact_ids": []any{p4a["id"], created["id"]}, "checkpoint_artifact_id": nil})
	}
	aStatus := 0
	var aReply Object
	if rStatus == 200 {
		f.token = o.owner
		updated := f.read("tasks", Str(p4, "id"))
		refs := Empty()
		for _, id := range Arr(updated, "output_artifact_ids") {
			refs = append(refs, Object{"entity_type": "Artifact", "id": id, "revision": 1, "content_hash": nil})
		}
		p4b := o.acceptance(p4r, p4a)
		p4b["artifact_refs"] = refs
		p4b["input_refs"] = updated["input_refs"]
		f.token = verifierToken
		aStatus, aReply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(updated), p4b)
	}
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-ACCESS-CLASS-REFUSED-BEFORE-OUTPUT-VECTOR", []any{403, "FORBIDDEN", "restricted reference unavailable", 0, 0},
		[]any{cStatus, created["code"], created["message"], rStatus, aStatus},
		Object{"evidence_kind": "GENERATED", "access_class": "VERIFIER_ONLY", "creation_reply": created,
			"mechanism": "output isolation is enforced on the artifact-creation route, before any run can declare a verifier-only result; that is what leaves the acceptance-level clause at :208 without an external route",
			"run_id": p4r.run["id"], "report_reply": rReply, "acceptance_reply": aReply})
}
