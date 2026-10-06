"""Derive execution/v2.4/receipts/W05/W05-01/review_request_round1.json from the files on disk.

The brief a reviewer receives must not contain numbers typed from memory: every count, id set, path and
revision below is read back out of receipt.json, the matrix file, the registry and the frozen invocation
receipts, and this script aborts if the receipt is not the executor's report shape. It also states, up
front, the four ways the author would most like to be proven wrong, because a review that only confirms
the receipt is worth less than one that tries to break it.
"""
import glob, io, json, os, subprocess, sys

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


def load(p):
    return json.load(io.open(p, encoding="utf-8-sig"))


def dump(p, obj):
    io.open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(obj, indent=1, ensure_ascii=False))


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, encoding="utf-8").stdout.strip()


receipt = load(os.path.join(RD, "receipt.json"))
if receipt.get("status") != "EXECUTION_REPORTED" or receipt.get("verifier_id") is not None \
        or receipt.get("independent_review") is not None or receipt.get("independent_reviews"):
    raise SystemExit("refusing to request a review of something that is not an executor report")
matrix = load(os.path.join(RD, receipt["mutation_selfcheck"]["matrix_source"]))
registry = load(os.path.join("execution", "v2.4", "commands.json"))
entry = registry["commands"]["test.runtime"]
ROUND = (sys.argv[1] if len(sys.argv) > 1 else "round1")
head = git("rev-parse", "HEAD")
rh = receipt["repository_head_at_reporting"]
# The receipt can only ever name the HEAD that existed while its evidence was produced, and committing
# that evidence moves HEAD again. What must hold is that nothing OUTSIDE execution/ changed between the
# two, so a reviewer re-running the binding command measures the same source tree the receipt describes.
moved = [l for l in git("diff", "--name-only", rh, head).splitlines() if l.strip()
         and not l.startswith("execution/") and not l.startswith(".local/")]
if moved:
    raise SystemExit("source outside execution/ moved between the receipt HEAD %s and the current HEAD %s: %s"
                     % (rh[:8], head[:8], moved))
runs = []
for d in sorted(glob.glob(os.path.join(RD, "invocations", "*"))):
    rp = os.path.join(d, "receipt.json")
    if os.path.isfile(rp):
        r = load(rp)
        if (r.get("code_revision") or "") == rh:
            runs.append({"dir": os.path.relpath(d, RD).replace("\\", "/"), "invocation_id": r["invocation_id"],
                         "status": r["status"], "assertions": len(r.get("assertion_ids") or []),
                         "assertion_ids": sorted(r.get("assertion_ids") or [])})
if len(runs) < 2:
    raise SystemExit("need two frozen runs at this HEAD, found %d" % len(runs))
if runs[0]["assertion_ids"] != runs[1]["assertion_ids"]:
    raise SystemExit("the two frozen runs disagree about the id set")
prior = sorted(os.path.basename(f) for f in glob.glob(os.path.join(RD, "independent_review*.json")))
wanted = "independent_review_%s.json" % ROUND
if wanted in prior:
    raise SystemExit("this round already has a verdict: " + wanted)
previous = []
for f in prior:
    v = load(os.path.join(RD, f))
    previous.append({"file": f, "verdict": v.get("verdict"), "reviewer_id": v.get("reviewer_id"),
                 "blocking_issues": [b.get("id") for b in (v.get("blocking_issues") or [])],
                 "reservations": len(v.get("reservations") or [])})

request = {
 "record": "W05-01 %s independent review request" % ROUND,
 "requested_at": git("log", "-1", "--format=%cI"),
 "reviewer_identity_rules": {
  "must_be": "an identity that has never reviewed W05-01 and has not read this window's narration; it forms its own verdict from the files and its own re-runs",
  "must_not": "reuse the W12-01 reviewer identities (w1201_verifier_r1/r2) or any identity that already touched this card",
  "self_signing": "the author of the receipt may not sign it; the verdict file is the reviewer's output, not the executor's"},
 "what_is_claimed": {
  "pin_timeline": {"receipt_head": rh, "request_head": head,
                   "why_they_differ": "committing the card's own evidence necessarily moves HEAD after the receipt was generated; the guard above proves that only execution/ paths differ, so the source tree a reviewer re-runs against is the one the receipt describes",
                   "binding_runs": [{"frozen_under": r["dir"], "invocation_id": r["invocation_id"],
                                     "assertions": r["assertions"], "status": r["status"]} for r in runs]},
  "status": receipt["status"],
  "assertions": receipt["check_results"]["assertions"],
  "assertion_ids": runs[0]["assertion_ids"],
  "binding_command": receipt["commands"][0]["argv"],
  "registry_entry": {"key": "test.runtime", "revision": registry["revision"],
                     "owner_card": entry.get("owner_card"), "handler": entry.get("handler"),
                     "selectors": {k: v for k, v in entry.items() if k.endswith("selectors") or k == "selectors"}},
  "mutation_matrix": {"cases": matrix["cases"], "buckets": matrix["buckets"],
                      "equivalence_probe": [[e["id"], e["bucket"]] for e in matrix["equivalence_probe"]["results"]],
                      "tree_clean_after_restore": matrix["tree_clean_after_restore"]},
  "not_verified_rows": receipt["check_results"]["not_verified"],
  "blocked_live_path": "the card's LIVE model-tool file read is disclosed as not verified, not asserted"},
 "please_try_to_break": [
  "Derived numbers: pick any count in receipt.json (assertions, artifact list length, matrix buckets, per-command result strings) and recompute it from the frozen files. If one is reachable only by reading prose, that is a defect.",
  "Assertions that cannot fail for the stated reason: for the settled/exit-code rows, for W0501-FIXTURE-DISPATCH-CHARGE-IS-PROVEN-ZERO and for W0501-UNQUALIFIED-LIVE-RUNTIME-REFUSED, ask what a wrong production value would do to the row, and check the matrix case that is supposed to prove it.",
  "The equivalence probe: E1 is filed outside the matrix on the argument that the fixture really drains its job object. Attack that argument. If a mutant of that line is in fact distinguishable, the matrix has an undeclared survivor.",
  "The skips: the three not_verified rows rest on measurements in executor_identity_measurement.json and ops/runtime/capabilities.json. Check that a substitute binary was not silently used, and that a skipped row was not quietly promoted to PASS.",
  "Registry side effects: binding a v2.4 entry for test.runtime changes resolution for every selector on that key. Re-resolve the pre-existing selectors against before_baseline_test.runtime.json and binding_and_parity_rev14.json and report any row that changed without a disclosure."],
 "reproduce": [
  "python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-01   (expect PASS with the %d ids above)" % runs[0]["assertions"],
  "python execution/v2.4/receipts/W05/W05-01/generate_receipt_w0501.py --capture && python execution/v2.4/receipts/W05/W05-01/generate_receipt_w0501.py   (the generator aborts unless the matrix and the frozen runs support every figure)",
  "python execution/v2.4/receipts/W05/W05-01/mut_w0501.py   (the matrix rewrites production lines and restores them; run it alone, never beside another heavy Go suite, and confirm tree_clean_after_restore)"],
 "environment": {"go": ".local/tools/go1.27.1/go/bin/go.exe",
                 "env": ["GOTOOLCHAIN=local", "GOENV=off", "GOPATH=.local/gopath", "GOCACHE=.local/gocache",
                         "RESEARCHOS_GO", "RESEARCHOS_TASK_ID=W05", "RESEARCHOS_CHECK_ID=W05-01",
                         "PYTHONIOENCODING=utf-8"],
                 "never": "go build ./pkg at the repository root (it drops a stray executable); concurrent heavy Go suites"},
 "previous_rounds": previous,
 "what_changed_since_the_previous_round": [d["defect"][:220] for d in receipt["defects_found_and_fixed_across_all_rounds"] if "review" in d["defect"]],
 "closure_to_verify": {"matrix_cases": matrix["cases"], "assertions": receipt["check_results"]["assertions"], "disclosed_rows": len(receipt["check_results"]["not_verified"])},
 "card": os.path.join(SPEC, "tasks", "steps", "W05-01.md"),
 "guardrails_for_the_reviewer": [
  "do not edit the receipt, the matrix, the code or the checkpoint; the verdict is a new file",
  "write the verdict as one atomic file and leave it byte-stable for at least 90 seconds before anyone pins it; a partial artifact is not a missing reviewer",
  "report blocking_issues as a separate array from limitations and reservations, and say which of the five claims above you actually re-ran"],
 "expected_output": {
  "path": os.path.join(RD, "independent_review_%s.json" % ROUND),
  "verdicts": ["ACCEPTED", "ACCEPT_WITH_RESERVATIONS", "REWORK_REQUIRED", "REJECTED"],
  "note": "the executor registers only from a verdict that carries blocking_issues == []"}}

dump(os.path.join(RD, "review_request_%s.json" % ROUND), request)
print("review_request_round1.json written | assertions", runs[0]["assertions"],
      "| matrix", matrix["buckets"], "| HEAD", head[:8], "| registry rev", registry["revision"])
