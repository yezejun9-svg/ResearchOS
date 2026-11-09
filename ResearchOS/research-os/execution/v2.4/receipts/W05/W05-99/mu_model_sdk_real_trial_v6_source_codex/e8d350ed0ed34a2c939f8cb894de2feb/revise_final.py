"""Exclusive final stream proposal, retaining the initial v6 draft as evidence."""
import ast
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source = (HERE / "mu_sdk_trial.v6.proposed.py").read_text(encoding="utf-8")
before = '''        kind = item.get("type")
        require(set(item) == {"type", "event"} and kind == "session.event",
                "CLI_UNKNOWN_OR_RESYNC_STREAM_RECORD")
        event = item.get("event")
'''
after = '''        kind = item.get("type")
        if kind == "session.snapshot":
            snapshot = item.get("snapshot")
            require(set(item) == {"type", "snapshot", "reason"} and
                    item.get("reason") == "EVENT_RESYNC_REQUIRED" and
                    isinstance(snapshot, dict) and
                    snapshot.get("session_id") == summary.get("session_id") and
                    snapshot.get("project_id") == execution.get("project_id") and
                    snapshot.get("protocol_version") == protocol,
                    "CLI_RESYNC_SNAPSHOT_SHAPE_OR_SCOPE_CHANGED")
            # The actual producer sets responseExit=exitNotImplemented here.
            raise ValueError("CLI_RESYNC_SNAPSHOT_CANNOT_QUALIFY_SUCCESS")
        require(set(item) == {"type", "event"} and kind == "session.event",
                "CLI_UNKNOWN_STREAM_RECORD")
        event = item.get("event")
'''
assert source.count(before) == 1
source = source.replace(before, after)
before = 'final_snapshot["event_sequence"] >= cursor,'
assert source.count(before) == 1
source = source.replace(before, 'final_snapshot["event_sequence"] == cursor,')
ast.parse(source)
target = HERE / "mu_sdk_trial.v6.final.proposed.py"
with target.open("xb") as stream:
    stream.write(source.encode("utf-8"))
raw = target.read_bytes()
assert raw == source.encode("utf-8")
print(json.dumps({"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}, ensure_ascii=False))
