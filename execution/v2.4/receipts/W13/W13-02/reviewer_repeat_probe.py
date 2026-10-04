"""Reviewer repeatability pass for W13-02's own verification command.

The card reports two PASS 28 rounds. Measured here: the same command on the same tree returned PASS 28, PASS 28 and
COMMAND_FAILED 27 in three dispatcher rounds, and inside the reviewer's mutation pass six of eight runs reported
W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE among their failures - including two mutants (R5 screen payload,
R6 stub fixture) that cannot reach that row. This script runs the check program N times on a clean tree and dumps
the FULL failure detail, so a red run is classified from what the program actually said rather than from a guess.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", ".."))
CHECK = os.path.join(ROOT, "tests", "ui", "continuity", "check", "main.py")
WATCH = ["apps/web/src/v2client.js", "apps/web/src/continuity.jsx", "apps/desktop/main/lib/v2.js",
         "tests/ui/continuity/producer_probe.py", "tests/ui/continuity/surfaces_driver.js"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 3

runs = []
for i in range(N):
    before = {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in WATCH}
    env = dict(os.environ, RESEARCHOS_TASK_ID="W13", RESEARCHOS_CHECK_ID="W13-02")
    p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=ROOT, timeout=1800)
    after = {q: hashlib.sha256(open(os.path.join(ROOT, q), "rb").read()).hexdigest() for q in WATCH}
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    d = json.loads(lines[-1]) if lines else {"status": "NOJSON", "stderr": (p.stderr or "")[:400]}
    runs.append({"i": i, "status": d.get("status"), "assertions": d.get("assertions"), "rc": p.returncode,
                 "failures": d.get("failures", []), "not_verified_count": len(d.get("not_verified", [])),
                 "tree_changed_during_run": [q for q in WATCH if before[q] != after[q]],
                 "watched_hashes_stable": before == after})
print(json.dumps({"reviewer_id": "qoder-desktop:/root/w1302_verifier_r1", "runs": runs}, ensure_ascii=False, indent=1))
