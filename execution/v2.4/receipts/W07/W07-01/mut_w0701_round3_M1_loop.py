"""Round 3b: keep re-running M1 until the pending branch is actually reached, so the mutant is either caught or proven innocent.

The earlier M1 runs died on infrastructure, not on the mutant: the GitHub attempt failed against a local proxy that
was not accepting connections, so the incomplete-page branch - the only branch M1 changes - was never executed. Each
attempt here is recorded with the message it produced, and the loop stops as soon as a run reaches the pending
branch, which is the precondition for the row to be able to fail.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
TARGET = os.path.join("tests", "sources", "live", "main.go")
ORIG = open(TARGET, "rb").read()
OLD = b'"opaque_cursor": capture.Page.NextCursor, "covered_until": nil,'
NEW = b'"opaque_cursor": capture.Page.NextCursor, "covered_until": r.WindowTo,'
assert ORIG.count(OLD) == 1, ORIG.count(OLD)
EXPECTED_KILL = {"W0701-GITHUB-CURSOR-ADVANCED", "W0701-PAPER-CURSOR-ADVANCED",
                 "W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE"}


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-01")
    p = subprocess.run([sys.executable, "-X", "utf8", os.path.join("tests", "sources", "check", "main.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=1500)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    d = json.loads(lines[-1]) if lines else {}
    branches = [x.get("observed") for x in (d.get("diagnostics") or []) if str(x.get("probe", "")).startswith("cursor-branch")]
    return {"status": d.get("status"), "assertions": d.get("assertions"),
            "failed": sorted(f["id"] for f in (d.get("failures") or [])),
            "blocked": [b[0] if isinstance(b, list) else b for b in (d.get("blocked_kinds") or [])],
            "branches": sum([b for b in branches if isinstance(b, list)], []) or branches}


runs = []
verdict = "not-exercised"
try:
    open(TARGET, "wb").write(ORIG.replace(OLD, NEW, 1))
    for attempt in range(1, 5):
        outcome = run_check()
        runs.append({"attempt": attempt, **outcome})
        if "pending" in json.dumps(outcome.get("branches")):
            verdict = "caught" if set(outcome["failed"]) & EXPECTED_KILL else "exercised-and-survived"
            break
finally:
    open(TARGET, "wb").write(ORIG)
    restored = hashlib.sha256(open(TARGET, "rb").read()).hexdigest() == hashlib.sha256(ORIG).hexdigest()
    clean = run_check()

out = {"mutant": "M1-incomplete-page-claims-coverage", "verdict": verdict, "runs": runs,
       "restored_byte_exact": restored, "clean_recheck": clean}
path = os.path.join("execution", "v2.4", "receipts", "W07", "W07-01", "mutation_selfcheck_round3_M1.json")
open(path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
print("verdict", verdict, "| restored", restored, "| clean", clean.get("status"), clean.get("assertions"))
for r in runs:
    print("  attempt", r["attempt"], r["status"], "branches", r["branches"], "failed", r["failed"][:4],
          "blocked", r["blocked"])
