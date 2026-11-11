//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
	"time"
)

// This tests the typed command transaction, not the native runtime producer.
// The separate runtime tests use the production coordinator permission gate.
type clientPermissionPort struct {
	waiting        bool
	resourcesReady bool
	err            error
	calls          int
}

func (*clientPermissionPort) ValidateBinding(context.Context, *sql.Tx, string, string, string, string) error {
	return nil
}
func (*clientPermissionPort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return Fail(503, "RESOURCE_BLOCKED", "fixture does not dispatch")
}
func (p *clientPermissionPort) CheckPermission(context.Context, *sql.Tx, string, string, Object, Object, Object) (bool, bool, error) {
	p.calls++
	return p.waiting, p.resourcesReady, p.err
}

type permissionFixture struct {
	o       *orchestrationFixture
	r       *runtimeFixture
	svc     *ClientService
	port    *clientPermissionPort
	binding *WorkspaceBinding
	sid     string
	key     string
	request Object
	scope   Object
}

func newPermissionFixture(t *testing.T, authority string, expires time.Time) *permissionFixture {
	t.Helper()
	o := orchestrationSetup(t)
	r := o.claim(o.task("original-permission-action", Empty(), Empty()))
	r.call("/heartbeat", r.heartbeat(), 200)
	f, svc, _, b, sid := clientWorkspaceFixtureFor(t, o.f)
	f.token = o.owner
	r.task = f.read("tasks", Str(r.task, "id"))
	r.run = f.read("runs", Str(r.run, "id"))
	port := &clientPermissionPort{waiting: true, resourcesReady: true}
	svc.SessionRuntime = port
	key := "permission-action-" + ID()
	args := Object{"path": "source.txt", "expected_hash": nil, "content": "approved bytes"}
	payload := Object{"capability": "TOOL", "route": "fixture", "credential_revision": "fixture", "payload": Object{"name": "write", "arguments": args}}
	policy := f.expect(200, "GET", f.path("/goals/"+Str(o.goal, "id")+"/budget-policy"), "", "", nil)
	cost := budgetRequest(r, Str(policy, "id"), "RESERVE", key, Object{"amount": "0", "currency": "USD"}, "UPPER_BOUND", nil)
	if _, err := f.s.PrepareEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key, payload, cost); err != nil {
		t.Fatal(err)
	}
	intent, err := f.s.BeginEffect(context.Background(), o.owner, f.project, Str(r.run, "id"), key)
	if err != nil {
		t.Fatal(err)
	}
	pf := &permissionFixture{o: o, r: r, svc: svc, port: port, binding: b, sid: sid, key: key}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		b.Access = "READ_WRITE"
		b.Revision++
		if err := f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, b.AuthorizedRef, b.record()); err != nil {
			return err
		}
		if _, err := tx.Exec("UPDATE client_sessions SET task_id=?,run_id=?,goal_id=?,model_config_ref='permission-fixture',core_build_id='workspace-fixture' WHERE id=?", r.task["id"], r.run["id"], o.goal["id"], sid); err != nil {
			return err
		}
		p, err := clientPrincipal(context.Background(), tx, f.owner, f.project, true)
		if err != nil {
			return err
		}
		arguments, err := sealPermissionArtifact(f.s, tx, p, f.project, Bytes(args), "FIXTURE")
		if err != nil {
			return err
		}
		pf.scope = Object{"project_id": f.project, "task_id": r.task["id"], "run_id": r.run["id"], "tool_name": "write", "arguments_artifact_ref": Ref(arguments, "Artifact"),
			"workspace_ref": b.AuthorizedRef, "allowed_relative_paths": []any{"source.txt"}, "input_refs": permissionTaskInputs(r.task), "model_config_ref": "permission-fixture",
			"issued_at": time.Now().Add(-time.Minute).UTC().Format(time.RFC3339Nano), "expires_at": expires.UTC().Format(time.RFC3339Nano), "max_uses": 1, "authority": authority}
		scope, err := sealPermissionArtifact(f.s, tx, p, f.project, Bytes(pf.scope), "FIXTURE")
		if err != nil {
			return err
		}
		pf.request, err = f.s.createResourceRequest(tx, p, f.project, Object{"category": "PERMISSION", "account_ref": "fixture-original-tool", "reason_code": "TOOL_PERMISSION_" + key,
			"summary": "Original write awaits an explicit decision", "blocked_task_ids": []any{r.task["id"]}, "continuable_task_ids": Empty(), "completed_artifact_refs": []any{Ref(scope, "Artifact"), Ref(arguments, "Artifact")},
			"requested_capability": "write", "estimated_cost": nil, "cost_known": false, "resume_checkpoint_ref": nil})
		if err != nil {
			return err
		}
		record := Object{"session_id": sid, "request_id": pf.request["id"], "scope_ref": Ref(scope, "Artifact"), "action_digest": Hash(pf.scope), "task_ref": Ref(r.task, "Task"), "binding_revision": b.Revision, "principal_id": f.owner}
		intent["permission"] = record
		if err = effectAppend(tx, f.project, Str(r.run, "id"), key, intent); err != nil {
			return err
		}
		prompt, err := permissionPrompt(svc.Doc, intent, record, pf.scope, pf.request)
		if err != nil {
			return err
		}
		return appendPermissionEvent(context.Background(), tx, svc.Doc, f.project, sid, Str(r.run, "id"), "PERMISSION_REQUIRED", prompt)
	})
	return pf
}

func (p *permissionFixture) envelope(t *testing.T, decision string) *Envelope {
	t.Helper()
	f := p.o.f
	env := workspaceTestEnvelope(f, p.sid, "permission.respond", Object{"resource_request_id": p.request["id"], "resource_request_revision": p.request["revision"], "action_digest": Hash(p.scope), "decision": decision, "reason": "Explicit fixture user choice"})
	var revision int64
	if err := f.db.QueryRow("SELECT revision FROM client_sessions WHERE id=?", p.sid).Scan(&revision); err != nil {
		t.Fatal(err)
	}
	env.ExpectedRevision = &revision
	return env
}

func TestClientPermissionOriginalDecisionAndReplay(t *testing.T) {
	for _, decision := range []string{"ALLOW_ONCE", "DENY"} {
		t.Run(decision, func(t *testing.T) {
			p := newPermissionFixture(t, "USER_DECIDABLE", time.Now().Add(time.Minute))
			f := p.o.f
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				snapshot, err := BuildSessionSnapshot(context.Background(), tx, p.svc.Doc, f.project, p.sid)
				if err != nil {
					return err
				}
				prompts := Arr(snapshot, "pending_permissions")
				if len(prompts) != 1 || prompts[0].(map[string]any)["action_digest"] != Hash(p.scope) {
					t.Fatalf("original prompt absent: %s", Bytes(snapshot))
				}
				return nil
			})
			env := p.envelope(t, decision)
			res, replay := executeWorkspaceTest(t, f, p.svc, env)
			if deref(res.Status) != "COMPLETED" || replay || res.Result["decision"] != decision || res.Result["consumed"] != (decision == "ALLOW_ONCE") || res.Result["resumption_scheduled"] != (decision == "ALLOW_ONCE") {
				t.Fatalf("decision result: %s", Bytes(res))
			}
			before := p.port.calls
			again, replay := executeWorkspaceTest(t, f, p.svc, env)
			if !replay || Hash(res) != Hash(again) || before != p.port.calls {
				t.Fatal("replay revalidated or consumed again")
			}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				intent, record, scope, request, err := loadClientPermission(tx, f.project, p.sid, Str(p.request, "id"))
				if err != nil {
					return err
				}
				if intent["state"] != "STARTED" || request["status"] != "RESOLVED" || record["decision"] != decision || Hash(scope) != Hash(p.scope) {
					t.Fatal("decision changed original effect or lost original scope")
				}
				_, sealedDecision, err := permissionArtifact(tx, f.project, record["decision_artifact_ref"].(map[string]any))
				if err != nil || sealedDecision["decision"] != decision || sealedDecision["effect_key"] != p.key {
					t.Fatalf("missing sealed decision: %v", err)
				}
				var resolutions, events int
				tx.QueryRow("SELECT count(*) FROM resource_resolutions WHERE request=?", p.request["id"]).Scan(&resolutions)
				tx.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='PERMISSION_RESOLVED'", p.sid).Scan(&events)
				if resolutions != 1 || events != 1 {
					t.Fatalf("duplicate decision writes: %d %d", resolutions, events)
				}
				snap, err := BuildSessionSnapshot(context.Background(), tx, p.svc.Doc, f.project, p.sid)
				if err != nil || len(Arr(snap, "pending_permissions")) != 0 {
					t.Fatalf("resolved prompt remains: %v", err)
				}
				return nil
			})
			if decision == "DENY" && f.read("runs", Str(p.r.run, "id"))["status"] != "CANCEL_REQUESTED" {
				t.Fatal("denial did not request original run cancellation")
			}
		})
	}
}

func TestClientPermissionOtherResourcesPreserveOneDecision(t *testing.T) {
	p := newPermissionFixture(t, "USER_DECIDABLE", time.Now().Add(time.Minute))
	f := p.o.f
	p.port.resourcesReady = false
	env := p.envelope(t, "ALLOW_ONCE")
	res, replay := executeWorkspaceTest(t, f, p.svc, env)
	if deref(res.Status) != "COMPLETED" || replay || res.Result["consumed"] != true || res.Result["resumption_scheduled"] != false {
		t.Fatalf("blocked-resource decision was not recorded: %s", Bytes(res))
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		intent, record, _, request, err := loadClientPermission(tx, f.project, p.sid, Str(p.request, "id"))
		if err != nil {
			return err
		}
		if intent["state"] != "STARTED" || record["decision"] != "ALLOW_ONCE" || record["consumed"] != true || request["status"] != "RESOLVED" {
			t.Fatalf("decision lost the pending original effect: %s", Bytes(intent))
		}
		_, decision, err := permissionArtifact(tx, f.project, record["decision_artifact_ref"].(map[string]any))
		if err != nil || decision["decision"] != "ALLOW_ONCE" || decision["effect_key"] != p.key {
			t.Fatalf("one-time decision evidence missing: %v", err)
		}
		snap, err := BuildSessionSnapshot(context.Background(), tx, p.svc.Doc, f.project, p.sid)
		if err != nil || len(Arr(snap, "pending_permissions")) != 0 {
			t.Fatalf("recorded decision still prompts: %v", err)
		}
		return nil
	})
	if f.read("tasks", Str(p.r.task, "id"))["status"] != "RUNNING" || f.read("runs", Str(p.r.run, "id"))["status"] != "RUNNING" {
		t.Fatal("permission resolution changed the running task or run")
	}
	p.port.resourcesReady = true
	calls := p.port.calls
	again, replay := executeWorkspaceTest(t, f, p.svc, env)
	if !replay || Hash(res) != Hash(again) || p.port.calls != calls || again.Result["resumption_scheduled"] != false {
		t.Fatal("resource readiness rewrote or consumed the recorded response again")
	}
	var resolutions, events int
	if err := f.db.QueryRow("SELECT count(*) FROM resource_resolutions WHERE request=?", p.request["id"]).Scan(&resolutions); err != nil {
		t.Fatal(err)
	}
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='PERMISSION_RESOLVED'", p.sid).Scan(&events); err != nil {
		t.Fatal(err)
	}
	if resolutions != 1 || events != 1 {
		t.Fatalf("one decision duplicated its evidence: %d %d", resolutions, events)
	}
}

func TestClientPermissionRefusalsPreserveOriginalAction(t *testing.T) {
	for _, name := range []string{"expired", "policy-denied", "old-request", "wrong-digest", "old-writer", "revoked-workspace", "changed-input", "no-waiter", "runtime-denied", "unknown-effect", "changed-arguments", "closed-request"} {
		t.Run(name, func(t *testing.T) {
			authority, expires := "USER_DECIDABLE", time.Now().Add(time.Minute)
			if name == "expired" {
				expires = time.Now().Add(-time.Second)
			}
			if name == "policy-denied" {
				authority = "POLICY_DENIED"
			}
			p := newPermissionFixture(t, authority, expires)
			f := p.o.f
			env := p.envelope(t, "ALLOW_ONCE")
			body, _ := Decode(env.Payload)
			switch name {
			case "old-request":
				body["resource_request_revision"] = 100
			case "wrong-digest":
				body["action_digest"] = Digest([]byte("different action"))
			case "old-writer":
				env.WriterEpoch = int64ptr(0)
			case "no-waiter":
				p.port.waiting = false
			case "runtime-denied":
				p.port.err = Fail(403, "POLICY_DENIED", "runtime policy is no longer current")
			}
			env.Payload = Bytes(body)
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				switch name {
				case "revoked-workspace":
					p.binding.Status = WorkspaceRevoked
					p.binding.Revision++
					return f.s.putOpaque(context.Background(), tx, "", KindWorkspaceBinding, p.binding.AuthorizedRef, p.binding.record())
				case "changed-input":
					req, err := load(tx, f.project, "Requirement", Str(p.o.req, "id"))
					if err != nil {
						return err
					}
					if err = bump(req); err != nil {
						return err
					}
					return f.s.put(tx, "Requirement", req)
				case "unknown-effect", "changed-arguments":
					intent, err := latestEffect(tx, f.project, Str(p.r.run, "id"), p.key)
					if err != nil {
						return err
					}
					if name == "unknown-effect" {
						intent["state"] = "UNKNOWN"
					} else {
						intent["payload"].(map[string]any)["payload"].(map[string]any)["arguments"] = Object{"path": "different.txt"}
					}
					return effectAppend(tx, f.project, Str(p.r.run, "id"), p.key, intent)
				case "closed-request":
					request, err := load(tx, f.project, "ResourceRequest", Str(p.request, "id"))
					if err != nil {
						return err
					}
					request["status"] = "CANCELLED"
					if err = bump(request); err != nil {
						return err
					}
					return f.s.put(tx, "ResourceRequest", request)
				}
				return nil
			})
			var artifactCount int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact'", f.project).Scan(&artifactCount)
			res, _ := executeWorkspaceTest(t, f, p.svc, env)
			if deref(res.Status) != "REJECTED" {
				t.Fatalf("invalid decision accepted: %s", Bytes(res))
			}
			if name == "policy-denied" && deref(res.ErrorCode) != "POLICY_DENIED" {
				t.Fatalf("policy refusal downgraded: %s", Bytes(res))
			}
			var after, resolutions int
			f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact'", f.project).Scan(&after)
			f.db.QueryRow("SELECT count(*) FROM resource_resolutions WHERE request=?", p.request["id"]).Scan(&resolutions)
			if after != artifactCount || resolutions != 0 {
				t.Fatal("rejected decision left a resolution or artifact")
			}
		})
	}
}
