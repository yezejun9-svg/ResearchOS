"""Inspect only the structural shape of Root's pinned nonformal sample."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
root = P.parents[6]
sample = root / ("execution/v2.4/receipts/W09/W09-99/"
                 "checkpoint_r369_native_source_root/cp369-c19-20261009/"
                 "nonformal-registration-delivery.original.root.jsonl")
raw = sample.read_bytes()
assert len(raw) == 24304
assert hashlib.sha256(raw).hexdigest() == "219312642745d2ee5cc919a410faa2e59e560aba41b0dfef399e792aeeb7f900"
lines = raw.splitlines(keepends=True)
assert len(lines) == 3
records = [json.loads(line) for line in lines]
print(json.dumps({
    "line_sha256": [hashlib.sha256(line).hexdigest() for line in lines],
    "records": [{
        "type": item.get("type"), "timestamp": item.get("timestamp"),
        "ordinal": item.get("ordinal"),
        "top_keys": sorted(item),
        "payload_keys": sorted(item.get("payload", {})),
        "payload_type": item.get("payload", {}).get("type"),
        "payload_id": item.get("payload", {}).get("id"),
        "payload_author": item.get("payload", {}).get("author"),
        "payload_recipient": item.get("payload", {}).get("recipient"),
        "payload_content_type": type(item.get("payload", {}).get("content")).__name__,
        "payload_content_item_shapes": [sorted(v) for v in item.get("payload", {}).get("content", [])]
            if isinstance(item.get("payload", {}).get("content"), list) else None,
        "metadata_keys": sorted(item.get("metadata", {})),
    } for item in records],
}, ensure_ascii=False, indent=2))
