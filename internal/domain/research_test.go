package domain

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

func researchAssert(t *testing.T, id string, want, got any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W08_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": "HTTP+SQLite+sealed local source fixture"})))
	if status != "PASS" {
		t.Fatalf("%s mismatch", id)
	}
}

type researchFixture struct {
	f                        *fixture
	owner, source, scheduler string
	ids                      map[string]string
	cycle                    Object
}

func researchSetup(t *testing.T, xEnabled bool) *researchFixture {
	t.Helper()
	f := setup(t)
	ids := map[string]string{"GITHUB": ID(), "PAPER": ID(), "X": ID()}
	b := projectBody()
	b["intent"] = "research source changes relevant to the fixture project"
	b["constraints"] = []any{"preserve accepted project behavior"}
	b["source_configs"] = []any{
		Object{"source_id": ids["GITHUB"], "kind": "GITHUB", "required": true, "enabled": true, "query": "repo:researchos/research", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil},
		Object{"source_id": ids["PAPER"], "kind": "PAPER", "required": true, "enabled": true, "query": "research agents", "allowed_origins": []any{"https://arxiv.org", "https://export.arxiv.org"}, "credential_ref": nil},
		Object{"source_id": ids["X"], "kind": "X", "required": true, "enabled": xEnabled, "query": "research agents", "allowed_origins": []any{"https://x.com"}, "credential_ref": nil},
	}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", b)
	f.project = Str(p, "project_id")
	f.owner = "w08-owner-planner"
	f.switchPrincipal(f.owner, []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"})
	owner := f.token
	actor := Principal{ID: "w08-source-adapter", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
		t.Fatal(e)
	}
	source, e := f.s.IssueCredential(context.Background(), actor.ID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	schedulerActor := Principal{ID: "w08-scheduler", Roles: []string{"SCHEDULER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e = f.s.ProvisionPrincipal(context.Background(), schedulerActor); e != nil {
		t.Fatal(e)
	}
	scheduler, e := f.s.IssueCredential(context.Background(), schedulerActor.ID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return &researchFixture{f: f, owner: owner, source: source, scheduler: scheduler, ids: ids}
}

func (r *researchFixture) start(t *testing.T, to time.Time) Object {
	t.Helper()
	r.f.token = r.owner
	profile := r.f.expect(200, "GET", r.f.path("/profile"), "", "", nil)
	body := Object{"trigger": "SCHEDULE", "window_from": to.Add(-7 * 24 * time.Hour).Format(time.RFC3339Nano), "window_to": to.Format(time.RFC3339Nano), "profile_revision": profile["revision"]}
	r.cycle = r.f.expect(201, "POST", r.f.path("/research-cycles"), ID(), r.f.stateTag(), body)
	return r.cycle
}

func (r *researchFixture) cursor(t *testing.T, kind string) Object {
	t.Helper()
	var raw string
	if e := r.f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor' AND json_extract(body,'$.source_id')=?", r.f.project, r.ids[kind]).Scan(&raw); e != nil {
		t.Fatal(e)
	}
	o, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	return o
}

func (r *researchFixture) capture(t *testing.T, kind string, item bool) []Object {
	t.Helper()
	f := r.f
	from, to, e := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	if e != nil {
		t.Fatal(e)
	}
	f.token = r.source
	current := r.cursor(t, kind)
	config, cursor, e := f.s.sourceConfig(context.Background(), r.source, f.project, Str(current, "id"))
	if e != nil {
		t.Fatal(e)
	}
	requestURL, canonical := map[string]string{"GITHUB": "https://api.github.com/repos/researchos/research/releases", "PAPER": "https://export.arxiv.org/api/query", "X": "https://x.com/search?q=research"}[kind], map[string]string{"GITHUB": "https://github.com/researchos/research/releases/tag/v1", "PAPER": "https://arxiv.org/abs/2609.00001", "X": "https://x.com/research/status/123"}[kind]
	page := sources.Page{RawResponse: Bytes(Object{"fixture": "bounded local source page", "kind": kind}), RawMediaType: "application/json", Complete: true,
		HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{requestURL}, FinalURLs: []string{requestURL}}
	if item {
		body := []byte("full local source fixture body for " + canonical)
		page.RawResponse = Bytes(Object{"url": requestURL, "items": []any{Object{"url": canonical, "body": string(body)}}})
		page.Items = []sources.Item{{SourceID: r.ids[kind], CanonicalURL: canonical, UpstreamID: kind + "-v1", PublishedAt: to.Add(-time.Minute), Body: body, MediaType: "text/plain", Locator: "body"}}
	}
	result, e := f.s.captureSourcePage(context.Background(), r.source, f.project, cursor, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil {
		t.Fatalf("capture %s: %v", kind, e)
	}
	if result.RawArtifact == nil || result.Manifest == nil {
		t.Fatal("raw W07 page was not sealed")
	}
	advance := Object{"opaque_cursor": nil, "covered_until": r.cycle["window_to"], "last_success_at": Now(), "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": r.cycle["id"]}
	f.expect(200, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), advance)
	out := []Object{}
	for _, ev := range result.Evidence {
		out = append(out, ev)
	}
	return out
}

func (r *researchFixture) checkpoint(t *testing.T, candidates, experiments []any) Object {
	t.Helper()
	r.f.token = r.scheduler
	b := Object{"source_coverage": r.cycle["source_coverage"], "candidate_evidence_ids": candidates, "required_experiment_ids": experiments,
		"decision_ids": Empty(), "follow_up_task_ids": Empty(), "checkpoint_artifact_id": nil}
	r.cycle = r.f.expect(200, "POST", r.f.path("/research-cycles/"+Str(r.cycle, "id")+"/checkpoint"), ID(), testTag(r.cycle), b)
	return r.cycle
}

func (r *researchFixture) close(t *testing.T, status string) Object {
	t.Helper()
	r.f.token = r.scheduler
	r.cycle = r.f.expect(200, "POST", r.f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": status, "outcome_summary": "No observed improvement; retain stable project version and review gaps later."})
	return r.cycle
}

func TestW08C06MissingXContinuesSources(t *testing.T) {
	r := researchSetup(t, false)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	r.capture(t, "GITHUB", false)
	r.capture(t, "PAPER", false)
	r.checkpoint(t, Empty(), Empty())
	statuses := map[string]any{}
	for _, raw := range Arr(r.cycle, "source_coverage") {
		c := raw.(map[string]any)
		for kind, id := range r.ids {
			if c["source_id"] == id {
				statuses[kind] = c["status"]
			}
		}
	}
	researchAssert(t, "C06-01", []any{"COMPLETE", "COMPLETE"}, []any{statuses["GITHUB"], statuses["PAPER"]})
	researchAssert(t, "C06-02-X", "NOT_CONFIGURED", statuses["X"])
	r.f.token = r.scheduler
	status, _, _ := r.f.request("POST", r.f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "forged full scan"})
	researchAssert(t, "C06-02-NO-FALSE-COMPLETE", 422, status)
	r.close(t, "PARTIAL")
	researchAssert(t, "C06-02", "PARTIAL", r.cycle["status"])
	var requests int
	if e := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND json_extract(body,'$.reason_code')=?", r.f.project, "RESEARCH_SOURCE_NOT_CONFIGURED:"+r.ids["X"]).Scan(&requests); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C06-03-REQUEST", 1, requests)
	r.f.token = r.owner
	profile := r.f.expect(200, "GET", r.f.path("/profile"), "", "", nil)
	now := time.Now().UTC().Add(-time.Second).Truncate(time.Second)
	r.f.expect(201, "POST", r.f.path("/research-cycles"), ID(), r.f.stateTag(), Object{"trigger": "USER", "window_from": r.cycle["window_to"], "window_to": now.Format(time.RFC3339Nano), "profile_revision": profile["revision"]})
	if e := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND json_extract(body,'$.reason_code')=?", r.f.project, "RESEARCH_SOURCE_NOT_CONFIGURED:"+r.ids["X"]).Scan(&requests); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C06-03-DEDUP", 1, requests)
	if dir := os.Getenv("W08_EVIDENCE_DIR"); dir != "" {
		researchSnapshot(t, r, dir, "missing-x")
	}
}

func TestW08C06RateLimitedXCoalesces(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	r.capture(t, "GITHUB", false)
	r.capture(t, "PAPER", false)
	r.f.token = r.source
	cur := r.cursor(t, "X")
	config, current, e := r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(cur, "id"))
	if e != nil {
		t.Fatal(e)
	}
	from, to, _ := parseCycleWindow(Str(r.cycle, "window_from"), Str(r.cycle, "window_to"))
	wait := time.Now().UTC().Add(time.Minute)
	page := sources.Page{Failure: "RATE_LIMITED", RetryAfter: &wait, HTTPStatus: 429}
	result, e := r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, current, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil || result.Page.Failure != "RATE_LIMITED" {
		t.Fatal(result, e)
	}
	persisted := r.cursor(t, "X")
	retryAt, e := time.Parse(time.RFC3339Nano, Str(persisted, "retry_after"))
	if e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C06-03-RETRY-AFTER", true, retryAt.Sub(time.Now().UTC()) >= 59*time.Second)
	config, current, e = r.f.s.sourceConfig(context.Background(), r.source, r.f.project, Str(cur, "id"))
	if e != nil {
		t.Fatal(e)
	}
	never := &neverFetchSource{}
	result, e = r.f.s.captureSourcePage(context.Background(), r.source, r.f.project, current, config, from, to, 20, never)
	if e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C06-03-RETRY", []any{"RATE_LIMITED", 0}, []any{result.Page.Failure, never.calls})
	r.f.token = r.owner
	profile := r.f.expect(200, "GET", r.f.path("/profile"), "", "", nil)
	conflict := r.f.expect(409, "POST", r.f.path("/research-cycles"), ID(), r.f.stateTag(), Object{"trigger": "SCHEDULE", "window_from": r.cycle["window_from"], "window_to": r.cycle["window_to"], "profile_revision": profile["revision"]})
	researchAssert(t, "W08-G02-COALESCE", "STATE_CONFLICT", conflict["code"])
	r.checkpoint(t, Empty(), Empty())
	r.close(t, "PARTIAL")
	researchAssert(t, "C06-02-429", "RATE_LIMITED", Arr(r.cycle, "source_coverage")[2].(map[string]any)["status"])
	var cycles int
	if e := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", r.f.project).Scan(&cycles); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "W08-G02-ONE-ACTIVE", 1, cycles)
	if dir := os.Getenv("W08_EVIDENCE_DIR"); dir != "" {
		researchSnapshot(t, r, dir, "x-429")
	}
}

func researchStableExperiment(t *testing.T, r *researchFixture) Object {
	t.Helper()
	x := researchExperiment(t, r, "stable")
	var verdict string
	if err := r.f.db.QueryRow("SELECT json_extract(body,'$.verdict') FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND id=?", r.f.project, x["acceptance_id"]).Scan(&verdict); err != nil {
		t.Fatal(err)
	}
	researchAssert(t, "C05-EXPERIMENT", []any{"COMPLETED", "NO_IMPROVEMENT", "PASS"}, []any{x["status"], x["outcome"], verdict})
	return x
}

func researchExperiment(t *testing.T, r *researchFixture, mode string) Object {
	t.Helper()
	f := r.f
	f.token = r.owner
	req := f.requirement()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{
		"title": "Research no-gain experiment", "original_intent": "Check whether candidate improves paired quality",
		"scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"research-fixture"},
		"deliverables": []any{"paired result"}, "acceptance_contract": experimentContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "bounded research experiment"})
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "research fixture observation producer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); e != nil {
		t.Fatal(e)
	}
	o := &orchestrationFixture{f: f, goal: goal, req: req, rt: rt, owner: r.owner}
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	refs := []any{Ref(req, "Requirement")}
	contract := experimentContract()
	stop := Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "attempt-limit"}}
	x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), Object{"cycle_id": r.cycle["id"], "scope": "PROJECT",
		"hypothesis": "candidate improves paired quality", "candidate_ref": refs[0], "baseline_refs": refs, "input_refs": refs,
		"metrics":             []any{Object{"metric_id": "quality", "description": "paired arithmetic mean", "unit": "points", "operator": "GTE", "target": "2", "upper_target": nil, "mandatory": true}},
		"acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"})
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": x["preregistration_hash"]})
	if mode == "registered" {
		return x
	}
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(goal, "id"))), Object{"goal_id": goal["id"], "title": "check stable baseline",
		"task_type": "paired-metric", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": refs, "input_refs": refs,
		"acceptance_contract": contract, "origin_problem_id": "research-fixture", "candidate_id": "stable", "stop_policy": stop})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "registered paired research experiment"})
	if e := f.s.BindExperimentTask(context.Background(), r.owner, f.project, Str(x, "id"), Str(task, "id")); e != nil {
		t.Fatal(e)
	}
	run := o.claim(task)
	var e error
	x, e = f.s.BeginExperiment(context.Background(), r.owner, f.project, Str(x, "id"), Str(run.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	raw := Object{"experiment_id": x["id"], "preregistration_hash": x["preregistration_hash"], "observations": []any{Object{"metric_id": "quality", "case_ids": []any{"s1", "s2"}, "baseline": []any{"1", "1"}, "candidate": []any{"1", "1"}}}}
	if mode == "inconclusive" {
		Arr(raw, "observations")[0].(map[string]any)["candidate"] = []any{nil, nil}
	}
	if mode == "regressed" {
		Arr(raw, "observations")[0].(map[string]any)["baseline"] = []any{"3", "3"}
	}
	results, outcome, e := recomputeExperiment(x, raw)
	if e != nil {
		t.Fatal(e)
	}
	raw["results"], raw["outcome"] = results, outcome
	a := o.report(run, Bytes(raw))
	request := o.acceptance(run, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), request)
	f.token = r.owner
	final := f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), Object{"run_ids": x["run_ids"], "results": results, "outcome": outcome, "acceptance_id": receipt["id"]})
	return final
}

func TestW08C05CompleteWithoutAdoption(t *testing.T) {
	r := researchSetup(t, true)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	before := r.f.expect(200, "GET", r.f.path("/state"), "", "", nil)["latest_release_id"]
	gh := r.capture(t, "GITHUB", true)
	paper := r.capture(t, "PAPER", true)
	x := r.capture(t, "X", true) // trusted complete local fixture adapter, never live XBrowser
	experiment := researchStableExperiment(t, r)
	ids := []any{gh[0]["id"], paper[0]["id"], x[0]["id"]}
	r.checkpoint(t, ids, []any{experiment["id"]})
	_, adoptErr := r.f.s.ReviewResearchCandidate(context.Background(), r.owner, r.f.project, Str(r.cycle, "id"), ids[0].(string), "fixture", "ADOPT", "claim improvement", "", "")
	denied := false
	if fault, ok := adoptErr.(*Fault); ok {
		denied = fault.Status == 422 && fault.Code == "GATE_FAILED"
	}
	researchAssert(t, "C05-02-NO-FALSE-ADOPT", true, denied)
	for i, spec := range []struct{ outcome, missing, revisit string }{{"REJECT", "", ""}, {"WATCH", "need independent measurement", "new primary measurement"}, {"INCONCLUSIVE", "unknown origin chain", "review original source"}} {
		_, e := r.f.s.ReviewResearchCandidate(context.Background(), r.owner, r.f.project, Str(r.cycle, "id"), ids[i].(string), "fixture", spec.outcome,
			"Candidate does not show a measured improvement for the current project", spec.missing, spec.revisit)
		if e != nil {
			t.Fatal(e)
		}
	}
	for _, raw := range Arr(r.cycle, "source_coverage") {
		if raw.(map[string]any)["status"] != "COMPLETE" {
			t.Fatal("source fixture did not close bounded window", raw)
		}
	}
	r.close(t, "COMPLETE")
	researchAssert(t, "C05-01", "COMPLETE", r.cycle["status"])
	after := r.f.expect(200, "GET", r.f.path("/state"), "", "", nil)["latest_release_id"]
	researchAssert(t, "C05-02", before, after)
	var reviews int
	if e := r.f.db.QueryRow("SELECT count(*) FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND outcome IN ('REJECT','WATCH','INCONCLUSIVE')", r.f.project, r.cycle["id"]).Scan(&reviews); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C05-03", 3, reviews)
	var adoption, followups, falselyIndependent int
	if e := r.f.db.QueryRow("SELECT count(*),sum(CASE WHEN outcome IN ('WATCH','INCONCLUSIVE') AND length(missing_evidence)>0 AND length(revisit_trigger)>0 THEN 1 ELSE 0 END),sum(CASE WHEN json_extract(origin_summary_json,'$.independent_observed_count')>0 THEN 1 ELSE 0 END) FROM research_candidate_reviews WHERE project=? AND cycle_id=?", r.f.project, r.cycle["id"]).Scan(&adoption, &followups, &falselyIndependent); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C05-03-REVISIT", []any{3, 2, 0}, []any{adoption, followups, falselyIndependent})
	if e := r.f.db.QueryRow("SELECT count(*) FROM research_candidate_reviews WHERE project=? AND cycle_id=? AND outcome='ADOPT'", r.f.project, r.cycle["id"]).Scan(&adoption); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C05-02-NO-ADOPT", 0, adoption)
	var pages int
	if e := r.f.db.QueryRow("SELECT count(*) FROM source_pages WHERE project=? AND complete=1 AND window_to=?", r.f.project, r.cycle["window_to"]).Scan(&pages); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "C05-01-PAGES", 3, pages)
	if dir := os.Getenv("W08_EVIDENCE_DIR"); dir != "" {
		researchSnapshot(t, r, dir, "c05-no-adopt")
	}
}

func TestW08G02SixHourAndMissedTicks(t *testing.T) {
	r := researchSetup(t, true)
	first := time.Now().UTC().Add(-19 * time.Hour).Truncate(time.Second)
	r.start(t, first)
	researchAssert(t, "W08-G02-FIRST-LOOKBACK", int64(7*24*time.Hour/time.Second), cycleSeconds(t, r.cycle))
	r.close(t, "BLOCKED")
	r.f.token = r.owner
	profile := r.f.expect(200, "GET", r.f.path("/profile"), "", "", nil)
	latest := time.Now().UTC().Add(-time.Minute).Truncate(time.Second)
	next := r.f.expect(201, "POST", r.f.path("/research-cycles"), ID(), r.f.stateTag(), Object{"trigger": "SCHEDULE", "window_from": latest.Add(-6 * time.Hour).Format(time.RFC3339Nano), "window_to": latest.Format(time.RFC3339Nano), "profile_revision": profile["revision"]})
	researchAssert(t, "W08-G02-MISSED-WINDOW", first.Format(time.RFC3339Nano), next["window_from"])
	var count int
	if e := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", r.f.project).Scan(&count); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "W08-G02-MISSED-COALESCED", 2, count)
}

func cycleSeconds(t *testing.T, cycle Object) int64 {
	t.Helper()
	from, to, e := parseCycleWindow(Str(cycle, "window_from"), Str(cycle, "window_to"))
	if e != nil {
		t.Fatal(e)
	}
	return int64(to.Sub(from) / time.Second)
}

func researchSnapshot(t *testing.T, r *researchFixture, dir, name string) {
	t.Helper()
	if e := os.MkdirAll(dir, 0755); e != nil {
		t.Fatal(e)
	}
	rows, e := r.f.db.Query("SELECT kind,id,body FROM domain_objects WHERE project=? AND kind IN ('ResearchCycle','SourceCursor','ResourceRequest','Experiment','Evidence','Artifact','AcceptanceReceipt') ORDER BY kind,id", r.f.project)
	if e != nil {
		t.Fatal(e)
	}
	defer rows.Close()
	objects := Empty()
	for rows.Next() {
		var kind, id, body string
		if e = rows.Scan(&kind, &id, &body); e != nil {
			t.Fatal(e)
		}
		objects = append(objects, Object{"kind": kind, "id": id, "body": json.RawMessage(body)})
	}
	if e = rows.Err(); e != nil {
		t.Fatal(e)
	}
	pages := Empty()
	pageRows, e := r.f.db.Query("SELECT cursor_id,source_id,window_from,window_to,raw_artifact_id,item_refs_json,complete,fetched_at FROM source_pages WHERE project=? ORDER BY source_id", r.f.project)
	if e != nil {
		t.Fatal(e)
	}
	for pageRows.Next() {
		var cursorID, sourceID, from, to, artifactID, refs, fetched string
		var complete int
		if e = pageRows.Scan(&cursorID, &sourceID, &from, &to, &artifactID, &refs, &complete, &fetched); e != nil {
			t.Fatal(e)
		}
		pages = append(pages, Object{"cursor_id": cursorID, "source_id": sourceID, "window_from": from, "window_to": to, "raw_artifact_id": artifactID, "item_refs": json.RawMessage(refs), "complete": complete, "fetched_at": fetched})
	}
	if e = pageRows.Err(); e != nil {
		t.Fatal(e)
	}
	pageRows.Close()
	reviews := Empty()
	reviewRows, e := r.f.db.Query("SELECT evidence_id,outcome,reason,missing_evidence,revisit_trigger,origin_summary_json FROM research_candidate_reviews WHERE project=? ORDER BY evidence_id", r.f.project)
	if e != nil {
		t.Fatal(e)
	}
	for reviewRows.Next() {
		var evidenceID, outcome, reason string
		var missing, revisit *string
		var origins string
		if e = reviewRows.Scan(&evidenceID, &outcome, &reason, &missing, &revisit, &origins); e != nil {
			t.Fatal(e)
		}
		reviews = append(reviews, Object{"evidence_id": evidenceID, "outcome": outcome, "reason": reason, "missing_evidence": missing, "revisit_trigger": revisit, "origin_summary": json.RawMessage(origins)})
	}
	if e = reviewRows.Err(); e != nil {
		t.Fatal(e)
	}
	reviewRows.Close()
	if e = os.WriteFile(filepath.Join(dir, name+"-sqlite.json"), Bytes(Object{"objects": objects, "pages": pages, "reviews": reviews}), 0600); e != nil {
		t.Fatal(e)
	}
}
