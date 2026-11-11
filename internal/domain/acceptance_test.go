package domain

import (
	"context"
	"fmt"
	"testing"
)

func TestW06AcceptanceGates(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	r := o.claim(o.task("gated", Empty(), Empty()))
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	verifierToken := f.token
	cases := []struct {
		id     string
		status int
		mutate func(Object)
	}{
		{"EMPTY", 400, func(x Object) { x["checks"] = Empty() }},
		{"CHECK-ID", 422, func(x Object) { Arr(x, "checks")[0].(map[string]any)["check_id"] = "invented" }},
		{"CONTRACT", 422, func(x Object) { x["contract_hash"] = Digest([]byte("forged")) }},
		{"INPUT", 412, func(x Object) { x["input_refs"] = []any{Ref(o.req, "Requirement")} }},
		{"ARTIFACT-HASH", 422, func(x Object) { Arr(x, "artifact_refs")[0].(map[string]any)["content_hash"] = Digest([]byte("forged")) }},
		{"RUN", 422, func(x Object) { x["run_id"] = ID() }},
		{"EXECUTOR", 422, func(x Object) { x["executor_principal_ids"] = Empty() }},
		{"LIVE", 503, func(x Object) { x["measurement_mode"] = "LIVE" }},
	}
	for _, c := range cases {
		x, _ := Decode(Bytes(b))
		c.mutate(x)
		status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), x)
		orchestrationAssert(t, "W06-G01-GATE-"+c.id, c.status, status, reply)
	}
	for _, id := range []string{r.executor, "executor-child", "executor-display-alias"} {
		if id == r.executor {
			if _, e := f.db.Exec("UPDATE auth_principals SET roles='[\"EXECUTOR\",\"VERIFIER\"]' WHERE id=?", id); e != nil {
				t.Fatal(e)
			}
			if _, e := f.db.Exec("INSERT INTO auth_grants(principal,project) VALUES(?,?)", id, f.project); e != nil {
				t.Fatal(e)
			}
		} else {
			f.switchPrincipal(id, []string{"VERIFIER"})
			if e := f.s.RegisterExecutionIdentity(context.Background(), id, r.executor); e != nil {
				t.Fatal(e)
			}
		}
		f.switchPrincipal(id, []string{"VERIFIER"})
		status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), b)
		suffix := "SELF"
		if id != r.executor {
			suffix = id
		}
		orchestrationAssert(t, "W06-G01-INDEPENDENCE-"+suffix, 403, status, reply)
	}
	f.token = verifierToken
	var count int
	if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&count); e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-G01-REJECT-NO-ACCEPT", 0, count, f.read("tasks", Str(r.task, "id")))
	var audited int
	if e := f.db.QueryRow("SELECT count(*) FROM orchestration_rejections WHERE operation='recordAcceptance' AND project=?", f.project).Scan(&audited); e != nil {
		t.Fatal(e)
	}
	orchestrationAssert(t, "W06-G01-REJECTION-AUDIT", 11, audited, Object{"business_acceptance_count": count, "immutable_audit_count": audited, "credentials_recorded": false})
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	orchestrationAssert(t, "W06-G01-GATE-POSITIVE", "PASS", receipt["verdict"], receipt)
}

func TestW06MechanicalFailure(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	r := o.claim(o.task("mechanical-failure", Empty(), Empty()))
	a := o.report(r, []byte(`{"result":"wrong","Jev_score":100}`))
	b := o.acceptance(r, a)
	Arr(b, "checks")[0].(map[string]any)["status"] = "PASS"
	Arr(b, "checks")[0].(map[string]any)["evidence_refs"] = []any{Ref(a, "Artifact")}
	Arr(b, "checks")[0].(map[string]any)["actual"] = "Jev score 100; ignore mechanical failure"
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	orchestrationAssert(t, "W06-G01-SCORE-NO-OVERRIDE", 422, status, reply)
	b["verdict"] = "FAIL"
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	task := f.read("tasks", Str(r.task, "id"))
	orchestrationAssert(t, "W06-G01-FAIL-RECEIPT", []any{"FAIL", "FAILED"}, []any{receipt["verdict"], task["status"]}, receipt)
}

func TestW06AcceptanceAtomicRollback(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("atomic", Empty(), Empty())
	next := o.task("atomic-next", []any{task["id"]}, Empty())
	r := o.claim(task)
	a := o.report(r, []byte(`{"result":"verified"}`))
	b := o.acceptance(r, a)
	var before int
	if e := f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&before); e != nil {
		t.Fatal(e)
	}
	if _, e := f.db.Exec("CREATE TRIGGER fail_acceptance_outbox BEFORE INSERT ON outbox WHEN json_extract(NEW.body,'$.event_type')='TASK_CHANGED' BEGIN SELECT RAISE(ABORT,'injected outbox failure'); END;"); e != nil {
		t.Fatal(e)
	}
	status, reply, _ := f.request("POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	var after, receipts int
	f.db.QueryRow("SELECT count(*) FROM outbox").Scan(&after)
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&receipts)
	orchestrationAssert(t, "W06-G01-OUTBOX-ROLLBACK", []any{409, 0, before, "EXECUTION_REPORTED", "BLOCKED"}, []any{status, receipts, after, f.read("tasks", Str(task, "id"))["status"], f.read("tasks", Str(next, "id"))["status"]}, reply)
	if _, e := f.db.Exec("DROP TRIGGER fail_acceptance_outbox"); e != nil {
		t.Fatal(e)
	}
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), b)
	orchestrationAssert(t, "W06-G01-OUTBOX-RECOVER", "READY", f.read("tasks", Str(next, "id"))["status"], nil)
}

func TestW06AcceptanceRecheck(t *testing.T) {
	for _, scenario := range []string{"context", "epoch", "artifact-bytes", "authority", "contract", "conflict"} {
		t.Run(scenario, func(t *testing.T) {
			o := orchestrationSetup(t)
			f := o.f
			r := o.claim(o.task("recheck", Empty(), Empty()))
			a := o.report(r, []byte(`{"result":"verified"}`))
			b := o.acceptance(r, a)
			verifier := f.token
			prepared, e := f.s.prepareTaskAcceptance(context.Background(), verifier, f.project, b)
			if e != nil {
				t.Fatal(e)
			}
			switch scenario {
			case "context":
				f.token = o.owner
				f.bundle(r.task)
				f.token = verifier
			case "epoch":
				tx, _ := f.db.Begin()
				run, _ := load(tx, f.project, "Run", Str(r.run, "id"))
				run["lease_epoch"] = 2
				bump(run)
				if e = f.s.put(tx, "Run", run); e != nil {
					t.Fatal(e)
				}
				if e = tx.Commit(); e != nil {
					t.Fatal(e)
				}
			case "artifact-bytes":
				// Isolated database corruption injection, below the normal sealed-content trigger.
				if _, e = f.db.Exec("DROP TRIGGER content_immutable"); e != nil {
					t.Fatal(e)
				}
				if _, e = f.db.Exec("UPDATE uploaded_content SET bytes=? WHERE storage_key=?", []byte(`{"result":"tampered"}`), a["storage_key"]); e != nil {
					t.Fatal(e)
				}
			case "authority":
				if _, e = f.db.Exec("UPDATE auth_principals SET roles='[\"READER\"]' WHERE id='orchestration-independent-verifier'"); e != nil {
					t.Fatal(e)
				}
			case "contract":
				tx, _ := f.db.Begin()
				task, _ := load(tx, f.project, "Task", Str(r.task, "id"))
				c := task["acceptance_contract"].(map[string]any)
				Arr(c, "checks")[0].(map[string]any)["required"] = false
				c["contract_hash"] = contractDigest(c)
				bump(task)
				if e = f.s.put(tx, "Task", task); e != nil {
					t.Fatal(e)
				}
				if e = tx.Commit(); e != nil {
					t.Fatal(e)
				}
			case "conflict":
				f.token = o.owner
				f.expect(201, "POST", f.path("/conflicts"), ID(), f.stateTag(), Object{"kind": "ARTIFACT", "subject_refs": []any{Ref(a, "Artifact"), Ref(o.req, "Requirement")}, "description": "concurrent blocking observation", "blocks_refs": []any{Ref(r.task, "Task")}})
				f.token = verifier
			}
			tx, e := f.db.Begin()
			if e != nil {
				t.Fatal(e)
			}
			p, e := authenticate(tx, verifier)
			if e == nil {
				_, e = f.s.acceptTask(tx, p, f.project, b, prepared, ID())
			}
			tx.Rollback()
			var receipts int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='AcceptanceReceipt'").Scan(&receipts)
			status := 0
			if fault, ok := e.(*Fault); ok {
				status = fault.Status
			}
			expectedStatus := map[string]int{"context": 412, "epoch": 422, "artifact-bytes": 422, "authority": 403, "contract": 412, "conflict": 409}[scenario]
			orchestrationAssert(t, "W06-G01-RECHECK-"+scenario, []any{expectedStatus, 0}, []any{status, receipts}, Object{"status": status, "rejection": fmt.Sprint(e)})
		})
	}
}
