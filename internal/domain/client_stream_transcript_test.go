//go:build windows

package domain

import (
	"context"
	"database/sql"
	"testing"
)

func TestClientStreamTranscriptPartialCASAndFullRecovery(t *testing.T) {
	o := orchestrationSetup(t)
	f := o.f
	doc, sid := transcriptSession(t, f, 199)
	r := o.claim(o.task("stream-prefix", Empty(), Empty()))
	runID := Str(r.run, "id")
	var originalRevision, writer int64
	if err := f.db.QueryRow(`SELECT revision,writer_epoch FROM client_sessions WHERE id=?`, sid).Scan(&originalRevision, &writer); err != nil {
		t.Fatal(err)
	}
	appendPart := func(tx *sql.Tx, phase, text string, offset int, revision int64) error {
		var wm int64
		if err := tx.QueryRow(`SELECT event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&wm); err != nil {
			return err
		}
		wm++
		ev := &SessionEvent{EventID: strptr(ID()), SessionID: &sid, Sequence: &wm, ProtocolVersion: strptr(ProtocolV2), CoreBuildID: strptr("fixture-build"), RunID: &runID, Kind: strptr("MESSAGE"), Payload: Bytes(Object{"message_id": "partial-model", "role": "ASSISTANT", "phase": phase, "part_index": 0, "text": text, "content_offset_utf8_bytes": offset})}
		if err := appendRuntimeMessageEvent(context.Background(), tx, doc, f.project, ev, writer, revision); err != nil {
			return err
		}
		return f.s.sealSessionTranscript(context.Background(), tx, doc, f.project, sid, f.owner)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if err := appendPart(tx, "START", "", 0, originalRevision); err != nil {
			return err
		}
		return appendPart(tx, "DELTA", "前缀🙂", 0, originalRevision)
	})
	var first, firstHash string
	if err := f.db.QueryRow(`SELECT transcript_artifact_id FROM client_sessions WHERE id=?`, sid).Scan(&first); err != nil {
		t.Fatal(err)
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		a, err := load(tx, f.project, "Artifact", first)
		if err != nil {
			return err
		}
		firstHash = Str(a, "content_hash")
		return transcriptAppend(context.Background(), tx, doc, f.project, sid, "user-during-stream", "用户在流中提交")
	})
	var currentRevision int64
	if err := f.db.QueryRow(`SELECT revision FROM client_sessions WHERE id=?`, sid).Scan(&currentRevision); err != nil {
		t.Fatal(err)
	}
	if currentRevision != originalRevision+3 {
		t.Fatalf("runtime tokens changed revision: old=%d current=%d", originalRevision, currentRevision)
	}
	before := transcriptCounts(t, f)
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = appendPart(tx, "DELTA", "B", len("前缀🙂"), originalRevision)
	tx.Rollback()
	if err == nil || before != transcriptCounts(t, f) {
		t.Fatal("stale revision wrote stream prefix")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error { return appendPart(tx, "DELTA", "B", len("前缀🙂"), currentRevision) })
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		snapshot, err := BuildSessionSnapshot(context.Background(), tx, doc, f.project, sid)
		if err != nil {
			return err
		}
		if len(Arr(snapshot, "messages")) != 200 || snapshot["has_earlier_messages"] != true {
			t.Fatal("stream snapshot did not retain 200 latest messages")
		}
		reference := snapshot["transcript_artifact_ref"].(Object)
		a, err := load(tx, f.project, "Artifact", Str(reference, "id"))
		if err != nil {
			return err
		}
		if a["id"] == first || a["measurement_mode"] == "LIVE" {
			t.Fatal("partial reused/promoted immutable artifact")
		}
		var raw []byte
		if err = tx.QueryRow(`SELECT bytes FROM uploaded_content WHERE project=? AND storage_key=? AND sealed=1`, f.project, a["storage_key"]).Scan(&raw); err != nil {
			return err
		}
		body, err := Decode(raw)
		if err != nil {
			return err
		}
		if len(Arr(body, "messages")) != 201 || body["complete"] != false {
			t.Fatal("full partial history truncated or completed")
		}
		messages := Arr(body, "messages")
		partial := messages[199].(map[string]any)
		if partial["complete"] != false || Arr(partial, "parts")[0].(map[string]any)["text"] != "前缀🙂B" {
			t.Fatal("interleaved prefix changed")
		}
		old, err := load(tx, f.project, "Artifact", first)
		if err != nil {
			return err
		}
		if old["content_hash"] != firstHash {
			t.Fatal("old partial artifact mutated")
		}
		svc := &ClientService{Doc: doc, Domain: f.s}
		var wm int64
		tx.QueryRow(`SELECT event_watermark FROM client_sessions WHERE id=?`, sid).Scan(&wm)
		if _, err = svc.clientHistoryArtifact(context.Background(), tx, Principal{ID:f.owner}, f.project, sid, wm); err == nil {
			t.Fatal("new NORMAL accepted unfinished assistant history")
		}
		return nil
	})
	// A failed seal rolls the watermark and public delta back with its pointer.
	if _, err = f.db.Exec(`CREATE TRIGGER fail_stream_pointer BEFORE UPDATE OF transcript_artifact_id ON client_sessions BEGIN SELECT RAISE(ABORT,'injected stream pointer failure'); END`); err != nil {
		t.Fatal(err)
	}
	before = transcriptCounts(t, f)
	tx, err = f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	err = appendPart(tx, "DELTA", "C", len("前缀🙂B"), currentRevision)
	tx.Rollback()
	if err == nil || before != transcriptCounts(t, f) {
		t.Fatal("failed pointer seal left a public prefix")
	}
}
