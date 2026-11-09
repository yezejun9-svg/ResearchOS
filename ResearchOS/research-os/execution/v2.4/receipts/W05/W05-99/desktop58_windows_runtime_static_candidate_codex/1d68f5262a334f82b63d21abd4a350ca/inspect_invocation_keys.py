"""Print only type and key names from the exact failed-build JSON."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
path = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/build-current58.invocation.json")
data = json.loads(path.read_bytes())
out = {}
for group in ("request", "result", "exception"):
    obj = data.get(group)
    out[group] = {"type": type(obj).__name__, "keys": sorted(obj) if isinstance(obj, dict) else None,
                  "list_length": len(obj) if isinstance(obj, list) else None}
print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
