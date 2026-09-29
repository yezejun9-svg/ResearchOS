package domain

import (
	"context"
	"database/sql"
	"researchos.local/research-os/adapters/sources"
	"testing"
	"time"
)

type sourceFixtureAdapter struct{ page sources.Page }

func (a sourceFixtureAdapter) Fetch(_ context.Context, q sources.Query) (sources.Page, error) {
	p := a.page
	p.RequestedFrom = q.From
	p.RequestedTo = q.To
	return p, nil
}

type neverFetchSource struct{ calls int }

func (a *neverFetchSource) Fetch(context.Context, sources.Query) (sources.Page, error) {
	a.calls++
	return sources.Page{}, nil
}

func sourceProject(t *testing.T) (*fixture, Object, Object) {
	t.Helper()
	f := setup(t)
	sid := ID()
	b := projectBody()
	b["source_configs"] = []any{Object{"source_id": sid, "kind": "GITHUB", "required": true, "enabled": true,
		"query": "repo:paperclipai/paperclip", "allowed_origins": []any{"https://github.com", "https://api.github.com"}, "credential_ref": nil}}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", b)
	f.project = Str(p, "project_id")
	tx, err := f.db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	var cursor Object
	rows, err := tx.Query("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor'", f.project)
	if err != nil {
		t.Fatal(err)
	}
	if !rows.Next() {
		t.Fatal("source cursor was not created")
	}
	var raw string
	if err := rows.Scan(&raw); err != nil {
		t.Fatal(err)
	}
	rows.Close()
	cursor, err = Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	return f, p, cursor
}

func sourceTx(t *testing.T, db *sql.DB, fn func(*sql.Tx) error) {
	t.Helper()
	tx, err := db.Begin()
	if err != nil {
		t.Fatal(err)
	}
	defer tx.Rollback()
	if err := fn(tx); err != nil {
		t.Fatal(err)
	}
	if err := tx.Commit(); err != nil {
		t.Fatal(err)
	}
}

func TestW07EvidenceNeedsSealedLiveSnapshotAndAllowedOrigin(t *testing.T) {
	f, _, cursor := sourceProject(t)
	actor := Principal{ID: "fixture-source"}
	actor.Roles = []string{"SOURCE_ADAPTER"}
	actor.Grants = []Grant{{ProjectID: f.project}}
	if err := f.s.ProvisionPrincipal(context.Background(), actor); err != nil {
		t.Fatal(err)
	}
	bytes := []byte("full public release body")
	var artifact Object
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		u, err := f.s.upload(tx, actor, f.project, bytes)
		if err != nil {
			return err
		}
		artifact, err = f.s.seal(tx, actor, f.project, Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED",
			"measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"],
			"media_type": "text/markdown", "byte_size": len(bytes), "input_refs": []any{Ref(cursor, "SourceCursor")},
			"source_refs": Empty(), "produced_by": actor.ID, "access_class": "PROJECT"})
		return err
	})
	now := Now()
	evidence := Object{"claim": "release describes a public change", "stance": "CONTEXT", "evidence_kind": "OBSERVED",
		"source_kind": "GITHUB", "canonical_url": "https://github.com/paperclipai/paperclip/releases/tag/v2",
		"publisher": "maintainer", "upstream_revision": "0123456789abcdef0123456789abcdef01234567",
		"published_at": now, "modified_at": nil, "retrieved_at": now, "time_status": "KNOWN",
		"snapshot_artifact_ref": Ref(artifact, "Artifact"), "locator": "release.body", "independence_key": Hash("release-22"),
		"origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		bad := Merge(Object{}, evidence)
		bad["canonical_url"] = "https://other.example/release"
		if _, err := f.s.createEvidence(tx, f.project, bad); err == nil {
			t.Fatal("unconfigured origin was accepted")
		}
		bad = Merge(Object{}, evidence)
		bad["snapshot_artifact_ref"] = Object{"entity_type": "Artifact", "id": artifact["id"], "revision": 1, "content_hash": Hash("tampered")}
		if _, err := f.s.createEvidence(tx, f.project, bad); err == nil {
			t.Fatal("tampered hash was accepted")
		}
		_, err := f.s.createEvidence(tx, f.project, evidence)
		return err
	})
	if n := countKind(t, f.db, "Evidence"); n != 1 {
		t.Fatalf("evidence count %d", n)
	}
}

func TestW07CursorDoesNotAdvanceFailedOrUnpersistedWindow(t *testing.T) {
	f, _, cursor := sourceProject(t)
	now := time.Now().UTC()
	covered := now.Add(-time.Minute).Format(time.RFC3339Nano)
	request := Object{"opaque_cursor": "page2", "covered_until": covered, "last_success_at": now.Format(time.RFC3339Nano),
		"retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": nil}
	sourceTx(t, f.db, func(tx *sql.Tx) error {
		if _, err := f.s.advanceSourceCursor(tx, f.project, Str(cursor, "id"), request); err == nil {
			t.Fatal("unpersisted window advanced")
		}
		ratelimited := Merge(Object{}, request)
		ratelimited["retry_after"] = now.Add(time.Minute).Format(time.RFC3339Nano)
		if _, err := f.s.advanceSourceCursor(tx, f.project, Str(cursor, "id"), ratelimited); err == nil {
			t.Fatal("rate-limited window advanced")
		}
		return nil
	})
	var raw string
	if err := f.db.QueryRow("SELECT body FROM domain_objects WHERE project=? AND kind='SourceCursor'", f.project).Scan(&raw); err != nil {
		t.Fatal(err)
	}
	after, err := Decode([]byte(raw))
	if err != nil {
		t.Fatal(err)
	}
	if after["covered_until"] != nil || after["opaque_cursor"] != nil {
		t.Fatalf("failed cursor changed: %v", after)
	}
}

func TestW07HTTPSourceEvidenceAndDurableEmptyWindow(t *testing.T) {
	f, _, cursor := sourceProject(t)
	actor := Principal{ID: "fixture-source-http", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	f.token = token
	// The source actor's HTTP path checks role, grant, body schema, seal,
	// references, and response schema; invalid canonical origins are rejected.
	content := []byte("Full public release body")
	u := f.expect(201, "POST", f.path("/content"), ID(), "", content)
	a := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "text/plain", "byte_size": len(content), "input_refs": []any{Ref(cursor, "SourceCursor")}, "source_refs": Empty(), "produced_by": actor.ID, "access_class": "PROJECT"})
	base := Object{"claim": "release content observed", "stance": "CONTEXT", "evidence_kind": "OBSERVED", "source_kind": "GITHUB", "canonical_url": "https://github.com/paperclipai/paperclip/releases/tag/v1", "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(a, "Artifact"), "locator": "release.body", "independence_key": Hash("release-1"), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil}
	bad := MergeCopy(base, Object{"canonical_url": "https://other.example/release"})
	f.expect(403, "POST", f.path("/evidence"), ID(), f.stateTag(), bad)
	ev := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), base)
	if ev["publisher"] != nil || ev["upstream_revision"] != nil {
		t.Fatal("unknown metadata was invented")
	}
	f.expect(200, "GET", f.path("/evidence/"+Str(ev, "id")), "", "", nil)
	f.expect(200, "GET", f.path("/evidence"), "", "", nil)
	f.expect(200, "GET", f.path("/source-cursors"), "", "", nil)
	f.expect(200, "GET", f.path("/source-cursors/"+Str(cursor, "id")), "", "", nil)
	// A different Evidence does not authorize arbitrary coverage.
	advanceEnabled := false
	for _, op := range f.s.Contracts.Operations {
		if op.ID == "advanceSourceCursor" {
			advanceEnabled = op.Implemented
		}
	}
	from := time.Now().UTC().Add(-2 * time.Hour).Truncate(time.Second)
	to := from.Add(time.Hour)
	advance := Object{"opaque_cursor": nil, "covered_until": to.Format(time.RFC3339Nano), "last_success_at": Now(), "retry_after": nil, "pending_window_from": nil, "pending_window_to": nil, "last_cycle_id": nil}
	if advanceEnabled {
		f.expect(422, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), advance)
	} else {
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			if _, e := f.s.advanceSourceCursor(tx, f.project, Str(cursor, "id"), advance); e == nil {
				t.Fatal("unpersisted window accepted")
			}
			return nil
		})
	}
	config, current, e := f.s.sourceConfig(context.Background(), token, f.project, Str(cursor, "id"))
	if e != nil {
		t.Fatal(e)
	}
	page := sources.Page{RawResponse: []byte("[]"), RawMediaType: "application/json", Complete: true, HTTPStatus: 200, FetchedAt: time.Now().UTC(), RequestURLs: []string{"https://api.github.com/repos/paperclipai/paperclip/releases"}, FinalURLs: []string{"https://api.github.com/repos/paperclipai/paperclip/releases"}}
	eventsBefore := countKind(t, f.db, "EventEnvelope")
	artifactsBefore := countKind(t, f.db, "Artifact")
	got, e := f.s.captureSourcePage(context.Background(), token, f.project, current, config, from, to, 20, sourceFixtureAdapter{page})
	if e != nil || !got.Page.Complete || len(got.Evidence) != 0 || got.RawArtifact == nil {
		t.Fatalf("empty page checkpoint: %+v %v", got, e)
	}
	if got.Manifest == nil || countKind(t, f.db, "EventEnvelope") != eventsBefore+1 {
		t.Fatal("capture event/outbox missing")
	}
	pending, e := f.s.PendingEvents(context.Background(), f.project)
	if e != nil || len(pending) != eventsBefore+1 {
		t.Fatal("capture outbox missing", len(pending), e)
	}
	if _, e = f.s.captureSourcePage(context.Background(), token, f.project, current, config, from, to, 20, sourceFixtureAdapter{page}); e == nil {
		t.Fatal("duplicate page checkpoint accepted")
	}
	if countKind(t, f.db, "EventEnvelope") != eventsBefore+1 || countKind(t, f.db, "Artifact") != artifactsBefore+2 {
		t.Fatal("failed capture left artifacts or events")
	}
	advance["last_success_at"] = Now()
	var advanced Object
	if advanceEnabled {
		advanced = f.expect(200, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), advance)
	} else {
		sourceTx(t, f.db, func(tx *sql.Tx) error {
			var e error
			advanced, e = f.s.advanceSourceCursor(tx, f.project, Str(cursor, "id"), advance)
			return e
		})
	}
	if advanced["covered_until"] != advance["covered_until"] {
		t.Fatal("window not covered", advanced)
	}
	if n := countKind(t, f.db, "Evidence"); n != 1 {
		t.Fatal("fixture evidence count", n)
	}
}

func countKind(t *testing.T, db *sql.DB, kind string) int {
	t.Helper()
	var n int
	if err := db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind=?", kind).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}

func TestW07RetryAfterPreventsPrematureSourceRequest(t *testing.T) {
	f, _, cursor := sourceProject(t)
	actor := Principal{ID: "fixture-source-retry", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	from := time.Now().UTC().Add(-time.Hour)
	to := time.Now().UTC().Add(-time.Minute)
	retry := time.Now().UTC().Add(time.Minute).Format(time.RFC3339Nano)
	body := Object{"opaque_cursor": nil, "covered_until": nil, "last_success_at": nil, "retry_after": retry, "pending_window_from": from.Format(time.RFC3339Nano), "pending_window_to": to.Format(time.RFC3339Nano), "last_cycle_id": nil}
	f.token = token
	updated := f.expect(200, "PUT", f.path("/source-cursors/"+Str(cursor, "id")), ID(), testTag(cursor), body)
	config, current, e := f.s.sourceConfig(context.Background(), token, f.project, Str(cursor, "id"))
	if e != nil {
		t.Fatal(e)
	}
	adapter := &neverFetchSource{}
	result, e := f.s.captureSourcePage(context.Background(), token, f.project, current, config, from, to, 1, adapter)
	if e != nil || result.Page.Failure != "RATE_LIMITED" || result.Page.RetryAfter == nil || adapter.calls != 0 || updated["covered_until"] != nil {
		t.Fatalf("retry guard failed: %+v %v calls=%d", result, e, adapter.calls)
	}
	var n int
	if e = f.db.QueryRow("SELECT count(*) FROM source_pages WHERE project=?", f.project).Scan(&n); e != nil || n != 0 {
		t.Fatal("failed source page persisted", n, e)
	}
}

func TestW07MissingAuthorizedXChannelDoesNotFetch(t *testing.T) {
	f := setup(t)
	sourceID := ID()
	b := projectBody()
	b["source_configs"] = []any{Object{"source_id": sourceID, "kind": "X", "required": true, "enabled": true, "query": "paperclip agents", "allowed_origins": []any{"https://x.com"}, "credential_ref": nil}}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", b)
	f.project = Str(p, "project_id")
	actor := Principal{ID: "fixture-x-source", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	var cursorID string
	e = f.db.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='SourceCursor'", f.project).Scan(&cursorID)
	if e != nil {
		t.Fatal(e)
	}
	from := time.Now().UTC().Add(-time.Hour)
	to := time.Now().UTC().Add(-time.Minute)
	_, e = f.s.CaptureSourcePage(context.Background(), token, f.project, cursorID, from, to, 1, "", "")
	if fault, ok := e.(*Fault); !ok || fault.Status != 503 {
		t.Fatalf("missing authorized browser not classified: %v", e)
	}
	if n := countKind(t, f.db, "Evidence"); n != 0 {
		t.Fatal("missing X channel left evidence", n)
	}
}

func TestW07XVisibleEmptySealsObservationWithoutCoverage(t *testing.T) {
	f := setup(t)
	sourceID := ID()
	b := projectBody()
	b["source_configs"] = []any{Object{"source_id": sourceID, "kind": "X", "required": true, "enabled": true, "query": "paperclip agents", "allowed_origins": []any{"https://x.com"}, "credential_ref": nil}}
	p := f.expect(201, "POST", "/v1/projects", ID(), "", b)
	f.project = Str(p, "project_id")
	actor := Principal{ID: "fixture-x-empty", Roles: []string{"SOURCE_ADAPTER"}, Grants: []Grant{{ProjectID: f.project}}}
	if e := f.s.ProvisionPrincipal(context.Background(), actor); e != nil {
		t.Fatal(e)
	}
	token, e := f.s.IssueCredential(context.Background(), actor.ID, time.Minute)
	if e != nil {
		t.Fatal(e)
	}
	var cursorID string
	if e = f.db.QueryRow("SELECT id FROM domain_objects WHERE project=? AND kind='SourceCursor'", f.project).Scan(&cursorID); e != nil {
		t.Fatal(e)
	}
	config, cursor, e := f.s.sourceConfig(context.Background(), token, f.project, cursorID)
	if e != nil {
		t.Fatal(e)
	}
	from := time.Now().UTC().Add(-time.Hour)
	to := time.Now().UTC().Add(-time.Minute)
	searchURL := "https://x.com/search?q=paperclip"
	raw := []byte(`{"url":"https://x.com/search?q=paperclip","items":[],"empty":true}`)
	page := sources.Page{RawResponse: raw, RawMediaType: "application/json", VisibleEmpty: true, Complete: false, FetchedAt: time.Now().UTC(), RequestURLs: []string{searchURL}, FinalURLs: []string{searchURL}}
	beforeEvents := countKind(t, f.db, "EventEnvelope")
	got, e := f.s.captureSourcePage(context.Background(), token, f.project, cursor, config, from, to, 1, sourceFixtureAdapter{page})
	if e != nil || got.Manifest == nil || got.RawArtifact == nil || len(got.Evidence) != 0 {
		t.Fatalf("valid empty observation rejected: %+v %v", got, e)
	}
	if countKind(t, f.db, "EventEnvelope") != beforeEvents+1 {
		t.Fatal("empty observation event missing")
	}
	var pages int
	if e = f.db.QueryRow("SELECT count(*) FROM source_pages WHERE project=?", f.project).Scan(&pages); e != nil || pages != 0 {
		t.Fatal("visible empty wrongly completed window", pages, e)
	}
	updated := f.expect(200, "GET", f.path("/source-cursors/"+cursorID), "", "", nil)
	if updated["covered_until"] != nil {
		t.Fatal("visible empty advanced coverage")
	}
	bad := page
	bad.RawResponse = []byte(`{"url":"https://x.com/search?q=paperclip","items":[],"empty":false}`)
	if _, e = f.s.captureSourcePage(context.Background(), token, f.project, cursor, config, from, to, 1, sourceFixtureAdapter{bad}); e == nil {
		t.Fatal("unrendered empty accepted")
	}
	if countKind(t, f.db, "EventEnvelope") != beforeEvents+1 {
		t.Fatal("failed empty wrote event")
	}
}
