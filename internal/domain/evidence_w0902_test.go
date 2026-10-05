package domain

import (
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

	// Source leg: same principal, same project, same index; only the sealed bytes change.
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
	w09Assertion(t, "W0902-KEY-CHANGES-WHEN-SEALED-CONTENT-CHANGES", Object{"before": hashFirst,
		"after": Str(afterSource, "snapshot_hash"), "varied": "source bytes only",
		"hits_after": len(Arr(afterSource, "hits"))})

	// Permission leg. The construction this card hoped for does not isolate it, and the run
	// says so: a second principal with equal roles and equal grants cannot see the artifact at
	// all, so any key movement between those two calls is the manifest leg moving underneath it.
	// Recording that as a row rather than quietly reporting a hash difference keeps the claim
	// honest, and names what a real isolation would need.
	f.switchPrincipal("w0902_equal_reader", []string{"READER"})
	afterPrincipal := w0902Search(f, marker, snapshotID, 10)
	if len(Arr(afterPrincipal, "hits")) != 0 {
		t.Fatalf("the second principal unexpectedly still saw the snapshot, so this row's premise changed: %v", afterPrincipal)
	}
	if !strings.Contains(string(Bytes(afterPrincipal)), "snapshot changed or unavailable") {
		t.Fatalf("the second principal lost the hit for some reason other than the one characterised here: %v", afterPrincipal)
	}
	w09Assertion(t, "W0902-PERMISSION-LEG-CANNOT-BE-ISOLATED-AT-THE-SEARCH-SURFACE", Object{
		"before": hashFirst, "after": Str(afterPrincipal, "snapshot_hash"),
		"hits_after": 0, "warning": "snapshot changed or unavailable",
		"meaning": "visibility is bound to more than the grant set the key hashes, so no cross-principal construction here varies the permission leg alone; the row goes red if that stops being true"})

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
