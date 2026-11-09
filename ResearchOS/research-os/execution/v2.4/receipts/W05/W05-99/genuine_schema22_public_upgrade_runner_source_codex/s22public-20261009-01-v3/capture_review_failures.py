"""Preserve reviewer-side failed tool calls from the actual session log."""
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent
LOG = Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl")
raws = []
with LOG.open("rb") as stream:
    for raw in stream:
        raws.append((json.loads(raw), raw))
header, header_raw = raws[0]
assert header["type"] == "session_meta" and header["payload"]["id"] == "01a12011-7d41-7991-a01c-de2d71701ff7"

def pin(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

results = []
for index, (call, call_raw) in enumerate(raws):
    if call.get("ordinal", -1) < 6775 or call.get("type") != "response_item" or call.get("payload", {}).get("type") != "custom_tool_call" or call["payload"].get("name") != "exec":
        continue
    call_id = call["payload"]["call_id"]
    later = [(j, row, raw) for j, (row, raw) in enumerate(raws[index + 1:], index + 1)
             if row.get("type") == "response_item" and row.get("payload", {}).get("type") == "custom_tool_call_output" and row["payload"].get("call_id") == call_id]
    if len(later) != 1:
        continue
    output_index, output, output_raw = later[0]
    events = [(row, raw) for row, raw in raws[index + 1:output_index]
              if row.get("type") == "event_msg" and row.get("payload", {}).get("item", {}).get("type") == "CommandExecution"]
    if len(events) != 1 or events[0][0]["payload"]["item"].get("exit_code") in (None, 0):
        continue
    execution, exec_raw = events[0]
    selected = [(header, header_raw), (call, call_raw), (execution, exec_raw), (output, output_raw)]
    stem = "v3-review-failure-actual-call-" + str(call["ordinal"])
    capture = N / (stem + ".jsonl")
    capture.write_bytes(b"".join(raw for _, raw in selected))
    binding = {"schema": "researchos.public22-v3-review-actual-failed-tool-binding.v1",
               "source_log": LOG.as_posix(), "source_session_id": header["payload"]["id"],
               "source_ordinals": [row["ordinal"] for row, _ in selected], "original_call_id": call_id,
               "original_line_sha256": [hashlib.sha256(raw).hexdigest() for _, raw in selected],
               "source_line_bytes": [len(raw) for _, raw in selected],
               "actual_exit_code": execution["payload"]["item"]["exit_code"],
               "actual_call_timestamp": call["timestamp"], "actual_result_timestamp": output["timestamp"],
               "capture_ref": pin(capture), "classification": "Reviewer-side failed diagnostic/capture command; no product, Native, Go or Main child."}
    binding_path = N / (stem + ".binding.json")
    binding_path.write_text(json.dumps(binding, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    results.append({"call_ordinal": call["ordinal"], "call_id": call_id, "exit": binding["actual_exit_code"],
                    "capture": pin(capture), "binding": pin(binding_path)})
print(json.dumps(results, ensure_ascii=False))
