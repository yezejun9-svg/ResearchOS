import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True

repo = pathlib.Path(r"D:\作品集\ResearchOS\research-os")
parent = repo / "execution/v2.4/receipts/W05/W05-99/provider_budget_b01_targeted_readonly_codex/b01-20261008-0727"
base = parent / "failure_origins_20261008"
web_path = parent / "web_tool_io.json"
local_raw_path = base / "raw_local_bridge_failure.json"


def file_ref(path):
    content = path.read_bytes()
    return {
        "path": path.relative_to(repo).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
    }


def write_new(name, value):
    path = base / name
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")
    return file_ref(path)


web = json.loads(web_path.read_text(encoding="utf-8"))
matches = [(index, entry) for index, entry in enumerate(web["entries"]) if entry["id"] == "b01_web_open_1"]
assert len(matches) == 1
entry_index, entry = matches[0]
requests = entry["input"]["open"]
segments = entry["output"].split("\n--------------------------------------------------------------------------------\n")
assert len(requests) == len(segments) == 3
urls = [
    "https://api-docs.deepseek.com/api/create-chat-completion/",
    "https://api-docs.deepseek.com/guides/thinking_mode/",
    "https://opencode.ai/v2/docs/console/api/inference",
]
assert [request["ref_id"] for request in requests] == urls
assert all(url in segment for url, segment in zip(urls, segments))
assert "(400) Timeout fetching" in segments[0]
assert "(400) Timeout fetching" in segments[1]
assert "is not accessible via this tool" in segments[2]

source_web_ref = file_ref(web_path)
page_refs = []
for index, (request, segment) in enumerate(zip(requests, segments), start=1):
    status = "WEB_TOOL_FETCH_TIMEOUT" if index < 3 else "WEB_TOOL_URL_INACCESSIBLE"
    origin = {
        "schema": "researchos.failure-origin.public-page-open.v1",
        "origin_id": f"B01-PUBLIC-WEB-OPEN-{index:02d}",
        "count_increment": 1,
        "source_ref": source_web_ref,
        "source_entry_id": "b01_web_open_1",
        "source_entry_index_zero_based": entry_index,
        "source_request_index_zero_based": index - 1,
        "whole_web_tool_input": entry["input"],
        "attempted_open_input": request,
        "raw_result_segment": segment,
        "classification": status,
        "embedded_400_meaning": "web tool fetch diagnostic, not an observed provider HTTP status" if index < 3 else None,
        "outer_tool_exit_code": None,
        "python_exit_code": None,
        "provider_http_status": None,
        "retry_count": 0,
        "paid_or_private_request": False,
        "note": "One distinct page-open failure in one batched public web tool call; no source/model/production effect.",
    }
    page_refs.append(write_new(f"origin_{index:02d}.json", origin))

local_raw = json.loads(local_raw_path.read_text(encoding="utf-8"))
assert local_raw["returned"]["exit_code"] == 1
assert not local_raw["actual_python_exit_marker_observed"]
local_origin_ref = write_new("origin_04_local_bridge.json", {
    "schema": "researchos.failure-origin.local-evidence-read.v1",
    "origin_id": "B01-LOCAL-EVIDENCE-READ-01",
    "count_increment": 1,
    "raw_call_ref": file_ref(local_raw_path),
    "classification": "LOCAL_STDOUT_ENCODING_FAILURE",
    "tool": "exec_command",
    "exec_command_exit_code": 1,
    "actual_python_exit_marker_observed": False,
    "actual_python_exit_code": None,
    "outer_functions_exec_status": "completed; no separate numeric outer exit code established",
    "stderr_observation": "UnicodeEncodeError: GBK stdout could not encode a private-use citation character while printing an already stored Web result",
    "remote_retry_count": 0,
    "paid_or_private_request": False,
    "note": "Independent local display/encoding tool failure; not one of the three public page-open origins. A later UTF-8 read succeeded without a new Web request.",
})

refs_ref = write_new("refs.json", {
    "schema": "researchos.failure-origin.refs.v1",
    "source_web_tool_io_ref": source_web_ref,
    "source_local_tool_io_ref": file_ref(local_raw_path),
    "page_open_origin_refs": page_refs,
    "local_bridge_origin_ref": local_origin_ref,
})
manifest_ref = write_new("manifest.json", {
    "schema": "researchos.failure-origin.manifest.v1",
    "origin_refs": page_refs + [local_origin_ref],
    "refs_ref": refs_ref,
    "failure_origin_count": 4,
    "public_page_open_origins": 3,
    "additional_local_tool_origin": 1,
})
handoff_ref = write_new("handoff.json", {
    "schema": "researchos.failure-origin.handoff.v1",
    "source_head": "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7",
    "manifest_ref": manifest_ref,
    "refs_ref": refs_ref,
    "page_open_origin_refs": page_refs,
    "local_bridge_origin_ref": local_origin_ref,
    "requested_page_open_increment": 3,
    "additional_local_tool_increment": 1,
    "bookkeeping_if_same_failure_ledger": {"registered": 532, "observed": 545, "later_pending": 13},
    "existing_report_manifest_and_checkpoint_modified": False,
    "paid_or_private_or_model_calls": 0,
})
print("SEALED_ORIGINS=4")
print("HANDOFF_SHA256=" + handoff_ref["sha256"])
