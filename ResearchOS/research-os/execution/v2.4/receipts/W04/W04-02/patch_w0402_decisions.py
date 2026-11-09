"""Teach the W04-02 change phase to record real decisions first.

The domain refuses a proposal over current_decision_refs unless the proposed value names
DecisionReceipt refs, and a decision needs a rubric artifact and an accepted requirement. Building
that chain is also how the card's first step gets its deprecation half: with two decisions in one
lineage the frozen bundle must carry the current one and keep the superseded one as history, which
is the "effective and deprecated decisions" the card asks for.
"""
import io

P = "tests/context/check/w0402.go"
s = io.open(P, encoding="utf-8", newline="").read()

# 1. a rubric artifact, then two decisions in one lineage, recorded before the freeze
anchor = '''	// a real input file, so the worker manifest has bytes to deliver and hashes to check'''
inject = '''	// a rubric artifact gives the decisions something pinned to point at
	rubric := []byte(`{"rubric":"w0402 deterministic fixture"}`)
	state, _ = h.liveState(ctx, token, base)
	code, rubricUpload, body := h.api(ctx, token, "POST", base+"/content", domain.ID(), "", rubric)
	ok("CTX-RUBRIC-CONTENT-UPLOADED", code == 201, code, body)
	if code != 201 {
		return
	}
	code, rubricArt, body := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(), tagOf(state), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": rubricUpload["content_hash"], "storage_key": rubricUpload["storage_key"],
		"media_type": "application/json", "byte_size": len(rubric),
		"input_refs": domain.Empty(), "source_refs": domain.Empty(),
		"produced_by": "w0402-planner", "access_class": "PROJECT"})
	ok("CTX-RUBRIC-ARTIFACT-SEALED", code == 201, code, body)
	if code != 201 {
		return
	}

	// two decisions in one lineage: the second supersedes the first, so the freeze has to carry both
	// roles - the current one as a decision reference, the older one as history
	reqRef := domain.Ref(accepted, "Requirement")
	recordDecision := func(selected string, supersedes any, key string) (int, domain.Object, string) {
		_, st, _ := h.liveState(ctx, token, base)
		return h.api(ctx, token, "POST", base+"/decisions", key, tagOf(st), domain.Object{
			"subject_ref": reqRef, "input_refs": []any{reqRef}, "input_hash": domain.Digest([]byte(key)),
			"scope": domain.Object{"task_type": "construction", "language": "en",
				"provider": "deterministic-fixture", "model_revision": "none", "rubric_revision": "1"},
			"mode": "ADVISORY", "qualification_id": nil,
			"rubric_ref": domain.Ref(rubricArt, "Artifact"), "options": []any{"A", "B"},
			"selected": selected, "status": "DECIDED", "signals": domain.Empty(),
			"deterministic_results": domain.Empty(),
			"evidence_refs": []any{domain.Ref(rubricArt, "Artifact")},
			"rationale": "explicit deterministic fixture decision", "missing_evidence": domain.Empty(),
			"revocation_conditions": []any{"input changes"}, "supersedes_id": supersedes})
	}
	code, decisionA, body := recordDecision("A", nil, "w0402-decision-a")
	ok("CTX-DECISION-RECORDED", code == 201, code, body)
	var decisionB domain.Object
	if code == 201 {
		code, decisionB, body = recordDecision("B", Str2(decisionA, "id"), "w0402-decision-b")
		ok("CTX-SUPERSEDING-DECISION-RECORDED", code == 201, code, body)
	}

'''
if s.count(anchor) != 1:
    raise SystemExit("inject anchor not unique")
s = s.replace(anchor, inject + anchor, 1)

# 2. the proposed value names DecisionReceipt refs, which is what the field's schema demands
s = s.replace('''	evidence := []byte(fmt.Sprintf(`[{"entity_type":"ProjectState","id":%q,"revision":%v,"content_hash":null}]`, Str2(state, "id"), state["revision"]))''',
'''	proposedRefs := []any{domain.Ref(decisionA, "DecisionReceipt")}
	if Str2(decisionB, "id") != "" {
		proposedRefs = []any{domain.Ref(decisionB, "DecisionReceipt")}
	}
	evidence := domain.Bytes(domain.Object{"value": proposedRefs})["value"]
	evidence = append([]byte(nil), evidence...)''')
s = s.replace('''	evidence := domain.Bytes(domain.Object{"value": proposedRefs})["value"]
	evidence = append([]byte(nil), evidence...)''',
'''	rawProposed, marshalErr := json.Marshal(proposedRefs)
	if marshalErr != nil {
		ok("CTX-PROPOSAL-VALUE-ENCODABLE", false, errText(marshalErr))
		return
	}
	ok("CTX-PROPOSAL-VALUE-ENCODABLE", true)
	evidence := rawProposed''')
s = s.replace('''		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": len(evidence),''',
'''		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": len(evidence),''')

# 3. the freeze must show which decision is current and keep the retired one as history
s = s.replace('''	ok("CTX-BUNDLE-KEEPS-USER-WORDS-VERBATIM", strings.Contains(bundleJSON, userWords),
		bundleJSON[:min(len(bundleJSON), 500)])''',
'''	ok("CTX-BUNDLE-KEEPS-USER-WORDS-VERBATIM", strings.Contains(bundleJSON, userWords),
		bundleJSON[:min(len(bundleJSON), 500)])
	if Str2(decisionB, "id") != "" {
		ok("CTX-BUNDLE-CARRIES-CURRENT-DECISION", strings.Contains(
			string(domain.Bytes(domain.Arr(bundle, "latest_decision_refs"))), Str2(decisionB, "id")),
			domain.Arr(bundle, "latest_decision_refs"))
		ok("CTX-BUNDLE-KEEPS-RETIRED-DECISION-AS-HISTORY",
			strings.Contains(Str2(bundle, "summary"), Str2(decisionA, "id")) &&
				strings.Contains(Str2(bundle, "summary"), "historical"), Str2(bundle, "summary")[:240])
	}''')

# 4. hand the decisions to the change phase
s = s.replace('''		art: art, bundle: bundle, task: task, state: state, contract: contract}''',
'''		art: art, bundle: bundle, task: task, state: state, contract: contract,
		decisions: proposedRefs}''')
s = s.replace('''	art, bundle, task, state     domain.Object
	contract                     domain.Object
}''','''	art, bundle, task, state     domain.Object
	contract                     domain.Object
	decisions                    []any
}''')
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("decisions wired into the W04-02 phases")
