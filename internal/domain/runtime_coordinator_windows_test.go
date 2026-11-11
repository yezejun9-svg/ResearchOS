//go:build windows

package domain

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

type runtimeRoundTrip func(*http.Request) (*http.Response, error)

func (f runtimeRoundTrip) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestRuntimeCoordinatorChild(t *testing.T) {
	child := false
	for _, arg := range os.Args {
		if arg == "--coordinator-child" {
			child = true
		}
	}
	if !child {
		return
	}
	raw, e := os.ReadFile(os.Args[len(os.Args)-1])
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		os.Exit(70)
	}
	if os.Getenv("RUNTIME_SECRET_SENTINEL") != "" {
		os.Exit(71)
	}
	fmt.Printf("{\"sequence\":1,\"type\":\"context.ready\",\"payload\":{\"input_hash\":%q}}\n", Digest(raw))
	request, e := Decode(raw)
	if e != nil {
		os.Exit(73)
	}
	sequence := 2
	checkpointMode := false
	for _, arg := range os.Args {
		if arg == "--wait-heartbeat" && request["task_type"] != "runtime_qualification" {
			time.Sleep(19 * time.Second)
		}
		if arg == "--exit-one" && request["task_type"] != "runtime_qualification" {
			os.Exit(1)
		}
		if arg == "--checkpoint" {
			checkpointMode = true
		}
	}
	if checkpointMode && request["task_type"] != "runtime_qualification" {
		if request["checkpoint_artifact_id"] == nil || request["checkpoint_artifact_id"] == "" {
			fmt.Printf("{\"sequence\":2,\"type\":\"checkpoint\",\"payload\":{\"cursor\":\"durable-fixture-position\"}}\n")
			line, err := bufio.NewReader(os.Stdin).ReadBytes('\n')
			if err != nil {
				os.Exit(76)
			}
			reply, err := Decode(line)
			if err != nil || reply["type"] != "checkpoint.sealed" {
				os.Exit(77)
			}
			fmt.Println(`{"sequence":3,"type":"turn.paused"}`)
			os.Exit(0)
		}
		checkpoint, err := os.ReadFile(filepath.Join(filepath.Dir(os.Args[len(os.Args)-1]), "checkpoint.json"))
		if err != nil || string(checkpoint) != `{"cursor":"durable-fixture-position"}` {
			os.Exit(78)
		}
	}
	effectMode := false
	for _, arg := range os.Args {
		if arg == "--effect" {
			effectMode = true
		}
	}
	if effectMode && request["task_type"] != "runtime_qualification" {
		reader := bufio.NewReader(os.Stdin)
		for repeat := 0; repeat < 2; repeat++ {
			fmt.Printf("{\"sequence\":%d,\"type\":\"effect.request\",\"key\":\"single-fixture-effect\",\"route\":\"fixture-echo\",\"capability\":\"fixture.echo\",\"payload\":{\"value\":\"approved\"}}\n", sequence)
			line, e := reader.ReadBytes('\n')
			if e != nil {
				os.Exit(74)
			}
			reply, e := Decode(line)
			if e != nil || reply["state"] != "CONFIRMED" || reply["payload"].(map[string]any)["echo"] != "approved" {
				os.Exit(75)
			}
			sequence++
		}
	}
	if e = os.WriteFile("result.json", []byte(`{"result":"verified"}`), 0600); e != nil {
		os.Exit(72)
	}
	fmt.Printf("{\"sequence\":%d,\"type\":\"turn.completed\"}\n", sequence)
	os.Exit(0)
}

func coordinatorFixture(t *testing.T) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	return coordinatorFixtureMode(t, false)
}
func coordinatorFixtureMode(t *testing.T, effect bool) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	return coordinatorFixtureOptions(t, effect, false)
}
func coordinatorFixtureOptions(t *testing.T, effect, checkpoint bool, flags ...string) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
	return coordinatorFixtureProgram(t, effect, checkpoint, nil, flags...)
}

func coordinatorFixtureProgram(t *testing.T, effect, checkpoint bool, program func(Object) (string, string), flags ...string) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture) {
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
	argv := []any{"-test.run=^TestRuntimeCoordinatorChild$", "--", "--coordinator-child"}
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
	profileBody := Object{"runtime_id": registration["id"], "technical_hash": runtimeTechnicalHash(registration), "adapter": registration["adapter"], "adapter_revision": runtimeBridgeRevision, "platform": "windows-amd64", "build_hash": Digest(binary), "sandbox": runtimeSandboxProfile, "credential_revision": "none", "backend": "native-offline", "model": "none", "command_id": "native-fixture", "argv": argv, "effect_routes": []any{Object{"id": "fixture-echo", "capability": "fixture.echo", "credential_revision": "test-v1", "upper_bound": dollars("1")}}, "permissions": Object{"network": "none", "environment": "staging-only", "capabilities": Empty(), "process_limit": 1, "memory_mib": 256}, "timeout_seconds": timeoutSeconds, "outputs": []any{"result.json"}}
	bundleFile := ""
	if program != nil {
		exe, bundleFile = program(profileBody)
	}
	profile := f.artifact(profileBody, Empty())
	contract := orchestrationContract()
	if profileBody["backend"] == runtimeMuBackend {
		contract = clientTurnContract()
	}
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "runtime qualification", "original_intent": "verify native coordinator", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"runtime"}, "deliverables": []any{"receipt"}, "acceptance_contract": contract})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "approved native fixture"})
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "runtime qualification", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": []any{Ref(profile, "Artifact")}, "acceptance_contract": contract, "origin_problem_id": "runtime", "candidate_id": "runtime", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
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
	route := RuntimeCoordinatorRoute{ProjectID: f.project, RuntimeID: Str(registration, "id"), ExecutorID: executor, ExecutorToken: executorToken, CommandID: Str(profileBody, "command_id"), Executable: exe, BundleFile: bundleFile}
	c, e := f.s.NewRuntimeCoordinator(context.Background(), RuntimeCoordinatorConfig{DataRoot: filepath.Dir(dbPath), APIURL: server.URL, SchedulerToken: schedulerToken, Routes: []RuntimeCoordinatorRoute{route}})
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { c.Close() })
	return c, route, &runtimeFixture{f: f, ownerToken: f.token, executor: executor, lease: lease, run: run, task: task, registration: registration}
}

func TestRuntimeCoordinatorNativeQualification(t *testing.T) {
	t.Setenv("RUNTIME_SECRET_SENTINEL", "host-only")
	c, route, r := coordinatorFixture(t)
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e != nil {
		var raw, dispatch string
		r.f.db.QueryRow("SELECT body FROM domain_objects WHERE kind='Run' AND id=?", r.run["id"]).Scan(&raw)
		r.f.db.QueryRow("SELECT identity||' '||state||' '||reason FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&dispatch)
		t.Fatalf("native coordinator: %v; run=%s dispatch=%s", e, raw, dispatch)
	}
	run := r.f.read("runs", Str(r.run, "id"))
	task := r.f.read("tasks", Str(r.task, "id"))
	if run["status"] != "SETTLED" || task["status"] != "EXECUTION_REPORTED" || task["acceptance_id"] != nil {
		t.Fatalf("unexpected lifecycle %v %v", run, task)
	}
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e == nil {
		t.Fatal("duplicate dispatch relaunched")
	}
	t.Logf("RUNTIME_NATIVE_COORDINATOR run=%s status=%s task=%s independent_acceptance_pending=true", run["id"], run["status"], task["status"])
}

func qualifyNativeCoordinator(t *testing.T, c *RuntimeCoordinator, route RuntimeCoordinatorRoute, r *runtimeFixture) {
	t.Helper()
	f := r.f
	if e := c.RunAdmitted(context.Background(), route, r.run, r.lease); e != nil {
		t.Fatal(e)
	}
	r.run = f.read("runs", Str(r.run, "id"))
	r.task = f.read("tasks", Str(r.task, "id"))
	a := f.read("artifacts", Arr(r.run, "result_artifact_ids")[0].(string))
	o := &orchestrationFixture{f: f, owner: r.ownerToken}
	body := o.acceptance(r, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), body)
	if receipt["verdict"] != "PASS" {
		t.Fatalf("native independent verification failed: %s", Bytes(receipt))
	}
	var raw string
	if e := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.kind')='LOG'", f.project, r.run["id"]).Scan(&raw); e != nil {
		t.Fatal(e)
	}
	log, e := Decode([]byte(raw))
	if e != nil {
		t.Fatal(e)
	}
	r.registration = f.expect(200, "POST", f.path("/runtimes/"+Str(r.registration, "id")+"/qualify"), ID(), testTag(r.registration), Object{"qualification_ids": []any{receipt["id"]}, "supports_resume": false, "resume_evidence_ref": nil, "receipt_artifact_ref": Ref(log, "Artifact")})
	if r.registration["status"] != "AVAILABLE" {
		t.Fatal("native runtime unavailable")
	}
}

func TestRuntimeCoordinatorReadyToIndependentAcceptance(t *testing.T) {
	coordinatorReadyChain(t, false)
}
func TestRuntimeCoordinatorTypedBroker(t *testing.T) { coordinatorReadyChain(t, true) }
func coordinatorReadyChain(t *testing.T, effect bool) {
	c, route, r, o := nativeNormalFixture(t, effect)
	f := r.f
	task := r.task
	executor := route.ExecutorID
	var e error
	var calls atomic.Int32
	if effect {
		provider, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, request *http.Request) {
			if request.URL.Path == "/__researchos_fixture_readiness__" {
				w.WriteHeader(404)
				return
			}
			calls.Add(1)
			if request.Header.Get("Authorization") != "Bearer host-fixture-secret" {
				w.WriteHeader(403)
				return
			}
			var body Object
			if e := json.NewDecoder(request.Body).Decode(&body); e != nil {
				w.WriteHeader(400)
				return
			}
			json.NewEncoder(w).Encode(Object{"key": body["key"], "epoch": body["epoch"], "run_id": body["run_id"], "receipt_id": "fixture-receipt-one", "state": "CONFIRMED", "actual_cost": dollars("1.25"), "payload": Object{"echo": "approved"}})
		}))
		defer provider.Close()
		c.config.Providers = []RuntimeProviderRoute{{ID: "fixture-echo", ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "json-verification", Capability: "fixture.echo", CredentialRevision: "test-v1", Endpoint: provider.URL, BearerToken: "host-fixture-secret", UpperBound: dollars("1"), MeasurementMode: "FIXTURE"}}
	}
	if e = c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	task = f.read("tasks", Str(task, "id"))
	if task["status"] != "EXECUTION_REPORTED" {
		var reason, state string
		f.db.QueryRow("SELECT reason,state FROM runtime_dispatches WHERE run=?", task["active_run_id"]).Scan(&reason, &state)
		t.Fatalf("native normal not reported: %s dispatch=%s/%s", Bytes(task), state, reason)
	}
	run := f.read("runs", Str(task, "active_run_id"))
	a := f.read("artifacts", Arr(run, "result_artifact_ids")[0].(string))
	normal := &runtimeFixture{f: f, ownerToken: r.ownerToken, executor: executor, run: run, task: task, registration: r.registration}
	body := o.acceptance(normal, a)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(task), body)
	if receipt["verdict"] != "PASS" || f.read("tasks", Str(task, "id"))["status"] != "ACCEPTED" {
		t.Fatalf("native normal acceptance failed: %s", Bytes(receipt))
	}
	t.Logf("RUNTIME_READY_CHAIN admission=qualified dispatch=atomic native=AppContainer heartbeat=HTTP upload=HTTP seal=HTTP report=HTTP independent_acceptance=PASS measurement_mode=FIXTURE run=%s", run["id"])
	if effect {
		if calls.Load() != 1 {
			t.Fatalf("logical effect repeated: %d", calls.Load())
		}
		var amount string
		if e = f.db.QueryRow("SELECT json_extract(body,'$.money.amount') FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.operation')='RECONCILE'", f.project, run["id"]).Scan(&amount); e != nil || amount != "1.25" {
			t.Fatalf("actual effect cost missing: %s %v", amount, e)
		}
		t.Log("RUNTIME_TYPED_BROKER requests=2 provider_calls=1 reservation=1 actual_cost=1.25 host_credentials_not_in_child=true")
	}
}

func nativeNormalFixture(t *testing.T, effect bool) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, *orchestrationFixture) {
	c, route, r := coordinatorFixtureMode(t, effect)
	return nativeNormalFrom(t, c, route, r)
}
func nativeNormalFrom(t *testing.T, c *RuntimeCoordinator, route RuntimeCoordinatorRoute, r *runtimeFixture) (*RuntimeCoordinator, RuntimeCoordinatorRoute, *runtimeFixture, *orchestrationFixture) {
	qualifyNativeCoordinator(t, c, route, r)
	f := r.f
	f.token = r.ownerToken
	req := f.read("requirements", Arr(r.task, "requirement_refs")[0].(map[string]any)["id"].(string))
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "native normal flow", "original_intent": "execute qualified native task", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"orchestration-problem"}, "deliverables": []any{"verified JSON"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "native fixture"})
	o := &orchestrationFixture{f: f, goal: goal, req: req, rt: r.registration, owner: r.ownerToken}
	task := o.task("native-normal", Empty(), r.task["input_refs"].([]any))
	if e := f.s.AuthorizeRuntimePurpose(context.Background(), r.ownerToken, f.project, route.RuntimeID, "json-verification", time.Now().Add(30*time.Minute)); e != nil {
		t.Fatal(e)
	}
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	route.ExecutorID = executor
	route.ExecutorToken = token
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	return c, route, &runtimeFixture{f: f, ownerToken: r.ownerToken, executor: executor, task: task, registration: r.registration}, o
}

func TestRuntimeCoordinatorSkipsUnrelatedReady(t *testing.T) {
	c, route, r, o := nativeNormalFixture(t, false)
	f := r.f
	first := r.task
	second := o.task("permitted-second-ready", Empty(), Arr(first, "input_refs"))
	route.ExecutorID = ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: route.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(second, "id")}}}); e != nil {
		t.Fatal(e)
	}
	var e error
	route.ExecutorToken, e = f.s.IssueCredential(context.Background(), route.ExecutorID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	if f.read("tasks", Str(first, "id"))["status"] != "READY" || f.read("tasks", Str(second, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatal("unrelated READY task starved authorized later candidate")
	}
	t.Log("RUNTIME_READY_SELECTION first_without_executor_grant=READY second_with_grant=EXECUTION_REPORTED")
}

func TestRuntimeCoordinatorCheckpointResume(t *testing.T) {
	c, route, qualification := coordinatorFixtureOptions(t, false, true)
	c, route, r, _ := nativeNormalFrom(t, c, route, qualification)
	f := r.f
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	task := f.read("tasks", Str(r.task, "id"))
	run := f.read("runs", Str(task, "active_run_id"))
	if Str(run, "checkpoint_artifact_id") == "" || task["status"] != "RUNNING" {
		t.Fatalf("checkpoint not durably attached: %s", Bytes(run))
	}
	oldEpoch, _ := Num(run, "lease_epoch")
	revision, _ := Num(run, "revision")
	resumed, e := f.s.ResumeCheckpoint(context.Background(), c.config.SchedulerToken, f.project, Str(run, "id"), ID(), revision)
	if e != nil {
		t.Fatal(e)
	}
	next := resumed["run"].(map[string]any)
	newEpoch, _ := Num(next, "lease_epoch")
	if next["id"] != run["id"] || newEpoch != oldEpoch+1 || resumed["native_resume"] != false || next["checkpoint_artifact_id"] != run["checkpoint_artifact_id"] {
		t.Fatalf("resume identity changed: %s", Bytes(resumed))
	}
	if e = c.RunAdmitted(context.Background(), route, next, Str(resumed, "lease_token")); e != nil {
		t.Fatal(e)
	}
	completed := f.read("runs", Str(run, "id"))
	var count int
	if e = f.db.QueryRow("SELECT count(*) FROM runtime_dispatches WHERE project=? AND run=?", f.project, run["id"]).Scan(&count); e != nil || count != 2 || completed["status"] != "SETTLED" {
		t.Fatalf("explicit resume incomplete dispatches=%d run=%s err=%v", count, Bytes(completed), e)
	}
	t.Log("RUNTIME_CHECKPOINT_RESUME same_run=true epoch=1_to_2 checkpoint_carried=true context_rebuilt=true native_resume=false dispatch_count=2")
}

func TestRuntimeCoordinatorConcurrentSealConflict(t *testing.T) {
	c, route, r, o := nativeNormalFixture(t, false)
	f := r.f
	second := o.task("second-concurrent-task", Empty(), Arr(r.task, "input_refs"))
	other := route
	other.ExecutorID = ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: other.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(second, "id")}}}); e != nil {
		t.Fatal(e)
	}
	var e error
	other.ExecutorToken, e = f.s.IssueCredential(context.Background(), other.ExecutorID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	c.config.Routes = append(c.config.Routes, other)
	var stateReads, stale atomic.Int32
	barrier := make(chan struct{})
	c.client.Transport = runtimeRoundTrip(func(req *http.Request) (*http.Response, error) {
		res, err := http.DefaultTransport.RoundTrip(req)
		if err != nil {
			return nil, err
		}
		if req.Method == "GET" && strings.HasSuffix(req.URL.Path, "/state") {
			n := stateReads.Add(1)
			if n == 2 {
				close(barrier)
			}
			if n <= 2 {
				select {
				case <-barrier:
				case <-req.Context().Done():
					return nil, req.Context().Err()
				}
			}
		}
		if req.Method == "POST" && strings.HasSuffix(req.URL.Path, "/artifacts") && res.StatusCode == 412 {
			stale.Add(1)
		}
		return res, nil
	})
	if e = c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	if stale.Load() == 0 || f.read("tasks", Str(r.task, "id"))["status"] != "EXECUTION_REPORTED" || f.read("tasks", Str(second, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatalf("concurrent seal did not recover known stale tag: 412=%d", stale.Load())
	}
	t.Logf("RUNTIME_CONCURRENT_SEAL workers=2 known_412=%d both_reported=true transport_retry=false", stale.Load())
}

func TestRuntimeCoordinatorPurposeRevocation(t *testing.T) {
	for _, boundary := range []string{"before_launch_fence", "dispatch_started"} {
		t.Run(boundary, func(t *testing.T) {
			c, _, r, _ := nativeNormalFixture(t, false)
			f := r.f
			c.boundaryHook = func(name string, _ Object) {
				if name == boundary {
					_, e := f.db.Exec("UPDATE resource_route_grants SET body=json_set(body,'$.expires_at',?) WHERE project=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), f.project)
					if e != nil {
						t.Error(e)
					}
				}
			}
			if e := c.Scan(context.Background()); e != nil {
				t.Fatal(e)
			}
			c.workers.Wait()
			select {
			case <-c.errors:
			default:
				t.Fatal("revoked authority allowed native execution")
			}
			task := f.read("tasks", Str(r.task, "id"))
			var identity string
			if e := f.db.QueryRow("SELECT identity FROM runtime_dispatches WHERE run=?", task["active_run_id"]).Scan(&identity); e != nil {
				t.Fatal(e)
			}
			if identity != "{}" || task["status"] != "RUNNING" {
				t.Fatalf("authority expiry crossed ResumeThread: identity=%s task=%s", identity, task["status"])
			}
			t.Log("RUNTIME_AUTHORITY_EXPIRY native_resumed=false task_reported=false")
		})
	}
}

func TestRuntimeCoordinatorFailedExitReleasesExecutor(t *testing.T) {
	c, route, q := coordinatorFixtureOptions(t, false, false, "--exit-one")
	c, _, r, o := nativeNormalFrom(t, c, route, q)
	f := r.f
	second := o.task("next-after-failure", Empty(), Arr(r.task, "input_refs"))
	for _, task := range []Object{r.task, second} {
		if e := c.Scan(context.Background()); e != nil {
			t.Fatal(e)
		}
		c.workers.Wait()
		select {
		case e := <-c.errors:
			t.Fatal(e)
		default:
		}
		current := f.read("tasks", Str(task, "id"))
		run := f.read("runs", Str(current, "active_run_id"))
		if run["status"] != "FAILED" || Hash(run["exit_code"]) != Hash(1) {
			t.Fatalf("nonzero exit not reported: %s", Bytes(run))
		}
	}
	t.Log("RUNTIME_FAILED_EXIT run_status=FAILED exit_code=1 next_ready_dispatched=true executor_not_starved=true")
}

func TestRuntimeCoordinatorBrokerFailure(t *testing.T) {
	for _, mode := range []string{"provider_unavailable", "purpose_expired_after_prepare"} {
		t.Run(mode, func(t *testing.T) {
			c, route, r, _ := nativeNormalFixture(t, true)
			f := r.f
			var calls atomic.Int32
			provider, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
				if req.URL.Path == "/__researchos_fixture_readiness__" {
					w.WriteHeader(404)
					return
				}
				calls.Add(1)
				w.WriteHeader(503)
			}))
			defer provider.Close()
			c.config.Providers = []RuntimeProviderRoute{{ID: "fixture-echo", ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "json-verification", Capability: "fixture.echo", CredentialRevision: "test-v1", Endpoint: provider.URL, UpperBound: dollars("1"), MeasurementMode: "FIXTURE"}}
			if mode == "purpose_expired_after_prepare" {
				c.boundaryHook = func(name string, _ Object) {
					if name == "effect_prepared" {
						if _, e := f.db.Exec("UPDATE resource_route_grants SET body=json_set(body,'$.expires_at',?) WHERE project=?", time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), f.project); e != nil {
							t.Error(e)
						}
					}
				}
			}
			if e := c.Scan(context.Background()); e != nil {
				t.Fatal(e)
			}
			c.workers.Wait()
			select {
			case <-c.errors:
			default:
				t.Fatal("unavailable provider should stop worker")
			}
			task := f.read("tasks", Str(r.task, "id"))
			var state string
			if e := f.db.QueryRow("SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? ORDER BY sequence DESC LIMIT 1", task["active_run_id"]).Scan(&state); e != nil {
				t.Fatal(e)
			}
			wantCalls, wantState := int32(1), "UNKNOWN"
			if mode == "purpose_expired_after_prepare" {
				wantCalls, wantState = 0, "PREPARED"
			}
			if calls.Load() != wantCalls || state != wantState || task["status"] != "RUNNING" {
				t.Fatalf("effect retried or promoted: calls=%d state=%s task=%s", calls.Load(), state, task["status"])
			}
			if e := c.Scan(context.Background()); e != nil {
				t.Fatal(e)
			}
			c.workers.Wait()
			if calls.Load() != wantCalls {
				t.Fatal("scan retried unavailable effect")
			}
			t.Logf("RUNTIME_BROKER_FAILURE mode=%s provider_calls=%d effect=%s no_fallback=true no_retry=true", mode, calls.Load(), state)
		})
	}
}

func TestRuntimeCoordinatorPeriodicHeartbeat(t *testing.T) {
	c, route, q := coordinatorFixtureOptions(t, false, false, "--wait-heartbeat")
	c, _, r, _ := nativeNormalFrom(t, c, route, q)
	heartbeats := make(chan Object, 4)
	c.client.Transport = runtimeRoundTrip(func(request *http.Request) (*http.Response, error) {
		response, e := http.DefaultTransport.RoundTrip(request)
		if e != nil {
			return nil, e
		}
		if request.Method == "POST" && strings.HasSuffix(request.URL.Path, "/heartbeat") && response.StatusCode == http.StatusOK {
			raw, e := io.ReadAll(response.Body)
			response.Body.Close()
			if e != nil {
				return nil, e
			}
			response.Body = io.NopCloser(bytes.NewReader(raw))
			heartbeat, e := Decode(raw)
			if e != nil {
				return nil, e
			}
			heartbeats <- heartbeat
		}
		return response, nil
	})
	started := time.Now()
	if e := c.Scan(context.Background()); e != nil {
		t.Fatal(e)
	}
	c.workers.Wait()
	select {
	case e := <-c.errors:
		t.Fatal(e)
	default:
	}
	close(heartbeats)
	observed := []Object{}
	for heartbeat := range heartbeats {
		observed = append(observed, heartbeat)
	}
	if len(observed) < 2 {
		t.Fatalf("periodic heartbeat not reached: successful responses=%d", len(observed))
	}
	first, last := observed[0], observed[len(observed)-1]
	firstExpiry, e := time.Parse(time.RFC3339Nano, Str(first, "lease_expires_at"))
	if e != nil {
		t.Fatal(e)
	}
	lastExpiry, e := time.Parse(time.RFC3339Nano, Str(last, "lease_expires_at"))
	if e != nil {
		t.Fatal(e)
	}
	task := r.f.read("tasks", Str(r.task, "id"))
	run := r.f.read("runs", Str(task, "active_run_id"))
	if first["id"] != last["id"] || run["id"] != first["id"] || Hash(first["lease_epoch"]) != Hash(last["lease_epoch"]) || Hash(run["lease_epoch"]) != Hash(first["lease_epoch"]) || lastExpiry.Sub(firstExpiry) < 14*time.Second || run["lease_expires_at"] != last["lease_expires_at"] || run["status"] != "SETTLED" || task["status"] != "EXECUTION_REPORTED" {
		t.Fatal("periodic lease renewal or final report mismatch")
	}
	t.Logf("RUNTIME_PERIODIC_HEARTBEAT responses=%d first_expiry=%s last_expiry=%s lease_advance_seconds=%.3f epoch_unchanged=true worker_renew_error=false run=SETTLED task=EXECUTION_REPORTED elapsed_seconds=%.3f", len(observed), first["lease_expires_at"], last["lease_expires_at"], lastExpiry.Sub(firstExpiry).Seconds(), time.Since(started).Seconds())
}
