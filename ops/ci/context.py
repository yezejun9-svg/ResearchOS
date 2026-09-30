#!/usr/bin/env python3
"""Run W04 HTTP/module fixtures and retain exact assertions, including failures."""
import hashlib
import platform
import time
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = {"C03": "TestW04C03", "C04": "TestW04C04", "A01": "TestW04A01"}
GROUPS = {
    "W04-G01": ["TestW04A01", "TestW04CanonicalNumbers"],
    "W04-G02": ["TestW04C03", "TestW04C04", "TestW04DecisionDependencies", "TestW04CandidateIndependence"],
    "W04-G03": ["TestW04ContextRecovery", "TestW04RestrictedContext"],
}
EXPECTED = {
    "TestW04DecisionDependencies": ["W04-G02-DEPENDENCY-rubric_ref", "W04-G02-DEPENDENCY-evidence_refs", "W04-G02-DEPENDENCY-subject_ref"],
    "TestW04CandidateIndependence": ["W04-G02-CANDIDATE-SELF", "W04-G02-HISTORY-NOT-CANDIDATE"],
    "TestW04A01": ["A01-01", "A01-02", "A01-03"],
    "TestW04C03": ["C03-01", "C03-02", "C03-03"],
    "TestW04C04": ["C04-01", "C04-02", "C04-03"],
    "TestW04CanonicalNumbers": ["W04-G01-NUMBERS"],
    "TestW04ContextRecovery": ["W04-G03-RECOVERY", "W04-G03-PROFILE", "W04-G03-REBUILT", "W04-G03-REVOKED"],
    "TestW04RestrictedContext": ["W04-G03-RESTRICTED"],
}

def version_manifest():
    sampled = datetime.now(timezone.utc).isoformat()
    def git(*args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
        return result.stdout.rstrip("\r\n")
    sources = ["internal/domain/context.go", "internal/domain/changes.go", "internal/domain/conflicts.go",
               "internal/domain/import.go", "internal/domain/materialize.go", "internal/domain/http.go",
               "internal/domain/contracts.go", "internal/domain/operations.go", "internal/domain/store.go",
               "internal/domain/domain_test.go", "internal/domain/context_test.go", "internal/domain/context_regression_test.go",
               "migrations/sqlite/0003_context.sql", "ops/ci/context.py", "go.mod", "go.sum"]
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    status = git("status", "--porcelain")
    return {"sampled_at": sampled, "git_head": git("rev-parse", "HEAD"),
            "git_status_porcelain": status, "working_tree_clean": not bool(status),
            "tracked_status_porcelain": git("status", "--porcelain", "--untracked-files=no"),
            "os": platform.system(), "os_release": platform.release(), "architecture": platform.machine(),
            "timezone": str(datetime.now().astimezone().tzinfo), "timezone_names": list(time.tzname), "local_time_with_offset": datetime.now().astimezone().isoformat(),
            "python_version": platform.python_version(),
            "spec_manifest_sha256": hashlib.sha256((ROOT / "spec/v2.0/PACKAGE_MANIFEST.json").read_bytes()).hexdigest(),
            "go_lock_sha256": hashlib.sha256((ROOT / "execution/toolchains/locked.json").read_bytes()).hexdigest(),
            "source_sha256": hashes,
            "model_runtime": {"status": "NOT_APPLICABLE", "reason": "Pure deterministic Go/HTTP/SQLite fixtures; no model invocation."},
            "external_services": {"status": "NOT_APPLICABLE", "reason": "No external service or provider is used."}}

def main():
    versions = version_manifest()
    evidence = ROOT / "execution/receipts/W04/context" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True)
    task, check, case = (os.getenv(k, default) for k, default in [
        ("RESEARCHOS_TASK_ID", "W04"), ("RESEARCHOS_CHECK_ID", ""), ("RESEARCHOS_CASE_ID", "")])
    report = {"status": "FAIL", "task_id": task, "check_id": check or None,
              "case_id": case or None, "scope": "FIXTURE_IMPLEMENTED_SERVICE",
              "formal_construction_acceptance": "PENDING_INDEPENDENT_VERIFIER",
              "product_live_qualification": "NOT_RUN", "assertions": 0, "assertion_ids": [],
              "started_at": datetime.now(timezone.utc).isoformat(), "version_manifest": versions}
    try:
        if task != "W04" or (check and check not in GROUPS) or (case and case not in CASES):
            raise ValueError("unknown task/check/case selector")
        selected = GROUPS[check] if check else [t for group in GROUPS.values() for t in group]
        if case:
            selected = [test for test in selected if test == CASES[case]]
        if not selected:
            raise ValueError("selector intersection contains zero tests")
        go = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]["go"]["path"]
        command = [go, "test", "-count=1", "-json", "-run", "^(" + "|".join(selected) + ")$", "./internal/domain"]
        report["actual_invocation"] = command
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=150)
        (evidence / "stdout.jsonl").write_text(result.stdout, encoding="utf-8")
        (evidence / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
        passed = {event["Test"] for event in events if event.get("Action") == "pass" and "Test" in event}
        records = []
        output = "".join(event.get("Output", "") for event in events)
        for line in output.splitlines():
            if line.startswith("W04_ASSERTION "):
                record = json.loads(line.removeprefix("W04_ASSERTION "))
                record["raw_evidence_reference"] = str((evidence / "stdout.jsonl").relative_to(ROOT)).replace("\\", "/")
                records.append(record)
        wanted = [item for test in selected for item in EXPECTED[test]]
        found = [item["assertion_id"] for item in records]
        okay = (result.returncode == 0 and set(selected) <= passed and sorted(found) == sorted(wanted)
                and all(item["status"] == "PASS" for item in records) and len(records) > 0)
        report.update(status="PASS" if okay else "FAIL", exit_code=result.returncode,
                      assertions=len(records), assertion_ids=found, expected_assertion_ids=wanted,
                      missing_assertion_ids=sorted(set(wanted) - set(found)),
                      assertion_results=records, owned_acceptance_ids=[c for c, test in CASES.items() if test in selected],
                      raw_evidence_references=[str((evidence / name).relative_to(ROOT)).replace("\\", "/")
                                               for name in ["stdout.jsonl", "stderr.txt"]])
    except Exception as exc:
        report["error"] = str(exc)
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    path = evidence / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "assertion_results"}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" and report["assertions"] else 1

if __name__ == "__main__":
    if os.getenv("RESEARCHOS_TASK_ID") == "W06":
        sys.exit(subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "ops/ci/orchestration.py"), "--mode", "fixture"]))
    sys.exit(main())
