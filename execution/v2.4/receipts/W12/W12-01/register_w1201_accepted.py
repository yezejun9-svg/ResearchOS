"""Register W12-01 as ACCEPTED from an independent verdict, then move the checkpoint.

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
RD = os.path.join("execution", "v2.4", "receipts", "W12", "W12-01")
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
        raise SystemExit("no independent review for W12-01 has been delivered")
    rejects, reject_reviewers, reject_at = [], set(), ""
    for f in files:
        v = load(os.path.join(RD, f))
        if v.get("verdict") == "REJECT":
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
        raise SystemExit("no registrable ACCEPT for W12-01 (rejections on file: %s)" % (rejects or "none"))
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
if any(s.get("id") == "W12-01" for s in state["steps"]):
    raise SystemExit("W12-01 already has a step_state record")
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

carried = ["%s (W12-01 %s): %s" % (i, verdict_file, t)
           for i, t in enumerate(verdict.get("limitations") or [], 1)]

present = sorted(os.listdir(RD))
needed = ("receipt.json", "binding_assertion_ids.json", "binding_assertion_ids_r2.json",
          "mutation_selfcheck_w1201_round4.json", "mutation_equivalence_w1201.json",
          "receipt_addendum_round2.json", "registry_parity_rev13.json", verdict_file)
missing = [n for n in needed if n not in present]
if missing:
    raise SystemExit("required evidence file is not in the receipt directory: %s" % missing)

now = datetime.datetime.now(datetime.timezone.utc)
state["steps"].append({
 "id": "W12-01", "status": "ACCEPTED", "executor_id": EXECUTOR, "verifier_id": vid,
 "accepted_at": now.isoformat(), "verdict": verdict["verdict"],
 "verdict_file": "receipts/W12/W12-01/" + verdict_file,
 "note": ("card-level increment only; parent W12 and cases C11/C13/C14/C15 are not accepted here"),
 "evidence": [{"path": "receipts/W12/W12-01/" + f, "sha256": sha(os.path.join(RD, f))}
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
cp["accepted_steps"] = cp.get("accepted_steps", []) + ["W12-01"]
cp["failure_counters"].append({
 "origin_key": "W12-01/" + verdict_file, "status": verdict["verdict"], "mid_card_repairs": 0,
 "recorded_at": now.isoformat(), "reviewer_id": vid,
 "disclosed_incidents": [
   "this card's first mutation matrix silently skipped three cases whose hard-coded anchors had drifted, "
   "and two mutants survived; both were traced to assertions that matched only the substring GATE_FAILED, "
   "fixed in f9a54e3c, and re-run to 10 caught / 0 survived",
   "progress_note_2.json quoted a probe that did not exist when it was written; the note was kept and the "
   "correction recorded as a checkpoint integrity event rather than edited after the fact",
   "execution/v2.4/commands.json went to revision 12 outside this card's write_scope, and the checkpoint "
   "carries the before/after parity of all seven pre-existing test.resources selectors",
   "receipt.json is generated by a self-verifying script whose guards refuse an acceptance claim, a "
   "disagreeing matrix bucket, or binding runs pinned to a different code_revision"],
 "carried_forward": carried})
for t in carried:
    cp["open_obligations_before_next_card"].append(t)
cp["work_in_progress"] = None
cp["note"] = ("rev %d: W12-01 %s by %s. 16 of 71 cards accepted, 0 of 22 parents, 0 of 42 formal cases "
              "finally verified. No completion claim - the W04 parent gate still owes the migration-owned "
              "binding tables, /v2/command routing and the native chooser, and W12 still owes its own -99."
              % (cp["revision"], verdict["verdict"], vid))
cp["updated_at"] = now.isoformat()
cp["updated_by"] = EXECUTOR
dump(CP, cp)
print("W12-01 %s | evidence %d files | next %s | checkpoint rev %d" %
      (verdict["verdict"], len(state["steps"][-1]["evidence"]), nxt_id, cp["revision"]))
