from pathlib import Path
import ast, difflib, hashlib, json
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).parent
BASE=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94'
PEER=ROOT/'execution/v2.4/receipts/W05/W05-99/a04_formal_profile_binding_independent_review_codex/70ca957e1f4b4d7fb4223159361c86e4'
def pin(p):
 b=p.read_bytes();return {'path':p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def write(name,d):
 with (OUT/name).open('xb') as f:f.write(json.dumps(d,ensure_ascii=False,indent=2).encode()+b'\n')
 return pin(OUT/name)
def check(ref):
 p=Path(ref['path']);p=p if p.is_absolute() else ROOT/p
 got=pin(p);assert got['sha256']==ref['sha256'] and got['bytes']==ref['bytes'];return got
review=json.loads((PEER/'review.json').read_bytes());hdf=json.loads((BASE/'handoff.json').read_bytes())
assert pin(PEER/'review.json')['sha256']=='53b70fa8ce1aa14aadd23af2844d8cfaa0dbfd89ca9c99ef2d685bfb976b0d57'
assert pin(PEER/'handoff.json')['sha256']=='43e8055526de07d0b334f26c4437843e3c51ed6bf5f84f77de11799aeeed8bc8'
peer_controls=check(review['independent_controls_ref'])
assert peer_controls['sha256']=='c6d7a23626aea4d968337c2cc4a354d359b74f51bd5450a420ab6d63f87fbcb0'
mf=json.loads((BASE/'manifest.json').read_bytes());old_members=[check(x) for x in mf['members']]
old_sources={k:check(v) for k,v in hdf['source_pins'].items()}
assert old_sources==review['selected_source_refs']
old=Path(old_sources['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8')
replacements=[
("closed.get('actual_refusal_response') != response","not _same_json(closed.get('actual_refusal_response'), response)"),
("    if kind == 'Run' and value['task_id'] != identity['task_id']:\n","    if kind == 'Task':\n        _current_run(value, identity['run_id'])\n    if kind == 'Run' and value['task_id'] != identity['task_id']:\n"),
("    task, run = objects['Task'], objects['TaskRun']\n","    task, run = objects['Task'], objects['TaskRun']\n    _current_run(task, identity['run_id'])\n")]
new=old
for a,b in replacements:
 assert new.count(a)==1
 new=new.replace(a,b)
helper="""

def _same_json(left, right):
    # Compare JSON values, never Python's cross-type numeric equality.
    # Object key order is not semantic; array order and each JSON type are.
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (all(type(key) is str for key in left) and
                all(type(key) is str for key in right) and
                set(left) == set(right) and
                all(_same_json(left[key], right[key]) for key in left))
    if type(left) is list:
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    if type(left) is float:
        import math
        return math.isfinite(left) and math.isfinite(right) and left == right
    if type(left) in (str, int, bool, type(None)):
        return left == right
    return False


def _current_run(task, selected_run_id):
    # Terminal Task pointers are nullable in the public schema. Other readers
    # still require the exact selected terminal Run/event/version provenance.
    if task['active_run_id'] not in (None, selected_run_id):
        raise ValueError('OPEN_TASK_FOREIGN_ACTIVE_RUN')
"""
new+=helper
ast.parse(new)
p=OUT/'formal_profile_w05.identity.v4.proposed.py'
with p.open('xb') as f:f.write(new.encode())
sources={'execution/v2.4/formal_profile_w05.py':pin(p)}
new_hash=sources['execution/v2.4/formal_profile_w05.py']['sha256']
mapping={'ops/ci/runtime_w05_live.py':'runtime_w05_live.identity.v4.proposed.py','ops/ci/export_a04_live.py':'export_a04_live.identity.v4.proposed.py','execution/v2.4/formal_case_index.py':'formal_case_index.w05.identity.v4.proposed.py','ops/ci/runtime.py':'runtime.w05.route.identity.v4.proposed.py'}
for k,name in mapping.items():
 b=Path(old_sources[k]['path']).read_bytes()
 if k=='ops/ci/runtime_w05_live.py':
  assert b.count(old_sources['execution/v2.4/formal_profile_w05.py']['sha256'].encode())==2
  b=b.replace(old_sources['execution/v2.4/formal_profile_w05.py']['sha256'].encode(),new_hash.encode())
 ast.parse(b)
 with (OUT/name).open('xb') as f:f.write(b)
 sources[k]=pin(OUT/name)
entries=[]
for k,after in sources.items():
 before=old_sources[k];a=Path(before['path']).read_text(encoding='utf-8');b=Path(after['path']).read_text(encoding='utf-8')
 delta=list(difflib.ndiff(a.splitlines(keepends=True),b.splitlines(keepends=True)))
 assert ''.join(difflib.restore(delta,1))==a and ''.join(difflib.restore(delta,2))==b
 am={n.name:n for n in ast.parse(a).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 bm={n.name:n for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 changed=[n for n in am if ast.dump(am[n],include_attributes=False)!=ast.dump(bm[n],include_attributes=False) or ast.get_source_segment(a,am[n])!=ast.get_source_segment(b,bm[n])]
 if k=='execution/v2.4/formal_profile_w05.py':
  assert set(changed)=={'verify_refusal','_database_row','verify_live_originals'}
  old_assignment=next(n for n in ast.parse(a).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PUBLIC_SCHEMAS' for t in n.targets))
  new_assignment=next(n for n in ast.parse(b).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PUBLIC_SCHEMAS' for t in n.targets))
  assert ast.get_source_segment(a,old_assignment)==ast.get_source_segment(b,new_assignment)
 elif k=='ops/ci/runtime_w05_live.py':assert changed==['verify_bundle']
 else:assert not changed and before['sha256']==after['sha256']
 entries.append({'target':k,'before_ref':before,'after_ref':after,'ndiff':delta,'changed_definitions':changed,'unchanged_definitions':[n for n in am if n not in changed],'new_definitions':sorted(set(bm)-set(am)),'whole_byte_inverse':True})
inverse=write('source.inverse.actual.json',{'schema':'researchos.a04-json-identity-source-inverse.v1','entries':entries})
for name,source in [('basis.review.original.json',PEER/'review.json'),('basis.review.handoff.original.json',PEER/'handoff.json'),('basis.source.handoff.original.json',BASE/'handoff.json'),('basis.source.manifest.original.json',BASE/'manifest.json')]:
 with (OUT/name).open('xb') as f:f.write(source.read_bytes())
construction=write('construction.actual.json',{'schema':'researchos.a04-json-identity-source-construction.v1','author_id':'codex:/root/f08_whole_scope_review','basis_review_ref':pin(PEER/'review.json'),'basis_review_handoff_ref':pin(PEER/'handoff.json'),'basis_peer_controls_ref':peer_controls,'basis_handoff_ref':pin(BASE/'handoff.json'),'basis_manifest_ref':pin(BASE/'manifest.json'),'basis_members':old_members,'source_pins':sources,'inverse_ref':inverse,'runtime_producer_ref':pin(ROOT/'internal/domain/runtime.go'),'candidate_module_imports':0,'SQL_Go_CLI_model_native_calls':0,'new_tool_failures':0})
print(json.dumps({'source_pins':sources,'old_members_verified':len(old_members),'profile_changed_definitions':entries[0]['changed_definitions'],'new_helpers':entries[0]['new_definitions'],'public55_schema_data_unchanged':True,'inverse_ref':inverse},ensure_ascii=False))

