package domain

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func w09LocalEvidence(t *testing.T, f *fixture, rootID, rel, text string) (Object, Object) {
	t.Helper()
	a, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, rel)
	if err != nil {
		t.Fatal(err)
	}
	ev := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), Object{"claim": "Observed local fixture: " + rel, "stance": "CONTEXT", "evidence_kind": "OBSERVED", "source_kind": "LOCAL", "canonical_url": nil, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(a, "Artifact"), "locator": rel, "independence_key": Hash(rel), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil})
	if text != "" {
		t.Logf("sealed %s as %s", rel, a["content_hash"])
	}
	return a, ev
}

func TestW09A06HTTPInvalidationAndContext(t *testing.T) {
	f := contextFixture(t)
	base := t.TempDir()
	aRoot := filepath.Join(base, "A")
	bRoot := filepath.Join(base, "B")
	for _, dir := range []string{aRoot, bRoot} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(aRoot, "same.txt"), []byte("alpha current v1"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(bRoot, "same.txt"), []byte("SECRET-B-UNAUTHORIZED"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, aRoot)
	if err != nil {
		t.Fatal(err)
	}
	artifact, evidence := w09LocalEvidence(t, f, rootID, "same.txt", "alpha current v1")
	for _, escape := range []string{"../B/same.txt", filepath.Join(bRoot, "same.txt")} {
		if _, err = f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, escape); err == nil {
			t.Fatal("escaped root", escape)
		}
	}
	state := f.state()
	query := Object{"query": "alpha", "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	key := ID()
	initial := f.expect(200, "POST", f.path("/search"), key, "", query)
	if len(Arr(initial, "hits")) != 1 || strings.Contains(string(Bytes(initial)), "SECRET-B-UNAUTHORIZED") {
		t.Fatal("initial search leak", initial)
	}
	if got := f.expect(200, "POST", f.path("/search"), key, "", query); len(Arr(got, "hits")) != 1 {
		t.Fatal("repeat search", got)
	}
	bad := MergeCopy(query, Object{"query": "different"})
	f.expect(409, "POST", f.path("/search"), key, "", bad)
	req := f.requirement()
	task := f.task(req, Empty(), "retrieval-task")
	bundle := f.bundle(task)
	if !containsSnapshot(Arr(bundle, "authorized_snapshot_ids"), Str(artifact, "id")) {
		t.Fatal("current snapshot absent from bundle")
	}
	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "materialized-v1")); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(aRoot, "same.txt"), []byte("beta changed v2"), 0600); err != nil {
		t.Fatal(err)
	}
	// Even before the maintenance projection, the old key must not replay v1.
	state = f.state()
	query["expected_state_revision"] = state["revision"]
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", query); len(Arr(got, "hits")) != 0 || strings.Contains(string(Bytes(got)), "alpha current v1") {
		t.Fatal("stale bytes escaped", got)
	}
	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "stale-context")); err == nil {
		t.Fatal("old context materialized changed bytes")
	}
	changed, err := f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project)
	if err != nil || changed != 1 {
		t.Fatal("refresh", changed, err)
	}
	if got := f.read("artifacts", Str(artifact, "id")); got["validity"] != "STALE" {
		t.Fatal("artifact not stale", got)
	}
	if got := f.read("evidence", Str(evidence, "id")); got["validity"] != "STALE" {
		t.Fatal("evidence not stale", got)
	}
	f.expect(412, "POST", f.path("/search"), ID(), "", query)
	newArtifact, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt")
	if err != nil {
		t.Fatal(err)
	}
	if newArtifact["content_hash"] == artifact["content_hash"] {
		t.Fatal("unchanged hash after edit")
	}
	if err = f.s.RevokeLocalRoot(context.Background(), f.token, f.project, rootID); err != nil {
		t.Fatal(err)
	}
	if got := f.read("artifacts", Str(newArtifact, "id")); got["validity"] != "REVOKED" {
		t.Fatal("revocation not projected", got)
	}
	state = f.state()
	query = Object{"query": "beta", "snapshot_ids": []any{newArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", query); len(Arr(got, "hits")) != 0 {
		t.Fatal("revoked source returned", got)
	}
}
