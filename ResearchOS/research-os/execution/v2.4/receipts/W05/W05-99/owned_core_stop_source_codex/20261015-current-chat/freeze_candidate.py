"""Freeze a captured exact 19-path Source candidate without running Git again."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CAP = ROOT / "command-captures"
SCOPE = ROOT.parent.parent / "resume_cp398_codex" / "20261015-current-chat" / "continuation-cp502" / "owned-core-stop-source-implementation-scope.json"

def capture(label):
    found = list(CAP.glob(f"*-{label}-*"))
    if len(found) != 1:
        raise RuntimeError((label, len(found)))
    p = found[0]
    before = json.loads((p / "before.json").read_text(encoding="utf-8"))
    after = json.loads((p / "after.json").read_text(encoding="utf-8"))
    if after["native_exit"] != 0:
        raise RuntimeError((label, after))
    return p, before, after, (p / "stdout.bin").read_bytes()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    head = capture("final-head")[3].decode().strip()
    tree = capture("final-tree")[3].decode().strip()
    names = capture("final-names")[3].decode().splitlines()
    patch_capture, _, _, patch = capture("final-patch")
    if capture("final-status")[3]:
        raise RuntimeError("worktree dirty")
    if set(names) != set(scope["production_new_allowed"] + scope["tests_new_allowed"]) or len(names) != 19:
        raise RuntimeError("diff names differ from 19-path scope")
    if head != "56e44e1b8a5086c26074c13db14173c5b1ab6116":
        raise RuntimeError("wrong candidate")
    output = ROOT / "candidate-56e44e1b-final"
    output.mkdir(exist_ok=False)
    patch_path = output / "source.patch"
    shutil.copyfile(patch_capture / "stdout.bin", patch_path)
    files = {}
    worktree = Path(scope["worktree"])
    for name in names:
        raw = (worktree / name).read_bytes()
        files[name] = {"sha256": sha(raw), "bytes": len(raw)}
    captures = []
    for p in sorted(CAP.iterdir()):
        if not p.is_dir() or not (p / "before.json").exists() or not (p / "after.json").exists():
            continue
        before = json.loads((p / "before.json").read_text(encoding="utf-8"))
        after = json.loads((p / "after.json").read_text(encoding="utf-8"))
        captures.append({"path": str(p.relative_to(ROOT)), "argv": before["argv"], "native_exit": after["native_exit"], "stdout_sha256": sha((p / "stdout.bin").read_bytes()), "stderr_sha256": sha((p / "stderr.bin").read_bytes())})
    manifest = {
        "schema": "researchos.owned-core-stop-source-candidate.v1",
        "status": "INTERMEDIATE_SOURCE_CANDIDATE_NOT_ACCEPTED",
        "base_commit": scope["base_commit"], "commit": head, "tree": tree,
        "scope_sha256": sha(SCOPE.read_bytes()),
        "architecture_sha256": scope["architecture_ref"]["sha256"],
        "test_cuts_sha256": scope["test_cuts_ref"]["sha256"],
        "patch_sha256": sha(patch), "patch_bytes": len(patch),
        "paths": files, "commands": captures,
        "actual_operation": "NOT_AUTHORIZED_NOT_RUN", "formal_increment": 0,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"commit": head, "tree": tree, "paths": len(names), "patch_sha256": sha(patch), "captures": len(captures)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
