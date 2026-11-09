import difflib
import hashlib
import json
from pathlib import Path

receipts = Path(__file__).parent
worktree = Path(r"D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-maintenance-c57-20261025")
path = "internal/domain/backup_source_lease_windows_test.go"
preseal = json.loads((receipts / "C51-PRESEAL.json").read_text(encoding="utf-8"))
r3freeze = json.loads((receipts / "C51-R3-SOURCEFREEZE.json").read_text(encoding="utf-8"))
preseal_item = next(item for item in preseal["owned_files"] if item["path"] == path)
r3_item = next(item for item in r3freeze["owned_files"] if item["path"] == path)
section = (receipts / "C51-PRESEAL.patch").read_text(encoding="utf-8").split(f"diff --git a/{path} b/{path}\n", 1)[1].split("diff --git a/", 1)[0]
if "--- /dev/null\n" not in section:
    raise RuntimeError("expected original added file")
old_text = "".join(line[1:] for line in section.split("@@", 2)[2].splitlines(keepends=True) if line.startswith("+"))
old = old_text.encode("utf-8")
old_hash = hashlib.sha256(old).hexdigest()
if old_hash != preseal_item["sha256"] or old_hash != r3_item["sha256"]:
    raise RuntimeError("R3 baseline differs from preseal")
current = (worktree / path).read_bytes()
delta = "".join(difflib.unified_diff(old_text.splitlines(keepends=True), current.decode("utf-8").splitlines(keepends=True),
                                     fromfile=f"a/{path}", tofile=f"b/{path}")).encode("utf-8")
(receipts / "C51-R4-DELTA.patch").write_bytes(delta)
manifest = {"schema": "researchos.c51-r4-increment.v1",
            "base_r3_sourcefreeze_sha256": hashlib.sha256((receipts / "C51-R3-SOURCEFREEZE.json").read_bytes()).hexdigest(),
            "changed_paths": [{"path": path, "r3_sha256": old_hash, "r4_sha256": hashlib.sha256(current).hexdigest(),
                               "r3_bytes": len(old), "r4_bytes": len(current)}],
            "delta_sha256": hashlib.sha256(delta).hexdigest(), "delta_bytes": len(delta),
            "test_receipts": []}
for id in ("065-domain", "070-domain-lease-isolate", "071-domain-lease-isolate", "073-domain-lease-d-env", "074-domain-combined-r4"):
    prefix = f"combined-{id}" if id == "065-domain" else id
    for suffix in ("recipe.txt", "stdout.raw", "stderr.raw", "native-exit.txt"):
        item = receipts / f"{prefix}.{suffix}"
        manifest["test_receipts"].append({"path": item.name, "sha256": hashlib.sha256(item.read_bytes()).hexdigest()})
(receipts / "C51-R4-INCREMENT.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
