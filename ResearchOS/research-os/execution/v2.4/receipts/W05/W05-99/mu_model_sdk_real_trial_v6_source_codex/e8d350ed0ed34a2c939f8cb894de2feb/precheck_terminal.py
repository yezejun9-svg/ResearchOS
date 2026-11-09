"""Synthetic CLI JSONL stream controls; only selected pure functions execute."""
import ast
import copy
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source = (HERE / "mu_sdk_trial.v6.terminal.proposed.py").read_text(encoding="utf-8")
tree = ast.parse(source)
names = {"original_cli_summary_stream", "verified_cli_context_transition", "strict_consumed_json"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names


def require(ok, message):
    if not ok:
        raise ValueError(message)


scope = {"require": require, "json": json}
exec(compile(ast.Module(body=nodes, type_ignores=[]), "<selected-pure-io-only>", "exec"), scope)
verify = scope["verified_cli_context_transition"]
old = {"config_revision": 1, "model": "opencode-go/deepseek-v4.1-flash",
       "settled_run_id": "", "workspace_ref": "workspace-A", "project_id": "project-A",
       "session_id": "", "session_revision": 0, "writer_epoch": 0, "updated_by": ""}


def fixture(label, event_count):
    name = "goal" if label == "cli-goal" else "run"
    writer = {"client_id": "cli-owner-A", "epoch": 2, "expires_at": "2030-01-01T00:00:00Z"}
    common = {"project_id": "project-A", "session_id": "session-A",
              "protocol_version": "protocol-A", "core_build_id": "build-A", "writer": writer}
    admitted = dict(common, revision=2, event_sequence=0)
    final = dict(common, revision=3, event_sequence=event_count)
    saved = {"project_id": "project-A", "session_id": "session-A",
             "session_revision": 3, "writer_epoch": 2, "updated_by": "cli-owner-A"}
    execution = {"status": "EXECUTION_REPORTED", "exit_code": 0,
                 "reason": "HOST_EXECUTION_SETTLED", "independent_acceptance": "NOT_EVALUATED",
                 "project_id": "project-A", "session_id": "session-A",
                 "goal_id": "goal-A", "run_id": "run-A", "message_id": "message-A",
                 "event_sequence": event_count,
                 "host_execution": {"status": "SETTLED", "revision": 5,
                                    "children_stopped": True, "queue_empty": True,
                                    "runtime_settled_at": "2030-01-01T00:00:00Z",
                                    "execution_report": "actual host report",
                                    "result_artifact_ids": ["artifact-A"]}}
    if name == "goal":
        ops = [{"method": "goal.start", "status": "COMPLETED", "exit_code": 0,
                "result": {"snapshot": admitted, "goal_id": "goal-A"}}]
    else:
        created = dict(common, revision=1, event_sequence=0)
        ops = [{"method": "session.create", "status": "COMPLETED", "exit_code": 0,
                "result": {"snapshot": created}},
               {"method": "session.send", "status": "COMPLETED", "exit_code": 0,
                "result": {"snapshot": admitted, "message_id": "message-A", "run_id": "run-A"}}]
    summary = {"command": name, "status": "EXECUTION_REPORTED", "exit_code": 0,
               "client_id": "cli-owner-A", "session_id": "session-A",
               "admission_command_id": "command-A", "operations": ops,
               "execution": execution, "last_verified_session_snapshot": final,
               "saved_context": saved}
    events = []
    for number in range(1, event_count + 1):
        events.append({"type": "session.event", "event": {
            "sequence": number, "event_id": "event-" + str(number),
            "kind": ("RUN_STATE" if number == event_count - 1 else
                     "ARTIFACT" if number == event_count else
                     "MODEL" if number == 1 else "TOOL"),
            "payload": ({"run_id": "run-A", "revision": 5, "status": "SETTLED",
                         "children_stopped": True, "queue_empty": True,
                         "settled_at": "2030-01-01T00:00:00Z"}
                        if number == event_count - 1 else
                        {"availability": "AVAILABLE", "artifact_ref": {"id": "artifact-A"}}
                        if number == event_count else {"observed": True}),
            "session_id": "session-A",
            "protocol_version": "protocol-A", "core_build_id": "build-A",
            "run_id": "run-A"}})
    post = dict(old, **saved)
    return events + [summary], (json.dumps(post, separators=(",", ":")) + "\n").encode()


checks = []
for label, count in (("cli-run", 4), ("cli-goal", 2)):
    stream, raw = fixture(label, count)
    evidence = verify(label, old, stream, raw)
    assert evidence["stream_evidence"]["session_event_count"] == count
    checks.append(label + "_original_stream_positive")

stream, raw = fixture("cli-run", 4)
negative = (
    ("unknown_prefix", lambda s: s.insert(0, {"type": "unknown", "event": {}})),
    ("duplicate_final", lambda s: s.insert(-1, copy.deepcopy(s[-1]))),
    ("final_not_last", lambda s: s.append(s.pop(0))),
    ("foreign_session", lambda s: s[0]["event"].__setitem__("session_id", "foreign")),
    ("foreign_build", lambda s: s[0]["event"].__setitem__("core_build_id", "foreign")),
    ("foreign_protocol", lambda s: s[0]["event"].__setitem__("protocol_version", "foreign")),
    ("foreign_run", lambda s: s[0]["event"].__setitem__("run_id", "foreign")),
    ("sequence_gap", lambda s: s[1]["event"].__setitem__("sequence", 4)),
    ("duplicate_event_id", lambda s: s[1]["event"].__setitem__("event_id", "event-1")),
    ("bad_payload", lambda s: s[0]["event"].__setitem__("payload", None)),
    ("wrong_final_cursor", lambda s: s[-1]["execution"].__setitem__("event_sequence", 999)),
    ("wrong_snapshot_cursor", lambda s: s[-1]["last_verified_session_snapshot"].__setitem__("event_sequence", 0)),
    ("wrong_admission_message", lambda s: s[-1]["execution"].__setitem__("message_id", "foreign")),
    ("missing_admission_id", lambda s: s[-1].__setitem__("admission_command_id", "")),
    ("resync_snapshot", lambda s: s.insert(1, {"type": "session.snapshot", "snapshot": {}, "reason": "EVENT_RESYNC_REQUIRED"})),
    ("early_command_summary", lambda s: s.insert(0, {"command": "status", "exit_code": 0})),
    ("wrong_saved_revision", lambda s: s[-1]["saved_context"].__setitem__("session_revision", 99)),
    ("foreign_writer", lambda s: s[-1]["last_verified_session_snapshot"]["writer"].__setitem__("client_id", "foreign")),
    ("missing_run_state", lambda s: s.pop(-3)),
    ("missing_artifact", lambda s: s.pop(-2)),
    ("foreign_terminal_revision", lambda s: s[-3]["event"]["payload"].__setitem__("revision", 8)),
    ("foreign_artifact_id", lambda s: s[-2]["event"]["payload"]["artifact_ref"].__setitem__("id", "foreign")),
)
for name, change in negative:
    bad = copy.deepcopy(stream)
    change(bad)
    try:
        verify("cli-run", old, bad, raw)
    except (ValueError, KeyError, TypeError):
        checks.append(name + "_rejected")
    else:
        raise AssertionError(name + "_accepted")

# An event-free normal goal cannot pass cliExecution.terminal: it lacks
# both the RUN_STATE projection and the AVAILABLE result artifact event.
empty_goal, empty_raw = fixture("cli-goal", 0)
try:
    verify("cli-goal", old, empty_goal, empty_raw)
except (ValueError, KeyError, TypeError):
    checks.append("event_free_non_draft_goal_rejected")
else:
    raise AssertionError("event-free non-draft goal accepted")

cli = HERE / "cli_stream.context_receipt.v6.proposed.go"
assert cli.read_bytes() == pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v5_source_codex/39387323960a441ca81f04b9bcdecd17/cli_stream.context_receipt.v5.proposed.go").read_bytes()
checks.append("cli_receipt_producer_byte_identical")
payload = {"schema": "researchos.mu-sdk-v6-pure-io-precheck.v1", "all_passed": True,
           "checks": checks, "synthetic_real_shape_not_qualification": True,
           "actual_cli_executions": 0, "actual_model_requests": 0,
           "resync_snapshot_success_positive": False,
           "resync_reason": "Current CLI sets responseExit=exitNotImplemented after EVENT_RESYNC_REQUIRED"}
with (HERE / "precheck.v6.terminal.json").open("xb") as stream:
    stream.write((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({"all_passed": True, "checks": len(checks)}, ensure_ascii=False))
