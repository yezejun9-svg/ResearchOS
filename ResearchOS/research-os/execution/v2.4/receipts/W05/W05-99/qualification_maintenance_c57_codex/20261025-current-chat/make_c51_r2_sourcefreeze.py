import hashlib
import json
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
r2 = json.loads((receipts / "C51-R2-FINAL.json").read_text(encoding="utf-8"))
changed = {item["path"]: item for item in r2["changed_paths"]}
owned = []
for item in preseal["owned_files"]:
    path = item["path"]
    raw = (worktree / path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    expected = changed[path]["r2_sha256"] if path in changed else item["sha256"]
    if actual != expected:
        raise RuntimeError(f"owned51 changed outside R2: {path} {actual} expected {expected}")
    owned.append({"path": path, "bytes": len(raw), "sha256": actual, "changed_from_preseal": path in changed})
pins = []
for item in preseal["inherited43_exact_pins"]:
    raw = (worktree / item["path"]).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != item["sha256"]:
        raise RuntimeError(f"inherited pin drift: {item['path']}")
    pins.append(item["path"])
freeze = {
    "schema": "researchos.c51-r2-sourcefreeze.v1",
    "base_commit": preseal["base_commit"],
    "base_tree": preseal["base_tree"],
    "scope_sha256": preseal["scope_sha256"],
    "old_preseal_sha256": hashlib.sha256((receipts / "C51-PRESEAL.json").read_bytes()).hexdigest(),
    "r2_final_sha256": hashlib.sha256((receipts / "C51-R2-FINAL.json").read_bytes()).hexdigest(),
    "owned_count": len(owned),
    "changed_from_preseal_count": len(changed),
    "inherited_pin_count": len(pins),
    "owned_files": owned,
    "inherited_pins_verified": pins,
    "status": "SOURCE_FROZEN_NO_COMMIT_BOOT6_SEPARATE",
}
out = receipts / "C51-R2-SOURCEFREEZE.json"
if out.exists():
    raise RuntimeError("R2 sourcefreeze already exists; preserve it")
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
