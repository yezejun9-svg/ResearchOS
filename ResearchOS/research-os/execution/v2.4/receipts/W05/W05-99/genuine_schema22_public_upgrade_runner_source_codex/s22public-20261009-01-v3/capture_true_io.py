"""Extract exact recorded tool-call/CommandExecution/output lines; no replay."""
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent
LOG = Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\09\rollout-2026-10-09T17-49-39-01a12011-7d41-7991-a01c-de2d71701ff7.jsonl")
raws = []
with LOG.open("rb") as stream:
    for raw in stream:
        raws.append((json.loads(raw), raw))

def pin(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def extract(label, fragment, expected_exit):
    calls = [(index, row, raw) for index, (row, raw) in enumerate(raws)
             if row.get("type") == "response_item" and row.get("payload", {}).get("type") == "custom_tool_call"
             and row["payload"].get("name") == "exec"
             and row["payload"].get("input", "").startswith('const r=await tools.exec_command({cmd:"python -B ')
             and fragment in row["payload"].get("input", "")]
    assert calls, label
    call_index, call, call_raw = calls[-1]
    call_id = call["payload"]["call_id"]
    outcomes = [(i, row, raw) for i, (row, raw) in enumerate(raws[call_index + 1:], call_index + 1)
                if row.get("type") == "response_item" and row.get("payload", {}).get("type") == "custom_tool_call_output"
                and row["payload"].get("call_id") == call_id]
    assert len(outcomes) == 1
    output_index, output, output_raw = outcomes[0]
    executions = [(i, row, raw) for i, (row, raw) in enumerate(raws[call_index + 1:output_index], call_index + 1)
                  if row.get("type") == "event_msg" and row.get("payload", {}).get("item", {}).get("type") == "CommandExecution"]
    assert len(executions) == 1, (label, len(executions))
    exec_index, execution, exec_raw = executions[0]
    assert execution["payload"]["item"].get("exit_code") == expected_exit
    header, header_raw = raws[0]
    assert header["type"] == "session_meta" and header["payload"]["id"] == "01a12011-7d41-7991-a01c-de2d71701ff7"
    selected = [(header, header_raw), (call, call_raw), (execution, exec_raw), (output, output_raw)]
    capture = N / (label + ".actual-fullhostpair.jsonl")
    capture.write_bytes(b"".join(raw for _, raw in selected))
    binding = {
        "schema": "researchos.public22-v3-source-actual-tool-hostpair-binding.v1",
        "label": label,
        "source_log": LOG.as_posix(),
        "source_session_id": header["payload"]["id"],
        "source_ordinals": [row["ordinal"] for row, _ in selected],
        "original_call_id": call_id,
        "original_line_sha256": [hashlib.sha256(raw).hexdigest() for _, raw in selected],
        "source_line_bytes": [len(raw) for _, raw in selected],
        "actual_exit_code": expected_exit,
        "actual_call_timestamp": call["timestamp"],
        "actual_result_timestamp": output["timestamp"],
        "capture_ref": pin(capture),
        "scope": "Reviewer-side Source control/read-only diagnostic tool pair; no product execution or original1025 reclassification.",
    }
    path = N / (label + ".actual-fullhostpair.binding.json")
    path.write_text(json.dumps(binding, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"capture": pin(capture), "binding": pin(path), "ordinals": binding["source_ordinals"]}

def main():
    result = {
        "controls": extract("v3-source-controls", "source_controls.py", 0),
        "readonly": extract("v3-existing-readonly", "actual_readonly_probe.py", 0),
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
