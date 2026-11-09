"""Seal verified repair02; no additional build/import/GUI/model operation."""
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
TARGET=Path('D:/作品集/ResearchOS/research-os/.local/product-v1-build-inputs-20261104/web-node_modules-02')
MODULES=TARGET/'node_modules'
OLD=TARGET.parent/'web-node_modules'
LIB=HERE.parent/'copy_public_web.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
assert not (HERE/'INPUTS-02.json').exists(),'Existing seal: inspect, never replay'
spec=importlib.util.spec_from_file_location('_public_tree_readback',LIB);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
copy=json.loads((HERE/'COPY-RESULT.json').read_bytes())
source=json.loads((HERE/'SOURCE.resolution-02.json').read_bytes())
target=json.loads((HERE/'TARGET.resolution.json').read_bytes())
validation=json.loads((HERE/'ENTRY-IMPORT-VALIDATION.json').read_bytes())
run=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-owned-verification-20261104/runs/product-v1-webcache-02-entry-import')
stop=json.loads((run/'RESULT.json').read_bytes())
assert stop['status']=='COMPLETED_OWNED_JOB_STOPPED' and stop['stop_proved'] and stop['root_signaled'] and stop['job_active_zero']
assert stop['errors']==[] and stop['input_drift'] is False
assert validation['status']=='C_OWNED_VITE_ACTUAL_ENTRY_IMPORT_PASSED' and validation['package_count']==18
def identities(graph):return sorted((v['name'],v['version'],v['package_sha256']) for v in graph['nodes'])
assert identities(source)==identities(target)
for pkg in target['nodes']:assert Path(pkg['entry']).is_relative_to(MODULES)
after=lib.tree(MODULES,True);old_after=lib.tree(OLD,True)
assert after==json.loads((HERE/'TARGET.readback.json').read_bytes())
assert old_after==json.loads((HERE/'OLD01.before.json').read_bytes())
lib.save(HERE/'TARGET.after-import.json',after)
assert sha(TARGET.parent/'INPUTS.json')=='87856127688f28e6d3b3cb24addbefbb1b6bfb3630690be8b76085d16113ddff'
result={
    'schema':'researchos.product-v1-public-build-inputs.v2','status':'PHYSICAL_CLOSURE_AND_ACTUAL_VITE_ENTRY_IMPORT_VERIFIED',
    'at':datetime.now(timezone.utc).isoformat(),'origin':'product-v1-webcache-missing-hoisted-rolldown','resource_attempt':2,
    'corrected_diagnosis':'Original packages were present; naming the physical cache root web-node_modules instead of node_modules broke realpath-based sibling package resolution. No extra hoisted packages were missing.',
    'target_root':str(TARGET),'web_modules':str(MODULES),'files':copy['files'],'directories':copy['directories'],
    'logical_bytes':copy['logical_bytes'],'reparse_count':0,'additional_hoisted_packages_copied':0,
    'source_before_sha256':copy['tree_sha256'],'source_after_sha256':copy['source_after_sha256'],
    'target_readback_sha256':copy['target_readback_sha256'],'target_after_actual_import_sha256':sha(HERE/'TARGET.after-import.json'),
    'all_content_trees_equal':True,'resolved_packages':18,'dependency_edges':len(target['edges']),
    'os_cpu_excluded_optional':len(target['excluded']),'actual_Node_platform':target['platform'],'actual_Node_arch':target['arch'],
    'source_resolution_sha256':sha(HERE/'SOURCE.resolution-02.json'),'target_resolution_sha256':sha(HERE/'TARGET.resolution.json'),
    'C_actual_entry_validation_sha256':sha(HERE/'ENTRY-IMPORT-VALIDATION.json'),'C_validation_scope_sha256':stop['scope_sha256'],
    'C_validation_controller_status':stop['status'],'C_validation_stop_proved':True,'C_validation_root_exit_code':stop['root_exit_code'],
    'native_binding_imports':validation['native_binaries'],'D_free_before':copy['D_free_before'],'D_free_after_copy':copy['D_free_after'],
    'required_bytes':copy['required_bytes'],'old01_unchanged':True,'old01_inputs_sha256':copy['old01_inputs_sha256'],
    'source_opened_readonly':True,'physical_copy_only':True,'installs':0,'C_minimal_project_builds':0,
    'D_Desktop_builds':0,'GUI_or_model_calls':0,'network_calls':0,'formal_increment':0,'failure_counter_reset':False}
save(HERE/'INPUTS-02.json',result);save(TARGET/'INPUTS-02.json',result)
assert sha(HERE/'INPUTS-02.json')==sha(TARGET/'INPUTS-02.json')
save(HERE/'DIAGNOSTICS.json',{
    'origin':result['origin'],'origin_name_and_original_failure_preserved':True,
    'root_reported_build01':{'scope':'product-v1-build-01','status':'CHILD_NONZERO_STOPPED','stop_proved':True,
        'failure':'react-build ERR_MODULE_NOT_FOUND rolldown','replayed':False},
    'source_metadata_attempt01':{'started':'c96915','session':82665,'terminal':'47cb10','exit':1,
        'cause':'Resolver assumed every dependency has a runtime entry; @oxc-project/types is types-only. This was an author metadata-harness error, not missing public package bytes.',
        'source_and_raw':'resolve-packages.attempt-01.mjs and SOURCE.resolution.stderr retained'},
    'source_metadata_attempt02':{'terminal':'d4770d','exit':0,'types_only':'Node resolve.paths metadata lookup; no guessed package.json export'},
    'C_scope_journal_before_copy':'d80cd5 exit0','copy02':{'started':'30cde6','session':47473,'terminal':'4cfd9d','exit':0},
    'target_Node_resolution':{'terminal':'e5f469','exit':0},
    'C_actual_entry_import':{'started':'88f8cb','session':43655,'terminal':'61d124','exit':0,
        'owned_scope':'product-v1-webcache-02-entry-import','scope_sha256':stop['scope_sha256'],'stop_proved':True},
    'minimal_vite_check_mjs':'Prepared but not executed; chose actual entry/native import only to keep repair minimal',
    'uncertain_operations':[],'automatic_retries':0,'old_cache_writes':0,'old01_modified':False,
    'Desktop_build01_replay':False,'D_Desktop_builds':0,'GUI_or_model_calls':0,'installs':0,'formal_increment':0,'failure_counter_reset':False})
save(HERE/'README.json',{
    'use_as_web_modules':str(MODULES),'INPUTS02_sha256':sha(HERE/'INPUTS-02.json'),
    'why':'The real cache basename must be node_modules. Do not use preserve-symlinks or copy unrelated ancestor caches to conceal the layout defect.',
    'evidence':'365 physical files,18 actual resolved package roots/19 edges,25 non-Win-x64 optional exclusions; original failing Vite chunk and public index actually imported, ReactDOM/client loaded and both Windows native bindings loaded entirely from new cache.',
    'limits':'Resource import verification only; Root must separately scope bounded full build02. No installer, GUI/model or V1 business acceptance. Old build01 and all failure history remain consumed and unchanged.'})
files=[{'path':p.relative_to(HERE).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(HERE.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST.json']
save(HERE/'MANIFEST.json',{'schema':'researchos.product-v1-web-cache-repair.v2','status':'RESOURCE_REPAIR_VERIFIED_READY_FOR_ROOT_EXPLICIT_BUILD02',
    'origin':result['origin'],'scope_sha256':sha(HERE/'SCOPE.json'),'INPUTS02_sha256':sha(HERE/'INPUTS-02.json'),
    'target_root':str(TARGET),'web_modules':str(MODULES),'source_modification_permitted':False,'resource_copy_complete':True,
    'old01_unchanged':True,'D_Desktop_builds':0,'GUI_or_model_calls':0,'installs':0,'formal_increment':0,'failure_counter_reset':False,
    'files':files})
print(json.dumps({'INPUTS02_sha256':sha(HERE/'INPUTS-02.json'),'manifest_sha256':sha(HERE/'MANIFEST.json'),
    'D_INPUTS02':str(TARGET/'INPUTS-02.json'),'web_modules':str(MODULES),'files':len(files),'actual_entry_import':'PASS','old01_unchanged':True}))
