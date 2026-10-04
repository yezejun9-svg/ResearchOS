"""W07-01 construction check: two real source kinds over pinned question windows, and a cursor that only moves
after the page lands in the database.

Modes, exactly one selector each (the dispatcher forwards the selector environment verbatim):
  --check-id W07-01                     run this program's own phases
  --check-id W07-G01|W07-G02, case A05  forwarded unchanged to ops/ci/sources.py, which owns those rows

Nothing here is formal product acceptance. The live phases read the real public GitHub and arXiv endpoints, so
FIXTURE and LIVE_SERVICE evidence are recorded separately, a capture that cannot reach the service has to fail
loudly (or be disclosed as a blocked resource with the message the service actually returned), and every run
uses its own fresh database so an earlier capture cannot make a later one look green.
"""
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LOCKED = os.path.join("execution", "toolchains", "locked.json")
LIVE_PKG = "./tests/sources/live"
ADAPTER_DIR = os.path.join("adapters", "sources")
LEGACY_ARGS = [sys.executable, "-X", "utf8", "ops/ci/sources.py"]
REQUIRED_ITEM_FIELDS = ("url", "author", "published_at", "retrieved_at", "upstream_revision",
                        "body_sha256", "artifact_ref", "evidence_id", "locator")

# Each card action is carried by named tests that already exist in the accepted adapter suite. Naming them (rather
# than counting green tests) is what keeps reuse honest: a renamed or deleted guard shows up as a missing id
# instead of a phase that still passes.
ACTION_TESTS = {
    "W0701-ACTION-CURSOR-AFTER-PERSISTENCE": [
        "TestW07CursorDoesNotAdvanceFailedOrUnpersistedWindow",
        "TestW07HTTPSourceEvidenceAndDurableEmptyWindow"],
    "W0701-ACTION-RETRY-DEDUP-KEEPS-SOURCES": [
        "TestW07RetryAfterPreventsPrematureSourceRequest",
        "TestW07Provider429PersistsRetryBeforeAnotherFetch"],
    "W0701-ACTION-EMPTY-VS-FAILURE-DISTINCTIONS": [
        "TestW07GitHubEmptyAuthAndTimeoutAreDistinct",
        "TestW07ArxivErrorPageIsNotValidEmptyFeed",
        "TestW07XVisibleEmptyDiffersFromUnrendered"],
    "W0701-ACTION-EXTERNAL-TEXT-INERT": [
        "TestW07GitHubRejectsForeignRedirectBeforeRequest",
        "TestW07ArxivRejectsForeignRedirectBeforeRequest",
        "TestW07EvidenceNeedsSealedLiveSnapshotAndAllowedOrigin"],
    "W0701-ACTION-NO-SECOND-SCHEDULER": [
        "TestW07MissingAuthorizedXChannelDoesNotFetch",
        "TestW07XOnlyPublicPostAndNoFalseComplete"],
}
KINDS = {
    "GITHUB": ("W0701-GITHUB-LIVE-READ", "W0701-GITHUB-EVIDENCE-FIELDS", "W0701-GITHUB-CURSOR-ADVANCED"),
    "PAPER": ("W0701-PAPER-LIVE-READ", "W0701-PAPER-EVIDENCE-FIELDS", "W0701-PAPER-CURSOR-ADVANCED"),
}


def locked_go():
    try:
        return json.loads(io.open(os.path.join(ROOT, LOCKED), encoding="utf-8-sig").read())["tools"]["go"]
    except Exception:
        return None


def resolve_go(tools):
    """Absolute pinned binary verified by hash and version output, or nothing. Never a PATH lookup."""
    if not tools:
        return None, None, "the locked toolchain table could not be read"
    path = tools.get("path")
    if not path or not os.path.isabs(path) or not os.path.isfile(path):
        return None, None, "the pinned go binary is absent: %r" % path
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != tools.get("sha256"):
        return None, None, "the pinned go binary hash does not match the locked table"
    argv = [path] + list(tools.get("version_argv") or ["version"])
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=60)
    except Exception as exc:
        return None, None, "the pinned go could not report its version: %s" % exc
    version = (r.stdout or "").strip()
    if r.returncode != 0 or version != tools.get("version_output"):
        return None, None, "the pinned go reports %r while the table says %r" % (version, tools.get("version_output"))
    return path, version, "verified"


def routing(task, check, case):
    if task == "W07" and check == "W07-01" and not case:
        return "local"
    if task == "W07" and check in ("W07-G01", "W07-G02") and not case:
        return "legacy"
    if task == "W07" and case == "A05" and not check:
        return "legacy"
    return "refuse"


def forward(task, check, case):
    env = dict(os.environ, RESEARCHOS_TASK_ID=task, RESEARCHOS_CHECK_ID=check, RESEARCHOS_CASE_ID=case)
    p = subprocess.run(LEGACY_ARGS, capture_output=True, text=True, timeout=1800, encoding="utf-8",
                       errors="replace", env=env, cwd=ROOT)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    return (json.loads(lines[-1]) if lines else None), p.returncode


def declared_ids():
    source = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    # Every quoted W0701-* token is part of the roster EXCEPT the ones that name a failure of another exit path
    # (`{"id": "W0701-SELECTORS-REQUIRED"}` inside the refuse branch), which a normal run can never emit.
    return sorted(set(re.findall(r'(?<!"id": )"(W0701-[A-Z0-9-]+)"', source)))


def emit(ids, failures, not_verified, diagnostics, extra=None):
    if len(ids) != len(set(ids)):
        failures.append({"id": "W0701-ASSERTION-IDS-UNIQUE",
                         "detail": "duplicated: %s" % sorted({i for i in ids if ids.count(i) > 1})})
    else:
        ids.append("W0701-ASSERTION-IDS-UNIQUE")
    declared = set(declared_ids())
    emitted = set(ids) | {f["id"] for f in failures} | {n.split(":")[0] for n in not_verified}
    never = sorted(declared - emitted - {"W0701-ASSERTION-IDS-UNIQUE", "W0701-ROSTER-DECLARED-IDS-ALL-EMITTED",
                                         "W0701-ROSTER-EMITTED-IDS-ALL-DECLARED"})
    undeclared = sorted(emitted - declared)
    if never:
        failures.append({"id": "W0701-ROSTER-DECLARED-IDS-ALL-EMITTED", "detail": ", ".join(never)})
    else:
        ids.append("W0701-ROSTER-DECLARED-IDS-ALL-EMITTED")
    if undeclared:
        failures.append({"id": "W0701-ROSTER-EMITTED-IDS-ALL-DECLARED", "detail": ", ".join(undeclared)})
    else:
        ids.append("W0701-ROSTER-EMITTED-IDS-ALL-DECLARED")
    status = "PASS" if not failures else "FAIL"
    report = {"status": status, "assertions": len(set(ids)), "assertion_ids": sorted(set(ids)),
              "failures": failures, "not_verified": not_verified, "diagnostics": diagnostics,
              "task_id": "W07", "check_id": "W07-01", "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
              "forwarded": "W07-G01/W07-G02/A05 go to ops/ci/sources.py unchanged"}
    if extra:
        report.update(extra)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


def cursor_persisted(db_path, cursor_id):
    """Read the authoritative SourceCursor back out of the live database the probe just wrote.

    domain_objects carries the current body and domain_versions the whole history, so the same read can show that
    the cursor existed with covered_until null before the advance - which is the difference between 'the page
    landed and then the window moved' and 'the window moved regardless'.
    """
    real = db_path if os.path.isabs(db_path) else os.path.join(ROOT, db_path)
    if not cursor_id or not os.path.isfile(real):
        return {"reason": "no database at %s" % real}
    con = sqlite3.connect("file:" + real.replace("\\", "/") + "?mode=ro", uri=True)
    try:
        current = con.execute("SELECT kind, revision, body FROM domain_objects WHERE id=?", (cursor_id,)).fetchone()
        if not current:
            return {"reason": "cursor id absent from domain_objects"}
        kind, revision, body = current
        row = json.loads(body)
        history = con.execute("SELECT revision, body FROM domain_versions WHERE id=? ORDER BY revision",
                              (cursor_id,)).fetchall()
        versions = [{"revision": r, "covered_until": json.loads(b).get("covered_until"),
                     "pending_window_from": json.loads(b).get("pending_window_from")} for r, b in history]
        advances = con.execute("SELECT COUNT(*) FROM idempotency WHERE operation LIKE '%ourceCursor%'").fetchone()[0]
        return {"found": True, "kind": kind, "revision": revision, "covered_until": row.get("covered_until"),
                "opaque_cursor": row.get("opaque_cursor"), "pending_window_from": row.get("pending_window_from"),
                "versions": versions, "cursor_advance_records": advances}
    finally:
        con.close()


def main():
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    decision = routing(task, check, case)
    if decision == "legacy":
        rep, rc = forward(task, check, case)
        print(json.dumps(rep if rep else {"status": "COMMAND_FAILED", "assertions": 0,
                                          "note": "the forwarded sources harness produced no report"},
                         ensure_ascii=False))
        return rc
    if decision == "refuse":
        print(json.dumps({"status": "COMMAND_FAILED", "assertions": 0, "assertion_ids": [],
                          "failures": [{"id": "W0701-SELECTORS-REQUIRED",
                                        "detail": "pass --check-id W07-01, or a gate/case selector this program "
                                                  "forwards to ops/ci/sources.py"}],
                          "not_verified": [], "diagnostics": [],
                          "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}, ensure_ascii=False))
        return 1

    ids, failures, diagnostics, not_verified = [], [], [], []

    def ok(label, cond, detail=None):
        if cond:
            ids.append(label)
        else:
            failures.append({"id": label, "detail": str(detail)[:500]})

    def note(probe, observed, detail):
        diagnostics.append({"probe": probe, "observed": observed, "detail": str(detail)[:300]})

    def skip(label, reason):
        not_verified.append(label + ": " + reason)

    run_dir = os.path.join(".local", "w0701-evidence", str(uuid.uuid4()))
    os.makedirs(os.path.join(ROOT, run_dir), exist_ok=True)
    tools = locked_go()
    go_bin, go_version, go_reason = resolve_go(tools)
    ok("W0701-TOOLCHAIN-GO-FROM-LOCKED-TABLE", go_bin is not None, go_reason)
    ok("W0701-TOOLCHAIN-GO-PATH-FALLBACK-IS-REFUSED",
       resolve_go({"path": os.path.join(ROOT, "no", "such", "go.exe"), "sha256": "0" * 64,
                   "version_argv": ["version"], "version_output": "go0"})[0] is None,
       "positive control: a table naming an absent binary must yield no executable, not a PATH name")
    note("pinned-go", go_version, "every number below came from the locked go %s, not a PATH toolchain" % go_version)

    if go_bin is None:
        for label in declared_ids():
            if label not in set(ids) | {f["id"] for f in failures}:
                skip(label, "the pinned go is unavailable (%s), so the suite, the live probe and the negative "
                            "control could not be executed" % go_reason)
        return emit(ids, failures, not_verified, diagnostics)

    # Phase 1 - reuse the accepted adapter suite, graded per card action rather than as one blanket green.
    argv = [go_bin, "test", "-count=1", "-json", "-run", "^TestW07",
            "./adapters/sources", "./internal/domain", "./tests/sources/live"]
    suite = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, GOFLAGS="-mod=mod"), cwd=ROOT, timeout=900)
    seen, failed = set(), set()
    for line in (suite.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("Action") == "run":
            seen.add(ev.get("Test", ""))
        elif ev.get("Action") == "output" and ev.get("Test") and ev.get("Data", "").startswith("--- FAIL"):
            failed.add(ev["Test"])
    note("adapter-suite", {"rc": suite.returncode, "tests_seen": len(seen), "failed": sorted(failed)[:6]},
         "this is the accepted W07 adapter contract; the card reuses it instead of re-implementing it")
    for label, required in ACTION_TESTS.items():
        missing = [t for t in required if t not in seen]
        broken = [t for t in required if t in failed]
        ok(label, suite.returncode == 0 and not missing and not broken,
           "missing %s failed %s rc %s" % (missing, broken, suite.returncode))

    # Phase 2 - two real captures, each in its own fresh database and evidence directory.
    binary = os.path.join(run_dir, "w0701-live.exe" if os.name == "nt" else "w0701-live")
    builds = subprocess.run([go_bin, "build", "-o", binary, LIVE_PKG], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=dict(os.environ, GOFLAGS="-mod=mod"),
                            cwd=ROOT, timeout=600)
    ok("W0701-LIVE-PROBE-BUILDS", builds.returncode == 0, (builds.stderr or builds.stdout)[:400])
    captures = {}
    window_rows = []
    if builds.returncode == 0:
        for kind in KINDS:
            env = dict(os.environ, RESEARCHOS_SOURCE_KIND=kind,
                       RESEARCHOS_SOURCE_OUTPUT_DIR=os.path.abspath(os.path.join(ROOT, run_dir)))
            started = time.monotonic()
            r = subprocess.run([os.path.abspath(binary)], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env, cwd=ROOT, timeout=300)
            path = os.path.join(ROOT, run_dir, "report-" + kind + ".json")
            captures[kind] = {"rc": r.returncode, "seconds": round(time.monotonic() - started, 2),
                              "report": json.loads(io.open(path, encoding="utf-8").read())
                              if os.path.isfile(path) else None,
                              "stderr": (r.stderr or "")[-300:], "stdout": (r.stdout or "")[-300:]}

    blocked_kinds = []
    for kind, (read_id, fields_id, cursor_id) in KINDS.items():
        got = captures.get(kind)
        if not got:
            for label in (read_id, fields_id, cursor_id):
                skip(label, "the live probe binary did not build, so no capture was attempted")
            continue
        rep = got.get("report") or {}
        items = rep.get("items") or []
        reason_text = " ".join([str(rep.get("reason") or ""), got["stderr"], got["stdout"]])
        rate_limited = bool(re.search(r"(?i)(rate[ _-]?limit|403|secondary rate|api rate)", reason_text))
        if rate_limited:
            blocked_kinds.append((kind, reason_text[:200]))
            for label in (read_id, fields_id, cursor_id):
                skip(label, "the public endpoint refused the request before any item could be read: %s" %
                     reason_text[:200])
            continue
        ok(read_id, got["rc"] == 0 and rep.get("status") == "PASS" and rep.get("scope") == "LIVE_SERVICE" and
           bool(items) and rep.get("window_from") and rep.get("window_to") and rep.get("cursor_id"),
           json.dumps({"rc": got["rc"], "status": rep.get("status"), "scope": rep.get("scope"),
                       "seconds": got["seconds"], "reason": reason_text[:200]}, ensure_ascii=False))
        incomplete = [i.get("url") for i in items if not all(i.get(f) for f in REQUIRED_ITEM_FIELDS)]
        hashes_bad = [i.get("url") for i in items
                      if not re.fullmatch(r"(sha256:)?[0-9a-f]{64}", str(i.get("body_sha256") or ""))]
        redirected = [a for a, b in zip(rep.get("request_urls") or [], rep.get("final_urls") or []) if a != b]
        ok(fields_id, bool(items) and not incomplete and not hashes_bad and not redirected and
           rep.get("raw_page") and rep.get("manifest"),
           json.dumps({"incomplete": incomplete, "hashes_bad": hashes_bad, "redirected": redirected},
                      ensure_ascii=False)[:400])
        stored = cursor_persisted(rep.get("db_path"), rep.get("cursor_id"))
        versions = stored.get("versions") or []
        # Two legitimate endings, and only these two. A complete page moves the covered window; an incomplete page
        # leaves the window pending and keeps covered_until exactly where it was. Anything else - a covered window
        # the probe did not finish reading - is the defect the card names.
        complete_ok = (rep.get("page_complete") is True and bool(stored.get("covered_until")) and
                       any(v.get("covered_until") is None for v in versions))
        partial_ok = (rep.get("page_complete") is False and bool(stored.get("pending_window_from")) and
                      stored.get("covered_until") is None and bool(stored.get("opaque_cursor")))
        branch = "complete" if complete_ok else ("pending" if partial_ok else "neither")
        ok(cursor_id, stored.get("found") is True and stored.get("kind") == "SourceCursor" and
           (complete_ok or partial_ok),
           json.dumps({"branch": branch, "report_page_complete": rep.get("page_complete"),
                       "stored": stored}, ensure_ascii=False, default=str)[:500])
        note("cursor-branch-" + kind, branch,
             "complete = window covered after a full page; pending = more pages remain so the window must not move")
        window_rows.append((kind, rep.get("page_complete"), stored.get("covered_until"),
                            stored.get("pending_window_from")))
        note("capture-" + kind, {"seconds": got["seconds"], "items": len(items),
                                 "request": (rep.get("request_urls") or [None])[0],
                                 "window": [rep.get("window_from"), rep.get("window_to")]},
             "real service read, own fresh database, no idempotency carry-over")

    # Across both kinds, one invariant must hold with no exception: a cursor may report a covered window only when
    # the page that covered it was complete. GitHub lands in the pending branch and arXiv in the complete branch,
    # so this row is measured against two different shapes rather than against one lucky case.
    over_claimed = [r for r in window_rows if r[2] and r[1] is not True]
    ok("W0701-NO-WINDOW-COVERED-WITHOUT-A-COMPLETE-PAGE",
       not over_claimed and len(window_rows) == len(captures) and
       any(r[1] is True for r in window_rows) and any(r[1] is False for r in window_rows),
       json.dumps({"over_claimed": over_claimed, "rows": window_rows, "captures": len(captures)},
                  ensure_ascii=False, default=str)[:400])

    # Phase 3 - the negative control that keeps phase 2 from being vacuous: the same binary, the same window,
    if builds.returncode == 0 and captures:
        env = dict(os.environ, RESEARCHOS_SOURCE_KIND="GITHUB",
                   RESEARCHOS_SOURCE_OUTPUT_DIR=os.path.abspath(os.path.join(ROOT, run_dir, "blocked")),
                   HTTPS_PROXY="http://127.0.0.1:9", https_proxy="http://127.0.0.1:9", NO_PROXY="")
        os.makedirs(os.path.join(ROOT, run_dir, "blocked"), exist_ok=True)
        started = time.monotonic()
        dead = subprocess.run([os.path.abspath(binary)], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=env, cwd=ROOT, timeout=300)
        path = os.path.join(ROOT, run_dir, "blocked", "report-GITHUB.json")
        dre = json.loads(io.open(path, encoding="utf-8").read()) if os.path.isfile(path) else {}
        stored = cursor_persisted(dre.get("db_path"), dre.get("cursor_id")) if dre.get("cursor_id") else {}
        advanced = bool(stored.get("found") and stored.get("covered_until"))
        ok("W0701-UNREACHABLE-SOURCE-DOES-NOT-ADVANCE-THE-CURSOR",
           (dead.returncode != 0 or dre.get("status") != "PASS") and not advanced,
           json.dumps({"rc": dead.returncode, "status": dre.get("status"), "advanced": advanced,
                       "stored": stored, "stderr": (dead.stderr or "")[-200:]}, ensure_ascii=False, default=str))
        note("unreachable-control", {"rc": dead.returncode, "seconds": round(time.monotonic() - started, 2),
                                     "status": dre.get("status")},
             "only the proxy changed; the happy-path green is only meaningful because this one fails")
    else:
        skip("W0701-UNREACHABLE-SOURCE-DOES-NOT-ADVANCE-THE-CURSOR",
             "the live probe did not build, so the unreachable-endpoint control could not be run")

    # Phase 4 - no second watchlist scheduler: the observable form is that each capture process terminates on its
    # own well inside the timeout. An unbounded poller would have hit the 300s subprocess timeout instead.
    slowest = max([g["seconds"] for g in captures.values()] + [0])
    ok("W0701-CAPTURE-PROCESSES-TERMINATE-WITHOUT-A-SCHEDULER", 0 < slowest < 120,
       "slowest capture %.1fs" % slowest)
    pollers = {}
    for f in sorted(os.listdir(os.path.join(ROOT, ADAPTER_DIR))):
        if not f.endswith(".go") or f.endswith("_test.go"):
            continue
        text = io.open(os.path.join(ROOT, ADAPTER_DIR, f), encoding="utf-8").read()
        hits = re.findall(r"time\.(NewTicker|Tick)\(", text)
        if hits:
            pollers[f] = hits
    note("adapter-ticker-scan", pollers,
         "a ticker inside an adapter would be the second scheduler the card forbids; reported beside the "
         "behavioural proof above rather than asserted on its own")

    skip("W0701-X-SOURCE-LIVE-CAPTURE",
         "this card names GitHub and paper sources; the same probe's X kind needs an authorized BrowserAct tool "
         "and browser id (RESEARCHOS_BROWSER_ACT / RESEARCHOS_BROWSER_ID), which this environment does not "
         "provide, so the forwarded A05/C19 branch of ops/ci/sources.py reports BLOCKED for it. Owed by that "
         "case's owner, not by this card")
    skip("W0701-LIVE-DEDUPLICATE-ACROSS-REPOSTS",
         "repost and duplicate-page deduplication is asserted by the reused fixture tests "
         "(W0701-ACTION-RETRY-DEDUP-KEEPS-SOURCES), not against the live endpoints, because the pinned probe "
         "reads exactly one positive item per page and a second live fetch of the same window would re-read that "
         "same item rather than exercise a duplicate")

    return emit(ids, failures, not_verified, diagnostics,
                extra={"pinned_go": go_version, "evidence_run_dir": run_dir,
                       "blocked_kinds": blocked_kinds,
                       "captures": {k: {"status": (v.get("report") or {}).get("status"),
                                        "scope": (v.get("report") or {}).get("scope"),
                                        "items": len((v.get("report") or {}).get("items") or []),
                                        "seconds": v["seconds"]} for k, v in captures.items()}})


if __name__ == "__main__":
    sys.exit(main())
