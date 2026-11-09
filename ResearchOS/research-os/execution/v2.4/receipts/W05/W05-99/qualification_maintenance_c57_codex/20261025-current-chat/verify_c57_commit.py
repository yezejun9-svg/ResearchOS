import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
snapshot_path = receipts / "C57-COMBINED-V11-POSTTEST.json"
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
expected_changed = {item["path"] for item in snapshot["files"] if item["changed"]}

def git(*args):
    result = subprocess.run(["git", *args], cwd=worktree, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.returncode}: {result.stderr.decode(errors='replace')}")
    return result.stdout

commit = git("rev-parse", "HEAD").decode().strip()
tree = git("rev-parse", "HEAD^{tree}").decode().strip()
parent = git("rev-parse", "HEAD^").decode().strip()
branch = git("branch", "--show-current").decode().strip()
status = git("status", "--porcelain=v1", "-z", "-uall")
changed = {path.decode("utf-8") for path in git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").split(b"\0") if path}
if parent != snapshot["base_commit"] or branch != "qualification-maintenance-c57-20261025" or status or changed != expected_changed:
    raise RuntimeError(f"commit identity, changed set, or clean status mismatch: {commit} {branch} {len(status)} {len(changed)}")
files = []
for item in snapshot["files"]:
    raw = git("show", f"HEAD:{item['path']}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != item["sha256"] or len(raw) != item["bytes"]:
        raise RuntimeError(f"committed blob differs from frozen source: {item['path']}")
    files.append({"path": item["path"], "bytes": len(raw), "sha256": digest,
                  "changed_in_commit": item["path"] in changed})
manifest = {"schema": "researchos.c57-exact-commit.v1", "commit": commit, "tree": tree, "parent": parent,
            "branch": branch, "source_snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
            "source_allowlist_count": len(files), "actual_changed_count": len(changed),
            "clean_worktree": not status, "files": files}
out = receipts / "C57-COMMIT-SOURCE57-MANIFEST.json"
if out.exists():
    raise RuntimeError("commit manifest already exists; preserve it")
out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(receipts / "092-postcommit-diff-names.raw").write_bytes(git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"))
(receipts / "092-postcommit-status.raw").write_bytes(status)
print(json.dumps({"commit": commit, "tree": tree, "parent": parent, "changed_count": len(changed),
                  "manifest_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))
