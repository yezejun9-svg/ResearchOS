"""Adapt strict three-key capture pins to the existing two-key Reader API."""
from __future__ import annotations

import ast
from pathlib import Path

path = Path(__file__).resolve().parent / "formal_profile_w09.after.py"
old = path.read_text(encoding="utf-8")
candidate = old


def replace_once(left, before, after):
    assert left.count(before) == 1, (before, left.count(before))
    return left.replace(before, after, 1)


candidate = replace_once(candidate,
    '    path = reader.ref(authority, ROOT_CAPTURE_PREFIX)\n',
    '    path = reader.ref({"path": authority["path"], "sha256": authority["sha256"]},\n'
    '                      ROOT_CAPTURE_PREFIX)\n')
candidate = replace_once(candidate,
    '    capture = _doc(api, reader, entry["capture_ref"], ROOT_CAPTURE_PREFIX)\n'
    '    origin_path = _ref(api, reader, entry["origin_ref"], ROOT_ORIGIN_PREFIX)\n',
    '    capture_ref, origin_ref = entry["capture_ref"], entry["origin_ref"]\n'
    '    api.require(type(capture_ref) is dict and set(capture_ref) == {"path", "sha256", "bytes"}\n'
    '                and type(origin_ref) is dict and set(origin_ref) == {"path", "sha256", "bytes"},\n'
    '                "ROOT_CAPTURE_REGISTRY", "strict capture references")\n'
    '    capture_path = reader.ref({"path": capture_ref["path"], "sha256": capture_ref["sha256"]},\n'
    '                              ROOT_CAPTURE_PREFIX)\n'
    '    api.require(type(capture_ref["bytes"]) is int\n'
    '                and capture_path.stat().st_size == capture_ref["bytes"],\n'
    '                "ROOT_CAPTURE_REGISTRY", "capture bytes")\n'
    '    capture = reader.read(capture_path)\n'
    '    origin_path = reader.ref({"path": origin_ref["path"], "sha256": origin_ref["sha256"]},\n'
    '                             ROOT_ORIGIN_PREFIX)\n')
ast.parse(candidate, filename=str(path))
assert path.read_text(encoding="utf-8") == old
path.write_text(candidate, encoding="utf-8", newline="")
assert path.read_text(encoding="utf-8") == candidate
print("V3_STRICT_REF_READER_ADAPTER_AST_PASS")
