"""W18-01 construction check over the production backup CLI and native SQLite."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[2]
CHECK = "W18-01"
EXPECTED = {
    "W18-01-WAL-OMISSION",
    "W18-01-STATE-REVISIONS",
    "W18-01-COST-FAILURE",
    "W18-01-AUTHORIZATION",
    "W18-01-MANIFEST-CURSOR",
    "W18-01-NO-PLAINTEXT-CREDENTIAL",
    "W18-01-MIGRATION-ROLLBACK",
    "W18-01-SOURCE-STABLE",
}
SOURCE = [
    "internal/domain/backup.go",
    "internal/domain/backup_upgrade.go",
    "internal/domain/backup_w1801_windows_test.go",
    "ops/backup/main.go",
    "scripts/backup/w1801.py",
]


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def legacy():
    return subprocess.call([sys.executable, "ops/ci/backup.py"], cwd=ROOT)


def main():
    task, check, case = (os.environ.get(name, "") for name in
                         ("RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"))
    if task == "W18" and not case and check != CHECK and check in {"W18-G01", "W18-G02"}:
        return legacy()
    if task == "W18" and not check and case == "A12":
        return legacy()
    if task != "W18" or check != CHECK or case:
        print(json.dumps({"status": "NOT_IMPLEMENTED", "assertion_ids": [], "scope": "W18-01 exact selector required"}))
        return 3
    go = Path(os.environ.get("RESEARCHOS_GO", ""))
    if platform.system() != "Windows" or not go.is_absolute() or not go.is_file():
        print(json.dumps({"status": "UNAVAILABLE", "assertion_ids": [], "scope": "pinned Windows Go required"}))
        return 4

    run_id = str(uuid.uuid4())
    receipt = ROOT / "execution/v2.4/receipts/W18/W18-01" / run_id
    receipt.mkdir(parents=True, exist_ok=False)
    source_hashes = {path: digest((ROOT / path).read_bytes()) for path in SOURCE}
    source_hashes.update({p.relative_to(ROOT).as_posix(): digest(p.read_bytes())
                          for p in (ROOT / "migrations/sqlite").glob("*.sql")})
    argv = [str(go), "test", "./internal/domain", "-run", "^TestW1801BackupContract$",
            "-count=1", "-timeout=2m", "-v"]
    env_keys = {"SystemRoot", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA",
                "PATH", "GOTOOLCHAIN", "GOENV", "GOPATH", "GOCACHE", "RESEARCHOS_GO"}
    child_env = {k: v for k, v in os.environ.items() if k in env_keys}
    child_env["W18_EVIDENCE_DIR"] = str(receipt)
    before = {
        "task_id": task, "check_id": check, "run_id": run_id,
        "started_at": now(), "command": argv, "cwd": str(ROOT),
        "source_hashes": source_hashes, "expected_assertion_ids": sorted(EXPECTED),
        "environment_names": sorted(child_env), "environment_mode": "LIVE_WINDOWS_SQLITE_FIXTURE_BUSINESS",
        "provider_calls": 0, "independent_acceptance": "NOT_RUN",
    }
    write_json(receipt / "before.json", before)
    try:
        result = subprocess.run(argv, cwd=ROOT, env=child_env, capture_output=True, timeout=145)
        stdout, stderr, exit_code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, exit_code = exc.stdout or b"", exc.stderr or b"", 124
    (receipt / "stdout.txt").write_bytes(stdout)
    (receipt / "stderr.txt").write_bytes(stderr)

    assertions = []
    malformed = False
    for number, line in enumerate(stdout.decode("utf-8", errors="replace").splitlines(), 1):
        if not line.startswith("W18_ASSERTION "):
            continue
        try:
            row = json.loads(line.removeprefix("W18_ASSERTION "))
            if not isinstance(row, dict) or not all(k in row for k in
                ("assertion_id", "expected", "actual", "status", "evidence")):
                malformed = True
                continue
            row["raw_line"] = number
            assertions.append(row)
        except (ValueError, TypeError):
            malformed = True
    ids = [row["assertion_id"] for row in assertions]
    drift = [path for path, prior in source_hashes.items()
             if not (ROOT / path).is_file() or digest((ROOT / path).read_bytes()) != prior]
    passed = (exit_code == 0 and not malformed and not drift and len(ids) == len(EXPECTED)
              and set(ids) == EXPECTED and all(row["status"] == "PASS" and
              row["expected"] == row["actual"] for row in assertions))
    evidence_hashes = {p.relative_to(receipt).as_posix(): digest(p.read_bytes())
                       for p in receipt.rglob("*") if p.is_file()}
    report = {
        "task_id": task, "check_id": check, "run_id": run_id,
        "status": "PASS" if passed else "FAIL", "exit_code": exit_code,
        "assertions": assertions, "assertion_ids": ids,
        "expected_assertion_ids": sorted(EXPECTED),
        "missing": sorted(EXPECTED.difference(ids)), "unexpected": sorted(set(ids).difference(EXPECTED)),
        "malformed": malformed, "source_drift": drift,
        "raw_evidence_hashes": evidence_hashes, "ended_at": now(),
        "environment_mode": before["environment_mode"], "provider_calls": 0,
        "executor_status": "EXECUTION_REPORTED", "independent_acceptance": "NOT_RUN",
    }
    write_json(receipt / "report.json", report)
    print(json.dumps({"status": report["status"], "assertions": len(ids), "assertion_ids": ids,
                      "scope": before["environment_mode"], "receipt": str(receipt / "report.json")}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
