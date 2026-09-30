#!/usr/bin/env python3
"""Build pinned sources and run real Go/HTTP/SQLite checks."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IDS = []
COMMANDS = []


def run(name, argv, cwd=ROOT):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=600)
    COMMANDS.append({"name": name, "argv": argv, "cwd": str(cwd),
                     "exit_code": result.returncode, "stdout_tail": result.stdout[-2500:],
                     "stderr_tail": result.stderr[-2500:]})
    if result.returncode:
        raise RuntimeError(f"{name} exited {result.returncode}: {result.stderr[-500:]}")
    return result.stdout


def main():
    task = os.getenv("RESEARCHOS_TASK_ID", "W02")
    if task not in ("W02", "W03", "W04", "W05", "W06", "W07", "W09", "W10", "W12") or os.getenv("RESEARCHOS_CHECK_ID", "") not in ("", *(f"{task}-G0{n}" for n in (1, 2, 3))) or os.getenv("RESEARCHOS_CASE_ID"):
        raise NotImplementedError("unbound task/check/case selection")
    go = os.environ["RESEARCHOS_GO"]
    node = os.environ["RESEARCHOS_NODE"]
    npm_cli = os.environ["RESEARCHOS_NPM_CLI"]
    web = ROOT / "apps" / "web"
    run("go-mod-verify", [go, "mod", "verify"])
    IDS.append("W02-LOCK-GO")
    run("npm-ci", [node, npm_cli, "ci", "--no-audit", "--no-fund"], web)
    IDS.append("W02-LOCK-WEB")
    run("web-build", [node, str(web / "node_modules" / "vite" / "bin" / "vite.js"), "build"], web)
    if not (web / "dist" / "index.html").is_file():
        raise RuntimeError("Vite did not produce index.html")
    IDS.append("W02-BUILD-WEB")
    binary = ROOT / ".local" / "bin" / ("researchos-control.exe" if os.name == "nt" else "researchos-control")
    binary.parent.mkdir(parents=True, exist_ok=True)
    run("go-build", [go, "build", "-trimpath", "-o", str(binary), "./apps/control"])
    IDS.append("W02-BUILD-GO")
    output = run("go-test", [go, "test", "-json", "-count=1", "./..."])
    passed = {event.get("Test") for line in output.splitlines()
              if (event := json.loads(line)).get("Action") == "pass" and event.get("Test")}
    if not {"TestJSON", "TestOpenSettings"} <= passed:
        raise RuntimeError(f"required Go tests missing: {passed}")
    IDS.extend(["W02-JCS", "W02-SQLITE-CONNECTION"])
    probe = run("startup-probe", [sys.executable, str(ROOT / "tests" / "bootstrap" / "skeleton_check.py")])
    result = json.loads(probe.splitlines()[-1])
    if result.get("status") != "PASS" or result.get("assertions", 0) < 3:
        raise RuntimeError("startup probe did not pass")
    IDS.extend(result["assertion_ids"])


if __name__ == "__main__":
    reason = None
    try:
        main()
        status = "PASS"
    except NotImplementedError as exc:
        status, reason = "FAIL", f"NOT_IMPLEMENTED: {exc}"
    except Exception as exc:
        status, reason = "FAIL", str(exc)
    if not IDS:
        IDS.append("W02-BUILD-ATTEMPTED")
    print(json.dumps({"status": status, "assertions": len(IDS), "assertion_ids": IDS,
                      "scope": "DEVELOPMENT_ONLY", "commands": COMMANDS,
                      "error": reason}, ensure_ascii=False))
    sys.exit(0 if status == "PASS" else 1)
