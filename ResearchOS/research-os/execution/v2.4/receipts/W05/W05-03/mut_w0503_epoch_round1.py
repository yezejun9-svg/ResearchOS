"""Two mutants against the W05-03 epoch fix, each restored byte-for-byte.

M-E1 removes the wire assignment (the defect the round-2 review proved); M-E2 removes the local refusal. Each is
expected to kill a specific row and leave the rest green; a mutant that kills nothing is a row without teeth.
"""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__) + "/..")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GO = json.load(open(os.path.join(ROOT, "execution/toolchains/locked.json"), encoding="utf-8-sig"))["tools"]["go"]["path"]
V2 = os.path.join(ROOT, "apps", "cli", "cli_v2.go")
ORIG = open(V2, "rb").read()

MUTANTS = [
    ("M-E1-wire-epoch-removed",
     b"\t\tif hasModel || hasProvider {\n\t\t\t// Refusing locally is only half of it",
     b"\t\tif false && (hasModel || hasProvider) {\n\t\t\t// Refusing locally is only half of it"),
    ("M-E2-local-refusal-removed",
     b'\t\tif (hasModel || hasProvider) && ctx.epoch == 0 {\n\t\t\treturn nil, "MODEL_CHANGE_WITHOUT_EPOCH"',
     b'\t\tif false && (hasModel || hasProvider) && ctx.epoch == 0 {\n\t\t\treturn nil, "MODEL_CHANGE_WITHOUT_EPOCH"'),
]


def run_suite():
    env = dict(os.environ, RESEARCHOS_TASK_ID="W05", RESEARCHOS_CHECK_ID="W05-03", GOFLAGS="-mod=mod")
    b = subprocess.run([GO, "build", "./apps/cli", "./tests/runtime/cli_contract"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env, cwd=ROOT)
    if b.returncode != 0:
        return {"status": "BUILD_FAILED", "detail": (b.stderr or "")[:200]}
    r = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=ROOT, timeout=900)
    lines = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "stderr": (r.stderr or "")[:200]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"),
            "failed_ids": sorted(f["id"] for f in (d.get("failures") or []))}


results = []
try:
    for name, old, new in MUTANTS:
        text = ORIG
        if text.count(old) != 1:
            results.append({"mutant": name, "class": "anchor-missing", "occurrences": text.count(old)})
            continue
        open(V2, "wb").write(text.replace(old, new, 1))
        outcome = run_suite()
        results.append({"mutant": name, "outcome": outcome})
finally:
    open(V2, "wb").write(ORIG)
    restored = hashlib.sha256(open(V2, "rb").read()).hexdigest() == hashlib.sha256(ORIG).hexdigest()
    clean = run_suite()

print(json.dumps({"restored_byte_exact": restored, "clean_recheck": clean, "mutants": results},
                 ensure_ascii=False, indent=1))
