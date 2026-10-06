"""Bind exact W04 selectors, preserving all unrelated decoded registry entries."""
from pathlib import Path
import copy, datetime as dt, hashlib, json
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[5]
PATH=ROOT/'execution/v2.4/commands.json'; EXEC=HERE.parent/'executor_codex'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_new(p,value):
    with p.open('x',encoding='utf8',newline='\n') as f: json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
registry=load(PATH); original=copy.deepcopy(registry)
assert registry['revision']==37 and len(registry['commands'])==31 and sha(PATH)=='04eea86be4c832e3d20f343c2ade2e020c210581a7a4ec561954c5ccdba1cb49'
assert (ROOT/'execution/v2.4/step_state.json').is_file()
before=HERE/'commands_before_r37.json'; before.write_bytes(PATH.read_bytes())
bridge=(EXEC/'bridge.py').relative_to(ROOT).as_posix()
common=[(EXEC/name).relative_to(ROOT).as_posix() for name in ['bridge.py','parent_driver.py','evidence_module.py','expected.json','collect.py','test_bridge.py']]
common += [(EXEC/'frozen_inputs'/name).relative_to(ROOT).as_posix() for name in ['legacy_entries.json','commands-v24-r37.json']]
for key in ['test.context','test.domain']:
    entry=registry['commands'][key]
    entry.update(executable_tool='python',argv=['-B','-X','utf8',bridge,key],owner_card='W04-99',
        note='Exact W04 parent/case selectors reuse immutable real current proof and emit full frozen assertion IDs; every other pre-W04 admitted tuple forwards its complete frozen r37 entry unchanged. Independent acceptance remains separate.')
    entry['expected_artifacts']=common
    for field,values in [('task_id',['W04']),('case_id',['C03','C04','A01'])]:
        for value in values:
            if value not in entry['selectors'][field]: entry['selectors'][field].append(value)
    if key=='test.context':
        for value in ['W04-G01','W04-G02','W04-G03','W04-H01','W04-B01']:
            if value not in entry['selectors']['check_id']: entry['selectors']['check_id'].append(value)
entry=copy.deepcopy(original['commands']['package.validate_v24'])
entry.update(argv=['-B','-X','utf8',bridge,'package.validate'],selectors={'task_id':['W04'],'case_id':['A01'],'check_id':[]},
    assertion_field='assertion_ids',owner_card='W04-99',expected_artifacts=common,
    note='Exact W04 A01 formal specification-import/inventory evidence binding; actual frozen package-only validator remains NOT_RUN for product tests. Original package.validate_v24 is untouched.')
entry['allowed_env']=[name for name in entry['allowed_env'] if name not in ['DEEPSEEK_API_KEY','MOONSHOT_API_KEY']]
registry['commands']['package.validate']=entry
assert len(registry['commands'])==32
changed={key for key in original['commands'] if original['commands'][key]!=registry['commands'][key]}
assert changed=={'test.context','test.domain'}
assert registry['commands']['package.validate_v24']==original['commands']['package.validate_v24']
registry['revision']=38
now=dt.datetime.now(dt.timezone.utc).isoformat()
registry.update(updated_at=now,updated_by='codex:/root')
PATH.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
after=HERE/'commands_snapshot_r38.json'; after.write_bytes(PATH.read_bytes())
write_new(HERE/'commands_registration_codex.json',{'schema':'researchos.root-command-registration.v1','step_id':'W04-99','actor':'codex:/root','registered_at':now,
    'before':{'path':before.relative_to(ROOT).as_posix(),'sha256':sha(before)},'after':{'path':after.relative_to(ROOT).as_posix(),'sha256':sha(after)},
    'revision':38,'entry_count':32,'modified_keys':sorted(changed),'added_keys':['package.validate'],'unchanged_existing_entry_count':29,
    'legacy_key_unchanged':True,'mode':'FIXTURE','formal_case_count_delta':0,'parent_accepted':False,
    'bindings':load(EXEC/'expected.json')['case_entries']+load(EXEC/'expected.json')['gate_entries']})
print(json.dumps({'status':'PASS_EXACT_W04_REGISTERED','revision':38,'entry_count':32,'unchanged_existing_entries':29}))
