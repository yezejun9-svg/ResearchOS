"""Round 1b: the two mutants round 1 could not apply because their anchors did not match the delivered text.

C and D in mutation_selfcheck_round1.json were classified anchor-missing, which is not a kill and not a survivor -
it is a row that measured nothing. The anchors here are taken from the file bytes rather than from memory.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT = os.path.join(ROOT, "apps", "web", "src", "v2client.js")
ORIG = open(CLIENT, "rb").read()

MUTANTS = [
    {"name": "C-client-adopts-revision-from-any-reply",
     "old": "    if (result.kind === 'COMPLETED' || result.kind === 'ACKNOWLEDGED') {",
     "new": "    if (true) {",
     "expect": ["W1302-REFUSED-WRITE-DOES-NOT-REBASELINE", "W1302-IN-PROGRESS-DOES-NOT-REBASELINE"]},
    {"name": "D-producer-surface-map-loses-a-method",
     "old": " 'session.handoff': 'continuity',",
     "new": ",",
     "expect": ["W1302-PRODUCERS-COVER-EVERY-METHOD"]},
]


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W13", RESEARCHOS_CHECK_ID="W13-02")
    p = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tests/ui/continuity/check/main.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                       cwd=ROOT, timeout=1500)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "stderr": (p.stderr or "")[:300]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"),
            "failed": sorted(f["id"] for f in (d.get("failures") or []))}


results = []
try:
    for m in MUTANTS:
        text = ORIG.decode("utf-8")
        if text.count(m["old"]) != 1:
            results.append({"mutant": m["name"], "class": "anchor-missing", "occurrences": text.count(m["old"])})
            continue
        open(CLIENT, "w", encoding="utf-8", newline="\n").write(text.replace(m["old"], m["new"], 1))
        outcome = run_check()
        killed = [e for e in m["expect"] if e in outcome.get("failed", [])]
        results.append({"mutant": m["name"], "outcome": outcome, "expected": m["expect"], "killed_by": killed,
                        "class": "caught" if killed else ("survived" if outcome.get("status") == "PASS" else
                                                          "other-failure")})
finally:
    open(CLIENT, "wb").write(ORIG)
    restored = hashlib.sha256(open(CLIENT, "rb").read()).hexdigest() == hashlib.sha256(ORIG).hexdigest()
    clean = run_check()

print(json.dumps({"restored_byte_exact": restored, "clean_recheck": clean, "mutants": results},
                 ensure_ascii=False, indent=1))
