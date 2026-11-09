"""Preserved retry after attempt 1 used wrong test working directory."""
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

def run(name, argv, cwd, env, timeout=360):
    stdout, stderr = RAW / (name + ".stdout"), RAW / (name + ".stderr")
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        try:
            code = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                                  stdout=out, stderr=err, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    row = {"argv": [str(x) for x in argv], "cwd": str(cwd), "started_at": start,
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
        save(HERE / (name + ".stopped.json"), {"first_unexpected": row,
             "formal_acceptance": False, "previous_failure_preserved": str(HERE / "stopped.json")})
        raise SystemExit(code)
    return row

def main():
    first = json.loads((HERE / "stopped.json").read_bytes())
    assert first["first_unexpected"]["exit"] == 1
    assert "cb-validator-test" in first["first_unexpected"]["stdout"]
    assert not (HERE / "retry-validator-and-desktop.stopped.json").exists()
    assert not (RAW / "cb-validator-test-cwd-corrected.invocation.json").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
    assert not subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT)
    original = json.loads((RAW / "cb-control-build.invocation.json").read_bytes())
    verifier = json.loads((RAW / "cb-verifier-build.invocation.json").read_bytes())
    assert original["exit"] == verifier["exit"] == 0
    env = os.environ.copy()
    env.update(GOTOOLCHAIN="local", GOENV="off", GOROOT=str(GO.parent.parent),
               GOPATH=r"D:/作品集/ResearchOS/research-os/.local/tools/gopath",
               GOMODCACHE=r"D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod",
               GOCACHE=str(BUILD / "go-cache"), GOTMPDIR=str(BUILD / "go-tmp"),
               GOPROXY="off", GOSUMDB="off",
               RESEARCHOS_DESKTOP_WIRE_ROOT=str(BUILD),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(RAW / "desktop-cases"),
               RESEARCHOS_DESKTOP_ELECTRON=str(ELECTRON))
    rows = []
    rows.append(run("cb-validator-test-cwd-corrected", [BUILD / "validator.test.exe", "-test.v"],
                    ROOT / "apps/desktop/validator", env))
    rows.append(run("cb-desktop-suite-cwd-corrected", [NODE, "--test",
                    "tests/ui/desktop/coding-authorization-boundary.test.mjs",
                    "tests/ui/desktop/desktop-management-boundary.test.mjs",
                    "tests/ui/desktop/http-wire-boundary.test.mjs",
                    "tests/ui/desktop/w13-react.test.js"], ROOT, env))
    output = (RAW / "cb-desktop-suite-cwd-corrected.stdout").read_text(encoding="utf-8")
    counts = {key: int(match.group(1)) if (match := re.search(r"^# " + key + r" (\d+)$", output, re.M)) else None
              for key in ("tests", "pass", "fail", "skipped")}
    assert counts["tests"] and counts["tests"] == counts["pass"] and counts["fail"] == counts["skipped"] == 0, counts
    result = json.loads((RAW / "result.json").read_bytes())
    save(HERE / "bound-verification.json", {
        "status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "source_commit": "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8",
        "source_main_tree_equal": True, "build_input_digest": result["build_input_digest"],
        "build_input_count": len(json.loads((RAW / "inputs.before.json").read_bytes())),
        "build_drift": result["drift"], "desktop_counts": counts,
        "control_sha256": sha(BUILD / "control.exe"), "verifier_sha256": sha(BUILD / "runtime-verifier.exe"),
        "validator_sha256": result["binary_sha256"], "invocations": [original, verifier, *rows],
        "previous_failed_attempt": str(HERE / "stopped.json"),
        "previous_failure_cause": "Test executable started from repository root; fixture path resolves relative to validator package directory",
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "desktop_counts": counts,
                      "control_sha256": sha(BUILD / "control.exe"), "verifier_sha256": sha(BUILD / "runtime-verifier.exe")}, ensure_ascii=False))

if __name__ == "__main__":
    main()
