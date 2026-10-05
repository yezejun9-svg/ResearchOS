"""W09-02 handler for the v2.4 registry key `test.retrieval.revocation`, selector W09/W09-02.

Why this card has its own program instead of widening tests/evidence/check/main.py
- main.py belongs to accepted card W09-01. Its binding line, its 41-id output and its
  expected_artifacts all name that file, so editing it to answer a second card would move an
  accepted card's deliverable underneath its own receipt.
- The plan declares `test.security` for W09-02. That key is BOUND with selectors W17/W17-01 and
  its handler is tests/security/check, owned by accepted card W17-01 and writable by no card in
  the W09 line. Appending W09/W09-02 to that key would answer a W09 dispatch with W17's host
  roster, which is a fabricated PASS - the one outcome this line exists to prevent. The deviation
  is disclosed in the receipt with the measured refusal of the declared selector.

What it does
- Serves exactly one binding; every other binding is refused with an empty roster and a non-zero
  exit, and the handler proves that by re-running itself under a foreign binding (depth capped).
- Runs `go test -json -run '^TestW0902' ./internal/domain` with go resolved only from the locked
  toolchain table, never from PATH.
- Requires the emitted card roster to equal the expected 15 exactly, with no duplicate, no
  non-PASS record, and the Go source literals to agree with the same set.
- Creates its receipt directory lazily at the first write, because W09-01 disclosed that creating
  it up front left 694 empty directories behind.
"""
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
GO_TEST_FILE = ROOT / "internal" / "domain" / "evidence_w0902_test.go"
PACKAGES = ["./internal/domain"]
# Inside the registry's 600s budget on purpose: if the outer timeout fired first the dispatcher
# would kill the child and no report line would exist to say why.
SUITE_TIMEOUT_SECONDS = 540
OWNED_TASK, OWNED_CHECK = "W09", "W09-02"
RECEIPT_ROOT = ROOT / "execution" / "v2.4" / "receipts" / "W09" / "W09-02" / "dispatched"

CARD_IDS = [
    "W0902-ADAPTER-NAMES-A-JUNCTION-ESCAPE-AS-A-LINK",
    "W0902-ADAPTER-NAMES-AN-ABSENT-FILE-AS-ABSENCE",
    "W0902-DELETED-SOURCE-DROPS-THE-CACHED-HIT-AND-SAYS-WHY",
    "W0902-DELETED-SOURCE-SEALED-BODY-READ-IS-REFUSED",
    "W0902-HIT-SERVED-BEFORE-THE-SOURCE-WAS-DELETED",
    "W0902-INDEX-LEG-IS-A-COMPILE-TIME-CONSTANT",
    "W0902-KEY-CHANGES-WHEN-A-SEALED-ARTIFACT-IDENTITY-MOVES",
    "W0902-KEY-CHANGES-WHEN-THE-ACTING-PRINCIPAL-CHANGES",
    "W0902-KEY-RESTORES-WHEN-THE-ORIGINAL-PRINCIPAL-RESUMES",
    "W0902-KEY-STABLE-FOR-IDENTICAL-INPUT",
    "W0902-KNOWN-GAP-HARD-LINK-INTO-A-ROOT-IS-SEALED-AND-SERVED",
    "W0902-KNOWN-GAP-THE-DOMAIN-COLLAPSES-EVERY-READ-REFUSAL-TO-ONE-MESSAGE",
    "W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",
    "W0902-ORDINARY-REGULAR-FILE-STILL-SEALS-AFTER-THE-CLASSIFIER",
    "W0902-REVOKED-CREDENTIAL-LOSES-THE-SEARCH-SURFACE",
    "W0902-SHARED-PROJECTION-CARRIES-EVIDENCE-AND-SOURCE-KIND",
]
OWNED_TESTS = [
    "TestW0902SearchKeyBindsEachComponent",
    "TestW0902LinkAndAbsenceRefusalsDiffer",
    "TestW0902AuthorityChangesDropTheCachedResult",
    "TestW0902HardLinkIntoRootIsCurrentlyServed",
]
# Each negative class the card names, and the rows that witness it. A group whose rows are all
# present proves coverage; the point of listing them per class is that an absent class is visible
# instead of being averaged into a total.
CLASS_ROWS = {
    "source_deleted": ["W0902-HIT-SERVED-BEFORE-THE-SOURCE-WAS-DELETED",
                       "W0902-DELETED-SOURCE-DROPS-THE-CACHED-HIT-AND-SAYS-WHY",
                       "W0902-DELETED-SOURCE-SEALED-BODY-READ-IS-REFUSED"],
    "authority_changed": ["W0902-REVOKED-CREDENTIAL-LOSES-THE-SEARCH-SURFACE",
                          "W0902-KEY-CHANGES-WHEN-THE-ACTING-PRINCIPAL-CHANGES",
                          "W0902-KEY-RESTORES-WHEN-THE-ORIGINAL-PRINCIPAL-RESUMES"],
    "path_escape": ["W0902-LEXICAL-ESCAPE-REFUSED-BEFORE-THE-ROOT-IS-OPENED",
                    "W0902-ADAPTER-NAMES-AN-ABSENT-FILE-AS-ABSENCE",
                    "W0902-KNOWN-GAP-THE-DOMAIN-COLLAPSES-EVERY-READ-REFUSAL-TO-ONE-MESSAGE"],
    "link_reshape": ["W0902-ADAPTER-NAMES-A-JUNCTION-ESCAPE-AS-A-LINK",
                     "W0902-KNOWN-GAP-HARD-LINK-INTO-A-ROOT-IS-SEALED-AND-SERVED",
                     "W0902-KNOWN-GAP-THE-DOMAIN-COLLAPSES-EVERY-READ-REFUSAL-TO-ONE-MESSAGE"],
    "stale_reference": ["W0902-KEY-CHANGES-WHEN-A-SEALED-ARTIFACT-IDENTITY-MOVES",
                        "W0902-DELETED-SOURCE-DROPS-THE-CACHED-HIT-AND-SAYS-WHY",
                        "W0902-SHARED-PROJECTION-CARRIES-EVIDENCE-AND-SOURCE-KIND"],
}
NOT_COVERED = [
    "the ContextBundle call site of currentAuthorizedSnapshots is not asserted by THIS roster. The reason first "
    "given here was wrong and an independent reviewer corrected it: a green pre-existing test in the same package "
    "already exercises bundle creation, so the real gap is only that this handler's -run filter (^TestW0902) does "
    "not select it. Calling a guard 'unreachable' while a passing test exists is the error this line punishes",
    "the event/journal surface (SessionEvents) after revocation, which is the 'events still return revoked content' "
    "half of the card's counter-example: it needs a live client-protocol session this card does not own",
    "source_coverage on the ResearchCycle projection: the field lives on a research cycle object behind W16's flow, "
    "so action 3's coverage half is only reachable here through the evidence summary aggregates",
    "the lexical pre-check and the intermediate Lstat branch are asserted by nothing: removing !filepath.IsLocal "
    "outright leaves the roster green because os.Root refuses the same escape anyway, so the escape row evidences "
    "the collapsed constant rather than the pre-check",
]

ROUTING_TABLE = [
    {"task": "W09", "check": "W09-02", "case": "", "expected": "serve"},
    {"task": "W09", "check": "W09-01", "case": "", "expected": "refuse"},
    {"task": "W09", "check": "W09-03", "case": "", "expected": "refuse"},
    {"task": "W09", "check": "W09-G02", "case": "A06", "expected": "refuse"},
    {"task": "W08", "check": "W08-01", "case": "", "expected": "refuse"},
    {"task": "W17", "check": "W09-02", "case": "", "expected": "refuse"},
    {"task": "", "check": "", "case": "", "expected": "refuse"},
]
FOREIGN_PROBE_CHECK = "W09-03"


def route(task, check, case):
    return "serve" if (task, check, case) == (OWNED_TASK, OWNED_CHECK, "") else "refuse"


def utc():
    return __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()


def emit(status, ids, failures, extra=None):
    """The one and only report line; the dispatcher parses the child's LAST stdout line as JSON."""
    failures = list(failures)
    clean = [i for i in ids if isinstance(i, str) and i]
    duplicates = sorted({i for i in clean if clean.count(i) > 1})
    if duplicates or len(clean) != len(ids):
        failures.append({"id": "W0902-HARNESS-ROSTER-UNIQUE",
                         "detail": "duplicated: %s; blank ids: %d" % (duplicates, len(ids) - len(clean))})
        status = "FAIL"
    unique = sorted(set(clean))
    report = {"status": status, "assertions": len(unique), "assertion_ids": unique, "failures": failures,
              "task_id": OWNED_TASK, "check_id": OWNED_CHECK,
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
              "expected_card_assertion_ids": sorted(CARD_IDS),
              "handler": "tests/evidence/check/revoke_cache.py", "emitted_at": utc()}
    if extra:
        report.update(extra)
    print(json.dumps(report))
    return 0 if status == "PASS" and unique else 1


def refuse(reason, observed):
    return emit("FAIL", [], [{"id": "W0902-ROUTING-BINDING-REFUSED", "detail": reason}],
                extra={"routing": {"task_id": observed[0], "check_id": observed[1], "case_id": observed[2],
                                   "decision": "refuse",
                                   "note": "W09-01 belongs to tests/evidence/check/main.py; W09-G01/W09-G02/A06/C19 "
                                           "belong to ops/ci/retrieval.py; every other card id to its own handler"}})


def resolve_go(explicit=None):
    """An absolute pinned executable verified against the locked table, or nothing. Never a PATH lookup."""
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
    return sorted(set(re.findall(r'w09Assertion\(\s*t,\s*"(W0902-[A-Z0-9-]+)"', text)))


def git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=str(ROOT), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60).stdout.strip()
    except Exception:
        return ""


def run_suite(go_binary, out):
    env = dict(os.environ)
    injected = {}
    for name, value in (("GOTOOLCHAIN", "local"),
                        ("GOPATH", str(ROOT / ".local" / "gopath")),
                        ("GOCACHE", str(ROOT / ".local" / "gocache"))):
        if not env.get(name):
            env[name] = value
            injected[name] = value
    argv = [go_binary, "test", "-count=1", "-json", "-timeout", "%ds" % SUITE_TIMEOUT_SECONDS,
            "-run", "^TestW0902"] + PACKAGES
    (out / "before.json").write_text(json.dumps({
        "selector": OWNED_CHECK, "owner": OWNED_CHECK, "argv": argv, "cwd": str(ROOT),
        "started_at": utc(), "git_head": git("rev-parse", "HEAD"), "code_tree": git("write-tree"),
        "tracked_status_porcelain": git("status", "--porcelain", "--untracked-files=no"),
        "untracked_status_lines": len([line for line in git("status", "--porcelain").splitlines() if line.strip()]),
        "executor": os.environ.get("RESEARCHOS_EXECUTOR_ID", "local:operator"),
        "go_executable": go_binary, "go_environment_injected": injected,
        "expected_assertion_ids": sorted(CARD_IDS), "owned_tests": OWNED_TESTS,
        "pinned_toolchain_table": LOCKED.relative_to(ROOT).as_posix(),
        "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    timed_out = False
    try:
        completed = subprocess.run(argv, cwd=str(ROOT), env=env, capture_output=True, timeout=SUITE_TIMEOUT_SECONDS + 60)
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
    passed = sorted({e.get("Test") for e in events if e.get("Action") == "pass" and e.get("Test")})
    failed = sorted({e.get("Test") for e in events if e.get("Action") == "fail" and e.get("Test")})
    return {"code": code, "timed_out": timed_out, "records": records, "malformed": malformed,
            "passed": passed, "failed": failed, "argv": argv,
            "stderr_tail": (stderr or b"").decode("utf-8", errors="replace")[-600:]}


def probe_foreign_binding():
    """Re-run this program under a binding it does not own and measure the refusal.

    The depth cap is mandatory: without it a build whose routing guard was removed would re-probe
    all the way down. A marked child never probes again; it can only refuse or answer.
    """
    if os.environ.get("W0902_PROBE_DEPTH", ""):
        return {"ran": False, "skipped": True, "reason": "already a nested probe child; nesting capped at depth 1"}
    environment = dict(os.environ, RESEARCHOS_TASK_ID=OWNED_TASK, RESEARCHOS_CHECK_ID=FOREIGN_PROBE_CHECK,
                       RESEARCHOS_CASE_ID="", W0902_PROBE_DEPTH="1")
    try:
        # A refusal must be fast by definition, so a generous budget here would only hide a build
        # whose routing guard is gone by spending the parent's whole timeout on it.
        completed = subprocess.run([sys.executable, "-X", "utf8", str(pathlib.Path(__file__))],
                                   cwd=str(ROOT), env=environment, capture_output=True, timeout=120)
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
            "stdout_lines": len(lines), "probed_check_id": FOREIGN_PROBE_CHECK,
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
    ok("W0902-ROUTING-TRUTH-TABLE", not wrong and len(ROUTING_TABLE) >= 6,
       "mismatched rows %s" % json.dumps(wrong, ensure_ascii=False)[:400])
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    ok("W0902-ROUTING-BINDING-SERVED", route(task, check, case) == "serve",
       "task_id=%r check_id=%r case_id=%r" % (task, check, case))
    dirs_before = len(os.listdir(RECEIPT_ROOT)) if RECEIPT_ROOT.is_dir() else 0
    probe = probe_foreign_binding()
    dirs_after = len(os.listdir(RECEIPT_ROOT)) if RECEIPT_ROOT.is_dir() else 0
    ok("W0902-ROUTING-FOREIGN-BINDING-REFUSED",
       probe.get("ran") is True and probe.get("exit_code") not in (0, None) and probe.get("status") == "FAIL"
       and probe.get("assertions") == 0 and probe.get("assertion_ids") == [] and probe.get("stdout_lines") == 1,
       json.dumps(probe, ensure_ascii=False)[:450])
    # W09-01 disclosed that its own handler created a receipt directory before it knew whether the
    # run would write anything, leaving 694 empty directories behind. Refusals must cost nothing.
    ok("W0902-REFUSED-BINDINGS-LEAVE-NO-DIRECTORY-BEHIND", dirs_after == dirs_before,
       "directory count moved from %d to %d across a refused binding" % (dirs_before, dirs_after))
    note("foreign-binding-self-probe", {k: probe.get(k) for k in ("exit_code", "status", "assertions", "stdout_lines")},
         "re-ran this program with RESEARCHOS_CHECK_ID=%s and W0902_PROBE_DEPTH=1; the refusal is exactly one report "
         "line whose roster is empty, and the marked child never probes again" % FOREIGN_PROBE_CHECK)

    go_binary, go_reason = resolve_go()
    ok("W0902-TOOLCHAIN-GO-FROM-LOCKED-TABLE", go_binary is not None, go_reason)
    absent, _ = resolve_go(explicit=str(ROOT / "no" / "such" / "go.exe"))
    relative, _ = resolve_go(explicit="go")
    ok("W0902-TOOLCHAIN-NEVER-FALLS-BACK-TO-PATH", absent is None and relative is None,
       "an absent absolute path and a bare relative name must yield no executable, not a PATH lookup")
    note("pinned-go", go_binary, "every number below came from %s (%s)" % (go_binary, go_reason))

    # A real wrong-binary probe, because the two rows above only reach the isabs/isfile legs.
    decoy, decoy_reason = resolve_go(explicit=str(pathlib.Path(sys.executable).resolve()))
    ok("W0902-TOOLCHAIN-REFUSES-A-REAL-BUT-WRONG-BINARY", decoy is None,
       "RESEARCHOS_GO pointed at a live executable that is not the pinned go, and it resolved to %r (%s)"
       % (decoy, decoy_reason))

    if go_binary is None:
        for label in CARD_IDS:
            failures.append({"id": label, "detail": "the pinned go is unavailable: %s" % go_reason})
        refusal = {"status": "FAIL", "task_id": OWNED_TASK, "check_id": OWNED_CHECK, "measured_at": utc(),
                   "reason": "the pinned go could not be resolved, so no test process was started",
                   "go_reason": go_reason, "harness_assertion_ids": sorted(ids),
                   "missing_assertion_ids": sorted(CARD_IDS), "failures": failures, "diagnostics": notes,
                   "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}
        (out / "report.json").write_text(json.dumps(refusal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return emit("FAIL", ids, failures,
                    extra={"missing_assertion_ids": sorted(CARD_IDS),
                           "receipt_directory": out.relative_to(ROOT).as_posix(),
                           "harness_assertion_ids": sorted(ids), "diagnostics": notes})

    result = run_suite(go_binary, out)
    emitted = [str(row.get("assertion_id")) for row in result["records"]]
    ok("W0902-GO-TEST-SUITE-EXIT-ZERO",
       result["code"] == 0 and not result["timed_out"] and not result["failed"]
       and set(OWNED_TESTS) <= set(result["passed"]),
       "rc=%s timed_out=%s failed=%s passed=%s stderr=%s" % (result["code"], result["timed_out"],
                                                             result["failed"], result["passed"],
                                                             result["stderr_tail"][:200]))
    missing = sorted(set(CARD_IDS) - set(emitted))
    unexpected = sorted(set(emitted) - set(CARD_IDS))
    duplicates = sorted({i for i in emitted if emitted.count(i) > 1})
    not_passing = sorted({str(row.get("assertion_id")) for row in result["records"] if row.get("status") != "PASS"})
    ok("W0902-ROSTER-EMITTED-EQUALS-EXPECTED",
       result["code"] == 0 and not missing and not unexpected and not duplicates and not not_passing
       and not result["malformed"] and len(emitted) == len(CARD_IDS),
       json.dumps({"missing_assertion_ids": missing, "unexpected_assertion_ids": unexpected,
                   "duplicate_assertion_ids": duplicates, "non_passing": not_passing,
                   "malformed": result["malformed"][:3], "emitted": len(emitted),
                   "expected": len(CARD_IDS)}, ensure_ascii=False)[:480])
    for label in missing:
        failures.append({"id": label, "detail": "not emitted by %s" % " ".join(result["argv"])})
    source_ids = declared_in_go_source()
    ok("W0902-ROSTER-GO-SOURCE-EQUALS-EXPECTED", source_ids is not None and source_ids == sorted(CARD_IDS),
       json.dumps({"test_file": GO_TEST_FILE.relative_to(ROOT).as_posix(),
                   "source_only": sorted(set(source_ids or []) - set(CARD_IDS)),
                   "registry_only": sorted(set(CARD_IDS) - set(source_ids or []))}, ensure_ascii=False)[:400])
    absent_classes = {label: sorted(set(rows) - set(emitted)) for label, rows in CLASS_ROWS.items()}
    ok("W0902-EVERY-NEGATIVE-CLASS-HAS-ITS-OWN-WITNESS",
       not any(absent_classes.values()) and all(len(rows) >= 2 for rows in CLASS_ROWS.values()),
       json.dumps(absent_classes, ensure_ascii=False)[:400])
    ok("W0902-CLASSES-ARE-NOT-PROVED-BY-ONE-ROW",
       len({row for rows in CLASS_ROWS.values() for row in rows}) >= 5,
       "the five classes share rows, but no single row may stand for all five")

    evidence_files = ("before.json", "go-test.stdout.jsonl", "go-test.stderr.txt")
    expected_prefix = "execution/v2.4/receipts/W09/W09-02/dispatched/"
    under_card_path = out.relative_to(ROOT).as_posix().startswith(expected_prefix)
    short = [name for name in evidence_files if not (out / name).is_file()]
    empty = [name for name in ("before.json", "go-test.stdout.jsonl")
             if (out / name).is_file() and (out / name).stat().st_size == 0]
    ok("W0902-GO-TEST-EVIDENCE-WRITTEN-UNDER-CARD-DIRECTORY",
       under_card_path and not short and not empty and bool(result["records"]),
       "missing %s empty %s records %d path %s" % (short, empty, len(result["records"]),
                                                   out.relative_to(ROOT).as_posix()))
    note("roster", {"emitted": len(emitted), "expected": len(CARD_IDS), "unique": len(set(emitted)),
                    "harness_rows": len(ids)},
         "assertion_ids below are the card roster plus this handler's own rows")
    note("not_covered", {"count": len(NOT_COVERED)}, json.dumps(NOT_COVERED, ensure_ascii=False)[:900])

    # Last, because a roster-exactness row cannot otherwise see itself: ok() appends the label only
    # when the condition already held, so comparing against the full declared set would fail forever.
    # The declared set therefore excludes this row, and the exclusion is asserted rather than implied.
    expected_harness = sorted(set(HARNESS_IDS) - {"W0902-HARNESS-ROSTER-EXACT"})
    ok("W0902-HARNESS-ROSTER-EXACT", sorted(ids) == expected_harness,
       json.dumps({"emitted_harness": sorted(ids), "expected_harness": expected_harness},
                  ensure_ascii=False)[:400])

    status = "PASS" if not failures else "FAIL"
    report = {"status": status, "task_id": OWNED_TASK, "check_id": OWNED_CHECK,
              "selector": "test.retrieval.revocation --task-id W09 --check-id W09-02",
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE", "measured_at": utc(),
              "go_test": {"exit_code": result["code"], "timed_out": result["timed_out"], "argv": result["argv"],
                          "packages": PACKAGES, "passed_tests": result["passed"], "failed_tests": result["failed"],
                          "assertion_records": len(result["records"]), "malformed": result["malformed"]},
              "assertion_results": result["records"],
              "emitted_assertion_ids": sorted(set(emitted)), "missing_assertion_ids": missing,
              "unexpected_assertion_ids": unexpected, "duplicate_assertion_ids": duplicates,
              "non_passing_assertion_ids": not_passing, "negative_class_absence": absent_classes,
              "routing_self_probe": probe, "harness_assertion_ids": sorted(ids),
              "declared_command_deviation": DECLARED_COMMAND_DEVIATION,
              "not_covered": NOT_COVERED, "failures": failures, "diagnostics": notes,
              "raw_evidence": {name: (out / name).relative_to(ROOT).as_posix() for name in evidence_files},
              "independent_acceptance": "NOT_REQUESTED"}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return emit(status, ids + emitted, failures,
                extra={"missing_assertion_ids": missing, "unexpected_assertion_ids": unexpected,
                       "duplicate_assertion_ids": duplicates, "non_passing_assertion_ids": not_passing,
                       "negative_class_absence": absent_classes, "go_test_exit_code": result["code"],
                       "routing_probe": {k: probe.get(k) for k in ("ran", "exit_code", "status", "assertions",
                                                                   "stdout_lines")},
                       "pinned_go": go_binary, "harness_assertion_ids": sorted(ids),
                       "card_assertion_id_count": len(set(emitted) & set(CARD_IDS)),
                       "receipt_directory": out.relative_to(ROOT).as_posix(),
                       "report_reference": (out / "report.json").relative_to(ROOT).as_posix(),
                       "report_hash": "sha256:" + hashlib.sha256((out / "report.json").read_bytes()).hexdigest(),
                       "not_covered": NOT_COVERED, "diagnostics": notes})


DECLARED_COMMAND_DEVIATION = (
    "The plan declares `test.security --task-id W09 --check-id W09-02` for this card. That key is BOUND at "
    "registry revision 21 with selectors {task_id:[W17], check_id:[W17-01]} and handler `go run ./tests/security/"
    "check`, which is owned by accepted card W17-01 and writable by no card in the W09 line; its program emits host-"
    "boundary ids (BOOT/CRED/IPC/WS/REVOKE) with no check-id routing. Dispatching the declared selector therefore "
    "refuses at the selector check with zero assertions, and appending this card's selector to that key would have it "
    "answer a W09 dispatch with W17's roster - a fabricated PASS. This card's rows are served from a handler inside "
    "its own write_scope instead, under a new key, and the deviation plus the measured refusal are carried in the "
    "receipt for the independent reviewer to judge.")
HARNESS_IDS = [
    "W0902-CLASSES-ARE-NOT-PROVED-BY-ONE-ROW",
    "W0902-EVERY-NEGATIVE-CLASS-HAS-ITS-OWN-WITNESS",
    "W0902-GO-TEST-EVIDENCE-WRITTEN-UNDER-CARD-DIRECTORY",
    "W0902-GO-TEST-SUITE-EXIT-ZERO",
    "W0902-HARNESS-ROSTER-EXACT",
    "W0902-REFUSED-BINDINGS-LEAVE-NO-DIRECTORY-BEHIND",
    "W0902-ROUTING-BINDING-SERVED",
    "W0902-ROUTING-FOREIGN-BINDING-REFUSED",
    "W0902-ROUTING-TRUTH-TABLE",
    "W0902-ROSTER-EMITTED-EQUALS-EXPECTED",
    "W0902-ROSTER-GO-SOURCE-EQUALS-EXPECTED",
    "W0902-TOOLCHAIN-GO-FROM-LOCKED-TABLE",
    "W0902-TOOLCHAIN-NEVER-FALLS-BACK-TO-PATH",
    "W0902-TOOLCHAIN-REFUSES-A-REAL-BUT-WRONG-BINARY",
]


def main():
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    if route(task, check, case) != "serve":
        return refuse("this handler answers only W09/W09-02; observed task_id=%r check_id=%r case_id=%r"
                      % (task, check, case), (task, check, case))
    # Created lazily, immediately before the first write: W09-01 disclosed 694 empty directories
    # left behind by a receipt root that was made before the run knew whether it would write.
    out = RECEIPT_ROOT / str(uuid.uuid4())
    out.mkdir(parents=True, exist_ok=False)
    try:
        return serve(out)
    except Exception as exc:
        # A crash is never a PASS and never borrows another row's name.
        return emit("FAIL", [], [{"id": "W0902-HANDLER-CRASHED",
                                  "detail": "%s: %s" % (type(exc).__name__, str(exc)[:400])}],
                    extra={"receipt_directory": out.relative_to(ROOT).as_posix()})


if __name__ == "__main__":
    sys.exit(main())
