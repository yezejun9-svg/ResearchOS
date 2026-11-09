import hashlib
import json
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
r3 = json.loads((receipts / "C51-R3-SOURCEFREEZE.json").read_text(encoding="utf-8"))
r4 = json.loads((receipts / "C51-R4-INCREMENT.json").read_text(encoding="utf-8"))
changed = {item["path"]: item for item in r4["changed_paths"]}
owned = []
for item in r3["owned_files"]:
    path = item["path"]
    raw = (worktree / path).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    expected = changed[path]["r4_sha256"] if path in changed else item["sha256"]
    if actual != expected:
        raise RuntimeError(f"owned51 changed outside R4: {path} {actual} expected {expected}")
    owned.append({"path": path, "bytes": len(raw), "sha256": actual, "changed_from_r3": path in changed})
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
for item in preseal["inherited43_exact_pins"]:
    if hashlib.sha256((worktree / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
        raise RuntimeError(f"inherited pin drift: {item['path']}")
freeze = {"schema": "researchos.c51-r4-sourcefreeze.v1", "base_commit": r3["base_commit"],
          "base_tree": r3["base_tree"], "scope_sha256": r3["scope_sha256"],
          "r3_sourcefreeze_sha256": hashlib.sha256((receipts / "C51-R3-SOURCEFREEZE.json").read_bytes()).hexdigest(),
          "r4_increment_sha256": hashlib.sha256((receipts / "C51-R4-INCREMENT.json").read_bytes()).hexdigest(),
          "owned_count": len(owned), "changed_from_r3_count": len(changed),
          "inherited_pin_count": len(preseal["inherited43_exact_pins"]), "owned_files": owned,
          "status": "SOURCE_FROZEN_NO_COMMIT_BOOT6_V11_PENDING"}
out = receipts / "C51-R4-SOURCEFREEZE.json"
if out.exists():
    raise RuntimeError("R4 sourcefreeze already exists; preserve it")
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(hashlib.sha256(out.read_bytes()).hexdigest())
