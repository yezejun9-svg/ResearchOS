"""Finalize static candidate pointers into exclusive files; no candidate import."""
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
runner = (here / "whole58_finite_runner.rev4.proposed.py").read_text(encoding="utf-8")
old = 'EXECUTION = Path(__file__).with_name("whole58-execution.contract.proposed.json")'
assert runner.count(old) == 1
runner = runner.replace(old, 'EXECUTION = Path(__file__).with_name("whole58-execution.contract.rev3.proposed.json")')
ast.parse(runner)
interface = json.loads((here / "authority-interface.rev4.proposed.json").read_bytes())
manifest_names = interface["registered_source_manifest"]["must_contain_exact_pins_for"]
assert manifest_names == [
    "whole58_finite_runner.rev4.proposed.py",
    "whole58_gate.rev3.proposed.py",
    "whole58-execution.contract.proposed.json",
    "whole58-finite.contract.proposed.json",
]
manifest_names[0] = "whole58_finite_runner.rev5.proposed.py"
manifest_names[2] = "whole58-execution.contract.rev3.proposed.json"
assert interface["execution_argv_template"][5] == "<whole58_finite_runner.rev4.proposed.py>"
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev5.proposed.py>"
interface["final_candidate_source_files"] = [
    "whole58_gate.rev3.proposed.py",
    "whole58_finite_runner.rev5.proposed.py",
    "whole58-execution.contract.rev3.proposed.json",
    "authority-interface.rev5.proposed.json",
]
outputs = [
    ("whole58_finite_runner.rev5.proposed.py", runner.encode("utf-8")),
    ("authority-interface.rev5.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, data in outputs:
    if name.endswith(".py"): ast.parse(data, filename=name)
    else: json.loads(data)
for name, data in outputs:
    with (here / name).open("xb") as stream:
        stream.write(data)
print("FINAL_POINTER_CANDIDATES_READY", len(outputs))
