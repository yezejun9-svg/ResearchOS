"""Register W05-01 as ACCEPTED from an independent verdict, then move the checkpoint.

Written before any verdict exists, so it can only succeed after one does. Every figure is recomputed
from disk, the verifier identity is taken from the verdict file rather than from here, and it refuses
when the evidence does not support acceptance. Failure counters are appended to, never rewritten.
"""
import argparse, datetime, glob, hashlib, io, json, os, subprocess, sys

def _root():
    # was dirname(__file__)/".." while the script lived in .local; kept working from either place
    g = os.path.abspath(os.path.dirname(__file__))
    while g != os.path.dirname(g):
        if os.path.exists(os.path.join(g, "execution", "v2.4", "commands.json")):
            return g
        g = os.path.dirname(g)
    raise RuntimeError("repository root not found from " + __file__)


REPO = _root()
os.chdir(REPO)
SPEC = r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4"
RD = os.path.join("execution", "v2.4", "receipts", "W05", "W05-01")
STATE = os.path.join("execution", "v2.4", "step_state.json")
CP = os.path.join("execution", "v2.4", "checkpoint.json")
EXECUTOR = "qoder-desktop:/root/construction"
# The plan of record has used ACCEPT, ACCEPT_WITH_LIMITATIONS and ACCEPT_WITH_RESERVATIONS (W04-02 was
# registered with the last of these), so all three are registrable - but only when the verdict carries no
# blocking_issues, which is checked below. ACCEPT_BLOCKED_RECORDING is deliberately absent: round 1 of
# this card used exactly that word to say the increment reproduces while recording is refused, and a
# script that matched on an "ACCEPT" prefix would have registered it.
ACCEPTS = ("ACCEPT", "ACCEPT_WITH_LIMITATIONS", "ACCEPT_WITH_RESERVATIONS")
NON_REGISTRABLE = ("ACCEPT_BLOCKED_RECORDING", "REJECT", "REJECT_FOR_REWORK")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def dump(p, obj):
    io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=1, ensure_ascii=False))


def find_verdict():
    """The newest verdict on disk that is an accept, postdates every rejection, and is a fresh identity."""
    files = [f for f in sorted(os.listdir(RD)) if f.startswith("independent_review") and f.endswith(".json")]
    if not files:
        raise SystemExit("no independent review for W05-01 has been delivered")
    rejects, reject_reviewers, reject_at = [], set(), ""
    for f in files:
        v = load(os.path.join(RD, f))
        if str(v.get("verdict") or "").upper() in ("REJECT", "REJECTED", "REWORK", "REWORK_REQUIRED"):
            rejects.append(f)
            reject_at = max(reject_at, str(v.get("reviewed_at") or ""))
            reject_reviewers.add(v.get("reviewer_id") or v.get("verifier_id"))
        else:
            print("%s verdict=%r" % (f, v.get("verdict")))
    best, best_at = None, ""
    for f in files:
        v = load(os.path.join(RD, f))
        if v.get("verdict") in NON_REGISTRABLE:
            print("%s verdict=%r is not registrable by name" % (f, v.get("verdict")))
            continue
        if v.get("verdict") not in ACCEPTS:
            continue
        at = str(v.get("reviewed_at") or "")
        if reject_at and at <= reject_at:
            print("%s accepts at %s, which does not postdate a rejection at %s: a reviewer that began "
                  "before the blocking items existed is not the post-remediation verdict" % (f, at, reject_at))
            continue
        if at >= best_at:
            best, best_at = (f, v), at
    if best is None:
        raise SystemExit("no registrable ACCEPT for W05-01 (rejections on file: %s)" % (rejects or "none"))
    fname, verdict = best
    vid = verdict.get("reviewer_id") or verdict.get("verifier_id")
    if not vid or vid == EXECUTOR or vid in reject_reviewers:
        raise SystemExit("verdict identity is missing, is the executor, or already ruled on this tree: %r" % vid)
    if verdict.get("blocking_issues"):
        # a verdict that lists items to fix before recording is not a recording authorisation,
        # whatever its verdict word says
        raise SystemExit("%s says %s while still naming %d blocking issue(s)" %
                         (fname, verdict["verdict"], len(verdict["blocking_issues"])))
    if verdict.get("verdict") == "ACCEPT_WITH_LIMITATIONS" and not (
            verdict.get("limitations") or verdict.get("acceptance_scope")):
        raise SystemExit("an accept-with-limitations must state the limitations this script can carry forward")
    return fname, verdict, vid


ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
args = ap.parse_args()

state = load(STATE)
if any(s.get("id") == "W05-01" for s in state["steps"]):
    raise SystemExit("W05-01 already has a step_state record")
cp = load(CP)
frozen = {(RD, e["path"]) for s in state["steps"] for e in s.get("evidence", [])}
for guard in (STATE, CP):
    if os.path.abspath(guard) in {os.path.abspath(os.path.join("execution", "v2.4", p)) for _, p in frozen}:
        raise SystemExit("a state file is itself registered as evidence; stop and reconcile")

verdict_file, verdict, vid = find_verdict()
if args.dry_run:
    print("registrable: %s verdict=%s by %s" % (verdict_file, verdict["verdict"], vid))
    raise SystemExit(0)

receipt = load(os.path.join(RD, "receipt.json"))
if receipt.get("status") != "EXECUTION_REPORTED" or receipt.get("verifier_id") is not None:
    raise SystemExit("the receipt must stay an executor report; acceptance lives in step_state and the verdict")

# a registration that carries only limitations is how a duty stated in a receipt never reached the
# continuation state, which the round-2 reviewer measured directly; reservations travel too
carried = ["%s (W05-01 %s, limitation): %s" % (i, verdict_file, t)
           for i, t in enumerate(verdict.get("limitations") or [], 1)]
carried += ["%s (W05-01 %s, reservation): %s" % (len(carried) + k, verdict_file, t)
            for k, t in enumerate(verdict.get("reservations") or [], 1)]

present = sorted(os.listdir(RD))
needed = ("receipt.json", "mutation_selfcheck_w0501.json", "binding_and_parity_rev14.json",
          "before_baseline_test.runtime.json", "executor_identity_measurement.json",
          "receipt_selfaudit.json", verdict_file)
for r in ("independent_review_round1.json", "independent_review_round2.json", "independent_review_round3.json"):
    if r not in present:
        raise SystemExit("this card history is incomplete, refusing to register without " + r)
missing = [n for n in needed if n not in present]
if missing:
    raise SystemExit("required evidence file is not in the receipt directory: %s" % missing)

now = datetime.datetime.now(datetime.timezone.utc)
state["steps"].append({
 "id": "W05-01", "status": "ACCEPTED", "executor_id": EXECUTOR, "verifier_id": vid,
 "accepted_at": now.isoformat(), "verdict": verdict["verdict"],
 "verdict_file": "receipts/W05/W05-01/" + verdict_file,
 "note": ("card-level increment only; parent W05 and case A04 and parent W05 are not accepted here"),
 "evidence": [{"path": "receipts/W05/W05-01/" + f, "sha256": sha(os.path.join(RD, f))}
              for f in present if not os.path.isdir(os.path.join(RD, f))]})
dump(STATE, state)

out = subprocess.run([sys.executable, os.path.join(SPEC, "tools", "task_packet.py"), "next", "--state", STATE],
                     capture_output=True, text=True, encoding="utf-8", errors="replace")
nxt = None
if out.returncode == 0:
    try:
        nxt = json.loads(out.stdout)
    except ValueError:
        raise SystemExit("task_packet next produced no JSON: %r" % out.stdout[:400])
nxt_id = ((nxt or {}).get("step") or {}).get("id")
if not nxt_id:
    raise SystemExit("task_packet next named no step after the acceptance: rc=%s out=%r"
                     % (out.returncode, out.stdout[:400]))

old = cp["revision"]
cp["revision"] = old + 1
cp["expected_previous_revision"] = old
cp["current_step_id"] = None
cp["next_step_id"] = nxt_id
cp["accepted_steps"] = cp.get("accepted_steps", []) + ["W05-01"]
cp["failure_counters"].append({
 "origin_key": "W05-01/" + verdict_file, "status": verdict["verdict"], "mid_card_repairs": 0,
 "recorded_at": now.isoformat(), "reviewer_id": vid,
 "disclosed_incidents": [
   "W05-01 disclosure: the LIVE model-tool capability is not asserted at all. Model shell execution and "
   "model workspace writes are denied by the executor policy recorded in ops/runtime/capabilities.json, "
   "and the executor binary pinned by that record is absent while a different build is installed, so the "
   "live identity cannot be re-qualified without substituting the binary, which the card forbids. A real "
   "file read is proven only through the adapter phase, which runs without a model",
   "W05-01 self-caught defects: an early draft asserted a 4xx class for the unqualified LIVE refusal "
   "(the service really answers 503 RESOURCE_UNAVAILABLE), read the claim reply's Run from the wrong "
   "level, created the journal directory the adapter must create itself, paraphrased the denial needle "
   "the decoder does not match, and one cost assertion was tautological until it was replaced by a "
   "count over reservations keyed by provider_request_id and amount",
   "W05-01 tooling lesson repeated: the mutation runner and receipt generator both resolve the "
   "repository root by walking up from their own path, because a copied script that assumes "
   'dirname(__file__)/\"..\" points at a tree that is not the repository',
   "this card was reviewed three times before the current round and each review found something the "
   "executor had asserted too generously: round 1 caught an executor-identity comparison that returned "
   "false for every input because it demanded a sha256: prefix the record does not store, round 2 caught a "
   "parity note claiming a freshness its captured logs did not have and a provider disclosure that blamed "
   "the absent executor binary for an upstream unbound client, and round 3 caught a disclosure row asserting "
   "that nothing drives turn.failed while a passing accepted test inside this cards own write scope does, "
   "plus a summary sentence that said all 23 mapped methods carry an empty rpc_binding when twenty do, one "
   "is annotated n/a as a Go-owned catalog and two name something",
   "the positive control W0501-PINNED-EXECUTOR-COMPARISON-IS-NOT-VACUOUS failed on its first run and that "
   "failure is the reason the prefix asymmetry between this harness hashing and the execution record was "
   "found at all; the control and matrix cases M16, M17 and M18 are what keep the absence row falsifiable",
   "W0501-RUN-EVENT-AND-COST-CORRELATION is disclosed as unmet, not asserted: the adapter journal and the "
   "domain Run never meet in this tree, and the duty lives in open_obligations_before_next_card rather than "
   "in a receipt sentence, which the round-2 reviewer measured to be the difference",
   "one process slip is on the record: a checkpoint commit landed while the evidence chain was running, "
   "HEAD moved under it, and the receipt generator refused to write a receipt quoting a HEAD nobody "
   "measured; the chain was re-run whole and no wrong figure was ever published",
   "the mutation matrix keeps the drained-tree case outside itself as equivalence probe E1 because the "
   "fixture worker really does drain its job object, and the claim is pinned instead by "
   "W0501-ADAPTER-DRAINED-REPORT-CORRELATES-TREE comparing the report against the observed tree",
   "receipt.json is generated by a script that runs every guard before writing, renames a temporary only "
   "after both passes, derives each command row from a captured log or the frozen harness report, and "
   "aborts if the binding runs or the captured logs are pinned to a different code_revision than it names"],
 "carried_forward": carried})
for t in carried:
    cp["open_obligations_before_next_card"].append(t)
cp["work_in_progress"] = None
cp["note"] = ("rev %d: W05-01 %s by %s. Step counts are read from step_state, not typed: %d steps now "
              "recorded. This step accepts one card only; parent tasks and formal cases are not accepted "
              "here, and the objective stays open until every parent task and every formal case is validly "
              "accepted. No completion claim is made by this note. The W04 parent gate still owes the "
              "migration-owned binding tables, /v2/command routing and the native chooser, and W05 still "
              "owes its own -99."
              % (cp["revision"], verdict["verdict"], vid, len(state["steps"])))
cp["updated_at"] = now.isoformat()
cp["updated_by"] = EXECUTOR
dump(CP, cp)
print("W05-01 %s | evidence %d files | next %s | checkpoint rev %d" %
      (verdict["verdict"], len(state["steps"][-1]["evidence"]), nxt_id, cp["revision"]))
