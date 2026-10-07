"""Reproduce frozen-source rejection against a disposable detached checkout."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


root = Path.cwd()
evidence = Path(__file__).resolve().parent
builder = root / "ops/release/build.py"
cases = [
    ("dirty-package-doc", "docs/installation/README.md", False),
    ("dirty-command-registry", "execution/commands.json", False),
    ("dirty-tool-lock", "execution/toolchains/locked.json", False),
    ("untracked-package-json", "release/independent-untracked.json", True),
    ("untracked-go-build-input", "internal/domain/independent_untracked.go", True),
    ("untracked-web-build-input", "apps/web/src/independent-untracked.js", True),
]
results = []
for name, relative, untracked in cases:
    path = root / relative
    if untracked and path.exists():
        raise RuntimeError(f"unexpected existing file: {relative}")
    original = None if untracked else path.read_bytes()
    try:
        path.write_bytes((original or b"") + b"\nresearchos-source-freeze-negative-marker\n")
        result = subprocess.run(
            [sys.executable, str(builder), "--output", str(evidence / "must-not-build.zip")],
            cwd=root, capture_output=True, text=True, timeout=90,
        )
        observed = {"case": name, "input": relative, "exit_code": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr}
        results.append(observed)
        if result.returncode == 0 or "frozen" not in result.stderr:
            raise AssertionError(observed)
    finally:
        if untracked:
            path.unlink()
        else:
            path.write_bytes(original)

spec = importlib.util.spec_from_file_location("release_builder", builder)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
unrelated = root / "execution/receipts/W20/release-package-unrelated.json"
if unrelated.exists():
    raise RuntimeError("unexpected existing unrelated evidence path")
try:
    unrelated.parent.mkdir(parents=True, exist_ok=True)
    unrelated.write_text('{"unrelated":true}', encoding="utf-8")
    snapshot = module.check_frozen_inputs(root)
    results.append({"case": "unrelated-execution-evidence-allowed", "input": unrelated.relative_to(root).as_posix(),
                    "status": "PASS", "frozen_snapshot": snapshot})
finally:
    unrelated.unlink()

status = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True, check=True)
if status.stdout.strip():
    raise AssertionError("disposable checkout not clean after probes: " + status.stdout)
(evidence / "source-negative-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "cases": len(results), "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}))
