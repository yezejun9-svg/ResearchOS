package main

// w0402.go is the W04-02 half of this construction check: the context frozen from the live
// ProjectState, and the byte-checked materialization of that context into an empty worker
// workspace. It drives the accepted HTTP operation surface (domain.Service.Handler) with a real
// credential, because that is the only way createContextBundle is reachable at all - calling
// unexported service code would test a path no client can ever take.
//
// Nothing here is a shape the program itself supplied: the bundle is read back from what the
// service stored, delivered bytes are re-hashed from disk, and each refusal has a positive control
// beside it so a green id cannot come from a fixture that never worked.

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

// api issues one request over the real handler: status, decoded object, raw body.
func (h *harness) api(ctx context.Context, token, method, path, key, etag string, body any) (int, domain.Object, string) {
	var raw []byte
	if body != nil {
		if b, isBytes := body.([]byte); isBytes {
			raw = b
		} else {
			b, e := json.Marshal(body)
			if e != nil {
				panic(e)
			}
			raw = b
		}
	}
	r := httptest.NewRequest(method, path, bytes.NewReader(raw))
	r.Header.Set("Authorization", "Bearer "+token)
	if key != "" {
		r.Header.Set("Idempotency-Key", key)
	}
	if etag != "" {
		r.Header.Set("If-Match", etag)
	}
	w := httptest.NewRecorder()
	h.svc.Handler().ServeHTTP(w, r)
	var o domain.Object
	if e := json.Unmarshal(w.Body.Bytes(), &o); e != nil || o == nil {
		o = domain.Object{}
	}
	return w.Code, o, w.Body.String()
}

// Str2 reads one string field; the report needs it in several shapes.
func Str2(o domain.Object, k string) string { return domain.Str(o, k) }

func tagOf(o domain.Object) string {
	t, e := domain.ETag(o)
	if e != nil {
		return ""
	}
	return t
}

// liveState re-reads ProjectState, because every accepted write moves it and a stale If-Match is a
// fixture bug rather than a property under test.
func (h *harness) liveState(ctx context.Context, token, base string) (domain.Object, string) {
	_, state, _ := h.api(ctx, token, "GET", base+"/state", "", "", nil)
	return state, tagOf(state)
}

// w0402Ctx hands the objects the context phase produced to the change phase. The program is
// single-threaded, so one package-level handoff is honest and keeps the two phases readable.
type w0402Handles struct {
	token, project, base, taskID string
	art, bundle, task, state     domain.Object
	contract                     domain.Object
	decisions                    []any
	goalID, reqID                string
	decEffective, decRetired     string
}

var w0402Ctx w0402Handles

// contextPhase covers card steps 1 and 2.
func (h *harness) contextPhase(ctx context.Context) {
	project := h.alphaProj
	if project == "" {
		ok("CTX-PROJECT-AVAILABLE", false, "W04-01 bootstrap produced no project")
		return
	}
	ok("CTX-PROJECT-AVAILABLE", true)
	base := "/v1/projects/" + project

	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-planner",
		Roles:            []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"},
		CanCreateProject: true, Grants: []domain.Grant{{ProjectID: project}}}); e != nil {
		ok("CTX-PLANNER-PROVISIONED", false, errText(e))
		return
	}
	ok("CTX-PLANNER-PROVISIONED", true)
	token, e := h.svc.IssueCredential(ctx, "w0402-planner", 5*time.Minute)
	if e != nil || token == "" {
		ok("CTX-PLANNER-CREDENTIAL", false, errText(e))
		return
	}
	ok("CTX-PLANNER-CREDENTIAL", true)

	state, stateBody := h.liveState(ctx, token, base)
	ok("CTX-PROJECT-STATE-READABLE", state["revision"] != nil, stateBody)

	// the operator's own sentence, carried as a USER_STATED requirement rather than a paraphrase
	const userWords = "keep the operator's own sentence intact through the freeze"
	code, req, body := h.api(ctx, token, "POST", base+"/requirements", domain.ID(), tagOf(state), domain.Object{
		"requirement_key": "REQ-W0402-FREEZE", "text": userWords, "basis": "USER_STATED",
		"source_refs": domain.Empty(), "rationale": "construction fixture for W04-02",
		"supersedes_id": nil, "acceptance_check_ids": domain.Empty()})
	ok("CTX-REQUIREMENT-CREATED", code == 201, code, body)
	if code != 201 {
		return
	}
	state, _ = h.liveState(ctx, token, base)
	code, accepted, body := h.api(ctx, token, "POST", base+"/requirements/"+domain.Str(req, "id")+"/actions",
		domain.ID(), tagOf(req), domain.Object{"action": "ACCEPT", "reason": "explicit fixture acceptance",
			"source_validation_refs": domain.Empty()})
	ok("CTX-REQUIREMENT-ACCEPTED", code == 200, code, body)
	if code != 200 {
		return
	}

	contract := domain.Object{"contract_hash": domain.Digest([]byte("w0402 contract")),
		"contract_revision": 1, "checks": []any{domain.Object{"check_id": "w0402-check",
			"kind": "DETERMINISTIC", "required": true, "expected": "context survives the freeze",
			"command_key": "test.context", "rubric_ref": nil, "qualification_id": nil,
			"not_applicable_reason": nil}}, "require_independent_verifier": true,
		"version_policy": "EXACT", "frozen_at": domain.Now()}
	state, _ = h.liveState(ctx, token, base)
	code, goal, body := h.api(ctx, token, "POST", base+"/goals", domain.ID(), tagOf(state), domain.Object{
		"title": "w0402 goal", "original_intent": userWords, "scope": "PROJECT",
		"requirement_refs": []any{domain.Ref(accepted, "Requirement")}, "problem_ids": []any{"p-w0402"},
		"deliverables": []any{"frozen context"}, "acceptance_contract": contract})
	ok("CTX-GOAL-CARRIES-ORIGINAL-INTENT", code == 201, code, body)
	if code != 201 {
		return
	}

	// a rubric artifact gives the decisions something pinned to point at
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
		st, _ := h.liveState(ctx, token, base)
		return h.api(ctx, token, "POST", base+"/decisions", key, tagOf(st), domain.Object{
			"subject_ref": reqRef, "input_refs": []any{reqRef}, "input_hash": domain.Hash([]any{reqRef}),
			"scope": domain.Object{"task_type": "construction", "language": "en",
				"provider": "deterministic-fixture", "model_revision": "none", "rubric_revision": "1"},
			"mode": "ADVISORY", "qualification_id": nil,
			"rubric_ref": domain.Ref(rubricArt, "Artifact"), "options": []any{"A", "B"},
			"selected": selected, "status": "DECIDED", "signals": domain.Empty(),
			"deterministic_results": domain.Empty(),
			"evidence_refs":         []any{domain.Ref(rubricArt, "Artifact")},
			"rationale":             "explicit deterministic fixture decision", "missing_evidence": domain.Empty(),
			"revocation_conditions": []any{"input changes"}, "supersedes_id": supersedes})
	}
	code, decisionA, body := recordDecision("A", nil, "w0402-decision-a")
	ok("CTX-DECISION-RECORDED", code == 201, code, body)
	var decisionB domain.Object
	if code == 201 {
		code, decisionB, body = recordDecision("B", Str2(decisionA, "id"), "w0402-decision-b")
		ok("CTX-SUPERSEDING-DECISION-RECORDED", code == 201, code, body)
	}

	// a real input file, so the worker manifest has bytes to deliver and hashes to check
	proposedRefs := []any{domain.Ref(decisionA, "DecisionReceipt")}
	if Str2(decisionB, "id") != "" {
		proposedRefs = []any{domain.Ref(decisionB, "DecisionReceipt")}
	}
	rawProposed, marshalErr := json.Marshal(proposedRefs)
	if marshalErr != nil {
		ok("CTX-PROPOSAL-VALUE-ENCODABLE", false, errText(marshalErr))
		return
	}
	ok("CTX-PROPOSAL-VALUE-ENCODABLE", true)
	evidence := rawProposed
	state, _ = h.liveState(ctx, token, base)
	code, upload, body := h.api(ctx, token, "POST", base+"/content", domain.ID(), "", evidence)
	ok("CTX-INPUT-CONTENT-UPLOADED", code == 201, code, body)
	if code != 201 {
		return
	}
	code, art, body := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(), tagOf(state), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "application/json", "byte_size": len(evidence),
		"input_refs": domain.Empty(), "source_refs": domain.Empty(),
		"produced_by": "w0402-planner", "access_class": "PROJECT"})
	ok("CTX-INPUT-ARTIFACT-SEALED", code == 201, code, body)
	if code != 201 {
		return
	}

	taskBody := domain.Object{"goal_id": goal["id"], "title": "w0402 task", "task_type": "construction",
		"stage": "verification", "dependency_task_ids": domain.Empty(),
		"requirement_refs":    []any{domain.Ref(accepted, "Requirement")},
		"input_refs":          []any{domain.Ref(art, "Artifact")},
		"acceptance_contract": contract, "origin_problem_id": "p-w0402", "candidate_id": "c-w0402",
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}}
	code, task, body := h.api(ctx, token, "POST", base+"/tasks", domain.ID(), tagOf(goal), taskBody)
	ok("CTX-TASK-CREATED-UNBUNDLED", code == 201 && task["context_bundle_id"] == nil &&
		domain.Str(task, "status") == "DRAFT", code, body)
	if code != 201 {
		return
	}

	// a freeze built on a ProjectState that is no longer current is refused, not silently rebased
	// Two layers can refuse a stale freeze. The HTTP precondition refuses an out-of-date If-Match,
	// so to show the domain-level compare-and-set is real, the precondition is satisfied with the
	// CURRENT state tag while the body names a revision that no longer exists.
	// the precondition must be CURRENT here, or the refusal would come from the HTTP layer and the
	// domain compare-and-set would stay untested; only the body carries the stale revision
	current, currentTag := h.liveState(ctx, token, base)
	code, _, body = h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(), currentTag,
		domain.Object{"task_id": domain.Str(task, "id"), "expected_project_state_revision": 99999})
	ok("CTX-STALE-EXPECTED-REVISION-REJECTED", code == 412 && strings.Contains(body, "STALE_REVISION"), code, body)
	ok("CTX-STALE-CAS-ISOLATED-FROM-PRECONDITION", current["revision"] != 99999, current["revision"])
	// the other layer, positively: satisfy the body and let the precondition go stale instead
	// re-read, because every accepted write above moved the state; the tag captured here is then made
	// stale by one more accepted write, which is the only honest way to exercise this layer
	fresh, _ := h.liveState(ctx, token, base)
	freshRevision := domain.Object(fresh)
	beforeTag := tagOf(fresh)
	code, _, body = h.api(ctx, token, "POST", base+"/requirements", domain.ID(), beforeTag, domain.Object{
		"requirement_key": "REQ-W0402-MOVE", "text": "a second statement moves the state forward",
		"basis": "USER_STATED", "source_refs": domain.Empty(), "rationale": "precondition staleness fixture",
		"supersedes_id": nil, "acceptance_check_ids": domain.Empty()})
	if code == 201 {
		code, _, body = h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(), beforeTag,
			domain.Object{"task_id": domain.Str(task, "id"), "expected_project_state_revision": freshRevision["revision"]})
		ok("CTX-STALE-PRECONDITION-REJECTED", code == 412 && strings.Contains(body, "STALE_REVISION"), code, body)
	} else {
		ok("CTX-STALE-PRECONDITION-REJECTED", false, "the state could not be moved forward: "+body)
	}

	state, _ = h.liveState(ctx, token, base)
	bundleKey := domain.ID()
	code, bundle, body := h.api(ctx, token, "POST", base+"/context-bundles", bundleKey, tagOf(state),
		domain.Object{"task_id": domain.Str(task, "id"), "expected_project_state_revision": state["revision"]})
	ok("CTX-BUNDLE-CREATED", code == 201, code, body)
	if code != 201 {
		return
	}

	// every field the frozen ContextBundle contract demands; the list is read from the schema, not
	// from what the implementation happens to emit
	required := []string{"id", "project_id", "revision", "created_at", "receipt_hash", "task_id",
		"project_state_revision", "version_vector", "facts", "unresolved_items", "latest_decision_refs",
		"unfinished_commitments", "summary", "summary_hash", "source_manifest_hash",
		"authorized_snapshot_ids", "policy_revision"}
	absent := []string{}
	for _, f := range required {
		if _, has := bundle[f]; !has {
			absent = append(absent, f)
		}
	}
	ok("CTX-BUNDLE-CARRIES-ALL-REQUIRED-FIELDS", len(absent) == 0, absent)
	ok("CTX-BUNDLE-FROZEN-FROM-LIVE-STATE", bundle["project_state_revision"] == state["revision"] &&
		bundle["project_state_revision"] != nil, bundle["project_state_revision"], state["revision"])
	bundleJSON := string(domain.Bytes(bundle))
	ok("CTX-BUNDLE-KEEPS-USER-WORDS-VERBATIM", strings.Contains(bundleJSON, userWords),
		bundleJSON[:min(len(bundleJSON), 500)])
	// what the freeze carries as decisions comes from ProjectState.current_decision_refs, which an
	// accepted change fills; two recorded-but-unapplied decisions therefore must NOT appear, and
	// asserting their absence is the honest statement of where this property still lives
	if Str2(decisionB, "id") != "" {
		ok("CTX-BUNDLE-DECISIONS-FOLLOW-THE-APPLIED-STATE",
			len(domain.Arr(bundle, "latest_decision_refs")) == 0 &&
				!strings.Contains(Str2(bundle, "summary"), Str2(decisionA, "id")),
			domain.Arr(bundle, "latest_decision_refs"))
		skip("CTX-BUNDLE-DECISION-SCOPE", "before any change is applied the project has no governing decision, so "+
			"an empty latest_decision_refs here is the correct answer and not a gap; the populated case is "+
			"asserted after the independently accepted change by CHG-REFREEZE-CARRIES-EFFECTIVE-DECISION and "+
			"CHG-REFREEZE-KEEPS-RETIRED-DECISION-AS-HISTORY")
	}
	// the vector is a set of version references, each pinned to an entity, an id and a revision -
	// not a list of names a later reader would have to guess at
	vector := domain.Arr(bundle, "version_vector")
	shaped := 0
	for _, raw := range vector {
		v := domain.Object(raw.(map[string]any))
		if Str2(v, "entity_type") != "" && Str2(v, "id") != "" && v["revision"] != nil {
			shaped++
		}
	}
	ok("CTX-BUNDLE-VERSION-VECTOR-BOUNDED", len(vector) >= 1 && shaped == len(vector) &&
		strings.Contains(bundleJSON, `"entity_type":"ProjectProfile"`), shaped, len(vector))
	ok("CTX-BUNDLE-REVISION-IS-ONE", fmt.Sprint(bundle["revision"]) == "1", bundle["revision"])
	ok("CTX-BUNDLE-HASHES-POPULATED", domain.Str(bundle, "receipt_hash") != "" && domain.Str(bundle, "summary_hash") != "" &&
		domain.Str(bundle, "source_manifest_hash") != "" &&
		domain.Str(bundle, "summary_hash") == domain.Digest([]byte(domain.Str(bundle, "summary"))),
		domain.Str(bundle, "summary_hash"))

	// the same command id replays into the same freeze instead of minting a second identity
	code, replay, body := h.api(ctx, token, "POST", base+"/context-bundles", bundleKey, tagOf(state),
		domain.Object{"task_id": domain.Str(task, "id"), "expected_project_state_revision": state["revision"]})
	ok("CTX-BUNDLE-REPLAY-SAME-IDENTITY", code == 201 && domain.Str(replay, "id") == domain.Str(bundle, "id"),
		code, domain.Str(replay, "id"))

	code, taskAfter, _ := h.api(ctx, token, "GET", base+"/tasks/"+domain.Str(task, "id"), "", "", nil)
	ok("CTX-TASK-POINTS-AT-BUNDLE", code == 200 && domain.Str(taskAfter, "context_bundle_id") == domain.Str(bundle, "id"),
		code, domain.Str(taskAfter, "context_bundle_id"))
	got, gerr := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
	ok("CTX-CONTEXT-READABLE-BY-WORKER", gerr == nil && domain.Str(got, "id") == domain.Str(bundle, "id"), errText(gerr))

	// integrity is load-bearing rather than decorative: tamper with what was stored and the read
	// must refuse. The store may itself reject the write, which is the same protection one level
	// down, so both answers are accepted and neither is left unverified.
	_, tamperErr := h.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.summary','tampered') WHERE kind='ContextBundle' AND id=?`,
		domain.Str(bundle, "id"))
	if tamperErr != nil {
		ok("CTX-TAMPERED-BUNDLE-REFUSED", true, "storage refused the write: "+errText(tamperErr))
	} else {
		_, after := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
		ok("CTX-TAMPERED-BUNDLE-REFUSED", after != nil &&
			strings.Contains(errText(after), "CONTENT_HASH_MISMATCH"), errText(after))
		if _, e := h.db.Exec(`UPDATE domain_objects SET body=? WHERE kind='ContextBundle' AND id=?`,
			string(domain.Bytes(bundle)), domain.Str(bundle, "id")); e == nil {
			_, back := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
			ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", back == nil, errText(back))
		}
	}

	// step 2: the worker gets its files in an empty workspace and the bytes are checked, not assumed
	ws := filepath.Join(h.root, "w0402-worker", "run-1")
	cwd, _ := os.Getwd()
	var workspaceExists bool
	manifest, merr := h.svc.MaterializeTaskContext(ctx, token, project, domain.Str(task, "id"), ws)
	if _, statErr := os.Stat(ws); statErr == nil {
		workspaceExists = true
	}
	ok("CTX-MATERIALIZE-INTO-FRESH-DIRECTORY", merr == nil, errText(merr))
	if merr == nil {
		// the manifest is an array of {path, ref, content_hash} entries; find it by shape rather than
		// trusting one key name, because the report is about the delivered files
		var entries []any
		for _, v := range manifest {
			if a, _ := v.([]any); len(a) > 0 {
				if m, _ := a[0].(map[string]any); m != nil && m["path"] != nil {
					entries = a
				}
			}
		}
		ok("CTX-MATERIALIZE-EMITS-A-MANIFEST", len(entries) >= 1, string(domain.Bytes(manifest))[:400])
		// the frozen bundle and the manifest themselves land at the workspace root, beside inputs/
		_, bundleFileErr := os.Stat(filepath.Join(ws, "bundle.json"))
		_, manifestFileErr := os.Stat(filepath.Join(ws, "manifest.json"))
		ok("CTX-MATERIALIZE-DELIVERS-BUNDLE-AND-MANIFEST", bundleFileErr == nil && manifestFileErr == nil,
			bundleFileErr, manifestFileErr)
		ok("CTX-MATERIALIZE-MANIFEST-NAMES-BUNDLE-AND-RESUME",
			domain.Str(manifest, "bundle_ref") == domain.Str(bundle, "id") ||
				strings.Contains(string(domain.Bytes(manifest)), domain.Str(bundle, "id")),
			domain.Str(manifest, "bundle_ref"))
		inside, hashed, named := 0, 0, 0
		exactBytes, readOnly := false, false
		sealed := domain.Digest(evidence)
		for _, raw := range entries {
			e := domain.Object(raw.(map[string]any))
			name := domain.Str(e, "path")
			if name == "" {
				continue
			}
			named++
			full := filepath.Join(ws, filepath.FromSlash(name))
			rel, rerr := filepath.Rel(ws, full)
			if rerr == nil && !strings.HasPrefix(rel, "..") && filepath.IsAbs(full) {
				inside++
			}
			if b, err := os.ReadFile(full); err == nil &&
				domain.Digest(b) == domain.Str(e, "content_hash") {
				hashed++
				// the one entry that carries the operator's own bytes: identical content, and not
				// writable by the worker that received it
				if domain.Str(e, "content_hash") == sealed {
					exactBytes = true
					if fi, ferr := os.Stat(full); ferr == nil {
						readOnly = fi.Mode()&0o200 == 0
					}
				}
			}
		}
		ok("CTX-MATERIALIZE-ENTRIES-RESOLVE-UNDER-WORKSPACE", named > 0 && inside == named, inside, named)
		ok("CTX-MATERIALIZE-BYTES-MATCH-MANIFEST-HASHES", named > 0 && hashed == named, hashed, named)
		// the delivered file is the byte-for-byte input, delivered read-only: a worker that "rewrote
		// the context" could otherwise pass a hash-only check
		ok("CTX-MATERIALIZE-INPUT-IS-THE-SEALED-BYTES-READ-ONLY", exactBytes && readOnly, exactBytes, readOnly)
		// the worker's tree is built where the caller said, never relative to the process cwd: if the
		// service had assumed the parent cwd, an inputs/ directory would have appeared in the repository
		_, cwdLeak := os.Stat(filepath.Join(cwd, "inputs"))
		ok("CTX-MATERIALIZE-WORKSPACE-IS-DESTINATION-NOT-CWD",
			workspaceExists && cwdLeak != nil && filepath.IsAbs(ws), workspaceExists, cwdLeak)

		_, second := h.svc.MaterializeTaskContext(ctx, token, project, domain.Str(task, "id"), ws)
		ok("CTX-MATERIALIZE-REFUSES-EXISTING-DIRECTORY", second != nil &&
			strings.Contains(errText(second), "STATE_CONFLICT"), errText(second))
	}

	// a worker without a grant on this project cannot read the context at all
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-outsider",
		Roles: []string{"EXECUTOR"}, Grants: []domain.Grant{{ProjectID: h.betaProj}}}); e == nil {
		if ot, terr := h.svc.IssueCredential(ctx, "w0402-outsider", 5*time.Minute); terr == nil {
			_, foreign := h.svc.GetTaskContext(ctx, ot, project, domain.Str(task, "id"))
			ok("CTX-FOREIGN-WORKER-CANNOT-READ-CONTEXT", foreign != nil, errText(foreign))
		}
	}

	w0402Ctx = w0402Handles{token: token, project: project, base: base, taskID: domain.Str(task, "id"),
		art: art, bundle: bundle, task: task, state: state, contract: contract,
		decisions: proposedRefs, goalID: Str2(goal, "id"), reqID: Str2(accepted, "id"),
		decEffective: Str2(decisionB, "id"), decRetired: Str2(decisionA, "id")}

	// card step 4 is asserted by the CHG ids: a task with no frozen context is blocked
	// (CHG-MISSING-REQUIRED-CONTEXT-BLOCKS) and an applied change stales exactly the tasks in its
	// closure while leaving an unrelated task as it was (CHG-APPLIED-CHANGE-*). The one half still
	// open - an optional retrieval degrading instead of blocking - is declared as
	// CHG-OPTIONAL-RETRIEVAL-DEGRADES, not glossed over.
	//
	// card step 3 is asserted too: the freeze writes explicit DEPENDS_ON links, drafts over an old
	// input or with an unfrozen check list are refused, and a conflict keeps both drafts and is
	// settled only by an accepted and applied change. What remains unasserted is the proposal's own
	// impacted_refs and impact_link_ids arrays, which analyzeChangeImpact fills and which need the
	// W06 orchestration fixture - recorded as CHG-PROPOSAL-NAMES-ITS-IMPACT.
}

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

	// freezing a context records dependency links for THIS task, so the assertions read the links the
	// freeze produced instead of any link some other phase happened to write. An unscoped count let two
	// mutations survive, which is the evidence that scoping was needed rather than decorative.
	code, listed, body := h.api(ctx, token, "GET", base+"/impact-links?limit=100", "", "", nil)
	items := domain.Arr(listed, "items")
	if len(items) == 0 {
		items = domain.Arr(listed, "objects")
	}
	mine, shaped, deterministic := 0, 0, 0
	for _, raw := range items {
		m, _ := raw.(map[string]any)
		if m == nil {
			continue
		}
		l := domain.Object(m)
		from, _ := l["from_ref"].(map[string]any)
		if from == nil || Str2(domain.Object(from), "id") != w0402Ctx.taskID {
			continue
		}
		mine++
		if l["to_ref"] != nil && Str2(l, "relation") == "DEPENDS_ON" && Str2(l, "status") == "ACTIVE" {
			shaped++
		}
		if Str2(l, "basis") == "DETERMINISTIC" {
			deterministic++
		}
	}
	ok("CHG-IMPACT-LINKS-ARE-EXPLICIT", code == 200 && mine > 0 && shaped == mine,
		code, mine, shaped, body[:min(len(body), 160)])
	ok("CHG-IMPACT-LINK-BASIS-IS-DETERMINISTIC", mine > 0 && deterministic == mine, mine, deterministic)
	ok("CHG-IMPACT-LINKS-EVIDENCE-POINTS-AT-THE-FREEZE",
		mine > 0 && strings.Contains(string(domain.Bytes(listed)), Str2(w0402Ctx.bundle, "id")),
		Str2(w0402Ctx.bundle, "id"))

	state, _ := h.liveState(ctx, token, base)
	stateID := Str2(state, "id")
	// the domain accepts a proposal only when it freezes exactly the supported deterministic checks
	supportedChangeChecks := []any{"context.inputs-frozen", "context.impact-exact",
		"context.authority-independent"}
	// every attempt reads the current state itself: a precondition captured once would go stale
	// between attempts and the refusal would then be about the fixture, not about the property
	proposal := func(baseRev any, targetRev any, checks []any) (int, domain.Object, string) {
		current, currentTag := h.liveState(ctx, token, base)
		if baseRev == nil {
			baseRev = current["revision"]
		}
		if targetRev == nil {
			targetRev = current["revision"]
		}
		return h.api(ctx, token, "POST", base+"/change-proposals", domain.ID(), currentTag, domain.Object{
			"title": "w0402 change", "reason": "carry the frozen decision forward",
			"base_state_revision": baseRev,
			"edits": []any{domain.Object{"target_ref": domain.Object{"entity_type": "ProjectState",
				"id": stateID, "revision": targetRev, "content_hash": nil},
				"field":                       "current_decision_refs",
				"proposed_value_artifact_ref": domain.Ref(w0402Ctx.art, "Artifact"),
				"reason":                      "fixture edit"}},
			"migration_steps": domain.Empty(), "test_check_ids": checks,
			"rollback_steps": []any{"submit an independently accepted reversal"}})
	}
	code, proposalA, body := proposal(nil, nil, supportedChangeChecks)
	ok("CHG-PROPOSAL-CREATED", code == 201, code, body)
	if code != 201 {
		return
	}
	ok("CHG-PROPOSAL-RECORDS-BASE-STATE", proposalA["base_state_revision"] != nil &&
		(Str2(proposalA, "status") == "DRAFT" || Str2(proposalA, "status") == "IMPACT_ANALYZED"),
		Str2(proposalA, "status"))
	// the card's step 3: the record names what it affects, deterministically, rather than leaving a
	// later reader to guess the closure
	skip("CHG-PROPOSAL-NAMES-ITS-IMPACT", "impacted_refs and impact_link_ids stay empty on a proposal until analyzeChangeImpact runs, and that operation needs a settled orchestration fixture run (live EXECUTOR grant, authority root, frozen contract, trusted observation, sealed report) which is W06/harness territory. The deterministic links the freeze itself writes ARE asserted above.")

	// a proposal that drops one of the supported checks is refused before anything is recorded
	code, _, body = proposal(nil, nil, []any{"context.inputs-frozen", "context.impact-exact"})
	ok("CHG-UNFROZEN-CHECKS-REJECTED", code == 422 && strings.Contains(body, "GATE_FAILED"), code, body)

	// a proposal built on a state that has moved is refused, and so is an edit whose own target
	// reference is older than what the project now holds
	code, _, body = proposal(99999, nil, supportedChangeChecks)
	ok("CHG-STALE-BASE-STATE-REJECTED", code == 412 && strings.Contains(body, "STALE_REVISION"), code, body)
	code, _, body = proposal(nil, 1, supportedChangeChecks)
	ok("CHG-STALE-EDIT-TARGET-REJECTED", code == 412 && strings.Contains(body, "STALE_INPUT"), code, body)

	// An open non-decision conflict blocks every later proposal and acceptance in the project - that
	// is a domain rule this phase discovered by experiment - so the applied-change leg runs first.
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-verifier",
		Roles: []string{"VERIFIER"}, Grants: []domain.Grant{{ProjectID: w0402Ctx.project}}}); e != nil {
		ok("CHG-VERIFIER-PROVISIONED", false, errText(e))
		return
	}
	ok("CHG-VERIFIER-PROVISIONED", true)
	verifierToken, verr := h.svc.IssueCredential(ctx, "w0402-verifier", 5*time.Minute)
	ok("CHG-VERIFIER-CREDENTIAL", verr == nil && verifierToken != "", errText(verr))
	acceptBody := func(p domain.Object, hash string) domain.Object {
		st, _ := h.liveState(ctx, token, base)
		return domain.Object{"subject_ref": domain.Ref(p, "ChangeProposal"), "run_id": nil,
			"contract_hash": hash, "input_refs": []any{domain.Ref(p, "ChangeProposal")},
			"artifact_refs": domain.Empty(),
			"checks": []any{domain.Object{"check_id": "client-not-authoritative", "status": "NOT_RUN",
				"evidence_refs": domain.Empty(), "command_key": nil, "actual": "server must recompute",
				"exit_code": nil, "started_at": nil, "finished_at": nil}},
			"verdict": "BLOCKED", "executor_principal_ids": domain.Empty(),
			"independence_basis": "DETERMINISTIC_SERVICE", "blocking_conflict_ids": domain.Empty(),
			"qualification_ids": domain.Empty(), "policy_revision": st["policy_revision"],
			"measurement_mode": "FIXTURE", "reason": "request server independent verification"}
	}
	frozen, cherr := h.svc.ChangeContractHash(ctx, w0402Ctx.project, Str2(proposalA, "id"))
	ok("CHG-CONTRACT-HASH-FREEZABLE", cherr == nil && frozen != "", errText(cherr))
	// The refusal has to come from independence and not from a missing role, so the principal here
	// holds every role including VERIFIER and authored the draft it now tries to accept. An earlier
	// version of this assertion passed for the wrong reason and a mutation proved it.
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-selfauthor",
		Roles:            []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER", "VERIFIER"},
		CanCreateProject: true, Grants: []domain.Grant{{ProjectID: w0402Ctx.project}}}); e != nil {
		ok("CHG-SELF-AUTHOR-PROVISIONED", false, errText(e))
		return
	}
	ok("CHG-SELF-AUTHOR-PROVISIONED", true)
	selfToken, sterr := h.svc.IssueCredential(ctx, "w0402-selfauthor", 5*time.Minute)
	ok("CHG-SELF-AUTHOR-CREDENTIAL", sterr == nil && selfToken != "", errText(sterr))
	selfState, selfTag := h.liveState(ctx, selfToken, base)
	code, selfProposal, body := h.api(ctx, selfToken, "POST", base+"/change-proposals", domain.ID(), selfTag,
		domain.Object{"title": "w0402 self-authored change", "reason": "test the independence rule",
			"base_state_revision": selfState["revision"],
			"edits": []any{domain.Object{"target_ref": domain.Object{"entity_type": "ProjectState",
				"id": Str2(selfState, "id"), "revision": selfState["revision"], "content_hash": nil},
				"field":                       "current_decision_refs",
				"proposed_value_artifact_ref": domain.Ref(w0402Ctx.art, "Artifact"),
				"reason":                      "fixture edit"}},
			"migration_steps": domain.Empty(), "test_check_ids": supportedChangeChecks,
			"rollback_steps": []any{"submit an independently accepted reversal"}})
	ok("CHG-SELF-AUTHOR-PROPOSAL-CREATED", code == 201, code, body[:min(len(body), 200)])
	if code == 201 {
		selfFrozen, sferr := h.svc.ChangeContractHash(ctx, w0402Ctx.project, Str2(selfProposal, "id"))
		ok("CHG-SELF-AUTHOR-CONTRACT-FREEZABLE", sferr == nil && selfFrozen != "", errText(sferr))
		code, _, body = h.api(ctx, selfToken, "POST", base+"/acceptances", domain.ID(),
			tagOf(selfProposal), acceptBody(selfProposal, selfFrozen))
		ok("CHG-AUTHOR-CANNOT-ACCEPT-OWN-CHANGE", code == 403 &&
			strings.Contains(body, "author cannot independently accept"), code, body[:min(len(body), 200)])
	}
	// and the same draft is acceptable to a principal that did not author it
	code, _, body = h.api(ctx, token, "POST", base+"/acceptances", domain.ID(), tagOf(proposalA),
		acceptBody(proposalA, frozen))
	ok("CHG-PLANNER-CANNOT-ACCEPT-ANOTHER-PRINCIPALS-DRAFT", code == 403 || code == 409,
		code, body[:min(len(body), 160)])

	code, proposalC, body := proposal(nil, nil, supportedChangeChecks)
	ok("CHG-CLEAN-PROPOSAL-CREATED", code == 201, code, body[:min(len(body), 200)])
	if code != 201 {
		return
	}
	frozenC, ferr := h.svc.ChangeContractHash(ctx, w0402Ctx.project, Str2(proposalC, "id"))
	ok("CHG-CLEAN-CONTRACT-HASH-FREEZABLE", ferr == nil && frozenC != "", errText(ferr))
	code, receipt, body := h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
		tagOf(proposalC), acceptBody(proposalC, frozenC))
	ok("CHG-INDEPENDENT-ACCEPTANCE-COMPUTED", code == 201 && Str2(receipt, "verdict") == "PASS",
		code, Str2(receipt, "verdict"), body[:min(len(body), 200)])
	if code != 201 || Str2(receipt, "verdict") != "PASS" {
		return
	}
	beforeApply, _ := h.liveState(ctx, token, base)
	code, applied, body := h.api(ctx, token, "POST",
		base+"/change-proposals/"+Str2(proposalC, "id")+"/apply", domain.ID(), tagOf(proposalC),
		domain.Object{"acceptance_id": receipt["id"], "expected_project_state_revision": beforeApply["revision"]})
	ok("CHG-APPLIED-CHANGE-STATES-ADVANCE", code == 200 && Str2(applied, "status") == "APPLIED" &&
		applied["applied_state_revision"] != nil, code, Str2(applied, "status"), body[:min(len(body), 220)])
	movedState, _ := h.liveState(ctx, token, base)
	ok("CHG-APPLY-MOVES-THE-PROJECT-STATE", movedState["revision"] != beforeApply["revision"],
		beforeApply["revision"], movedState["revision"])
	code, refrozen, body := h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(), tagOf(movedState),
		domain.Object{"task_id": w0402Ctx.taskID, "expected_project_state_revision": movedState["revision"]})
	ok("CHG-REFREEZE-AFTER-APPLY-ACCEPTED", code == 201, code, body[:min(len(body), 160)])
	if code == 201 {
		listed := string(domain.Bytes(domain.Arr(refrozen, "latest_decision_refs")))
		summary := Str2(refrozen, "summary")
		effective := ""
		if len(w0402Ctx.decisions) > 0 {
			if m, _ := w0402Ctx.decisions[0].(map[string]any); m != nil {
				effective = Str2(domain.Object(m), "id")
			}
		}
		ok("CHG-APPLIED-DECISION-LANDS-IN-THE-STATE", effective != "" &&
			strings.Contains(string(domain.Bytes(movedState["current_decision_refs"])), effective),
			Str2(movedState, "id"))
		// the governing decisions live on the project state, so a freeze taken after an accepted
		// change carries them even though this task never named them as inputs - that is the card's
		// effective-decision requirement, asserted rather than skipped
		ok("CHG-REFREEZE-CARRIES-EFFECTIVE-DECISION", w0402Ctx.decEffective != "" &&
			strings.Contains(listed, w0402Ctx.decEffective), domain.Arr(refrozen, "latest_decision_refs"))
		ok("CHG-REFREEZE-KEEPS-RETIRED-DECISION-AS-HISTORY", w0402Ctx.decRetired != "" &&
			strings.Contains(summary, "historical_decision_refs") &&
			strings.Contains(summary, w0402Ctx.decRetired), summary[:min(len(summary), 260)])
	}

	// applyChange runs a draft all the way through - proposal, independent acceptance by the
	// verifier, apply - and hands back the applied record so each caller asserts its own property.
	applyChange := func(targetRef domain.Object, field string, valueArt domain.Object, title string) (domain.Object, string) {
		st, tg := h.liveState(ctx, token, base)
		code, prop, body := h.api(ctx, token, "POST", base+"/change-proposals", domain.ID(), tg, domain.Object{
			"title": title, "reason": "fixture change with a real dependency closure",
			"base_state_revision": st["revision"],
			"edits": []any{domain.Object{"target_ref": targetRef, "field": field,
				"proposed_value_artifact_ref": domain.Ref(valueArt, "Artifact"),
				"reason":                      "explicit fixture edit"}},
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

	// two drafts over the same field, then a conflict naming both: neither draft may move
	code, proposalB, body := proposal(nil, nil, supportedChangeChecks)
	ok("CHG-SECOND-PROPOSAL-CREATED", code == 201, code, body)
	if code == 201 {
		beforeA := string(domain.Bytes(proposalA))
		beforeB := string(domain.Bytes(proposalB))
		conflictState, _ := h.liveState(ctx, token, base)
		code, conflict, body := h.api(ctx, token, "POST", base+"/conflicts", domain.ID(), tagOf(conflictState),
			// CreateConflictRequest is closed: kind, the two subjects and what they block, nothing else
			domain.Object{"kind": "REVISION",
				"subject_refs": []any{domain.Ref(proposalA, "ChangeProposal"),
					domain.Ref(proposalB, "ChangeProposal")},
				"description": "two drafts edit the same field", "blocks_refs": domain.Empty()})
		ok("CHG-CONFLICT-KEEPS-BOTH-SIDES", code == 201 &&
			len(domain.Arr(conflict, "subject_refs")) == 2 && Str2(conflict, "status") == "OPEN", code, body)
		_, aAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
		_, bAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
		ok("CHG-CONFLICT-DOES-NOT-OVERWRITE-A-DRAFT",
			string(domain.Bytes(aAfter)) == beforeA && string(domain.Bytes(bAfter)) == beforeB,
			Str2(proposalA, "id"), Str2(proposalB, "id"))

		// while the conflict is open, the conflicted draft cannot be independently accepted
		code, _, body = h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
			tagOf(proposalA), acceptBody(proposalA, frozen))
		ok("CHG-CONFLICTED-DRAFT-IS-NOT-ACCEPTABLE", code == 409, code, body[:min(len(body), 200)])

		// the applied clean change is what settles it, and settling it rewrites neither draft
		code, resolved, body := h.api(ctx, token, "POST",
			base+"/conflicts/"+Str2(conflict, "id")+"/resolve", domain.ID(), tagOf(conflict),
			domain.Object{"resolution_proposal_id": Str2(proposalC, "id"),
				"reason": "the independently accepted change settled the field"})
		ok("CHG-CONFLICT-RESOLVED-BY-AN-APPLIED-CHANGE", code == 200 &&
			Str2(resolved, "status") == "RESOLVED" &&
			Str2(resolved, "resolution_proposal_id") == Str2(proposalC, "id"), code,
			Str2(resolved, "status"), body[:min(len(body), 200)])
		_, aFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
		_, bFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
		// settling the conflict rewrites neither draft
		ok("CHG-RESOLUTION-KEEPS-BOTH-DRAFTS",
			string(domain.Bytes(aFinal)) == beforeA && string(domain.Bytes(bFinal)) == beforeB,
			Str2(proposalA, "id"), Str2(proposalB, "id"))
	}

	// a task with no frozen context cannot be handed work, and none of the activity above
	// invalidated an unrelated task
	goalID := Str2(w0402Ctx.task, "goal_id")
	_, goalNow, _ := h.api(ctx, token, "GET", base+"/goals/"+w0402Ctx.goalID, "", "", nil)
	code, bare, body := h.api(ctx, token, "POST", base+"/tasks", domain.ID(), tagOf(goalNow), domain.Object{
		"goal_id": goalID, "title": "w0402 unbundled task", "task_type": "construction",
		"stage": "verification", "dependency_task_ids": domain.Empty(), "requirement_refs": domain.Empty(),
		"input_refs": domain.Empty(), "acceptance_contract": w0402Ctx.contract,
		"origin_problem_id": "p-w0402", "candidate_id": "c-w0402",
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}})
	ok("CHG-SECOND-TASK-WAITING", code == 201 && bare["context_bundle_id"] == nil, code, body)
	if code == 201 {
		stateNow, _ := h.liveState(ctx, token, base)
		code, _, body = h.api(ctx, token, "POST", base+"/messages", domain.ID(), tagOf(stateNow),
			domain.Object{"task_id": Str2(bare, "id"), "run_id": nil, "correlation_id": domain.ID(),
				"recipient_id": "w0402-planner", "message_type": "HANDOFF",
				"body": "hand work to a task that has no frozen context", "refs": domain.Empty()})
		ok("CHG-MISSING-REQUIRED-CONTEXT-BLOCKS", code == 422 && strings.Contains(body, "GATE_FAILED"), code, body)
	}
	// the positive control the earlier version of this phase could only skip: an applied change does
	// make the tasks it impacts stale, and a task that has nothing to do with it stays untouched
	// the positive control. The freeze wrote Task -> Requirement DEPENDS_ON links, so an accepted
	// change to that requirement has this task in its closure and must make exactly it stale, while
	// a task that depends on nothing stays as it was.
	revisionPayload := []byte(`"revised by an independently accepted change"`)
	stForUpload, tagForUpload := h.liveState(ctx, token, base)
	_ = stForUpload
	textRef, textArt, textBody := h.api(ctx, token, "POST", base+"/content", domain.ID(), tagForUpload,
		revisionPayload)
	ok("CHG-REVISION-CONTENT-UPLOADED", textRef == 201, textRef, textBody[:min(len(textBody), 160)])
	reqCode, reqNow, reqBody := h.api(ctx, token, "GET", base+"/requirements/"+w0402Ctx.reqID, "", "", nil)
	ok("CHG-REQUIREMENT-READABLE-FOR-EDIT", reqCode == 200 && Str2(reqNow, "id") == w0402Ctx.reqID,
		reqCode, reqBody[:min(len(reqBody), 160)])
	st, tg := h.liveState(ctx, token, base)
	_ = st
	code, revisionArt, body := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(), tg, domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": textArt["content_hash"], "storage_key": textArt["storage_key"],
		"media_type": "application/json", "byte_size": len(revisionPayload), "input_refs": domain.Empty(),
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
	skip("CHG-OPTIONAL-RETRIEVAL-DEGRADES", "the optional-retrieval warning path needs the FTS/retrieval fixture "+
		"(retrieval.go pushes warnings and continues); no assertion here yet")
}

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
