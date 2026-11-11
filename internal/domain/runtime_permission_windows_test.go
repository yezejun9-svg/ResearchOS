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

func TestPermissionProducerNeverTurnsFrozenWriteDenialIntoUserChoice(t *testing.T) {
	policy := Object{"user_confirmation_tools": []any{"write", "edit"}, "write_paths": []any{"draft.txt"}, "max_write_bytes": 8}
	missing, missingErr := permissionSelection(Object{}, "write")
	read, readErr := permissionSelection(policy, "read")
	write, writeErr := permissionSelection(policy, "write")
	if missingErr != nil || readErr != nil || writeErr != nil || missing || read || !write {
		t.Fatal("only explicitly selected mutating tools may enter the permission flow")
	}
	for name, malformed := range map[string]any{"null": nil, "text": "write", "unknown": []any{"run_check"}, "duplicate": []any{"write", "write"}, "non-text": []any{42}} {
		t.Run("invalid policy "+name, func(t *testing.T) {
			_, err := permissionSelection(Object{"user_confirmation_tools": malformed}, "write")
			if err == nil {
				t.Fatal("malformed present frozen field bypassed policy denial")
			}
		})
	}
	base := RuntimeToolRequest{Access: "READ_WRITE", Name: "write", Policy: policy, Arguments: Object{"path": "draft.txt", "expected_hash": nil, "content": "saved"}}
	if err := permissionStaticToolGate(base); err != nil {
		t.Fatalf("bounded original write rejected: %v", err)
	}
	for name, mutate := range map[string]func(*RuntimeToolRequest){
		"read-only workspace": func(r *RuntimeToolRequest) { r.Access = "READ_ONLY" },
		"outside path":        func(r *RuntimeToolRequest) { r.Arguments["path"] = "other.txt" },
		"traversal":           func(r *RuntimeToolRequest) { r.Arguments["path"] = "../draft.txt" },
		"oversized content":   func(r *RuntimeToolRequest) { r.Arguments["content"] = strings.Repeat("x", 9) },
		"missing hash":        func(r *RuntimeToolRequest) { delete(r.Arguments, "expected_hash") },
		"unexpected argument": func(r *RuntimeToolRequest) {
			r.Arguments["command"] = "run"
		},
	} {
		t.Run(name, func(t *testing.T) {
			r := base
			r.Arguments = Merge(Object{}, base.Arguments)
			mutate(&r)
			if err := permissionStaticToolGate(r); err == nil {
				t.Fatal("frozen-policy violation reached user-decidable path")
			}
		})
	}
}

func TestPermissionRespondCannotFindAReplacementWaiter(t *testing.T) {
	coordinator := &RuntimeCoordinator{}
	waiting, resourcesReady, err := coordinator.CheckPermission(context.Background(), nil, "project", "session",
		Object{"run_id": "run", "key": "effect"}, Object{"request_id": "request"}, Object{"authority": "USER_DECIDABLE"})
	if err != nil || waiting || resourcesReady {
		t.Fatalf("absent original waiter must not schedule replay: waiting=%v resourcesReady=%v error=%v", waiting, resourcesReady, err)
	}
}

type permissionWorkspaceFixture struct{ root string }

func (p permissionWorkspaceFixture) ConsumeSelection(context.Context, string, string, string) (WorkspaceSelection, error) {
	return WorkspaceSelection{}, fmt.Errorf("fixture selection unavailable")
}

func (p permissionWorkspaceFixture) ConfirmPath(_ context.Context, path, access string) error {
	if path != p.root || access != "READ_WRITE" {
		return fmt.Errorf("fixture workspace changed")
	}
	return nil
}

func TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite(t *testing.T) {
	for _, choice := range []string{"ALLOW_ONCE", "DENY"} {
		t.Run(choice, func(t *testing.T) {
			runtimePermissionToolCycle(t, choice)
		})
	}
}

func TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite(t *testing.T) {
	runtimePermissionToolCycle(t, "EXPIRE")
}

func TestRuntimePermissionDecisionWaitsForAnotherRequiredResource(t *testing.T) {
	runtimePermissionToolCycle(t, "BLOCKED_ALLOW")
}

func runtimePermissionToolCycle(t *testing.T, choice string) {
	var providerCalls, physicalWrites atomic.Int32
	c, route, r, _ := muBrokerFixtureProgram(t, func(w http.ResponseWriter, request *http.Request) {
		n := providerCalls.Add(1)
		var body Object
		if json.NewDecoder(request.Body).Decode(&body) != nil {
			t.Error("invalid fixture model request")
			w.WriteHeader(400)
			return
		}
		delta, finish := Object{"role": "assistant", "content": "qualified"}, "stop"
		if n == 2 {
			delta = Object{"role": "assistant", "tool_calls": []any{Object{"index": 0, "id": "original-write", "type": "function", "function": Object{"name": "write", "arguments": `{"path":"draft.txt","expected_hash":null,"content":"approved"}`}}}}
			finish = "tool_calls"
		} else if n == 3 {
			delta["content"] = "File saved."
		} else if n != 1 {
			t.Errorf("unexpected model request %d", n)
		}
		w.Header().Set("Content-Type", "text/event-stream")
		for i, part := range []Object{delta, {}} {
			var stop any
			if i == 1 {
				stop = finish
			}
			fmt.Fprintf(w, "data: %s\n\n", Bytes(Object{"id": "permission-fixture", "object": "chat.completion.chunk", "created": 1, "model": "fixture-model", "choices": []any{Object{"index": 0, "delta": part, "finish_reason": stop}}}))
		}
		fmt.Fprint(w, "data: [DONE]\n\n")
	}, func(config, profile Object) {
		config["tools"] = []any{Object{"type": "function", "function": Object{"name": "write", "description": "Write an authorized file", "parameters": Object{"type": "object", "properties": Object{"path": Object{"type": "string"}, "expected_hash": Object{"type": []any{"string", "null"}}, "content": Object{"type": "string"}}, "required": []any{"path", "expected_hash", "content"}, "additionalProperties": false}}}}
		profile["tool_policy"] = Object{"max_calls": 1, "read_paths": Empty(), "write_paths": []any{"draft.txt"}, "max_read_bytes": 4096, "max_write_bytes": 4096, "user_confirmation_tools": []any{"write"}}
		profile["effect_routes"] = append(Arr(profile, "effect_routes"), Object{"id": config["route"], "capability": "TOOL", "credential_revision": "local-tools-v1", "upper_bound": dollars("0")})
	})
	qualifyNativeCoordinator(t, c, route, r)
	f := r.f
	f.token = r.ownerToken
	workspace := t.TempDir()
	c.config.WorkspaceAuthority = permissionWorkspaceFixture{workspace}
	c.config.ClientSchema = clientHistoryDoc(t)
	c.config.RunTool = func(_ context.Context, request RuntimeToolRequest) (Object, error) {
		if request.Name != "write" || request.WorkspacePath != workspace || request.Access != "READ_WRITE" || request.Arguments["path"] != "draft.txt" || request.Arguments["content"] != "approved" {
			return nil, fmt.Errorf("tool request changed after original permission")
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
	binding := WorkspaceBinding{AuthorizedRef: "permission-workspace", DisplayName: "permission fixture", DisplayPath: workspace, RealPath: workspace, Access: "READ_WRITE", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "permission-client", HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err = f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, binding.AuthorizedRef, string(Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	service := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c, WorkspaceAuthority: permissionWorkspaceFixture{workspace}, WorkspaceFiles: &clientWorkspacePort{}, Host: ClientHostInfo{CoreBuildID: "permission-fixture", LeaseTTL: time.Minute}}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("permission-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": binding.AuthorizedRef, "model_config_ref": modelRoute.ModelConfig["ref"], "title": "permission turn"})}
	created := muClientCall(t, f, service, env)
	sessionID := deref(created.SessionID)
	env = &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("permission-client"), ProjectID: &f.project, SessionID: created.SessionID, Method: strptr("session.send"), ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Payload: Bytes(Object{"text": "Write draft.txt", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
	muClientCall(t, f, service, env)
	var runCtx context.Context
	var cancelRun context.CancelFunc
	if choice == "EXPIRE" {
		runCtx, cancelRun = context.WithTimeout(context.Background(), 15*time.Second)
	} else {
		runCtx, cancelRun = context.WithCancel(context.Background())
	}
	defer cancelRun()
	if err = c.Scan(runCtx); err != nil {
		t.Fatal(err)
	}
	var requestID, runID string
	deadline := time.Now().Add(15 * time.Second)
	for time.Now().Before(deadline) {
		err = f.db.QueryRow(`SELECT json_extract(body,'$.permission.request_id'),run FROM resource_effects WHERE project=? AND json_extract(body,'$.permission.session_id')=? ORDER BY rowid DESC LIMIT 1`, f.project, sessionID).Scan(&requestID, &runID)
		if err == nil && requestID != "" {
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	if requestID == "" {
		t.Fatalf("production broker did not emit permission request: %v", err)
	}
	var resource Object
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var e error
		resource, e = load(tx, f.project, "ResourceRequest", requestID)
		return e
	})
	var other Object
	if choice == "BLOCKED_ALLOW" {
		var taskID string
		if err = f.db.QueryRow("SELECT task_id FROM client_sessions WHERE id=?", sessionID).Scan(&taskID); err != nil {
			t.Fatal(err)
		}
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			principal, e := clientPrincipal(context.Background(), tx, f.owner, f.project, true)
			if e != nil {
				return e
			}
			other, e = f.s.createResourceRequest(tx, principal, f.project, Object{"category": "BUSINESS_CHOICE", "account_ref": nil,
				"reason_code": "OTHER_REQUIRED_RESOURCE", "summary": "A second required resource remains open", "blocked_task_ids": []any{taskID},
				"continuable_task_ids": Empty(), "completed_artifact_refs": Empty(), "requested_capability": "Resolve second required resource",
				"estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil})
			if e != nil {
				return e
			}
			return f.s.event(tx, f.project, "ResourceRequest", other, principal.ID, ID(), "RESOURCE_REQUESTED")
		})
	}
	var required, canonical int
	if err = f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='PERMISSION_REQUIRED'`, f.project, sessionID).Scan(&required); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.event_type')='RESOURCE_REQUESTED' AND json_extract(body,'$.aggregate_ref.id')=?`, f.project, requestID).Scan(&canonical); err != nil {
		t.Fatal(err)
	}
	if required != 1 || canonical != 1 {
		t.Fatalf("permission event=%d resource event=%d", required, canonical)
	}
	var revision, epoch int64
	if err = f.db.QueryRow("SELECT revision,writer_epoch FROM client_sessions WHERE id=?", sessionID).Scan(&revision, &epoch); err != nil {
		t.Fatal(err)
	}
	var digest string
	if err = f.db.QueryRow(`SELECT json_extract(body,'$.permission.action_digest') FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=? ORDER BY sequence DESC LIMIT 1`, f.project, runID, requestID).Scan(&digest); err != nil {
		t.Fatal(err)
	}
	if choice != "EXPIRE" {
		decision := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("permission-client"), ProjectID: &f.project, SessionID: created.SessionID, Method: strptr("permission.respond"), ExpectedRevision: &revision, WriterEpoch: &epoch,
			Payload: Bytes(Object{"resource_request_id": requestID, "resource_request_revision": resource["revision"], "action_digest": digest, "decision": map[bool]string{true: "ALLOW_ONCE", false: choice}[choice == "BLOCKED_ALLOW"], "reason": "fixture owner choice"})}
		response := muClientCall(t, f, service, decision)
		if choice == "BLOCKED_ALLOW" {
			if response.Result["consumed"] != true || response.Result["resumption_scheduled"] != false || physicalWrites.Load() != 0 {
				t.Fatalf("other resource did not defer consumed decision: %s writes=%d", Bytes(response), physicalWrites.Load())
			}
			var state, decided string
			if err = f.db.QueryRow(`SELECT json_extract(body,'$.state'),json_extract(body,'$.permission.decision') FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=? ORDER BY sequence DESC LIMIT 1`, f.project, runID, requestID).Scan(&state, &decided); err != nil {
				t.Fatal(err)
			}
			if state != "STARTED" || decided != "ALLOW_ONCE" {
				t.Fatalf("blocked permission did not preserve original STARTED action: %s %s", state, decided)
			}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				principal, e := clientPrincipal(context.Background(), tx, f.owner, f.project, true)
				if e != nil {
					return e
				}
				evidence, e := sealPermissionArtifact(f.s, tx, principal, f.project, Bytes(Object{"schema": "researchos.second-resource-resolution.v1", "request_id": other["id"], "at": Now()}), "FIXTURE")
				if e != nil {
					return e
				}
				resolved, e := f.s.resolveResourceRequest(tx, principal, f.project, Str(other, "id"), Object{"resolution_evidence_refs": []any{Ref(evidence, "Artifact")}, "reason": "fixture prerequisite completed"})
				if e != nil {
					return e
				}
				return f.s.event(tx, f.project, "ResourceRequest", resolved, principal.ID, ID(), "RESOURCE_REQUESTED")
			})
		}
	}
	c.workers.Wait()
	select {
	case workerErr := <-c.errors:
		if choice == "ALLOW_ONCE" {
			t.Fatalf("allowed broker failed: %v", workerErr)
		}
	default:
	}
	writes := physicalWrites.Load()
	bytes, readErr := os.ReadFile(filepath.Join(workspace, "draft.txt"))
	if choice == "ALLOW_ONCE" || choice == "BLOCKED_ALLOW" {
		if writes != 1 || readErr != nil || string(bytes) != "approved" {
			t.Fatalf("allow did not produce exactly one physical write: count=%d content=%q err=%v", writes, bytes, readErr)
		}
	} else if writes != 0 || !os.IsNotExist(readErr) {
		t.Fatalf("deny physically wrote file: count=%d err=%v", writes, readErr)
	}
	var state string
	if err = f.db.QueryRow(`SELECT json_extract(body,'$.state') FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=? ORDER BY sequence DESC LIMIT 1`, f.project, runID, requestID).Scan(&state); err != nil {
		t.Fatal(err)
	}
	if (choice == "ALLOW_ONCE" || choice == "BLOCKED_ALLOW") && state != "CONFIRMED" || (choice == "DENY" || choice == "EXPIRE") && state != "NOT_APPLIED" {
		t.Fatalf("original effect state=%s after %s", state, choice)
	}
	if choice == "BLOCKED_ALLOW" {
		var scopes int
		var currentRunID string
		if err = f.db.QueryRow(`SELECT count(DISTINCT json_extract(body,'$.permission.scope_ref.id')) FROM resource_effects WHERE project=? AND run=? AND json_extract(body,'$.permission.request_id')=?`, f.project, runID, requestID).Scan(&scopes); err != nil {
			t.Fatal(err)
		}
		if err = f.db.QueryRow("SELECT run_id FROM client_sessions WHERE id=?", sessionID).Scan(&currentRunID); err != nil {
			t.Fatal(err)
		}
		if scopes != 1 || currentRunID != runID || providerCalls.Load() != 3 {
			t.Fatalf("deferred grant launched a replacement action: scopes=%d old=%s now=%s modelCalls=%d", scopes, runID, currentRunID, providerCalls.Load())
		}
	}
	if choice != "EXPIRE" {
		if err = f.db.QueryRow("SELECT revision,writer_epoch FROM client_sessions WHERE id=?", sessionID).Scan(&revision, &epoch); err != nil {
			t.Fatal(err)
		}
		stale := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("permission-client"), ProjectID: &f.project, SessionID: created.SessionID, Method: strptr("permission.respond"), ExpectedRevision: &revision, WriterEpoch: &epoch,
			Payload: Bytes(Object{"resource_request_id": requestID, "resource_request_revision": resource["revision"], "action_digest": digest, "decision": "ALLOW_ONCE", "reason": "attempt to replay old run"})}
		var response *Response
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			var executeErr error
			response, _, executeErr = service.Execute(context.Background(), tx, handlerDecode(t, stale), f.owner)
			return executeErr
		})
		if deref(response.Status) != "REJECTED" || physicalWrites.Load() != writes {
			t.Fatalf("closed original run accepted a second decision: response=%s writes=%d", Bytes(response), physicalWrites.Load())
		}
	}
	if choice == "EXPIRE" {
		var status string
		if err = f.db.QueryRow(`SELECT json_extract(body,'$.status') FROM domain_objects WHERE project=? AND kind='ResourceRequest' AND id=?`, f.project, requestID).Scan(&status); err != nil {
			t.Fatal(err)
		}
		if err = f.db.QueryRow(`SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.event_type')='RESOURCE_REQUESTED' AND json_extract(body,'$.aggregate_ref.id')=?`, f.project, requestID).Scan(&canonical); err != nil {
			t.Fatal(err)
		}
		if status != "RESOLVED" || canonical != 2 {
			t.Fatalf("expired permission request remained actionable: status=%s canonical events=%d", status, canonical)
		}
	}
}
