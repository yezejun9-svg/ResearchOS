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

	// Key presence is already guaranteed by the frozen schema, so asserting it proves nothing. Each
	// field below is compared against the value the live project actually holds, read back
	// independently of the freeze that produced the bundle.
	profileCode, profile, profileBody := h.api(ctx, token, "GET", base+"/profile", "", "", nil)
	ok("CTX-FACTS-COME-FROM-THE-LIVE-PROFILE", profileCode == 200 &&
		domain.Hash(bundle["facts"]) == domain.Hash(profile["facts"]),
		profileCode, domain.Hash(bundle["facts"]), domain.Hash(profile["facts"]),
		profileBody[:min(len(profileBody), 160)])
	ok("CTX-POLICY-REVISION-MATCHES-THE-LIVE-STATE",
		bundle["policy_revision"] != nil && domain.Hash(bundle["policy_revision"]) == domain.Hash(state["policy_revision"]),
		bundle["policy_revision"], state["policy_revision"])

	// unresolved_items is the field that tells a new session what is still open, so it is compared
	// against the blocking index the freeze read, entry for entry - not merely counted.
	expectedUnresolved := domain.Empty()
	for _, v := range domain.Arr(state, "blocking_conflict_ids") {
		expectedUnresolved = append(expectedUnresolved, "Open conflict: "+fmt.Sprint(v))
	}
	unresolvedItems := domain.Arr(bundle, "unresolved_items")
	ok("CTX-UNRESOLVED-ITEMS-MATCH-THE-LIVE-BLOCKING-INDEX",
		len(unresolvedItems) == len(expectedUnresolved) &&
			domain.Hash(unresolvedItems) == domain.Hash(expectedUnresolved),
		unresolvedItems, expectedUnresolved)

	// The authorized snapshot list is the subset of the profile's registered retrieval snapshots that
	// still resolve. No retrieval root is registered in this fixture, so the honest expected value on
	// both sides is empty, and the assertion is that the freeze invented nothing.
	var profileSnapshotsJSON string
	if e := h.db.QueryRowContext(ctx,
		`SELECT json_extract(body,'$.read_snapshot_ids') FROM domain_objects WHERE project=? AND kind='ProjectProfile'`,
		project).Scan(&profileSnapshotsJSON); e != nil {
		ok("CTX-AUTHORIZED-SNAPSHOTS-COME-FROM-THE-PROFILE-INDEX", false, errText(e))
	} else {
		var profileSnapshots []string
		if profileSnapshotsJSON != "" && profileSnapshotsJSON != "null" {
			if e := json.Unmarshal([]byte(profileSnapshotsJSON), &profileSnapshots); e != nil {
				ok("CTX-AUTHORIZED-SNAPSHOTS-COME-FROM-THE-PROFILE-INDEX", false, errText(e))
			}
		}
		registered := map[string]bool{}
		for _, id := range profileSnapshots {
			registered[id] = true
		}
		snapshotIDs := domain.Arr(bundle, "authorized_snapshot_ids")
		unregistered := []string{}
		for _, v := range snapshotIDs {
			if id := fmt.Sprint(v); !registered[id] {
				unregistered = append(unregistered, id)
			}
		}
		ok("CTX-AUTHORIZED-SNAPSHOTS-COME-FROM-THE-PROFILE-INDEX",
			len(unregistered) == 0 && len(snapshotIDs) <= len(profileSnapshots),
			len(snapshotIDs), len(profileSnapshots), unregistered)
	}

	// The continuation is the answer to "what is the accurate next step", so it is parsed out of the
	// frozen summary and read field by field rather than searched for as a substring.
	summary := Str2(bundle, "summary")
	continuation := continuationOf(bundle)
	continuationRaw := ""
	if strings.Contains(summary, continuationMarker) {
		continuationRaw = summary[strings.Index(summary, continuationMarker)+len(continuationMarker):]
	}
	ok("CTX-FREEZE-NAMES-THE-ACCURATE-NEXT-STEP", continuation != nil &&
		domain.Str(continuation, "next_task_id") == domain.Str(task, "id") &&
		domain.Str(continuation, "next_task_title") == domain.Str(task, "title") &&
		domain.Str(continuation, "goal_id") == Str2(goal, "id"),
		continuationRaw[:min(len(continuationRaw), 400)])
	ok("CTX-CONTINUATION-CARRIES-THE-OPERATORS-OWN-INTENT",
		continuation != nil && domain.Str(continuation, "goal_intent") == userWords,
		domain.Str(continuation, "goal_intent"))
	contractInContinuation, _ := continuation["acceptance_contract"].(map[string]any)
	ok("CTX-CONTINUATION-CARRIES-THE-ACCEPTANCE-CONTRACT", contractInContinuation != nil &&
		domain.Str(domain.Object(contractInContinuation), "contract_hash") == domain.Str(contract, "contract_hash"),
		domain.Str(domain.Object(contractInContinuation), "contract_hash"),
		domain.Str(contract, "contract_hash"))

	// what the freeze carries as decisions comes from ProjectState.current_decision_refs, which an
	// accepted change fills; two recorded-but-unapplied decisions therefore must NOT appear, and
	// asserting their absence is the honest statement of where this property still lives
	if Str2(decisionB, "id") != "" {
		ok("CTX-BUNDLE-DECISIONS-FOLLOW-THE-APPLIED-STATE",
			len(domain.Arr(bundle, "latest_decision_refs")) == 0 &&
				len(domain.Arr(continuation, "current_decision_refs")) == 0 &&
				len(domain.Arr(continuation, "historical_decision_refs")) == 0 &&
				!strings.Contains(summary, Str2(decisionA, "id")),
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

	// Integrity is load-bearing at two separate layers, and each layer needs its own positive control.
	// The stored bundle row carries a receipt hash, so the storage trigger refuses a direct rewrite;
	// that refusal used to be the only branch this block could take, which left the service-side hash
	// check in authorizedContext with zero coverage and let a mutation of it survive. Lifting the
	// trigger on this throwaway fixture database - and putting it back, asserted below - is what makes
	// the service guard the thing that refuses.
	var sealedBody string
	if e := h.db.QueryRowContext(ctx,
		`SELECT body FROM domain_objects WHERE project=? AND kind='ContextBundle' AND id=?`,
		project, domain.Str(bundle, "id")).Scan(&sealedBody); e != nil {
		sealedBody = ""
		ok("CTX-SEALED-BUNDLE-BYTES-CAPTURED", false, errText(e))
	} else {
		ok("CTX-SEALED-BUNDLE-BYTES-CAPTURED", sealedBody != "", len(sealedBody))
	}

	_, tamperErr := h.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.summary','tampered') WHERE kind='ContextBundle' AND id=?`,
		domain.Str(bundle, "id"))
	ok("CTX-STORAGE-REFUSES-TO-REWRITE-A-SEALED-BUNDLE", tamperErr != nil &&
		strings.Contains(errText(tamperErr), "immutable"), errText(tamperErr))
	untouched, stillReadable := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
	ok("CTX-BUNDLE-SURVIVES-A-REFUSED-TAMPERING", stillReadable == nil &&
		domain.Str(untouched, "id") == domain.Str(bundle, "id"), errText(stillReadable))

	const immutabilityTrigger = `CREATE TRIGGER IF NOT EXISTS objects_immutable BEFORE UPDATE ON domain_objects WHEN OLD.immutable=1 BEGIN SELECT RAISE(ABORT,'immutable receipt'); END`
	if _, dropErr := h.db.Exec(`DROP TRIGGER IF EXISTS objects_immutable`); dropErr != nil {
		ok("CTX-SERVICE-REFUSES-A-TAMPERED-BUNDLE", false, "the storage trigger could not be lifted: "+errText(dropErr))
		ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", false, "not reached: the trigger could not be lifted")
	} else {
		_, updErr := h.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.summary','tampered') WHERE kind='ContextBundle' AND id=?`,
			domain.Str(bundle, "id"))
		if updErr != nil {
			ok("CTX-SERVICE-REFUSES-A-TAMPERED-BUNDLE", false,
				"the tampering write failed even with the trigger lifted: "+errText(updErr))
			ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", false, "not reached: the tampering write failed")
		} else {
			_, svcErr := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
			status, code := faultOf(svcErr)
			// the typed answer, not a substring: status class and protocol code together
			ok("CTX-SERVICE-REFUSES-A-TAMPERED-BUNDLE", svcErr != nil && status == 422 &&
				code == "CONTENT_HASH_MISMATCH", status, code, errText(svcErr))
			restore := func() error {
				_, e := h.db.Exec(`UPDATE domain_objects SET body=? WHERE kind='ContextBundle' AND id=?`,
					sealedBody, domain.Str(bundle, "id"))
				return e
			}
			// The guard has two halves and a summary tamper cannot tell them apart, because changing
			// $.summary breaks the summary hash as well as the receipt hash. So restore first, then
			// corrupt a field that leaves the summary alone: only the receipt hash can refuse that, and
			// the assertion below proves the summary half was still satisfied when it did. The field is
			// facts rather than policy_revision on purpose - a policy tamper is caught earlier, by the
			// 412 policy check in validateBundleSnapshots, and would prove nothing about this guard.
			if sealedBody == "" {
				ok("CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE", false,
					"no captured bytes to restore from")
			} else if e := restore(); e != nil {
				ok("CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE", false,
					"the bundle could not be restored before the second tamper: "+errText(e))
			} else if _, e := h.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.facts',json('["tampered by the fixture"]')) WHERE kind='ContextBundle' AND id=?`,
				domain.Str(bundle, "id")); e != nil {
				ok("CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE", false, errText(e))
			} else {
				var tamperedBody string
				h.db.QueryRowContext(ctx,
					`SELECT body FROM domain_objects WHERE project=? AND kind='ContextBundle' AND id=?`,
					project, domain.Str(bundle, "id")).Scan(&tamperedBody)
				var tampered map[string]any
				if e := json.Unmarshal([]byte(tamperedBody), &tampered); e != nil {
					tampered = nil
				}
				tamperedObj := domain.Object(tampered)
				summaryStillMatches := tampered != nil &&
					domain.Str(tamperedObj, "summary_hash") == domain.Digest([]byte(domain.Str(tamperedObj, "summary")))
				_, svcErr2 := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
				status2, code2 := faultOf(svcErr2)
				ok("CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE",
					summaryStillMatches && svcErr2 != nil && status2 == 422 &&
						code2 == "CONTENT_HASH_MISMATCH",
					summaryStillMatches, status2, code2, errText(svcErr2))
			}
			if sealedBody == "" {
				ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", false, "no captured bytes to restore from")
			} else if backErr := restore(); backErr != nil {
				ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", false,
					"the bundle could not be restored: "+errText(backErr))
			} else {
				restored, readErr := h.svc.GetTaskContext(ctx, token, project, domain.Str(task, "id"))
				ok("CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE", readErr == nil &&
					domain.Str(restored, "id") == domain.Str(bundle, "id") &&
					domain.Str(restored, "receipt_hash") == domain.Receipt(restored) &&
					domain.Str(restored, "summary_hash") == domain.Digest([]byte(domain.Str(restored, "summary"))),
					errText(readErr))
			}
		}
	}
	// the fixture database is put back exactly as the migrations left it, and that is proven by
	// re-attempting the write the trigger exists to refuse
	if _, restoreErr := h.db.Exec(immutabilityTrigger); restoreErr != nil {
		ok("CTX-STORAGE-IMMUTABILITY-TRIGGER-RESTORED", false, errText(restoreErr))
	} else {
		_, probeErr := h.db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.summary','tampered-again') WHERE kind='ContextBundle' AND id=?`,
			domain.Str(bundle, "id"))
		ok("CTX-STORAGE-IMMUTABILITY-TRIGGER-RESTORED", probeErr != nil &&
			strings.Contains(errText(probeErr), "immutable"), errText(probeErr))
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
		// The id promises the manifest names the bundle AND the resume instruction, so both are read
		// out of the file the worker actually receives and compared by value. The earlier form fell
		// back to "the bundle id appears somewhere in the bytes", which a manifest that named the
		// bundle but carried no usable resume instruction would still have satisfied.
		deliveredManifestRaw, manifestReadErr := os.ReadFile(filepath.Join(ws, "manifest.json"))
		var deliveredManifest map[string]any
		if manifestReadErr == nil {
			if e := json.Unmarshal(deliveredManifestRaw, &deliveredManifest); e != nil {
				deliveredManifest = nil
			}
		}
		delivered := domain.Object(deliveredManifest)
		bundleRefInManifest, _ := delivered["bundle_ref"].(map[string]any)
		ok("CTX-MATERIALIZE-MANIFEST-NAMES-BUNDLE-AND-RESUME", manifestReadErr == nil &&
			deliveredManifest != nil &&
			domain.Str(domain.Object(bundleRefInManifest), "id") == domain.Str(bundle, "id") &&
			domain.Str(domain.Object(bundleRefInManifest), "entity_type") == "ContextBundle" &&
			domain.Str(delivered, "task_id") == domain.Str(task, "id") &&
			domain.Str(delivered, "resume_instruction") != "" &&
			domain.Str(delivered, "resume_instruction") == domain.Str(manifest, "resume_instruction"),
			errText(manifestReadErr), domain.Str(domain.Object(bundleRefInManifest), "id"),
			domain.Str(delivered, "resume_instruction"))
		ok("CTX-MATERIALIZE-DELIVERED-MANIFEST-IS-WHAT-THE-SERVICE-RETURNED",
			manifestReadErr == nil && string(deliveredManifestRaw) == string(domain.Bytes(manifest)),
			len(deliveredManifestRaw), len(domain.Bytes(manifest)))
		deliveredBundleRaw, bundleReadErr := os.ReadFile(filepath.Join(ws, "bundle.json"))
		var deliveredBundle map[string]any
		if bundleReadErr == nil {
			if e := json.Unmarshal(deliveredBundleRaw, &deliveredBundle); e != nil {
				deliveredBundle = nil
			}
		}
		deliveredFrozen := domain.Object(deliveredBundle)
		deliveredSummary := domain.Str(deliveredFrozen, "summary")
		deliveredNextTask := domain.Str(continuationOf(deliveredFrozen), "next_task_id")
		// the worker's own copy has to be the sealed bundle, verifiable from the bytes it was handed
		ok("CTX-MATERIALIZE-DELIVERED-BUNDLE-IS-THE-SEALED-BUNDLE", bundleReadErr == nil &&
			deliveredBundle != nil && domain.Str(deliveredFrozen, "id") == domain.Str(bundle, "id") &&
			string(deliveredBundleRaw) == sealedBody &&
			domain.Str(deliveredFrozen, "receipt_hash") == domain.Receipt(deliveredFrozen) &&
			domain.Str(deliveredFrozen, "summary_hash") == domain.Digest([]byte(deliveredSummary)) &&
			deliveredNextTask == domain.Str(task, "id"),
			errText(bundleReadErr), len(deliveredBundleRaw), len(sealedBody), deliveredNextTask)
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

	// a worker without a grant on this project cannot read the context at all. Every branch of the
	// fixture setup records something: an id that is simply never emitted is an assertion the report
	// silently lost, which reads as coverage that does not exist.
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: "w0402-outsider",
		Roles: []string{"EXECUTOR"}, Grants: []domain.Grant{{ProjectID: h.betaProj}}}); e != nil {
		ok("CTX-FOREIGN-WORKER-CANNOT-READ-CONTEXT", false, "the outsider could not be provisioned: "+errText(e))
	} else if ot, terr := h.svc.IssueCredential(ctx, "w0402-outsider", 5*time.Minute); terr != nil {
		ok("CTX-FOREIGN-WORKER-CANNOT-READ-CONTEXT", false, "no credential for the outsider: "+errText(terr))
	} else {
		_, foreign := h.svc.GetTaskContext(ctx, ot, project, domain.Str(task, "id"))
		status, code := faultOf(foreign)
		ok("CTX-FOREIGN-WORKER-CANNOT-READ-CONTEXT", foreign != nil && status == 404 &&
			code == "NOT_FOUND", status, code, errText(foreign))
	}

	w0402Ctx = w0402Handles{token: token, project: project, base: base, taskID: domain.Str(task, "id"),
		art: art, bundle: bundle, task: task, state: state, contract: contract,
		decisions: proposedRefs, goalID: Str2(goal, "id"), reqID: Str2(accepted, "id"),
		decEffective: Str2(decisionB, "id"), decRetired: Str2(decisionA, "id")}

	// card step 4 is asserted by the CHG ids: a task with no frozen context is blocked
	// (CHG-MISSING-REQUIRED-CONTEXT-BLOCKS) and an applied change stales exactly the tasks in its
	// closure while leaving an unrelated task as it was (CHG-APPLIED-CHANGE-*). The one half still
	// open - an optional retrieval degrading instead of blocking - is declared as
	// CHG-OPTIONAL-RETRIEVAL-DEGRADES with the reason it is actually deferred, not glossed over.
	//
	// card step 3 is asserted too: the freeze writes explicit DEPENDS_ON links, drafts over an old
	// input or with an unfrozen check list are refused, and a conflict keeps both drafts and is
	// settled only by an accepted and applied change that touches the disputed scope. The proposal's
	// own impacted_refs and impact_link_ids arrays are asserted by CHG-PROPOSAL-NAMES-ITS-IMPACT on
	// the applied requirement change, whose closure this fixture really produces.
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
	// The card's step 3: the record names what it affects, deterministically, rather than leaving a
	// later reader to guess the closure. createChange fills both arrays itself through closure() at
	// changes.go:202-207 and checkChange re-verifies them at apply, so analyzeChangeImpact is not what
	// populates them and this is not another card's debt. On THIS proposal the honest expected value is
	// empty: the project governs no decision yet and the edit retires nothing, so the closure has no
	// root to walk. The non-empty case is asserted by value on the applied requirement change below,
	// where this fixture really produces a closure.
	ok("CHG-PROPOSAL-IMPACT-IS-COMPUTED-NOT-DEFERRED",
		Str2(proposalA, "status") == "IMPACT_ANALYZED" &&
			proposalA["impacted_refs"] != nil && proposalA["impact_link_ids"] != nil &&
			len(domain.Arr(proposalA, "impacted_refs")) == 0 &&
			len(domain.Arr(proposalA, "impact_link_ids")) == 0,
		Str2(proposalA, "status"), domain.Arr(proposalA, "impacted_refs"),
		domain.Arr(proposalA, "impact_link_ids"))

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
	independenceBody := ""
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
		indepCode, indepObj, indepBody := h.api(ctx, selfToken, "POST", base+"/acceptances", domain.ID(),
			tagOf(selfProposal), acceptBody(selfProposal, selfFrozen))
		independenceBody = indepBody
		ok("CHG-AUTHOR-CANNOT-ACCEPT-OWN-CHANGE", indepCode == 403 &&
			domain.Str(indepObj, "code") == "FORBIDDEN" &&
			strings.Contains(indepBody, "author cannot independently accept"),
			indepCode, domain.Str(indepObj, "code"), indepBody[:min(len(indepBody), 200)])
	}
	// A principal without VERIFIER is refused at the frozen role gate before any authorship or
	// independence rule is consulted, so this leg proves the role requirement and nothing else. It
	// used to be named as an independence assertion and to accept `403 || 409`, which let the role
	// gate and the open-conflict refusal both satisfy it - the twin of the trap the sibling leg above
	// was already fixed for. The status, the protocol code and the reason are now all pinned, and the
	// positive control that a VERIFIER-holding non-author is NOT refused here is
	// CHG-INDEPENDENT-ACCEPTANCE-COMPUTED below.
	roleCode, roleObj, roleBody := h.api(ctx, token, "POST", base+"/acceptances", domain.ID(),
		tagOf(proposalA), acceptBody(proposalA, frozen))
	ok("CHG-ACCEPTANCE-REQUIRES-THE-VERIFIER-ROLE", roleCode == 403 &&
		domain.Str(roleObj, "code") == "FORBIDDEN" &&
		strings.Contains(roleBody, "role not authorized"),
		roleCode, domain.Str(roleObj, "code"), roleBody[:min(len(roleBody), 200)])
	// The two refusals must be distinguishable, and the role claim is read from the authority table
	// rather than restated from the fixture that provisioned it.
	rolesOf := func(principal string) string {
		var roles string
		if e := h.db.QueryRowContext(ctx,
			`SELECT roles FROM auth_principals WHERE id=? AND revoked=0`, principal).Scan(&roles); e != nil {
			return "unavailable: " + errText(e)
		}
		return roles
	}
	plannerRoles, selfRoles := rolesOf("w0402-planner"), rolesOf("w0402-selfauthor")
	ok("CHG-ROLE-REFUSAL-IS-NOT-THE-INDEPENDENCE-REFUSAL",
		!strings.Contains(plannerRoles, "VERIFIER") && strings.Contains(selfRoles, "VERIFIER") &&
			strings.Contains(roleBody, "role not authorized") &&
			strings.Contains(independenceBody, "author cannot independently accept") &&
			!strings.Contains(independenceBody, "role not authorized"),
		plannerRoles, selfRoles, roleBody[:min(len(roleBody), 120)],
		independenceBody[:min(len(independenceBody), 120)])

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
			containsRefID(domain.Arr(refrozen, "latest_decision_refs"), w0402Ctx.decEffective),
			domain.Arr(refrozen, "latest_decision_refs"))
		ok("CHG-REFREEZE-KEEPS-RETIRED-DECISION-AS-HISTORY", w0402Ctx.decRetired != "" &&
			strings.Contains(summary, "historical_decision_refs") &&
			strings.Contains(summary, w0402Ctx.decRetired), summary[:min(len(summary), 260)])
		// the same, by value on the continuation a new session actually resumes from: the effective
		// decision is current, the superseded one is history, and neither is merely mentioned
		refrozenContinuation := continuationOf(refrozen)
		ok("CHG-REFREEZE-CONTINUATION-CARRIES-EFFECTIVE-AND-RETIRED",
			refrozenContinuation != nil &&
				containsRefID(domain.Arr(refrozenContinuation, "current_decision_refs"), w0402Ctx.decEffective) &&
				!containsRefID(domain.Arr(refrozenContinuation, "current_decision_refs"), w0402Ctx.decRetired) &&
				containsRefID(domain.Arr(refrozenContinuation, "historical_decision_refs"), w0402Ctx.decRetired) &&
				domain.Str(refrozenContinuation, "next_task_id") == w0402Ctx.taskID,
			refIDsOf(domain.Arr(refrozenContinuation, "current_decision_refs")),
			refIDsOf(domain.Arr(refrozenContinuation, "historical_decision_refs")))
		ok("CHG-REFREEZE-IS-PINNED-TO-THE-STATE-IT-READ",
			refrozen["project_state_revision"] != nil &&
				domain.Hash(refrozen["project_state_revision"]) == domain.Hash(movedState["revision"]) &&
				len(domain.Arr(refrozen, "unresolved_items")) == 0,
			refrozen["project_state_revision"], movedState["revision"],
			domain.Arr(refrozen, "unresolved_items"))
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
	// An applied change with no relation to the conflict below, so the relation check has something
	// real to refuse. It revises a requirement that no task, decision or bundle references, which keeps
	// it a clean control rather than a second source of side effects. It has to be applied before the
	// conflict exists, because an OPEN non-decision conflict refuses every later proposal - and it
	// cannot be the requirement revision used further down, because revising THAT requirement makes the
	// decisions pinning it non-effective and the second draft proposes exactly such a decision.
	_, unrelTag := h.liveState(ctx, token, base)
	unrelReqCode, unrelReq, unrelReqBody := h.api(ctx, token, "POST", base+"/requirements", domain.ID(),
		unrelTag, domain.Object{
			"requirement_key": "REQ-W0402-UNRELATED", "text": "a requirement nothing in this fixture depends on",
			"basis": "USER_STATED", "source_refs": domain.Empty(),
			"rationale":            "control for the conflict relation check",
			"supersedes_id":        nil,
			"acceptance_check_ids": domain.Empty()})
	ok("CHG-UNRELATED-REQUIREMENT-CREATED", unrelReqCode == 201 && Str2(unrelReq, "id") != "",
		unrelReqCode, unrelReqBody[:min(len(unrelReqBody), 200)])
	_, unrelReqNow, _ := h.api(ctx, token, "GET", base+"/requirements/"+Str2(unrelReq, "id"), "", "", nil)
	unrelPayload := []byte(`"revised by an unrelated applied change"`)
	unrelUpCode, unrelUp, unrelUpBody := h.api(ctx, token, "POST", base+"/content", domain.ID(), "",
		unrelPayload)
	ok("CHG-UNRELATED-CONTENT-UPLOADED", unrelUpCode == 201, unrelUpCode,
		unrelUpBody[:min(len(unrelUpBody), 200)])
	_, unrelArtTag := h.liveState(ctx, token, base)
	unrelArtCode, unrelArt, unrelArtBody := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(),
		unrelArtTag, domain.Object{
			"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
			"content_hash": unrelUp["content_hash"], "storage_key": unrelUp["storage_key"],
			"media_type": "application/json", "byte_size": len(unrelPayload),
			"input_refs": domain.Empty(), "source_refs": domain.Empty(),
			"produced_by": "w0402-planner", "access_class": "PROJECT"})
	ok("CHG-UNRELATED-ARTIFACT-SEALED", unrelArtCode == 201, unrelArtCode,
		unrelArtBody[:min(len(unrelArtBody), 200)])
	unrelatedApplied, unrelatedWhy := applyChange(domain.Ref(unrelReqNow, "Requirement"), "text",
		unrelArt, "w0402 unrelated revision")
	ok("CHG-UNRELATED-CHANGE-APPLIED", unrelatedApplied != nil &&
		Str2(unrelatedApplied, "status") == "APPLIED", unrelatedWhy)
	// The control has to stay a control: an empty impact closure here is what makes the refusal below
	// about the relation and not about some other task this change happened to invalidate.
	ok("CHG-UNRELATED-CHANGE-STALES-NOTHING-HERE", unrelatedApplied != nil &&
		len(domain.Arr(unrelatedApplied, "impacted_refs")) == 0 &&
		len(domain.Arr(unrelatedApplied, "impact_link_ids")) == 0,
		domain.Arr(unrelatedApplied, "impacted_refs"),
		domain.Arr(unrelatedApplied, "impact_link_ids"))

	// facts has to be asserted by content, not by presence. A bootstrapped profile carries no facts,
	// so "the bundle carries the profile's facts" is indistinguishable from "the bundle carries
	// nothing" until the fixture gives the profile a fact and then requires the freeze to hand that
	// exact fact to a new session.
	const factText = "a fact the operator stated and the freeze must carry"
	factsPayload := []byte(`[{"text":"` + factText +
		`","basis":"USER_STATED","source_refs":[],"validity":"CURRENT"}]`)
	_, profileNow, profileBody := h.api(ctx, token, "GET", base+"/profile", "", "", nil)
	ok("CHG-PROFILE-READABLE-FOR-FACTS", Str2(profileNow, "id") != "",
		profileBody[:min(len(profileBody), 160)])
	factsUpCode, factsUp, factsUpBody := h.api(ctx, token, "POST", base+"/content", domain.ID(), "",
		factsPayload)
	ok("CHG-FACTS-CONTENT-UPLOADED", factsUpCode == 201, factsUpCode,
		factsUpBody[:min(len(factsUpBody), 160)])
	_, factsArtTag := h.liveState(ctx, token, base)
	factsArtCode, factsArt, factsArtBody := h.api(ctx, token, "POST", base+"/artifacts", domain.ID(),
		factsArtTag, domain.Object{
			"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE",
			"content_hash": factsUp["content_hash"], "storage_key": factsUp["storage_key"],
			"media_type": "application/json", "byte_size": len(factsPayload),
			"input_refs": domain.Empty(), "source_refs": domain.Empty(),
			"produced_by": "w0402-planner", "access_class": "PROJECT"})
	ok("CHG-FACTS-ARTIFACT-SEALED", factsArtCode == 201, factsArtCode,
		factsArtBody[:min(len(factsArtBody), 200)])
	factsApplied, factsWhy := applyChange(domain.Ref(profileNow, "ProjectProfile"), "facts", factsArt,
		"w0402 profile facts")
	ok("CHG-PROFILE-FACTS-CHANGED", factsApplied != nil && Str2(factsApplied, "status") == "APPLIED",
		factsWhy)
	factsState, factsTag := h.liveState(ctx, token, base)
	factsFreezeCode, factsBundle, factsFreezeBody := h.api(ctx, token, "POST", base+"/context-bundles",
		domain.ID(), factsTag, domain.Object{"task_id": Str2(bare, "id"),
			"expected_project_state_revision": factsState["revision"]})
	frozenFacts := domain.Arr(factsBundle, "facts")
	exactFact := false
	if len(frozenFacts) == 1 {
		if f, isFact := frozenFacts[0].(map[string]any); isFact {
			fact := domain.Object(f)
			exactFact = domain.Str(fact, "text") == factText &&
				domain.Str(fact, "basis") == "USER_STATED" &&
				domain.Str(fact, "validity") == "CURRENT"
		}
	}
	ok("CTX-FREEZE-CARRIES-THE-PROFILE-FACTS-BY-CONTENT", factsFreezeCode == 201 && exactFact &&
		strings.Contains(string(domain.Bytes(factsBundle)), factText),
		factsFreezeCode, frozenFacts, factsFreezeBody[:min(len(factsFreezeBody), 200)])

	// two drafts over the same field, then a conflict naming both: neither draft may move
	code, proposalB, body := proposal(nil, nil, supportedChangeChecks)
	ok("CHG-SECOND-PROPOSAL-CREATED", code == 201, code, body[:min(len(body), 300)])
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
		conflictID := Str2(conflict, "id")
		// the conflict is now on the project's blocking index, which is what a freeze reports from
		blockedState, _ := h.liveState(ctx, token, base)
		ok("CHG-OPEN-CONFLICT-BLOCKS-THE-PROJECT",
			containsID(domain.Arr(blockedState, "blocking_conflict_ids"), conflictID),
			domain.Arr(blockedState, "blocking_conflict_ids"), conflictID)

		// frozen while it is open, the context must tell a new session exactly which conflict is open
		openState, openTag := h.liveState(ctx, token, base)
		openCode, openBundle, openBody := h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(),
			openTag, domain.Object{"task_id": Str2(bare, "id"),
				"expected_project_state_revision": openState["revision"]})
		expectedOpen := domain.Empty()
		expectedOpen = append(expectedOpen, "Open conflict: "+conflictID)
		ok("CTX-FREEZE-NAMES-THE-OPEN-CONFLICT", openCode == 201 &&
			len(domain.Arr(openBundle, "unresolved_items")) == 1 &&
			domain.Hash(domain.Arr(openBundle, "unresolved_items")) == domain.Hash(expectedOpen),
			openCode, domain.Arr(openBundle, "unresolved_items"), expectedOpen,
			openBody[:min(len(openBody), 200)])

		_, aAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
		_, bAfter, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
		ok("CHG-CONFLICT-DOES-NOT-OVERWRITE-A-DRAFT",
			string(domain.Bytes(aAfter)) == beforeA && string(domain.Bytes(bAfter)) == beforeB,
			Str2(proposalA, "id"), Str2(proposalB, "id"))

		// while the conflict is open, the conflicted draft cannot be independently accepted
		code, _, body = h.api(ctx, verifierToken, "POST", base+"/acceptances", domain.ID(),
			tagOf(proposalA), acceptBody(proposalA, frozen))
		ok("CHG-CONFLICTED-DRAFT-IS-NOT-ACCEPTABLE", code == 409, code, body[:min(len(body), 200)])

		// Being applied is not by itself authority to settle this conflict: the settling change has to
		// touch the disputed scope. The requirement revision above is applied and unrelated - it edits a
		// Requirement's text while this conflict is over two drafts of ProjectState.current_decision_refs
		// - and accepting it as the resolution is what recorded a relation that did not exist.
		if unrelatedApplied == nil {
			ok("CHG-CONFLICT-IS-NOT-SETTLED-BY-AN-UNRELATED-CHANGE", false,
				"no unrelated applied change was available to test against: "+unrelatedWhy)
			ok("CHG-REFUSED-RESOLUTION-LEAVES-THE-CONFLICT-OPEN", false, "not reached")
		} else {
			unrelatedCode, unrelatedObj, unrelatedBody := h.api(ctx, token, "POST",
				base+"/conflicts/"+conflictID+"/resolve", domain.ID(), tagOf(conflict),
				domain.Object{"resolution_proposal_id": Str2(unrelatedApplied, "id"),
					"reason": "an applied change with nothing to do with the disputed field"})
			ok("CHG-CONFLICT-IS-NOT-SETTLED-BY-AN-UNRELATED-CHANGE", unrelatedCode == 409 &&
				domain.Str(unrelatedObj, "code") == "STATE_CONFLICT" &&
				strings.Contains(unrelatedBody, "does not touch the disputed scope"),
				unrelatedCode, domain.Str(unrelatedObj, "code"),
				unrelatedBody[:min(len(unrelatedBody), 200)])
			_, stillOpen, _ := h.api(ctx, token, "GET", base+"/conflicts/"+conflictID, "", "", nil)
			ok("CHG-REFUSED-RESOLUTION-LEAVES-THE-CONFLICT-OPEN",
				Str2(stillOpen, "status") == "OPEN" && stillOpen["resolution_proposal_id"] == nil,
				Str2(stillOpen, "status"), stillOpen["resolution_proposal_id"])
		}

		// Being a party to the dispute is not enough either: the settling change has to have been
		// independently accepted and applied. proposalB is one of the two subjects and is still a draft.
		draftCode, draftObj, draftBody := h.api(ctx, token, "POST",
			base+"/conflicts/"+conflictID+"/resolve", domain.ID(), tagOf(conflict),
			domain.Object{"resolution_proposal_id": Str2(proposalB, "id"),
				"reason": "a party to the conflict that was never accepted and applied"})
		ok("CHG-UNAPPLIED-PARTY-CANNOT-SETTLE-THE-CONFLICT", draftCode == 409 &&
			domain.Str(draftObj, "code") == "STATE_CONFLICT" &&
			strings.Contains(draftBody, "has not been accepted and applied"),
			draftCode, domain.Str(draftObj, "code"), draftBody[:min(len(draftBody), 200)])

		// the applied change that edits the same disputed field is what settles it
		code, resolved, body := h.api(ctx, token, "POST",
			base+"/conflicts/"+conflictID+"/resolve", domain.ID(), tagOf(conflict),
			domain.Object{"resolution_proposal_id": Str2(proposalC, "id"),
				"reason": "the independently accepted change settled the field"})
		ok("CHG-CONFLICT-RESOLVED-BY-AN-APPLIED-CHANGE", code == 200 &&
			Str2(resolved, "status") == "RESOLVED" &&
			Str2(resolved, "resolution_proposal_id") == Str2(proposalC, "id"), code,
			Str2(resolved, "status"), body[:min(len(body), 200)])

		// a settled conflict cannot be settled again
		_, conflictNow, _ := h.api(ctx, token, "GET", base+"/conflicts/"+conflictID, "", "", nil)
		againCode, againObj, againBody := h.api(ctx, token, "POST",
			base+"/conflicts/"+conflictID+"/resolve", domain.ID(), tagOf(conflictNow),
			domain.Object{"resolution_proposal_id": Str2(proposalC, "id"),
				"reason": "settling the same conflict a second time"})
		ok("CHG-RESOLVED-CONFLICT-CANNOT-BE-SETTLED-AGAIN", againCode == 409 &&
			domain.Str(againObj, "code") == "STATE_CONFLICT" &&
			strings.Contains(againBody, "already RESOLVED"),
			againCode, domain.Str(againObj, "code"), againBody[:min(len(againBody), 200)])

		// settling it must also stop it blocking the project. This is the index createContext reads to
		// build unresolved_items, so leaving the settled id behind made every later freeze tell a new
		// session that a closed conflict was still open.
		afterState, _ := h.liveState(ctx, token, base)
		ok("CHG-RESOLUTION-CLEARS-THE-BLOCKING-INDEX",
			!containsID(domain.Arr(afterState, "blocking_conflict_ids"), conflictID),
			domain.Arr(afterState, "blocking_conflict_ids"), conflictID)
		clearedState, clearedTag := h.liveState(ctx, token, base)
		clearedCode, clearedBundle, clearedBody := h.api(ctx, token, "POST", base+"/context-bundles",
			domain.ID(), clearedTag, domain.Object{"task_id": Str2(bare, "id"),
				"expected_project_state_revision": clearedState["revision"]})
		clearedItems := domain.Arr(clearedBundle, "unresolved_items")
		ok("CTX-FREEZE-AFTER-RESOLUTION-REPORTS-NO-OPEN-CONFLICT", clearedCode == 201 &&
			len(clearedItems) == 0 &&
			!strings.Contains(string(domain.Bytes(clearedBundle)), conflictID),
			clearedCode, clearedItems, clearedBody[:min(len(clearedBody), 200)])

		_, aFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalA, "id"), "", "", nil)
		_, bFinal, _ := h.api(ctx, token, "GET", base+"/change-proposals/"+Str2(proposalB, "id"), "", "", nil)
		// settling the conflict rewrites neither draft
		ok("CHG-RESOLUTION-KEEPS-BOTH-DRAFTS",
			string(domain.Bytes(aFinal)) == beforeA && string(domain.Bytes(bFinal)) == beforeB,
			Str2(proposalA, "id"), Str2(proposalB, "id"))
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

	// Card step 3, first sentence: the change record names what it affects. Both arrays are read off
	// the applied proposal itself, every impact link id is resolved back through the API, and the
	// closure has to reach beyond the edited entity - an echo of the edit target is not a closure.
	impacted := domain.Arr(applied2, "impacted_refs")
	impactLinkIDs := domain.Arr(applied2, "impact_link_ids")
	shapedImpact, kinds := 0, map[string]int{}
	editedID := Str2(reqNow, "id")
	beyondTarget := 0
	for _, v := range impacted {
		r, isRef := v.(map[string]any)
		if !isRef {
			continue
		}
		ref := domain.Object(r)
		if Str2(ref, "entity_type") != "" && Str2(ref, "id") != "" && ref["revision"] != nil {
			shapedImpact++
		}
		kinds[Str2(ref, "entity_type")]++
		if Str2(ref, "id") != editedID {
			beyondTarget++
		}
	}
	ok("CHG-PROPOSAL-NAMES-ITS-IMPACT", len(impacted) >= 1 && shapedImpact == len(impacted) &&
		len(impactLinkIDs) >= 1 && beyondTarget >= 1 && kinds["Task"] >= 1 &&
		kinds["DecisionReceipt"] >= 1,
		len(impacted), shapedImpact, len(impactLinkIDs), beyondTarget, kinds, why)
	resolvedLinks, activeLinks, dependsLinks := 0, 0, 0
	for _, v := range impactLinkIDs {
		linkCode, link, _ := h.api(ctx, token, "GET", base+"/impact-links/"+fmt.Sprint(v), "", "", nil)
		if linkCode == 200 && Str2(link, "id") == fmt.Sprint(v) {
			resolvedLinks++
		}
		if Str2(link, "status") == "ACTIVE" {
			activeLinks++
		}
		if Str2(link, "relation") == "DEPENDS_ON" {
			dependsLinks++
		}
	}
	ok("CHG-IMPACT-LINK-IDS-RESOLVE-TO-ACTIVE-DEPENDENCIES",
		len(impactLinkIDs) >= 1 && resolvedLinks == len(impactLinkIDs) &&
			activeLinks == resolvedLinks && dependsLinks == resolvedLinks,
		len(impactLinkIDs), resolvedLinks, activeLinks, dependsLinks)

	// unfinished_commitments has to carry the commitment, not merely the key: schema validation
	// already guarantees the key exists, so a presence check proved nothing. A task that depends on a
	// task which is not ACCEPTED must freeze the exact sentence a new session needs. The goal is
	// re-read for its precondition here, because every accepted write above moved it and a stale
	// If-Match would make this a fixture failure rather than a property under test.
	_, goalForDependent, _ := h.api(ctx, token, "GET", base+"/goals/"+w0402Ctx.goalID, "", "", nil)
	code, dependent, depBody := h.api(ctx, token, "POST", base+"/tasks", domain.ID(), tagOf(goalForDependent), domain.Object{
		"goal_id": goalID, "title": "w0402 dependent task", "task_type": "construction",
		"stage": "verification", "dependency_task_ids": []any{Str2(bare, "id")},
		"requirement_refs":    domain.Empty(),
		"input_refs":          domain.Empty(),
		"acceptance_contract": w0402Ctx.contract,
		"origin_problem_id":   "p-w0402", "candidate_id": "c-w0402",
		"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 3, "max_parallel_runs": 1,
			"stop_conditions": []any{"no effective progress"}}})
	ok("CHG-DEPENDENT-TASK-CREATED", code == 201 && Str2(dependent, "id") != "", code,
		depBody[:min(len(depBody), 200)])
	if code == 201 {
		depState, depTag := h.liveState(ctx, token, base)
		depCode, depBundle, depFreezeBody := h.api(ctx, token, "POST", base+"/context-bundles", domain.ID(),
			depTag, domain.Object{"task_id": Str2(dependent, "id"),
				"expected_project_state_revision": depState["revision"]})
		expectedCommitment := "Dependency " + Str2(bare, "id") + " remains " + Str2(laterTask, "status")
		frozenCommitments := domain.Arr(depBundle, "unfinished_commitments")
		ok("CTX-UNFINISHED-COMMITMENTS-NAME-THE-BLOCKING-DEPENDENCY", depCode == 201 &&
			len(frozenCommitments) == 1 && fmt.Sprint(frozenCommitments[0]) == expectedCommitment,
			depCode, frozenCommitments, expectedCommitment, depFreezeBody[:min(len(depFreezeBody), 200)])
	}

	skip("CHG-OPTIONAL-RETRIEVAL-DEGRADES", "deferred on ownership, not on difficulty: the operation whose "+
		"degradation this names is searchEvidence, which the frozen ownership map in internal/domain/contracts.go "+
		"assigns to W09, and driving its warning branch needs a registered local retrieval root plus a "+
		"SOURCE_SNAPSHOT artifact - neither of which this card's fixture creates. The earlier wording blamed a "+
		"missing FTS fixture and implied the branch was nearly reachable from here; it is not. What this card "+
		"does cover is the freeze-side analogue: currentAuthorizedSnapshots skips a snapshot it cannot resolve "+
		"and createContext reports an unresolvable governing decision in unresolved_items instead of failing, "+
		"asserted by CTX-AUTHORIZED-SNAPSHOTS-COME-FROM-THE-PROFILE-INDEX and "+
		"CTX-UNRESOLVED-ITEMS-MATCH-THE-LIVE-BLOCKING-INDEX.")
}

// containsID reports whether one id appears in a stored id array.
func containsID(values []any, want string) bool {
	for _, v := range values {
		if fmt.Sprint(v) == want {
			return true
		}
	}
	return false
}

// containsRefID reports whether one id appears among a set of version references.
func containsRefID(values []any, want string) bool {
	for _, v := range values {
		if r, isRef := v.(map[string]any); isRef && domain.Str(domain.Object(r), "id") == want {
			return true
		}
	}
	return false
}

// refIDsOf flattens version references to their ids, for a failure detail that names what was there.
func refIDsOf(values []any) []string {
	out := []string{}
	for _, v := range values {
		if r, isRef := v.(map[string]any); isRef {
			out = append(out, domain.Str(domain.Object(r), "id"))
		}
	}
	return out
}

// continuationOf parses the frozen continuation back out of a bundle summary. It is the answer to
// "what is the accurate next step", so it is read as a value rather than searched for as a substring.
const continuationMarker = "\nContinuation: "

func continuationOf(bundle domain.Object) domain.Object {
	summary := domain.Str(bundle, "summary")
	if !strings.Contains(summary, continuationMarker) {
		return nil
	}
	var parsed map[string]any
	tail := summary[strings.Index(summary, continuationMarker)+len(continuationMarker):]
	if e := json.Unmarshal([]byte(tail), &parsed); e != nil {
		return nil
	}
	return domain.Object(parsed)
}

// w0402Roster is every assertion id
// the two phases declare. It is the floor this report did not have: an id that is
// declared in the source but never emitted - because a fixture setup failed, or a phase
// returned early on its first refusal - used to vanish from the report without a failure,
// so the run stayed green while covering less than it claimed. w0402Reconcile turns any
// such loss into a named failure, and also fails if the run emits an id this list does
// not declare, so the floor cannot drift away from the source it is meant to bound.
var w0402Roster = []string{
	// contextPhase
	"CTX-AUTHORIZED-SNAPSHOTS-COME-FROM-THE-PROFILE-INDEX",
	"CTX-BUNDLE-CARRIES-ALL-REQUIRED-FIELDS",
	"CTX-BUNDLE-CREATED",
	"CTX-BUNDLE-DECISION-SCOPE",
	"CTX-BUNDLE-DECISIONS-FOLLOW-THE-APPLIED-STATE",
	"CTX-BUNDLE-FROZEN-FROM-LIVE-STATE",
	"CTX-BUNDLE-HASHES-POPULATED",
	"CTX-BUNDLE-KEEPS-USER-WORDS-VERBATIM",
	"CTX-BUNDLE-REPLAY-SAME-IDENTITY",
	"CTX-BUNDLE-REVISION-IS-ONE",
	"CTX-BUNDLE-SURVIVES-A-REFUSED-TAMPERING",
	"CTX-BUNDLE-VERSION-VECTOR-BOUNDED",
	"CTX-CONTEXT-READABLE-AGAIN-AFTER-RESTORE",
	"CTX-CONTEXT-READABLE-BY-WORKER",
	"CTX-CONTINUATION-CARRIES-THE-ACCEPTANCE-CONTRACT",
	"CTX-CONTINUATION-CARRIES-THE-OPERATORS-OWN-INTENT",
	"CTX-DECISION-RECORDED",
	"CTX-FACTS-COME-FROM-THE-LIVE-PROFILE",
	"CTX-FOREIGN-WORKER-CANNOT-READ-CONTEXT",
	"CTX-FREEZE-AFTER-RESOLUTION-REPORTS-NO-OPEN-CONFLICT",
	"CTX-FREEZE-CARRIES-THE-PROFILE-FACTS-BY-CONTENT",
	"CTX-FREEZE-NAMES-THE-ACCURATE-NEXT-STEP",
	"CTX-FREEZE-NAMES-THE-OPEN-CONFLICT",
	"CTX-GOAL-CARRIES-ORIGINAL-INTENT",
	"CTX-INPUT-ARTIFACT-SEALED",
	"CTX-INPUT-CONTENT-UPLOADED",
	"CTX-MATERIALIZE-BYTES-MATCH-MANIFEST-HASHES",
	"CTX-MATERIALIZE-DELIVERED-BUNDLE-IS-THE-SEALED-BUNDLE",
	"CTX-MATERIALIZE-DELIVERED-MANIFEST-IS-WHAT-THE-SERVICE-RETURNED",
	"CTX-MATERIALIZE-DELIVERS-BUNDLE-AND-MANIFEST",
	"CTX-MATERIALIZE-EMITS-A-MANIFEST",
	"CTX-MATERIALIZE-ENTRIES-RESOLVE-UNDER-WORKSPACE",
	"CTX-MATERIALIZE-INPUT-IS-THE-SEALED-BYTES-READ-ONLY",
	"CTX-MATERIALIZE-INTO-FRESH-DIRECTORY",
	"CTX-MATERIALIZE-MANIFEST-NAMES-BUNDLE-AND-RESUME",
	"CTX-MATERIALIZE-REFUSES-EXISTING-DIRECTORY",
	"CTX-MATERIALIZE-WORKSPACE-IS-DESTINATION-NOT-CWD",
	"CTX-PLANNER-CREDENTIAL",
	"CTX-PLANNER-PROVISIONED",
	"CTX-POLICY-REVISION-MATCHES-THE-LIVE-STATE",
	"CTX-PROJECT-AVAILABLE",
	"CTX-PROJECT-STATE-READABLE",
	"CTX-PROPOSAL-VALUE-ENCODABLE",
	"CTX-REQUIREMENT-ACCEPTED",
	"CTX-REQUIREMENT-CREATED",
	"CTX-RUBRIC-ARTIFACT-SEALED",
	"CTX-RUBRIC-CONTENT-UPLOADED",
	"CTX-SEALED-BUNDLE-BYTES-CAPTURED",
	"CTX-SERVICE-REFUSES-A-TAMPER-THAT-LEAVES-THE-SUMMARY-ALONE",
	"CTX-SERVICE-REFUSES-A-TAMPERED-BUNDLE",
	"CTX-STALE-CAS-ISOLATED-FROM-PRECONDITION",
	"CTX-STALE-EXPECTED-REVISION-REJECTED",
	"CTX-STALE-PRECONDITION-REJECTED",
	"CTX-STORAGE-IMMUTABILITY-TRIGGER-RESTORED",
	"CTX-STORAGE-REFUSES-TO-REWRITE-A-SEALED-BUNDLE",
	"CTX-SUPERSEDING-DECISION-RECORDED",
	"CTX-TASK-CREATED-UNBUNDLED",
	"CTX-TASK-POINTS-AT-BUNDLE",
	"CTX-UNFINISHED-COMMITMENTS-NAME-THE-BLOCKING-DEPENDENCY",
	"CTX-UNRESOLVED-ITEMS-MATCH-THE-LIVE-BLOCKING-INDEX",
	// changePhase
	"CHG-ACCEPTANCE-REQUIRES-THE-VERIFIER-ROLE",
	"CHG-APPLIED-CHANGE-LEAVES-THE-UNRELATED-TASK-ALONE",
	"CHG-APPLIED-CHANGE-STALES-THE-DEPENDENT-TASK",
	"CHG-APPLIED-CHANGE-STATES-ADVANCE",
	"CHG-APPLIED-DECISION-LANDS-IN-THE-STATE",
	"CHG-APPLY-MOVES-THE-PROJECT-STATE",
	"CHG-AUTHOR-CANNOT-ACCEPT-OWN-CHANGE",
	"CHG-CLEAN-CONTRACT-HASH-FREEZABLE",
	"CHG-CLEAN-PROPOSAL-CREATED",
	"CHG-CONFLICT-DOES-NOT-OVERWRITE-A-DRAFT",
	"CHG-CONFLICT-IS-NOT-SETTLED-BY-AN-UNRELATED-CHANGE",
	"CHG-CONFLICT-KEEPS-BOTH-SIDES",
	"CHG-CONFLICT-RESOLVED-BY-AN-APPLIED-CHANGE",
	"CHG-CONFLICTED-DRAFT-IS-NOT-ACCEPTABLE",
	"CHG-CONTEXT-PHASE-RAN-FIRST",
	"CHG-CONTRACT-HASH-FREEZABLE",
	"CHG-DEPENDENT-TASK-CREATED",
	"CHG-FACTS-ARTIFACT-SEALED",
	"CHG-FACTS-CONTENT-UPLOADED",
	"CHG-IMPACT-LINK-BASIS-IS-DETERMINISTIC",
	"CHG-IMPACT-LINK-IDS-RESOLVE-TO-ACTIVE-DEPENDENCIES",
	"CHG-IMPACT-LINKS-ARE-EXPLICIT",
	"CHG-IMPACT-LINKS-EVIDENCE-POINTS-AT-THE-FREEZE",
	"CHG-INDEPENDENT-ACCEPTANCE-COMPUTED",
	"CHG-MISSING-REQUIRED-CONTEXT-BLOCKS",
	"CHG-OPEN-CONFLICT-BLOCKS-THE-PROJECT",
	"CHG-OPTIONAL-RETRIEVAL-DEGRADES",
	"CHG-PROFILE-FACTS-CHANGED",
	"CHG-PROFILE-READABLE-FOR-FACTS",
	"CHG-PROPOSAL-CREATED",
	"CHG-PROPOSAL-IMPACT-IS-COMPUTED-NOT-DEFERRED",
	"CHG-PROPOSAL-NAMES-ITS-IMPACT",
	"CHG-PROPOSAL-RECORDS-BASE-STATE",
	"CHG-REFREEZE-AFTER-APPLY-ACCEPTED",
	"CHG-REFREEZE-CARRIES-EFFECTIVE-DECISION",
	"CHG-REFREEZE-CONTINUATION-CARRIES-EFFECTIVE-AND-RETIRED",
	"CHG-REFREEZE-IS-PINNED-TO-THE-STATE-IT-READ",
	"CHG-REFREEZE-KEEPS-RETIRED-DECISION-AS-HISTORY",
	"CHG-REFUSED-RESOLUTION-LEAVES-THE-CONFLICT-OPEN",
	"CHG-REQUIREMENT-CHANGE-APPLIED",
	"CHG-REQUIREMENT-READABLE-FOR-EDIT",
	"CHG-RESOLUTION-CLEARS-THE-BLOCKING-INDEX",
	"CHG-RESOLUTION-KEEPS-BOTH-DRAFTS",
	"CHG-RESOLVED-CONFLICT-CANNOT-BE-SETTLED-AGAIN",
	"CHG-REVISION-ARTIFACT-SEALED",
	"CHG-REVISION-CONTENT-UPLOADED",
	"CHG-ROLE-REFUSAL-IS-NOT-THE-INDEPENDENCE-REFUSAL",
	"CHG-SECOND-PROPOSAL-CREATED",
	"CHG-SECOND-TASK-WAITING",
	"CHG-SELF-AUTHOR-CONTRACT-FREEZABLE",
	"CHG-SELF-AUTHOR-CREDENTIAL",
	"CHG-SELF-AUTHOR-PROPOSAL-CREATED",
	"CHG-SELF-AUTHOR-PROVISIONED",
	"CHG-STALE-BASE-STATE-REJECTED",
	"CHG-STALE-EDIT-TARGET-REJECTED",
	"CHG-UNAPPLIED-PARTY-CANNOT-SETTLE-THE-CONFLICT",
	"CHG-UNFROZEN-CHECKS-REJECTED",
	"CHG-UNRELATED-ARTIFACT-SEALED",
	"CHG-UNRELATED-CHANGE-APPLIED",
	"CHG-UNRELATED-CHANGE-STALES-NOTHING-HERE",
	"CHG-UNRELATED-CONTENT-UPLOADED",
	"CHG-UNRELATED-REQUIREMENT-CREATED",
	"CHG-VERIFIER-CREDENTIAL",
	"CHG-VERIFIER-PROVISIONED",
}

// w0402Reconcile proves no declared assertion went unaccounted for, in both directions.
func (h *harness) w0402Reconcile(ctx context.Context) {
	accounted := map[string]bool{}
	for _, id := range ids {
		accounted[id] = true
	}
	for _, f := range failures {
		accounted[f["id"]] = true
	}
	for _, n := range notVerified {
		if i := strings.Index(n, ":"); i > 0 {
			accounted[strings.TrimSpace(n[:i])] = true
		}
	}
	lost := []string{}
	for _, id := range w0402Roster {
		if !accounted[id] {
			lost = append(lost, id)
		}
	}
	ok("W0402-NO-DECLARED-ASSERTION-WAS-SILENTLY-DROPPED", len(lost) == 0,
		len(w0402Roster), lost)
	declared := map[string]bool{}
	for _, id := range w0402Roster {
		declared[id] = true
	}
	undeclared := []string{}
	for _, id := range ids {
		if strings.HasPrefix(id, "CTX-") || strings.HasPrefix(id, "CHG-") {
			if !declared[id] {
				undeclared = append(undeclared, id)
			}
		}
	}
	ok("W0402-ROSTER-MATCHES-THE-EMITTED-IDS", len(undeclared) == 0, undeclared)
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
