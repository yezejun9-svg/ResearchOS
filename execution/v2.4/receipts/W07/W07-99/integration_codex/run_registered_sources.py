"""Execute the four actual registered W07 checks; no acceptance is issued."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", required=True, type=Path)
    args = parser.parse_args()
    proof_path = args.proof.resolve(strict=True)
    assert proof_path.is_relative_to(ROOT / "execution/v2.4/receipts/W07/W07-99/source_executor_codex")
    proof = json.loads(proof_path.read_bytes())
    assert proof["mode"] == "LIVE_SERVICE"
    source = json.loads((ROOT / proof["source_before_ref"]["path"]).read_bytes())
    assert source == json.loads((ROOT / proof["source_after_ref"]["path"]).read_bytes())
    assert all(sha(ROOT / path) == digest.removeprefix("sha256:") for path, digest in source.items())
    lock = json.loads((ROOT / "execution/toolchains/locked.json").read_bytes())
    python = lock["tools"]["python"]
    assert sha(Path(python["path"])) == python["sha256"]
    run = HERE / "native-runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10])
    run.mkdir(parents=True)
    (run / "runner.py.txt").write_bytes(Path(__file__).read_bytes())
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", RESEARCHOS_W07_PROOF_REF=str(proof_path))
    inputs = {"schema": "researchos.root-w07-native-inputs.v1", "started_at": now(),
              "root_actor": "codex:/root", "scope": "ACTUAL_REGISTERED_CONSTRUCTION_NOT_FORMAL_ACCEPTANCE",
              "proof_ref": ref(proof_path), "tool": python,
              "registry_refs": [ref(ROOT / path) for path in ("execution/commands.json", "execution/v2.4/commands.json", "execution/toolchains/locked.json", "execution/command_dispatcher/dispatch.py")],
              "source_before_ref": proof["source_before_ref"], "source_files": len(source)}
    write(run / "inputs.json", inputs)
    results = []
    for ident, key, spec, selector in (
        ("W07-G01", "test.sources.fixture", "v2.0", "--check-id"),
        ("W07-G02", "test.sources.live", "v2.4", "--check-id"),
        ("W07-H07", "test.sources.live", "v2.4", "--check-id"),
        ("A05", "test.sources.live", "v2.4", "--case-id"),
    ):
        argv = [python["path"], "-B", "-X", "utf8", "execution/command_dispatcher/dispatch.py", key,
                "--spec", spec, "--task-id", "W07", selector, ident]
        row = {"id": ident, "actual_argv": argv, "cwd": str(ROOT), "started_at": now()}
        with (run / (ident + ".stdout.raw")).open("wb") as stdout, (run / (ident + ".stderr.raw")).open("wb") as stderr:
            try:
                row["actual_exit_code"] = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr, timeout=1900).returncode
            except subprocess.TimeoutExpired:
                row["actual_exit_code"] = 124
        row.update(ended_at=now(), stdout_ref=ref(run / (ident + ".stdout.raw")), stderr_ref=ref(run / (ident + ".stderr.raw")))
        if row["actual_exit_code"] == 0:
            output = json.loads((run / (ident + ".stdout.raw")).read_bytes())
            receipt = Path(output["receipt"]).resolve(strict=True)
            assert receipt.is_relative_to(ROOT / "execution/invocations")
            row["receipt_ref"] = ref(receipt)
            row["reported_status"] = output["status"]
        write(run / (ident + ".wrapper.json"), row)
        results.append(row)
        print(json.dumps({"id": ident, "exit": row["actual_exit_code"], "receipt": row.get("receipt_ref")}), flush=True)
        if row["actual_exit_code"] != 0:
            break
    drift = [path for path, digest in source.items() if sha(ROOT / path) != digest.removeprefix("sha256:")]
    result = {"schema": "researchos.root-w07-native-results.v1", "started_at": inputs["started_at"], "ended_at": now(),
              "inputs_ref": ref(run / "inputs.json"), "registered_commands": [{"id": r["id"], "receipt_ref": r["receipt_ref"]} for r in results if "receipt_ref" in r],
              "results": results, "source_drift": drift, "formal_acceptance_delta": 0, "parent_acceptance_delta": 0}
    passed = len(results) == 4 and not drift and all(r["actual_exit_code"] == 0 and r.get("reported_status") == "PASS" for r in results)
    result["status"] = "PASS" if passed else "FAIL"
    write(run / "result.json", result)
    print(json.dumps({"status": result["status"], "result_ref": ref(run / "result.json")}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
