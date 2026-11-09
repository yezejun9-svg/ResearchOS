"""Close reviewer R1 launch and per-stream completeness predicates."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent

def once(source, old, new):
    assert source.count(old) == 1, old[:70]
    return source.replace(old, new)

gate = (here / "whole58_gate.rev3.proposed.py").read_text(encoding="utf-8")
gate = once(gate,
'''            and budgets.get("max_model_requests") == 0 and budgets["max_child_processes"] >= 1
''',
'''            and type(budgets.get("max_model_requests")) is int
            and budgets["max_model_requests"] == 0 and budgets["max_child_processes"] >= 1
''')
ast.parse(gate)
gate_data = gate.encode("utf-8")
gate_sha = hashlib.sha256(gate_data).hexdigest()

runner = (here / "whole58_finite_runner.rev7.proposed.py").read_text(encoding="utf-8")
runner = once(runner,
    'GATE = Path(__file__).with_name("whole58_gate.rev3.proposed.py")',
    'GATE = Path(__file__).with_name("whole58_gate.rev4.proposed.py")')
sha_line = next(line for line in runner.splitlines() if line.startswith("GATE_SHA256 = "))
bytes_line = next(line for line in runner.splitlines() if line.startswith("GATE_BYTES = "))
runner = once(runner, sha_line, f'GATE_SHA256 = "{gate_sha}"')
runner = once(runner, bytes_line, f'GATE_BYTES = {len(gate_data)}')
runner = once(runner,
'''               "stderr": None, "stdout_overflow": False, "stderr_overflow": False,
''',
'''               "stderr": None, "stdout_overflow": False, "stderr_overflow": False,
               "stdout_raw_complete": False, "stderr_raw_complete": False,
               "stdout_partial_raw": None, "stderr_partial_raw": None,
''')
runner = once(runner,
'''    drain_done = {"stdout": False, "stderr": False}
''',
'''    drain_done = {"stdout": False, "stderr": False}
    saw_eof = {"stdout": False, "stderr": False}
''')
runner = once(runner,
'''                    if not chunk:
                        break
''',
'''                    if not chunk:
                        saw_eof[label] = True
                        break
''')
runner = once(runner,
'''    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, shell=False,
''',
'''    try:
        # mkdir and receipt setup may consume the reserved launch window.
        wall = guarded_wall(budgets, deadline)
        receipt["timeout_seconds"] = wall
        proc = subprocess.Popen(argv, cwd=cwd, env=env, shell=False,
''')
runner = once(runner,
'''        for label in ("stdout", "stderr"):
            if drain_done[label] and not receipt["drain_incomplete"] and raw_paths[label].is_file():
                try: receipt[label] = pin(raw_paths[label])
                except BaseException as exc: fail("RAW_PIN_FAILURE", label + ":" + repr(exc))
''',
'''        for label in ("stdout", "stderr"):
            if drain_done[label] and not receipt["drain_incomplete"] and raw_paths[label].is_file():
                try:
                    raw_pin = pin(raw_paths[label])
                    receipt[label + "_raw_complete"] = bool(saw_eof[label] and
                                                            not receipt[label + "_overflow"])
                    if receipt[label + "_raw_complete"]:
                        receipt[label] = raw_pin
                    else:
                        receipt[label + "_partial_raw"] = raw_pin
                except BaseException as exc: fail("RAW_PIN_FAILURE", label + ":" + repr(exc))
''')
runner = once(runner,
'''            or receipt.get("stderr") is None or receipt.get("actual_exit") != 0):
''',
'''            or receipt.get("stderr") is None
            or not receipt.get("stdout_raw_complete")
            or not receipt.get("stderr_raw_complete")
            or receipt.get("actual_exit") != 0):
''')
runner = once(runner,
'''            or receipt.get("stdout") is None or receipt.get("stderr") is None):
''',
'''            or receipt.get("stdout") is None or receipt.get("stderr") is None
            or not receipt.get("stdout_raw_complete")
            or not receipt.get("stderr_raw_complete")):
''')
runner = once(runner,
'''            or receipt.get("stdout") is None or receipt.get("stderr") is None):
''',
'''            or receipt.get("stdout") is None or receipt.get("stderr") is None
            or not receipt.get("stdout_raw_complete")
            or not receipt.get("stderr_raw_complete")):
''')
ast.parse(runner)
contract = json.loads((here / "whole58-execution.contract.rev3.proposed.json").read_bytes())
contract["required_actual_root_gate"].append(
    "re-evaluate remaining wall after filesystem setup and immediately before Popen; both streams must reach EOF with complete pinned raw")
interface = json.loads((here / "authority-interface.rev7.proposed.json").read_bytes())
interface["registered_source_manifest"]["must_contain_exact_pins_for"][:3] = [
    "whole58_finite_runner.rev8.proposed.py", "whole58_gate.rev4.proposed.py",
    "whole58-execution.contract.rev4.proposed.json"]
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev8.proposed.py>"
interface["final_candidate_source_files"] = [
    "whole58_gate.rev4.proposed.py", "whole58_finite_runner.rev8.proposed.py",
    "whole58-execution.contract.rev4.proposed.json", "authority-interface.rev8.proposed.json"]
interface["raw_stream_completion_contract"] = (
    "EOF plus sealed exact raw pin per stdout/stderr. Cap crossing saves at most a partial raw pin "
    "and never exposes it as a complete raw stream; roster and lane fail closed.")
outputs = [
    ("whole58_gate.rev4.proposed.py", gate_data),
    ("whole58_finite_runner.rev8.proposed.py", runner.encode("utf-8")),
    ("whole58-execution.contract.rev4.proposed.json",
     (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
    ("authority-interface.rev8.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, data in outputs:
    if name.endswith(".py"): ast.parse(data, filename=name)
    else: json.loads(data)
for name, data in outputs:
    with (here / name).open("xb") as stream: stream.write(data)
print("R1_R3_STATIC_SOURCE_READY", gate_sha, len(gate_data), len(outputs))
