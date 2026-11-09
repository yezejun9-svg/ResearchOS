"""One-shot parent-inclusive bootstrap revision of the static source builder."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
source = Path(__file__).with_name("build_whole_go_rev3.py").read_text(encoding="utf-8")
old = 'for item in (GATE, *list(GATE.parents)[:7]):'
assert source.count(old) == 1
source = source.replace(old, 'for item in (GATE, *list(GATE.parents)[:8]):')
code = compile(ast.parse(source), str(Path(__file__).with_name("build_whole_go_rev3.py")), "exec")
exec(code, {"__file__": str(Path(__file__).with_name("build_whole_go_rev3.py"))})
