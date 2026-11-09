"""Restore original W07 prefix bytes after a v3 text transform newline conversion."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

P = Path(__file__).resolve().parent
before = (P / "formal_case_index.before.py").read_bytes()
target = P / "formal_case_index.after.py"
current = target.read_bytes()
assert b"\r\n" not in current
candidate = current.replace(b"\n", b"\r\n")
assert candidate[:51719] == before[:51719]
assert hashlib.sha256(candidate[:51719]).hexdigest() == (
    "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1")
ast.parse(candidate, filename=str(target))
assert target.read_bytes() == current
target.write_bytes(candidate)
assert target.read_bytes() == candidate
print("W07_PREFIX_EXACT_RESTORED", len(candidate))
