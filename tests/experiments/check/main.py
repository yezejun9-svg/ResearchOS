"""W10-01's check handler: drive the three suites that actually implement the card and report per-check rows.

This file is deliberately thin. Every assertion it reports was emitted by a Go test that a reviewer can
re-run; nothing here grades anything itself. Two consequences are designed in:

* the roster must equal the union of what the suites emitted, so a row that goes quiet or appears without
  being declared fails this card rather than passing it;
* the pinned go comes from execution/toolchains/locked.json only. A PATH lookup is never used, because a
  different toolchain would make the run un-reproducible while still looking green.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

# tests/experiments/check/main.py -> the repository root is four levels up
ROOT = pathlib.Path(__file__).resolve().parents[3]
LOCKED = ROOT / "execution" / "toolchains" / "locked.json"
SMOKE_FILE = ROOT / "spec" / "v2.0" / "examples" / "evaluation_smoke_cases.json"
DOMAIN_DIR = ROOT / "internal" / "domain"
ADAPTER_DIR = ROOT / "adapters" / "evaluation"
SANDBOX_DIR = ROOT / "ops" / "experiment_sandbox"
CARD_ID = "W10-01"
CHECKS = ("W10-01-OUTPUT", "W10-01-NEGATIVE", "W10-01-EVIDENCE")
SUITE_TIMEOUT_SECONDS = 900

# Which check each id family answers. Rules are prefix-based and the union is pinned below by
# W1001-ROSTER-EXACTNESS, so an unexpected new id makes the run red instead of silently unclassified.
OUTPUT_RULES = [r"^PF-\d\d$", r"^C21-(COUNTS|STABLE|VALID|EXIT|HIGH-SCORE|NATIVE-PROVIDER-STATUS)$",
                r"^A07-(RECOMPUTE|OUTCOME|VERIFIED|REGISTER-FIRST|NATIVE)-", r"^W1001-(TWO-ATTEMPTS|EVALUABLE|BETWEEN|SAME-EXPERIMENT-STILL-ACCEPTS)",
                r"^SANDBOX-(RECOMPUTE|EXIT|STABLE)"]
NEGATIVE_RULES = [r"^A07-(HASH|POSTHOC|NO-RECEIPT|METRIC-FORGE)-",
                  r"^C21-(ZERO|TAMPER|REJECT|COUNT-TAMPER|REGRESSION|OBSERVED-FENCE)",
                  r"^W1001-(DELETING|RETENTION-REFUSAL|REPORTED-TASK|METRIC-VERDICT|ZERO-SAMPLE)",
                  r"^SANDBOX-(REJECT|TIMEOUT|OBSERVED-EGRESS|HOST-CONTROL|baseline-|candidate-)"]

SUITES = {
    "adapter": {"dir": ADAPTER_DIR, "argv": ["test", "./adapters/evaluation", "-count=1", "-v"],
                "why": "the 12 frozen smoke cases, the count recomputation and the raw-integrity refusals"},
    "domain": {"dir": DOMAIN_DIR, "argv": ["test", "./internal/domain", "-run", "TestW10|TestW1001",
                                                "-count=1", "-v"],
               "why": "the preregistration freeze, the independent recompute and this card's retention rows"},
    "sandbox": {"dir": SANDBOX_DIR, "argv": ["test", "./ops/experiment_sandbox", "-count=1", "-v"],
                "why": "arm isolation: per-arm exit, denials for writes/reads/egress outside the workspace"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def emit(status, rows, failures, extra=None):
    ids = [r["assertion_id"] for r in rows]
    # dispatch.py has an invariant: if a report carries a key named `assertions`, that key must be the
    # integer count of assertion ids, so the ids live in `assertion_ids` and the count in `assertions`.
    payload = {"check_id": CARD_ID, "task_id": "W10", "case_id": "A07", "mode": "FIXTURE",
               "status": status, "run_at": now(),
               "assertion_ids": ids,
               "assertions": len(ids),
               "assertions_total": len(rows), "assertions_failed": len(failures),
               "checks": {c: {"rows": sum(1 for r in rows if r.get("check") == c),
                              "failed": sum(1 for r in failures if r.get("check") == c)} for c in CHECKS},
               "failures": failures, "rows": rows}
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == "PASS" else 1


def refuse(reason, observed):
    return emit("FAIL", [], [{"id": "W1001-ROUTING-BINDING-REFUSED", "detail": reason}],
                extra={"routing": {"task_id": observed[0], "check_id": observed[1], "case_id": observed[2],
                                   "decision": "refuse",
                                   "note": "this key belongs to W10-01 only; W10-G01/W10-G02/W08-G01 stay on "
                                           "the legacy test.experiments binding, whose handler "
                                           "ops/ci/experiments.py is outside this card's write_scope"}})


def resolve_go(explicit=None):
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
        [s for s, _ in candidates])


def check_binding():
    task = os.environ.get("RESEARCHOS_TASK_ID") or ""
    check = os.environ.get("RESEARCHOS_CHECK_ID") or ""
    case = os.environ.get("RESEARCHOS_CASE_ID") or ""
    return task, check, case


def classify(assertion_id):
    for rule in OUTPUT_RULES:
        if re.match(rule, assertion_id):
            return CHECKS[0]
    for rule in NEGATIVE_RULES:
        if re.match(rule, assertion_id):
            return CHECKS[1]
    return None


def declared_in_go_source():
    """Ids literally emitted by this card's own test, read out of the source rather than assumed."""
    path = DOMAIN_DIR / "experiments_w1001_test.go"
    if not path.is_file():
        return None
    return sorted(set(re.findall(r'w1001Assert\(\s*t,\s*"(W1001-[A-Z0-9_-]+)"',
                                path.read_text(encoding="utf-8"))))


def run_suite(go_binary, name):
    spec = SUITES[name]
    env = dict(os.environ, GOTOOLCHAIN="local", GOENV="off", RESEARCHOS_GO=go_binary,
               W10_EVIDENCE_DIR=str(ROOT / ".local" / "w1001-evidence"))
    os.makedirs(env["W10_EVIDENCE_DIR"], exist_ok=True)
    try:
        p = subprocess.run([go_binary] + spec["argv"], cwd=str(ROOT), env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=SUITE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return None, "suite %s timed out after %ds" % (name, SUITE_TIMEOUT_SECONDS)
    rows = []
    for line in (p.stdout or "").splitlines():
        m = re.match(r"^\s*W10_ASSERTION\s+(\{.*\})$", line)
        if not m:
            continue
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        if d.get("assertion_id"):
            rows.append(d)
    if p.returncode != 0 and not rows:
        return None, "suite %s exited %d with no assertion lines: %s" % (
            name, p.returncode, (p.stderr or p.stdout or "")[-400:])
    tail = ""
    if p.returncode != 0:
        keep = [line for line in (p.stdout or "").splitlines()
                if line.startswith("--- FAIL") or line.startswith("    ") and ".go:" in line
                or line.startswith("FAIL")]
        tail = " | ".join(keep[-6:])[:900]
    return {"name": name, "rc": p.returncode, "rows": rows, "failure_output": tail}, None


def main():
    task, check, case = check_binding()
    if task != "W10" or check != CARD_ID:
        return refuse("this handler answers task W10 / check %s only; observed %r / %r / %r" %
                      (CARD_ID, task, check, case), (task, check, case))
    go_binary, go_note = resolve_go()
    if go_binary is None:
        return emit("FAIL", [], [{"id": "W1001-PINNED-GO-UNRESOLVED", "detail": go_note, "check": CHECKS[2]}])

    suites, problems = [], []
    for name in SUITES:
        result, err = run_suite(go_binary, name)
        if err:
            problems.append({"id": "W1001-SUITE-COULD-NOT-RUN", "detail": "%s: %s" % (name, err),
                             "check": CHECKS[2]})
            continue
        suites.append(result)

    seen, rows = {}, []
    for suite in suites:
        for d in suite["rows"]:
            ident = d["assertion_id"]
            if ident in seen:
                problems.append({"id": "W1001-ASSERTION-ID-EMITTED-TWICE",
                                 "detail": "%s came from %s and %s" % (ident, seen[ident], suite["name"]),
                                 "check": CHECKS[2]})
                continue
            seen[ident] = suite["name"]
            owner = classify(ident)
            if owner is None:
                problems.append({"id": "W1001-ASSERTION-UNCLASSIFIED",
                                 "detail": "%s emitted by %s matches no check rule" % (ident, suite["name"]),
                                 "check": CHECKS[2]})
                continue
            rows.append({"assertion_id": ident, "check": owner, "status": d.get("status"),
                         "suite": suite["name"], "expected": d.get("expected"), "actual": d.get("actual"),
                         "evidence": d.get("evidence")})

    declared = declared_in_go_source()
    emitted_w1001 = sorted(i for i in seen if i.startswith("W1001-"))
    if declared is None:
        problems.append({"id": "W1001-CARD-TEST-MISSING", "detail": "experiments_w1001_test.go could not be read",
                         "check": CHECKS[2]})
    else:
        if declared != emitted_w1001:
            problems.append({"id": "W1001-ROSTER-EXACTNESS", "check": CHECKS[2],
                             "detail": "the test source declares %s but the run emitted %s" % (declared,
                                                                                               emitted_w1001),
                             "only_in_source": sorted(set(declared) - set(emitted_w1001)),
                             "only_in_run": sorted(set(emitted_w1001) - set(declared))})

    smoke = {"exists": SMOKE_FILE.is_file()}
    if smoke["exists"]:
        raw = SMOKE_FILE.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        smoke.update({"sha256": hashlib.sha256(raw).hexdigest(), "case_count": len(doc.get("cases") or []),
                      "case_ids": [c.get("id") for c in doc.get("cases") or []],
                      "measurement_mode": doc.get("measurement_mode")})
        pf_rows = sorted(i for i in seen if re.match(r"^PF-\d\d$", i))
        smoke["emitted_pf_rows"] = pf_rows
        if smoke["case_count"] != 12 or pf_rows != smoke["case_ids"]:
            problems.append({"id": "W1001-FROZEN-SMOKE-SET-NOT-ALL-RUN", "check": CHECKS[0],
                             "detail": "the frozen file declares %d cases %s; the adapter emitted %s" %
                                       (smoke["case_count"], smoke["case_ids"], pf_rows)})
    rows.append({"assertion_id": "W1001-FROZEN-SMOKE-SET-DRIVEN-CASE-BY-CASE", "check": CHECKS[0],
                 "status": "PASS" if smoke.get("case_count") == 12 and not
                 any(p["id"] == "W1001-FROZEN-SMOKE-SET-NOT-ALL-RUN" for p in problems) else "FAIL",
                 "suite": "harness", "expected": "12 frozen ids, each emitted", "actual": smoke,
                 "evidence": "spec/v2.0/examples/evaluation_smoke_cases.json read from disk, compared with the "
                             "adapter's own PF-* rows"})

    for suite in suites:
        bad = [r for r in suite["rows"] if r.get("status") != "PASS"]
        rows.append({"assertion_id": "W1001-SUITE-CLEAN-%s" % suite["name"], "check": CHECKS[2],
                     "status": "PASS" if not bad and suite["rc"] == 0 else "FAIL",
                     "suite": "harness", "expected": "exit 0 and every row PASS",
                     "actual": {"rc": suite["rc"], "rows": len(suite["rows"]), "not_pass": [b["assertion_id"] for b in bad],
                                "go_failure_output": suite.get("failure_output") or ""},
                     "evidence": SUITES[suite["name"]]["why"]})
        for b in bad:
            problems.append({"id": b["assertion_id"], "check": classify(b["assertion_id"]) or CHECKS[2],
                             "detail": "emitted FAIL by suite %s" % suite["name"],
                             "expected": b.get("expected"), "actual": b.get("actual")})

    failed = problems + [{"id": r["assertion_id"], "check": r["check"], "detail": "row status %s" % r["status"]}
                         for r in rows if r["status"] != "PASS"]
    status = "PASS" if not failed else "FAIL"
    return emit(status, rows, failed,
                extra={"toolchain": {"go": go_binary, "note": go_note,
                                     "locked_sha256": json.loads(LOCKED.read_text(encoding="utf-8-sig"))
                                     ["tools"]["go"].get("sha256")},
                       "suites": [{"name": s["name"], "rc": s["rc"], "rows": len(s["rows"])} for s in suites],
                       "frozen_smoke": smoke,
                       "declared_card_ids": declared,
                       "binding": {"key": "test.experiments.w1001", "declared_key": "test.experiments",
                                   "declared_key_reason": "the declared key is not in the v2.4 registry; the "
                                                          "legacy binding it resolves to lists check ids "
                                                          "W10-G01/W10-G02/W08-G01 and a handler outside this "
                                                          "card's write_scope, so appending W10-01 there would "
                                                          "re-route accepted parent gates"},
                       "receipt_directory": "execution/v2.4/receipts/W10/W10-01"})


if __name__ == "__main__":
    raise SystemExit(main())
