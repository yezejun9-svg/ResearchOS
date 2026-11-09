"""Pure source-copy revision for original multi-record CLI JSONL streams."""
import ast
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path("D:/作品集/ResearchOS/research-os")
HERE = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb"
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17"


def ref(path):
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(name, raw):
    path = HERE / name
    with path.open("xb") as stream:
        stream.write(raw)
    assert path.read_bytes() == raw
    return ref(path)


old = (OLD / "mu_sdk_trial.v5.final.proposed.py").read_text(encoding="utf-8")
needle = '''    rows = [row for row in parsed if row.get("command") == name]
    require(len(rows) == len(parsed) == 1, "CLI_CONTEXT_JSONL_NOT_UNIQUE")
    row = rows[0]
'''
print("ANCHOR_COUNT=" + str(old.count(needle)))
assert old.count(needle) == 1
helper = '''def original_cli_summary_stream(label, parsed):
    """Validate each original outJSON record, including live event streaming."""
    name = "goal" if label == "cli-goal" else "run"
    require(isinstance(parsed, list) and 1 <= len(parsed) <= 65537 and
            all(isinstance(item, dict) for item in parsed),
            "CLI_JSONL_STREAM_SHAPE")
    summary = parsed[-1]
    require(summary.get("command") == name and "type" not in summary and
            type(summary.get("exit_code")) is int and summary["exit_code"] == 0 and
            len([item for item in parsed if "command" in item]) == 1,
            "CLI_FINAL_SUMMARY_NOT_UNIQUE_OR_LAST")
    operations = summary.get("operations")
    require(isinstance(operations, list) and operations and
            all(isinstance(item, dict) for item in operations),
            "CLI_FINAL_OPERATIONS_INVALID")
    first_method = operations[0].get("method")
    if first_method in ("session.create", "session.get"):
        first_result = operations[0].get("result")
        require(isinstance(first_result, dict), "CLI_FIRST_OPERATION_RESULT_INVALID")
        first_snapshot = first_result.get("snapshot", first_result)
        require(isinstance(first_snapshot, dict) and
                type(first_snapshot.get("event_sequence")) is int and
                first_snapshot["event_sequence"] >= 0,
                "CLI_EVENT_INITIAL_CURSOR_INVALID")
        cursor = first_snapshot["event_sequence"]
    else:
        require(name == "goal" and first_method == "goal.start",
                "CLI_EVENT_INITIAL_OPERATION_INVALID")
        cursor = 0
    final_snapshot = summary.get("last_verified_session_snapshot")
    execution = summary.get("execution")
    require(isinstance(final_snapshot, dict) and isinstance(execution, dict) and
            execution.get("status") == "EXECUTION_REPORTED" and
            type(execution.get("exit_code")) is int and execution["exit_code"] == 0 and
            execution.get("independent_acceptance") == "NOT_EVALUATED" and
            execution.get("reason") == "HOST_EXECUTION_SETTLED" and
            isinstance(execution.get("run_id"), str) and execution["run_id"] and
            isinstance(summary.get("admission_command_id"), str) and
            summary["admission_command_id"] and
            execution.get("project_id") == final_snapshot.get("project_id") and
            execution.get("session_id") == summary.get("session_id") ==
            final_snapshot.get("session_id"),
            "CLI_FINAL_EXECUTION_SCOPE_INVALID")
    last_result = operations[-1].get("result")
    require(isinstance(last_result, dict), "CLI_ADMISSION_RESULT_INVALID")
    if name == "run":
        require(last_result.get("message_id") == execution.get("message_id") and
                isinstance(execution.get("message_id"), str) and execution["message_id"] and
                (not last_result.get("run_id") or
                 last_result.get("run_id") == execution["run_id"]),
                "CLI_RUN_ADMISSION_IDENTITY_MISMATCH")
    else:
        require(last_result.get("goal_id") == execution.get("goal_id") and
                isinstance(execution.get("goal_id"), str) and execution["goal_id"],
                "CLI_GOAL_ADMISSION_IDENTITY_MISMATCH")
    build = final_snapshot.get("core_build_id")
    protocol = final_snapshot.get("protocol_version")
    require(isinstance(build, str) and build and isinstance(protocol, str) and protocol,
            "CLI_FINAL_SNAPSHOT_BUILD_OR_PROTOCOL_ABSENT")
    seen = set()
    for item in parsed[:-1]:
        kind = item.get("type")
        require(set(item) == {"type", "event"} and kind == "session.event",
                "CLI_UNKNOWN_OR_RESYNC_STREAM_RECORD")
        event = item.get("event")
        require(isinstance(event, dict) and type(event.get("sequence")) is int and
                event["sequence"] == cursor + 1 and
                isinstance(event.get("event_id"), str) and event["event_id"] and
                event["event_id"] not in seen and
                isinstance(event.get("kind"), str) and event["kind"] and
                isinstance(event.get("payload"), dict) and
                event.get("session_id") == summary.get("session_id") and
                event.get("protocol_version") == protocol and
                event.get("core_build_id") == build and
                (event.get("project_id") in (None, execution["project_id"])) and
                (event.get("run_id") in (None, "", execution["run_id"])),
                "CLI_EVENT_SCOPE_SEQUENCE_OR_SHAPE_CHANGED")
        seen.add(event["event_id"])
        cursor = event["sequence"]
    require(type(execution.get("event_sequence")) is int and
            execution["event_sequence"] == cursor and
            type(final_snapshot.get("event_sequence")) is int and
            final_snapshot["event_sequence"] >= cursor,
            "CLI_EVENT_CURSOR_FINAL_MISMATCH")
    return summary, {"original_jsonl_records": len(parsed),
                     "session_event_count": len(parsed) - 1,
                     "initial_cursor": cursor - (len(parsed) - 1),
                     "final_cursor": cursor}


'''
replacement = '''    row, stream_evidence = original_cli_summary_stream(label, parsed)
'''
new = old.replace(needle, replacement)
assert new.count("def verified_cli_context_transition(") == 1
new = new.replace("def verified_cli_context_transition(", helper + "def verified_cli_context_transition(", 1)
new = new.replace('return {"original_jsonl_command": name, "admission_method": methods[-1],',
                  'return {"original_jsonl_command": name, "stream_evidence": stream_evidence,\n            "admission_method": methods[-1],', 1)
ast.parse(new)
runner_ref = write("mu_sdk_trial.v6.proposed.py", new.encode("utf-8"))
cli_ref = write("cli_stream.context_receipt.v6.proposed.go",
                (OLD / "cli_stream.context_receipt.v5.proposed.go").read_bytes())
go_refs = []
for name in ("internal_host_vault.v5.proposed.go", "internal_host_host.v5.proposed.go",
             "apps_control_main.v5.proposed.go", "runtime_qualification.unlimited.v5.proposed.go"):
    original = OLD / name
    candidate = name.replace(".v5.proposed.go", ".v6.proposed.go")
    go_refs.append({"prior": ref(original), "candidate": write(candidate, original.read_bytes())})
template_ref = write("input.v6.template.json", (OLD / "input.v5.template.json").read_bytes())
assert all(item["prior"]["sha256"] == item["candidate"]["sha256"] for item in go_refs)
write("build-result.json", (json.dumps({"runner_ref": runner_ref, "cli_ref": cli_ref,
                                         "go_refs": go_refs, "template_ref": template_ref},
                                        ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"source_built": True, "runner_sha": runner_ref["sha256"],
                  "cli_byte_identical": cli_ref["sha256"] == ref(OLD / "cli_stream.context_receipt.v5.proposed.go")["sha256"],
                  "four_go_byte_identical": True}, ensure_ascii=False))
