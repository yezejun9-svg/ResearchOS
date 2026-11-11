//go:build windows

package domain

import (
	"bufio"
	"context"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"researchos.local/research-os/adapters/sources"
	"strings"
	"testing"
	"time"
)

func TestResearchNativeChild(t *testing.T) {
	child := false
	for _, arg := range os.Args {
		child = child || arg == "--research-child"
	}
	if !child {
		return
	}
	raw, err := os.ReadFile(os.Args[len(os.Args)-1])
	if err != nil {
		os.Exit(70)
	}
	request, err := Decode(raw)
	if err != nil {
		os.Exit(71)
	}
	fmt.Printf("{\"sequence\":1,\"type\":\"context.ready\",\"payload\":{\"input_hash\":%q}}\n", Digest(raw))
	output := []byte(`{"result":"verified"}`)
	sequence := 2
	switch request["task_type"] {
	case "intent_planning":
		ctx := request["context"].(map[string]any)
		_, tail, _ := strings.Cut(Str(ctx, "summary"), "Preserve this exact USER_STATED intent: ")
		statement, _, _ := strings.Cut(tail, ". Never promote suggestions to facts.")
		req, err := Decode([]byte(statement))
		if err != nil {
			os.Exit(72)
		}
		_, tail, _ = strings.Cut(Str(ctx, "summary"), "Current profile=")
		profileText, policyText, _ := strings.Cut(tail, "; run_policy=")
		policyText, _, _ = strings.Cut(policyText, ". Use exactly one node")
		profile, err := Decode([]byte(profileText))
		if err != nil {
			os.Exit(73)
		}
		policy, err := Decode([]byte(policyText))
		if err != nil {
			os.Exit(74)
		}
		output = Bytes(monitorBriefCurrent(req, ctx, profile, policy))
	case "research_discovery":
		work := request["research_work"].(map[string]any)
		params := work["parameters"].(map[string]any)
		reader := bufio.NewReader(os.Stdin)
		for repeat := 0; repeat < 2; repeat++ {
			frame := Object{"sequence": sequence, "type": "effect.request", "key": "source-" + Str(work, "logical_key"), "route": "research-source-" + Str(params, "source_id"), "capability": "SOURCE", "payload": Object{"logical_key": work["logical_key"]}}
			fmt.Println(string(Bytes(frame)))
			line, err := reader.ReadBytes('\n')
			if err != nil {
				os.Exit(75)
			}
			response, err := Decode(line)
			if err != nil || response["state"] != "CONFIRMED" {
				fmt.Fprintln(os.Stderr, string(line))
				os.Exit(76)
			}
			output = Bytes(response["payload"])
			sequence++
		}
	case "research_delivery", "research_verification", "research_review":
		output = Bytes(request["research_facts"])
	}
	if err = os.WriteFile("result.json", output, 0600); err != nil {
		os.Exit(77)
	}
	fmt.Println(string(Bytes(Object{"sequence": sequence, "type": "turn.completed"})))
	os.Exit(0)
}

func TestResearchNativeSourceReceiptToIndependentClose(t *testing.T) {
	c, route, qualification := researchNativeCoordinatorFixture(t, false, false)
	qualifyNativeCoordinator(t, c, route, qualification)
	f := qualification.f
	f.token = qualification.ownerToken
	owner := f.token
	executor := ID()
	if err := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	route.ExecutorID = executor
	route.ExecutorToken, _ = f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	for _, purpose := range []string{"intent_planning", "research_discovery", "research_delivery"} {
		if err := f.s.AuthorizeRuntimePurpose(context.Background(), owner, f.project, route.RuntimeID, purpose, time.Now().Add(20*time.Minute)); err != nil {
			t.Fatal(err)
		}
	}
	f.token = owner
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": monitorStatement, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "Owner requests existing bounded monitoring", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "explicit current monitoring", "source_validation_refs": Empty()})
	var gid, tid string
	if err := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); err != nil {
		t.Fatal(err)
	}
	o := &orchestrationFixture{f: f, owner: owner, req: req, goal: f.read("goals", gid), rt: qualification.registration}
	scan := func() {
		t.Helper()
		if err := c.Scan(context.Background()); err != nil {
			t.Fatal(err)
		}
		c.workers.Wait()
		select {
		case err := <-c.errors:
			t.Fatal(err)
		default:
		}
	}
	accept := func(id string) (*runtimeFixture, Object) {
		t.Helper()
		f.token = owner
		task := f.read("tasks", id)
		if task["status"] != "EXECUTION_REPORTED" {
			t.Fatalf("native stage not reported: %s", Bytes(task))
		}
		run := f.read("runs", Str(task, "active_run_id"))
		artifact := f.read("artifacts", Arr(task, "output_artifact_ids")[0].(string))
		r := &runtimeFixture{f: f, ownerToken: owner, executor: executor, task: task, run: run, registration: qualification.registration}
		body := o.acceptance(r, artifact)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(task), body)
		return r, body
	}
	scan()
	planner, body := accept(tid)
	acceptIntentGoal(o, planner, body)
	calls := 0
	c.sourceFixtureAdapter = func(config Object) sources.Adapter {
		calls++
		endpoint := map[string]string{"GITHUB": "https://api.github.com/repos/researchos/research/releases", "PAPER": "https://export.arxiv.org/api/query"}[Str(config, "kind")]
		return sourceFixtureAdapter{sources.Page{RawResponse: Bytes(Object{"fixture": "offline explicit empty source page", "kind": config["kind"]}), RawMediaType: "application/json", Complete: true, HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{endpoint}, FinalURLs: []string{endpoint}}}
	}
	scan()
	rows, err := f.db.Query("SELECT task FROM research_cycle_work WHERE project=? AND stage='discovery' ORDER BY task", f.project)
	if err != nil {
		t.Fatal(err)
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			t.Fatal(err)
		}
		ids = append(ids, id)
	}
	rows.Close()
	accepted := 0
	for tick := 0; tick < 3 && accepted < 2; tick++ {
		for _, id := range ids {
			f.token = owner
			task := f.read("tasks", id)
			if task["status"] != "EXECUTION_REPORTED" {
				continue
			}
			accept(id)
			accepted++
		}
		if accepted < 2 {
			scan()
		}
	}
	if accepted != 2 || calls != 2 {
		t.Fatalf("exactly two captures, each repeated bridge request replays once: accepted=%d calls=%d", accepted, calls)
	}
	scan()
	var reportID, cycleID string
	if err = f.db.QueryRow("SELECT task,cycle FROM research_cycle_work WHERE project=? AND stage='delivery'", f.project).Scan(&reportID, &cycleID); err != nil {
		t.Fatal(err)
	}
	accept(reportID)
	scan()
	f.token = owner
	cycle := f.read("research-cycles", cycleID)
	if cycle["status"] != "PARTIAL" || f.read("tasks", reportID)["status"] != "ACCEPTED" {
		t.Fatalf("truthful cycle close failed: %s", Bytes(cycle))
	}
	var total, unknown int
	if err = f.db.QueryRow("SELECT count(*),coalesce(sum(json_extract(body,'$.cost_basis')='UNKNOWN' AND json_type(body,'$.money')='null'),0) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry'", f.project).Scan(&total, &unknown); err != nil || unknown < 4 {
		t.Fatalf("SOURCE cost must remain unknown: total=%d unknown=%d err=%v", total, unknown, err)
	}
	t.Logf("I2-NATIVE: actual Scan/AppContainer/typed SOURCE capture transactions; 2 source calls with ACK replay; 2 independent source acceptances; missing X remains explicit; report independently ACCEPTED; cycle=%s PARTIAL; billing UNKNOWN/null; external provider=false FIXTURE", cycleID)
}

func researchNativeCoordinatorFixture(t *testing.T, effect, checkpoint bool, flags ...string) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	t.Helper()
	rf := researchSetup(t, false)
	f := rf.f
	req := f.requirement()
	exe, e := os.Executable()
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(exe)
	if e != nil {
		t.Fatal(e)
	}
	registration := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "native coordinator fixture", "adapter": "codex-cli", "adapter_revision": runtimeBridgeRevision, "capabilities": []any{"start", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	argv := []any{"-test.run=^TestResearchNativeChild$", "--", "--research-child"}
	if effect {
		argv = append(argv, "--effect")
	}
	if checkpoint {
		argv = append(argv, "--checkpoint")
	}
	timeoutSeconds := 15
	for _, flag := range flags {
		argv = append(argv, flag)
		if flag == "--wait-heartbeat" {
			timeoutSeconds = 25
		}
	}
	argv = append(argv, "{manifest}")
	effectRoutes := Empty()
	for _, sourceID := range rf.ids {
		effectRoutes = append(effectRoutes, Object{"id": "research-source-" + sourceID, "capability": "SOURCE", "credential_revision": "fixture-source-v1", "upper_bound": nil})
	}
	profile := f.artifact(Object{"runtime_id": registration["id"], "technical_hash": runtimeTechnicalHash(registration), "adapter": registration["adapter"], "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "build_hash": Digest(binary), "sandbox": runtimeSandboxProfile, "credential_revision": "none", "backend": "native-offline", "model": "none", "command_id": "native-fixture", "argv": argv, "effect_routes": effectRoutes, "permissions": Object{"network": "none", "environment": "staging-only", "capabilities": Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": timeoutSeconds, "outputs": []any{"result.json"}}, Empty())
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "runtime qualification", "original_intent": "verify native coordinator", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"runtime"}, "deliverables": []any{"receipt"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "approved native fixture"})
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "runtime qualification", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": []any{Ref(profile, "Artifact")}, "acceptance_contract": orchestrationContract(), "origin_problem_id": "runtime", "candidate_id": "runtime", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	executor := ID()
	scheduler := ID()
	for _, p := range []Principal{{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(task, "id")}}}, {ID: scheduler, Roles: []string{"SCHEDULER"}, Grants: []Grant{{ProjectID: f.project}}}} {
		if e = f.s.ProvisionPrincipal(context.Background(), p); e != nil {
			t.Fatal(e)
		}
	}
	if e = f.s.RegisterRuntimeQualificationPlan(context.Background(), f.token, f.project, Str(task, "id"), Str(registration, "id"), Ref(profile, "Artifact"), []any{"start", "context_rebuild"}, time.Hour, ""); e != nil {
		t.Fatal(e)
	}
	run, lease, e := f.s.BeginRuntimeQualification(context.Background(), f.token, f.project, Str(task, "id"), Str(registration, "id"), executor)
	if e != nil {
		t.Fatal(e)
	}
	executorToken, e := f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	schedulerToken, e := f.s.IssueCredential(context.Background(), scheduler, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/__researchos_fixture_readiness__" {
			w.WriteHeader(404)
			return
		}
		f.h.ServeHTTP(w, r)
	}))
	t.Cleanup(server.Close)
	var dbPath string
	var seq int
	var name string
	if e = f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); e != nil {
		t.Fatal(e)
	}
	route := RuntimeCoordinatorRoute{ProjectID: f.project, RuntimeID: Str(registration, "id"), ExecutorID: executor, ExecutorToken: executorToken, CommandID: "native-fixture", Executable: exe}
	c, e := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot: filepath.Dir(dbPath), APIURL: server.URL, SchedulerToken: schedulerToken, Routes: []RuntimeCoordinatorRoute{route}})
	if e != nil {
		t.Fatal(e)
	}
	for _, sourceID := range rf.ids {
		c.config.Providers = append(c.config.Providers, RuntimeProviderRoute{ID: "research-source-" + sourceID, ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "research_discovery", Capability: "SOURCE", CredentialRevision: "fixture-source-v1", MeasurementMode: "FIXTURE", SourceID: sourceID, SourceToken: rf.source})
	}
	t.Cleanup(func() { c.Close() })
	return c, route, &runtimeFixture{f: f, ownerToken: f.token, executor: executor, lease: lease, run: run, task: task, registration: registration}
}
