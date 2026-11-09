"""Mirror cliExecution.runStates' last matching RUN_STATE assignment."""
import ast
import hashlib
import json
import pathlib
import sys
sys.dont_write_bytecode = True
HERE = pathlib.Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb")
source = (HERE / "mu_sdk_trial.v6.terminal.proposed.py").read_text(encoding="utf-8")
before = '''    require(any(state.get("revision") == report["revision"] and
                state.get("status") == report["status"] and
                state.get("children_stopped") is True and
                state.get("queue_empty") is True and
                state.get("settled_at") == report["runtime_settled_at"]
                for state in states), "CLI_TERMINAL_RUN_STATE_EVENT_ABSENT")
'''
after = '''    require(bool(states) and states[-1].get("revision") == report["revision"] and
            states[-1].get("status") == report["status"] and
            states[-1].get("children_stopped") is True and
            states[-1].get("queue_empty") is True and
            states[-1].get("settled_at") == report["runtime_settled_at"],
            "CLI_TERMINAL_LATEST_RUN_STATE_MISMATCH")
'''
assert source.count(before) == 1
source = source.replace(before, after)
ast.parse(source)
target = HERE / "mu_sdk_trial.v6.latest_state.proposed.py"
with target.open("xb") as stream:
    stream.write(source.encode("utf-8"))
raw = target.read_bytes()
print(json.dumps({"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}))
