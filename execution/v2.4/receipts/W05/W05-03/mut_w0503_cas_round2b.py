"""Verify that stripping a CAS field from the write envelope is caught by a named row, then restore byte-exactly."""
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GO = json.load(open(os.path.join(ROOT, "execution/toolchains/locked.json"), encoding="utf-8-sig"))["tools"]["go"]["path"]
TARGET = os.path.join(ROOT, "apps", "cli", "cli_v2.go")
ORIG = open(TARGET, "rb").read()
ANCHOR = b"\t\tenv.ExpectedRevision = &ctx.revision"
assert ORIG.count(ANCHOR) == 1, ORIG.count(ANCHOR)

ENV = dict(os.environ, RESEARCHOS_TASK_ID="W05", RESEARCHOS_CHECK_ID="W05-03", GOFLAGS="-mod=mod")


def run_suite():
    b = subprocess.run([GO, "build", "./apps/cli", "./tests/runtime/cli_contract"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=ENV, cwd=ROOT, timeout=600)
    if b.returncode != 0:
        return {"status": "BUILD_FAILED", "detail": (b.stderr or "")[:200]}
    r = subprocess.run([GO, "run", "./tests/runtime/cli_contract"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV, cwd=ROOT, timeout=900)
    lines = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        return {"status": "NOJSON", "rc": r.returncode, "stderr": (r.stderr or "")[:200]}
    d = json.loads(lines[-1])
    return {"status": d.get("status"), "assertions": d.get("assertions"), "rc": r.returncode,
            "failed": sorted(f["id"] for f in (d.get("failures") or []))}


out = {}
try:
    open(TARGET, "wb").write(ORIG.replace(ANCHOR, b"\t\tif false {\n" + ANCHOR + b"\n\t\t}", 1))
    out["M-CAS-expected-revision-stripped"] = run_suite()
finally:
    open(TARGET, "wb").write(ORIG)
    out["restored_byte_exact"] = hashlib.sha256(open(TARGET, "rb").read()).hexdigest() == hashlib.sha256(ORIG).hexdigest()
    out["clean_recheck"] = run_suite()

print(json.dumps(out, ensure_ascii=False, indent=1))
