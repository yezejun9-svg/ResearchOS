#!/usr/bin/env python3
"""Run actual W03 domain fixtures. Product acceptance remains NOT_RUN."""
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GROUPS = {
    "W03-G01": ["TestW03SchemaMigrationDefaults", "TestW03OperationCoverage", "TestW03PrivateOwnerBootstrap"],
    "W03-G02": ["TestW03PreconditionReplayAuthorization", "TestW03ConcurrentWriteOutboxRollback",
                "TestW03ReferenceIsolationAndHistoricalHash", "TestW03DeferredContractAndScope",
                "TestW03GoalTaskDraftAndRefusals", "TestW03CursorSnapshotAndReceipt",
                "TestW03CursorQueryBinding", "TestW03SlowBodyDoesNotBlockDatabase"],
    "W03-G03": ["TestW03ContentSealAccessAndImmutability", "TestW03RestrictedMetadataPositiveAndNegative",
                "TestJSON", "TestUTF16AndFieldOrder", "TestW03ExactIntegerOverflow"],
}


def main():
    task = os.getenv("RESEARCHOS_TASK_ID", "W03")
    check = os.getenv("RESEARCHOS_CHECK_ID", "")
    if task != "W03" or (check and check not in GROUPS) or os.getenv("RESEARCHOS_CASE_ID"):
        raise NotImplementedError("unbound task/check/case selection")
    expected = GROUPS[check] if check else [test for tests in GROUPS.values() for test in tests]
    go = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]["go"]["path"]
    command = [go, "test", "-count=1", "-json", "-run", "^(" + "|".join(expected) + ")$",
               "./internal/domain", "./internal/canonical", "./apps/control"]
    evidence = ROOT / "execution/receipts/W03/domain" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
    (evidence / "stdout.jsonl").write_text(result.stdout, encoding="utf-8")
    (evidence / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    passed = {item["Test"] for item in events if item.get("Action") == "pass" and "Test" in item}
    report = {"status": "PASS" if result.returncode == 0 and set(expected) <= passed else "FAIL",
              "scope": "DEVELOPMENT_FIXTURE_ONLY", "task_id": task, "check_id": check or None,
              "assertions": len(passed), "assertion_ids": sorted(passed), "expected_assertion_ids": expected,
              "missing_assertion_ids": sorted(set(expected) - passed), "actual_invocation": command,
              "exit_code": result.returncode, "started_at": started,
              "ended_at": datetime.now(timezone.utc).isoformat(),
              "raw_evidence_references": [str((evidence / "stdout.jsonl").relative_to(ROOT)),
                                          str((evidence / "stderr.txt").relative_to(ROOT))],
              "owned_acceptance_ids": [], "formal_product_acceptance": "NOT_RUN"}
    (evidence / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    try:
        report = main()
    except Exception as exc:
        report = {"status": "NOT_IMPLEMENTED" if isinstance(exc, NotImplementedError) else "FAIL",
                  "assertions": 0, "assertion_ids": [], "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if report["status"] == "PASS" and report["assertions"] > 0 else 1)
