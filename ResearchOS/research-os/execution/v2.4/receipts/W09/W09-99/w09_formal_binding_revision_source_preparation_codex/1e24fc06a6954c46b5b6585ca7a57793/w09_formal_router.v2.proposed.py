"""W09 formal binding candidate. Source only; not registered or executable authority.

The existing retrieval runner supplies native test facts. A separate exporter,
scope decision, Root command receipt and independent Verifier must close the
formal evidence before any frozen acceptance ID can pass.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

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
    ("test.retrieval", "W09", "", "A06"): "LIVE_WINDOWS_LOCAL",
    ("test.security", "W09", "", "A06"): "LIVE_WINDOWS_LOCAL",
}
SELECTED = {
    ("test.retrieval", "W09", "W09-G01", ""): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation", "TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape"),
    ("test.retrieval", "W09", "W09-G02", ""): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
    ("test.research.fixture", "W09", "", "C19"): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation"),
    ("test.retrieval", "W09", "", "C19"): ("TestW09C19ExplicitOriginAndUnknown", "TestW09C19ChainInvalidation"),
    ("test.retrieval", "W09", "", "A06"): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
    ("test.security", "W09", "", "A06"): ("TestW09A06HTTPInvalidationAndContext", "TestW09A06FTSFallbackAndDuplicatePath", "TestW09RootReadRejectsEscape", "TestW09UnicodeLocator", "TestW09RootIdentityRejectsReplacement", "TestW09RootReplacementCannotFeedProduct", "TestW09TaskInputCannotRematerializeStaleLocalBody", "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"),
}


def _failure(reason, native=None):
    print(json.dumps({"status": "NOT_RUN", "assertions": 0, "assertion_ids": [],
                      "formal_acceptance": "OPEN", "reason": reason,
                      "native_test_status": native}, ensure_ascii=False))
    return 2


def _inside_repo(relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("BAD_RELATIVE_REF")
    path = (ROOT / relative).resolve(strict=True)
    if path != ROOT and ROOT not in path.parents:
        raise ValueError("FOREIGN_REF")
    return path


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
    for key in ("status", "task_id", "check_id", "case_id", "scope", "exit_code",
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
    return pins


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"test.retrieval", "test.research.fixture", "test.security"}:
        return _failure("INVALID_COMMAND_KEY")
    route = (sys.argv[1], os.getenv("RESEARCHOS_TASK_ID", ""),
             os.getenv("RESEARCHOS_CHECK_ID", ""), os.getenv("RESEARCHOS_CASE_ID", ""))
    if route not in NATIVE and route not in PRESERVED:
        return _failure("UNBOUND_SELECTOR_TUPLE")
    if not (ROOT / "execution/toolchains/locked.json").is_file():
        return _failure("WRONG_REPOSITORY_CWD")
    go = os.getenv("RESEARCHOS_GO", "")
    if route[1] == "W09" and route[2] == "W09-01":
        argv = [sys.executable, "-X", "utf8", str(ROOT / "tests/evidence/check/main.py")]
    elif route[1] == "W08":
        if not go:
            return _failure("MISSING_LOCKED_GO")
        argv = [go, "run", "./tests/research/check"]
    elif route[1] == "W17":
        if not go:
            return _failure("MISSING_LOCKED_GO")
        argv = [go, "run", "./tests/security/check"]
    else:
        argv = [sys.executable, "-X", "utf8", str(ROOT / "ops/ci/retrieval.py")]
    child = subprocess.run(argv, cwd=ROOT, env=os.environ.copy(),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, shell=False)
    sys.stderr.buffer.write(child.stderr)
    if route in PRESERVED or child.returncode != 0:
        sys.stdout.buffer.write(child.stdout)
        return child.returncode
    try:
        source = json.loads(child.stdout.decode("utf-8").strip().splitlines()[-1])
        pins = _native_exact(source, route)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        sys.stdout.buffer.write(child.stdout)
        return _failure("SOURCE_REPORT_NOT_EXACT_OR_INCOMPLETE", type(exc).__name__)
    # The existing runner does not export the input/HTTP/SQL evidence closure.
    # Consequently this candidate cannot turn a native PASS into a formal PASS.
    # The next source slice must produce and independently verify the closure.
    return _failure("W09_OWNED_EXPORT_AND_MODE_DECISION_NOT_IMPLEMENTED", {
        "status": "PASS", "assertion_ids": list(NATIVE[route]),
        "formal_projection_pending": list(FORMAL[route]), "source_pins": pins,
    })


if __name__ == "__main__":
    sys.exit(main())
