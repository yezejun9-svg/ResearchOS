"""W09 formal binding candidate. Source only; not registered or executable authority.

The existing retrieval runner supplies native test facts. A separate exporter,
scope decision, Root command receipt and independent Verifier must close the
formal evidence before any frozen acceptance ID can pass.
"""

import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
from w09_evidence_closure import verify_native, verify_owned, verify_c19, verify_a06, verify_mode, safe_repo_rel

ROOT = Path.cwd().resolve()
NATIVE = {
    ("test.retrieval", "W09", "W09-G01", ""): ("C19-01", "C19-02", "C19-03", "C19-04", "C19-05", "A06-01", "A06-02", "A06-03"),
    ("test.retrieval", "W09", "W09-G02", ""): ("A06-01", "A06-02", "A06-03", "W09-G02-UNICODE-LOCATOR", "W09-G02-ROOT-REPLACEMENT", "W09-G02-STALE-INPUT-BODY", "W09-G02-LEGACY-ROOT"),
    ("test.research.fixture", "W09", "", "C19"): ("C19-01", "C19-02", "C19-03", "C19-04", "C19-05"),
    ("test.retrieval", "W09", "", "C19"): ("C19-01", "C19-02", "C19-03", "C19-04", "C19-05"),
    ("test.retrieval", "W09", "", "A06"): ("A06-01", "A06-02", "A06-03", "W09-G02-UNICODE-LOCATOR", "W09-G02-ROOT-REPLACEMENT", "W09-G02-STALE-INPUT-BODY", "W09-G02-LEGACY-ROOT"),
    ("test.security", "W09", "", "A06"): ("A06-01", "A06-02", "A06-03", "W09-G02-UNICODE-LOCATOR", "W09-G02-ROOT-REPLACEMENT", "W09-G02-STALE-INPUT-BODY", "W09-G02-LEGACY-ROOT"),
}
FORMAL = {
    ("test.retrieval", "W09", "W09-G01", ""): ("W09-G01",),
    ("test.retrieval", "W09", "W09-G02", ""): ("W09-G02",),
    ("test.research.fixture", "W09", "", "C19"): ("C19-01", "C19-02", "C19-03"),
    ("test.retrieval", "W09", "", "C19"): ("C19-01", "C19-02", "C19-03"),
    ("test.retrieval", "W09", "", "A06"): ("A06-01", "A06-02", "A06-03"),
    ("test.security", "W09", "", "A06"): ("A06-01", "A06-02", "A06-03"),
}
PRESERVED = {
    ("test.retrieval", "W09", "W09-01", ""),
    ("test.research.fixture", "W08", "W08-01", ""),
    ("test.research.fixture", "W08", "W08-02", ""),
    ("test.security", "W17", "W17-01", ""),
}
SOURCE_SCOPE = {
    ("test.retrieval", "W09", "W09-G01", ""): "FIXTURE_IMPLEMENTED_SERVICE",
    ("test.retrieval", "W09", "W09-G02", ""): "LIVE_WINDOWS_LOCAL",
    ("test.research.fixture", "W09", "", "C19"): "FIXTURE_IMPLEMENTED_SERVICE",
    ("test.retrieval", "W09", "", "C19"): "FIXTURE_IMPLEMENTED_SERVICE",
    ("test.retrieval", "W09", "", "A06"): "FIXTURE_IMPLEMENTED_SERVICE",
    ("test.security", "W09", "", "A06"): "FIXTURE_IMPLEMENTED_SERVICE",
}
SELECTED = {
    ("test.retrieval", "W09", "W09-G01", ""): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation", "TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape"),
    ("test.retrieval", "W09", "W09-G02", ""): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
    ("test.research.fixture", "W09", "", "C19"): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation"),
    ("test.retrieval", "W09", "", "C19"): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation"),
    ("test.retrieval", "W09", "", "A06"): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
    ("test.security", "W09", "", "A06"): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
}


ASSERTION_OWNER = {
    **{item: "TestW09C19ExplicitOriginAndUnknown" for item in ("C19-01", "C19-02", "C19-03", "C19-04")},
    "C19-05": "TestW09C19ChainInvalidation",
    "A06-01": "TestW09A06HTTPInvalidationAndContext",
    "A06-02": "TestW09A06HTTPInvalidationAndContext",
    "A06-03": "TestW09A06FTSFallbackAndDuplicatePath",
    "W09-G02-UNICODE-LOCATOR": "TestW09UnicodeLocator",
    "W09-G02-ROOT-REPLACEMENT": "TestW09RootReplacementCannotFeedProduct",
    "W09-G02-STALE-INPUT-BODY": "TestW09TaskInputCannotRematerializeStaleLocalBody",
    "W09-G02-LEGACY-ROOT": "TestW09LegacyRootMigrationRevokesUnidentifiedRoot",
}


def _failure(reason, native=None):
    print(json.dumps({"status": "NOT_RUN", "assertions": 0, "assertion_ids": [],
                      "formal_acceptance": "OPEN", "reason": reason,
                      "native_test_status": native}, ensure_ascii=False))
    return 2


def _inside_repo(relative):
    return safe_repo_rel(ROOT, relative)


def _pin(relative):
    path = _inside_repo(relative)
    data = path.read_bytes()
    return {"path": relative.replace("\\", "/"),
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _native_exact(source, route):
    expected = NATIVE[route]
    observed = source["assertion_ids"]
    produced = source["expected_assertion_ids"]
    selected = source["selected_tests"]
    passed = source["passed_tests"]
    if (source.get("status") != "PASS" or source.get("task_id") != "W09"
            or source.get("check_id") != (route[2] or None)
            or source.get("case_id") != (route[3] or None)
            or source.get("scope") != SOURCE_SCOPE[route]
            or source.get("exit_code") != 0 or source.get("timed_out") is not False
            or not isinstance(observed, list) or not isinstance(produced, list)
            or len(observed) != len(set(observed))
            or sorted(observed) != sorted(expected)
            or sorted(produced) != sorted(expected)
            or source.get("assertions") != len(expected)
            or not isinstance(selected, list) or not selected
            or len(selected) != len(set(selected))
            or sorted(selected) != sorted(SELECTED[route])
            or sorted(passed) != sorted(selected)
            or not isinstance(source.get("actual_invocation"), list)
            or not isinstance(source.get("raw_evidence_references"), list)
            or len(source["raw_evidence_references"]) != 2
            or not source.get("report_reference")):
        raise ValueError("NATIVE_ROSTER_OR_SCOPE_MISMATCH")
    pins = [_pin(ref) for ref in [*source["raw_evidence_references"], source["report_reference"]]]
    report = json.loads(_inside_repo(source["report_reference"]).read_bytes())
    for key in ("status", "task_id", "check_id", "case_id", "scope", "exit_code", "run_id", "go_executable",
                "timed_out", "assertions", "assertion_ids", "expected_assertion_ids",
                "selected_tests", "passed_tests", "raw_evidence_references"):
        if report.get(key) != source.get(key):
            raise ValueError("SOURCE_REPORT_DISAGREES_WITH_RAW")
    records = report.get("assertion_results")
    if (not isinstance(records, list) or len(records) != len(expected)
            or sorted(record.get("assertion_id") for record in records) != sorted(expected)
            or any(record.get("status") != "PASS" or
                   record.get("raw_evidence_reference") != source["raw_evidence_references"][0]
                   for record in records)):
        raise ValueError("SOURCE_ASSERTION_RESULTS_INCOMPLETE")
    native = verify_native(ROOT, source, report, expected, selected)
    return pins, report, native


def _owned_exact(source, report, route):
    export = report.get("owned_export")
    if not isinstance(export, dict) or export.get("complete") is not True:
        raise ValueError("OWNED_EXPORT_NOT_COMPLETE")
    members = export.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("OWNED_EXPORT_MEMBERS_MISSING")
    report_path = _inside_repo(source["report_reference"])
    owned_root = (report_path.parent / "owned").resolve(strict=True)
    if not owned_root.is_dir() or owned_root.is_symlink():
        raise ValueError("OWNED_EXPORT_ROOT_BAD")
    member_map = {}
    for claimed in members:
        if not isinstance(claimed, dict):
            raise ValueError("OWNED_MEMBER_MALFORMED")
        path = _inside_repo(claimed["path"])
        if owned_root not in path.parents or path in member_map or path.is_symlink():
            raise ValueError("OWNED_MEMBER_FOREIGN_OR_DUPLICATE")
        actual = _pin(claimed["path"])
        if actual != claimed:
            raise ValueError("OWNED_MEMBER_PIN_DRIFT")
        member_map[path] = claimed
    actual_paths = {path.resolve(strict=True) for path in owned_root.rglob("*.raw")}
    if actual_paths != set(member_map):
        raise ValueError("OWNED_MEMBER_SET_MISMATCH")
    events = {}
    for path in member_map:
        label = path.name.split("-", 1)[-1].removesuffix(".raw")
        if label.startswith(("http-request", "http-response", "file-body-", "g02-junction-stdout")) or __import__("re").fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label):
            continue
        if label.startswith(("assertion-", "c19-", "chain-", "a06-", "g02-", "http-", "origins-", "state-", "file-")):
            try:
                events.setdefault(label, []).append(json.loads(path.read_bytes()))
            except (UnicodeDecodeError, ValueError):
                if not label.startswith(("http-request", "http-response", "file-body")):
                    raise ValueError("OWNED_EVENT_NOT_JSON")
    for exchange in events.get("http-exchange", []):
        if (exchange.get("delivery") != "IN_PROCESS_HTTptest_RECORDER"
                or exchange.get("authorization_header_exported") is not False
                or not isinstance(exchange.get("status"), int)
                or not exchange.get("method") or not exchange.get("path")):
            raise ValueError("HTTP_EXCHANGE_MALFORMED")
        for field in ("request", "response"):
            claim = exchange.get(field)
            if not isinstance(claim, dict):
                raise ValueError("HTTP_BODY_PIN_MISSING")
            path = Path(claim["path"]).resolve(strict=True)
            if path not in member_map or claim["sha256"] != member_map[path]["sha256"] or claim["bytes"] != member_map[path]["bytes"]:
                raise ValueError("HTTP_BODY_PIN_DRIFT")
    for label, group in events.items():
        if label.startswith("file-"):
            for entry in group:
                if not isinstance(entry, dict) or "exists" not in entry:
                    raise ValueError("FILE_OBSERVATION_MALFORMED")
                if entry["exists"] is True and entry.get("type") == "regular":
                    claim = entry.get("body")
                    if not isinstance(claim, dict):
                        raise ValueError("FILE_BODY_PIN_MISSING")
                    path = Path(claim["path"]).resolve(strict=True)
                    if path not in member_map or claim["sha256"] != member_map[path]["sha256"] or claim["bytes"] != member_map[path]["bytes"]:
                        raise ValueError("FILE_BODY_PIN_DRIFT")
    records = report["assertion_results"]
    for record in records:
        name = "assertion-" + record["assertion_id"]
        if len(events.get(name, [])) != 1:
            raise ValueError("ASSERTION_RAW_CARDINALITY")
        raw = events[name][0]
        if (raw.get("assertion_id") != record["assertion_id"]
                or raw.get("status") != "PASS"
                or raw.get("actual") != record.get("evidence")
                or not isinstance(raw.get("expected"), dict)
                or not raw["expected"]):
            raise ValueError("ASSERTION_EXPECTED_ACTUAL_MISMATCH")
        if any(raw["actual"].get(key) != value for key, value in raw["expected"].items()):
            raise ValueError("ASSERTION_EXPECTED_VALUE_MISMATCH")
        claimed = record.get("owned_export_ref")
        if not isinstance(claimed, dict):
            raise ValueError("ASSERTION_RAW_REF_MISSING")
        path = Path(claimed["path"]).resolve(strict=True)
        if path not in member_map or claimed["sha256"] != member_map[path]["sha256"] or claimed["bytes"] != member_map[path]["bytes"]:
            raise ValueError("ASSERTION_RAW_REF_DRIFT")
        if path.parent.name != ASSERTION_OWNER[record["assertion_id"]]:
            raise ValueError("ASSERTION_RAW_TEST_OWNER_MISMATCH")
    if route[3] == "C19" or route[2] == "W09-G01":
        for label in ("c19-complete-graph-before", "c19-complete-graph-after", "chain-before-after", "origins-c19-before", "origins-c19-after"):
            if len(events.get(label, [])) != 1:
                raise ValueError("C19_GRAPH_EXPORT_MISSING")
        before = events["c19-complete-graph-before"][0]
        after = events["c19-complete-graph-after"][0]
        if (len(before.get("records", [])) != 27 or len(after.get("records", [])) != 27
                or before.get("counts", {}).get("independent_observed_count") != 2
                or before.get("counts", {}).get("simulated_count") != 20
                or before.get("counts", {}).get("unknown_count") != 1
                or after.get("counts", {}).get("independent_observed_count") != 1
                or after.get("counts", {}).get("unknown_count") != 6):
            raise ValueError("C19_GRAPH_COUNTS_MISMATCH")
        records = before["records"]
        if (len({row.get("evidence_id") for row in records}) != 27
                or sum(row.get("evidence_kind") == "SIMULATED" for row in records) != 20
                or sum(row.get("evidence_kind") == "OBSERVED" and row.get("origin_relation") == "UNKNOWN" for row in records) != 1
                or len(events["origins-c19-before"][0].get("rows", [])) != 6):
            raise ValueError("C19_GRAPH_RELATIONS_MISMATCH")
        if len([label for label in events if label.startswith("file-c19-before-")]) != 7:
            raise ValueError("C19_INPUT_SNAPSHOTS_MISSING")
        if len([path for path in member_map if __import__("re").fullmatch(
                r"[0-9]{8}-simulated-opinion-(?:0[0-9]|1[0-9])\.raw", path.name)]) != 20:
            raise ValueError("C19_SIMULATED_INPUTS_MISSING")
        rejection = events.get("c19-unsupported-relation-rejection", [])
        if len(rejection) != 1 or not rejection[0].get("actual_error"):
            raise ValueError("C19_UNSUPPORTED_RELATION_RESULT_MISSING")
    if route[3] == "A06" or route[2] in ("W09-G01", "W09-G02"):
        for label in ("a06-indexed-result", "a06-fallback-result", "state-a06-fts-indexed", "state-a06-fts-fallback"):
            if len(events.get(label, [])) != 1:
                raise ValueError("A06_FTS_EXPORT_MISSING")
        if len(events.get("http-exchange", [])) < 1:
            raise ValueError("A06_HTTP_EXCHANGE_MISSING")
        for label in ("file-a06-initial-authorized", "file-a06-initial-denied", "file-a06-modified", "file-a06-moved-source-absent", "file-a06-moved-destination", "file-a06-deleted", "file-a06-revoked-body"):
            if len(events.get(label, [])) != 1:
                raise ValueError("A06_FILE_TRANSITION_MISSING")
        escapes = events.get("a06-escape-rejection", [])
        if len(escapes) != 2 or any(not row.get("actual_error") or row.get("accepted") is not False for row in escapes):
            raise ValueError("A06_ESCAPE_RESULT_MISSING")
        initial = events["file-a06-initial-authorized"][0]
        initial_state = events.get("state-a06-before-capture", [])
        if (len(initial_state) != 1 or not initial.get("exists")
                or Path(initial["path"]).parent != Path(initial_state[0].get("root_path", ""))
                or initial_state[0].get("root_id") != initial.get("root_id")):
            raise ValueError("A06_ROOT_INPUT_NOT_BOUND")
        indexed = events["a06-indexed-result"][0]["result"]["hits"]
        fallback = events["a06-fallback-result"][0]["result"]["hits"]
        if (len(indexed) != 2 or len(fallback) != 2
                or any(hit.get("backend") != "sqlite-fts5" for hit in indexed)
                or any(hit.get("backend") != "bounded-scan" for hit in fallback)):
            raise ValueError("A06_FTS_OBSERVATION_MISMATCH")
    closed = verify_owned(ROOT, source, report, SELECTED[route], ASSERTION_OWNER)
    if route[3] == "C19" or route[2] == "W09-G01":
        verify_c19(closed)
    if route[3] == "A06" or route[2] in ("W09-G01", "W09-G02"):
        verify_a06(closed)
    return closed


def _mode_review(source, report, route, owned, native):
    return verify_mode(ROOT, source, report, route, owned, native,
                       os.getenv("RESEARCHOS_W09_MODE_DECISION_REF", ""),
                       os.getenv("RESEARCHOS_W09_MODE_DECISION_SHA256", ""))


def _pinned_native_report():
    relative = os.getenv("RESEARCHOS_W09_NATIVE_REPORT_REF", "")
    expected = os.getenv("RESEARCHOS_W09_NATIVE_REPORT_SHA256", "")
    if not relative or len(expected) != 64:
        raise ValueError("SEALED_NATIVE_REPORT_NOT_GIVEN")
    path = _inside_repo(relative)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SEALED_NATIVE_REPORT_DRIFT")
    report = json.loads(raw)
    if report.get("formal_construction_acceptance") != "NOT_RUN_POSTRUN_REVIEW_PENDING":
        raise ValueError("NATIVE_PRODUCER_PRETENDS_FORMAL")
    tool_ref = os.getenv("RESEARCHOS_W09_TOOL_RUN_REF", "")
    tool_sha = os.getenv("RESEARCHOS_W09_TOOL_RUN_SHA256", "")
    tool_path = _inside_repo(tool_ref)
    tool_raw = tool_path.read_bytes()
    if hashlib.sha256(tool_raw).hexdigest() != tool_sha:
        raise ValueError("NATIVE_TOOL_RUN_PIN_DRIFT")
    tool = json.loads(tool_raw)
    if (tool.get("schema") != "researchos.w09-native-producer-tool-run.v1"
            or tool.get("report_ref") != relative or tool.get("report_sha256") != expected
            or tool.get("run_id") != report.get("run_id")
            or tool.get("actual_invocation") != report.get("actual_invocation")
            or tool.get("native_exit_code") != report.get("exit_code")
            or tool.get("stdout_ref") != report.get("raw_evidence_references", [None])[0]
            or tool.get("stderr_ref") != report.get("raw_evidence_references", [None, None])[1]
            or tool.get("stdout_sha256") != _pin(tool["stdout_ref"])["sha256"]
            or tool.get("stderr_sha256") != _pin(tool["stderr_ref"])["sha256"]):
        raise ValueError("NATIVE_TOOL_RUN_NOT_SAME_RUN")
    source = dict(report)
    source["report_reference"] = relative
    return source, report, tool


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"test.retrieval", "test.research.fixture", "test.security"}:
        return _failure("INVALID_COMMAND_KEY")
    route = (sys.argv[1], os.getenv("RESEARCHOS_TASK_ID", ""),
             os.getenv("RESEARCHOS_CHECK_ID", ""), os.getenv("RESEARCHOS_CASE_ID", ""))
    if route not in NATIVE and route not in PRESERVED:
        return _failure("UNBOUND_SELECTOR_TUPLE")
    if not (ROOT / "execution/toolchains/locked.json").is_file():
        return _failure("WRONG_REPOSITORY_CWD")
    if route in PRESERVED:
        go = os.getenv("RESEARCHOS_GO", "")
        if route[1] == "W09":
            argv = [sys.executable, "-X", "utf8", str(ROOT / "tests/evidence/check/main.py")]
        elif route[1] == "W08":
            if not go: return _failure("MISSING_LOCKED_GO")
            argv = [go, "run", "./tests/research/check"]
        else:
            if not go: return _failure("MISSING_LOCKED_GO")
            argv = [go, "run", "./tests/security/check"]
        child = subprocess.run(argv, cwd=ROOT, env=os.environ.copy(),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False, shell=False)
        sys.stderr.buffer.write(child.stderr)
        sys.stdout.buffer.write(child.stdout)
        return child.returncode
    try:
        source, report, tool = _pinned_native_report()
        pins, report, native = _native_exact(source, route)
        owned = _owned_exact(source, report, route)
        mode = _mode_review(source, report, route, owned, native)
        if mode.get("formal_authority") is not False:
            raise ValueError("MODE_REVIEW_MUST_NOT_SELF_ACCEPT")
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        return _failure("SEALED_NATIVE_OR_POSTRUN_MODE_OPEN", type(exc).__name__)
    print(json.dumps({"status": "PASS", "assertion_ids": list(FORMAL[route]),
                      "assertions": len(FORMAL[route]), "task_id": "W09",
                      "check_id": route[2] or None, "case_id": route[3] or None,
                      "native_assertion_ids": list(NATIVE[route]),
                      "source_pins": pins, "owned_export_member_count": len(owned["members"]),
                      "native_tool_run_ref": os.getenv("RESEARCHOS_W09_TOOL_RUN_REF"),
                      "mode_evidence": mode,
                      "formal_acceptance": "PENDING_INDEPENDENT_VERIFIER"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
