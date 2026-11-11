package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"golang.org/x/sys/windows"
	"os"
	"os/exec"
	"path/filepath"
	rt "researchos.local/research-os/adapters/runtime"
	"testing"
	"time"
)

func runtimeProfileEvidence(db *sql.DB, project string, rt Object) Object {
	var raw string
	if e := db.QueryRow("SELECT profile_ref FROM runtime_bindings WHERE project=? AND runtime=?", project, rt["id"]).Scan(&raw); e != nil {
		return Object{}
	}
	ref, e := Decode([]byte(raw))
	if e != nil {
		panic(e)
	}
	var content []byte
	if e = db.QueryRow("SELECT u.bytes FROM domain_objects d JOIN uploaded_content u ON u.project=d.project AND u.storage_key=json_extract(d.body,'$.storage_key') WHERE d.project=? AND d.kind='Artifact' AND d.id=?", project, ref["id"]).Scan(&content); e != nil {
		panic(e)
	}
	profile, e := Decode(content)
	if e != nil {
		panic(e)
	}
	return Object{"profile_hash": Hash(ref), "build_hash": profile["build_hash"], "backend": profile["backend"], "model": profile["model"], "sandbox": profile["sandbox"], "platform": profile["platform"], "adapter": profile["adapter"], "adapter_revision": profile["adapter_revision"], "credential_revision": profile["credential_revision"]}
}

func runtimeAssert(t *testing.T, id string, want, got any, evidence any) {
	t.Helper()
	status := "PASS"
	if Hash(want) != Hash(got) {
		status = "FAIL"
	}
	fmt.Println("W05_ASSERTION " + string(Bytes(Object{"assertion_id": id, "expected": want, "actual": got, "status": status, "evidence": evidence})))
	if status == "FAIL" {
		t.Fatalf("%s: %s", id, Bytes(evidence))
	}
}

type runtimeFixture struct {
	f                           *fixture
	ownerToken, executor, lease string
	run, task, registration     Object
}

func runtimeSetup(t *testing.T) *runtimeFixture {
	return runtimeSetupMode(t, "LIVE")
}

func runtimeSetupMode(t *testing.T, mode string) *runtimeFixture {
	return runtimeSetupModeHook(t, mode, "1", nil, false, false)
}

func runtimeSetupModeHook(t *testing.T, mode, cost string, before func(*fixture, Object), expectPlanFailure, expectBeginFailure bool) *runtimeFixture {
	f := contextFixture(t)
	req := f.requirement()
	rt := f.expect(201, "POST", f.path("/runtimes"), ID(), f.stateTag(), Object{"name": "controlled runtime qualification", "adapter": "codex-cli", "adapter_revision": "windows-job-v1", "capabilities": []any{"start", "cancel_job_tree", "reconcile", "context_rebuild"}, "platform": "windows-amd64", "measurement_mode": mode, "credential_ref": nil})
	profileBody := Object{"runtime_id": rt["id"], "technical_hash": runtimeTechnicalHash(rt), "adapter": rt["adapter"], "adapter_revision": rt["adapter_revision"], "platform": rt["platform"], "build_hash": Digest([]byte("native-fixture")), "sandbox": "fixture-no-network", "credential_revision": "none", "backend": "fixture", "model": "none"}
	if cost != "" {
		profileBody["max_cost"] = Object{"amount": cost, "currency": "USD"}
	}
	profile := f.artifact(profileBody, Empty())
	goal := f.expect(201, "POST", f.path("/goals"), ID(), f.stateTag(), Object{"title": "runtime qualification", "original_intent": "verify registered runtime", "scope": "PROJECT", "requirement_refs": []any{Ref(req, "Requirement")}, "problem_ids": []any{"runtime"}, "deliverables": []any{"receipt"}, "acceptance_contract": orchestrationContract()})
	goal = f.expect(200, "POST", f.path("/goals/"+Str(goal, "id")+"/actions"), ID(), testTag(goal), Object{"action": "ACTIVATE", "reason": "approved fixture"})
	task := f.expect(201, "POST", f.path("/tasks"), ID(), testTag(goal), Object{"goal_id": goal["id"], "title": "runtime qualification", "task_type": "runtime_qualification", "stage": "verification", "dependency_task_ids": Empty(), "requirement_refs": []any{Ref(req, "Requirement")}, "input_refs": []any{Ref(profile, "Artifact")}, "acceptance_contract": orchestrationContract(), "origin_problem_id": "runtime", "candidate_id": "runtime", "stop_policy": Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1, "stop_conditions": []any{"no progress"}}})
	f.bundle(task)
	task = f.read("tasks", Str(task, "id"))
	executor := ID()
	if e := f.s.ProvisionPrincipal(context.Background(), Principal{ID: executor, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project, TaskID: Str(task, "id")}}}); e != nil {
		t.Fatal(e)
	}
	if e := f.s.RegisterRuntimeQualificationPlan(context.Background(), f.token, f.project, Str(task, "id"), Str(rt, "id"), Ref(profile, "Artifact"), []any{"start"}, time.Hour, ""); expectPlanFailure {
		if e == nil {
			t.Fatal("unknown LIVE cost unexpectedly accepted")
		}
		return &runtimeFixture{f: f, ownerToken: f.token, executor: executor, task: task, registration: rt}
	} else if e != nil {
		t.Fatal(e)
	}
	if before != nil {
		before(f, goal)
	}
	run, lease, e := f.s.BeginRuntimeQualification(context.Background(), f.token, f.project, Str(task, "id"), Str(rt, "id"), executor)
	if expectBeginFailure {
		if e == nil {
			t.Fatal("qualification claim unexpectedly passed")
		}
		return &runtimeFixture{f: f, ownerToken: f.token, executor: executor, task: task, registration: rt}
	}
	if e != nil {
		t.Fatal(e)
	}
	f.token, e = f.s.IssueCredential(context.Background(), f.owner, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	rf := &runtimeFixture{f: f, ownerToken: f.token, executor: executor, lease: lease, run: run, task: task, registration: rt}
	f.token, e = f.s.IssueCredential(context.Background(), executor, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	return rf
}
func (r *runtimeFixture) refresh() {
	r.run = r.f.expect(200, "GET", r.f.path("/runs/"+Str(r.run, "id")), "", "", nil)
}
func (r *runtimeFixture) heartbeat() Object {
	return Object{"lease_token": r.lease, "lease_epoch": r.run["lease_epoch"], "external_run_id": "qualified-" + Str(r.run, "id"), "checkpoint_artifact_id": nil}
}
func (r *runtimeFixture) call(path string, b Object, status int) Object {
	r.f.t.Helper()
	o := r.f.expect(status, "POST", r.f.path("/runs/"+Str(r.run, "id")+path), ID(), testTag(r.run), b)
	if status == 200 {
		r.run = o
	}
	return o
}
func (r *runtimeFixture) seal(raw []byte) Object {
	return r.sealKind(raw, "REPORT")
}
func (r *runtimeFixture) sealKind(raw []byte, kind string) Object {
	f := r.f
	token := f.token
	f.token = r.ownerToken
	tag := f.stateTag()
	f.token = token
	u := f.expect(201, "POST", f.path("/content"), ID(), "", raw)
	return f.expect(201, "POST", f.path("/artifacts"), ID(), tag, Object{"run_id": r.run["id"], "kind": kind, "evidence_kind": "GENERATED", "measurement_mode": r.registration["measurement_mode"], "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "application/json", "byte_size": len(raw), "input_refs": Empty(), "source_refs": Empty(), "produced_by": r.executor, "access_class": "PROJECT"})
}
func (r *runtimeFixture) observation(state string, settled bool) Object {
	spec := Object{"run_id": r.run["id"], "task_id": r.task["id"], "epoch": r.run["lease_epoch"], "technical_hash": runtimeTechnicalHash(r.registration), "capabilities": []any{"start"}}
	Merge(spec, runtimeProfileEvidence(r.f.db, r.f.project, r.registration))
	return Object{"spec": spec, "state": state, "children_stopped": true, "queue_empty": true, "exit_code": 0, "ended": Now(), "protocol": Object{"settled": settled}}
}
func (r *runtimeFixture) observe(o Object) {
	r.f.t.Helper()
	n, _ := Num(r.run, "lease_epoch")
	if e := r.f.s.ObserveRuntime(context.Background(), r.f.project, Str(r.run, "id"), n, o); e != nil {
		r.f.t.Fatal(e)
	}
}
func (r *runtimeFixture) report(artifacts []any, exit any) Object {
	return Object{"lease_token": r.lease, "lease_epoch": r.run["lease_epoch"], "runtime_settled": true, "execution_report": "execution declaration; independent acceptance still required", "exit_code": exit, "result_artifact_ids": artifacts, "checkpoint_artifact_id": nil}
}
func TestW05ServiceLifecycle(t *testing.T) {
	r := runtimeSetup(t)
	r.call("/heartbeat", r.heartbeat(), 200)
	r.call("/report", r.report(Empty(), 0), 422)
	artifact := r.seal([]byte(`{"actual":"fixture output"}`))
	o := r.observation("SETTLED", true)
	o["artifacts"] = []any{Object{"path": "result.json", "content_hash": artifact["content_hash"], "byte_size": artifact["byte_size"]}}
	r.observe(o)
	report := r.report([]any{artifact["id"]}, 0)
	key := ID()
	tag := testTag(r.run)
	r.run = r.f.expect(200, "POST", r.f.path("/runs/"+Str(r.run, "id")+"/report"), key, tag, report)
	r.f.expect(200, "POST", r.f.path("/runs/"+Str(r.run, "id")+"/report"), key, tag, report)
	task := r.f.read("tasks", Str(r.task, "id"))
	runtimeAssert(t, "W05-G01-SERVICE-REPORTED", "EXECUTION_REPORTED", task["status"], Object{"run": r.run, "task": task, "fixture": true})
	runtimeAssert(t, "W05-G01-NO-SELF-ACCEPT", nil, task["acceptance_id"], nil)
}

func TestW05ServiceLogOnly(t *testing.T) {
	r := runtimeSetup(t)
	o := r.observation("SETTLED", true)
	r.observe(o)
	a := r.sealKind(Bytes(o), "LOG")
	r.call("/report", r.report([]any{a["id"]}, 0), 422)
	report := r.report(Empty(), 0)
	report["checkpoint_artifact_id"] = a["id"]
	r.call("/report", report, 200)
	task := r.f.read("tasks", Str(r.task, "id"))
	runtimeAssert(t, "W05-G01-LOG-NOT-OUTPUT", true, r.run["status"] == "FAILED" && task["status"] == "RUNNING", r.run)
}
func TestW05ServiceManifestExact(t *testing.T) {
	r := runtimeSetup(t)
	first := r.seal([]byte(`{"output":"first"}`))
	second := r.seal([]byte(`{"output":"second"}`))
	extra := r.seal([]byte(`{"unobserved":"executor addition"}`))
	o := r.observation("SETTLED", true)
	o["artifacts"] = []any{
		Object{"path": "first.json", "content_hash": first["content_hash"], "byte_size": first["byte_size"]},
		Object{"path": "second.json", "content_hash": second["content_hash"], "byte_size": second["byte_size"]},
	}
	r.observe(o)
	log := r.sealKind(Bytes(o), "LOG")
	for _, c := range []struct {
		id      string
		outputs []any
	}{
		{"EXTRA", []any{first["id"], second["id"], extra["id"]}},
		{"SUBSTITUTE", []any{first["id"], extra["id"]}},
		{"MISSING", []any{first["id"]}},
		{"DUPLICATE", []any{first["id"], first["id"]}},
	} {
		before := r.f.read("tasks", Str(r.task, "id"))
		status, response, _ := r.f.request("POST", r.f.path("/runs/"+Str(r.run, "id")+"/report"), ID(), testTag(r.run), r.report(c.outputs, 0))
		after := r.f.read("tasks", Str(r.task, "id"))
		current := r.f.read("runs", Str(r.run, "id"))
		runtimeAssert(t, "W05-G01-MANIFEST-"+c.id, true, status == 422 && Hash(before) == Hash(after) && Hash(current) == Hash(r.run), Object{"status": status, "response": response, "task": after, "run": current})
	}
	outputs := []any{second["id"], first["id"]}
	report := r.report(outputs, 0)
	executorToken := r.f.token
	r.f.token = r.ownerToken
	unrelatedCheckpoint := r.f.artifact(Object{"unrelated": "owner attachment"}, Empty())
	r.f.token = executorToken
	report["checkpoint_artifact_id"] = unrelatedCheckpoint["id"]
	status, response, _ := r.f.request("POST", r.f.path("/runs/"+Str(r.run, "id")+"/report"), ID(), testTag(r.run), report)
	runtimeAssert(t, "W05-G01-MANIFEST-CHECKPOINT-SCOPE", 422, status, response)
	report["checkpoint_artifact_id"] = log["id"]
	r.call("/report", report, 200)
	task := r.f.read("tasks", Str(r.task, "id"))
	runtimeAssert(t, "W05-G01-MANIFEST-EXACT", true, r.run["status"] == "SETTLED" && Hash(task["output_artifact_ids"]) == Hash(outputs) && r.run["checkpoint_artifact_id"] == log["id"] && task["acceptance_id"] == nil, Object{"run": r.run, "task": task, "checkpoint": log})
}
func TestW05Scope(t *testing.T) {
	r := runtimeSetup(t)
	f := r.f
	_, _, repeatError := f.s.BeginRuntimeQualification(context.Background(), r.ownerToken, f.project, Str(r.task, "id"), Str(r.registration, "id"), r.executor)
	runtimeAssert(t, "W05-G01-ACTIVE-BEGIN-FENCE", true, repeatError != nil, Object{"error": fmt.Sprint(repeatError)})
	_, e := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(r.task, "id"))
	runtimeAssert(t, "W05-G01-CONTEXT-SCOPE", true, e == nil, nil)
	f.expect(404, "GET", f.path("/state"), "", "", nil)
	f.expect(404, "GET", f.path("/tasks"), "", "", nil)
	own := f.token
	f.token = r.ownerToken
	req := f.requirement()
	other := f.task(req, Empty(), "unrelated")
	f.token = own
	f.expect(404, "GET", f.path("/tasks/"+Str(other, "id")), "", "", nil)
	bad := r.heartbeat()
	bad["lease_epoch"] = 99
	r.call("/heartbeat", bad, 409)
	runtimeAssert(t, "W05-G01-SCOPED-DENIALS", true, true, Object{"project_list": 404, "other_task": 404, "old_epoch": 409})
	if e = f.s.RevokePrincipal(context.Background(), r.executor); e != nil {
		t.Fatal(e)
	}
	f.expect(401, "GET", f.path("/runs/"+Str(r.run, "id")), "", "", nil)
	runtimeAssert(t, "W05-G01-REVOKED", true, true, nil)
}
func TestW05UnknownCancellation(t *testing.T) {
	r := runtimeSetup(t)
	f := r.f
	executorToken := f.token
	f.token = r.ownerToken
	r.call("/cancel", Object{"reason": "fixture cancel"}, 200)
	f.token = executorToken
	o := r.observation("UNKNOWN", false)
	o["children_stopped"] = false
	r.observe(o)
	a := r.seal(Bytes(o))
	r.call("/cancel-ack", Object{"lease_token": r.lease, "lease_epoch": r.run["lease_epoch"], "children_stopped": true, "queue_empty": true, "receipt_artifact_ref": Ref(a, "Artifact")}, 422)
	f.token = r.ownerToken
	r.call("/reconcile", Object{"observed_external_run_id": nil, "observed_status": "UNKNOWN", "receipt_artifact_ref": Ref(a, "Artifact")}, 200)
	_, _, e := f.s.BeginRuntimeQualification(context.Background(), r.ownerToken, f.project, Str(r.task, "id"), Str(r.registration, "id"), r.executor)
	runtimeAssert(t, "W05-G01-UNKNOWN-FENCE", true, r.run["status"] == "RECONCILING" && e != nil, r.run)
}
func asObject(t *testing.T, v any) Object {
	t.Helper()
	var o Object
	if e := json.Unmarshal(Bytes(v), &o); e != nil {
		t.Fatal(e)
	}
	return o
}

func TestW05Live(t *testing.T) {
	if os.Getenv("RESEARCHOS_RUNTIME_LIVE") != "1" {
		t.Skip("explicit live authorization required")
	}
	executable, e := exec.LookPath("codex.exe")
	if e != nil {
		t.Fatal(e)
	}
	binary, e := os.ReadFile(executable)
	if e != nil {
		t.Fatal(e)
	}
	if rt.Hash(binary) != "sha256:8f0554ede25bbc5450921897c468b2e84635aa513c5017457997af0954581f49" {
		t.Fatal("Codex version lock mismatch")
	}
	model := os.Getenv("RESEARCHOS_RUNTIME_MODEL")
	if model == "" {
		model = "gpt-6-luna"
	}
	for _, name := range []string{"success", "tool_failed", "request_timeout", "pending_queue_cancel", "executor_crash"} {
		t.Run(name, func(t *testing.T) {
			if name == "tool_failed" {
				runtimeBlocked("A04-01-TOOL-FAILED", "tool subprocess exits 7", "local tool policy rejected both approved write and read probes; no further retry", "execution/receipts/W05/live-readonly-probe/success/000.stderr")
				return
			}
			r := runtimeSetup(t)
			f := r.f
			root := t.TempDir()
			workspace := filepath.Join(root, "workspace")
			if _, e = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(r.task, "id"), workspace); e != nil {
				t.Fatal(e)
			}
			// Copy only the already-authorized login into a fresh runtime home. Never copy config, skills or project identities.
			authBase, e := filepath.Abs(filepath.Join("..", "..", ".local", "runtime-auth"))
			if e != nil {
				t.Fatal(e)
			}
			if e = os.MkdirAll(authBase, 0700); e != nil {
				t.Fatal(e)
			}
			authHome, e := os.MkdirTemp(authBase, "qualified-")
			if e != nil {
				t.Fatal(e)
			}
			dacl, e := rt.PrivateDirectory(authHome)
			if e != nil {
				t.Fatal(e)
			}
			t.Cleanup(func() { os.RemoveAll(authHome) })
			original := os.Getenv("CODEX_HOME")
			if original == "" {
				original = filepath.Join(os.Getenv("USERPROFILE"), ".codex")
			}
			auth, e := os.ReadFile(filepath.Join(original, "auth.json"))
			if e != nil {
				t.Fatal("authorized login unavailable")
			}
			if e = os.WriteFile(filepath.Join(authHome, "auth.json"), auth, 0600); e != nil {
				t.Fatal(e)
			}
			credentialSD, e := windows.GetNamedSecurityInfo(filepath.Join(authHome, "auth.json"), windows.SE_FILE_OBJECT, windows.DACL_SECURITY_INFORMATION)
			if e != nil {
				t.Fatal(e)
			}
			credentialDACL := credentialSD.String()
			auth = nil
			publicInput := Object{"nonce": ID(), "value": 42}
			if e = os.WriteFile(filepath.Join(workspace, "public-input.json"), Bytes(publicInput), 0444); e != nil {
				t.Fatal(e)
			}
			outputSchema := Object{"type": "object", "properties": Object{"nonce": Object{"type": "string"}, "value": Object{"type": "integer"}}, "required": []any{"nonce", "value"}, "additionalProperties": false}
			if e = os.WriteFile(filepath.Join(workspace, "output.schema.json"), Bytes(outputSchema), 0444); e != nil {
				t.Fatal(e)
			}
			prompt := "Authorized local ResearchOS qualification. Do not invoke any tools, read any files, modify files, or access the network. Return exactly the following public JSON input as your final structured result: " + string(Bytes(publicInput))
			if name == "tool_failed" {
				prompt = "This is an authorized local qualification. Use exactly one shell tool invocation that runs powershell.exe -NoProfile -NonInteractive -Command \"exit 7\". This expected failure must not be fixed or retried. Then reply expected failure. Do not read files, credentials, configs, other directories or network."
			}
			if name == "pending_queue_cancel" || name == "executor_crash" {
				prompt = "Authorized local CLI process lifecycle test. Do not use tools, read files or access network. Return a JSON object with the integer value 42."
			}
			args := []string{"exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check", "--sandbox", "read-only", "--model", model, "-c", `model_reasoning_effort="low"`, "--cd", workspace, "-"}
			if name == "success" {
				args = append(args[:len(args)-1], "--output-schema", filepath.Join(workspace, "output.schema.json"), "-")
			}
			command := rt.Command{Executable: executable, Args: args, Directory: workspace, Input: prompt}
			commands := []rt.Command{command}
			if name == "pending_queue_cancel" {
				second := command
				second.Input = "Write candidates/forbidden.txt with should-never-launch, then finish."
				commands = append(commands, second)
			}
			timeout := 4 * time.Minute
			if name == "request_timeout" {
				timeout = 1500 * time.Millisecond
			}
			epoch, _ := Num(r.run, "lease_epoch")
			spec := rt.Spec{RunID: Str(r.run, "id"), TaskID: Str(r.task, "id"), Epoch: epoch, Commands: commands, Model: model, Environment: rt.Environment(authHome), Timeout: timeout}
			if name == "success" {
				spec.ArtifactTransport = "protocol-json"
			}
			r.call("/heartbeat", r.heartbeat(), 200)
			journalDir := filepath.Join(root, "journal")
			out := os.Getenv("W05_EVIDENCE_DIR")
			if out == "" {
				t.Fatal("W05_EVIDENCE_DIR required for a real execution")
			}
			out, e = filepath.Abs(filepath.Join(out, name))
			if e != nil {
				t.Fatal(e)
			}
			if e = os.MkdirAll(out, 0700); e != nil {
				t.Fatal(e)
			}
			bundleBefore, be := f.s.GetTaskContext(context.Background(), f.token, f.project, Str(r.task, "id"))
			if be != nil {
				t.Fatal(be)
			}
			if e = os.WriteFile(filepath.Join(out, "before.json"), Bytes(Object{"at": Now(), "run": r.run, "spec": spec, "prompt_hash": Digest([]byte(prompt)), "public_input_hash": Hash(publicInput), "bundle_receipt_hash": bundleBefore["receipt_hash"], "executor_binary_hash": rt.Hash(binary), "configured_model": model, "adapter_revision": rt.Revision, "rubric_hash": Hash(r.task["acceptance_contract"]), "credential_directory_dacl": dacl, "credential_file_dacl": credentialDACL, "authorization": "existing user ChatGPT login; no external publication", "artifact_transport": spec.ArtifactTransport}), 0600); e != nil {
				t.Fatal(e)
			}
			w, e := rt.Start(journalDir, spec)
			if e != nil {
				t.Fatal(e)
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
			defer cancel()
			done := make(chan rt.Journal, 1)
			go func() { j, _ := w.Wait(ctx); done <- j }()
			heartbeat := time.NewTicker(rt.HeartbeatInterval)
			defer heartbeat.Stop()
			poll := time.NewTicker(100 * time.Millisecond)
			defer poll.Stop()
			cancelled := false
			crashed := false
			var j rt.Journal
		loop:
			for {
				select {
				case j = <-done:
					break loop
				case <-ctx.Done():
					w.Cancel(epoch, "qualification deadline")
					t.Fatal("qualification timed out")
				case <-heartbeat.C:
					r.refresh()
					if r.run["status"] == "CANCEL_REQUESTED" {
						continue
					}
					r.call("/heartbeat", r.heartbeat(), 200)
					if e = w.Renew(epoch, rt.LeaseDuration); e != nil && !cancelled {
						t.Fatal(e)
					}
				case <-poll.C:
					if !cancelled && (name == "pending_queue_cancel" || name == "executor_crash") {
						if snapshot := w.Read(); snapshot.PID != 0 && time.Since(parseRuntimeTime(snapshot.Started)) > time.Second {
							if name == "executor_crash" && !crashed {
								snapshot := w.Read()
								h, err := windows.OpenProcess(windows.PROCESS_TERMINATE, false, snapshot.PID)
								if err != nil {
									t.Fatal(err)
								}
								err = windows.TerminateProcess(h, 99)
								windows.CloseHandle(h)
								if err != nil {
									t.Fatal(err)
								}
								crashed = true
								cancelled = true
								continue
							}
							token := f.token
							f.token = r.ownerToken
							r.call("/cancel", Object{"reason": name}, 200)
							f.token = token
							if e = w.Cancel(epoch, name); e != nil {
								t.Fatal(e)
							}
							cancelled = true
						}
					}
				}
			}
			// Persist scrubbed raw protocol and process receipts before making assertions, including failures.
			for _, file := range []string{"journal.json", "000.stdout", "000.stderr", "result.json"} {
				b, er := os.ReadFile(filepath.Join(journalDir, file))
				if er == nil {
					if er = os.WriteFile(filepath.Join(out, file), rt.Redact(b), 0600); er != nil {
						t.Fatal(er)
					}
				}
			}
			os.WriteFile(filepath.Join(out, "prompt.txt"), []byte(prompt), 0600)
			os.WriteFile(filepath.Join(out, "public-input.json"), Bytes(publicInput), 0600)
			os.WriteFile(filepath.Join(out, "credential-boundary.json"), Bytes(Object{"directory_dacl": dacl, "file_dacl": credentialDACL, "original_credential_retained": true, "copied_fields": "auth.json only", "home_purpose": "helper alias temp-path configuration repair", "artifact_transport": "protocol-json", "cli_write_workspace_capability": false}), 0600)
			observation := asObject(t, j)
			r.observe(observation)
			if j.State == "CANCELLED" {
				if !cancelled {
					token := f.token
					f.token = r.ownerToken
					r.call("/cancel", Object{"reason": name}, 200)
					f.token = token
				}
				receipt := r.seal(Bytes(observation))
				r.call("/cancel-ack", Object{"lease_token": r.lease, "lease_epoch": epoch, "children_stopped": true, "queue_empty": true, "receipt_artifact_ref": Ref(receipt, "Artifact")}, 200)
			} else {
				artifacts := Empty()
				log := r.sealKind(Bytes(observation), "LOG")
				if raw, er := os.ReadFile(filepath.Join(journalDir, "result.json")); er == nil {
					os.WriteFile(filepath.Join(out, "result.json"), raw, 0600)
					a := r.seal(raw)
					artifacts = append(artifacts, a["id"])
				}
				var code any
				if j.Exit != nil {
					code = *j.Exit
				}
				report := r.report(artifacts, code)
				report["checkpoint_artifact_id"] = log["id"]
				r.call("/report", report, 200)
			}
			task := f.read("tasks", Str(r.task, "id"))
			evidence := Object{"run": r.run, "task_status": task["status"], "process": observation, "raw_directory": out, "binary_hash": rt.Hash(binary), "configured_model": model, "provider_model_revision": j.Protocol.ModelRevision, "cost": j.Protocol.Cost, "native_resume": false}
			os.WriteFile(filepath.Join(out, "service.json"), Bytes(evidence), 0600)
			switch name {
			case "success":
				raw, er := os.ReadFile(filepath.Join(out, "result.json"))
				var result Object
				parseError := json.Unmarshal(raw, &result)
				runtimeAssert(t, "A04-01-SUCCESS", true, er == nil && parseError == nil && Hash(result) == Hash(publicInput) && j.Protocol.ToolsCompleted == 0 && j.Protocol.Settled && r.run["status"] == "SETTLED" && task["status"] == "EXECUTION_REPORTED" && task["acceptance_id"] == nil, evidence)
			case "tool_failed":
				runtimeAssert(t, "A04-01-TOOL-FAILED", true, j.Protocol.ToolFailed && r.run["status"] == "FAILED" && task["status"] != "ACCEPTED", evidence)
			case "request_timeout":
				runtimeAssert(t, "A04-03-TIMEOUT", true, j.Reason == "request_timeout" && j.ChildrenStopped && r.run["status"] == "CANCELLED", evidence)
			case "pending_queue_cancel":
				_, er := os.Stat(filepath.Join(workspace, "candidates", "forbidden.txt"))
				runtimeAssert(t, "W05-LIVE-CLI-QUEUE-CANCEL", true, cancelled && j.ChildrenStopped && j.QueueEmpty && j.Launched == 1 && os.IsNotExist(er) && r.run["status"] == "CANCELLED", evidence)
				runtimeBlocked("A04-02-CANCEL", "active model tool process stopped with queue empty", "CLI process tree and queue stopped; model tool subprocess unavailable under current policy", out)
			case "executor_crash":
				recovered, er := rt.Reconcile(journalDir)
				runtimeAssert(t, "A04-03-CRASH", true, crashed && er == nil && recovered.ChildrenStopped && recovered.QueueEmpty && task["status"] != "ACCEPTED", evidence)
				// A new process obtains a fresh validated bundle. No claim of native Codex resume.
				reconstructed := filepath.Join(root, "rebuilt")
				restarted, restartError := New(f.db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
				if restartError != nil {
					t.Fatal(restartError)
				}
				_, er = restarted.MaterializeTaskContext(context.Background(), f.token, f.project, Str(r.task, "id"), reconstructed)
				runtimeAssert(t, "A04-03-CONTEXT-REBUILD", true, er == nil, Object{"path": reconstructed, "error": fmt.Sprint(er)})
			}
		})
	}
}

func runtimeBlocked(id string, expected, actual, raw string) {
	fmt.Println("W05_ASSERTION " + string(Bytes(Object{"assertion_id": id, "status": "BLOCKED", "expected": expected, "actual": actual, "evidence": Object{"raw": raw, "retry_policy": "two policy failures retained; no bypass or further tool retries"}})))
}
func parseRuntimeTime(value string) time.Time { t, _ := time.Parse(time.RFC3339Nano, value); return t }
