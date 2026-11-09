"""Read-only diagnosis of the earlier static assertion; no output artifact writes."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("create_source_audit.py")
source = target.read_text(encoding="utf-8")
anchor = "assert all(checks.values())"
assert source.count(anchor) == 1
scope = {"__file__": str(target)}
exec(compile(source.split(anchor)[0], str(target), "exec"), scope)
print("FALSE_STATIC_CHECKS", [key for key, value in scope["checks"].items() if not value])
