"""Freeze only the CP516 bounded Source candidate and its task-owned evidence."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-proof-r3-20261015")
SCOPE = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp516\owned-core-stop-proof-revision03-source-scope.json")
BASE = "f5db4a9639f1a50380eb5929ee6295887baeb756"
MAIN = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
OUT = ROOT / "candidate-2816daac-final"

def digest(raw): return hashlib.sha256(raw).hexdigest()
def artifact(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}
def write_json(path, obj):
    path.write_bytes((json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return artifact(path)
def git(label, *args):
    invocation = [sys.executable, "-B", "-X", "utf8", str(ROOT / "run_logged.py"), "--label", label, "--cwd", str(WORKTREE), "--", "git", *args]
    result = subprocess.run(invocation, cwd=WORKTREE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f"{label}: {result.returncode}: {result.stderr.decode(errors='replace')}")
    return result.stdout

scope_raw = SCOPE.read_bytes()
if digest(scope_raw) != "f30a352913da75ecabb560709aca5a138989c183d9459adc6eb67df27c824b5a":
    raise RuntimeError("scope hash drift")
scope = json.loads(scope_raw)
allowed = scope["source_allowlist"]
if len(allowed) != 7 or len(set(allowed)) != 7:
    raise RuntimeError("exact seven-file scope required")
head = git("freeze-r3-head", "rev-parse", "HEAD").decode().strip()
tree = git("freeze-r3-tree", "rev-parse", "HEAD^{tree}").decode().strip()
base_tree = git("freeze-r3-base-tree", "rev-parse", f"{BASE}^{{tree}}").decode().strip()
if not head.startswith("2816daac") or base_tree != scope["base_tree"]:
    raise RuntimeError("candidate or base mismatch")
if git("freeze-r3-status", "status", "--porcelain=v1"):
    raise RuntimeError("candidate worktree dirty")
changed = git("freeze-r3-delta-names", "diff", "--name-only", BASE, head).decode().splitlines()
if set(changed) != set(allowed):
    raise RuntimeError(f"delta path mismatch: {changed}")
whole = git("freeze-r3-whole-names", "diff", "--name-only", MAIN, head).decode().splitlines()
if len(whole) != 19 or not set(allowed).issubset(whole):
    raise RuntimeError(f"whole19 path mismatch: {whole}")
OUT.mkdir(exist_ok=True)
delta_path = OUT / "f5db4a96-to-2816daac-seven.patch"
whole_path = OUT / "Main4f-to-2816daac-whole19.patch"
delta_path.write_bytes(git("freeze-r3-delta-patch", "diff", "--binary", BASE, head, "--", *allowed))
whole_path.write_bytes(git("freeze-r3-whole-patch", "diff", "--binary", MAIN, head, "--", *whole))
members = {}
for line in git("freeze-r3-ls-tree", "ls-tree", "-r", head, "--", *whole).decode().splitlines():
    pre, path = line.split("\t", 1)
    members[path] = pre.split()[-1]
if set(members) != set(whole):
    raise RuntimeError("tree member mismatch")
sources = []
for rel in whole:
    row = artifact(WORKTREE / rel)
    row.update(relative_path=rel, git_blob=members[rel], changed_from_f5=rel in changed)
    sources.append(row)

case_rows = []
for case in sorted(ROOT.glob("fixture-e2e-*/case-result.json")):
    data = json.loads(case.read_text(encoding="utf-8"))
    row = {"mode": data["mode"], "case_result": artifact(case), "case_dir": str(case.parent),
           "state": (data.get("result") or {}).get("state"),
           "zero_native_signal": data.get("zero_native_signal"),
           "native_signal_count": data.get("native_signal_count"),
           "injection": data.get("injection")}
    for name in ("PREFLIGHT-grant.json", "STOP-grant.json", "preflight-only.exe", "stop-once.exe"):
        path = case.parent / name
        if path.exists(): row[name] = artifact(path)
    raw = []
    for path in sorted(case.parent.iterdir()):
        if path.is_file() and (path.name.endswith("before.json") or path.name.endswith("after.json") or path.name.endswith("stdout.bin") or path.name.endswith("stderr.bin")):
            raw.append(artifact(path))
    row["raw_invocation_artifacts"] = raw
    case_rows.append(row)

captures, failures = [], []
for after in sorted((ROOT / "command-captures").glob("*/after.json")):
    before = after.parent / "before.json"
    result = json.loads(after.read_text(encoding="utf-8"))
    recipe = json.loads(before.read_text(encoding="utf-8"))
    row = {"directory": str(after.parent), "before": artifact(before), "after": artifact(after),
           "stdout": artifact(after.parent / "stdout.bin"), "stderr": artifact(after.parent / "stderr.bin"),
           "native_exit": result["native_exit"]}
    captures.append(row)
    if result["native_exit"]:
        label = after.parent.name.split("Z-", 1)[-1].rsplit("-", 1)[0]
        expected = ("preflight-binary-cannot-commit", "stop-binary-cannot-preflight",
                    "cli-real-stop-once", "cli-real-inspect", "cli-synthetic-crash-reentry",
                    "preflight-after-consumed-attempt-denied", "third-grant-conflict", "reject-")
        classification = "EXPECTED_DENIAL_ASSERTED_BY_CASE" if label.startswith(expected) else "DIAGNOSTIC_ERROR_RETAINED"
        failures.append({"capture": row["directory"], "native_exit": result["native_exit"],
                         "argv": recipe["argv"], "classification": classification})

matrix = {
    "F01": "worker and verifier required native exit/wait numeric presence, null/negative/overflow/fractional rejects, explicit 0/nonzero and WAIT_OBJECT_0; two final fresh real CLI bad receipts reject at preflight before STOP grant; final positive succeeds",
    "F02": "caller canceled/earlier deadline/native prewait zero-call unit; durable intent cancellation/expiry consumed journal unit and true CLI synthetic reachable intent reentry; full live Commit cancellation after intent not deterministically injected",
    "F03": "real child plus parent copied-image chain retained; hardlink, reparse/junction where available, write-sharing, directory swap, wrong parent identity zero-signal tests; no live hostile rename race claim",
    "COV01": "six synthetic reachable/torn journal images; true CLI independent reentry, third grant conflict, preflight reset denied; synthetic injection is not actual killed grant-aware CLI or hardware power-loss proof",
    "COV02": "wrong expected SID/Host/Owner/native/parent/root/opdir true CLI and supervisor native chain; genuine foreign-user process unavailable",
    "COV03": "intent consumed and zero call by unit seam, earlier deadline/cancel/native prewait; true CLI expired inspect from preceding revision; no full live Commit cancel after intent",
    "COV04": "true CLI STARTED, UNKNOWN, nonmodel effect, other run/dispatch/control request reject with STALE_PLAN and zero native signal; fixture mutations change logical census",
    "COV05": "malformed compiled grant true CLI side-effect matrix plus F01 bad-receipt early preflight refusal; parser unit covers remaining numeric shape and canonical policy",
}
matrix_ref = write_json(OUT / "claim-to-test-matrix.json", {"schema": "researchos.owned-core-stop-proof-revision03-matrix.v1", "claims": matrix, "cases": [{k:v for k,v in row.items() if k in ("mode","case_result","state","zero_native_signal","native_signal_count","injection")} for row in case_rows]})
capture_ref = write_json(OUT / "command-capture-index.json", {"schema":"researchos.owned-core-stop-proof-revision03-command-index.v1", "captures":captures})
ledger_ref = write_json(OUT / "failure-and-gap-ledger.json", {
    "schema":"researchos.owned-core-stop-proof-revision03-ledger.v1",
    "root_command_nonzero":failures,
    "capture_gaps":["Two read-only git status/diff commands after context reset were not wrapped by run_logged.py; no mutation occurred.", "Source edits through apply_patch are not shell commands.", "The index is a finite snapshot; the outer final freeze command after.json and any later audit commands are recorded separately outside it."],
    "known_harness_correction":"Initial malformed_grants evidence scan tried reading live Core lock and raised PermissionError; corrected to record unreadable files and reran, retaining original failure.",
    "limits":["Synthetic reachable journal images are not actual process crashes or power-fail durability tests.", "No genuine foreign-user process or live hostile image ancestor race was created.", "No deterministic full Commit context cancellation after intent; unit/native boundary cuts provide narrower evidence.", "Source author did not independently review or accept this candidate."],
    "prior_f5_status":"NEEDS_CHANGES_NOT_ACCEPTED", "prior_f5_nonzero_classification":"63 original records, 54 expected and 9 errors; unchanged and not recounted", "formal_increment":0})
manifest = write_json(OUT / "manifest.json", {
    "schema":"researchos.owned-core-stop-proof-revision03-candidate.v1", "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
    "source_status":"CANDIDATE_FOR_INDEPENDENT_REVIEW_NOT_ACCEPTED_NOT_OPERATION_AUTHORITY", "branch":scope["branch"],
    "worktree":str(WORKTREE), "scope":artifact(SCOPE), "base_commit":BASE, "base_tree":base_tree,
    "main_base":MAIN, "commit":head, "tree":tree, "changed_from_f5":changed, "whole19_from_main":whole,
    "source_files":sources, "delta_patch":artifact(delta_path), "whole19_patch":artifact(whole_path),
    "case_rows":case_rows, "claim_to_test_matrix":matrix_ref, "command_capture_index":capture_ref,
    "failure_and_gap_ledger":ledger_ref, "formal_increment":0,
    "scope_limits":"Only isolated owned synthetic fixtures; no actual current Core/Desktop/Ollama/data/signing authority; restart proof class outside card."})
print(json.dumps({"manifest":manifest,"commit":head,"tree":tree,"delta_patch":artifact(delta_path),"whole19_patch":artifact(whole_path),"cases":len(case_rows),"captures":len(captures),"root_nonzero":len(failures)},ensure_ascii=False,indent=2))
