import sys
sys.dont_write_bytecode=True
import observe_actual as o
import pathlib,json,base64,datetime
E=o.E
P=o.R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_actual_root_codex/20261015-current-chat/replacement-plan-01.json'
p=json.loads(P.read_text(encoding='utf-8'))
acl=json.loads((E/'02-preflight-plan-acl.json').read_text(encoding='utf-8'))
sid=acl['rows'][0]['current_sid'];ref='windows_sid:'+o.sha(('WINDOWS_SID|'+sid).encode())[:16]
assert p['principal_ref']==ref
datetime.datetime.fromisoformat(p['created_at'].replace('Z','+00:00'))
old=json.loads(base64.b64decode(p['old_record_bytes']))
new={key:old[key] for key in ['schema','owner_host','owner_principal','service_root']}
new['installation_hash']=p['installation_hash']
new['installation']={key:p['installation'][key] for key in ['schema','service_id','protocol','executable','executable_hash','source_commit','arguments']}
expected=json.dumps(new,ensure_ascii=False,indent=2).encode()
assert expected==base64.b64decode(p['new_record_bytes'])
ids=[]
for path in [P,pathlib.Path(p['manifest']),pathlib.Path(p['installation']['executable'])]:
 h=o.openread(path)
 try:
  identity=o.fileid(h);assert identity['links']==1
  for parent in path.parents:assert not parent.lstat().st_file_attributes&0x400
  ids.append({'path':str(path),'identity':identity,'all_parent_paths_nonreparse':True})
 finally:o.k.CloseHandle(h)
arch=o.R/'execution/v2.4/receipts/W05/W05-99/coding_qualification_rejection_diagnosis_codex/20261014-current-chat/replacement-architecture/ARCHITECTURE.md'
assert o.pin(arch)['sha256']=='66b0023d91a53827cbccbf5cbc58010224d69969c17a59e1365cd4f4d11c13cc'
assert 'SQLite WAL/SHM 的文件系统行为应单列观察' in arch.read_text(encoding='utf-8')
o.save(E/'02-preflight-additional-checks.json',{'at':o.now(),'fresh_native_sid_reference_matches':True,'principal_ref':ref,'created_at_RFC3339_parse':True,'exact_new_record_bytes_reconstructed_in_frozen_Go_struct_field_order':True,'plan_manifest_exe_file_id_checks':ids,'strict_plan_manifest_exe_acl_receipt':o.pin(E/'02-preflight-plan-acl.json'),'architecture':o.pin(arch),'architecture_line':74,'observed_shm_change_requires_separate_observation':True,'old_shm_raw_bytes_not_preserved':True,'specific_shm_offset_or_readmark_cause_not_claimed':True,'signed_acceptance':False,'formal_increment':0})
print(json.dumps(o.pin(E/'02-preflight-additional-checks.json'),ensure_ascii=False))
