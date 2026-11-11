//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sync/atomic"
	"testing"
	"time"

	rt "researchos.local/research-os/adapters/runtime"
)

func TestClientGoalCurrentBindingSelection(t *testing.T) {
	config := modelFixtureConfig("https://model.invalid/v1/chat/completions")
	c, route, runtime := coordinatorFixtureProgram(t, false, false, func(profile Object) (string, string) {
		bundle := filepath.Join(t.TempDir(), "inert-bundle.mjs")
		bytes := []byte("// inert model metadata; no worker started\n")
		if err := os.WriteFile(bundle, bytes, 0600); err != nil {
			t.Fatal(err)
		}
		exe, err := os.Executable()
		if err != nil {
			t.Fatal(err)
		}
		profile["backend"], profile["model"], profile["model_config"] = runtimeMuBackend, config["model"], config
		profile["bundle_hash"] = Digest(bytes)
		profile["argv"] = []any{"{bundle}", "{manifest}"}
		profile["effect_routes"] = []any{Object{"id": config["route"], "capability": "MODEL", "credential_revision": "test-v1", "upper_bound": dollars("1")}}
		profile["model_qualification"] = Object{"route": config["route"], "model_config_hash": Hash(config), "max_calls": 1}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": Empty(), "write_paths": Empty(), "max_read_bytes": 16, "max_write_bytes": 16}
		return exe, bundle
	})
	c.config.WorkspaceAuthority = clientWorkspaceAuthority{}
	f := runtime.f
	ctx := context.Background()
	client := "goal-binding-client"
	principal := f.owner
	workspace := "goal-binding-workspace-" + ID()
	insert := func(ref, actor, clientID string) {
		t.Helper()
		b := WorkspaceBinding{AuthorizedRef: ref, DisplayName: "binding fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: actor, ClientID: clientID, HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
		if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, ref, string(Bytes(b))); err != nil {
			t.Fatal(err)
		}
	}
	resolve := func() (string, string, error) {
		t.Helper()
		var workspaceRef, modelRef string
		var resolveErr error
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			workspaceRef, modelRef, resolveErr = c.ResolveGoalBinding(ctx, tx, principal, f.project, client)
			return nil
		})
		return workspaceRef, modelRef, resolveErr
	}
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal selected a workspace without an authorized binding")
	}
	insert("wrong-principal-"+ID(), "other-principal", client)
	insert("wrong-client-"+ID(), principal, "other-client")
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal selected a workspace of another principal or client")
	}
	insert(workspace, principal, client)
	gotWorkspace, gotModel, err := resolve()
	if err != nil || gotWorkspace != workspace || gotModel != Str(config, "ref") {
		t.Fatalf("current goal binding=%q %q err=%v", gotWorkspace, gotModel, err)
	}
	insert("ambiguous-workspace-"+ID(), principal, client)
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal silently selected one of two authorized workspaces")
	}
	if _, err := f.db.Exec(`DELETE FROM domain_objects WHERE project='' AND kind=? AND id LIKE 'ambiguous-workspace-%'`, KindWorkspaceBinding); err != nil {
		t.Fatal(err)
	}
	c.config.Routes = append(c.config.Routes, route)
	if _, _, err := resolve(); err == nil {
		t.Fatal("project goal silently selected one of two model routes")
	}
}

// The project-level command itself creates the original Session. This follows
// that Session through the real broker's tool and permission gates without a
// synthetic session.create receipt or a second Goal/Run.
func TestClientGoalCreatedSessionOriginalToolPermission(t *testing.T) {
	var modelCalls, physicalWrites atomic.Int32
	c, route, runtime, _ := muBrokerFixtureProgram(t, func(w http.ResponseWriter, request *http.Request) {
		n := modelCalls.Add(1)
		delta, finish := Object{"role": "assistant", "content": "qualified"}, "stop"
		if n == 2 {
			delta = Object{"role": "assistant", "tool_calls": []any{Object{"index": 0, "id": "goal-original-write", "type": "function", "function": Object{"name": "write", "arguments": `{"path":"draft.txt","expected_hash":null,"content":"approved"}`}}}}
			finish = "tool_calls"
		} else if n == 3 {
			delta["content"] = "Goal file saved."
		} else if n != 1 {
			t.Errorf("unexpected fixture model call %d", n)
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for i, part := range []Object{delta, {}} {
			var stop any
			if i == 1 {
				stop = finish
			}
			fmt.Fprintf(w, "data: %s\n\n", Bytes(Object{"id": "goal-permission-fixture", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{Object{"index": 0, "delta": part, "finish_reason": stop}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}, func(config, profile Object) {
		config["tools"] = []any{Object{"type": "function", "function": Object{"name": "write", "description": "Write one authorized file", "parameters": Object{"type": "object", "properties": Object{"path": Object{"type": "string"}, "expected_hash": Object{"type": []any{"string", "null"}}, "content": Object{"type": "string"}}, "required": []any{"path", "expected_hash", "content"}, "additionalProperties": false}}}}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": Empty(), "write_paths": []any{"draft.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096, "user_confirmation_tools": []any{"write"}}
		profile["effect_routes"] = append(Arr(profile, "effect_routes"), Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": dollars("0")})
	})
	qualifyNativeCoordinator(t, c, route, runtime)
	f := runtime.f
	f.token = runtime.ownerToken
	workspace := t.TempDir()
	c.config.WorkspaceAuthority = permissionWorkspaceFixture{workspace}
	c.config.ClientSchema = clientHistoryDoc(t)
	c.config.RunTool = func(_ context.Context, request RuntimeToolRequest) (Object, error) {
		if request.Name != "write" || request.WorkspacePath != workspace || request.Access != "READ_WRITE" || request.Arguments["path"] != "draft.txt" || request.Arguments["content"] != "approved" {
			return nil, fmt.Errorf("original Goal tool binding changed")
		}
		if err := os.WriteFile(filepath.Join(workspace, "draft.txt"), []byte("approved"), 0600); err != nil {
			return nil, err
		}
		physicalWrites.Add(1)
		return Object{"content": []any{Object{"type": "text", "text": "saved"}}, "details": Object{"path": "draft.txt"}}, nil
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
	var err error
	route.ExecutorToken, err = f.s.IssueCredential(context.Background(), route.ExecutorID, 15*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
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
	client := "goal-tool-client"
	binding := WorkspaceBinding{AuthorizedRef: "goal-tool-workspace-" + ID(), DisplayName: "goal tool fixture", DisplayPath: workspace, RealPath: workspace, Access: "READ_WRITE", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: client, HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err = f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, binding.AuthorizedRef, string(Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	service := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c,
		WorkspaceAuthority: permissionWorkspaceFixture{workspace}, WorkspaceFiles: &clientWorkspacePort{},
		Host: ClientHostInfo{CoreBuildID: "goal-tool-fixture", LeaseTTL: time.Minute}}
	created, _ := goalCommand(t, f, service, goalEnvelope(f, client, "Write draft.txt", false))
	if deref(created.Status) != "COMPLETED" || created.SessionID != nil {
		t.Fatalf("project Goal did not create a real session: %s", Bytes(created))
	}
	snapshot := created.Result["snapshot"].(map[string]any)
	sessionID, goalID := Str(snapshot, "session_id"), Str(created.Result, "goal_id")
	if sessionID == "" || goalID == "" || snapshot["goal_id"] != goalID || snapshot["workspace_ref"] != binding.AuthorizedRef || snapshot["model_config_ref"] != modelRoute.ModelConfig["ref"] {
		t.Fatalf("Goal result lost original identity: %s", Bytes(created))
	}
	var fakeCreate int
	if err = f.db.QueryRow(`SELECT count(*) FROM idempotency WHERE operation='v2:session.create'`).Scan(&fakeCreate); err != nil || fakeCreate != 0 {
		t.Fatalf("Goal manufactured a session.create receipt: %d %v", fakeCreate, err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	if err = c.Scan(ctx); err != nil {
		t.Fatal(err)
	}
	var requestID, runID, effectKey string
	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		err = f.db.QueryRow(`SELECT json_extract(body,'$.permission.request_id'),run,effect_key FROM resource_effects WHERE project=? AND json_extract(body,'$.permission.session_id')=? ORDER BY rowid DESC LIMIT 1`, f.project, sessionID).Scan(&requestID, &runID, &effectKey)
		if err == nil && requestID != "" {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if requestID == "" {
		t.Fatalf("Goal-created Session did not reach original createToolPermission: %v", err)
	}
	var taskID string
	if err = f.db.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, sessionID).Scan(&taskID); err != nil {
		t.Fatal(err)
	}
	task := f.read("tasks", taskID)
	run := f.read("runs", runID)
	if task["goal_id"] != goalID || task["active_run_id"] != runID || run["task_id"] != taskID {
		t.Fatalf("permission changed original Goal Task/Run: %s %s", Bytes(task), Bytes(run))
	}
	var promptCount, resourceCount int
	if err = f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='PERMISSION_REQUIRED'`, f.project, sessionID).Scan(&promptCount); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow(`SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND id=?`, f.project, requestID).Scan(&resourceCount); err != nil {
		t.Fatal(err)
	}
	if promptCount != 1 || resourceCount != 1 || physicalWrites.Load() != 0 {
		t.Fatalf("original permission not pending: prompt=%d resource=%d writes=%d", promptCount, resourceCount, physicalWrites.Load())
	}
	toolPayload := Object{"name": "write", "arguments": Object{"path": "draft.txt", "expected_hash": nil, "content": "approved"}}
	gate := func(tx *sql.Tx) (RuntimeToolRequest, error) {
		currentTask, e := load(tx, f.project, "Task", taskID)
		if e != nil {
			return RuntimeToolRequest{}, e
		}
		epoch, _ := Num(run, "lease_epoch")
		dispatch, e := runtimeDispatch(tx, f.project, runID, epoch)
		if e != nil {
			return RuntimeToolRequest{}, e
		}
		return c.runtimeToolGate(context.Background(), tx, route, currentTask, dispatch, rt.BridgeFrame{Key: effectKey}, toolPayload)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		owner, e := clientSessionCreationPrincipal(context.Background(), tx, f.project, sessionID)
		if e != nil || owner != f.owner {
			return fmt.Errorf("Goal receipt principal=%q: %w", owner, e)
		}
		request, e := gate(tx)
		if e != nil || request.WorkspacePath != workspace || request.Access != "READ_WRITE" || request.Name != "write" {
			return fmt.Errorf("original runtimeToolGate refused Goal creator: request=%+v err=%w", request, e)
		}
		return nil
	})
	other := ID()
	if err = f.s.ProvisionPrincipal(context.Background(), Principal{ID: other, Roles: []string{"OWNER"}, Grants: []Grant{{ProjectID: f.project}}}); err != nil {
		t.Fatal(err)
	}
	// Abnormal conflicting receipt exists only inside this rollback-only negative
	// transaction; the positive path above has no synthetic creation receipt.
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = tx.Exec(`INSERT INTO idempotency(principal,project,operation,key,request_hash,status,body,headers,created_at) VALUES(?,?,?,?,?,?,?,?,?)`, other, f.project, "v2:session.create", ID(), Hash(Object{}), 200, string(Bytes(Object{"status": "COMPLETED", "result": Object{"session_id": sessionID}})), "{}", Now()); err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	if _, err = gate(tx); err == nil {
		tx.Rollback()
		t.Fatal("original runtimeToolGate accepted conflicting creation attribution")
	}
	tx.Rollback()
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = tx.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','REVOKED') WHERE project='' AND kind=? AND id=?`, KindWorkspaceBinding, binding.AuthorizedRef); err != nil {
		tx.Rollback()
		t.Fatal(err)
	}
	if _, err = gate(tx); err == nil {
		tx.Rollback()
		t.Fatal("original runtimeToolGate accepted revoked Goal workspace")
	}
	tx.Rollback()
	var resource Object
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var loadErr error
		resource, loadErr = load(tx, f.project, "ResourceRequest", requestID)
		return loadErr
	})
	var revision, epoch int64
	if err = f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, sessionID).Scan(&revision, &epoch); err != nil {
		t.Fatal(err)
	}
	var digest string
	if err = f.db.QueryRow(`SELECT json_extract(body,'$.permission.action_digest') FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=? ORDER BY sequence DESC LIMIT 1`, f.project, runID, requestID).Scan(&digest); err != nil {
		t.Fatal(err)
	}
	permission := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, SessionID: &sessionID, Method: strptr("permission.respond"), ExpectedRevision: &revision, WriterEpoch: &epoch,
		Payload: Bytes(Object{"resource_request_id": requestID, "resource_request_revision": resource["revision"], "action_digest": digest, "decision": "ALLOW_ONCE", "reason": "Goal creator approves original tool"})}
	decoded, err := DecodeEnvelope(Bytes(permission))
	if err != nil {
		t.Fatal(err)
	}
	var foreign *Response
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var executeErr error
		foreign, _, executeErr = service.Execute(context.Background(), tx, decoded, other)
		return executeErr
	})
	if deref(foreign.Status) != "REJECTED" || deref(foreign.ErrorCode) != "FORBIDDEN" || physicalWrites.Load() != 0 {
		t.Fatalf("foreign Owner approved original Goal tool: response=%s writes=%d", Bytes(foreign), physicalWrites.Load())
	}
	response := muClientCall(t, f, service, permission)
	if response.Result["consumed"] != true {
		t.Fatalf("Goal creator's original permission not consumed: %s", Bytes(response))
	}
	c.workers.Wait()
	select {
	case workerErr := <-c.errors:
		t.Fatalf("Goal-created Session worker failed: %v", workerErr)
	default:
	}
	content, err := os.ReadFile(filepath.Join(workspace, "draft.txt"))
	if err != nil || string(content) != "approved" || physicalWrites.Load() != 1 {
		t.Fatalf("original write count=%d bytes=%q err=%v", physicalWrites.Load(), content, err)
	}
	var distinctRequests, distinctRuns int
	if err = f.db.QueryRow(`SELECT count(DISTINCT json_extract(body,'$.permission.request_id')),count(DISTINCT run) FROM resource_effects WHERE project=? AND json_extract(body,'$.permission.session_id')=?`, f.project, sessionID).Scan(&distinctRequests, &distinctRuns); err != nil {
		t.Fatal(err)
	}
	if distinctRequests != 1 || distinctRuns != 1 || modelCalls.Load() != 3 {
		t.Fatalf("replacement permission/Run or extra model: requests=%d runs=%d model=%d", distinctRequests, distinctRuns, modelCalls.Load())
	}
	var state string
	if err = f.db.QueryRow(`SELECT json_extract(body,'$.state') FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=? ORDER BY sequence DESC LIMIT 1`, f.project, runID, requestID).Scan(&state); err != nil || state != "CONFIRMED" {
		t.Fatalf("original Goal effect state=%q err=%v", state, err)
	}
	t.Logf("Goal receipt=%s Session=%s Task=%s Run=%s permission=%s; real gate/ResourceRequest, foreign refusal, exactly one original physical write", deref(created.CommandID), sessionID, taskID, runID, requestID)
}
