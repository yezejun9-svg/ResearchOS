"""Final static inverse and 3R checks, without importing any candidate."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("create_source_audit.py")
source = target.read_text(encoding="utf-8")
for old, new in (
    ("whole58_gate.rev3.proposed.py", "whole58_gate.rev4.proposed.py"),
    ("whole58_finite_runner.rev7.proposed.py", "whole58_finite_runner.rev8.proposed.py"),
    ("whole58-execution.contract.rev3.proposed.json", "whole58-execution.contract.rev4.proposed.json"),
    ("authority-interface.rev7.proposed.json", "authority-interface.rev8.proposed.json"),
    ("source-inverse.patch", "source-inverse.final.patch"),
    ("static-audit.json", "static-audit.final.json"),
):
    assert old in source
    source = source.replace(old, new)
old = '"runner_does_not_use_sourcefileloader": "SourceFileLoader" not in runner,'
new = '''"runner_does_not_use_sourcefileloader": not any(
        isinstance(node, ast.Name) and node.id == "SourceFileLoader"
        for node in ast.walk(ast.parse(runner))),'''
assert source.count(old) == 1
source = source.replace(old, new)
anchor = 'report["checks"] = [{"id": k, "pass": v} for k, v in checks.items()]'
new = '''checks.update({
    "runner_rechecks_deadline_immediately_before_popen":
        runner.index('wall = guarded_wall(budgets, deadline)\\n        receipt["timeout_seconds"]') < runner.index('proc = subprocess.Popen'),
    "runner_tracks_each_stream_eof": 'saw_eof[label] = True' in runner,
    "runner_partial_raw_separate": 'receipt[label + "_partial_raw"] = raw_pin' in runner,
    "runner_complete_raw_requires_eof": 'receipt[label + "_raw_complete"] = bool(saw_eof[label]' in runner,
    "gate_model_zero_exact_int": 'type(budgets.get("max_model_requests")) is int' in gate,
})
''' + anchor
assert source.count(anchor) == 1
source = source.replace(anchor, new)
exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})
