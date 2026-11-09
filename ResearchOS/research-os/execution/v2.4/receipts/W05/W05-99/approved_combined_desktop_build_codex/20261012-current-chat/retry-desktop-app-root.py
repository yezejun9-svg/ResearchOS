"""Desktop fixture retry with the app-root environment contract, preserving prior failures."""
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
NODE = Path(r"C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe")
ELECTRON = Path(r"D:/作品集/ResearchOS/research-os/apps/desktop/node_modules/electron/dist/electron.exe")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def main():
    previous = json.loads((HERE / "cb-desktop-suite-cwd-corrected.stopped.json").read_bytes())
    assert previous["first_unexpected"]["exit"] != 0
    assert json.loads((RAW / "cb-validator-test-cwd-corrected.invocation.json").read_bytes())["exit"] == 0
    assert not (RAW / "cb-desktop-suite-app-root.invocation.json").exists()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8"
    assert subprocess.check_output(["git", "status", "--porcelain=v1"], cwd=ROOT) == b""
    env = os.environ.copy()
    env.update(RESEARCHOS_DESKTOP_WIRE_ROOT=str(BUILD / "apps/desktop"),
               RESEARCHOS_DESKTOP_CASE_RECEIPT=str(RAW / "desktop-cases"),
               RESEARCHOS_DESKTOP_ELECTRON=str(ELECTRON))
    argv = [str(NODE), "--test", "tests/ui/desktop/coding-authorization-boundary.test.mjs",
            "tests/ui/desktop/desktop-management-boundary.test.mjs",
            "tests/ui/desktop/http-wire-boundary.test.mjs",
            "tests/ui/desktop/w13-react.test.js"]
    stdout = RAW / "cb-desktop-suite-app-root.stdout"
    stderr = RAW / "cb-desktop-suite-app-root.stderr"
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        try:
            code = subprocess.run(argv, cwd=ROOT, env=env, stdout=out, stderr=err, timeout=360).returncode
        except subprocess.TimeoutExpired:
            code = 124
    row = {"argv": argv, "cwd": str(ROOT), "started_at": start,
           "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "exit": code,
           "stdout": str(stdout), "stdout_sha256": sha(stdout), "stderr": str(stderr),
           "stderr_sha256": sha(stderr), "environment": {k: env[k] for k in (
               "RESEARCHOS_DESKTOP_WIRE_ROOT", "RESEARCHOS_DESKTOP_CASE_RECEIPT", "RESEARCHOS_DESKTOP_ELECTRON")},
           "previous_failed_attempt": str(HERE / "cb-desktop-suite-cwd-corrected.stopped.json")}
    save(RAW / "cb-desktop-suite-app-root.invocation.json", row)
    if code:
        save(HERE / "cb-desktop-suite-app-root.stopped.json", {"first_unexpected": row,
             "cause": "Inspect raw TAP; prior failure not erased", "formal_acceptance": False})
        raise SystemExit(code)
    output = stdout.read_text(encoding="utf-8")
    counts = {key: int(match.group(1)) if (match := re.search(r"^# " + key + r" (\d+)$", output, re.M)) else None
              for key in ("tests", "pass", "fail", "skipped")}
    if not (counts["tests"] and counts["tests"] == counts["pass"] and counts["fail"] == counts["skipped"] == 0):
        save(HERE / "cb-desktop-suite-app-root.stopped.json", {"first_unexpected": row, "cause": "TAP count mismatch", "counts": counts})
        raise SystemExit("TAP count mismatch")
    result = json.loads((RAW / "result.json").read_bytes())
    control = BUILD / "control.exe"
    verifier = BUILD / "runtime-verifier.exe"
    save(HERE / "bound-verification.json", {
        "status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "source_commit": "cb3646d384dcaee1670f3ca4c4891cd0fd12a2c8",
        "source_main_tree_equal": True, "build_input_digest": result["build_input_digest"],
        "build_input_count": len(json.loads((RAW / "inputs.before.json").read_bytes())),
        "build_drift": result["drift"], "desktop_counts": counts,
        "control_sha256": sha(control), "verifier_sha256": sha(verifier),
        "validator_sha256": result["binary_sha256"],
        "invocations": [json.loads((RAW / (name + ".invocation.json")).read_bytes()) for name in (
            "cb-control-build", "cb-verifier-build", "cb-validator-test-cwd-corrected", "cb-desktop-suite-app-root")],
        "previous_failed_attempts": [str(HERE / "stopped.json"), str(HERE / "cb-desktop-suite-cwd-corrected.stopped.json")],
        "model_calls": 0, "formal_increment": 0, "parent_acceptance": False})
    print(json.dumps({"status": "SOURCE_BOUND_LOCAL_FIXTURE_PASS", "desktop_counts": counts,
                      "control_sha256": sha(control), "verifier_sha256": sha(verifier)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
