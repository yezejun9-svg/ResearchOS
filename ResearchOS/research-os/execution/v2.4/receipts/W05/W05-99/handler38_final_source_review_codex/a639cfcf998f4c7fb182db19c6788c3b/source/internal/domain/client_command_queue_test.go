//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
)

func queueClientFixture(t *testing.T) (*fixture, *ClientService, string, string) {
	t.Helper()
	f, svc, client := goalFixture(t)
	svc.ConfigurationAuthority = handlerMetadataFixture{f.owner}
	saved, _ := handlerCommand(t, f, svc, handlerDefaultEnvelope(1))
	if deref(saved.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(saved)))
	}
	configuredPort := svc.SessionRuntime.(goalClientPort)
	configuredPort.model = Str(saved.Result, "model_config_ref")
	svc.SessionRuntime = configuredPort
	reply, _ := goalCommand(t, f, svc, goalEnvelope(f, client, "original finite task", false))
	if deref(reply.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(reply)))
	}
	port := svc.SessionRuntime.(goalClientPort)
	port.admitErr = nil
	svc.SessionRuntime = port
	return f, svc, client, Str(reply.Result["snapshot"].(map[string]any), "session_id")
}
func queueClientEnvelope(t *testing.T, f *fixture, client, sid, method string, payload Object) *Envelope {
	t.Helper()
	var rev, epoch int64
	if err := f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, sid).Scan(&rev, &epoch); err != nil {
		t.Fatal(err)
	}
	return &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: &client, ProjectID: &f.project, SessionID: &sid, ExpectedRevision: &rev, WriterEpoch: &epoch, Method: &method, Payload: Bytes(payload)}
}
func TestClientQueueDurableReplayAndWriterFence(t *testing.T) {
	f, svc, client, sid := queueClientFixture(t)
	_, goals, tasks, runs := goalCounts(t, f)
	payload := Object{"text": "同样的完整输入", "attachment_artifact_ids": Empty(), "delivery": "STEER"}
	env := queueClientEnvelope(t, f, client, sid, "session.send", payload)
	reply, replay := goalCommand(t, f, svc, env)
	if replay || deref(reply.Status) != "COMPLETED" {
		t.Fatalf("enqueue: %s", Bytes(reply))
	}
	repeated, replayed := goalCommand(t, f, svc, env)
	if !replayed || Hash(repeated) != Hash(reply) {
		t.Fatal("enqueue identity changed on replay")
	}
	env2 := queueClientEnvelope(t, f, client, sid, "session.send", payload)
	second, _ := goalCommand(t, f, svc, env2)
	if second.Result["message_id"] == reply.Result["message_id"] {
		t.Fatal("duplicate text lost message identity")
	}
	pending := Arr(second.Result["snapshot"].(map[string]any), "pending_command_ids")
	if len(pending) != 2 {
		t.Fatalf("pending ids=%v", pending)
	}
	stale := *env
	stale.CommandID = strptr(ID())
	rejected, _ := goalCommand(t, f, svc, &stale)
	if deref(rejected.Status) != "REJECTED" {
		t.Fatal("stale CAS accepted")
	}
	fresh := queueClientEnvelope(t, f, client, sid, "session.send", payload)
	fresh.WriterEpoch = revPtr(123)
	rejected, _ = goalCommand(t, f, svc, fresh)
	if deref(rejected.ErrorCode) != "STALE_WRITER_EPOCH" {
		t.Fatal("stale writer accepted")
	}
	_, g, task, run := goalCounts(t, f)
	if goals != g || tasks != task || runs != run {
		t.Fatal("queue created business execution")
	}
	var count int
	if err := f.db.QueryRow(`SELECT count(*) FROM client_command_queue`).Scan(&count); err != nil || count != 2 {
		t.Fatalf("durable count=%d err=%v", count, err)
	}
}
func TestClientQueueSealAndCapacityRejectBeforeSuccess(t *testing.T) {
	for _, kind := range []string{"seal", "capacity"} {
		t.Run(kind, func(t *testing.T) {
			f, svc, client, sid := queueClientFixture(t)
			payload := Object{"text": "bounded", "attachment_artifact_ids": Empty(), "delivery": "FOLLOW_UP"}
			limit := 1
			if kind == "capacity" {
				limit = clientQueueCapacity
			}
			for i := 0; i < limit; i++ {
				reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", payload))
				if deref(reply.Status) != "COMPLETED" {
					t.Fatal(string(Bytes(reply)))
				}
			}
			if kind == "seal" {
				if _, err := f.db.Exec(`UPDATE client_queue_fences SET state='SEALING'`); err != nil {
					t.Fatal(err)
				}
			}
			refused, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", payload))
			if deref(refused.Status) != "REJECTED" {
				t.Fatal("fenced queue accepted")
			}
			var n int
			f.db.QueryRow(`SELECT count(*) FROM client_command_queue`).Scan(&n)
			if n != limit {
				t.Fatal("rejection left partial enqueue")
			}
		})
	}
}
func TestClientQueueAppendOnlyReceipts(t *testing.T) {
	f := setup(t)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		body := Object{"fact": "same"}
		if err := appendClientReceipt(tx, f.project, "generation", "command", "TEST", "receipt", body, nil); err != nil {
			return err
		}
		if err := appendClientReceipt(tx, f.project, "generation", "command", "TEST", "receipt", body, nil); err != nil {
			return err
		}
		if appendClientReceipt(tx, f.project, "generation", "command", "TEST", "receipt", Object{"fact": "changed"}, nil) == nil {
			t.Fatal("conflicting receipt accepted")
		}
		if _, err := tx.ExecContext(context.Background(), `DELETE FROM client_control_receipts`); err == nil {
			t.Fatal("receipt deletion allowed")
		}
		return nil
	})
}
func TestClientQueueEnqueueCommitBoundary(t *testing.T) {
	f, svc, client, sid := queueClientFixture(t)
	env := queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "commit boundary", "attachment_artifact_ids": Empty(), "delivery": "FOLLOW_UP"})
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	reply, _, err := svc.Execute(context.Background(), tx, handlerDecode(t, env), f.owner)
	if err != nil || deref(reply.Status) != "COMPLETED" {
		tx.Rollback()
		t.Fatalf("transaction enqueue %v %s", err, Bytes(reply))
	}
	if err = tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	var rows int
	if err = f.db.QueryRow(`SELECT count(*) FROM client_command_queue`).Scan(&rows); err != nil || rows != 0 {
		t.Fatal("uncommitted enqueue survived", rows, err)
	}
	reply, replay := goalCommand(t, f, svc, env)
	if replay || deref(reply.Status) != "COMPLETED" {
		t.Fatal("rollback left replay receipt", string(Bytes(reply)))
	}
	var task string
	if err = f.db.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, sid).Scan(&task); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return unknownClientRunQueue(tx, f.project, "no-dispatch", "fixture crash before dispatch")
	})
	var state string
	f.db.QueryRow(`SELECT state FROM client_command_queue`).Scan(&state)
	if state != "ENQUEUED" {
		t.Fatal("never-dispatched durable input lost", state)
	}
	again, replay := goalCommand(t, f, svc, env)
	if !replay || Hash(again) != Hash(reply) {
		t.Fatal("committed acceptance changed after recovery")
	}
}
func TestClientQueueRestoredNoRunCannotHideUnknownWithNewTurn(t *testing.T) {
	f, svc, client, sid := queueClientFixture(t)
	reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "future uncertainty", "attachment_artifact_ids": Empty(), "delivery": "STEER"}))
	if deref(reply.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(reply)))
	}
	var goal, task string
	f.db.QueryRow(`SELECT goal_id,task_id FROM client_sessions WHERE id=?`, sid).Scan(&goal, &task)
	reply, _ = goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "noRun cancellation fixture"}))
	if deref(reply.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(reply)))
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if _, err := tx.Exec(`UPDATE client_command_queue SET state='UNKNOWN'`); err != nil {
			return err
		}
		return fenceRestoredClientQueues(tx)
	})
	for _, method := range []string{"session.send", "session.control"} {
		payload := Object{"text": "must retain previous UNKNOWN", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"}
		if method == "session.control" {
			payload = Object{"action": "RESUME", "target_id": sid, "reason": "explicit resume is not unknown reconciliation"}
		}
		refused, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, method, payload))
		if deref(refused.ErrorCode) != "SESSION_BUSY" {
			t.Fatalf("%s hid original queue: %s", method, Bytes(refused))
		}
	}
	var current string
	f.db.QueryRow(`SELECT task_id FROM client_sessions WHERE id=?`, sid).Scan(&current)
	if current != task {
		t.Fatal("restored unknown Task mapping changed")
	}
}
