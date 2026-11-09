package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"strings"
	"testing"
)

func streamTestEvent(text string) []byte {
	raw, _ := json.Marshal(map[string]any{"choices": []any{map[string]any{"index": 0, "delta": map[string]any{"content": text}}}})
	return append(append([]byte("data: "), raw...), []byte("\n\n")...)
}

func modelStreamArchivedFixture(t *testing.T) (*sql.DB, *Service) {
	t.Helper()
	path := filepath.Join("..", "..", "execution", "v2.4", "receipts", "W05", "W05-99", "model_stream_executor_codex", "test-f4a65b87734641c8a39d7060dd8b24fb", "actual-fixtures", "TestCLIModelStreamInterruptedPrefix", "fixture.sqlite")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	copy := filepath.Join(t.TempDir(), "state.sqlite")
	if err = os.WriteFile(copy, raw, 0600); err != nil {
		t.Fatal(err)
	}
	db, err := store.Open(copy)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	contracts, err := LoadContracts("../../spec/v2.0/contracts")
	if err != nil {
		t.Fatal(err)
	}
	return db, &Service{DB: db, Contracts: contracts}
}

func TestModelStreamInterruptedActualBackupRestore(t *testing.T) {
	db, s := modelStreamArchivedFixture(t)
	if err := validateBackupQueue(db); err != nil {
		t.Fatal("original observed partial", err)
	}
	// This copy is a local fixture. Revoke the already removed fixture workspace,
	// exactly as the existing queue restore suite does; original bytes stay sealed.
	if _, err := db.Exec(`UPDATE domain_objects SET body=json_set(body,'$.status','REVOKED') WHERE kind='WorkspaceBinding'`); err != nil {
		t.Fatal(err)
	}
	var before string
	if err := db.QueryRow(`SELECT group_concat(body,'') FROM client_control_receipts WHERE kind=? ORDER BY rowid`, modelObservationKind).Scan(&before); err != nil {
		t.Fatal(err)
	}
	key := backupTestKey(t)
	archive, _ := backupTestCreate(t, s, key)
	destination := filepath.Join(t.TempDir(), "restored")
	report, err := RestoreBackup(context.Background(), archive, destination, backupOpt(t, s, key))
	if err != nil {
		t.Fatal(err)
	}
	if report.Status != "RESTORED_RECONCILIATION_REQUIRED" {
		t.Fatal(report.Status)
	}
	restored, err := store.Open(filepath.Join(destination, "state.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer restored.Close()
	if err = validateBackupQueue(restored); err != nil {
		t.Fatal("restored immutable prefix", err)
	}
	var after string
	var unknown, ends, fenced int
	if err = restored.QueryRow(`SELECT group_concat(body,'') FROM client_control_receipts WHERE kind=? ORDER BY rowid`, modelObservationKind).Scan(&after); err != nil {
		t.Fatal(err)
	}
	restored.QueryRow(`SELECT count(*) FROM resource_effects x WHERE json_extract(body,'$.state')='UNKNOWN' AND sequence=(SELECT max(y.sequence) FROM resource_effects y WHERE y.project=x.project AND y.run=x.run AND y.effect_key=x.effect_key)`).Scan(&unknown)
	restored.QueryRow(`SELECT count(*) FROM outbox WHERE json_extract(body,'$.kind')='MESSAGE' AND json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='END'`).Scan(&ends)
	restored.QueryRow(`SELECT count(*) FROM client_queue_fences WHERE restore_fenced=1 AND state='RECONCILING'`).Scan(&fenced)
	if before != after || unknown != 1 || ends != 0 || fenced != 1 {
		t.Fatalf("partial restore changed facts equal=%v UNKNOWN=%d END=%d fenced=%d", before == after, unknown, ends, fenced)
	}
	// The old process/sequence cannot turn the restored prefix into a current live
	// stream. Restore preserves the evidence and fences its execution separately.
	t.Logf("MODEL_STREAM_RESTORE immutable=%v UNKNOWN=%d END=%d restore_fenced=%d", before == after, unknown, ends, fenced)
}

func TestModelStreamBackupRejectsChangedCanonicalEvidence(t *testing.T) {
	for name, change := range map[string]string{
		"binding":            `UPDATE client_control_receipts SET body=json_set(body,'$.observation.binding.run_id','foreign') WHERE kind='MODEL_STREAM_OBSERVATION_V1'`,
		"sequence":           `UPDATE client_control_receipts SET body=json_set(body,'$.observation.sequence',99) WHERE kind='MODEL_STREAM_OBSERVATION_V1'`,
		"digest":             `UPDATE client_control_receipts SET body=json_set(body,'$.observation.digest','sha256:forged') WHERE kind='MODEL_STREAM_OBSERVATION_V1'`,
		"event-id":           `UPDATE client_control_receipts SET body=json_set(body,'$.journal_event_ids[0]','foreign') WHERE kind='MODEL_STREAM_OBSERVATION_V1' AND json_extract(body,'$.observation.payload.event')='text_delta'`,
		"durable-prefix":     `UPDATE outbox SET body=json_set(body,'$.payload.text','forged') WHERE json_extract(body,'$.payload.role')='ASSISTANT' AND json_extract(body,'$.payload.phase')='DELTA'`,
		"missing-transcript": `UPDATE client_sessions SET transcript_artifact_id=NULL`,
		"claim-complete":     `UPDATE client_control_receipts SET body=json_set(body,'$.observation.payload.event','message_end') WHERE kind='MODEL_STREAM_OBSERVATION_V1' AND json_extract(body,'$.observation.sequence')=1`,
		"source-process":     `UPDATE runtime_dispatches SET identity='{}' WHERE run IN (SELECT run_id FROM client_queue_fences)`,
	} {
		t.Run(name, func(t *testing.T) {
			db, _ := modelStreamArchivedFixture(t)
			if err := validateModelStreamBackup(db); err != nil {
				t.Fatal(err)
			}
			// Fault injection is confined to a copy of this test's own closed database.
			rows, err := db.Query(`SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name IN ('client_control_receipts','outbox','runtime_dispatches')`)
			if err != nil {
				t.Fatal(err)
			}
			names := []string{}
			for rows.Next() {
				var n string
				rows.Scan(&n)
				names = append(names, n)
			}
			rows.Close()
			for _, n := range names {
				if _, err = db.Exec(`DROP TRIGGER "` + strings.ReplaceAll(n, `"`, `""`) + `"`); err != nil {
					t.Fatal(err)
				}
			}
			if _, err = db.Exec(change); err != nil {
				t.Fatal(err)
			}
			rows, err = db.Query(`SELECT receipt_id,body FROM client_control_receipts WHERE kind=?`, modelObservationKind)
			if err != nil {
				t.Fatal(err)
			}
			updates := map[string]string{}
			for rows.Next() {
				var id, body string
				rows.Scan(&id, &body)
				updates[id] = Digest([]byte(body))
			}
			rows.Close()
			for id, hash := range updates {
				if _, err = db.Exec(`UPDATE client_control_receipts SET body_hash=? WHERE receipt_id=?`, hash, id); err != nil {
					t.Fatal(err)
				}
			}
			if err = validateModelStreamBackup(db); err == nil {
				t.Fatal("forged canonical evidence accepted despite recomputed self hash")
			}
		})
	}
}

func TestModelStreamQuarantineOriginalBytesAndTerminalBarrier(t *testing.T) {
	// Independently enumerate valid SSE boundary variants, including one event
	// much larger than the auxiliary wire frame (which must not narrow SSE).
	for _, input := range [][]byte{
		append(streamTestEvent("中文 A"), []byte("data: [DONE]\n\n")...),
		[]byte(": comment\r\n\r\ndata: {\"choices\":[],\r\ndata: \"usage\":{}}\r\n\r\ndata: [DONE]\r\n\r\n"),
		append(streamTestEvent(strings.Repeat("界", 30000)), []byte("data: [DONE]\n\n")...),
	} {
		if !completeRuntimeModelSSE(input) {
			t.Fatal("invalid test input")
		}
		for _, step := range []int{1, 7, 8192, len(input)} {
			q, _ := newModelSSEQuarantine("SYNTHETIC-secret-credential")
			var visible []byte
			for pos := 0; pos < len(input); pos += step {
				part, err := q.Feed(input[pos:min(pos+step, len(input))])
				if err != nil {
					t.Fatal(err)
				}
				visible = append(visible, part...)
			}
			if bytes.Contains(visible, []byte("[DONE]")) {
				t.Fatal("terminal escaped before original confirmation")
			}
			original, terminal, err := q.Finish()
			if err != nil || !bytes.Equal(original, input) || !bytes.Equal(append(visible, terminal...), input) {
				t.Fatal("original bytes/hash changed", err)
			}
		}
	}
}

func TestModelStreamQuarantineSplitSecretAndEscapes(t *testing.T) {
	secret := "SYNTHETIC-密钥-secret"
	for split := 1; split < len([]rune(secret)); split++ {
		a, b := string([]rune(secret)[:split]), string([]rune(secret)[split:])
		raw := append(streamTestEvent(a), streamTestEvent(b)...)
		// JSON escapes and UTF-8 reads exercise independent decoding boundaries.
		raw = bytes.ReplaceAll(raw, []byte("密"), []byte(`\u5bc6`))
		for step := 1; step <= len(raw); step++ {
			q, _ := newModelSSEQuarantine(secret)
			var exposed []byte
			rejected := false
			for pos := 0; pos < len(raw); pos += step {
				part, err := q.Feed(raw[pos:min(pos+step, len(raw))])
				exposed = append(exposed, part...)
				if err != nil {
					rejected = true
					break
				}
			}
			if !rejected || len(exposed) != 0 {
				t.Fatalf("secret prefix escaped split=%d step=%d bytes=%d", split, step, len(exposed))
			}
		}
	}
	q, _ := newModelSSEQuarantine(secret)
	if ready, err := q.Feed(streamTestEvent("SYNTHETIC-")); err != nil || len(ready) != 0 {
		t.Fatal("suspect prefix must wait")
	}
	if ready, err := q.Feed(streamTestEvent("different")); err != nil || len(ready) == 0 {
		t.Fatal("disambiguated original events must progress")
	}
}

func TestModelStreamQuarantineMalformedEOFAndBounds(t *testing.T) {
	for _, raw := range [][]byte{
		streamTestEvent("partial"), []byte("data: [DONE]\n\n"), []byte("data: nope\n\ndata: [DONE]\n\n"),
		append(append(streamTestEvent("ok"), []byte("data: [DONE]\n\n")...), streamTestEvent("late")...),
		[]byte("data: {\"x\":\"\xff\"}\n\ndata: [DONE]\n\n"),
		bytes.Repeat([]byte("x"), modelStreamMaxRaw+1),
	} {
		q, _ := newModelSSEQuarantine()
		_, err := q.Feed(raw)
		if err == nil {
			_, _, err = q.Finish()
		}
		if err == nil {
			t.Fatal("invalid input accepted")
		}
	}
	q, _ := newModelSSEQuarantine()
	if _, err := q.Feed([]byte("data: broken\n\n")); err == nil {
		t.Fatal("expected refusal")
	}
	if _, err := q.Feed(streamTestEvent("later")); err == nil {
		t.Fatal("failed stream reopened")
	}
}
