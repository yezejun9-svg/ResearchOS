"""W13-02 mutation matrix: six single-edit mutants against the delivered files.

Each mutant is expected to be killed by a named assertion id of tests/ui/continuity/check/main.py. The tree is
restored byte-for-byte in a finally clause and a clean re-run must return to the baseline id set, so a survivor
is a measurement, not a guess. Anchors are matched with an occurrence assert: an anchor that appears twice (or
not at all) is reported as anchor-missing rather than quietly replacing the wrong bytes.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLIENT = os.path.join(ROOT, "apps", "web", "src", "v2client.js")
SCREEN = os.path.join(ROOT, "apps", "web", "src", "continuity.jsx")

MUTANTS = [
    {"name": "A-renderer-drops-the-model-epoch-rule", "file": CLIENT,
     "old": "  if (method === 'host.configure' && (Object.prototype.hasOwnProperty.call(payload, 'model_id') ||\n"
            "    Object.prototype.hasOwnProperty.call(payload, 'provider_id')) && env.writer_epoch === null) {\n"
            "    return { ok: false, reason: 'MODEL_CHANGE_WITHOUT_EPOCH', method };\n  }",
     "new": "  if (false) {\n    return { ok: false, reason: 'MODEL_CHANGE_WITHOUT_EPOCH', method };\n  }",
     "expect": ["W1302-REFUSAL-REASONS-AGREE"]},
    {"name": "B-renderer-weakens-a-required-set", "file": CLIENT,
     "old": "'session.send': { payload: 'SendMessagePayload', result: 'SendMessageResult', required: ['text', 'attachment_artifact_ids', 'delivery'] },",
     "new": "'session.send': { payload: 'SendMessagePayload', result: 'SendMessageResult', required: ['text', 'attachment_artifact_ids'] },",
     "expect": ["W1302-RENDERER-TABLE-MATCHES-THE-FROZEN-SCHEMA", "W1302-ENVELOPES-AGREE-ACROSS-SURFACES"]},
    {"name": "C-client-adopts-revision-from-any-reply", "file": CLIENT,
     "old": "      if (result.kind === 'COMPLETED' || result.kind === 'ACKNOWLEDGED') {\n"
            "        if (result.revision !== null && result.revision !== undefined) mutable.expectedRevision = result.revision;",
     "new": "      if (true) {\n        if (result.revision !== null && result.revision !== undefined) mutable.expectedRevision = result.revision;",
     "expect": ["W1302-REFUSED-WRITE-DOES-NOT-REBASELINE", "W1302-IN-PROGRESS-DOES-NOT-REBASELINE"]},
    {"name": "D-producer-surface-map-loses-a-method", "file": CLIENT,
     "old": "  'session.handoff': 'continuity',", "new": "",
     "expect": ["W1302-PRODUCERS-COVER-EVERY-METHOD"]},
    {"name": "E-screen-drops-the-bare-snapshot-branch", "file": SCREEN,
     "old": "        const bare = value.session_id && value.revision !== undefined && value.event_sequence !== undefined\n"
            "        if (value.snapshot || bare) applySnapshot(value.snapshot || value)",
     "new": "        const bare = false\n        if (value.snapshot || bare) applySnapshot(value.snapshot || value)",
     "expect": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"]},
    {"name": "F-recovery-read-ignores-the-watermark", "file": CLIENT,
     "old": "export function readEventsAfter(cursor) {\n  return { after_sequence: Number(cursor || 0), limit: 200 };",
     "new": "export function readEventsAfter(cursor) {\n  return { after_sequence: 0, limit: 200 };",
     "expect": ["W1302-RECOVERY-READ-CARRIES-THE-HOST-WATERMARK"]},
]

orig = {}
for path in {m["file"] for m in MUTANTS}:
    orig[path] = open(path, "rb").read()
baseline = hashlib.sha256(orig[CLIENT]).hexdigest(), hashlib.sha256(orig[SCREEN]).hexdigest()


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W13", RESEARCHOS_CHECK_ID="W13-02")
    p = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tests/ui/continuity/check/main.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                       cwd=ROOT, timeout=1800)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "rc": p.returncode, "stderr": (p.stderr or "")[:300]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"),
            "failed": sorted(f["id"] for f in (d.get("failures") or []))}


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
        killed = [e for e in m["expect"] if e in outcome.get("failed", [])]
        results.append({"mutant": m["name"], "outcome": outcome, "expected": m["expect"],
                        "killed_by": killed,
                        "class": "caught" if killed else ("survived" if outcome.get("status") == "PASS" else
                                                          "crashed-or-other-failure")})
finally:
    for path, blob in orig.items():
        open(path, "wb").write(blob)
    restored = (hashlib.sha256(open(CLIENT, "rb").read()).hexdigest(),
                hashlib.sha256(open(SCREEN, "rb").read()).hexdigest()) == baseline
    clean = run_check()

print(json.dumps({"restored_byte_exact": restored, "clean_recheck": clean, "mutants": results},
                 ensure_ascii=False, indent=1))
