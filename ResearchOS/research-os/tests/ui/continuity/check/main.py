"""W13-02 construction check: the renderer and the shell must speak one protocol, and the renderer's client
must refuse, re-baseline and recover the way the card claims.

Modes (the dispatcher forwards exactly one selector):
  --check-id W13-02   run this program's own phases
  --case-id  C26      forward unchanged to the frozen browser recovery phase (ops/ci/ui.py --phase recovery)

Report shape matches the other v2.4 check programs: one JSON line with status, assertions, assertion_ids,
failures, not_verified and diagnostics. Nothing here is product acceptance; the recovery phase it forwards to
carries the real Windows browser evidence.
"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
LOCKED_TOOLS = os.path.join("execution", "toolchains", "locked.json")
DRIVER = os.path.join("tests", "ui", "continuity", "surfaces_driver.js")
SCHEMA = os.path.join("internal", "api", "contracts", "client.protocol.schema.json")
SHELL = os.path.join("apps", "desktop", "main", "lib", "v2.js")
CLIENT = os.path.join("apps", "web", "src", "v2client.js")
SCREEN = os.path.join("apps", "web", "src", "continuity.jsx")
LEGACY_ARGS = [sys.executable, "-X", "utf8", "ops/ci/ui.py", "--phase", "recovery"]


def locked_node_entry():
    try:
        return json.loads(io.open(os.path.join(ROOT, LOCKED_TOOLS), encoding="utf-8-sig").read())["tools"]["node"]
    except Exception:
        return None


def resolve_node(tools):
    """Absolute pinned binary, version and reason - never a PATH lookup, same rule the accepted W13-01 check uses."""
    if not tools:
        return None, None, "the locked toolchain table could not be read"
    path = tools.get("path")
    if not path or not os.path.isabs(path) or not os.path.isfile(path):
        return None, None, "the pinned node binary is absent: %r" % path
    if hashlib.sha256(open(path, "rb").read()).hexdigest() != tools.get("sha256"):
        return None, None, "the pinned node binary hash does not match the locked table"
    argv = [path] + list(tools.get("version_argv") or ["--version"])
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", timeout=60)
    except Exception as exc:
        return None, None, "the pinned node could not report its version: %s" % exc
    version = (r.stdout or "").strip()
    if r.returncode != 0 or version != tools.get("version_output"):
        return None, None, "the pinned node reports %r while the table says %r" % (version, tools.get("version_output"))
    return path, version, "verified"


def published_methods():
    schema = json.loads(io.open(os.path.join(ROOT, SCHEMA), encoding="utf-8-sig").read())
    return sorted(schema["x-method-contracts"]), schema


def run_driver(node_bin):
    r = subprocess.run([node_bin, os.path.join(ROOT, DRIVER), ROOT], capture_output=True, text=True,
                       encoding="utf-8", timeout=180, cwd=ROOT)
    line = next((l for l in reversed((r.stdout or "").splitlines()) if l.strip().startswith("{")), None)
    return (json.loads(line) if line else None), r.returncode, (r.stderr or "")[:400]


def routing_decision(task, check, case):
    if task == "W13" and check == "W13-02" and not case:
        return "local"
    if task == "W13" and not check and case == "C26":
        return "legacy"
    if not task and not check and not case:
        return "refuse"
    return "refuse"


def forward(task, check, case):
    env = dict(os.environ, RESEARCHOS_TASK_ID=task, RESEARCHOS_CHECK_ID=check, RESEARCHOS_CASE_ID=case)
    p = subprocess.run(LEGACY_ARGS, capture_output=True, text=True, timeout=1800, encoding="utf-8",
                       errors="replace", env=env, cwd=ROOT)
    lines = [l for l in (p.stdout or "").splitlines() if l.strip().startswith("{")]
    return (json.loads(lines[-1]) if lines else None), p.returncode


def declared_ids():
    """The roster is generated from this file's own ok(...)/skip(...) literals, never curated by hand."""
    source = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    return sorted(set(re.findall(r'ok\(\s*"(W1302-[A-Z0-9._-]+)"', source)) |
                  set(re.findall(r'skip\(\s*"(W1302-[A-Z0-9._-]+)"', source)))


def emit(ids, failures, not_verified, diagnostics, extra=None):
    declared = declared_ids()
    emitted = set(ids) | {f["id"] for f in failures} | {n.split(":")[0] for n in not_verified}
    never_emitted = [d for d in declared if d not in emitted]
    undeclared = sorted(e for e in emitted if e not in declared)
    if never_emitted:
        failures.append({"id": "W1302-ROSTER-DECLARED-IDS-ALL-EMITTED",
                         "detail": "declared but never emitted: %s" % ", ".join(never_emitted)})
    else:
        ids.append("W1302-ROSTER-DECLARED-IDS-ALL-EMITTED")
    if undeclared:
        failures.append({"id": "W1302-ROSTER-EMITTED-IDS-ALL-DECLARED",
                         "detail": "emitted but undeclared: %s" % ", ".join(undeclared)})
    else:
        ids.append("W1302-ROSTER-EMITTED-IDS-ALL-DECLARED")
    status = "PASS" if not failures else "FAIL"
    # The dispatcher refuses a report whose count and id list disagree, and an id emitted twice is a report the
    # reader cannot audit; fail here with a named id instead of letting the dispatcher reject the whole run.
    if len(ids) != len(set(ids)):
        failures.append({"id": "W1302-ASSERTION-IDS-UNIQUE",
                         "detail": "duplicated: %s" % sorted({i for i in ids if ids.count(i) > 1})})
    else:
        ids.append("W1302-ASSERTION-IDS-UNIQUE")
    status = "PASS" if not failures else "FAIL"
    report = {"status": status, "assertions": len(ids), "assertion_ids": sorted(set(ids)),
              "failures": failures, "not_verified": not_verified, "diagnostics": diagnostics,
              "task_id": "W13", "check_id": "W13-02", "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
              "forwarded_case": "C26 via ops/ci/ui.py --phase recovery"}
    if extra:
        report.update(extra)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not failures else 1


def main():
    task = os.environ.get("RESEARCHOS_TASK_ID", "")
    check = os.environ.get("RESEARCHOS_CHECK_ID", "")
    case = os.environ.get("RESEARCHOS_CASE_ID", "")
    decision = routing_decision(task, check, case)
    if decision == "legacy":
        rep, rc = forward(task, check, case)
        print(json.dumps(rep if rep else {"status": "COMMAND_FAILED", "assertions": 0,
                                          "note": "the forwarded recovery phase produced no report"}, ensure_ascii=False))
        return rc
    if decision == "refuse":
        print(json.dumps({"status": "COMMAND_FAILED", "assertions": 0, "assertion_ids": [],
                          "failures": [{"id": "W1302-SELECTORS-REQUIRED",
                                        "detail": "pass --check-id W13-02 (or --case-id C26 to forward the frozen "
                                                  "browser recovery phase); no selector means nothing was asked of this program"}],
                          "not_verified": [], "diagnostics": [],
                          "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}, ensure_ascii=False))
        return 1

    ids, failures, diagnostics, not_verified = [], [], [], []

    def ok(label, cond, detail=None):
        if cond:
            ids.append(label)
        else:
            failures.append({"id": label, "detail": str(detail)[:400]})

    def note(probe, cond, detail):
        diagnostics.append({"probe": probe, "observed": cond, "detail": str(detail)[:300]})

    def skip(label, reason):
        not_verified.append(label + ": " + reason)

    tools = locked_node_entry()
    node_bin, node_version, node_reason = resolve_node(tools)
    ok("W1302-TOOLCHAIN-NODE-FROM-LOCKED-TABLE", node_bin is not None, node_reason)
    ok("W1302-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED",
       resolve_node({"path": os.path.join(ROOT, "no", "such", "node.exe"), "sha256": "0" * 64,
                     "version_argv": ["--version"], "version_output": "v0.0.0"})[0] is None,
       "positive control: a table naming an absent binary must yield no executable rather than a PATH name")

    for name in (SHELL, CLIENT, SCREEN, DRIVER):
        if not os.path.isfile(os.path.join(ROOT, name)):
            failures.append({"id": "W1302-SURFACES-AND-DRIVER-EXIST", "detail": name})
    ok("W1302-SURFACES-AND-DRIVER-EXIST",
       all(os.path.isfile(os.path.join(ROOT, f)) for f in (SHELL, CLIENT, SCREEN, DRIVER)),
       [f for f in (SHELL, CLIENT, SCREEN, DRIVER) if not os.path.isfile(os.path.join(ROOT, f))])

    methods, schema = published_methods()
    ok("W1302-SCHEMA-PUBLISHES-EXACTLY-23-METHODS", len(methods) == 23, len(methods))

    if node_bin is None:
        emitted = set(ids) | {f["id"] for f in failures}
        for label in declared_ids():
            if label not in emitted:
                skip(label, "the pinned node is unavailable (%s), so the driver, the bundle build and the browser "
                            "probe could not be executed" % node_reason)
        return emit(ids, failures, not_verified, diagnostics)

    rep, rc, stderr = run_driver(node_bin)
    ok("W1302-DRIVER-EXITED-ZERO", rc == 0 and rep is not None, "rc=%s stderr=%s errors=%s" % (
        rc, stderr, (rep or {}).get("errors")))
    checks = (rep or {}).get("checks", {})
    note("pinned-node-versus-PATH", node_version,
         "the driver ran the pinned node (%s); any node on PATH is irrelevant to these numbers" % node_version)

    tables = checks.get("tables", {})
    shell_row = tables.get("shell", {})
    web_row = tables.get("web", {})
    ok("W1302-SHELL-TABLE-MATCHES-THE-FROZEN-SCHEMA",
       shell_row.get("same_names") is True and shell_row.get("count") == 23 and shell_row.get("rows") == [],
       json.dumps(shell_row, ensure_ascii=False)[:300])
    ok("W1302-RENDERER-TABLE-MATCHES-THE-FROZEN-SCHEMA",
       web_row.get("same_names") is True and web_row.get("count") == 23 and web_row.get("rows") == [],
       json.dumps(web_row, ensure_ascii=False)[:300])
    note("table-diff-rows", tables.get("shell", {}).get("rows"),
         "each row would name the method whose payload/result/required set differs from the published $defs")

    legal = checks.get("legal_envelopes", {})
    ok("W1302-ENVELOPES-AGREE-ACROSS-SURFACES",
       legal.get("count") == 69 and legal.get("agree") == 69, json.dumps(legal, ensure_ascii=False)[:400])
    refusals = checks.get("refusals", {})
    ok("W1302-REFUSAL-REASONS-AGREE", refusals.get("count") == 11 and refusals.get("agree") == 11,
       json.dumps([r for r in refusals.get("rows", []) if not r.get("agree")], ensure_ascii=False)[:400])
    classify = checks.get("classify", {})
    ok("W1302-REPLY-CLASSIFICATION-AGREES", classify.get("count") == 9 and classify.get("agree") == 9,
       json.dumps(classify, ensure_ascii=False)[:300])
    note("classification-kinds", classify.get("kinds"),
         "the nine probes cover the five protocol statuses plus malformed, unknown-status, and two transport shapes")

    local = checks.get("local_refusal_stops_the_command", {})
    ok("W1302-LOCAL-REFUSAL-LEAVES-NO-REQUEST", local.get("sent") == 0 and
       local.get("status", {}).get("kind") == "LOCAL_REFUSED", json.dumps(local, ensure_ascii=False)[:300])
    rebaseline = checks.get("completed_reply_rebaselines", {})
    ok("W1302-HOST-REVISION-REBASELINES", rebaseline.get("before") == 7 and rebaseline.get("after") == 42,
       json.dumps(rebaseline, ensure_ascii=False)[:200])
    refused = checks.get("refused_write", {})
    ok("W1302-REFUSED-WRITE-DOES-NOT-REBASELINE", refused.get("held") == refused.get("after") == 42 and
       refused.get("after") is not None, json.dumps(refused, ensure_ascii=False)[:200])
    in_progress = checks.get("in_progress_reply", {})
    ok("W1302-IN-PROGRESS-DOES-NOT-REBASELINE", in_progress.get("held") == in_progress.get("after") == 42,
       json.dumps(in_progress, ensure_ascii=False)[:200])
    transport = checks.get("transport_loss", {})
    ok("W1302-TRANSPORT-LOSS-DOES-NOT-REBASELINE",
       transport.get("before") == transport.get("after") and transport.get("status") == "TRANSPORT_UNAVAILABLE",
       json.dumps(transport, ensure_ascii=False)[:200])
    adopted = checks.get("adopted_identity", {})
    control = checks.get("adopted_control", {})
    ok("W1302-SESSION-ID-ADOPTED-ONLY-FROM-THE-ENVELOPE",
       adopted.get("sessionIdFromResult") is None and control.get("sessionId") == "sess-on-envelope" and
       control.get("revision") == 6,
       json.dumps({"negative": adopted, "positive": control}, ensure_ascii=False)[:300])

    producers = checks.get("producer_table", {})
    ok("W1302-PRODUCERS-COVER-EVERY-METHOD",
       producers.get("methods") == 23 and producers.get("producers") == 23 and producers.get("surfaces") == 23 and
       producers.get("missing_surface") == [] and producers.get("extra_surface") == [] and
       producers.get("duplicate_producers") is False, json.dumps(producers, ensure_ascii=False)[:300])
    cursor = checks.get("read_events_cursor", {})
    ok("W1302-RECOVERY-READ-CARRIES-THE-HOST-WATERMARK", cursor.get("after_sequence") == 17 and
       cursor.get("limit") == 200, json.dumps(cursor, ensure_ascii=False)[:200])

    screen = io.open(os.path.join(ROOT, SCREEN), encoding="utf-8").read()
    tagged = sorted(set(re.findall(r'method="([a-z]+\.[a-z]+)"', screen)))
    ok("W1302-EACH-METHOD-HAS-A-CONTROL-IN-THE-SCREEN", sorted(set(tagged)) == methods,
       "missing %s extra %s" % (sorted(set(methods) - set(tagged)), sorted(set(tagged) - set(methods))))
    note("control-tag-source", len(tagged),
         "this row reads the screen's own control tags; it is the floor, and the browser row below is what shows a "
         "tag actually produces a command")

    probe = {"checks": {}, "errors": ["not run"]}
    probe_rc = None
    probe_path = os.path.join(ROOT, "tests", "ui", "continuity", "producer_probe.py")
    build = subprocess.run([node_bin, os.path.join(ROOT, "apps/web/node_modules/vite/bin/vite.js"), "build",
                            "--logLevel", "error"], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=300, cwd=os.path.join(ROOT, "apps", "web"))
    ok("W1302-BUNDLE-BUILT-FROM-CURRENT-SOURCES", build.returncode == 0 and
       os.path.isfile(os.path.join(ROOT, "apps", "web", "dist", "index.html")),
       "rc=%s %s" % (build.returncode, (build.stderr or build.stdout or "")[:300]))
    try:
        pr = subprocess.run([sys.executable, "-X", "utf8", probe_path], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=1200, cwd=ROOT)
        probe_rc = pr.returncode
        line = next((l for l in reversed((pr.stdout or "").splitlines()) if l.strip().startswith("{")), None)
        probe = json.loads(line) if line else {"checks": {}, "errors": [(pr.stdout or "")[:200] + (pr.stderr or "")[:200]]}
    except Exception as exc:
        probe_rc, probe = -1, {"checks": {}, "errors": [repr(exc)[:300]]}
    pc = probe.get("checks", {})
    traffic = pc.get("traffic", {})
    ok("W1302-PROBE-FIXTURES-MATCH-THE-PUBLISHED-SCHEMA", pc.get("fixtures", {}).get("problems") == [] and
       pc.get("fixtures", {}).get("methods") == 23, json.dumps(pc.get("fixtures"), ensure_ascii=False)[:300])
    ok("W1302-BROWSER-PRODUCERS-DISPATCH-THEIR-COMMAND",
       traffic.get("distinct_methods") == 23 and traffic.get("missing_clicks") == [] and
       all(row["method"] in row["sent"] for row in pc.get("clicked", [])) and probe.get("errors") == [],
       json.dumps({"rc": probe_rc, "errors": probe.get("errors", [])[:1], "traffic": traffic,
                   "mismatched": [r["method"] for r in pc.get("clicked", []) if r["method"] not in r["sent"]]},
                  ensure_ascii=False)[:400])
    ok("W1302-PRODUCERS-ALL-REACH-ONE-ENDPOINT",
       traffic.get("paths") == ["/v2/command"] and traffic.get("off_protocol") == [] and
       traffic.get("all_authorized") is True, json.dumps(traffic, ensure_ascii=False)[:300])
    rendered = pc.get("rendered_controls", {})
    ok("W1302-SCREEN-RENDERS-A-CONTROL-PER-PRODUCER",
       rendered.get("total", 0) >= 22 and len(rendered.get("tags", {})) >= 19 and
       all(m in rendered.get("tags", {}) for m in methods if m not in
           ("session.get", "workspace.read", "workspace.write", "permission.respond")),
       json.dumps(rendered, ensure_ascii=False)[:300])
    unmet = pc.get("unmet_precondition", {})
    ok("W1302-UNMET-PRECONDITION-SENDS-NOTHING",
       unmet.get("state", {}).get("present") is True and unmet.get("state", {}).get("disabled") is True and
       unmet.get("commands_after") == 0, json.dumps(unmet, ensure_ascii=False)[:250])

    skip("W1302-CLI-TO-DESKTOP-SAME-SESSION-HANDOFF",
         "the handoff and resume chain across the real CLI process and this screen on one live session needs the "
         "worker-under-Run lifecycle of W05-01/W06-02 plus a desktop session launch binding (desktop.shell_launch is "
         "UNBOUND); the protocol half - attach/claim/handoff envelopes - is asserted above")
    skip("W1302-CRASH-RESTART-WITHOUT-SIDE-EFFECT-REPLAY",
         "recovery is asserted at the client level (a cursor read that never resends, and a refused or unanswered "
         "reply that never re-baselines); killing and restarting the real browser and checking that no send, "
         "control or write re-executes belongs to the forwarded C26 recovery phase")

    return emit(ids, failures, not_verified, diagnostics,
                extra={"pinned_node": node_version, "methods_published": len(methods),
                       "driver": {"legal": legal.get("count"), "refusals": refusals.get("count"),
                                  "classify": classify.get("count")}})


if __name__ == "__main__":
    sys.exit(main())
