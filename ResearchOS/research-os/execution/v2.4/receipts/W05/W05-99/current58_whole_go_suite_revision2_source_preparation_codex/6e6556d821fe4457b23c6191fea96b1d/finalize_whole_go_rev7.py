"""Bind runner to the selected rev4 execution contract bytes and filename."""
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
runner = (here / "whole58_finite_runner.rev8.proposed.py").read_text(encoding="utf-8")
old = 'EXECUTION = Path(__file__).with_name("whole58-execution.contract.rev3.proposed.json")'
assert runner.count(old) == 1
runner = runner.replace(old, 'EXECUTION = Path(__file__).with_name("whole58-execution.contract.rev4.proposed.json")')
ast.parse(runner)
interface = json.loads((here / "authority-interface.rev8.proposed.json").read_bytes())
assert interface["registered_source_manifest"]["must_contain_exact_pins_for"][0] == "whole58_finite_runner.rev8.proposed.py"
interface["registered_source_manifest"]["must_contain_exact_pins_for"][0] = "whole58_finite_runner.rev9.proposed.py"
assert interface["execution_argv_template"][5] == "<whole58_finite_runner.rev8.proposed.py>"
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev9.proposed.py>"
interface["final_candidate_source_files"][1] = "whole58_finite_runner.rev9.proposed.py"
outputs = [
    ("whole58_finite_runner.rev9.proposed.py", runner.encode("utf-8")),
    ("authority-interface.rev9.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, raw in outputs:
    if name.endswith(".py"): ast.parse(raw, filename=name)
    else: json.loads(raw)
for name, raw in outputs:
    with (here / name).open("xb") as stream: stream.write(raw)
print("SELECTED_CONTRACT_POINTER_READY", len(outputs))
