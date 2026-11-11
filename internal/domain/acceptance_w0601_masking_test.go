package domain

import (
	"bytes"
	"context"
	"testing"
	"time"
)

// W06-01: the card's three masking negatives - a report that merely parses to the accepted marker,
// a runtime renamed to a stronger-sounding model, and a run whose last command exited 0 - must not
// mask a failing required check. Each refusal is paired with a control so it fails for its own reason.
func TestW06CardMaskingNegatives(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	countReceipts := func() int {
		var n int
		if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&n); e != nil {
			t.Fatal(e)
		}
		return n
	}
	computed := func(p *preparedAcceptance) Object { return p.checks[0].(Object) }

	// Control: the exact frozen expectation is what makes the required check pass, and the
	// independently computed row is what lands in the receipt.
	ctl := o.task("masking-control", Empty(), Empty())
	ctlNext := o.task("masking-control-next", []any{ctl["id"]}, Empty())
	cr := o.claim(ctl)
	ca := o.report(cr, []byte(`{"result":"verified"}`))
	cb := o.acceptance(cr, ca)
	cp, e := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, cb)
	if e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-01-CONTROL-EXACT-MATCH-COMPUTED-PASS", []any{"PASS", "PASS", 0},
		[]any{cp.verdict, computed(cp)["status"], computed(cp)["exit_code"]}, cp.checks)
	ctlReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(cr.task), cb)
	orchestrationAssert(t, "W06-01-CONTROL-ACCEPTED-AND-SUCCESSOR-READY", []any{"PASS", "ACCEPTED", "READY"},
		[]any{ctlReceipt["verdict"], Str(f.read("tasks", Str(ctl, "id")), "status"), Str(f.read("tasks", Str(ctlNext, "id")), "status")},
		Object{"receipt_verdict": ctlReceipt["verdict"], "task": f.read("tasks", Str(ctl, "id")), "successor": f.read("tasks", Str(ctlNext, "id"))})

	// Negative 1: the report contains the frozen expectation verbatim plus met/done/exit-0 markers.
	// A parser that reads the marker calls this success; exact equality against the frozen check does not.
	metRaw := []byte(`{"result":"verified","met":true,"done":true,"exit_code":0,"status":"ACCEPTED","verdict":"PASS"}`)
	met := o.task("masking-met", Empty(), Empty())
	metNext := o.task("masking-met-next", []any{met["id"]}, Empty())
	mr := o.claim(met)
	ma := o.report(mr, metRaw)
	mb := o.acceptance(mr, ma)
	mp, e := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, mb)
	if e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-01-NEG-MET-PARSE-COMPUTED-FAIL", []any{true, false, "FAIL", "FAIL", 1},
		[]any{bytes.Contains(metRaw, []byte(`"result":"verified"`)), bytes.Contains(metRaw, []byte(`{"result":"verified"}`)), mp.verdict, computed(mp)["status"], computed(mp)["exit_code"]},
		Object{"report_bytes": string(metRaw), "check": computed(mp)})
	metBefore := countReceipts()
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(mr.task), mb)
	orchestrationAssert(t, "W06-01-NEG-MET-PASS-VERDICT-REFUSED", []any{422, "GATE_FAILED", "requested verdict differs from independently computed checks", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - metBefore}, reply)
	mb["verdict"] = "FAIL"
	mReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(mr.task), mb)
	orchestrationAssert(t, "W06-01-NEG-MET-FAIL-VERDICT-ACCEPTED-NO-RELEASE", []any{"FAIL", "FAILED", "BLOCKED"},
		[]any{mReceipt["verdict"], Str(f.read("tasks", Str(met, "id")), "status"), Str(f.read("tasks", Str(metNext, "id")), "status")},
		Object{"task": f.read("tasks", Str(met, "id")), "successor": f.read("tasks", Str(metNext, "id"))})

	// Negative 2: the executor renames the runtime to a stronger-sounding model. The label is not
	// provenance: it buys no LIVE mode and it does not change the computed verdict.
	f.token = o.owner
	renamed := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{
		"name": "gpt-6-astra high-reasoning (qualified)", "adapter": "fixture", "adapter_revision": "1",
		"capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e = f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(renamed, "id")); e != nil {
		t.Fatal(e)
	}
	rn := o.task("masking-rename", Empty(), Empty())
	executor := ID()
	if e = f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		t.Fatal(e)
	}
	f.token = o.owner
	response := f.expect(201, "POST", f.path("/tasks/"+Str(rn, "id")+"/claim"), ID(), testTag(rn), Object{"runtime_id": renamed["id"], "executor_principal_id": executor, "context_bundle_id": rn["context_bundle_id"]})
	rr := &runtimeFixture{f: f, ownerToken: o.owner, executor: executor, lease: Str(response, "lease_token"), task: response["task"].(map[string]any), run: response["run"].(map[string]any), registration: renamed}
	f.token, e = f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	ra := o.report(rr, []byte(`{"result":"wrong"}`))
	ab := o.acceptance(rr, ra)
	orchestrationAssert(t, "W06-01-NEG-RENAME-RUNTIME-REGISTERS-AS-FIXTURE", []any{"gpt-6-astra high-reasoning (qualified)", "fixture", "FIXTURE"},
		[]any{Str(renamed, "name"), Str(renamed, "adapter"), Str(renamed, "measurement_mode")}, renamed)
	liveClaim := Object{}
	for k, v := range ab {
		liveClaim[k] = v
	}
	liveClaim["measurement_mode"] = "LIVE"
	renameBefore := countReceipts()
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(rr.task), liveClaim)
	orchestrationAssert(t, "W06-01-NEG-RENAME-LIVE-CLAIM-REFUSED", []any{503, "RESOURCE_UNAVAILABLE", "acceptance requires qualified native dispatch", 0},
		[]any{status, reply["code"], reply["message"], countReceipts() - renameBefore}, Object{"runtime": renamed, "rejection": reply})
	ab["verdict"] = "FAIL"
	rReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(rr.task), ab)
	orchestrationAssert(t, "W06-01-NEG-RENAME-MODE-STAYS-FIXTURE", []any{"FAIL", "FIXTURE", "fixture"},
		[]any{rReceipt["verdict"], rReceipt["measurement_mode"], Str(renamed, "adapter")}, rReceipt)

	// Negative 3: the run's last command exited 0 and the run settled. The executor copies that
	// exit-0/green shape into its own submitted check rows. The receipt carries the computed row.
	ex := o.task("masking-exit0", Empty(), Empty())
	er := o.claim(ex)
	ea := o.report(er, []byte(`{"result":"wrong","last_command":"lint","exit_code":0}`))
	eb := o.acceptance(er, ea)
	submitted := Arr(eb, "checks")[0].(map[string]any)
	submitted["status"] = "PASS"
	submitted["exit_code"] = 0
	submitted["actual"] = "last command lint exited 0; run settled"
	submitted["evidence_refs"] = []any{Ref(ea, "Artifact")}
	eb["verdict"] = "FAIL"
	eReceipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(er.task), eb)
	receiptCheck := Arr(eReceipt, "checks")[0].(map[string]any)
	orchestrationAssert(t, "W06-01-NEG-EXIT0-SUBMITTED-GREEN-CHECKS-NOT-IN-RECEIPT", []any{"FAIL", 1, int64(1)},
		[]any{receiptCheck["status"], receiptCheck["exit_code"], int64(len(Arr(eReceipt, "checks")))},
		Object{"submitted_row": submitted, "receipt_row": receiptCheck})
	orchestrationAssert(t, "W06-01-NEG-EXIT0-RUN-DECLARED-ZERO-AND-SETTLED", []any{0, true, "FAIL"},
		[]any{er.run["exit_code"], er.run["runtime_settled_at"] != nil, eReceipt["verdict"]},
		Object{"run_status": er.run["status"], "run_exit_code": er.run["exit_code"], "receipt_verdict": eReceipt["verdict"]})
	orchestrationAssert(t, "W06-01-NEG-EXIT0-SUBMITTED-ACTUAL-DISCARDED", false,
		bytes.Contains(Bytes(eReceipt), []byte("last command lint exited 0")), Object{"receipt": eReceipt})

	// Only the exact match was accepted in this fixture.
	var accepted int
	var acceptedTitle string
	if e = f.db.QueryRow("SELECT count(*), coalesce(group_concat(json_extract(body,'$.title'),''),'') FROM domain_objects WHERE kind='Task' AND json_extract(body,'$.status')='ACCEPTED'").Scan(&accepted, &acceptedTitle); e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-01-OUTPUT-ONLY-EXACT-MATCH-ACCEPTED", []any{1, "masking-control"}, []any{accepted, acceptedTitle}, Object{"accepted_tasks": acceptedTitle})
}
