import hashlib
import json
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
r2freeze = json.loads((receipts / "C51-R2-SOURCEFREEZE.json").read_text(encoding="utf-8"))
r3 = json.loads((receipts / "C51-R3-INCREMENT.json").read_text(encoding="utf-8"))
changed = {item["path"]: item for item in r3["changed_paths"]}
owned = []
for item in r2freeze["owned_files"]:
    path = item["path"]
    raw = (worktree / path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    expected = changed[path]["r3_sha256"] if path in changed else item["sha256"]
    if actual != expected:
        raise RuntimeError(f"owned51 changed outside R3: {path} {actual} expected {expected}")
    owned.append({"path": path, "bytes": len(raw), "sha256": actual, "changed_from_r2": path in changed})
for path in r2freeze["inherited_pins_verified"]:
    raw = (worktree / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != next(item["sha256"] for item in json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))["inherited43_exact_pins"] if item["path"] == path):
        raise RuntimeError(f"inherited pin drift: {path}")
freeze = {
    "schema": "researchos.c51-r3-sourcefreeze.v1",
    "base_commit": r2freeze["base_commit"], "base_tree": r2freeze["base_tree"],
    "scope_sha256": r2freeze["scope_sha256"],
    "r2_sourcefreeze_sha256": hashlib.sha256((receipts / "C51-R2-SOURCEFREEZE.json").read_bytes()).hexdigest(),
    "r3_increment_sha256": hashlib.sha256((receipts / "C51-R3-INCREMENT.json").read_bytes()).hexdigest(),
    "owned_count": len(owned), "changed_from_r2_count": len(changed),
    "inherited_pin_count": len(r2freeze["inherited_pins_verified"]),
    "owned_files": owned,
    "status": "SOURCE_FROZEN_NO_COMMIT_BOOT6_SEPARATE",
}
out = receipts / "C51-R3-SOURCEFREEZE.json"
if out.exists():
    raise RuntimeError("R3 sourcefreeze already exists; preserve it")
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
