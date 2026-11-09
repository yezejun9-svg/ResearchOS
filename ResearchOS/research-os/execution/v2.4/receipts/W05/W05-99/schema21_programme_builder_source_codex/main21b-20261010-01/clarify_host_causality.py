"""Bounded Source-contract clarification; immutable initial contract preserved."""
import hashlib,json,sys,types
from pathlib import Path
N=Path(__file__).resolve().parent
G=Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=p.as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(name,x):
    p=N/name
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
    return ref(p)
raw=G.read_bytes();assert hashlib.sha256(raw).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and len(raw)==11404
gm=types.ModuleType('old21_causal_guard');exec(compile(raw,str(G),'exec'),gm.__dict__)
g=gm.SourceReadGuard();checks=[];audits=[]
try:
    initial=ref(N/'contract.json');assert initial['sha256']=='4051f116fa6b5d7be8f8d4999a499d8baa586db43bed0f3367127680cbba270b' and initial['bytes']==20353
    try:
        g.acquire([initial,ref(N/'old21_builder.py'),ref(N/'source-controls.json')])
        old=json.loads(g.get_buffer(initial['path']));c=json.loads(g.get_buffer(initial['path']))
        assert json.loads(g.get_buffer(str(N/'source-controls.json')))['passed']==75
        c['schema']='researchos.old21-programme-builder-contract.v2'
        c['superseded_initial_contract_ref']=initial
        c['Root_mandatory_boundary']=[s.replace('actual outer host binding refs','prior completed Root authority-observation host binding refs').replace('Full original Root host call/output captured losslessly, including integer FILETIME; source-only mocked observations cannot satisfy actual host binding','Prior completed Root registration/qualification/activation/current4 hostpair is validated before entry. Current build full original call/output is captured externally only after return/failure; lossless integer FILETIME, no mocked or future completed hostpair') for s in c['Root_mandatory_boundary']]
        c['outer_host_binding_contract']={'meaning':'PRIOR_COMPLETED_REAL_ROOT_AUTHORITY_OBSERVATION','allowed_observations':['RootScope registration','resource qualification','activation','current-four-files observation'],'must_predate_this_build_entry':True,'caller_must_bind_same_scope_and_exact_inputs':True,'caller_must_verify_original_host_bytes_Root_identity_and_time_order':True,'current_build_not_yet_returned_complete_pair_prohibited':True,'caller_authored_JSON_is_not_actual_hostpair':True,'future_timestamp_prohibited':True}
        c['actual_build_hostpair_obligation']={'owner':'codex:/root','timing':'EXTERNAL_CAPTURE_AFTER_BUILD_RETURNS_OR_FAILS','required_before_independent_programme_qualification':True,'current_build_complete_pair_required_at_entry':False,'actual_complete_pair_ref':None,'capture_method':'Actual original Root tool call and matching output bytes, independently bound after return; do not synthesize call completion.'}
        c['future_Root_scope_ref']=None;c['future_activation_ref']=None;c['future_runtime_grant_ref']=None
        c['Root_counter_last_reported_at_causality_clarification']=1067
        new=save('contract.v2.json',c)
        builder_raw=g.get_buffer(str(N/'old21_builder.py'))
    finally:
        audit=g.close();audits.append(save('causality_input.guard.closed.json',audit))
        assert audit['closed'] is True and audit['retained_handles_count']==0 and audit['errors']==[]
    h=gm.SourceReadGuard()
    try:
        h.acquire([new,old['base_helper_ref'],old['common_builder_ref'],old['builder_ref']])
        mod=types.ModuleType('old21_causal_builder');exec(compile(h.get_buffer(old['builder_ref']['path']),old['builder_ref']['path'],'exec'),mod.__dict__)
        base=types.ModuleType('old21_causal_base');exec(compile(h.get_buffer(old['base_helper_ref']['path']),old['base_helper_ref']['path'],'exec'),base.__dict__)
        final=json.loads(h.get_buffer(new['path']))
        request={'case_id':'b'*32,'output_root':final['output_parent']+'/old21-build-'+'b'*32}
        pairs=[('unchanged-builder-ref',final['builder_ref']==old['builder_ref']),('unchanged-input-manifest-and-source',final['input_manifest_ref']==old['input_manifest_ref'] and final['frozen_source_manifest_ref']==old['frozen_source_manifest_ref']),('unchanged-nine-phase-projection',mod.compile_request(final,request,base)==mod.compile_request(old,request,base)),('only-prior-completed-host-binding',final['outer_host_binding_contract']['must_predate_this_build_entry'] and final['outer_host_binding_contract']['current_build_not_yet_returned_complete_pair_prohibited']),('post-return-capture-obligation',final['actual_build_hostpair_obligation']['timing']=='EXTERNAL_CAPTURE_AFTER_BUILD_RETURNS_OR_FAILS' and final['actual_build_hostpair_obligation']['current_build_complete_pair_required_at_entry'] is False),('future-complete-pair-null',final['actual_build_hostpair_obligation']['actual_complete_pair_ref'] is None),('future-authority-refs-null',all(final[k] is None for k in ['future_Root_scope_ref','future_activation_ref','future_runtime_grant_ref'])),('original-contract-preserved',ref(N/'contract.json')==initial)]
        for name,ok in pairs:
            checks.append({'id':name,'passed':bool(ok),'scope':'PURE_SOURCE_CONTRACT_ONLY'});assert ok,name
    finally:
        audit=h.close();audits.append(save('causality_output.guard.closed.json',audit))
        assert audit['closed'] is True and audit['retained_handles_count']==0 and audit['errors']==[]
    report=save('causality-clarification.json',{'schema':'researchos.old21-source-host-causality-clarification.v1','final_contract_ref':new,'initial_contract_ref':initial,'checks':checks,'passed':len(checks),'failed':0,'prior75_controls_reused':True,'builder_changed':False,'input_source_or_resources_changed':False,'runtime_branch_called':False,'Go_Native_SQL_subprocess_calls':0,'guard_audit_refs':audits,'actual_scope_grant_or_host_completion_created':False})
    print(json.dumps({'contract_ref':new,'causality_clarification_ref':report,'checks_passed':len(checks),'guards':audits,'runtime_branch_called':False},ensure_ascii=False))
except BaseException as exc:
    save('causality-clarification.failure.json',{'type':type(exc).__name__,'message':str(exc),'script_ref':ref(Path(__file__)),'argv':sys.argv,'checks':checks,'guards':audits,'original_ordinal':None,'Root_assignment_required':True,'automatic_retry':False})
    raise
