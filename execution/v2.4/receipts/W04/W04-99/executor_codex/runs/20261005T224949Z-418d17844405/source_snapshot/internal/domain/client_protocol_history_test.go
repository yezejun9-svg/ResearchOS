//go:build windows

package domain

import (
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"
)

func clientHistoryDoc(t *testing.T) *SchemaDoc {
	t.Helper()
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
	return doc
}

func sendHistoryTurn(t *testing.T, f *fixture, doc *SchemaDoc, sid, text string) {
	t.Helper()
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		sess, err := loadClientSession(context.Background(), tx, sid, f.project)
		if err != nil {
			return err
		}
		svc := ClientService{Doc: doc, Domain: f.s, SessionRuntime: nextTurnFixturePort{},
			Host: ClientHostInfo{CoreBuildID: "history-fixture"}}
		env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), Method: strptr("session.send"),
			ProjectID: &f.project, SessionID: &sid,
			Payload: Bytes(Object{"text": text, "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
		reply, err := svc.sendClientMessage(context.Background(), tx, env, f.owner, sess)
		if err != nil {
			return err
		}
		if reply.Status == nil || *reply.Status != "COMPLETED" {
			t.Fatalf("send refused code=%v error=%+v", reply.ErrorCode, reply.Error)
		}
		return nil
	})
}

func TestClientHistoryRejectsIncompleteAndOversize(t *testing.T) {
	f := contextFixture(t)
	sid := mixedSessionEvents(t, f, 0)
	doc := clientHistoryDoc(t)
	appendMessage := func(phase, text string, offset int, id string) {
		t.Helper()
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			var wm, revision int64
			if err := tx.QueryRow("SELECT event_watermark,revision FROM client_sessions WHERE id=?", sid).Scan(&wm, &revision); err != nil {
				return err
			}
			kind := "MESSAGE"
			seq := wm + 1
			ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sid, Sequence: &seq,
				CoreBuildID: strptr("history-fixture"), ProtocolVersion: strptr(ProtocolV2), Kind: &kind,
				Payload: Bytes(Object{"message_id": id, "role": "USER", "phase": phase, "part_index": 0,
					"content_offset_utf8_bytes": offset, "text": text})}
			return AppendSessionEvent(context.Background(), tx, doc, f.project, ev, 1, revision)
		})
	}
	appendMessage("START", "", 0, "incomplete")
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		service := &ClientService{Doc: doc, Domain: f.s}
		_, err := service.clientHistoryArtifact(context.Background(), tx, Principal{ID: f.owner}, f.project, sid, 1)
		if err == nil || !strings.Contains(err.Error(), "GATE_FAILED") {
			t.Fatalf("incomplete prior message accepted: %v", err)
		}
		return nil
	})
	appendMessage("DELTA", "ok", 0, "incomplete")
	appendMessage("END", "", 2, "incomplete")
	for i := 0; i < 34; i++ {
		id := "large-" + ID()
		appendMessage("START", "", 0, id)
		appendMessage("DELTA", strings.Repeat("x", 1024), 0, id)
		appendMessage("END", "", 1024, id)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		service := &ClientService{Doc: doc, Domain: f.s}
		var wm int64
		if err := tx.QueryRow("SELECT event_watermark FROM client_sessions WHERE id=?", sid).Scan(&wm); err != nil {
			return err
		}
		_, err := service.clientHistoryArtifact(context.Background(), tx, Principal{ID: f.owner}, f.project, sid, wm)
		if err == nil || !strings.Contains(err.Error(), "CONTENT_TOO_LARGE") {
			t.Fatalf("oversize complete history was not refused: %v", err)
		}
		return nil
	})
	var artifacts int
	if err := f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='Artifact' AND json_extract(body,'$.evidence_kind')='OBSERVED'", f.project).Scan(&artifacts); err != nil {
		t.Fatal(err)
	}
	if artifacts != 0 {
		t.Fatal("refused history left a sealed artifact")
	}
}

func TestClientHistoryKeepsTwoRealSendRoundsAndAssistantRole(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	sid := mixedSessionEvents(t, f, 0)
	doc := clientHistoryDoc(t)
	workspace := "history-workspace"
	binding := WorkspaceBinding{AuthorizedRef: workspace, DisplayName: "history", DisplayPath: "fixture",
		RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive,
		PrincipalID: f.owner, ClientID: "history-client", HostPrincipalRef: "fixture-local-user", CreatedAt: Now()}
	if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, workspace, string(Bytes(binding))); err != nil {
		t.Fatal(err)
	}
	if _, err := f.db.Exec("UPDATE client_sessions SET workspace_ref=?,model_config_ref='fixture-model',core_build_id='history-fixture',lease_expires_at=? WHERE id=?",
		workspace, time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	// Both USER turns go through sendClientMessage and its real requirement,
	// Task, context and typed journal writes. The first runtime is explicitly a
	// fixture; its settled projection supplies the ASSISTANT message between them.
	firstUserText := "下一条独立消息"
	sendHistoryTurn(t, f, doc, sid, firstUserText)
	var firstTaskID string
	if err := f.db.QueryRow("SELECT task_id FROM client_sessions WHERE id=?", sid).Scan(&firstTaskID); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		first, err := load(tx, f.project, "Task", firstTaskID)
		if err != nil {
			return err
		}
		for _, v := range Arr(first, "input_refs") {
			if ref, ok := v.(map[string]any); ok && ref["entity_type"] == "Artifact" {
				t.Fatal("first turn received a phantom history artifact")
			}
		}
		return nil
	})
	projectedText := "夹在两轮之间的模型回答。"
	fixtureTask := o.task("history-fixture-response", Empty(), Empty())
	r := o.claim(fixtureTask)
	result := Bytes(Object{"messages": []any{Object{"role": "assistant", "stopReason": "stop",
		"content": []any{Object{"type": "text", "text": projectedText}}}}})
	artifact := o.report(r, result)
	run := f.read("runs", Str(r.run, "id"))
	if _, err := f.db.Exec("UPDATE client_sessions SET task_id=?,goal_id=?,lease_expires_at=? WHERE id=?",
		fixtureTask["id"], fixtureTask["goal_id"], time.Now().Add(time.Minute).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		current, err := load(tx, f.project, "Task", Str(fixtureTask, "id"))
		if err != nil {
			return err
		}
		current["task_type"] = "mu_turn"
		if err = bump(current); err != nil {
			return err
		}
		return f.s.put(tx, "Task", current)
	})
	coordinator := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: doc}}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return coordinator.projectSessionRun(tx, f.project, run, []any{artifact["id"]})
	})
	foreignSession := mixedSessionEvents(t, f, 0)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		foreignText := "另一个会话的私有消息"
		for i, part := range []Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0},
			{"phase": "DELTA", "text": foreignText, "content_offset_utf8_bytes": 0},
			{"phase": "END", "text": "", "content_offset_utf8_bytes": len([]byte(foreignText))}} {
			part["message_id"], part["role"], part["part_index"] = "foreign-message", "USER", 0
			kind, sequence := "MESSAGE", int64(i+1)
			ev := &SessionEvent{EventID: strptr(ID()), SessionID: &foreignSession, Sequence: &sequence,
				CoreBuildID: strptr("history-fixture"), ProtocolVersion: strptr(ProtocolV2), Kind: &kind, Payload: Bytes(part)}
			if err := AppendSessionEvent(context.Background(), tx, doc, f.project, ev, 1, sequence); err != nil {
				return err
			}
		}
		return nil
	})
	sendHistoryTurn(t, f, doc, sid, "第二轮消息")
	var taskID string
	if err := f.db.QueryRow("SELECT task_id FROM client_sessions WHERE id=?", sid).Scan(&taskID); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		task, err := load(tx, f.project, "Task", taskID)
		if err != nil {
			return err
		}
		var historyRef Object
		for _, v := range Arr(task, "input_refs") {
			if ref, ok := v.(map[string]any); ok && ref["entity_type"] == "Artifact" {
				historyRef = Object(ref)
			}
		}
		if historyRef == nil {
			t.Fatal("second Mu turn did not receive a sealed history artifact")
		}
		history, err := load(tx, f.project, "Artifact", Str(historyRef, "id"))
		if err != nil {
			return err
		}
		if Hash(Ref(history, "Artifact")) != Hash(historyRef) || history["access_class"] != "PROJECT" || history["measurement_mode"] != "FIXTURE" || history["evidence_kind"] != "OBSERVED" {
			t.Fatalf("history artifact provenance or ref changed: %s", Bytes(history))
		}
		var sealed int
		var raw []byte
		if err := tx.QueryRow("SELECT bytes,sealed FROM uploaded_content WHERE project=? AND storage_key=?", f.project, history["storage_key"]).Scan(&raw, &sealed); err != nil {
			return err
		}
		if sealed != 1 || Digest(raw) != history["content_hash"] {
			t.Fatal("history bytes were not sealed")
		}
		var manifest Object
		if err := json.Unmarshal(raw, &manifest); err != nil {
			return err
		}
		messages := Arr(manifest, "messages")
		if len(messages) != 2 || messages[0].(map[string]any)["role"] != "USER" || messages[0].(map[string]any)["text"] != firstUserText ||
			messages[1].(map[string]any)["role"] != "ASSISTANT" || messages[1].(map[string]any)["text"] != projectedText {
			t.Fatalf("two-turn history lost role or bytes: %s", raw)
		}
		if manifest["origin"] != "SESSION_MESSAGE_JOURNAL" || manifest["measurement_basis"] != "FIXTURE_OR_UNKNOWN_ASSISTANT_RUN" || len(Arr(manifest, "source_run_refs")) != 1 {
			t.Fatalf("history origin or fixture run basis missing: %s", raw)
		}
		return nil
	})
}
