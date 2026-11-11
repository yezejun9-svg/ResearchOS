package domain

import (
	"bytes"
	"context"
	"crypto/sha256"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// W09-01 seals the increment this card owns on top of the accepted W09 retrieval
// surface: the sealed original must be the exact source bytes, a same-source
// repost must merge without losing its citation chain, source updates and root
// revocation must reach the dependent judgement, and every search hit must pass
// both the project grant and the current source hash. Each refusal below is
// asserted by the status, machine code and message the product really returns,
// never by "some error came back", so every row can go red on its own.

// w0901EvidenceBody builds a complete CreateEvidenceRequest. The frozen schema is
// additionalProperties:false with 18 required fields, so a refusal here refuses
// the claim itself, not a malformed payload.
func w0901EvidenceBody(claim, evidenceKind, sourceKind string, ref Object, locator string) Object {
	return Object{"claim": claim, "stance": "SUPPORT", "evidence_kind": evidenceKind, "source_kind": sourceKind, "canonical_url": "https://fixture.example/" + locator, "publisher": nil, "upstream_revision": nil, "published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN", "snapshot_artifact_ref": ref, "locator": locator, "independence_key": Hash(locator + evidenceKind), "origin_evidence_id": nil, "discovery_urls": Empty(), "license_status": "UNKNOWN", "license_expression": nil}
}

// w0901Content reads a sealed body through the product's own HTTP surface and
// hands back the untouched bytes: f.request decodes JSON, which would destroy a
// text/plain source body and make a byte comparison meaningless.
func w0901Content(t *testing.T, f *fixture, artifactID string) (int, []byte, http.Header) {
	t.Helper()
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest("GET", f.path("/artifacts/"+artifactID+"/content"), nil)
	request.Header.Set("Authorization", "Bearer "+f.token)
	f.h.ServeHTTP(recorder, request)
	return recorder.Code, recorder.Body.Bytes(), recorder.Header()
}

// w0901Denied asserts an HTTP refusal by status, machine code and message.
func w0901Denied(t *testing.T, f *fixture, method, path, key, etag string, body any, wantStatus int, wantCode, wantMessage string) Object {
	t.Helper()
	status, reply, _ := f.request(method, path, key, etag, body)
	if status != wantStatus || Str(reply, "code") != wantCode || !strings.Contains(Str(reply, "message"), wantMessage) {
		t.Fatalf("%s %s: got %d %q %q; want %d %s containing %q", method, path, status, Str(reply, "code"), Str(reply, "message"), wantStatus, wantCode, wantMessage)
	}
	return reply
}

// w0901Fault asserts a refusal from the trusted local service calls, which return
// the same *Fault the HTTP layer renders.
func w0901Fault(t *testing.T, err error, wantStatus int, wantCode, wantMessage string) *Fault {
	t.Helper()
	if err == nil {
		t.Fatalf("expected refusal %d %s containing %q, but the call succeeded", wantStatus, wantCode, wantMessage)
	}
	fault, ok := err.(*Fault)
	if !ok {
		t.Fatalf("expected a *Fault, got %T: %v", err, err)
	}
	if fault.Status != wantStatus || fault.Code != wantCode || !strings.Contains(fault.Message, wantMessage) {
		t.Fatalf("got %d %s %q; want %d %s containing %q", fault.Status, fault.Code, fault.Message, wantStatus, wantCode, wantMessage)
	}
	return fault
}

func w0901LeakCount(marker string, replies []string) int {
	total := 0
	for _, reply := range replies {
		total += strings.Count(reply, marker)
	}
	return total
}

// Action 1: the Artifact is the original, not a summary of it, and the Evidence row
// carries the source URL, revision, hash, locator, type and observed time.
func TestW0901SealedOriginalIsTheProductBody(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const claim = "the sealed original states the measured digest"
	const marker = "W0901_PRIMARY_ORIGINAL_TAIL_4471"
	original := []byte("ResearchOS primary statement.\nhttps://fixture.example/original.txt\nSecond line of the untouched original.\n" + marker + "\n")
	if err := os.WriteFile(filepath.Join(rootPath, "original.txt"), original, 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, evidence := w09LocalEvidence(t, f, rootID, "original.txt", claim)
	recomputed := "sha256:" + fmt.Sprintf("%x", sha256.Sum256(original))
	size, err := Num(artifact, "byte_size")
	if err != nil {
		t.Fatal(err)
	}
	if artifact["content_hash"] != recomputed || size != int64(len(original)) || artifact["kind"] != "SOURCE_SNAPSHOT" || artifact["evidence_kind"] != "OBSERVED" || artifact["measurement_mode"] != "LIVE" || artifact["media_type"] != "text/plain; charset=utf-8" {
		t.Fatalf("sealed artifact is not the original bytes: %v, recomputed %s", artifact, recomputed)
	}
	w09Assertion(t, "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES", Object{"content_hash": artifact["content_hash"], "recomputed_sha256": recomputed, "byte_size": size, "on_disk_bytes": len(original), "kind": artifact["kind"], "evidence_kind": artifact["evidence_kind"], "measurement_mode": artifact["measurement_mode"], "media_type": artifact["media_type"]})
	status, body, header := w0901Content(t, f, Str(artifact, "id"))
	if status != 200 || !bytes.Equal(body, original) || Digest(body) != Str(artifact, "content_hash") || header.Get("Cache-Control") != "no-store" || header.Get("Digest") == "" {
		t.Fatalf("sealed body did not read back byte-identical: status %d bytes %d headers %v", status, len(body), header)
	}
	w09Assertion(t, "W0901-SEALED-BODY-READS-BACK-BYTES-IDENTICAL", Object{"status": status, "body_bytes": len(body), "body_sha256": Digest(body), "digest_header": header.Get("Digest"), "cache_control": header.Get("Cache-Control"), "tail_marker_present": bytes.Contains(body, []byte(marker))})
	row := f.read("evidence", Str(evidence, "id"))
	reference, ok := row["snapshot_artifact_ref"].(map[string]any)
	if !ok {
		t.Fatalf("evidence carries no snapshot reference: %v", row)
	}
	if Str(row, "locator") != "original.txt" || Str(row, "evidence_kind") != "OBSERVED" || Str(row, "source_kind") != "LOCAL" || Str(row, "validity") != "CURRENT" || Str(row, "canonical_url") != "https://fixture.example/original.txt" || Str(row, "claim") != claim || Str(row, "verification_status") != "UNVERIFIED" {
		t.Fatalf("evidence row lost its source locator, type or URL: %v", row)
	}
	if _, e := time.Parse(time.RFC3339Nano, Str(row, "retrieved_at")); e != nil {
		t.Fatalf("observed time is not a timestamp: %v in %v", e, row)
	}
	if reference["id"] != artifact["id"] || reference["content_hash"] != artifact["content_hash"] || reference["entity_type"] != "Artifact" || reference["revision"] == nil {
		t.Fatalf("snapshot reference does not pin the sealed artifact revision: %v", reference)
	}
	for _, field := range []string{"upstream_revision", "publisher", "published_at", "modified_at", "origin_evidence_id", "license_expression"} {
		if _, present := row[field]; !present {
			t.Fatalf("sealed Evidence is missing the frozen field %q: %v", field, row)
		}
	}
	w09Assertion(t, "W0901-EVIDENCE-ROW-CARRIES-LOCATOR-TYPE-OBSERVED-AT-AND-SNAPSHOT-REF", Object{"locator": row["locator"], "evidence_kind": row["evidence_kind"], "source_kind": row["source_kind"], "canonical_url": row["canonical_url"], "retrieved_at": row["retrieved_at"], "time_status": row["time_status"], "upstream_revision_absent_as_recorded": row["upstream_revision"] == nil, "snapshot_ref": reference, "validity": row["validity"]})
	// A summary must never stand in for the original: the reference is bound to the
	// sealed bytes by hash, so redirecting it at a shorter body is refused.
	summary := []byte("Summary only: the original supports the claim.\n")
	uploaded := f.expect(201, "POST", f.path("/content"), ID(), "", summary)
	summaryArtifact := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "LIVE", "content_hash": uploaded["content_hash"], "storage_key": uploaded["storage_key"], "media_type": "text/plain; charset=utf-8", "byte_size": len(summary), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	tampered := Ref(artifact, "Artifact")
	tampered["content_hash"] = summaryArtifact["content_hash"]
	denied := w0901Denied(t, f, "POST", f.path("/evidence"), ID(), f.stateTag(), w0901EvidenceBody(claim, "OBSERVED", "LOCAL", tampered, "original.txt"), 422, "GATE_FAILED", "hash changed")
	repeat, err := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "original.txt")
	if err != nil {
		t.Fatal(err)
	}
	_, stillOriginal, _ := w0901Content(t, f, Str(artifact, "id"))
	if repeat["id"] != artifact["id"] || repeat["content_hash"] != recomputed || !bytes.Equal(stillOriginal, original) {
		t.Fatalf("the refused request altered or duplicated the sealed original: %v", repeat)
	}
	w09Assertion(t, "W0901-SUMMARY-BODY-CANNOT-BE-SWAPPED-FOR-SEALED-ORIGINAL", Object{"refused_status": 422, "refused_code": Str(denied, "code"), "refused_message": Str(denied, "message"), "summary_sha256": summaryArtifact["content_hash"], "summary_bytes": len(summary), "original_bytes": len(original), "original_body_untouched": bytes.Equal(stillOriginal, original), "replay_reused_one_artifact": repeat["id"] == artifact["id"]})
}

// Action 2, first half: identical source bytes merge into one Artifact while each
// citation keeps its own Evidence row and its reviewed chain; a repost that cites
// nothing cannot be attached; revocation reaches the dependent evidence.
func TestW0901SameBytesRepostMergesButKeepsChain(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const primaryURL = "https://fixture.example/original.txt"
	const claim = "the primary statement is the source of the claim"
	primaryBody := "Primary statement about the measured digest.\n" + primaryURL + "\nTail of the sealed original.\n"
	if err := os.WriteFile(filepath.Join(rootPath, "original.txt"), []byte(primaryBody), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	merged, primary := w09LocalEvidence(t, f, rootID, "original.txt", claim)
	if err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(primary, "id"), "", Str(merged, "id"), rootID, "original.txt"); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(rootPath, "repost.txt"), []byte(primaryBody), 0600); err != nil {
		t.Fatal(err)
	}
	repostArtifact, repost := w09LocalEvidence(t, f, rootID, "repost.txt", claim)
	if repostArtifact["id"] != merged["id"] {
		t.Fatalf("identical source bytes produced a duplicate artifact: %v vs %v", repostArtifact, merged)
	}
	if repost["id"] == primary["id"] {
		t.Fatal("merged repost lost its own evidence row")
	}
	if err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(repost, "id"), Str(primary, "id"), Str(repostArtifact, "id"), rootID, "repost.txt"); err != nil {
		t.Fatal(err)
	}
	row := f.read("evidence", Str(repost, "id"))
	if row["origin_evidence_id"] != primary["id"] || row["independence_key"] != primary["independence_key"] {
		t.Fatalf("citation chain lost after the merge: %v", row)
	}
	summary, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(primary, "id"), Str(repost, "id")})
	if err != nil || summary["independent_observed_count"] != 1 || len(Arr(summary, "records")) != 2 {
		t.Fatalf("same-source repost did not collapse to one independent root: %v %v", summary, err)
	}
	w09Assertion(t, "W0901-SAME-BYTES-REPOST-MERGED-INTO-ONE-ARTIFACT-KEEPS-CHAIN", Object{"shared_artifact_id": merged["id"], "evidence_rows": len(Arr(summary, "records")), "independent_roots": summary["independent_observed_count"], "origin_evidence_id": row["origin_evidence_id"], "independence_key_inherited": row["independence_key"] == primary["independence_key"]})
	if err = os.WriteFile(filepath.Join(rootPath, "paraphrase.txt"), []byte("A rewrite that repeats the claim and cites nothing.\n"), 0600); err != nil {
		t.Fatal(err)
	}
	paraphraseArtifact, paraphrase := w09LocalEvidence(t, f, rootID, "paraphrase.txt", claim)
	err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(paraphrase, "id"), Str(primary, "id"), Str(paraphraseArtifact, "id"), rootID, "paraphrase.txt")
	fault := w0901Fault(t, err, 422, "GATE_FAILED", "does not cite claimed origin URL")
	if got := f.read("evidence", Str(paraphrase, "id")); got["origin_evidence_id"] != nil {
		t.Fatalf("the refused annotation still wrote a chain link: %v", got)
	}
	w09Assertion(t, "W0901-UNCITED-REPOST-CANNOT-BE-ATTACHED-TO-THE-ORIGIN", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "origin_evidence_id_after_refusal": f.read("evidence", Str(paraphrase, "id"))["origin_evidence_id"]})
	if err = f.s.RevokeLocalRoot(ctx, f.token, f.project, rootID); err != nil {
		t.Fatal(err)
	}
	if got := f.read("artifacts", Str(merged, "id")); got["validity"] != "REVOKED" {
		t.Fatalf("the merged artifact survived revocation: %v", got)
	}
	originRow, downstreamRow := f.read("evidence", Str(primary, "id")), f.read("evidence", Str(repost, "id"))
	if originRow["validity"] != "REVOKED" || downstreamRow["validity"] != "REVOKED" {
		t.Fatalf("revocation did not reach the dependent evidence: %v %v", originRow, downstreamRow)
	}
	if downstreamRow["origin_evidence_id"] != primary["id"] {
		t.Fatalf("revocation destroyed the citation chain: %v", downstreamRow)
	}
	after, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(primary, "id"), Str(repost, "id"), Str(paraphrase, "id")})
	if err != nil || after["independent_observed_count"] != 0 || after["unknown_count"] != 3 || len(Arr(after, "records")) != 3 {
		t.Fatalf("revoked evidence still counted as support: %v %v", after, err)
	}
	records := map[string]map[string]any{}
	for _, raw := range Arr(after, "records") {
		record, ok := raw.(map[string]any)
		if !ok {
			t.Fatalf("support record is not an object: %v", raw)
		}
		records[Str(record, "evidence_id")] = record
	}
	downstream := records[Str(repost, "id")]
	if Str(downstream, "validity") != "REVOKED" || downstream["origin_evidence_id"] != primary["id"] {
		t.Fatalf("the dependency judgement dropped the chain it must preserve: %v", records)
	}
	w09Assertion(t, "W0901-REVOCATION-PROPAGATES-THROUGH-THE-CITATION-CHAIN", Object{"artifact_validity": f.read("artifacts", Str(merged, "id"))["validity"], "origin_validity": originRow["validity"], "downstream_validity": downstreamRow["validity"], "independent_roots": after["independent_observed_count"], "unknown": after["unknown_count"], "chain_kept_in_records": downstream["origin_evidence_id"]})
}

// Action 2, second half: a source update makes the origin non-CURRENT, the
// dependent evidence stops counting as support, and the stale origin cannot
// anchor new downstream work.
func TestW0901SourceUpdateDropsDependentSupport(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const primaryURL = "https://fixture.example/original.txt"
	const claim = "the primary statement is the source of the claim"
	if err := os.WriteFile(filepath.Join(rootPath, "original.txt"), []byte("Primary statement v1.\n"+primaryURL+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	primaryArtifact, primary := w09LocalEvidence(t, f, rootID, "original.txt", claim)
	if err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(primary, "id"), "", Str(primaryArtifact, "id"), rootID, "original.txt"); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(rootPath, "cited.txt"), []byte("Secondary article citing "+primaryURL+" verbatim.\n"), 0600); err != nil {
		t.Fatal(err)
	}
	citedArtifact, cited := w09LocalEvidence(t, f, rootID, "cited.txt", claim)
	if err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(cited, "id"), Str(primary, "id"), Str(citedArtifact, "id"), rootID, "cited.txt"); err != nil {
		t.Fatal(err)
	}
	before, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(cited, "id")})
	if err != nil || before["independent_observed_count"] != 1 {
		t.Fatalf("valid chain unavailable: %v %v", before, err)
	}
	if err = os.WriteFile(filepath.Join(rootPath, "original.txt"), []byte("Primary statement v2 replaces the source text.\n"+primaryURL+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	changed, err := f.s.RefreshLocalSnapshots(ctx, f.token, f.project)
	if err != nil || changed != 1 {
		t.Fatalf("refresh after a source update: changed %d err %v", changed, err)
	}
	originRow := f.read("evidence", Str(primary, "id"))
	artifactRow := f.read("artifacts", Str(primaryArtifact, "id"))
	if originRow["validity"] == "CURRENT" || artifactRow["validity"] == "CURRENT" {
		t.Fatalf("updated source still CURRENT: %v %v", originRow, artifactRow)
	}
	downstream := f.read("evidence", Str(cited, "id"))
	if downstream["validity"] != "CURRENT" || downstream["origin_evidence_id"] != primary["id"] {
		t.Fatalf("downstream evidence lost its own row or its chain: %v", downstream)
	}
	after, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(cited, "id")})
	if err != nil || after["independent_observed_count"] != 0 || after["unknown_count"] != 1 || len(Arr(after, "records")) != 1 {
		t.Fatalf("stale origin still counted as support: %v %v", after, err)
	}
	record, ok := Arr(after, "records")[0].(map[string]any)
	if !ok || record["origin_evidence_id"] != primary["id"] || Str(record, "origin_relation") != "UNKNOWN" {
		t.Fatalf("the dependency judgement must demote the chain, not delete it: %v", Arr(after, "records"))
	}
	w09Assertion(t, "W0901-SOURCE-UPDATE-DROPS-DEPENDENT-OBSERVED-SUPPORT", Object{"refreshed_snapshots": changed, "origin_validity": originRow["validity"], "artifact_validity": artifactRow["validity"], "downstream_validity": downstream["validity"], "independent_roots_before": before["independent_observed_count"], "independent_roots_after": after["independent_observed_count"], "unknown_after": after["unknown_count"], "chain_preserved": record["origin_evidence_id"]})
	if err = os.WriteFile(filepath.Join(rootPath, "late.txt"), []byte("Later work citing "+primaryURL+".\n"), 0600); err != nil {
		t.Fatal(err)
	}
	lateArtifact, late := w09LocalEvidence(t, f, rootID, "late.txt", claim)
	err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(late, "id"), Str(primary, "id"), Str(lateArtifact, "id"), rootID, "late.txt")
	fault := w0901Fault(t, err, 422, "GATE_FAILED", "current observed origin required")
	w09Assertion(t, "W0901-STALE-ORIGIN-CANNOT-ANCHOR-A-NEW-DOWNSTREAM", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "origin_validity": f.read("evidence", Str(primary, "id"))["validity"], "late_evidence_id": late["id"]})
}

// Action 3 plus the fourth half of action 4: the local index answers, the hit cites
// the sealed original, and every hit is revalidated against the live source hash and
// the caller's project grant.
func TestW0901LocalSearchCitesSealedOriginalAndRevalidates(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const claim = "the sealed local file is the source"
	const marker = "qzsealedneedle4471"
	const replacedMarker = "qznewneedle9982"
	body := []byte("first line\nsecond line\nlocal token " + marker + " here\nfourth line\n")
	if err := os.WriteFile(filepath.Join(rootPath, "source.txt"), body, 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, evidence := w09LocalEvidence(t, f, rootID, "source.txt", claim)
	state := f.state()
	query := Object{"query": marker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	result := f.expect(200, "POST", f.path("/search"), ID(), "", query)
	hits := Arr(result, "hits")
	if len(hits) != 1 {
		t.Fatalf("local search lost the sealed original: %v warnings %v", result, Arr(result, "warnings"))
	}
	hit, ok := hits[0].(map[string]any)
	if !ok {
		t.Fatalf("hit is not an object: %v", hits[0])
	}
	reference, ok := hit["artifact_ref"].(map[string]any)
	if !ok {
		t.Fatalf("hit carries no artifact reference: %v", hit)
	}
	if hit["evidence_id"] != evidence["id"] || Str(hit, "locator") != "line:3" || !strings.Contains(Str(hit, "excerpt"), marker) || Str(hit, "validity") != "CURRENT" || reference["id"] != artifact["id"] || reference["content_hash"] != artifact["content_hash"] {
		t.Fatalf("hit does not cite the sealed original, its hash and a locator: %v", hit)
	}
	if len(Arr(result, "warnings")) != 0 || Str(result, "snapshot_hash") == "" || result["state_revision"] != state["revision"] {
		t.Fatalf("a clean search reported a warning or no snapshot identity: %v", result)
	}
	w09Assertion(t, "W0901-SEARCH-HIT-CITES-SEALED-ARTIFACT-EVIDENCE-AND-LOCATOR", Object{"locator": hit["locator"], "excerpt": Str(hit, "excerpt"), "evidence_id": hit["evidence_id"], "artifact_ref": reference, "snapshot_hash": result["snapshot_hash"], "warnings": result["warnings"]})
	if hit["backend"] != "sqlite-fts5" || hit["backend_revision"] != "fts5-v1" {
		t.Fatalf("the local index did not answer this hit: %v", hit)
	}
	w09Assertion(t, "W0901-BASELINE-LOCAL-FTS5-INDEX-ANSWERS-THE-HIT", Object{"backend": hit["backend"], "backend_revision": hit["backend_revision"], "indexed_artifact_id": artifact["id"], "alternative_backend_observed": "bounded-scan is the only other value this build emits"})
	// The source changes on disk and has not been refreshed yet: the hit must be
	// refused because the live bytes no longer match the sealed hash, and neither the
	// stale index entry nor the un-indexed replacement may be served.
	if err = os.WriteFile(filepath.Join(rootPath, "source.txt"), []byte("first line\nsecond line\nreplaced content "+replacedMarker+" here\nfourth line\n"), 0600); err != nil {
		t.Fatal(err)
	}
	state = f.state()
	stale := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	unseen := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": replacedMarker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	if len(Arr(stale, "hits")) != 0 || len(Arr(unseen, "hits")) != 0 || !strings.Contains(string(Bytes(stale)), "snapshot changed or unavailable") {
		t.Fatalf("a changed source was still served from the index: %v %v", stale, unseen)
	}
	if w0901LeakCount(marker, []string{string(Bytes(stale)), string(Bytes(unseen))}) != 0 || strings.Contains(string(Bytes(unseen)), replacedMarker) {
		t.Fatalf("revalidation leaked source bytes: %s / %s", Bytes(stale), Bytes(unseen))
	}
	w09Assertion(t, "W0901-SEARCH-REVALIDATES-CURRENT-SOURCE-HASH-BEFORE-HIT", Object{"stale_hits": len(Arr(stale, "hits")), "unindexed_hits": len(Arr(unseen, "hits")), "warning": Arr(stale, "warnings")[0], "sealed_hash": artifact["content_hash"], "old_marker_leaks": w0901LeakCount(marker, []string{string(Bytes(stale)), string(Bytes(unseen))})})
	// The authorization half of the same action: only project-scoped snapshot IDs are
	// consulted, and no host path can be supplied to the search at all.
	pather := MergeCopy(query, Object{"path": filepath.Join(rootPath, "source.txt")})
	denied := w0901Denied(t, f, "POST", f.path("/search"), ID(), "", pather, 400, "INVALID_REQUEST", "request violates")
	w09Assertion(t, "W0901-SEARCH-REFUSES-HOST-PATH-INPUT", Object{"refused_status": 400, "refused_code": Str(denied, "code"), "schema": "SearchRequest", "rejected_field": "path", "refused_message": Str(denied, "message")})
	// The revision the stranger will quote is read while the caller still holds the
	// grant, so the denial below can only come from the project scope, never from a
	// stale-revision precondition that would have fired first.
	state = f.state()
	if err = f.s.ProvisionPrincipal(ctx, Principal{ID: "w0901-stranger", Roles: []string{"OWNER", "PLANNER", "EXECUTOR", "SCHEDULER"}, CanCreateProject: true}); err != nil {
		t.Fatal(err)
	}
	strangerToken, err := f.s.IssueCredential(ctx, "w0901-stranger", time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	ownToken, ownProject := f.token, f.project
	f.token = strangerToken
	strangerProject := Str(f.expect(201, "POST", "/v1/projects", ID(), "", projectBody()), "project_id")
	f.project = ownProject
	w0901Denied(t, f, "GET", f.path("/state"), "", "", nil, 404, "NOT_FOUND", "project or object unavailable")
	rejected := w0901Denied(t, f, "POST", f.path("/search"), ID(), "", Object{"query": marker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}, 404, "NOT_FOUND", "project or object unavailable")
	f.token, f.project = ownToken, ownProject
	if restored := f.expect(200, "GET", f.path("/state"), "", "", nil); restored["project_id"] != ownProject {
		t.Fatalf("fixture lost its own project scope: %v", restored)
	}
	w09Assertion(t, "W0901-SEARCH-REFUSES-PRINCIPAL-WITHOUT-PROJECT-GRANT", Object{"refused_status": 404, "refused_code": Str(rejected, "code"), "refused_message": Str(rejected, "message"), "guard": "project grant checked before any snapshot is read", "principal": "w0901-stranger", "granted_only_on": strangerProject, "owner_read_still_works": true})
}

// Deliverable 2 counter-example 1: SIMULATED disguised as OBSERVED. Every route that
// could launder a simulated body into observed support is asserted as a refusal, and
// a correctly labelled simulation is asserted to contribute no independent support.
func TestW0901SimulatedSourceCannotPoseAsObserved(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const claim = "an agent opinion that supports the claim"
	simulatedBody := []byte("simulated agent opinion, produced by a fixture model call\n")
	uploaded := f.expect(201, "POST", f.path("/content"), ID(), "", simulatedBody)
	simulated := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "SIMULATED", "measurement_mode": "FIXTURE", "content_hash": uploaded["content_hash"], "storage_key": uploaded["storage_key"], "media_type": "text/plain; charset=utf-8", "byte_size": len(simulatedBody), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	denied := w0901Denied(t, f, "POST", f.path("/evidence"), ID(), f.stateTag(), w0901EvidenceBody(claim, "OBSERVED", "LOCAL", Ref(simulated, "Artifact"), "simulated.txt"), 422, "GATE_FAILED", "snapshot evidence kind differs")
	w09Assertion(t, "W0901-OBSERVED-CLAIM-REFUSED-OVER-SIMULATED-SNAPSHOT", Object{"status": 422, "code": Str(denied, "code"), "message": Str(denied, "message"), "snapshot_evidence_kind": simulated["evidence_kind"], "snapshot_measurement_mode": simulated["measurement_mode"]})
	fixtureBody := []byte("fixture snapshot labelled as observed on the artifact itself\n")
	fixtureUpload := f.expect(201, "POST", f.path("/content"), ID(), "", fixtureBody)
	fixtureSnapshot := f.expect(201, "POST", f.path("/artifacts"), ID(), f.stateTag(), Object{"run_id": nil, "kind": "SOURCE_SNAPSHOT", "evidence_kind": "OBSERVED", "measurement_mode": "FIXTURE", "content_hash": fixtureUpload["content_hash"], "storage_key": fixtureUpload["storage_key"], "media_type": "text/plain; charset=utf-8", "byte_size": len(fixtureBody), "input_refs": Empty(), "source_refs": Empty(), "produced_by": f.owner, "access_class": "PROJECT"})
	denied = w0901Denied(t, f, "POST", f.path("/evidence"), ID(), f.stateTag(), w0901EvidenceBody(claim, "OBSERVED", "LOCAL", Ref(fixtureSnapshot, "Artifact"), "fixture-snapshot.txt"), 422, "GATE_FAILED", "requires a live snapshot")
	w09Assertion(t, "W0901-OBSERVED-CLAIM-REFUSED-OVER-FIXTURE-MODE-SNAPSHOT", Object{"status": 422, "code": Str(denied, "code"), "message": Str(denied, "message"), "artifact_evidence_kind": fixtureSnapshot["evidence_kind"], "artifact_measurement_mode": fixtureSnapshot["measurement_mode"]})
	// The remaining disguise needs no forged label at all: write the simulated bytes
	// into an authorized local root and let the trusted importer seal them as a LIVE
	// observed snapshot. The importer refuses, and writes no index row.
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(rootPath, "reseal.txt"), simulatedBody, 0600); err != nil {
		t.Fatal(err)
	}
	_, err = f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "reseal.txt")
	fault := w0901Fault(t, err, 409, "STATE_CONFLICT", "same hash has incompatible source snapshot metadata")
	var laundered int
	if err = f.db.QueryRow("SELECT count(*) FROM retrieval_snapshots WHERE project=? AND artifact_id=?", f.project, Str(simulated, "id")).Scan(&laundered); err != nil {
		t.Fatal(err)
	}
	if laundered != 0 {
		t.Fatalf("the refused local re-seal still wrote %d index rows", laundered)
	}
	// Positive control: the same root, caller and importer do accept bytes that were
	// never simulated, so the refusal above is about the simulated body alone.
	if err = os.WriteFile(filepath.Join(rootPath, "control.txt"), []byte("genuine local observation qzlocalcontrol5577\n"), 0600); err != nil {
		t.Fatal(err)
	}
	controlArtifact, controlEvidence := w09LocalEvidence(t, f, rootID, "control.txt", "a genuine local observation")
	if err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(controlEvidence, "id"), "", Str(controlArtifact, "id"), rootID, "control.txt"); err != nil {
		t.Fatal(err)
	}
	w09Assertion(t, "W0901-SIMULATED-BYTES-REFUSED-RESEAL-AS-LIVE-LOCAL-SNAPSHOT", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "index_rows_written": laundered, "simulated_sha256": simulated["content_hash"], "control_artifact_id": controlArtifact["id"], "control_measurement_mode": controlArtifact["measurement_mode"], "control_evidence_kind": controlArtifact["evidence_kind"]})
	// Labelled honestly, the simulation is still admissible as what it is, but it can
	// never be reviewed into an observed chain.
	simulatedEvidenceBody := w0901EvidenceBody(claim, "SIMULATED", "SIMULATION", Ref(simulated, "Artifact"), "opinion-1")
	simulatedEvidenceBody["canonical_url"] = nil
	simulatedEvidence := f.expect(201, "POST", f.path("/evidence"), ID(), f.stateTag(), simulatedEvidenceBody)
	err = f.s.RecordEvidenceOrigin(ctx, f.token, f.project, Str(simulatedEvidence, "id"), Str(controlEvidence, "id"), Str(simulated, "id"), rootID, "opinion-1")
	fault = w0901Fault(t, err, 422, "GATE_FAILED", "current observed evidence required")
	w09Assertion(t, "W0901-SIMULATED-EVIDENCE-REFUSED-ORIGIN-REVIEW", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "evidence_kind": simulatedEvidence["evidence_kind"], "source_kind": simulatedEvidence["source_kind"]})
	summary, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(simulatedEvidence, "id"), Str(controlEvidence, "id")})
	if err != nil || summary["simulated_count"] != 1 || summary["independent_observed_count"] != 1 || len(Arr(summary, "records")) != 2 {
		t.Fatalf("support summary miscounted the simulation: %v %v", summary, err)
	}
	for _, raw := range Arr(summary, "records") {
		record, ok := raw.(map[string]any)
		if !ok {
			t.Fatalf("support record is not an object: %v", raw)
		}
		if Str(record, "evidence_id") == Str(simulatedEvidence, "id") && (Str(record, "root_evidence_id") != "" || Str(record, "origin_relation") == "CONFIRMED") {
			t.Fatalf("a simulation was counted as an independent observed root: %v", record)
		}
	}
	w09Assertion(t, "W0901-SIMULATION-NEVER-COUNTED-AS-INDEPENDENT-OBSERVED-SUPPORT", Object{"simulated_count": summary["simulated_count"], "independent_observed_count": summary["independent_observed_count"], "independent_root_ids": summary["independent_root_ids"], "records": len(Arr(summary, "records")), "observed_root_id": controlEvidence["id"]})
}

// Deliverable 2 counter-example 2: a same-named file in a second project's root. The
// caller is authorized on both projects, so every denial below is project scoping and
// not an authentication accident.
func TestW0901SameNameFileStaysInsideItsOwnProject(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	firstProject := f.project
	base := t.TempDir()
	firstRoot, secondRoot := filepath.Join(base, "A"), filepath.Join(base, "B")
	for _, dir := range []string{firstRoot, secondRoot} {
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
	}
	const sharedName = "same-name.txt"
	const foreignMarker = "secondprojectprivatemarker7732"
	const ownMarker = "qzfirstprojectneedle6601"
	if err := os.WriteFile(filepath.Join(firstRoot, sharedName), []byte("first project material "+ownMarker+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(secondRoot, sharedName), []byte("second project private material "+foreignMarker+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	secondProject := Str(f.createProject(), "project_id")
	secondRootID, err := f.s.RegisterLocalRoot(ctx, f.token, secondProject, secondRoot)
	if err != nil {
		t.Fatal(err)
	}
	secondArtifact, secondEvidence := w09LocalEvidence(t, f, secondRootID, sharedName, "second project statement")
	state := f.state()
	ownSearch := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": foreignMarker, "snapshot_ids": []any{secondArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	contentStatus, contentBody, _ := w0901Content(t, f, Str(secondArtifact, "id"))
	if len(Arr(ownSearch, "hits")) != 1 || contentStatus != 200 || !bytes.Contains(contentBody, []byte(foreignMarker)) {
		t.Fatalf("positive control failed: the second project cannot read its own same-named file: %d %v", contentStatus, ownSearch)
	}
	w09Assertion(t, "W0901-CROSS-PROJECT-SECOND-PROJECT-READS-ITS-OWN-SAME-NAME-BODY", Object{"project": secondProject, "hits": len(Arr(ownSearch, "hits")), "content_status": contentStatus, "locator": Arr(ownSearch, "hits")[0].(map[string]any)["locator"], "evidence_id": secondEvidence["id"]})
	f.project = firstProject
	firstRootID, err := f.s.RegisterLocalRoot(ctx, f.token, firstProject, firstRoot)
	if err != nil {
		t.Fatal(err)
	}
	firstArtifact, firstEvidence := w09LocalEvidence(t, f, firstRootID, sharedName, "first project statement")
	if firstArtifact["id"] == secondArtifact["id"] || firstEvidence["id"] == secondEvidence["id"] {
		t.Fatalf("same-named files from two projects collapsed: %v %v", firstArtifact, secondArtifact)
	}
	metadata := w0901Denied(t, f, "GET", f.path("/artifacts/"+Str(secondArtifact, "id")), "", "", nil, 404, "NOT_FOUND", "artifact unavailable")
	w09Assertion(t, "W0901-CROSS-PROJECT-SAME-NAME-ARTIFACT-METADATA-DENIED", Object{"status": 404, "code": Str(metadata, "code"), "message": Str(metadata, "message"), "foreign_artifact_id": secondArtifact["id"], "requesting_project": firstProject})
	bodyStatus, leakedBody, _ := w0901Content(t, f, Str(secondArtifact, "id"))
	if bodyStatus != 404 || bytes.Contains(leakedBody, []byte(foreignMarker)) {
		t.Fatalf("the second project's sealed bytes leaked into the first project: status %d body %q", bodyStatus, leakedBody)
	}
	w09Assertion(t, "W0901-CROSS-PROJECT-SAME-NAME-SEALED-BODY-DENIED", Object{"status": bodyStatus, "response_bytes": len(leakedBody), "marker_leaks": strings.Count(string(leakedBody), foreignMarker)})
	state = f.state()
	searchDenied := w0901Denied(t, f, "POST", f.path("/search"), ID(), "", Object{"query": foreignMarker, "snapshot_ids": []any{secondArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}, 404, "NOT_FOUND", "artifact unavailable")
	w09Assertion(t, "W0901-CROSS-PROJECT-SAME-NAME-SEARCH-DENIED", Object{"status": 404, "code": Str(searchDenied, "code"), "message": Str(searchDenied, "message"), "requested_snapshot_id": secondArtifact["id"]})
	state = f.state()
	foreignQuery := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": foreignMarker, "snapshot_ids": []any{firstArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	state = f.state()
	ownQuery := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": ownMarker, "snapshot_ids": []any{firstArtifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	if len(Arr(foreignQuery, "hits")) != 0 || len(Arr(ownQuery, "hits")) != 1 {
		t.Fatalf("first project search is not scoped to its own file: foreign %v own %v", foreignQuery, ownQuery)
	}
	var foreignIndexed, ownIndexed int
	if err = f.db.QueryRow("SELECT count(*) FROM retrieval_fts WHERE project=? AND retrieval_fts MATCH ?", firstProject, "\""+foreignMarker+"\"").Scan(&foreignIndexed); err != nil {
		t.Fatal(err)
	}
	if err = f.db.QueryRow("SELECT count(*) FROM retrieval_fts WHERE project=? AND retrieval_fts MATCH ?", secondProject, "\""+foreignMarker+"\"").Scan(&ownIndexed); err != nil {
		t.Fatal(err)
	}
	replies := []string{string(Bytes(metadata)), string(leakedBody), string(Bytes(searchDenied)), string(Bytes(foreignQuery)), string(Bytes(ownQuery)), string(Bytes(firstArtifact)), string(Bytes(firstEvidence))}
	leaks := w0901LeakCount(foreignMarker, replies)
	if leaks != 0 || foreignIndexed != 0 || ownIndexed != 1 {
		t.Fatalf("same-name cross-project leak: leaks %d foreign rows indexed in the first project %d, second project %d", leaks, foreignIndexed, ownIndexed)
	}
	w09Assertion(t, "W0901-CROSS-PROJECT-SAME-NAME-MARKER-ABSENT-FROM-FIRST-PROJECT-REPLIES", Object{"marker_leaks": leaks, "replies_scanned": len(replies), "first_project_indexed_foreign_rows": foreignIndexed, "second_project_indexed_own_rows": ownIndexed, "first_project_own_hits": len(Arr(ownQuery, "hits")), "artifact_ids_distinct": firstArtifact["id"] != secondArtifact["id"], "evidence_ids_distinct": firstEvidence["id"] != secondEvidence["id"]})
	_, err = f.s.CaptureLocalSnapshot(ctx, f.token, firstProject, firstRootID, filepath.Join(secondRoot, sharedName))
	fault := w0901Fault(t, err, 422, "GATE_FAILED", "root-scoped file unavailable")
	_, err = f.s.CaptureLocalSnapshot(ctx, f.token, firstProject, firstRootID, filepath.Join("..", filepath.Base(secondRoot), sharedName))
	w0901Fault(t, err, 422, "GATE_FAILED", "root-scoped file unavailable")
	w09Assertion(t, "W0901-CROSS-PROJECT-SAME-NAME-CAPTURE-THROUGH-FIRST-ROOT-REFUSED", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "absolute_path_attempt": filepath.Join(secondRoot, sharedName), "traversal_attempt": filepath.Join("..", filepath.Base(secondRoot), sharedName)})
}

// Deliverable 2 counter-example 3: after the root is revoked, the search replayed with
// its original idempotency key must not serve the revoked body again.
func TestW0901RevokedRootCannotServeSealedBodyAgain(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const marker = "qzrevokedbody3311"
	const claim = "the sealed local source is the citation"
	if err := os.WriteFile(filepath.Join(rootPath, "source.txt"), []byte("sealed local source containing "+marker+" on its only line\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, evidence := w09LocalEvidence(t, f, rootID, "source.txt", claim)
	state := f.state()
	query := Object{"query": marker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]}
	key := ID()
	first := f.expect(200, "POST", f.path("/search"), key, "", query)
	hits := Arr(first, "hits")
	if len(hits) != 1 || !strings.Contains(string(Bytes(first)), marker) {
		t.Fatalf("positive control failed: the sealed body was never searchable: %v", first)
	}
	w09Assertion(t, "W0901-SEALED-BODY-SERVED-BEFORE-REVOCATION", Object{"hits": len(hits), "locator": hits[0].(map[string]any)["locator"], "idempotency_key": key, "state_revision": first["state_revision"], "evidence_id": hits[0].(map[string]any)["evidence_id"]})
	if err = f.s.RevokeLocalRoot(ctx, f.token, f.project, rootID); err != nil {
		t.Fatal(err)
	}
	// The create path has to revalidate currency too, not just the hash: a sealed snapshot that exists and whose
	// digest still matches must still be refused once the root behind it is revoked. Deleting the validity leg of that
	// guard is what this row exists to catch.
	revokedCreateStatus, revokedCreate, _ := f.request("POST", f.path("/evidence"), ID(), f.stateTag(), Object{
		"claim": claim, "stance": "SUPPORT", "evidence_kind": "OBSERVED", "source_kind": "LOCAL",
		"canonical_url": "https://fixture.example/source.txt", "publisher": nil, "upstream_revision": nil,
		"published_at": nil, "modified_at": nil, "retrieved_at": Now(), "time_status": "UNKNOWN",
		"snapshot_artifact_ref": Ref(artifact, "Artifact"), "locator": "source.txt",
		"independence_key": Hash("source.txt"), "origin_evidence_id": nil, "discovery_urls": Empty(),
		"license_status": "UNKNOWN", "license_expression": nil})
	if revokedCreateStatus != 422 || !strings.Contains(Str(revokedCreate, "message"), "not current") {
		t.Fatalf("evidence was created over a revoked snapshot: %d %v", revokedCreateStatus, revokedCreate)
	}
	w09Assertion(t, "W0901-CREATE-REFUSED-WHEN-SNAPSHOT-NOT-CURRENT",
		Object{"status": revokedCreateStatus, "code": Str(revokedCreate, "code"),
			"message": Str(revokedCreate, "message"), "artifact_hash": artifact["content_hash"]})
	replayStatus, replay, replayHeader := f.request("POST", f.path("/search"), key, "", query)

	if replayStatus != 412 || Str(replay, "code") != "STALE_REVISION" {
		t.Fatalf("revoked replay returned %d %q instead of a precondition refusal", replayStatus, Str(replay, "code"))
	}
	if strings.Contains(string(Bytes(replay)), marker) || replayHeader.Get("Idempotency-Replayed") == "true" {
		t.Fatalf("the revoked body was replayed from cache: %s", Bytes(replay))
	}
	w09Assertion(t, "W0901-REVOKED-ROOT-IDEMPOTENT-REPLAY-DOES-NOT-SERVE-SEALED-BODY", Object{"status": replayStatus, "code": Str(replay, "code"), "message": Str(replay, "message"), "idempotency_key": key, "idempotency_replayed_header": replayHeader.Get("Idempotency-Replayed"), "marker_leaks": w0901LeakCount(marker, []string{string(Bytes(replay))}), "sealed_body_bytes_at_stake": len("sealed local source containing " + marker + " on its only line\n")})
	state = f.state()
	after := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker, "snapshot_ids": []any{artifact["id"]}, "limit": 10, "expected_state_revision": state["revision"]})
	if len(Arr(after, "hits")) != 0 || strings.Contains(string(Bytes(after)), marker) {
		t.Fatalf("a revoked snapshot still produced hits: %v", after)
	}
	if len(Arr(after, "warnings")) == 0 || !strings.Contains(Str(after, "snapshot_hash"), "sha256:") {
		t.Fatalf("revoked snapshot was dropped silently instead of as a revalidation warning: %v", after)
	}
	w09Assertion(t, "W0901-REVOKED-ROOT-FRESH-SEARCH-RETURNS-NO-HITS", Object{"hits": len(Arr(after, "hits")), "warning": Arr(after, "warnings")[0], "snapshot_hash": after["snapshot_hash"], "marker_leaks": w0901LeakCount(marker, []string{string(Bytes(after))})})
	f.expect(409, "GET", f.path("/artifacts/"+Str(artifact, "id")+"/content"), "", "", nil)
	bodyStatus, body, _ := w0901Content(t, f, Str(artifact, "id"))
	if bodyStatus != 409 || bytes.Contains(body, []byte(marker)) {
		t.Fatalf("revoked body readable: status %d body %q", bodyStatus, body)
	}
	w09Assertion(t, "W0901-REVOKED-ROOT-SEALED-BODY-READ-DENIED", Object{"status": bodyStatus, "code": "STATE_CONFLICT", "response_bytes": len(body), "marker_leaks": strings.Count(string(body), marker), "evidence_validity": f.read("evidence", Str(evidence, "id"))["validity"]})
	_, err = f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "source.txt")
	fault := w0901Fault(t, err, 404, "NOT_FOUND", "authorized root unavailable")
	w09Assertion(t, "W0901-REVOKED-ROOT-CANNOT-CAPTURE-AGAIN", Object{"status": fault.Status, "code": fault.Code, "message": fault.Message, "root_id": rootID})
}
