"""Record actual synthetic validator tests, keeping every attempt immutable."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


HERE = Path(__file__).resolve().parent
SCOPE = "SYNTHETIC_INTEGRITY_CONTROLS_NOT_PRODUCT_EVIDENCE"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    hashes = {name: sha(HERE / name) for name in ("validate.py", "test_validate.py", "run_synthetic.py", "README.md")}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    records = HERE / "synthetic-runs"
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
    for name in hashes:
        (archive / name).write_bytes((HERE / name).read_bytes())
    argv = [sys.executable, "-B", "-X", "utf8", str(HERE / "test_validate.py")]
    started = datetime.now(timezone.utc).isoformat()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    output = subprocess.run(argv, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (directory / "stdout.txt").write_bytes(output.stdout)
    (directory / "stderr.txt").write_bytes(output.stderr)
    unchanged = hashes == {name: sha(HERE / name) for name in hashes}
    receipt = {"schema": "researchos.synthetic-validator-run.v1", "scope": SCOPE,
               "actual_argv": argv, "cwd": str(HERE), "started_at": started,
               "ended_at": datetime.now(timezone.utc).isoformat(), "exit_code": output.returncode,
               "input_digest": digest, "source_hashes": hashes, "source_unchanged_during_run": unchanged,
               "stdout_sha256": sha(directory / "stdout.txt"), "stderr_sha256": sha(directory / "stderr.txt"),
               "formal_assertion_count": 0, "formal_accepted_case_count": 0,
               "product_commands_executed": 0}
    write(directory / "receipt.json", receipt)
    print(json.dumps({"scope": SCOPE, "exit_code": output.returncode, "source_unchanged": unchanged,
                      "receipt": str(directory / "receipt.json"), "receipt_sha256": sha(directory / "receipt.json")}, ensure_ascii=False))
    # TemporaryDirectory removes each bounded test fixture; only remove an empty
    # scratch parent that is exactly inside this owned folder.
    scratch = HERE / ".synthetic-work"
    if scratch.exists() and scratch.resolve().parent == HERE.resolve() and not any(scratch.iterdir()):
        scratch.rmdir()
    return output.returncode if unchanged else 3


if __name__ == "__main__":
    sys.exit(main())
