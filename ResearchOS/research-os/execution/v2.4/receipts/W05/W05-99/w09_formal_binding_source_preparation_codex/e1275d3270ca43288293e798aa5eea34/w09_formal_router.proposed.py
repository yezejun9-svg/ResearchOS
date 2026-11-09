"""Proposed v2.4 selector router. Source preparation only; not an active command."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
EXPECTED = {
    ("test.retrieval", "W09", "W09-G01", ""): ["W09-G01"],
    ("test.retrieval", "W09", "W09-G02", ""): ["W09-G02"],
    ("test.retrieval", "W09", "", "C19"): ["C19-01", "C19-02", "C19-03"],
    ("test.retrieval", "W09", "", "A06"): ["A06-01", "A06-02", "A06-03"],
    ("test.research.fixture", "W09", "", "C19"): ["C19-01", "C19-02", "C19-03"],
    ("test.security", "W09", "", "A06"): ["A06-01", "A06-02", "A06-03"],
}
PRESERVED = {
    ("test.retrieval", "W09", "W09-01", ""),
    ("test.research.fixture", "W08", "W08-01", ""),
    ("test.research.fixture", "W08", "W08-02", ""),
    ("test.security", "W17", "W17-01", ""),
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"test.retrieval", "test.research.fixture", "test.security"}:
        raise SystemExit("INVALID_COMMAND_KEY")
    route = (sys.argv[1], os.getenv("RESEARCHOS_TASK_ID", ""),
             os.getenv("RESEARCHOS_CHECK_ID", ""), os.getenv("RESEARCHOS_CASE_ID", ""))
    if route not in EXPECTED and route not in PRESERVED:
        raise SystemExit("UNBOUND_SELECTOR_TUPLE")
    if not (ROOT / "execution/toolchains/locked.json").is_file():
        raise SystemExit("WRONG_REPOSITORY_CWD")
    go = os.getenv("RESEARCHOS_GO", "")
    if route[1] == "W09" and route[2] == "W09-01":
        argv = [sys.executable, "-X", "utf8", str(ROOT / "tests/evidence/check/main.py")]
    elif route[1] == "W08":
        if not go:
            raise SystemExit("MISSING_LOCKED_GO")
        argv = [go, "run", "./tests/research/check"]
    elif route[1] == "W17":
        if not go:
            raise SystemExit("MISSING_LOCKED_GO")
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
        observed = source["assertion_ids"]
        expected = EXPECTED[route]
        if (source.get("status") != "PASS" or source.get("task_id") != "W09"
                or source.get("check_id") != (route[2] or None)
                or source.get("case_id") != (route[3] or None)
                or source.get("assertions") != len(observed)
                or len(observed) != len(set(observed))
                or not set(expected).issubset(observed)
                or not source.get("raw_evidence_references")
                or not source.get("report_reference")):
            raise ValueError("SOURCE_REPORT_NOT_EXACT_OR_INCOMPLETE")
        mode = "LIVE_WINDOWS" if route[2] == "W09-G02" else "FIXTURE"
        if route[3] == "A06" and source.get("scope") != "LIVE_WINDOWS_LOCAL":
            raise ValueError("A06_SOURCE_SCOPE_CHANGED")
        if route[3] == "C19" and source.get("scope") != "FIXTURE_IMPLEMENTED_SERVICE":
            raise ValueError("C19_SOURCE_SCOPE_CHANGED")
        report = {
            "status": "PASS", "assertions": len(expected), "assertion_ids": expected,
            "task_id": "W09", "check_id": route[2] or None, "case_id": route[3] or None,
            "mode": mode, "scope": source.get("scope"),
            "source_assertion_ids": observed,
            "source_report_reference": source["report_reference"],
            "raw_evidence_references": source["raw_evidence_references"],
            "source_scope_reclassification_required": route[3] == "A06",
            "formal_acceptance": "PENDING_INDEPENDENT_VERIFIER",
        }
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        sys.stdout.buffer.write(child.stdout)
        print(json.dumps({"status": "FAIL", "assertion_ids": [], "assertions": 0,
                          "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
