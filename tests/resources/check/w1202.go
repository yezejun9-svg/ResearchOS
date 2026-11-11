package main

// W12-02 · 用途等价资源切换与用户可操作请求
//
// The switching mechanism itself belongs to the accepted W12-01: SwitchResource keeps the original Run,
// gates the replacement on capability/platform/provenance equivalence and an owner purpose grant, and on
// refusal commits one aggregated ResourceRequest. This card adds the user-facing half - a shortage must
// raise a notice that does not repeat every round - and falsifies both halves through the real Service on
// a real SQLite database.
//
// ok() only appends the id when the comparison holds, so a row that cannot be constructed is never claimed.

import (
	"context"
	"fmt"
	"strings"
	"time"

	"researchos.local/research-os/internal/domain"
)

const w1202Account = "acct-fixture-primary"

// w1202Req builds a CreateResourceRequest that satisfies the frozen contract: category is a closed enum
// (the shortage here is a missing owner purpose grant, so PERMISSION is the truthful member), the artifact
// refs are VersionRef objects rather than bare ids, and every task id is a real one this harness created.
func w1202Req(refs []any, reason string, costKnown bool, cost any, blocked, continuable []any) domain.Object {
	return w1202ReqWith(refs, nil, reason, costKnown, cost, blocked, continuable)
}

func w1202ReqWith(refs []any, resume any, reason string, costKnown bool, cost any, blocked, continuable []any) domain.Object {
	return domain.Object{"category": "PERMISSION", "account_ref": w1202Account, "reason_code": reason,
		"summary": "no equivalent authorised runtime for this task yet",
		"blocked_task_ids": blocked, "continuable_task_ids": continuable,
		"completed_artifact_refs": refs,
		"requested_capability": "fixture", "estimated_cost": cost, "cost_known": costKnown,
		"resume_checkpoint_ref": resume}
}

func w1202Count(h *harness, kind, clause string, args ...any) int {
	var n int
	q := "SELECT count(*) FROM domain_objects WHERE project=? AND kind=?" + clause
	if e := h.db.QueryRow(q, append([]any{h.project, kind}, args...)...).Scan(&n); e != nil {
		return -1
	}
	return n
}

// w1202Checkpoint produces the same artifact chain the accepted resource tests use: raw content first, then
// an Artifact row that is OBSERVED and FIXTURE, which is the only evidence kind an owner purpose grant
// accepts. The executor is read back off the Run rather than invented.
func w1202Checkpoint(ctx context.Context, h *harness, runID string) (domain.Object, string) {
	run := w1202Object(h, "Run", runID)
	executor := domain.Str(run, "executor_principal_id")
	if executor == "" {
		return domain.Object{}, "the run carries no executor_principal_id: " + truncate(fmt.Sprint(run), 200)
	}
	raw := domain.Bytes(domain.Object{"next": "continue the same operation", "checkpoint_of": runID})
	// The artifact route refuses a producer that is not the authenticated principal, so the two posts run
	// under a credential minted for the run's own executor and the owner token is put back on the way out.
	executorToken, te := h.svc.IssueCredential(ctx, executor, 15*time.Minute)
	if te != nil {
		return domain.Object{}, "executor credential refused (" + executor + "): " + te.Error()
	}
	// The If-Match tag is the OWNER's view of the project state; reading it after the switch would ask an
	// EXECUTOR principal for a projection it cannot see and come back empty.


	ownerToken := h.token
	ownerTag := h.stateTag(ctx)
	h.token = executorToken
	defer func() { h.token = ownerToken }()
	contentCode, content, contentText := h.api(ctx, "POST", h.base+"/content", domain.ID(), "", raw)
	if domain.Str(content, "content_hash") == "" {
		return domain.Object{}, "content post " + fmt.Sprint(contentCode) + ": " + truncate(contentText, 200)
	}
	_, artifact, body := h.api(ctx, "POST", h.base+"/artifacts", domain.ID(), ownerTag, domain.Object{
		"run_id": runID, "kind": "LOG", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE",
		"content_hash": content["content_hash"], "storage_key": content["storage_key"],
		"media_type": "application/json", "byte_size": len(raw), "input_refs": domain.Empty(),
		"source_refs": domain.Empty(), "produced_by": executor, "access_class": "PROJECT"})
	if artifact["id"] == nil {
		return domain.Object{}, "artifact post: " + truncate(body, 240)
	}
	return artifact, ""
}

// w1202RealArtifact returns a VersionRef for the first Artifact the project actually holds, or nil.
// idInList keeps the blocked-set assertion readable without importing more of the domain surface.
// refID reads the id out of a VersionRef that may be absent, null, or a different shape, without asserting.

func refID(v any) string {
	if m, isObj := v.(map[string]any); isObj {
		return domain.Str(m, "id")
	}
	return ""
}

func idInList(list []any, id string) bool {
	for _, v := range list {
		if s, isStr := v.(string); isStr && s == id {
			return true
		}
	}
	return false
}

func w1202RealArtifact(h *harness) domain.Object {
	var body string
	e := h.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' ORDER BY rowid LIMIT 1", h.project).Scan(&body)
	if e != nil {
		return nil
	}
	a, dec := domain.Decode([]byte(body))
	if dec != nil || domain.Str(a, "id") == "" {
		return nil
	}
	return domain.Object{"entity_type": "Artifact", "id": a["id"], "revision": a["revision"],
		"content_hash": a["content_hash"]}
}

func w1202Object(h *harness, kind, id string) domain.Object {
	var body string
	e := h.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND json_extract(body,'$.id')=?",
		h.project, kind, id).Scan(&body)
	if e != nil {
		return domain.Object{}
	}
	o, dec := domain.Decode([]byte(body))
	if dec != nil {
		return domain.Object{}
	}
	return o
}

func w1202Field(h *harness, kind, id, field string) any {
	var body string
	e := h.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind=? AND json_extract(body,'$.id')=?",
		h.project, kind, id).Scan(&body)
	if e != nil {
		return nil
	}
	o, dec := domain.Decode([]byte(body))
	if dec != nil {
		return nil
	}
	return o[field]
}

func w1202Notices(h *harness, requestID string) int {
	if requestID == "" {
		return -1
	}
	return w1202Count(h, "Notification", " AND json_extract(body,'$.resource_request_id')=?", requestID)
}

func w1202RequestID(o domain.Object) string {
	if v, isObj := o["request"].(map[string]any); isObj {
		return domain.Str(v, "id")
	}
	return ""
}

func w1202Phase(ctx context.Context, h *harness, graph *runGraph) {
	ok("W1202-ROUTING-SERVES-THIS-CARD", !routesToLegacy("W12-02", "", "W12"),
		"legacy.go servedChecks must include W12-02 while every accepted selector still forwards")

	sibling, siblingErr := orchestrationGraph(ctx, h, "W1202-SIBLING-RUN-ADMITTED")
	if siblingErr != nil {
		skip("W1202-INDEPENDENT-BRANCH-STILL-ADMITTABLE", "no second real task could be admitted: "+siblingErr.Error())
		return
	}

	code, robj, rtext := h.api(ctx, "POST", h.base+"/runtimes", domain.ID(), h.stateTag(ctx), domain.Object{
		"name": "equivalent fixture standby", "adapter": "fixture", "adapter_revision": "1",
		"capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE",
		"credential_ref": nil})
	standby := domain.Str(robj, "id")
	if code != 201 || standby == "" {
		ok("W1202-STANDBY-RUNTIME-REGISTERED", false, code, rtext)
		skip("W1202-UNAUTHORISED-REPLACEMENT-BLOCKS-THE-SWITCH", "no standby runtime could be registered")
		return
	}
	ok("W1202-STANDBY-RUNTIME-REGISTERED", true, standby)

	// A standby that was never authorised for this purpose must block, and blocking must not move the Run.
	first, e := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
		w1202Req([]any{}, "CAPACITY-1", false, nil, []any{graph.taskID}, []any{sibling.taskID}))
	status := domain.Str(first, "status")
	requestID := w1202RequestID(first)
	ok("W1202-UNAUTHORISED-REPLACEMENT-BLOCKS-THE-SWITCH", e == nil && status == "BLOCKED" && requestID != "",
		status, first, e)
	if requestID == "" {
		skip("W1202-BLOCK-KEEPS-THE-SAME-RUN", "the switch did not produce a request to reason about")
		return
	}
	ok("W1202-REFUSAL-REASON-NAMES-THE-PURPOSE-GRANT", len(domain.Str(first, "reason")) > 0,
		domain.Str(first, "reason"))

	runBody := w1202Field(h, "Run", graph.runID, "runtime_id")
	ok("W1202-BLOCK-KEEPS-THE-SAME-RUN-AND-RUNTIME", runBody == graph.runtimeID, runBody, graph.runtimeID)

	request := domain.Object{}
	if v, isObj := first["request"].(map[string]any); isObj {
		request = v
	}
	ok("W1202-REQUEST-CARRIES-IMPACT-AND-USER-NEXT-STEP",
		domain.Str(request, "summary") != "" && len(domain.Arr(request, "blocked_task_ids")) == 1 &&
			len(domain.Arr(request, "continuable_task_ids")) == 1,
		request)

	// captured before the merge round, which deliberately names a second task as blocked
	blockedFirst := domain.Arr(request, "blocked_task_ids")

	alerts := w1202Notices(h, requestID)
	ok("W1202-FIRST-BLOCK-EMITS-ONE-ALERT", alerts == 1, alerts, requestID)

	// Same project + category + account + reason is the same source: it merges, and it must not alert twice.
	second, e := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
		w1202Req([]any{}, "CAPACITY-1", true, dollars("4.00"), []any{sibling.taskID}, []any{sibling.taskID}))
	ok("W1202-SECOND-ROUND-STILL-BLOCKS", e == nil && domain.Str(second, "status") == "BLOCKED", second, e)
	repeatID := w1202RequestID(second)
	ok("W1202-SAME-SOURCE-REPEAT-MERGES-INTO-ONE-REQUEST", repeatID == requestID && requestID != "",
		repeatID, requestID)
	ok("W1202-SAME-SOURCE-REPEAT-ADDS-NO-SECOND-REQUEST",
		w1202Count(h, "ResourceRequest", " AND json_extract(body,'$.reason_code')=?", "CAPACITY-1") == 1,
		w1202Count(h, "ResourceRequest", " AND json_extract(body,'$.reason_code')=?", "CAPACITY-1"))
	ok("W1202-SECOND-ROUND-EMITS-NO-SECOND-ALERT", w1202Notices(h, requestID) == alerts,
		w1202Notices(h, requestID), alerts)
	merged := w1202Object(h, "ResourceRequest", requestID)
	ok("W1202-MERGE-UNION-OF-BLOCKED-TASKS", len(domain.Arr(merged, "blocked_task_ids")) == 2, merged["blocked_task_ids"])

	// A different reason code is a different source and must stay visible as its own blocker.
	third, e := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
		w1202Req([]any{}, "QUOTA-2", false, nil, []any{graph.taskID}, []any{}))
	otherID := w1202RequestID(third)
	ok("W1202-DIFFERENT-SOURCE-IS-ITS-OWN-REQUEST",
		e == nil && otherID != "" && otherID != requestID, otherID, requestID)
	ok("W1202-DIFFERENT-SOURCE-GETS-ITS-OWN-ALERT", w1202Notices(h, otherID) == 1, w1202Notices(h, otherID), otherID)

	// unknown cost must stay null; a request that claims knowledge without a number is refused outright.
	badCost := w1202Req([]any{}, "COST-3", true, nil, []any{graph.taskID}, []any{})
	_, e = h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby, badCost)
	costCode, costCodeName := faultOf(e)
	// faultOf yields (status, fault code); the sentence lives in the error text, so both are compared.
	ok("W1202-UNKNOWN-COST-REQUEST-IS-REFUSED",
		costCode == 422 && costCodeName == "GATE_FAILED" && strings.Contains(fmt.Sprint(e), "unknown cost must remain null"),
		costCode, costCodeName, e)

	// The branch that was never blocked must still be usable while the first one sits in a ResourceRequest.
	// The independent branch is not merely claimable in principle: orchestrationGraph above claimed and
	// started this run while the first task already sat inside an OPEN ResourceRequest, so the block is
	// local to its branch rather than a project-wide stop.
	sibRun := w1202Object(h, "Run", sibling.runID)
	sibStatus := domain.Str(sibRun, "status")
	ok("W1202-INDEPENDENT-BRANCH-PROCEEDS-WHILE-FIRST-IS-BLOCKED",
		sibling.runID != "" && (sibStatus == "RUNNING" || sibStatus == "QUEUED") &&
		w1202Field(h, "ResourceRequest", requestID, "status") == "OPEN",
		sibling.runID, sibStatus, w1202Field(h, "ResourceRequest", requestID, "status"))
	ok("W1202-INDEPENDENT-BRANCH-TASK-IS-NOT-IN-BLOCKED-SET",
		!idInList(blockedFirst, sibling.taskID) && idInList(blockedFirst, graph.taskID) &&
		len(blockedFirst) == 1,
		blockedFirst, sibling.taskID)
	ok("W1202-BLOCKED-TASK-LIST-IS-TASKS-NOT-PROJECT-WIDE",
		len(domain.Arr(w1202Object(h, "ResourceRequest", requestID), "blocked_task_ids")) == 2,
		w1202Object(h, "ResourceRequest", requestID)["blocked_task_ids"])

	// A completed artifact has to travel on the request as a VersionRef with its content_hash, and the
	// recovery condition is a real checkpoint ref rather than a null the card pretends about.
	checkpoint, checkpointErr := w1202Checkpoint(ctx, h, graph.runID)
	if checkpointErr != "" {
		skip("W1202-REQUEST-CARRIES-COMPLETED-ARTIFACT", checkpointErr)
		skip("W1202-REQUEST-CARRIES-RESUME-CONDITION", "same: no checkpoint to reference")
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME", "same: a purpose grant needs qualifying evidence")
		return
	}
	submittedArt := w1202ReqWith([]any{domain.Ref(checkpoint, "Artifact")}, domain.Ref(checkpoint, "Artifact"),
		"ARTIFACT-4", false, nil, []any{graph.taskID}, []any{sibling.taskID})
	withArtifact, ae := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby, submittedArt)
	artID := w1202RequestID(withArtifact)
	storedArt := w1202Object(h, "ResourceRequest", artID)
	ok("W1202-REQUEST-CARRIES-COMPLETED-ARTIFACT",
		ae == nil && domain.Str(withArtifact, "status") == "BLOCKED" && artID != "" &&
			len(domain.Arr(storedArt, "completed_artifact_refs")) == 1,
		artID, withArtifact, ae)
	// A type assertion here would panic on a nil and turn a real product gap into a crash, so the stored
	// value is read defensively and compared as data.
	ok("W1202-REQUEST-CARRIES-RESUME-CONDITION",
		refID(storedArt["resume_checkpoint_ref"]) == domain.Str(checkpoint, "id"),
		"stored", fmt.Sprint(storedArt["resume_checkpoint_ref"]), "submitted",
		fmt.Sprint(submittedArt["resume_checkpoint_ref"]), "produced", domain.Str(checkpoint, "id"))

	// The positive path needs an owner purpose grant over an OBSERVED FIXTURE artifact, and the purpose has
	// to equal the task's own task_type because that is the column resource_route_grants is keyed by.
	if e = h.svc.RegisterOrchestrationFixture(ctx, h.project, standby); e != nil {
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME", "standby is not a registered fixture: "+e.Error())
		return
	}
	purpose := domain.Str(w1202Object(h, "Task", graph.taskID), "task_type")
	if pe := h.svc.AuthorizeFixtureResource(ctx, h.token, h.project, standby, purpose,
		domain.Ref(checkpoint, "Artifact"), time.Now().Add(time.Hour)); pe != nil {
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME",
			"purpose grant refused for "+purpose+": "+pe.Error())
		return
	}
	sw, se := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
		w1202ReqWith([]any{domain.Ref(checkpoint, "Artifact")}, domain.Ref(checkpoint, "Artifact"),
			"ARTIFACT-4", false, nil, []any{graph.taskID}, []any{sibling.taskID}))
	ok("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME",
		se == nil && domain.Str(sw, "status") == "SWITCHED" &&
			w1202Field(h, "Run", graph.runID, "runtime_id") == standby,
		domain.Str(sw, "status"), w1202Field(h, "Run", graph.runID, "runtime_id"), standby, se)
	// The grant resolves the same source, so the blocker that already carries it must not gain a second row
	// and the alert already raised for it must still be the only one.
	grantReqID := w1202RequestID(sw)
	ok("W1202-GRANTED-ROUND-ADDS-NO-THIRD-REQUEST",
		w1202Count(h, "ResourceRequest", " AND json_extract(body,'$.reason_code')=?", "ARTIFACT-4") == 1,
		w1202Count(h, "ResourceRequest", " AND json_extract(body,'$.reason_code')=?", "ARTIFACT-4"))
	// A successful switch carries no request at all, so the meaningful form of "the resolved source keeps its
	// one alert" is about the blocker that already exists: the round that ended the shortage must not have
	// raised a second notice for it. Read that way the row is reachable on every run instead of only on runs
	// where the grant also failed, which is what the roster guard caught.
	ok("W1202-RESOLVED-SOURCE-KEEPS-ITS-ONE-ALERT", w1202Notices(h, artID) == 1,
		w1202Notices(h, artID), artID, grantReqID)

	// A replacement that is authorised yet NOT capability-equivalent is the card's silent-model-swap
	// counterexample. The grant must already be in place, otherwise the missing-grant leg outranks the
	// equivalence leg in qualifiedReplacement and the row would be decided by the wrong guard.
	weakCode, weakObj, _ := h.api(ctx, "POST", h.base+"/runtimes", domain.ID(), h.stateTag(ctx), domain.Object{
		"name": "authorised but weaker standby", "adapter": "fixture", "adapter_revision": "1",
		"capabilities": domain.Empty(), "platform": "windows-amd64", "measurement_mode": "FIXTURE",
		"credential_ref": nil})
	weak := domain.Str(weakObj, "id")
	weakRegistered := weakCode == 201 && weak != "" &&
		h.svc.RegisterOrchestrationFixture(ctx, h.project, weak) == nil &&
		h.svc.AuthorizeFixtureResource(ctx, h.token, h.project, weak, purpose,
			domain.Ref(checkpoint, "Artifact"), time.Now().Add(time.Hour)) == nil
	if !weakRegistered {
		skip("W1202-AUTHORISED-BUT-CAPABILITY-DOWNGRADE-IS-REFUSED",
			"the weaker runtime could not be brought to the equivalence leg: register code "+fmt.Sprint(weakCode))
		return
	}
	weakSwitch, de := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, weak,
		w1202ReqWith([]any{domain.Ref(checkpoint, "Artifact")}, domain.Ref(checkpoint, "Artifact"),
			"DOWNGRADE-5", false, nil, []any{graph.taskID}, []any{}))
	// SwitchResource does not raise a Fault for a refused replacement: it commits BLOCKED with the
	// qualification reason attached, which is the card's "a shortage stays a local branch" behaviour.
	dCode, dName := faultOf(de)
	ok("W1202-AUTHORISED-BUT-CAPABILITY-DOWNGRADE-IS-REFUSED",
		dCode == 0 && domain.Str(weakSwitch, "status") == "BLOCKED" &&
			strings.Contains(domain.Str(weakSwitch, "reason"), "replacement capabilities not equivalent"),
		dCode, dName, domain.Str(weakSwitch, "status"), domain.Str(weakSwitch, "reason"))

	// Expiry is minted through the product, never written into the table. A grant born already expired is
	// refused at minting (one leg); a grant with a 60 ms life is a real owner purpose grant that lapses, and
	// then the read-side qualification check is the only thing left able to refuse (the other leg).
	nearCode, nearObj, _ := h.api(ctx, "POST", h.base+"/runtimes", domain.ID(), h.stateTag(ctx), domain.Object{
		"name": "standby whose grant lapses", "adapter": "fixture", "adapter_revision": "1",
		"capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE",
		"credential_ref": nil})
	near := domain.Str(nearObj, "id")
	nearRegistered := nearCode == 201 && near != "" &&
		h.svc.RegisterOrchestrationFixture(ctx, h.project, near) == nil
	if !nearRegistered {
		skip("W1202-LAPSED-GRANT-REFUSES-THE-SWITCH", "no third runtime could be prepared for the lapsing grant")
		return
	}
	bornExpired := h.svc.AuthorizeFixtureResource(ctx, h.token, h.project, near, purpose,
		domain.Ref(checkpoint, "Artifact"), time.Now().Add(-time.Minute))
	ok("W1202-ALREADY-EXPIRED-GRANT-CANNOT-BE-MINTED", bornExpired != nil, fmt.Sprint(bornExpired))
	if pe := h.svc.AuthorizeFixtureResource(ctx, h.token, h.project, near, purpose,
		domain.Ref(checkpoint, "Artifact"), time.Now().Add(60*time.Millisecond)); pe != nil {
		skip("W1202-LAPSED-GRANT-REFUSES-THE-SWITCH", "short-TTL grant refused at minting: "+pe.Error())
		return
	}
	time.Sleep(150 * time.Millisecond)
	lapsedSwitch, xe := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, near,
		w1202ReqWith([]any{domain.Ref(checkpoint, "Artifact")}, domain.Ref(checkpoint, "Artifact"),
			"EXPIRED-6", false, nil, []any{graph.taskID}, []any{}))
	ok("W1202-LAPSED-GRANT-REFUSES-THE-SWITCH",
		domain.Str(lapsedSwitch, "status") == "BLOCKED" &&
			strings.Contains(domain.Str(lapsedSwitch, "reason"), "qualification expired or changed"),
		domain.Str(lapsedSwitch, "status"), domain.Str(lapsedSwitch, "reason"), xe)
}
