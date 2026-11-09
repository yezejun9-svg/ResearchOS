"""Keep a failed drainer thread start/join inside the invocation receipt."""
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
runner = (here / "whole58_finite_runner.rev6.proposed.py").read_text(encoding="utf-8")
old = '''        for worker in workers:
            worker.join(timeout=max(0, min(budgets["drain_join_seconds"],
                        deadline-time.monotonic()-budgets["finalization_reserve_seconds"])))
        receipt["drain_incomplete"] = len(workers) != 2 or any(w.is_alive() for w in workers)
'''
new = '''        for worker in workers:
            try:
                if worker.ident is not None:
                    worker.join(timeout=max(0, min(budgets["drain_join_seconds"],
                                deadline-time.monotonic()-budgets["finalization_reserve_seconds"])))
                else:
                    fail("RAW_DRAIN_THREAD_NOT_STARTED")
            except BaseException as exc:
                fail("RAW_DRAIN_JOIN_FAILURE", repr(exc))
        receipt["drain_incomplete"] = (len(workers) != 2 or
                                      any(w.ident is None or w.is_alive() for w in workers))
'''
assert runner.count(old) == 1
runner = runner.replace(old, new)
ast.parse(runner)
interface = json.loads((here / "authority-interface.rev6.proposed.json").read_bytes())
names = interface["registered_source_manifest"]["must_contain_exact_pins_for"]
assert names[0] == "whole58_finite_runner.rev6.proposed.py"
names[0] = "whole58_finite_runner.rev7.proposed.py"
assert interface["execution_argv_template"][5] == "<whole58_finite_runner.rev6.proposed.py>"
interface["execution_argv_template"][5] = "<whole58_finite_runner.rev7.proposed.py>"
interface["final_candidate_source_files"][1] = "whole58_finite_runner.rev7.proposed.py"
interface["drain_join_failure_behavior"] = (
    "Thread start/join failure is recorded once; incomplete drains keep raw pins NULL. "
    "The bounded parent does not treat an unstarted worker as a successful drain.")
outputs = [
    ("whole58_finite_runner.rev7.proposed.py", runner.encode("utf-8")),
    ("authority-interface.rev7.proposed.json",
     (json.dumps(interface, ensure_ascii=False, indent=2) + "\n").encode("utf-8")),
]
for name, data in outputs:
    if name.endswith(".py"): ast.parse(data, filename=name)
    else: json.loads(data)
for name, data in outputs:
    with (here / name).open("xb") as stream:
        stream.write(data)
print("FINAL_BOUNDED_DRAIN_CANDIDATES_READY", len(outputs))
