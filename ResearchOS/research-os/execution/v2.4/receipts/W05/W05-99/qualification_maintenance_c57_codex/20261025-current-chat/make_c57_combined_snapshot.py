import hashlib
import json
import subprocess
import sys
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
scope_path = project / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp533/C57-source-scope.json"
boot_path = project / "execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat/final-v10-six-source-manifest.json"
scope = json.loads(scope_path.read_text(encoding="utf-8"))
boot = json.loads(boot_path.read_text(encoding="utf-8"))
source = scope["source_allowlist"]
if len(source) != 57 or len(set(source)) != 57:
    raise RuntimeError("C57 exact allowlist not 57 unique paths")
raw_status = subprocess.run(["git", "status", "--porcelain=v1", "-z", "-uall"], cwd=worktree,
                            check=True, capture_output=True).stdout
changed = set()
for record in raw_status.split(b"\0"):
    if not record:
        continue
    path = record[3:].decode("utf-8")
    if path not in source:
        raise RuntimeError(f"changed outside C57 allowlist: {path}")
    changed.add(path)
if len(changed) != 52:
    raise RuntimeError(f"expected 52 changed C51+Boot6 paths, got {len(changed)}")
files = []
for path in source:
    content = (worktree / path).read_bytes()
    files.append({"path": path, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                  "changed": path in changed})
file_by_path = {item["path"]: item for item in files}
for item in boot:
    if file_by_path[item["path"]]["sha256"] != item["sha256"]:
        raise RuntimeError(f"Boot6 V10 drift: {item['path']}")
r3 = json.loads((receipts / "C51-R3-SOURCEFREEZE.json").read_text(encoding="utf-8"))
for item in r3["owned_files"]:
    if file_by_path[item["path"]]["sha256"] != item["sha256"]:
        raise RuntimeError(f"C51 R3 drift: {item['path']}")
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
for item in preseal["inherited43_exact_pins"]:
    actual = hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest()
    if actual != item["sha256"]:
        raise RuntimeError(f"Source43 inherited pin drift: {item['path']}")
snapshot = {
    "schema": "researchos.c57-combined-source-snapshot.v1",
    "base_commit": scope["base_commit"], "base_tree": scope["base_tree"],
    "scope_sha256": hashlib.sha256(scope_path.read_bytes()).hexdigest(),
    "c51_r3_freeze_sha256": hashlib.sha256((receipts / "C51-R3-SOURCEFREEZE.json").read_bytes()).hexdigest(),
    "boot6_v10_manifest_sha256": hashlib.sha256(boot_path.read_bytes()).hexdigest(),
    "changed_count": len(changed), "inherited_pin_count": len(preseal["inherited43_exact_pins"]),
    "files": files,
}
name = sys.argv[1]
out = receipts / name
if out.exists():
    raise RuntimeError(f"snapshot exists: {name}")
out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
