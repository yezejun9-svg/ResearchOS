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
    "TestW09C19ChainInvalidation": ("./internal/domain", ["C19-05"]),
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
    "W09-G01": ["TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation", "TestW09A06HTTPInvalidationAndContext",
                "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape"],
    "W09-G02": [name for name in TESTS if not name.startswith("TestW09C19")],
}
CASES = {
    "C19": ["TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation"],
    "A06": [name for name in TESTS if not name.startswith("TestW09C19")],
}
SOURCES = [
    "adapters/retrieval/local.go", "adapters/retrieval/local_test.go",
    "adapters/retrieval/identity_windows.go", "adapters/retrieval/identity_unix.go",
    "internal/domain/retrieval.go", "internal/domain/retrieval_local.go",
    "internal/domain/evidence_origin.go", "internal/domain/retrieval_test.go",
    "internal/domain/w09_evidence_export_test.go", "internal/domain/domain_test.go",
    "internal/domain/http.go", "internal/domain/context.go", "internal/domain/materialize.go",
    "internal/domain/contracts.go", "migrations/sqlite/0007_retrieval.sql",
    "migrations/sqlite/0009_retrieval_root_identity.sql",
    "ops/ci/retrieval.py", "ops/ci/w09_formal_router.py", "ops/ci/w09_evidence_closure.py",
    "go.mod", "go.sum",
]


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, evidence, timeout=180):
    options = {"cwd": ROOT, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE,
               "env": os.environ.copy()}
    owned = evidence / "owned"
    owned.mkdir(mode=0o700)
    options["env"]["RESEARCHOS_W09_EVIDENCE_DIR"] = str(owned.resolve())
    options["env"]["RESEARCHOS_W09_RUN_ID"] = evidence.name.removeprefix("run-")
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
    with stdout.open("xb") as stream: stream.write(out)
    with stderr.open("xb") as stream: stream.write(err)
    return (-1 if timed_out else process.returncode), timed_out, stdout, stderr



def collect_w09_owned(owned, selected, records):
    """Pin actual test exports. Missing/foreign/duplicate/changed files fail closed."""
    root = owned.resolve(strict=True)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("W09_OWNED_EXPORT_ROOT_MISSING")
    pins, paths = [], set()
    for file in sorted(root.rglob("*.raw")):
        resolved = file.resolve(strict=True)
        if root not in resolved.parents or file.is_symlink():
            raise ValueError("W09_FOREIGN_EXPORT")
        relative = str(resolved.relative_to(root)).replace("\\", "/")
        if relative in paths:
            raise ValueError("W09_DUPLICATE_EXPORT")
        paths.add(relative)
        data = resolved.read_bytes()
        pins.append({"path": str(resolved.relative_to(ROOT)).replace("\\", "/"),
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    asserted = [r.get("owned_export_ref") for r in records]
    if not pins or len(asserted) != len(records) or any(not isinstance(p, dict) for p in asserted):
        return {"complete": False, "reason": "MISSING_ASSERTION_EXPORT", "members": pins}
    member_by_abs = {(ROOT / p["path"]).resolve(): p for p in pins}
    for record, claim in zip(records, asserted):
        path = Path(claim["path"]).resolve(strict=True)
        actual = member_by_abs.get(path)
        if actual is None or actual["sha256"] != claim["sha256"] or actual["bytes"] != claim["bytes"]:
            return {"complete": False, "reason": "ASSERTION_EXPORT_DRIFT", "members": pins}
        if path.parent.name != record.get("test_name") or not path.name.endswith("-assertion-" + record["assertion_id"] + ".raw"):
            return {"complete": False, "reason": "ASSERTION_EXPORT_ID_OR_OWNER", "members": pins}
    tests = {p["path"].split("/owned/", 1)[1].split("/", 1)[0] for p in pins if "/owned/" in p["path"]}
    domain_selected = {name for name in selected if TESTS[name][0] == "./internal/domain"}
    return {"complete": tests == domain_selected, "selected_tests": selected,
            "exported_tests": sorted(tests), "assertion_export_refs": asserted, "members": pins}

def main():
    task = os.getenv("RESEARCHOS_TASK_ID", "W09")
    if task == "W17":
        fixture = "c22_fixture.py" if os.getenv("RESEARCHOS_CASE_ID") == "C22" or os.getenv("RESEARCHOS_CHECK_ID") == "W17-G03" else "c02_fixture.py"
        return subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tests/security" / fixture), *sys.argv[1:]])
    if task == "W08":
        import research
        return research.main("test.research.fixture")
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
        "scope": "LIVE_WINDOWS_LOCAL" if check == "W09-G02" else "FIXTURE_IMPLEMENTED_SERVICE",
        "retrieval_backend": "SQLite FTS5 with bounded scan on FTS failure",
        "sirchmunk_status": "NOT_SELECTED",
        "formal_construction_acceptance": "NOT_RUN_POSTRUN_REVIEW_PENDING",
        "formal_case_accepted_delta": 0,
        "assertions": 0, "assertion_ids": [],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "run_id": evidence.name.removeprefix("run-"),
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
                or mode == "live" and case == "A06" and check != "W09-G02"):
            raise ValueError("NOT_IMPLEMENTED: mode/check mismatch")
        selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]
        if case:
            selected = [name for name in selected if name in CASES[case]]
        if not selected:
            raise ValueError("NOT_IMPLEMENTED: empty selector intersection")
        locked = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))
        go = os.getenv("RESEARCHOS_GO") or locked["tools"]["go"]["path"]
        go_path = Path(go).resolve(strict=True)
        go_raw = go_path.read_bytes()
        report["go_executable"] = {"path": str(go_path), "sha256": hashlib.sha256(go_raw).hexdigest(), "bytes": len(go_raw)}
        if report["go_executable"]["sha256"] != locked["tools"]["go"]["sha256"] or go_path != Path(locked["tools"]["go"]["path"]).resolve(strict=True):
            raise ValueError("LOCKED_GO_ACTUAL_MISMATCH")
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
        owned = evidence / "owned"
        export = collect_w09_owned(owned, selected, records)
        okay = okay and export["complete"]
        report["owned_export"] = export
        report.update(status="PASS" if okay else "FAIL", assertions=len(found), assertion_ids=found,
                      expected_assertion_ids=wanted, missing_assertion_ids=sorted(set(wanted) - set(found)),
                      passed_tests=sorted(passed & set(selected)), selected_tests=selected,
                      assertion_results=records,
                      owned_acceptance_ids=[item for item, tests in CASES.items() if set(tests) <= set(selected)])
    except Exception as exc:
        report["error"] = str(exc)
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    path = evidence / "report.json"
    with path.open("xb") as stream:
        stream.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    report_ref = str(path.relative_to(ROOT)).replace("\\", "/")
    tool_run = {"schema": "researchos.w09-native-producer-tool-run.v1",
                "run_id": report["run_id"], "report_ref": report_ref,
                "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "native_exit_code": report.get("exit_code"),
                "actual_invocation": report.get("actual_invocation"),
                "stdout_ref": report.get("raw_evidence_references", [None])[0],
                "stderr_ref": report.get("raw_evidence_references", [None, None])[1],
                "stdout_sha256": hashlib.sha256((evidence / "go-test.stdout.jsonl").read_bytes()).hexdigest()
                                 if (evidence / "go-test.stdout.jsonl").is_file() else None,
                "stderr_sha256": hashlib.sha256((evidence / "go-test.stderr.txt").read_bytes()).hexdigest()
                                 if (evidence / "go-test.stderr.txt").is_file() else None,
                "formal_acceptance": "NOT_RUN"}
    tool_path = evidence / "native-tool-run.json"
    with tool_path.open("xb") as stream:
        stream.write((json.dumps(tool_run, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    report["report_reference"] = report_ref
    report["tool_run_reference"] = str(tool_path.relative_to(ROOT)).replace("\\", "/")
    report["tool_run_sha256"] = hashlib.sha256(tool_path.read_bytes()).hexdigest()
    print(json.dumps({key: value for key, value in report.items() if key not in {"assertion_results", "owned_export"}}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" and report["assertions"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
