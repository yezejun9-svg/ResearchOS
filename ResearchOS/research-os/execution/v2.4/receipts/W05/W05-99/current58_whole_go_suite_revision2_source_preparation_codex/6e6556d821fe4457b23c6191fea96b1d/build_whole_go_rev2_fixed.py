"""Static builder AST fix for exactly two identical receipt guard sites."""
import ast
from pathlib import Path
import sys
sys.dont_write_bytecode = True
here = Path(__file__).resolve().parent
source = (here / "build_whole_go_rev2.py").read_bytes()
tree = ast.parse(source)
guard = '    if receipt["first_cause"] or receipt["actual_exit"] != 0 or not receipt["stdout"]:\n'
seen = 0
kept = []
for node in tree.body:
    if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "replace_once"
            and len(node.value.args) >= 2
            and isinstance(node.value.args[1], ast.Constant)
            and node.value.args[1].value == guard):
        seen += 1
        if seen == 1:
            node.value.func.id = "replace_exactly_two"
            kept.append(node)
        continue
    kept.append(node)
if seen != 2:
    raise SystemExit("expected exactly two original guard replacement nodes")
tree.body = kept
def replace_exactly_two(text, before, after):
    if text.count(before) != 2:
        raise ValueError("expected exactly two guard sites")
    return text.replace(before, after)
exec(compile(ast.fix_missing_locations(tree), str(here / "build_whole_go_rev2.py"), "exec"), globals())
