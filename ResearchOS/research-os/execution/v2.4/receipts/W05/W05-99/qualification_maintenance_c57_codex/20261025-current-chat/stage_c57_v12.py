import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
pre = receipts / "C57-V12-PRETEST.json"
post = receipts / "C57-V12-POSTTEST.json"
if hashlib.sha256(pre.read_bytes()).hexdigest() != hashlib.sha256(post.read_bytes()).hexdigest():
    raise RuntimeError("V12 source moved during tests")
snapshot = json.loads(post.read_text(encoding="utf-8"))
paths = ["internal/recoveryboundary/boot_windows.go", "internal/recoveryboundary/boot_windows_test.go"]
if snapshot["v12_delta_count"] != 2 or snapshot["parent_commit"] != "08d63ed86356a93fe5715732cfeae0624c5cb6c9":
    raise RuntimeError("V12 staged scope or parent invalid")
for item in snapshot["files"]:
    if hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError(f"source moved after posttest: {item['path']}")

def run(name, args):
    result = subprocess.run(args, cwd=worktree, capture_output=True)
    (receipts / f"{name}.stdout.raw").write_bytes(result.stdout)
    (receipts / f"{name}.stderr.raw").write_bytes(result.stderr)
    (receipts / f"{name}.native-exit.txt").write_text(f"{result.returncode}\n", encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{name} failed: {result.returncode}")
    return result.stdout

head = run("099-v12-stage-head", ["git", "rev-parse", "HEAD"]).decode().strip()
if head != snapshot["parent_commit"]:
    raise RuntimeError("V12 branch HEAD changed")
if run("100-v12-stage-preexisting", ["git", "diff", "--cached", "--name-only", "-z"]):
    raise RuntimeError("preexisting staged content")
recipe = {"schema": "researchos.c57-v12-exact-stage-recipe.v1", "worktree": str(worktree),
          "source_snapshot_sha256": hashlib.sha256(post.read_bytes()).hexdigest(),
          "argv": ["git", "-c", "maintenance.auto=false", "-c", "gc.auto=0", "add", "--", *paths]}
(receipts / "101-v12-stage.recipe.json").write_text(json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
run("101-v12-stage", recipe["argv"])
staged = {path.decode() for path in run("102-v12-stage-names", ["git", "diff", "--cached", "--name-only", "-z"]).split(b"\0") if path}
if staged != set(paths):
    raise RuntimeError(f"staged V12 paths differ: {sorted(staged)}")
run("103-v12-stage-check", ["git", "diff", "--cached", "--check"])
patch = run("104-v12-staged-patch", ["git", "--no-pager", "diff", "--cached", "--binary", "--full-index"])
(receipts / "C57-V12-STAGED-DELTA.patch").write_bytes(patch)
manifest = {"schema": "researchos.c57-v12-staged-delta.v1", "parent_commit": head,
            "source_snapshot_sha256": recipe["source_snapshot_sha256"],
            "staged_paths": sorted(staged), "patch_sha256": hashlib.sha256(patch).hexdigest(),
            "patch_bytes": len(patch)}
(receipts / "C57-V12-STAGED-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"paths": sorted(staged), "patch_sha256": manifest["patch_sha256"],
                  "manifest_sha256": hashlib.sha256((receipts / "C57-V12-STAGED-MANIFEST.json").read_bytes()).hexdigest()}))
