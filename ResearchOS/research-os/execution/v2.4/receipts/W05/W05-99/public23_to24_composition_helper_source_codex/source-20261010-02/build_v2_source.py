import ast,hashlib,json,os
from pathlib import Path
O=Path(__file__).resolve().parent
OLD=O.parent/'source-20261010-01/compose_main24.source.py'
raw=OLD.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e2e70ce36c9bfd473bb24c5d23aa18e2e9da238cab77f5b98a26e4970854e373'
original=raw.decode()
gates=(O/'v2_gate_additions.py.txt').read_text(encoding='utf-8')+(O/'v2_authority_additions.py.txt').read_text(encoding='utf-8')
patches=[
("def input_bundle(request_ref):",gates+"\ndef input_bundle(request_ref):"),
("need(set(req) == {'schema','actor_id','repo_root','project_identity_ref','source_helper_ref','merge_map_ref','native_revision','output_directory'}, 'REQUEST_FIELDS')",
 "need(set(req) == {'schema','actor_id','repo_root','project_identity_ref','source_helper_ref','merge_map_ref','native_revision','output_directory','git_baseline_ref','prepare_scope_ref','prepare_audit_ref','source_package_hdf_ref','source_package_mf_ref','source_contract_ref'}, 'REQUEST_FIELDS')"),
("req['schema'] == 'researchos.main24-compose-request.v1'","req['schema'] == 'researchos.main24-compose-request.v2'"),
("    return req, rows, edits, refs, out\n","    validate_source_package(req,refs)\n    verify_prepare_authority(req,refs)\n    verify_git_baseline(req,refs)\n    return req, rows, edits, refs, out\n"),
("    preflight(rows, edits)\n    prepared = dict(","    preflight(rows, edits)\n    verify_prepare_authority(req,refs)\n    verify_git_baseline(req)\n    prepared = dict("),
("need(set(grant)=={'schema','issued_by','project_id','operation_id','source_helper_ref','prepared_ref','independent_source_review_ref','root_authorization_observation_ref','target_paths','issued_at','expires_at'},'GRANT_FIELDS')",
 "need(set(grant)=={'schema','issued_by','project_id','operation_id','source_helper_ref','prepared_ref','independent_source_review_ref','root_authorization_observation_ref','target_paths','issued_at','expires_at','source_review_audit_ref','root_authorization_audit_ref','independent_source_review_hdf_ref','independent_source_review_mf_ref'},'GRANT_FIELDS')"),
("grant['schema']=='researchos.root-main24-composition-grant.v1'","grant['schema']=='researchos.root-main24-composition-grant.v2'"),
("    # These are externally verified Root evidence inputs, not cryptographic actor authentication.\n",
 "    # V2 verifies canonical original audit bytes, typed Root observation and exact independent approval.\n    verify_apply_authority(grant,req,prepared,prepared_ref,refs)\n"),
("        with serial_apply_lock():\n            # All ten",
 "        with serial_apply_lock():\n            # Recheck actual authority while all immutable proof dependencies are held.\n            verify_prepare_authority(req,refs)\n            verify_apply_authority(grant,req,prepared,prepared_ref,refs)\n            # All ten"),
("            originals,desired,inverse=preflight(rows,edits,handles)\n",
 "            originals,desired,inverse=preflight(rows,edits,handles)\n            verify_git_baseline(req)\n"),
]
result=original;records=[]
for number,(old,new) in enumerate(patches,1):
 assert result.count(old)==1,('PATCH_NOT_UNIQUE',number,result.count(old))
 result=result.replace(old,new,1)
 records.append(dict(number=number,old=old,new=new))
restored=result
for old,new in reversed(patches):
 assert restored.count(new)==1
 restored=restored.replace(new,old,1)
assert restored.encode()==raw
ast.parse(result)
def save(name,content):
 p=O/name
 with p.open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
 return dict(path=str(p),sha256=hashlib.sha256(content).hexdigest(),bytes=len(content))
ref=save('compose_main24.source.py',result.encode())
proof=dict(schema='researchos.main24-helper-v2-source-inverse.v1',base_ref=dict(path=str(OLD),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)),v2_ref=ref,patches=records,patch_count=len(records),complete_inverse_equals_v1_raw=True,base_operations_preserved=True,prepare_apply_executed=False,old_14_controls_replayed=0)
proofref=save('source-inverse.json',(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(source_ref=ref,inverse_ref=proofref,patch_count=len(patches),AST_parse='PASS',Main_Canon_writes=0),ensure_ascii=True))

