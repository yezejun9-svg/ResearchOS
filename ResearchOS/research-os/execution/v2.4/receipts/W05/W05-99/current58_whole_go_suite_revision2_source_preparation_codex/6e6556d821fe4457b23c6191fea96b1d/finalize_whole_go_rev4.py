"""Freeze the returned invocation snapshot before any still-live drainer can mutate it."""
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
runner = (here / "whole58_finite_runner.rev5.proposed.py").read_text(encoding="utf-8")
old = '''        try: bounded_json(out_dir / "invocation.json", receipt,
                          deadline - budgets["finalization_reserve_seconds"])
        except BaseException as exc: fail("INVOCATION_RECEIPT_WRITE_FAILURE", repr(exc))
    return receipt
'''
new = '''        # A drainer that missed the bounded join cannot mutate the returned report.
        with cause_lock:
            frozen_receipt = json.loads(json.dumps(receipt))
        try: bounded_json(out_dir / "invocation.json", frozen_receipt,
                          deadline - budgets["finalization_reserve_seconds"])
        except BaseException as exc:
            fail("INVOCATION_RECEIPT_WRITE_FAILURE", repr(exc))
            with cause_lock:
                frozen_receipt = json.loads(json.dumps(receipt))
    return frozen_receipt
'''
assert runner.count(old) == 1
runner = runner.replace(old, new)
ast.parse(runner)
interface = json.loads((here / "authority-interface.rev5.proposed.json").read_bytes())
names = interface["registered_source_manifest"]["must_contain_exact_pins_for"]
assert names[0] == "whole58_finite_runner.rev5.proposed.py"
names[0] = "whole58_finite_runner.rev6.proposed.py"
assert interface["execution_argv_template"][5] == "<whole58_finite_runner.rev5.proposed.py>"
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev6.proposed.py>"
interface["final_candidate_source_files"][1] = "whole58_finite_runner.rev6.proposed.py"
interface["drain_incomplete_snapshot"] = (
    "A bounded join failure leaves raw pins NULL and fails. The invocation JSON and returned "
    "value are copied under the cause lock; a late daemon drainer cannot change sealed facts.")
outputs = [
    ("whole58_finite_runner.rev6.proposed.py", runner.encode("utf-8")),
    ("authority-interface.rev6.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, data in outputs:
    if name.endswith(".py"): ast.parse(data, filename=name)
    else: json.loads(data)
for name, data in outputs:
    with (here / name).open("xb") as stream:
        stream.write(data)
print("FINAL_SNAPSHOT_CANDIDATES_READY", len(outputs))
