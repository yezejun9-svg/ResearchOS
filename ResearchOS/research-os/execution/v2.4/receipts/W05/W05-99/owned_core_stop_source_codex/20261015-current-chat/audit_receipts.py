"""Produce final append-only candidate index and failure count from raw captures."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent

def hash_file(path):
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def one(label):
    matches = list((root / "command-captures").glob(f"*-{label}-*"))
    if len(matches) != 1: raise RuntimeError((label, len(matches)))
    p = matches[0]
    if json.loads((p / "after.json").read_text())["native_exit"] != 0: raise RuntimeError(label)
    return p, (p / "stdout.bin").read_bytes()

def main():
    candidates = {}
    for short in ("2ed14cf7", "56e44e1b"):
        directory = root / f"candidate-{short}-final"
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if hash_file(directory / "source.patch")["sha256"] != manifest["patch_sha256"]: raise RuntimeError("patch mismatch")
        candidates[short] = {"commit": manifest["commit"], "tree": manifest["tree"],
            "manifest": hash_file(directory / "manifest.json"), "patch": hash_file(directory / "source.patch"),
            "cut_ledger": hash_file(directory / "CUT-LEDGER.md"), "path_count": len(manifest["paths"])}
    _, main_head = one("guard-main-head")
    _, protected = one("guard-protected-paths")
    _, status = one("guard-final-worktree-clean")
    if main_head.decode().strip() != "4f4023c956f84d65743f39ce77d6c8899a21ada1" or protected or status:
        raise RuntimeError("protected/main/worktree guard failed")
    fails = []
    successes = 0
    incomplete = []
    for p in sorted((root / "command-captures").iterdir()):
        if not p.is_dir(): continue
        if "-audit-final-receipts-" in p.name: continue
        if not (p / "after.json").exists():
            incomplete.append(p.name)
            continue
        after = json.loads((p / "after.json").read_text())
        if after["native_exit"] != 0:
            fails.append({"capture": p.name, "native_exit": after["native_exit"],
                "stderr": hash_file(p / "stderr.bin"), "stdout": hash_file(p / "stdout.bin")})
        else: successes += 1
    index = {"schema":"researchos.owned-core-stop-source-receipt-index.v1",
        "source_acceptance":"NOT_ACCEPTED_REQUIRES_INDEPENDENT_REVIEW_AND_TRUST_ANCHOR",
        "actual_operation":"NOT_AUTHORIZED_NOT_RUN", "formal_increment":0,
        "candidates":candidates,
        "guards":{"main_head":main_head.decode().strip(),"protected_diff_paths":[],"worktree_porcelain":""},
        "raw_command_counts":{"completed_success":successes,"completed_failure":len(fails),"incomplete":len(incomplete)},
        "raw_failures":fails,"raw_incomplete":incomplete}
    target = root / "FINAL-RECEIPT-INDEX.json"
    target.write_text(json.dumps(index, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"index":str(target),"candidates":candidates,"failure_count":len(fails),"failures":[f["capture"] for f in fails],"incomplete":incomplete},ensure_ascii=False))

if __name__ == "__main__": main()
