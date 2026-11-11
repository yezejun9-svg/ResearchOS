"""Strict W17/C22 fixture runner: native AppContainer plus host-issued HTTP.

This reports execution only. Independent acceptance and all LIVE authority remain
outside this fixture. TASK=W17 with CASE=C22 or CHECK=W17-G03 is required.
"""
from __future__ import annotations

import base64
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
EXPECTED = ROOT / "tests/security/c22_expected.json"
TEST = "TestW17C22ProtectedIsolation"
MARKER = "fixture_holdout_private_marker"
PHASES = ("before-restart", "after-restart")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_inventory(inventory: dict) -> list[str]:
    require(inventory.get("task_id") == "W17" and inventory.get("case_id") == "C22"
            and inventory.get("measurement_mode") == "FIXTURE" and inventory.get("go_test") == TEST
            and inventory.get("restricted_marker") == MARKER, "Incorrect frozen C22 fixture binding")
    ids = inventory.get("required_assertions", [])
    require(len(ids) == 137 and len(ids) == len(set(ids))
            and {"C22-01", "C22-02", "C22-03", "C22-04"}.issubset(ids), "Nonzero exact C22 assertion inventory required")
    require(inventory.get("native_runs") == 4 and inventory.get("native_denial_code") == 5
            and inventory.get("native_questions") == [[2, 5], [8, 9]], "Native fixture inventory differs")
    return ids


def validate_evidence(out: Path, events: list[dict], inventory: dict) -> dict:
    ids = validate_inventory(inventory)
    endings = [e for e in events if not e.get("Test") and e.get("Action") in ("pass", "fail")]
    require(len(endings) == 1 and endings[0]["Action"] == "pass", "Go package did not pass")
    require([e.get("Test") for e in events if e.get("Test") and e.get("Action") == "pass"] == [TEST]
            and not any(e.get("Action") == "fail" for e in events), "Wrong or absent executed test")
    # test2json splits long output strings across events; reassemble before parsing.
    lines = "".join(e.get("Output", "") for e in events).splitlines()
    assertions = [json.loads(line[len("C22_ASSERTION "):]) for line in lines if line.startswith("C22_ASSERTION ")]
    require(len(assertions) == len(ids) and {a.get("assertion_id") for a in assertions} == set(ids), "Assertion coverage differs")
    require(all(a.get("status") == "PASS" and a.get("actual") == a.get("expected") for a in assertions), "An assertion failed")
    records = [json.loads(line) for line in (out / "audit.jsonl").read_text(encoding="utf-8").splitlines() if line]
    http = [r for r in records if r.get("record_type") == "http"]
    require(len(http) >= inventory["minimum_http_count"] and [r["request_id"] for r in http] == list(range(1, len(http) + 1)), "HTTP transcript absent or discontinuous")
    require(all(r.get("transport") == "HOST_ISSUED_REAL_LOOPBACK_HTTP" and r.get("raw_request") and r.get("raw_response")
                and r.get("started_at") and r.get("finished_at") and r.get("credential") == "REDACTED"
                and "Authorization: Bearer [REDACTED]" in r["raw_request"] for r in http), "Incomplete/redaction-invalid HTTP evidence")
    candidate = [r for r in http if r.get("audience") == "CANDIDATE"]
    require(candidate and not any(MARKER in r["raw_response"] for r in candidate), "Candidate HTTP marker leak")
    controls = read(out / "host-positive-controls.json")
    forbidden = set()
    for artifact in controls["artifact_refs"].values():
        require(artifact["access_class"] == "VERIFIER_ONLY", "Private artifact classification lost")
        forbidden.update(str(artifact[k]) for k in ("id", "content_hash", "storage_key"))
    results = [r for r in records if r.get("record_type") == "private_result"]
    require(len(results) == 4 and {r["name"] for r in results} == {f"{p}-case-{i}" for p in PHASES for i in (1, 2)}, "Raw results absent")
    for result in results:
        forbidden.update((result["artifact_ref"]["id"], result["content_sha256"]))
        require(len(result["lineage"]) == 2, "Raw result lost input/label provenance")
    require(not any(secret in r["raw_response"] for secret in forbidden for r in candidate), "Private metadata escaped into candidate response")
    authorized = [r for r in http if r.get("audience") == "AUTHORIZED_CONTROL" and r["status"] == 200 and r["path"].endswith("/content")]
    require(sum(MARKER in r["response_body"] for r in authorized) >= 29, "Authorized full-evidence positive controls missing")
    require(all("Cache-Control: no-store" in r["raw_response"] for r in authorized), "Authorized content cache boundary differs")
    matrix = []
    for phase in PHASES:
        for role in inventory["http_roles"]:
            rows = [r for r in candidate if r["phase"] == phase and r["role"] == role]
            require(rows and not any(r["status"] == 401 for r in rows), "Invalid credential cannot demonstrate ordinary isolation")
            for suffix in ("/artifacts", "/events", "/context-bundles", "/qualifications"):
                require(any(r["path"].endswith(suffix) and r["status"] == 200 for r in rows), "List/event surface missing")
            for artifact in controls["artifact_refs"].values():
                for suffix in ("", "/content"):
                    require(any(r["path"].endswith("/artifacts/" + artifact["id"] + suffix) and r["status"] == 404 for r in rows), "Known private object denial missing")
            for suffix in ("/preview", "/export", "/backups", "/backup", "/logs"):
                require(any(r["path"].endswith(suffix) and r["status"] == 404 for r in rows), "Guessed unavailable route probe missing")
            if role in ("executor", "planner"):
                require(any(r["path"].endswith("/search") and 400 <= r["status"] < 500 for r in rows), "Search negative missing")
                require(any(r["path"].endswith("/context-bundles") and r["method"] == "POST" and 400 <= r["status"] < 500 for r in rows), "Context construction negative missing")
                require(any(r["path"].endswith("/result") and r["method"] == "POST" and r["status"] in (403, 404) for r in rows), "Candidate self-score negative missing")
            matrix.extend({k: r[k] for k in ("request_id", "phase", "role", "method", "path", "status")} for r in rows)
    native = []
    sids, pids, binaries = set(), set(), set()
    for phase in PHASES:
        for i, operands in enumerate(inventory["native_questions"], 1):
            name = f"{phase}-case-{i}"
            receipt = read(out / (name + "-native-receipt.json"))
            received = read(out / (name + "-native-output.json"))
            sent = read(out / (name + "-native-input.json"))
            require(receipt["exit_code"] == 0 and receipt["children_stopped"] and not receipt["timed_out"]
                    and receipt["capabilities"] == [] and receipt["appcontainer_sid"] and receipt["pid"] == received["pid"], "Native process evidence not bounded")
            require(json.loads(base64.b64decode(receipt["stdout"])) == received and not base64.b64decode(receipt["stderr"] or ""), "Native raw stdout diverges")
            require(received["input_files"] == ["candidate.exe", "question.json"] and sent["input_files"] == received["input_files"], "Unexpected candidate staged file")
            request = json.loads(received["input_raw"])
            require(request == sent["question_request"] and set(request) == {"question", "private_directory", "probes"}
                    and request["question"] == {"operands": operands} and received["question"] == request["question"], "Candidate did not receive one exact necessary question")
            require(sent["stdin"] == "NONE" and sent["previous_feedback"] == "NONE" and MARKER not in json.dumps(received), "Private data/feedback entered candidate")
            require(received["result"] == sum(operands) and received["list_code"] == 5 and received["listed_entries"] == 0, "Native computation/list denial differs")
            expected_probes = set(inventory["private_blob_names"]) | {"authority-db"}
            if phase == "after-restart":
                expected_probes |= {"result-before-restart-case-1", "result-before-restart-case-2"}
            require({r["name"] for r in received["probes"]} == expected_probes and len(received["probes"]) == len(expected_probes), "Native private target inventory differs")
            require(all(r["read_code"] == 5 and r["read_bytes"] == 0 and r["read_body"] == ""
                        and r["write_code"] == 5 and r["written_bytes"] == 0 for r in received["probes"]), "Actual OS read/write access was not denied")
            sids.add(receipt["appcontainer_sid"]); pids.add(receipt["pid"]); binaries.add(sent["binary_sha256"])
            native.append({"name": name, "sid": receipt["appcontainer_sid"], "pid": receipt["pid"], "probes": len(received["probes"]), "binary_sha256": sent["binary_sha256"]})
    require(len(sids) == 4 and len(pids) == 4 and len(binaries) == 1, "Native identity reuse or binary drift")
    started = [read(out / (phase + "-control-ready.json")) for phase in (*PHASES, "missing-provider")]
    require(len({s["pid"] for s in started}) == 3 and all(s["database"] == controls["database"] and s["private"] == controls["private_store"] for s in started), "Restart used a different store or same process")
    require([s["provider"] for s in started] == [True, True, False], "Missing-provider process not exercised")
    for phase in (*PHASES, "missing-provider"):
        exited = read(out / (phase + "-control-exit.json"))
        require(exited["exit_code"] == 0 and exited["error"] == "<nil>", "Control-plane process did not shut down cleanly")
        require(MARKER not in (out / (phase + "-service.log")).read_text(encoding="utf-8"), "Actual HTTP service log leaked marker")
    revoked = [r for r in http if r["role"] == "revoked-verifier"]
    require([r["status"] for r in revoked] == [200, 401], "Revocation lacks a prior positive or restart denial")
    require(any(r["phase"] == "missing-provider" and r["path"].endswith("/content") and r["status"] == 503 for r in http), "Unavailable provider did not fail closed")
    public = read(out / "public-report.json")
    require(set(public) == {"schema", "status", "total", "correct", "false_accept", "false_reject", "abstain", "critical_false_accept", "maximum_mode"}
            and public["schema"] == "researchos.protected-summary.v1" and public["status"] == "EXECUTION_REPORTED"
            and public["maximum_mode"] == "ADVISORY" and public["total"] == public["correct"] == 2, "Unsafe or uncomputed public summary")
    summaries = [r for r in records if r.get("record_type") == "public_summary"]
    require(len(summaries) == 1 and summaries[0]["summary"] == public, "Public summary publication differs")
    public_id = summaries[0]["artifact_ref"]["id"]
    public_reads = [r for r in candidate if r["path"].endswith("/artifacts/" + public_id + "/content")]
    require(len(public_reads) == 4 and all(r["status"] == 200 and json.loads(r["response_body"]) == public for r in public_reads), "Candidate safe summary positive reads missing")
    db = read(out / "sqlite-readback.json")
    require(all(db[k] == 0 for k in ("cache_marker_rows", "uploaded_marker_rows", "domain_marker_rows", "event_marker_rows")), "Marker entered database/cache/events")
    scan = read(out / "scan-summary.json")
    require(scan["http_count"] == len(http) and scan["candidate_responses"] == len(candidate) and scan["marker_leaks"] == 0
            and scan["native_runs"] == 4 and scan["qualification_maximum_mode"] == "ADVISORY" and scan["formal_live"] is False, "Scan evidence inconsistent")
    return {"assertions": assertions, "http_count": len(http), "permission_matrix": matrix, "native_matrix": native,
            "scan": {"candidate_http_responses": len(candidate), "authorized_body_controls": len(authorized), "native_processes": 4,
                     "private_marker_matches": 0, "private_metadata_matches": 0, "control_plane_processes": 3}}


def main() -> int:
    output = {"status": "FAIL", "assertions": 0, "assertion_ids": [], "receipt": None}
    out = report = None
    started = time.monotonic()
    try:
        require(len(sys.argv) == 1, "No arguments; use the registered W17/C22 or W17-G03 selector")
        case, check = os.environ.get("RESEARCHOS_CASE_ID", ""), os.environ.get("RESEARCHOS_CHECK_ID", "")
        require(os.environ.get("RESEARCHOS_TASK_ID") == "W17" and ((case == "C22" and not check) or (check == "W17-G03" and not case)),
                "Only TASK=W17 with CASE=C22 or CHECK=W17-G03 is bound, not both")
        require(os.environ.get("RESEARCHOS_MEASUREMENT_MODE", "FIXTURE") == "FIXTURE"
                and os.environ.get("RESEARCHOS_MODE", "FIXTURE") == "FIXTURE", "Only FIXTURE is authorized")
        inventory = read(EXPECTED); ids = validate_inventory(inventory)
        locked = read(ROOT / "execution/toolchains/locked.json")["tools"]["go"]
        go = Path(os.environ.get("RESEARCHOS_GO", locked["path"]))
        require(go.is_file() and digest(go) == "sha256:" + locked["sha256"], "Locked Go executable hash differs")
        run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        out = ROOT / "execution/receipts/W17/c22" / run; out.mkdir(parents=True)
        output["receipt"] = str(out / "report.json")
        tracked = subprocess.check_output(["git", "ls-files", "internal/domain", "internal/store", "adapters", "evaluation", "ops/experiment_sandbox", "ops/protected_fixture", "migrations/sqlite", "spec/v2.0/contracts", "go.mod", "go.sum"], cwd=ROOT, text=True).splitlines()
        paths = {ROOT / path for path in tracked} | {EXPECTED, Path(__file__), ROOT / "internal/domain/protected_c22_test.go", ROOT / "ops/protected_fixture/main_windows.go"}
        hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        save(out / "source-manifest.json", {"source_commit": head, "files": hashes, "go": {"path": str(go), "sha256": digest(go)}})
        report = {"status": "FAIL", "task_id": "W17", "case_id": case or None, "check_id": check or None, "covered_case": "C22", "mode": "FIXTURE", "source_commit": head,
                  "execution_status": "EXECUTION_REPORTED", "independent_acceptance": "PENDING", "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "platform": platform.platform(), "cwd": str(ROOT), "assertions": [], "project_identity": read(ROOT / "execution/project_identity.json"),
                  "real_provider_called": False, "formal_holdout_accessed": False, "actual_product_database_accessed": False,
                  "protected_service_accessed": False, "LIVE_qualified": False, "BOUNDED_AUTO_granted": False,
                  "limitations": ["Only synthetic exact-marker data and temporary fixture DB/store; no protected service, main DB, provider or real model.",
                                  "Host-issued loopback HTTP under scoped fixture credentials and AppContainer OS calls are separate evidence layers. Zero-network candidate does not send HTTP.",
                                  "Each child receives one arithmetic question plus metadata-only known paths for negative access probes; no labels, full batch or prior feedback.",
                                  "Fixture host computes strict SafeSummary and stores private per-case results; this does not add or attest production frozen-engine/declassification authority.",
                                  "Preview/export content is protected by the existing content route. Dedicated preview/export/log/backup routes are absent and probed as 404; actual local backup engine independently refuses protected bytes.",
                                  "CanaryStore denies LIVE and declares same-user access; only the fresh constrained AppContainer candidate is OS-isolated. All qualifications remain ADVISORY.",
                                  "Go cleanup removes generated DB/store/process configuration/staging. Raw native receipts, HTTP transcripts, hashes, counts and process proofs remain."]}
        command = [str(go), "test", "./internal/domain", "-run", "^" + TEST + "$", "-count=1", "-timeout=120s", "-json"]
        report["command"] = command
        env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", RESEARCHOS_GO=str(go), RESEARCHOS_C22_EVIDENCE=str(out))
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="strict", timeout=180)
        (out / "go.stdout.jsonl").write_text(result.stdout, encoding="utf-8"); (out / "go.stderr.log").write_text(result.stderr, encoding="utf-8")
        report["exit_code"] = result.returncode
        require(result.returncode == 0, "Go fixture failed; see raw stdout/stderr")
        events = [json.loads(line) for line in result.stdout.splitlines() if line]
        checked = validate_evidence(out, events, inventory)
        require(hashes == {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}, "Source changed during execution")
        save(out / "permission-matrix.json", checked.pop("permission_matrix")); save(out / "native-matrix.json", checked.pop("native_matrix")); save(out / "marker-scan.json", checked["scan"])
        report.update(checked); report["status"] = output["status"] = "PASS"
        output["assertions"] = len(ids); output["assertion_ids"] = ids
    except Exception as error:
        output["error"] = str(error)
        if report is not None: report["error"] = traceback.format_exc()
    finally:
        if out is not None and report is not None:
            report["elapsed_seconds"] = round(time.monotonic() - started, 3); report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            report["evidence_hashes"] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}
            save(out / "report.json", report)
            save(out / "evidence-index.json", {"source_commit": report["source_commit"], "files": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()}})
        print(json.dumps(output, ensure_ascii=False))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
