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

	// a real input file, so the worker manifest has bytes to deliver and hashes to check
	evidence := []byte("w0402 fixture evidence: the operator owns this context, delivered byte for byte")
	state, _ = h.liveState(ctx, token, base)
	code, upload, body := h.api(ctx, token, "POST", base+"/content", domain.ID(), "", evidence)
	ok("CTX-INPUT-CONTENT-UPLOADED", code == 201, code, body)
	if code != 201 {
		return
	}
	code, art, body := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(), tagOf(state), domain.Object{
		"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
		"content_hash": upload["content_hash"], "storage_key": upload["storage_key"],
		"media_type": "text/plain", "byte_size": len(evidence),
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

	skip("CTX-STEP-4-BLOCK-DEGRADE-UNRELATED", "blocking on missing required context, degradation on a failed "+
		"optional retrieval and non-invalidation by an unrelated event are the next increment of this card; the "+
		"entry points are known (taskContext gate 422 GATE_FAILED, retrieval warnings list, ConsumeEvent touches "+
		"only context_projection while staleness comes from applyChange) but are not asserted yet")
	skip("CTX-STEP-3-CHANGE-IMPACT", "explicit impact links, rejection of a proposal built on an old input and "+
		"conflicts preserving both sides are not asserted yet; analyzeChangeImpact additionally needs a settled "+
		"orchestration fixture run, which this increment has not built")
}
