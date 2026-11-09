import hashlib
import json
import subprocess
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
snapshot_path = receipts / "C57-V12-POSTTEST.json"
snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
delta_expected = {item["path"] for item in snapshot["files"] if item["changed_from_08d63"]}
cumulative_expected = {item["path"] for item in snapshot["files"] if item["changed_from_085b"]}

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
delta = {p.decode("utf-8") for p in git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").split(b"\0") if p}
cumulative = {p.decode("utf-8") for p in git("diff", "--name-only", "-z", "085b4711afe0c1288448b174eef24ecd5af0551b", "HEAD").split(b"\0") if p}
if parent != "08d63ed86356a93fe5715732cfeae0624c5cb6c9" or branch != "qualification-maintenance-c57-20261025" or status or delta != delta_expected or cumulative != cumulative_expected:
    raise RuntimeError(f"V12 commit parent, status, or changed set differs: {parent} {len(status)} {sorted(delta)} {len(cumulative)}")
files = []
for item in snapshot["files"]:
    raw = git("show", f"HEAD:{item['path']}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != item["sha256"] or len(raw) != item["bytes"]:
        raise RuntimeError(f"V12 committed blob differs: {item['path']}")
    files.append({"path": item["path"], "bytes": len(raw), "sha256": digest,
                  "changed_in_delta": item["path"] in delta,
                  "changed_from_085b": item["path"] in cumulative})
manifest = {"schema": "researchos.c57-v12-exact-commit.v1", "commit": commit, "tree": tree,
            "parent": parent, "baseline": snapshot["base_commit"], "branch": branch,
            "source_snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
            "source_allowlist_count": len(files), "delta_count": len(delta),
            "cumulative_changed_count": len(cumulative), "inherited_pin_count": snapshot["inherited_pin_count"],
            "clean_worktree": not status, "delta_paths": sorted(delta), "files": files}
out = receipts / "C57-V12-COMMIT-SOURCE57-MANIFEST.json"
if out.exists():
    raise RuntimeError("V12 commit manifest exists; preserve it")
out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(receipts / "107-v12-postcommit-delta-names.raw").write_bytes(git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"))
(receipts / "107-v12-postcommit-cumulative-names.raw").write_bytes(git("diff", "--name-only", "-z", "085b4711afe0c1288448b174eef24ecd5af0551b", "HEAD"))
(receipts / "107-v12-postcommit-status.raw").write_bytes(status)
print(json.dumps({"commit": commit, "tree": tree, "parent": parent,
                  "delta_count": len(delta), "cumulative_changed_count": len(cumulative),
                  "manifest_sha256": hashlib.sha256(out.read_bytes()).hexdigest()}))
