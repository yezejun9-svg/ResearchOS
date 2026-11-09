"""Copy exact, finite execution records from this agent's original session log."""
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent
LOG = Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl")
TARGETS = ("rebase_source.py", "peer_audit_controls.py", "source_guard_proof.py")

records = []
offset = 0
with LOG.open("rb") as stream:
    for ordinal, raw in enumerate(stream):
        record = json.loads(raw)
        records.append((offset, raw, record))
        offset += len(raw)

header = records[0]
assert header[2]["type"] == "session_meta" and header[2]["payload"]["id"] == "01a12011-7d41-7991-a01c-de2d71701ff7"
proof = {"schema": "researchos.w09.fullw09-source-real-hostpairs.v1", "source_log": str(LOG), "source_prefix_size_observed": offset, "captures": []}
for target in TARGETS:
    matches = []
    for i, (pos, raw, rec) in enumerate(records):
        item = rec.get("payload", {})
        if rec.get("type") == "response_item" and item.get("type") == "custom_tool_call" and item.get("name") == "exec":
            if target in item.get("input", "") and "tools.exec_command" in item.get("input", ""):
                matches.append(i)
    assert matches, target
    # The successful invocation is the last matching call before the source record.
    selected = None
    for i in matches:
        call = records[i][2]["payload"]
        call_id = call.get("call_id")
        outputs = [(j, r) for j, (_, _, r) in enumerate(records[i + 1:], i + 1)
                   if r.get("type") == "response_item" and r.get("payload", {}).get("call_id") == call_id
                   and r.get("payload", {}).get("type") in {"function_call_output", "custom_tool_call_output"}]
        if not outputs:
            continue
        j, result = outputs[0]
        text = json.dumps(result.get("payload", {}), ensure_ascii=False)
        if 'exit_code\\":0' in text or 'exit_code\\": 0' in text or 'exit_code":0' in text or 'exit_code": 0' in text:
            selected = (i, j)
    assert selected, target
    i, j = selected
    pair = [header, records[i], records[j]]
    raw = b"".join(row[1] for row in pair)
    dest = N / (target.replace(".py", "") + ".actual-host.raw.jsonl")
    dest.write_bytes(raw)
    proof["captures"].append({
        "target": target,
        "actual_capture_ref": {"path": str(dest), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
        "source_line_offsets": [row[0] for row in pair],
        "source_line_bytes": [len(row[1]) for row in pair],
        "original_line_sha256": [hashlib.sha256(row[1]).hexdigest() for row in pair],
        "source_ordinals": [row[2]["ordinal"] for row in pair],
        "call_id": records[i][2]["payload"]["call_id"],
        "call_timestamp": records[i][2]["timestamp"],
        "result_timestamp": records[j][2]["timestamp"],
    })

# Preserve the first failed invocation of this exact capture script as original1044.
failure = next((j for j, (_, _, rec) in enumerate(records)
                if rec.get("type") == "response_item"
                and rec.get("payload", {}).get("type") == "custom_tool_call_output"
                and "073ed3" in json.dumps(rec.get("payload", {}).get("output", []), ensure_ascii=False)), None)
assert failure is not None
failure_id = records[failure][2]["payload"]["call_id"]
failure_call = next(i for i, (_, _, rec) in enumerate(records[:failure])
                    if rec.get("type") == "response_item"
                    and rec.get("payload", {}).get("type") == "custom_tool_call"
                    and rec.get("payload", {}).get("call_id") == failure_id)
assert "python -B capture_hostpairs.py" in records[failure_call][2]["payload"]["input"]
pair = [header, records[failure_call], records[failure]]
raw = b"".join(row[1] for row in pair)
dest = N / "capture-hostpairs-failure-073ed3.actual-host.raw.jsonl"
dest.write_bytes(raw)
proof["captures"].append({
    "target": "capture_hostpairs.py:first_failed_invocation",
    "original_failure": "original1044",
    "actual_capture_ref": {"path": str(dest), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
    "source_line_offsets": [row[0] for row in pair],
    "source_line_bytes": [len(row[1]) for row in pair],
    "original_line_sha256": [hashlib.sha256(row[1]).hexdigest() for row in pair],
    "source_ordinals": [row[2]["ordinal"] for row in pair],
    "call_id": failure_id,
    "call_timestamp": records[failure_call][2]["timestamp"],
    "result_timestamp": records[failure][2]["timestamp"],
    "chunk_id": "073ed3",
    "exit_code": 1,
})

# Preserve the subsequent read-only PowerShell diagnostic original1045.
diagnostic_calls = [(i, rec) for i, (_, _, rec) in enumerate(records)
                    if rec.get("type") == "response_item"
                    and rec.get("payload", {}).get("type") == "custom_tool_call"
                    and rec.get("payload", {}).get("name") == "exec"
                    and "$p.Substring" in rec.get("payload", {}).get("input", "")
                    and "rebase_source.actual-host.raw.jsonl" in rec.get("payload", {}).get("input", "")]
for i, call_rec in diagnostic_calls:
    call_id = call_rec["payload"]["call_id"]
    results = [(j, rec) for j, (_, _, rec) in enumerate(records[i + 1:], i + 1)
               if rec.get("type") == "response_item"
               and rec.get("payload", {}).get("type") == "custom_tool_call_output"
               and rec.get("payload", {}).get("call_id") == call_id]
    if not results:
        continue
    j, result_rec = results[0]
    if "does not contain a method named 'Substring'" not in json.dumps(result_rec["payload"]["output"], ensure_ascii=False):
        continue
    pair = [header, records[i], records[j]]
    raw = b"".join(row[1] for row in pair)
    dest = N / "powershell-substring-diagnostic.actual-host.raw.jsonl"
    dest.write_bytes(raw)
    proof["captures"].append({
        "target": "PowerShell read-only output-shape diagnostic",
        "original_failure": "original1045",
        "actual_capture_ref": {"path": str(dest), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
        "source_line_offsets": [row[0] for row in pair],
        "source_line_bytes": [len(row[1]) for row in pair],
        "original_line_sha256": [hashlib.sha256(row[1]).hexdigest() for row in pair],
        "source_ordinals": [row[2]["ordinal"] for row in pair],
        "call_id": call_id,
        "call_timestamp": records[i][2]["timestamp"],
        "result_timestamp": records[j][2]["timestamp"],
        "outer_exit_code": 0,
        "PowerShell_diagnostic_error": "Method invocation failed: PSCustomObject has no Substring method",
    })
    break

dest = N / "actual-hostpairs.binding.json"
dest.write_text(json.dumps(proof, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"binding_ref": {"path": str(dest), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "bytes": dest.stat().st_size}, "targets": [x["target"] for x in proof["captures"]]}, ensure_ascii=False))
