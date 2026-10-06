"""Reviewer run: does the CARD's OWN check program catch an incomplete page that claims a covered window?

Both mutants are applied together for the duration of one check run:
  tests/sources/live/main.go        pending branch writes covered_until = window_to   (the builder's M1 harness)
  internal/domain/sources.go:180    guard wrapped in false && (...) so it cannot fire (the builder's P-M1)

If the check is honest, the run must go RED on W0701-GITHUB-CURSOR-ADVANCED and on
W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE. If it stays green, the invariant row is decoration and M1 survives
for real. The builder never managed this because GitHub refused during every mutant run; here GitHub answers on a
clean run, so the pending branch is reachable. Every attempt is recorded, including any that GitHub refused.
Files are restored byte-exactly in a finally block.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import uuid

REPO = r"D:/作品集/ResearchOS/research-os"
DOMAIN = os.path.join(REPO, "internal", "domain", "sources.go")
PROBE = os.path.join(REPO, "tests", "sources", "live", "main.go")
CHECK = os.path.join(REPO, "tests", "sources", "check", "main.py")

GUARD_ANCHOR = '} else if newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to {'
GUARD_MUTANT = '} else if false && (newCovered != oldCovered || Str(b, "opaque_cursor") == "" || b["pending_window_from"] != from || b["pending_window_to"] != to) {'
OVERCLAIM_ANCHOR = ('body := domain.Object{"opaque_cursor": capture.Page.NextCursor, "covered_until": nil, '
                    '"last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": r.WindowFrom, '
                    '"pending_window_to": r.WindowTo, "last_cycle_id": nil}')
OVERCLAIM_MUTANT = ('body := domain.Object{"opaque_cursor": capture.Page.NextCursor, "covered_until": r.WindowTo, '
                    '"last_success_at": domain.Now(), "retry_after": nil, "pending_window_from": r.WindowFrom, '
                    '"pending_window_to": r.WindowTo, "last_cycle_id": nil}')


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def patch(path, anchor, mutant):
    t = io.open(path, encoding="utf-8").read()
    assert t.count(anchor) == 1
    io.open(path, "w", encoding="utf-8", newline="").write(t.replace(anchor, mutant, 1))


def main():
    pd, pp = open(DOMAIN, "rb").read(), open(PROBE, "rb").read()
    sd, sp = sha(DOMAIN), sha(PROBE)
    attempts = []
    try:
        patch(PROBE, OVERCLAIM_ANCHOR, OVERCLAIM_MUTANT)
        patch(DOMAIN, GUARD_ANCHOR, GUARD_MUTANT)
        assert sha(DOMAIN) != sd and sha(PROBE) != sp
        env = dict(os.environ, RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-01", RESEARCHOS_CASE_ID="",
                   PYTHONUTF8="1", GOTOOLCHAIN="local", GOENV="off")
        env.pop("RESEARCHOS_SOURCE_KIND", None)
        for i in (1, 2, 3):
            t0 = time.time()
            p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", cwd=REPO, env=env, timeout=1500)
            lines = [l.strip() for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
            rep = json.loads(lines[-1]) if lines else {}
            attempts.append({"attempt": i, "rc": p.returncode, "seconds": round(time.time() - t0, 1),
                             "status": rep.get("status"), "assertions": rep.get("assertions"),
                             "failures": [{"id": f["id"], "detail": f["detail"][:400]} for f in rep.get("failures", [])],
                             "blocked_kinds": rep.get("blocked_kinds"),
                             "captures": rep.get("captures"),
                             "cursor_branch_diagnostics": [d for d in (rep.get("diagnostics") or [])
                                                           if str(d.get("probe", "")).startswith("cursor-branch")],
                             "evidence_run_dir": rep.get("evidence_run_dir")})
            if rep.get("status") == "FAIL" and any(f["id"] == "W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE"
                                                   for f in rep.get("failures", [])):
                break
            if rep.get("status") == "PASS":
                break
            time.sleep(3)
    finally:
        io.open(DOMAIN, "wb").write(pd)
        io.open(PROBE, "wb").write(pp)

    result = {
        "pristine_sha256": {"internal/domain/sources.go": sd, "tests/sources/live/main.go": sp},
        "restored_sha256": {"internal/domain/sources.go": sha(DOMAIN), "tests/sources/live/main.go": sha(PROBE)},
        "restored_byte_exact": sha(DOMAIN) == sd and sha(PROBE) == sp,
        "git_dirty_after_restore": subprocess.run(["git", "-C", REPO, "status", "--porcelain", "--untracked-files=no"],
                                                  capture_output=True, text=True).stdout.strip(),
        "attempts": attempts,
    }
    killed = [a for a in attempts if any(f["id"] == "W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE"
                                        for f in a["failures"])]
    result["M1_harness_killed_by_the_card_check"] = bool(killed)
    result["killing_rows"] = sorted({f["id"] for a in attempts for f in a["failures"]}) if killed else []
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
