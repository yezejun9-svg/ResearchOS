"""Append the W04-02 change phase to the construction check.

Heredocs with apostrophes are unreliable on this console, so the Go source goes through a file.
"""
import io

HANDOFF = '''// w0402Ctx hands the objects the context phase produced to the change phase. The program is
// single-threaded, so one package-level handoff is honest and keeps the two phases readable.
type w0402Handles struct {
	token, project, base, taskID string
	art, bundle, task, state     domain.Object
	contract                     domain.Object
}

var w0402Ctx w0402Handles

// contextPhase covers card steps 1 and 2.'''

STORE = '''	w0402Ctx = w0402Handles{token: token, project: project, base: base, taskID: domain.Str(task, "id"),
		art: art, bundle: bundle, task: task, state: state, contract: contract}

	skip("CTX-STEP-4-BLOCK-DEGRADE-UNRELATED"'''

PHASE = r'''
// changePhase covers card step 3 and the reachable half of step 4: a change record must name what it
// affects, a proposal built on an input that has moved must be refused, and a conflict must keep both
// drafts instead of silently promoting the newer one.
func (h *harness) changePhase(ctx context.Context) {
	if w0402Ctx.task == nil {
		ok("CHG-CONTEXT-PHASE-RAN-FIRST", false, "the change phase needs the bundle, task and artifact from contextPhase")
		return
	}
	ok("CHG-CONTEXT-PHASE-RAN-FIRST", true)
	token, base := w0402Ctx.token, w0402Ctx.base

	// freezing a context records deterministic dependency links, not just a bundle row
	links := h.countKind(ctx, "ImpactLink")
	code, listed, body := h.api(ctx, token, "GET", base+"/impact-links?limit=50", "", "", nil)
	items := domain.Arr(listed, "items")
	if len(items) == 0 {
		items = domain.Arr(listed, "objects")
	}
	shaped := 0
	for _, raw := range items {
		m, _ := raw.(map[string]any)
		l := domain.Object(m)
		if m != nil && l["from_ref"] != nil && l["to_ref"] != nil && Str2(l, "relation") != "" &&
			Str2(l, "basis") != "" && Str2(l, "status") == "ACTIVE" {
			shaped++
		}
	}
	ok("CHG-IMPACT-LINKS-ARE-EXPLICIT", code == 200 && links > 0 && len(items) > 0 && shaped == len(items),
		code, links, shaped, len(items), body[:min(len(body), 160)])
	ok("CHG-IMPACT-LINK-BASIS-IS-DETERMINISTIC",
		strings.Contains(string(domain.Bytes(listed)), `"basis":"DETERMINISTIC"`),
		string(domain.Bytes(listed))[:min(len(string(domain.Bytes(listed))), 160)])

	_, state, _ := h.liveState(ctx, token, base)
	stateID := Str2(state, "id")
	stateRev := int64(0)
	if v, _ := state["revision"].(float64); v > 0 {
		stateRev = int64(v)
	}
	proposal := func(baseRev any, targetRev int64) (int, domain.Object, string) {
		return h.api(ctx, token, "POST", base+"/change-proposals", domain.ID(), tagOf(state), domain.Object{
			"title": "w0402 change", "reason": "carry the frozen decision forward",
			"base_state_revision": baseRev,
			"edits": []any{domain.Object{"target_ref": domain.Object{"entity_type": "ProjectState",
				"id": stateID, "revision": targetRev, "content_hash": nil},
				"field": "current_decision_refs",
				"proposed_value_artifact_ref": domain.Ref(w0402Ctx.art, "Artifact"),
				"reason": "fixture edit"}},
			"migration_steps": domain.Empty(), "test_check_ids": []any{"w0402-check"},
			"rollback_steps": []any{"submit an independently accepted reversal"}})
	}
	code, proposalA, body := proposal(stateRev, stateRev)
	ok("CHG-PROPOSAL-CREATED", code == 201, code, body)
	if code != 201 {
		return
	}
	ok("CHG-PROPOSAL-RECORDS-BASE-STATE", proposalA["base_state_revision"] != nil &&
		Str2(proposalA, "status") == "DRAFT", Str2(proposalA, "status"))

	// a proposal built on a state that has moved is refused, and so is an edit whose own target
	// reference is older than what the project now holds
	code, _, body = proposal(99999, stateRev)
	ok("CHG-STALE-BASE-STATE-REJECTED", code == 412 && strings.Contains(body, "STALE_REVISION"), code, body)
	code, _, body = proposal(stateRev, 1)
	ok("CHG-STALE-EDIT-TARGET-REJECTED", code == 412 && strings.Contains(body, "STALE_INPUT"), code, body)

	// two drafts over the same field, then a conflict naming both: neither draft may move
	code, proposalB, body := proposal(stateRev, stateRev)
	ok("CHG-SECOND-PROPOSAL-CREATED", code == 201, code, body)
	if code == 201 {
		beforeA := string(domain.Bytes(proposalA))
		beforeB := string(domain.Bytes(proposalB))
		code, conflict, body := h.api(ctx, token, "POST", base+"/conflicts", domain.ID(), tagOf(state),
			domain.Object{"status": "OPEN", "kind": "REVISION",
				"subject_refs": []any{domain.Ref(proposalA, "ChangeProposal"),
					domain.Ref(proposalB, "ChangeProposal")},
				"description": "two drafts edit the same field", "blocks_refs": domain.Empty(),
				"resolution_proposal_id": nil, "resolution_reason": nil})
		ok("CHG-CONFLICT-KEEPS-BOTH-SIDES", code == 201 &&
			len(domain.Arr(conflict, "subject_refs")) == 2 && Str2(conflict, "status") == "OPEN", code, body)
		_, aAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
		_, bAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
		ok("CHG-CONFLICT-DOES-NOT-OVERWRITE-A-DRAFT",
			string(domain.Bytes(aAfter)) == beforeA && string(domain.Bytes(bAfter)) == beforeB,
			Str2(proposalA, "id"), Str2(proposalB, "id"))
	}

	// a task with no frozen context cannot be handed work, and none of the activity above
	// invalidated an unrelated task
	goalID := Str2(w0402Ctx.task, "goal_id")
	code, bare, body := h.api(ctx, token, "POST", base+"/tasks", domain.ID(), tagOf(w0402Ctx.state), domain.Object{
		"goal_id": goalID, "title": "w0402 unbundled task", "task_type": "construction",
		"stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": domain.Empty(),
		"input_refs": domain.Empty(), "acceptance_contract": w0402Ctx.contract,
		"origin_problem_id": "p-w0402", "candidate_id": "c-w0402",
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}})
	ok("CHG-SECOND-TASK-WAITING", code == 201 && bare["context_bundle_id"] == nil, code, body)
	if code == 201 {
		_, stateNow, _ := h.liveState(ctx, token, base)
		code, _, body = h.api(ctx, token, "POST", base+"/agent-messages", domain.ID(), tagOf(stateNow),
			domain.Object{"task_id": Str2(bare, "id"), "run_id": nil, "correlation_id": domain.ID(),
				"sender_id": "w0402-planner", "recipient_id": "w0402-planner",
				"message_type": "HANDOFF", "body": "hand work to a task that has no frozen context",
				"refs": domain.Empty(), "dedup_key": domain.Digest([]byte("w0402-handoff"))})
		ok("CHG-MISSING-REQUIRED-CONTEXT-BLOCKS", code == 422 && strings.Contains(body, "GATE_FAILED"), code, body)
	}
	staleTasks := h.countStaleTasks(ctx)
	ok("CHG-UNRELATED-ACTIVITY-INVALIDATES-NOTHING", staleTasks == 0, staleTasks)
	skip("CHG-OPTIONAL-RETRIEVAL-DEGRADES", "the optional-retrieval warning path needs the FTS/retrieval fixture "+
		"(retrieval.go pushes warnings and continues); no assertion here yet")
	skip("CHG-CHANGE-DOES-INVALIDATE-TARGETS", "the positive control - that an APPLIED change really moves its "+
		"impacted tasks to NEEDS_REVALIDATION - needs an accepted change with an independent verifier; without it "+
		"the blocking assertion above could be vacuous")
}
'''

PATCH = "tests/context/check/w0402.go"
s = io.open(PATCH, encoding="utf-8", newline="").read()
old_head = "// contextPhase covers card steps 1 and 2."
if s.count(old_head) != 1:
    raise SystemExit("handoff anchor missing")
s = s.replace(old_head, HANDOFF, 1)
old_skip = '\tskip("CTX-STEP-4-BLOCK-DEGRADE-UNRELATED"'
if s.count(old_skip) != 1:
    raise SystemExit("store anchor missing")
s = s.replace(old_skip, STORE, 1)
s = s.rstrip("\n") + "\n" + PHASE
io.open(PATCH, "w", encoding="utf-8", newline="").write(s)

MAIN = "tests/context/check/main.go"
m = io.open(MAIN, encoding="utf-8", newline="").read()
if "\th.changePhase(ctx)" not in m:
    m = m.replace("\th.contextPhase(ctx)\n", "\th.contextPhase(ctx)\n\th.changePhase(ctx)\n", 1)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(m)

HELPERS = '''
// countKind counts stored objects of one kind, and countStaleTasks counts tasks the domain has
// marked for revalidation. Both read the store the service wrote, not a value the test kept.
func (h *harness) countKind(ctx context.Context, kind string) int {
	var n int
	if err := h.db.QueryRowContext(ctx,
		`SELECT count(*) FROM domain_objects WHERE project=? AND kind=?`, h.alphaProj, kind).Scan(&n); err != nil {
		return -1
	}
	return n
}

func (h *harness) countStaleTasks(ctx context.Context) int {
	var n int
	if err := h.db.QueryRowContext(ctx, `SELECT count(*) FROM domain_objects WHERE project=?
		AND kind='Task' AND json_extract(body,'$.status')='NEEDS_REVALIDATION'`, h.alphaProj).Scan(&n); err != nil {
		return -1
	}
	return n
}
'''
# the context phase's skip was written before the change phase existed; narrow it to what is still open
narrow_old = s[s.find('	skip("CTX-STEP-4-BLOCK-DEGRADE-UNRELATED"'):0] if False else None
s = s.replace("""		"entry points are known (taskContext gate 422 GATE_FAILED, retrieval warnings list, ConsumeEvent touches "+
		"only context_projection while staleness comes from applyChange) but are not asserted yet")""",
 """		"entry points are known (taskContext gate 422 GATE_FAILED, retrieval warnings list, ConsumeEvent touches "+
		"only context_projection while staleness comes from applyChange) but are not asserted yet")""",1)
if "func (h *harness) countStaleTasks" not in s:
    io.open(PATCH, "a", encoding="utf-8", newline="").write(HELPERS)
print("change phase appended")
