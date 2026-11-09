import hashlib
import json
import subprocess
import sys
from pathlib import Path

receipts = Path(__file__).parent
project = Path(r"D:\作品集\ResearchOS\research-os")
worktree = project / ".local/worktrees/qualification-maintenance-c57-20261025"
scope_path = project / "execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp533/C57-source-scope.json"
boot_dir = project / "execution/v2.4/receipts/W05/W05-99/qualification_recovery_boundary_boot6_codex/20261025-current-chat"
boot_path = boot_dir / "final-v12-six-source-manifest.json"
scope = json.loads(scope_path.read_text(encoding="utf-8"))
boot = json.loads(boot_path.read_text(encoding="utf-8"))
first = json.loads((receipts / "C57-COMMIT-SOURCE57-MANIFEST.json").read_text(encoding="utf-8"))
c51 = json.loads((receipts / "C51-R4-SOURCEFREEZE.json").read_text(encoding="utf-8"))
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
source = scope["source_allowlist"]
delta_expected = {"internal/recoveryboundary/boot_windows.go", "internal/recoveryboundary/boot_windows_test.go"}
if len(source) != 57 or len(set(source)) != 57 or first["commit"] != "08d63ed86356a93fe5715732cfeae0624c5cb6c9":
    raise RuntimeError("frozen C57 scope or first commit invalid")
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, check=True, capture_output=True).stdout.decode().strip()
if head != first["commit"]:
    raise RuntimeError("V12 parent HEAD changed")
status = subprocess.run(["git", "status", "--porcelain=v1", "-z", "-uall"], cwd=worktree,
                        check=True, capture_output=True).stdout
delta = {record[3:].decode("utf-8") for record in status.split(b"\0") if record}
if delta != delta_expected:
    raise RuntimeError(f"V12 changed paths differ: {sorted(delta)}")
files = []
for path in source:
    raw = (worktree / path).read_bytes()
    files.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                  "changed_from_08d63": path in delta,
                  "changed_from_085b": next(item["changed_in_commit"] for item in first["files"] if item["path"] == path)})
by_path = {item["path"]: item for item in files}
for item in boot + c51["owned_files"]:
    if by_path[item["path"]]["sha256"] != item["sha256"]:
        raise RuntimeError(f"frozen source drift: {item['path']}")
for old in first["files"]:
    if old["path"] not in delta and by_path[old["path"]]["sha256"] != old["sha256"]:
        raise RuntimeError(f"unlicensed V12 source drift: {old['path']}")
for item in preseal["inherited43_exact_pins"]:
    if hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError(f"Source43 inherited pin drift: {item['path']}")
snapshot = {"schema": "researchos.c57-v12-source-snapshot.v1", "parent_commit": head,
            "base_commit": scope["base_commit"], "base_tree": scope["base_tree"],
            "scope_sha256": hashlib.sha256(scope_path.read_bytes()).hexdigest(),
            "first_commit_manifest_sha256": hashlib.sha256((receipts / "C57-COMMIT-SOURCE57-MANIFEST.json").read_bytes()).hexdigest(),
            "c51_r4_freeze_sha256": hashlib.sha256((receipts / "C51-R4-SOURCEFREEZE.json").read_bytes()).hexdigest(),
            "boot6_v12_manifest_sha256": hashlib.sha256(boot_path.read_bytes()).hexdigest(),
            "boot6_v12_seal_sha256": hashlib.sha256((boot_dir / "final-v12-additive-seal.json").read_bytes()).hexdigest(),
            "v12_delta_count": len(delta), "cumulative_changed_count": sum(item["changed_from_085b"] for item in files),
            "inherited_pin_count": len(preseal["inherited43_exact_pins"]), "files": files}
out = receipts / sys.argv[1]
if out.exists():
    raise RuntimeError(f"snapshot exists: {out.name}")
out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
