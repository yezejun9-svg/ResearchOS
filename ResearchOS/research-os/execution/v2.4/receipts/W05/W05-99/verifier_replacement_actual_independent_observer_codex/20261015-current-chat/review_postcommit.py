import sys
sys.dont_write_bytecode=True
import observe_actual as o
import json,base64,pathlib,datetime
E=o.E;D=o.D
RE=o.R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_root_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
b=read(E/'01-baseline.json');f=read(E/'02-preflight.json');z=read(E/'03-postcommit.json');p=read(RE/'replacement-plan-01.json')
stable=['public_file_ids','schema_version_summary','global_census','db_schema','tables','identity','public_state_fields']
for field in stable:assert b[field]==f[field]==z[field],field
regkey=str(pathlib.Path('host')/'runtime-verifier-installation.json')
for key in set(z['public_files'])-{'researchos.sqlite-shm',regkey}:assert b['public_files'][key]==f['public_files'][key]==z['public_files'][key],key
oldraw=base64.b64decode(p['old_record_bytes']);newraw=base64.b64decode(p['new_record_bytes'])
assert oldraw==(E/'01-baseline-registration.raw.json').read_bytes()
assert newraw==(E/'03-postcommit-registration.raw.json').read_bytes()==(D/'host/runtime-verifier-installation.json').read_bytes()
assert o.sha(newraw)=='d87a7aa4233e4b274842a1430148b0010d1942ead71e333104a74b635313c7fe'
op=p['operation_id'];jr=D/'host/runtime-verifier-replacements';d=jr/op
assert [x.name for x in jr.iterdir()]==[op]
expected={'plan.json','old-registration.bin','new-registration.bin','actual-backup.bin','0001-prepared.json','0002-publishing.json','0003-committed.json'}
assert {x.name for x in d.iterdir()}==expected
assert (d/'plan.json').read_bytes()==(RE/'replacement-plan-01.json').read_bytes()
assert (d/'old-registration.bin').read_bytes()==(d/'actual-backup.bin').read_bytes()==oldraw
assert (d/'new-registration.bin').read_bytes()==newraw
events=[];previous=''
for index,state in enumerate(['PREPARED','PUBLISHING','COMMITTED'],1):
 path=d/f'{index:04d}-{state.lower()}.json';v=read(path);saved=v['hash'];v['hash']=''
 assert o.digest(v)==saved
 assert v['sequence']==index and v['previous']==previous and v['state']==state
 assert v['schema']=='researchos.runtime-verifier-replacement.v1' and v['operation_id']==op
 assert v['plan_sha256']=='sha256:'+o.pin(RE/'replacement-plan-01.json')['sha256']
 assert v['old_record_sha256']==p['old_record_sha256'] and v['new_record_sha256']==p['new_record_sha256']
 datetime.datetime.fromisoformat(v['at'].replace('Z','+00:00'));v['hash']=saved;events.append(v);previous=saved
assert p['history_sequence']==1 and all(not p.get(k) for k in ['predecessor_operation','predecessor_plan_sha256','predecessor_terminal_hash'])
acl=read(E/'03-postcommit-acl.json')
for row in acl['rows']:
 assert row['owner_is_current']
 path=pathlib.Path(row['path'])
 if path==D or path.name in ['researchos.sqlite','coordinator.lock']:continue
 assert row['protected'] and len(row['rules'])==1
 r=row['rules'][0];assert r['sid']==acl['current_sid'] and r['type']=='Allow' and r['mask']==0x001f01ff and not r['inherited'] and r['propagation_flags']==0
 assert r['inheritance_flags']==(3 if path.is_dir() else 0)
ids=[]
for path in [D/'host/runtime-verifier-installation.json',jr,d]+sorted(d.iterdir()):
 h=o.openread(path)
 try:
  identity=o.fileid(h)
  if path.is_file():assert identity['links']==1
  for parent in path.parents:assert not parent.lstat().st_file_attributes&0x400
  ids.append({'path':str(path),'identity':identity})
 finally:o.k.CloseHandle(h)
delta={key:{'before':f['data_metadata_only'].get(key),'after':z['data_metadata_only'].get(key)} for key in set(f['data_metadata_only'])|set(z['data_metadata_only']) if f['data_metadata_only'].get(key)!=z['data_metadata_only'].get(key)}
for key in delta:assert key in ['host','host/runtime-verifier-installation.json','researchos.sqlite-shm'] or key.startswith('host/runtime-verifier-replacements'),key
result=read(RE/'03-commit.result.json');decision=read(RE/'03-root-explicit-commit-decision.json')
assert result['native_exit']==0 and decision['action']=='COMMIT_EXACT_REVIEWED_PLAN_ONCE' and not decision['automatic_retry'] and not decision['automatic_recovery']
for v in result.values():
 if isinstance(v,dict) and {'path','sha256','bytes'}<=v.keys():assert o.pin(pathlib.Path(v['path']))==v
stdout=read(RE/'03-commit.stdout.raw.json');assert stdout['state']=='COMMITTED' and stdout['outcome']=='APPLIED' and stdout['operation_id']==op
shm={stage:{'file':x['public_files']['researchos.sqlite-shm'],'metadata':x['data_metadata_only']['researchos.sqlite-shm']} for stage,x in [('baseline',b),('preflight',f),('postcommit',z)]}
o.save(E/'03-postcommit-review.json',{'at':o.now(),'verdict':'LIMITED_ACTUAL_REGISTRATION_ACCEPTED','scope':'single actual registration maintenance only','operation_id':op,'plan':o.pin(RE/'replacement-plan-01.json'),'root_commit_result':o.pin(RE/'03-commit.result.json'),'root_explicit_decision':o.pin(RE/'03-root-explicit-commit-decision.json'),'stable_fields':stable,'DB_WAL_state_raw_unchanged':True,'all_88_tables_including_config_and_idempotency_unchanged':True,'registration_exact_planned_new':True,'backup_exact_old':True,'journal_files':[o.pin(x) for x in sorted(d.iterdir())],'events':events,'actual_event_states':['PREPARED','PUBLISHING','COMMITTED'],'note':'FILE_REPLACED is not the frozen journal event name; publication is proved by actual-backup and current exact new bytes','history_sequence':1,'private_acl_verified':True,'native_identities':ids,'metadata_delta':delta,'shm_separate_observation':shm,'old_shm_raw_not_saved_no_offset_cause_claim':True,'all_observer_handles_closed':True,'schema_migration_performed':False,'observer_commit_or_recover':False,'product_formal_acceptance':False,'formal_increment':0,'formal_accepted':0,'formal_total':42,'parents_open':22})
print(json.dumps({'review':o.pin(E/'03-postcommit-review.json'),'actual_states':[x['state'] for x in events],'shm_preflight_equals_postcommit':f['public_files']['researchos.sqlite-shm']==z['public_files']['researchos.sqlite-shm']},ensure_ascii=False))
