"""AST-corrected audit: comments can mention SourceFileLoader without importing it."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("create_source_audit.py")
source = target.read_text(encoding="utf-8")
old = '"runner_does_not_use_sourcefileloader": "SourceFileLoader" not in runner,'
new = '''"runner_does_not_use_sourcefileloader": not any(
        isinstance(node, ast.Name) and node.id == "SourceFileLoader"
        for node in ast.walk(ast.parse(runner))),'''
assert source.count(old) == 1
source = source.replace(old, new)
exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})
