import hashlib
import json
import subprocess
import sys
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
scope_path = project / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp533/C57-source-scope.json"
boot_path = project / "execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat/final-v11-six-source-manifest.json"
c51_path = receipts / "C51-R4-SOURCEFREEZE.json"
scope = json.loads(scope_path.read_text(encoding="utf-8"))
boot = json.loads(boot_path.read_text(encoding="utf-8"))
c51 = json.loads(c51_path.read_text(encoding="utf-8"))
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
source = scope["source_allowlist"]
if len(source) != 57 or len(set(source)) != 57:
    raise RuntimeError("C57 exact allowlist not 57 unique paths")
status = subprocess.run(["git", "status", "--porcelain=v1", "-z", "-uall"], cwd=worktree,
                        check=True, capture_output=True).stdout
changed = set()
for record in status.split(b"\0"):
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
    raw = (worktree / path).read_bytes()
    files.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                  "changed": path in changed})
by_path = {item["path"]: item for item in files}
for group in (boot, c51["owned_files"]):
    for item in group:
        if by_path[item["path"]]["sha256"] != item["sha256"]:
            raise RuntimeError(f"frozen source drift: {item['path']}")
for item in preseal["inherited43_exact_pins"]:
    if hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError(f"Source43 inherited pin drift: {item['path']}")
snapshot = {"schema": "researchos.c57-combined-v11-source-snapshot.v1",
            "base_commit": scope["base_commit"], "base_tree": scope["base_tree"],
            "scope_sha256": hashlib.sha256(scope_path.read_bytes()).hexdigest(),
            "c51_r4_freeze_sha256": hashlib.sha256(c51_path.read_bytes()).hexdigest(),
            "boot6_v11_manifest_sha256": hashlib.sha256(boot_path.read_bytes()).hexdigest(),
            "changed_count": len(changed), "inherited_pin_count": len(preseal["inherited43_exact_pins"]),
            "files": files}
out = receipts / sys.argv[1]
if out.exists():
    raise RuntimeError(f"snapshot exists: {out.name}")
out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
