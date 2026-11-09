package domain

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// W06-02: one effective writer per client session, a handoff that cannot overtake a producing writer, and a
// reconnect that admits what it missed.
//
// Seeding disclosure: the v2.4 client_sessions index (internal/domain/v24_sessions.go, accepted W03-01/W03-02)
// requires a domain_objects row of kind 'Project' for its project id, and the accepted contracts check seeds that
// row plus its Run rows itself (tests/contracts/check/main.go:867-869). This file follows the same precedent: the
// project and run rows are seeded through the store, the writer is a real provisioned principal with a real grant
// on that project, and every refusal below comes from the service reading the store, not from a value this file
// handed to the guard. The gap this exposes for a real claimed run is measured as its own id, not smoothed over.

func w0602Seed(t *testing.T, f *fixture) (string, string, string, Principal) {
	t.Helper()
	ctx := context.Background()
	// The shared fixture store is migrated to 0002_domain.sql, which predates the additive v2.4 sessions
	// migration; this test applies the committed migration file itself and then the accepted restore fence, so the
	// epoch trigger it asserts on is the production one rather than a test-local imitation.
	raw, e := os.ReadFile(filepath.Join("..", "..", "migrations", "sqlite", "next_v24_sessions.sql"))
	if e != nil {
		t.Fatalf("read committed v2.4 sessions migration: %v", e)
	}
	if _, e = f.db.ExecContext(ctx, string(raw)); e != nil {
		t.Fatalf("apply committed v2.4 sessions migration: %v", e)
	}
	if e = EnsureClientSessionFence(ctx, f.db); e != nil {
		t.Fatalf("ensure accepted session fence: %v", e)
	}
	project := "w0602-proj-" + ID()
	liveRun := "w0602-run-live-" + ID()
	settledRun := "w0602-run-settled-" + ID()
	must := func(q string, args ...any) {
		if _, e := f.db.ExecContext(ctx, q, args...); e != nil {
			t.Fatalf("seed failed: %v", e)
		}
	}
	must(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Project',?,1,'{}',0)`, project, project)
	must(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Run',?,1,'{"status":"RUNNING","children_stopped":false,"queue_empty":false}',0)`, project, liveRun)
	must(`INSERT INTO domain_objects(project,kind,id,revision,body,immutable) VALUES(?,'Run',?,1,'{"status":"SETTLED","children_stopped":true,"queue_empty":true}',0)`, project, settledRun)
	writerID := "w0602-writer-" + ID()
	if e := f.s.ProvisionPrincipal(ctx, Principal{ID: writerID, Roles: []string{"EXECUTOR"},
		Grants: []Grant{{ProjectID: project}}}); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(ctx, writerID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	defer tx.Rollback()
	p, e := authenticate(tx, token)
	if e != nil {
		t.Fatal(e)
	}
	return project, liveRun, settledRun, p
}

func w0602Count(db *sql.DB, query string, args ...any) int64 {
	var n int64
	if e := db.QueryRowContext(context.Background(), query, args...).Scan(&n); e != nil {
		return -1
	}
	return n
}

func w0602StrPtr(v string) *string {
	if v == "" {
		return nil
	}
	return &v
}

func w0602ErrText(e error) string {
	if e == nil {
		return ""
	}
	return e.Error()
}

func w0602FaultCode(e error) string {
	if f, ok := e.(*Fault); ok {
		return f.Code
	}
	return ""
}

func w0602FaultStatus(e error) any {
	if f, ok := e.(*Fault); ok {
		return f.Status
	}
	return 0
}

func TestW0602SessionSingleWriterHandoff(t *testing.T) {
	ctx := context.Background()
	o := orchestrationSetup(t)
	f := o.f
	project, liveRun, settledRun, writer := w0602Seed(t, f)
	clientA, clientB := "client-alpha-"+ID(), "client-beta-"+ID()
	sessionLive, sessionSettled := "sess-live-"+ID(), "sess-settled-"+ID()
	goal := Str(o.goal, "id")

	liveStatus, liveQuiet, _ := runState(ctx, f.db, project, liveRun)
	settledStatus, settledQuiet, _ := runState(ctx, f.db, project, settledRun)
	probeTask := o.task("index-probe", Empty(), Empty())
	_, _, probeErr := runState(ctx, f.db, f.project, Str(probeTask, "id"))
	fixtureProjectRows := w0602Count(f.db, `SELECT count(*) FROM domain_objects WHERE kind='Project' AND id=?`, f.project)
	orchestrationAssert(t, "W06-02-INDEX-SUBSTRATE-GAP-MEASURED", []any{int64(0), fixtureProjectRows},
		[]any{w0602Count(f.db, `SELECT count(*) FROM domain_objects WHERE kind='Run' AND id=?`, Str(probeTask, "id")), fixtureProjectRows},
		Object{"probe_error": w0602FaultCode(probeErr), "live_run_status": liveStatus, "settled_run_status": settledStatus,
			"client_sessions_schema_source": "applied by this test from migrations/sqlite/next_v24_sessions.sql plus EnsureClientSessionFence",
			"meaning": "a claimed task is not a domain_objects Run row, so the v2.4 client-session index and the mainline " +
				"run store meet only where a Project row exists; recorded as measured, not worked around"})

	openedLive, e := f.s.OpenClientSession(ctx, writer, project, sessionLive, clientA, "upstream-live-1", w0602StrPtr(goal), nil, w0602StrPtr(liveRun))
	orchestrationAssert(t, "W06-02-SESSION-OPENED-WITH-EPOCH-ONE", []any{int64(1), int64(1), clientA, ""},
		[]any{openedLive["writer_epoch"], openedLive["revision"], openedLive["writer_client_id"], w0602ErrText(e)},
		Object{"error": w0602ErrText(e), "opened": openedLive})
	if e != nil {
		t.Fatalf("open live session: %v", e)
	}
	if _, e2 := f.s.OpenClientSession(ctx, writer, project, sessionSettled, clientA, "upstream-settled-1", w0602StrPtr(goal), nil, w0602StrPtr(settledRun)); e2 != nil {
		t.Fatalf("open settled session: %v", e2)
	}

	view, e3 := f.s.AttachClientSession(ctx, writer, project, SessionClaim{SessionID: sessionLive, ClientID: clientB})
	orchestrationAssert(t, "W06-02-READ-ATTACH-CLAIMS-NOTHING", []any{int64(1), clientA, false, ""},
		[]any{view["writer_epoch"], view["writer_client_id"], view["takeover"], w0602ErrText(e3)}, Object{"view": view})

	_, e4 := f.s.AttachClientSession(ctx, writer, project, SessionClaim{SessionID: sessionLive, ClientID: clientB,
		Takeover: true, Reason: "second client wants to write"})
	orchestrationAssert(t, "W06-02-TAKEOVER-REFUSED-WHILE-RUN-LIVE", []any{409, "STOP_CONFIRMATION_REQUIRED", "RUNNING", false},
		[]any{w0602FaultStatus(e4), w0602FaultCode(e4), liveStatus, liveQuiet},
		Object{"message": w0602ErrText(e4)})

	after, e5 := f.s.GetClientSession(ctx, writer, project, sessionLive)
	orchestrationAssert(t, "W06-02-REFUSED-TAKEOVER-LEFT-ONE-WRITER", []any{int64(1), clientA, int64(2), ""},
		[]any{after["writer_epoch"], after["writer_client_id"],
			w0602Count(f.db, `SELECT count(*) FROM client_sessions WHERE project_id=? AND sealed_at IS NULL`, project), w0602ErrText(e5)},
		Object{"after_refusal": after})

	_, e6 := f.s.ConfirmRunStop(ctx, writer, project, liveRun, "w0602-stop-live", "stop-live-key")
	orchestrationAssert(t, "W06-02-STOP-CONFIRM-REFUSED-UNTIL-STORE-SAYS-SETTLED", []any{409, "STOP_UNCONFIRMED"},
		[]any{w0602FaultStatus(e6), w0602FaultCode(e6)},
		Object{"error": w0602ErrText(e6), "run_status": liveStatus})

	confirmed, e7 := f.s.ConfirmRunStop(ctx, writer, project, settledRun, "w0602-stop-settled", "stop-settled-key")
	orchestrationAssert(t, "W06-02-STOP-CONFIRMATION-LANDED-FOR-A-SETTLED-RUN", []any{"COMPLETED", "SETTLED", "", true, true},
		[]any{confirmed["status"], confirmed["run_status"], w0602ErrText(e7), Str(confirmed, "stop_confirmation_ref") != "", settledQuiet},
		Object{"confirmation": confirmed})

	ref, _ := confirmed["stop_confirmation_ref"].(string)
	taken, e8 := f.s.AttachClientSession(ctx, writer, project, SessionClaim{SessionID: sessionSettled, ClientID: clientB,
		Takeover: true, StopConfirmationRef: ref, Reason: "documented transfer"})
	orchestrationAssert(t, "W06-02-TAKEOVER-AFTER-CONFIRMED-STOP-ADVANCES-EPOCH-ONCE", []any{int64(2), clientB, true, int64(1), clientA, ""},
		[]any{taken["writer_epoch"], taken["writer_client_id"], taken["takeover"], taken["from_epoch"], taken["from_client_id"], w0602ErrText(e8)},
		Object{"error": w0602ErrText(e8)})
	if e8 != nil {
		t.Fatalf("takeover after confirmed stop: %v", e8)
	}
	handoffEvents := w0602Count(f.db, `SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.type')='SESSION_HANDOFF'`, project)
	orchestrationAssert(t, "W06-02-HANDOFF-RECORDED-IN-THE-SAME-STREAM", []any{int64(1), clientA},
		[]any{handoffEvents, after["writer_client_id"]},
		Object{"note": "the untouched live session still attributes its writer to clientA; one handoff event exists"})

	_, staleErr := f.s.WriteAsWriter(ctx, writer, project, sessionSettled, clientB, 1, "w0602-write", "old-epoch-key", Object{"text": "old writer returns"})
	orchestrationAssert(t, "W06-02-STALE-EPOCH-WRITE-REFUSED", []any{"STALE_WRITER_EPOCH", 409},
		[]any{w0602FaultCode(staleErr), w0602FaultStatus(staleErr)}, Object{"error": w0602ErrText(staleErr)})

	_, busyErr := f.s.WriteAsWriter(ctx, writer, project, sessionSettled, "client-third-"+ID(), 2, "w0602-write", "other-client-key", Object{"text": "wrong client"})
	orchestrationAssert(t, "W06-02-NON-WRITER-CLIENT-REFUSED", []any{"WRITER_BUSY", 409},
		[]any{w0602FaultCode(busyErr), w0602FaultStatus(busyErr)}, Object{"error": w0602ErrText(busyErr)})

	current, werr := f.s.WriteAsWriter(ctx, writer, project, sessionSettled, clientB, 2, "w0602-write", "charge-key-1", Object{"text": "one command"})
	replay, rerr := f.s.WriteAsWriter(ctx, writer, project, sessionSettled, clientB, 2, "w0602-write", "charge-key-1", Object{"text": "one command"})
	charged := w0602Count(f.db, `SELECT count(*) FROM outbox WHERE project=? AND json_extract(body,'$.idempotency_key')=?`, project, "charge-key-1")
	orchestrationAssert(t, "W06-02-DUPLICATE-COMMAND-CHARGES-ONCE", []any{false, true, int64(1), "", ""},
		[]any{current["replayed"], replay["replayed"], charged, w0602ErrText(werr), w0602ErrText(rerr)},
		Object{"first": current, "replay": replay})

	_, cerr := f.s.WriteAsWriter(ctx, writer, project, sessionSettled, clientB, 2, "w0602-write", "charge-key-1", Object{"text": "different body same key"})
	orchestrationAssert(t, "W06-02-SAME-KEY-DIFFERENT-REQUEST-REFUSED", []any{"IDEMPOTENCY_KEY_REUSED", 409},
		[]any{w0602FaultCode(cerr), w0602FaultStatus(cerr)}, Object{"error": w0602ErrText(cerr)})

	race := "sess-race-" + ID()
	if _, e = f.s.OpenClientSession(ctx, writer, project, race, clientA, "upstream-race-1", w0602StrPtr(goal), nil, nil); e != nil {
		t.Fatal(e)
	}
	var mu sync.Mutex
	landed, refused := 0, []string{}
	landedAs := []string{}
	c1, c2 := "client-race-1-"+ID(), "client-race-2-"+ID()
	var wg sync.WaitGroup
	for _, c := range []string{c1, c2} {
		wg.Add(1)
		go func(clientID string) {
			defer wg.Done()
			res, err := f.s.AttachClientSession(ctx, writer, project, SessionClaim{SessionID: race, ClientID: clientID, Takeover: true})
			mu.Lock()
			defer mu.Unlock()
			if err == nil {
				landed++
				landedAs = append(landedAs, clientID+"@"+fmt.Sprint(res["to_epoch"]))
				return
			}
			refused = append(refused, clientID+":"+w0602FaultCode(err))
		}(c)
	}
	wg.Wait()
	raceRow, _ := f.s.GetClientSession(ctx, writer, project, race)
	finalWriter, _ := raceRow["writer_client_id"].(string)
	other := c1
	if finalWriter == c1 {
		other = c2
	}
	// Whoever did not end up as the writer cannot write, whichever epoch they observed on the way in.
	_, raceWriteErr := f.s.WriteAsWriter(ctx, writer, project, race, other, 1, "w0602-write", "race-loser-key", Object{"text": "lost the race"})
	_, raceWriteErr2 := f.s.WriteAsWriter(ctx, writer, project, race, other, 2, "w0602-write", "race-loser-key-2", Object{"text": "lost the race"})
	// The invariant is no lost update, not "exactly one request succeeded": under real serialization both claims can
	// land in order, and then the epoch advanced exactly once per landing handoff.
	orchestrationAssert(t, "W06-02-CONCURRENT-CLAIMS-NEVER-LOST-AN-UPDATE", []any{2, int64(1+landed), true, true},
		[]any{landed + len(refused), raceRow["writer_epoch"],
			raceRow["writer_epoch"] == int64(1+landed),
			finalWriter == c1 || finalWriter == c2},
		Object{"landed": landed, "landed_as": landedAs, "refused": refused, "race_session": raceRow, "claimants": []string{c1, c2}})
	orchestrationAssert(t, "W06-02-RACE-LOSER-CANNOT-WRITE", []any{"STALE_WRITER_EPOCH", "STALE_WRITER_EPOCH"},
		[]any{w0602FaultCode(raceWriteErr), w0602FaultCode(raceWriteErr2)},
		Object{"final_writer": finalWriter, "loser": other,
			"epochs_tried": []int64{1, 2}, "errors": []string{w0602ErrText(raceWriteErr), w0602ErrText(raceWriteErr2)}})

	regress := func() string {
		tx, e := f.db.BeginTx(ctx, nil)
		if e != nil {
			return w0602ErrText(e)
		}
		defer tx.Rollback()
		if _, e = tx.ExecContext(ctx, `UPDATE client_sessions SET writer_epoch=writer_epoch-1 WHERE id=?`, race); e != nil {
			return w0602ErrText(e)
		}
		return "no error"
	}()
	orchestrationAssert(t, "W06-02-EPOCH-CANNOT-REGRESS", true, strings.Contains(regress, "SESSION_EPOCH_REGRESSION"),
		Object{"direct_sql_error": regress})

	head := w0602Count(f.db, `SELECT COALESCE(max(sequence),0) FROM outbox WHERE project=?`, project)
	page, pe := f.s.SessionEvents(ctx, writer, project, sessionSettled, 0, 2)
	orchestrationAssert(t, "W06-02-RECONNECT-PAGE-REPORTS-ITS-OWN-GAP", []any{true, false, head - 2, 2, ""},
		[]any{page["truncated"], page["complete"], page["missed_events"], len(Arr(page, "events")), w0602ErrText(pe)},
		Object{"head_sequence": head, "from_sequence": page["from_sequence"], "delivered_through": page["delivered_through"]})
	full, fe := f.s.SessionEvents(ctx, writer, project, sessionSettled, 0, 200)
	orchestrationAssert(t, "W06-02-COMPLETENESS-CLAIM-MATCHES-THE-STREAM", []any{false, true, int64(0), head, head, ""},
		[]any{full["truncated"], full["complete"], full["missed_events"], full["head_sequence"], full["delivered_through"], w0602ErrText(fe)},
		Object{"returned": len(Arr(full, "events"))})

	_, aheadErr := f.s.SessionEvents(ctx, writer, project, sessionSettled, head+50, 10)
	orchestrationAssert(t, "W06-02-WATERMARK-AHEAD-OF-STREAM-REFUSED", []any{"STALE_WATERMARK", 409},
		[]any{w0602FaultCode(aheadErr), w0602FaultStatus(aheadErr)}, Object{"asked_after": head + 50, "head": head})

	sharedA, sharedB := "sess-shared-a-"+ID(), "sess-shared-b-"+ID()
	if _, e = f.s.OpenClientSession(ctx, writer, project, sharedA, clientB, "upstream-shared-a", w0602StrPtr(goal), nil, nil); e != nil {
		t.Fatal(e)
	}
	if _, e = f.s.OpenClientSession(ctx, writer, project, sharedB, clientB, "upstream-shared-b", w0602StrPtr(goal), nil, nil); e != nil {
		t.Fatal(e)
	}
	aBefore, _ := f.s.GetClientSession(ctx, writer, project, sharedA)
	bBefore, _ := f.s.GetClientSession(ctx, writer, project, sharedB)
	_, crossErr := f.s.WriteAsWriter(ctx, writer, project, sharedB, clientB, 2, "w0602-write", "cross-epoch-key", Object{"text": "epoch held on the other session"})
	own, ownErr := f.s.WriteAsWriter(ctx, writer, project, sharedB, clientB, 1, "w0602-write", "own-epoch-key", Object{"text": "own epoch"})
	orchestrationAssert(t, "W06-02-SESSIONS-SHARING-A-CLIENT-STAY-INDEPENDENT", []any{int64(1), int64(1), "STALE_WRITER_EPOCH", false, ""},
		[]any{aBefore["writer_epoch"], bBefore["writer_epoch"], w0602FaultCode(crossErr), own["replayed"], w0602ErrText(ownErr)},
		Object{"cross_epoch_refusal": w0602ErrText(crossErr), "session_a": aBefore, "session_b": bBefore})

	strangerID := "w0602-stranger-" + ID()
	if e = f.s.ProvisionPrincipal(ctx, Principal{ID: strangerID, Roles: []string{"VERIFIER"}}); e != nil {
		t.Fatal(e)
	}
	strangerToken, e := f.s.IssueCredential(ctx, strangerID, 15*time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	tx, e := f.db.BeginTx(ctx, nil)
	if e != nil {
		t.Fatal(e)
	}
	noGrant, e := authenticate(tx, strangerToken)
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	_, perr := f.s.GetClientSession(ctx, noGrant, project, sessionSettled)
	orchestrationAssert(t, "W06-02-PRINCIPAL-WITHOUT-GRANT-REFUSED", []any{"FORBIDDEN", 403, false},
		[]any{w0602FaultCode(perr), w0602FaultStatus(perr), noGrant.Allowed(project, "", "", false)},
		Object{"error": w0602ErrText(perr), "roles": noGrant.Roles})

	// Two guards that the round-1 mutation matrix showed were asserted by no id: the grant check on the attach
	// path, and the sealed-session gate on takeover. Each now has a refusal id and a control beside it.
	_, attachNoGrant := f.s.AttachClientSession(ctx, noGrant, project, SessionClaim{SessionID: sessionLive, ClientID: clientA})
	orchestrationAssert(t, "W06-02-ATTACH-BY-PRINCIPAL-WITHOUT-GRANT-REFUSED", []any{"FORBIDDEN", 403, "FORBIDDEN", 403},
		[]any{w0602FaultCode(attachNoGrant), w0602FaultStatus(attachNoGrant), w0602FaultCode(perr), w0602FaultStatus(perr)},
		Object{"attach_error": w0602ErrText(attachNoGrant), "read_error": w0602ErrText(perr),
			"control": "the same stranger principal is refused on read too, so the two refusals share one cause"})
	// The seal runs in its own transaction that is closed before any service call follows, because the store is a
	// single SQLite connection: holding a write transaction open across AttachClientSession deadlocks the run.
	liveRow, _ := f.s.GetClientSession(ctx, writer, project, sessionLive)
	epoch, _ := liveRow["writer_epoch"].(int64)
	rev, _ := liveRow["revision"].(int64)
	sealErr := func() error {
		sTx, e := f.db.BeginTx(ctx, nil)
		if e != nil {
			return e
		}
		if e = Seal(ctx, sTx, sessionLive, epoch, rev); e != nil {
			sTx.Rollback()
			return e
		}
		return sTx.Commit()
	}()
	if sealErr != nil {
		t.Fatalf("seal the live session: %v", sealErr)
	}
	_, sealedTakeover := f.s.AttachClientSession(ctx, writer, project, SessionClaim{SessionID: sessionLive, ClientID: clientB,
		Takeover: true, Reason: "must not overtake a sealed session"})
	sealedRow, _ := f.s.GetClientSession(ctx, writer, project, sessionLive)
	orchestrationAssert(t, "W06-02-TAKEOVER-OF-SEALED-SESSION-REFUSED", []any{"SESSION_SEALED", 409, true, int64(1)},
		[]any{w0602FaultCode(sealedTakeover), w0602FaultStatus(sealedTakeover), sealedRow["sealed"], sealedRow["writer_epoch"]},
		Object{"seal_error": w0602ErrText(sealErr), "takeover_error": w0602ErrText(sealedTakeover),
			"control_row": liveRow})

	list, le := f.s.ListClientSessions(ctx, writer, project, 3)
	// The page must cap at the requested size AND say there is more, rather than reporting a short page as the whole set.
	totalSessions := w0602Count(f.db, `SELECT count(*) FROM client_sessions WHERE project_id=?`, project)
	orchestrationAssert(t, "W06-02-LIST-IS-BOUNDED-AND-HONEST", []any{3, true, true, true, ""},
		[]any{list["count"], list["has_more"], len(Arr(list, "sessions")) == 3, int64(len(Arr(list, "sessions"))) < totalSessions, w0602ErrText(le)},
		Object{"listed": list["sessions"], "total_sessions": totalSessions,
			"note": "the page returns three of the sessions that exist and reports has_more; a short page is never presented as the whole set"})
}
