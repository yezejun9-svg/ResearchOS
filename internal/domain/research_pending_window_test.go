package domain

import (
	"researchos.local/research-os/internal/store"
	"testing"
	"time"
)

func TestW0802PendingWindowsCoalesceAcrossRestart(t *testing.T) {
	r := researchSetup(t, false)
	now := time.Now().UTC().Truncate(time.Second)
	first := r.start(t, now.Add(-19*time.Hour))
	r.f.token = r.owner
	profile := r.f.expect(200, "GET", r.f.path("/profile"), "", "", nil)
	request := func(from, to time.Time) {
		t.Helper()
		body := Object{"trigger": "SCHEDULE", "window_from": from.Format(time.RFC3339Nano), "window_to": to.Format(time.RFC3339Nano), "profile_revision": profile["revision"]}
		key, tag := ID(), r.f.stateTag()
		conflict := r.f.expect(409, "POST", r.f.path("/research-cycles"), key, tag, body)
		if conflict["code"] != "STATE_CONFLICT" || len(Arr(conflict, "details")) == 0 {
			t.Fatalf("active cycle conflict omitted current-cycle details: %v", conflict)
		}
		status, replay, headers := r.f.request("POST", r.f.path("/research-cycles"), key, tag, body)
		if status != 409 || headers.Get("Idempotency-Replayed") != "true" || Hash(replay) != Hash(conflict) {
			t.Fatalf("coalesced conflict did not replay atomically: %d %v %v", status, replay, headers)
		}
	}
	activeEnd, e := time.Parse(time.RFC3339Nano, Str(first, "window_to"))
	if e != nil {
		t.Fatal(e)
	}
	request(activeEnd, now.Add(-12*time.Hour))
	request(activeEnd, now.Add(-5*time.Hour))
	var active, from, to string
	var n int
	if e := r.f.db.QueryRow("SELECT active_cycle,window_from,window_to FROM research_pending_windows WHERE project=?", r.f.project).Scan(&active, &from, &to); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "W08-02-PENDING-MERGE", []any{first["id"], first["window_to"], now.Add(-5 * time.Hour).Format(time.RFC3339Nano)}, []any{active, from, to})
	activeStart, e := time.Parse(time.RFC3339Nano, Str(first, "window_from"))
	if e != nil {
		t.Fatal(e)
	}
	prefix := activeStart.Add(-2 * time.Hour).Format(time.RFC3339Nano)
	request(activeStart.Add(-2*time.Hour), activeStart.Add(time.Hour))
	if e = r.f.db.QueryRow("SELECT window_from,window_to FROM research_pending_windows WHERE project=?", r.f.project).Scan(&from, &to); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "W08-02-OLDER-PREFIX", []any{prefix, now.Add(-5 * time.Hour).Format(time.RFC3339Nano)}, []any{from, to})
	if e := r.f.db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", r.f.project).Scan(&n); e != nil || n != 1 {
		t.Fatalf("active cycle count changed: %d %v", n, e)
	}
	current := r.f.read("research-cycles", Str(first, "id"))
	if current["window_from"] != first["window_from"] || current["window_to"] != first["window_to"] {
		t.Fatalf("queued trigger changed the active cycle's frozen window: %v", current)
	}
	r.checkpoint(t, Empty(), Empty())
	tx, e := r.f.db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	manualFacts, e := r.f.s.researchCycleFacts(tx, r.f.project, r.cycle, nil)
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	origin, _ := manualFacts["origin"].(map[string]any)
	continuation, _ := manualFacts["continuation"].(map[string]any)
	if origin["intent"] == "" || continuation["mode"] != "FINITE_CYCLE" || len(Arr(continuation, "next_review_conditions")) == 0 {
		t.Fatalf("manual cycle omitted finite intent or next review: %v %v", origin, continuation)
	}
	r.close(t, "BLOCKED")
	var seq int
	var name, dbPath string
	if e := r.f.db.QueryRow("PRAGMA database_list").Scan(&seq, &name, &dbPath); e != nil {
		t.Fatal(e)
	}
	if e := r.f.db.Close(); e != nil {
		t.Fatal(e)
	}
	db, e := store.Open(dbPath)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(func() { db.Close() })
	s, e := New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")
	if e != nil {
		t.Fatal(e)
	}
	r.f.db, r.f.s, r.f.h = db, s, s.Handler()
	tx, e = db.Begin()
	if e != nil {
		t.Fatal(e)
	}
	closed, e := load(tx, r.f.project, "ResearchCycle", Str(first, "id"))
	if e == nil {
		var restored Object
		restored, e = s.researchCycleFacts(tx, r.f.project, closed, nil)
		if e == nil && (Hash(restored["origin"]) != Hash(origin) || Hash(restored["continuation"]) != Hash(continuation)) {
			e = Fail(500, "TEST_MISMATCH", "manual continuation changed across close and restart")
		}
	}
	tx.Rollback()
	if e != nil {
		t.Fatal(e)
	}
	if e = db.QueryRow("SELECT window_from,window_to FROM research_pending_windows WHERE project=?", r.f.project).Scan(&from, &to); e != nil {
		t.Fatal(e)
	}
	researchAssert(t, "W08-02-RESTART-PENDING", []any{prefix, now.Add(-5 * time.Hour).Format(time.RFC3339Nano)}, []any{from, to})
	r.f.token = r.owner
	next := r.f.expect(201, "POST", r.f.path("/research-cycles"), ID(), r.f.stateTag(), Object{
		"trigger": "SCHEDULE", "window_from": first["window_to"], "window_to": now.Add(-11 * time.Hour).Format(time.RFC3339Nano), "profile_revision": profile["revision"]})
	researchAssert(t, "W08-02-CONSUMED-WINDOW", []any{prefix, now.Add(-5 * time.Hour).Format(time.RFC3339Nano)}, []any{next["window_from"], next["window_to"]})
	if e = db.QueryRow("SELECT count(*) FROM research_pending_windows WHERE project=?", r.f.project).Scan(&n); e != nil || n != 0 {
		t.Fatalf("pending row not consumed: %d %v", n, e)
	}
	if e = db.QueryRow("SELECT count(*) FROM domain_objects WHERE project=? AND kind='ResearchCycle'", r.f.project).Scan(&n); e != nil || n != 2 {
		t.Fatalf("missed ticks created multiple cycles: %d %v", n, e)
	}
}
