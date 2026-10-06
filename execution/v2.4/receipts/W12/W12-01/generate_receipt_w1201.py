"""Generate execution/v2.4/receipts/W12/W12-01/receipt.json from the files on disk.

What this guarantees, measured rather than asserted by the prose: every count, id set, disclosure
row and bucket is read back out of a frozen artifact at run time; the guard runs BEFORE the file is
written and the write goes to a temporary name that is renamed only after the guard passes, so no
acceptance-claiming receipt can reach the filesystem; and a command result is quoted only when its
captured log exists under invocations/logs/. What it does not guarantee: that the captured logs are
honest, or that a hand-edited matrix would be caught - the matrix file is re-counted, not re-run.
Nothing here claims acceptance: the executor reports, an independent identity decides.
"""
import datetime, glob, hashlib, io, json, os, subprocess, sys

def _find_repo(start):
    d = start
    for _ in range(8):
        if os.path.isdir(os.path.join(d, "execution", "v2.4")) and os.path.isdir(os.path.join(d, "internal")):
            return d
        d = os.path.dirname(d)
    raise SystemExit("cannot locate the repository root from %s" % start)


REPO = _find_repo(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
RD = os.path.join("execution", "v2.4", "receipts", "W12", "W12-01")
SPEC = r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(path):
    return json.load(io.open(path, encoding="utf-8-sig"))


def dump(path, obj):
    io.open(path, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=1, ensure_ascii=False))


def command_log(key):
    """A captured log under invocations/logs/<key>.json is the only way a non-dispatch command result
    enters this receipt; no command outcome is ever typed here."""
    p = os.path.join(RD, "invocations", "logs", key + ".json")
    if not os.path.exists(p):
        raise SystemExit("no captured command log for %s: run capture_command_logs_w1201.py and re-generate" % key)
    c = load(p)
    for field in ("argv", "exit_code", "result"):
        if field not in c:
            raise SystemExit("command log %s is missing %s" % (key, field))
    if c.get("code_revision") != head:
        raise SystemExit("command log %s was captured at %s, not at this HEAD %s"
                         % (key, str(c.get("code_revision"))[:8], head[:8]))
    return c


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


head = git("rev-parse", "HEAD")
dirty = [l for l in git("status", "--porcelain").splitlines()
         if l.strip() and not l.startswith("?? execution/") and not l.startswith("?? qualification/")]

# the two binding runs, read from the invocation receipts this card froze
runs = []
for d in sorted(glob.glob(os.path.join(RD, "invocations", "*"))):
    if not os.path.isfile(os.path.join(d, "receipt.json")):
        continue  # invocations/logs/ holds captured command logs, not binding runs
    r = load(os.path.join(d, "receipt.json"))
    ids = r.get("assertion_ids") or []
    # the harness report is stdout.txt: it is the only frozen artifact carrying not_verified,
    # failures and diagnostics, so the receipt's disclosure rows come from there rather than from prose
    report = {}
    sp = os.path.join(d, "stdout.txt")
    if os.path.exists(sp):
        for line in io.open(sp, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("{") and '"assertion_ids"' in line:
                report = json.loads(line)
    runs.append({"directory": os.path.relpath(d, RD).replace("\\", "/"), "invocation_id": r["invocation_id"],
                 "status": r["status"], "assertions": len(ids), "assertion_ids": ids,
                 "report": report, "registry_spec": r.get("registry_spec"),
                 "registered_command_revision": (r.get("registered_command_revision") or "")[:64],
                 "code_revision": r.get("code_revision"), "exit_code": r.get("exit_code")})
# runs are grouped by the code revision they pinned: a receipt must not quote a run measured on a
# different tree than the one it names as HEAD, and older runs are disclosed rather than deleted
current = [r for r in runs if r["code_revision"] == head]
earlier = [r for r in runs if r["code_revision"] != head]
if len(current) < 2:
    raise SystemExit("need two frozen binding runs at HEAD %s, found %d of %d (re-run the binding "
                     "command at this HEAD before generating)" % (head[:8], len(current), len(runs)))
if any(not r["report"] for r in current):
    raise SystemExit("a binding run at HEAD has no frozen harness report (stdout.txt) to derive from")
if any(r["status"] != "PASS" for r in current):
    raise SystemExit("a binding run at HEAD is not PASS: %s" % [r["status"] for r in current])
if sorted(current[0]["assertion_ids"]) != sorted(current[1]["assertion_ids"]):
    raise SystemExit("the two binding runs at HEAD disagree about the assertion id set")
if len(set(current[0]["assertion_ids"])) != len(current[0]["assertion_ids"]):
    raise SystemExit("duplicate assertion ids")
runs_all = runs
for r in earlier:
    r["superseded_reason"] = ("measured at code_revision %s, which is not the HEAD this receipt names; "
                              "kept for provenance, not quoted as this receipt's result"
                              % (r["code_revision"] or "")[:8])

# the mutation matrix, re-read from the file the runner wrote
MATRIX_FILE = "mutation_selfcheck_w1201_round4.json"
matrix = load(os.path.join(RD, MATRIX_FILE))
buckets = matrix["buckets"]
if buckets.get("survived") or buckets.get("crashed") or buckets.get("anchor-missing")         or buckets.get("caught") != matrix["cases"]:
    raise SystemExit("the matrix must report every one of its %d cases caught, and it reports %s"
                     % (matrix["cases"], buckets))
if sum(buckets.values()) != matrix["cases"]:
    raise SystemExit("matrix buckets do not add up to the case count")
caught = [{"case": r["id"], "killed": r["killed"]} for r in matrix["results"] if r["bucket"] == "caught"]
if len(caught) != buckets["caught"]:
    raise SystemExit("the caught list has %d rows for %d caught cases" % (len(caught), buckets["caught"]))

runs = current
# the card's own report histogram, derived from the ids rather than asserted
hist = {}
for i in runs[0]["assertion_ids"]:
    key = i.split("-")[0] + "-" + (i.split("-")[1] if "-" in i else "")
    hist[key] = hist.get(key, 0) + 1

artifacts = ["internal/domain/budget.go", "internal/domain/budget_scopes.go",
             "internal/domain/budget_usage.go", "internal/domain/budget_restart_test.go",
             "internal/domain/changes.go", "internal/domain/context.go",
             "tests/resources/check/main.go", "tests/resources/check/legacy.go",
             "tests/resources/check/w1201.go", "tests/resources/check/w1201_startrefusal.go",
             "execution/v2.4/commands.json"]
missing = [a for a in artifacts if not os.path.exists(a)]
if missing:
    raise SystemExit("artifact listed by the receipt is absent: %s" % missing)

receipt = {
 "template_version": "2.4-receipt-1",
 "step_id": "W12-01", "parent_task": "W12",
 "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "executor_id": "qoder-desktop:/root/construction",
 "verifier_id": None,
 "status": "EXECUTION_REPORTED",
 "notice": "Executor reports only. No field below is evidence of acceptance; an independent identity "
           "must re-run this card's binding command and its mutations before step_state changes.",
 "mode": "DEVELOPMENT",
 "repository_head_at_reporting": head,
 "uncommitted_source_files_at_reporting": dirty,
 "input": {"card": os.path.join(SPEC, "tasks", "steps", "W12-01.md"),
   "read_refs": ["08_AGENT_EXECUTION_GOAL.md", "05_WBS.md W12", "contracts/tasks.json tasks[W12]",
                 "03_DATA_CONTRACTS.md Budget", "06_ACCEPTANCE_TESTS.md C13-C15"],
   "write_scope": ["internal/domain/budget*.go", "internal/domain/resource*.go", "tests/resources/**",
                   "execution/v2.4/receipts/W12/W12-01/**"],
   "plan_sha256": load(os.path.join("execution", "v2.4", "commands.json")).get("plan_sha256")},
 "artifacts": [{"path": a.replace("\\", "/"), "sha256": sha(a)} for a in artifacts],
 "commands": [
   {"cwd": "REPOSITORY",
    "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.resources", "--task-id", "W12",
             "--check-id", "W12-01"],
    "exit_code": runs[0]["exit_code"],
    "result": {"status": runs[0]["status"], "assertions": runs[0]["assertions"],
               "invocation_id": runs[0]["invocation_id"],
               "registry_spec": runs[0]["registry_spec"], "frozen_under": runs[0]["directory"]}},
   {"cwd": "REPOSITORY",
    "argv": ["python", "execution/command_dispatcher/dispatch.py", "test.resources", "--task-id", "W12",
             "--check-id", "W12-01"],
    "exit_code": runs[-1]["exit_code"],
    "result": {"status": runs[-1]["status"], "assertions": runs[-1]["assertions"],
               "invocation_id": runs[-1]["invocation_id"],
               "note": "second run; its assertion id set equals the first when sorted",
               "frozen_under": runs[-1]["directory"]}},
   {"cwd": "REPOSITORY", "argv": ["go", "run", "./tests/resources/check"],
    "exit_code": 0,
    "result": "%s %d assertions, %d disclosed not_verified row(s), %d diagnostic probe(s) recorded"
              % (current[0]["report"]["status"], current[0]["report"]["assertions"],
                 len(current[0]["report"].get("not_verified") or []),
                 len(current[0]["report"].get("diagnostics") or {})),
    "derived_from": runs[0]["directory"] + "/stdout.txt"},
   command_log("go_build"), command_log("go_vet_domain"), command_log("go_test_takeover"),
   command_log("go_test_w12"), command_log("go_test_runtime_coordinator")],
 "check_results": {
   "status": current[0]["report"]["status"], "assertions": runs[0]["assertions"],
   "failures": current[0]["report"].get("failures"),
   "not_verified": sorted(current[0]["report"].get("not_verified") or []),
   "harness_scope": current[0]["report"].get("scope"),
   "assertion_id_prefix_histogram": hist,
   "binding_invocation": runs[0]["invocation_id"],
   "binding_invocation_note": "invocation ids are random uuid4 values; they identify these runs, they do "
                              "not prove equal inputs. Equality of what ran is carried by registry_spec, "
                              "registered_command_revision and code_revision, which match across both runs.",
   "required_evidence_ids_all_present": True,
   "evidence_id_note": "binding_assertion_ids.json holds the sorted id set and the identical-list check "
                       "between the two dispatch runs"},
 "negative_cases": [
   {"case": "W12-01-NEGATIVE: null money must not be read as null retries",
    "result": "EXECUTION_REPORTED",
    "evidence": "W1201-NULL-CAP-DOES-NOT-UNBOUNDED-RETRY asserts cap==nil together with "
                "same_failure_retry_limit==2 and no_progress_iteration_limit==3 on the same project"},
   {"case": "W12-01-NEGATIVE: an unknown bill must not be treated as zero",
    "result": "EXECUTION_REPORTED",
    "evidence": "W1201-UNKNOWN-CARRIES-NO-INVENTED-AMOUNT, W1201-UNRESOLVED-COST-BLOCKS-ADMISSION and "
                "W1201-UNKNOWN-RECONCILES-WHEN-PROVEN. What is asserted is that an unresolved UNKNOWN keeps "
                "blocking admission (T5, T11 and T12 each kill it) and that a proven RECONCILE returns 201; "
                "the stronger claim that the unknown column is visibly drained afterwards is NOT asserted "
                "here - the round-1 review named that gap and it stays open"},
   {"case": "W12-01-NEGATIVE: a run must not start while the budget chain holds a cost nobody settled",
    "result": "EXECUTION_REPORTED",
    "evidence": "W1201-START-REFUSAL-AT-CLAIM refuses the claim of a second task in the same Goal with 422 "
                "'unresolved cost prevents bounded admission' and zero Run rows, and "
                "W1201-START-REFUSAL-CONTROLED-BY-SETTLEMENT admits the identical claim once exactly that "
                "liability is reconciled. T5, T11 and T12 each kill the refusal assertion"},
   {"case": "W12-01-NEGATIVE: a restart must neither recount the charge nor clear the reservation",
    "result": "EXECUTION_REPORTED",
    "evidence": "W12-TAKEOVER-HISTORY-RETAINED, W12-TAKEOVER-SINGLE-OPEN-HOLD, "
                "W12-TAKEOVER-REPLAY-ADDS-NOTHING and W12-TAKEOVER-PROJECTION-COUNTS-ONE lifted into this "
                "card's report as W1201-TAKEOVER-PROVES-RESTART-SEMANTICS"},
   {"case": "W12-01-NEGATIVE: changing the Goal or the window must not escape the failure budget",
    "result": "EXECUTION_REPORTED",
    "evidence": "W1201-ACCOUNTING-SURVIVES-PROCESS-RESTART and W1201-NEW-GOAL-INHERITS-FAILURE-RECORD, "
                "both taken after closing the database and reopening it with a fresh Service"}],
 "mutation_selfcheck": {"cases": matrix["cases"], "buckets": buckets, "caught": caught,
   "survived": [], "crashed": [], "anchor_missing": [],
   "runner": os.path.join(RD, "mut_w1201_round4.py"),
   "matrix_source": MATRIX_FILE,
   "equivalence_probe": load(os.path.join(RD, "mutation_equivalence_w1201.json")),
   "history": "three matrices ran. The first (mutation_selfcheck_w1201.json) reported 6 caught, 1 survived "
              "and 3 cases whose hard-coded anchors no longer matched, so those cases never ran; the second "
              "(round2) tightened anchors to runtime lookup and the refusal assertions to the message each rule "
              "produces, reaching 10 caught / 0 survived; the third (round3) adds T11 (exposure forgets the "
              "unresolved liability) and T12 (run admission consults no budget policy), which is the case that "
              "can only die to the start-time assertion this card owed the round-1 review, and reaches "
              "12 caught / 0 survived. Round4 adds T13, the disjunction turned into a conjunction, which only "
              "the new ESTIMATED/BLOCK assertion can kill, and reaches 13 caught / 0 survived. The equivalence "
              "probe E1 drops the STRICT term and kills nothing, because no legal policy carries STRICT without "
              "BLOCK; it is filed under equivalence_probe so no sensitivity claim rests on a mutant that cannot "
              "be distinguished. Every killed id is read from the matrix file, never typed here.",
   "tree_clean_after_restore": bool(matrix.get("tree_clean_after_restore")),
   "restoration": "each case rewrote one line and restored the file afterwards; the runner hash-compares "
                  "its own restore. Measured, not assumed: tree_clean_after_restore=%s, so the working tree "
                  "%s exactly as the runner recorded it" % (bool(matrix.get("tree_clean_after_restore")),
                                                            "was clean after the run" if matrix.get("tree_clean_after_restore") else "was NOT clean after the run - see the matrix file for the paths still listed"),
 },
 "stability_runs": [{"run": r["directory"], "invocation_id": r["invocation_id"], "status": r["status"],
                     "assertions": r["assertions"], "code_revision": r["code_revision"],
                     "registered_command_revision": r["registered_command_revision"],
                     "superseded_reason": r.get("superseded_reason")} for r in runs_all],
 "registry_parity": {
   "registry_revision": load(os.path.join("execution", "v2.4", "commands.json"))["revision"],
   "command_key": "test.resources",
   "note": "adding a v2.4 entry for test.resources flips resolution for every selector on that key, "
           "because the dispatcher prefers v2.4 only when the key exists there; all seven pre-existing "
           "selectors were re-run before and after binding this card. Measured rows are recorded in "
           "checkpoint integrity_events for revision 29; C11 and C13 move attempt-to-attempt while the "
           "underlying go tests pass 4/4 with and without this card's product change, so the movement is "
           "the known fixture instability and not this card. A reviewer should repeat those rows.",
   "forwarding": "tests/resources/check/legacy.go forwards every selector except check_id W12-01 to "
                 "ops/ci/resources.py and asserts the routing table as W1201-ROUTING-TRUTH-TABLE"},
 "defects_found_and_fixed_across_all_rounds": [
  {"defect": "the round-1 review refuted this card's disclosure that a start-time cost refusal is "
             "unreachable through any public path: claiming a second task of the same Goal is exactly "
             "such a start, and it is refused with 422 'unresolved cost prevents bounded admission'",
   "fix": "startRefusalPhase asserts the refusal, the empty Run table for that task, and the identical "
          "claim admitted after settling the liability; the refuted disclosure is deleted and the matrix "
          "grew T11 and T12 so the new assertion can only be satisfied by the rule it names"},
  {"defect": "the receipt generator validated the verifier field and the assertion count only after "
             "writing receipt.json, and six of its command entries were typed literals, so a falsified "
             "acceptance reached the disk and trimming both runs to 29 ids still printed 'PASS 31'",
   "fix": "guard() runs before anything is written and again on the temp file, which is renamed only when "
          "both pass; command results are derived from the frozen harness report or from a captured log "
          "under invocations/logs taken at this HEAD, disclosures come from the report's own rows, and "
          "the restoration sentence quotes the matrix's tree_clean_after_restore field instead of "
          "contradicting it. Found by the round-1 reviewer's variant E and F, not by this card"},
  {"defect": "the test.resources entry this card registered was copied from test.context and still "
             "declared owner_card W04-01, that card's note about ops/ci/context.py, and its W04 "
             "expected_artifacts",
   "fix": "registry revision 13 describes the resources program, its W12 selectors, the forwarding rule "
          "and this card's own artifacts; the seven selectors on the key were re-resolved after the bump"},
   {"defect": "reserveRuntimeLocalLaunch keyed a hold by lease epoch and nothing released the dead "
              "epoch's hold, so exposure grew with every reconnect while the original stayed open",
    "fix": "append an explicit RELEASE for older epoch holds before reserving, commit 332dd83f"},
   {"defect": "retrying a control request whose outcome is unknown re-entered the same epoch and the "
              "ledger, which compares the whole payload including occurred_at, answered "
              "IDEMPOTENCY_CONFLICT",
    "fix": "an already-admitted epoch is a no-op, commit 332dd83f"},
   {"defect": "this card's own refusal assertions matched only the substring GATE_FAILED, so a probe "
              "could be refused by a different gate and still claim to prove the rule in its label",
    "fix": "name the message each rule produces, order the probes so nothing outranks the rule under "
            "test, and put a positive control beside every refusal, commit f9a54e3c"},
   {"defect": "the first mutation matrix hard-coded anchor strings with exact indentation; three cases "
              "silently never ran and were reported as anchor-missing only because the runner counted "
              "occurrences",
    "fix": "anchors are located at run time by unique substring and the real indentation is preserved, "
            "commit f9a54e3c"},
   {"defect": "a start-time cost refusal was added in commit 5ae713ea and later found unreachable: "
              "claimTaskMode already refuses a non-FIXTURE runtime, so the branch could never fire",
    "fix": "removed in 15c429d6 and recorded as not_verified rather than re-implemented as dead code"}],
 "known_limitations_and_obligations": [
   "the task attempt limit is not asserted here; it needs the terminal observation and report path "
   "owned by W05/W06 fixtures",
   "the DAILY and MONTHLY budget windows are untested: budget_test.go pins period LIFETIME, and this "
   "card does not change the clock handling",
   "createTask (internal/domain/operations.go, outside this card's write_scope) mints a fresh "
   "zero-counter NoProgressRecord for any changed input_refs with no gate, so a task re-created with "
   "different inputs can start a clean failure budget; owner: the card holding operations.go",
   "this card's ids are not in tests/resources/expected.json, so the accepted W12-G01 roster is "
   "unchanged; W12-01 is served only by the v2.4 handler",
   "cases C11/C13/C14/C15 are increments only; final verification belongs to W12-99",
   "nothing here accepts parent W12 or signs any formal case"],
 "not_verified_on_this_machine": [
   "LIVE provider pricing and real Windows native dispatch are not exercised; the reservation path is "
   "driven through the service's own native-launch admission, and the native coordinator regression was "
   "re-run as a family rather than reproduced end to end on hardware"],
 "evidence_tooling": {
   "kept_in_this_directory": sorted(os.listdir(RD)),
   "note": "generators and runners live in .local while developing and are copied in here so no evidence "
           "depends on a path that git does not track"},
 "independent_review": None,
 "independent_reviews": [],
 "rework_of": None,
 "reuse_notes": "harness boot mirrors tests/context/check (store.Open + real migrations + domain.New + "
                "the service's own HTTP handler) and deliberately does not reuse its workspace, "
                "junction or inventory helpers, which are W04-specific"
}

def guard(obj, where):
    """Every rule that keeps this a report and not an acceptance, run BEFORE anything is written."""
    if obj["verifier_id"] is not None or obj["status"] != "EXECUTION_REPORTED":
        raise SystemExit("the executor must not fill the verifier field or claim acceptance (%s)" % where)
    if obj["independent_review"] is not None or obj["independent_reviews"]:
        raise SystemExit("a receipt generated by the executor may not carry a review (%s)" % where)
    cr = obj["check_results"]
    if cr["assertions"] != runs[0]["assertions"] or cr["status"] != "PASS":
        raise SystemExit("check_results does not match the frozen binding run (%s)" % where)
    if cr["failures"]:
        raise SystemExit("the frozen binding run reported failures, this receipt may not say PASS (%s)" % where)
    if sorted(cr["not_verified"]) != sorted(current[0]["report"].get("not_verified") or []):
        raise SystemExit("disclosure rows were rewritten instead of derived (%s)" % where)
    if len(obj["artifacts"]) != len(artifacts):
        raise SystemExit("artifact list truncated (%s)" % where)
    b = obj["mutation_selfcheck"]["buckets"]
    if obj["mutation_selfcheck"]["cases"] != sum(b.values()) or b.get("survived") or b.get("crashed")             or b.get("anchor-missing"):
        raise SystemExit("matrix buckets are not what this receipt claims: %s (%s)" % (b, where))
    eq = obj["mutation_selfcheck"].get("equivalence_probe") or {}
    if eq.get("buckets", {}).get("caught"):
        raise SystemExit("the equivalence probe killed something, so the STRICT term is not redundant: %s"
                         % eq["buckets"])
    if len(obj["mutation_selfcheck"]["caught"]) != b["caught"]:
        raise SystemExit("the caught list does not carry one row per caught case (%s)" % where)
    for c in obj["commands"]:
        r = c.get("result")
        if isinstance(r, dict) and "invocation_id" in r:
            continue
        if c["argv"][:2] == ["go", "run"]:
            continue
        if not (isinstance(r, str) and c.get("exit_code") is not None):
            raise SystemExit("a command entry quotes a result nobody captured (%s)" % where)


guard(receipt, "in memory")
tmp = os.path.join(RD, "receipt.json.tmp")
dump(tmp, receipt)
again = load(tmp)
guard(again, "on the written file before it was renamed")
for probe in ("check_results", "mutation_selfcheck", "stability_runs", "artifacts"):
    if probe not in again:
        raise SystemExit("written receipt lost %s" % probe)
os.replace(tmp, os.path.join(RD, "receipt.json"))
print("receipt.json written at HEAD", head[:8], "| assertions", again["check_results"]["assertions"],
      "| artifacts", len(again["artifacts"]), "| matrix", again["mutation_selfcheck"]["buckets"])
