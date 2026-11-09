"""Reviewer mutation pass round 2 for W13-02: four mutants aimed at the card's own negatives at the SCREEN layer,
plus a revision-CAS removal at the library layer.

Unlike round 1 this driver records, for every run, the full failure detail and the sha256 of the five files the
check program reads, before and after the run. Round 1 left six of eight runs reporting
W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE among their failures - a row none of those mutants can reach, which
passes when the node driver is run standalone - so the discriminator between "the gate moved" and "the environment
moved under the gate" is needed, not assumed.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
CLIENT = os.path.join(ROOT, "apps", "web", "src", "v2client.js")
SCREEN = os.path.join(ROOT, "apps", "web", "src", "continuity.jsx")
PROBE = os.path.join(ROOT, "tests", "ui", "continuity", "producer_probe.py")
CHECK = os.path.join(ROOT, "tests", "ui", "continuity", "check", "main.py")
WATCH = ["apps/web/src/v2client.js", "apps/web/src/continuity.jsx", "apps/desktop/main/lib/v2.js",
         "tests/ui/continuity/producer_probe.py", "tests/ui/continuity/surfaces_driver.js"]

MUTANTS = [
    {"name": "R9-screen-cancels-nothing (cancel producer deleted)",
     "file": SCREEN,
     "old": "<Producer method=\"session.control\" data-action=\"CANCEL\" disabled={!!busy || !hasRun} onClick={() => run('session.control', { action: 'CANCEL', target_id: snapshot.active_run_id, reason: '用户在工作台请求取消' })}>取消</Producer>",
     "new": "",
     "expect": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND", "W1302-EACH-METHOD-HAS-A-CONTROL-IN-THE-SCREEN"]},
    {"name": "R10-screen-stops-adopting-a-body-session-id",
     "file": SCREEN,
     "old": "        if (value.session_id && !value.snapshot) client.adopt({ sessionId: value.session_id })",
     "new": "",
     "expect": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"]},
    {"name": "R11-recovery-resend-instead-of-re-read",
     "file": SCREEN,
     "old": "  function resync() { return run('session.events', { after_sequence: watermark, limit: 200 }) }",
     "new": "  function resync() { return run('session.send', { text: chat, attachment_artifact_ids: [], delivery: 'NORMAL' }) }",
     "expect": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"]},
    {"name": "R12-renderer-drops-the-expected-revision-guard",
     "file": CLIENT,
     "old": "    if (env.expected_revision === null) return { ok: false, reason: 'MISSING_FIELD:expected_revision', method };",
     "new": "    if (false) return { ok: false, reason: 'MISSING_FIELD:expected_revision', method };",
     "expect": ["W1302-REFUSAL-REASONS-AGREE", "W1302-ENVELOPES-AGREE-ACROSS-SURFACES"]},
]

CARD_IDS = set(re.findall(r'"(W1302-[A-Z0-9._-]+)"', open(CHECK, encoding="utf-8").read()))


def snap():
    return {p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest() for p in WATCH}


def run_check():
    before = snap()
    env = dict(os.environ, RESEARCHOS_TASK_ID="W13", RESEARCHOS_CHECK_ID="W13-02")
    p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=ROOT, timeout=1800)
    after = snap()
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "rc": p.returncode, "stderr": (p.stderr or "")[:300],
                "tree_moved_during_run": [q for q in WATCH if before[q] != after[q]]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"), "rc": p.returncode,
            "failed": [{"id": f["id"], "detail": str(f.get("detail"))[:260]} for f in (d.get("failures") or [])],
            "tree_moved_during_run": [q for q in WATCH if before[q] != after[q]]}


orig = {p: open(p, "rb").read() for p in {m["file"] for m in MUTANTS}}
baseline = {p: hashlib.sha256(b).hexdigest() for p, b in orig.items()}
results = []
try:
    for m in MUTANTS:
        text = orig[m["file"]].decode("utf-8")
        count = text.count(m["old"])
        if count != 1:
            results.append({"mutant": m["name"], "class": "anchor-missing", "occurrences": count})
            continue
        open(m["file"], "w", encoding="utf-8", newline="\n").write(text.replace(m["old"], m["new"], 1))
        outcome = run_check()
        names = [f["id"] for f in outcome.get("failed", [])] if isinstance(outcome.get("failed"), list) else []
        killed = [e for e in m["expect"] if e in names]
        if killed:
            cls = "caught"
        elif outcome.get("status") == "PASS":
            cls = "survived"
        elif outcome.get("status") == "NOJSON":
            cls = "crashed-or-ill-formed"
        elif set(names) & CARD_IDS:
            cls = "caught-by-gate-id-only"
        else:
            cls = "other-failure"
        results.append({"mutant": m["name"], "file": os.path.relpath(m["file"], ROOT).replace("\\", "/"),
                        "outcome": outcome, "expected": m["expect"], "killed_by": killed,
                        "other_card_ids_moved": sorted((set(names) & CARD_IDS) - set(killed)), "class": cls})
finally:
    for path, blob in orig.items():
        open(path, "wb").write(blob)
    restored = all(hashlib.sha256(open(p, "rb").read()).hexdigest() == h for p, h in baseline.items())
    clean = run_check()

print(json.dumps({"reviewer_id": "qoder-desktop:/root/w1302_verifier_r1", "round": 2,
                  "restored_byte_exact": restored,
                  "restored_hashes": {os.path.relpath(p, ROOT).replace("\\", "/"): hashlib.sha256(open(p, "rb").read()).hexdigest() for p in orig},
                  "clean_recheck": clean, "mutants": results}, ensure_ascii=False, indent=1))
