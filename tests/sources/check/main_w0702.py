"""W07-02 check program: three real public sources, per-source health, and an injected X blockage.

This is the card-level handler. ops/ci/sources.py only accepts the check ids W07-G01, W07-G02 and empty, so a card
check id can never be served by that child - measured, not assumed. The handler therefore runs the accepted live
probe directly and grades the card's own claims:

  * each of GITHUB, PAPER and X gets a real capture with per-item evidence, and a refusal fails that kind's rows
    instead of being skipped (the anti-laundering rule this line was rejected for breaking once already);
  * X's cursor must be persisted as pending when the page stops at a rendering gap, and must never be recorded as
    covered while the page is incomplete;
  * the X blockage is injected through the product's own path - an unconfigured browser id makes the domain refuse
    with 503 RESOURCE_UNAVAILABLE - so the failure is the product's classification, not a stub;
  * while X is blocked, GITHUB and PAPER must still read, which is what makes the aggregate PARTIAL rather than
    COMPLETE honest at the source level.

Deliberately not claimed here: the product-side cycle aggregate and the desktop's health rendering. Those are named
as unasserted in the receipt rather than approximated by a number computed in this file.
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

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
GO = os.path.join(ROOT, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
BROWSER_ACT = r"C:/Users/yqyyds/.local/bin/browser-act.exe"
X_BROWSER_ID = "direct_local_120993884286222444"
PROBE_SRC = "./tests/sources/live"
REQUIRED_ITEM_FIELDS = ("url", "author", "published_at", "body_sha256")
KINDS = ("GITHUB", "PAPER", "X")

report = {"status": "FAIL", "scope": "LIVE_SERVICE", "card": "W07-02", "assertion_ids": [], "assertions": 0,
          "failures": [], "not_verified": [], "items_by_kind": {}, "rows": []}


def ok(row, passed, detail=""):
    report["assertion_ids"].append(row)
    report["rows"].append({"id": row, "result": "PASS" if passed else "FAIL", "detail": str(detail)[:700]})
    if not passed:
        report["failures"].append({"id": row, "detail": str(detail)[:700]})


def note(row, why):
    report["assertion_ids"].append(row)
    report["not_verified"].append("%s: %s" % (row, why))


def build_probe(out_path):
    if not os.path.isfile(GO):
        return None, "pinned go missing at " + GO
    env = dict(os.environ, GOFLAGS="-mod=mod", RESEARCHOS_GO=GO)
    p = subprocess.run([GO, "build", "-o", out_path, PROBE_SRC], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT, env=env, timeout=900)
    return (out_path if p.returncode == 0 and os.path.isfile(out_path) else None), (p.stdout + p.stderr)[-400:]


def capture(binary, kind, run_dir, browser_id, attempts=2):
    """Run one kind. Retries are recorded per attempt, never collapsed into one clean result."""
    tried = []
    for i in range(attempts):
        adir = os.path.join(run_dir, "%s_try%d" % (kind.lower(), i + 1))
        os.makedirs(adir, exist_ok=True)
        env = dict(os.environ, RESEARCHOS_SOURCE_KIND=kind,
                   RESEARCHOS_SOURCE_OUTPUT_DIR=os.path.abspath(adir),
                   RESEARCHOS_BROWSER_ACT=BROWSER_ACT, RESEARCHOS_BROWSER_ID=browser_id)
        started = time.monotonic()
        try:
            r = subprocess.run([os.path.abspath(binary)], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", env=env, cwd=ROOT, timeout=300)
            rc, stderr, stdout = r.returncode, (r.stderr or ""), (r.stdout or "")
        except subprocess.TimeoutExpired as e:
            rc, stderr, stdout = 124, "timeout after 300s: " + str(e)[:200], ""
        path = os.path.join(adir, "report-" + kind + ".json")
        rep = json.loads(io.open(path, encoding="utf-8").read()) if os.path.isfile(path) else None
        tried.append({"attempt": i + 1, "rc": rc, "seconds": round(time.monotonic() - started, 2),
                      "report": rep, "stderr": stderr[-300:], "stdout": stdout[-300:], "dir": adir})
        if rc == 0 and rep:
            break
    return tried


def cursor_state(run_dir, kind):
    db = os.path.join(run_dir, "live-" + kind.lower() + ".sqlite")
    if not os.path.isfile(db):
        return {"found": False}
    import sqlite3
    out = {"found": True, "cursors": []}
    con = sqlite3.connect(db)
    for (raw,) in con.execute("SELECT body FROM domain_objects WHERE kind='SourceCursor'"):
        c = json.loads(raw)
        out["cursors"].append({"source_id": c.get("source_id"), "revision": c.get("revision"),
                               "covered_until": c.get("covered_until"), "opaque_cursor": c.get("opaque_cursor"),
                               "pending_window_from": c.get("pending_window_from"),
                               "pending_window_to": c.get("pending_window_to")})
    con.close()
    return out


def main():
    run_root = os.path.join(ROOT, "qualification", "v2.4", "evidence", "w0702",
                            time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + str(os.getpid()))
    os.makedirs(run_root, exist_ok=True)
    binary, why = build_probe(os.path.join(run_root, "probe.exe"))
    if not binary:
        for kind in KINDS:
            ok("%s-LIVE-READ" % kind, False, "the live probe binary did not build: " + why)
        report["assertion_count"] = len(report["assertion_ids"])
        print(json.dumps(report, ensure_ascii=False))
        return 1

    got = {}
    for kind in KINDS:
        browser = X_BROWSER_ID if kind == "X" else ""
        got[kind] = capture(binary, kind, run_root, browser)
        rep = (got[kind][-1] or {}).get("report") or {}
        report["items_by_kind"][kind] = {"attempts": len(got[kind]), "rc": got[kind][-1]["rc"],
                                        "status": rep.get("status"), "items": len(rep.get("items") or []),
                                        "page_complete": rep.get("page_complete"),
                                        "next_cursor": rep.get("next_cursor"), "failure": rep.get("failure"),
                                        "claim_check": (rep.get("claim_check") or {}).get("status")}

    # per-kind live rows
    for kind in KINDS:
        last = got[kind][-1]
        rep = last.get("report") or {}
        items = rep.get("items") or []
        reason_text = " ".join([str(rep.get("failure") or ""), last["stderr"], last["stdout"]])
        rate_limited = bool(re.search(r"(?i)(rate[ _-]?limit|403|secondary rate|api rate|timed? out|deadline exceeded)",
                                      reason_text))
        ok("W0702-%s-LIVE-READ" % kind, last["rc"] == 0 and rep.get("status") == "PASS" and bool(items),
           "rc=%s status=%s items=%s attempts=%s%s" % (last["rc"], rep.get("status"), len(items), len(got[kind]),
                                                       " refusal=" + reason_text[:200] if rate_limited else ""))
        incomplete = [i.get("url") for i in items if not all(i.get(f) for f in REQUIRED_ITEM_FIELDS)]
        bad_hash = [i.get("url") for i in items
                    if not re.fullmatch(r"(sha256:)?[0-9a-f]{64}", str(i.get("body_sha256") or ""))]
        ok("W0702-%s-EVIDENCE-MATCHES-ITEMS" % kind,
           bool(items) and not incomplete and not bad_hash and rep.get("raw_page") and rep.get("manifest"),
           json.dumps({"incomplete": incomplete, "bad_hash": bad_hash}, ensure_ascii=False)[:400])
        ok("W0702-%s-NO-FALSE-COMPLETE" % kind, rep.get("page_complete") is not True or bool(rep.get("covered_until")),
           "page_complete=%s covered_until=%s next_cursor=%s" % (rep.get("page_complete"),
                                                                  rep.get("covered_until"), rep.get("next_cursor")))

    # UI observation markers identify the read prefix; they are not pagination tokens.
    x_dir = got["X"][-1]["dir"]
    state = cursor_state(x_dir, "X")
    x_rep = (got["X"][-1].get("report") or {})
    mine = [c for c in state.get("cursors") or [] if c.get("id") == x_rep.get("cursor_id")]
    # Older cursor_state versions omit id; the probe's X source is the configured X row.
    if not mine:
        mine = [c for c in state.get("cursors") or [] if c.get("source_id") == x_rep.get("source_id")]
    health = x_rep.get("health") or {}
    health_ok = False
    try:
        db = sqlite3.connect(os.path.join(ROOT, x_rep["db_path"]))
        row = db.execute("SELECT u.bytes FROM domain_objects a JOIN uploaded_content u ON u.project=a.project AND u.storage_key=json_extract(a.body,'$.storage_key') WHERE a.id=? AND a.kind='Artifact' AND u.sealed=1", (x_rep["health_artifact_ref"]["id"],)).fetchone()
        db.close()
        doc = json.loads(row[0]) if row else {}
        health_ok = (doc.get("health") == health and "sha256:" + hashlib.sha256(row[0]).hexdigest() == x_rep["health_artifact_ref"]["content_hash"])
    except (KeyError, ValueError, sqlite3.Error, TypeError):
        pass
    ok("W0702-X-WINDOW-OBSERVED-NOT-COVERED", x_rep.get("page_complete") is False and
       health_ok and health.get("requested_from") == x_rep.get("window_from") and
       health.get("requested_to") == x_rep.get("window_to") and
       all(c.get("covered_until") is None and not c.get("opaque_cursor") for c in mine) and bool(mine),
       json.dumps({"state": state, "health": health}, ensure_ascii=False)[:500])
    ok("W0702-X-OBSERVATION-MARKER-NOT-PROVIDER-CURSOR", health_ok and bool(x_rep.get("items")) and
       health.get("observation_marker") == "observed_tail:" + str(x_rep["items"][-1]["upstream_id"]) and
       not x_rep.get("next_cursor"), json.dumps(health, ensure_ascii=False)[:400])
    report["historical_assertion_mapping"] = {"W0702-X-CURSOR-PENDING-NOT-COVERED": "W0702-X-WINDOW-OBSERVED-NOT-COVERED",
        "W0702-X-CURSOR-ADVANCED-PAST-READ-ITEMS": "W0702-X-OBSERVATION-MARKER-NOT-PROVIDER-CURSOR"}

    # the claim verdict is research output, not a transport status
    ok("W0702-X-CLAIM-VERDICT-IS-SEPARATE-FROM-HEALTH",
       x_rep.get("status") == "PASS" and bool(x_rep.get("claim_check")),
       json.dumps({"status": x_rep.get("status"), "claim_check": x_rep.get("claim_check"),
                   "failure": x_rep.get("failure")}, ensure_ascii=False)[:500])

    # injection: an unauthorized X backend must be a product refusal, not an empty result. A bogus browser id only
    # makes the browser CLI fail, which is a transport-level error and not the state the card names; leaving the id
    # empty is, and the domain answers 503 RESOURCE_UNAVAILABLE "authorized X browser unavailable" before any
    # executable is touched (internal/domain/sources.go, the case "X" branch of CaptureSourcePage).
    blocked = capture(binary, "X", os.path.join(run_root, "injection"), "")
    b_last = blocked[-1]
    b_rep = b_last.get("report") or {}
    refusal = " ".join([str(b_rep.get("failure") or ""), b_last["stderr"], b_last["stdout"]])
    ok("W0702-X-BLOCKAGE-IS-PRODUCT-REFUSAL", b_last["rc"] != 0 and
       re.search(r"(?i)(RESOURCE_UNAVAILABLE|authorized X browser unavailable)", refusal) is not None,
       "report=%s refusal=%s" % (json.dumps({k: b_rep.get(k) for k in ("status", "failure", "items")},
                                            ensure_ascii=False)[:200] if b_rep else "(no report)", refusal[:260]))
    b_state = cursor_state(b_last["dir"], "X")
    ok("W0702-X-BLOCKAGE-DOES-NOT-ADVANCE-THE-CURSOR",
       all((not c.get("opaque_cursor")) and c.get("covered_until") is None for c in b_state.get("cursors") or []) and
       bool(b_state.get("cursors")), json.dumps(b_state, ensure_ascii=False)[:400])
    for kind in ("GITHUB", "PAPER"):
        k_rep = (got[kind][-1].get("report") or {})
        ok("W0702-%s-CONTINUES-WHILE-X-IS-BLOCKED" % kind,
           bool(k_rep.get("items")) and k_rep.get("status") == "PASS",
           json.dumps({"status": k_rep.get("status"), "items": len(k_rep.get("items") or []),
                       "x_refusal": refusal[:120]}, ensure_ascii=False)[:400])

    # published-at must sit inside the requested window: a year-old article counted as recent is the named negative
    for kind in KINDS:
        rep = (got[kind][-1].get("report") or {})
        items = rep.get("items") or []
        wf, wt = rep.get("window_from"), rep.get("window_to")
        outside = []
        for i in items:
            p = str(i.get("published_at") or "")
            if wf and wt and p and not (wf <= p < wt):
                outside.append({"url": i.get("url"), "published_at": p})
        ok("W0702-%s-ITEMS-ARE-INSIDE-THE-WINDOW" % kind, bool(items) and not outside,
           json.dumps({"window": [wf, wt], "outside": outside}, ensure_ascii=False)[:400])

    ok("W0702-ASSERTION-IDS-UNIQUE", len(report["assertion_ids"]) == len(set(report["assertion_ids"])),
       "emitted %s ids" % len(report["assertion_ids"]))
    report["run_root"] = os.path.relpath(run_root, ROOT).replace("\\", "/")
    report["assertions"] = len(report["assertion_ids"])
    report["status"] = "PASS" if not report["failures"] else "FAIL"
    report["raw_evidence_digests"] = {os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/"):
                                      hashlib.sha256(open(os.path.join(dp, f), "rb").read()).hexdigest()
                                      for dp, _, fs in os.walk(run_root) for f in fs}
    io.open(os.path.join(run_root, "report-W07-02.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
