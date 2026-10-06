"""Reviewer experiment: is the product guard at internal/domain/sources.go:180-181 actually REACHABLE?

The builder disclosed that deleting it is invisible to every check in the tree and reasoned that reaching it
"honestly" needs a multi-page stub whose base URL would have to be threaded through internal/domain and the frozen
source_configs schema.

This script tests that reasoning without any base-URL hook and without a second page. It makes the card's own live
probe over-claim from its pending branch (tests/sources/live/main.go, else branch: covered_until nil -> r.WindowTo)
and runs it against the REAL GitHub endpoint, which returns an incomplete first page in a clean run.

  A = harness over-claims, guard INTACT      -> the PUT must be refused
  B = harness over-claims, guard DELETED     -> the PUT must be accepted and land a covered window in the DB
      while page_complete stays false

A and B differ in exactly one character-level edit to internal/domain/sources.go, so whatever A refuses and B
accepts IS the guard. Both files are restored byte-exactly in a finally block and re-hashed.
"""
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

REPO = r"D:/作品集/ResearchOS/research-os"
DOMAIN = os.path.join(REPO, "internal", "domain", "sources.go")
PROBE = os.path.join(REPO, "tests", "sources", "live", "main.go")

GUARD_ANCHOR = '} else if newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to {'
GUARD_MUTANT = '} else if false && (newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to) {'

OVERCLAIM_ANCHOR = ('body := domain.Object{"opaque_cursor": capture.Page.NextCursor, "covered_until": nil, '
                    '"last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": r.WindowFrom, '
                    '"pending_window_to": r.WindowTo, "last_cycle_id": nil}')
OVERCLAIM_MUTANT = ('body := domain.Object{"opaque_cursor": capture.Page.NextCursor, "covered_until": r.WindowTo, '
                    '"last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": r.WindowFrom, '
                    '"pending_window_to": r.WindowTo, "last_cycle_id": nil}')

GO = json.loads(open(os.path.join(REPO, "execution", "toolchains", "locked.json"), encoding="utf-8-sig").read())["tools"]["go"]["path"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def patch(path, anchor, mutant):
    t = io.open(path, encoding="utf-8").read()
    assert t.count(anchor) == 1, "anchor count %d in %s" % (t.count(anchor), path)
    io.open(path, "w", encoding="utf-8", newline="").write(t.replace(anchor, mutant, 1))


def restore(path, pristine):
    io.open(path, "wb").write(pristine)


def build_probe(out):
    r = subprocess.run([GO, "build", "-o", out, "./tests/sources/live"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=REPO, env=dict(os.environ, GOFLAGS="-mod=mod"),
                       timeout=600)
    return r


def run_probe(binary, workdir):
    os.makedirs(workdir, exist_ok=True)
    env = dict(os.environ, RESEARCHOS_SOURCE_KIND="GITHUB",
               RESEARCHOS_SOURCE_OUTPUT_DIR=os.path.abspath(workdir))
    started = time.time()
    p = subprocess.run([binary], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, cwd=REPO, timeout=300)
    rep_path = os.path.join(workdir, "report-GITHUB.json")
    rep = json.loads(io.open(rep_path, encoding="utf-8").read()) if os.path.isfile(rep_path) else None
    res = {"rc": p.returncode, "seconds": round(time.time() - started, 2),
           "stderr_tail": (p.stderr or "")[-300:], "report": rep}
    if rep and rep.get("db_path"):
        db = rep["db_path"] if os.path.isabs(rep["db_path"]) else os.path.join(REPO, rep["db_path"])
        if os.path.isfile(db):
            con = sqlite3.connect("file:" + db.replace("\\", "/") + "?mode=ro", uri=True)
            try:
                row = con.execute("SELECT kind, revision, body FROM domain_objects WHERE id=?",
                                  (rep.get("cursor_id"),)).fetchone()
                body = json.loads(row[2]) if row else {}
                res["db_cursor"] = {"kind": row[0] if row else None, "revision": row[1] if row else None,
                                    "covered_until": body.get("covered_until"),
                                    "pending_window_from": body.get("pending_window_from"),
                                    "opaque_cursor": body.get("opaque_cursor")}
            finally:
                con.close()
    return res


def main():
    base = os.path.join(REPO, ".local", "w0701-reviewer-guardreach", str(uuid.uuid4()))
    os.makedirs(base, exist_ok=True)
    pristine_domain = open(DOMAIN, "rb").read()
    pristine_probe = open(PROBE, "rb").read()
    out = {"pristine_sha256": {"internal/domain/sources.go": sha(DOMAIN), "tests/sources/live/main.go": sha(PROBE)},
           "anchors_unique": {
               "guard": io.open(DOMAIN, encoding="utf-8").read().count(GUARD_ANCHOR),
               "probe_overclaim": io.open(PROBE, encoding="utf-8").read().count(OVERCLAIM_ANCHOR)}}
    try:
        patch(PROBE, OVERCLAIM_ANCHOR, OVERCLAIM_MUTANT)
        out["probe_mutant_applied"] = sha(PROBE) != out["pristine_sha256"]["tests/sources/live/main.go"]

        # ---- A: harness over-claims while the guard is intact
        bA = os.path.join(base, "A", "w0701-live.exe")
        os.makedirs(os.path.dirname(bA), exist_ok=True)
        bres = build_probe(bA)
        out["A_build"] = {"rc": bres.returncode, "err": (bres.stderr or bres.stdout)[-300:]}
        if bres.returncode == 0:
            out["A_overclaim_with_guard_intact"] = run_probe(bA, os.path.join(base, "A", "run"))

        # ---- B: same harness, guard now inert
        patch(DOMAIN, GUARD_ANCHOR, GUARD_MUTANT)
        out["guard_mutant_applied"] = sha(DOMAIN) != out["pristine_sha256"]["internal/domain/sources.go"]
        bB = os.path.join(base, "B", "w0701-live.exe")
        os.makedirs(os.path.dirname(bB), exist_ok=True)
        bres = build_probe(bB)
        out["B_build"] = {"rc": bres.returncode, "err": (bres.stderr or bres.stdout)[-300:]}
        if bres.returncode == 0:
            out["B_overclaim_with_guard_deleted"] = run_probe(bB, os.path.join(base, "B", "run"))
    finally:
        restore(DOMAIN, pristine_domain)
        restore(PROBE, pristine_probe)
        out["restored"] = {p: sha(p) for p in (DOMAIN, PROBE)}
        out["restored_byte_exact"] = (out["restored"][DOMAIN] == out["pristine_sha256"]["internal/domain/sources.go"]
                                      and out["restored"][PROBE] == out["pristine_sha256"]["tests/sources/live/main.go"])
        out["git_dirty_after_restore"] = subprocess.run(
            ["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True).stdout.strip()

    # ---- verdict on reachability
    a, b = out.get("A_overclaim_with_guard_intact", {}), out.get("B_overclaim_with_guard_deleted", {})
    a_rep, b_rep = a.get("report") or {}, b.get("report") or {}
    out["guard_reachability_verdict"] = {
        "A_probe_rc": a.get("rc"), "A_report_status": a_rep.get("status"),
        "A_failure_text": (a_rep.get("failure") or "")[:300],
        "A_db_covered_until": (a.get("db_cursor") or {}).get("covered_until"),
        "B_probe_rc": b.get("rc"), "B_report_status": b_rep.get("status"),
        "B_db_covered_until": (b.get("db_cursor") or {}).get("covered_until"),
        "B_page_complete": b_rep.get("page_complete"),
        "B_over_claimed_window_in_db": bool((b.get("db_cursor") or {}).get("covered_until")) and b_rep.get("page_complete") is False,
        "guard_is_reachable_by_this_card_own_probe": a.get("rc") == 1 and b.get("rc") == 0,
    }
    out["workdir"] = base
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
