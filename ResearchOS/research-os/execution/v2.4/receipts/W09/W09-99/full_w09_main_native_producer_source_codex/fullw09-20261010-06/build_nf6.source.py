"""Build conditional Source files only; no stage, Scope, TP or product execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,re,traceback,types,uuid

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
O=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
G=W/'w09_nf4_root_registration_source_codex/register-20261010-02'
P=W/'nf6_minimal_repin_preparation_source_codex/prepare-20261010-01'
C=W/'nf5_c19_main_order_candidate_source_codex/candidate-20261010-01'
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp);exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D
AUTHOR='codex:/root/full_w09_source_review';THREAD=s.THREAD;OLD_AUTHOR='codex:/root/attach_restore_independent_review'
OLD_GENERATION='fullw09-20261010-05';GENERATION='fullw09-20261010-06';STATUS='CONDITIONAL_SOURCE_PENDING_MAIN_ADOPTION'
refs={k:s.pin(p) for k,p in {'old_hdf':O/'HDF.json','old_mf':O/'MF.json','old_reg_hdf':G/'HDF.json','old_reg_mf':G/'MF.json','recipe_hdf':P/'HDF.json','recipe':P/'conditional-repin-recipe.source.json','candidate_hdf':C/'HDF.json','current_Main':R/'ops/ci/retrieval.py'}.items()}
old_hdf=json.loads((O/'HDF.json').read_bytes());old_mf=json.loads((O/'MF.json').read_bytes());old_reg_mf=json.loads((G/'MF.json').read_bytes());candidate_hdf=json.loads((C/'HDF.json').read_bytes())
candidate_ref=candidate_hdf['sourcecandidate_ref'];refs['candidate_source']=candidate_ref
for i,r in enumerate(old_mf['members']):refs['old_producer_member_'+str(i)]=r
for i,r in enumerate(old_reg_mf['members']):refs['old_registrar_member_'+str(i)]=r
g=s.guard();checks=[];failure=None;built={};inverse=[]
def check(name,ok,evidence=None):
    checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
    if not ok:raise ValueError(name)
def raw_write(name,raw):
    with (D/name).open('xb') as f:f.write(raw)
    return s.pin(D/name)
def replace_record(raw,old,new,records):
    if old==new:return raw
    count=raw.count(old)
    if not count:raise ValueError('EXPECTED_REPLACEMENT_ABSENT: '+old.decode('utf-8'))
    if raw.count(new):raise ValueError('REPLACEMENT_AFTER_ALREADY_PRESENT: '+new.decode('utf-8'))
    records.append({'before':old.decode('utf-8'),'after':new.decode('utf-8'),'occurrences':count})
    return raw.replace(old,new)
def restore(raw,records):
    for record in reversed(records):
        old,new=record['before'].encode(),record['after'].encode()
        if raw.count(new)!=record['occurrences']:raise ValueError('INVERSE_OCCURRENCE_DRIFT')
        raw=raw.replace(new,old)
    return raw
def replace_ref(raw,before,after,records):
    # Existing immutable documents use exact path/sha256/bytes objects.
    old_obj=json.dumps(before,ensure_ascii=False,indent=2).splitlines()
    for indent in range(0,18,2):
        before_text=('\n'.join(old_obj[0:1]+[(' '*indent)+line for line in old_obj[1:]])).encode()
        if before_text in raw:
            new_obj=json.dumps(after,ensure_ascii=False,indent=2).splitlines()
            after_text=('\n'.join(new_obj[0:1]+[(' '*indent)+line for line in new_obj[1:]])).encode()
            return replace_record(raw,before_text,after_text,records)
    # Source JSON object indentation can be established directly from its ref span.
    digest=before['sha256'].encode();pos=raw.find(digest)
    if pos<0 or raw.find(digest,pos+1)>=0:raise ValueError('REF_DIGEST_NOT_UNIQUE')
    begin=raw.rfind(b'{',0,pos);end=raw.find(b'}',pos)+1
    before_text=raw[begin:end]
    if json.loads(before_text)!=before:raise ValueError('REF_SPAN_NOT_EXACT')
    after_text=before_text
    for k in ('path','sha256','bytes'):
        old_token=json.dumps(before[k],ensure_ascii=False).encode();new_token=json.dumps(after[k],ensure_ascii=False).encode()
        if old_token!=new_token:
            if after_text.count(old_token)!=1:raise ValueError('REF_TOKEN_NOT_UNIQUE')
            after_text=after_text.replace(old_token,new_token,1)
    return replace_record(raw,before_text,after_text,records)
try:
    g.acquire(list({r['path']:r for r in refs.values()}.values()))
    before=candidate_hdf['before_main_ref'];actual=refs['current_Main']
    check('actual_Main_precondition_is_observed_not_claimed_qualified',actual==before,{'observed_current_Main_ref':actual,'expected_after_is_conditional':True})
    expected=dict(path=before['path'],sha256=candidate_ref['sha256'],bytes=candidate_ref['bytes'])
    check('held_candidate_exact_known_after_bytes',hashlib.sha256(g.get_buffer(candidate_ref['path'])).hexdigest()=='b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11' and candidate_ref['bytes']==14545)
    bp_old=g.get_buffer(old_hdf['compiler_blueprint_ref']['path']);bp_records=[]
    bp_new=replace_ref(bp_old,before,expected,bp_records)
    bp0,bp1=json.loads(bp_old),json.loads(bp_new)
    bp_back=copy.deepcopy(bp1);bp_back['stable_input_refs'][3850]=copy.deepcopy(before)
    check('blueprint_only_ref3850_changes_all_3904_and_rosters_unchanged',bp0['stable_input_refs'][3850]==before and bp1['stable_input_refs'][3850]==expected and bp_back==bp0 and len(bp1['stable_input_refs'])==3905 and bp1['allowed_package_roster']==bp0['allowed_package_roster'] and restore(bp_new,bp_records)==bp_old)
    built['compiler_blueprint_ref']=raw_write('compiler-source-blueprint.json',bp_new)
    inverse.append({'file':'compiler-source-blueprint.json','before_ref':old_hdf['compiler_blueprint_ref'],'after_ref':built['compiler_blueprint_ref'],'replacements':bp_records,'exact_byte_inverse':True})

    runtime_old=g.get_buffer(old_hdf['runtime_ref']['path']);runtime_records=[];runtime_new=runtime_old
    for a,b in [(OLD_AUTHOR,AUTHOR),(OLD_GENERATION,GENERATION),('SOURCE_READY_PENDING_INDEPENDENT_REVIEW',STATUS)]:runtime_new=replace_record(runtime_new,a.encode(),b.encode(),runtime_records)
    ast.parse(runtime_new)
    check('runtime_only_actual_author_generation_and_exact_conditional_marker',restore(runtime_new,runtime_records)==runtime_old and runtime_new.count(STATUS.encode())==1 and b"obj['status']=='CONDITIONAL_SOURCE_PENDING_MAIN_ADOPTION'" in runtime_new)
    built['runtime_ref']=raw_write('full_w09_runtime.source.py',runtime_new)
    inverse.append({'file':'full_w09_runtime.source.py','before_ref':old_hdf['runtime_ref'],'after_ref':built['runtime_ref'],'replacements':runtime_records,'exact_byte_inverse':True})
    over_old=g.get_buffer(old_hdf['overrides_ref']['path']);over_records=[]
    over_new=replace_record(over_old,OLD_GENERATION.encode(),GENERATION.encode(),over_records)
    ast.parse(over_new);check('overrides_generation_only_full_inverse',restore(over_new,over_records)==over_old)
    built['overrides_ref']=raw_write('runtime-overrides.source.py',over_new)
    inverse.append({'file':'runtime-overrides.source.py','before_ref':old_hdf['overrides_ref'],'after_ref':built['overrides_ref'],'replacements':over_records,'exact_byte_inverse':True})
    for name,key in [('prepare_full_w09.source.py','prepare_caller_ref'),('run_full_w09.source.py','producer_caller_ref'),('full_w09_launcher.source.py','launcher_ref')]:
        raw_old=g.get_buffer(old_hdf[key]['path']);records=[]
        raw_new=replace_record(raw_old,old_hdf['runtime_ref']['sha256'].encode(),built['runtime_ref']['sha256'].encode(),records)
        ast.parse(raw_new);check(name+'_only_runtime_pin_changes',restore(raw_new,records)==raw_old)
        built[key]=raw_write(name,raw_new)
        inverse.append({'file':name,'before_ref':old_hdf[key],'after_ref':built[key],'replacements':records,'exact_byte_inverse':True})

    choice_old=g.get_buffer(old_hdf['source_choice_ref']['path']);choice_records=[];choice_new=choice_old
    choice_new=replace_ref(choice_new,before,expected,choice_records)
    choice_new=replace_record(choice_new,OLD_GENERATION.encode(),GENERATION.encode(),choice_records)
    intermediate_blueprint_ref=copy.deepcopy(old_hdf['compiler_blueprint_ref']);intermediate_blueprint_ref['path']=intermediate_blueprint_ref['path'].replace(OLD_GENERATION,GENERATION)
    choice_new=replace_ref(choice_new,intermediate_blueprint_ref,built['compiler_blueprint_ref'],choice_records)
    old_choice=json.loads(choice_old);runids={k:uuid.uuid4().hex for k in old_choice['selectors']}
    for key,runid in runids.items():choice_new=replace_record(choice_new,old_choice['selectors'][key]['run_id'].encode(),runid.encode(),choice_records)
    choice=json.loads(choice_new)
    check('choice_only_Source21_blueprint_generation_and_fresh_UUID_repin',restore(choice_new,choice_records)==choice_old and choice['common']['source21'][16]==expected and choice['common']['compiler_blueprint_ref']==built['compiler_blueprint_ref'])
    check('four_fresh_distinct_UUID_roots_actual_absent_without_creation',len(set(runids.values()))==4 and all(re.fullmatch('[0-9a-f]{32}',v) for v in runids.values()) and all(not Path(v[f]).exists() for v in choice['selectors'].values() for f in ('receipt_root','scratch_root','output_root')))
    check('four_existing_argv_tests_packages_and_assertion_rosters_unchanged',all({k:v for k,v in value.items() if k not in ('run_id','receipt_root','scratch_root','output_root')}=={k:v for k,v in old_choice['selectors'][key].items() if k not in ('run_id','receipt_root','scratch_root','output_root')} for key,value in choice['selectors'].items()))
    check('physical_C_parent_unchanged_private_empty_cache_policy_unchanged',all(str(Path(v['scratch_root']).parent)==r'C:\Users\yqyyds\.researchos\w09-native-v5' for v in choice['selectors'].values()) and b"require(not any((scratch/'gocache').iterdir()),'FRESH_PRIVATE_GOCACHE')" in runtime_new)
    built['source_choice_ref']=raw_write('source.choice.json',choice_new)
    inverse.append({'file':'source.choice.json','before_ref':old_hdf['source_choice_ref'],'after_ref':built['source_choice_ref'],'replacements':choice_records,'exact_byte_inverse':True})
    contract_old=json.loads(g.get_buffer(old_hdf['calling_contract_ref']['path']));contract=copy.deepcopy(contract_old)
    contract['author']=contract['source_actor']=AUTHOR;contract['source_thread_id']=THREAD;contract['generation']=GENERATION
    contract['canonical_registration']={k:v.replace(OLD_GENERATION,GENERATION) for k,v in contract['canonical_registration'].items()}
    bindings={'prepare_caller_ref':built['prepare_caller_ref'],'producer_caller_ref':built['producer_caller_ref'],'launcher_ref':built['launcher_ref'],'runtime_ref':built['runtime_ref'],'choice_ref':built['source_choice_ref'],'compiler_blueprint_ref':built['compiler_blueprint_ref']}
    contract['bound_source_refs']=bindings
    for mode in ('prepare','run'):contract['future_argv'][mode]=[arg.replace(OLD_GENERATION,GENERATION) for arg in contract['future_argv'][mode]]
    contract.update(source_handoff_status=STATUS,conditional_Main_adoption_required=True,conditional_Main_after_ref=expected,observed_Main_before_ref=actual,current_Main_qualification=False,Root_execute=False,parallel_schedule={'maximum_active_selector_runs':2,'waves':[['W09-G01','W09-G02'],['A06','C19']],'Root_actual_Scope_lease_and_resource_observation_required':True,'shared_GOCACHE':False},prior_Source_author={'actor_id':OLD_AUTHOR,'source_thread_id':old_hdf['source_thread_id'],'hdf_ref':refs['old_hdf'],'mf_ref':refs['old_mf']})
    check('contract_exact_Scope_request_schemas_and_all_budgets_retained',contract['scope_required_fields']==contract_old['scope_required_fields'] and contract['request_exact_fields']==contract_old['request_exact_fields'] and contract['scope_schema']==contract_old['scope_schema'] and contract['request_schema']==contract_old['request_schema'] and contract['review_schema']==contract_old['review_schema'] and contract['review_decision']==contract_old['review_decision'])
    built['calling_contract_ref']=s.write('root-calling-contract.json',contract)
    built['source_delta_ref']=s.write('source-delta.json',{'schema':'researchos.w09-nf6-conditional-source-delta.v1','actual_author':AUTHOR,'source_thread_id':THREAD,'prior_Source_actor':OLD_AUTHOR,'prior_source_hdf_ref':refs['old_hdf'],'prior_source_mf_ref':refs['old_mf'],'recipe_hdf_ref':refs['recipe_hdf'],'recipe_ref':refs['recipe'],'candidate_hdf_ref':refs['candidate_hdf'],'candidate_ref':candidate_ref,'actual_Main_before_ref':actual,'conditional_Main_after_ref':expected,'Main_adopted':False,'source21_is_current_actual':False,'byte_inverse_records':inverse,'conditional_status_token_is_not_execution_authority':True,'Source21_and_root_authority_must_revalidate_before_any_stage':True,'3905_old_controls_rerun':False,'old_successful_controls_rerun':False,'Rootexecute':False,'execution_grant':False,'formal_acceptance':False})
    built['build-input-pins-ref']=s.write('build-input-pins.json',{'schema':'researchos.w09-nf6-source-build-inputs.v1','refs':refs,'fresh_run_UUIDs':runids,'actual_Main_before_ref':actual,'conditional_Main_after_ref':expected,'source21_is_current_actual':False,'SourceRoot_scope_grant':False,'historical_Source_refs_not_rewritten':True})
except BaseException as exc:failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed=g.close();guard_ref=s.write('source-guard.closed.json',closed)
    result_ref=s.write('delta-controls.json',{'schema':'researchos.w09-nf6-conditional-delta-controls.v1','source_author':AUTHOR,'created_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'passed':sum(row['passed'] for row in checks),'failed':sum(not row['passed'] for row in checks),'failure':failure,'guard_ref':guard_ref,'built_refs':built,'pure_Source_only':True,'old_3905_and_old_successful_controls_rerun':False,'actual_Root_stage_Go_Native_SQL_model_TP_calls':0,'Main_Canon_Scope_written':False,'current_Main_qualification':False,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'status':'CONDITIONAL_SOURCE_FILES_BUILT_PENDING_SEAL' if failure is None else 'FAILED_SOURCE_BUILD','result_ref':result_ref,'guard_ref':guard_ref,'passed':sum(row['passed'] for row in checks),'failure':failure,'built_refs':built,'guard_closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'Rootexecute':False,'currentMainqualified':False,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:raise SystemExit(1)
