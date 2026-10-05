"""W09-01 handler for the v2.4 registry key `test.retrieval`, selector W09/W09-01.

Why this file exists (measured, not assumed):
  * `execution/v2.4/commands.json` has no `test.retrieval` entry yet, and the accepted legacy binding
    `execution/commands.json:test.retrieval` -> ops/ci/retrieval.py whitelists only check ids W09-G01 and
    W09-G02 (retrieval.py:125) over a TESTS table of W09* selectors (retrieval.py:16-27). A card id of `W09-01`
    is therefore a guaranteed "NOT_IMPLEMENTED: unknown task/check/case selector" refusal there, and editing that
    accepted harness is outside this card's write_scope. This program is the handler the W02 registration should
    point at; registering the key itself belongs to W02/the orchestrator.
  * Like tests/orchestration/check/main.py and tests/sources/check/main.py, the card's evidence is the assertion
    roster its own Go tests emit. This program runs `go test -json -run '^TestW0901' ./internal/domain`, collects
    the W09_ASSERTION lines and requires the emitted set to equal the expected W0901 roster exactly - sorted
    equality, no duplicates, every record status PASS, exit code zero - and names missing_assertion_ids otherwise.
    A green suite with a shrunken roster is a FAIL here, never a PASS with fewer rows.

Nothing in this report is product acceptance. Scope is CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE.
"""
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[3]
LOCKED = ROOT / "execution" / "toolchains" / "locked.json"
GO_TEST_FILE = ROOT / "internal" / "domain" / "evidence_w0901_test.go"
RECEIPT_ROOT = ROOT / "execution" / "v2.4" / "receipts" / "W09" / "W09-01" / "dispatched"
OWNED_TASK, OWNED_CHECK = "W09", "W09-01"
PACKAGES = ["./internal/domain"]
SUITE_TIMEOUT_SECONDS = 600

# The roster is declared here and cross-checked against the Go source, so an assertion that is deleted, renamed
# or never emitted shows up as a red row instead of as a quietly smaller PASS.
EXPECTED_IDS = [
    "W0901-BASELINE-LOCAL-FTS5-INDEX-ANSWERS-THE-HIT",
    "W0901-CROSS-PROJECT-SAME-NAME-ARTIFACT-METADATA-DENIED",
    "W0901-CROSS-PROJECT-SAME-NAME-CAPTURE-THROUGH-FIRST-ROOT-REFUSED",
    "W0901-CROSS-PROJECT-SAME-NAME-MARKER-ABSENT-FROM-FIRST-PROJECT-REPLIES",
    "W0901-CROSS-PROJECT-SAME-NAME-SEALED-BODY-DENIED",
    "W0901-CROSS-PROJECT-SAME-NAME-SEARCH-DENIED",
    "W0901-CROSS-PROJECT-SECOND-PROJECT-READS-ITS-OWN-SAME-NAME-BODY",
    "W0901-EVIDENCE-ROW-CARRIES-LOCATOR-TYPE-OBSERVED-AT-AND-SNAPSHOT-REF",
    "W0901-OBSERVED-CLAIM-REFUSED-OVER-FIXTURE-MODE-SNAPSHOT",
    "W0901-OBSERVED-CLAIM-REFUSED-OVER-SIMULATED-SNAPSHOT",
    "W0901-REVOCATION-PROPAGATES-THROUGH-THE-CITATION-CHAIN",
    "W0901-REVOKED-ROOT-CANNOT-CAPTURE-AGAIN",
    "W0901-REVOKED-ROOT-FRESH-SEARCH-RETURNS-NO-HITS",
    "W0901-REVOKED-ROOT-IDEMPOTENT-REPLAY-DOES-NOT-SERVE-SEALED-BODY",
    "W0901-REVOKED-ROOT-SEALED-BODY-READ-DENIED",
    "W0901-SAME-BYTES-REPOST-MERGED-INTO-ONE-ARTIFACT-KEEPS-CHAIN",
    "W0901-SEALED-BODY-READS-BACK-BYTES-IDENTICAL",
    "W0901-SEALED-BODY-SERVED-BEFORE-REVOCATION",
    "W0901-SEALED-HASH-EQUALS-SHA256-OF-ORIGINAL-BYTES",
    "W0901-SEARCH-HIT-CITES-SEALED-ARTIFACT-EVIDENCE-AND-LOCATOR",
    "W0901-SEARCH-REFUSES-HOST-PATH-INPUT",
    "W0901-SEARCH-REFUSES-PRINCIPAL-WITHOUT-PROJECT-GRANT",
    "W0901-SEARCH-REVALIDATES-CURRENT-SOURCE-HASH-BEFORE-HIT",
    "W0901-SIMULATED-BYTES-REFUSED-RESEAL-AS-LIVE-LOCAL-SNAPSHOT",
    "W0901-SIMULATED-EVIDENCE-REFUSED-ORIGIN-REVIEW",
    "W0901-SIMULATION-NEVER-COUNTED-AS-INDEPENDENT-OBSERVED-SUPPORT",
    "W0901-SOURCE-UPDATE-DROPS-DEPENDENT-OBSERVED-SUPPORT",
    "W0901-STALE-ORIGIN-CANNOT-ANCHOR-A-NEW-DOWNSTREAM",
    "W0901-SUMMARY-BODY-CANNOT-BE-SWAPPED-FOR-SEALED-ORIGINAL",
    "W0901-UNCITED-REPOST-CANNOT-BE-ATTACHED-TO-THE-ORIGIN",
]
OWNED_TESTS = [
    "TestW0901SealedOriginalIsTheProductBody",
    "TestW0901SameBytesRepostMergesButKeepsChain",
    "TestW0901SourceUpdateDropsDependentSupport",
    "TestW0901LocalSearchCitesSealedOriginalAndRevalidates",
    "TestW0901SimulatedSourceCannotPoseAsObserved",
    "TestW0901SameNameFileStaysInsideItsOwnProject",
    "TestW0901RevokedRootCannotServeSealedBodyAgain",
]
# Deliverable 2 names three counter-examples that must be refused. Each is carried by every row that measures it,
# so losing any one of them - not only the headline row - turns this check red.
COUNTEREXAMPLE_ROWS = {
    "simulated-disguised-as-observed": [
        "W0901-OBSERVED-CLAIM-REFUSED-OVER-SIMULATED-SNAPSHOT",
        "W0901-OBSERVED-CLAIM-REFUSED-OVER-FIXTURE-MODE-SNAPSHOT",
        "W0901-SIMULATED-BYTES-REFUSED-RESEAL-AS-LIVE-LOCAL-SNAPSHOT",
        "W0901-SIMULATED-EVIDENCE-REFUSED-ORIGIN-REVIEW",
        "W0901-SIMULATION-NEVER-COUNTED-AS-INDEPENDENT-OBSERVED-SUPPORT",
    ],
    "same-name-file-cross-project-leak": [
        "W0901-CROSS-PROJECT-SAME-NAME-ARTIFACT-METADATA-DENIED",
        "W0901-CROSS-PROJECT-SAME-NAME-SEALED-BODY-DENIED",
        "W0901-CROSS-PROJECT-SAME-NAME-SEARCH-DENIED",
        "W0901-CROSS-PROJECT-SAME-NAME-CAPTURE-THROUGH-FIRST-ROOT-REFUSED",
        "W0901-CROSS-PROJECT-SAME-NAME-MARKER-ABSENT-FROM-FIRST-PROJECT-REPLIES",
        "W0901-SEARCH-REFUSES-PRINCIPAL-WITHOUT-PROJECT-GRANT",
        "W0901-SEARCH-REFUSES-HOST-PATH-INPUT",
    ],
    "cache-hits-after-revocation": [
        "W0901-SEALED-BODY-SERVED-BEFORE-REVOCATION",
        "W0901-REVOKED-ROOT-IDEMPOTENT-REPLAY-DOES-NOT-SERVE-SEALED-BODY",
        "W0901-REVOKED-ROOT-FRESH-SEARCH-RETURNS-NO-HITS",
        "W0901-REVOKED-ROOT-SEALED-BODY-READ-DENIED",
        "W0901-REVOKED-ROOT-CANNOT-CAPTURE-AGAIN",
        "W0901-REVOCATION-PROPAGATES-THROUGH-THE-CITATION-CHAIN",
    ],
}
ACTION_FOUR_NOTE = ("action 4 is asserted only as the local index the product really exposes (backend sqlite-fts5, "
                    "revision fts5-v1, bounded-scan as the only other value). No field, state or adapter slot in "
                    "this build represents a Sirchmunk source qualification - `sirchmunk_status` exists only as a "
                    "constant in ops/ci/retrieval.py - so no Sirchmunk row is claimed here. The gap is disclosed, "
                    "not papered over.")

# Routing is part of the deliverable: this handler answers exactly one binding. W09-G01/W09-G02/A06/C19 belong to
# ops/ci/retrieval.py and to the parent gate, and W09-02 belongs to the next card, so a foreign binding is refused
# with an EMPTY roster rather than answered or paraphrased. Answering another card's selector here would let this
# card's guard decide what that card's evidence means.
ROUTING_TABLE = [
    {"task": "W09", "check": "W09-01", "case": "", "expected": "serve"},
    {"task": "W09", "check": "W09-02", "case": "", "expected": "refuse"},
    {"task": "W09", "check": "W09-G01", "case": "", "expected": "refuse"},
    {"task": "W09", "check": "W09-G02", "case": "A06", "expected": "refuse"},
    {"task": "W09", "check": "", "case": "C19", "expected": "refuse"},
    {"task": "W08", "check": "W08-01", "case": "", "expected": "refuse"},
    {"task": "W17", "check": "W09-01", "case": "", "expected": "refuse"},
    {"task": "", "check": "", "case": "", "expected": "refuse"},
]


def route(task, check, case):
    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def emit(status, ids, failures, extra=None):
    """Print the one and only report line. The dispatcher parses the child's LAST stdout line as JSON."""
    failures = list(failures)
    clean = [i for i in ids if isinstance(i, str) and i]
    duplicates = sorted({i for i in clean if clean.count(i) > 1})
    if duplicates or len(clean) != len(ids):
        failures.append({"id": "W0901-ASSERTION-IDS-UNIQUE",
                         "detail": "duplicated: %s; blank ids: %d" % (duplicates, len(ids) - len(clean))})
        status = "FAIL"
    unique = sorted(set(clean))
    report = {"status": status, "assertions": len(unique), "assertion_ids": unique, "failures": failures,
              "task_id": OWNED_TASK, "check_id": OWNED_CHECK,
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
              "expected_card_assertion_ids": sorted(EXPECTED_IDS),
              "handler": "tests/evidence/check/main.py", "emitted_at": utc()}
    if extra:
        report.update(extra)
    print(json.dumps(report))
    return 0 if status == "PASS" and unique else 1


def refuse(reason, observed):
    """A binding this card does not own: status FAIL, empty assertion list, non-zero exit."""
    return emit("FAIL", [], [{"id": "W0901-ROUTING-BINDING-REFUSED", "detail": reason}],
                extra={"routing": {"task_id": observed[0], "check_id": observed[1], "case_id": observed[2],
                                   "decision": "refuse",
                                   "note": "W09-G01/W09-G02/A06/C19 belong to ops/ci/retrieval.py; every other "
                                           "card id belongs to its own handler"}})


def resolve_go(explicit=None):
    """Absolute pinned executable verified against the locked table, or nothing. Never a PATH lookup."""
    try:
        tools = json.loads(LOCKED.read_text(encoding="utf-8-sig"))["tools"]["go"]
    except Exception as exc:
        return None, "the locked toolchain table could not be read: %s" % exc
    candidates = []
    if explicit is not None:
        candidates.append(("explicit-probe", explicit))
    else:
        from_env = os.environ.get("RESEARCHOS_GO") or ""
        if from_env:
            candidates.append(("RESEARCHOS_GO", from_env))
        candidates.append(("execution/toolchains/locked.json", tools.get("path")))
    for source, path in candidates:
        if not path or not os.path.isabs(path) or not os.path.isfile(path):
            continue
        try:
            digest = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
        except OSError:
            continue
        if digest != tools.get("sha256"):
            return None, "%s points at %s, whose sha256 is not the locked table's" % (source, path)
        try:
            version = subprocess.run([path] + list(tools.get("version_argv") or ["version"]),
                                     capture_output=True, text=True, encoding="utf-8", timeout=120)
        except Exception as exc:
            return None, "the pinned go from %s could not report its version: %s" % (source, exc)
        if version.returncode != 0 or (version.stdout or "").strip() != tools.get("version_output"):
            return None, "the go from %s reports %r while the table says %r" % (
                source, (version.stdout or "").strip(), tools.get("version_output"))
        return path, "verified from %s" % source
    return None, "no absolute pinned go executable found among %s; a PATH lookup is never used" % (
        [source for source, _ in candidates])


def declared_in_go_source():
    """Every id literally emitted by this card's Go tests, read out of the test source."""
    if not GO_TEST_FILE.is_file():
        return None
    text = GO_TEST_FILE.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'w09Assertion\(\s*t,\s*"(W0901-[A-Z0-9-]+)"', text)))


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60).stdout.strip()
    except Exception:
        return ""


def run_suite(go_binary, out):
    """go test -json for this card only, with the raw output kept as evidence."""
    env = dict(os.environ)
    injected = {}
    for name, value in (("GOTOOLCHAIN", "local"),
                        ("GOPATH", str(ROOT / ".local" / "gopath")),
                        ("GOCACHE", str(ROOT / ".local" / "gocache"))):
        if not env.get(name):
            env[name] = value
            injected[name] = value
    argv = [go_binary, "test", "-count=1", "-json", "-timeout", "%ds" % SUITE_TIMEOUT_SECONDS,
            "-run", "^TestW0901"] + PACKAGES
    (out / "before.json").write_text(json.dumps({
        "selector": OWNED_CHECK, "owner": OWNED_CHECK, "argv": argv, "cwd": str(ROOT),
        "started_at": utc(), "git_head": git("rev-parse", "HEAD"), "code_tree": git("write-tree"),
        "tracked_status_porcelain": git("status", "--porcelain", "--untracked-files=no"),
        "untracked_status_lines": len([line for line in git("status", "--porcelain").splitlines() if line.strip()]),
        "executor": os.environ.get("RESEARCHOS_EXECUTOR_ID", "local:operator"),
        "go_executable": go_binary, "go_environment_injected": injected,
        "expected_assertion_ids": sorted(EXPECTED_IDS), "owned_tests": OWNED_TESTS,
        "pinned_toolchain_table": LOCKED.relative_to(ROOT).as_posix(),
        "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    timed_out = False
    try:
        completed = subprocess.run(argv, cwd=str(ROOT), env=env, capture_output=True, timeout=660)
        stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b"", exc.stderr or b"", 124, True
    (out / "go-test.stdout.jsonl").write_bytes(stdout or b"")
    (out / "go-test.stderr.txt").write_bytes(stderr or b"")
    events, malformed = [], []
    for line in (stdout or b"").decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            malformed.append(line[:200])
    emitted_text = "".join(event.get("Output", "") for event in events)
    records = []
    for number, line in enumerate(emitted_text.splitlines(), 1):
        if not line.startswith("W09_ASSERTION "):
            continue
        try:
            row = json.loads(line[len("W09_ASSERTION "):])
        except ValueError:
            malformed.append("assertion line %d is not parsable JSON" % number)
            continue
        if "assertion_id" not in row or "status" not in row:
            malformed.append("assertion line %d has no assertion_id/status" % number)
            continue
        row["raw"] = {"path": (out / "go-test.stdout.jsonl").relative_to(ROOT).as_posix(), "line": number}
        records.append(row)
    passed = sorted({event.get("Test") for event in events
                     if event.get("Action") == "pass" and event.get("Test")})
    failed = sorted({event.get("Test") for event in events
                     if event.get("Action") == "fail" and event.get("Test")})
    return {"code": code, "timed_out": timed_out, "records": records, "malformed": malformed,
            "passed": passed, "failed": failed, "argv": argv,
            "stderr_tail": (stderr or b"").decode("utf-8", errors="replace")[-600:]}


def probe_foreign_binding():
    """Re-run this program under a binding it does not own and measure the refusal.

    The depth cap is mandatory, not optional: without it, a build whose routing guard was removed would re-probe
    all the way down. The child is marked, and a marked child never probes again - it can only refuse or answer.
    """
    if os.environ.get("W0901_PROBE_DEPTH", ""):
        return {"ran": False, "skipped": True, "reason": "already a nested probe child; nesting capped at depth 1"}
    environment = dict(os.environ, RESEARCHOS_TASK_ID=OWNED_TASK, RESEARCHOS_CHECK_ID="W09-02",
                       RESEARCHOS_CASE_ID="", W0901_PROBE_DEPTH="1")
    try:
        completed = subprocess.run([sys.executable, "-X", "utf8", str(pathlib.Path(__file__))],
                                   cwd=str(ROOT), env=environment, capture_output=True, timeout=600)
    except Exception as exc:
        return {"ran": False, "reason": "%s: %s" % (type(exc).__name__, exc)}
    stdout = (completed.stdout or b"").decode("utf-8", errors="replace").strip()
    lines = stdout.splitlines() if stdout else []
    parsed = {}
    if lines:
        try:
            parsed = json.loads(lines[-1])
        except ValueError:
            parsed = {}
    ids = parsed.get("assertion_ids")
    return {"ran": True, "exit_code": completed.returncode, "status": parsed.get("status"),
            "assertions": parsed.get("assertions"), "assertion_ids": ids if isinstance(ids, list) else None,
            "stdout_lines": len(lines),
            "stderr_tail": (completed.stderr or b"").decode("utf-8", errors="replace")[-400:]}


def serve(out):
    ids, failures, notes = [], [], []

    def ok(label, condition, detail=None):
        if condition:
            ids.append(label)
        else:
            failures.append({"id": label, "detail": str(detail)[:500]})

    def note(probe, observed, detail):
        notes.append({"probe": probe, "observed": observed, "detail": str(detail)[:300]})

    wrong = [row for row in ROUTING_TABLE if route(row["task"], row["check"], row["case"]) != row["expected"]]
    ok("W0901-ROUTING-TRUTH-TABLE", not wrong and len(ROUTING_TABLE) >= 6,
       "mismatched rows %s" % json.dumps(wrong, ensure_ascii=False)[:400])
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    ok("W0901-ROUTING-BINDING-SERVED", route(task, check, case) == "serve" and
       (task, check, case) == (OWNED_TASK, OWNED_CHECK, ""),
       "task_id=%r check_id=%r case_id=%r" % (task, check, case))
    probe = probe_foreign_binding()
    ok("W0901-ROUTING-FOREIGN-BINDING-REFUSED",
       probe.get("ran") is True and probe.get("exit_code") not in (0, None) and probe.get("status") == "FAIL"
       and probe.get("assertions") == 0 and probe.get("assertion_ids") == [] and probe.get("stdout_lines") == 1,
       json.dumps(probe, ensure_ascii=False)[:450])
    note("foreign-binding-self-probe", {key: probe.get(key) for key in
                                        ("exit_code", "status", "assertions", "stdout_lines")},
         "re-ran this program with RESEARCHOS_CHECK_ID=W09-02 and W0901_PROBE_DEPTH=1; the refusal is exactly one "
         "report line whose roster is empty, and the marked child never probes again")

    go_binary, go_reason = resolve_go()
    ok("W0901-TOOLCHAIN-GO-FROM-LOCKED-TABLE", go_binary is not None, go_reason)
    absent, _ = resolve_go(explicit=str(ROOT / "no" / "such" / "go.exe"))
    relative, _ = resolve_go(explicit="go")
    ok("W0901-TOOLCHAIN-PATH-FALLBACK-IS-REFUSED", absent is None and relative is None,
       "an absent absolute path and a bare relative name must yield no executable, not a PATH lookup")
    note("pinned-go", go_binary, "every number below came from %s (%s)" % (go_binary, go_reason))
    if go_binary is None:
        for label in EXPECTED_IDS:
            failures.append({"id": label, "detail": "the pinned go is unavailable: %s" % go_reason})
        # Even a run that never started a test process leaves its own receipt, so the refused toolchain is
        # auditable instead of being an empty directory.
        refusal = {"status": "FAIL", "task_id": OWNED_TASK, "check_id": OWNED_CHECK, "measured_at": utc(),
                   "reason": "the pinned go could not be resolved, so no test process was started",
                   "go_reason": go_reason, "harness_assertion_ids": sorted(ids),
                   "missing_assertion_ids": sorted(EXPECTED_IDS), "failures": failures,
                   "diagnostics": notes, "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
                   "action_4_scope": ACTION_FOUR_NOTE}
        (out / "report.json").write_text(json.dumps(refusal, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
        return emit("FAIL", ids, failures,
                    extra={"missing_assertion_ids": sorted(EXPECTED_IDS),
                           "receipt_directory": out.relative_to(ROOT).as_posix(),
                           "report_reference": (out / "report.json").relative_to(ROOT).as_posix(),
                           "report_hash": "sha256:" + hashlib.sha256(
                               (out / "report.json").read_bytes()).hexdigest(),
                           "pinned_go": None, "go_reason": go_reason,
                           "harness_assertion_ids": sorted(ids), "diagnostics": notes})

    result = run_suite(go_binary, out)
    emitted = [str(row.get("assertion_id")) for row in result["records"]]
    ok("W0901-GO-TEST-SUITE-GREEN",
       result["code"] == 0 and not result["timed_out"] and not result["failed"]
       and set(OWNED_TESTS) <= set(result["passed"]),
       "rc=%s timed_out=%s failed=%s passed=%s stderr=%s" % (result["code"], result["timed_out"],
                                                             result["failed"], result["passed"],
                                                             result["stderr_tail"][:200]))
    missing = sorted(set(EXPECTED_IDS) - set(emitted))
    unexpected = sorted(set(emitted) - set(EXPECTED_IDS))
    duplicates = sorted({i for i in emitted if emitted.count(i) > 1})
    not_passing = sorted({str(row.get("assertion_id")) for row in result["records"]
                          if row.get("status") != "PASS"})
    ok("W0901-ROSTER-EMITTED-EQUALS-EXPECTED",
       result["code"] == 0 and not missing and not unexpected and not duplicates and not not_passing
       and not result["malformed"] and len(emitted) == len(EXPECTED_IDS),
       json.dumps({"missing_assertion_ids": missing, "unexpected_assertion_ids": unexpected,
                   "duplicate_assertion_ids": duplicates, "non_passing": not_passing,
                   "malformed": result["malformed"][:3], "emitted": len(emitted),
                   "expected": len(EXPECTED_IDS)}, ensure_ascii=False)[:480])
    for label in missing:
        failures.append({"id": label, "detail": "not emitted by %s" % " ".join(result["argv"])})
    source_ids = declared_in_go_source()
    ok("W0901-ROSTER-GO-SOURCE-EQUALS-EXPECTED", source_ids is not None and source_ids == sorted(EXPECTED_IDS),
       json.dumps({"test_file": GO_TEST_FILE.relative_to(ROOT).as_posix(),
                   "source_only": sorted(set(source_ids or []) - set(EXPECTED_IDS)),
                   "registry_only": sorted(set(EXPECTED_IDS) - set(source_ids or []))},
                  ensure_ascii=False)[:400])
    absent_rows = {group: sorted(set(rows) - set(emitted)) for group, rows in COUNTEREXAMPLE_ROWS.items()}
    ok("W0901-COUNTEREXAMPLES-ALL-REFUSED",
       not any(absent_rows.values()) and all(len(rows) >= 3 for rows in COUNTEREXAMPLE_ROWS.values()),
       json.dumps(absent_rows, ensure_ascii=False)[:450])
    # Every raw command output this card claims must exist under this card's own receipts directory, in a fresh
    # run uuid, so a report can never point at another card's evidence. go test writes nothing to stderr on a
    # clean run, so the stderr file only has to exist; the stdout file has to carry the assertion records.
    evidence_files = ("before.json", "go-test.stdout.jsonl", "go-test.stderr.txt")
    under_card_path = out.relative_to(ROOT).as_posix().startswith(
        "execution/v2.4/receipts/W09/W09-01/dispatched/")
    short_files = [name for name in evidence_files if not (out / name).is_file()]
    empty_files = [name for name in ("before.json", "go-test.stdout.jsonl")
                   if (out / name).is_file() and (out / name).stat().st_size == 0]
    ok("W0901-GO-TEST-EVIDENCE-WRITTEN-UNDER-CARD-DIRECTORY",
       under_card_path and not short_files and not empty_files and bool(result["records"]),
       "missing %s empty %s records %d path %s prefix_ok %s" % (short_files, empty_files,
                                                                len(result["records"]),
                                                                out.relative_to(ROOT).as_posix(), under_card_path))
    note("roster", {"emitted": len(emitted), "expected": len(EXPECTED_IDS),
                    "unique": len(set(emitted)), "harness_rows": len(ids)},
         "assertion_ids below are the card roster plus this handler's own rows")

    status = "PASS" if not failures else "FAIL"
    report = {"status": status, "task_id": OWNED_TASK, "check_id": OWNED_CHECK,
              "selector": "test.retrieval --task-id W09 --check-id W09-01",
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE", "measured_at": utc(),
              "go_test": {"exit_code": result["code"], "timed_out": result["timed_out"], "argv": result["argv"],
                          "packages": PACKAGES, "passed_tests": result["passed"], "failed_tests": result["failed"],
                          "assertion_records": len(result["records"]), "malformed": result["malformed"]},
              "assertion_results": result["records"],
              "emitted_assertion_ids": sorted(set(emitted)), "missing_assertion_ids": missing,
              "unexpected_assertion_ids": unexpected, "duplicate_assertion_ids": duplicates,
              "non_passing_assertion_ids": not_passing, "counterexample_absence": absent_rows,
              "routing_self_probe": probe, "harness_assertion_ids": sorted(ids),
              "action_4_scope": ACTION_FOUR_NOTE, "failures": failures, "diagnostics": notes,
              "raw_evidence": {name: (out / name).relative_to(ROOT).as_posix() for name in
                               ("before.json", "go-test.stdout.jsonl", "go-test.stderr.txt")},
              "independent_acceptance": "NOT_REQUESTED"}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reference = (out / "report.json").relative_to(ROOT).as_posix()
    return emit(status, ids + emitted, failures,
                extra={"missing_assertion_ids": missing, "unexpected_assertion_ids": unexpected,
                       "duplicate_assertion_ids": duplicates, "non_passing_assertion_ids": not_passing,
                       "counterexample_absence": absent_rows, "go_test_exit_code": result["code"],
                       "routing_probe": {key: probe.get(key) for key in ("ran", "exit_code", "status",
                                                                         "assertions", "stdout_lines")},
                       "pinned_go": go_binary, "harness_assertion_ids": sorted(ids),
                       "card_assertion_id_count": len(set(emitted) & set(EXPECTED_IDS)),
                       "receipt_directory": out.relative_to(ROOT).as_posix(),
                       "report_reference": reference,
                       "report_hash": "sha256:" + hashlib.sha256((out / "report.json").read_bytes()).hexdigest(),
                       "action_4_scope": ACTION_FOUR_NOTE, "diagnostics": notes})


def main():
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    if route(task, check, case) != "serve":
        return refuse("this handler answers only W09/W09-01; observed task_id=%r check_id=%r case_id=%r"
                      % (task, check, case), (task, check, case))
    out = RECEIPT_ROOT / str(uuid.uuid4())
    out.mkdir(parents=True, exist_ok=False)
    try:
        return serve(out)
    except Exception as exc:
        # An unexpected failure still produces exactly one report line, and never a PASS.
        return emit("FAIL", [], [{"id": "W0901-HANDLER-CRASHED",
                                  "detail": "%s: %s" % (type(exc).__name__, str(exc)[:400])}],
                    extra={"receipt_directory": out.relative_to(ROOT).as_posix()})


if __name__ == "__main__":
    sys.exit(main())
