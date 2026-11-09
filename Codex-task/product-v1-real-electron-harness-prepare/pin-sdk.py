"""Hash the public installed playwright-core package only, without importing it."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/yqyyds/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core")
rows = []
for file in sorted(ROOT.rglob("*")):
    if file.is_symlink():
        raise SystemExit("SDK_ALIAS_REFUSED")
    if file.is_file():
        raw = file.read_bytes()
        rows.append({"path": file.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
payload = {"schema": "researchos.public-sdk-inventory/1", "root": str(ROOT), "version": "1.62.1", "files": rows,
           "status": "STATIC_HASHED_NOT_IMPORTED_OR_EXECUTED"}
target = HERE / "SDK_INVENTORY.json"
if target.exists():
    raise SystemExit("SDK_INVENTORY_ALREADY_EXISTS")
target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"path": str(target), "files": len(rows), "bytes": sum(row["bytes"] for row in rows),
                  "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}))
