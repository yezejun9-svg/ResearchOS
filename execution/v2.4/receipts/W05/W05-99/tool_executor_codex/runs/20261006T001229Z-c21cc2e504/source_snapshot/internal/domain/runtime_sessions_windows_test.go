//go:build windows

package domain

import (
	"context"
	"database/sql"
	"os"
	"testing"
	"time"
)

type nextTurnFixturePort struct{}

func (nextTurnFixturePort) ValidateBinding(context.Context, *sql.Tx, string, string, string, string) error {
	return nil
}
func (nextTurnFixturePort) AdmitTurn(context.Context, *sql.Tx, string, string, Object) error {
	return Fail(503, "RESOURCE_UNAVAILABLE", "next turn runtime remains an explicit fixture block")
}

func nextSessionTurn(t *testing.T, f *fixture, doc *SchemaDoc, sid, want string) {
	t.Helper()
	workspace := "projection-workspace"
	b := WorkspaceBinding{AuthorizedRef: workspace, DisplayName: "projection", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "mixed-client", HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err := f.db.Exec(`INSERT OR REPLACE INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, workspace, string(Bytes(b))); err != nil {
		t.Fatal(err)
	}
	if _, err := f.db.Exec("UPDATE client_sessions SET workspace_ref=?,model_config_ref='fixture-model',title='fixture',lease_expires_at=? WHERE id=?", workspace, time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		sess, err := loadClientSession(context.Background(), tx, sid, f.project)
		if err != nil {
			return err
		}
		svc := ClientService{Doc: doc, Domain: f.s, SessionRuntime: nextTurnFixturePort{}, Host: ClientHostInfo{CoreBuildID: "fixture-build"}}
		env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), Method: strptr("session.send"), ProjectID: &f.project, SessionID: &sid, Payload: Bytes(Object{"text": "下一条独立消息", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
		reply, err := svc.sendClientMessage(context.Background(), tx, env, f.owner, sess)
		if err != nil {
			return err
		}
		if want == "SESSION_BUSY" {
			if reply.ErrorCode == nil || *reply.ErrorCode != want {
				t.Fatalf("premature next turn: %+v", reply)
			}
		} else if reply.Status == nil || *reply.Status != "COMPLETED" {
			t.Fatalf("settled turn blocked next finite Task: %+v", reply)
		}
		return nil
	})
}

func sessionProjectionMapping(t *testing.T, f *fixture, task Object) (*SchemaDoc, string) {
	t.Helper()
	sid := mixedSessionEvents(t, f, 0)
	raw, err := os.ReadFile("../api/contracts/client.protocol.schema.json")
	if err != nil {
		t.Fatal(err)
	}
	external, err := os.ReadFile("../api/contracts/domain.schema.json")
	if err != nil {
		t.Fatal(err)
	}
	doc, err := LoadSchemaWithExternals(raw, map[string][]byte{"domain.schema.json": external})
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.db.Exec("UPDATE client_sessions SET task_id=?,goal_id=?,core_build_id='fixture-build' WHERE id=?", task["id"], task["goal_id"], sid); err != nil {
		t.Fatal(err)
	}
	// Only the mapping/type is a fixture: the underlying Run has already passed
	// the real report HTTP transaction and retains its independent acceptance gate.
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		current, err := load(tx, f.project, "Task", Str(task, "id"))
		if err != nil {
			return err
		}
		current["task_type"] = "mu_turn"
		if err = bump(current); err != nil {
			return err
		}
		return f.s.put(tx, "Task", current)
	})
	return doc, sid
}

func TestW14SessionProjectionSettledTurnAndReplay(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("finite-response-projection", Empty(), Empty())
	r := o.claim(task)
	artifact := o.report(r, Bytes(Object{"messages": []any{Object{"role": "assistant", "stopReason": "stop", "content": []any{Object{"type": "text", "text": "回答：已完成。"}}}}}))
	run := f.read("runs", Str(r.run, "id"))
	task = f.read("tasks", Str(task, "id"))
	doc, sid := sessionProjectionMapping(t, f, task)
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: doc}}
	nextSessionTurn(t, f, doc, sid, "SESSION_BUSY")
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if clientTurnSettled(tx, f.project, sid, task) {
			t.Fatal("unprojected response released session binding")
		}
		return c.projectSessionRun(tx, f.project, run, []any{artifact["id"]})
	})
	var before, after int
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=?", sid).Scan(&before); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if !clientTurnSettled(tx, f.project, sid, task) {
			t.Fatal("settled response still waits for Task acceptance")
		}
		// A confirmed model response may retain its upper-bound reservation while
		// actual cost is unavailable; that does not turn it into an unknown effect.
		if err := effectAppend(tx, f.project, Str(run, "id"), "confirmed-model", Object{"state": "CONFIRMED", "reservation_id": "retained-upper-bound", "receipt": Object{"actual_cost": nil}}); err != nil {
			return err
		}
		if !clientTurnSettled(tx, f.project, sid, task) {
			t.Fatal("confirmed response was blocked on unknown billing amount")
		}
		return c.projectSessionRun(tx, f.project, run, []any{artifact["id"]})
	})
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=?", sid).Scan(&after); err != nil {
		t.Fatal(err)
	}
	if before != 5 || after != before {
		t.Fatalf("projection duplicated or lost events: %d -> %d", before, after)
	}
	var settled string
	if err := f.db.QueryRow("SELECT json_extract(body,'$.payload.settled_at') FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='RUN_STATE'", sid).Scan(&settled); err != nil || settled != run["runtime_settled_at"] {
		t.Fatalf("wrong settled timestamp: %q %v", settled, err)
	}
	if f.read("tasks", Str(task, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatal("response projection self-accepted Task")
	}
	// Unknown effects and missing stop evidence retain the session even if the
	// original terminal event is present. Fixture transaction rolls back each case.
	for _, test := range []string{"RUNNING", "UNKNOWN", "children", "queue"} {
		t.Run(test, func(t *testing.T) {
			tx, err := f.db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			current, err := load(tx, f.project, "Run", Str(run, "id"))
			if err != nil {
				t.Fatal(err)
			}
			switch test {
			case "RUNNING":
				current["status"] = "RUNNING"
			case "children":
				current["children_stopped"] = false
			case "queue":
				current["queue_empty"] = false
			case "UNKNOWN":
				if err = effectAppend(tx, f.project, Str(run, "id"), "unconfirmed", Object{"state": "UNKNOWN"}); err != nil {
					t.Fatal(err)
				}
			}
			if _, err = tx.Exec("UPDATE domain_objects SET body=? WHERE project=? AND kind='Run' AND id=?", string(Bytes(current)), f.project, run["id"]); err != nil {
				t.Fatal(err)
			}
			if clientTurnSettled(tx, f.project, sid, task) {
				t.Fatal("unsettled response released session")
			}
		})
	}
	nextSessionTurn(t, f, doc, sid, "COMPLETED")
	var nextTask string
	if err := f.db.QueryRow("SELECT task_id FROM client_sessions WHERE id=?", sid).Scan(&nextTask); err != nil || nextTask == task["id"] {
		t.Fatalf("second message did not create a distinct finite Task: %s %v", nextTask, err)
	}
	if f.read("tasks", Str(task, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatal("next message self-accepted previous Task")
	}
}

func TestW14SessionProjectionFailureCancelAndUnknown(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	task := o.task("terminal-projection", Empty(), Empty())
	r := o.claim(task)
	doc, sid := sessionProjectionMapping(t, f, task)
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: doc}}
	for _, status := range []string{"RUNNING", "CANCEL_REQUESTED", "CANCELLED", "FAILED"} {
		t.Run(status, func(t *testing.T) {
			// Explicit canonical-state fixture: only the projection and finite-turn
			// gate are under test here, not an OS cancellation qualification.
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				run, err := load(tx, f.project, "Run", Str(r.run, "id"))
				if err != nil {
					return err
				}
				run["status"] = status
				run["children_stopped"], run["queue_empty"] = false, false
				run["runtime_settled_at"], run["cancel_confirmed_at"] = nil, nil
				if status == "CANCEL_REQUESTED" || status == "CANCELLED" {
					run["cancel_requested_at"] = Now()
				}
				if status == "CANCELLED" {
					run["cancel_confirmed_at"] = Now()
					run["children_stopped"], run["queue_empty"] = true, true
				}
				if status == "FAILED" {
					run["runtime_settled_at"] = Now()
					run["children_stopped"], run["queue_empty"] = true, true
				}
				if err = bump(run); err != nil {
					return err
				}
				if _, err = tx.Exec("UPDATE domain_objects SET body=?,revision=? WHERE project=? AND kind='Run' AND id=?", string(Bytes(run)), run["revision"], f.project, run["id"]); err != nil {
					return err
				}
				return nil
			})
			if err := c.projectCurrentSessionRuns(context.Background()); err != nil {
				t.Fatal(err)
			}
			sourceTx(t, f.db, func(tx *sql.Tx) error {
				current, err := load(tx, f.project, "Task", Str(task, "id"))
				if err != nil {
					return err
				}
				want := status == "FAILED" || status == "CANCELLED"
				if clientTurnSettled(tx, f.project, sid, current) != want {
					t.Fatalf("status %s gave wrong turn gate", status)
				}
				return nil
			})
		})
	}
	// Simulate unresolved transport in an active canonical Run. markUnknown must
	// emit a visible wait condition without claiming the process was stopped.
	var epoch int64
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		run, err := load(tx, f.project, "Run", Str(r.run, "id"))
		if err != nil {
			return err
		}
		run["status"] = "RUNNING"
		run["children_stopped"], run["queue_empty"] = nil, nil
		if err = bump(run); err != nil {
			return err
		}
		epoch, _ = Num(run, "lease_epoch")
		_, err = tx.Exec("UPDATE domain_objects SET body=?,revision=? WHERE project=? AND kind='Run' AND id=?", string(Bytes(run)), run["revision"], f.project, run["id"])
		return err
	})
	for i := 0; i < 2; i++ {
		if err := c.markUnknown(context.Background(), f.project, Str(r.run, "id"), epoch, "incomplete model SSE"); err != nil {
			t.Fatal(err)
		}
	}
	var errors int
	if err := f.db.QueryRow("SELECT count(*) FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='ERROR'", sid).Scan(&errors); err != nil || errors != 1 {
		t.Fatalf("unknown event duplication: %d %v", errors, err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		current, err := load(tx, f.project, "Task", Str(task, "id"))
		if err != nil {
			return err
		}
		if clientTurnSettled(tx, f.project, sid, current) {
			t.Fatal("UNKNOWN response released turn")
		}
		return nil
	})
}

func TestW14SessionProjectionRecoveryAfterReportCommit(t *testing.T) {
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
		t.Fatalf("native fixture never reported: %s", Bytes(task))
	}
	doc, sid := sessionProjectionMapping(t, r.f, task)
	c.config.ClientSchema = doc
	var firstProjection string
	for i := 0; i < 2; i++ {
		if err := c.Recover(context.Background()); err != nil {
			t.Fatal(err)
		}
		var actual string
		if err := r.f.db.QueryRow("SELECT group_concat(body,char(10)) FROM (SELECT body FROM outbox WHERE json_extract(body,'$.session_id')=? ORDER BY json_extract(body,'$.sequence'))", sid).Scan(&actual); err != nil {
			t.Fatal(err)
		}
		if i == 0 {
			firstProjection = actual
		} else if actual != firstProjection {
			t.Fatal("recovery changed event IDs, payload or sequence")
		}
	}
	var events, states, artifacts, usages int
	if err := r.f.db.QueryRow("SELECT count(*),sum(json_extract(body,'$.kind')='RUN_STATE'),sum(json_extract(body,'$.kind')='ARTIFACT'),sum(json_extract(body,'$.kind')='USAGE') FROM outbox WHERE json_extract(body,'$.session_id')=?", sid).Scan(&events, &states, &artifacts, &usages); err != nil {
		t.Fatal(err)
	}
	if events != 3 || states != 1 || artifacts != 1 || usages != 1 {
		t.Fatalf("recovery needs exactly one original state, native JSON artifact and canonical usage: %d/%d/%d/%d", events, states, artifacts, usages)
	}
	sourceTx(t, r.f.db, func(tx *sql.Tx) error {
		var raw string
		if err := tx.QueryRow("SELECT body FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.kind')='USAGE'", sid).Scan(&raw); err != nil {
			return err
		}
		event, err := Decode([]byte(raw))
		if err != nil {
			return err
		}
		payload := event["payload"].(map[string]any)
		ledger, err := load(tx, r.f.project, "BudgetLedgerEntry", Str(payload, "ledger_entry_id"))
		if err != nil {
			return err
		}
		if event["run_id"] != task["active_run_id"] || ledger["run_id"] != task["active_run_id"] || ledger["cost_basis"] != "UNKNOWN" || payload["cost_known"] != false || payload["money"] != nil || payload["provider_usage_id"] != nil || payload["input_tokens"] != nil || payload["output_tokens"] != nil {
			t.Fatal("recovery invented cost or changed original immutable ledger attribution")
		}
		if !clientTurnSettled(tx, r.f.project, sid, task) {
			t.Fatal("recovered terminal response did not release turn")
		}
		return nil
	})
	if r.f.read("tasks", Str(task, "id"))["status"] != "EXECUTION_REPORTED" {
		t.Fatal("recovery self-accepted Task")
	}
}
