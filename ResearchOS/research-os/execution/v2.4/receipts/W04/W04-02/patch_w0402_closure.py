"""Close W04-02 step 4's positive control: a change to a dependency really does stale its task.

The freeze already writes Task -> Requirement DEPENDS_ON links, so an accepted change that edits the
requirement this task references has a non-empty impact closure and must make exactly that task stale,
while a second task that references nothing stays as it was. Without this pair the "nothing unrelated
was invalidated" claim would be vacuous.
"""
import io

P = "tests/context/check/w0402.go"
s = io.open(P, encoding="utf-8", newline="").read()

# 1. hand the accepted requirement's id to the change phase
s = s.replace('''	art, bundle, task, state     domain.Object
	contract                     domain.Object
	decisions                    []any
	goalID                       string''',
'''	art, bundle, task, state     domain.Object
	contract                     domain.Object
	decisions                    []any
	goalID, reqID                string''')
s = s.replace('''		decisions: proposedRefs, goalID: Str2(goal, "id")}''',
              '''		decisions: proposedRefs, goalID: Str2(goal, "id"), reqID: Str2(accepted, "id")}''')

# 2. one reusable draft-accept-apply pipeline
HELPER = '''	// applyChange runs a draft all the way through - proposal, independent acceptance by the
	// verifier, apply - and hands back the applied record so each caller asserts its own property.
	applyChange := func(targetRef domain.Object, field string, valueArt domain.Object, title string) (domain.Object, string) {
		st, tg := h.liveState(ctx, token, base)
		code, prop, body := h.api(ctx, token, "POST", base+"/change-proposals", domain.ID(), tg, domain.Object{
			"title": title, "reason": "fixture change with a real dependency closure",
			"base_state_revision": st["revision"],
			"edits": []any{domain.Object{"target_ref": targetRef, "field": field,
				"proposed_value_artifact_ref": domain.Ref(valueArt, "Artifact"),
				"reason": "explicit fixture edit"}},
			"migration_steps": domain.Empty(), "test_check_ids": supportedChangeChecks,
			"rollback_steps": []any{"submit an independently accepted reversal"}})
		if code != 201 {
			return nil, "proposal refused " + body
		}
		hash, herr := h.svc.ChangeContractHash(ctx, w0402Ctx.project, Str2(prop, "id"))
		if herr != nil {
			return nil, "contract hash unavailable " + errText(herr)
		}
		code, receipt, body := h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
			tagOf(prop), acceptBody(prop, hash))
		if code != 201 || Str2(receipt, "verdict") != "PASS" {
			return nil, "acceptance " + Str2(receipt, "verdict") + " " + body
		}
		beforeApply, _ := h.liveState(ctx, token, base)
		code, applied, body := h.api(ctx, token, "POST",
			base+"/change-proposals/"+Str2(prop, "id")+"/apply", domain.ID(), tagOf(prop),
			domain.Object{"acceptance_id": receipt["id"],
				"expected_project_state_revision": beforeApply["revision"]})
		if code != 200 {
			return nil, "apply refused " + body
		}
		return applied, ""
	}

'''
anchor = "\t// two drafts over the same field, then a conflict naming both: neither draft may move"
if s.count(anchor) != 1:
    raise SystemExit("helper anchor missing")
s = s.replace(anchor, HELPER + anchor, 1)

# 3. replace the two weak step-4 lines with the real control pair
start = s.index("\t// this change's closure is the project state and its policies")
end = s.index("\tskip(\"CHG-OPTIONAL-RETRIEVAL-DEGRADES\"")
new = '''	// the positive control. The freeze wrote Task -> Requirement DEPENDS_ON links, so an accepted
	// change to that requirement has this task in its closure and must make exactly it stale, while
	// a task that depends on nothing stays as it was.
	textRef, textArt, textBody := h.api(ctx, token, "POST", base+"/content", domain.ID(),
		func() string { st, tg := h.liveState(ctx, token, base); _ = st; return tg }(),
		[]byte(`"revised by an independently accepted change"`))
	ok("CHG-REVISION-CONTENT-UPLOADED", textRef == 201, textRef, textBody[:min(len(textBody), 160)])
	_, reqNow, _ := h.api(ctx, token, "GET", base+"/requirements/"+w0402Ctx.reqID, "", "", nil)
	st, tg := h.liveState(ctx, token, base)
	_ = st
	code, revisionArt, body := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(), tg, domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": textArt["content_hash"], "storage_key": textArt["storage_key"],
		"media_type": "application/json", "byte_size": 42, "input_refs": domain.Empty(),
		"source_refs": domain.Empty(), "produced_by": "w0402-planner", "access_class": "PROJECT"})
	ok("CHG-REVISION-ARTIFACT-SEALED", code == 201, code, body[:min(len(body), 200)])
	applied2, why := applyChange(domain.Ref(reqNow, "Requirement"), "text", revisionArt,
		"w0402 requirement revision")
	ok("CHG-REQUIREMENT-CHANGE-APPLIED", applied2 != nil && Str2(applied2, "status") == "APPLIED", why)
	_, frozenTask, _ := h.api(ctx, token, "GET", base+"/tasks/"+w0402Ctx.taskID, "", "", nil)
	_, laterTask, _ := h.api(ctx, token, "GET", base+"/tasks/"+Str2(bare, "id"), "", "", nil)
	ok("CHG-APPLIED-CHANGE-STALES-THE-DEPENDENT-TASK",
		Str2(frozenTask, "status") == "NEEDS_REVALIDATION", Str2(frozenTask, "status"))
	ok("CHG-APPLIED-CHANGE-LEAVES-THE-UNRELATED-TASK-ALONE",
		Str2(laterTask, "status") == "DRAFT", Str2(laterTask, "status"))
'''
s = s[:start] + new + s[end:]
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("positive control added")
