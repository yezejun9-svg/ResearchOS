"""Build exclusive synthetic terminal-stream controls from the first v6 fixture."""
import ast
import pathlib
import sys
sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source = (HERE / "precheck_v6.py").read_text(encoding="utf-8")


def replace(old, new):
    assert source.count(old) == 1, source.count(old)
    return source.replace(old, new)


source = replace('mu_sdk_trial.v6.proposed.py', 'mu_sdk_trial.v6.terminal.proposed.py')
source = replace('precheck.v6.json', 'precheck.v6.terminal.json')
source = replace('''                 "event_sequence": event_count}
''', '''                 "event_sequence": event_count,
                 "host_execution": {"status": "SETTLED", "revision": 5,
                                    "children_stopped": True, "queue_empty": True,
                                    "runtime_settled_at": "2030-01-01T00:00:00Z",
                                    "execution_report": "actual host report",
                                    "result_artifact_ids": ["artifact-A"]}}
''')
source = replace('''            "kind": "MODEL" if number == 1 else "TOOL",
            "payload": {"observed": True}, "session_id": "session-A",
''', '''            "kind": ("RUN_STATE" if number == event_count - 1 else
                     "ARTIFACT" if number == event_count else
                     "MODEL" if number == 1 else "TOOL"),
            "payload": ({"run_id": "run-A", "revision": 5, "status": "SETTLED",
                         "children_stopped": True, "queue_empty": True,
                         "settled_at": "2030-01-01T00:00:00Z"}
                        if number == event_count - 1 else
                        {"availability": "AVAILABLE", "artifact_ref": {"id": "artifact-A"}}
                        if number == event_count else {"observed": True}),
            "session_id": "session-A",
''')
source = replace('''for label, count in (("cli-run", 3), ("cli-goal", 0)):
''', '''for label, count in (("cli-run", 4), ("cli-goal", 2)):
''')
source = replace('''stream, raw = fixture("cli-run", 3)
negative = (
''', '''stream, raw = fixture("cli-run", 4)
negative = (
''')
source = replace('''    ("foreign_writer", lambda s: s[-1]["last_verified_session_snapshot"]["writer"].__setitem__("client_id", "foreign")),
''', '''    ("foreign_writer", lambda s: s[-1]["last_verified_session_snapshot"]["writer"].__setitem__("client_id", "foreign")),
    ("missing_run_state", lambda s: s.pop(-3)),
    ("missing_artifact", lambda s: s.pop(-2)),
    ("foreign_terminal_revision", lambda s: s[-2]["event"]["payload"].__setitem__("revision", 8)),
    ("foreign_artifact_id", lambda s: s[-2]["event"]["payload"]["artifact_ref"].__setitem__("id", "foreign")),
''')
source = replace('''cli = HERE / "cli_stream.context_receipt.v6.proposed.go"
''', '''# An event-free normal goal cannot pass cliExecution.terminal: it lacks
# both the RUN_STATE projection and the AVAILABLE result artifact event.
empty_goal, empty_raw = fixture("cli-goal", 0)
try:
    verify("cli-goal", old, empty_goal, empty_raw)
except (ValueError, KeyError, TypeError):
    checks.append("event_free_non_draft_goal_rejected")
else:
    raise AssertionError("event-free non-draft goal accepted")

cli = HERE / "cli_stream.context_receipt.v6.proposed.go"
''')
ast.parse(source)
with (HERE / "precheck_terminal.py").open("xb") as stream:
    stream.write(source.encode("utf-8"))
print("TERMINAL_PRECHECK_SOURCE_READY")
