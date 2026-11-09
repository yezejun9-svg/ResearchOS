import difflib
import hashlib
import json
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
r2freeze = json.loads((receipts / "C51-R2-SOURCEFREEZE.json").read_text(encoding="utf-8"))
old_patch = (receipts / "C51-PRESEAL.patch").read_text(encoding="utf-8")
old_entries = {item["path"]: item for item in preseal["owned_files"]}
r2_entries = {item["path"]: item for item in r2freeze["owned_files"]}
paths = [
    "internal/qualificationmaintenancejournal/journal_windows.go",
    "internal/qualificationmaintenancejournal/journal_windows_test.go",
    "internal/host/qualification_failure_maintenance_windows_test.go",
]
delta = []
manifest = {"schema": "researchos.c51-r3-increment.v1",
            "base_r2_sourcefreeze_sha256": hashlib.sha256((receipts / "C51-R2-SOURCEFREEZE.json").read_bytes()).hexdigest(),
            "changed_paths": [], "test_receipts": []}
for path in paths:
    header = f"diff --git a/{path} b/{path}\n"
    section = old_patch.split(header, 1)[1].split("diff --git a/", 1)[0]
    if "--- /dev/null\n" not in section:
        raise RuntimeError(f"expected original added file: {path}")
    old_text = "".join(line[1:] for line in section.split("@@", 2)[2].splitlines(keepends=True) if line.startswith("+"))
    old = old_text.encode("utf-8")
    old_hash = hashlib.sha256(old).hexdigest()
    if old_hash != old_entries[path]["sha256"] or old_hash != r2_entries[path]["sha256"]:
        raise RuntimeError(f"R2 baseline differs from preseal: {path}")
    current = (worktree / path).read_bytes()
    if old == current:
        raise RuntimeError(f"no R3 delta: {path}")
    delta.extend(difflib.unified_diff(old_text.splitlines(keepends=True), current.decode("utf-8").splitlines(keepends=True),
                                      fromfile=f"a/{path}", tofile=f"b/{path}"))
    manifest["changed_paths"].append({"path": path, "r2_sha256": old_hash,
                                      "r3_sha256": hashlib.sha256(current).hexdigest(),
                                      "r2_bytes": len(old), "r3_bytes": len(current)})

delta_bytes = "".join(delta).encode("utf-8")
(receipts / "C51-R3-DELTA.patch").write_bytes(delta_bytes)
manifest["delta_sha256"] = hashlib.sha256(delta_bytes).hexdigest()
manifest["delta_bytes"] = len(delta_bytes)
for suffix in ("recipe.txt", "stdout.raw", "stderr.raw", "native-exit.txt"):
    path = receipts / f"061-r3-journal.{suffix}"
    manifest["test_receipts"].append({"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
(receipts / "C51-R3-INCREMENT.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
