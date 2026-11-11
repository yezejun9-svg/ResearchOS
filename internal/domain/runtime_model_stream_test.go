package domain

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
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

func streamTestDelta(delta Object) []byte {
	return append(append([]byte("data: "), Bytes(Object{"choices": []any{Object{"index": 0, "delta": delta}}})...), []byte("\n\n")...)
}

func TestModelStreamQuarantineSDKSemanticMerges(t *testing.T) {
	secret := "SYNTHETIC-密钥-secret"
	for _, kind := range []string{"alias", "reasoning.text", "reasoning.summary"} {
		t.Run(kind, func(t *testing.T) {
			for split := 1; split < len([]rune(secret)); split++ {
				a, b := string([]rune(secret)[:split]), string([]rune(secret)[split:])
				events := [][]byte{}
				for i, text := range []string{a, b} {
					delta := Object{}
					if kind == "alias" {
						key := "reasoning"
						if i == 1 {
							key = "reasoning_content"
						}
						delta[key] = text
					} else {
						field := "text"
						if kind == "reasoning.summary" {
							field = "summary"
						}
						delta["reasoning_details"] = []any{Object{"type": kind, field: text, "index": i, "id": fmt.Sprint(i)}}
					}
					events = append(events, streamTestDelta(delta))
				}
				raw := append(events[0], events[1]...)
				raw = bytes.ReplaceAll(raw, []byte("密"), []byte(`\u5bc6`))
				for _, step := range []int{1, 7, 31, len(raw)} {
					q, _ := newModelSSEQuarantine(secret)
					exposed := 0
					rejected := false
					for pos := 0; pos < len(raw); pos += step {
						part, err := q.Feed(raw[pos:min(pos+step, len(raw))])
						exposed += len(part)
						if err != nil {
							rejected = true
							break
						}
					}
					if !rejected || exposed != 0 {
						t.Fatalf("semantic quarantine failed split=%d step=%d exposed=%d", split, step, exposed)
					}
					if _, _, err := q.Finish(); err == nil {
						t.Fatal("rejected stream released at EOF")
					}
				}
			}
		})
	}
}

func TestModelStreamQuarantineSDKAliasPriorityAndBenignProgress(t *testing.T) {
	for _, kind := range []string{"alias", "reasoning.text", "reasoning.summary"} {
		t.Run(kind, func(t *testing.T) {
			q, _ := newModelSSEQuarantine("PREFIX-SECRET")
			delta := func(text string) Object {
				if kind == "alias" {
					return Object{"reasoning_content": text, "reasoning": "unused"}
				}
				field := "text"
				if kind == "reasoning.summary" {
					field = "summary"
				}
				return Object{"reasoning_details": []any{Object{"type": kind, field: text}}}
			}
			a, b := streamTestDelta(delta("PREFIX-")), streamTestDelta(delta("different"))
			if r, e := q.Feed(a); e != nil || len(r) != 0 {
				t.Fatal("suspect semantic prefix escaped", e)
			}
			r, e := q.Feed(b)
			if e != nil || !bytes.Equal(r, append(a, b...)) {
				t.Fatal("benign semantic divergence did not progress", e)
			}
			end := []byte("data: [DONE]\n\n")
			if r, e = q.Feed(end); e != nil || len(r) != 0 {
				t.Fatal("terminal bypass", e)
			}
			original, terminal, e := q.Finish()
			if e != nil || !bytes.Equal(original, append(append(a, b...), end...)) || !bytes.Equal(terminal, end) {
				t.Fatal("semantic original bytes changed", e)
			}
		})
	}
	// Same-event aliases are selected, never concatenated with each other.
	q, _ := newModelSSEQuarantine("PREFIX-SECRET")
	for _, d := range []Object{{"reasoning_content": "safe", "reasoning": "PREFIX-"}, {"reasoning_content": "safe", "reasoning": "SECRET"}, {"reasoning_content": "", "reasoning": "safe", "reasoning_text": "PREFIX-"}, {"reasoning_content": nil, "reasoning": "safe", "reasoning_text": "SECRET"}} {
		raw := streamTestDelta(d)
		r, e := q.Feed(raw)
		if e != nil || !bytes.Equal(r, raw) {
			t.Fatal("unused lower-priority alias held or joined", e)
		}
	}
	// Invalid details do not break a valid SDK merge. Valid other types do.
	for _, middle := range []Object{{"type": "reasoning.text", "text": 42}, {"type": "reasoning.text", "text": "ignored", "index": "invalid"}} {
		q, _ := newModelSSEQuarantine("PREFIX-SECRET")
		a := streamTestDelta(Object{"reasoning_details": []any{Object{"type": "reasoning.text", "text": "PREFIX-"}, middle, Object{"type": "reasoning.text", "text": "SECRET"}}})
		if _, e := q.Feed(a); e == nil {
			t.Fatal("invalid detail incorrectly terminated merge")
		}
	}
	q, _ = newModelSSEQuarantine("PREFIX-SECRET")
	for _, d := range []Object{{"type": "reasoning.text", "text": "PREFIX-"}, {"type": "reasoning.encrypted", "data": "opaque"}, {"type": "reasoning.text", "text": "SECRET"}} {
		if _, e := q.Feed(streamTestDelta(Object{"reasoning_details": []any{d}})); e != nil {
			t.Fatal("discrete encrypted metadata joined adjacent text", e)
		}
	}
}

func TestModelStreamQuarantineOtherConcatenatedLanes(t *testing.T) {
	for _, lane := range []string{"content", "arguments", "input", "reasoning_text"} {
		t.Run(lane, func(t *testing.T) {
			q, _ := newModelSSEQuarantine("PREFIX-SECRET")
			for i, text := range []string{"PREFIX-", "SECRET"} {
				delta := Object{lane: text}
				if lane == "arguments" || lane == "input" {
					key := "function"
					if lane == "input" {
						key = "custom"
					}
					calls := []any{Object{"index": 7, key: Object{lane: text}}}
					if i == 1 {
						calls = append([]any{Object{"index": 0, "function": Object{"name": "unrelated"}}}, calls...)
					}
					delta = Object{"tool_calls": calls}
				}
				exposed, err := q.Feed(streamTestDelta(delta))
				if len(exposed) != 0 || i == 0 && err != nil || i == 1 && err == nil {
					t.Fatal("concatenated lane escaped", lane, i, err)
				}
			}
		})
	}
	for _, first := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
		for _, second := range []string{"reasoning_content", "reasoning", "reasoning_text"} {
			q, _ := newModelSSEQuarantine("PREFIX-SECRET")
			if r, e := q.Feed(streamTestDelta(Object{first: "PREFIX-"})); e != nil || len(r) != 0 {
				t.Fatal(first, e)
			}
			if _, e := q.Feed(streamTestDelta(Object{second: "SECRET"})); e == nil {
				t.Fatal("alias switch accepted", first, second)
			}
		}
	}
}

func TestModelStreamQuarantineSDKNumberToolIdentity(t *testing.T) {
	for _, indexes := range [][2]string{{"-0", "0"}, {"0", "-0"}, {"-0e123", "0.0"}, {"1", "1.0"}, {"9007199254740992", "9007199254740993"}, {"1e-400", "0"}} {
		t.Run(indexes[0]+"_"+indexes[1], func(t *testing.T) {
			q, _ := newModelSSEQuarantine("permission-loopback-fixture")
			for i, part := range []string{`{"value":"perm\u0069`, `ssion-loopback-fixture"}`} {
				call := Object{"index": json.RawMessage(indexes[i]), "function": Object{"arguments": part}}
				if i == 0 {
					call["id"] = "synthetic-call"
				}
				out, err := q.Feed(streamTestDelta(Object{"tool_calls": []any{call}}))
				if len(out) != 0 || i == 0 && err != nil || i == 1 && err == nil {
					t.Fatalf("SDK numeric identity split its semantic lane: part=%d released=%d err=%v", i, len(out), err)
				}
			}
		})
	}
	q, _ := newModelSSEQuarantine("permission-loopback-fixture")
	first := streamTestDelta(Object{"tool_calls": []any{Object{"index": json.RawMessage("-0"), "function": Object{"arguments": `{"value":"perm\u0069`}}}})
	second := streamTestDelta(Object{"tool_calls": []any{Object{"index": 0, "function": Object{"arguments": `ssion-benign"}`}}}})
	if out, err := q.Feed(first); err != nil || len(out) != 0 {
		t.Fatal("suspected JSON prefix must remain held", err)
	}
	if out, err := q.Feed(second); err != nil || !bytes.Equal(out, append(first, second...)) {
		t.Fatal("same numeric lane must release benign bytes before EOF", err)
	}
}

func TestModelStreamQuarantineNestedToolJSON(t *testing.T) {
	for _, encoded := range []string{`{"value":"perm\u0069ssion-loopback-fixture"}`, `{"value":"perm\u0069ssion-\ud83d\ude42-fixture"}`} {
		secret := "permission-loopback-fixture"
		if strings.Contains(encoded, "d83d") {
			secret = "permission-🙂-fixture"
		}
		for split := 1; split < len(encoded); split++ {
			q, _ := newModelSSEQuarantine(secret)
			rejected := false
			for i, part := range []string{encoded[:split], encoded[split:]} {
				call := Object{"index": 7, "function": Object{"arguments": part}}
				if i == 0 {
					call["id"] = "test-tool"
				} else {
					delete(call, "index")
					call["id"] = "test-tool"
				}
				event := streamTestDelta(Object{"tool_calls": []any{call}})
				for pos := 0; pos < len(event); pos++ {
					if _, e := q.Feed(event[pos : pos+1]); e != nil {
						rejected = true
						break
					}
				}
				if rejected {
					break
				}
			}
			if !rejected {
				t.Fatalf("nested decoded token escaped split=%d", split)
			}
		}
	}
	q, _ := newModelSSEQuarantine("PREFIX-SECRET")
	event := func(s string) []byte {
		return streamTestDelta(Object{"tool_calls": []any{Object{"index": 0, "function": Object{"arguments": s}}}})
	}
	a, b := event(`{"value":"PREFIX-`), event(`different"}`)
	if r, e := q.Feed(a); e != nil || len(r) != 0 {
		t.Fatal("nested suspect prefix escaped", e)
	}
	if r, e := q.Feed(b); e != nil || !bytes.Equal(r, append(a, b...)) {
		t.Fatal("benign tool JSON did not progress before EOF", e)
	}
	// A split escape is held even when there is no decoded prefix yet.
	q, _ = newModelSSEQuarantine("🙂SECRET")
	for i, s := range []string{`{"value":"\ud83d`, `\ude42SECRET"}`} {
		r, e := q.Feed(event(s))
		if len(r) != 0 || i == 0 && e != nil || i == 1 && e == nil {
			t.Fatal("surrogate boundary escaped", i, e)
		}
	}
	q, _ = newModelSSEQuarantine("secret")
	if _, e := q.Feed(event(`{"value":"\u00`)); e != nil {
		t.Fatal(e)
	}
	if _, e := q.Feed([]byte("data: [DONE]\n\n")); e != nil {
		t.Fatal(e)
	}
	if _, _, e := q.Finish(); e == nil {
		t.Fatal("unfinished JSON escape released at EOF")
	}
}
