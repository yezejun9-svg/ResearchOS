//go:build windows

package domain

import (
	"context"
	"database/sql"
	"errors"
	"strings"
	"testing"
	"time"
)

type goalClientPort struct {
	workspace, model string
	resolveErr       error
	admitErr         error
}

func (p goalClientPort) ResolveGoalBinding(context.Context, *sql.Tx, string, string, string) (string, string, error) {
	return p.workspace, p.model, p.resolveErr
}
func (p goalClientPort) ValidateBinding(_ context.Context, _ *sql.Tx, _, _, workspace, model string) error {
	if workspace != p.workspace || model != p.model {
		return Fail(403, "FORBIDDEN", "fixture binding mismatch")
	}
	return nil
}
func (p goalClientPort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return p.admitErr
}

func goalFixture(t *testing.T) (*fixture, *ClientService, string) {
	t.Helper()
	f := contextFixture(t)
	workspace := "goal-workspace-" + ID()
	client := "goal-client"
	b := WorkspaceBinding{AuthorizedRef: workspace, DisplayName: "goal fixture", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: client, HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, workspace, string(Bytes(b))); err != nil {
		t.Fatal(err)
	}
	svc := &ClientService{Doc: clientHistoryDoc(t), Domain: f.s, SessionRuntime: goalClientPort{workspace: workspace, model: "goal-model", admitErr: Fail(503, "RESOURCE_UNAVAILABLE", "fixture runtime unqualified")}, Host: ClientHostInfo{CoreBuildID: "goal-fixture-core", LeaseTTL: time.Minute}}
	return f, svc, client
}

func goalEnvelope(f *fixture, client, text string, draft bool) *Envelope {
	return &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, Method: strptr("goal.start"), Payload: Bytes(Object{"objective": text, "contract_artifact_ids": Empty(), "start_as_draft": draft})}
}

func goalCommand(t *testing.T, f *fixture, svc *ClientService, env *Envelope) (*Response, bool) {
	t.Helper()
	decoded, err := DecodeEnvelope(Bytes(env))
	if err != nil {
		t.Fatal(err)
	}
	var reply *Response
	var replay bool
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		reply, replay, err = svc.Execute(context.Background(), tx, decoded, f.owner)
		return err
	})
	return reply, replay
}

func goalCounts(t *testing.T, f *fixture) (int, int, int, int) {
	t.Helper()
	counts := [4]int{}
	for i, kind := range []string{"Requirement", "Goal", "Task", "Run"} {
		if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?", f.project, kind).Scan(&counts[i]); err != nil {
			t.Fatal(err)
		}
	}
	return counts[0], counts[1], counts[2], counts[3]
}

func TestClientGoalProjectDraftIsRealSessionWithoutTask(t *testing.T) {
	f, svc, client := goalFixture(t)
	env := goalEnvelope(f, client, "保存这个明确目标", true)
	reply, replay := goalCommand(t, f, svc, env)
	if replay || deref(reply.Status) != "COMPLETED" || reply.SessionID != nil {
		t.Fatalf("project-level Goal did not create a typed Goal result: %s", Bytes(reply))
	}
	result := reply.Result
	snap := result["snapshot"].(map[string]any)
	if result["goal_status"] != "DRAFT" || snap["goal_id"] != result["goal_id"] || snap["workspace_ref"] == "" || snap["model_config_ref"] != "goal-model" || snap["native_session_ref"] == "" {
		t.Fatalf("draft result or native session missing: %s", Bytes(reply))
	}
	if _, g, task, run := goalCounts(t, f); g != 1 || task != 0 || run != 0 {
		t.Fatalf("draft dispatched work: goals=%d tasks=%d runs=%d", g, task, run)
	}
	var fake int
	if err := f.db.QueryRow("SELECT count(*) FROM idempotency WHERE operation='v2:session.create'").Scan(&fake); err != nil || fake != 0 {
		t.Fatalf("goal made a fake session.create receipt: %d %v", fake, err)
	}
	repeated, isReplay := goalCommand(t, f, svc, env)
	if !isReplay || Hash(repeated) != Hash(reply) {
		t.Fatalf("same command did not replay exact identity: %s", Bytes(repeated))
	}
	var principal string
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var err error
		principal, err = clientSessionCreationPrincipal(context.Background(), tx, f.project, Str(snap, "session_id"))
		return err
	})
	if principal != f.owner {
		t.Fatalf("goal session creator mismatch: %s", principal)
	}
}

func TestClientGoalNonDraftKeepsFiniteIndependentContractAndBlockedAdmission(t *testing.T) {
	f, svc, client := goalFixture(t)
	reply, _ := goalCommand(t, f, svc, goalEnvelope(f, client, "解释这项用户目标", false))
	if deref(reply.Status) != "COMPLETED" {
		t.Fatalf("goal creation refused: %s", Bytes(reply))
	}
	result := reply.Result
	goal := f.read("goals", Str(result, "goal_id"))
	contract := goal["acceptance_contract"].(map[string]any)
	if goal["status"] != "ACTIVE" || contract["require_independent_verifier"] != true || contract["version_policy"] != "EXACT" || Arr(contract, "checks")[0].(map[string]any)["check_id"] != "mu-turn-output" {
		t.Fatalf("finite contract became business acceptance: %s", Bytes(goal))
	}
	_, _, taskCount, runCount := goalCounts(t, f)
	if taskCount != 1 || runCount != 0 {
		t.Fatalf("blocked qualification pretended to run: tasks=%d runs=%d", taskCount, runCount)
	}
	task := f.read("tasks", Arr(goal, "task_ids")[0].(string))
	progress := f.read("no-progress-records", Str(task, "no_progress_record_id"))
	if task["status"] != "BLOCKED" || progress["candidate_id"] == "" || progress["origin_problem_id"] != Arr(goal, "problem_ids")[0] {
		t.Fatalf("Task lost original Goal or blocked state: %s", Bytes(task))
	}
	second, _ := goalCommand(t, f, svc, goalEnvelope(f, client, "解释这项用户目标", false))
	if deref(second.Status) != "REJECTED" {
		t.Fatalf("new command reset same Goal budget: %s", Bytes(second))
	}
	if _, goals, tasks, runs := goalCounts(t, f); goals != 1 || tasks != 1 || runs != 0 {
		t.Fatalf("duplicate Goal committed state: %d %d %d", goals, tasks, runs)
	}
}

func TestClientGoalResolverFailureAndChangedReplayAreAtomic(t *testing.T) {
	f, svc, client := goalFixture(t)
	port := svc.SessionRuntime.(goalClientPort)
	port.resolveErr = Fail(503, "RESOURCE_BLOCKED", "ambiguous binding")
	svc.SessionRuntime = port
	env := goalEnvelope(f, client, "不能猜绑定", false)
	reply, _ := goalCommand(t, f, svc, env)
	if deref(reply.Status) != "REJECTED" {
		t.Fatalf("missing binding accepted: %s", Bytes(reply))
	}
	if req, goals, tasks, runs := goalCounts(t, f); req != 0 || goals != 0 || tasks != 0 || runs != 0 {
		t.Fatalf("typed refusal persisted business data: %d %d %d %d", req, goals, tasks, runs)
	}
	var sessions int
	if err := f.db.QueryRow("SELECT count(*) FROM client_sessions").Scan(&sessions); err != nil || sessions != 0 {
		t.Fatalf("typed refusal persisted session: %d %v", sessions, err)
	}
	changed := *env
	changed.Payload = Bytes(Object{"objective": "别的目标", "contract_artifact_ids": Empty(), "start_as_draft": false})
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	decoded, decodeErr := DecodeEnvelope(Bytes(&changed))
	if decodeErr != nil {
		t.Fatal(decodeErr)
	}
	_, _, err = svc.Execute(context.Background(), tx, decoded, f.owner)
	tx.Rollback()
	if !errors.Is(err, ErrIdemConflict) {
		t.Fatalf("changed command id replay should conflict, got %v", err)
	}
}

func goalContract(checkID string) Object {
	c := clientTurnContract()
	check := Object{"check_id": checkID, "kind": "DETERMINISTIC", "required": true,
		"expected": "Exact independent fixture check", "command_key": "fixture." + checkID,
		"rubric_ref": nil, "qualification_id": nil, "not_applicable_reason": nil}
	c["checks"] = []any{check}
	c["contract_hash"] = contractDigest(c)
	return c
}

func goalWithContracts(f *fixture, client, objective string, refs ...string) *Envelope {
	env := goalEnvelope(f, client, objective, true)
	items := Empty()
	for _, ref := range refs {
		items = append(items, ref)
	}
	env.Payload = Bytes(Object{"objective": objective, "contract_artifact_ids": items, "start_as_draft": true})
	return env
}

func TestClientGoalContractArtifactsMergeEveryMandatoryCheck(t *testing.T) {
	f, svc, client := goalFixture(t)
	a := f.artifact(goalContract("goal-a"), Empty())
	b := f.artifact(goalContract("goal-b"), Empty())
	reply, _ := goalCommand(t, f, svc, goalWithContracts(f, client, "审核这两个合同", Str(a, "id"), Str(b, "id")))
	if deref(reply.Status) != "COMPLETED" {
		t.Fatalf("valid contract merge refused: %s", Bytes(reply))
	}
	goal := f.read("goals", Str(reply.Result, "goal_id"))
	checks := Arr(goal["acceptance_contract"].(map[string]any), "checks")
	if len(checks) != 3 || Str(checks[0].(map[string]any), "check_id") != "mu-turn-output" || Str(checks[1].(map[string]any), "check_id") != "goal-a" || Str(checks[2].(map[string]any), "check_id") != "goal-b" {
		t.Fatalf("merged checks silently dropped a requirement: %s", Bytes(checks))
	}
	req := f.read("requirements", Str(goal["requirement_refs"].([]any)[0].(map[string]any), "id"))
	if len(Arr(req, "source_refs")) != 2 {
		t.Fatalf("contract source provenance absent: %s", Bytes(req))
	}
}

func TestClientGoalContractArtifactRefusalsAreAtomic(t *testing.T) {
	for _, name := range []string{"wrong_project", "protected", "stale", "unsealed", "hash_tampered", "invalid_contract", "conflicting_check"} {
		t.Run(name, func(t *testing.T) {
			f, svc, client := goalFixture(t)
			artifact := f.artifact(goalContract("goal-a"), Empty())
			refs := []string{Str(artifact, "id")}
			switch name {
			case "wrong_project":
				original := f.project
				f.createProject()
				foreign := f.artifact(goalContract("goal-foreign"), Empty())
				f.project = original
				refs = []string{Str(foreign, "id")}
			case "protected", "stale":
				if name == "protected" {
					copy, err := Decode(Bytes(artifact))
					if err != nil {
						t.Fatal(err)
					}
					copy["id"], copy["access_class"], copy["content_hash"] = ID(), "VERIFIER_ONLY", Digest([]byte("protected fixture metadata"))
					sourceTx(t, f.db, func(tx *sql.Tx) error { return f.s.put(tx, "Artifact", copy) })
					refs = []string{Str(copy, "id")}
				} else if _, err := f.db.Exec("UPDATE domain_objects SET body=json_set(body,'$.validity','STALE') WHERE project=? AND kind='Artifact' AND id=?", f.project, artifact["id"]); err != nil {
					t.Fatal(err)
				}
			case "unsealed":
				if _, err := f.db.Exec("UPDATE uploaded_content SET sealed=0 WHERE project=? AND storage_key=?", f.project, artifact["storage_key"]); err != nil {
					t.Fatal(err)
				}
			case "hash_tampered":
				copy, err := Decode(Bytes(artifact))
				if err != nil {
					t.Fatal(err)
				}
				copy["id"], copy["content_hash"] = ID(), Digest([]byte("tampered"))
				sourceTx(t, f.db, func(tx *sql.Tx) error { return f.s.put(tx, "Artifact", copy) })
				refs = []string{Str(copy, "id")}
			case "invalid_contract":
				bad := f.artifact(Object{"not": "an AcceptanceContract"}, Empty())
				refs = []string{Str(bad, "id")}
			case "conflicting_check":
				left := goalContract("same-check")
				right := goalContract("same-check")
				rightCheck := Arr(right, "checks")[0].(map[string]any)
				rightCheck["expected"] = "Different expected result"
				right["contract_hash"] = contractDigest(right)
				first := f.artifact(left, Empty())
				second := f.artifact(right, Empty())
				refs = []string{Str(first, "id"), Str(second, "id")}
			}
			reply, _ := goalCommand(t, f, svc, goalWithContracts(f, client, "合同不应越权", refs...))
			if deref(reply.Status) != "REJECTED" {
				t.Fatalf("%s was accepted: %s", name, Bytes(reply))
			}
			if _, goals, tasks, runs := goalCounts(t, f); goals != 0 || tasks != 0 || runs != 0 {
				t.Fatalf("%s wrote business Goal/Task: %d %d %d", name, goals, tasks, runs)
			}
			var sessions int
			if err := f.db.QueryRow("SELECT count(*) FROM client_sessions").Scan(&sessions); err != nil || sessions != 0 {
				t.Fatalf("%s left session after refusal: %d %v", name, sessions, err)
			}
		})
	}
}

func TestClientGoalSessionWriterAndSettlementGates(t *testing.T) {
	f, svc, client := goalFixture(t)
	created, _ := goalCommand(t, f, svc, goalEnvelope(f, client, "first bounded Goal", false))
	sid := Str(created.Result["snapshot"].(map[string]any), "session_id")
	base := goalEnvelope(f, client, "second bounded Goal", true)
	base.SessionID, base.ExpectedRevision, base.WriterEpoch = &sid, revPtr(*created.Revision), revPtr(1)
	for _, name := range []string{"stale_revision", "stale_epoch", "foreign_client", "expired_lease", "unsettled_task", "archived"} {
		t.Run(name, func(t *testing.T) {
			env := *base
			id := ID()
			env.CommandID = &id
			switch name {
			case "stale_revision":
				env.ExpectedRevision = revPtr(1)
			case "stale_epoch":
				env.WriterEpoch = revPtr(2)
			case "foreign_client":
				other := "other-client"
				env.ClientID = &other
			case "expired_lease":
				f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(-time.Hour).UTC().Format(time.RFC3339Nano), sid)
			case "archived":
				f.db.Exec("UPDATE client_sessions SET archived_at=? WHERE id=?", Now(), sid)
			}
			reply, _ := goalCommand(t, f, svc, &env)
			if deref(reply.Status) != "REJECTED" {
				t.Fatalf("%s bypassed writer/settlement gate: %s", name, Bytes(reply))
			}
			if _, goals, tasks, runs := goalCounts(t, f); goals != 1 || tasks != 1 || runs != 0 {
				t.Fatalf("%s changed business rows: %d %d %d", name, goals, tasks, runs)
			}
			if name == "expired_lease" {
				f.db.Exec("UPDATE client_sessions SET lease_expires_at=? WHERE id=?", time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano), sid)
			}
			if name == "archived" {
				f.db.Exec("UPDATE client_sessions SET archived_at=NULL WHERE id=?", sid)
			}
		})
	}
	if !strings.Contains(Str(created.Result["snapshot"].(map[string]any), "workspace_ref"), "goal-workspace") {
		t.Fatal("first Goal snapshot lost selected workspace")
	}
}
