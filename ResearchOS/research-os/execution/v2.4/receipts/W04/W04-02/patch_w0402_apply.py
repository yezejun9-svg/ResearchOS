"""Try the independent acceptance and apply leg inside the W04-02 construction check.

The card's step 4 needs a real control, not just an absence: staleness has to be shown to come from
an APPLIED change so that "nothing else invalidated anything" means something. Whether this leg is
reachable here at all - without the W06 orchestration fixture - is exactly what this probe answers,
so the assertions are written to fail loudly if the chain does not hold rather than to soften.
"""
import io

P = "tests/context/check/w0402.go"
s = io.open(P, encoding="utf-8", newline="").read()

BLOCK = r'''
	// independent acceptance and apply: the deterministic checks are recomputed by the service, the
	// author is refused, and only an applied change is allowed to make a task stale. This is the
	// control that turns "unrelated activity invalidated nothing" into a claim with teeth.
	authorToken := token
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-verifier",
		Roles: []string{"VERIFIER"}, Grants: []domain.Grant{{ProjectID: w0402Ctx.project}}}); e != nil {
		ok("CHG-VERIFIER-PROVISIONED", false, errText(e))
		return
	}
	ok("CHG-VERIFIER-PROVISIONED", true)
	verifierToken, verr := h.svc.IssueCredential(ctx, "w0402-verifier", 5*time.Minute)
	ok("CHG-VERIFIER-CREDENTIAL", verr == nil && verifierToken != "", errText(verr))

	frozen, cherr := h.svc.ChangeContractHash(ctx, w0402Ctx.project, Str2(proposalA, "id"))
	ok("CHG-CONTRACT-HASH-FREEZABLE", cherr == nil && frozen != "", errText(cherr))
	acceptBody := func() domain.Object {
		_, st, _ := h.liveState(ctx, token, base)
		return domain.Object{"subject_ref": domain.Ref(proposalA, "ChangeProposal"), "run_id": nil,
			"contract_hash": frozen, "input_refs": []any{domain.Ref(proposalA, "ChangeProposal")},
			"artifact_refs": domain.Empty(),
			"checks": []any{domain.Object{"check_id": "client-not-authoritative", "status": "NOT_RUN",
				"evidence_refs": domain.Empty(), "command_key": nil, "actual": "server must recompute",
				"exit_code": nil, "started_at": nil, "finished_at": nil}},
			"verdict": "BLOCKED", "executor_principal_ids": domain.Empty(),
			"independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(),
			"qualification_ids": domain.Empty(), "policy_revision": st["policy_revision"],
			"measurement_mode": "FIXTURE", "reason": "request server independent verification"}
	}
	// the author cannot accept its own change, whatever else happens
	_, stateNow, _ := h.liveState(ctx, token, base)
	code, _, body = h.api(ctx, authorToken, "POST", base+"/acceptances", domain.ID(), tagOf(stateNow), acceptBody())
	ok("CHG-AUTHOR-CANNOT-ACCEPT-OWN-CHANGE", code == 403, code, body[:min(len(body), 160)])

	_, verifierState, _ := h.api(ctx, verifierToken, "GET", base+"/state", "", "", nil)
	code, receipt, body := h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
		tagOf(verifierState), acceptBody())
	ok("CHG-INDEPENDENT-ACCEPTANCE-COMPUTED", code == 201 && Str2(receipt, "verdict") == "PASS",
		code, Str2(receipt, "verdict"), body[:min(len(body), 200)])
	if code != 201 || Str2(receipt, "verdict") != "PASS" {
		return
	}

	// the task that will be touched by the change, plus a control that must stay untouched
	downstreamID := Str2(bare, "id")
	_, appliedState, _ := h.liveState(ctx, token, base)
	code, applied, body := h.api(ctx, token, "POST",
		base+"/change-proposals/"+Str2(proposalA, "id")+"/apply", domain.ID(), tagOf(proposalA),
		domain.Object{"acceptance_id": receipt["id"], "expected_project_state_revision": appliedState["revision"]})
	ok("CHG-APPLIED-CHANGE-STATES-ADVANCE", code == 200 && Str2(applied, "status") == "APPLIED" &&
		applied["applied_state_revision"] != nil, code, Str2(applied, "status"), body[:min(len(body), 200)])

	_, movedState, _ := h.liveState(ctx, token, base)
	ok("CHG-APPLY-MOVES-THE-PROJECT-STATE", movedState["revision"] != appliedState["revision"],
		appliedState["revision"], movedState["revision"])
	staled := h.countStaleTasks(ctx)
	ok("CHG-APPLY-MAKES-NO-TASK-STALE-WITHOUT-IMPACT", staled == 0, staled)

	// and now the half of step 1 that was previously unassertable: a freeze taken after an applied
	// decision carries the effective decision and keeps the retired one as history
	code, refrozen, body := h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(), tagOf(movedState),
		domain.Object{"task_id": w0402Ctx.taskID, "expected_project_state_revision": movedState["revision"]})
	ok("CHG-REFREEZE-AFTER-APPLY-ACCEPTED", code == 201, code, body[:min(len(body), 160)])
	if code == 201 {
		listed := string(domain.Bytes(domain.Arr(refrozen, "latest_decision_refs")))
		summary := Str2(refrozen, "summary")
		ok("CHG-REFREEZE-CARRIES-EFFECTIVE-DECISION",
			strings.Contains(listed, Str2(w0402Ctx.decisions[0], "id")) ||
				strings.Contains(summary, Str2(w0402Ctx.decisions[0], "id")), listed, summary[:min(len(summary), 200)])
	}
'''

anchor = '''	skip("CHG-OPTIONAL-RETRIEVAL-DEGRADES",'''
if s.count(anchor) != 1:
    raise SystemExit("anchor missing")
s = s.replace(anchor, BLOCK.rstrip("\n") + "\n\n" + anchor, 1)

# the two skips this leg replaces are dropped only if the leg actually runs; keep them honest for now
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("acceptance/apply leg added")
