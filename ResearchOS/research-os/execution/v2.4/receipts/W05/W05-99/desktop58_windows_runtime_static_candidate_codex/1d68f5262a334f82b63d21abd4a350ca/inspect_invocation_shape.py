"""Pure JSON inspection of an explicitly named failed invocation; no child execution."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
path = Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/build-current58.invocation.json")
data = json.loads(path.read_bytes())
out = {"type": type(data).__name__, "top_keys": sorted(data) if isinstance(data, dict) else None,
       "selected_fields": []}

def visit(obj, parents=()):
    if len(out["selected_fields"]) >= 24 or len(parents) > 9:
        return
    if isinstance(obj, dict):
        for key, val in obj.items():
            where = parents + (key,)
            low = key.lower()
            if any(term in low for term in ("runtime", "catalog", "scope", "registration", "failure", "wldp")):
                if isinstance(val, dict):
                    item = {k: val.get(k) for k in ("path", "sha256", "bytes", "schema", "state", "error") if k in val}
                    if item: out["selected_fields"].append({"key_path": ".".join(where), "projection": item})
                elif isinstance(val, (str, int, float, bool)) or val is None:
                    out["selected_fields"].append({"key_path": ".".join(where), "value": val if isinstance(val, (int, float, bool)) or val is None else val[:220]})
            if isinstance(val, (dict, list)):
                visit(val, where)
    elif isinstance(obj, list):
        for idx, val in enumerate(obj[:20]):
            if isinstance(val, (dict, list)): visit(val, parents + (str(idx),))

visit(data)
print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
