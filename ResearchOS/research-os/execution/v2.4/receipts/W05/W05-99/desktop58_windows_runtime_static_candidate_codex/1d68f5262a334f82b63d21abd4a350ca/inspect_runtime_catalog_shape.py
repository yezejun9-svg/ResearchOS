"""Bounded shape/membership projection from exact 72ff frozen runtime catalog."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
path = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-72ff32d0d24a42c4a8effd849d54f882/runtime-resources.desktop58.json")
data = json.loads(path.read_bytes())
out = {"top_keys": sorted(data), "schema": data.get("schema"), "lists": {}, "wldp_exact_rows": []}
for key, val in data.items():
    if isinstance(val, list):
        out["lists"][key] = {"count": len(val), "first_row_keys": sorted(val[0]) if val and isinstance(val[0], dict) else None}
        for row in val:
            if isinstance(row, dict) and any("wldp.dll" in str(v).lower() for k, v in row.items() if k in ("path", "name", "canonical_path")):
                out["wldp_exact_rows"].append(row)
print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
