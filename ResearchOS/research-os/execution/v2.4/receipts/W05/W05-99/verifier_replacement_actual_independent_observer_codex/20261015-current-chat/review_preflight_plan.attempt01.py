import sys
sys.dont_write_bytecode=True
import observe_actual as o
import json,base64,pathlib,sqlite3
E=o.E;D=o.D;R=o.R
ROOT_E=R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_root_codex/20261015-current-chat'
PLAN=ROOT_E/'replacement-plan-01.json'
SCOPE=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp492/actual-verifier-replacement-scope.json'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert o.pin(SCOPE)['sha256']=='036a859495a8d377fd61f0a328521a31d9c82da69cf2a745e3f77a5ceac29f29'
assert o.pin(PLAN)['sha256']=='8ba3ed5d6a1cc467b2e8539d3c90ff710c3038b913aea8937e3e20989393cefe'
base=read(E/'01-baseline.json');fresh=read(E/'02-preflight.json');p=read(PLAN)
stable=['public_file_ids','schema_version_summary','global_census','db_schema','tables','identity','public_state_fields','public_files','data_metadata_only','maintenance_journal']
for field in stable:assert base[field]==fresh[field],field
assert not fresh['maintenance_journal']
assert p['schema']=='researchos.runtime-verifier-replacement-plan.v2' and p['history_sequence']==1
assert all(not p.get(k) for k in ['predecessor_operation','predecessor_plan_sha256','predecessor_terminal_hash','rollback_of'])
assert len(p['operation_id'])==32 and len(bytes.fromhex(p['operation_id']))==16
assert [p[k] for k in ['data_root','host_path','db_path']]==[str(D),str(D/'host'),str(D/'researchos.sqlite')]
assert p['file_ids']==[{k:x[k] for k in ['Volume','IndexHigh','IndexLow']} for x in fresh['public_file_ids']]
assert p['principal_ref']==fresh['public_state_fields']['principal_ref']
for key,observed in [('host_id','host_id'),('owner','owner'),('service_root','service_root')]:assert p[key]==fresh['identity'][observed]
assert p['state_sha256']=='sha256:'+fresh['public_files']['host/host_state.json']['sha256']
assert p['schema_version']==24 and p['readonly_census']==fresh['global_census']==[0,0,0,0]
oldraw=base64.b64decode(p['old_record_bytes']);newraw=base64.b64decode(p['new_record_bytes'])
assert oldraw==(E/'01-baseline-registration.raw.json').read_bytes()==(E/'02-preflight-registration.raw.json').read_bytes()
assert p['old_record_sha256']=='sha256:'+o.sha(oldraw) and p['new_record_sha256']=='sha256:'+o.sha(newraw)
old=json.loads(oldraw);new=json.loads(newraw)
assert p['old_registration_hash']==o.digest(old) and p['registration_hash']==o.digest(new)
assert p['old_installation_hash']==old['installation_hash']==o.digest(old['installation'])
assert p['installation_hash']==new['installation_hash']==o.digest(new['installation'])==o.digest(p['installation'])
assert old.keys()==new.keys()
for key in set(old)-{'installation','installation_hash'}:assert old[key]==new[key],key
changes=[key for key in old['installation'] if old['installation'][key]!=new['installation'][key]]
assert sorted(changes)==['executable','executable_hash','source_commit']
assert new['installation']==p['installation']
manifest=pathlib.Path(p['manifest']);assert o.pin(manifest)['sha256']=='74ca846daf8f6ad82692b43dcd3b664fe2970247072546495d05519b01358609'
assert read(manifest)==p['installation'] and p['manifest_sha256']=='sha256:'+o.pin(manifest)['sha256']
exe=pathlib.Path(p['installation']['executable']);assert p['installation']['executable_hash']=='sha256:'+o.pin(exe)['sha256']
assert p['installation']['source_commit']=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
handles=[o.openread(D/'coordinator.lock',True)]
conn=None
try:
 for suffix in ['', '-wal','-shm']:handles.append(o.openread(pathlib.Path(str(D/'researchos.sqlite')+suffix)))
 conn=sqlite3.connect((D/'researchos.sqlite').as_uri()+'?mode=ro',uri=True);conn.execute('PRAGMA query_only=ON');conn.execute('BEGIN')
 ownerRoot=conn.execute('SELECT root FROM orchestration_identity WHERE principal=?',(p['owner'],)).fetchone()[0]
 members=[]
 for pid,roles,revoked,create in conn.execute('SELECT id,roles,revoked,can_create_project FROM auth_principals ORDER BY id'):
  if not pid.startswith('local-verifier-'):continue
  _,root,parent=conn.execute('SELECT principal,root,parent FROM orchestration_identity WHERE principal=?',(pid,)).fetchone()
  grants=[{'Project':project,'Task':task,'Run':run,'Restricted':bool(restricted)} for project,task,run,restricted in conn.execute('SELECT project,task,run,restricted FROM auth_grants WHERE principal=? ORDER BY project,task,run,restricted',(pid,))]
  members.append({'Principal':{'ID':pid,'Roles':roles,'Revoked':revoked,'Create':create},'Lineage':{'ID':pid,'Root':root,'Parent':{'String':parent or '', 'Valid':parent is not None}},'Grants':grants})
 lineage=o.digest([ownerRoot,members]);assert lineage==p['lineage_hash'],(lineage,p['lineage_hash'])
 conn.rollback();conn.close();conn=None
finally:
 if conn is not None:conn.rollback();conn.close()
 for h in reversed(handles):o.k.CloseHandle(h)
for ref in fresh['public_files'].values():assert o.pin(pathlib.Path(ref['path']))==ref
result=read(ROOT_E/'01-preflight.result.json');assert result['native_exit']==0
for key in ['stdout_ref','stderr_ref','plan_ref']:assert o.pin(pathlib.Path(result[key]['path']))==result[key]
stdout=read(ROOT_E/'01-preflight.stdout.raw.json')
assert stdout['state']=='PREFLIGHT' and stdout['outcome']=='NOT_APPLIED' and stdout['plan_sha256']=='sha256:'+o.pin(PLAN)['sha256']
o.save(E/'02-preflight-plan-review.json',{'schema':'researchos.independent-actual-preflight-observation/1','at':o.now(),'scope':o.pin(SCOPE),'plan':o.pin(PLAN),'root_preflight_result':o.pin(ROOT_E/'01-preflight.result.json'),'baseline':o.pin(E/'01-baseline.json'),'fresh_observation':o.pin(E/'02-preflight.json'),'unchanged_fields':stable,'plan_binding_checks':'identity/fileIDs/schema/census/state/lineage/raw-old/canonical-old/new/manifest/exe/all verified','lineage_hash_independently_recomputed':lineage,'history_sequence':1,'predecessor_empty_and_actual_journal_absent':True,'installation_changes_exact':changes,'registration_noninstallation_fields_unchanged':True,'result':'NO_DISCREPANCY_OBSERVED','commit_or_recover_performed':False,'signed_acceptance':False,'schema_migration_performed':False,'formal_increment':0})
print(json.dumps(o.pin(E/'02-preflight-plan-review.json'),ensure_ascii=False))
