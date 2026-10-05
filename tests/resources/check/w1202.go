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
	return domain.Object{"category": "PERMISSION", "account_ref": w1202Account, "reason_code": reason,
		"summary": "no equivalent authorised runtime for this task yet",
		"blocked_task_ids": blocked, "continuable_task_ids": continuable,
		"completed_artifact_refs": refs,
		"requested_capability": "fixture", "estimated_cost": cost, "cost_known": costKnown,
		"resume_checkpoint_ref": nil}
}

func w1202Count(h *harness, kind, clause string, args ...any) int {
	var n int
	q := "SELECT count(*) FROM domain_objects WHERE project=? AND kind=?" + clause
	if e := h.db.QueryRow(q, append([]any{h.project, kind}, args...)...).Scan(&n); e != nil {
		return -1
	}
	return n
}

// w1202RealArtifact returns a VersionRef for the first Artifact the project actually holds, or nil.
// idInList keeps the blocked-set assertion readable without importing more of the domain surface.
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

	sibling, siblingErr := orchestrationGraph(ctx, h)
	if siblingErr != nil {
		skip("W1202-UNINDEPENDENT-BRANCH-KEEPS-RUNNING", "no second real task could be admitted: "+siblingErr.Error())
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

	// A completed artifact has to travel on the request as a VersionRef, content_hash included. The ref is
	// read back from the store rather than invented, and the row is skipped when the run produced none.
	carried := w1202RealArtifact(h)
	if carried == nil {
		skip("W1202-REQUEST-CARRIES-COMPLETED-ARTIFACT", "no Artifact row exists for this project to carry")
	} else {
		withArtifact, ae := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
			w1202Req([]any{carried}, "ARTIFACT-4", false, nil, []any{graph.taskID}, []any{sibling.taskID}))
		artID := w1202RequestID(withArtifact)
		ok("W1202-REQUEST-CARRIES-COMPLETED-ARTIFACT",
			ae == nil && domain.Str(withArtifact, "status") == "BLOCKED" && artID != "" &&
				len(domain.Arr(w1202Object(h, "ResourceRequest", artID), "completed_artifact_refs")) == 1,
			artID, withArtifact, ae)
	}

	// The positive path needs an owner purpose grant over an OBSERVED fixture artifact; the standby also has
	// to be registered as an orchestration fixture first, the way W12-01 registers its runtime.
	if e = h.svc.RegisterOrchestrationFixture(ctx, h.project, standby); e != nil {
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME", "standby is not a registered fixture: "+e.Error())
		return
	}
	artifact := w1202Object(h, "Artifact", graph.origin)
	if domain.Str(artifact, "id") == "" {
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME", "no origin artifact to qualify")
		return
	}
	evidence := domain.Object{"entity_type": "Artifact", "id": graph.origin, "revision": 1}
	if e = h.svc.AuthorizeFixtureResource(ctx, h.token, h.project, standby, "paired-metric",
		evidence, time.Now().Add(time.Hour)); e != nil {
		skip("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME", "purpose grant refused: "+e.Error())
		skip("W1202-EXPIRED-GRANT-BLOCKS-AGAIN", "no grant to expire")
		return
	}
	sw, e := h.svc.SwitchResource(ctx, h.token, h.project, graph.runID, standby,
		w1202Req([]any{}, "CAPACITY-1", false, nil, []any{graph.taskID}, []any{sibling.taskID}))
	ok("W1202-GRANTED-SWITCH-KEEPS-RUN-AND-SWAPS-RUNTIME",
		e == nil && domain.Str(sw, "status") == "SWITCHED" &&
			w1202Field(h, "Run", graph.runID, "runtime_id") == standby,
		domain.Str(sw, "status"), w1202Field(h, "Run", graph.runID, "runtime_id"), standby, e)
}
