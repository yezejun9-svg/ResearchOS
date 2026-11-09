"""One-shot two-reader AST-safe correction for the rev6 static builder."""
import ast
from pathlib import Path
import sys

sys.dont_write_bytecode = True
target = Path(__file__).with_name("finalize_whole_go_rev6.py")
source = target.read_text(encoding="utf-8")
old = '''def once(source, old, new):
    assert source.count(old) == 1, old[:70]
    return source.replace(old, new)
'''
new = '''def once(source, old, new):
    count = source.count(old)
    if 'or receipt.get("stdout") is None or receipt.get("stderr") is None' in old:
        if count == 0:
            return source
        assert count == 2, old[:70]
        return source.replace(old, new)
    assert count == 1, old[:70]
    return source.replace(old, new)
'''
assert source.count(old) == 1
source = source.replace(old, new)
exec(compile(ast.parse(source), str(target), "exec"), {"__file__": str(target)})
