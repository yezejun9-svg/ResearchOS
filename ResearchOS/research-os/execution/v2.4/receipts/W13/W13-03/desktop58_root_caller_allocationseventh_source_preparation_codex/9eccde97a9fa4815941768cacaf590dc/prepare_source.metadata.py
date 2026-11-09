import sys, json, hashlib, ast
from pathlib import Path
sys.dont_write_bytecode=True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=Path(__file__).resolve().parent
def pin(p):
    p=Path(p)
    b=p.read_bytes()
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def checked(r):
    p=Path(r['path'])
    if not p.is_absolute(): p=ROOT/p
    b=p.read_bytes()
    assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
    return b
def save(name,value):
    with (BASE/name).open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
original=json.loads((BASE/'original-input.json').read_bytes())
assert original['actor']=='codex:/root' and original['expected_source_only'] is True
old=checked(original['base_source_ref'])
new_path=BASE/'root-launch-once.desktop58.allocatedseventh.proposed.py'
new=new_path.read_bytes()
old_uid='b4d53db07f1e4ab8b9c0b37e291a6da5'
new_uid='9eccde97a9fa4815941768cacaf590dc'
old_out='d8a016ddc71e440fb386a11957c098ea'
new_out='fd6fec9e9d2a482d98203421ac21a82b'
text=old.decode('utf-8')
assert text.count(old_uid)==3 and text.count(old_out)==1 and text.count('desktop58-finite169-go3-r337-')==1
expected=text.replace(old_uid,new_uid).replace(old_out,new_out).replace('desktop58-finite169-go3-r337-','desktop58-finite169-go3-r339-').encode('utf-8')
assert new==expected and len(new)==7393
inverse=new.decode('utf-8').replace(new_uid,old_uid).replace(new_out,old_out).replace('desktop58-finite169-go3-r339-','desktop58-finite169-go3-r337-').encode('utf-8')
assert inverse==old
old_ast=ast.parse(old); new_ast=ast.parse(new); inv_ast=ast.parse(inverse)
assert ast.dump(old_ast,include_attributes=False)==ast.dump(inv_ast,include_attributes=False)
old_functions={x.name:ast.dump(x,include_attributes=False) for x in old_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
new_functions={x.name:ast.dump(x,include_attributes=False) for x in new_ast.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert old_functions==new_functions
compile(new,str(new_path),'exec')
scope=json.loads(checked(original['actual_scope_ref']))
a=original['allocation']
assert a['future_before']==[338,166,635] and a['future_after']==[339,167,645] and a['uid']==new_uid
assert scope['run_uuid']==new_uid and scope['registration_namespace']==a['registry_rel']
assert scope['inner_seconds']==7200 and scope['outer_seconds']==7500 and scope['builder_seconds']==1800
assert scope['controller_evidence_reserve_seconds']==60 and scope['launcher_evidence_reserve_seconds']==60 and scope['cleanup_seconds']==5
caller_out=ROOT/a['caller_out_rel']
roots=[Path(scope[k]) for k in ('output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root')]+[caller_out]
assert len(set(roots))==6 and all(p.is_absolute() and not p.exists() for p in roots)
assert all(not x.is_relative_to(y) for x in roots for y in roots if x!=y)
audit={'schema':'researchos.desktop58-root-caller-source-preparation-audit.v1','actor':'codex:/root','decision':'SOURCE_PREPARED_FOR_INDEPENDENT_REVIEW_ONLY','base_source_ref':original['base_source_ref'],'proposed_source_ref':pin(new_path),'actual_scope_ref':original['actual_scope_ref'],'original_input_ref':pin(BASE/'original-input.json'),'metadata_source_ref':pin(__file__),'literal_changes':{'uuid_occurrences':3,'caller_output_occurrences':1,'registration_revision_occurrences':1},'all_bytes_full_inverse_equal':True,'all_module_ast_full_inverse_equal':True,'unchanged_functions':list(old_functions),'all_execution_and_caller_leaves_absent':True,'budgets':{'caller_timeout_seconds':7800,'launcher_outer_seconds':7500,'controller_inner_seconds':7200,'builder_seconds':1800,'controller_evidence_reserve_seconds':60,'launcher_evidence_reserve_seconds':60,'cleanup_seconds':5},'scope_build_actual_outer_exit':0,'scope_build_actual_python_exit':0,'product_native_calls':0,'SDK_model_calls':0,'canonical_writes':0,'caller_executed':False,'automatic_retry':False,'counter_reset':False,'formal_increment':0}
save('audit.json',audit)
members=[pin(BASE/n) for n in ('root-launch-once.desktop58.allocatedseventh.proposed.py','prepare_source.metadata.py','original-input.json','audit.json')]
save('manifest.json',{'schema':'researchos.desktop58-root-caller-source-preparation-manifest.v1','actor':'codex:/root','members':members,'immutable_external_inputs':[original['base_source_ref'],original['actual_scope_ref']],'execution_authorized':False,'formal_increment':0})
save('handoff.json',{'schema':'researchos.desktop58-root-caller-source-preparation-handoff.v1','actor':'codex:/root','decision':'SOURCE_PREPARED_FOR_INDEPENDENT_REVIEW_ONLY','proposed_source_ref':pin(new_path),'audit_ref':pin(BASE/'audit.json'),'manifest_ref':pin(BASE/'manifest.json'),'original_input_ref':pin(BASE/'original-input.json'),'scope_ref':original['actual_scope_ref'],'next_required_reviewer':'codex:/root/w05_merge_review','canonical_writes':0,'caller_executed':False,'execution_authorized':False,'formal_increment':0})
print(json.dumps({'source_ref':pin(new_path),'audit_ref':pin(BASE/'audit.json'),'manifest_ref':pin(BASE/'manifest.json'),'handoff_ref':pin(BASE/'handoff.json'),'metadata_source_ref':pin(__file__),'unchanged_function_count':len(old_functions),'actual_product_native_calls':0,'actual_canonical_writes':0},ensure_ascii=True))
