package domain

// Compiled only through the W14 driver's Go overlay. This keeps trusted fixture
// adapters package-local without adding a fixture control plane to the product.
import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"researchos.local/research-os/adapters/decision"
	"researchos.local/research-os/internal/store"
)

func w14Emit(t *testing.T, kind string, value Object) {
	t.Helper()
	value["record_type"], value["scope"], value["recorded_at"] = kind, "FIXTURE_SYNTHETIC", Now()
	file, e := os.OpenFile(filepath.Join(os.Getenv("W14_EVIDENCE_DIR"), os.Getenv("W14_PHASE")+".jsonl"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0600)
	if e != nil {
		t.Fatal(e)
	}
	defer file.Close()
	if _, e = file.Write(append(Bytes(value), '\n')); e != nil {
		t.Fatal(e)
	}
}

func w14Assert(t *testing.T, id string, want, got any, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	w14Emit(t, "assertion", Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})
	if status == "FAIL" {
		t.Fatalf("%s expected %s actual %s", id, Bytes(want), Bytes(got))
	}
}

func w14Redact(value any) any {
	switch v := value.(type) {
	case map[string]any:
		copy := Object{}
		for k, item := range v {
			if k == "lease_token" || k == "token" || k == "access_token" || k == "refresh_token" {
				copy[k] = "<redacted fixture credential>"
			} else {
				copy[k] = w14Redact(item)
			}
		}
		return copy
	case []any:
		copy := Empty()
		for _, item := range v {
			copy = append(copy, w14Redact(item))
		}
		return copy
	}
	return value
}

func w14Body(raw []byte) any {
	var value any
	if json.Unmarshal(raw, &value) == nil {
		return w14Redact(value)
	}
	return string(raw)
}

func w14ArtifactBody(t *testing.T, f *fixture, id string, artifact Object) {
	t.Helper()
	r := httptest.NewRequest("GET", f.path("/artifacts/"+Str(artifact, "id")+"/content"), nil)
	r.Header.Set("Authorization", "Bearer "+f.token)
	w := httptest.NewRecorder()
	f.h.ServeHTTP(w, r) // The bridge sends a real loopback HTTP request.
	w14Assert(t, id, []any{200, artifact["content_hash"]}, []any{w.Code, Digest(w.Body.Bytes())}, Ref(artifact, "Artifact"))
}

func w14Setup(t *testing.T, resume bool) *fixture {
	t.Helper()
	path := os.Getenv("W14_DATABASE")
	if os.Getenv("RESEARCHOS_TASK_ID") != "W14" || path == "" || !strings.HasPrefix(filepath.Base(filepath.Dir(path)), "researchos-w14-") {
		t.Fatal("isolated W14 driver database required")
	}
	db, e := store.Open(path)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	if e = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); e != nil {
		t.Fatal(e)
	}
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	f := &fixture{s: s, db: db, t: t, owner: "w14-fixture-owner"}
	if !resume {
		if e = s.ProvisionPrincipal(context.Background(), Principal{ID: f.owner, Roles: []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}, CanCreateProject: true}); e != nil {
			t.Fatal(e)
		}
	}
	f.token, e = s.IssueCredential(context.Background(), f.owner, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	server, startup := fixtureHTTPServer(t, s.Handler())
	t.Cleanup(server.Close)
	w14Emit(t, "transport", Object{"server": server.URL, "startup_probes": startup, "product_handler": "Service.Handler", "new_process": resume, "pid": os.Getpid()})
	client := server.Client()
	client.Timeout = 20 * time.Second
	f.h = http.HandlerFunc(func(w http.ResponseWriter, incoming *http.Request) {
		raw, err := io.ReadAll(incoming.Body)
		if err != nil {
			t.Fatal(err)
		}
		request, err := http.NewRequest(incoming.Method, server.URL+incoming.URL.RequestURI(), bytes.NewReader(raw))
		if err != nil {
			t.Fatal(err)
		}
		request.Header = incoming.Header.Clone()
		response, err := client.Do(request)
		if err != nil {
			t.Fatal(err)
		} // No replay of a submitted business request.
		defer response.Body.Close()
		body, err := io.ReadAll(response.Body)
		if err != nil {
			t.Fatal(err)
		}
		w14Emit(t, "http", Object{"method": incoming.Method, "path": incoming.URL.RequestURI(), "request": w14Body(raw), "request_sha256": Digest(raw),
			"if_match": incoming.Header.Get("If-Match"), "idempotency_key": incoming.Header.Get("Idempotency-Key"), "status": response.StatusCode,
			"response": w14Body(body), "response_sha256": Digest(body), "etag": response.Header.Get("ETag"), "correlation_id": response.Header.Get("X-Correlation-ID")})
		for k, values := range response.Header {
			for _, v := range values {
				w.Header().Add(k, v)
			}
		}
		w.WriteHeader(response.StatusCode)
		_, _ = w.Write(body)
	})
	return f
}

func w14Research(t *testing.T, f *fixture, enabled bool) *researchFixture {
	ids := map[string]string{"GITHUB": ID(), "PAPER": ID(), "X": ID()}
	b := projectBody()
	b["name"], b["intent"] = "W14 synthetic cross-module cycle", "Determine whether the fixed candidate improves the fixed baseline"
	b["source_configs"] = []any{
		Object{"source_id": ids["GITHUB"], "kind": "GITHUB", "required": true, "enabled": true, "query": "repo:researchos/research", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil},
		Object{"source_id": ids["PAPER"], "kind": "PAPER", "required": true, "enabled": true, "query": "research agents", "allowed_origins": []any{"https://arxiv.org", "https://export.arxiv.org"}, "credential_ref": nil},
		Object{"source_id": ids["X"], "kind": "X", "required": true, "enabled": enabled, "query": "research agents", "allowed_origins": []any{"https://x.com"}, "credential_ref": nil},
	}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", b)
	f.project = Str(p, "project_id")
	// Project creation gives its creating owner the project grant.
	r := &researchFixture{f: f, owner: f.token, ids: ids}
	for name, role := range map[string]string{"source": "SOURCE_ADAPTER", "scheduler": "SCHEDULER"} {
		actor := Principal{ID: ID(), Roles: []string{role}, Grants: []Grant{{ProjectID: f.project}}}
		if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
			t.Fatal(e)
		}
		token, e := f.s.IssueCredential(context.Background(), actor.ID, 15*time.Minute)
		if e != nil {
			t.Fatal(e)
		}
		if name == "source" {
			r.source = token
		} else {
			r.scheduler = token
		}
	}
	return r
}

func w14Fault(t *testing.T, id string, e error, status int) {
	t.Helper()
	got, code := 0, ""
	if f, ok := e.(*Fault); ok {
		got, code = f.Status, f.Code
	}
	w14Assert(t, id, status, got, Object{"service_error": fmt.Sprint(e), "code": code})
}

func TestW14VerticalCycle(t *testing.T) {
	f := w14Setup(t, false)
	r := w14Research(t, f, true)
	req := f.requirement()
	refs := []any{Ref(req, "Requirement")}
	contract := experimentContract()
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "W14 fixed baseline and candidate", "original_intent": "Verify the full synthetic pipeline without claiming live research", "scope": "PROJECT", "requirement_refs": refs, "problem_ids": []any{"w14-cycle-fixture"}, "deliverables": []any{"independently checked paired result and next step"}, "acceptance_contract": contract})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "bounded G01 fixture"})
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	candidates := Empty()
	for _, kind := range []string{"GITHUB", "PAPER", "X"} {
		items := r.capture(t, kind, true)
		w14Emit(t, "service", Object{"operation": "captureSourcePage", "source_kind": kind, "adapter": "sourceFixtureAdapter", "provider_contacted": false, "results": items,
			"mode_note": "Source sealing currently writes LIVE metadata even for the package-local synthetic adapter; it is not live qualification evidence"})
		for _, item := range items {
			candidates = append(candidates, item["id"])
			actual := f.read("evidence", Str(item, "id"))
			a := f.read("artifacts", Str(item["snapshot_artifact_ref"].(map[string]any), "id"))
			w14Assert(t, "W14-SOURCE-"+kind, true, actual["id"] == item["id"] && a["content_hash"] == item["snapshot_artifact_ref"].(map[string]any)["content_hash"], Object{"evidence": actual, "artifact": a})
			w14ArtifactBody(t, f, "W14-SOURCE-BODY-"+kind, a)
		}
	}
	f.token = r.owner
	profile := f.expect(200, "GET", f.path("/profile"), "", "", nil)
	stop := Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"wall-time", "attempt-limit"}}
	experimentBody := Object{"cycle_id": r.cycle["id"], "scope": "PROJECT", "hypothesis": "candidate improves paired quality", "candidate_ref": refs[0], "baseline_refs": refs, "input_refs": refs,
		"metrics": []any{Object{"metric_id": "quality", "description": "fixed paired arithmetic mean", "unit": "points", "operator": "GTE", "target": "2", "upper_target": nil, "mandatory": true}}, "acceptance_contract": contract, "stop_policy": stop, "budget_policy_id": profile["budget_policy_id"], "measurement_mode": "FIXTURE"}
	staleBody := copyObject(experimentBody)
	staleRef := Ref(req, "Requirement")
	staleRef["revision"] = 1 // Persisted draft version exists, but accepted version 2 is current.
	staleBody["candidate_ref"] = staleRef
	code, denied, _ := f.request("POST", f.path("/experiments"), ID(), f.stateTag(), staleBody)
	w14Assert(t, "W14-STALE-SEMANTIC-INPUT-REJECT", []any{412, "STALE_INPUT"}, []any{code, denied["code"]}, denied)
	x := f.expect(201, "POST", f.path("/experiments"), ID(), f.stateTag(), experimentBody)
	code, denied, _ = f.request("POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": Digest([]byte("wrong"))})
	w14Assert(t, "W14-FROZEN-PLAN-REJECT", 422, code, denied)
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/register"), ID(), testTag(x), Object{"expected_preregistration_hash": x["preregistration_hash"]})
	r.checkpoint(t, candidates, []any{x["id"]})
	code, denied, _ = f.request("POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "attempt to skip required experiment"})
	w14Assert(t, "W14-UNFINISHED-EXPERIMENT-BLOCKS-COMPLETE", 422, code, denied)
	f.token = r.owner
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "W14 synthetic observation producer", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(rt, "id")); e != nil {
		t.Fatal(e)
	}
	taskBody := Object{"goal_id": goal["id"], "title": "verify fixed paired outputs", "task_type": "paired-metric", "stage": "experiment", "dependency_task_ids": Empty(), "requirement_refs": refs, "input_refs": refs, "acceptance_contract": contract, "origin_problem_id": "w14-cycle-fixture", "candidate_id": "stable", "stop_policy": stop}
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(goal, "id"))), taskBody)
	bundle := f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	code, denied, _ = f.request("POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), `"r1"`, Object{"action": "SUBMIT", "reason": "stale input"})
	w14Assert(t, "W14-STALE-TASK-REVISION-REJECT", 412, code, denied)
	task = f.expect(200, "POST", f.path("/tasks/"+Str(task, "id")+"/actions"), ID(), testTag(task), Object{"action": "SUBMIT", "reason": "frozen current bundle"})
	w14Assert(t, "W14-GOAL-CONTEXT-TASK", []any{goal["id"], bundle["id"], "READY"}, []any{task["goal_id"], task["context_bundle_id"], task["status"]}, Object{"requirement": Ref(req, "Requirement"), "bundle": bundle, "task": task})
	if e := f.s.BindExperimentTask(context.Background(), r.owner, f.project, Str(x, "id"), Str(task, "id")); e != nil {
		t.Fatal(e)
	}
	o := &orchestrationFixture{f: f, goal: goal, req: req, rt: rt, owner: r.owner}
	run := o.claim(task)
	var e error
	x, e = f.s.BeginExperiment(context.Background(), r.owner, f.project, Str(x, "id"), Str(run.run, "id"))
	if e != nil {
		t.Fatal(e)
	}
	w14Emit(t, "service", Object{"operation": "BindExperimentTask + BeginExperiment", "experiment": x, "run_ref": Ref(run.run, "Run")})
	raw := Object{"experiment_id": x["id"], "preregistration_hash": x["preregistration_hash"], "observations": []any{Object{"metric_id": "quality", "case_ids": []any{"s1", "s2"}, "baseline": []any{"1", "1"}, "candidate": []any{"1", "1"}}}}
	results, outcome, e := recomputeExperiment(x, raw)
	if e != nil {
		t.Fatal(e)
	}
	raw["results"], raw["outcome"] = results, outcome
	artifact := o.report(run, Bytes(raw))
	w14ArtifactBody(t, f, "W14-EXPERIMENT-BODY-HASH", artifact)
	w14Assert(t, "W14-REPORT-NOT-ACCEPTANCE", []any{"EXECUTION_REPORTED", nil}, []any{run.task["status"], run.task["acceptance_id"]}, Object{"run": run.run, "task": run.task, "artifact": artifact, "synthetic_observation": true})
	request := o.acceptance(run, artifact)
	bad := copyObject(request)
	bad["artifact_refs"] = []any{Object{"entity_type": "Artifact", "id": artifact["id"], "revision": artifact["revision"], "content_hash": Digest([]byte("wrong result"))}}
	code, denied, _ = f.request("POST", f.path("/acceptances"), ID(), testTag(run.task), bad)
	w14Assert(t, "W14-TAMPERED-RESULT-REJECT", 422, code, denied)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(run.task), request)
	w14Assert(t, "W14-INDEPENDENT-SERVICE-ACCEPTANCE", []any{"PASS", "ACCEPTED", "FIXTURE", "DETERMINISTIC_SERVICE"}, []any{receipt["verdict"], f.read("tasks", Str(task, "id"))["status"], receipt["measurement_mode"], receipt["independence_basis"]}, receipt)
	f.token = r.owner
	resultBody := Object{"run_ids": x["run_ids"], "results": results, "outcome": outcome, "acceptance_id": receipt["id"]}
	bad = copyObject(resultBody)
	bad["outcome"] = "IMPROVED"
	code, denied, _ = f.request("POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), bad)
	w14Assert(t, "W14-FALSE-IMPROVEMENT-REJECT", 422, code, denied)
	x = f.expect(200, "POST", f.path("/experiments/"+Str(x, "id")+"/result"), ID(), testTag(x), resultBody)
	w14Assert(t, "W14-LEGAL-NO-IMPROVEMENT", []any{"COMPLETED", "NO_IMPROVEMENT"}, []any{x["status"], x["outcome"]}, x)
	// A maximum-confidence synthetic Jev response cannot overrule a deterministic counterexample.
	decisionBody := w11Body(f, req)
	decisionBody["input_refs"] = append(append(Empty(), refs...), Ref(artifact, "Artifact"))
	decisionBody["input_hash"] = Hash(decisionBody["input_refs"])
	decisionBody["evidence_refs"] = append(Arr(decisionBody, "evidence_refs"), Ref(artifact, "Artifact"))
	decisionBody["deterministic_results"] = []any{w11FailCheck("Candidate did not meet frozen improvement threshold", artifact)}
	provider, startup := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(w11Response()))
	}))
	t.Cleanup(provider.Close)
	abstained, e := f.s.InvokeJev(context.Background(), r.owner, f.project, decisionBody, decision.Client{URL: provider.URL, Fixture: true, Timeout: 5 * time.Second})
	if e != nil {
		t.Fatal(e)
	}
	w14Assert(t, "W14-COUNTEREVIDENCE-BLOCKS-HIGH-SCORE", []any{"ABSTAIN", "ADVISORY"}, []any{abstained["status"], abstained["mode"]}, Object{"decision": abstained, "provider_startup": startup, "provider_is_synthetic_loopback": true})
	decisionBody["deterministic_results"], decisionBody["signals"] = Empty(), Empty()
	decisionBody["selected"], decisionBody["rationale"] = "REJECT", "Fixed paired observations show no measured gain; retain baseline"
	decisionBody["scope"].(map[string]any)["provider"] = "deterministic-fixture"
	finalDecision := f.expect(201, "POST", f.path("/decisions"), ID(), f.stateTag(), decisionBody)
	proposal := f.proposal([]any{Ref(finalDecision, "DecisionReceipt")})
	change := f.apply(proposal)
	w14Assert(t, "W14-NEGATIVE-DECISION-INDEPENDENTLY-APPLIED", []any{Ref(finalDecision, "DecisionReceipt")}, f.state()["current_decision_refs"], Object{"proposal": proposal, "applied": change})
	r.checkpoint(t, candidates, []any{x["id"]})
	_, e = f.s.ReviewResearchCandidate(context.Background(), r.owner, f.project, Str(r.cycle, "id"), candidates[0].(string), "fixture", "ADOPT", "unproven improvement", "", "")
	w14Fault(t, "W14-UNSUPPORTED-ADOPTION-REJECT", e, 422)
	for i, disposition := range []struct{ outcome, gap, revisit string }{{"REJECT", "", ""}, {"WATCH", "independent measurement missing", "new measurement"}, {"INCONCLUSIVE", "unknown primary origin", "primary-origin review"}} {
		review, err := f.s.ReviewResearchCandidate(context.Background(), r.owner, f.project, Str(r.cycle, "id"), candidates[i].(string), "fixture", disposition.outcome, "Synthetic source does not establish an improvement", disposition.gap, disposition.revisit)
		if err != nil {
			t.Fatal(err)
		}
		w14Emit(t, "service", Object{"operation": "ReviewResearchCandidate", "review": review})
	}
	f.token = r.owner
	followBody := copyObject(taskBody)
	followBody["title"], followBody["task_type"], followBody["stage"], followBody["candidate_id"] = "Collect independent measurement only when new evidence exists", "json-verification", "follow_up", "next-evidence"
	followBody["input_refs"], followBody["acceptance_contract"] = []any{Ref(req, "Requirement"), Ref(artifact, "Artifact"), Ref(finalDecision, "DecisionReceipt")}, orchestrationContract()
	follow := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(f.read("goals", Str(goal, "id"))), followBody)
	f.token = r.scheduler
	r.cycle = f.expect(200, "POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/checkpoint"), ID(), testTag(r.cycle), Object{"source_coverage": r.cycle["source_coverage"], "candidate_evidence_ids": candidates, "required_experiment_ids": []any{x["id"]}, "decision_ids": []any{finalDecision["id"]}, "follow_up_task_ids": []any{follow["id"]}, "checkpoint_artifact_id": nil})
	r.close(t, "COMPLETE")
	w14Assert(t, "W14-NEGATIVE-CYCLE-COMPLETE", "COMPLETE", r.cycle["status"], r.cycle)
	release := f.expect(201, "POST", f.path("/releases"), ID(), f.stateTag(), Object{"scope": "PROJECT", "software_version": nil, "summary": "W14 fixture: no measured gain, baseline retained", "changes": []any{"Independent service checked fixed paired observations"}, "decision_ids": []any{finalDecision["id"]}, "artifact_refs": []any{Ref(artifact, "Artifact")}, "acceptance_ids": []any{receipt["id"]}, "open_issues": []any{"Synthetic fixture only; no real provider or A13 qualification"}, "next_steps": []any{Str(follow, "title")}, "policy_revision": f.state()["policy_revision"], "supersedes_id": nil})
	f.token = r.owner
	state, progress := f.state(), f.expect(200, "GET", f.path("/progress"), "", "", nil)
	notices := f.expect(200, "GET", f.path("/notifications"), "", "", nil)
	w14Assert(t, "W14-RELEASE-NOTIFICATION-STATE", []any{release["id"], 1, release["id"]}, []any{state["latest_release_id"], len(Arr(notices, "items")), Arr(notices, "items")[0].(map[string]any)["release_id"]}, Object{"release": release, "progress": progress, "notifications": notices, "state": state})
	checkpoint := Object{"project_id": f.project, "goal_id": goal["id"], "task_id": task["id"], "cycle_id": r.cycle["id"], "experiment_id": x["id"], "decision_id": finalDecision["id"], "release_id": release["id"], "follow_up_id": follow["id"], "artifact_ref": Ref(artifact, "Artifact"), "acceptance_id": receipt["id"], "expected_next_step": follow["title"], "state_hash": Hash(state), "progress_hash": Hash(progress), "cycle_hash": Hash(r.cycle), "release_hash": Hash(release), "notifications_hash": Hash(notices), "first_process_pid": os.Getpid()}
	checkpoint["goal_hash"] = Hash(f.read("goals", Str(goal, "id")))
	if e = os.WriteFile(filepath.Join(os.Getenv("W14_EVIDENCE_DIR"), "checkpoint.json"), Bytes(checkpoint), 0600); e != nil {
		t.Fatal(e)
	}
	w14Emit(t, "checkpoint", checkpoint)
}

func TestW14SessionResume(t *testing.T) {
	f := w14Setup(t, true)
	raw, e := os.ReadFile(filepath.Join(os.Getenv("W14_EVIDENCE_DIR"), "checkpoint.json"))
	if e != nil {
		t.Fatal(e)
	}
	checkpoint, e := Decode(raw)
	if e != nil {
		t.Fatal(e)
	}
	f.project = Str(checkpoint, "project_id")
	for _, item := range []struct{ path, key string }{{"/state", "state_hash"}, {"/goals/" + Str(checkpoint, "goal_id"), "goal_hash"}, {"/progress", "progress_hash"}, {"/research-cycles/" + Str(checkpoint, "cycle_id"), "cycle_hash"}, {"/releases/" + Str(checkpoint, "release_id"), "release_hash"}, {"/notifications", "notifications_hash"}} {
		current := f.expect(200, "GET", f.path(item.path), "", "", nil)
		w14Assert(t, "W14-NEW-SESSION-"+strings.ToUpper(item.key), checkpoint[item.key], Hash(current), current)
	}
	follow := f.read("tasks", Str(checkpoint, "follow_up_id"))
	w14Assert(t, "W14-NEW-SESSION-NEXT-STEP", checkpoint["expected_next_step"], follow["title"], Object{"follow_up": follow, "pid": os.Getpid(), "prior_pid": checkpoint["first_process_pid"], "background_resupplied": 0})
	prior, _ := Num(checkpoint, "first_process_pid")
	w14Assert(t, "W14-NEW-PROCESS", true, int64(os.Getpid()) != prior, nil)
}

func TestW14MissingSource(t *testing.T) {
	f := w14Setup(t, true)
	r := w14Research(t, f, false)
	r.start(t, time.Now().UTC().Add(-time.Minute).Truncate(time.Second))
	r.capture(t, "GITHUB", false)
	r.capture(t, "PAPER", false)
	r.checkpoint(t, Empty(), Empty())
	status, result, _ := f.request("POST", f.path("/research-cycles/"+Str(r.cycle, "id")+"/close"), ID(), testTag(r.cycle), Object{"requested_status": "COMPLETE", "outcome_summary": "missing required X cannot complete"})
	w14Assert(t, "W14-MISSING-SOURCE-REJECT", 422, status, result)
	r.close(t, "PARTIAL")
	w14Assert(t, "W14-MISSING-SOURCE-HONEST-PARTIAL", "PARTIAL", r.cycle["status"], r.cycle)
}
