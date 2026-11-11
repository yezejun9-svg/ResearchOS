package domain

import (
	"context"
	"testing"
	"time"
)

// W06-01 step-4 negatives, part E: closes the round-2 findings. E1 uses an independence_basis value the
// frozen schema accepts, so the refusal must come from the domain guard rather than the request layer.
// E2 puts a VERIFIER_ONLY artifact into the run's own output vector and records which layer refuses it.
func TestW06Step4NegativesPartE(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}

	// E1: SEPARATE_PRINCIPAL_AND_RUN is a schema-legal basis; acceptance.go:180 is what refuses it.
	bt := o.task("basis-separate-principal", Empty(), Empty())
	br := o.claim(bt)
	ba := o.report(br, []byte(`{"result":"verified"}`))
	bb := o.acceptance(br, ba)
	alt, _ := Decode(Bytes(bb))
	alt["independence_basis"] = "SEPARATE_PRINCIPAL_AND_RUN"
	before := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(br.task), alt)
	orchestrationAssert(t, "W06-01-NEG-BASIS-SEPARATE-PRINCIPAL-REFUSED-BY-DOMAIN-GUARD", []any{422, "GATE_FAILED", "only deterministic service verification is implemented", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - before},
		Object{"basis_submitted": alt["independence_basis"], "schema_allows_it": true, "rejection": reply})
	bReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(br.task), bb)
	orchestrationAssert(t, "W06-01-NEG-BASIS-DETERMINISTIC-CONTROL-STILL-LANDS", []any{"PASS", "ACCEPTED", "DETERMINISTIC_SERVICE"},
		[]any{bReceipt["verdict"], Str(f.read("tasks", Str(bt, "id")), "status"), Str(bReceipt, "independence_basis")}, bReceipt)

	// E2: isolation. The verifier records a side observation on the same run and the executor reports
	// both artifacts, so the task's output vector carries a VERIFIER_ONLY artifact.
	it := o.task("isolation-verifier-only", Empty(), Empty())
	ir := o.claim(it)
	ia := o.report(ir, []byte(`{"result":"verified"}`))
	raw := []byte(`{"verifier_only":"side observation"}`)
	f.token = o.owner
	tag := f.stateTag()
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	verifierToken := f.token
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	createStatus, created, _ := f.request("POST", f.path("/artifacts"), ID(), tag, Object{
		"run_id": ir.run["id"], "kind": "REPORT", "evidence_kind": "OBSERVATION", "measurement_mode": "FIXTURE",
		"content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json",
		"byte_size": len(raw), "input_refs": ir.task["input_refs"], "source_refs": Empty(),
		"produced_by": "orchestration-independent-verifier", "access_class": "VERIFIER_ONLY"})

	reportStatus := 0
	var reportReply Object
	if createStatus == 201 {
		tok, cerr := f.s.IssueCredential(context.Background(), ir.executor, 15*time.Minute)
		if cerr != nil {
			t.Fatal(cerr)
		}
		f.token = tok
		ir.refresh()
		reportStatus, reportReply, _ = f.request("POST", f.path("/runs/"+Str(ir.run, "id")+"/report"), ID(), testTag(ir.run), Object{
			"lease_token": ir.lease, "lease_epoch": ir.run["lease_epoch"], "runtime_settled": true,
			"execution_report": "both artifacts declared", "exit_code": 0,
			"result_artifact_ids": []any{ia["id"], created["id"]}, "checkpoint_artifact_id": nil})
	}
	acceptStatus := 0
	var acceptReply Object
	if reportStatus == 200 {
		f.token = o.owner
		updated := f.read("tasks", Str(it, "id"))
		refs := Empty()
		for _, id := range Arr(updated, "output_artifact_ids") {
			refs = append(refs, Object{"entity_type": "Artifact", "id": id, "revision": 1, "content_hash": nil})
		}
		eb := o.acceptance(ir, ia)
		eb["artifact_refs"] = refs
		eb["input_refs"] = updated["input_refs"]
		f.token = verifierToken
		acceptStatus, acceptReply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(updated), eb)
	}
	orchestrationAssert(t, "W06-01-NEG-ISOLATION-VERIFIER-ONLY-ARTIFACT-REFUSED-AT-CREATION", []any{400, 0, 0},
		[]any{createStatus, reportStatus, acceptStatus},
		Object{"creation_reply": created, "mechanism": "the isolation boundary is enforced where the artifact is created, so a verifier-only object cannot enter a run's output vector and acceptance.go:208 is unreachable from this path", "attempted_by": "orchestration-independent-verifier", "run_id": ir.run["id"], "report_reply": reportReply, "acceptance_reply": acceptReply})
}
