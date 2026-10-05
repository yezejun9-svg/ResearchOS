package domain

import (
	"bufio"
	"context"
	"database/sql"
	"fmt"
	"net/http/httptest"
	"os"
	"testing"
	"time"
)

// Events enter through the real typed journal, including its schema and CAS gates.
// Only the session mapping and ERROR payload are local fixture inputs.
func mixedSessionEvents(t *testing.T, f *fixture, count int) string {
	t.Helper()
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
	raw, err = os.ReadFile("../api/contracts/client.protocol.schema.json")
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
	sid := ID()
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		now := time.Now().UTC()
		if err := MapClientSession(context.Background(), tx, ClientSession{ID: sid, ProjectID: f.project,
			Revision: 1, WriterEpoch: 1, WriterClientID: "mixed-client", UpstreamSession: ID(),
			CreatedAt: now, UpdatedAt: now, Protocol: ClientSessionProtocol}); err != nil {
			return err
		}
		for i := 1; i <= count; i++ {
			body := Object{"event_id": ID(), "session_id": sid, "sequence": i, "core_build_id": "mixed-fixture",
				"protocol_version": ProtocolV2, "run_id": nil, "command_id": nil, "domain_event_id": nil,
				"kind": "ERROR", "payload": Object{"code": "RESOURCE_BLOCKED", "message": "fixture has no live runtime",
					"retryable": false, "recovery": "RESOLVE_RESOURCE", "current_revision": nil,
					"current_writer_epoch": nil, "resource_request_id": nil, "retry_after_ms": nil, "correlation_id": ID()}}
			ev, err := DecodeEvent(Bytes(body))
			if err != nil {
				return err
			}
			if err = AppendSessionEvent(context.Background(), tx, doc, f.project, ev, 1, int64(i)); err != nil {
				return err
			}
		}
		return nil
	})
	return sid
}

func TestW14MixedOutboxWorkbenchAndProjection(t *testing.T) {
	f := contextFixture(t)
	initial, _ := Num(f.state(), "event_sequence")
	sid := mixedSessionEvents(t, f, 130)
	op := Operation{Roles: []string{"OWNER"}}
	ctx := context.Background()
	if events, head, err := f.s.workbenchEvents(ctx, f.token, f.project, op, -1); err != nil || len(events) != 0 || head != initial+130 {
		t.Fatalf("typed-only head: events=%d head=%d err=%v", len(events), head, err)
	}
	position := initial
	for _, want := range []int64{initial + 128, initial + 130} {
		events, next, err := f.s.workbenchEvents(ctx, f.token, f.project, op, position)
		if err != nil || len(events) != 0 || next != want {
			t.Fatalf("typed page: next=%d want=%d events=%d err=%v", next, want, len(events), err)
		}
		position = next
	}
	// The HTTP stream must cross typed rows and preserve the frozen v1 envelope.
	server := httptest.NewServer(f.s.Handler())
	t.Cleanup(server.Close)
	response, cancel := workbenchStream(t, server, f.path("/events/stream"), f.token, fmt.Sprint(initial))
	defer cancel()
	reader := bufio.NewReader(response.Body)
	if response.StatusCode != 200 || workbenchFrame(t, reader) != ": connected\n\n" {
		t.Fatal("mixed stream unavailable")
	}
	req := f.requirement()
	event := workbenchEventFrame(t, workbenchFrame(t, reader))
	if err := f.s.Contracts.Validate("EventEnvelope", event); err != nil {
		t.Fatal(err)
	}
	sequence, _ := Num(event, "sequence")
	if sequence != initial+131 {
		t.Fatalf("domain global sequence=%d", sequence)
	}
	cancel()
	response.Body.Close()
	var finalHead int64
	if err := f.db.QueryRow("SELECT MAX(sequence) FROM outbox WHERE project=?", f.project).Scan(&finalHead); err != nil {
		t.Fatal(err)
	}
	rows, err := f.db.Query("SELECT id FROM outbox WHERE project=? ORDER BY sequence DESC", f.project)
	if err != nil {
		t.Fatal(err)
	}
	ids := []string{}
	for rows.Next() {
		var id string
		if err = rows.Scan(&id); err != nil {
			t.Fatal(err)
		}
		ids = append(ids, id)
	}
	if err = rows.Err(); err != nil {
		t.Fatal(err)
	}
	rows.Close()
	for _, id := range ids {
		if _, err = f.s.ConsumeEvent(ctx, "mixed-projection", f.project, id); err != nil {
			t.Fatal(err)
		}
	}
	duplicate, err := f.s.ConsumeEvent(ctx, "mixed-projection", f.project, ids[0])
	if err != nil || duplicate["status"] != "DUPLICATE" {
		t.Fatalf("replay: %v %v", duplicate, err)
	}
	var applied, snapshots int64
	if err = f.db.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer=? AND project=?", "mixed-projection", f.project).Scan(&applied); err != nil {
		t.Fatal(err)
	}
	if applied != finalHead {
		t.Fatalf("projection cursor %d != %d", applied, finalHead)
	}
	var projected string
	if err = f.db.QueryRow("SELECT body FROM context_projection WHERE consumer=? AND project=? AND kind='Requirement' AND id=?", "mixed-projection", f.project, req["id"]).Scan(&projected); err != nil {
		t.Fatal(err)
	}
	value, err := Decode([]byte(projected))
	if err != nil || Hash(value) != Hash(req) {
		t.Fatalf("domain projection lost: %v %v", value, err)
	}
	if err = f.db.QueryRow("SELECT count(*) FROM event_state_snapshots WHERE project=?", f.project).Scan(&snapshots); err != nil {
		t.Fatal(err)
	}
	if snapshots != finalHead-130 {
		t.Fatal("typed events fabricated domain snapshots")
	}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		page, err := ReadSessionEvents(ctx, tx, f.project, sid, 0, 200)
		if err == nil && (len(page.Events) != 130 || page.HighWatermark != 130 || page.NextSequence != 130) {
			return fmt.Errorf("session stream changed: %+v", page)
		}
		return err
	})
}

func TestW14MixedOutboxRejectsCorruptEnvelope(t *testing.T) {
	for _, mutation := range []string{"unknown_protocol", "missing_kind", "wrong_id", "unknown_object"} {
		t.Run(mutation, func(t *testing.T) {
			f := contextFixture(t)
			initial, _ := Num(f.state(), "event_sequence")
			mixedSessionEvents(t, f, 1)
			var id, raw string
			if err := f.db.QueryRow("SELECT id,body FROM outbox WHERE project=? AND sequence=?", f.project, initial+1).Scan(&id, &raw); err != nil {
				t.Fatal(err)
			}
			body, _ := Decode([]byte(raw))
			initial++ // The valid event remains immutable; corrupt only a new fixture row.
			id = ID()
			body["event_id"] = id
			body["sequence"] = 2
			switch mutation {
			case "unknown_protocol":
				body["protocol_version"] = "future/99"
			case "missing_kind":
				delete(body, "kind")
			case "wrong_id":
				body["event_id"] = "wrong"
			case "unknown_object":
				body = Object{"unrecognized": true}
			}
			if _, err := f.db.Exec("INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)", f.project, initial+1, id, string(Bytes(body))); err != nil {
				t.Fatal(err)
			}
			if _, _, err := f.s.workbenchEvents(context.Background(), f.token, f.project, Operation{Roles: []string{"OWNER"}}, initial); err == nil {
				t.Fatal("corrupt row silently skipped by stream")
			}
			rows, err := f.db.Query("SELECT id FROM outbox WHERE project=? AND sequence<=? ORDER BY sequence", f.project, initial)
			if err != nil {
				t.Fatal(err)
			}
			ids := []string{}
			for rows.Next() {
				var prior string
				if err = rows.Scan(&prior); err != nil {
					t.Fatal(err)
				}
				ids = append(ids, prior)
			}
			rows.Close()
			for _, prior := range ids {
				if _, err = f.s.ConsumeEvent(context.Background(), "corrupt-projection", f.project, prior); err != nil {
					t.Fatal(err)
				}
			}
			if _, err = f.s.ConsumeEvent(context.Background(), "corrupt-projection", f.project, id); err == nil {
				t.Fatal("corrupt row silently projected")
			}
			var position int64
			if err = f.db.QueryRow("SELECT sequence FROM consumer_positions WHERE consumer=? AND project=?", "corrupt-projection", f.project).Scan(&position); err != nil || position != initial {
				t.Fatalf("corrupt row advanced cursor: %d %v", position, err)
			}
			var inboxRows int
			if err = f.db.QueryRow("SELECT count(*) FROM consumer_inbox WHERE consumer=? AND project=? AND event_id=?", "corrupt-projection", f.project, id).Scan(&inboxRows); err != nil || inboxRows != 0 {
				t.Fatalf("corrupt inbox insert escaped rollback: %d %v", inboxRows, err)
			}
		})
	}
}
