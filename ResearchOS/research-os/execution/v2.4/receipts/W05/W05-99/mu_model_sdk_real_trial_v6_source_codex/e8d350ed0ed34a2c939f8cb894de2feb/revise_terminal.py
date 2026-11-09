"""Restrict success to the exact RUN_STATE/ARTIFACT terminal projection."""
import ast
import hashlib
import json
import pathlib
import sys
sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source = (HERE / "mu_sdk_trial.v6.final.proposed.py").read_text(encoding="utf-8")
before = '''    build = final_snapshot.get("core_build_id")
    protocol = final_snapshot.get("protocol_version")
    require(isinstance(build, str) and build and isinstance(protocol, str) and protocol,
            "CLI_FINAL_SNAPSHOT_BUILD_OR_PROTOCOL_ABSENT")
    seen = set()
'''
after = '''    build = final_snapshot.get("core_build_id")
    protocol = final_snapshot.get("protocol_version")
    require(isinstance(build, str) and build and isinstance(protocol, str) and protocol,
            "CLI_FINAL_SNAPSHOT_BUILD_OR_PROTOCOL_ABSENT")
    admitted = last_result.get("snapshot", last_result)
    require(isinstance(admitted, dict) and
            admitted.get("project_id") == execution["project_id"] and
            admitted.get("session_id") == execution["session_id"] and
            admitted.get("protocol_version") == protocol and
            admitted.get("core_build_id") == build and
            type(admitted.get("event_sequence")) is int and
            0 <= admitted["event_sequence"] <= final_snapshot.get("event_sequence", -1),
            "CLI_ADMISSION_SNAPSHOT_STREAM_SCOPE_CHANGED")
    if first_method in ("session.create", "session.get"):
        require(first_snapshot.get("project_id") == execution["project_id"] and
                first_snapshot.get("session_id") == execution["session_id"] and
                first_snapshot.get("protocol_version") == protocol and
                first_snapshot.get("core_build_id") == build,
                "CLI_INITIAL_SNAPSHOT_STREAM_SCOPE_CHANGED")
    seen = set()
'''
assert source.count(before) == 1
source = source.replace(before, after)
before = '''    require(type(execution.get("event_sequence")) is int and
            execution["event_sequence"] == cursor and
            type(final_snapshot.get("event_sequence")) is int and
            final_snapshot["event_sequence"] == cursor,
            "CLI_EVENT_CURSOR_FINAL_MISMATCH")
    return summary, {"original_jsonl_records": len(parsed),
'''
after = '''    require(type(execution.get("event_sequence")) is int and
            execution["event_sequence"] == cursor and
            type(final_snapshot.get("event_sequence")) is int and
            final_snapshot["event_sequence"] == cursor,
            "CLI_EVENT_CURSOR_FINAL_MISMATCH")
    report = execution.get("host_execution")
    require(isinstance(report, dict) and report.get("status") == "SETTLED" and
            type(report.get("revision")) is int and
            report.get("children_stopped") is True and report.get("queue_empty") is True and
            isinstance(report.get("runtime_settled_at"), str) and
            report["runtime_settled_at"] and
            isinstance(report.get("execution_report"), str) and
            report["execution_report"].strip() and
            isinstance(report.get("result_artifact_ids"), list) and
            len(report["result_artifact_ids"]) >= 1 and
            all(isinstance(value, str) and value for value in report["result_artifact_ids"]),
            "CLI_TERMINAL_HOST_REPORT_INVALID")
    events = [item["event"] for item in parsed[:-1]]
    states = [event["payload"] for event in events
              if event.get("kind") == "RUN_STATE" and
              event.get("run_id") == execution["run_id"] and
              event["payload"].get("run_id") == execution["run_id"]]
    require(any(state.get("revision") == report["revision"] and
                state.get("status") == report["status"] and
                state.get("children_stopped") is True and
                state.get("queue_empty") is True and
                state.get("settled_at") == report["runtime_settled_at"]
                for state in states), "CLI_TERMINAL_RUN_STATE_EVENT_ABSENT")
    artifacts = {event["payload"].get("artifact_ref", {}).get("id")
                 for event in events if event.get("kind") == "ARTIFACT" and
                 event.get("run_id") == execution["run_id"] and
                 event["payload"].get("availability") == "AVAILABLE" and
                 isinstance(event["payload"].get("artifact_ref"), dict)}
    require(set(report["result_artifact_ids"]).issubset(artifacts),
            "CLI_TERMINAL_RESULT_ARTIFACT_EVENT_ABSENT")
    return summary, {"original_jsonl_records": len(parsed),
'''
assert source.count(before) == 1
source = source.replace(before, after)
ast.parse(source)
target = HERE / "mu_sdk_trial.v6.terminal.proposed.py"
with target.open("xb") as stream:
    stream.write(source.encode("utf-8"))
raw = target.read_bytes()
assert raw == source.encode("utf-8")
print(json.dumps({"terminal_candidate_sha": hashlib.sha256(raw).hexdigest(),
                  "bytes": len(raw)}, ensure_ascii=False))
