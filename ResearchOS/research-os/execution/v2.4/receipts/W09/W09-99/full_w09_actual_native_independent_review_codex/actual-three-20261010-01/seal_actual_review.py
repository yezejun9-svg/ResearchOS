from pathlib import Path
import types,json,hashlib,datetime
p=Path(__file__).with_name('review_support.py');m=types.ModuleType('support');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__)
LOG=Path(r'C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl');THREAD='01a1215b-7210-7613-b033-756b9d553b83'
def docs(value):
    if type(value) is dict:
        yield value
        for v in value.values():yield from docs(v)
    elif type(value) is list:
        for v in value:yield from docs(v)
    elif type(value) is str:
        try:yield from docs(json.loads(value))
        except (ValueError,TypeError):pass
def host(chunk):
    calls={};matches=[];size=LOG.stat().st_size
    with LOG.open('rb') as f:
        header=f.readline();assert json.loads(header)['payload']['id']==THREAD;f.seek(max(0,size-64*1024*1024))
        if f.tell():f.readline()
        while f.tell()<size:
            offset=f.tell();line=f.readline();row=json.loads(line);v=row.get('payload',{})
            if v.get('type')=='custom_tool_call':calls[v['call_id']]=(offset,line,row)
            elif v.get('type')=='custom_tool_call_output':
                values=[x for x in docs(v.get('output')) if x.get('chunk_id')==chunk]
                if values and v['call_id'] in calls:matches.append((calls[v['call_id']],(offset,line,row),values))
    assert len(matches)==1 and len(matches[0][2])==1
    call,result,values=matches[0];value=values[0];assert value['exit_code']==0 and 'Python_exit=0' in value['output']
    lines=[header,call[1],result[1]];offsets=[0,call[0],result[0]]
    with LOG.open('rb') as f:
        for offset,line in zip(offsets,lines):f.seek(offset);assert f.read(len(line))==line
    path=m.D/('success-'+chunk+'.raw.jsonl')
    with path.open('xb') as f:f.write(b''.join(lines))
    raw=m.pin(path);binding=m.write('success-'+chunk+'.binding.json',{'schema':'researchos.w09-independent-readonly-host-binding.v1','actor_id':'/root/full_w09_source_review','actor_thread_id':THREAD,'source_audit_path':str(LOG),'source_prefix_size_observed':size,'source_line_offsets':offsets,'original_line_sha256':[hashlib.sha256(line).hexdigest() for line in lines],'original_line_bytes':[len(line) for line in lines],'original_raw_ref':raw,'actual_call_id':call[2]['payload']['call_id'],'actual_chunk_id':chunk,'actual_outer_exit':0,'actual_python_exit':0,'actual_native_exit':None,'actual_go_exit':None,'actual_sql_exit':None,'actual_dispatcher_exit':None,'actual_model_exit':None,'product_calls':0,'execution_grant':False,'formal_acceptance':False})
    return {'raw_ref':raw,'binding_ref':binding}
hosts={chunk:host(chunk) for chunk in ('5d0543','d1df0b','35b8f3','91e397','de99e8','95bd7e','bf4ef4')}
prior=json.loads((m.D/'G01.review-result.json').read_bytes());g01=json.loads((m.D/'G01.completed-review-result.json').read_bytes());failed=json.loads((m.D/'failed-selectors.independent-result.json').read_bytes());fixture=json.loads((m.D/'legacy-fixture-candidate.independent-review.json').read_bytes())
assert all(c['passed'] for c in prior['checks']) and all(c['passed'] for c in g01['new_checks']) and g01['mode_refs'] and fixture['verdict']=='SOURCE_ACCEPTED_CANDIDATE_ONLY'
guard_files=sorted(m.D.glob('*.guard.closed.json'));guard_refs=[m.pin(p) for p in guard_files]
for p in guard_files:
    obs=json.loads(p.read_bytes());assert obs['closed'] is True and obs['retained_handles_count']==0 and not obs['errors']
failures={str(ordinal):{'raw_ref':m.pin(m.D/('original-'+str(ordinal)+'.raw.jsonl')),'binding_ref':m.pin(m.D/('original-'+str(ordinal)+'.binding.json'))} for ordinal in (1122,1126,1128,1130)}
all_input_refs=[*g01['mode_refs'].values(),m.pin(m.D/'G01.completed-review-result.json'),m.pin(m.D/'failed-selectors.independent-result.json'),m.pin(m.D/'legacy-fixture-candidate.independent-review.json'),*guard_refs]
for item in failed['selectors'].values():all_input_refs.extend([item['review_ref'],*item['mode_decision_refs']])
g=m.guard()
try:
    g.acquire(all_input_refs)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    decision={'schema':'researchos.w09-three-selector-native-independent-decision.v1','review_author':'/root/full_w09_source_review','canonical_review_author':'codex:/root/full_w09_source_review','review_thread_id':THREAD,'producer_id':'codex:/root','Root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','issued_at':stamp,'status':'PARTIAL_NATIVE_MODE_QUALIFICATION','verdict':'G01_QUALIFIED_G02_A06_NOT_QUALIFIED','G01':{'decision':'QUALIFIED','checks':len(prior['checks'])+len(g01['new_checks']),**g01['mode_refs'],'actual_result_ref':m.pin(m.D/'G01.completed-review-result.json')},'failed_selectors':failed['selectors'],'fixture_candidate_source_review_ref':m.pin(m.D/'legacy-fixture-candidate.independent-review.json'),'fixture_candidate_verdict':fixture['verdict'],'fixture_checks':len(fixture['checks']),'guards_closed_refs':guard_refs,'actual_success_hostpairs':hosts,'reviewer_original_failure_refs':failures,'native_original_failure_ordinals':[1121,1125],'prior_Source_controls_repeated':False,'successful_G01_checks_repeated':False,'actual_product_runs_repeated':0,'Native_Source21_before_candidate_Main_change':True,'candidate_Main_change_invalidates_current_use_of_all_old_Source21_receipts':True,'execution_grant':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'current_formal_42_contract_reduced':False,'next_gate':'Root decides candidate adoption, then fresh current Source21 compiler/runtime/Native/C19/consumer revalidation; no failed selector may feed formal assembly.'}
    decision_ref=m.write('decision.json',decision)
finally:
    c=g.close();sealguard=m.write('seal-inputs.guard.closed.json',c);assert c['closed'] is True and c['retained_handles_count']==0 and not c['errors']
files=sorted(p for p in m.D.iterdir() if p.is_file() and p.name not in ('HDF.json','MF.json'))
manifest_ref=m.write('MF.json',{'schema':'researchos.w09-native-independent-review-manifest.v1','actor_id':'/root/full_w09_source_review','members':[m.pin(p) for p in files],'execution_grant':False,'formal_acceptance':False})
handoff={'schema':'researchos.w09-native-independent-review-handoff.v1','actor_id':'/root/full_w09_source_review','canonical_actor_id':'codex:/root/full_w09_source_review','thread_id':THREAD,'producer_id':'codex:/root','status':'PARTIAL_NATIVE_MODE_QUALIFICATION','verdict':decision['verdict'],'manifest_ref':manifest_ref,'decision_ref':decision_ref,'mode_results':{'W09-G01':decision['G01'],'W09-G02':failed['selectors']['W09-G02'],'A06':failed['selectors']['A06']},'fixture_source_review_ref':decision['fixture_candidate_source_review_ref'],'fixture_source_verdict':fixture['verdict'],'source_checks_reused_without_rerun':True,'guard_count':len(guard_refs)+1,'all_guards_closed':True,'retained_handles_count':0,'seal_guard_ref':sealguard,'diagnostic_original_ordinals':[1122,1126,1128,1130],'native_failure_ordinals':[1121,1125],'product_calls':0,'formal_acceptance':False,'execution_grant':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'STOP':True}
hdf_ref=m.write('HDF.json',handoff)
print(json.dumps({'HDF_ref':hdf_ref,'MF_ref':manifest_ref,'decision_ref':decision_ref,'verdict':decision['verdict'],'mode_results':handoff['mode_results'],'fixture_source_review_ref':handoff['fixture_source_review_ref'],'diagnostic_original_refs':failures,'all_guards_closed':True,'retained_handles_count':0,'product_calls':0,'execution_grant':False,'formal_acceptance':False,'STOP':True},ensure_ascii=False),flush=True)
