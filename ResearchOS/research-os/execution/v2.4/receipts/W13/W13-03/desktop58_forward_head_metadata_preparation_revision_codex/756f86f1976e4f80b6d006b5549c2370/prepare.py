"""Pure IO/AST preparation. Does not import or execute either candidate."""
from pathlib import Path
import ast
import difflib
import hashlib
import json

OUT = Path(__file__).parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_metadata_preparation_codex/503ef47ea65144029c73a4d7bf19409a'
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf/scope_registration.json'

def pin(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def put(name, raw):
    with (OUT / name).open('xb') as f:
        f.write(raw)
    return pin(OUT / name)

def obj(name, value):
    return put(name, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode())

engine_path = OLD / 'forward_head_engine.selected.proposed.py'
builder_path = OLD / 'build_forward_draft.selected.proposed.py'
old = engine_path.read_bytes()
builder = builder_path.read_bytes()
assert hashlib.sha256(old).hexdigest() == 'b9318a1f361b9ed4aa42e1e21e41bb4eefd5909310a73f396820e1680286ef47'
assert hashlib.sha256(builder).hexdigest() == '69c9c94a9e1b46fc85312743cb1899c0948f0d3e1ade93c6eda97e054297ce75'
scope_raw = SCOPE.read_bytes()
assert hashlib.sha256(scope_raw).hexdigest() == '62d704e9add7294f11ecfd8dc2ba35238a37b285fa32febfe8977b266142daba'
scope = json.loads(scope_raw)
runtime_ref = scope['runtime_resources_ref']
assert runtime_ref['sha256'] == 'c75ee385bdca56de3582f78695af8fc1b31fb67da0ecffa22cd1e4b4aca4b9b5'
assert runtime_ref['bytes'] == 282833
assert pin(Path(runtime_ref['path'])) == runtime_ref
inputs = [engine_path, builder_path, OLD / 'handoff.json', OLD / 'manifest.json', SCOPE, Path(runtime_ref['path'])]
before = [pin(p) for p in inputs]
obj('inputs.before.json', {'files': before, 'point_in_time_only': True})

anchor = b"    need(same(scope['toolchain_lock_ref'], q['toolchain_lock_ref']) and same(scope['owned_process_helper_ref'], q['helper_ref']), 'same source toolchain/helper')\n"
added = b"    need(same(scope['runtime_resources_ref'], q['runtime_resources_ref']), 'same source runtime catalog')\n"
assert old.count(anchor) == 1 and added not in old
new = old.replace(anchor, anchor + added, 1)
assert new.replace(added, b'', 1) == old
tree_old, tree_new = ast.parse(old), ast.parse(new)
funcs_old = {n.name: n for n in tree_old.body if isinstance(n, ast.FunctionDef)}
funcs_new = {n.name: n for n in tree_new.body if isinstance(n, ast.FunctionDef)}
assert set(funcs_old) == set(funcs_new)
changed = [k for k in funcs_old if ast.dump(funcs_old[k], include_attributes=False) != ast.dump(funcs_new[k], include_attributes=False)]
assert changed == ['closure']
oldlines, newlines = old.splitlines(keepends=True), new.splitlines(keepends=True)
unchanged = []
for k in funcs_old:
    if k == 'closure':
        continue
    a, b = funcs_old[k], funcs_new[k]
    assert b''.join(oldlines[a.lineno-1:a.end_lineno]) == b''.join(newlines[b.lineno-1:b.end_lineno])
    unchanged.append(k)
eref = put('forward_head_engine.v2.proposed.py', new)

replacements = [
    (repr(str(engine_path)).encode(), repr(eref['path']).encode()),
    (hashlib.sha256(old).hexdigest().encode(), eref['sha256'].encode()),
    (b'len(raw) != 44596', ('len(raw) != ' + str(eref['bytes'])).encode()),
]
newbuilder = builder
for oldpart, newpart in replacements:
    assert newbuilder.count(oldpart) == 1
    newbuilder = newbuilder.replace(oldpart, newpart, 1)
reverse = newbuilder
for oldpart, newpart in reversed(replacements):
    assert reverse.count(newpart) == 1
    reverse = reverse.replace(newpart, oldpart, 1)
assert reverse == builder
ast.parse(newbuilder)
bref = put('build_forward_draft.v2.proposed.py', newbuilder)
put('engine.diff', ''.join(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True), fromfile=str(engine_path), tofile=eref['path'])).encode())
put('builder.diff', ''.join(difflib.unified_diff(builder.decode().splitlines(True), newbuilder.decode().splitlines(True), fromfile=str(builder_path), tofile=bref['path'])).encode())
obj('whole-inverse.json', {
    'engine_original_ref': before[0], 'engine_candidate_ref': eref,
    'engine_remove_exact_once_hex': added.hex(), 'engine_restored_exact': True,
    'builder_original_ref': before[1], 'builder_candidate_ref': bref,
    'builder_replacements': [{'old_hex': a.hex(), 'new_hex': b.hex()} for a, b in replacements],
    'builder_restored_exact': True,
})
obj('static-audit.json', {
    'status': 'SOURCE_PREPARATION_ONLY_NOT_RUNTIME',
    'request': 'Bind request runtime_resources_ref to actual source scope runtime_resources_ref',
    'fixed_source_scope_ref': before[4], 'fixed_runtime_ref': runtime_ref,
    'changed_engine_functions': changed, 'unchanged_engine_AST_and_byte_functions': unchanged,
    'same_ref_predicate_unchanged': True, 'same_ref_fields': ['canonical path', 'sha256', 'bytes'],
    'engine_exact_one_line_added': True, 'builder_only_engine_path_SHA_bytes_changed': True,
    'AST_parsed_candidates': 2, 'candidate_imported': False, 'candidate_executed': False,
    'future_controls_NOT_RUN': [
        'Actual r332 runtime REF and 1212 member catalog -> existing positive path remains reachable',
        'Different catalog with 1212 entries -> reject before draft allocation',
        'Same bytes at different catalog path -> reject',
        'Same path with different SHA or bytes -> reject',
    ],
    'Root_params_target_namespace_canonical_product_writes': 0,
    'Git_Go_Node_SQL_Job_HTTP_models': 0,
    'root_before_after_cut_not_rewritten': True,
})
after = [pin(p) for p in inputs]
assert before == after
obj('inputs.after.json', {'files': after, 'drift': []})
obj('code-refs.json', {'engine': eref, 'builder': bref})
print(json.dumps({'engine': eref, 'builder': bref, 'input_count': len(before), 'drift': 0, 'unchanged_functions': len(unchanged)}, ensure_ascii=False))
