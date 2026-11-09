"""Pure IO/AST PUB-01 preparation. Never imports or executes candidate code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P13 = HERE.parents[1]
OLD = P13/'fresh58_public_source_authority_preparation_codex/52d89f9f274642189817dd242291ad8c'
REVIEW = P13/'fresh58_public_source_producer_independent_review_codex/781dbe5fd7ca4a0bace612ceca209397'


def ref(p):
    b = p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}


def put(name, value):
    with (HERE/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())


source = (OLD/'publish.proposed.py').read_bytes()
assert hashlib.sha256(source).hexdigest() == 'a3da1646eb2b745595885a0f9bae8cf6aafd1ccc83f4640244943d3da9f5cf90'
assert ref(REVIEW/'review.json')['sha256'] == 'effa5303624c7eb0014b6478bc32e1ad41f45b4ba4adac0437411dfa768e5352'
inputs = [ref(OLD/n) for n in ['publish.proposed.py','fixed-inputs.json','contract.json','manifest.json']]
inputs += [ref(REVIEW/n) for n in ['review.json','handoff.json','manifest.json']]
put('inputs.before.json',{'files':inputs})

old_stable = '''def stable():
    for p, raw in list(READS.items()):
        need(read(p) == raw, 'Frozen input drift')
'''
new_stable = '''def live_guard(copies, expected_tuple):
    # Mutable canonical files are observations, never immutable READS entries.
    observation = {'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'point_in_time_only':True,'lifecycle_proof':False,'files':[],
                   'tuple':None,'head':None,'matched':False}
    LIVE_OBSERVATIONS.append(observation)
    live_raw = []
    for i, canonical in enumerate(CANONICAL):
        need(copies[i]['canonical_path'] == canonical, 'Live canonical copy order')
        expected = verify(copies[i]['ref'])
        p = safe(ROOT/canonical)
        need(p.is_file(), 'Live canonical is not a regular file')
        raw = p.read_bytes()
        observation['files'].append({'canonical_path':canonical,'live_ref':pin_bytes(p,raw),
                                     'copy_ref':copies[i]['ref'],'byte_equal':raw == expected})
        live_raw.append(raw)
    need(all(x['byte_equal'] for x in observation['files']), 'Current live canonical bytes differ from reviewed copies')
    cp, ow = [parse(x) for x in live_raw[:2]]
    actual = [cp['revision'],ow['revision'],len(cp['failure_counters'])]
    observation['tuple'], observation['head'] = actual, cp['head']
    need(all(type(x) is int for x in actual) and actual == expected_tuple and cp['head'] == SOURCE,
         'Current live canonical tuple/head differs from explicit reviewed authority')
    observation['matched'] = True
    observation['completed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()


def stable(copies, expected_tuple):
    for p, raw in list(READS.items()):
        need(read(p) == raw, 'Frozen input drift')
    live_guard(copies, expected_tuple)
'''
edits = [
    (b'READS = {}\n',b'READS = {}\nLIVE_OBSERVATIONS = []\n',1),
    (old_stable.encode(),new_stable.encode(),1),
    (b'    stable()\n',b"    stable(copies, q['expected_current_tuple'])\n",4),
    (b"'source_acceptance':False,'formal_increment':0,'execution_authorized':False}))",
     b"'source_acceptance':False,'formal_increment':0,'execution_authorized':False,\n                          'live_canonical_observations':LIVE_OBSERVATIONS}))",1),
    (b"'source_acceptance':False,'automatic_retry':False,'counter_reset':False}))",
     b"'source_acceptance':False,'automatic_retry':False,'counter_reset':False,\n                                'live_canonical_observations':LIVE_OBSERVATIONS}))",1),
    (b'        traceback.print_exc()\n        sys.exit(1)\n',
     b"        traceback.print_exc()\n        print(json.dumps({'live_canonical_observations':LIVE_OBSERVATIONS,'actual_native_exit':None}),file=sys.stderr)\n        sys.exit(1)\n",1)
]
candidate = source
proof = []
for old, new, count in edits:
    assert candidate.count(old) == count
    candidate = candidate.replace(old,new)
    proof.append({'old':old.decode(),'new':new.decode(),'occurrences':count})
inverse = candidate
for old, new, count in reversed(edits):
    assert inverse.count(new) == count
    inverse = inverse.replace(new,old)
assert inverse == source
old_ast, new_ast = ast.parse(source), ast.parse(candidate)
old_defs = {x.name:x for x in old_ast.body if isinstance(x,ast.FunctionDef)}
new_defs = {x.name:x for x in new_ast.body if isinstance(x,ast.FunctionDef)}
unchanged = []
for name, node in old_defs.items():
    if name not in ['stable','main']:
        assert ast.dump(node,include_attributes=False)==ast.dump(new_defs[name],include_attributes=False)
        assert ast.get_source_segment(source.decode(),node)==ast.get_source_segment(candidate.decode(),new_defs[name])
        unchanged.append(name)
guard = ast.get_source_segment(candidate.decode(),new_defs['live_guard'])
assert 'p.read_bytes()' in guard and 'READS[' not in guard and 'read(p)' not in guard
assert 'raw == expected' in guard and "actual == expected_tuple and cp['head'] == SOURCE" in guard
assert len([n for n in ast.walk(new_defs['main']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='stable'])==4
assert candidate.index(b"stable(copies, q['expected_current_tuple'])") < candidate.index(b'    out.mkdir()')
tail = candidate[candidate.index(b"with (out/'manifest.json').open('xb')") :]
assert tail.index(b'stable(copies,') < tail.index(b'        print(')
with (HERE/'publish.v2.proposed.py').open('xb') as f:
    f.write(candidate)
with (HERE/'source.diff').open('xb') as f:
    f.write(''.join(difflib.unified_diff(source.decode().splitlines(True),candidate.decode().splitlines(True),fromfile='sealed/publish.proposed.py',tofile='new/publish.v2.proposed.py')).encode())
put('inverse.json',{'whole_byte_inverse':True,'baseline_ref':ref(OLD/'publish.proposed.py'),
                    'candidate_ref':ref(HERE/'publish.v2.proposed.py'),'edits':proof,
                    'unchanged_definitions_byte_and_AST':unchanged,'new_definition':'live_guard',
                    'changed_definitions':['stable','main']})
put('static-audit.json',{'status':'SOURCE_PREPARATION_ONLY','whole_inverse':True,
    'AST_parsed':True,'unchanged_original_definitions':len(unchanged),'stable_call_count':4,
    'live_buffers_separate_from_READS':True,'all_four_byte_equality':True,'actual_tuple_head_check':True,
    'allocation_guard':True,'post_manifest_success_guard':True,'point_in_time_only':True,
    'candidate_or_gate_imported':False,'candidate_executed':False,'canonical_read_or_write':False,
    'future_cases_NOT_RUN':['live revision advanced before allocation: reject with no leaf',
      'unchanged tuple but any of four raw bytes changed: reject',
      'live change after allocation: fail, preserve first cause, never success',
      'all four live bytes match r333 copies: preserve original publication predicates',
      'live paths are absent from immutable READS and inputs.json'],
    'new_failure_origins':[]})
after = [ref(Path(x['path'])) for x in inputs]
assert after == inputs
put('inputs.after.json',{'files':after,'drift':[]})
print(json.dumps({'candidate':ref(HERE/'publish.v2.proposed.py'),'static_audit':ref(HERE/'static-audit.json'),
                  'inverse':ref(HERE/'inverse.json')},ensure_ascii=False))
