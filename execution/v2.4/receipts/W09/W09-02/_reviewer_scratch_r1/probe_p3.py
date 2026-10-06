"""Reviewer probe P3: does W0902-KEY-CHANGES-WHEN-SEALED-CONTENT-CHANGES vary one leg?

The row's own evidence says "varied": "source bytes only". The key is
Hash([project, state_revision, grantHash, retrievalRevision, manifest]) and the step that changes
the bytes also calls RefreshLocalSnapshots. If the project state revision moves in that step, or the
snapshot leaves the manifest, then the row is an invalidation witness (which is what action 1 asks
for) and NOT a single-leg isolation, contradicting the receipt's actions_map claim that "each
runtime-varied leg was tested on its own".

Prints the state revision, the hash and the hit count before/after the refresh, plus a control that
changes the bytes WITHOUT refreshing. Temporary edit, hash-verified restore.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
TESTFILE = "internal/domain/evidence_w0902_test.go"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", GOTOOLCHAIN="local", RESEARCHOS_GO=GO,
           GOPATH=os.path.join(ROOT, ".local", "gopath"),
           GOCACHE=os.path.join(ROOT, ".local", "gocache"))

PROBE = '''
// TestW0902ReviewProbeP3 is a reviewer probe, temporary, reverted in the same run.
func TestW0902ReviewProbeP3(t *testing.T) {
	f := contextFixture(t)
	ctx := context.Background()
	rootPath := t.TempDir()
	const marker = "W0902_P3_MARKER_6620"
	target := filepath.Join(rootPath, "leg.txt")
	if err := os.WriteFile(target, []byte("v1 body "+marker+"\\n"), 0600); err != nil {
		t.Fatal(err)
	}
	rootID, err := f.s.RegisterLocalRoot(ctx, f.token, f.project, rootPath)
	if err != nil {
		t.Fatal(err)
	}
	artifact, _ := w09LocalEvidence(t, f, rootID, "leg.txt", "reviewer probe p3")
	snapshotID := Str(artifact, "id")
	search := func() (string, int64, int, string) {
		st := f.state()
		res := f.expect(200, "POST", f.path("/search"), ID(), "", Object{"query": marker,
			"snapshot_ids": []any{snapshotID}, "limit": 10, "expected_state_revision": st["revision"]})
		rev, _ := Num(st, "revision")
		return Str(res, "snapshot_hash"), rev, len(Arr(res, "hits")), string(Bytes(res))
	}
	h0, r0, n0, _ := search()
	if err := os.WriteFile(target, []byte("v2 body "+marker+" changed\\n"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := f.s.RefreshLocalSnapshots(ctx, f.token, f.project); err != nil {
		t.Fatal(err)
	}
	h1, r1, n1, body1 := search()
	if err := os.WriteFile(target, []byte("v3 body "+marker+" again\\n"), 0600); err != nil {
		t.Fatal(err)
	}
	h2, r2, n2, _ := search()
	t.Logf("REVIEW_P3_JSON hash0=%s rev0=%d hits0=%d || after_refresh hash1=%s rev1=%d hits1=%d || bytes_changed_no_refresh hash2=%s rev2=%d hits2=%d || revision_moved_with_refresh=%v hit_dropped_with_refresh=%v key_moved_without_refresh=%v old_body_still_served_without_refresh=%v new_body_served_without_refresh=%v stale_marker_in_refresh_reply=%v",
		h0, r0, n0, h1, r1, n1, h2, r2, n2, r1 != r0, n1 != 1, h2 != h0, n2 == 1,
		strings.Contains(body1, "changed"), strings.Contains(body1, "v2 body"))
}
'''


def digest(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def main():
    full = os.path.join(ROOT, TESTFILE)
    before, original = digest(TESTFILE), open(full, encoding="utf-8").read()
    open(full, "w", encoding="utf-8", newline="").write(original + PROBE)
    out = {}
    try:
        completed = subprocess.run([GO, "test", "-count=1", "-v", "-run", "^TestW0902ReviewProbeP3$",
                                    "./internal/domain"], cwd=ROOT, env=ENV, capture_output=True, timeout=900)
        text = completed.stdout.decode("utf-8", "replace")
        lines = [l for l in text.splitlines() if "REVIEW_P3_JSON" in l]
        out = {"rc": completed.returncode, "line": lines[-1].strip() if lines else None,
               "tail_if_no_line": "" if lines else text[-800:],
               "stderr_tail": completed.stderr.decode("utf-8", "replace")[-400:]}
    except subprocess.TimeoutExpired as exc:
        out = {"rc": "timeout", "detail": str(exc)[:300]}
    finally:
        open(full, "w", encoding="utf-8", newline="").write(original)
        out["restored_byte_identical"] = digest(TESTFILE) == before
    print(json.dumps(out, ensure_ascii=False)[:2500])
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reviewer_probe_p3_round1.json")
    open(dest, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
    print("tree_clean", subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                        capture_output=True, text=True).stdout.strip() == "")


if __name__ == "__main__":
    sys.exit(main())
