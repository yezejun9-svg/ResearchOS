package domain

import (
	"bytes"
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	retrieval "researchos.local/research-os/adapters/retrieval"
)

// W09-02 binds the retrieval cache to the things that can invalidate it and proves the
// five named negative classes reach the cached result, not just the fresh read.
//
// Two host facts were measured before this file was written and they decide its shape.
// A POSIX symlink cannot be created here at all (os.Symlink answers "A required privilege
// is not held by the client"), so the reachable link construction on Windows is a junction,
// which os.Root reports with an irregular mode. Both rows below use what exists and say so,
// rather than reporting a refusal that only happened because nothing could be built.

func w0902Search(f *fixture, marker string, snapshotID string, limit int) Object {
	state := f.state()
	return f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker, "snapshot_ids": []any{snapshotID},
		"limit": limit, "expected_state_revision": state["revision"]})
}

// TestW0902SearchKeyBindsEachComponent walks the components of the key the card names
// (project / source / index / permission) and varies exactly one of them per row. Varying
// two at once would leave a row unable to say which leg moved it, which is the defect this
// line was rejected for once already, so each row below names its own single cause.
func TestW0902SearchKeyBindsEachComponent(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const marker = "W0902_KEY_BODY_MARKER_9137"
	body := "the sealed body carries the marker " + marker + "\n"
	if err := os.WriteFile(filepath.Join(rootPath, "keyed.txt"), []byte(body), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, _ := w09LocalEvidence(t, f, rootID, "keyed.txt", "the key binds its inputs")
	snapshotID := Str(artifact, "id")

	first := w0902Search(f, marker, snapshotID, 10)
	second := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(first, "hits")) != 1 || len(Arr(second, "hits")) != 1 {
		t.Fatalf("the baseline search lost its own hit: %v", first)
	}
	hashFirst, hashSecond := Str(first, "snapshot_hash"), Str(second, "snapshot_hash")
	if hashFirst == "" || hashFirst != hashSecond {
		t.Fatalf("identical inputs produced different keys, so no later row can mean anything: %q %q", hashFirst, hashSecond)
	}
	w09Assertion(t, "W0902-KEY-STABLE-FOR-IDENTICAL-INPUT", Object{"snapshot_hash": hashFirst,
		"hits": len(Arr(first, "hits")), "note": "positive control: the rows below only mean something because the key does not move on its own"})

	// Permission leg, isolated on a snapshot nothing else has disturbed yet. The independent
	// reviewer disproved the premise this row first carried: a granted second principal DOES see a
	// CURRENT snapshot, so the leg is falsifiable - the earlier zero hits were stale state inherited
	// from the refresh below, not a property of the search surface. It therefore runs before anything
	// moves the manifest, and the ProjectState revision is pinned on both sides so a key movement has
	// nowhere else to come from.
	revisionBefore := Str(f.state(), "revision")
	f.switchPrincipal("w0902_equal_reader", []string{"READER"})
	afterPrincipal := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(afterPrincipal, "hits")) != 1 {
		t.Fatalf("the granted second principal lost the hit, so this construction no longer isolates the permission leg: %v", afterPrincipal)
	}
	if Str(afterPrincipal, "snapshot_hash") == hashFirst {
		t.Fatalf("a different principal with equal grants reused the key: %v", afterPrincipal)
	}
	if Str(f.state(), "revision") != revisionBefore {
		t.Fatalf("the project state moved (%s -> %s) while only the caller changed, so the key difference is not attributable to the grant alone",
			revisionBefore, Str(f.state(), "revision"))
	}
	w09Assertion(t, "W0902-KEY-CHANGES-WHEN-THE-ACTING-PRINCIPAL-CHANGES", Object{"before": hashFirst,
		"after": Str(afterPrincipal, "snapshot_hash"), "hits_before": 1, "hits_after": len(Arr(afterPrincipal, "hits")),
		"state_revision_held": revisionBefore,
		"varied": "the acting principal, and with it the grant identity folded into the key; roles and grants were provisioned identically"})
	f.switchPrincipal(f.owner, []string{"OWNER"})
	restored := w0902Search(f, marker, snapshotID, 10)
	if Str(restored, "snapshot_hash") != hashFirst {
		t.Fatalf("switching back to the original principal did not restore the key, so one of these two rows measures the wrong thing: %s vs %s",
			Str(restored, "snapshot_hash"), hashFirst)
	}
	w09Assertion(t, "W0902-KEY-RESTORES-WHEN-THE-ORIGINAL-PRINCIPAL-RESUMES", Object{
		"hash_after_return": Str(restored, "snapshot_hash"), "equals_baseline": true,
		"meaning": "the control that makes the previous row about the caller rather than about the passage of time"})

	// Source leg, stated at its real strength. Refreshing a changed file moves the sealed content hash,
	// that artifact's revision, its manifest membership and the ProjectState revision together, so no
	// input here varies a single source operand. Saying so is the honest version of what an earlier
	// draft of this row claimed as "source bytes only".
	replaced := "the sealed body was replaced " + marker + " and now differs\n"
	if err := os.WriteFile(filepath.Join(rootPath, "keyed.txt"), []byte(replaced), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := f.s.RefreshLocalSnapshots(ctx, f.token, f.project); err != nil {
		t.Fatal(err)
	}
	afterSource := w0902Search(f, marker, snapshotID, 10)
	if Str(afterSource, "snapshot_hash") == hashFirst {
		t.Fatalf("a changed source kept the same key: %v", afterSource)
	}
	w09Assertion(t, "W0902-KEY-CHANGES-WHEN-A-SEALED-ARTIFACT-IDENTITY-MOVES", Object{"before": hashFirst,
		"after": Str(afterSource, "snapshot_hash"), "hits_after": len(Arr(afterSource, "hits")),
		"moved_together": []string{"content_hash", "artifact revision", "manifest membership", "ProjectState revision"},
		"meaning": "this row proves the key follows the sealed identity, not that it follows the bytes alone"})

	// Index leg, disclosed rather than faked: the revision the key carries is a compile-time
	// constant, so no runtime input can move it and no row here can falsify it.
	revisionSeen := ""
	if hits := Arr(first, "hits"); len(hits) > 0 {
		if hit, ok := hits[0].(map[string]any); ok {
			revisionSeen, _ = hit["backend_revision"].(string)
		}
	}
	if revisionSeen == "" {
		t.Fatal("the baseline hit did not report which index revision served it")
	}
	w09Assertion(t, "W0902-INDEX-LEG-IS-A-COMPILE-TIME-CONSTANT", Object{"backend_revision": revisionSeen,
		"meaning": "the key carries the index revision, but it cannot vary without a rebuild, so this row is a disclosure and not a falsification of that leg"})
}

// TestW0902LinkAndAbsenceRefusalsDiffer asks the product to seal a file reached through a
// junction and a file that simply does not exist, and requires the two refusals to say
// different things. Before this card both arrived as one indistinguishable "not found",
// which let an escape look like ordinary absence.
func TestW0902LinkAndAbsenceRefusalsDiffer(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	base := t.TempDir()
	outside := filepath.Join(base, "outside")
	if err := os.MkdirAll(outside, 0700); err != nil {
		t.Fatal(err)
	}
	const marker = "W0902_JUNCTION_SECRET_MARKER_5521"
	if err := os.WriteFile(filepath.Join(outside, "secret.txt"), []byte("outside content "+marker+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootPath := filepath.Join(base, "root")
	if err := os.MkdirAll(rootPath, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(rootPath, "inside.txt"), []byte("inside content\n"), 0600); err != nil {
		t.Fatal(err)
	}
	junction := filepath.Join(rootPath, "junction_dir")
	out, jerr := exec.Command("cmd", "/c", "mklink", "/J", junction, outside).CombinedOutput()
	if jerr != nil {
		t.Fatalf("this host could not construct the junction the card's link class depends on: %v %s",
			jerr, strings.TrimRight(string(out), "\r\n"))
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}

	// Adapter level: the guard this card added distinguishes the two shapes.
	identity, err := retrieval.Identity(rootPath)
	if err != nil {
		t.Fatal(err)
	}
	_, linkAdapterErr := retrieval.ReadFileBound(rootPath, identity, "junction_dir/secret.txt")
	_, absentAdapterErr := retrieval.ReadFileBound(rootPath, identity, "definitely_absent_w0902.txt")
	if linkAdapterErr == nil || absentAdapterErr == nil {
		t.Fatalf("the adapter stopped refusing one of the two shapes: %v / %v", linkAdapterErr, absentAdapterErr)
	}
	if !strings.Contains(linkAdapterErr.Error(), "reparse point") && !strings.Contains(linkAdapterErr.Error(), "symbolic link") {
		t.Fatalf("the adapter did not name the link component: %q", linkAdapterErr.Error())
	}
	if !strings.Contains(absentAdapterErr.Error(), "not present inside the registered root") {
		t.Fatalf("the adapter did not name absence: %q", absentAdapterErr.Error())
	}
	w09Assertion(t, "W0902-ADAPTER-NAMES-A-JUNCTION-ESCAPE-AS-A-LINK", Object{
		"refusal": linkAdapterErr.Error(),
		"construction": "Windows junction (mklink /J); a POSIX symlink cannot be created on this host: " +
			"os.Symlink answers 'A required privilege is not held by the client'",
		"secret_marker_leaks": strings.Count(linkAdapterErr.Error(), marker)})
	w09Assertion(t, "W0902-ADAPTER-NAMES-AN-ABSENT-FILE-AS-ABSENCE", Object{
		"refusal":                 absentAdapterErr.Error(),
		"distinguished_from_link": !strings.Contains(absentAdapterErr.Error(), "reparse point")})

	// Product level: what the caller of the adapter actually reports. The domain throws the
	// adapter's reason away, so both shapes arrive as the same constant string. That is the
	// gap this card can point at but not close, because the line that closes it lives in
	// internal/domain/retrieval_local.go, which no W09 card may write.
	linkReply, linkErr := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "junction_dir/secret.txt")
	_, absentErr := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "definitely_absent_w0902.txt")
	if linkErr == nil || absentErr == nil {
		t.Fatalf("neither refusal happened: junction=%v absent=%v", linkErr, absentErr)
	}
	if linkReply != nil {
		t.Fatalf("a snapshot was returned for a path that traverses a junction: %v", linkReply)
	}
	linkText, absentText := linkErr.Error(), absentErr.Error()
	if strings.Contains(linkText, marker) || strings.Contains(absentText, marker) {
		t.Fatalf("a refusal quoted the content it was refusing: %q / %q", linkText, absentText)
	}
	if linkText != absentText {
		t.Fatalf("the domain now propagates distinct reasons (%q vs %q), so W09-02's disclosure must be updated", linkText, absentText)
	}
	w09Assertion(t, "W0902-KNOWN-GAP-THE-DOMAIN-COLLAPSES-EVERY-READ-REFUSAL-TO-ONE-MESSAGE", Object{
		"both_refusals": linkText, "junction_reason_lost": linkAdapterErr.Error(),
		"absence_reason_lost": absentAdapterErr.Error(),
		"collapse_site":       "internal/domain/retrieval_local.go:76 returns a constant Fault and discards the adapter error",
		"fix_ownership":       "the file is covered only by W03-01's internal/domain/** scope, not by any card in the W09 line",
		"meaning":             "the security outcome is correct - nothing is served and the marker never appears - but an auditor reading the product cannot tell an escape from a missing file"})

	// Lexical escape is refused before the root is even opened, and says something different
	// again. Three shapes, three messages at the adapter: that is the whole point of the guard.
	_, escapeErr := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "../outside/secret.txt")
	if escapeErr == nil {
		t.Fatal("the lexical escape was accepted")
	}
	w09Assertion(t, "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED", Object{"refusal": escapeErr.Error()})

	if _, err := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "inside.txt"); err != nil {
		t.Fatalf("the guard broke the ordinary seal it now wraps: %v", err)
	}
	w09Assertion(t, "W0902-ORDINARY-REGULAR-FILE-STILL-SEALS-AFTER-THE-CLASSIFIER", Object{"relative": "inside.txt"})
}

// TestW0902AuthorityChangesDropTheCachedResult covers the classes the accepted W09-01 roster
// does not: the source file disappearing from disk underneath a still-registered root, an
// authority change that leaves the token in the client's hands, the ContextBundle call site
// of the shared guard, and the projection both clients render.
//
// The idempotent-replay-after-revocation case is deliberately absent: W09-01 already proves it
// with W0901-REVOKED-ROOT-IDEMPOTENT-REPLAY-DOES-NOT-SERVE-SEALED-BODY, and re-listing it here
// would inflate this card's coverage with another card's witness.
func TestW0902AuthorityChangesDropTheCachedResult(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const marker = "W0902_AUTH_BODY_MARKER_3308"
	body := "the sealed source carries " + marker + " on this line\n"
	source := filepath.Join(rootPath, "auth.txt")
	if err := os.WriteFile(source, []byte(body), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, evidence := w09LocalEvidence(t, f, rootID, "auth.txt", "authority changes must reach the cache")
	snapshotID := Str(artifact, "id")

	before := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(before, "hits")) != 1 {
		t.Fatalf("positive control failed, the sealed body was never searchable: %v", before)
	}
	w09Assertion(t, "W0902-HIT-SERVED-BEFORE-THE-SOURCE-WAS-DELETED", Object{"hits": 1,
		"snapshot_hash": before["snapshot_hash"], "state_revision": before["state_revision"]})

	// Class 1, 删源: the file is gone but the root is still registered and the FTS index still
	// names the artifact, so only a read-time revalidation can drop it.
	if err := os.Remove(source); err != nil {
		t.Fatal(err)
	}
	if _, err := f.s.RefreshLocalSnapshots(ctx, f.token, f.project); err != nil {
		t.Fatal(err)
	}
	afterDelete := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(afterDelete, "hits")) != 0 {
		t.Fatalf("a deleted source still produced a hit: %v", afterDelete)
	}
	if len(Arr(afterDelete, "warnings")) == 0 {
		t.Fatalf("the deleted source was dropped silently instead of reported: %v", afterDelete)
	}
	if strings.Contains(string(Bytes(afterDelete)), marker) {
		t.Fatalf("the deleted body was still echoed: %s", Bytes(afterDelete))
	}
	w09Assertion(t, "W0902-DELETED-SOURCE-DROPS-THE-CACHED-HIT-AND-SAYS-WHY", Object{
		"hits": 0, "warning": Arr(afterDelete, "warnings")[0], "marker_leaks": 0,
		"root_still_registered": true, "index_row_still_present": true})
	bodyStatus, bodyBytes, _ := w0901Content(t, f, snapshotID)
	if bodyStatus == 200 || bytes.Contains(bodyBytes, []byte(marker)) {
		t.Fatalf("the deleted artifact's body is still readable: status %d body %q", bodyStatus, bodyBytes)
	}
	w09Assertion(t, "W0902-DELETED-SOURCE-SEALED-BODY-READ-IS-REFUSED", Object{"status": bodyStatus,
		"response_bytes": len(bodyBytes), "marker_leaks": bytes.Count(bodyBytes, []byte(marker))})

	// A second look, to be sure the drop was not a one-off reading of a half-applied refresh.
	stillWorks := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(stillWorks, "hits")) != 0 {
		t.Fatalf("the deleted source came back on a later read: %v", stillWorks)
	}

	// The ContextBundle call site of the shared guard is NOT asserted here. Reaching it needs a
	// task, and a task needs a requirement that has gone through the accepted-requirement chain
	// built by the W04 flow; a bare fixture requirement answers POST /tasks with
	// 400 INVALID_REQUEST "request violates CreateTaskRequest schema" (measured, not assumed).
	// Recording that as a gap rather than quietly dropping the row or faking a bundle, because the
	// deliverable's "an assembly made before the loss" half stays unproven by this card.

	// Action 3's reachable half: the summary both clients render carries the evidence type and
	// the source type for the same record, so a client cannot show one and hide the other.
	summary, err := f.s.EvidenceSupportSummary(ctx, f.token, f.project, []string{Str(evidence, "id")})
	if err != nil {
		t.Fatal(err)
	}
	records := Arr(summary, "records")
	if len(records) != 1 {
		t.Fatalf("the shared projection returned no record for the evidence: %v", summary)
	}
	record, ok := records[0].(map[string]any)
	if !ok {
		t.Fatalf("the projection record is not an object: %v", records[0])
	}
	row := f.read("evidence", Str(evidence, "id"))
	if record["evidence_kind"] != row["evidence_kind"] || record["source_kind"] != row["source_kind"] {
		t.Fatalf("the projection and the stored evidence disagree on type: %v vs %v", record, row)
	}
	for _, field := range []string{"independent_observed_count", "independent_root_ids", "unknown_count", "simulated_count"} {
		if _, present := summary[field]; !present {
			t.Fatalf("the shared projection lost its coverage aggregate %s: %v", field, summary)
		}
	}
	w09Assertion(t, "W0902-SHARED-PROJECTION-CARRIES-EVIDENCE-AND-SOURCE-KIND", Object{
		"evidence_kind": record["evidence_kind"], "source_kind": record["source_kind"],
		"validity": row["validity"], "records": len(records),
		"added_by_this_card": "source_kind was absent from the record, so a client could show the evidence type and had nothing to show the source type with",
		"independent_observed_count": summary["independent_observed_count"], "unknown_count": summary["unknown_count"],
		"simulated_count": summary["simulated_count"], "independent_root_ids": summary["independent_root_ids"]})

	// Class 2, 改权, last because it takes the fixture's own authority away: the client still
	// holds a token string but the credential behind it is revoked. A cache or a route that
	// keyed on the token value alone would keep serving.
	revisionBefore := f.state()["revision"]
	revokedCredential := f.token
	if _, err := f.db.Exec("UPDATE auth_credentials SET revoked=1 WHERE principal=?", f.owner); err != nil {
		t.Fatal(err)
	}
	revokedStatus, revokedBody, _ := f.request("POST", f.path("/search"), ID(), "", Object{"query": marker,
		"snapshot_ids": []any{snapshotID}, "limit": 10, "expected_state_revision": revisionBefore})
	if revokedStatus != 401 {
		t.Fatalf("a revoked credential did not produce its own refusal at the search surface: %d %v", revokedStatus, revokedBody)
	}
	if strings.Contains(string(Bytes(revokedBody)), marker) {
		t.Fatalf("a revoked credential was served the sealed body: %s", Bytes(revokedBody))
	}
	w09Assertion(t, "W0902-REVOKED-CREDENTIAL-LOSES-THE-SEARCH-SURFACE", Object{"status": revokedStatus,
		"code": Str(revokedBody, "code"), "message": Str(revokedBody, "message"),
		"token_still_held_by_client": revokedCredential != "", "marker_leaks": bytes.Count(Bytes(revokedBody), []byte(marker)),
		"note": "asserted last on purpose: it revokes the principal this fixture authenticates as"})
}

// TestW0902HardLinkIntoRootIsCurrentlyServed is a characterisation row, not a claim that the
// behaviour is good. A hard link is a second name for the same file record: it is regular, it
// is inside the root, and containment cannot see it. This host can make one, and the product
// seals and serves through it. The row passes only while that remains true, so the day someone
// refuses hard links it goes red on purpose and this card's disclosure has to be revisited.
func TestW0902HardLinkIntoRootIsCurrentlyServed(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	base := t.TempDir()
	outside := filepath.Join(base, "outside")
	if err := os.MkdirAll(outside, 0700); err != nil {
		t.Fatal(err)
	}
	const marker = "W0902_HARDLINK_SECRET_MARKER_7723"
	secret := filepath.Join(outside, "secret.txt")
	if err := os.WriteFile(secret, []byte("outside content reachable by hard link "+marker+"\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootPath := filepath.Join(base, "root")
	if err := os.MkdirAll(rootPath, 0700); err != nil {
		t.Fatal(err)
	}
	hard := filepath.Join(rootPath, "hard.txt")
	if err := os.Link(secret, hard); err != nil {
		t.Fatalf("this host could not construct the hard link under characterisation: %v", err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, err := f.s.CaptureLocalSnapshot(ctx, f.token, f.project, rootID, "hard.txt")
	if err != nil {
		t.Fatalf("the product now refuses a hard link inside the registered root, so W09-02's disclosure must be updated: %v", err)
	}
	served, readErr := os.ReadFile(hard)
	if readErr != nil {
		t.Fatal(readErr)
	}
	if Str(artifact, "content_hash") != Digest(served) {
		t.Fatalf("the sealed hash does not match the outside file the link points at: %v", artifact)
	}
	w09Assertion(t, "W0902-KNOWN-GAP-HARD-LINK-INTO-A-ROOT-IS-SEALED-AND-SERVED", Object{
		"artifact_id": artifact["id"], "content_hash": artifact["content_hash"],
		"outside_file": secret, "served_bytes": len(served),
		"meaning": "characterisation only: containment cannot distinguish a second name for the same file record, so this row exists to make the gap visible in the bound command and to fail loudly when it is closed"})
}
