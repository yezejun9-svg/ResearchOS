#!/usr/bin/env python3
"""Validate frozen contract package and selected-route dependency declarations."""
import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    task = os.getenv("RESEARCHOS_TASK_ID", "W02")
    if task not in ("W02", "W03", "W04", "W05", "W07") or os.getenv("RESEARCHOS_CHECK_ID", "") not in ("", *(f"{task}-G0{n}" for n in (1, 2, 3))) or os.getenv("RESEARCHOS_CASE_ID"):
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
    if task != "W02":
        coverage = json.loads((ROOT / "contracts/operation_coverage.json").read_text(encoding="utf-8"))
        expected = {operation["operationId"]: (method.upper(), path)
                    for path, methods in api["paths"].items()
                    for method, operation in methods.items()
                    if method in ("get", "post", "put", "patch", "delete", "options", "head")}
        operations = coverage["operations"]
        known_tasks = {t["task_id"] for t in json.loads((ROOT / "spec/v2.0/contracts/tasks.json").read_text(encoding="utf-8"))["tasks"]}
        observed = {op["operation_id"]: (op["method"], op["path"]) for op in operations}
        if not expected or observed != expected or len(operations) != len(observed):
            raise RuntimeError("operation coverage is incomplete, duplicated, or drifted")
        if any(op["status"] not in ("IMPLEMENTED_CORE", "DEFERRED") or op["owner_task"] not in known_tasks for op in operations):
            raise RuntimeError("operation coverage has invalid status or owner")
        ids.append("W03-CONTRACT-OPERATION-INVENTORY")
        for name in ("domain.schema.json", "openapi.json"):
            digest = hashlib.sha256((ROOT / "spec/v2.0/contracts" / name).read_bytes()).hexdigest()
            if coverage["contract_hashes"].get(name) != digest:
                raise RuntimeError("operation coverage references a different frozen contract")
        ids.append("W03-CONTRACT-COVERAGE-HASHES")
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
