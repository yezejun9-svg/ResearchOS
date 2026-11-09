"""Receipt-only exact textual revision and AST/inverse audit. No template exec."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'f2adb6bf003a47498516d95970690096'
ROOT = Path('D:/作品集/ResearchOS/research-os')
REVIEW = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop15_root_binding_static_independent_review_codex/743aa36608ea40829475e0128ea8992e/review.json'


def ref(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}


def encode(d):
    return (json.dumps(d, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def save(name, d, raw=False):
    with (HERE / name).open('xb') as f:
        f.write(d if raw else encode(d))
    return ref(HERE / name)


assert ref(REVIEW)['sha256'] == '146b4992373d6c528cf59ae57f36c44c5289d9c5aba5e2bbf4cf9bf112bc7e32'
assert ref(OLD / 'manifest.json')['sha256'] == '12fd849c6b942a8f50af4b4a8227884ebe9f89f767361fc64e533e090755a96a'
old_mf = json.loads((OLD / 'manifest.json').read_text(encoding='utf-8'))
inputs = [ref(REVIEW), ref(OLD / 'manifest.json')]
for r in old_mf['entries']:
    assert ref(Path(r['path'])) == r
    inputs.append(r)
save('inputs.before.json', inputs)
edits = {
    'build-metadata-templates.py': [(
        "def verify(r):\n    a = ref(r['path'])\n    need(a['sha256'] == r['sha256'] and a['bytes'] == r['bytes'], 'ref bytes changed')\n    return path(r['path']).read_bytes()\n",
        "def verify(r):\n    b = path(r['path']).read_bytes()\n    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'ref bytes changed')\n    return b\n")],
    'metadata-engine.template.py': [(
        "def verify(r):\n    actual = ref(r['path'])\n    need(actual['sha256'] == r['sha256'] and actual['bytes'] == r['bytes'], 'reference drift')\n    return raw(r['path'])\n",
        "def verify(r):\n    b = raw(r['path'])\n    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'reference drift')\n    return b\n"), (
        "        source_guard(p, lock, helper, 'register-pre-' + str(i))\n        os.replace(q.with_name(q.name + '.desktop-registration.tmp'), q)\n",
        "        source_guard(p, lock, helper, 'register-pre-' + str(i))\n        need(all(raw(x) == b for x, b in zip(CANON, live)), 'four canonical completed prefix drift after source guard')\n        os.replace(q.with_name(q.name + '.desktop-registration.tmp'), q)\n"), (
        "    source_guard(p, lock, helper, 'register-after')\n    save('canonical-write.verified.json',",
        "    source_guard(p, lock, helper, 'register-after')\n    need(all(raw(q) == b for q, b in zip(CANON, target)), 'four canonical target drift after final source guard')\n    save('canonical-write.verified.json',")],
    'build-scope.py': [],
}
audit = []
for name, replacements in edits.items():
    original = (OLD / name).read_bytes()
    assert b'\r' not in original
    text = original.decode('utf-8')
    for before, after in replacements:
        assert text.count(before) == 1, name
        text = text.replace(before, after, 1)
    derived = text.encode('utf-8')
    save(name, derived, True)
    undo = text
    for before, after in reversed(replacements):
        assert undo.count(after) == 1
        undo = undo.replace(after, before, 1)
    assert undo.encode('utf-8') == original
    syntax = ast.parse(text, filename=name)
    old_syntax = ast.parse(original, filename='old/' + name)
    new_functions = {n.name: ast.dump(n, include_attributes=False) for n in syntax.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    old_functions = {n.name: ast.dump(n, include_attributes=False) for n in old_syntax.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    changed = [k for k in old_functions if old_functions[k] != new_functions.get(k)]
    expected = {'build-scope.py': [], 'build-metadata-templates.py': ['verify'], 'metadata-engine.template.py': ['verify', 'register']}[name]
    assert changed == expected
    if expected:
        v = next(n for n in syntax.body if isinstance(n, ast.FunctionDef) and n.name == 'verify')
        assert len(v.body) == 3 and isinstance(v.body[0], ast.Assign) and v.body[0].targets[0].id == 'b'
        assert isinstance(v.body[-1], ast.Return) and isinstance(v.body[-1].value, ast.Name) and v.body[-1].value.id == 'b'
        assert old_functions['doc'] == new_functions['doc']
    audit.append({'name': name, 'old_ref': ref(OLD / name), 'new_ref': ref(HERE / name), 'exact_edit_count': len(replacements),
        'AST_changed_functions': changed, 'inverse_restores_original_bytes': True, 'AST_parse': 'PASS', 'template_execution': False})
    diff = ''.join(difflib.unified_diff(original.decode().splitlines(True), text.splitlines(True), fromfile='old/' + name, tofile='new/' + name))
    save(name + '.diff.txt', diff.encode('utf-8'), True)

engine = (HERE / 'metadata-engine.template.py').read_text(encoding='utf-8')
tree = ast.parse(engine)
reg = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'register')
replacement_loop = next(x for x in reg.body if isinstance(x, ast.For) and 'enumerate' in ast.unparse(x.iter))
body = replacement_loop.body
replace_i = next(i for i, x in enumerate(body) if isinstance(x, ast.Expr) and ast.unparse(x.value).startswith('os.replace('))
assert ast.unparse(body[replace_i - 2]).startswith('source_guard(')
assert ast.unparse(body[replace_i - 1]).startswith('need(all(') and 'zip(CANON, live)' in ast.unparse(body[replace_i - 1])
assert ast.unparse(reg.body[-3]).startswith('source_guard(')
assert ast.unparse(reg.body[-2]).startswith('need(all(') and 'zip(CANON, target)' in ast.unparse(reg.body[-2])
assert "save('canonical-write.verified.json'" in ast.unparse(reg.body[-1])
variants = []
marker = '\nMODE = ' + repr('register') + '\n'
assert engine.count(marker) == 1
for mode in ['register', 'run', 'seal', 'grant']:
    value = engine.replace(marker, '\nMODE = ' + repr(mode) + '\n', 1)
    ast.parse(value)
    variants.append({'mode': mode, 'sha256': hashlib.sha256(value.encode()).hexdigest(), 'bytes': len(value.encode()), 'AST_parse': 'PASS', 'executed': False})
save('static-revision-audit.json', {'actor': 'codex:/root/sources_parent_impl', 'kind': 'AUTHOR_STATIC_REVISION_NOT_ACCEPTANCE',
    'review_ref': ref(REVIEW), 'changes': audit, 'mode_variants': variants,
    'DESKTOP_BIND_01': 'All4 live expected-prefix check is the immediate preceding statement of each replacement; final all4 target check immediately precedes verified. Original long source guards retained.',
    'DESKTOP_BIND_02': 'Each verify reads one bytes buffer, hashes and length-checks it, then returns that buffer. doc/helper compile call sites unchanged and consume verify result.',
    'residual_race': 'Filesystem replacement is not a multi-file transaction. Root sole-writer lease remains necessary; no stronger CAS primitive claimed.',
    'unmodified': ['CAS paths only CP/OW; ST/CM original', 'all other AST functions', 'strict raw JSON/paths/allowlist/caps', 'scope/review/grant sequencing', 'counter prefix and explicit future tuple', 'old failed/accepted receipts'],
    'template_helper_DLL_Git_Go_Node_SQL_HTTP_MODEL_execution': 0, 'canonical_source_index_writes': 0})

request = (OLD / 'root-request.example.json').read_bytes()
save('root-request.example.json', request, True)
metadata = json.loads((OLD / 'metadata-input.example.json').read_text(encoding='utf-8'))
metadata['metadata_engine_ref'] = ref(HERE / 'metadata-engine.template.py')
save('metadata-input.example.json', metadata)
plan = json.loads((OLD / 'grant-launcher-derivation-plan.json').read_text(encoding='utf-8'))
for stage in plan['ordered_stages']:
    for i, arg in enumerate(stage.get('argv', [])):
        if arg in [str(OLD / 'build-scope.py'), str(OLD / 'build-metadata-templates.py')]:
            stage['argv'][i] = str(HERE / Path(arg).name)
save('grant-launcher-derivation-plan.json', plan)
save('revision-spec.json', {'schema': 'researchos.desktop15-binding-targeted-revision.v1', 'actor': 'codex:/root/sources_parent_impl',
    'status': 'PREPARATION_ONLY_NOT_EXECUTED', 'authorized': False, 'future_root_grant': None,
    'previous_manifest_ref': ref(OLD / 'manifest.json'), 'previous_spec_ref': ref(OLD / 'spec.json'), 'independent_request_ref': ref(REVIEW),
    'only_requested_changes': ['DESKTOP-BIND-01', 'DESKTOP-BIND-02'],
    'scope_builder_unchanged': True, 'metadata_changed_functions': {'builder': ['verify'], 'engine': ['verify', 'register']},
    'future_tuple': None, 'selected_pending_origins': None, 'count_reset': False,
    'counter_note': 'Root selects actual future before/after/cut. No pending payloads or counts are reconstructed in this revision.',
    'future_execution': 'Must use new builder/engine hashes in fresh nonauthor scope/template review; then actual emitted metadata review. No existing review authorizes these revised bytes.',
    'authority': 'Source-only suitability does not grant invocation. All old actual source/Node/Go3 limitations remain.',
    'source_acceptance': False, 'formal_increment': 0})
for r in inputs:
    assert ref(Path(r['path'])) == r
save('inputs.after.json', inputs)
print(json.dumps({'state': 'STATIC_REVISION_COMPLETE', 'AST_targets': 3, 'AST_variants': 4, 'inverse_checks': 3,
    'old_inputs_rechecked': len(inputs), 'input_drift': 0, 'template_executions': 0, 'directory': str(HERE)}, ensure_ascii=False))
