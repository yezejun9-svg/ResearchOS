package domain

import (
	"context"
	"encoding/json"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

type recoveryFixture struct {
	o                        *orchestrationFixture
	r                        *runtimeFixture
	cp, replacement, request Object
}

func recoverySetup(t *testing.T, purpose string) *recoveryFixture {
	t.Helper()
	o := orchestrationSetup(t)
	f := o.f
	resourceHTTP(f)
	r := o.claim(o.task("resume-user-work", Empty(), Empty()))
	cp := resourceCheckpoint(r, Object{"next": "continue the original user work"})
	r.observe(r.observation("LOST", false))
	f.token = o.owner
	replacement := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "authorized replacement", "adapter": "fixture", "adapter_revision": "1", "capabilities": []any{"fixture"}, "platform": "windows-amd64", "measurement_mode": "FIXTURE", "credential_ref": nil})
	if e := f.s.RegisterOrchestrationFixture(context.Background(), f.project, Str(replacement, "id")); e != nil {
		t.Fatal(e)
	}
	if purpose != "" {
		if e := f.s.AuthorizeFixtureResource(context.Background(), o.owner, f.project, Str(replacement, "id"), purpose, Ref(cp, "Artifact"), time.Now().Add(time.Hour)); e != nil {
			t.Fatal(e)
		}
	}
	request := f.expect(201, "POST", f.path("/resource-requests"), ID(), f.stateTag(), resourceRequestBody(r, cp))
	return &recoveryFixture{o, r, cp, replacement, request}
}

func (x *recoveryFixture) instruction() Object {
	f := x.o.f
	return Object{"schema": ResourceRecoverySchema, "action": "SWITCH_RUNTIME", "resource_request_ref": Ref(x.request, "ResourceRequest"), "replacements": []any{Object{"task_ref": Ref(f.read("tasks", Str(x.r.task, "id")), "Task"), "run_ref": Ref(f.read("runs", Str(x.r.run, "id")), "Run"), "runtime_ref": Ref(x.replacement, "RuntimeRegistration")}}}
}

func recoverySeal(f *fixture, body any, producer, media string) Object {
	raw := Bytes(body)
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	return f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "REPORT", "evidence_kind": "GENERATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": media, "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": producer, "access_class": "PROJECT"})
}

func recoveryHistory(f *fixture) int {
	var n int
	if e := f.db.QueryRow("SELECT count(*) FROM resource_route_history WHERE project=? AND json_extract(body,'$.from_runtime_ref') IS NOT NULL", f.project).Scan(&n); e != nil {
		f.t.Fatal(e)
	}
	return n
}

func (x *recoveryFixture) assertContinuation(t *testing.T, id string) {
	f := x.o.f
	after := f.read("runs", Str(x.r.run, "id"))
	task := f.read("tasks", Str(x.r.task, "id"))
	epoch, _ := Num(after, "lease_epoch")
	prior, _ := Num(x.r.run, "lease_epoch")
	resourcesAssert(t, id+"-CONTINUITY", true, after["id"] == x.r.run["id"] && after["runtime_id"] == x.replacement["id"] && after["checkpoint_artifact_id"] == x.cp["id"] && Hash(task["acceptance_contract"]) == Hash(x.r.task["acceptance_contract"]) && epoch > prior && task["acceptance_id"] == nil, Object{"run": after, "task": task})
	resourcesAssert(t, id+"-SINGLE-SWITCH", 1, recoveryHistory(f), nil)
}

func TestW12RecoveryHTTP(t *testing.T) {
	x := recoverySetup(t, "json-verification")
	f := x.o.f
	// Another user branch can finish while this request is still OPEN.
	independent := x.o.claim(x.o.task("unrelated-branch", Empty(), Empty()))
	out := x.o.report(independent, []byte(`{"result":"verified"}`))
	accept := x.o.acceptance(independent, out)
	f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(independent.task), accept)
	f.token = x.o.owner
	resourcesAssert(t, "W1202-HTTP-BRANCH-CONTINUES", []any{"ACCEPTED", "OPEN"}, []any{f.read("tasks", Str(independent.task, "id"))["status"], f.read("resource-requests", Str(x.request, "id"))["status"]}, nil)
	a := recoverySeal(f, x.instruction(), f.owner, ResourceRecoveryMediaType)
	body := Object{"resolution_evidence_refs": []any{Ref(a, "Artifact")}, "reason": "continue using the authorized runtime"}
	key, path := ID(), f.path("/resource-requests/"+Str(x.request, "id")+"/resolve")
	resolved := f.expect(200, "POST", path, key, testTag(x.request), body)
	replay := f.expect(200, "POST", path, key, testTag(x.request), body)
	resourcesAssert(t, "W1202-HTTP-RESOLVE-IDEMPOTENT", true, resolved["status"] == "RESOLVED" && Hash(resolved) == Hash(replay), resolved)
	x.assertContinuation(t, "W1202-HTTP")
	// A former executor cannot write with the previous epoch/lease.
	var e error
	f.token, e = f.s.IssueCredential(context.Background(), x.r.executor, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	code, refusal, _ := f.request("POST", f.path("/runs/"+Str(x.r.run, "id")+"/heartbeat"), ID(), testTag(x.r.run), x.r.heartbeat())
	resourcesAssert(t, "W1202-HTTP-OLD-EXECUTOR-REFUSED", true, code == 403 || code == 409 || code == 412, Object{"status": code, "response": refusal})
}

func TestW12RecoveryRefusals(t *testing.T) {
	for _, scenario := range []string{"unauthorized", "wrong-purpose", "stale-run", "unknown-effect", "partial-multi-task", "generic-evidence"} {
		t.Run(scenario, func(t *testing.T) {
			purpose := "json-verification"
			if scenario == "unauthorized" {
				purpose = ""
			}
			if scenario == "wrong-purpose" {
				purpose = "another-purpose"
			}
			x := recoverySetup(t, purpose)
			f := x.o.f
			action := x.instruction()
			status := 422
			media := ResourceRecoveryMediaType
			if scenario == "stale-run" {
				runRef := Arr(action, "replacements")[0].(map[string]any)["run_ref"].(map[string]any)
				rev, _ := Num(runRef, "revision")
				runRef["revision"] = rev - 1
				status = 412
			}
			if scenario == "unknown-effect" {
				tx, e := f.db.Begin()
				if e != nil {
					t.Fatal(e)
				}
				if e = effectAppend(tx, f.project, Str(x.r.run, "id"), "provider-operation", Object{"state": "UNKNOWN", "operation": "test uncertain external result"}); e != nil {
					tx.Rollback()
					t.Fatal(e)
				}
				if e = tx.Commit(); e != nil {
					t.Fatal(e)
				}
				status = 409
			}
			if scenario == "partial-multi-task" {
				second := x.o.claim(x.o.task("second-blocked-task", Empty(), Empty()))
				cp := resourceCheckpoint(second, Object{"next": "second work"})
				second.observe(second.observation("LOST", false))
				f.token = x.o.owner
				x.request = f.expect(201, "POST", f.path("/resource-requests"), ID(), f.stateTag(), resourceRequestBody(second, cp))
				action = x.instruction()
				// First valid switch is followed by a current-but-wrong run. All writes must roll back.
				action["replacements"] = append(Arr(action, "replacements"), Object{"task_ref": Ref(f.read("tasks", Str(second.task, "id")), "Task"), "run_ref": Ref(f.read("runs", Str(x.r.run, "id")), "Run"), "runtime_ref": Ref(x.replacement, "RuntimeRegistration")})
				// The first switch changes that repeated run's revision inside the
				// transaction, so the second reference must fail as stale.
				status = 412
			}
			if scenario == "generic-evidence" {
				media = "application/json"
				status = 200
			}
			before := f.read("runs", Str(x.r.run, "id"))
			a := recoverySeal(f, action, f.owner, media)
			response := f.expect(status, "POST", f.path("/resource-requests/"+Str(x.request, "id")+"/resolve"), ID(), testTag(x.request), Object{"resolution_evidence_refs": []any{Ref(a, "Artifact")}, "reason": scenario})
			after := f.read("runs", Str(x.r.run, "id"))
			wanted := "OPEN"
			if scenario == "generic-evidence" {
				wanted = "RESOLVED"
			}
			resourcesAssert(t, "W1202-HTTP-"+strings.ToUpper(scenario), true, Hash(before) == Hash(after) && recoveryHistory(f) == 0 && f.read("resource-requests", Str(x.request, "id"))["status"] == wanted, Object{"response": response, "run": after})
		})
	}
}

func TestW12RecoveryNoticeMerge(t *testing.T) {
	x := recoverySetup(t, "")
	f := x.o.f
	// A second human recipient joins; later reports merge and create only their missing notice.
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: "recovery-reader", Roles: []string{"READER"}, Grants: []Grant{{ProjectID: f.project}}}); e != nil {
		t.Fatal(e)
	}
	body := resourceRequestBody(x.r, x.cp)
	body["reason_code"] = "NEW_SHORTAGE"
	body["resume_checkpoint_ref"] = nil
	request := f.expect(201, "POST", f.path("/resource-requests"), ID(), f.stateTag(), body)
	body["resume_checkpoint_ref"] = Ref(x.cp, "Artifact")
	for i := 0; i < 3; i++ {
		merged := f.expect(201, "POST", f.path("/resource-requests"), ID(), f.stateTag(), body)
		if merged["id"] != request["id"] {
			t.Fatal("same shortage created another request")
		}
		request = merged
	}
	var n int
	if e := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Notification' AND json_extract(body,'$.resource_request_id')=?", f.project, request["id"]).Scan(&n); e != nil {
		t.Fatal(e)
	}
	// contextFixture already contains fixture-owner and fixture-author.
	resourcesAssert(t, "W1202-PUBLIC-CREATE-NOTICE-DEDUP", 3, n, request)
	var recipients int
	if e := f.db.QueryRow("SELECT count(DISTINCT json_extract(body,'$.recipient_id')) FROM domain_objects WHERE project=? AND kind='Notification' AND json_extract(body,'$.resource_request_id')=?", f.project, request["id"]).Scan(&recipients); e != nil {
		t.Fatal(e)
	}
	resourcesAssert(t, "W1202-NOTICE-EXACT-RECIPIENTS", 3, recipients, nil)
	resourcesAssert(t, "W1202-MERGE-PRESERVES-NEW-CHECKPOINT", Hash(Ref(x.cp, "Artifact")), Hash(request["resume_checkpoint_ref"]), request)
}

func TestW12RecoveryClients(t *testing.T) {
	goExe := os.Getenv("RESEARCHOS_GO")
	if goExe == "" {
		goExe = "go"
	}
	root, e := filepath.Abs("../..")
	if e != nil {
		t.Fatal(e)
	}
	bin := filepath.Join(t.TempDir(), "researchos.exe")
	build := exec.Command(goExe, "build", "-o", bin, "./apps/cli")
	build.Dir = root
	if out, e := build.CombinedOutput(); e != nil {
		t.Fatalf("CLI build: %v %s", e, out)
	}
	for _, client := range []string{"CLI", "DESKTOP-CLIENT"} {
		t.Run(client, func(t *testing.T) {
			x := recoverySetup(t, "json-verification")
			f := x.o.f
			server, _ := fixtureHTTPServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { f.s.Handler().ServeHTTP(w, r) }))
			defer server.Close()
			var command *exec.Cmd
			if client == "CLI" {
				dir := t.TempDir()
				discovery := filepath.Join(dir, "host.json")
				if e := os.WriteFile(discovery, Bytes(Object{"url": server.URL, "pid": os.Getpid(), "data_dir": dir, "started_at": Now()}), 0600); e != nil {
					t.Fatal(e)
				}
				command = exec.Command(bin, "resources", "recover", Str(x.request, "id"), "--runtime", Str(x.replacement, "id"), "--reason", "user selected replacement", "--project", f.project)
				command.Env = append(os.Environ(), "RESEARCHOS_CLI_DISCOVERY="+discovery, "RESEARCHOS_CLI_CREDENTIAL="+x.o.owner, "RESEARCHOS_CLI_CONFIG="+filepath.Join(dir, "config.json"))
			} else {
				// Run the exact Desktop API client + recovery action against the live server.
				// This verifies the client transaction, not native window rendering.
				script := `import {createApi} from './apps/web/src/api.js'; import {recoverResource} from './apps/web/src/resource-recovery.js'; globalThis.window={location:{origin:process.env.W12_HOST}}; const api=createApi(()=>process.env.W12_TOKEN); const request=await api.call('getResourceRequest',{params:{projectId:process.env.W12_PROJECT,id:process.env.W12_REQUEST}}); const result=await recoverResource(api,process.env.W12_PROJECT,request,process.env.W12_RUNTIME,'user selected replacement'); console.log(JSON.stringify({status:'COMPLETED',request:result}));`
				command = exec.Command("node", "--input-type=module", "-e", script)
				command.Env = append(os.Environ(), "W12_HOST="+server.URL, "W12_TOKEN="+x.o.owner, "W12_PROJECT="+f.project, "W12_REQUEST="+Str(x.request, "id"), "W12_RUNTIME="+Str(x.replacement, "id"))
			}
			command.Dir = root
			out, e := command.CombinedOutput()
			if e != nil {
				t.Fatalf("%s recovery failed: %v %s", client, e, out)
			}
			var result Object
			if e := json.Unmarshal(out, &result); e != nil {
				t.Fatalf("invalid client response: %v %s", e, out)
			}
			resourcesAssert(t, "W1202-"+client+"-REAL-HTTP", []any{"COMPLETED", "RESOLVED"}, []any{result["status"], f.read("resource-requests", Str(x.request, "id"))["status"]}, result)
			x.assertContinuation(t, "W1202-"+client)
		})
	}
}
