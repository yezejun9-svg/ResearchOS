//go:build windows

package domain

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// Dedicated deterministic GoalBrief producer. No external provider is involved.
func TestIntentNativeChild(t *testing.T) {
	child := false
	for _, arg := range os.Args {
		child = child || arg == "--intent-child"
	}
	if !child {
		return
	}
	raw, e := os.ReadFile(os.Args[len(os.Args)-1])
	if e != nil {
		os.Exit(70)
	}
	request, e := Decode(raw)
	if e != nil {
		os.Exit(71)
	}
	fmt.Printf("{\"sequence\":1,\"type\":\"context.ready\",\"payload\":{\"input_hash\":%q}}\n", Digest(raw))
	output := []byte(`{"result":"verified"}`)
	if request["task_type"] == "intent_planning" {
		ctx, ok := request["context"].(map[string]any)
		if !ok {
			os.Exit(72)
		}
		_, tail, ok := strings.Cut(Str(ctx, "summary"), "Preserve this exact USER_STATED intent: ")
		if !ok {
			os.Exit(73)
		}
		statement, _, ok := strings.Cut(tail, ". Never promote suggestions to facts.")
		if !ok {
			os.Exit(74)
		}
		req, e := Decode([]byte(statement))
		if e != nil {
			os.Exit(75)
		}
		output = Bytes(intentBriefFromContext(req, ctx, true))
	}
	if e = os.WriteFile("result.json", output, 0600); e != nil {
		os.Exit(76)
	}
	fmt.Println(`{"sequence":2,"type":"turn.completed"}`)
	os.Exit(0)
}

func TestIntentQualifiedNativePlannerToBusinessDAG(t *testing.T) {
	c, route, qualification := intentNativeCoordinatorFixture(t, false, false)
	qualifyNativeCoordinator(t, c, route, qualification)
	f := qualification.f
	f.token = qualification.ownerToken
	req := f.expect(201, "POST", f.path("/requirements"), ID(), f.stateTag(), Object{"requirement_key": "INTENT-" + ID(), "text": `请先后生成两份 {"result":"verified"} JSON 报告。`, "basis": "USER_STATED", "source_refs": Empty(), "rationale": "native intent fixture Owner", "supersedes_id": nil, "acceptance_check_ids": Empty()})
	req = f.expect(200, "POST", f.path("/requirements/"+Str(req, "id")+"/actions"), ID(), testTag(req), Object{"action": "ACCEPT", "reason": "confirmed natural statement", "source_validation_refs": Empty()})
	var gid, tid string
	if e := f.db.QueryRow("SELECT planning_goal,planning_task FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&gid, &tid); e != nil {
		t.Fatal(e)
	}
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	route.ExecutorID = executor
	route.ExecutorToken, _ = f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	task := f.read("tasks", tid)
	if task["status"] != "BLOCKED" || task["active_run_id"] != nil {
		t.Fatal("missing purpose launched planner")
	}
	if e := f.s.AuthorizeRuntimePurpose(context.Background(), qualification.ownerToken, f.project, route.RuntimeID, "intent_planning", time.Now().Add(20*time.Minute)); e != nil {
		t.Fatal(e)
	}
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	task = f.read("tasks", tid)
	if task["status"] != "EXECUTION_REPORTED" {
		t.Fatalf("planner not reported: %s", Bytes(task))
	}
	run := f.read("runs", Str(task, "active_run_id"))
	artifact := f.read("artifacts", Arr(task, "output_artifact_ids")[0].(string))
	if artifact["evidence_kind"] != "GENERATED" || artifact["measurement_mode"] != "FIXTURE" {
		t.Fatal("fixture proposal promoted to live/observed")
	}
	o := &orchestrationFixture{f: f, goal: f.read("goals", gid), req: req, rt: qualification.registration, owner: qualification.ownerToken}
	r := &runtimeFixture{f: f, ownerToken: qualification.ownerToken, executor: executor, task: task, run: run, registration: qualification.registration}
	body := o.acceptance(r, artifact)
	prepared, err := f.s.prepareTaskAcceptance(context.Background(), f.token, f.project, body)
	if err != nil {
		t.Fatal(err)
	}
	if prepared.verdict != "PASS" {
		t.Fatalf("native planning checks: %s", Bytes(prepared.checks))
	}
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(task), body)
	receipt := acceptIntentGoal(o, r, body)
	var businessID, mappingRaw string
	if e := f.db.QueryRow("SELECT compiled_goal,node_mapping FROM intent_plan_bindings WHERE project=? AND requirement=?", f.project, req["id"]).Scan(&businessID, &mappingRaw); e != nil {
		t.Fatal(e)
	}
	mapping, _ := Decode([]byte(mappingRaw))
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	if first := f.read("tasks", Str(mapping, "first")); first["status"] != "BLOCKED" {
		t.Fatal("compiled node lacks current purpose but is not visibly blocked")
	}
	if e := f.s.AuthorizeRuntimePurpose(context.Background(), qualification.ownerToken, f.project, route.RuntimeID, "json_report", time.Now().Add(20*time.Minute)); e != nil {
		t.Fatal(e)
	}
	for _, logical := range []string{"first", "second"} {
		if e := c.Scan(context.Background()); e != nil {
			t.Fatal(e)
		}
		c.workers.Wait()
		select {
		case e := <-c.errors:
			t.Fatal(e)
		default:
		}
		node := f.read("tasks", Str(mapping, logical))
		if node["status"] != "EXECUTION_REPORTED" {
			t.Fatalf("business %s not reported %s", logical, Bytes(node))
		}
		nr := f.read("runs", Str(node, "active_run_id"))
		na := f.read("artifacts", Arr(node, "output_artifact_ids")[0].(string))
		normal := &runtimeFixture{f: f, executor: executor, task: node, run: nr, registration: qualification.registration}
		request := o.acceptance(normal, na)
		f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(node), request)
	}
	var runs int
	f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind='Run' AND json_extract(body,'$.task_id')=?", tid).Scan(&runs)
	if runs != 1 {
		t.Fatal("planner replay launched more than once")
	}
	t.Logf("I1-NATIVE: actual AppContainer planner run=%s brief=%s accepted_goal_receipt=%s business_goal=%s both_business_nodes_accepted=true mode=FIXTURE no_model_accuracy_claim=true", run["id"], artifact["id"], receipt["id"], businessID)
}

func intentNativeCoordinatorFixture(t *testing.T, effect, checkpoint bool, flags ...string) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	t.Helper()
	f := contextFixture(t)
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
	argv := []any{"-test.run=^TestIntentNativeChild$", "--", "--intent-child"}
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
	profile := f.artifact(Object{"runtime_id": registration["id"], "technical_hash": runtimeTechnicalHash(registration), "adapter": registration["adapter"], "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "build_hash": Digest(binary), "sandbox": runtimeSandboxProfile, "credential_revision": "none", "backend": "native-offline", "model": "none", "command_id": "native-fixture", "argv": argv, "effect_routes": []any{Object{"id": "fixture-echo", "capability": "fixture.echo", "credential_revision": "test-v1", "upper_bound": dollars("1")}}, "permissions": Object{"network": "none", "environment": "staging-only", "capabilities": Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": timeoutSeconds, "outputs": []any{"result.json"}}, Empty())
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
	t.Cleanup(func() { c.Close() })
	return c, route, &runtimeFixture{f: f, ownerToken: f.token, executor: executor, lease: lease, run: run, task: task, registration: registration}
}
