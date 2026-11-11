package main

// The W05-01 phases. Everything asserted here is driven through the real adapter and the real domain
// service: a Windows Job Object worker really launches a process, really reads and writes files inside
// a bounded workspace, and the resulting journal is checked against bytes recomputed from disk. The
// properties that need the pinned executor binary or model tool execution are reported BLOCKED with the
// measurement that makes them blocked, never dressed up as fixtures.

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
)

// workspace returns a journal directory that does not exist yet (the adapter creates it and takes the
// exclusive owner lock inside) plus an existing bounded workspace the worker may read and write.
func workspace(root, name string) (string, string, error) {
	ws := filepath.Join(root, name, "workspace")
	if e := os.MkdirAll(ws, 0o700); e != nil {
		return "", "", e
	}
	return filepath.Join(root, name, "journal"), ws, nil
}

func comspec() string {
	for _, k := range []string{"COMSPEC", "SystemRoot"} {
		if v := os.Getenv(k); v != "" {
			if k == "COMSPEC" {
				return v
			}
			if p := filepath.Join(v, "System32", "cmd.exe"); fileExists(p) {
				return p
			}
		}
	}
	return ""
}

func fileExists(p string) bool { _, e := os.Stat(p); return e == nil }

// adapterPhase proves the loop the card can deliver today: one admitted Run, a finite command queue, a
// real file read, durable artifacts bound to content hashes, and lease epochs that refuse a stale
// controller. The model is deliberately absent from this phase; it is a process-lifecycle proof.
func adapterPhase(ctx context.Context) {
	root := filepath.Join(repoRoot(), ".local", "w0501-run", "adapter")
	_ = os.RemoveAll(root)
	if e := os.MkdirAll(root, 0o700); e != nil {
		ok("W0501-ADAPTER-WORKSPACE", false, e)
		return
	}
	spec := comspec()
	if spec == "" {
		ok("W0501-ADAPTER-WORKSPACE", false, "COMSPEC unavailable")
		return
	}
	ok("W0501-ADAPTER-WORKSPACE", true, spec)

	dir, ws, e := workspace(root, "copy")
	if e != nil {
		ok("W0501-ADAPTER-REAL-FILE-READ", false, e)
		return
	}
	content := []byte("w0501 public nonce 4242\n")
	if e = os.WriteFile(filepath.Join(ws, "input.txt"), content, 0o600); e != nil {
		ok("W0501-ADAPTER-REAL-FILE-READ", false, e)
		return
	}
	w, e := rt.Start(dir, rt.Spec{RunID: "run-copy-1", TaskID: "task-copy-1", Epoch: 1,
		Commands: []rt.Command{{Executable: spec, Args: []string{"/c", "type", "input.txt", ">", "output.txt"},
			Directory: ws}},
		Model: "", Environment: rt.Environment(""), Lease: 90 * time.Second,
		Timeout: 60 * time.Second, Outputs: []string{"output.txt"}})
	if e != nil {
		// cmd.exe handles redirection itself only when given a single command line, so retry through /c
		w, e = rt.Start(dir, rt.Spec{RunID: "run-copy-1", TaskID: "task-copy-1", Epoch: 1,
			Commands:    []rt.Command{{Executable: spec, Args: []string{"/c", "copy", "/y", "input.txt", "output.txt"}, Directory: ws}},
			Environment: rt.Environment(""), Lease: 90 * time.Second, Timeout: 60 * time.Second,
			Outputs: []string{"output.txt"}})
	}
	if e != nil {
		ok("W0501-ADAPTER-REAL-FILE-READ", false, e)
		return
	}
	stale := w.Renew(2, 30*time.Second)
	ok("W0501-ADAPTER-STALE-EPOCH-RENEWAL-REFUSED", stale != nil && strings.Contains(stale.Error(), "stale epoch"), stale)
	staleCancel := w.Cancel(77, "wrong epoch")
	ok("W0501-ADAPTER-STALE-EPOCH-CANCEL-REFUSED", staleCancel != nil && strings.Contains(staleCancel.Error(), "stale epoch"), staleCancel)
	renewed := w.Renew(1, 60*time.Second)
	ok("W0501-ADAPTER-CURRENT-EPOCH-RENEWAL-ACCEPTED", renewed == nil, renewed)

	waitCtx, cancel := context.WithTimeout(ctx, 90*time.Second)
	defer cancel()
	j, e := w.Wait(waitCtx)
	if e != nil {
		ok("W0501-ADAPTER-REAL-FILE-READ", false, e)
		return
	}
	outPath := filepath.Join(ws, "output.txt")
	got, readErr := os.ReadFile(outPath)
	ok("W0501-ADAPTER-REAL-FILE-READ",
		readErr == nil && j.State == "SETTLED" && j.Exit != nil && *j.Exit == 0 && bytesEq(got, content),
		domain.Object{"state": j.State, "exit": j.Exit, "read_error": fmt.Sprint(readErr), "bytes": len(got)})

	var declared []string
	for _, a := range j.Artifacts {
		declared = append(declared, fmt.Sprintf("%s|%d|%t", a.Path, a.Size, a.Hash == sha(got)))
	}
	ok("W0501-ADAPTER-ARTIFACT-BOUNDED-TO-BYTES",
		len(j.Artifacts) == 1 && j.Artifacts[0].Path == "output.txt" && j.Artifacts[0].Size == int64(len(got)) &&
			j.Artifacts[0].Hash == sha(got), domain.Object{"artifacts": declared, "journal_hash": j.Artifacts})
	ok("W0501-ADAPTER-TREE-DRAINED", j.ChildrenStopped && j.QueueEmpty && j.Pending == 0,
		domain.Object{"children_stopped": j.ChildrenStopped, "queue_empty": j.QueueEmpty, "pending": j.Pending})
	// the report is only as good as the observation behind it: the last tree snapshot must agree with
	// the flag, otherwise an adapter that simply asserts a drained tree would be believed
	var lastPids []uint32
	if len(j.Trees) > 0 {
		lastPids = j.Trees[len(j.Trees)-1].PIDs
	}
	ok("W0501-ADAPTER-DRAINED-REPORT-CORRELATES-TREE",
		j.ChildrenStopped == (len(lastPids) == 0) && len(j.Trees) >= 2,
		domain.Object{"children_stopped": j.ChildrenStopped, "last_tree_pids": len(lastPids),
			"tree_snapshots": len(j.Trees)})
	ok("W0501-ADAPTER-REVISION-RECORDED", j.Revision == rt.Revision && j.Launched == 1,
		domain.Object{"revision": j.Revision, "launched": j.Launched})
	note("adapter_journal", true, domain.Object{"state": j.State, "pid": j.PID, "trees": len(j.Trees), "streams": len(j.Streams)})

	// the declared-model branch in the worker is reachable, so it is asserted rather than described: the
	// same job settles with no model declared and must fail with the decoder's own named reason once a
	// model is declared, which proves the failure comes from the unsettled protocol and not from the exit
	// code, the command or the workspace
	mv, mws, me := workspace(root, "modelbranch")
	if me != nil {
		ok("W0501-ADAPTER-DECLARED-MODEL-REQUIRES-SETTLED-PROTOCOL", false, me)
	} else {
		mctx, mcancel := context.WithTimeout(ctx, 90*time.Second)
		defer mcancel()
		mw, we := rt.Start(mv, rt.Spec{RunID: "run-model-1", TaskID: "task-model-1", Epoch: 1,
			Model:       "fixed-model-for-this-run",
			Commands:    []rt.Command{{Executable: spec, Args: []string{"/c", "echo", "just-text"}, Directory: mws}},
			Environment: rt.Environment(""), Lease: 90 * time.Second, Timeout: 60 * time.Second})
		if we != nil {
			ok("W0501-ADAPTER-DECLARED-MODEL-REQUIRES-SETTLED-PROTOCOL", false, we)
		} else {
			mj, wer := mw.Wait(mctx)
			ok("W0501-ADAPTER-DECLARED-MODEL-REQUIRES-SETTLED-PROTOCOL",
				wer == nil && mj.State == "FAILED" && mj.Protocol.Failure == "invalid_protocol",
				domain.Object{"state": mj.State, "reason": mj.Reason, "failure": mj.Protocol.Failure, "exit": mj.Exit})
			cv, cws, ce := workspace(root, "modelcontrol")
			if ce != nil {
				ok("W0501-ADAPTER-JOB-SETTLES-WITHOUT-A-DECLARED-MODEL", false, ce)
			} else {
				cctx, ccancel := context.WithTimeout(ctx, 90*time.Second)
				defer ccancel()
				cw2, cwe := rt.Start(cv, rt.Spec{RunID: "run-nomodel-1", TaskID: "task-nomodel-1", Epoch: 1,
					Commands:    []rt.Command{{Executable: spec, Args: []string{"/c", "echo", "just-text"}, Directory: cws}},
					Environment: rt.Environment(""), Lease: 90 * time.Second, Timeout: 60 * time.Second})
				if cwe != nil {
					ok("W0501-ADAPTER-JOB-SETTLES-WITHOUT-A-DECLARED-MODEL", false, cwe)
				} else {
					cj, cer := cw2.Wait(cctx)
					ok("W0501-ADAPTER-JOB-SETTLES-WITHOUT-A-DECLARED-MODEL",
						cer == nil && cj.State == "SETTLED",
						domain.Object{"state": cj.State, "reason": cj.Reason, "wait_error": fmt.Sprint(cer)})
				}
			}
		}
	}

	badDir, badWs, e := workspace(root, "refusals")
	if e != nil {
		ok("W0501-ADAPTER-START-REFUSALS", false, e)
		return
	}
	_, e = rt.Start(badDir, rt.Spec{RunID: "r", TaskID: "t", Epoch: 1,
		Commands: []rt.Command{{Executable: spec, Args: []string{"/c", "exit", "0"}, Directory: badWs}},
		Outputs:  []string{`..\escape.txt`}, Environment: rt.Environment("")})
	ok("W0501-ADAPTER-OUTPUT-ESCAPE-REFUSED", e != nil && strings.Contains(e.Error(), "local relative path"), e)
	badDir2, _, _ := workspace(root, "badexe")
	_, e = rt.Start(badDir2, rt.Spec{RunID: "r", TaskID: "t", Epoch: 1,
		Commands:    []rt.Command{{Executable: filepath.Join(badWs, "missing.exe"), Directory: badWs}},
		Environment: rt.Environment("")})
	ok("W0501-ADAPTER-MISSING-EXECUTABLE-REFUSED", e != nil, e)
	badDir3, _, _ := workspace(root, "noenv")
	_, e = rt.Start(badDir3, rt.Spec{RunID: "r", TaskID: "t", Epoch: 1,
		Commands: []rt.Command{{Executable: spec, Args: []string{"/c", "exit", "0"}, Directory: badWs}}})
	ok("W0501-ADAPTER-EXPLICIT-ENVIRONMENT-REQUIRED", e != nil && strings.Contains(e.Error(), "environment"), e)
	badDir4, _, _ := workspace(root, "transport")
	_, e = rt.Start(badDir4, rt.Spec{RunID: "r", TaskID: "t", Epoch: 1,
		Commands:    []rt.Command{{Executable: spec, Args: []string{"/c", "exit", "0"}, Directory: badWs}},
		Environment: rt.Environment(""), ArtifactTransport: "carrier-pigeon"})
	ok("W0501-ADAPTER-TRANSPORT-WHITELIST", e != nil && strings.Contains(e.Error(), "unsupported artifact transport"), e)
}

func bytesEq(a, b []byte) bool { return string(a) == string(b) }

// protocolPhase pins how an executor reply becomes a Run outcome. Each row names the single rule it
// relies on, so a refusal cannot move to another branch unnoticed, and none of it is quoted as a live
// model capability.
func protocolPhase() {
	settled := []byte(`{"type":"thread.started","thread_id":"th-1"}` + "\n" +
		`{"type":"turn.completed","usage":{"input_tokens":11,"output_tokens":3}}` + "\n" +
		`{"type":"item.completed","item":{"type":"agent_message","text":"{\"nonce\":\"abc\",\"value\":42}"}}` + "\n")
	p := rt.Parse(settled, 0)
	ok("W0501-PROTOCOL-SETTLED-REQUIRES-COMPLETED-TURN",
		p.Settled && p.ThreadID == "th-1" && p.Failure == "" && p.ToolsCompleted == 0 &&
			json.Valid(p.Result) && strings.Contains(string(p.Result), "42"), p)

	noTurn := []byte(`{"type":"thread.started","thread_id":"th-2"}` + "\n")
	p = rt.Parse(noTurn, 0)
	ok("W0501-PROTOCOL-MISSING-SETTLED-IS-NOT-SUCCESS",
		!p.Settled && p.Failure == "missing_settled", p.Failure)

	garbage := []byte("not json at all\n")
	p = rt.Parse(garbage, 0)
	ok("W0501-PROTOCOL-MALFORMED-LINE-NAMED", !p.Settled && p.Failure == "invalid_protocol", p.Failure)

	exited := rt.Parse(settled, 99)
	ok("W0501-PROTOCOL-PROCESS-EXIT-OVERRIDES-SETTLEMENT", !exited.Settled && exited.Failure == "executor_exit", exited.Failure)

	// the needle is the detector's own contract, quoted from adapters/runtime/codex.go
	denied := rt.ParseStreams(settled, []byte("Rejected: blocked by policy"), 0)
	ok("W0501-PROTOCOL-POLICY-DENIAL-IS-TOOL-FAILURE",
		!denied.Settled && denied.ToolFailed && denied.Failure == "tool_permission_denied",
		domain.Object{"failure": denied.Failure, "stderr": "Rejected: blocked by policy"})
	// the detector matches one phrase; a differently worded denial is not recognised. Asserted so the
	// limit is visible rather than discovered later by a model reply that slips through
	lookalike := rt.ParseStreams(settled, []byte("tool call denied by tenant rules"), 0)
	ok("W0501-PROTOCOL-DENIAL-DETECTION-IS-PHRASE-SCOPED",
		!lookalike.ToolFailed && lookalike.Settled, domain.Object{"failure": lookalike.Failure})

	reconnect := []byte(`{"type":"error","message":"Reconnecting... 2/5 (stream disconnected before completion: reset)"}` + "\n")
	p = rt.Parse(reconnect, 0)
	ok("W0501-PROTOCOL-TRANSPORT-RETRY-NEEDS-LATER-COMPLETION",
		!p.Settled && p.Failure == "missing_settled", p.Failure)

	leak := rt.Redact([]byte(`header: Bearer abcdef.012345 sk-FAKEFAKEFAKEFAKE1234 and "api_key":"PRIVATESTRING"`))
	text := string(leak)
	ok("W0501-PROTOCOL-REDACTION-COVERS-ALL-THREE-SHAPES",
		!strings.Contains(text, "abcdef.012345") && !strings.Contains(text, "sk-FAKEFAKEFAKEFAKE1234") &&
			!strings.Contains(text, "PRIVATESTRING"), text)
	note("redaction_sample_is_synthetic", true, "the strings above are invented for this test; no credential was read")
}

func contractDigest(c domain.Object) string {
	v := domain.Object{}
	for k, x := range c {
		if k != "contract_hash" {
			v[k] = x
		}
	}
	return domain.Hash(v)
}

// servicePhase proves what the card states about admission: a FIXTURE runtime may be claimed, a LIVE
// runtime may not be claimed without qualification, and a report with no trusted observation cannot
// accept anything or invent a provider charge.
func servicePhase(ctx context.Context, h *harness) {
	code, req, body := h.api(ctx, "POST", h.base+"/requirements", domain.ID(), h.stateTag(ctx), domain.Object{
		"requirement_key": "REQ-W0501", "text": "one controlled delegated loop", "basis": "USER_STATED",
		"source_refs": domain.Empty(), "rationale": "runtime qualification fixture", "supersedes_id": nil,
		"acceptance_check_ids": domain.Empty()})
	if code != 201 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"requirement": code, "body": body})
		return
	}
	_, accReq, body := h.api(ctx, "POST", h.base+"/requirements/"+domain.Str(req, "id")+"/actions",
		domain.ID(), tagOf(req), domain.Object{"action": "ACCEPT", "reason": "fixture requirement",
			"source_validation_refs": domain.Empty()})
	if accReq["id"] == nil {
		ok("W0501-RUNTIME-ADMISSION", false, body)
		return
	}
	contract := domain.Object{"contract_revision": 1, "require_independent_verifier": true,
		"version_policy": "EXACT", "frozen_at": domain.Now(),
		"checks": []any{domain.Object{"check_id": "w0501-loop-check", "kind": "DETERMINISTIC", "required": true,
			"expected": "settled with drained tree", "command_key": "test.runtime", "rubric_ref": nil,
			"qualification_id": nil, "not_applicable_reason": nil}}}
	contract["contract_hash"] = contractDigest(contract)
	code, goal, body := h.api(ctx, "POST", h.base+"/goals", domain.ID(), h.stateTag(ctx), domain.Object{
		"title": "w0501 delegated loop", "original_intent": "one controlled loop over a real worker",
		"scope": "PROJECT", "requirement_refs": []any{domain.Ref(accReq, "Requirement")},
		"problem_ids": []any{"p-w0501"}, "deliverables": []any{"settled run"}, "acceptance_contract": contract})
	if code != 201 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"goal": code, "body": body})
		return
	}
	code, _, body = h.api(ctx, "POST", h.base+"/goals/"+domain.Str(goal, "id")+"/actions", domain.ID(),
		tagOf(goal), domain.Object{"action": "ACTIVATE", "reason": "fixture"})
	if code != 200 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"activate": code, "body": body})
		return
	}

	newRuntime := func(mode, name string) (domain.Object, int, string) {
		c, rt_, b := h.api(ctx, "POST", h.base+"/runtimes", domain.ID(), h.stateTag(ctx), domain.Object{
			"name": name, "adapter": "codex-cli", "adapter_revision": "windows-job-v1",
			"capabilities": []any{"start", "cancel_job_tree", "reconcile"}, "platform": "windows-amd64",
			"measurement_mode": mode, "credential_ref": nil})
		return rt_, c, b
	}
	fix, code, body := newRuntime("FIXTURE", "w0501 fixture runtime")
	if code != 201 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"runtime": code, "body": body})
		return
	}
	if e := h.svc.RegisterOrchestrationFixture(ctx, h.project, domain.Str(fix, "id")); e != nil {
		ok("W0501-RUNTIME-ADMISSION", false, e)
		return
	}
	live, code, body := newRuntime("LIVE", "w0501 unqualified live runtime")
	if code != 201 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"live runtime": code, "body": body})
		return
	}

	newSubmittedTask := func(label string) (domain.Object, int, string) {
		_, g, _ := h.api(ctx, "GET", h.base+"/goals/"+domain.Str(goal, "id"), "", "", nil)
		c, task, b := h.api(ctx, "POST", h.base+"/tasks", domain.ID(), tagOf(g), domain.Object{
			"goal_id": domain.Str(goal, "id"), "title": "w0501 loop " + label, "task_type": "json-verification",
			"stage": "verification", "dependency_task_ids": domain.Empty(),
			"requirement_refs": []any{domain.Ref(accReq, "Requirement")}, "input_refs": domain.Empty(),
			"acceptance_contract": contract, "origin_problem_id": "p-w0501", "candidate_id": "c-" + label,
			"stop_policy": domain.Object{"wall_time_seconds": 60, "max_attempts": 1, "max_parallel_runs": 1,
				"stop_conditions": []any{"no effective progress"}}})
		if c != 201 {
			return task, c, b
		}
		_, state, _ := h.api(ctx, "GET", h.base+"/state", "", "", nil)
		c, _, b = h.api(ctx, "POST", h.base+"/context-bundles", domain.ID(), tagOf(state), domain.Object{
			"task_id": domain.Str(task, "id"), "expected_project_state_revision": state["revision"]})
		if c != 201 {
			return task, c, b
		}
		_, t2, _ := h.api(ctx, "GET", h.base+"/tasks/"+domain.Str(task, "id"), "", "", nil)
		c, _, b = h.api(ctx, "POST", h.base+"/tasks/"+domain.Str(task, "id")+"/actions", domain.ID(),
			tagOf(t2), domain.Object{"action": "SUBMIT", "reason": "frozen bundle and contract"})
		_, t3, _ := h.api(ctx, "GET", h.base+"/tasks/"+domain.Str(task, "id"), "", "", nil)
		return t3, c, b
	}

	taskA, code, body := newSubmittedTask("a")
	if code != 200 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"submit a": code, "body": body})
		return
	}
	executor := domain.ID()
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: executor, Roles: []string{"EXECUTOR"}}); e != nil {
		ok("W0501-RUNTIME-ADMISSION", false, e)
		return
	}
	code, claim, body := h.api(ctx, "POST", h.base+"/tasks/"+domain.Str(taskA, "id")+"/claim", domain.ID(),
		tagOf(taskA), domain.Object{"runtime_id": domain.Str(fix, "id"), "executor_principal_id": executor,
			"context_bundle_id": taskA["context_bundle_id"]})
	run, _ := claim["run"].(domain.Object)
	if run == nil {
		if m, isMap := claim["run"].(map[string]any); isMap {
			run = domain.Object(m)
		}
	}
	ok("W0501-FIXTURE-RUNTIME-CLAIM-ADMITTED",
		code == 201 && run != nil && domain.Str(run, "id") != "" && run["lease_epoch"] != nil &&
			domain.Str(claim, "lease_token") != "",
		domain.Object{"code": code, "run_id_present": run != nil && domain.Str(run, "id") != "",
			"lease_epoch": runField(run, "lease_epoch"), "body": body})

	taskB, code, body := newSubmittedTask("b")
	if code != 200 {
		ok("W0501-RUNTIME-ADMISSION", false, domain.Object{"submit b": code, "body": body})
		return
	}
	executor2 := domain.ID()
	if e := h.svc.ProvisionPrincipal(ctx, domain.Principal{ID: executor2, Roles: []string{"EXECUTOR"}}); e != nil {
		ok("W0501-RUNTIME-ADMISSION", false, e)
		return
	}
	code, refused, body := h.api(ctx, "POST", h.base+"/tasks/"+domain.Str(taskB, "id")+"/claim", domain.ID(),
		tagOf(taskB), domain.Object{"runtime_id": domain.Str(live, "id"), "executor_principal_id": executor2,
			"context_bundle_id": taskB["context_bundle_id"]})
	// the service answers 503 RESOURCE_UNAVAILABLE with the qualification rule named; a 4xx-only
	// assertion would have failed a refusal that is actually correct
	ok("W0501-UNQUALIFIED-LIVE-RUNTIME-REFUSED",
		code == 503 && strings.Contains(body, "LIVE runtime has no current qualification") &&
			refused["id"] == nil,
		domain.Object{"code": code, "body": body})
	note("live_claim", code >= 400, body)

	if run != nil && domain.Str(run, "id") != "" {
		code, _, body = h.api(ctx, "POST", h.base+"/runs/"+domain.Str(run, "id")+"/report", domain.ID(),
			tagOf(run), domain.Object{"artifacts": domain.Empty(), "exit_code": 0, "metrics": domain.Empty()})
		_, after, _ := h.api(ctx, "GET", h.base+"/runs/"+domain.Str(run, "id"), "", "", nil)
		ok("W0501-REPORT-WITHOUT-TRUSTED-OBSERVATION-REFUSED",
			code >= 400 && code < 500 && domain.Str(after, "status") == domain.Str(run, "status"),
			domain.Object{"code": code, "body": body, "run_status": after["status"]})

		usage, e := h.svc.BudgetUsage(ctx, h.token, h.project, domain.Str(run, "id"))
		if e != nil {
			ok("W0501-FIXTURE-DISPATCH-CHARGE-IS-PROVEN-ZERO", false, e)
		} else {
			reserved := domain.Arr(usage, "reserved")
			zeroFixture, otherReserved := 0, 0
			for _, v := range reserved {
				hold, isObj := v.(domain.Object)
				if !isObj {
					if m, isMap := v.(map[string]any); isMap {
						hold = domain.Object(m)
					} else {
						continue
					}
				}
				money, _ := hold["money"].(map[string]any)
				amount, _ := money["amount"].(string)
				if strings.HasPrefix(domain.Str(hold, "provider_request_id"), "fixture-dispatch/") && amount == "0" {
					zeroFixture++
				} else {
					otherReserved++
				}
			}
			// the fixture path may only ever charge a proven zero; anything else would be an invented price
			ok("W0501-FIXTURE-DISPATCH-CHARGE-IS-PROVEN-ZERO",
				zeroFixture >= 1 && otherReserved == 0 && len(domain.Arr(usage, "incurred")) == 0 &&
					len(domain.Arr(usage, "estimated")) == 0 && len(domain.Arr(usage, "unknown")) == 0,
				domain.Object{"zero_fixture": zeroFixture, "other_reserved": otherReserved, "usage_columns": usage})
			note("budget_columns", true, domain.Object{"reserved": len(reserved)})
		}

	}
	// the Run-identity half of the card's events-and-cost property, asserted rather than disclosed: the
	// worker is started under the claimed domain Run id, task id and lease epoch, the settled journal must
	// carry exactly those values, and the ledger reservation must be keyed to the same Run id. The half
	// that stays disclosed is the dispatch-side event ledger: nothing in this tree launches the adapter
	// from the service, and that is the qualification gate rather than a call this program could have made
	if domain.Str(run, "id") != "" {
		rbase := filepath.Join(repoRoot(), ".local", "w0501-run", "runbound")
		_ = os.RemoveAll(rbase)
		if e := os.MkdirAll(rbase, 0o700); e != nil {
			ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, e)
		} else {
			rv, rws, rve := workspace(rbase, "runbound")
			if rve != nil {
				ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, rve)
			} else if wErr := os.WriteFile(filepath.Join(rws, "input.txt"), []byte("w0501 run bound 913\n"), 0o600); wErr != nil {
				ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, wErr)
			} else {
				var epoch int64 = 1
				if f, isNum := runField(run, "lease_epoch").(float64); isNum && int64(f) >= 1 {
					epoch = int64(f)
				}
				exe := comspec()
				if exe == "" {
					ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, "no absolute cmd.exe available in this environment")
				} else {
					rw, rwe := rt.Start(rv, rt.Spec{RunID: domain.Str(run, "id"), TaskID: domain.Str(taskA, "id"),
						Epoch: epoch,
						Commands: []rt.Command{{Executable: exe,
							Args:      []string{"/c", "copy", "/y", "input.txt", "output.txt"},
							Directory: rws}},
						Environment: rt.Environment(""), Lease: 90 * time.Second, Timeout: 60 * time.Second,
						Outputs: []string{"output.txt"}})
					if rwe != nil {
						ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL", false, rwe)
					} else {
						rctx, rcancel := context.WithTimeout(ctx, 120*time.Second)
						defer rcancel()
						rj, rjer := rw.Wait(rctx)
						runs, runsErr := h.svc.BudgetUsage(rctx, h.token, h.project, domain.Str(run, "id"))
						key, keyed, other := "fixture-dispatch/"+domain.Str(run, "id"), 0, 0
						for _, v := range domain.Arr(runs, "reserved") {
							hold, isObj := v.(domain.Object)
							if !isObj {
								if m2, isMap := v.(map[string]any); isMap {
									hold = domain.Object(m2)
								} else {
									continue
								}
							}
							if domain.Str(hold, "provider_request_id") == key {
								keyed++
							} else {
								other++
							}
						}
						ok("W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL",
							rjer == nil && runsErr == nil && rj.State == "SETTLED" &&
								rj.Spec.RunID == domain.Str(run, "id") && rj.Spec.TaskID == domain.Str(taskA, "id") &&
								rj.Spec.Epoch == epoch && len(rj.Artifacts) == 1 &&
								len(rj.Streams) >= 1 && rj.Streams[0].OutHash != "" && keyed >= 1 && other == 0,
							domain.Object{"journal_run": rj.Spec.RunID, "journal_task": rj.Spec.TaskID,
								"journal_epoch": rj.Spec.Epoch, "run_epoch": epoch, "state": rj.State,
								"artifacts": len(rj.Artifacts), "streams": len(rj.Streams),
								"ledger_keyed": keyed, "ledger_other": other,
								"wait_error": fmt.Sprint(rjer), "usage_error": fmt.Sprint(runsErr)})
					}
				}
			}
		}
	}

	// The v2.4 route is a non-executing gap preflight, never the old Codex LIVE harness.
	liveGate, gateErr := runtimePythonCommand(repoRoot(), "ops/ci/runtime_v24.py", "live")
	gateText := fmt.Sprint(gateErr)
	if gateErr == nil {
		liveGate.Env = append(os.Environ(), "RESEARCHOS_TASK_ID=W05", "RESEARCHOS_CHECK_ID=W05-G02",
			"RESEARCHOS_CASE_ID=", "PYTHONUTF8=1")
		out, runErr := liveGate.CombinedOutput()
		gateErr, gateText = runErr, string(out)
	}
	ok("W0501-LIVE-GATE-REFUSES-WITHOUT-EXPLICIT-OPT-IN",
		gateErr != nil && strings.Contains(gateText, `"status": "BLOCKED"`) &&
			strings.Contains(gateText, `"assertion_ids": []`) && !strings.Contains(gateText, `"status": "PASS"`), gateText)

	executionRecord := filepath.Join(repoRoot(), "ops", "runtime", "capabilities.json")
	cap := domain.Object{}
	if b, e := os.ReadFile(executionRecord); e == nil {
		_ = json.Unmarshal(b, &cap)
	}
	pinned := domain.Str(cap, "executor_sha256")
	installed := []string{}
	digests := []string{}
	dir := filepath.Join(os.Getenv("LOCALAPPDATA"), "OpenAI", "Codex", "bin")
	if hits, e := filepath.Glob(filepath.Join(dir, "*", "codex.exe")); e == nil {
		for _, p := range hits {
			b, e := os.ReadFile(p)
			if e == nil {
				installed = append(installed, filepath.Base(filepath.Dir(p))+"="+sha(b)[:24])
				digests = append(digests, sha(b))
			}
		}
	}
	note("executor_identity", true, domain.Object{"pinned": head(pinned, 24), "installed": installed,
		"digests_compared": len(digests), "compared_by": "full 64-hex digest of each installed codex.exe",
		"any_match": anyHashMatches(digests, pinned)})
	skip("W0501-LIVE-MODEL-TOOL-FILE-READ",
		"model shell tool execution and model workspace writes are denied by the current executor policy (ops/runtime/capabilities.json unavailable_capabilities), and the executor binary pinned by that record ("+head(pinned, 16)+"…) is absent while a different build is installed, so the live identity cannot be re-qualified without silently substituting the binary, which the card forbids; a real file read is proven only through the adapter phase, which runs without a model")
	skip("W0501-A04-TOOL-FAILED-AND-ACTIVE-TOOL-CANCELLATION",
		"carried from ops/runtime/capabilities.json acceptance: exit 7 from a real tool and cancellation of an active model tool stay BLOCKED because the tool never starts")
	skip("W0501-PROVIDER-MODEL-REVISION-AND-EXACT-COST",
		"the provider discloses token usage but not exact model revision or cost, so Run cost stays UNKNOWN by contract; only the fixture dispatch zero charge is asserted")
	// the card's own step 1 and the remaining step 4 classes are named here rather than left to a
	// reader's guess: a property that did not run is only honest while the disclosure list is complete
	skip("W0501-PROVIDER-MODELS-CONFIGURE-PROBE",
		"step 1's model directory, connection, authentication and real reasoning round trip is NOT_RUN for a reason measured in the client binding rather than in the executor: execution/v2.4/client_mapping.json records provider.models as PLANNED owned by W02-03 and provider.probe as PLANNED owned by W08-01, of the 23 mapped methods twenty carry an empty rpc_binding, provider.models is marked n/a (Go-owned catalog), provider.probe is empty, and only session.send and session.control name anything at all, so there is no bound client path this card could drive. No provider.* command key exists in either registry (v2.4 revision 14, v2.0 revision 5) and provider.configure is not part of the registered protocol. The separately blocked model backend (ops/runtime/capabilities.json lists model tool execution and model workspace writes as unavailable, and the executor binary pinned there is absent) would still prevent a live round trip after that binding lands. Nothing about the model directory is claimed by this card's PASS")
	skip("W0501-MODEL-SUBSTITUTION-NOT-DETECTED",
		"the card's rule that a fixed model may not be silently swapped for another is NOT_RUN for a reason measured in the decoder rather than in the harness: adapters/runtime/codex.go declares Protocol.ModelRevision and Protocol.Cost and Parse assigns neither, so a settled reply carries no model identity that could be differed from the requested one. What the adapter does enforce, and what is now asserted by W0501-ADAPTER-DECLARED-MODEL-REQUIRES-SETTLED-PROTOCOL with W0501-ADAPTER-JOB-SETTLES-WITHOUT-A-DECLARED-MODEL as its control, is that a declared model requires a settled protocol; that is a liveness rule, not an identity comparison, and this card does not claim otherwise. Closing the substitution property means populating the declared revision from the reply and comparing it against the requested model, which is carried as an obligation")
	skip("W0501-FAILURE-CLASS-EXPLICIT-PROTOCOL-ERROR",
		"the card's fifth step 4 class, an explicit or declared protocol error, is covered by accepted code but not by this check program, and the distinction matters: none of the rows emitted here drives turn.failed or the request_failed the decoder names, while adapters/runtime/runtime_windows_test.go:66-68 does drive all three shapes (terminal turn.failed after a reconnect line, an access-denied error line, and a malformed reconnect diagnostic) inside this card's write scope and passes today. The filter this receipt captured in round 3 did run TestW05Protocol from that same file, but its anchors excluded the sibling TestW05ProtocolTransientReconnect where the three shapes live; the selection is now widened to both names and the package listing is captured as its own receipt command row, so a reviewer can compare the filter against the names the package really contains instead of taking a family name on faith")
	skip("W0501-FAILURE-CLASS-AUTH-RATELIMIT-UNSUPPORTED-TOOL-CALLING",
		"the card's five step 4 failure classes are accounted one at a time, each mapped to exactly one row. Format error is asserted by W0501-PROTOCOL-MALFORMED-LINE-NAMED, which now requires the decoder's own invalid_protocol name rather than any non-empty failure. Explicit or declared protocol error is covered by the pre-existing accepted test named in W0501-FAILURE-CLASS-EXPLICIT-PROTOCOL-ERROR and is not claimed as a row of this program. Authentication failure, rate limit, and a model that does not support tool calling are NOT_RUN: each needs a live provider call and no provider command key is bound for this card, per the provider row above. Transport disconnect is asserted by W0501-PROTOCOL-TRANSPORT-RETRY-NEEDS-LATER-COMPLETION but is a card step 2 transport rule rather than one of the five, and policy denial is asserted by W0501-PROTOCOL-POLICY-DENIAL-IS-TOOL-FAILURE as a step 3 rule, so neither is counted among the five here")
	skip("W0501-CLI-LEG-OF-DELIVERABLE-ONE",
		"the deliverable's own-CLI leg is NOT_RUN for a reason measured in the registry rather than assumed: cli.entry_run is the only cli.* key in execution/v2.4/commands.json at revision 14, its selectors are wildcards so the card's own selector triple does match it, its owner_card names the already-accepted W03-01 interactive CLI, and its state is UNBOUND, so dispatching it for this card returns NOT_IMPLEMENTED with zero assertions. A zero-assertion run is never a PASS, so apps/cli stays unexercised here even though it is inside this card's write scope; the plan-level gap that leaves cli.* UNBOUND is owned by the registry, not by this card")
	skip("W0501-RUN-EVENT-AND-COST-CORRELATION",
		"only the dispatch-side half of the card's events-and-cost-bound-to-the-Run property stays NOT_RUN, and it is stated as the narrow thing it is: the Run identity join is asserted by W0501-RUN-IDENTITY-BOUND-WORKER-JOURNAL, which starts the worker under the claimed Run id, task id and lease epoch and requires the settled journal and the fixture reservation to carry that same Run id, so what is left is the service launching the adapter on its own, and that is the runtime qualification gate (ops/runtime/capabilities.json and the absent pinned executor build) rather than a call this program could have made")
	skip("W0501-NO-BORROWED-ACCOUNT-ASSUMPTION",
		"step 1's clause that the product provider must not borrow Qoder's internal account assumptions is NOT_RUN here and is disclosed rather than asserted: this card registers its runtimes with credential_ref nil and reads no credential value at all, which the program records as a diagnostic, but nothing in the increment can prove the absence of an inherited account assumption in a provider backend that has no bound client path yet. The rule belongs to the provider binding owned by W02-03 and W08-01, and it is carried there")
	skip("W0501-WORKER-IDENTITY-MU-PI-SDK-LOOP",
		"step 2's worker identity is a cmd.exe process killed and drained through a Windows Job Object, and the SDK model and tool loop the card names is NOT wired: the string SDK appears nowhere in the increment outside this row's own text, and the adapter phase runs a fixed command line with no model and no tool round trips. This card is named as the owner of the two commands that would carry that loop: execution/v2.4/commands.json revision 14 lists fork.worker_launch_rpc and fork.worker_stop with owner_card 'W05-01 worker adapter' and both are state UNBOUND, which makes this card the only owner besides test.runtime of an UNBOUND entry in the v2.4 file. Measured along the chain: third_party/mu and third_party/mu/packages/coding-agent exist, dist/rpc-entry.js does not, and the two commands that would build it, fork.build_worker and fork.install_deps, are themselves UNBOUND under W02-99/W01-G03 rerun. So the half this card owes is the adapter-side launch and stop contract, which the adapter phase does drive and the matrix does kill, and the half it cannot reach is a worker binary that another card's commands must produce. A real model-driven loop additionally needs the provider binding the rows above place with W02-03 and W08-01")
	skip("W0501-SINGLE-HOST-CONJUNCT",
		"deliverable 1 asks for the flow to run through the one and only host, and that conjunct is NOT_RUN: client_mapping.json lists host.status and host.configure as PLANNED_IN_W02_03_THEN_W03 owned by W02-03 with an empty rpc_binding, and the sibling CLI gap is measured as cli.entry_run being the only cli.* key in the v2.4 registry, state UNBOUND, wildcard selectors that do match this card, and an owner_card naming the already-accepted W03-01 interactive CLI, so there is no registered host path for this card to drive. What is asserted here is the adapter, the decoder and the shared service reached over its own HTTP handler, which is not the same claim")
	// positive control: the same comparison the absence row relies on must report a match when it is
	// handed a digest that really is installed, otherwise that row could not fail for its stated reason.
	// The harness's own sha() prefixes "sha256:" while capabilities.json stores bare hex, so both shapes
	// are compared here; this clause failed on its first run and is what found that out.
	control := ""
	if len(digests) > 0 {
		control = strings.TrimPrefix(digests[0], "sha256:")
	}
	ok("W0501-PINNED-EXECUTOR-COMPARISON-IS-NOT-VACUOUS",
		control != "" && anyHashMatches(digests, control) && anyHashMatches(digests, "sha256:"+control) &&
			!anyHashMatches(digests, pinned) && len(normalizeDigest(pinned)) == 64,
		domain.Object{"control": head(control, 16), "pinned": head(pinned, 16),
			"bare_hex_accepted":     anyHashMatches(digests, control),
			"prefixed_hex_accepted": anyHashMatches(digests, "sha256:"+control),
			"pin_is_full_hex":       len(normalizeDigest(pinned)) == 64})
	ok("W0501-PINNED-EXECUTOR-IDENTITY-ABSENT-MEASURED",
		pinned != "" && len(digests) > 0 && !anyHashMatches(digests, pinned),
		domain.Object{"pinned": head(pinned, 24), "installed": installed,
			"compared": "full digest of each installed codex.exe against executor_sha256", "digests": len(digests)})
}

func head(s string, n int) string {
	if len(s) < n {
		return s
	}
	return s[:n]
}

// anyHashMatches reports whether one of the recorded digests equals the pinned one. It compares whole
// sha256 values and accepts either the bare hex form used by ops/runtime/capabilities.json or a
// sha256:-prefixed one, because a truncated slice taken on the assumption of a prefix the value does
// not have makes a mismatch unfalsifiable. No credential is involved: these are build digests.
func anyHashMatches(list []string, want string) bool {
	digest := normalizeDigest(want)
	if digest == "" {
		return false
	}
	for _, entry := range list {
		if strings.EqualFold(normalizeDigest(entry), digest) {
			return true
		}
	}
	return false // no recorded digest carries the pinned one
}

// normalizeDigest lower-cases, strips an optional sha256: prefix and rejects anything that is not
// exactly 64 hex characters, so a malformed pin cannot silently compare equal to nothing.
func normalizeDigest(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	if after, isPrefix := strings.CutPrefix(s, "sha256:"); isPrefix {
		s = after
	}
	if len(s) != 64 {
		return ""
	}
	for _, r := range s {
		if !((r >= '0' && r <= '9') || (r >= 'a' && r <= 'f')) {
			return ""
		}
	}
	return s
}

func runField(o domain.Object, key string) any {
	if o == nil {
		return nil
	}
	return o[key]
}
