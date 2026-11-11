//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

type muWorkspaceFixture struct{ root string }

func (a muWorkspaceFixture) ConsumeSelection(context.Context, string, string, string) (WorkspaceSelection, error) {
	return WorkspaceSelection{}, fmt.Errorf("fixture selection is not an authorization flow")
}
func (a muWorkspaceFixture) ConfirmPath(_ context.Context, path, access string) error {
	if path != a.root || access != "READ_ONLY" {
		return fmt.Errorf("workspace changed")
	}
	return nil
}

func muClientCall(t *testing.T, f *fixture, service *ClientService, env *Envelope) *Response {
	t.Helper()
	env = handlerDecode(t, env)
	var reply *Response
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		reply, _, err = service.Execute(context.Background(), tx, env, f.owner)
		return err
	})
	if deref(reply.Status) != "COMPLETED" {
		t.Fatalf("typed command %s: %s", deref(env.Method), Bytes(reply))
	}
	return reply
}

func TestRuntimeMuSessionToolAndIndependentAcceptance(t *testing.T) {
	runtimeMuToolCycle(t, false)
}

func TestRuntimeMuToolRefusalAllowsNextTurn(t *testing.T) {
	runtimeMuToolCycle(t, true)
}

func runtimeMuToolCycle(t *testing.T, refuse bool) {
	var sequence, toolCalls atomic.Int32
	const witness = "workspace-file-observation-7719"
	c, route, r, calls := muBrokerFixtureProgram(t, func(w http.ResponseWriter, request *http.Request) {
		n := sequence.Add(1)
		var body Object
		if json.NewDecoder(request.Body).Decode(&body) != nil {
			t.Error("missing actual SDK request")
			w.WriteHeader(400)
			return
		}
		delta, finish := Object{"role": "assistant", "content": "qualified"}, "stop"
		if n == 2 {
			delta = Object{"role": "assistant", "tool_calls": []any{Object{"index": 0, "id": "call-read", "type": "function", "function": Object{"name": "read", "arguments": "{\"path\":\"evidence.txt\"}"}}}}
			finish = "tool_calls"
		} else if n == 3 {
			if !strings.Contains(string(Bytes(body["messages"])), witness) {
				t.Error("tool result never reached the next SDK model request")
			}
			delta["content"] = "已读取工作区文件。"
		} else if n != 1 {
			t.Errorf("unexpected provider call %d", n)
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for i, part := range []Object{delta, {}} {
			var stop any
			if i == 1 {
				stop = finish
			}
			fmt.Fprintf(w, "data: %s\n\n", Bytes(Object{"id": "fixture-response", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{Object{"index": 0, "delta": part, "finish_reason": stop}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}, func(config, profile Object) {
		config["tools"] = []any{Object{"type": "function", "function": Object{"name": "read", "description": "Read an authorized workspace file", "parameters": Object{"type": "object", "properties": Object{"path": Object{"type": "string"}}, "required": []any{"path"}, "additionalProperties": false}}}}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": []any{"evidence.txt"}, "write_paths": Empty(), "max_read_bytes": 4096, "max_write_bytes": 4096}
		profile["effect_routes"] = append(Arr(profile, "effect_routes"), Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": dollars("0")})
	})
	qualifyNativeCoordinator(t, c, route, r)
	f := r.f
	f.token = r.ownerToken
	workspace := t.TempDir()
	if err := os.WriteFile(filepath.Join(workspace, "evidence.txt"), []byte(witness), 0600); err != nil {
		t.Fatal(err)
	}
	c.config.WorkspaceAuthority = muWorkspaceFixture{workspace}
	c.config.ClientSchema = clientHistoryDoc(t)
	c.config.RunTool = func(_ context.Context, request RuntimeToolRequest) (Object, error) {
		toolCalls.Add(1)
		if refuse {
			return nil, &RuntimeToolFailure{Err: fmt.Errorf("fixture file absent before IO"), Outcome: "NOT_APPLIED"}
		}
		if request.WorkspacePath != workspace || request.Access != "READ_ONLY" || request.Name != "read" || request.Arguments["path"] != "evidence.txt" {
			return nil, fmt.Errorf("tool escaped its bound workspace")
		}
		content, err := os.ReadFile(filepath.Join(workspace, "evidence.txt"))
		return Object{"content": []any{Object{"type": "text", "text": string(content)}}, "details": Object{"content_hash": Digest(content)}}, err
	}
	modelRoute := c.config.Providers[0]
	modelRoute.Purpose = "mu_turn"
	c.config.Providers = append(c.config.Providers, modelRoute, RuntimeProviderRoute{ID: modelRoute.ID, ProjectID: f.project, RuntimeID: route.RuntimeID, Purpose: "mu_turn", Capability: "TOOL", CredentialRevision: "local-tools-v1", UpperBound: dollars("0"), MeasurementMode: "FIXTURE"})
	if err := f.s.AuthorizeRuntimePurpose(context.Background(), f.token, f.project, route.RuntimeID, "mu_turn", time.Now().Add(30*time.Minute)); err != nil {
		t.Fatal(err)
	}
	route.ExecutorID = ID()
	if err := f.s.ProvisionPrincipal(context.Background(), Principal{ID: route.ExecutorID, Roles: []string{"EXECUTOR"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	var tokenErr error
	route.ExecutorToken, tokenErr = f.s.IssueCredential(context.Background(), route.ExecutorID, 15*time.Minute)
	if tokenErr != nil {
		t.Fatal(tokenErr)
	}
	r.executor = route.ExecutorID
	c.config.Routes = []RuntimeCoordinatorRoute{route}
	raw, err := os.ReadFile("../../migrations/sqlite/next_v24_sessions.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.db.Exec(string(raw)); err != nil {
		t.Fatal(err)
	}
	if err = EnsureClientSessionFence(context.Background(), f.db); err != nil {
		t.Fatal(err)
	}
	binding := WorkspaceBinding{AuthorizedRef: "tool-workspace", DisplayName: "tool fixture", DisplayPath: workspace, RealPath: workspace, Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "mu-client", HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err = f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, binding.AuthorizedRef, string(Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	service := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c, Host: ClientHostInfo{CoreBuildID: "mu-tool-fixture", LeaseTTL: time.Minute}}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mu-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": binding.AuthorizedRef, "model_config_ref": modelRoute.ModelConfig["ref"], "title": "tool turn"})}
	created := muClientCall(t, f, service, env)
	env = &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mu-client"), ProjectID: &f.project, SessionID: created.SessionID, Method: strptr("session.send"), ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Payload: Bytes(Object{"text": "读取 evidence.txt 并报告内容", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
	muClientCall(t, f, service, env)
	if err = c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	select {
	case err = <-c.errors:
		t.Fatal(err)
	default:
	}
	var taskID string
	if err = f.db.QueryRow("SELECT task_id FROM client_sessions WHERE id=?", deref(created.SessionID)).Scan(&taskID); err != nil {
		t.Fatal(err)
	}
	r.task = f.read("tasks", taskID)
	if refuse {
		r.run = f.read("runs", Str(r.task, "active_run_id"))
		if r.task["status"] != "FAILED" || r.run["status"] != "FAILED" || calls.Load() != 2 || toolCalls.Load() != 1 {
			t.Fatalf("refused tool did not settle: task=%s run=%s model=%d tool=%d", r.task["status"], r.run["status"], calls.Load(), toolCalls.Load())
		}
		var state string
		if err := f.db.QueryRow(`SELECT json_extract(body,'$.state') FROM resource_effects WHERE run=? AND json_extract(body,'$.payload.capability')='TOOL' ORDER BY sequence DESC LIMIT 1`, r.run["id"]).Scan(&state); err != nil || state != "NOT_APPLIED" {
			t.Fatalf("tool outcome=%s %v", state, err)
		}
		var rev, epoch int64
		if err := f.db.QueryRow("SELECT revision,writer_epoch FROM client_sessions WHERE id=?", deref(created.SessionID)).Scan(&rev, &epoch); err != nil {
			t.Fatal(err)
		}
		env.CommandID, env.ExpectedRevision, env.WriterEpoch = strptr(ID()), &rev, &epoch
		muClientCall(t, f, service, env)
		t.Log("known pre-side-effect tool refusal settled FAILED; NOT_APPLIED preserved, no automatic retry, next explicit session turn accepted")
		return
	}
	if r.task["status"] != "EXECUTION_REPORTED" {
		t.Fatalf("turn not executed: %s", Bytes(r.task))
	}
	r.run = f.read("runs", Str(r.task, "active_run_id"))
	artifact := f.read("artifacts", Arr(r.run, "result_artifact_ids")[0].(string))
	body := (&orchestrationFixture{f: f, owner: r.ownerToken}).acceptance(r, artifact)
	receipt := f.expect(201, "POST", f.path("/acceptances"), ID(), testTag(r.task), body)
	if receipt["verdict"] != "PASS" {
		t.Fatalf("independent turn verification: %s", Bytes(receipt))
	}
	checkMuReceiptRecovery(t, c, r)
	if calls.Load() != 3 || toolCalls.Load() != 1 {
		t.Fatalf("provider=%d tool=%d", calls.Load(), toolCalls.Load())
	}
	var projected int
	if err = f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='MESSAGE' AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='DELTA'`, f.project, deref(created.SessionID)).Scan(&projected); err != nil || projected != 1 {
		t.Fatalf("assistant projection=%d %v", projected, err)
	}
	t.Log("real SDK qualification + typed create/send + canonical scheduler + MODEL/TOOL/MODEL + file witness + independent acceptance + assistant projection; provider and workspace authority are explicit FIXTURE ports")
}

func checkMuReceiptRecovery(t *testing.T, c *RuntimeCoordinator, r *runtimeFixture) {
	t.Helper()
	var locator string
	if err := r.f.db.QueryRow("SELECT journal_locator FROM runtime_dispatches WHERE run=?", r.run["id"]).Scan(&locator); err != nil {
		t.Fatal(err)
	}
	paths, err := filepath.Glob(filepath.Join(c.config.DataRoot, "runtime-dispatches", locator, "effect-*.json"))
	if err != nil {
		t.Fatal(err)
	}
	var fact Object
	for _, path := range paths {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		value, err := Decode(raw)
		if err != nil {
			t.Fatal(err)
		}
		if value["receipt"].(map[string]any)["host_tool"] == "read" {
			fact = value
			break
		}
	}
	if fact == nil {
		t.Fatal("durable tool receipt absent")
	}
	evidence := Object{"bounded_large_manifest": strings.Repeat("x", 160*1024)}
	fact["host_tool_evidence"], fact["host_tool_evidence_hash"] = evidence, Hash(evidence)
	directory := t.TempDir()
	if err := writeRuntimeFact(filepath.Join(directory, "effect-large.json"), Bytes(fact)); err != nil {
		t.Fatal(err)
	}
	epoch, _ := Num(r.run, "lease_epoch")
	if err := c.recoverEffects(context.Background(), r.f.project, Str(r.run, "id"), directory, epoch); err != nil {
		t.Fatalf("valid >128KiB host fact could not recover: %v", err)
	}
	for name, mutate := range map[string]func(Object){
		"run":           func(o Object) { o["receipt"].(map[string]any)["run_id"] = ID() },
		"epoch":         func(o Object) { o["receipt"].(map[string]any)["epoch"] = 99 },
		"state":         func(o Object) { o["receipt"].(map[string]any)["state"] = "UNKNOWN" },
		"response hash": func(o Object) { o["provider_response_hash"] = "sha256:wrong" },
		"evidence hash": func(o Object) { o["host_tool_evidence_hash"] = "sha256:wrong" },
		"tool":          func(o Object) { o["receipt"].(map[string]any)["host_tool"] = "write" },
	} {
		copy, err := Decode(Bytes(fact))
		if err != nil {
			t.Fatal(err)
		}
		mutate(copy)
		if err := c.ingestEffectFact(context.Background(), copy); err == nil {
			t.Fatalf("tampered %s receipt accepted", name)
		}
	}
}
