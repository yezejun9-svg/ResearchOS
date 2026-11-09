from pathlib import Path
import ast, difflib, hashlib, json

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).parent
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf/register.py'
raw = BASE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'bb3beccc2a4c2a576b648871dacc0dcab8f8bbff5258e1f0369d1d0af0f13280'
s = raw.decode('utf-8').replace('\r\n', '\n')
original = s
def replace_function(name, new):
    global s
    tree = ast.parse(s)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = s.splitlines(keepends=True)
    s = ''.join(lines[:node.lineno-1]) + new.rstrip() + '\n' + ''.join(lines[node.end_lineno:])
def exact(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new, 1)

exact('The active scope is materialized only by seal after independently reviewed CAS.', 'Head-forward metadata only. No source scope or grant is created by any mode.')
exact('HASHED = 0', 'HASHED = 0\nREADS = {}\nREQUEST_REF = None\nOWN_OUT = False')
replace_function('verify', '''def verify(r):
    need(type(r) is dict and set(r) == {'path', 'sha256', 'bytes'} and type(r['bytes']) is int and r['bytes'] >= 0, 'exact REF shape')
    q = path(r['path'])
    need(q not in CANON, 'live canonical belongs to CAS only')
    b = raw(q)
    need(hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes'], 'reference drift')
    normalized = {'path': str(q), 'sha256': r['sha256'], 'bytes': r['bytes']}
    need(q not in READS or READS[q] == normalized, 'same path changed during read')
    READS[q] = normalized
    return b''')
extension = (OUT / 'extension.proposed.py.txt').read_text(encoding='utf-8')
etree = ast.parse(extension)
new_desired = next(n for n in etree.body if isinstance(n, ast.FunctionDef) and n.name == 'desired')
elines = extension.splitlines(keepends=True)
replace_function('desired', ''.join(elines[new_desired.lineno-1:new_desired.end_lineno]))
s = s.replace('\ndef desired(p):', '\n' + ''.join(elines[:new_desired.lineno-1]) + '\ndef desired(p):', 1)
replace_function('setup', '''def setup():
    need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize, 'Python flags')
    need(Path.cwd().resolve() == ROOT, 'Root cwd')
    q, runtime, r, origins = initialize_request()
    if MODE == 'prepare':
        prepare_request(q, runtime, r, origins)
        return None, None, None
    p = parse(raw(OUT / 'prepared_refs.json'))
    need(path(p['registration_namespace']) == OUT and p['authorized'] is False and p['future_root_grant'] is None, 'metadata only')
    need(same(p['request_ref'], REQUEST_REF), 'prepared current immutable request')
    pairs = [('head', 'head_after'), ('head_before', 'head_before'), ('before_tuple', 'before_tuple'), ('after_tuple', 'after_tuple'),
             ('timestamp', 'timestamp'), ('status_ref', 'status_ref'), ('old_deleted_paths', 'old_deleted_paths'),
             ('toolchain_lock_ref', 'toolchain_lock_ref'), ('helper_ref', 'helper_ref'), ('source_closure_review_ref', 'source_closure_review_ref'),
             ('source_closure_manifest_ref', 'source_closure_manifest_ref'), ('origin_cut_ref', 'origin_cut_ref')]
    need(all(p[a] == q[b] for a, b in pairs) and p['runtime_files'] == runtime and p['origins'] == origins and p['source_paths'] == r['source_paths'], 'prepared/request fields')
    for key, name in [('completed_ref', 'completed_ref'), ('source_manifest_ref', 'manifest_ref'), ('outer_manifest_ref', 'outer_manifest_ref'), ('source_grant_ref', 'grant_ref'), ('source_scope_ref', 'scope_ref')]:
        need(same(p[key], r[name]), 'prepared actual closure relation')
    need(len(p['original_refs']) == len(p['desired_refs']) == 4, 'prepared four')
    for original, copied in zip(q['original_copy_refs'], p['original_refs']):
        need(verify(original) == verify(copied) and path(copied['path']).parent == OUT, 'prepared original copy')
    lock = doc(p['toolchain_lock_ref'])['tools']
    need(Path(sys.executable).resolve() == Path(lock['python']['path']).resolve(), 'Python exact path')
    for k in ['python', 'git']:
        need(ref(lock[k]['path'])['sha256'] == lock[k]['sha256'], 'tool bytes')
    for item in p['immutable_inputs']:
        verify(item)
    need(set(READS) <= {path(x['path']) for x in p['immutable_inputs']}, 'all request/closure reads immutable')
    need(set(p['script_refs']) == {'engine', 'builder', 'register', 'run', 'seal'}, 'no grant producer')
    source = verify(q['code_refs']['engine'])
    for mode in ['register', 'run', 'seal']:
        actual = p['script_refs'][mode]
        need(path(actual['path']) == OUT / (mode + '.py'), 'script layout')
        need(verify(actual) == source.replace(b"MODE = 'register'", ("MODE = '" + mode + "'").encode(), 1), 'only emitted mode differs')
    for k in ['engine', 'builder']:
        need(same(p['script_refs'][k], q['code_refs'][k]), 'preparation code provenance')
    save(MODE + '.runtime.before-import.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': loaded(p)})
    h = p['helper_ref']
    need(h['sha256'] == '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'owned helper')
    helper = types.ModuleType('desktop_registration_owned')
    helper.__file__ = str(path(h['path']))
    sys.modules[helper.__name__] = helper
    exec(compile(verify(h), helper.__file__, 'exec'), helper.__dict__)
    save(MODE + '.runtime.before.json', {'kind': 'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE', 'files': loaded(p, helper)})
    return p, lock, helper''')
exact("need(len(sys.argv) == 3, 'register review-path review-sha; cannot bypass independent metadata review')\n    review_ref = ref(sys.argv[1])\n    need(review_ref['sha256'] == sys.argv[2], 'metadata review SHA')", "need(len(sys.argv) == 5, 'register request-path request-sha review-path review-sha')\n    review_ref = ref(sys.argv[3])\n    need(review_ref['sha256'] == sys.argv[4], 'metadata review SHA')")
exact("    need(not path(p['future_scope_ref']['path'], False).exists(), 'active scope must not yet exist')\n", '')
exact("need(len(sys.argv) == 3, 'run review-path review-sha')\n    item = ref(sys.argv[1])\n    need(item['sha256'] == sys.argv[2], 'review SHA')", "need(len(sys.argv) == 5, 'run request-path request-sha review-path review-sha')\n    item = ref(sys.argv[3])\n    need(item['sha256'] == sys.argv[4], 'review SHA')")
exact("str(OUT / 'register.py'), str(path(item['path'])), item['sha256']]", "str(OUT / 'register.py'), str(path(REQUEST_REF['path'])), REQUEST_REF['sha256'], str(path(item['path'])), item['sha256']]")
exact("need(len(sys.argv) == 1, 'seal no args')", "need(len(sys.argv) == 3, 'seal request-path request-sha')")
start = s.index("    active = doc(p['active_scope_payload_ref'])['scope']", s.index('def seal('))
end = s.index("    audit = save('registration-audit.json'", start)
s = s[:start] + "    need(all(raw(q) == b for q, b in zip(CANON, target)), 'four targets after seal source guard')\n" + s[end:]
exact("'schema': 'researchos.desktop15-source-integration-registration-audit.v1'", "'schema': 'researchos.desktop58-forward-head-registration-audit.v1'")
exact("'scope_ref': p['future_scope_ref'], 'controller_review_ref': p['controller_review_ref'], 'source_acceptance': False, 'formal_increment': 0,", "'request_ref': p['request_ref'], 'source_closure_review_ref': p['source_closure_review_ref'], 'source_acceptance': False, 'formal_increment': 0,")
exact("'tuple': p['after_tuple'], 'scope_ref': p['future_scope_ref'], 'audit_ref': audit, 'formal_increment': 0", "'tuple': p['after_tuple'], 'request_ref': p['request_ref'], 'audit_ref': audit, 'formal_increment': 0")
replace_function('grant', '')
exact("        {'register': register, 'run': run, 'seal': seal, 'grant': grant}[MODE](p, lock, helper)", "        if MODE != 'prepare':\n            {'register': register, 'run': run, 'seal': seal}[MODE](p, lock, helper)")
exact("                save(MODE + '.failure.json', {'first_error': first, 'secondary_errors': secondary, 'counter_reset': False, 'automatic_retry': False})", "                if MODE != 'prepare' or OWN_OUT:\n                    save(MODE + '.failure.json', {'first_error': first, 'secondary_errors': secondary, 'counter_reset': False, 'automatic_retry': False})")
# No stage is allowed to report successful completion after the inherited soft deadline.
exact("    return 1 if first is not None else 0", "    if first is None and time.monotonic() >= DEADLINE:\n        first = {'phase': MODE + '-completion-deadline', 'error': 'metadata deadline1200 exceeded', 'actual_native_exit': None}\n        print(json.dumps(first, ensure_ascii=False), file=sys.stderr)\n    return 1 if first is not None else 0")
assert 'def grant(' not in s and 'future_scope_ref' not in s and 'active_scope_payload_ref' not in s
ast.parse(s)
engine = s.replace('\n', '\r\n').encode('utf-8')
def put(name, b):
    with (OUT/name).open('xb') as f: f.write(b)
    return {'path': str(OUT/name), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes':len(b)}
eref = put('forward_head_engine.proposed.py', engine)
builder = '''"""Root-only future pure-IO draft builder. Never imports the owned Windows helper."""
import sys
sys.dont_write_bytecode = True
import hashlib
from pathlib import Path
import types

def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize):
        raise RuntimeError('Python -I -S -X utf8 required')
    if len(sys.argv) != 3:
        raise RuntimeError('builder request-path request-sha')
    p = Path(ENGINE_PATH)
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ENGINE_SHA or len(raw) != ENGINE_BYTES:
        raise RuntimeError('fixed engine bytes')
    m = types.ModuleType('desktop58_forward_metadata_engine')
    m.__file__ = str(p)
    sys.modules[m.__name__] = m
    exec(compile(raw, str(p), 'exec'), m.__dict__)
    m.MODE = 'prepare'
    return m.main()

if __name__ == '__main__':
    raise SystemExit(main())
'''
builder = builder.replace('ENGINE_PATH', repr(eref['path'])).replace('ENGINE_SHA', repr(eref['sha256'])).replace('ENGINE_BYTES', str(eref['bytes']))
ast.parse(builder)
bref = put('build_forward_draft.proposed.py', builder.encode())
put('original.r332.register.py.txt', raw)
put('forward-engine.diff', ''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='r332/register.py',tofile='forward_head_engine.proposed.py')).encode())
ops=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,raw,engine,autojunk=False).get_opcodes():
    if tag!='equal': ops.append({'old_start':a,'old_end':b,'new_start':c,'new_end':d,'old_hex':raw[a:b].hex(),'new_hex':engine[c:d].hex()})
restored=bytearray(engine)
for op in reversed(ops):
    assert bytes(restored[op['new_start']:op['new_end']]).hex()==op['new_hex']
    restored[op['new_start']:op['new_end']]=bytes.fromhex(op['old_hex'])
assert bytes(restored)==raw
put('whole-inverse.json',(json.dumps({'base_sha256':hashlib.sha256(raw).hexdigest(),'candidate_ref':eref,'operations':ops,'restored_exact':True},indent=2)+'\n').encode())
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)}
newfunc={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
unchanged=[n for n in oldfunc if oldfunc[n]==newfunc.get(n)]
changed=[n for n in oldfunc if n in newfunc and oldfunc[n]!=newfunc[n]]
checks={
 'engine_AST':True,'builder_AST':True,'candidate_imported_or_executed':False,'whole_byte_inverse':True,
 'no_grant_function':'grant' not in newfunc,'no_future_scope_materialization':'future_scope_ref' not in s,
 'CAS_after_each_source_guard':"source_guard(p, lock, helper, 'register-pre-' + str(i))\n        need(all(raw(x) == b for x, b in zip(CANON, live))" in s,
 'final_register_CAS':"source_guard(p, lock, helper, 'register-after')\n    need(all(raw(q) == b for q, b in zip(CANON, target))" in s,
 'final_seal_CAS':"source_guard(p, lock, helper, 'seal-current')\n    need(all(raw(q) == b for q, b in zip(CANON, target))" in s,
 'only_CP_OW_replace':'for i, q in enumerate(CANON[:2]):' in s,
 'ST_CM_original_bytes':'return before, [encode(cp), encode(ow), before[2], before[3]]' in s,
 'no_product_command_additions':newfunc['source_guard']==oldfunc['source_guard'] and newfunc['owned_call']==oldfunc['owned_call'],
 'helper_Job_contract_unchanged':newfunc['job_ok']==oldfunc['job_ok'],
 'review_contract_unchanged':newfunc['review_ok']==oldfunc['review_ok'],
 'softdeadline1200_read32GiB_unchanged':newfunc['raw']==oldfunc['raw'],
 'no_actual_draft_created':True,
}
assert all(v for k,v in checks.items() if k not in ['candidate_imported_or_executed'])
put('static-audit.json',(json.dumps({'schema':'researchos.desktop58-forward-head-preparation-static.v1','checks':checks,'unchanged_functions':unchanged,'changed_functions':changed,'removed_functions':[n for n in oldfunc if n not in newfunc],'new_functions':[n for n in newfunc if n not in oldfunc],'runtime_tests':'NOT_RUN','source_acceptance':False,'canonical_writes':0},indent=2)+'\n').encode())
put('code-refs.json',(json.dumps({'engine':eref,'builder':bref},ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'engine':eref,'builder':bref,'unchanged_functions':unchanged,'changed_functions':changed,'inverse_hunks':len(ops),'static_checks':len(checks)},ensure_ascii=False))
