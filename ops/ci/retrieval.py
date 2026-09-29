#!/usr/bin/env python3
"""W09 product HTTP/SQLite and real local filesystem checks; verifier signs later."""
import hashlib
import json
import os
import platform
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = {
    "TestW09C19ExplicitOriginAndUnknown": ("./internal/domain", ["C19-01", "C19-02", "C19-03", "C19-04"]),
    "TestW09A06HTTPInvalidationAndContext": ("./internal/domain", ["A06-01", "A06-02"]),
    "TestW09A06FTSFallbackAndDuplicatePath": ("./internal/domain", ["A06-03"]),
    "TestW09RootReadRejectsEscape": ("./adapters/retrieval", []),
    "TestW09UnicodeLocator": ("./internal/domain", ["W09-G02-UNICODE-LOCATOR"]),
    "TestW09RootIdentityRejectsReplacement": ("./adapters/retrieval", []),
    "TestW09RootReplacementCannotFeedProduct": ("./internal/domain", ["W09-G02-ROOT-REPLACEMENT"]),
    "TestW09TaskInputCannotRematerializeStaleLocalBody": ("./internal/domain", ["W09-G02-STALE-INPUT-BODY"]),
    "TestW09LegacyRootMigrationRevokesUnidentifiedRoot": ("./internal/domain", ["W09-G02-LEGACY-ROOT"]),
}
GROUPS = {
    "W09-G01": ["TestW09C19ExplicitOriginAndUnknown", "TestW09A06HTTPInvalidationAndContext",
                "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape"],
    "W09-G02": [name for name in TESTS if name != "TestW09C19ExplicitOriginAndUnknown"],
}
CASES = {
    "C19": ["TestW09C19ExplicitOriginAndUnknown"],
    "A06": [name for name in TESTS if name != "TestW09C19ExplicitOriginAndUnknown"],
}
SOURCES = [
    "adapters/retrieval/local.go", "adapters/retrieval/local_test.go",
    "adapters/retrieval/identity_windows.go", "adapters/retrieval/identity_unix.go",
    "internal/domain/retrieval.go", "internal/domain/retrieval_local.go",
    "internal/domain/evidence_origin.go", "internal/domain/retrieval_test.go",
    "internal/domain/http.go", "internal/domain/context.go", "internal/domain/materialize.go",
    "internal/domain/contracts.go", "migrations/sqlite/0007_retrieval.sql",
    "migrations/sqlite/0009_retrieval_root_identity.sql",
    "ops/ci/retrieval.py", "go.mod", "go.sum",
]


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, evidence, timeout=180):
    options = {"cwd": ROOT, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
               "env": os.environ.copy()}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(command, **options)
    timed_out = False
    try:
        out, err = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        if os.name == "nt":
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=10, check=False)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        try:
            out, err = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
        out, err = out or exc.stdout or b"", err or exc.stderr or b""
    stdout = evidence / "go-test.stdout.jsonl"
    stderr = evidence / "go-test.stderr.txt"
    stdout.write_bytes(out)
    stderr.write_bytes(err)
    return (-1 if timed_out else process.returncode), timed_out, stdout, stderr


def main():
    task = os.getenv("RESEARCHOS_TASK_ID", "W09")
    check = os.getenv("RESEARCHOS_CHECK_ID", "")
    case = os.getenv("RESEARCHOS_CASE_ID", "")
    mode = os.getenv("RESEARCHOS_RETRIEVAL_MODE", "")
    evidence = ROOT / "execution/receipts/W09/retrieval" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True)
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout.rstrip("\r\n")
    report = {
        "status": "FAIL", "task_id": task, "check_id": check or None, "case_id": case or None,
        "scope": "LIVE_WINDOWS_LOCAL" if check == "W09-G02" or case == "A06" and check != "W09-G01" else "FIXTURE_IMPLEMENTED_SERVICE",
        "retrieval_backend": "SQLite FTS5 with bounded scan on FTS failure",
        "sirchmunk_status": "NOT_SELECTED",
        "formal_construction_acceptance": "PENDING_INDEPENDENT_VERIFIER",
        "assertions": 0, "assertion_ids": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "version_manifest": {
            "git_head": git("rev-parse", "HEAD"),
            "git_status_porcelain": git("status", "--porcelain"),
            "tracked_status_porcelain": git("status", "--porcelain", "--untracked-files=no"),
            "source_sha256": {name: digest(ROOT / name) for name in SOURCES},
            "go_lock_sha256": digest(ROOT / "execution/toolchains/locked.json"),
            "spec_manifest_sha256": digest(ROOT / "spec/v2.0/PACKAGE_MANIFEST.json"),
            "os": platform.system(), "os_release": platform.release(),
            "local_time_with_offset": datetime.now().astimezone().isoformat(),
            "timezone_names": list(time.tzname),
            "external_services": "NOT_APPLICABLE",
        },
    }
    try:
        if task != "W09" or (check and check not in GROUPS) or (case and case not in CASES):
            raise ValueError("NOT_IMPLEMENTED: unknown task/check/case selector")
        if not check and not case:
            raise ValueError("NOT_IMPLEMENTED: explicit W09 check or case required")
        if mode and mode not in {"fixture", "live"}:
            raise ValueError("NOT_IMPLEMENTED: unknown retrieval mode")
        if (mode == "fixture" and check == "W09-G02"
                or mode == "live" and check == "W09-G01"
                or mode == "live" and case == "C19"
                or mode == "fixture" and case == "A06" and check != "W09-G01"):
            raise ValueError("NOT_IMPLEMENTED: mode/check mismatch")
        selected = GROUPS[check] if check else list(TESTS)
        if case:
            selected = [name for name in selected if name in CASES[case]]
        if not selected:
            raise ValueError("NOT_IMPLEMENTED: empty selector intersection")
        locked = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))
        go = os.getenv("RESEARCHOS_GO") or locked["tools"]["go"]["path"]
        packages = sorted({TESTS[name][0] for name in selected})
        command = [go, "test", "-count=1", "-json", "-run", "^(?:" + "|".join(selected) + ")$", *packages]
        report["actual_invocation"] = command
        exit_code, timed_out, stdout, stderr = run(command, evidence)
        report.update(exit_code=exit_code, timed_out=timed_out,
                      raw_evidence_references=[str(path.relative_to(ROOT)).replace("\\", "/")
                                               for path in (stdout, stderr)])
        events = []
        for line in stdout.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        passed = {event["Test"] for event in events if event.get("Action") == "pass" and event.get("Test")}
        emitted = "".join(event.get("Output", "") for event in events)
        records = []
        for line in emitted.splitlines():
            if line.startswith("W09_ASSERTION "):
                record = json.loads(line.removeprefix("W09_ASSERTION "))
                record["raw_evidence_reference"] = str(stdout.relative_to(ROOT)).replace("\\", "/")
                records.append(record)
        wanted = [assertion for name in selected for assertion in TESTS[name][1]]
        found = [record["assertion_id"] for record in records]
        okay = (exit_code == 0 and not timed_out and set(selected) <= passed
                and sorted(wanted) == sorted(found) and len(found) == len(set(found))
                and len(found) > 0 and all(record.get("status") == "PASS" for record in records))
        report.update(status="PASS" if okay else "FAIL", assertions=len(found), assertion_ids=found,
                      expected_assertion_ids=wanted, missing_assertion_ids=sorted(set(wanted) - set(found)),
                      passed_tests=sorted(passed & set(selected)), selected_tests=selected,
                      assertion_results=records,
                      owned_acceptance_ids=[item for item, tests in CASES.items() if set(tests) <= set(selected)])
    except Exception as exc:
        report["error"] = str(exc)
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    path = evidence / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["report_reference"] = str(path.relative_to(ROOT)).replace("\\", "/")
    print(json.dumps({key: value for key, value in report.items() if key != "assertion_results"}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" and report["assertions"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
