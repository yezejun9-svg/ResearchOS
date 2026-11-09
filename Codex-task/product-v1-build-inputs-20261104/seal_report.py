"""Seal C-only copy evidence. No further copy/build/GUI/Go invocation."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
assert not (HERE/'MANIFEST.json').exists(),'Existing seal: readback only'
inputs=json.loads((HERE/'INPUTS.json').read_bytes())
expected='e1c316403d5e6614a48ade25ad8169227d39200a30426f213dbec73bcdebde26'
assert sha(HERE/'INPUTS.json')=='87856127688f28e6d3b3cb24addbefbb1b6bfb3630690be8b76085d16113ddff'
for name in ['SOURCE.before.json','SOURCE.after.json','TARGET.readback.json']:assert sha(HERE/name)==expected
assert inputs['all3_equal'] and inputs['files']==365 and inputs['logical_bytes']==45843230
assert not (HERE/'FAILURE.json').exists()
module=json.loads((HERE/'GOMODCACHE-READONLY.json').read_bytes())
assert sum(row['files'] for row in module['module_rows'])==module['source_files']
assert sum(row['bytes'] for row in module['module_rows'])==module['source_logical_bytes']
put('DIAGNOSTICS.json',{'copy_started':'ed2b28','copy_session':59548,'copy_terminal':'c2cf38','actual_copy_exit':0,
    'C_scope_and_journal_registered':'60206a exit0 before any D mkdir',
    'copy_scope_sha256':sha(HERE/'SCOPE.json'),'copy_script_sha256':sha(HERE/'copy_public_web.py'),
    'copy_failed_batches':0,'uncertain_operations':[],'old_cache_explicit_writes_rename_delete':0,
    'Go_readonly_evidence':['71a668','cb0ad5','a11535'],'Go_invocations':0,'Go_module_copy':0,
    'builds':0,'installs':0,'GUI_or_model_calls':0,'Electron_copy':False,'old_user_data_or_credentials_read':0,
    'old_probe_or_scope_replays':0,'failure_counter_reset':False,'formal_increment':0,
    'controller':'Owned controller remains frozen/unchanged; Root approved exact future scopes separately; unnamed top Job, no GUI-driven controller expansion'})
files=[{'path':p.relative_to(HERE).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(HERE.rglob('*'))
       if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST.json']
put('MANIFEST.json',{'schema':'researchos.product-v1-build-inputs-author.v1','status':'WEB_INPUTS_COPIED_HASH_VERIFIED_GO_READONLY_INVENTORY_ONLY',
    'at':datetime.now(timezone.utc).isoformat(),'owner':'codex:/root/runtime_readiness',
    'D_target_root':inputs['target_root'],'web_modules':inputs['web_modules'],'INPUTS_sha256':sha(HERE/'INPUTS.json'),
    'tree_before_after_target_digest':expected,'copied_files':365,'copied_directories':50,'copied_bytes':45843230,
    'Go_module_copies':0,'builds':0,'GUI_or_model_calls':0,'D_source_writes':0,'formal_increment':0,'failure_counter_reset':False,
    'resource_copy_complete':True,'further_copy_permitted':False,'files':files})
print(json.dumps({'manifest_sha256':sha(HERE/'MANIFEST.json'),'INPUTS_sha256':sha(HERE/'INPUTS.json'),
    'files':len(files),'D_web_modules':inputs['web_modules'],'copy_complete':True,'Go_copied':False}))
