import base64,datetime,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def digest(raw):return 'sha256:'+hashlib.sha256(raw).hexdigest()
def ref(p):return {'path':str(p),'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
p=read(E/'replacement-plan-01.json');b=read(R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_independent_observer_codex/20261015-current-chat/01-baseline.json')
data=Path(p['data_root']);j=data/'host/runtime-verifier-replacements'/p['operation_id'];record=data/'host/runtime-verifier-installation.json';old=base64.b64decode(p['old_record_bytes']);new=base64.b64decode(p['new_record_bytes'])
assert record.read_bytes()==new and digest(new)==p['new_record_sha256']
assert (j/'old-registration.bin').read_bytes()==(j/'actual-backup.bin').read_bytes()==old
assert (j/'new-registration.bin').read_bytes()==new and (j/'plan.json').read_bytes()==(E/'replacement-plan-01.json').read_bytes()
states=['PREPARED','PUBLISHING','COMMITTED'];names=['0001-prepared.json','0002-publishing.json','0003-committed.json'];previous='';events=[]
for n,state,name in zip(range(1,4),states,names):
 event=read(j/name);h=event['hash'];event['hash']=''
 assert digest(json.dumps(event,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())==h
 assert event['state']==state and event['sequence']==n and event['previous']==previous and event['operation_id']==p['operation_id']
 assert event['plan_sha256']==ref(E/'replacement-plan-01.json')['sha256'] and event['old_record_sha256']==p['old_record_sha256'] and event['new_record_sha256']==p['new_record_sha256']
 events.append(ref(j/name));previous=h
assert sorted(x.name for x in j.iterdir())==sorted(names+['plan.json','old-registration.bin','new-registration.bin','actual-backup.bin'])
assert [x.name for x in j.parent.iterdir()]==[p['operation_id']]
unchanged=[]
for name in ['researchos.sqlite','researchos.sqlite-wal','host\\host_state.json']:
 v=b['public_files'][name];path=Path(v['path']);assert ref(path)['sha256']=='sha256:'+v['sha256'];unchanged.append(ref(path))
out={'schema':'researchos.root-actual-verifier-committed-inspection.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operator':'codex:/root','script_ref':ref(Path(__file__)),'plan_ref':ref(E/'replacement-plan-01.json'),'new_registration_ref':ref(record),'actual_replacefile_backup_ref':ref(j/'actual-backup.bin'),'actual_backup_equals_exact_old_raw':True,'new_registration_equals_exact_plan_raw':True,'event_states':states,'event_hash_chain_verified':True,'terminal_hash':previous,'event_refs':events,'journal_exact_member_count':7,'unchanged_db_wal_state_refs':unchanged,'shm_current_ref':ref(data/'researchos.sqlite-shm'),'shm_byte_immutability_not_asserted':True,'no_second_commit_or_recover':True,'formal_increment':0}
with (E/'04-root-committed-inspection.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
