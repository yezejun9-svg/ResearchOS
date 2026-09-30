#!/usr/bin/env python3
"""Run bounded W08 fixture checks and preserve their raw evidence."""
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_IDS = {
    "C05": {"TestW08C05CompleteWithoutAdoption"},
    "C06": {"TestW08C06MissingXContinuesSources", "TestW08C06RateLimitedXCoalesces"},
    "W08-G02": {"TestW08G02SixHourAndMissedTicks", "TestW08C06RateLimitedXCoalesces"},
}
TEST_IDS["W08-G01"] = set().union(*TEST_IDS.values())
ASSERTIONS = {
    "C05": {"C05-EXPERIMENT", "C05-01", "C05-02", "C05-03", "C05-03-REVISIT", "C05-02-NO-ADOPT", "C05-02-NO-FALSE-ADOPT", "C05-01-PAGES"},
    "C06": {"C06-01", "C06-02-X", "C06-02-NO-FALSE-COMPLETE", "C06-02", "C06-03-REQUEST", "C06-03-DEDUP", "C06-03-RETRY-AFTER", "C06-03-RETRY", "C06-02-429", "W08-G02-COALESCE", "W08-G02-ONE-ACTIVE"},
    "W08-G02": {"W08-G02-FIRST-LOOKBACK", "W08-G02-MISSED-WINDOW", "W08-G02-MISSED-COALESCED", "W08-G02-COALESCE", "W08-G02-ONE-ACTIVE", "C06-02-429", "C06-03-RETRY", "C06-03-RETRY-AFTER"},
}
ASSERTIONS["W08-G01"] = set().union(*ASSERTIONS.values())
SOURCES = ["internal/domain/research.go", "internal/domain/candidates.go", "internal/domain/research_test.go", "migrations/sqlite/0013_research_cycles.sql", "ops/ci/research.py"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def main(command_key="test.research.fixture"):
    if os.getenv("RESEARCHOS_TASK_ID") != "W08":
        raise ValueError("RESEARCHOS_TASK_ID must be W08")
    check, case = os.getenv("RESEARCHOS_CHECK_ID", ""), os.getenv("RESEARCHOS_CASE_ID", "")
    selected = case or check
    if selected not in TEST_IDS or (case and check):
        raise ValueError("select one of W08-G01, W08-G02, C05, C06")
    allowed = {"test.research.fixture": TEST_IDS, "test.experiments": {"W08-G01", "C05"}, "test.sources.fixture": {"W08-G01", "C06"}}
    if selected not in allowed.get(command_key, {}):
        raise ValueError("command/selector mismatch")
    go = os.getenv("RESEARCHOS_GO") or json.loads((ROOT / "execution/toolchains/locked.json").read_text(encoding="utf-8"))["tools"]["go"]["path"]
    if not Path(go).is_file():
        raise FileNotFoundError("pinned Go executable unavailable")
    evidence = ROOT / "execution/receipts/W08" / ("run-" + uuid.uuid4().hex)
    evidence.mkdir(parents=True)
    tests = sorted(TEST_IDS[selected])
    import re
    command = [go, "test", "-count=1", "-json", "-run", "^(?:" + "|".join(re.escape(x) for x in tests) + ")$", "./internal/domain"]
    manifest = {"task_id": "W08", "selector": selected, "scope": "FIXTURE", "cwd": str(ROOT), "head": git("rev-parse", "HEAD"),
                "branch": git("branch", "--show-current"), "dirty_before": git("status", "--porcelain").splitlines(),
                "executor_id": os.getenv("RESEARCHOS_EXECUTOR_ID"), "command_key": command_key,
                "registered_command_revision": sha(ROOT / "execution/commands.json"),
                "source_hashes": {name: sha(ROOT / name) for name in SOURCES},
                "command": command, "started_at": now()}
    (evidence / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["W08_EVIDENCE_DIR"] = str(evidence)
    try:
        process = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180, check=False)
        code, out, err = process.returncode, process.stdout, process.stderr
        timeout = False
    except subprocess.TimeoutExpired as exc:
        code, out, err = -1, exc.stdout or b"", exc.stderr or b""
        timeout = True
    stdout, stderr = evidence / "go-test.jsonl", evidence / "go-test.stderr"
    stdout.write_bytes(out)
    stderr.write_bytes(err)
    passes, seen, failures, assertions = set(), set(), [], {}
    for line in out.decode("utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            failures.append("invalid Go test event")
            continue
        test = event.get("Test")
        if test in TEST_IDS[selected] and event.get("Action") == "pass":
            passes.add(test)
        if event.get("Action") == "output" and test in TEST_IDS[selected]:
            output = event.get("Output", "")
            if "W08_ASSERTION " not in output:
                continue
            try:
                assertion = json.loads(output.split("W08_ASSERTION ", 1)[1])
                aid = assertion["assertion_id"]
                if aid in seen:
                    failures.append("duplicate assertion " + aid)
                seen.add(aid)
                assertions[aid] = assertion
            except (ValueError, KeyError):
                failures.append("invalid assertion event")
    failures += ["missing test " + x for x in sorted(TEST_IDS[selected] - passes)]
    failures += ["missing assertion " + x for x in sorted(ASSERTIONS[selected] - seen)]
    failures += ["unexpected assertion " + x for x in sorted(seen - ASSERTIONS[selected])]
    failures += ["failed assertion " + x for x, a in assertions.items() if a.get("status") != "PASS"]
    failures += ["go test exit " + str(code)] if code else []
    snapshots = {p.name: sha(p) for p in sorted(evidence.glob("*-sqlite.json"))}
    if selected in {"C05", "C06", "W08-G01"} and not snapshots:
        failures.append("missing SQLite snapshots")
    report = {**manifest, "ended_at": now(), "exit_code": code, "timed_out": timeout,
              "status": "PASS" if not failures and seen else "FAIL", "test_ids": sorted(passes),
              "assertion_ids": sorted(seen), "expected_assertion_ids": sorted(ASSERTIONS[selected]),
              "assertion_count": len(seen), "failures": failures,
              "assertions": [assertions[key] for key in sorted(assertions)],
              "raw": {p.name: sha(p) for p in (stdout, stderr)}, "sqlite_snapshots": snapshots,
              "formal_product_acceptance": "PENDING_INDEPENDENT_REVIEW",
              "limitations": "Sealed local source fixture; no live XBrowser bounded-window proof or production scheduler."}
    (evidence / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "selector": selected, "scope": "FIXTURE", "assertions": len(seen),
                      "assertion_ids": sorted(seen), "failures": failures,
                      "report_reference": str((evidence / "report.json").relative_to(ROOT))}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        sys.exit(1)
