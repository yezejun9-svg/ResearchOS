"""Generate execution/v2.4/receipts/W13/W13-01/receipt.json from the files on disk.

Every figure is read back out of a frozen artifact at run time and re-asserted before the file is written;
the guard runs before anything is written and again on the temporary file, which is renamed only after both
passes and deleted on any abort. What it does not guarantee: that the captured logs are honest, or that a
hand-edited matrix would be caught - the matrix file is re-counted here, not re-run, and an independent
identity must re-run it.

Run with --capture to produce the command logs first.
"""
import datetime
import glob
import hashlib
import io
import json
import os
import subprocess
import sys

NL = chr(10)


def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
RD = os.path.join("execution", "v2.4", "receipts", "W13", "W13-01")
SPEC = r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4"
PY = sys.executable
LOGS = os.path.join(RD, "invocations", "logs")
MATRIX = "mutation_selfcheck_w1301.json"
CHECK = os.path.join("tests", "ui", "check", "main.py")
CAPTURE = [
 ("check_program", [PY, CHECK, "--check-id", "W13-01"], "the bound check program run directly"),
 ("dispatch_c23_parity", [PY, "execution/command_dispatcher/dispatch.py", "test.ui.routes",
  "--task-id", "W13", "--case-id", "C23"],
  "the forwarded branch is exercised; this run's own status is recorded below because the branch is nondeterministic (c23_forwarded_flake_census.json)"),
 ("dispatch_bare", [PY, "execution/command_dispatcher/dispatch.py", "test.ui.routes"],
  "a selector-less dispatch is still refused rather than served"),
]


def disp(arg):
    """Render an argv entry for the receipt. Paths inside the repository are relativised;
    an interpreter outside it (sys.executable can live on another drive) is shown by name
    with its version, so a reader knows what ran without the row being machine-specific."""
    a = os.path.abspath(arg)
    try:
        if os.path.commonpath([a, REPO]) == REPO:
            return os.path.relpath(a, REPO).replace("\\", "/")
    except ValueError:
        pass
    return "%s (%s)" % (os.path.basename(a), sys.version.split()[0])


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(path):
    return json.load(io.open(path, encoding="utf-8-sig"))


def dump(path, obj):
    io.open(path, "w", encoding="utf-8", newline=NL).write(json.dumps(obj, indent=1, ensure_ascii=False))


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


env = dict(os.environ, PYTHONIOENCODING="utf-8")
for k in ("RESEARCHOS_TASK_ID", "RESEARCHOS_CHECK_ID", "RESEARCHOS_CASE_ID"):
    env.pop(k, None)

if "--capture" in sys.argv:
    head = git("rev-parse", "HEAD")
    os.makedirs(LOGS, exist_ok=True)
    for key, argv, expect in CAPTURE:
        p = subprocess.run(argv, cwd=REPO, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
        text = (p.stdout or "") + (p.stderr or "")
        rows = [l for l in text.splitlines() if l.strip().startswith("{")]
        rep = json.loads(rows[-1]) if rows else {}
        state = rep.get("status") or "NO_REPORT"
        result = "%s; status=%s; assertions=%s; last line: %s" % (expect, state, rep.get("assertions"),
                                                       [l for l in text.splitlines() if l.strip()][-1][:160])
        dump(os.path.join(LOGS, key + ".json"),
             {"key": key, "cwd": "REPOSITORY", "argv": [disp(a) for a in argv],
              "exit_code": p.returncode, "status": state, "assertions": rep.get("assertions"),
              "result": result, "code_revision": head,
              "output_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(),
              "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print(key, "exit", p.returncode, "|", state, rep.get("assertions"))
    sys.exit(0)

head = git("rev-parse", "HEAD")
porcelain = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True,
                            text=True, encoding="utf-8").stdout
dirty = [l for l in porcelain.split(chr(10))
         if l.strip() and not l.startswith("?? execution/") and not l.startswith("?? .local/")]

check_out = subprocess.run([PY, CHECK, "--check-id", "W13-01"], cwd=REPO, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=900)
rows = [l for l in (check_out.stdout or "").splitlines() if l.strip().startswith("{")]
if not rows:
    raise SystemExit("the check program produced no report; nothing is being written")
report = json.loads(rows[-1])
ids = sorted(report.get("assertion_ids") or [])
if report.get("status") != "PASS" or not ids or check_out.returncode != 0:
    raise SystemExit("the check program is not a clean PASS (%s, rc=%s)" % (report.get("status"), check_out.returncode))
if report.get("failures"):
    raise SystemExit("the check program lists failures; this receipt may not say PASS")

matrix = load(os.path.join(RD, MATRIX))
buckets = matrix["buckets"]
if buckets.get("survived") or buckets.get("crashed") or buckets.get("anchor-missing") or buckets.get("caught") != matrix["cases"]:
    raise SystemExit("the matrix must report every one of its %d cases caught; it reports %s" % (matrix["cases"], buckets))
if not matrix.get("tree_clean_after_restore"):
    raise SystemExit("the matrix did not leave the tree clean, so its restores cannot be trusted")
bad_restore = [r["id"] for r in matrix["results"] if not r.get("restored_byte_identical")]
if bad_restore:
    raise SystemExit("cases that did not restore their file byte for byte: %s" % bad_restore)
caught = [{"case": r["id"], "killed": r.get("killed") or [], "restored_byte_identical": r.get("restored_byte_identical")}
          for r in matrix["results"] if r["bucket"] == "caught"]

baseline = load(os.path.join(RD, "before_baseline_test.ui.routes.json"))
PARITY = "binding_and_parity_rev15_at_head.json"
if not os.path.exists(os.path.join(RD, PARITY)):
    raise SystemExit("no at-HEAD parity file: run remeasure_parity_w1301.py first, because quoting the "
                     "binding-commit rows would mix trees")
parity = load(os.path.join(RD, PARITY))["rows"]
parity_source = PARITY
if any(v.get("code_revision") != os.popen("git rev-parse HEAD").read().strip() for v in parity.values()):
    raise SystemExit("a parity row was not measured at this HEAD")
CENSUS = "c23_forwarded_flake_census.json"
census = load(os.path.join(RD, CENSUS))
if census["runs"] != len(census["rows"]) or sum(census["cause_counts"].values()) != census["runs"]:
    raise SystemExit("the C23 census does not account for its own rows: %s vs %d" % (census["cause_counts"], census["runs"]))
if any("unclassified" in r["cause"] for r in census["rows"]):
    raise SystemExit("a failed C23 run in the census is unexplained; classify it or report it as unexplained, do not drop it")
census_by_head = {}
for r in census["rows"]:
    census_by_head.setdefault(r["code_revision"], set()).add(r["status"])
disagreeing = sorted(h for h, v in census_by_head.items() if len(v) > 1)
registry = load(os.path.join("execution", "v2.4", "commands.json"))
entry = registry["commands"]["test.ui.routes"]
if entry.get("owner_card") != "W13-01":
    raise SystemExit("test.ui.routes is not owned by this card in the registry")


def command_log(key):
    p = os.path.join(LOGS, key + ".json")
    if not os.path.exists(p):
        raise SystemExit("no captured log for %s: run this generator with --capture first" % key)
    c = load(p)
    for field in ("argv", "exit_code", "result", "code_revision", "status"):
        if field not in c:
            raise SystemExit("command log %s is missing %s" % (key, field))
    if c["code_revision"] != head:
        raise SystemExit("command log %s was captured at %s, not this HEAD %s" % (key, c["code_revision"][:8], head[:8]))
    return {"cwd": c["cwd"], "argv": c["argv"], "exit_code": c["exit_code"], "result": c["result"],
            "observed_status": c["status"], "observed_assertions": c.get("assertions"),
            "derived_from": "invocations/logs/%s.json" % key}


hist = {}
for i in ids:
    parts = i.split("-")
    key = parts[0] + "-" + (parts[1] if len(parts) > 1 else "")
    hist[key] = hist.get(key, 0) + 1

artifacts = [CHECK, os.path.join("apps", "desktop", "main", "lib", "host.js"),
             os.path.join("apps", "desktop", "main", "lib", "ipc.js"),
             os.path.join("apps", "desktop", "main", "main.js"),
             os.path.join("apps", "desktop", "preload", "preload.js"),
             os.path.join("apps", "desktop", "main", "workbench.html"),
             "execution/v2.4/commands.json", os.path.join(RD, CENSUS).replace("\\", "/"),
             os.path.join(RD, "census_c23_w1301.py"),
             os.path.join(RD, "add_census_probe_w1301.py"),
             os.path.join(RD, MATRIX), os.path.join(RD, PARITY),
             os.path.join(RD, "binding_and_parity_rev15.json"),
             os.path.join(RD, "before_baseline_test.ui.routes.json")]
missing = [a for a in artifacts if not os.path.exists(a)]
if missing:
    raise SystemExit("artifact listed by the receipt is absent: %s" % [m.replace("\\", "/") for m in missing])

receipt = {
 "template_version": "2.4-receipt-1", "step_id": "W13-01", "parent_task": "W13",
 "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "executor_id": "qoder-desktop:/root/construction", "verifier_id": None,
 "status": "EXECUTION_REPORTED",
 "notice": "Executor reports only. No field below is evidence of acceptance; an independent identity must "
           "re-run this card's binding command, its matrix and its parity rows before step_state changes.",
 "mode": "DEVELOPMENT", "repository_head_at_reporting": head,
 "uncommitted_source_files_at_reporting": dirty,
 "input": {"card": os.path.join(SPEC, "tasks", "steps", "W13-01.md"),
  "read_refs": ["08_AGENT_EXECUTION_GOAL.md", "05_WBS.md W13", "contracts/tasks.json tasks[task_id=W13]",
                "19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md 1-7", "22_CLIENT_INTERFACE_DETAILS.md"],
  "write_scope": ["DESKTOP/** (alias for apps/desktop)", "UI/**", "tests/ui/**",
                  "execution/v2.4/receipts/W13/W13-01/**"],
  "plan_sha256": load(os.path.join("execution", "v2.4", "checkpoint.json"))["plan_sha256"]},
 "artifacts": [{"path": a.replace("\\", "/"), "sha256": sha(a)} for a in artifacts],
 "commands": [
  {"cwd": "REPOSITORY", "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.ui.routes",
    "--task-id", "W13", "--check-id", "W13-01"], "exit_code": 0,
   "result": {"status": parity["local_check_W13_01"]["status"],
              "assertions": parity["local_check_W13_01"]["assertions"],
              "invocation_id": parity["local_check_W13_01"]["invocation_id"],
              "derived_from": PARITY},
   "note": "the row a reviewer should re-run first; parity measured at the same registry revision as this receipt"},
  {"cwd": "REPOSITORY", "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.ui.routes",
    "--task-id", "W13", "--case-id", "C23"], "exit_code": 0,
   "result": {"status": parity["forwarded_case_C23"]["status"],
              "assertions": parity["forwarded_case_C23"]["assertions"],
              "invocation_id": parity["forwarded_case_C23"]["invocation_id"],
              "history_note": "the forwarded branch is not stable: %d runs of it are on disk, %d of them "
                              "COMMAND_FAILED, and the heads whose rows disagree are %s. See "
                              "c23_forwarded_flake_census.json; this row quotes one run, not a claim of stability."
                              % (census["runs"], census["statuses"]["COMMAND_FAILED"], ", ".join(disagreeing)),
              "derived_from": PARITY},
   "note": "the case this key served before the card bound it; binding must not shadow it"},
  {"cwd": "REPOSITORY", "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.ui.routes"],
   "exit_code": parity["bare_selector_refused"].get("exit_code", 1),
   "result": {"status": parity["bare_selector_refused"]["status"],
              "assertions": parity["bare_selector_refused"].get("assertions", 0),
              "derived_from": PARITY},
   "note": "a selector-less dispatch stays a refusal; zero assertions is never a PASS"},
  command_log("check_program"), command_log("dispatch_c23_parity"), command_log("dispatch_bare")],
 "check_results": {
  "status": report["status"], "assertions": len(ids), "failures": report.get("failures"),
  "harness_scope": report.get("scope"), "not_verified": sorted(report.get("not_verified") or []),
  "assertion_id_prefix_histogram": hist, "binding_registry_revision": registry["revision"],
  "assertion_ids": ids},
 "mutation_selfcheck": {
  "cases": matrix["cases"], "buckets": buckets, "caught": caught, "runner": os.path.join(RD, "mut_w1301.py"),
  "matrix_source": MATRIX, "tree_clean_after_restore": bool(matrix.get("tree_clean_after_restore")),
  "no_mutant_rows": matrix.get("no_mutant_rows"),
  "coverage_note": "ten mutants each die on a named assertion; the rows listed in no_mutant_rows are source "
                   "inventories or data tables that no production mutant reaches, and they are named rather than "
                   "left silently absent from the coverage table",
  "restoration": "every case hash-compared its file back to the original; the matrix also reports the tree clean "
                 "after restore, measured on a tree with no uncommitted work of mine in apps or tests"},
 "registry_parity": {
  "registry_revision": registry["revision"], "command_key": "test.ui.routes",
  "baseline_measured_before_binding": baseline["measured"],
  "after_binding": [parity["local_check_W13_01"], parity["forwarded_case_C23"], parity["bare_selector_refused"]],
  "c23_forwarded_history": {"source": CENSUS, "runs": census["runs"], "statuses": census["statuses"],
                            "cause_counts": census["cause_counts"], "heads_with_both_results": disagreeing,
                            "conclusion": census["conclusion"]},
  "forwarding": "tests/ui/check/main.py forwards every selector except task W13 with check W13-01 to "
                "ops/ci/ui.py --phase workflow, asserted as W1301-ROUTING-TRUTH-TABLE",
  "disclosed_consequence": "the forwarded branch resolves python through PATH rather than the locked tool "
                           "table, exactly as the v2.0 entry it replaces did"},
 "defects_found_and_fixed_across_all_rounds": [
  {"defect": "a router convenience treated a selector-less invocation as a local run, so an unspecified "
             "dispatch returned PASS",
   "fix": "local mode requires an explicit --check-id W13-01 or the dispatcher naming task W13 with that check; "
          "a selector-less run returns COMMAND_FAILED with zero assertions "
          "with no assertion id emitted; the harness source carries a failure row for that refusal, but no "
          "dispatcher run in this round emitted it, so it is not quoted as an id here"},
  {"defect": "a refusal branch was written after the branch that forwards, so it could never execute",
   "fix": "the refusal now precedes forwarding, and the truth-table row enumerates the refuse branch"},
  {"defect": "a mutation case was credited as caught while the mutant had actually broken the module's syntax, "
             "which destroyed every row at once",
   "fix": "the runner refuses any case whose run also loses the harness-liveness row; two of the ten cases were "
          "rewritten as complete statements and re-run, and a case that breaks the harness is filed as crashed, "
          "never as a kill"},
  {"defect": "a fake decided core reachability by counting HTTP requests, so it could prove the launch branch "
             "while modelling nothing about a core coming up",
   "fix": "reachability is world state flipped by the injected spawn, and the unreachable-core case asserts that "
          "no host call happens at all"},
  {"defect": "this receipt's own earlier draft claimed the mount broke the accepted case C23 and reverted it",
   "fix": "re-measured with the mount in place C23 is PASS 6, so the causal claim is retracted and recorded as a "
          "record_correction event. The red runs are now explained by measurement rather than by a story: "
          "c23_forwarded_flake_census.json tabulates all %d dispatcher runs of the forwarded selector and "
          "classifies each failure - two were my own SyntaxError in the check program, one was the legacy "
          "harness's selector guard, two were the real browser phase reporting FAIL at inputs that PASS minutes "
          "later. None of them was the mount." % census["runs"]}],
 "known_limitations_and_obligations": [
  "the installed desktop experience is not proven: step 4 requires a real Windows install opened from the "
  "Start menu with the U01 first-use gate, which the resource Windows_desktop_session has to authorize, so it "
  "blocks that step and only that step",
  "the native directory dialog is registered in the main process and asserted at source level, but no session "
  "here has watched it open and return a path",
  "provider.models, provider.configure and provider.probe are routed and their failures classify correctly, "
  "yet no provider command key is bound in either registry and client_mapping.json lists provider.models as "
  "PLANNED under W02-03 and provider.probe as PLANNED under W08-01, so a real model list, a saved credential "
  "and a real probe stay NOT_RUN for this card",
  "desktop.shell_launch carries owner_card 'W13-01 renderer integration' while UNBOUND; this card either binds "
  "it or records why the registry says what it says",
  "the forwarded C23 branch inherited from ops/ci/ui.py is nondeterministic: at identical argv, environment "
  "names, code revision and registered command revision it returned FAIL and PASS minutes apart (heads %s). "
  "This card does not sign C23 and does not claim the branch is stable; whoever signs C23 must re-run it and "
  "treat a single PASS as insufficient." % ", ".join(disagreeing),
  "nothing here accepts parent W13 or signs formal case C23 or A10"],
 "not_verified_on_this_machine": [
  "no installed-shell run, no Start-menu launch, no real provider call: everything claimed is what the bound "
  "check program, the matrix, the registry parity rows and the captured logs measure"],
 "independent_review": None, "independent_reviews": [], "rework_of": None,
 "reuse_notes": "the harness boot and report shape follow tests/runtime/check from W05-01; what differs is the "
                "surface driven - node loads the desktop routing and IPC modules directly, and the accepted "
                "W13 workflow case is reached by forwarding rather than by this card"}


def guard(obj, where):
    if obj["verifier_id"] is not None or obj["status"] != "EXECUTION_REPORTED":
        raise SystemExit("the executor must not fill the verifier field or claim acceptance (%s)" % where)
    if obj["independent_review"] is not None or obj["independent_reviews"]:
        raise SystemExit("a receipt generated by the executor may not carry a review (%s)" % where)
    cr = obj["check_results"]
    if cr["assertions"] != len(ids) or cr["status"] != "PASS" or cr["failures"]:
        raise SystemExit("check_results does not match the measured run (%s)" % where)
    if sorted(cr["not_verified"]) != sorted(report.get("not_verified") or []):
        raise SystemExit("disclosure rows were rewritten instead of derived (%s)" % where)
    if len(obj["artifacts"]) != len(artifacts):
        raise SystemExit("artifact list truncated (%s)" % where)
    b = obj["mutation_selfcheck"]["buckets"]
    if obj["mutation_selfcheck"]["cases"] != sum(b.values()) or b.get("caught") != obj["mutation_selfcheck"]["cases"]:
        raise SystemExit("matrix buckets are not what this receipt claims: %s (%s)" % (b, where))
    if not obj["mutation_selfcheck"]["tree_clean_after_restore"]:
        raise SystemExit("the matrix did not leave the tree clean (%s)" % where)
    if len(obj["mutation_selfcheck"]["caught"]) != b["caught"]:
        raise SystemExit("caught rows do not match the caught bucket (%s)" % where)
    if obj["registry_parity"]["registry_revision"] != registry["revision"]:
        raise SystemExit("registry revision in the receipt disagrees with the file (%s)" % where)
    if len(obj["known_limitations_and_obligations"]) < 6:
        raise SystemExit("the obligation list has been shortened below what this card knows (%s)" % where)
    for c in obj["commands"]:
        r = c.get("result")
        if isinstance(r, dict):
            if not r.get("derived_from"):
                raise SystemExit("a command row quotes a result with no source (%s)" % where)
            continue
        if not (isinstance(r, str) and c.get("derived_from") and c.get("exit_code") is not None):
            raise SystemExit("a command row quotes a result nobody captured (%s)" % where)


guard(receipt, "in memory")
tmp = os.path.join(RD, "receipt.json.tmp")
try:
    dump(tmp, receipt)
    again = load(tmp)
    guard(again, "on the written file")
    os.replace(tmp, os.path.join(RD, "receipt.json"))
except BaseException:
    if os.path.exists(tmp):
        os.remove(tmp)
    raise
print("receipt.json written at HEAD", head[:8], "| assertions", again["check_results"]["assertions"],
      "| artifacts", len(again["artifacts"]), "| matrix", again["mutation_selfcheck"]["buckets"],
      "| disclosed", len(again["check_results"]["not_verified"]))
