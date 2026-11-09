import hashlib, json, shutil, subprocess
from pathlib import Path
N=Path(__file__).resolve().parent
ROOT=Path(r'D:/作品集/ResearchOS/research-os')
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):
    p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'sha256':sha(b),'bytes':len(b)}
def save(name,x):
    p=N/name;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return ref(p)
def refs_in(x):
    if isinstance(x,dict):
        if all(k in x for k in ['path','sha256','bytes']):yield x
        for v in x.values():yield from refs_in(v)
    elif isinstance(x,list):
        for v in x:yield from refs_in(v)
inputs={}
for name in ['existing-qualification-refs.json','old22-shared-runtime-source-comparison.json','tool-module-resources.json']:
    for r in refs_in(json.loads((N/name).read_bytes())):inputs[r['path']]=r
checks=[]
for r in inputs.values():
    actual=ref(r['path']);assert actual==r,{'drift':r,'actual':actual};checks.append(actual)
save('input-pins-final-check.json',{'checked_refs':checks,'drift':[],'check_type':'Byte hash recheck; no lifetime read lock claimed','go_executions':0,'private_file_reads':0})
cp=subprocess.run([r'C:/Program Files/Git/cmd/git.exe','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True)
(N/'final-head.stdout.raw').write_bytes(cp.stdout);(N/'final-head.stderr.raw').write_bytes(cp.stderr)
assert cp.returncode==0 and cp.stdout.decode().strip()=='adc460c2138528f163f7fdab5e8d81dde157b7fb'
save('final-head-check.json',{'argv':[r'C:/Program Files/Git/cmd/git.exe','-C',str(ROOT),'rev-parse','HEAD'],'exit':cp.returncode,'stdout_ref':ref(N/'final-head.stdout.raw'),'stderr_ref':ref(N/'final-head.stderr.raw'),'head':cp.stdout.decode().strip()})
summary=json.loads((N/'discovery-summary.json').read_bytes());resources=json.loads((N/'tool-module-resources.json').read_bytes())
effects={'writes_scope':N.as_posix(),'source_resource_reads_only':True,'main_writes':0,'canonical_writes':0,'existing_worktree_writes':0,'Go_executions':0,'Native_product_children':0,'SQL_queries':0,'model_requests':0,'dispatcher_calls':0,'active_TP':False,'runtime_grant':False,'private_key_owner_credential_reads':0,'formal_case_increment':0,'old22_rerun':False,'Development13_rerun':False}
opens=[{'branch':'OLD21_ONLY','id':name,'status':'OPEN'} for name in ['REAL_GO_DEPENDENCY_AND_MODULE_CONTENT_CLOSURE','INDEPENDENT_OLD21_CONTROL_BACKUP_BUILD_AND_QUALIFICATION','PUBLIC_BOOTSTRAP_BACKUP_RESTORE_NATIVE_OBSERVATION','ACTUAL_DATABASE_SCHEMA_AND_21_TO22_HANDOFF','HISTORICAL_FORMAL_RELEASE_OR_OLD21_CASE']]
report={'schema':'researchos.schema21-original-source-resource-discovery.v1','actor':'codex:/root/native_temp_independent_review','status':'SOURCE_RESOURCES_IDENTIFIED_PENDING_ROOT_INDEPENDENT_BUILD','recommended_source':{'repository':ROOT.as_posix(),'commit':summary['recommended_commit'],'tree':summary['tree'],'numbered_schema_max':21,'public_startup_installs_original_session_addon':True},'summary':summary,'source_inventory_ref':ref(N/'source-object-inventory.json'),'build_input_scope_ref':ref(N/'root-build-input-scope.json'),'tool_module_resources_ref':ref(N/'tool-module-resources.json'),'prior_qualification_refs_ref':ref(N/'existing-qualification-refs.json'),'prior_metadata_checks_ref':ref(N/'selected-prior-metadata-checks.json'),'old22_shared_runtime_comparison_ref':ref(N/'old22-shared-runtime-source-comparison.json'),'report_markdown_ref':ref(N/'DISCOVERY-REPORT.md'),'actual_tool_capture_index_ref':ref(N/'actual-discovery-capture-index.json'),'git_actual_commands_ref':ref(N/'git-commands.actual.json'),'input_pin_check_ref':ref(N/'input-pins-final-check.json'),'final_head_check_ref':ref(N/'final-head-check.json'),'module_expanded_present':resources['all_expanded_present'],'zip_missing_count':sum(not x['zip_present'] for x in resources['modules']),'ziphash_mismatches':[x['module'] for x in resources['modules'] if x['ziphash_matches_go_sum'] is False],'disk_free_bytes_observed':shutil.disk_usage(ROOT).free,'effects':effects,'branch_local_open_inputs':opens,'mechanical_failures_this_task':[],'program_qualification':False,'formal_old21_case':False,'independent_source_acceptance':False,'runtime_authorization':False}
save('discovery-report.json',report)
members=[ref(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json')]
assert all(Path(x['path']).is_relative_to(N) for x in members)
mf=save('MF.json',{'schema':'researchos.schema21-original-resource-discovery-manifest.v1','members':members,'external_inputs_ref':ref(N/'input-pins-final-check.json'),'scope':N.as_posix()})
hdf=save('HDF.json',{'schema':'researchos.schema21-original-resource-discovery-handoff.v1','actor':'codex:/root/native_temp_independent_review','status':report['status'],'manifest_ref':mf,'report_ref':ref(N/'discovery-report.json'),'source_inventory_ref':ref(N/'source-object-inventory.json'),'root_build_input_scope_ref':ref(N/'root-build-input-scope.json'),'recommended_commit':summary['recommended_commit'],'recommended_tree':summary['tree'],'effects':effects,'branch_local_open_inputs':opens,'Root_next':'Review exact original source objects, then independently materialize and build old21 control/backup inside a new Root-owned scope. This package grants no Go/Native/TP runtime authority.','no_program_or_formal_case_qualification':True})
for r in members:assert ref(r['path'])==r
assert ref(N/'MF.json')==mf
print(json.dumps({'HDF':hdf,'MF':mf,'report':ref(N/'discovery-report.json'),'build_scope':ref(N/'root-build-input-scope.json'),'source_inventory':ref(N/'source-object-inventory.json'),'members_verified':len(members),'external_input_refs_rechecked':len(checks),'seal_outer_expected':0},ensure_ascii=False))
