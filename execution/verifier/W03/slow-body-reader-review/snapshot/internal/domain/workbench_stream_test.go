package domain

import (
	"bufio"
	"context"
	"database/sql"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func workbenchStream(t *testing.T, server *httptest.Server, path, token, cursor string) (*http.Response, context.CancelFunc) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	req, e := http.NewRequestWithContext(ctx, "GET", server.URL+path, nil)
	if e != nil {
		t.Fatal(e)
	}
	req.Header.Set("Authorization", "Bearer "+token)
	if cursor != "" {
		req.Header.Set("Last-Event-ID", cursor)
	}
	res, e := server.Client().Do(req)
	if e != nil {
		cancel()
		t.Fatal(e)
	}
	t.Cleanup(func() { cancel(); res.Body.Close() })
	return res, cancel
}

func workbenchFrame(t *testing.T, reader *bufio.Reader) string {
	t.Helper()
	var frame strings.Builder
	for {
		line, e := reader.ReadString('\n')
		if e != nil {
			t.Fatal(e)
		}
		frame.WriteString(line)
		if line == "\n" {
			return frame.String()
		}
	}
}

func workbenchEventFrame(t *testing.T, frame string) Object {
	t.Helper()
	for _, line := range strings.Split(frame, "\n") {
		if strings.HasPrefix(line, "data: ") {
			o, e := Decode([]byte(strings.TrimPrefix(line, "data: ")))
			if e != nil {
				t.Fatal(e)
			}
			if !strings.Contains(frame, fmt.Sprintf("id: %v\n", o["sequence"])) || !strings.Contains(frame, "event: message\n") {
				t.Fatal("SSE id/event/data mismatch")
			}
			return o
		}
	}
	t.Fatalf("missing data in %q", frame)
	return nil
}

func TestW13EventStream(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	server := httptest.NewServer(f.s.Handler())
	t.Cleanup(server.Close)
	path := f.path("/events/stream")
	initial := f.state()
	res, cancel := workbenchStream(t, server, path, f.token, "")
	defer cancel()
	reader := bufio.NewReader(res.Body)
	connected := workbenchFrame(t, reader)
	if res.StatusCode != 200 || res.Header.Get("Content-Type") != "text/event-stream" {
		t.Fatal(res.StatusCode, res.Header)
	}
	// This read must complete while the SSE connection remains open: SQLite's
	// single connection may not be retained by a long-lived transport request.
	ctx, stop := context.WithTimeout(context.Background(), 2*time.Second)
	request, _ := http.NewRequestWithContext(ctx, "GET", server.URL+f.path("/state"), nil)
	request.Header.Set("Authorization", "Bearer "+f.token)
	stateResponse, e := server.Client().Do(request)
	if e != nil {
		stop()
		t.Fatal(e)
	}
	io.Copy(io.Discard, stateResponse.Body)
	stateResponse.Body.Close()
	stop()
	f.requirement()
	frame := workbenchFrame(t, reader)
	event := workbenchEventFrame(t, frame)
	start, _ := Num(initial, "event_sequence")
	next, _ := Num(event, "sequence")
	workbenchAssert(t, "W13-SSE-FRAME-AND-CONNECTION", []any{200, true, true, true}, []any{stateResponse.StatusCode, connected == ": connected\n\n", next == start+1, next > 0}, Object{"headers": res.Header, "connected": connected, "raw_frame": frame, "initial_sequence": start})
	cancel()
	res.Body.Close()
	replay, cancelReplay := workbenchStream(t, server, path, f.token, fmt.Sprint(start))
	defer cancelReplay()
	rr := bufio.NewReader(replay.Body)
	workbenchFrame(t, rr)
	replayed := workbenchEventFrame(t, workbenchFrame(t, rr))
	workbenchAssert(t, "W13-SSE-RESUME", event, replayed, Object{"last_event_id": start, "at_least_once": true})
	cancelReplay()
	replay.Body.Close()
	current := f.state()
	latest, _ := Num(current, "event_sequence")
	hb, cancelHeartbeat := workbenchStream(t, server, path, f.token, fmt.Sprint(latest))
	defer cancelHeartbeat()
	hr := bufio.NewReader(hb.Body)
	workbenchFrame(t, hr)
	at := time.Now()
	heartbeat := workbenchFrame(t, hr)
	elapsed := time.Since(at)
	workbenchAssert(t, "W13-SSE-HEARTBEAT", []any{true, true, latest}, []any{heartbeat == ": heartbeat\n\n", elapsed >= 14*time.Second && elapsed < 20*time.Second, f.state()["event_sequence"]}, Object{"raw_frame": heartbeat, "elapsed_ms": elapsed.Milliseconds(), "configured_seconds": int(workbenchHeartbeat.Seconds())})
	cancelHeartbeat()
	hb.Body.Close()
	resourceEvidence(t, "sse-frames.json", Object{"connected": connected, "event": frame, "replayed": replayed, "heartbeat": heartbeat, "heartbeat_elapsed_ms": elapsed.Milliseconds()})
}

func TestW13StreamExpiryAndAuthorization(t *testing.T) {
	o := workbenchFixture(t)
	f := o.f
	server := httptest.NewServer(f.s.Handler())
	t.Cleanup(server.Close)
	path := f.path("/events/stream")
	before := f.state()
	sequence, _ := Num(before, "event_sequence")
	// Explicit old, immutable event fixture. The frozen UtcTime schema requires
	// a Z suffix; the transport parses RFC3339Nano rather than comparing text.
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		state, e := singleton(tx, f.project, "ProjectState")
		if e != nil {
			return e
		}
		state["event_sequence"] = sequence + 1
		if e = bump(state); e != nil {
			return e
		}
		if e = f.s.put(tx, "ProjectState", state); e != nil {
			return e
		}
		ev := Object{"id": ID(), "project_id": f.project, "revision": 1, "created_at": time.Now().UTC().Add(-25 * time.Hour).Format(time.RFC3339Nano), "sequence": sequence + 1, "event_type": "PROJECT_UPDATED", "aggregate_ref": Ref(o.req, "Requirement"), "actor_id": f.owner, "correlation_id": ID(), "causation_id": nil, "event_data_artifact_ref": nil}
		ev["receipt_hash"] = Receipt(ev)
		if e = f.s.put(tx, "EventEnvelope", ev); e != nil {
			return e
		}
		if _, e = tx.Exec("INSERT INTO outbox(project,sequence,id,body) VALUES(?,?,?,?)", f.project, sequence+1, ev["id"], string(Bytes(ev))); e != nil {
			return e
		}
		_, e = tx.Exec("INSERT INTO event_state_snapshots(project,event_id,revision,body) VALUES(?,?,?,?)", f.project, ev["id"], state["revision"], string(Bytes(state)))
		return e
	})
	expired, cancelExpired := workbenchStream(t, server, path, f.token, fmt.Sprint(sequence))
	raw, _ := io.ReadAll(expired.Body)
	expired.Body.Close()
	cancelExpired()
	snapshot := f.expect(200, "GET", f.path("/progress"), "", "", nil)
	watermark, _ := Num(snapshot, "as_of_event_sequence")
	stream, cancel := workbenchStream(t, server, path, f.token, fmt.Sprint(watermark))
	reader := bufio.NewReader(stream.Body)
	workbenchFrame(t, reader)
	f.requirement()
	newFrame := workbenchFrame(t, reader)
	newEvent := workbenchEventFrame(t, newFrame)
	newSequence, _ := Num(newEvent, "sequence")
	workbenchAssert(t, "W13-SSE-EXPIRED-SNAPSHOT", []any{410, 200, true, true}, []any{expired.StatusCode, stream.StatusCode, newSequence == watermark+1, strings.Contains(string(raw), "CURSOR_EXPIRED")}, Object{"expired_response": string(raw), "snapshot": snapshot, "new_frame": newFrame, "outbox_history_deleted": false})
	cancel()
	stream.Body.Close()
	for _, cursor := range []string{"-1", "+1", "1.0", "9223372036854775808", fmt.Sprint(watermark + 100)} {
		bad, closeBad := workbenchStream(t, server, path, f.token, cursor)
		if bad.StatusCode != 400 {
			t.Fatalf("cursor %s returned %d", cursor, bad.StatusCode)
		}
		bad.Body.Close()
		closeBad()
	}
	f.switchPrincipal("w13-stream-reader", []string{"READER"})
	token := f.token
	current := f.state()
	currentSequence, _ := Num(current, "event_sequence")
	live, closeLive := workbenchStream(t, server, path, token, fmt.Sprint(currentSequence))
	lr := bufio.NewReader(live.Body)
	workbenchFrame(t, lr)
	if e := f.s.RevokePrincipal(context.Background(), "w13-stream-reader"); e != nil {
		t.Fatal(e)
	}
	_, e := lr.ReadString('\n')
	closeLive()
	live.Body.Close()
	revoked, closeRevoked := workbenchStream(t, server, path, token, fmt.Sprint(currentSequence))
	revoked.Body.Close()
	closeRevoked()
	other, closeOther := workbenchStream(t, server, "/v1/projects/other/events/stream", o.owner, "0")
	other.Body.Close()
	closeOther()
	workbenchAssert(t, "W13-SSE-AUTHORIZATION", []any{true, 401, 404}, []any{e != nil, revoked.StatusCode, other.StatusCode}, Object{"revoked_connection_read_error": fmt.Sprint(e), "malformed_cursors_rejected": 5})
	resourceEvidence(t, "sse-expiry.json", Object{"snapshot": snapshot, "expired_status": expired.StatusCode, "expired_response": string(raw), "next_frame": newFrame})
}
