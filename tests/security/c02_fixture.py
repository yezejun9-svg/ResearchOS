"""Strict W17/C02 public fixture: real loopback HTTP, SQLite, local import copies.

Run with RESEARCHOS_TASK_ID=W17, RESEARCHOS_CASE_ID=C02, and CHECK_ID unset.
This runner cannot stand in for W17-G01, other cases, a live gate or a provider.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = ROOT / "tests/security/c02_expected.json"
TEST = "TestW17C02ProjectIsolation"
ROLES = {"READER", "PLANNER", "EXECUTOR"}


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def validate_inventory(inventory: dict) -> list[str]:
    require(inventory.get("task_id") == "W17" and inventory.get("case_id") == "C02"
            and inventory.get("measurement_mode") == "FIXTURE" and inventory.get("go_test") == TEST,
            "Inventory is not the frozen W17/C02 fixture binding")
    ids = inventory.get("required_assertions")
    require(isinstance(ids, list) and len(ids) == 22 and len(set(ids)) == len(ids)
            and {"C02-01", "C02-02"}.issubset(ids), "Nonzero unique C02 inventory required")
    return ids


def validate_evidence(events: list[dict], records: list[dict], ids: list[str]) -> dict:
    package_end = [e for e in events if e.get("Action") in ("pass", "fail") and not e.get("Test")]
    require(len(package_end) == 1 and package_end[0]["Action"] == "pass", "Go package did not pass")
    passed = [e.get("Test") for e in events if e.get("Action") == "pass" and e.get("Test")]
    require(passed == [TEST] and not any(e.get("Action") == "fail" for e in events), "Wrong or missing executed test")
    stdout_assertions = []
    for event in events:
        output = event.get("Output", "")
        if output.startswith("W17_C02_ASSERTION "):
            stdout_assertions.append(json.loads(output[len("W17_C02_ASSERTION "):]))
    assertions = [r for r in records if r.get("record_type") == "assertion"]
    actual_ids = [a.get("assertion_id") for a in assertions]
    require(len(actual_ids) == len(set(actual_ids)) and set(actual_ids) == set(ids), "Assertion inventory differs")
    require(assertions == stdout_assertions, "Raw Go output and persisted assertions differ")
    require(all(a.get("status") == "PASS" and a.get("mode") == "FIXTURE" and a.get("expected") == a.get("actual")
                for a in assertions), "A required assertion failed")
    http = [r for r in records if r.get("record_type") == "http"]
    require(len(http) >= 100 and len({r["request_id"] for r in http}) == len(http), "Nonzero real HTTP transcript required")
    require(all(r.get("started_at") and r.get("finished_at") and r.get("raw_request") and r.get("raw_response")
                and r.get("credential") == "REDACTED" for r in http), "Incomplete raw request/response evidence")
    require(all("Authorization: Bearer [REDACTED]" in r["raw_request"] for r in http), "Unredacted authorization header")
    a_responses = [r for r in http if r.get("audience") == "A"]
    marker = "fixture_b_private_marker"
    positive = [r for r in http if r.get("audience") == "B_CONTROL" and r.get("status") == 200 and marker in r["response_body"]]
    require(bool(positive), "B secret marker positive control missing")
    materials = [r for r in records if r.get("record_type") == "materialized_file"]
    logs = [r for r in records if r.get("record_type") == "service_log"]
    require(bool(a_responses) and bool(materials) and len(logs) == 1, "Scan inputs absent")
    leaks = [r for r in a_responses if marker in r["raw_response"]]
    leaks += [r for r in materials + logs if marker in r["body"]]
    require(not leaks, "Private marker escaped into A output or service log")
    require({r.get("role") for r in materials} == ROLES, "All three roles must materialize authorized inputs")
    matrix = []
    for role in sorted(ROLES):
        rows = [r for r in a_responses if r.get("role") == role]
        require(any(r["status"] == 200 and "fixture_a_authorized_material" in r["response_body"] for r in rows), "A body positive missing: " + role)
        require(any(r["status"] == 200 and "fixture_explicit_shared_knowledge" in r["response_body"] for r in rows), "Shared body positive missing: " + role)
        require(sum(r["status"] in (403, 404) for r in rows) >= 15, "Genuine authorization denials missing: " + role)
        require(not any(r["status"] == 401 for r in rows), "Expired or invalid credentials cannot prove isolation")
        for row in rows:
            matrix.append({key: row[key] for key in ("role", "action", "method", "path", "status", "request_id")})
    readbacks = [r for r in records if r.get("record_type") == "sqlite_readback"]
    require(len(readbacks) == 1, "SQLite readback absent")
    readback = readbacks[0]
    require(readback["B_business_hash_before"] == readback["B_business_hash_after"], "A requests mutated B")
    shared = readback["data"]["shared_imports"]
    require(len(shared) == 2 and len({r["project_id"] for r in shared}) == 2
            and len({r["artifact_id"] for r in shared}) == 2 and len({r["root_id"] for r in shared}) == 2
            and len({r["content_hash"] for r in shared}) == 1, "Sharing did not use distinct scoped imports")
    require(readback["data"]["cross_project_references"] == 0, "Cross-project reference appeared")
    return {"assertions": assertions, "permission_matrix": matrix, "sqlite_readback": readback,
            "scan": {"A_http_responses": len(a_responses), "A_materialized_files": len(materials), "service_logs": len(logs),
                     "B_positive_controls": len(positive), "private_marker_matches": len(leaks),
                     "scan_scope": "All A response headers/bodies, actual materialized files and HTTP service ErrorLog; submitted query inputs and labelled B positive controls excluded."},
            "http_count": len(http)}


def main() -> int:
    output = {"status": "FAIL", "assertions": 0, "assertion_ids": [], "receipt": None}
    report = None
    out = None
    began = time.monotonic()
    try:
        require(len(sys.argv) == 1, "This runner takes no arguments; its only binding is TASK=W17 CASE=C02")
        require(os.environ.get("RESEARCHOS_TASK_ID") == "W17" and os.environ.get("RESEARCHOS_CASE_ID") == "C02"
                and not os.environ.get("RESEARCHOS_CHECK_ID"), "Only TASK=W17 CASE=C02 with CHECK unset is bound")
        require(os.environ.get("RESEARCHOS_MEASUREMENT_MODE", "FIXTURE") == "FIXTURE", "Only FIXTURE is authorized")
        require(os.environ.get("RESEARCHOS_MODE", "FIXTURE") == "FIXTURE", "Only FIXTURE is authorized")
        inventory = json.loads(EXPECTED.read_text(encoding="utf-8"))
        ids = validate_inventory(inventory)
        locked = json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]["go"]
        go = Path(os.environ.get("RESEARCHOS_GO", locked["path"]))
        require(go.is_file() and digest(go) == "sha256:" + locked["sha256"], "Locked Go executable hash differs")
        run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        out = ROOT / "execution/receipts/W17/c02" / run
        out.mkdir(parents=True)
        output["receipt"] = str(out / "report.json")
        tracked = subprocess.check_output(["git", "ls-files", "internal/domain", "internal/store", "adapters", "migrations/sqlite", "spec/v2.0/contracts", "go.mod", "go.sum"], cwd=ROOT, text=True).splitlines()
        paths = {ROOT / p for p in tracked} | {EXPECTED, Path(__file__), ROOT / "internal/domain/remote_isolation_test.go"}
        source_hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        save(out / "source-manifest.json", {"source_commit": head, "files": source_hashes, "go": {"path": str(go), "sha256": digest(go)}})
        report = {"status": "FAIL", "task_id": "W17", "case_id": "C02", "mode": "FIXTURE", "source_commit": head,
                  "execution_status": "EXECUTION_REPORTED", "independent_acceptance": "PENDING", "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "project_identity": json.loads((ROOT / "execution/project_identity.json").read_text(encoding="utf-8")),
                  "platform": platform.platform(), "cwd": str(ROOT), "assertions": [], "real_provider_called": False,
                  "real_product_database_accessed": False, "formal_holdout_accessed": False,
                  "limitations": ["Public fixture files and temporary SQLite only; no product database, provider, protected service or host isolation claim.",
                                  "Sharing is explicitly authorized trusted local Owner import into distinct project roots and artifact copies. Provenance text alone is not authority; no general sharing API is added.",
                                  "READER/EXECUTOR may read and materialize context; context creation remains PLANNER/SCHEDULER-only per frozen API.",
                                  "Real local source capture writes LIVE source metadata for observed filesystem bytes; this complete acceptance run is FIXTURE.",
                                  "Go testing removes all generated fixture databases, credentials and materialized directories at exit. Hashes/readback/transcripts survive."]}
        command = [str(go), "test", "./internal/domain", "-run", "^" + TEST + "$", "-count=1", "-timeout=90s", "-json"]
        report["command"] = command
        env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", W17_C02_EVIDENCE_DIR=str(out))
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=180)
        (out / "go.stdout.jsonl").write_text(result.stdout, encoding="utf-8")
        (out / "go.stderr.log").write_text(result.stderr, encoding="utf-8")
        report["exit_code"] = result.returncode
        require(result.returncode == 0, "Go fixture failed; see raw stdout/stderr")
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        records = [json.loads(line) for line in (out / "audit.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        checked = validate_evidence(events, records, ids)
        require(source_hashes == {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}, "Source changed during execution")
        save(out / "permission-matrix.json", checked.pop("permission_matrix"))
        save(out / "sqlite-readback.json", checked.pop("sqlite_readback"))
        save(out / "marker-scan.json", checked["scan"])
        report.update(checked)
        report["status"] = output["status"] = "PASS"
        output["assertions"] = len(ids)
        output["assertion_ids"] = ids
    except Exception as error:
        output["error"] = str(error)
        if report is not None:
            report["error"] = traceback.format_exc()
    finally:
        if report is not None and out is not None:
            report["elapsed_seconds"] = round(time.monotonic() - began, 3)
            report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report["evidence_hashes"] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}
            save(out / "report.json", report)
            save(out / "evidence-index.json", {"source_commit": report["source_commit"], "files": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}})
        print(json.dumps(output, ensure_ascii=False))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
