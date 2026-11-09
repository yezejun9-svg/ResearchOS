"""Use the enumerated W13/W13-03 input path; pure JSON projection only."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("inspect_invocation_shape.py")
source = target.read_text(encoding="utf-8")
old = "receipts/W05/W05-99/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882"
new = "receipts/W13/W13-03/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882"
assert source.count(old) == 1
source = source.replace(old, new)
exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})
