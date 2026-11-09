"""Read-only diagnosis of final audit assertions; never writes audit outputs."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("create_source_audit_final.py")
wrapper = target.read_text(encoding="utf-8")
marker = 'exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})'
assert wrapper.count(marker) == 1
scope = {"__file__": str(target)}
exec(compile(wrapper.split(marker)[0], str(target), "exec"), scope)
source = scope["source"]
anchor = "assert all(checks.values())"
assert source.count(anchor) == 1
inner = {"__file__": str(Path(__file__).with_name("create_source_audit.py"))}
exec(compile(source.split(anchor)[0], inner["__file__"], "exec"), inner)
print("FALSE_FINAL_STATIC_CHECKS", [key for key, value in inner["checks"].items() if not value])
