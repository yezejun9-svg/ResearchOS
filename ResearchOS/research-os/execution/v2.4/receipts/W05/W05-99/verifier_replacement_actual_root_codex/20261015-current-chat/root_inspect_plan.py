"""Root independently checks the exact public preflight plan before commit."""
import base64,datetime,hashlib,json
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def digest(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size}
plan=E/'replacement-plan-01.json';assert ref(plan)['sha256']=='sha256:8ba3ed5d6a1cc467b2e8539d3c90ff710c3038b913aea8937e3e20989393cefe'
p=read(plan);b=read(R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_independent_observer_codex/20261015-current-chat/01-baseline.json');i=b['identity']
assert p['schema']=='researchos.runtime-verifier-replacement-plan.v2' and p['history_sequence']==1
assert all(not p.get(k) for k in ['predecessor_operation','predecessor_plan_sha256','predecessor_terminal_hash','rollback_of'])
assert p['operation_id']=='86b256fde9424ebb810537650136ad29'
assert p['readonly_census']==[0,0,0,0] and p['schema_version']==24
assert p['data_root']==b['data_root'] and p['host_id']==i['host_id'] and p['owner']==i['owner'] and p['service_root']==i['service_root']
assert p['principal_ref']==b['public_state_fields']['principal_ref']
assert p['file_ids']==[{k:v[k] for k in ['Volume','IndexHigh','IndexLow']} for v in b['public_file_ids']]
data=Path(p['data_root']);assert p['host_path']==str(data/'host') and p['db_path']==str(data/'researchos.sqlite')
assert digest((data/'host/host_state.json').read_bytes())==p['state_sha256']=='sha256:'+b['public_files']['host\\host_state.json']['sha256']
oldraw=base64.b64decode(p['old_record_bytes'],validate=True);newraw=base64.b64decode(p['new_record_bytes'],validate=True)
assert oldraw==(data/'host/runtime-verifier-installation.json').read_bytes()
assert digest(oldraw)==p['old_record_sha256']=='sha256:c5650d6fb6aa6d8bd9648aba233d75ed2f46637810f32112968e845d96f7c1c4'
assert digest(newraw)==p['new_record_sha256']=='sha256:d87a7aa4233e4b274842a1430148b0010d1942ead71e333104a74b635313c7fe'
old=json.loads(oldraw);new=json.loads(newraw);manifest=Path(p['manifest']);installation=read(manifest)
assert digest(manifest.read_bytes())==p['manifest_sha256']=='sha256:74ca846daf8f6ad82692b43dcd3b664fe2970247072546495d05519b01358609'
assert new['installation']==p['installation']==installation
allowed=['executable','executable_hash','source_commit']
changes=[k for k in set(old['installation'])|set(installation) if old['installation'].get(k)!=installation.get(k)]
assert sorted(changes)==sorted(allowed)
assert installation['source_commit']=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert digest(Path(installation['executable']).read_bytes())==installation['executable_hash']=='sha256:f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43'
assert new['installation_hash']==p['installation_hash'] and old['installation_hash']==p['old_installation_hash']
old['installation']=installation;old['installation_hash']=p['installation_hash'];assert old==new
out={'schema':'researchos.root-exact-verifier-replacement-plan-inspection.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operator':'codex:/root','plan_ref':ref(plan),'script_ref':ref(Path(__file__)),'operation_id':p['operation_id'],'identity_and_native_file_ids_match':True,'history_sequence':1,'readonly_census':[0,0,0,0],'schema_version':24,'old_raw_registration_matches_actual':True,'old_record_sha256':p['old_record_sha256'],'new_record_sha256':p['new_record_sha256'],'changed_installation_fields_exact':allowed,'other_registration_fields_unchanged':True,'source_commit':installation['source_commit'],'commit_invoked':False,'formal_increment':0}
with (E/'02-root-plan-inspection.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
