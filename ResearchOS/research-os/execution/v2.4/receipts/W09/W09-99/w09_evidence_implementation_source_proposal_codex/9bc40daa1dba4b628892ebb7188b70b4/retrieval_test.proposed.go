package domain

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"researchos.local/research-os/internal/store"
	"runtime"
	"strings"
	"testing"
)

func w09Assertion(t *testing.T, id string, evidence Object) {
	t.Helper()
	value := Object{"assertion_id": id, "status": "PASS", "evidence": evidence}
	if pin := w09ExportEvent(t, "assertion-"+id, Object{"assertion_id": id, "expected": w09Expected(id), "actual": evidence, "status": "PASS"}); pin != nil { value["owned_export_ref"] = pin }
	line, _ := json.Marshal(value)
	fmt.Println("W09_ASSERTION " + string(line))
}

func w09LocalEvidence(t *testing.T, f *fixture, rootID, rel, claim string, sourceKind ...string) (Object, Object) {
	t.Helper()
	a, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, rel)
	if err != nil {
		t.Fatal(err)
	}
	kind := "LOCAL"
	if len(sourceKind) > 0 {
		kind = sourceKind[0]
	}
	ev := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), Object{"claim": claim, "stance": "SUPPORT", "evidence_kind": "OBSERVED", "source_kind": kind, "canonical_url": "https://fixture.example/" + rel, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(a, "Artifact"), "locator": rel, "independence_key": Hash(rel), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil})
	if claim != "" {
		t.Logf("sealed %s as %s", rel, a["content_hash"])
	}
	return a, ev
}

func TestW09C19ExplicitOriginAndUnknown(t *testing.T) {
	f := contextFixture(t)
	rootPath := t.TempDir()
	write := func(rel, body string) {
		t.Helper()
		if err := os.WriteFile(filepath.Join(rootPath, rel), []byte(body), 0600); err != nil {
			t.Fatal(err)
		}
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	const expectedDigest = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
	claim := "SHA-256 of abc is " + expectedDigest
	write("original.txt", "Primary repository statement: "+claim)
	first, original := w09LocalEvidence(t, f, rootID, "original.txt", claim)
	if err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(original, "id"), "", Str(first, "id"), rootID, "original.txt"); err != nil {
		t.Fatal(err)
	}
	actualDigest := fmt.Sprintf("%x", sha256.Sum256([]byte("abc")))
	if actualDigest != expectedDigest {
		t.Fatal("independent measurement contradicted primary claim")
	}
	write("experiment.txt", "Independent standard-library measurement, input=abc, SHA-256="+actualDigest)
	second, experiment := w09LocalEvidence(t, f, rootID, "experiment.txt", claim, "EXPERIMENT")
	if err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(experiment, "id"), "", Str(second, "id"), rootID, "experiment.txt"); err != nil {
		t.Fatal(err)
	}
	ids := []string{Str(original, "id"), Str(experiment, "id")}
	for i := 0; i < 4; i++ {
		rel := fmt.Sprintf("repost-%d.txt", i)
		write(rel, fmt.Sprintf("The same claim was reposted at https://fixture.example/%s on day %d; source https://fixture.example/original.txt", rel, i))
		a, ev := w09LocalEvidence(t, f, rootID, rel, claim)
		if err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(ev, "id"), Str(original, "id"), Str(a, "id"), rootID, rel); err != nil {
			t.Fatal(err)
		}
		current := f.read("evidence", Str(ev, "id"))
		if current["origin_evidence_id"] != original["id"] {
			t.Fatal("repost lost explicit source", current)
		}
		ids = append(ids, Str(ev, "id"))
	}
	// An exact copy at a new URL shares canonical bytes but remains UNKNOWN until
	// an explicit, reviewable source relationship is recorded.
	write("unknown.txt", "Primary repository statement: "+claim)
	copyArtifact, unknown := w09LocalEvidence(t, f, rootID, "unknown.txt", claim)
	if copyArtifact["id"] != first["id"] {
		t.Fatal("same source bytes were duplicated")
	}
	ids = append(ids, Str(unknown, "id"))
	for i := 0; i < 20; i++ {
		text := []byte(fmt.Sprintf("simulated agent opinion %d", i))
		w09ExportRaw(t, fmt.Sprintf("simulated-opinion-%02d", i), text)
		u := f.expect(201, "POST", f.path("/content"), ID(), "", text)
		a := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": u["content_hash"], "storage_key": u["storage_key"], "media_type": "text/plain", "byte_size": len(text), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
		ev := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), Object{"claim": claim, "stance": "SUPPORT", "evidence_kind": "SIMULATED", "source_kind": "SIMULATION", "canonical_url": nil, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": Ref(a, "Artifact"), "locator": fmt.Sprintf("opinion-%d", i), "independence_key": Hash(fmt.Sprintf("simulation-%d", i)), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil})
		ids = append(ids, Str(ev, "id"))
	}
	summary, err := f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, ids)
	if err != nil {
		t.Fatal(err)
	}
	if summary["independent_observed_count"] != 2 || summary["simulated_count"] != 20 || summary["unknown_count"] != 1 || len(Arr(summary, "records")) != 27 {
		t.Fatal("incorrect independent support", summary)
	}
	w09ExportEvent(t, "c19-complete-graph-before", Object{"records": summary["records"], "counts": summary, "evidence_ids": ids, "root_id": rootID})
	w09ExportOriginRows(t, f, "c19-before")
	for _, name := range []string{"original.txt", "experiment.txt", "repost-0.txt", "repost-1.txt", "repost-2.txt", "repost-3.txt", "unknown.txt"} { w09ExportFile(t, "c19-before-"+name, filepath.Join(rootPath, name), rootID) }
	w09ExportState(t, f, "c19-before", rootID)
	if err = f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(unknown, "id"), Str(original, "id"), Str(copyArtifact, "id"), rootID, "unknown.txt"); err == nil {
		t.Fatal("same-content body without explicit source citation was falsely linked")
	}
	w09ExportEvent(t, "c19-unsupported-relation-rejection", Object{"unknown_id": unknown["id"], "proposed_origin_id": original["id"], "actual_error": err.Error()})
	w09Assertion(t, "C19-01", Object{"reposts": 4, "retained_records": len(Arr(summary, "records")), "explicit_origin_id": original["id"]})
	w09Assertion(t, "C19-02", Object{"reviewed_independent_roots": summary["independent_observed_count"], "simulated": summary["simulated_count"], "experiment_source_kind": "EXPERIMENT"})
	w09Assertion(t, "C19-03", Object{"unknown": summary["unknown_count"], "same_bytes": copyArtifact["id"] == first["id"], "unsupported_relation_rejected": true})
	write("original.txt", "primary statement withdrawn")
	summary, err = f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, ids)
	if err != nil || summary["independent_observed_count"] != 1 || summary["unknown_count"] != 6 || len(Arr(summary, "records")) != 27 {
		t.Fatal("invalidated primary still counted", err, summary)
	}
	w09ExportFile(t, "c19-primary-changed", filepath.Join(rootPath, "original.txt"), rootID)
	w09ExportEvent(t, "c19-complete-graph-after", Object{"records": summary["records"], "counts": summary, "evidence_ids": ids, "root_id": rootID})
	w09ExportOriginRows(t, f, "c19-after")
	w09ExportState(t, f, "c19-after", rootID)
	w09Assertion(t, "C19-04", Object{"primary_changed": true, "remaining_independent_roots": 1, "retained_records": 27})
}

func TestW09C19ChainInvalidation(t *testing.T) {
	f := contextFixture(t)
	rootPath := t.TempDir()
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	add := func(name, parent string) (Object, Object) {
		t.Helper()
		body := name
		if parent != "" {
			body += " cites https://fixture.example/" + parent
		}
		if e := os.WriteFile(filepath.Join(rootPath, name), []byte(body), 0600); e != nil {
			t.Fatal(e)
		}
		return w09LocalEvidence(t, f, rootID, name, "reviewed source chain")
	}
	annotate := func(a, ev Object, parent, name string) error {
		return f.s.RecordEvidenceOrigin(context.Background(), f.token, f.project, Str(ev, "id"), parent, Str(a, "id"), rootID, name)
	}
	a, primary := add("primary.txt", "")
	if err = annotate(a, primary, "", "primary.txt"); err != nil {
		t.Fatal(err)
	}
	a, middle := add("middle.txt", "primary.txt")
	if err = annotate(a, middle, Str(primary, "id"), "middle.txt"); err != nil {
		t.Fatal(err)
	}
	a, leaf := add("leaf.txt", "middle.txt")
	if err = annotate(a, leaf, Str(middle, "id"), "leaf.txt"); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"primary.txt", "middle.txt", "leaf.txt"} { w09ExportFile(t, "chain-before-"+name, filepath.Join(rootPath, name), rootID) }
	w09ExportOriginRows(t, f, "chain-before")
	before, err := f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, []string{Str(leaf, "id")})
	if err != nil || before["independent_observed_count"] != 1 {
		t.Fatal("valid chain unavailable", err, before)
	}
	if err = os.Remove(filepath.Join(rootPath, "middle.txt")); err != nil {
		t.Fatal(err)
	}
	after, err := f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, []string{Str(leaf, "id")})
	if err != nil || after["independent_observed_count"] != 0 || after["unknown_count"] != 1 {
		t.Fatal("unavailable intermediate still counted before refresh", err, after)
	}
	a, later := add("later.txt", "leaf.txt")
	if err = annotate(a, later, Str(leaf, "id"), "later.txt"); err == nil {
		t.Fatal("new annotation traversed invalid intermediate")
	}
	if _, err = f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project); err != nil {
		t.Fatal(err)
	}
	after, err = f.s.EvidenceSupportSummary(context.Background(), f.token, f.project, []string{Str(leaf, "id")})
	if err != nil || after["independent_observed_count"] != 0 || after["unknown_count"] != 1 {
		t.Fatal("stale intermediate still counted after refresh", err, after)
	}
	w09ExportFile(t, "chain-middle-removed", filepath.Join(rootPath, "middle.txt"), rootID)
	w09ExportEvent(t, "chain-before-after", Object{"before": before, "after": after, "primary_id": primary["id"], "middle_id": middle["id"], "leaf_id": leaf["id"]})
	w09ExportOriginRows(t, f, "chain-after")
	w09ExportState(t, f, "chain-after", rootID)
	w09Assertion(t, "C19-05", Object{"before": before, "after": after, "new_relation_rejected": true, "intermediate_validity": f.read("evidence", Str(middle, "id"))["validity"]})
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
	w09ExportFile(t, "a06-initial-authorized", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportFile(t, "a06-initial-denied", filepath.Join(bRoot, "same.txt"), "")
	w09ExportState(t, f, "a06-before-capture", rootID)
	artifact, evidence := w09LocalEvidence(t, f, rootID, "same.txt", "alpha current v1")
	for _, escape := range []string{"../B/same.txt", filepath.Join(bRoot, "same.txt")} {
		if _, err = f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, escape); err == nil {
			t.Fatal("escaped root", escape)
		}
		w09ExportEvent(t, "a06-escape-rejection", Object{"attempted_path": escape, "actual_error": err.Error(), "accepted": false})
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
	w09ExportFile(t, "a06-modified", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportState(t, f, "a06-modified-before-refresh", rootID)
	// Even before the maintenance projection, the old key must not replay v1.
	if code, reply, _ := f.request("POST", f.path("/search"), key, "", query); code != 412 || strings.Contains(string(Bytes(reply)), "alpha current v1") {
		t.Fatal("old idempotency body replayed", code, reply)
	}
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
	if err = os.Rename(filepath.Join(aRoot, "same.txt"), filepath.Join(bRoot, "moved-out.txt")); err != nil {
		t.Fatal(err)
	}
	w09ExportFile(t, "a06-moved-source-absent", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportFile(t, "a06-moved-destination", filepath.Join(bRoot, "moved-out.txt"), "")
	w09ExportState(t, f, "a06-moved-before-refresh", rootID)
	state = f.state()
	moveQuery := Object{"query": "beta", "snapshot_ids": []any{newArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", moveQuery); len(Arr(got, "hits")) != 0 {
		t.Fatal("moved-out source returned", got)
	}
	changed, err = f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project)
	if err != nil || changed != 1 {
		t.Fatal("move refresh", changed, err)
	}
	if err = os.WriteFile(filepath.Join(aRoot, "same.txt"), []byte("gamma deleted v3"), 0600); err != nil {
		t.Fatal(err)
	}
	deletedArtifact, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt")
	if err != nil {
		t.Fatal(err)
	}
	if err = os.Remove(filepath.Join(aRoot, "same.txt")); err != nil {
		t.Fatal(err)
	}
	w09ExportFile(t, "a06-deleted", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportState(t, f, "a06-deleted-before-refresh", rootID)
	state = f.state()
	deleteQuery := Object{"query": "gamma", "snapshot_ids": []any{deletedArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", deleteQuery); len(Arr(got, "hits")) != 0 {
		t.Fatal("deleted source returned", got)
	}
	changed, err = f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project)
	if err != nil || changed != 1 {
		t.Fatal("delete refresh", changed, err)
	}
	newBundle := f.bundle(task)
	if containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(artifact, "id")) || containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(deletedArtifact, "id")) {
		t.Fatal("new context retained invalid snapshots", newBundle)
	}
	manifest, err := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "materialized-after-delete"))
	if err != nil || strings.Contains(string(Bytes(manifest)), "gamma deleted v3") {
		t.Fatal("invalid body materialized", err, manifest)
	}
	if err = os.WriteFile(filepath.Join(aRoot, "same.txt"), []byte("delta for revocation v4"), 0600); err != nil {
		t.Fatal(err)
	}
	newArtifact, err = f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt")
	if err != nil {
		t.Fatal(err)
	}
	if err = f.s.RevokeLocalRoot(context.Background(), f.token, f.project, rootID); err != nil {
		t.Fatal(err)
	}
	if got := f.read("artifacts", Str(newArtifact, "id")); got["validity"] != "REVOKED" {
		t.Fatal("revocation not projected", got)
	}
	state = f.state()
	query = Object{"query": "delta", "snapshot_ids": []any{newArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", query); len(Arr(got, "hits")) != 0 {
		t.Fatal("revoked source returned", got)
	}
	w09ExportFile(t, "a06-revoked-body", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportState(t, f, "a06-revoked", rootID)
	w09Assertion(t, "A06-01", Object{"modified_stale": true, "moved_stale": true, "deleted_stale": true, "revoked": true, "new_bundle_excludes_old": true, "old_materialization_rejected": true})
	w09Assertion(t, "A06-02", Object{"http_path_traversal_rejected": true, "secret_marker_leaks": 0})
}

func TestW09A06FTSFallbackAndDuplicatePath(t *testing.T) {
	f := contextFixture(t)
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "nested"), 0700); err != nil {
		t.Fatal(err)
	}
	for path, body := range map[string]string{"same.txt": "needle first locator", "nested/same.txt": "needle second locator"} {
		full := filepath.Join(root, filepath.FromSlash(path))
		if err := os.WriteFile(full, []byte(body), 0600); err != nil {
			t.Fatal(err)
		}
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, root)
	if err != nil {
		t.Fatal(err)
	}
	first, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt")
	if err != nil {
		t.Fatal(err)
	}
	second, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, filepath.Join("nested", "same.txt"))
	if err != nil {
		t.Fatal(err)
	}
	w09ExportFile(t, "a06-fts-file-1", filepath.Join(root, "same.txt"), rootID)
	w09ExportFile(t, "a06-fts-file-2", filepath.Join(root, "nested", "same.txt"), rootID)
	if first["id"] == second["id"] {
		t.Fatal("different same-named files collapsed")
	}
	state := f.state()
	request := Object{"query": "needle", "snapshot_ids": []any{first["id"], second["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	indexed := f.expect(200, "POST", f.path("/search"), ID(), "", request)
	if len(Arr(indexed, "hits")) != 2 {
		t.Fatal("FTS failed", indexed)
	}
	for _, raw := range Arr(indexed, "hits") {
		if raw.(map[string]any)["backend"] != "sqlite-fts5" {
			t.Fatal("FTS path not exercised", raw)
		}
	}
	w09ExportEvent(t, "a06-indexed-result", Object{"result": indexed, "first_artifact": first, "second_artifact": second})
	w09ExportState(t, f, "a06-fts-indexed", rootID)
	if _, err = f.db.Exec("DROP TABLE retrieval_fts"); err != nil {
		t.Fatal(err)
	}
	fallback := f.expect(200, "POST", f.path("/search"), ID(), "", request)
	if len(Arr(fallback, "hits")) != 2 {
		t.Fatal("fallback lost authorized results", fallback)
	}
	for _, raw := range Arr(fallback, "hits") {
		if raw.(map[string]any)["backend"] != "bounded-scan" {
			t.Fatal("candidate failure did not fall back", raw)
		}
	}
	w09ExportEvent(t, "a06-fallback-result", Object{"result": fallback, "retrieval_fts_table_dropped": true})
	w09ExportState(t, f, "a06-fts-fallback", rootID)
	w09Assertion(t, "A06-03", Object{"indexed_hits": 2, "fallback_hits": 2, "backend": "bounded-scan", "same_named_paths_distinct": first["id"] != second["id"]})
}

func TestW09UnicodeLocator(t *testing.T) {
	f := contextFixture(t)
	root := t.TempDir()
	if err := os.WriteFile(filepath.Join(root, "unicode.txt"), []byte("İ\nneedle\n中文检索"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, root)
	if err != nil {
		t.Fatal(err)
	}
	a, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "unicode.txt")
	if err != nil {
		t.Fatal(err)
	}
	state := f.state()
	query := Object{"query": "needle", "snapshot_ids": []any{a["id"]}, "limit": 1, "expected_state_revision": state["revision"]}
	result := f.expect(200, "POST", f.path("/search"), ID(), "", query)
	hits := Arr(result, "hits")
	if len(hits) != 1 || hits[0].(map[string]any)["locator"] != "line:2" || !strings.Contains(Str(hits[0].(map[string]any), "excerpt"), "needle") {
		t.Fatal("casefold changed source byte offset", result)
	}
	w09ExportFile(t, "g02-unicode-input", filepath.Join(root, "unicode.txt"), rootID)
	w09ExportState(t, f, "g02-unicode", rootID)
	w09Assertion(t, "W09-G02-UNICODE-LOCATOR", Object{"locator": "line:2", "content_hash": a["content_hash"]})
}

func TestW09RootReplacementCannotFeedProduct(t *testing.T) {
	f := contextFixture(t)
	base := t.TempDir()
	aRoot, bRoot := filepath.Join(base, "A"), filepath.Join(base, "B")
	for _, path := range []string{aRoot, bRoot} {
		if err := os.Mkdir(path, 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(aRoot, "same.txt"), []byte("authorized v1"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(bRoot, "same.txt"), []byte("SECRET-B-UNAUTHORIZED"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, aRoot)
	if err != nil {
		t.Fatal(err)
	}
	a, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt")
	if err != nil {
		t.Fatal(err)
	}
	w09ExportFile(t, "g02-authorized-before-replacement", filepath.Join(aRoot, "same.txt"), rootID)
	w09ExportFile(t, "g02-denied-before-replacement", filepath.Join(bRoot, "same.txt"), "")
	w09ExportState(t, f, "g02-before-replacement", rootID)
	if err = os.Rename(aRoot, filepath.Join(base, "A-original")); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS == "windows" {
		if output, createErr := exec.Command("cmd.exe", "/c", "mklink", "/J", aRoot, bRoot).CombinedOutput(); createErr != nil {
			t.Fatalf("junction fixture unavailable: %v: %s", createErr, output)
		}
	} else if err = os.Symlink(bRoot, aRoot); err != nil {
		t.Fatal(err)
	}
	if _, err = f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "same.txt"); err == nil {
		t.Fatal("replaced root captured B")
	}
	state := f.state()
	query := Object{"query": "SECRET-B-UNAUTHORIZED", "snapshot_ids": []any{a["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	if got := f.expect(200, "POST", f.path("/search"), ID(), "", query); len(Arr(got, "hits")) != 0 || strings.Contains(string(Bytes(got)), "SECRET-B-UNAUTHORIZED") {
		t.Fatal("replacement leaked B", got)
	}
	f.expect(412, "GET", f.path("/artifacts/"+Str(a, "id")+"/content"), "", "", nil)
	changed, err := f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project)
	if err != nil || changed != 1 {
		t.Fatal("replacement not invalidated", changed, err)
	}
	w09ExportFile(t, "g02-replacement-path", aRoot, rootID)
	w09ExportFile(t, "g02-denied-target", filepath.Join(bRoot, "same.txt"), "")
	w09ExportState(t, f, "g02-replacement-after-refresh", rootID)
	w09ExportEvent(t, "g02-os-branch", Object{"goos": runtime.GOOS, "goarch": runtime.GOARCH, "junction_branch": runtime.GOOS == "windows"})
	w09Assertion(t, "W09-G02-ROOT-REPLACEMENT", Object{"capture_denied": true, "search_leaks": 0, "content_denied": true, "invalidated": true})
}

func TestW09TaskInputCannotRematerializeStaleLocalBody(t *testing.T) {
	f := contextFixture(t)
	base := t.TempDir()
	source := filepath.Join(base, "source")
	if err := os.Mkdir(source, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(source, "input.txt"), []byte("v1 stale input body"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(context.Background(), f.token, f.project, source)
	if err != nil {
		t.Fatal(err)
	}
	a, err := f.s.CaptureLocalSnapshot(context.Background(), f.token, f.project, rootID, "input.txt")
	if err != nil {
		t.Fatal(err)
	}
	req := f.requirement()
	task := f.task(req, []any{Ref(a, "Artifact")}, "needs-source-input")
	bundle := f.bundle(task)
	if !containsSnapshot(Arr(bundle, "authorized_snapshot_ids"), Str(a, "id")) {
		t.Fatal("initial source not bound")
	}
	w09ExportFile(t, "g02-stale-input-before-delete", filepath.Join(source, "input.txt"), rootID)
	w09ExportState(t, f, "g02-before-delete", rootID)
	if err = os.Remove(filepath.Join(source, "input.txt")); err != nil {
		t.Fatal(err)
	}
	state := f.state()
	f.expect(412, "POST", f.path("/context-bundles"), ID(), testTag(state), Object{"task_id": task["id"], "expected_project_state_revision": state["revision"]})
	if _, err = f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(task, "id"), filepath.Join(base, "stale-bundle")); err == nil {
		t.Fatal("old input rematerialized")
	}
	f.expect(412, "GET", f.path("/artifacts/"+Str(a, "id")+"/content"), "", "", nil)
	if _, err = f.s.RefreshLocalSnapshots(context.Background(), f.token, f.project); err != nil {
		t.Fatal(err)
	}
	f.expect(409, "GET", f.path("/artifacts/"+Str(a, "id")+"/content"), "", "", nil)
	other := f.task(req, Empty(), "without-deleted-source")
	newBundle := f.bundle(other)
	if containsSnapshot(Arr(newBundle, "authorized_snapshot_ids"), Str(a, "id")) {
		t.Fatal("new bundle retained deleted ID")
	}
	manifest, err := f.s.MaterializeTaskContext(context.Background(), f.token, f.project, Str(other, "id"), filepath.Join(base, "clean-bundle"))
	if err != nil || strings.Contains(string(Bytes(manifest)), "v1 stale input body") {
		t.Fatal("new bundle retained deleted bytes", err, manifest)
	}
	w09ExportFile(t, "g02-stale-input-after-delete", filepath.Join(source, "input.txt"), rootID)
	w09ExportState(t, f, "g02-after-delete", rootID)
	w09ExportEvent(t, "g02-clean-context-manifest", manifest)
	w09Assertion(t, "W09-G02-STALE-INPUT-BODY", Object{"new_context_refused_for_stale_task": true, "old_materialize_denied": true, "get_content_denied": true, "new_task_context_clean": true})
}

func TestW09LegacyRootMigrationRevokesUnidentifiedRoot(t *testing.T) {
	db, err := store.Open(filepath.Join(t.TempDir(), "legacy.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err = store.Bootstrap(context.Background(), db, "../../migrations/sqlite/0001_bootstrap.sql"); err != nil {
		t.Fatal(err)
	}
	legacy, err := os.ReadFile("../../migrations/sqlite/0007_retrieval.sql")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec(string(legacy)); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("INSERT INTO retrieval_roots(project,id,path,revision) VALUES('legacy','old','C:/prior-root',1)"); err != nil {
		t.Fatal(err)
	}
	if _, err = db.Exec("INSERT INTO schema_migrations(version) VALUES(7)"); err != nil {
		t.Fatal(err)
	}
	if _, err = New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql"); err != nil {
		t.Fatal(err)
	}
	var identity string
	var revoked, revision int
	if err = db.QueryRow("SELECT root_identity,revoked,revision FROM retrieval_roots WHERE project='legacy' AND id='old'").Scan(&identity, &revoked, &revision); err != nil {
		t.Fatal(err)
	}
	if identity != "" || revoked != 1 || revision != 2 {
		t.Fatalf("legacy root kept authority: identity=%q revoked=%d revision=%d", identity, revoked, revision)
	}
	w09ExportEvent(t, "g02-legacy-sql-observation", Object{"root_identity": identity, "revoked": revoked, "revision": revision, "source": "SELECT root_identity,revoked,revision FROM retrieval_roots"})
	w09Assertion(t, "W09-G02-LEGACY-ROOT", Object{"old_root_revoked": true, "identity_unknown": true})
}
