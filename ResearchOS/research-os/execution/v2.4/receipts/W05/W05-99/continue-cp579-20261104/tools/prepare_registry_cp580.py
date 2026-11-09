import copy, hashlib, json
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104'
raw=(root/'execution/v2.4/commands.json').read_bytes()
assert raw==(out/'commands.before.json').read_bytes()
old=json.loads(raw); assert old['revision']==40
candidate=copy.deepcopy(old); entry=candidate['commands']['test.runtime']
entry['selectors']['check_id']+=['W05-H08','W05-P01','W05-U02']
entry['tool_env']['RESEARCHOS_PYTHON']='python'
entry['fixed_env']['RESEARCHOS_V24_SPEC_ROOT']='D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4'
for path in ['tests/runtime/check/routing_test.go','tests/runtime/check/w0502.go','ops/ci/runtime_v24.py','tests/runtime/runtime_v24_test.py']:
    if path not in entry['expected_artifacts']: entry['expected_artifacts'].append(path)
entry['note']='W05 routing compatibility repair: exact W05-01/02 continue to the served Go suites; exact W05-G01 and W12/C11 continue to legacy fixture. Exact W05-G02/H08/P01/U02 and W05/A04 route to the frozen v2.4 LIVE gap preflight. Missing formal Mu driver returns nonzero BLOCKED/IMPLEMENTATION_GAP with all assertions NOT_RUN and zero passed IDs; this is not LIVE execution or acceptance. Mixed, unknown and cross-task tuples are rejected. Python resolves from the locked absolute tool path with SHA256 verification, never PATH. No LIVE permission or provider/native execution is added. Historical revision40 entry is retained byte-for-byte in this receipt commands.before.json. Owner and owner_card remain unchanged; this patch is root-integrated under the user-authorized compatibility scope.'
candidate['revision']=41
candidate['revision_note']='Root integration of independently reviewed W05 selector/interpreter compatibility repair. Other command entries retained exactly; formal LIVE driver remains unimplemented.'
assert {k:v for k,v in candidate['commands'].items() if k!='test.runtime'}=={k:v for k,v in old['commands'].items() if k!='test.runtime'}
destination=out/'registry-candidate.json'
assert not destination.exists()
destination.write_text(json.dumps(candidate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary={'base_revision':40,'candidate_revision':41,'base_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'only_command_changed':'test.runtime','other_entries_preserved':True,'runtime_entry_before':old['commands']['test.runtime'],'runtime_entry_after':entry,'formal_increment':0}
(out/'registry-proposal.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if not k.startswith('runtime_entry')}))
