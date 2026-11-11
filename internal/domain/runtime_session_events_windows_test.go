//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/base64"
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

// These lower-level cases use explicitly constructed journal observations on
// a real fixture Run/dispatch. They assert projection, never LIVE execution.
func runtimeEventFixture(t *testing.T) (*RuntimeCoordinator, *runtimeFixture, string, Object) {
	t.Helper()
	c, _, r := coordinatorFixture(t)
	doc, sid := sessionProjectionMapping(t, r.f, r.task)
	c.config.ClientSchema = doc
	var intent Object
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		goal, err := load(tx, r.f.project, "Goal", Str(r.task, "goal_id"))
		if err != nil {
			return err
		}
		key := ID()
		ledger, err := c.service.appendBudget(tx, r.f.project, Object{"policy_id": goal["budget_policy_id"], "run_id": r.run["id"], "operation": "RESERVE", "money": dollars("0"), "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UPPER_BOUND", "occurred_at": Now()})
		if err != nil {
			return err
		}
		intent = Object{"project_id": r.f.project, "run_id": r.run["id"], "task_id": r.task["id"], "key": key, "epoch": r.run["lease_epoch"], "state": "STARTED", "request_hash": Hash("explicit journal fixture"), "reservation_id": ledger["id"], "receipt": nil, "payload": Object{"capability": "TOOL", "payload": Object{"name": "run_check", "arguments": Object{"command": "fixture"}}}}
		return effectAppend(tx, r.f.project, Str(r.run, "id"), key, intent)
	})
	return c, r, sid, intent
}

func runtimeEventRows(t *testing.T, r *runtimeFixture, sid, kind string) []Object {
	t.Helper()
	rows, err := r.f.db.Query("SELECT body FROM outbox WHERE project=? AND json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')=? ORDER BY json_extract(body,'$.sequence')", r.f.project, sid, kind)
	if err != nil {
		t.Fatal(err)
	}
	defer rows.Close()
	result := []Object{}
	for rows.Next() {
		var raw string
		if err = rows.Scan(&raw); err != nil {
			t.Fatal(err)
		}
		ev, e := Decode([]byte(raw))
		if e != nil {
			t.Fatal(e)
		}
		result = append(result, ev)
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	return result
}

func runtimeEventProject(t *testing.T, c *RuntimeCoordinator, r *runtimeFixture, fact Object) {
	t.Helper()
	sourceTx(t, r.f.db, func(tx *sql.Tx) error { return c.projectSessionEffects(tx, r.f.project, r.run, fact) })
}

func runtimeEventFact(t *testing.T, c *RuntimeCoordinator, r *runtimeFixture, intent Object, result Object, evidence Object) Object {
	t.Helper()
	var dispatch Object
	sourceTx(t, r.f.db, func(tx *sql.Tx) (err error) {
		dispatch, err = runtimeDispatch(tx, r.f.project, Str(r.run, "id"), intent["epoch"])
		return
	})
	receipt := Object{"key": intent["key"], "run_id": r.run["id"], "epoch": intent["epoch"], "receipt_id": Digest(Bytes(result)), "state": "CONFIRMED", "host_tool": "run_check", "actual_cost": dollars("0"), "payload": result}
	fact := Object{"project_id": r.f.project, "run_id": r.run["id"], "effect_key": intent["key"], "epoch": intent["epoch"], "request_hash": intent["request_hash"], "reservation_id": intent["reservation_id"], "dispatch_key": dispatch["dispatch_key"], "manifest_hash": dispatch["manifest_hash"], "provider_response_hash": receipt["receipt_id"], "receipt": receipt}
	if evidence != nil {
		fact["host_tool_evidence"], fact["host_tool_evidence_hash"] = evidence, Hash(evidence)
	}
	// The lower-level fixture supplies the actual immutable host-journal file
	// used by scan recovery, rather than relying on a callback-only object.
	locator := Str(dispatch, "dispatch_key")
	if _, err := r.f.db.Exec("UPDATE runtime_dispatches SET journal_locator=? WHERE project=? AND run=? AND epoch=?", locator, r.f.project, r.run["id"], intent["epoch"]); err != nil {
		t.Fatal(err)
	}
	directory := filepath.Join(c.config.DataRoot, "runtime-dispatches", locator)
	if err := os.MkdirAll(directory, 0700); err != nil {
		t.Fatal(err)
	}
	if err := writeRuntimeFact(filepath.Join(directory, "effect-"+strings.TrimPrefix(Digest([]byte(Str(intent, "key"))), "sha256:")+".json"), Bytes(fact)); err != nil {
		t.Fatal(err)
	}
	return fact
}

func runtimeArtifactBytes(t *testing.T, r *runtimeFixture, value any) []byte {
	t.Helper()
	ref, ok := value.(map[string]any)
	if !ok {
		t.Fatalf("missing real artifact ref: %v", value)
	}
	var a Object
	sourceTx(t, r.f.db, func(tx *sql.Tx) (err error) { a, err = version(tx, r.f.project, ref); return })
	var raw []byte
	err := r.f.db.QueryRow("SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1", r.f.project, a["storage_key"]).Scan(&raw)
	if err != nil {
		t.Fatal(err)
	}
	if Digest(raw) != a["content_hash"] || Hash(len(raw)) != Hash(a["byte_size"]) || a["measurement_mode"] != "FIXTURE" {
		t.Fatal("artifact bytes/provenance mismatch")
	}
	return raw
}

func TestW05RuntimeEventJournalReplayRawAndUnknownCost(t *testing.T) {
	c, r, sid, intent := runtimeEventFixture(t)
	runtimeEventProject(t, c, r, nil)
	start := runtimeEventRows(t, r, sid, "TOOL_STARTED")
	if len(start) != 1 || start[0]["payload"].(map[string]any)["parent_tool_call_id"] != nil {
		t.Fatal("logical STARTED missing or invented parent")
	}
	input := start[0]["payload"].(map[string]any)["input_artifact_ref"]
	if Hash(string(runtimeArtifactBytes(t, r, input))) != Hash(string(Bytes(intent["payload"].(map[string]any)["payload"]))) {
		t.Fatal("actual tool input lost")
	}
	usage := runtimeEventRows(t, r, sid, "USAGE")
	initialUsage := len(usage)
	if initialUsage == 0 {
		t.Fatal("missing reservation usage")
	}
	for _, ev := range usage {
		p := ev["payload"].(map[string]any)
		if p["money"] != nil || p["cost_known"] != false {
			t.Fatalf("upper bound became actual: %s", Bytes(ev))
		}
	}
	// A crash observation remains UNKNOWN even if the Run later cancels.
	if err := c.service.ObserveEffect(context.Background(), r.f.project, Str(r.run, "id"), Str(intent, "key"), "UNKNOWN", Object{"reason": "fixture crash"}); err != nil {
		t.Fatal(err)
	}
	runtimeEventProject(t, c, r, nil)
	unknown := runtimeEventRows(t, r, sid, "TOOL_RESULT")
	if len(unknown) != 1 || unknown[0]["payload"].(map[string]any)["outcome"] != "UNKNOWN" {
		t.Fatal("unknown inferred as tool success/cancel")
	}
	stdout, stderr := []byte(strings.Repeat("long stdout\n", 20000)), []byte{0, 0xff, 'e', 'r', 'r'}
	evidence := Object{"sandbox_receipt": Object{"stdout_raw": stdout, "stdout_hash": Digest(stdout), "stdout_raw_bytes": len(stdout), "stderr_raw": stderr, "stderr_hash": Digest(stderr), "stderr_raw_bytes": len(stderr)}}
	fact := runtimeEventFact(t, c, r, intent, Object{"content": Empty(), "details": Object{"exit_code": 7, "timed_out": false}}, evidence)
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal(err)
	}
	results := runtimeEventRows(t, r, sid, "TOOL_RESULT")
	if len(results) != 2 {
		t.Fatalf("lost original UNKNOWN or new complete result: %d", len(results))
	}
	p := results[1]["payload"].(map[string]any)
	if p["outcome"] != "FAILED" || p["tool_call_id"] != start[0]["payload"].(map[string]any)["tool_call_id"] {
		t.Fatal("nonzero exit or logical identity lost")
	}
	if string(runtimeArtifactBytes(t, r, p["stdout_artifact_ref"])) != string(stdout) || string(runtimeArtifactBytes(t, r, p["stderr_artifact_ref"])) != string(stderr) {
		t.Fatal("raw stream was truncated or altered")
	}
	usage = runtimeEventRows(t, r, sid, "USAGE")
	if len(usage) != initialUsage+1 || usage[initialUsage]["payload"].(map[string]any)["cost_known"] != true || Hash(usage[initialUsage]["payload"].(map[string]any)["money"]) != Hash(dollars("0")) {
		t.Fatal("explicit actual tool zero not represented")
	}
	var before, after int64
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&before); err != nil {
		t.Fatal(err)
	}
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal(err)
	}
	runtimeEventProject(t, c, r, fact)
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&after); err != nil || after != before {
		t.Fatal("same fact replay changed event watermark")
	}
	for name, mutate := range map[string]func(Object){
		"wrong run": func(f Object) { f["run_id"] = ID() }, "wrong epoch": func(f Object) { f["epoch"] = 99 }, "wrong response": func(f Object) { f["provider_response_hash"] = Hash("wrong") }, "wrong evidence": func(f Object) { f["host_tool_evidence_hash"] = Hash("wrong") }, "wrong reservation": func(f Object) { f["reservation_id"] = ID() },
	} {
		t.Run(name, func(t *testing.T) {
			copy, _ := Decode(Bytes(fact))
			mutate(copy)
			if c.ingestEffectFact(context.Background(), copy) == nil {
				t.Fatal("tampered receipt accepted")
			}
		})
	}
	// A raw hash error rolls back the ledger and effect receipt, including the
	// duplicate-receipt repair path. It cannot create a fake empty output.
	bad, _ := Decode(Bytes(fact))
	sandbox := bad["host_tool_evidence"].(map[string]any)["sandbox_receipt"].(map[string]any)
	sandbox["stdout_raw"] = base64.StdEncoding.EncodeToString([]byte("wrong"))
	bad["host_tool_evidence_hash"] = Hash(bad["host_tool_evidence"])
	if c.ingestEffectFact(context.Background(), bad) == nil {
		t.Fatal("wrong raw witness accepted")
	}
	if len(runtimeEventRows(t, r, sid, "TOOL_RESULT")) != 2 {
		t.Fatal("failed repair leaked event")
	}
}

func TestW05RuntimeEventHistoricalWriterAndSealedBilling(t *testing.T) {
	c, r, sid, intent := runtimeEventFixture(t)
	sourceTx(t, r.f.db, func(tx *sql.Tx) error { return c.projectSessionRun(tx, r.f.project, r.run, nil) })
	// Preserve the actual original RUN_STATE association after a next turn and
	// writer handoff; neither the old effect epoch nor fixture lease is renewed.
	if _, err := r.f.db.Exec("UPDATE client_sessions SET task_id=NULL,goal_id=NULL,writer_epoch=writer_epoch+1,revision=revision+1 WHERE id=?", sid); err != nil {
		t.Fatal(err)
	}
	fact := runtimeEventFact(t, c, r, intent, Object{"content": Empty(), "details": Object{"exit_code": 0}}, nil)
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal(err)
	}
	if len(runtimeEventRows(t, r, sid, "TOOL_RESULT")) != 1 {
		t.Fatal("late original result lost after handoff")
	}
	beforeLateUsage := len(runtimeEventRows(t, r, sid, "USAGE"))
	var runEpoch any
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		current, err := load(tx, r.f.project, "Run", Str(r.run, "id"))
		if err == nil {
			runEpoch = current["lease_epoch"]
		}
		return err
	})
	if Hash(runEpoch) != Hash(intent["epoch"]) {
		t.Fatal("projection renewed execution epoch")
	}
	// Late immutable billing on an old Run is repaired through its provenance,
	// independently of the current session Task.
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		goal, err := load(tx, r.f.project, "Goal", Str(r.task, "goal_id"))
		if err != nil {
			return err
		}
		key := ID()
		_, err = c.service.appendBudget(tx, r.f.project, Object{"policy_id": goal["budget_policy_id"], "run_id": r.run["id"], "operation": "UNKNOWN", "money": nil, "provider_request_id": key, "provider_event_id": "prepare/" + key, "reservation_id": nil, "cost_basis": "UNKNOWN", "occurred_at": Now()})
		return err
	})
	if err := c.projectCurrentSessionRuns(context.Background()); err != nil {
		t.Fatal(err)
	}
	if len(runtimeEventRows(t, r, sid, "USAGE")) != beforeLateUsage+1 {
		t.Fatal("historical usage not repaired")
	}
	var before, after int64
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&before); err != nil {
		t.Fatal(err)
	}
	if _, err := r.f.db.Exec("UPDATE client_sessions SET sealed_at=? WHERE id=?", Now(), sid); err != nil {
		t.Fatal(err)
	}
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal("sealed session prevented billing replay:", err)
	}
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&after); err != nil || before != after {
		t.Fatal("sealed session emitted new events")
	}
}

func TestW05RuntimeEventOutcomeWitness(t *testing.T) {
	for _, test := range []struct {
		name, state string
		result      Object
		want        string
	}{
		{"failed check", "CONFIRMED", Object{"details": Object{"exit_code": 1}}, "FAILED"},
		{"timeout", "CONFIRMED", Object{"details": Object{"exit_code": 0, "timed_out": true}}, "FAILED"},
		{"explicit error", "CONFIRMED", Object{"isError": true}, "FAILED"},
		{"refusal", "NOT_APPLIED", Object{"reason": "before IO"}, "BLOCKED"},
		{"unconfirmed cancel", "UNKNOWN", Object{}, "UNKNOWN"},
		{"complete", "CONFIRMED", Object{"details": Object{"exit_code": 0}}, "SUCCEEDED"},
	} {
		t.Run(test.name, func(t *testing.T) {
			got, _ := runtimeToolOutcome(Object{"state": test.state, "receipt": Object{"payload": test.result}})
			if got != test.want {
				t.Fatalf("%s != %s", got, test.want)
			}
		})
	}
}

func TestW05RuntimeEventSealedSessionStillReconcilesOriginalCost(t *testing.T) {
	c, r, sid, intent := runtimeEventFixture(t)
	runtimeEventProject(t, c, r, nil)
	var before, after int64
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&before); err != nil {
		t.Fatal(err)
	}
	if _, err := r.f.db.Exec("UPDATE client_sessions SET sealed_at=? WHERE id=?", Now(), sid); err != nil {
		t.Fatal(err)
	}
	fact := runtimeEventFact(t, c, r, intent, Object{"content": Empty(), "details": Object{"exit_code": 0}}, nil)
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal(err)
	}
	var count int
	if err := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? AND json_extract(body,'$.operation')='RECONCILE' AND json_extract(body,'$.reservation_id')=?", r.f.project, r.run["id"], intent["reservation_id"]).Scan(&count); err != nil || count != 1 {
		t.Fatal("sealed session lost original billing", err)
	}
	if err := r.f.db.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&after); err != nil || before != after {
		t.Fatal("sealed session watermark changed")
	}
	if err := c.projectCurrentSessionRuns(context.Background()); err != nil {
		t.Fatal("sealed current session stopped coordinator projection:", err)
	}
	sourceTx(t, r.f.db, func(tx *sql.Tx) error { return c.projectSessionRun(tx, r.f.project, r.run, nil) })
}

func TestW05RuntimeEventDiskWitnessAndAmbiguousProvenance(t *testing.T) {
	c, r, sid, intent := runtimeEventFixture(t)
	fact := runtimeEventFact(t, c, r, intent, Object{"content": Empty(), "details": Object{"exit_code": 0}}, nil)
	if err := c.ingestEffectFact(context.Background(), fact); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(c.config.DataRoot, "runtime-dispatches", Str(fact, "dispatch_key"), "effect-"+strings.TrimPrefix(Digest([]byte(Str(intent, "key"))), "sha256:")+".json")
	bad, _ := Decode(Bytes(fact))
	bad["provider_response_hash"] = Hash("corrupt disk witness")
	if err := os.WriteFile(path, Bytes(bad), 0600); err != nil {
		t.Fatal(err)
	}
	tx, err := r.f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = c.projectSessionEffects(tx, r.f.project, r.run, nil)
	tx.Rollback()
	if err == nil {
		t.Fatal("corrupt disk response witness accepted")
	}
	if err = os.WriteFile(path, Bytes(fact), 0600); err != nil {
		t.Fatal(err)
	}
	bad, _ = Decode(Bytes(fact))
	bad["host_tool_evidence"] = Object{"sandbox_receipt": Object{"stdout_raw": "invalid base64 !", "stdout_raw_bytes": 0, "stdout_hash": Digest(nil)}}
	bad["host_tool_evidence_hash"] = Hash(bad["host_tool_evidence"])
	if c.ingestEffectFact(context.Background(), bad) == nil {
		t.Fatal("malformed encoded raw output accepted")
	}
	if len(runtimeEventRows(t, r, sid, "TOOL_RESULT")) != 1 {
		t.Fatal("bad evidence repair leaked an event")
	}
	other := mixedSessionEvents(t, r.f, 0)
	if _, err = r.f.db.Exec("UPDATE client_sessions SET task_id=? WHERE id=?", r.task["id"], other); err != nil {
		t.Fatal(err)
	}
	tx, err = r.f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = c.projectSessionEffects(tx, r.f.project, r.run, fact)
	tx.Rollback()
	if err == nil {
		t.Fatal("ambiguous session provenance selected an arbitrary target")
	}
}

func TestW05RuntimeEventReportRecoveryHasOriginalUsage(t *testing.T) {
	c, _, r, _ := nativeNormalFixture(t, false)
	if err := c.Scan(context.Background()); err != nil {
		t.Fatal(err)
	}
	c.workers.Wait()
	select {
	case err := <-c.errors:
		t.Fatal(err)
	default:
	}
	task := r.f.read("tasks", Str(r.task, "id"))
	if task["status"] != "EXECUTION_REPORTED" {
		t.Fatal("real native fixture did not report")
	}
	r.run = r.f.read("runs", Str(task, "active_run_id"))
	doc, sid := sessionProjectionMapping(t, r.f, task)
	c.config.ClientSchema = doc
	for i := 0; i < 2; i++ {
		if err := c.Recover(context.Background()); err != nil {
			t.Fatal(err)
		}
	}
	usage := runtimeEventRows(t, r, sid, "USAGE")
	if len(usage) != 1 || len(runtimeEventRows(t, r, sid, "RUN_STATE")) != 1 || len(runtimeEventRows(t, r, sid, "ARTIFACT")) != 1 {
		t.Fatal("expected original state, artifact and one usage")
	}
	p := usage[0]["payload"].(map[string]any)
	var ledger Object
	sourceTx(t, r.f.db, func(tx *sql.Tx) (err error) {
		ledger, err = load(tx, r.f.project, "BudgetLedgerEntry", Str(p, "ledger_entry_id"))
		return
	})
	known := ledger["cost_basis"] == "ACTUAL" && (ledger["operation"] == "COMMIT" || ledger["operation"] == "RECONCILE") && ledger["money"] != nil
	if ledger["run_id"] != r.run["id"] || p["cost_known"] != known || (known && Hash(p["money"]) != Hash(ledger["money"])) || (!known && p["money"] != nil) {
		t.Fatal("projected usage does not describe its original ledger")
	}
	t.Logf("RECOVERY_CANONICAL_USAGE mode=FIXTURE journal=%s ledger=%s", Bytes(usage[0]), Bytes(ledger))
}

// Real SDK, real broker and typed session, with explicit loopback model and
// host-tool FIXTURE ports. Observe committed STARTED from a separate DB query
// at the actual RunTool call, and force an event write failure in the other case.
func TestW05RuntimeEventBrokerBeforeIOAndRollback(t *testing.T) {
	for _, rollback := range []bool{false, true} {
		t.Run(fmt.Sprintf("rollback=%v", rollback), func(t *testing.T) {
			var modelCalls, physical atomic.Int32
			c, route, r, _ := muBrokerFixtureProgram(t, func(w http.ResponseWriter, req *http.Request) {
				n := modelCalls.Add(1)
				var body Object
				if json.NewDecoder(req.Body).Decode(&body) != nil {
					t.Error("invalid SDK body")
					return
				}
				delta, finish := Object{"role": "assistant", "content": "complete"}, "stop"
				if n == 2 {
					delta = Object{"role": "assistant", "tool_calls": []any{Object{"index": 0, "id": "call-read", "type": "function", "function": Object{"name": "read", "arguments": "{\"path\":\"evidence.txt\"}"}}}}
					finish = "tool_calls"
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
			c.config.WorkspaceAuthority = muWorkspaceFixture{workspace}
			c.config.ClientSchema = clientHistoryDoc(t)
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
			binding := WorkspaceBinding{AuthorizedRef: "event-workspace", DisplayName: "fixture", DisplayPath: workspace, RealPath: workspace, Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "event-client", HostPrincipalRef: "fixture-user", CreatedAt: Now()}
			if _, err = f.db.Exec("INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)", KindWorkspaceBinding, binding.AuthorizedRef, string(Bytes(binding))); err != nil {
				t.Fatal(err)
			}
			svc := &ClientService{Doc: c.config.ClientSchema, Domain: f.s, SessionRuntime: c, Host: ClientHostInfo{CoreBuildID: "event-fixture", LeaseTTL: time.Minute}}
			created := muClientCall(t, f, svc, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("event-client"), ProjectID: &f.project, Method: strptr("session.create"), Payload: Bytes(Object{"workspace_ref": binding.AuthorizedRef, "model_config_ref": modelRoute.ModelConfig["ref"], "title": "events"})})
			sid := deref(created.SessionID)
			if rollback {
				if _, err = f.db.Exec("CREATE TRIGGER reject_fixture_start BEFORE INSERT ON outbox WHEN json_extract(NEW.body,'$.kind')='TOOL_STARTED' BEGIN SELECT RAISE(ABORT,'fixture tool event failure'); END"); err != nil {
					t.Fatal(err)
				}
			}
			c.config.RunTool = func(_ context.Context, req RuntimeToolRequest) (Object, error) {
				physical.Add(1)
				starts := runtimeEventRows(t, r, sid, "TOOL_STARTED")
				results := runtimeEventRows(t, r, sid, "TOOL_RESULT")
				if len(starts) != 1 || len(results) != 0 {
					t.Error("physical tool entered without committed logical start")
				}
				if req.Name != "read" || req.WorkspacePath != workspace {
					return nil, fmt.Errorf("wrong real tool binding")
				}
				return Object{"content": []any{Object{"type": "text", "text": "fixture file"}}, "details": Object{}}, nil
			}
			muClientCall(t, f, svc, &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("event-client"), ProjectID: &f.project, SessionID: created.SessionID, Method: strptr("session.send"), ExpectedRevision: revPtr(1), WriterEpoch: revPtr(1), Payload: Bytes(Object{"text": "read evidence.txt", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})})
			if err = c.Scan(context.Background()); err != nil {
				t.Fatal(err)
			}
			c.workers.Wait()
			if rollback {
				if physical.Load() != 0 || len(runtimeEventRows(t, r, sid, "TOOL_STARTED")) != 0 {
					t.Fatal("failed event transaction dispatched tool")
				}
				var started int
				if err = f.db.QueryRow("SELECT count(*) FROM resource_effects WHERE json_extract(body,'$.payload.capability')='TOOL' AND json_extract(body,'$.state')='STARTED'").Scan(&started); err != nil || started != 0 {
					t.Fatal("event rollback retained STARTED effect")
				}
			} else {
				select {
				case err = <-c.errors:
					t.Fatal(err)
				default:
				}
				if physical.Load() != 1 || len(runtimeEventRows(t, r, sid, "TOOL_RESULT")) != 1 {
					t.Fatal("actual broker result absent or tool repeated")
				}
				if err = c.projectCurrentSessionRuns(context.Background()); err != nil {
					t.Fatal(err)
				}
				if len(runtimeEventRows(t, r, sid, "TOOL_STARTED")) != 1 || len(runtimeEventRows(t, r, sid, "TOOL_RESULT")) != 1 {
					t.Fatal("scan repeated tool projection")
				}
			}
		})
	}
}
