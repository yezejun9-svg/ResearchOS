"""Reviewer probes that need a temporary, hash-verified source edit (round 1).

P1  V05 redo: the executor's/ my own symlink-branch mutant only went red because the replacement
    left `target` unused, i.e. a compile failure, not a behavioural kill. This variant keeps the
    branch compiling and changes only the message, so the bucket reports whether any row can see
    that branch at all on this host.
P2  Permission-leg isolation probe: the receipt's characterisation row says the permission leg
    cannot be isolated at the search surface because "a second principal with equal roles and
    equal grants sees zero hits". In the card's own sequence the snapshot was ALREADY stale and
    already zero-hit before the principal switch, so that observation is confounded. This probe
    builds the clean construction: one fresh CURRENT snapshot, searched by two principals, with
    nothing else varied. It prints both snapshot_hash values and both hit counts.

Both probes restore the file and prove the restored bytes match the digest captured before the
edit; anything else is reported, not hidden.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
LOCAL = "adapters/retrieval/local.go"
TESTFILE = "internal/domain/evidence_w0902_test.go"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", GOTOOLCHAIN="local", RESEARCHOS_GO=GO,
           GOPATH=os.path.join(ROOT, ".local", "gopath"),
           GOCACHE=os.path.join(ROOT, ".local", "gocache"))

PROBE = '''
// TestW0902ReviewProbe is a reviewer probe, temporary, reverted in the same run.
func TestW0902ReviewProbe(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const marker = "W0902_REVIEW_PROBE_MARKER_4417"
	if err := os.WriteFile(filepath.Join(rootPath, "probe.txt"), []byte("probe body "+marker+"\\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, _ := w09LocalEvidence(t, f, rootID, "probe.txt", "reviewer probe")
	snapshotID := Str(artifact, "id")
	ownerState := f.state()
	res := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker,
		"snapshot_ids": []any{snapshotID}, "limit": 10, "expected_state_revision": ownerState["revision"]})
	ownerHash, ownerHits := Str(res, "snapshot_hash"), len(Arr(res, "hits"))
	// Same snapshot, same project, same state revision: only the principal changes.
	f.switchPrincipal("w0902_review_reader", []string{"READER"})
	secondState := f.state()
	res2 := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker,
		"snapshot_ids": []any{snapshotID}, "limit": 10, "expected_state_revision": secondState["revision"]})
	secondHash, secondHits := Str(res2, "snapshot_hash"), len(Arr(res2, "hits"))
	t.Logf("REVIEW_PROBE_JSON owner_hash=%s second_hash=%s owner_hits=%d second_hits=%d rev_owner=%v rev_second=%v key_moved=%v warnings_second=%v body_second=%s",
		ownerHash, secondHash, ownerHits, secondHits, ownerState["revision"], secondState["revision"],
		ownerHash != secondHash, Arr(res2, "warnings"), string(Bytes(res2)))
}
'''


def digest(path):
    return hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest()


def edit(path, pairs=None, append_text=None):
    full = os.path.join(ROOT, path)
    text = open(full, encoding="utf-8").read()
    for anchor, replacement in (pairs or []):
        if text.count(anchor) != 1:
            return text, "anchor-missing:%d" % text.count(anchor)
        text = text.replace(anchor, replacement, 1)
    if append_text:
        text = text + append_text
    open(full, "w", encoding="utf-8", newline="").write(text)
    return text, "applied"


def restore(path, original, want):
    full = os.path.join(ROOT, path)
    open(full, "w", encoding="utf-8", newline="").write(original)
    return digest(path) == want


def run(cmd, timeout=900):
    return subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, timeout=timeout)


def main():
    results = {}

    # ---- P1: compile-safe symlink-branch mutant
    path, before = LOCAL, digest(LOCAL)
    original = open(os.path.join(ROOT, path), encoding="utf-8").read()
    anchor = 'return fmt.Errorf("path component %q is a symbolic link to %q; snapshots must be a regular file inside the registered root", prefix, target)'
    replacement = 'return fmt.Errorf("path component %q is a link-shaped file at %q; snapshots must be a regular file inside the registered root", prefix, target)'
    _, state = edit(path, [(anchor, replacement)])
    p1 = {"state": state}
    if state == "applied":
        completed = run([GO, "test", "-count=1", "-run", "^TestW0902LinkAndAbsenceRefusalsDiffer$",
                         "./internal/domain"], timeout=900)
        p1["rc"] = completed.returncode
        p1["output_tail"] = completed.stdout.decode("utf-8", "replace")[-700:]
        p1["bucket"] = "survived" if completed.returncode == 0 else "caught"
    p1["restored"] = restore(path, original, before)
    results["P1_symlink_branch_compile_safe"] = p1
    print("P1", json.dumps(p1, ensure_ascii=False)[:900])

    # ---- P2: permission-leg isolation probe
    path, before = TESTFILE, digest(path)
    original = open(os.path.join(ROOT, path), encoding="utf-8").read()
    _, state = edit(path, None, PROBE)
    p2 = {"state": state}
    if state == "applied":
        completed = run([GO, "test", "-count=1", "-v", "-run", "^TestW0902ReviewProbe$", "./internal/domain"],
                        timeout=900)
        text = completed.stdout.decode("utf-8", "replace")
        line = [l for l in text.splitlines() if "REVIEW_PROBE_JSON" in l]
        p2["rc"] = completed.returncode
        p2["probe_line"] = line[-1].strip()[:1200] if line else None
        p2["test_output_tail"] = text[-900:]
        p2["stderr_tail"] = completed.stderr.decode("utf-8", "replace")[-500:]
    p2["restored"] = restore(path, original, before)
    results["P2_permission_leg_isolation"] = p2
    print("P2", json.dumps(p2, ensure_ascii=False)[:1200])

    results["tree_clean_after_probes"] = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                                        cwd=ROOT, capture_output=True, text=True).stdout.strip() == ""
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reviewer_probes_round1.json")
    open(dest, "w", encoding="utf-8").write(json.dumps(results, ensure_ascii=False, indent=1))
    print("wrote", dest, "tree_clean", results["tree_clean_after_probes"])


if __name__ == "__main__":
    sys.exit(main())
