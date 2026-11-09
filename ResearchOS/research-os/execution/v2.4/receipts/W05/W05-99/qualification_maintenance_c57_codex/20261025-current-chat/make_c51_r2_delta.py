import difflib
import hashlib
import json
from pathlib import Path


receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
old_patch = (receipts / "C51-PRESEAL.patch").read_text(encoding="utf-8")
paths = [
    "internal/domain/qualification_failure_maintenance_windows.go",
    "internal/domain/qualification_failure_maintenance_windows_test.go",
]
old_entries = {item["path"]: item for item in preseal["owned_files"]}
delta = []
manifest = {
    "schema": "researchos.c51-r2-increment.v1",
    "base_preseal_sha256": hashlib.sha256((receipts / "C51-PRESEAL.json").read_bytes()).hexdigest(),
    "base_patch_sha256": hashlib.sha256((receipts / "C51-PRESEAL.patch").read_bytes()).hexdigest(),
    "changed_paths": [],
    "test_receipts": [],
}

for path in paths:
    header = f"diff --git a/{path} b/{path}\n"
    section = old_patch.split(header, 1)[1].split("diff --git a/", 1)[0]
    if "--- /dev/null\n" not in section:
        raise RuntimeError(f"expected original added file: {path}")
    hunk = section.split("@@", 2)[2]
    old_text = "".join(line[1:] for line in hunk.splitlines(keepends=True) if line.startswith("+"))
    old = old_text.encode("utf-8")
    old_hash = hashlib.sha256(old).hexdigest()
    if old_hash != old_entries[path]["sha256"]:
        raise RuntimeError(f"preseal reconstruction hash mismatch: {path}: {old_hash}")
    current = (worktree / path).read_bytes()
    if old == current:
        raise RuntimeError(f"no r2 delta: {path}")
    current_text = current.decode("utf-8")
    delta.extend(difflib.unified_diff(old_text.splitlines(keepends=True), current_text.splitlines(keepends=True),
                                      fromfile=f"a/{path}", tofile=f"b/{path}"))
    manifest["changed_paths"].append({"path": path, "preseal_sha256": old_hash,
                                      "r2_sha256": hashlib.sha256(current).hexdigest(),
                                      "preseal_bytes": len(old), "r2_bytes": len(current)})

delta_bytes = "".join(delta).encode("utf-8")
delta_path = receipts / "C51-R2-DELTA.patch"
if delta_path.exists():
    if delta_path.read_bytes() != delta_bytes:
        raise RuntimeError("existing R2 delta differs; preserve it and create a new suffix")
else:
    delta_path.write_bytes(delta_bytes)
manifest["delta_sha256"] = hashlib.sha256(delta_bytes).hexdigest()
manifest["delta_bytes"] = len(delta_bytes)
for number in ("055", "056", "057", "058"):
    for suffix in ("recipe.txt", "stdout.raw", "stderr.raw", "native-exit.txt"):
        item = receipts / f"{number}-r2-domain.{suffix}"
        manifest["test_receipts"].append({"path": item.name, "sha256": hashlib.sha256(item.read_bytes()).hexdigest()})
(receipts / "C51-R2-FINAL.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
