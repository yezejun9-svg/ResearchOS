//go:build windows

package domain

import (
	"testing"
)

func TestClientQueueGoalCancelBeforeRun(t *testing.T) {
	f, svc, client, sid := queueClientFixture(t)
	send, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.send", Object{"text": "pending supplement", "attachment_artifact_ids": Empty(), "delivery": "FOLLOW_UP"}))
	if deref(send.Status) != "COMPLETED" {
		t.Fatal(string(Bytes(send)))
	}
	var goal string
	f.db.QueryRow(`SELECT goal_id FROM client_sessions WHERE id=?`, sid).Scan(&goal)
	env := queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": goal, "reason": "stop before claim"})
	reply, _ := goalCommand(t, f, svc, env)
	if deref(reply.Status) != "COMPLETED" || reply.Result["settled"] != true || reply.Result["queue_empty"] != true {
		t.Fatalf("no-run cancellation: %s", Bytes(reply))
	}
	snap := reply.Result["snapshot"].(map[string]any)
	if snap["active_run_id"] != nil || len(Arr(snap, "pending_command_ids")) != 0 {
		t.Fatal("no-run cancel invented Run or retained settled pending")
	}
	repeated, replay := goalCommand(t, f, svc, env)
	if !replay || Hash(repeated) != Hash(reply) {
		t.Fatal("cancel replay changed")
	}
	var state string
	f.db.QueryRow(`SELECT state FROM client_command_queue`).Scan(&state)
	if state != "DROPPED" {
		t.Fatal(state)
	}
	_, _, _, runs := goalCounts(t, f)
	if runs != 0 {
		t.Fatal("cancellation admitted Run")
	}
	var original, final string
	if err := f.db.QueryRow(`SELECT original_response,final_response FROM client_control_requests`).Scan(&original, &final); err != nil || original == "" || final == "" {
		t.Fatalf("original/final receipts missing %v", err)
	}
}
func TestClientQueueForeignGoalCancelRefused(t *testing.T) {
	f, svc, client, sid := queueClientFixture(t)
	reply, _ := goalCommand(t, f, svc, queueClientEnvelope(t, f, client, sid, "session.control", Object{"action": "CANCEL", "target_id": ID(), "reason": "foreign"}))
	if deref(reply.ErrorCode) != "NOT_FOUND" {
		t.Fatal(string(Bytes(reply)))
	}
	var n int
	f.db.QueryRow(`SELECT count(*) FROM client_control_requests`).Scan(&n)
	if n != 0 {
		t.Fatal("foreign cancellation persisted")
	}
}
