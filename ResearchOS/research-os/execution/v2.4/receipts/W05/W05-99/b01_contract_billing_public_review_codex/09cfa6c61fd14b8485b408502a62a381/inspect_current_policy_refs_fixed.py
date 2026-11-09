"""One-shot root-depth corrected read-only pointer inspection."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("inspect_current_policy_refs.py")
source = target.read_text(encoding="utf-8")
old = "root = Path(__file__).resolve().parents[7]"
assert source.count(old) == 1
source = source.replace(old, "root = Path(__file__).resolve().parents[6]")
exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})
