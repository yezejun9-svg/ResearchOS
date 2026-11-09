"""Freeze the bounded CP508 Source revision without editing Main or old receipts."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-anchor-r2-20261015")
SCOPE = Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp508\owned-stop-anchor-revision02-source-scope.json")
MAIN = "4f4023c956f84d65743f39ce77d6c8899a21ada1"
BASE = "56e44e1b8a5086c26074c13db14173c5b1ab6116"
OUT = ROOT / "candidate-f5db4a96-final"

def sha(raw): return hashlib.sha256(raw).hexdigest()
def write_json(path, value):
    raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    path.write_bytes(raw)
    return {"path":str(path),"sha256":sha(raw),"bytes":len(raw)}
def git(label,*argv):
    cmd=[sys.executable,"-B","-X","utf8",str(ROOT/"run_logged.py"),"--label",label,"--cwd",str(WORKTREE),"--","git",*argv]
    done=subprocess.run(cmd,cwd=WORKTREE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if done.returncode:raise RuntimeError(f"{label}: {done.returncode}: {done.stderr.decode(errors='replace')}")
    return done.stdout
def artifact(path):
    raw=path.read_bytes()
    return {"path":str(path),"sha256":sha(raw),"bytes":len(raw)}

OUT.mkdir(exist_ok=True)
scope_raw=SCOPE.read_bytes()
scope=json.loads(scope_raw)
allowed=scope["allowed_existing_production"]+scope["allowed_existing_tests"]
if len(allowed)!=19 or len(set(allowed))!=19:raise RuntimeError("exact 19 scope files required")
head=git("freeze-r2-head","rev-parse","HEAD").decode().strip()
tree=git("freeze-r2-tree","rev-parse","HEAD^{tree}").decode().strip()
base_tree=git("freeze-r2-base-tree","rev-parse",f"{BASE}^{{tree}}").decode().strip()
if not head.startswith("f5db4a96") or base_tree!=scope["base_tree"]:raise RuntimeError("revision or base tree differs")
status=git("freeze-r2-status","status","--porcelain=v1")
if status:raise RuntimeError("repair worktree dirty before freeze")
changed=git("freeze-r2-changed","diff","--name-only",BASE,head).decode().splitlines()
if any(p not in allowed for p in changed):raise RuntimeError("outside-allowlist patch")
whole=git("freeze-r2-whole19-names","diff","--name-only",MAIN,head).decode().splitlines()
if any(p not in allowed for p in whole):raise RuntimeError("combined patch outside-allowlist")
if len(whole)!=19:raise RuntimeError(f"expected 19 combined files, got {len(whole)}")
repair_patch=git("freeze-r2-repair-patch","diff","--binary",BASE,head,"--",*allowed)
combined_patch=git("freeze-r2-combined-patch","diff","--binary",MAIN,head,"--",*allowed)
repair_path=OUT/"56e44e1b-to-f5db4a96.patch"
combined_path=OUT/"Main4f-to-f5db4a96-whole19.patch"
repair_path.write_bytes(repair_patch)
combined_path.write_bytes(combined_patch)
ls=git("freeze-r2-ls-tree","ls-tree","-r",head,"--",*allowed).decode().splitlines()
blobs={line.split("\t",1)[1]:line.split("\t",1)[0].split()[-1] for line in ls}
if set(blobs)!=set(allowed):raise RuntimeError("whole 19 tree members differ")
source_files=[]
for rel in allowed:
    p=WORKTREE/rel
    member=artifact(p)
    member.update(relative_path=rel,git_blob=blobs[rel],changed_from_56e=rel in changed)
    source_files.append(member)
cases=[]
for p in sorted(ROOT.glob("fixture-e2e-*/case-result.json")):
    rec=json.loads(p.read_text(encoding="utf-8"))
    item=artifact(p)
    item.update(mode=rec.get("mode","UNLABELED_EARLY_CASE"),case_dir=str(p.parent),result_state=rec.get("result",{}).get("state"),zero_signal=rec.get("zero_signal"))
    for name in ("PREFLIGHT-grant.json","STOP-grant.json","preflight-only.exe","stop-once.exe"):
        member=p.parent/name
        if member.exists():item[name]=artifact(member)
    cases.append(item)
captures=[]
failed=[]
for p in sorted((ROOT/"command-captures").glob("*/after.json")):
    after=json.loads(p.read_text(encoding="utf-8"))
    before=p.parent/"before.json"
    item={"directory":str(p.parent),"before":artifact(before),"after":artifact(p),"stdout":artifact(p.parent/"stdout.bin"),"stderr":artifact(p.parent/"stderr.bin"),"native_exit":after["native_exit"]}
    captures.append(item)
    if after["native_exit"]!=0:
        invocation=json.loads(before.read_text(encoding="utf-8"))
        failed.append({"capture":str(p.parent),"native_exit":after["native_exit"],"argv":invocation["argv"],"stderr_sha256":item["stderr"]["sha256"],"classification":"REVIEW_RAW_EXPECTED_DENY_OR_FAILURE"})
ledger=write_json(OUT/"failure-ledger.json",{
    "schema":"researchos.owned-core-stop-source-revision02-failure-ledger.v1",
    "raw_nonzero_command_captures":failed,
    "known_harness_corrections":["wrong_native initially expected JSON on fail-fast exit 1; fixed and reran", "wrong_root initially expected exit 1 but CLI returned STOP_UNAVAILABLE exit 3; fixed and reran", "final focused Go test initially used wrong fixture environment variable and noncanonical forward-slash TEMP; corrected and reran"],
    "capture_gap":"Initial revision02 worktree creation/scope read preceded the new run_logged.py wrapper; preserved honestly in earlier conversation and not recast as captured commands. Source edits via apply_patch are not shell commands.",
    "pending_independent_acceptance":True
})
capture_index=write_json(OUT/"command-capture-index.json",{"schema":"researchos.owned-core-stop-source-revision02-command-index.v1","captures":captures})
cuts={
 "SA01_SA03_SA10":"real compiled-grant positive, default/expired fail-fast, strict CLI unit tests, expired inspect immutable file comparison",
 "SA02_SA04_SA08":"seven pinned historical proof classes, synthetic review/scope with matching exact binding; proof drift, forged whole caller set, bad review, wrong native/parent/root/opdir fail before native intent",
 "SA05_SA06_SA07_SA11":"native single-call/deadline/cancellation focused unit tests, two real concurrent CLI commits one native call, crash-stage journal test; no real hardware fault injection claim",
 "SA09_SA12_SA14":"two real -ldflags -X binaries, backward DAG/grant and predecessor hashes, immutable preflight/repeat commit and wrong phase actions",
 "SA13_SA15":"held authority/opdir lock and write-sharing/rename denial unit test; wrong pinned opdir/root CLI grant cases; no OS reparse creation fixture claim",
 "S209":"real CLI stale plan after new pending effect; Core stays alive and no terminate intent",
 "S216":"real CLI poststop writer drift; one native exit, real lease, maintenance blocked",
 "S208":"private fixed SQL catalogue source audit plus query_only/rollback focused test; no native SQLite authorizer hook claim",
 "S201_S203":"real child native crash, durable WAL row preserved, inflight queued write absent, lease acquired; unrelated child survival focused test",
 "S202_S211":"foreign identity/native parent mismatches, finite supervisor deadline and zero-call expiry unit tests"
}
manifest=write_json(OUT/"manifest.json",{
    "schema":"researchos.owned-core-stop-source-revision02-candidate.v1",
    "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
    "branch":scope["branch"],"worktree":str(WORKTREE),"main_base":MAIN,"repair_base":BASE,"repair_base_tree":base_tree,"commit":head,"tree":tree,
    "scope":artifact(SCOPE),"source_status":"ROOT_FROZEN_FOR_INDEPENDENT_REVIEW_NOT_ACCEPTED_NOT_OPERATION_AUTHORITY",
    "changed_from_repair_base":changed,"whole19_changed_from_main":whole,"source_files":source_files,
    "repair_patch":artifact(repair_path),"whole19_patch":artifact(combined_path),
    "fixture_cases":cases,"command_capture_index":capture_index,"failure_ledger":ledger,
    "grant_build_mechanism":"Go build -ldflags -X researchos.local/research-os/internal/ownedcorestop.compiledOperationGrantBase64=<canonical grant bytes encoded base64>; full exact argv and nonsecret fixture grant bytes in raw case command captures/grant JSON members",
    "proof_claims":cuts,"limits":["Synthetic owned fixture authority only; no actual Core/Desktop/Ollama/data pins", "No Source author acceptance or formal case acceptance", "No native hardware fault injection or same-SID malicious rollback claim", "Main base 4f and protected paths untouched by this worktree"],
    "formal_increment":0
})
print(json.dumps({"manifest":manifest,"commit":head,"tree":tree,"repair_patch":artifact(repair_path),"whole19_patch":artifact(combined_path),"failure_ledger":ledger,"command_capture_index":capture_index,"cases":len(cases)},ensure_ascii=False,indent=2))
