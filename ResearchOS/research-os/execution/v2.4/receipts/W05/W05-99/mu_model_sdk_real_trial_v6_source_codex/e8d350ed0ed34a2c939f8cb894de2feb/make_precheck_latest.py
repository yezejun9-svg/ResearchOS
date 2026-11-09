import pathlib
import sys
sys.dont_write_bytecode = True
here=pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source=(here/"precheck_terminal.py").read_text(encoding="utf-8")
assert source.count("mu_sdk_trial.v6.terminal.proposed.py")==1
assert source.count("precheck.v6.terminal.json")==1
source=source.replace("mu_sdk_trial.v6.terminal.proposed.py","mu_sdk_trial.v6.latest_state.proposed.py")
source=source.replace("precheck.v6.terminal.json","precheck.v6.latest_state.json")
source=source.replace('negative = (', '''def mutate_late_state(s):
    s[-2]["event"]["sequence"] = 5
    s[-1]["execution"]["event_sequence"] = 5
    s[-1]["last_verified_session_snapshot"]["event_sequence"] = 5
    s.insert(-2, {"type": "session.event", "event": {
        "sequence": 4, "event_id": "event-late", "kind": "RUN_STATE",
        "payload": {"run_id": "run-A", "revision": 99, "status": "FAILED",
                    "children_stopped": True, "queue_empty": True,
                    "settled_at": "2030-01-01T00:00:00Z"},
        "session_id": "session-A", "protocol_version": "protocol-A",
        "core_build_id": "build-A", "run_id": "run-A"}})

negative = (''')
source=source.replace('    ("missing_artifact", lambda s: s.pop(-2)),',
'''    ("missing_artifact", lambda s: s.pop(-2)),
    ("late_foreign_run_state", mutate_late_state),''')
with (here/"precheck_latest.py").open("xb") as stream: stream.write(source.encode("utf-8"))
print("LATEST_PRECHECK_READY")
