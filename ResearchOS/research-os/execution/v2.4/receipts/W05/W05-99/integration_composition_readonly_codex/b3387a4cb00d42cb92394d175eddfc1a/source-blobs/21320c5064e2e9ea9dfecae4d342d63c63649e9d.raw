//go:build windows

package domain

import (
	"context"
	"database/sql"
	"fmt"
	"strings"
	"testing"
	"time"
)

func transcriptSession(t *testing.T, f *fixture, count int) (*SchemaDoc, string) {
	t.Helper()
	doc, sid := clientHistoryDoc(t), mixedSessionEvents(t, f, 0)
	workspace := "transcript-" + sid
	b := WorkspaceBinding{AuthorizedRef: workspace, DisplayName: "transcript", DisplayPath: "fixture", RealPath: t.TempDir(), Access: "READ_ONLY", ProjectID: &f.project, Revision: 1, Status: WorkspaceActive, PrincipalID: f.owner, ClientID: "mixed-client", HostPrincipalRef: "fixture", CreatedAt: Now()}
	if _, err := f.db.Exec(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES('',?,?,1,?,0)`, KindWorkspaceBinding, workspace, string(Bytes(b))); err != nil {
		t.Fatal(err)
	}
	if _, err := f.db.Exec(`UPDATE client_sessions SET workspace_ref=?,model_config_ref='fixture-model',core_build_id='fixture-build',title='transcript',lease_expires_at=? WHERE id=?`, workspace, time.Now().Add(time.Hour).UTC().Format(time.RFC3339Nano), sid); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		for i := 0; i < count; i++ {
			if err := transcriptAppend(ctxTranscript, tx, doc, f.project, sid, fmt.Sprintf("m%d", i), "中🙂"); err != nil {
				return err
			}
		}
		return nil
	})
	return doc, sid
}

var ctxTranscript = context.Background()

func transcriptAppend(ctx context.Context, tx *sql.Tx, doc *SchemaDoc, project, sid, id, text string, roles ...string) error {
	role := "USER"
	if len(roles) > 0 {
		role = roles[0]
	}
	var wm, revision, epoch int64
	if err := tx.QueryRow(`SELECT event_watermark,revision,writer_epoch FROM client_sessions WHERE id=?`, sid).Scan(&wm, &revision, &epoch); err != nil {
		return err
	}
	for _, p := range []Object{{"phase": "START", "text": "", "content_offset_utf8_bytes": 0}, {"phase": "DELTA", "text": text, "content_offset_utf8_bytes": 0}, {"phase": "END", "text": "", "content_offset_utf8_bytes": len(text)}} {
		p["message_id"], p["role"], p["part_index"] = id, role, 0
		wm++
		ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sid, Sequence: &wm, CoreBuildID: strptr("fixture-build"), ProtocolVersion: strptr(ProtocolV2), Kind: strptr("MESSAGE"), Payload: Bytes(p)}
		if err := AppendSessionEvent(ctx, tx, doc, project, ev, epoch, revision); err != nil {
			return err
		}
		revision++
	}
	return nil
}

func transcriptSend(t *testing.T, f *fixture, doc *SchemaDoc, sid string) (*ClientService, *Envelope) {
	t.Helper()
	var revision int64
	if err := f.db.QueryRow(`SELECT revision FROM client_sessions WHERE id=?`, sid).Scan(&revision); err != nil {
		t.Fatal(err)
	}
	svc := &ClientService{Doc: doc, Domain: f.s, SessionRuntime: nextTurnFixturePort{}, Host: ClientHostInfo{CoreBuildID: "fixture-build"}}
	env := &Envelope{ProtocolVersion: strptr(ProtocolV2), CommandID: strptr(ID()), ClientID: strptr("mixed-client"), ProjectID: &f.project, SessionID: &sid, ExpectedRevision: &revision, WriterEpoch: revPtr(1), Method: strptr("session.send"), Payload: Bytes(Object{"text": "真正的用户发送🙂", "attachment_artifact_ids": Empty(), "delivery": "NORMAL"})}
	return svc, env
}

func transcriptCounts(t *testing.T, f *fixture) string {
	t.Helper()
	var counts []any
	for _, table := range []string{"domain_objects", "domain_versions", "outbox", "uploaded_content", "idempotency"} {
		var n int
		if err := f.db.QueryRow("SELECT count(*) FROM " + table).Scan(&n); err != nil {
			t.Fatal(err)
		}
		counts = append(counts, n)
	}
	var raw string
	if err := f.db.QueryRow(`SELECT json_group_array(json_object('id',id,'revision',revision,'wm',event_watermark,'task',task_id,'goal',goal_id,'run',run_id,'transcript',transcript_artifact_id)) FROM client_sessions`).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	return string(Bytes(counts)) + raw
}

func TestClientTranscriptFullRecoveryAndBothProducers(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	doc, sid := transcriptSession(t, f, 199)
	svc, env := transcriptSend(t, f, doc, sid)
	var userID string
	for attempt := 0; attempt < 2; attempt++ {
		before := transcriptCounts(t, f)
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			res, replay, err := svc.Execute(ctxTranscript, tx, env, f.owner)
			if err != nil {
				return err
			}
			if deref(res.Status) != "COMPLETED" || replay != (attempt == 1) {
				t.Fatalf("send: %s replay=%v", Bytes(res), replay)
			}
			userID = Str(res.Result, "message_id")
			return nil
		})
		if attempt == 1 && before != transcriptCounts(t, f) {
			t.Fatal("command replay created records")
		}
	}
	var userRef string
	if err := f.db.QueryRow(`SELECT transcript_artifact_id FROM client_sessions WHERE id=?`, sid).Scan(&userRef); err != nil || userRef == "" {
		t.Fatalf("USER producer did not seal: %v", err)
	}
	task := o.task("transcript-assistant", Empty(), Empty())
	r := o.claim(task)
	assistantText := strings.Repeat("回答🙂", 17000)
	artifact := o.report(r, Bytes(Object{"messages": []any{Object{"role": "assistant", "stopReason": "stop", "content": []any{Object{"type": "text", "text": assistantText}}}}}))
	run := f.read("runs", Str(r.run, "id"))
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		current, err := load(tx, f.project, "Task", Str(task, "id"))
		if err != nil {
			return err
		}
		current["task_type"] = "mu_turn"
		if err = bump(current); err != nil {
			return err
		}
		if err = f.s.put(tx, "Task", current); err != nil {
			return err
		}
		_, err = tx.Exec(`UPDATE client_sessions SET task_id=?,goal_id=? WHERE id=?`, task["id"], task["goal_id"], sid)
		return err
	})
	c := &RuntimeCoordinator{service: f.s, config: RuntimeCoordinatorConfig{ClientSchema: doc}}
	// A sealing error must also abort the runtime's RUN_STATE/ARTIFACT/MESSAGE
	// projection, so recovery cannot skip a response whose artifact was not sealed.
	if _, err := f.db.Exec(`CREATE TRIGGER fail_assistant_transcript BEFORE UPDATE OF sealed ON uploaded_content WHEN CAST(NEW.bytes AS TEXT) LIKE '%researchos.session-transcript.v1%' BEGIN SELECT RAISE(ABORT,'assistant transcript seal failure'); END`); err != nil {
		t.Fatal(err)
	}
	failedBefore := transcriptCounts(t, f)
	failedTx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = c.projectSessionRun(failedTx, f.project, run, []any{artifact["id"]})
	if err == nil || !strings.Contains(err.Error(), "assistant transcript seal failure") {
		failedTx.Rollback()
		t.Fatalf("assistant seal fault: %v", err)
	}
	if err = failedTx.Rollback(); err != nil {
		t.Fatal(err)
	}
	if failedBefore != transcriptCounts(t, f) {
		t.Fatal("failed assistant seal left projection writes")
	}
	if _, err = f.db.Exec(`DROP TRIGGER fail_assistant_transcript`); err != nil {
		t.Fatal(err)
	}
	for attempt := 0; attempt < 2; attempt++ {
		before := transcriptCounts(t, f)
		sourceTx(t, f.db, func(tx *sql.Tx) error { return c.projectSessionRun(tx, f.project, run, []any{artifact["id"]}) })
		if attempt == 1 && before != transcriptCounts(t, f) {
			t.Fatal("assistant projection replay created records")
		}
	}
	before := transcriptCounts(t, f)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		snap, err := BuildSessionSnapshot(ctxTranscript, tx, doc, f.project, sid)
		if err != nil {
			return err
		}
		messages := Arr(snap, "messages")
		if len(messages) != 200 || snap["has_earlier_messages"] != true || messages[0].(Object)["message_id"] != "m1" || messages[198].(Object)["message_id"] != userID {
			t.Fatalf("wrong last 200: %d first=%v", len(messages), messages[0])
		}
		ref := snap["transcript_artifact_ref"].(Object)
		if ref["id"] == userRef {
			t.Fatal("assistant reused stale USER artifact")
		}
		a, err := load(tx, f.project, "Artifact", Str(ref, "id"))
		if err != nil {
			return err
		}
		var raw []byte
		if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, f.project, a["storage_key"]).Scan(&raw); err != nil {
			return err
		}
		body, err := Decode(raw)
		if err != nil {
			return err
		}
		all := Arr(body, "messages")
		last := all[200].(map[string]any)
		if len(all) != 201 || all[0].(map[string]any)["message_id"] != "m0" || last["role"] != "ASSISTANT" || Arr(last, "parts")[0].(map[string]any)["text"] != assistantText || len(raw) <= maxClientHistoryBytes || ref["content_hash"] != Digest(raw) || Hash(ref) != Hash(Ref(a, "Artifact")) {
			t.Fatal("full transcript lost identity, bytes or ref hash")
		}
		for i := 0; i < 199; i++ {
			m := all[i].(map[string]any)
			if m["message_id"] != fmt.Sprintf("m%d", i) || m["role"] != "USER" || m["complete"] != true || Arr(m, "parts")[0].(map[string]any)["text"] != "中🙂" {
				t.Fatalf("full transcript changed record %d", i)
			}
		}
		if all[199].(map[string]any)["message_id"] != userID || len(Arr(body, "message_sequences")) != 201 || Arr(body, "source_run_refs")[0].(map[string]any)["id"] != run["id"] {
			t.Fatal("full transcript lost user ID, sequence coverage or run identity")
		}
		through, _ := Num(body, "through_sequence")
		wm, _ := Num(snap, "event_sequence")
		if through != wm || len(Arr(body, "source_run_refs")) != 1 || a["measurement_mode"] != "FIXTURE" || body["measurement_basis"] != "FIXTURE_OR_UNKNOWN_ASSISTANT_RUN" {
			t.Fatalf("provenance/watermark: %s", Bytes(body["measurement_basis"]))
		}
		t.Logf("201 complete messages; snapshot last 200; %d sealed UTF-8 bytes; USER/ASSISTANT producer and replay checked; mode=%v", len(raw), a["measurement_mode"])
		return nil
	})
	if before != transcriptCounts(t, f) {
		t.Fatal("snapshot read created records")
	}
	// This transaction is a synthetic provenance branch test, not a LIVE run.
	// It proves the resolver preserves verified LIVE labels rather than forcing
	// every transcript into FIXTURE. The synthetic registration edit is rolled back.
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if _, err = tx.Exec(`UPDATE domain_objects SET body=json_set(body,'$.measurement_mode','LIVE') WHERE project=? AND kind='RuntimeRegistration' AND id=?`, f.project, run["runtime_id"]); err != nil {
		t.Fatal(err)
	}
	transcript, err := replaySessionTranscript(ctxTranscript, tx, doc, f.project, sid)
	if err != nil {
		t.Fatal(err)
	}
	_, mode, basis, err := transcriptProvenance(ctxTranscript, tx, f.project, sid, transcript)
	if err != nil || mode != "LIVE" || basis != "ALL_ASSISTANT_RUNS_LIVE" {
		t.Fatalf("synthetic LIVE provenance branch: %s %s %v", mode, basis, err)
	}
}

func TestClientTranscriptSendSealFailureRollsBack(t *testing.T) {
	f := contextFixture(t)
	doc, sid := transcriptSession(t, f, 0)
	svc, env := transcriptSend(t, f, doc, sid)
	if _, err := f.db.Exec(`CREATE TRIGGER fail_transcript BEFORE UPDATE OF sealed ON uploaded_content WHEN CAST(NEW.bytes AS TEXT) LIKE '%researchos.session-transcript.v1%' BEGIN SELECT RAISE(ABORT,'transcript seal failure'); END`); err != nil {
		t.Fatal(err)
	}
	before := transcriptCounts(t, f)
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	_, _, err = svc.Execute(ctxTranscript, tx, env, f.owner)
	if err == nil || !strings.Contains(err.Error(), "transcript seal failure") {
		tx.Rollback()
		t.Fatalf("seal failure not propagated: %v", err)
	}
	if err = tx.Rollback(); err != nil {
		t.Fatal(err)
	}
	if before != transcriptCounts(t, f) {
		t.Fatal("failed seal left business, journal, idempotency or artifact writes")
	}
}

func TestClientTranscriptRejectsStaleForeignAndCorruptReferences(t *testing.T) {
	f := contextFixture(t)
	doc, sid := transcriptSession(t, f, 201)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		return f.s.sealSessionTranscript(ctxTranscript, tx, doc, f.project, sid, f.owner)
	})
	for _, name := range []string{"stale-message", "foreign-session", "foreign-project", "content-hash", "missing-seal", "missing-reference"} {
		t.Run(name, func(t *testing.T) {
			tx, err := f.db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			var id string
			if err = tx.QueryRow(`SELECT transcript_artifact_id FROM client_sessions WHERE id=?`, sid).Scan(&id); err != nil {
				t.Fatal(err)
			}
			a, err := load(tx, f.project, "Artifact", id)
			if err != nil {
				t.Fatal(err)
			}
			switch name {
			case "stale-message":
				err = transcriptAppend(ctxTranscript, tx, doc, f.project, sid, "new-message", "新消息")
			case "foreign-session", "foreign-project":
				var raw []byte
				if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE storage_key=?`, a["storage_key"]).Scan(&raw); err != nil {
					t.Fatal(err)
				}
				body, e := Decode(raw)
				if e != nil {
					t.Fatal(e)
				}
				key := "session_id"
				if name == "foreign-project" {
					key = "project_id"
				}
				body[key] = "foreign"
				foreign, e := f.s.serverArtifact(tx, f.project, f.owner, "REPORT", Bytes(body), Empty())
				if e != nil {
					t.Fatal(e)
				}
				_, err = tx.Exec(`UPDATE client_sessions SET transcript_artifact_id=? WHERE id=?`, foreign["id"], sid)
			case "content-hash":
				// Deliberate disk-corruption fixture; the ordinary write trigger rejects this.
				if _, err = tx.Exec("DROP TRIGGER content_immutable"); err != nil {
					t.Fatal(err)
				}
				_, err = tx.Exec(`UPDATE uploaded_content SET bytes=? WHERE storage_key=?`, []byte("tampered"), a["storage_key"])
			case "missing-seal":
				_, err = tx.Exec(`UPDATE uploaded_content SET sealed=0 WHERE storage_key=?`, a["storage_key"])
			case "missing-reference":
				_, err = tx.Exec(`UPDATE client_sessions SET transcript_artifact_id=NULL WHERE id=?`, sid)
			}
			if err != nil {
				t.Fatal(err)
			}
			if _, err = BuildSessionSnapshot(ctxTranscript, tx, doc, f.project, sid); err == nil {
				t.Fatal("invalid full transcript accepted")
			}
		})
	}
	// Non-message events change event_sequence, not the transcript's message coverage.
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		var wm, revision int64
		if err := tx.QueryRow(`SELECT event_watermark,revision FROM client_sessions WHERE id=?`, sid).Scan(&wm, &revision); err != nil {
			return err
		}
		wm++
		ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sid, Sequence: &wm, CoreBuildID: strptr("fixture-build"), ProtocolVersion: strptr(ProtocolV2), Kind: strptr("ERROR"), Payload: Bytes(Object{"code": "RESOURCE_BLOCKED", "message": "fixture", "retryable": false, "recovery": "RESOLVE_RESOURCE", "current_revision": nil, "current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": ID()})}
		if err := AppendSessionEvent(ctxTranscript, tx, doc, f.project, ev, 1, revision); err != nil {
			return err
		}
		_, err := BuildSessionSnapshot(ctxTranscript, tx, doc, f.project, sid)
		return err
	})
}

func TestClientTranscriptStrictUTF8Replay(t *testing.T) {
	f := contextFixture(t)
	doc, sid := transcriptSession(t, f, 1)
	for _, name := range []string{"offset", "duplicate-start", "changed-role", "invalid-utf8", "part-gap"} {
		t.Run(name, func(t *testing.T) {
			tx, err := f.db.Begin()
			if err != nil {
				t.Fatal(err)
			}
			defer tx.Rollback()
			var raw string
			if err = tx.QueryRow(`SELECT body FROM outbox WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.sequence')=2`, sid).Scan(&raw); err != nil {
				t.Fatal(err)
			}
			body, e := Decode([]byte(raw))
			if e != nil {
				t.Fatal(e)
			}
			p := body["payload"].(map[string]any)
			switch name {
			case "offset":
				p["content_offset_utf8_bytes"] = 1
			case "duplicate-start":
				p["phase"], p["text"] = "START", ""
			case "changed-role":
				p["role"] = "SYSTEM"
			case "part-gap":
				p["part_index"] = 1
			}
			// Isolate the read validator from the independent immutable-journal write guard.
			if _, err = tx.Exec("DROP TRIGGER outbox_immutable"); err != nil {
				t.Fatal(err)
			}
			bytes := Bytes(body)
			if name == "invalid-utf8" {
				bytes = []byte(strings.Replace(string(bytes), "中🙂", string([]byte{0xff}), 1))
			}
			if _, err = tx.Exec(`UPDATE outbox SET body=? WHERE json_extract(body,'$.session_id')=? AND json_extract(body,'$.sequence')=2`, string(bytes), sid); err != nil {
				t.Fatal(err)
			}
			if _, err = replaySessionTranscript(ctxTranscript, tx, doc, f.project, sid); err == nil {
				t.Fatal("malformed journal accepted")
			}
		})
	}
}

func TestClientTranscriptUnknownAssistantRemainsRecoverableFixture(t *testing.T) {
	f := contextFixture(t)
	doc, sid := transcriptSession(t, f, 0)
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if err := transcriptAppend(ctxTranscript, tx, doc, f.project, sid, "unknown-assistant", "已有夹具回答", "ASSISTANT"); err != nil {
			return err
		}
		if err := f.s.sealSessionTranscript(ctxTranscript, tx, doc, f.project, sid, f.owner); err != nil {
			return err
		}
		snap, err := BuildSessionSnapshot(ctxTranscript, tx, doc, f.project, sid)
		if err != nil {
			return err
		}
		a, err := load(tx, f.project, "Artifact", Str(snap["transcript_artifact_ref"].(Object), "id"))
		if err != nil {
			return err
		}
		var raw []byte
		if err := tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE storage_key=?`, a["storage_key"]).Scan(&raw); err != nil {
			return err
		}
		body, err := Decode(raw)
		if err != nil {
			return err
		}
		if a["measurement_mode"] != "FIXTURE" || body["measurement_basis"] != "ASSISTANT_RUN_UNKNOWN" || len(Arr(body, "source_run_refs")) != 0 || len(Arr(snap, "messages")) != 1 {
			t.Fatal("nullable source became LIVE or was lost")
		}
		return nil
	})
}
