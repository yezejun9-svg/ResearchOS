"""Capture actual public-reader synthetic controls, retaining failed attempts."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[5]
SCOPE = "SYNTHETIC_GENERIC_CONTROLS_NOT_PRODUCT_EVIDENCE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    sources = {name: HERE / name for name in ("test_generic.py", "run_generic.py", "README.md")}
    sources.update({"fixture_builder.py": BASE / "test_validate.py", "fixture_helpers.py": BASE / "validate.py",
                    "formal_case_index.py": REPO / "execution/v2.4/formal_case_index.py"})
    hashes = {name: sha(path) for name, path in sources.items()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    records = HERE / "runs"
    records.mkdir(exist_ok=True)
    for previous in records.glob("*/receipt.json"):
        data = json.loads(previous.read_text(encoding="utf-8"))
        if data.get("input_digest") == digest and data.get("exit_code") != 0:
            print(json.dumps({"scope": SCOPE, "status": "UNCHANGED_FAILED_INPUT_NOT_RETRIED", "previous": str(previous)}))
            return 2
    directory = records / ("controls-" + uuid.uuid4().hex)
    directory.mkdir()
    archive = directory / "source"
    archive.mkdir()
    for name, path in sources.items():
        (archive / name).write_bytes(path.read_bytes())
    argv = [sys.executable, "-B", "-X", "utf8", str(HERE / "test_generic.py")]
    started = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    output = subprocess.run(argv, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (directory / "stdout.txt").write_bytes(output.stdout)
    (directory / "stderr.txt").write_bytes(output.stderr)
    main_argv = [sys.executable, "-B", "-X", "utf8", str(REPO / "execution/v2.4/formal_case_index.py"),
                 "--repo", str(REPO), "--state", str(REPO / "execution/v2.4/step_state.json"),
                 "--plan", str(REPO / ".local/worktrees/v24-continuation/spec/v2.4/contracts/execution.plan.json")]
    main_state_before = sha(REPO / "execution/v2.4/step_state.json")
    main_output = subprocess.run(main_argv, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (directory / "main-read.stdout.json").write_bytes(main_output.stdout)
    (directory / "main-read.stderr.txt").write_bytes(main_output.stderr)
    main_state_after = sha(REPO / "execution/v2.4/step_state.json")
    unchanged = hashes == {name: sha(path) for name, path in sources.items()}
    receipt = {"schema": "researchos.generic-synthetic-run.v1", "scope": SCOPE,
               "actual_argv": argv, "cwd": str(HERE), "started_at": started,
               "ended_at": datetime.now(timezone.utc).isoformat(), "exit_code": output.returncode,
               "input_digest": digest, "source_hashes": hashes, "source_unchanged_during_run": unchanged,
               "stdout_sha256": sha(directory / "stdout.txt"), "stderr_sha256": sha(directory / "stderr.txt"),
               "main_read": {"actual_argv": main_argv, "cwd": str(REPO), "exit_code": main_output.returncode,
                             "state_before_sha256": main_state_before, "state_after_sha256": main_state_after,
                             "stdout_sha256": sha(directory / "main-read.stdout.json"),
                             "stderr_sha256": sha(directory / "main-read.stderr.txt")},
               "formal_assertion_count": 0, "formal_accepted_case_count": 0, "product_commands_executed": 0}
    write(directory / "receipt.json", receipt)
    print(json.dumps({"scope": SCOPE, "exit_code": output.returncode, "source_unchanged": unchanged,
                      "main_read_exit_code": main_output.returncode,
                      "receipt": str(directory / "receipt.json"), "receipt_sha256": sha(directory / "receipt.json")}, ensure_ascii=False))
    scratch = HERE / ".synthetic-work"
    if scratch.exists() and scratch.resolve().parent == HERE.resolve() and not any(scratch.iterdir()):
        scratch.rmdir()
    return output.returncode if unchanged else 3


if __name__ == "__main__":
    raise SystemExit(main())
