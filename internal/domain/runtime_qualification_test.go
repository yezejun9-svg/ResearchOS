package domain

import (
	"context"
	"testing"
)

func acceptedRuntimeQualification(t *testing.T) (*runtimeFixture, Object, Object) {
	t.Helper()
	r := runtimeSetupMode(t, "FIXTURE")
	f := r.f
	output := r.seal([]byte(`{"result":"verified"}`))
	obs := r.observation("SETTLED", true)
	obs["artifacts"] = []any{Object{"path": "result.json", "content_hash": output["content_hash"], "byte_size": output["byte_size"]}}
	log := r.sealKind(Bytes(obs), "LOG")
	r.observe(obs)
	r.call("/report", r.report([]any{output["id"]}, 0), 200)
	f.switchPrincipal("runtime-independent-verifier", []string{"VERIFIER"})
	task := f.read("tasks", Str(r.task, "id"))
	r.task = task
	c := task["acceptance_contract"].(map[string]any)
	body := Object{"subject_ref": Ref(task, "Task"), "run_id": r.run["id"], "contract_hash": c["contract_hash"], "input_refs": task["input_refs"], "artifact_refs": []any{Ref(output, "Artifact")}, "checks": []any{Object{"check_id": "json-result", "status": "NOT_RUN", "evidence_refs": Empty(), "command_key": "orchestration.json-equals", "actual": "request independent verification", "exit_code": nil, "started_at": nil, "finished_at": nil}}, "verdict": "PASS", "executor_principal_ids": []any{r.executor}, "independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": Empty(), "qualification_ids": Empty(), "policy_revision": f.state()["policy_revision"], "measurement_mode": "FIXTURE", "reason": "frozen fixture qualification"}
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(task), body)
	if receipt["verdict"] != "PASS" || receipt["measurement_mode"] != "FIXTURE" {
		t.Fatalf("qualification acceptance mismatch: %s", Bytes(receipt))
	}
	return r, receipt, log
}

func TestRuntimeQualificationS1HTTP(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	body := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
	path := f.path("/runtimes/" + Str(r.registration, "id") + "/qualify")
	f.expect(428, "POST", path, "", testTag(r.registration), body)
	f.expect(428, "POST", path, ID(), "", body)
	bad := Object{"qualification_ids": []any{receipt["id"], receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
	f.expect(422, "POST", path, ID(), testTag(r.registration), bad)
	resume := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": true, "resume_evidence_ref": Ref(log, "Artifact"), "receipt_artifact_ref": Ref(log, "Artifact")}
	f.expect(422, "POST", path, ID(), testTag(r.registration), resume)
	key := ID()
	rt := f.expect(200, "POST", path, key, testTag(r.registration), body)
	if rt["status"] != "AVAILABLE" || Hash(rt["qualification_ids"]) != Hash([]any{receipt["id"]}) {
		t.Fatalf("qualification update mismatch: %s", Bytes(rt))
	}
	f.expect(200, "POST", path, key, testTag(r.registration), body)
	f.expect(412, "POST", path, ID(), testTag(r.registration), body)
	current := f.read("runtimes", Str(rt, "id"))
	if Hash(current) != Hash(rt) {
		t.Fatal("runtime visibility lost accepted receipt")
	}
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	admission, e := f.s.currentRuntimeAdmission(tx, f.project, nil, current, []any{"start"}, "claim")
	tx.Rollback()
	if e != nil || admission["mode"] != "FIXTURE" {
		t.Fatalf("qualified fixture admission failed: %v %s", e, Bytes(admission))
	}
	if _, _, err := f.s.BeginRuntimeQualification(context.Background(), r.ownerToken, f.project, Str(r.task, "id"), Str(rt, "id"), r.executor); err == nil {
		t.Fatal("bootstrap repeated")
	}
	if e := f.s.RevokePrincipal(context.Background(), "runtime-independent-verifier"); e != nil {
		t.Fatal(e)
	}
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, e = f.s.currentRuntimeAdmission(tx, f.project, nil, current, []any{"start"}, "claim")
	tx.Rollback()
	if e == nil {
		t.Fatal("revoked signer retained runtime admission")
	}
}

func TestRuntimeQualificationS1RejectsFalseReceipts(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	path := f.path("/runtimes/" + Str(r.registration, "id") + "/qualify")
	base := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
	wrong := Object{"qualification_ids": []any{r.task["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
	f.expect(422, "POST", path, ID(), testTag(r.registration), wrong)
	wrong = Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(r.task, "Task")}
	f.expect(422, "POST", path, ID(), testTag(r.registration), wrong)
	// A verifier who signed the Task acceptance must remain authorized even when
	// another current verifier submits the final runtime qualification.
	if e := f.s.RevokePrincipal(context.Background(), "runtime-independent-verifier"); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("runtime-later-verifier", []string{"VERIFIER"})
	f.expect(403, "POST", path, ID(), testTag(r.registration), base)
}

func TestRuntimeQualificationS1RejectsTamperedHostBytes(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	if _, e := f.db.Exec("UPDATE uploaded_content SET bytes=? WHERE project=? AND storage_key=?", []byte(`{"tampered":true}`), f.project, log["storage_key"]); e == nil {
		t.Fatal("sealed bytes unexpectedly writable")
	}
	ref := Ref(log, "Artifact")
	ref["content_hash"] = Digest([]byte(`{"tampered":true}`))
	body := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": ref}
	f.expect(422, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), body)
}

func TestRuntimeQualificationS1RejectsChangedProfileAndIdentity(t *testing.T) {
	for _, field := range []string{"adapter_revision", "profile_validity"} {
		t.Run(field, func(t *testing.T) {
			r, receipt, log := acceptedRuntimeQualification(t)
			f := r.f
			if field == "adapter_revision" {
				if _, e := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.adapter_revision','other-build') WHERE project=? AND kind='RuntimeRegistration' AND id=?", f.project, r.registration["id"]); e != nil {
					t.Fatal(e)
				}
			} else {
				var raw string
				if e := f.db.QueryRow("SELECT profile_ref FROM runtime_bindings WHERE project=? AND runtime=?", f.project, r.registration["id"]).Scan(&raw); e != nil {
					t.Fatal(e)
				}
				ref, e := Decode([]byte(raw))
				if e != nil {
					t.Fatal(e)
				}
				if _, e = f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.validity','STALE') WHERE project=? AND kind='Artifact' AND id=?", f.project, ref["id"]); e != nil {
					t.Fatal(e)
				}
			}
			body := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
			code, _, _ := f.request("POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), body)
			if code < 400 {
				t.Fatalf("changed %s retained qualification: HTTP %d", field, code)
			}
		})
	}
}

func TestRuntimeQualificationS1RejectsSharedAuthorityRoot(t *testing.T) {
	r, receipt, log := acceptedRuntimeQualification(t)
	f := r.f
	if e := f.s.RegisterExecutionIdentity(context.Background(), "runtime-independent-verifier", f.owner); e != nil {
		t.Fatal(e)
	}
	f.switchPrincipal("runtime-later-verifier", []string{"VERIFIER"})
	body := Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")}
	f.expect(403, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), body)
}

func TestRuntimeQualificationS1BudgetAndNoProviderAuthority(t *testing.T) {
	t.Run("unknown_bound", func(t *testing.T) {
		r := runtimeSetupModeHook(t, "LIVE", "", nil, true, false)
		var count int
		if e := r.f.db.QueryRow("SELECT count(*) FROM runtime_qualification_plans WHERE project=? AND task=?", r.f.project, r.task["id"]).Scan(&count); e != nil || count != 0 {
			t.Fatalf("invalid plan persisted: %d %v", count, e)
		}
	})
	t.Run("strict_cap", func(t *testing.T) {
		r := runtimeSetupModeHook(t, "LIVE", "1", func(f *fixture, goal Object) {
			path := f.path("/goals/" + Str(goal, "id") + "/budget-policy")
			policy := f.expect(200, "GET", path, "", "", nil)
			f.expect(200, "PUT", path, ID(), testTag(policy), capBody("0.5"))
		}, false, true)
		var runs, charges int
		r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Run' AND json_extract(body,'$.task_id')=?", r.f.project, r.task["id"]).Scan(&runs)
		r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id') LIKE 'qualification-dispatch/%'", r.f.project).Scan(&charges)
		if runs != 0 || charges != 0 || r.f.read("tasks", Str(r.task, "id"))["status"] != "DRAFT" {
			t.Fatalf("failed claim left authority: runs=%d charges=%d", runs, charges)
		}
	})
	t.Run("no_provider_and_release", func(t *testing.T) {
		r := runtimeSetup(t)
		f := r.f
		executorToken := f.token
		f.token = r.ownerToken
		goal := f.read("goals", Str(r.task, "goal_id"))
		f.token = executorToken
		cost := Object{"policy_id": goal["budget_policy_id"], "run_id": r.run["id"], "operation": "RESERVE", "money": dollars("0.1"), "provider_request_id": "forbidden-provider-call", "provider_event_id": ID(), "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()}
		if _, e := f.s.PrepareEffect(context.Background(), r.ownerToken, f.project, Str(r.run, "id"), ID(), Object{"route": "forbidden"}, cost); e == nil {
			t.Fatal("qualification marker authorized provider effect")
		}
		var effects int
		f.db.QueryRow("SELECT count(*) FROM resource_effects WHERE project=? AND run=?", f.project, r.run["id"]).Scan(&effects)
		if effects != 0 {
			t.Fatal("provider effect persisted")
		}
		out := r.seal([]byte(`{"result":"verified"}`))
		obs := r.observation("SETTLED", true)
		obs["artifacts"] = []any{Object{"path": "result.json", "content_hash": out["content_hash"], "byte_size": out["byte_size"]}}
		r.observe(obs)
		r.call("/report", r.report([]any{out["id"]}, 0), 200)
		var reserved, released int
		f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation')='RESERVE'", f.project, "qualification-dispatch/"+Str(r.run, "id")).Scan(&reserved)
		f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.provider_request_id')=? AND json_extract(body,'$.operation')='RELEASE'", f.project, "qualification-dispatch/"+Str(r.run, "id")).Scan(&released)
		if reserved != 1 || released != 1 {
			t.Fatalf("qualification reservation not released: reserve=%d release=%d", reserved, released)
		}
	})
}
