import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone


WORKTREE = pathlib.Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
RECEIPT = pathlib.Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_maintenance_c57_codex\20261025-current-chat")
SCOPE = pathlib.Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp533\C57-source-scope.json")


def git(*args):
    result = subprocess.run(["git", *args], cwd=WORKTREE, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"git {args!r}: {result.returncode}: {result.stderr.decode(errors='replace')}")
    return result.stdout


scope = json.loads(SCOPE.read_text(encoding="utf-8"))
boot = set(scope["source_groups"]["boot_production_and_tests"])
owned = sorted(set(scope["source_allowlist"]) - boot)
if len(owned) != 51 or len(boot) != 6:
    raise RuntimeError(f"scope ownership changed: {len(owned)} + {len(boot)}")
head = git("rev-parse", "HEAD").decode().strip()
tree = git("rev-parse", "HEAD^{tree}").decode().strip()
if head != scope["base_commit"] or tree != scope["base_tree"]:
    raise RuntimeError("base commit/tree changed")
untracked = set(git("ls-files", "--others", "--exclude-standard", "-z").decode().strip("\x00").split("\x00"))
changed = set(git("diff", "--name-only", "HEAD", "--", *owned).decode().splitlines()) | (untracked & set(owned))
if not changed <= set(owned):
    raise RuntimeError("changed path outside owned51")

entries = []
for path in owned:
    raw = (WORKTREE / path).read_bytes()
    entries.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "changed": path in changed})

pins = []
for pin in scope["inherited43_other_paths_must_remain_exact"]:
    raw = (WORKTREE / pin["path"]).read_bytes()
    actual = {"path": pin["path"], "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    if actual["bytes"] != pin["bytes"] or actual["sha256"] != pin["sha256"]:
        raise RuntimeError(f"inherited43 pin drift: {pin['path']}")
    pins.append(actual)
if len(pins) != 40:
    raise RuntimeError(f"inherited43 pin count changed: {len(pins)}")

patch = git("diff", "--binary", "HEAD", "--", *owned)
for path in sorted(untracked & set(owned)):
    result = subprocess.run(["git", "diff", "--no-index", "--binary", "--", "/dev/null", path],
                            cwd=WORKTREE, capture_output=True, check=False)
    if result.returncode != 1:
        raise RuntimeError(f"untracked additive diff failed {path}: {result.returncode}")
    patch += result.stdout
patch_path = RECEIPT / "C51-PRESEAL.patch"
patch_path.write_bytes(patch)

manifest = {
    "schema": "researchos.c57-owned51-preseal.v1",
    "status": "OWNED51_SOURCE_PRESEAL_BOOT6_UNFROZEN_NO_COMMIT",
    "at": datetime.now(timezone.utc).isoformat(),
    "base_commit": head,
    "base_tree": tree,
    "scope_sha256": hashlib.sha256(SCOPE.read_bytes()).hexdigest(),
    "worktree": str(WORKTREE),
    "owned_count": len(owned),
    "changed_count": len(changed),
    "changed_paths": sorted(changed),
    "owned_files": entries,
    "inherited43_exact_pins": pins,
    "patch": {"path": str(patch_path), "bytes": len(patch), "sha256": hashlib.sha256(patch).hexdigest()},
    "test_source_snapshot_042_049_sha256": hashlib.sha256((RECEIPT / "042-049-source-snapshot.json").read_bytes()).hexdigest(),
    "limitations": [
        "No combined57 commit or tree yet",
        "Boot6 six source files are owned by a separate author and still under independent correction",
        "042-049 test source snapshot predates later owned51 transaction-lifetime and fixture-test edits",
    ],
}
(RECEIPT / "C51-PRESEAL.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"owned": len(owned), "changed": len(changed), "pins": len(pins),
                  "patch_sha256": manifest["patch"]["sha256"], "manifest": str(RECEIPT / "C51-PRESEAL.json")}))
