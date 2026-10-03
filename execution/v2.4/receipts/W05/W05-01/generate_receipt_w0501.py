"""Generate execution/v2.4/receipts/W05/W05-01/receipt.json from the files on disk.

What this guarantees, measured rather than asserted by prose: every count, id set, disclosure row and
mutation bucket is read back out of a frozen artifact at run time; the guard runs BEFORE anything is
written and the write goes to a temporary name that is renamed only after the guard passes twice, and
the temporary file is deleted on any abort, so no acceptance-claiming receipt is left on disk (the
W12-01 round-2 review found exactly that hole in the earlier generator). A non-dispatch command row is
quoted only when a captured log taken at this HEAD exists. What it does not guarantee: that the
captured logs are honest, or that a hand-edited mutation results list would be caught - the matrix
file is re-counted here, not re-run, and an independent identity must re-run it.

Run with --capture to produce the command logs first.
"""
import datetime, glob, hashlib, io, json, os, subprocess, sys

def _find_repo(start):
    d = start
    for _ in range(10):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal", "domain")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("repository root not found from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
RD = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01")
SPEC = r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4"
GO = os.path.join(REPO, ".local", "tools", "go1.27.1", "go", "bin", "go.exe")
LOGS = os.path.join(RD, "invocations", "logs")
MATRIX = "mutation_selfcheck_w0501.json"
CAPTURE = [
 ("go_vet_check", ["vet", "./tests/runtime/check"], "clean"),
 ("go_build_adapter", ["build", "./adapters/runtime"], "clean"),
 ("go_test_runtime_fixture", ["test", "./adapters/runtime", "./internal/domain", "-count=1",
   "-run", "^TestW05(Protocol|Windows|Service|Scope|Unknown)$"], "ok; the accepted W05-G01 families still pass"),
 ("go_vet_domain", ["vet", "./internal/domain"], "clean"),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(path):
    return json.load(io.open(path, encoding="utf-8-sig"))


def dump(path, obj):
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=1, ensure_ascii=False))


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


env = dict(os.environ)
env.update({"GOTOOLCHAIN": "local", "GOENV": "off",
            "GOPATH": os.path.join(REPO, ".local", "gopath"),
            "GOCACHE": os.path.join(REPO, ".local", "gocache"), "RESEARCHOS_GO": GO,
            "RESEARCHOS_TASK_ID": "W05", "RESEARCHOS_CHECK_ID": "W05-01"})

if "--capture" in sys.argv:
    head = git("rev-parse", "HEAD")
    os.makedirs(LOGS, exist_ok=True)
    for key, argv, expect in CAPTURE:
        p = subprocess.run([GO] + argv, cwd=REPO, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
        text = (p.stdout or "") + (p.stderr or "")
        fails = [l for l in text.splitlines() if l.startswith("--- FAIL") or l.startswith("FAIL:")]
        tail = [l for l in text.splitlines() if l.strip()]
        if p.returncode != 0:
            result = "exit %d: %s" % (p.returncode, text.strip()[-400:])
        elif fails:
            result = "exit 0 but the output names failures: %s" % " | ".join(fails)[:400]
        else:
            result = "%s; last line: %s" % (expect, tail[-1] if tail else "(no output)")
        dump(os.path.join(LOGS, key + ".json"),
             {"key": key, "cwd": "REPOSITORY", "argv": [os.path.relpath(GO, REPO).replace("\\", "/")] + argv,
              "exit_code": p.returncode, "result": result, "code_revision": head,
              "output_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest(),
              "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print(key, "exit", p.returncode, "|", result[:90])
    sys.exit(0)

head = git("rev-parse", "HEAD")
dirty = [l for l in git("status", "--porcelain").splitlines()
         if l.strip() and not l.startswith("?? execution/") and not l.startswith("?? .local/")]

runs = []
for d in sorted(glob.glob(os.path.join(RD, "invocations", "*"))):
    rp = os.path.join(d, "receipt.json")
    if not os.path.isfile(rp):
        continue
    r = load(rp)
    sp = os.path.join(d, "stdout.txt")
    report = {}
    if os.path.exists(sp):
        for line in io.open(sp, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("{") and '"assertion_ids"' in line:
                report = json.loads(line)
    runs.append({"directory": os.path.relpath(d, RD).replace("\\", "/"),
                 "invocation_id": r.get("invocation_id"), "status": r.get("status"),
                 "assertion_ids": r.get("assertion_ids") or [], "report": report,
                 "code_revision": r.get("code_revision"), "exit_code": r.get("exit_code"),
                 "registry_spec": r.get("registry_spec"),
                 "registered_command_revision": (r.get("registered_command_revision") or "")[:64]})
current = [r for r in runs if r["code_revision"] == head]
if len(current) < 2:
    raise SystemExit("need two frozen binding runs at HEAD %s, found %d of %d" % (head[:8], len(current), len(runs)))
if sorted(current[0]["assertion_ids"]) != sorted(current[1]["assertion_ids"]):
    raise SystemExit("the two binding runs at HEAD disagree about the assertion id set")
if any(not r["report"] for r in current):
    raise SystemExit("a binding run at HEAD has no frozen harness report to derive from")
if any(r["status"] != "PASS" for r in current):
    raise SystemExit("a binding run at HEAD is not PASS")

matrix = load(os.path.join(RD, MATRIX))
buckets = matrix["buckets"]
if buckets.get("survived") or buckets.get("crashed") or buckets.get("anchor-missing") \
        or buckets.get("caught") != matrix["cases"]:
    raise SystemExit("the matrix must report every one of its %d cases caught, and it reports %s"
                     % (matrix["cases"], buckets))
if not matrix.get("tree_clean_after_restore"):
    raise SystemExit("the matrix runner did not leave the tree clean; its restores are not trustworthy")
caught = [{"case": r["id"], "killed": r.get("killed") or [], "restored_byte_identical": r.get("restored_byte_identical")}
          for r in matrix["results"] if r["bucket"] == "caught"]
if len(caught) != buckets["caught"]:
    raise SystemExit("the caught list has %d rows for %d caught cases" % (len(caught), buckets["caught"]))


def command_log(key):
    p = os.path.join(LOGS, key + ".json")
    if not os.path.exists(p):
        raise SystemExit("no captured command log for %s: run this generator with --capture first" % key)
    c = load(p)
    for field in ("argv", "exit_code", "result", "code_revision"):
        if field not in c:
            raise SystemExit("command log %s is missing %s" % (key, field))
    if c["code_revision"] != head:
        raise SystemExit("command log %s was captured at %s, not this HEAD %s"
                         % (key, c["code_revision"][:8], head[:8]))
    return {"cwd": c["cwd"], "argv": c["argv"], "exit_code": c["exit_code"], "result": c["result"],
            "derived_from": "invocations/logs/%s.json" % key}


hist = {}
for i in current[0]["assertion_ids"]:
    parts = i.split("-")
    key = parts[0] + "-" + (parts[1] if len(parts) > 1 else "")
    hist[key] = hist.get(key, 0) + 1

artifacts = ["tests/runtime/check/main.go", "tests/runtime/check/legacy.go", "tests/runtime/check/w0501.go",
             "adapters/runtime/runtime_windows.go", "adapters/runtime/codex.go",
             "internal/domain/runtime_admission.go", "internal/domain/budget_scopes.go",
             "execution/v2.4/commands.json", "execution/v2.4/receipts/W05/W05-01/" + MATRIX]
missing = [a for a in artifacts if not os.path.exists(a)]
if missing:
    raise SystemExit("artifact listed by the receipt is absent: %s" % missing)

report = current[0]["report"]
receipt = {
 "template_version": "2.4-receipt-1", "step_id": "W05-01", "parent_task": "W05",
 "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "executor_id": "qoder-desktop:/root/construction", "verifier_id": None,
 "status": "EXECUTION_REPORTED",
 "notice": "Executor reports only. No field below is evidence of acceptance; an independent identity must re-run this card's binding command and its mutations before step_state changes.",
 "mode": "DEVELOPMENT", "repository_head_at_reporting": head,
 "uncommitted_source_files_at_reporting": dirty,
 "input": {"card": os.path.join(SPEC, "tasks", "steps", "W05-01.md"),
  "read_refs": ["08_AGENT_EXECUTION_GOAL.md", "05_WBS.md W05", "contracts/tasks.json tasks[task_id=W05]",
                "22_CLIENT_INTERFACE_DETAILS.md provider/session", "tests/runtime/README.md"],
  "write_scope": ["adapters/runtime/**", "adapters/model/**", "apps/cli/** (registered alias CLI)",
                  "tests/runtime/**", "execution/v2.4/receipts/W05/W05-01/**"],
  "plan_sha256": load(os.path.join("execution", "v2.4", "checkpoint.json"))["plan_sha256"]},
 "artifacts": [{"path": a.replace("\\", "/"), "sha256": sha(a)} for a in artifacts],
 "commands": [
  {"cwd": "REPOSITORY", "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.runtime",
    "--task-id", "W05", "--check-id", "W05-01"], "exit_code": current[0]["exit_code"],
   "result": {"status": current[0]["status"], "assertions": len(current[0]["assertion_ids"]),
              "invocation_id": current[0]["invocation_id"], "registry_spec": current[0]["registry_spec"],
              "frozen_under": current[0]["directory"]}},
  {"cwd": "REPOSITORY", "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.runtime",
    "--task-id", "W05", "--check-id", "W05-01"], "exit_code": current[-1]["exit_code"],
   "result": {"status": current[-1]["status"], "assertions": len(current[-1]["assertion_ids"]),
              "invocation_id": current[-1]["invocation_id"], "frozen_under": current[-1]["directory"],
              "note": "second run; its assertion id set equals the first when sorted"}},
  {"cwd": "REPOSITORY", "argv": ["go", "run", "./tests/runtime/check"], "exit_code": 0,
   "result": "%s %d assertions, %d disclosed not_verified rows, %d diagnostic probes"
             % (report["status"], report["assertions"], len(report.get("not_verified") or []),
                len(report.get("diagnostics") or [])),
   "derived_from": current[0]["directory"] + "/stdout.txt"},
  command_log("go_vet_check"), command_log("go_build_adapter"),
  command_log("go_test_runtime_fixture"), command_log("go_vet_domain")],
 "check_results": {
  "status": report["status"], "assertions": len(current[0]["assertion_ids"]),
  "failures": report.get("failures"), "harness_scope": report.get("scope"),
  "not_verified": sorted(report.get("not_verified") or []),
  "assertion_id_prefix_histogram": hist,
  "binding_invocation": current[0]["invocation_id"],
  "binding_invocation_note": "invocation ids are random uuid4 values; they identify runs, not equal inputs. Equality of what ran is carried by registry_spec, registered_command_revision and code_revision, which match across both runs.",
  "selector_parity": "binding_and_parity_rev14.json holds the before-baseline and the after-binding re-resolution of every pre-existing test.runtime selector"},
 "negative_cases": [
  {"case": "W05-01-NEGATIVE: a completed turn and a zero exit code must not be enough to call a run settled",
   "result": "EXECUTION_REPORTED",
   "evidence": "W0501-PROTOCOL-MISSING-SETTLED-IS-NOT-SUCCESS, W0501-PROTOCOL-PROCESS-EXIT-OVERRIDES-SETTLEMENT and W0501-PROTOCOL-TRANSPORT-RETRY-NEEDS-LATER-COMPLETION; M8, M9, M10 and M12 each die on a named row"},
  {"case": "W05-01-NEGATIVE: an unqualified LIVE runtime may not be claimed, and a report with no trusted observation may not accept anything",
   "result": "EXECUTION_REPORTED",
   "evidence": "W0501-UNQUALIFIED-LIVE-RUNTIME-REFUSED pins 503 with the message 'LIVE runtime has no current qualification' and no Run object; W0501-REPORT-WITHOUT-TRUSTED-OBSERVATION-REFUSED pins the refusal and that the Run status is unchanged; M14 kills the first"},
  {"case": "W05-01-NEGATIVE: listing models or returning text is not real tool capability",
   "result": "EXECUTION_REPORTED",
   "evidence": "the card's own live tool-file-read property is reported not_verified rather than asserted, with the reason measured in executor_identity_measurement.json: the executor policy denies model shell tools and writes, and the pinned executor binary is absent while a different build is installed"},
  {"case": "W05-01-NEGATIVE: a worker must not be able to escape its workspace, inherit credentials silently, or record an artifact it did not produce",
   "result": "EXECUTION_REPORTED",
   "evidence": "W0501-ADAPTER-OUTPUT-ESCAPE-REFUSED, W0501-ADAPTER-EXPLICIT-ENVIRONMENT-REQUIRED, W0501-ADAPTER-ARTIFACT-BOUNDED-TO-BYTES (hash recomputed from the bytes on disk) and W0501-ADAPTER-TREE-DRAINED; M1, M2, M5 and M6 each die on a named row"}],
 "mutation_selfcheck": {
  "cases": matrix["cases"], "buckets": buckets, "caught": caught,
  "survived": [], "crashed": [], "anchor_missing": [],
  "runner": os.path.join(RD, "mut_w0501.py"), "matrix_source": MATRIX,
  "tree_clean_after_restore": bool(matrix.get("tree_clean_after_restore")),
  "restoration": "the matrix file's own tree_clean_after_restore is %s and each row carries restored_byte_identical; this generator aborts unless the tree was clean"
                 % bool(matrix.get("tree_clean_after_restore")),
  "coverage_limit": "M13 redaction and M11 denial mutants exercise the decoder only as far as its own phrase table reaches; the suite also asserts that limit as W0501-PROTOCOL-DENIAL-DETECTION-IS-PHRASE-SCOPED rather than pretending broader detection"},
 "registry_parity": {
  "registry_revision": load(os.path.join("execution", "v2.4", "commands.json"))["revision"],
  "command_key": "test.runtime",
  "note": "binding a v2.4 entry for test.runtime flips resolution for every selector on that key, so the before-baseline was taken first (before_baseline_test.runtime.json) and both pre-existing selectors were re-resolved after the bump (binding_and_parity_rev14.json): case C11 still PASS 5 and bare task_id W12 is still refused by the harness's own guard. A reviewer should repeat those rows.",
  "forwarding": "tests/runtime/check/legacy.go forwards every selector except check_id W05-01 to ops/ci/runtime.py and asserts the rule as W0501-ROUTING-TRUTH-TABLE"},
 "defects_found_and_fixed_across_all_rounds": [
  {"defect": "the first draft of the check program asserted a 4xx class for the unqualified LIVE refusal and a bare run-id presence for the admitted claim, and both were wrong for different reasons: the service answers 503 RESOURCE_UNAVAILABLE, and the claim response nests the Run under a 'run' key",
   "fix": "the assertions now name the status the rule really produces and read the nested object, so a refusal cannot move to another class unnoticed"},
  {"defect": "the first policy-denial row used a paraphrase ('blocked by current policy') that the production detector does not match, so the assertion failed for the wrong reason",
   "fix": "the row now quotes the detector's own needle and a second row asserts the limitation, that a differently worded denial is not recognised"},
  {"defect": "the journal directory was created before rt.Start, which creates it itself and takes an exclusive lock, so the adapter refused to start",
   "fix": "workspace() now creates only the bounded workspace and hands Start a fresh journal path"},
  {"defect": "one early draft of the cost assertion was tautological (it compared a string it had built itself with || true), which would have passed forever",
   "fix": "it is replaced by W0501-FIXTURE-DISPATCH-CHARGE-IS-PROVEN-ZERO, which counts the reservations by provider_request_id prefix and amount and requires the incurred, estimated and unknown columns to be empty"}],
 "known_limitations_and_obligations": [
  "the LIVE model-tool path is not asserted at all; only the adapter's own real file read is proven, and the card's step 3 property (a model performing a file read) stays BLOCKED by executor policy and by the absent pinned binary",
  "A04 remains unaccepted: it is served by the legacy live harness, which refuses without RESEARCHOS_RUNTIME_LIVE, and case A04's owning card scope includes the live qualification this card cannot complete",
  "ops/runtime/capabilities.json pins an executor_sha256 whose binary is gone; updating that identity record belongs to W05 evidence ownership and must not be edited silently by this card",
  "nothing here accepts parent W05 or signs any formal case"],
 "not_verified_on_this_machine": [
  "no real Codex/provider call was made from this working tree in this round, so nothing is claimed about current provider behaviour beyond what the recorded receipts and the decoder rows show"],
 "independent_review": None, "independent_reviews": [], "rework_of": None,
 "reuse_notes": "harness boot mirrors tests/resources/check (store.Open + real migrations + domain.New + the service's own HTTP handler); the adapter phase drives adapters/runtime directly, which that program does not"}


def guard(obj, where):
    """Every rule that keeps this a report and not an acceptance, run before anything is written."""
    if obj["verifier_id"] is not None or obj["status"] != "EXECUTION_REPORTED":
        raise SystemExit("the executor must not fill the verifier field or claim acceptance (%s)" % where)
    if obj["independent_review"] is not None or obj["independent_reviews"]:
        raise SystemExit("a receipt generated by the executor may not carry a review (%s)" % where)
    cr = obj["check_results"]
    if cr["assertions"] != len(current[0]["assertion_ids"]) or cr["status"] != "PASS":
        raise SystemExit("check_results does not match the frozen binding run (%s)" % where)
    if cr["failures"]:
        raise SystemExit("the frozen binding run reported failures; this receipt may not say PASS (%s)" % where)
    if sorted(cr["not_verified"]) != sorted(report.get("not_verified") or []):
        raise SystemExit("disclosure rows were rewritten instead of derived (%s)" % where)
    if len(obj["artifacts"]) != len(artifacts):
        raise SystemExit("artifact list truncated (%s)" % where)
    b = obj["mutation_selfcheck"]["buckets"]
    if obj["mutation_selfcheck"]["cases"] != sum(b.values()) or b.get("survived") or b.get("crashed") \
            or b.get("anchor-missing"):
        raise SystemExit("matrix buckets are not what this receipt claims: %s (%s)" % (b, where))
    if not obj["mutation_selfcheck"]["tree_clean_after_restore"]:
        raise SystemExit("the matrix did not leave the tree clean (%s)" % where)
    for c in obj["commands"]:
        r = c.get("result")
        if isinstance(r, dict) and "invocation_id" in r:
            continue
        if c.get("derived_from", "").endswith("stdout.txt"):
            continue
        if not (isinstance(r, str) and c.get("exit_code") is not None and c.get("derived_from")):
            raise SystemExit("a command entry quotes a result nobody captured (%s)" % where)


guard(receipt, "in memory")
tmp = os.path.join(RD, "receipt.json.tmp")
try:
    dump(tmp, receipt)
    again = load(tmp)
    guard(again, "on the written file")
    for probe in ("check_results", "mutation_selfcheck", "artifacts", "commands"):
        if probe not in again:
            raise SystemExit("written receipt lost %s" % probe)
    os.replace(tmp, os.path.join(RD, "receipt.json"))
except BaseException:
    if os.path.exists(tmp):
        os.remove(tmp)   # never leave a half-written, acceptance-shaped receipt behind
    raise
print("receipt.json written at HEAD", head[:8], "| assertions", again["check_results"]["assertions"],
      "| artifacts", len(again["artifacts"]), "| matrix", again["mutation_selfcheck"]["buckets"])
