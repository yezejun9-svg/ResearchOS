"""Run only the approved CB-bound local build and Desktop fixture checks."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(r"C:/Users/yqyyds/.codex/researchos-build-worktrees/workspace-projection-20261012")
BUILD = ROOT / ".local/builds/approved-combined-first-use-20261012"
RAW = ROOT / ".local/receipts/approved-combined-first-use-20261012"
HERE = Path(__file__).resolve().parent
GO = Path(r"D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe")
NODE = Path(r"C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe")
ELECTRON = Path(r"D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def run(name, argv, env, timeout=240):
    stdout, stderr = RAW / (name + ".stdout"), RAW / (name + ".stderr")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        try:
            result = subprocess.run([str(x) for x in argv], cwd=ROOT, env=env,
                                    stdout=out, stderr=err, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    row = {"argv": [str(x) for x in argv], "cwd": str(ROOT),
           "started_at": started,
           "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "exit": code, "stdout": str(stdout), "stdout_sha256": sha(stdout),
           "stderr": str(stderr), "stderr_sha256": sha(stderr),
           "environment": {key: env[key] for key in (
               "GOTOOLCHAIN", "GOENV", "GOROOT", "GOPATH", "GOMODCACHE",
               "GOCACHE", "GOTMPDIR", "GOPROXY", "GOSUMDB",
               "RESEARCHOS_DESKTOP_WIRE_ROOT", "RESEARCHOS_DESKTOP_CASE_RECEIPT",
               "RESEARCHOS_DESKTOP_ELECTRON") if key in env}}
    save(RAW / (name + ".invocation.json"), row)
    if code:
        save(HERE / "stopped.json", {"first_unexpected": row, "cause": "Nonzero local build/test exit; inspect immutable raw", "formal_acceptance": False})
        raise SystemExit(code)
    return row

def main():
    assert not (HERE / "stopped.json").exists()
    assert not (RAW / "cb-control-build.invocation.json").exists()
    result = json.loads((RAW / "result.json").read_bytes())
    assert result["drift"] == [] and result["status"] == "BUILT_NOT_TESTED"
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
    assert not subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT)
    env = os.environ.copy()
    env.update(GOTOOLCHAIN="local", GOENV="off", GOROOT=str(GO.parent.parent),
               GOPATH=r"D:/作品集/ResearchOS/research-os/.local/tools/gopath",
               GOMODCACHE=r"D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod",
               GOCACHE=str(BUILD / "go-cache"), GOTMPDIR=str(BUILD / "go-tmp"),
               GOPROXY="off", GOSUMDB="off",
               RESEARCHOS_DESKTOP_WIRE_ROOT=str(BUILD),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(RAW / "desktop-cases"),
               RESEARCHOS_DESKTOP_ELECTRON=str(ELECTRON))
    (RAW / "desktop-cases").mkdir(exist_ok=False)
    rows = []
    rows.append(run("cb-control-build", [GO, "build", "-mod=readonly", "-buildvcs=true", "-o", BUILD / "control.exe", "./apps/control"], env))
    rows.append(run("cb-verifier-build", [GO, "build", "-mod=readonly", "-buildvcs=true", "-o", BUILD / "runtime-verifier.exe", "./apps/runtime-verifier"], env))
    rows.append(run("cb-validator-test", [BUILD / "validator.test.exe", "-test.v"], env))
    rows.append(run("cb-desktop-suite", [NODE, "--test",
                     "tests/ui/desktop/coding-authorization-boundary.test.mjs",
                     "tests/ui/desktop/desktop-management-boundary.test.mjs",
                     "tests/ui/desktop/http-wire-boundary.test.mjs",
                     "tests/ui/desktop/w13-react.test.js"], env, timeout=360))
    output = (RAW / "cb-desktop-suite.stdout").read_text(encoding="utf-8")
    counts = {key: int(match.group(1)) if (match := re.search(r"^# " + key + r" (\d+)$", output, re.M)) else None
              for key in ("tests", "pass", "fail", "skipped")}
    assert counts["tests"] and counts["tests"] == counts["pass"] and counts["fail"] == counts["skipped"] == 0, counts
    save(HERE / "bound-verification.json", {
        "status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "source_commit": "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8",
        "source_main_tree_equal": True, "build_input_digest": result["build_input_digest"],
        "build_input_count": len(json.loads((RAW / "inputs.before.json").read_bytes())),
        "build_drift": result["drift"], "desktop_counts": counts,
        "control_sha256": sha(BUILD / "control.exe"), "verifier_sha256": sha(BUILD / "runtime-verifier.exe"),
        "validator_sha256": result["binary_sha256"], "invocations": rows,
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "desktop_counts": counts,
                      "control_sha256": sha(BUILD / "control.exe"), "verifier_sha256": sha(BUILD / "runtime-verifier.exe")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
