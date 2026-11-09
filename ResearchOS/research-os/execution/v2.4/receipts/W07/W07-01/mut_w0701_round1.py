"""W07-01 mutation matrix round 1: two product mutants against the live probe, each restored byte-for-byte.

M1 makes an incomplete page claim a covered window - the exact defect the card's second sentence names ("失败不推进
成功游标"). M2 stops verifying the sealed bytes against what was fetched. Anchors are taken from the delivered file
bytes with an occurrence assert, so an anchor that does not match is reported as anchor-missing rather than quietly
replacing the wrong text.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TARGET = os.path.join(ROOT, "tests", "sources", "live", "main.go")
ORIG = open(TARGET, "rb").read()
GO = json.load(open(os.path.join(ROOT, "execution/toolchains/locked.json"), encoding="utf-8-sig"))["tools"]["go"]["path"]

MUTANTS = [
    {"name": "M1-incomplete-page-claims-coverage",
     "old": b'"opaque_cursor": capture.Page.NextCursor, "covered_until": nil,',
     "new": b'"opaque_cursor": capture.Page.NextCursor, "covered_until": r.WindowTo,',
     "expect_any": ["W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE", "W0701-GITHUB-CURSOR-ADVANCED",
                    "W0701-PAPER-CURSOR-ADVANCED"]},
    {"name": "M2-sealed-bytes-never-verified",
     "old": b'if e = verifyArtifact(s.Handler(), token, projectID, mustArtifact(db, projectID, ev), item.Body); e != nil {',
     "new": b'if e = error(nil); e != nil {',
     "expect_any": ["W0701-GITHUB-EVIDENCE-FIELDS", "W0701-PAPER-EVIDENCE-FIELDS",
                    "W0701-GITHUB-LIVE-READ", "W0701-PAPER-LIVE-READ"]},
]


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W07", RESEARCHOS_CHECK_ID="W07-01")
    p = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tests/sources/check/main.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                       cwd=ROOT, timeout=1500)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "stderr": (p.stderr or "")[:300]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"),
            "failed": sorted(f["id"] for f in (d.get("failures") or [])),
            "blocked": [b[0] if isinstance(b, (list, tuple)) else b for b in (d.get("blocked_kinds") or [])]}


results = []
try:
    for m in MUTANTS:
        text = ORIG
        if text.count(m["old"]) != 1:
            results.append({"mutant": m["name"], "class": "anchor-missing", "occurrences": text.count(m["old"])})
            continue
        open(TARGET, "wb").write(text.replace(m["old"], m["new"], 1))
        outcome = run_check()
        killed = [e for e in m["expect_any"] if e in outcome.get("failed", [])]
        results.append({"mutant": m["name"], "outcome": outcome, "expect_any": m["expect_any"],
                        "killed_by": killed,
                        "class": "caught" if killed else ("survived" if outcome.get("status") == "PASS"
                                                          else "other-failure")})
finally:
    open(TARGET, "wb").write(ORIG)
    restored = hashlib.sha256(open(TARGET, "rb").read()).hexdigest() == hashlib.sha256(ORIG).hexdigest()
    clean = run_check()

print(json.dumps({"restored_byte_exact": restored, "clean_recheck": clean, "mutants": results},
                 ensure_ascii=False, indent=1))
