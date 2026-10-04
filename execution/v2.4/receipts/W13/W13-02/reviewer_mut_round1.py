"""Reviewer mutation pass (qoder-desktop:/root/w1302_verifier_r1) for W13-02.

Independent of the builder's frozen drivers (which, measured: cannot be re-run from the receipt directory because
their ROOT resolves to execution/v2.4/receipts/W13). This driver resolves the repository root from the receipt
directory five levels up, asserts each anchor occurs exactly once before writing, restores every file byte-for-byte
in a finally clause with a sha256 comparison, and re-runs the clean check afterwards.

With --dry it only reports anchor occurrences and writes nothing.

Classifications: caught-by-card-id (an expected id of THIS card moved), caught-by-gate-id-only (some other row of
the same gate moved but none of the expected ones), survived (the gate still reported PASS), anchor-missing,
crashed-or-ill-formed (no JSON report / no assertion count).
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "..", "..", ".."))
CLIENT = os.path.join(ROOT, "apps", "web", "src", "v2client.js")
SCREEN = os.path.join(ROOT, "apps", "web", "src", "continuity.jsx")
SHELL = os.path.join(ROOT, "apps", "desktop", "main", "lib", "v2.js")
PROBE = os.path.join(ROOT, "tests", "ui", "continuity", "producer_probe.py")
CHECK = os.path.join(ROOT, "tests", "ui", "continuity", "check", "main.py")

MUTANTS = [
    {"name": "R1-renderer-drops-action-digest-from-required",
     "file": CLIENT,
     "old": "'permission.respond': { payload: 'RespondPermissionPayload', result: 'RespondPermissionResult', required: ['resource_request_id', 'resource_request_revision', 'action_digest', 'decision', 'reason'] },",
     "new": "'permission.respond': { payload: 'RespondPermissionPayload', result: 'RespondPermissionResult', required: ['resource_request_id', 'resource_request_revision', 'decision', 'reason'] },",
     "expect": ["W1302-RENDERER-TABLE-MATCHES-THE-FROZEN-SCHEMA", "W1302-ENVELOPES-AGREE-ACROSS-SURFACES"]},
    {"name": "R2-renderer-sends-without-a-credential",
     "file": CLIENT,
     "old": "  if (!identity.credential) return { ok: false, reason: 'CREDENTIAL_ABSENT' };",
     "new": "  if (false) return { ok: false, reason: 'CREDENTIAL_ABSENT' };",
     "expect": ["W1302-REFUSAL-REASONS-AGREE"]},
    {"name": "R3-renderer-adopts-session-id-from-a-result-body",
     "file": CLIENT,
     "old": "      if (result.session_id) mutable.sessionId = result.session_id;",
     "new": "      const borrowed = result.session_id || (result.result && result.result.session_id);\n      if (borrowed) mutable.sessionId = borrowed;",
     "expect": ["W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE"]},
    {"name": "R4-screen-send-becomes-restyle-only",
     "file": SCREEN,
     "old": "onClick={() => run('session.send', { text: chat, attachment_artifact_ids: form.attachment ? [form.attachment] : [], delivery: form.delivery }).then(result => { if (!statusLine(result)) setChat('') })}",
     "new": "onClick={() => setChat('')}",
     "expect": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"]},
    {"name": "R5-screen-save-drops-the-base-hash",
     "file": SCREEN,
     "old": "task_id: snapshot?.active_run_id || '', expected_content_hash: base.content_hash || null, text: draft, create_if_missing: false",
     "new": "task_id: snapshot?.active_run_id || '', expected_content_hash: null, text: draft, create_if_missing: false",
     "expect": ["W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND"]},
    {"name": "R6-stub-host-status-result-loses-a-required-key",
     "file": PROBE,
     "old": '"host.status": {"state": "READY", "core_build_id": "stub-build", "protocol_version": "researchos-client/2"},',
     "new": '"host.status": {"state": "READY", "protocol_version": "researchos-client/2"},',
     "expect": ["W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA"]},
    {"name": "R7-stub-session-events-result-loses-a-required-key",
     "file": PROBE,
     "old": '"session.events": {"events": [event], "next_sequence": 8, "high_watermark": 8, "has_more": False},',
     "new": '"session.events": {"events": [event], "high_watermark": 8, "has_more": False},',
     "expect": ["W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA"]},
    {"name": "R8-shell-drops-the-claimed-epoch-rule",
     "file": SHELL,
     "old": "    if (claiming && env.writer_epoch !== null) return { ok: false, reason: 'ATTACKER_CLAIMED_EPOCH', method };",
     "new": "    if (false) return { ok: false, reason: 'ATTACKER_CLAIMED_EPOCH', method };",
     "expect": ["W1302-REFUSAL-REASONS-AGREE", "W1302-ENVELOPES-AGREE-ACROSS-SURFACES"]},
]

CARD_IDS = set()
src = open(CHECK, encoding="utf-8").read()
import re
CARD_IDS = set(re.findall(r'"(W1302-[A-Z0-9._-]+)"', src))

if "--dry" in sys.argv:
    blobs = {p: open(p, "rb").read().decode("utf-8") for p in {m["file"] for m in MUTANTS}}
    print(json.dumps({"root": ROOT, "card_ids_discovered": len(CARD_IDS),
                      "anchors": {m["name"]: {"file": os.path.basename(m["file"]),
                                              "occurrences": blobs[m["file"]].count(m["old"])} for m in MUTANTS}},
                     indent=1))
    sys.exit(0)

orig = {p: open(p, "rb").read() for p in {m["file"] for m in MUTANTS}}
baseline = {p: hashlib.sha256(b).hexdigest() for p, b in orig.items()}
results = []


def run_check():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W13", RESEARCHOS_CHECK_ID="W13-02")
    p = subprocess.run([sys.executable, "-X", "utf8", CHECK], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=ROOT, timeout=1800)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "rc": p.returncode, "stderr": (p.stderr or "")[:300]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"), "rc": p.returncode,
            "failed": sorted(f["id"] for f in (d.get("failures") or []))}


try:
    for m in MUTANTS:
        text = orig[m["file"]].decode("utf-8")
        count = text.count(m["old"])
        if count != 1:
            results.append({"mutant": m["name"], "class": "anchor-missing", "occurrences": count})
            continue
        open(m["file"], "w", encoding="utf-8", newline="\n").write(text.replace(m["old"], m["new"], 1))
        outcome = run_check()
        failed = set(outcome.get("failed", []))
        killed = [e for e in m["expect"] if e in failed]
        if killed:
            cls = "caught"
        elif outcome.get("status") == "PASS":
            cls = "survived"
        elif outcome.get("status") == "NOJSON" or "assertions" not in outcome:
            cls = "crashed-or-ill-formed"
        elif failed & CARD_IDS:
            cls = "caught-by-gate-id-only"
        else:
            cls = "other-failure"
        results.append({"mutant": m["name"], "file": os.path.relpath(m["file"], ROOT).replace("\\", "/"),
                        "outcome": outcome, "expected": m["expect"], "killed_by": killed,
                        "other_card_ids_moved": sorted((failed & CARD_IDS) - set(killed)), "class": cls})
finally:
    for path, blob in orig.items():
        open(path, "wb").write(blob)
    restored = all(hashlib.sha256(open(p, "rb").read()).hexdigest() == h for p, h in baseline.items())
    clean = run_check()

print(json.dumps({"reviewer_id": "qoder-desktop:/root/w1302_verifier_r1", "repository_root": ROOT,
                  "restored_byte_exact": restored, "restored_hashes": {os.path.relpath(p, ROOT).replace("\\", "/"):
                                                                       hashlib.sha256(open(p, "rb").read()).hexdigest()
                                                                       for p in orig},
                  "clean_recheck": clean, "mutants": results}, ensure_ascii=False, indent=1))
