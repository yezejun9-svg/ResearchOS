"""Static precise candidate correction; no candidate import or execution."""
import ast
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
runner = (here / "whole58_finite_runner.rev2.proposed.py").read_text(encoding="utf-8")
old = 'note_overflow(label, count + len(chunk))'
new = 'note_overflow(label, count - kept + len(chunk))'
if runner.count(old) != 1:
    raise SystemExit("overflow observed-byte anchor not unique")
runner = runner.replace(old, new)
ast.parse(runner)
interface = json.loads((here / "authority-interface.rev2.proposed.json").read_bytes())
template = interface["execution_argv_template"]
match = [i for i, value in enumerate(template) if value == "<whole58_finite_runner.v4.proposed.py>"]
if match != [5]:
    raise SystemExit("authority template runner slot drift")
template[5] = "<whole58_finite_runner.rev3.proposed.py>"
copy_list = interface["registered_source_manifest"]["must_contain_exact_pins_for"]
if copy_list[0] != "whole58_finite_runner.v4.proposed.py":
    raise SystemExit("source manifest runner slot drift")
copy_list[0] = "whole58_finite_runner.rev3.proposed.py"
interface["overflow_observed_bytes_lower_bound"] = (
    "The drainer counts all bytes returned by the cap-crossing read; it never invents unread pipe bytes.")
serialized = (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
json.loads(serialized)
with (here / "whole58_finite_runner.rev3.proposed.py").open("xb") as stream:
    stream.write(runner.encode("utf-8"))
with (here / "authority-interface.rev3.proposed.json").open("xb") as stream:
    stream.write(serialized)
print("REV3_FINAL_CANDIDATE_SOURCE_CREATED")
