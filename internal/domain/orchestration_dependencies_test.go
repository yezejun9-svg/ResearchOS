package domain

import (
	"context"
	"path/filepath"
	"testing"
)

func dependencyFixtureTask(o *orchestrationFixture, title string, deps, inputs []any, expected string) Object {
	f := o.f
	f.token = o.owner
	g := f.read("goals", Str(o.goal, "id"))
	contract := orchestrationContract()
	Arr(contract, "checks")[0].(map[string]any)["expected"] = expected
	contract["contract_hash"] = contractDigest(contract)
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(g), Object{"goal_id": g["id"], "title": title, "task_type": "dependency-fixture", "stage": "verification", "dependency_task_ids": deps, "requirement_refs": []any{Ref(o.req, "Requirement")}, "input_refs": inputs, "acceptance_contract": contract, "origin_problem_id": "orchestration-problem", "candidate_id": title, "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	return f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "freeze actual dependency fixture"})
}

func TestW06DependenciesInvalidated(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	rubric := f.artifact(Object{"rubric": "explicit decision lineage"}, Empty())
	d1 := f.decision(o.req, rubric, nil, "A")
	f.apply(f.proposal([]any{Ref(d1, "DecisionReceipt")}))
	o.owner = f.token
	a := dependencyFixtureTask(o, "dependency-A", Empty(), []any{Ref(d1, "DecisionReceipt")}, `{"result":"A verified"}`)
	b := dependencyFixtureTask(o, "dependency-B", []any{a["id"]}, Empty(), `{"result":"B derived from A"}`)
	ar := o.claim(a)
	artifactA := o.report(ar, []byte(`{"result":"A verified"}`))
	requestA := o.acceptance(ar, artifactA)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(ar.task), requestA)
	f.token = o.owner
	b = f.read("tasks", Str(b, "id"))
	// B's old bundle was made before A became accepted and cannot be dispatched.
	claimBody := Object{"runtime_id": o.rt["id"], "executor_principal_id": f.owner, "context_bundle_id": b["context_bundle_id"]}
	status, reply, _ := f.request("POST", f.path("/tasks/"+Str(b, "id")+"/claim"), ID(), testTag(b), claimBody)
	orchestrationAssert(t, "W06-G01-DEPENDENCY-CONTEXT", 412, status, reply)
	f.bundle(b)
	b = f.read("tasks", Str(b, "id"))
	br := o.claim(b)
	artifactB := o.report(br, []byte(`{"result":"B derived from A"}`))
	requestB := o.acceptance(br, artifactB)
	// Frozen dependency refs are distinct from B's intentionally empty direct input_refs.
	var snapshot string
	if e := f.db.QueryRow("SELECT snapshot FROM orchestration_run_dependencies WHERE project=? AND run=?", f.project, br.run["id"]).Scan(&snapshot); e != nil {
		t.Fatal(e)
	}
	frozen, _ := Decode([]byte(snapshot))
	orchestrationAssert(t, "W06-G01-DEPENDENCY-FROZEN", []any{0, 3}, []any{len(Arr(br.task, "input_refs")), len(Arr(frozen, "refs"))}, frozen)
	f.token = o.owner
	acceptedA := f.read("tasks", Str(a, "id"))
	f.bundle(acceptedA)
	// A remains ACCEPTED but has a new version. Exercise the same dependency
	// validator used in the final transaction, independently of B's status gate.
	tx, e := f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	ready, readyErr := f.s.dependenciesReady(tx, f.project, br.task)
	_, changedErr := f.s.runDependenciesCurrent(tx, f.project, br.task, br.run)
	tx.Rollback()
	changedStatus := 0
	if fault, ok := changedErr.(*Fault); ok {
		changedStatus = fault.Status
	}
	orchestrationAssert(t, "W06-G01-DEPENDENCY-VERSION-NOT-STATUS", []any{true, true, 412}, []any{ready, readyErr == nil, changedStatus}, Object{"basis": "current accepted dependency has a new Task revision; complete ABA HTTP awaits canonical artifact reuse", "original_frozen_refs": frozen})
	d2 := f.decision(o.req, rubric, d1["id"], "B")
	f.apply(f.proposal([]any{Ref(d2, "DecisionReceipt")}))
	o.owner = f.token
	currentA := f.read("tasks", Str(a, "id"))
	currentB := f.read("tasks", Str(b, "id"))
	requestB["subject_ref"] = Ref(currentB, "Task")
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(currentB), requestB)
	orchestrationAssert(t, "W06-G01-DEPENDENCY-INVALIDATED", []any{"NEEDS_REVALIDATION", "NEEDS_REVALIDATION", 409}, []any{currentA["status"], currentB["status"], status}, Object{"rejection": reply, "previous_run": Ref(br.run, "Run"), "frozen_dependencies": frozen, "D1": Ref(d1, "DecisionReceipt"), "D2": Ref(d2, "DecisionReceipt")})

	f.token = o.owner
	currentA = f.expect(200, "POST", f.path("/tasks/"+Str(a, "id")+"/actions"), ID(), testTag(currentA), Object{"action": "REVALIDATE", "reason": "same bytes independently re-proven under D2"})
	f.bundle(currentA)
	currentA = f.read("tasks", Str(a, "id"))
	currentA = f.expect(200, "POST", f.path("/tasks/"+Str(a, "id")+"/actions"), ID(), testTag(currentA), Object{"action": "SUBMIT", "reason": "current D2 context"})
	var oldProgressRaw, newProgressRaw string
	f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='NoProgressRecord' AND id=?", a["no_progress_record_id"]).Scan(&oldProgressRaw)
	f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='NoProgressRecord' AND id=?", currentA["no_progress_record_id"]).Scan(&newProgressRaw)
	oldProgress, _ := Decode([]byte(oldProgressRaw))
	newProgress, _ := Decode([]byte(newProgressRaw))
	orchestrationAssert(t, "W06-G01-REVALIDATED-ORIGIN", []any{true, true, true}, []any{oldProgress["id"] != newProgress["id"], oldProgress["candidate_id"] == newProgress["candidate_id"], newProgress["input_hash"] == Hash(currentA["input_refs"])}, Object{"old": oldProgress, "new": newProgress})
	ar2 := o.claim(currentA)
	artifactA2 := o.report(ar2, []byte(`{"result":"A verified"}`))
	requestA2 := o.acceptance(ar2, artifactA2)
	receiptA2 := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(ar2.task), requestA2)
	f.token = o.owner
	currentA = f.read("tasks", Str(a, "id"))
	currentB = f.read("tasks", Str(b, "id"))
	requestB["subject_ref"] = Ref(currentB, "Task")
	f.switchPrincipal("orchestration-independent-verifier", []string{"VERIFIER"})
	status, reply, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(currentB), requestB)
	orchestrationAssert(t, "W06-G01-DEPENDENCY-ABA", []any{"ACCEPTED", true, "STALE", true, 409}, []any{currentA["status"], artifactA2["id"] == artifactA["id"], artifactA2["validity"], receiptA2["run_id"] != requestA["run_id"], status}, Object{"old_downstream_rejection": reply, "canonical": artifactA2, "new_acceptance": receiptA2})
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	genericErr := f.s.effective(tx, f.project, Ref(artifactA2, "Artifact"))
	_, oldUseErr := f.s.dependencyProofRefs(tx, f.project, Object{"run_id": ar.run["id"], "artifact_refs": []any{Ref(artifactA2, "Artifact")}})
	_, frozenErr := f.s.runDependenciesCurrent(tx, f.project, currentB, br.run)
	tx.Rollback()
	orchestrationAssert(t, "W06-USES-HISTORY-NOT-REVIVED", []any{true, true, true}, []any{genericErr != nil, oldUseErr != nil, frozenErr != nil}, Object{"generic_error": genericErr.Error(), "old_use_error": oldUseErr.Error(), "old_run_dependency_error": frozenErr.Error()})
	f.token = o.owner
	currentB = f.expect(200, "POST", f.path("/tasks/"+Str(b, "id")+"/actions"), ID(), testTag(currentB), Object{"action": "REVALIDATE", "reason": "new dependency acceptance"})
	f.bundle(currentB)
	currentB = f.read("tasks", Str(b, "id"))
	currentB = f.expect(200, "POST", f.path("/tasks/"+Str(b, "id")+"/actions"), ID(), testTag(currentB), Object{"action": "SUBMIT", "reason": "freeze new dependency use"})
	br2 := o.claim(currentB)
	manifest, e := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(b, "id"), filepath.Join(t.TempDir(), "context"))
	if e != nil {
		t.Fatal(e)
	}
	proofPresent := false
	for _, v := range Arr(manifest, "input_manifest") {
		entry := v.(map[string]any)
		ref := entry["ref"].(map[string]any)
		if ref["id"] == artifactA2["id"] {
			proofPresent = entry["proof_ref"] != nil && entry["use_receipt_hash"] != nil && entry["canonical_validity"] == "STALE"
		}
	}
	artifactB2 := o.report(br2, []byte(`{"result":"B derived from A"}`))
	requestB2 := o.acceptance(br2, artifactB2)
	acceptedB2 := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(br2.task), requestB2)
	orchestrationAssert(t, "W06-USES-NEW-DEPENDENCY-CONTEXT", []any{true, "PASS"}, []any{proofPresent, acceptedB2["verdict"]}, Object{"materialized": manifest, "acceptance": acceptedB2})

	// A proof cannot become valid just because the canonical bytes still match.
	f.token = o.owner
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, newUse, e := f.s.artifactUse(tx, f.project, ar2.run, Str(artifactA2, "id"), true)
	if e != nil {
		t.Fatal(e)
	}
	proofRef, e := f.s.artifactUseProof(tx, f.project, ar2.run, artifactA2, newUse)
	if e != nil {
		t.Fatal(e)
	}
	proofObject, e := version(tx, f.project, proofRef)
	if e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec("DROP TRIGGER content_immutable"); e != nil {
		t.Fatal(e)
	}
	if _, e = tx.Exec("UPDATE uploaded_content SET bytes=? WHERE storage_key=?", []byte("tampered proof"), proofObject["storage_key"]); e != nil {
		t.Fatal(e)
	}
	_, _, tamperErr := f.s.artifactUse(tx, f.project, ar2.run, Str(artifactA2, "id"), true)
	tx.Rollback()
	orchestrationAssert(t, "W06-USES-PROOF-HASH", true, tamperErr != nil, Object{"reason": "manifest uploaded bytes changed inside rolled-back transaction"})
	d3 := f.decision(o.req, rubric, d2["id"], "A")
	f.apply(f.proposal([]any{Ref(d3, "DecisionReceipt")}))
	tx, e = f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	_, _, staleProofErr := f.s.artifactUse(tx, f.project, ar2.run, Str(artifactA2, "id"), true)
	source := Object{"kind": "SOURCE_SNAPSHOT", "access_class": "PROJECT", "validity": "STALE"}
	_, sourceErr := f.s.artifactUseProof(tx, f.project, ar2.run, source, newUse)
	revoked := Merge(Object{}, artifactA2)
	revoked["validity"] = "REVOKED"
	_, revokedErr := f.s.artifactUseProof(tx, f.project, ar2.run, revoked, newUse)
	tx.Rollback()
	_, contextErr := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(b, "id"))
	orchestrationAssert(t, "W06-USES-PROOF-INVALIDATION", []any{true, true, true, true}, []any{staleProofErr != nil, contextErr != nil, sourceErr != nil, revokedErr != nil}, Object{"decision": Ref(d3, "DecisionReceipt"), "proof_error": staleProofErr.Error(), "context_error": contextErr.Error(), "source_boundary": "SOURCE_SNAPSHOT never eligible", "revocation_boundary": "REVOKED never eligible"})
}
