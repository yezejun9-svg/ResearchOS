"""Seal conditional NF6 and build new registrar Source only."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,traceback,types

R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
N=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
O=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
OLDREG=W/'w09_nf4_root_registration_source_codex/register-20261010-02'
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp);exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__)
AUTHOR='codex:/root/full_w09_source_review';OLD_AUTHOR='codex:/root/attach_restore_independent_review';THREAD=s.THREAD
OLD_GENERATION='fullw09-20261010-05';GENERATION='fullw09-20261010-06';STATUS='CONDITIONAL_SOURCE_PENDING_MAIN_ADOPTION'
def write_at(root,name,value):s.D=root;return s.write(name,value)
def raw_write(root,name,raw):
    with (root/name).open('xb') as f:f.write(raw)
    return s.pin(root/name)
def load(ref):
    raw=Path(ref['path']).read_bytes()
    if s.pin(ref['path'])!=ref:raise ValueError('PERSISTED_BUILD_REF_DRIFT')
    return json.loads(raw)
control_ref={'path':str(N/'delta-controls.json'),'sha256':'92bc67a988d6df44e42a39ce1b6039d2ca3ad7500a379c4988bf387b338d033b','bytes':6110}
controls=load(control_ref);buildpins=load(controls['built_refs']['build-input-pins-ref']);closed=load(controls['guard_ref'])
if controls['failure'] is not None or controls['failed'] or controls['passed']!=13 or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:raise ValueError('PRODUCER_BUILD_NOT_CLOSED_PASSED')
old_hdf=load(buildpins['refs']['old_hdf']);old_reg_hdf=load(buildpins['refs']['old_reg_hdf']);built=controls['built_refs'];choice=load(built['source_choice_ref']);delta=load(built['source_delta_ref'])
created=datetime.now(timezone.utc).isoformat();s.D=N;producer_host=s.capture('0d2ef9',0,0)
mf=write_at(N,'MF.json',{'schema':'researchos.w09-four-selector-producer-source-manifest.v1','members':[s.pin(p) for p in sorted(N.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')],'conditional_Main_adoption_required':True,'execution_grant':False,'formal_acceptance':False})
h=copy.deepcopy(old_hdf)
h.update(actor_id=AUTHOR,source_actor_backend=s.ACTOR,source_thread_id=THREAD,status=STATUS,manifest_ref=mf,generation=GENERATION,source21=choice['common']['source21'],selectors=choice['selectors'],calling_contract_ref=built['calling_contract_ref'],source_choice_ref=built['source_choice_ref'],runtime_ref=built['runtime_ref'],overrides_ref=built['overrides_ref'],launcher_ref=built['launcher_ref'],prepare_caller_ref=built['prepare_caller_ref'],producer_caller_ref=built['producer_caller_ref'],compiler_blueprint_ref=built['compiler_blueprint_ref'],source_delta_ref=built['source_delta_ref'],source_guard_ref=controls['guard_ref'],finite_controls_ref=control_ref,new_finite_controls={'passed':13,'failed':0,'pure_Source_only':True},prior_source_hdf_ref=buildpins['refs']['old_hdf'],prior_source_mf_ref=buildpins['refs']['old_mf'],prior_Source_author={'actor_id':OLD_AUTHOR,'source_thread_id':old_hdf['source_thread_id']},actual_source_build_host=producer_host,created_utc=created,conditional_Main_adoption_required=True,actual_Main_observed_ref=delta['actual_Main_before_ref'],conditional_Main_after_ref=delta['conditional_Main_after_ref'],current_Main_qualification=False,current_Source21_qualification=False,Rootexecute=False,independent_source_review_required=True,independent_source_review_refs=None,original_diagnostics=[],old_NF5_controls_rerun=False,compiler_3905_controls_rerun=False,root_only_scope_registration='New registrar Source w09_nf6_root_registration_source_codex/register-20261010-01; no scopes issued by Source.',next_gate='Actual Root adoption of the single-line Main candidate, fresh current Source21 reobservation, real non-author Source reviews/peer audits, then Root-only new generation registration and finite leases.',future_Root_scope=None,future_Root_request=None,future_registration=None,future_ModeProof=None,execution_grant=False,formal_acceptance=False,actual_executed=False)
producer_hdf=write_at(N,'HDF.json',h)

# Extract only pure text replacement helpers, never execute the build script.
helper_env={'json':json}
tree=ast.parse((N/'build_nf6.source.py').read_bytes())
pure_defs=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ('replace_record','restore','replace_ref')]
exec(compile(ast.Module(body=pure_defs,type_ignores=[]),str(N/'build_nf6.source.py')+'#pure-text-helpers','exec'),helper_env)
replace_record,restore,replace_ref=[helper_env[k] for k in ('replace_record','restore','replace_ref')]
refs={'old_reg_hdf':buildpins['refs']['old_reg_hdf'],'old_reg_mf':buildpins['refs']['old_reg_mf'],'old_caller':old_reg_hdf['caller_ref'],'old_core':old_reg_hdf['core_ref'],'old_contract':old_reg_hdf['contract_ref'],'old_inputs':old_reg_hdf['input_pins_ref'],'producer_hdf':producer_hdf,'producer_mf':mf}
for i,r in enumerate(json.loads(Path(mf['path']).read_bytes())['members']):refs['producer_member_'+str(i)]=r
g=s.guard();checks=[];failure=None;registrar_built={};inverse=[]
def check(name,ok,evidence=None):
    checks.append({'name':name,'passed':bool(ok),'evidence':evidence})
    if not ok:raise ValueError(name)
try:
    g.acquire(list({r['path']:r for r in refs.values()}.values()))
    runtime=s.inert(built['runtime_ref']['path'],g.get_buffer(built['runtime_ref']['path']))
    package_hdf,package_mf,package_refs=runtime.package_refs()
    check('actual_NF6_package_refs_accepts_only_its_exact_conditional_Source_token',package_hdf==producer_hdf and package_mf==mf and json.loads(g.get_buffer(producer_hdf['path']))['status']==STATUS,{'pure_Source_package_interface_called':True,'stage_called':False,'Main_Source21_current_gate_not_bypassed':True})
    core_old=g.get_buffer(refs['old_core']['path']);core_records=[];core_new=core_old
    for a,b in [(OLD_AUTHOR,AUTHOR),(OLD_GENERATION,GENERATION)]:core_new=replace_record(core_new,a.encode(),b.encode(),core_records)
    ast.parse(core_new)
    check('registrar_core_only_author_and_generation_identifiers_change',restore(core_new,core_records)==core_old)
    registrar_built['core_ref']=raw_write(D,'adoption_core.source.py',core_new)
    inverse.append({'file':'adoption_core.source.py','before_ref':refs['old_core'],'after_ref':registrar_built['core_ref'],'replacements':core_records,'exact_byte_inverse':True})

    inputs_old=g.get_buffer(refs['old_inputs']['path']);inputs_records=[];inputs_new=inputs_old;inputs0=json.loads(inputs_old)
    nfrefs={'NF_hdf':producer_hdf,'NF_mf':mf,'NF_contract':built['calling_contract_ref'],'NF_choice':built['source_choice_ref'],'NF_runtime':built['runtime_ref'],'NF_prepare':built['prepare_caller_ref'],'NF_run':built['producer_caller_ref'],'NF_launcher':built['launcher_ref'],'NF_blueprint':built['compiler_blueprint_ref']}
    for key,newref in nfrefs.items():inputs_new=replace_ref(inputs_new,inputs0['refs'][key],newref,inputs_records)
    inputs1=json.loads(inputs_new);inputs_back=copy.deepcopy(inputs1)
    for key in nfrefs:inputs_back['refs'][key]=copy.deepcopy(inputs0['refs'][key])
    check('registrar_input_only_nine_new_producer_refs_rest_is_exact_historical',inputs_back==inputs0 and restore(inputs_new,inputs_records)==inputs_old and all(inputs1['refs'][k]==v for k,v in nfrefs.items()))
    registrar_built['input_pins_ref']=raw_write(D,'input-pins.json',inputs_new)
    inverse.append({'file':'input-pins.json','before_ref':refs['old_inputs'],'after_ref':registrar_built['input_pins_ref'],'replacements':inputs_records,'exact_byte_inverse':True})
    caller_old=g.get_buffer(refs['old_caller']['path']);caller_records=[];caller_new=caller_old
    for a,b in [(OLD_AUTHOR,AUTHOR),(refs['old_inputs']['sha256'],registrar_built['input_pins_ref']['sha256']),('w09_nf5_root_registration_root','w09_nf6_root_registration_root')]:caller_new=replace_record(caller_new,a.encode(),b.encode(),caller_records)
    ast.parse(caller_new)
    check('registrar_caller_only_author_input_SHA_and_Root_output_namespace_change',restore(caller_new,caller_records)==caller_old)
    registrar_built['caller_ref']=raw_write(D,'register_w09_adoption.source.py',caller_new)
    inverse.append({'file':'register_w09_adoption.source.py','before_ref':refs['old_caller'],'after_ref':registrar_built['caller_ref'],'replacements':caller_records,'exact_byte_inverse':True})
    caller=s.inert(registrar_built['caller_ref']['path'],caller_new);input_doc,actual_input_pin=caller.inputs()
    check('registrar_pure_inputs_interface_observes_actual_new_input_pin',input_doc==inputs1 and actual_input_pin==registrar_built['input_pins_ref'],{'Root_stage_called':False})
    core=s.inert(registrar_built['core_ref']['path'],core_new)
    check('registrar_new_generation_owner_worker_and_actual_author_constants',core.GENERATION==GENERATION and core.NKEY=='full_w09_main_native_producer_'+GENERATION and core.NSLICE=='FULL_W09_MAIN_NATIVE_PRODUCER_'+GENERATION and caller.AUTHOR==core.AUTHOR==AUTHOR)
    check('four_new_Source_choice_routes_scopes_root_leases_not_constructed',set(runtime.choice(k)['generation'] for k in ('W09-G01','W09-G02','A06','C19'))=={GENERATION} and core.SELECTORS==('W09-G01','W09-G02','A06','C19'),{'choice_pure_Source_interface_only':True,'make_native_scopes_called':False,'Root_Scope_or_lease_issued':False})

    old_contract=json.loads(g.get_buffer(refs['old_contract']['path']));contract=copy.deepcopy(old_contract)
    contract['source_author']=AUTHOR;contract['source_thread_id']=THREAD;contract['generation']=GENERATION
    contract['source_bindings']={'caller_ref':registrar_built['caller_ref'],'core_ref':registrar_built['core_ref']};contract['input_pins_ref']=registrar_built['input_pins_ref'];contract['existing_native_contract_ref']=built['calling_contract_ref']
    contract['CLI']['entrypoint']=str(D/'register_w09_adoption.source.py');contract['CLI']['prefix'][-1]=str(D/'register_w09_adoption.source.py')
    contract.update(source_handoff_status=STATUS,conditional_Main_adoption_required=True,conditional_Main_after_ref=delta['conditional_Main_after_ref'],observed_Main_before_ref=delta['actual_Main_before_ref'],current_Main_qualification=False,Rootexecute=False,new_Root_output_namespace=str(W/'w09_nf6_root_registration_root'),producer_source_hdf_ref=producer_hdf,producer_source_mf_ref=mf,prior_Source_author={'actor_id':OLD_AUTHOR,'source_thread_id':old_reg_hdf['source_thread_id'],'hdf_ref':refs['old_reg_hdf'],'mf_ref':refs['old_reg_mf']},parallel_schedule=load(built['calling_contract_ref'])['parallel_schedule'])
    check('registrar_all_original_request_and_review_schemas_and_TP_gate_retained',contract['request_required_fields']==old_contract['request_required_fields'] and set(contract['request_required_fields'])==caller.REQUEST_FIELDS and contract['request_schema']==old_contract['request_schema'] and contract['review_schema']==old_contract['review_schema'] and contract['review_decision']==old_contract['review_decision'] and contract['shared_canonical_transaction_ref']==old_contract['shared_canonical_transaction_ref'] and contract['permitted_Main_writes']==[])
    registrar_built['contract_ref']=write_at(D,'root-calling-contract.source.json',contract)
    registrar_built['source_delta_ref']=write_at(D,'source-delta.json',{'schema':'researchos.w09-nf6-registration-conditional-source-delta.v1','actual_author':AUTHOR,'source_thread_id':THREAD,'prior_source_hdf_ref':refs['old_reg_hdf'],'prior_source_mf_ref':refs['old_reg_mf'],'prior_Source_author':OLD_AUTHOR,'byte_inverse_records':inverse,'producer_hdf_ref':producer_hdf,'producer_mf_ref':mf,'conditional_Main_adoption_required':True,'conditional_Main_after_ref':delta['conditional_Main_after_ref'],'actual_Main_observed_ref':delta['actual_Main_before_ref'],'dynamic_actual_current4_and_pending_suffix_preserved':True,'Root_next_ordinal_not_issued':True,'Root_stages_called':False,'Rootexecute':False,'execution_grant':False,'formal_acceptance':False})
    registrar_built['source_input_refs']=write_at(D,'source-input-pins.json',{'schema':'researchos.w09-nf6-registration-source-build-inputs.v1','refs':refs,'producer_source_hdf_ref':producer_hdf,'producer_source_mf_ref':mf,'Root_actual_Scope_lease_review_witness_refs':None,'Rootexecute':False})
except BaseException as exc:failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed2=g.close();reg_guard=write_at(D,'source-guard.closed.json',closed2)
    reg_controls=write_at(D,'delta-controls.json',{'schema':'researchos.w09-nf6-registration-conditional-delta-controls.v1','actual_author':AUTHOR,'created_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'passed':sum(row['passed'] for row in checks),'failed':sum(not row['passed'] for row in checks),'failure':failure,'guard_ref':reg_guard,'built_refs':registrar_built,'producer_source_hdf_ref':producer_hdf,'producer_source_mf_ref':mf,'pure_Source_interfaces_only':True,'old_successful_controls_rerun':False,'actual_Root_stage_Go_Native_SQL_model_TP_calls':0,'Main_Canon_Scope_written':False,'current_Main_qualification':False,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'status':'PRODUCER_SEALED_REGISTRAR_FILES_BUILT_PENDING_SEAL' if failure is None else 'FAILED_REGISTRAR_SOURCE_BUILD','producer_refs':{'hdf':producer_hdf,'mf':mf,'calling_contract':built['calling_contract_ref']},'registrar_controls_ref':reg_controls,'registrar_guard_ref':reg_guard,'registrar_built_refs':registrar_built,'passed':sum(row['passed'] for row in checks),'failure':failure,'all_guards_closed':closed['closed'] and closed2['closed'],'retained_handles_count':closed['retained_handles_count']+closed2['retained_handles_count'],'Rootexecute':False,'currentMainqualified':False,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
if failure or not closed2['closed'] or closed2['retained_handles_count'] or closed2['errors']:raise SystemExit(1)
