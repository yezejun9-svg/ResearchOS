import hashlib
import json
from pathlib import Path

source = Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl")
out = Path(__file__).resolve().parent
wanted = {0, 6319, 6321, 6322}
raws = []
with source.open("rb") as f:
    for line in f:
        row = json.loads(line)
        if row.get("ordinal") in wanted:
            raws.append((row["ordinal"], line))
assert [n for n, _ in raws] == sorted(wanted)
capture = b"".join(x for _, x in raws)
assert b"call_c090aaac8cd54e41827ea837b6aeea71" in capture
capture_path = out / "source-controls-actual-fullhostpair.jsonl"
capture_path.write_bytes(capture)

def ref(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

binding = {
    "schema": "researchos.source-review-actual-control-hostpair-binding.v1",
    "source_log": source.as_posix(),
    "source_session_id": "01a12011-7d41-7991-a01c-de2d71701ff7",
    "source_ordinals": [n for n, _ in raws],
    "original_call_id": "call_c090aaac8cd54e41827ea837b6aeea71",
    "original_line_sha256": [hashlib.sha256(x).hexdigest() for _, x in raws],
    "source_line_bytes": [len(x) for _, x in raws],
    "capture_ref": ref(capture_path),
    "classification": "Actual reviewer-side Python pure Source controls; exit 0, no Main23 child execution.",
}
binding_path = out / "source-controls-actual-fullhostpair.binding.json"
binding_path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"capture": ref(capture_path), "binding": ref(binding_path)}))
