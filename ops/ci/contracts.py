#!/usr/bin/env python3
"""Validate frozen contract package and selected-route dependency declarations."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    if os.getenv("RESEARCHOS_TASK_ID", "W02") != "W02" or os.getenv("RESEARCHOS_CHECK_ID", "") not in ("", "W02-G01", "W02-G02", "W02-G03") or os.getenv("RESEARCHOS_CASE_ID"):
        raise NotImplementedError("unbound task/check/case selection")
    command = [sys.executable, str(ROOT / "spec" / "v2.0" / "tools" / "validate_package.py")]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
    report = json.loads(result.stdout)
    if result.returncode or report["status"] != "PASS" or not report["checks"]:
        raise RuntimeError(f"package validation failed: {report.get('errors', result.stderr)}")
    ids = ["W02-CONTRACT-PACKAGE"]
    schema = json.loads((ROOT / "spec" / "v2.0" / "contracts" / "domain.schema.json").read_text(encoding="utf-8"))
    api = json.loads((ROOT / "spec" / "v2.0" / "contracts" / "openapi.json").read_text(encoding="utf-8"))
    if not schema.get("$defs") or api.get("openapi") != "3.1.0" or not api.get("paths", {}).get("/v1/projects"):
        raise RuntimeError("domain/OpenAPI contract missing required structure")
    ids.append("W02-CONTRACT-SHAPE")
    route = json.loads((ROOT / "execution" / "route.json").read_text(encoding="utf-8"))
    pkg = json.loads((ROOT / "apps" / "web" / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "apps" / "web" / "package-lock.json").read_text(encoding="utf-8"))
    root_lock = lock["packages"][""]
    if route["selected_route"] != "THIN_CORE" or any(root_lock[k] != pkg[k] for k in ("dependencies", "devDependencies")):
        raise RuntimeError("route or web lock declarations drifted")
    ids.append("W02-CONTRACT-ROUTE-LOCK")
    return {"status": "PASS", "assertions": len(ids), "assertion_ids": ids,
            "scope": "DEVELOPMENT_ONLY", "package_checks": len(report["checks"]),
            "command": command, "exit_code": result.returncode}


if __name__ == "__main__":
    try:
        report = main()
    except Exception as exc:
        report = {"status": "FAIL", "assertions": 1,
                  "assertion_ids": ["W02-CONTRACT-ATTEMPTED"], "scope": "DEVELOPMENT_ONLY",
                  "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if report["status"] == "PASS" else 1)
