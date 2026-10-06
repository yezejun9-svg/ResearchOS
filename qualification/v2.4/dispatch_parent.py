"""Bounded core.qualify selector bridge; preserves every legacy tuple verbatim."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PARENT_CHECKS = tuple("W01-G0" + str(n) for n in range(1, 5))


def select(task, check, case, python=sys.executable, root=ROOT):
    if task == "W01" and check in PARENT_CHECKS and case == "":
        return [python, "-B", "-X", "utf8", str(root / "qualification/v2.4/qualify.py"), "--check-id", check]
    if task in {"", "W01", "W02", "W06"} and check == "" and case in {"", "A02"}:
        # Exact legacy interpreter flags, environment and streams. No new claims
        # or interception of the old archived-evidence / W06 fixture report.
        return [python, "-X", "utf8", str(root / "ops/ci/core_evidence.py")]
    return None


def main(env=None, execute=None):
    env = os.environ if env is None else env
    execute = subprocess.call if execute is None else execute
    task, check, case = (env.get("RESEARCHOS_" + key + "_ID", "") for key in ("TASK", "CHECK", "CASE"))
    command = select(task, check, case)
    if command is None:
        print(json.dumps({"status": "NOT_IMPLEMENTED", "task_id": task, "check_id": check, "case_id": case,
                          "assertion_ids": [], "reason": "Unsupported exact core.qualify selector tuple"}))
        return 2
    return execute(command, cwd=ROOT, env=env)


if __name__ == "__main__":
    sys.exit(main())
