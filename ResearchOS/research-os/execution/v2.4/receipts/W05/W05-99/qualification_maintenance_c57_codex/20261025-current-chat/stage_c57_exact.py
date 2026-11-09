import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
scope = json.loads((project / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp533/C57-source-scope.json").read_text(encoding="utf-8"))
snapshot = json.loads((receipts / "C57-COMBINED-V11-POSTTEST.json").read_text(encoding="utf-8"))
paths = scope["source_allowlist"]
expected_changed = {item["path"] for item in snapshot["files"] if item["changed"]}
if len(paths) != 57 or len(expected_changed) != 52 or snapshot["base_commit"] != scope["base_commit"]:
    raise RuntimeError("frozen C57 scope/count invalid")
for item in snapshot["files"]:
    if hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError(f"source changed after posttest snapshot: {item['path']}")

def run(name, args):
    result = subprocess.run(args, cwd=worktree, capture_output=True)
    (receipts / f"{name}.stdout.raw").write_bytes(result.stdout)
    (receipts / f"{name}.stderr.raw").write_bytes(result.stderr)
    (receipts / f"{name}.native-exit.txt").write_text(str(result.returncode) + "\n", encoding="utf-8")
    return result

head = run("084-stage-prehead", ["git", "rev-parse", "HEAD"])
if head.returncode or head.stdout.decode().strip() != scope["base_commit"]:
    raise RuntimeError("worktree base HEAD changed")
staged_before = run("085-stage-preexisting", ["git", "diff", "--cached", "--name-only", "-z"])
if staged_before.returncode or staged_before.stdout:
    raise RuntimeError("preexisting staged changes; refuse to mix")
recipe = {"schema": "researchos.c57-exact-stage-recipe.v1", "worktree": str(worktree),
          "source_snapshot_sha256": hashlib.sha256((receipts / "C57-COMBINED-V11-POSTTEST.json").read_bytes()).hexdigest(),
          "argv": ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0", "add", "--", *paths]}
(receipts / "086-stage-exact.recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
stage = run("086-stage-exact", recipe["argv"])
if stage.returncode:
    raise RuntimeError(f"git add failed with {stage.returncode}")
staged = run("087-stage-names", ["git", "diff", "--cached", "--name-only", "-z"])
if staged.returncode:
    raise RuntimeError("staged name inventory failed")
actual = {path.decode("utf-8") for path in staged.stdout.split(b"\0") if path}
if actual != expected_changed:
    raise RuntimeError(f"staged set differs: missing={sorted(expected_changed-actual)}, extra={sorted(actual-expected_changed)}")
check = run("088-stage-check", ["git", "diff", "--cached", "--check"])
if check.returncode:
    raise RuntimeError("staged whitespace check failed")
patch = run("089-stage-fullpatch", ["git", "--no-pager", "diff", "--cached", "--binary", "--full-index"])
if patch.returncode:
    raise RuntimeError("staged patch failed")
(receipts / "C57-STAGED-FULL.patch").write_bytes(patch.stdout)
manifest = {"schema": "researchos.c57-exact-staged.v1", "base_commit": scope["base_commit"],
            "source_snapshot_sha256": recipe["source_snapshot_sha256"],
            "allowlist_count": len(paths), "staged_count": len(actual),
            "staged_paths": sorted(actual), "staged_patch_sha256": hashlib.sha256(patch.stdout).hexdigest(),
            "staged_patch_bytes": len(patch.stdout), "diff_check_exit": check.returncode}
(receipts / "C57-STAGED-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"staged_count": len(actual), "patch_sha256": manifest["staged_patch_sha256"],
                  "manifest_sha256": hashlib.sha256((receipts / "C57-STAGED-MANIFEST.json").read_bytes()).hexdigest()}))
