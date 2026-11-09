"""One-shot runner source transform after preserving first transform failure."""
import ast
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
tree = ast.parse((here / "build_final_revision_source.py").read_bytes())
call = next(node.value for node in tree.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "revised"
            and ast.literal_eval(node.value.args[0]) == "whole58_finite_runner.v2.proposed.py")
old_name = ast.literal_eval(call.args[0])
new_name = ast.literal_eval(call.args[1])
changes = ast.literal_eval(call.args[2])[:-1]
source = (here / old_name).read_text(encoding="utf-8")
for old, new in changes:
    if source.count(old) != 1:
        raise SystemExit("non-unique runner anchor")
    source = source.replace(old, new)
with (here / new_name).open("xb") as stream:
    stream.write(source.encode("utf-8"))
print("exclusive runner v3 source created")
