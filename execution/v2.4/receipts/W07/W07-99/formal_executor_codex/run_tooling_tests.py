"""Record an actual bounded local tooling test; never runs product LIVE."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-dir", required=True, type=Path)
    parser.add_argument("--acceptance-baseline", required=True, type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[6]
    assert (repo / "execution/v2.4/formal_profile_w07_test.py").is_file()
    proof_dir = args.proof_dir.resolve(strict=True)
    baseline = args.acceptance_baseline.resolve(strict=True)
    assert digest(baseline) == "ae8aa1ce632aecce595b2adbcb05fd73aa7360b8fd4186fcef6fd5e7872caa66"
    prefix = repo / "execution/v2.4/receipts/W07/W07-99/formal_executor_codex"
    folder = prefix / ("tooling-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    folder.mkdir(exist_ok=False)
    names = ["execution/v2.4/formal_case_index.py", "execution/v2.4/formal_profile_w07.py",
             "execution/v2.4/formal_profile_w07_test.py", "execution/toolchains/locked.json"]
    before = {n: digest(repo / n) for n in names}
    tools = json.loads((repo / "execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]
    python = tools["python"]
    assert digest(python["path"]) == python["sha256"]
    argv = [python["path"], "-B", "-X", "utf8", "execution/v2.4/formal_profile_w07_test.py"]
    started = datetime.now(timezone.utc).isoformat()
    env = dict(os.environ, W07_ACTUAL_PROOF_DIR=str(proof_dir), W07_ACCEPTANCE_BASELINE_PATH=str(baseline))
    timed_out = False
    try:
        result = subprocess.run(argv, cwd=repo, env=env, capture_output=True, timeout=180)
        out, err, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        out, err, code, timed_out = exc.stdout or b"", exc.stderr or b"", None, True
    for name, value in (("stdout.raw", out), ("stderr.raw", err)):
        (folder / name).write_bytes(value)
    after = {n: digest(repo / n) for n in names}
    stderr = err.decode("utf-8", errors="strict")
    match = re.search(r"Ran (\d+) tests", stderr)
    count = int(match[1]) if match else 0
    clean = code == 0 and count > 0 and not timed_out and before == after and "skipped=" not in stderr
    receipt = {"schema": "researchos.w07.formal-tooling-test-execution.v1",
               "scope": "LOCAL_TOOLING_TEST_NOT_PRODUCT_LIVE_ACCEPTANCE", "actor": "codex:/root",
               "actualargv": argv, "cwd": str(repo), "started_at": started,
               "ended_at": datetime.now(timezone.utc).isoformat(), "exit_code": code, "timed_out": timed_out,
               "test_count": count, "status": "PASS" if clean else "FAIL", "source_before": before,
               "source_after": after, "source_unchanged": before == after,
               "actual_product_evidence_dir": str(proof_dir), "actual_proof_sha256": digest(proof_dir / "proof.json"),
               "acceptance_baseline_path": str(baseline), "acceptance_baseline_sha256": digest(baseline),
               "python_sha256": digest(python["path"]), "formal_count_delta": 0,
               "raw_refs": [{"path": (folder / n).relative_to(repo).as_posix(), "sha256": digest(folder / n)}
                            for n in ("stdout.raw", "stderr.raw")]}
    (folder / "result.json").write_bytes((json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"receipt": (folder / "result.json").relative_to(repo).as_posix(), "exit": code,
                      "tests": count, "source_drift": before != after, "status": receipt["status"]}))
    if not clean:
        print(stderr[-6000:])
    return 0 if clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
