"""Exact W03 parent routing; legacy/child subprocess streams remain inherited."""
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]

def route(key, env):
    if key not in ("contracts.validate", "test.domain"):
        raise ValueError("unknown bridge key")
    task, check, case = (env.get("RESEARCHOS_" + k, "") for k in ("TASK_ID", "CHECK_ID", "CASE_ID"))
    parents = {"W03-G01": "contracts.validate", "W03-G02": "test.domain", "W03-G03": "contracts.validate"}
    if task == "W03" and check in parents:
        if case or key != parents[check]:
            raise ValueError("parent key/check/case mismatch")
        return "parent", check
    child = "W03-02" if key == "contracts.validate" else "W03-01"
    if task == "W03" and check == child and not case:
        go = env.get("RESEARCHOS_GO")
        if not go:
            raise ValueError("locked Go tool missing")
        return "forward", [go, "run", "./tests/contracts/check" if key == "contracts.validate" else "./tests/domain/check"]
    # Wrong combinations of W03 child selectors must not fall through to a
    # different meaning. All historical non-parent tuples go to the old driver.
    if task == "W03" and check in ("W03-01", "W03-02"):
        raise ValueError("wrong W03 exact selector")
    legacy = "ops/ci/contracts.py" if key == "contracts.validate" else "ops/ci/domain.py"
    return "forward", [sys.executable, legacy]

def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("one explicit command key required")
        kind, target = route(sys.argv[1], os.environ)
        if kind == "forward":
            return subprocess.call(target, cwd=ROOT)
        # This local module is enrolled in the archived manifest; there is no
        # AST extraction, dynamically selected external module, or fallback run.
        import gate_driver
        report = gate_driver.run_gate(target, fresh=False)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report["status"] == "PASS" else 1
    except Exception as error:
        print(json.dumps({"status": "FAIL", "assertion_ids": [], "assertions": 0, "error": str(error)}))
        return 1

if __name__ == "__main__":
    sys.exit(main())
