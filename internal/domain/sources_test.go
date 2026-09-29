package domain

import (
	"context"
	"database/sql"
	"testing"
	"time"
)

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

func countKind(t *testing.T, db *sql.DB, kind string) int {
	t.Helper()
	var n int
	if err := db.QueryRow("SELECT count(*) FROM domain_objects WHERE kind=?", kind).Scan(&n); err != nil {
		t.Fatal(err)
	}
	return n
}
