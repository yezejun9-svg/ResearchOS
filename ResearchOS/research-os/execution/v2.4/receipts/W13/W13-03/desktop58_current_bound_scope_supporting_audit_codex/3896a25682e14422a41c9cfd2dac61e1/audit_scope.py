import sys
sys.dont_write_bytecode=True
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import re
import time
ROOT=Path('D:/作品集/ResearchOS/research-os')
REG=ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r336-dc4fe023ed714e74b8d3692b504cf55d'
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_current_bound_scope_supporting_audit_codex/3896a25682e14422a41c9cfd2dac61e1")
ACTOR='codex:/root/f08_whole_scope_review'
SCOPE_SHA='86d77dd84af6557c4f956d8c39e0aba3d2858de526bb6c1ff8aeb178c85469bc'
HEAD='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
PARENT='a510dbef4a7e08fb5c428df44c39b133f3ffa856'
UID='dc4fe023ed714e74b8d3692b504cf55d'
checks=[]
inputs={}
def check(name,ok,detail=None):
    checks.append({'name':name,'ok':bool(ok),'detail':detail})
def path(value):
    p=Path(value)
    return p if p.is_absolute() else ROOT/p
def digest(p):
    h=hashlib.sha256()
    size=0
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block);size+=len(block)
    return h.hexdigest(),size
def reference(p):
    sha,size=digest(p)
    return {'path':str(p),'sha256':sha,'bytes':size}
def verify(r,tag=None):
    p=path(r['path']);actual=reference(p)
    check('pin:'+str(tag or r['path']),actual['sha256']==r['sha256'] and actual['bytes']==r['bytes'])
    if tag:inputs[tag]={'serialized_ref':r,'actual_ref':actual}
    return p
def doc(r,tag=None):
    return json.loads(verify(r,tag).read_bytes())
def named(name):
    p=REG/name;ref=reference(p);inputs[name]={'actual_ref':ref};return json.loads(p.read_bytes())
def put(name,value):
    p=BASE/name
    with p.open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return reference(p)
scope=named('scope_registration.json')
check('scope_exact_root_pin',inputs['scope_registration.json']['actual_ref']['sha256']==SCOPE_SHA and inputs['scope_registration.json']['actual_ref']['bytes']==25595)
binding=named('binding.pre-review.json')
root_inputs=named('root-inputs.desktop58.pre-review.json')
check('binding_exact_root_pin',inputs['binding.pre-review.json']['actual_ref']['sha256']=='480143d387c385c1f808f6c4b84a9f3e23133dad2a751cf51efc5ad1e52f7c0e')
check('inputs_exact_root_pin',inputs['root-inputs.desktop58.pre-review.json']['actual_ref']['sha256']=='f49fadd98d1eac1037507deee61617669848d4e2bc2638c477ab1021aef9f617')
root_ref_keys=[k for k in root_inputs if k.endswith('_ref')]
for key in root_ref_keys:verify(root_inputs[key],'root-input:'+key)
check('eleven_root_input_refs',len(root_ref_keys)==11,root_ref_keys)
template=doc(binding['scope_template_ref'],'template')
projected=copy.deepcopy(template)
mapping={'output_root':'new_output_root','outer_output_root':'new_wrapper_root','export_root':'new_export_root',
'new_authorization_root':'new_authorization_root','new_grant_preflight_root':'new_grant_preflight_root',
'current_source_authority_ref':'current43_authority_ref','authorization_verifier_ref':'authorization_gate_ref',
'controller_ref':'runner_ref','owned_helper_ref':'owned_process_helper_ref','debug_helper_ref':'debug_tree_helper_ref'}
check('preparation_template_flags',template['preparation_only'] is True and template['execution_authorized'] is False)
for key,src in mapping.items():projected[key]=binding[src]
for key in ('run_uuid','registration_namespace','runtime_resources_ref','compiler_resources_ref','controller_review_path','main_git','public_environment','launcher_ref','utility_ref','toolchain_lock_ref'):
    projected[key]=binding[key]
projected.update(binding['desktop_scope_values'])
projected.update(preparation_only=False,execution_authorized=True,expected_before_registration=binding['before'],
expected_registration=binding['after'],registration_metadata_paths=['execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json'])
basis=('scope_template_ref','runtime_resources_ref','compiler_resources_ref','current43_authority_ref','origin_cut_ref','canonical_before_ref','source_inputs_ref','failure_prefix430_ref')
projected['Root_metadata_binding_inputs']={'refs':{key:binding[key] for key in basis},'metadata_code_refs':copy.deepcopy(binding['metadata_code_refs'])}
check('whole_scope_independent_projection_exact',projected==scope)
check('eight_basis_refs_exact',scope['Root_metadata_binding_inputs']['refs']=={key:binding[key] for key in basis})
check('metadata8_exact',scope['Root_metadata_binding_inputs']['metadata_code_refs']==binding['metadata_code_refs'] and len(binding['metadata_code_refs'])==8)
for key in basis:check('basis_root_q:'+key,binding[key]==root_inputs[key])
code=doc(root_inputs['metadata_code_refs_ref'],'metadata8-source')['entries']
check('metadata8_root_q_exact',code==binding['metadata_code_refs'])
for row in code:verify(row,'metadata-code:'+Path(row['path']).name)
check('null_pre_review_only',binding['controller_review_ref'] is None and root_inputs['controller_review_ref'] is None)
check('actor_head_parent',scope['owner']=='codex:/root' and scope['source_commit']==HEAD and scope['source_parent']==PARENT)
check('relative_registration_exact',scope['registration_namespace']==REG.relative_to(ROOT).as_posix() and binding['registration_namespace']==scope['registration_namespace'])
check('run_uid_all_exact',scope['run_uuid']==binding['run_uuid']==root_inputs['run_uuid']==UID)
before=[335,163,580];after=[336,164,603]
check('typed_fixed_tuple',all(type(v) is int and v>=0 for v in before+after) and scope['expected_before_registration']==binding['before']==root_inputs['before']==before and scope['expected_registration']==binding['after']==root_inputs['after']==after)
check('public_env5_exact',scope['public_environment']==binding['public_environment']==root_inputs['public_environment'] and set(scope['public_environment'])=={'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'})
check('python_flags_exact',scope['python_flags']==binding['python_flags']==['-I','-S','-X','utf8'])
for key in [k for k in scope if k.endswith('_ref')]:verify(scope[key],'scope:'+key)
catalog=doc(scope['resource_catalog_ref'],'catalog')
compiler=doc(scope['compiler_resources_ref'],'compiler')
runtime=doc(scope['runtime_resources_ref'],'runtime')
source=doc(scope['source_catalog_ref'],'public-source')
source_inputs=doc(root_inputs['source_inputs_ref'],'source-input-files')
check('source_identity_census',source['commit']==source_inputs['source_commit']==HEAD and source['file_count']==len(source['files'])==639 and source['all_platform_Go_count']==559)
check('sourceinputs_639',source_inputs['count']==len(source_inputs['files'])==639 and source_inputs['catalog_ref']==scope['source_catalog_ref'])
source_map={}
source_bytes=0
for item in source['files']:
    p=ROOT/item['path'];sha,size=digest(p);source_bytes+=size
    check('Main-source-sha:'+item['path'],sha==item['sha256'] and size==item['bytes'])
    h=hashlib.sha1();h.update(('blob '+str(size)+'\0').encode('ascii'))
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    check('Main-source-GitBlob:'+item['path'],h.hexdigest()==item['git_blob'])
    source_map[os.path.normcase(str(p.resolve()))]={'path':str(p.resolve()),'sha256':sha,'bytes':size}
check('Source_input_rows_exact', {os.path.normcase(str(path(r['path']).resolve())):(r['sha256'],r['bytes']) for r in source_inputs['files']}=={k:(v['sha256'],v['bytes']) for k,v in source_map.items()})
expected={}
conflicts=[]
def merge(rows,label):
    for row in rows:
        p=path(row['path']);key=os.path.normcase(str(p.resolve()))
        check('closed-ref-shape:'+label+':'+str(p),set(row)=={'path','sha256','bytes'} and type(row['bytes']) is int and row['bytes']>=0 and p.is_absolute())
        value=(row['sha256'],row['bytes'])
        if key in expected and expected[key]!=value:conflicts.append({'path':str(p),'label':label})
        expected[key]=value
merge(list(source_map.values()),'source')
merge(compiler['files'],'compiler')
merge(runtime['files'],'runtime')
catalog_rows=catalog['files'];catalog_keys=[os.path.normcase(str(path(r['path']).resolve())) for r in catalog_rows]
catalog_map={k:(r['sha256'],r['bytes']) for k,r in zip(catalog_keys,catalog_rows)}
check('catalog_no_duplicates',len(catalog_keys)==len(set(catalog_keys)))
check('union_no_conflicting_refs',not conflicts,conflicts)
check('catalog_exact_union',catalog_map==expected and len(catalog_rows)==23868)
check('catalog_counts',len(compiler['files'])==22138 and len(runtime['files'])==1297 and len(catalog['images'])==16)
check('catalog_bindings',catalog['runtime_resources_ref']==scope['runtime_resources_ref'] and catalog['compiler_resources_ref']==scope['compiler_resources_ref'])
check('catalog_static_not_authority',catalog['complete_public_roots_frozen'] is True and catalog['actual_runtime_closure_verified'] is False and catalog['preparation_only'] is True and catalog['execution_authorized'] is False and catalog['source_acceptance'] is False and catalog['formal_increment']==0)
resource_rows=[];total_bytes=0
for index,row in enumerate(catalog_rows):
    p=path(row['path']);st=p.stat();sha,size=digest(p);total_bytes+=size
    ok=sha==row['sha256'] and size==row['bytes']
    reparse=bool(getattr(st,'st_file_attributes',0)&1024)
    check('actual-resource:'+str(p),ok and not reparse)
    resource_rows.append({'path':str(p),'sha256':sha,'bytes':size,'match':ok,'reparse':reparse})
    if (index+1)%8000==0:print('RESOURCE_HASH_PROGRESS='+str(index+1),flush=True)
def physical_members(root):
    members=set();reparse=[]
    def fail(error):raise error
    for dirname,dirs,files in os.walk(root,followlinks=False,onerror=fail):
        dp=Path(dirname)
        if getattr(dp.stat(),'st_file_attributes',0)&1024:reparse.append(str(dp))
        for name in dirs:
            p=dp/name
            if getattr(p.stat(),'st_file_attributes',0)&1024:reparse.append(str(p))
        for name in files:
            p=dp/name
            if getattr(p.stat(),'st_file_attributes',0)&1024:reparse.append(str(p))
            members.add(os.path.normcase(str(p.resolve())))
    return members,reparse
membership=doc(catalog['root_membership_ref'],'actual-root-membership')
root_checks=[]
roots=[(Path(item['path']),{os.path.normcase(str(path(row['path']).resolve())) for row in item['files']}) for item in compiler['complete_public_roots']]
for key in ['electron_dist','web_modules']:
    declared=membership['membership'][key];p=Path(declared['root'])
    roots.append((p,{k for k in catalog_map if path(k).is_relative_to(p)}))
for root,declared in roots:
    actual,reparse=physical_members(root)
    result={'root':str(root),'actual_count':len(actual),'expected_count':len(declared),'missing':sorted(declared-actual),'extra':sorted(actual-declared),'reparse':reparse}
    root_checks.append(result)
    check('complete-membership:'+str(root),not result['missing'] and not result['extra'] and not reparse,result)
check('fourteen_public_roots',len(root_checks)==14)
check('membership_75_356',root_checks[-2]['actual_count']==75 and root_checks[-1]['actual_count']==356)
for rootrow in membership['membership']['compiler_roots']+[membership['membership']['electron_dist'],membership['membership']['web_modules']]:
    actual=next((v for v in root_checks if Path(v['root'])==Path(rootrow['root'])),None)
    check('root_producer_membership:'+rootrow['root'],actual is not None and rootrow['member_count']==rootrow['matched_expected_count']==actual['actual_count'] and not rootrow['missing'] and not rootrow['extra'])
for row in catalog['images']:
    key=os.path.normcase(str(path(row['path']).resolve()))
    check('image_pin_membership:'+row['path'],catalog_map.get(key)==(row['sha256'],row['bytes']))
for key,row in catalog['tools'].items():
    check('tool_pin_membership:'+key,catalog_map.get(os.path.normcase(str(path(row['path']).resolve())))==(row['sha256'],row['bytes']))
overlay=runtime['desktop58_overlay']
check('runtime_metadata8_current',overlay['metadata8_refs']==binding['metadata_code_refs'])
check('no_cli8_inheritance',overlay['old_CLI_metadata8_inherited'] is False and overlay['actual_case_acceptance'] is False)
for row in overlay['metadata8_refs']+overlay['six_runtime_controller_refs']:
    check('runtime_controller_pin:'+row['path'],expected.get(os.path.normcase(str(path(row['path']).resolve())))==(row['sha256'],row['bytes']))
wldp=overlay['Windows_Wldp_static_ref']
check('wldp_static_only',wldp['path']=='C:\\Windows\\System32\\wldp.dll' and wldp['sha256']=='ecf34c9c64b2e6be9f622f0ca3a6ca7b95dcfdb88eb0419b045b853934bae0ba' and wldp['bytes']==443664 and overlay['Windows_Wldp_actual_loaded_proven'] is False)
verify(wldp,'wldp-current')
wldp_evidence=doc(overlay['Windows_Wldp_static_evidence_ref'],'wldp-source-evidence')
parameters=named('root-construction.parameters.desktop58.json')
wldp_review=doc(parameters['wldp_candidate_report_ref'],'wldp-independent-review')
check('wldp_independent_current_ref',inputs['wldp-independent-review']['actual_ref']['sha256'].startswith('c516a') and inputs['wldp-independent-review']['actual_ref']['bytes']==3664)
aliases=doc(scope['alias_roster_ref'],'alias-roster')
declarations=scope['negative_alias_declarations'];alias_matrix=[]
for row,decl in zip(aliases['rows'],declarations):
    expected_path=Path(scope['export_root'])/'.local'/'desktop-wire-negative'/(UID+'-'+str(row['allocation_ordinal']).zfill(2))/'resources'/'client-wire'/'researchos-client-wire-validator.exe'
    ok=decl['case_name']==row['name'] and decl['mode']==row['mode'] and decl['allocation_ordinal']==row['allocation_ordinal'] and Path(decl['path'])==expected_path and decl['max_creates']==row['expected_image_creates']
    check('alias-declaration:'+row['name'],ok)
    alias_matrix.append({'case':row['name'],'ordinal':row['allocation_ordinal'],'path':str(expected_path),'max_creates':decl['max_creates'],'mode':row['mode'],'match':ok})
check('alias20_exact_census',len(aliases['rows'])==len(declarations)==20 and aliases['count']==20 and [r['allocation_ordinal'] for r in aliases['rows']]==list(range(20)))
check('alias15_exec16_create',sum(r['max_creates']>0 for r in declarations)==15 and sum(r['max_creates'] for r in declarations)==16)
check('negative_setup_unchanged',aliases['original_setup_copy_mkdir_wx_preserved'] is True and aliases['prebuild_clones'] is False and aliases['all_NOT_RUN'] is True)
instrument=verify(scope['instrumented_test_ref'],'instrumentation').read_bytes()
alias_edits=doc(scope['alias_edits_ref'],'instrumentation-edits')
restored=instrument
for edit in reversed(alias_edits):
    new=edit['new'].encode('utf-8');old=edit['old'].encode('utf-8')
    check('instrumentation_edit_exact_once',restored.count(new)==1)
    restored=restored.replace(new,old,1)
roster=doc(scope['roster_ref'],'finite-roster')
original=roster['original']
# The frozen original is a receipt reference, not a guessed Main path.
original_path=verify(original,'original-instrumented-input')
check('instrumentation_inverse',restored==original_path.read_bytes())
check('finite_162_plus7_plusGo3',len(roster['leaves'])==162 and len(roster['regressions'])==7 and len(roster['go_units'])==3)
qualification=doc(scope['current58_CLI2_qualification_ref'],'CLI2-qualified')
cli_review=doc(scope['current58_CLI2_review_ref'],'CLI2-review')
cli_manifest=doc(scope['current58_CLI2_manifest_ref'],'CLI2-manifest')
check('CLI2_current58',qualification['source_commit']==HEAD and qualification['unique_combined_source_paths']==58 and qualification['current58_fresh_held2_qualified'] is True and qualification['qualified_case_count']==2)
check('CLI2_two_actual_cases',qualification['qualified_case_ids']==['real-existing-open-readonly','real-existing-self-send'] and qualification['native_calls']==qualification['native_calls_exit0']==14 and qualification['cases_NOT_RUN']==[])
check('CLI2_not_desktop_grant',qualification['desktop169_new_scope_preparation_permitted'] is True and qualification['desktop169_execution_authorized'] is False and qualification['whole58_test_suite_qualified'] is False and qualification['source_acceptance'] is False and qualification['formal_increment']==0)
canonical=doc(binding['canonical_before_ref'],'canonical-four-before')['entries']
canonical_results=[]
for item in canonical:
    frozen=verify(item['ref'],'canonical-copy:'+item['canonical_path']).read_bytes();current=(ROOT/item['canonical_path']).read_bytes()
    check('four-canonical-live-equal:'+item['canonical_path'],frozen==current)
    canonical_results.append({'canonical_path':item['canonical_path'],'ref':item['ref'],'live_equal':frozen==current})
cp=json.loads(path(canonical[0]['ref']['path']).read_bytes());ow=json.loads(path(canonical[1]['ref']['path']).read_bytes())
check('canonical_before_tuple',cp['revision']==335 and ow['revision']==163 and len(cp['failure_counters'])==580)
prefix=doc(binding['failure_prefix430_ref'],'original-prefix430')
check('prefix430_exact',prefix['actual_origin_count']==430 and cp['failure_counters'][:430]==prefix['failure_counters'])
cut=doc(binding['origin_cut_ref'],'fixed-origin-cut')
check('fixed23_tuples',cut['before']==before and cut['after']==after and len(cut['origins'])==23 and cut['counter_reset'] is False)
origin_keys=[]
for row in cut['origins']:
    actual=json.loads(verify(row['evidence_ref'],'cut-origin:'+row['origin_key']).read_bytes())
    check('original-cut-payload:'+row['origin_key'],actual==row['original_payload'] and row['counted_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False)
    origin_keys.append(row['origin_key'])
check('cut_origin_unique',len(origin_keys)==len(set(origin_keys)))
leaves=[scope[k] for k in ['output_root','outer_output_root','export_root','new_authorization_root','new_grant_preflight_root']]
leaf_results=[{'path':str(path(value)),'exists':path(value).exists()} for value in leaves]
check('five_future_leaves_absent',not any(v['exists'] for v in leaf_results))
expected_limits={'inner_seconds':7200,'outer_seconds':7500,'builder_seconds':1800,'node_cases':169,'Go_top_cases':3,'native_top_command_cap':176,'loopback_HTTP_max':390,'offscreen_Electron_controls':2,'installed_visible_GUI_calls':0,'SDK_model_external_paid_calls':0,'process_cap':2048,'active_job_processes':16,'image_cap':64,'cleanup_seconds':5,'controller_evidence_reserve_seconds':60,'launcher_evidence_reserve_seconds':60}
for key,value in expected_limits.items():check('finite-limit:'+key,type(scope[key]) is int and scope[key]==value)
check('no_retry_reset_acceptance',scope['first_unexpected_stop'] is True and scope['automatic_retry'] is False and scope['counter_reset'] is False and scope['source_acceptance'] is False and scope['formal_increment']==0)
check('three_runtime_phase_paths',scope['expected_runtime_observation_paths']==[str(Path(scope['new_authorization_root'])/(stage+'.json')) for stage in ['admission.runtime','grant-final.runtime','grant-final.runtime.after']] and [v['path'] for v in scope['runtime_observation_phases']]==scope['expected_runtime_observation_paths'])
caller_ref={'path':str(ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocationdc4f_independent_source_review_codex/ca4c76a72d524f459ecf2bef305939c8/review.json'),'sha256':'0730b206239cb9e20a25e82dd5481d387c9e69b6f4d8397e2302d3a409ec18b2','bytes':3125}
caller=doc(caller_ref,'caller-w05-nonauthor')
check('caller_only_nonauthor_source_review',caller['reviewer']=='codex:/root/w05_merge_review' and caller['non_author'] is True and caller['decision']=='READY_SOURCE_PREPARATION_ONLY' and caller['requested_changes']==[] and caller['caller_sha256']=='6332aeab65da7a8893299ae93f54831eda0fba4da50dc215d07070f4839e24d8' and caller['actual_launch_authorized'] is False)
ob=named('tool-observations.fifth-construction.closed.original.json')
check('actual_observation_pin',inputs['tool-observations.fifth-construction.closed.original.json']['actual_ref']['sha256']=='714c08dff94b88ec6c7eda73e64208930726245102dfb43413418b85c3718fc4' and inputs['tool-observations.fifth-construction.closed.original.json']['actual_ref']['bytes']==194723)
pairs=[]
for start,end,session,first_chunk,last_chunk in [('capture_once','capture_poll_5',14030,'693aaa','fee815'),('scope_once','scope_poll',58056,'4437e2','b919fb')]:
    initial=next(v for v in ob['records'] if v['kind']==start);terminal=next(v for v in ob['records'] if v['kind']==end)
    result=terminal['result'];markers=re.findall(r'^ACTUAL_PYTHON_EXIT=(-?\\d+)\r?$',result['output'],re.M)
    # The exact marker form is additionally retained below, even if no match is established.
    marker_lines=[l for l in result['output'].splitlines() if l.startswith('ACTUAL_PYTHON_EXIT=')]
    ok=initial['result']['chunk_id']==first_chunk and initial['result']['session_id']==session and terminal['input']['session_id']==session and result['chunk_id']==last_chunk and result['exit_code']==0 and marker_lines==['ACTUAL_PYTHON_EXIT=0']
    check('Root_actual_tool_pair:'+start,ok)
    pairs.append({'start':start,'end':end,'session':session,'initial_chunk':initial['result']['chunk_id'],'terminal_chunk':result['chunk_id'],'outer_exit':result['exit_code'],'marker_lines':marker_lines,'matched':ok})
check('tool_only_metadata',ob['controller_or_launcher_executed'] is False and ob['canonical_writes']==0 and ob['formal_increment']==0 and ob['counter_reset'] is False)
failed=[c for c in checks if not c['ok']]
resource_ref=put('resources.readonly.audit.json',{'schema':'researchos.desktop58-readonly-resource-audit.v1','reviewer':ACTOR,'catalog_ref':scope['resource_catalog_ref'],'source639':{'files':639,'Go':559,'bytes':source_bytes,'actual_Main_hash_and_GitBlob':True},'resource_members':resource_rows,'resource_member_count':len(resource_rows),'resource_bytes_read':total_bytes,'compiler_count':len(compiler['files']),'runtime_count':len(runtime['files']),'image_count':len(catalog['images']),'physical_public_root_membership':root_checks,'actual_runtime_closure_verified':False,'resource_loading_or_products_executed':0})
matrix_ref=put('scope.matrix.audit.json',{'schema':'researchos.desktop58-supporting-scope-matrix.v1','reviewer':ACTOR,'checks':checks,'check_count':len(checks),'failed_checks':failed,'inputs':inputs,'projection_exact':projected==scope,'canonical_four':canonical_results,'fixed_cut':{'before':before,'after':after,'origins':origin_keys},'five_future_leaves':leaf_results,'alias20':alias_matrix,'Root_original_tool_pairs':pairs,'resources_audit_ref':resource_ref,'actual_products_executed':0,'candidate_imported_or_executed':False,'Git_native_calls':0,'canonical_writes':0,'source_acceptance':False,'formal_increment':0,'new_tool_failures':0,'Root_controller_review_not_written_by_f08':True,'actual_final_review_required_actor':'codex:/root/w05_merge_review'})
print(json.dumps({'matrix_ref':matrix_ref,'resources_ref':resource_ref,'check_count':len(checks),'failed_checks':failed,'source639_actual_sha_GitBlob':True,'resources':len(resource_rows),'public_roots':len(root_checks),'new_tool_failures':0,'products':0},ensure_ascii=False))
