"""Verify the scoped candidate commit against the frozen tested source."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\desktop-main7d-native-20261025")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


freeze = json.loads((HERE / "SOURCE-FREEZE-03.json").read_bytes())
precommit = json.loads((HERE / "PRECOMMIT-MANIFEST-r3.json").read_bytes())
head, tree, parent = git("log", "-1", "--format=%H%n%T%n%P").decode("ascii").splitlines()
assert parent == freeze["base_commit"] == precommit["base_commit"]
assert git("status", "--porcelain=v1") == b""
changes = [line.split("\t", 1) for line in git("diff-tree", "--no-commit-id", "--name-status", "-r", "HEAD").decode("utf-8").splitlines()]
assert {path for _, path in changes} == set(freeze["seven_file_hashes"])
assert sorted(status for status, _ in changes) == ["A"] * 6 + ["M"]
for path, row in freeze["seven_file_hashes"].items():
    content = git("show", f"HEAD:{path}")
    assert sha(content) == row["sha256"] and len(content) == row["bytes"], path
    assert sha((ROOT / path).read_bytes()) == row["sha256"], path
assert precommit["patch_sha256"] == freeze["patch"]["sha256"]
assert precommit["development_manifest_sha256"] == sha((HERE / "build-02/development-manifest.json").read_bytes())
record = {
    "schema": "researchos.desktop-complete-tree-postcommit.v1",
    "candidate_commit": head, "candidate_tree": tree, "parent_commit": parent,
    "scope_sha256": freeze["scope_sha256"],
    "precommit_manifest_sha256": sha((HERE / "PRECOMMIT-MANIFEST-r3.json").read_bytes()),
    "source_freeze_sha256": sha((HERE / "SOURCE-FREEZE-03.json").read_bytes()),
    "tested_bundle_manifest_sha256": precommit["development_manifest_sha256"],
    "changes": changes, "worktree_clean": True,
    "status": "SOURCE_CANDIDATE_ONLY_NO_NATIVE_GUI_OR_FORMAL_ACCEPTANCE",
}
with (HERE / "POSTCOMMIT-VALIDATION.json").open("xb") as out:
    out.write((json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"commit": head, "tree": tree, "files": len(changes),
                  "validation_sha256": sha((HERE / "POSTCOMMIT-VALIDATION.json").read_bytes())}))
