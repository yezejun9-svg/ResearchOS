"""Seal independent candidate checks and actual initial/completed host records."""
from pathlib import Path
import datetime, hashlib, json, types
R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D

def capture_start(chunk):
    size=s.LOG.stat().st_size;calls={};matches=[]
    with s.LOG.open('rb') as f:
        header=f.readline();assert json.loads(header)['payload']['id']==s.THREAD
        f.seek(max(0,size-64*1024*1024))
        if f.tell():f.readline()
        while f.tell()<size:
            offset=f.tell();line=f.readline();row=json.loads(line);v=row.get('payload',{})
            if v.get('type')=='custom_tool_call':calls[v['call_id']]=(offset,line,row)
            elif v.get('type')=='custom_tool_call_output':
                values=[x for x in s.docs(v.get('output')) if x.get('chunk_id')==chunk]
                if values and v['call_id'] in calls:matches.append((calls[v['call_id']],(offset,line,row),values))
    assert len(matches)==1 and len(matches[0][2])==1
    call,result,values=matches[0];value=values[0]
    assert value.get('session_id')==59261 and value.get('exit_code') is None
    lines=[header,call[1],result[1]];offsets=[0,call[0],result[0]]
    with s.LOG.open('rb') as f:
        for offset,line in zip(offsets,lines):f.seek(offset);assert f.read(len(line))==line
    rawpath=D/('actual-'+chunk+'.raw.jsonl')
    with rawpath.open('xb') as f:f.write(b''.join(lines))
    raw=s.pin(rawpath)
    binding=s.write('actual-'+chunk+'.binding.json',dict(schema='researchos.w09-main-candidate-review-host-binding.v1',
        actor_id=s.ACTOR,actor_thread_id=s.THREAD,source_audit_path=str(s.LOG),source_prefix_size_observed=size,
        source_line_offsets=offsets,original_line_sha256=[hashlib.sha256(line).hexdigest() for line in lines],
        original_line_bytes=[len(line) for line in lines],original_raw_ref=raw,actual_call_id=call[2]['payload']['call_id'],
        actual_chunk_id=chunk,actual_session_id=59261,actual_outer_exit=None,actual_Python_exit=None,
        actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,
        actual_dispatcher_exit=None,actual_RootStage_exit=None,actual_model_exit=None,
        state='RUNNING_NO_EXIT_OBSERVED_AT_INITIAL_RETURN',product_calls=0,execution_grant=False,formal_acceptance=False))
    return dict(raw_ref=raw,binding_ref=binding)

initial_host=capture_start('6f0529')
completed_host=s.capture('7b29d2',0,0)
inspection_host=s.capture('58f7b9',0,0)
refs=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file()]
refs.append(s.pin(HELPER))
g=s.guard()
try:
    g.acquire(refs)
    result=json.loads(g.get_buffer(str(D/'independent-review-result.json')))
    inventory=json.loads(g.get_buffer(str(D/'input-inventory.json')))
    closed=json.loads(g.get_buffer(result['source_guard_ref']['path']))
    assert result['failure'] is None and result['count']==result['passed']==len(result['checks'])==47
    assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    assert len(result['actual_candidate_native_rows'])==6
    assert len({row['run_id'] for row in result['actual_candidate_native_rows']})==4
finally:
    seal_guard_ref=s.write('seal-source-guard.closed.json',g.close())

now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
guards=[]
for path in (D/'source-guard.closed.json',D/'seal-source-guard.closed.json'):
    value=json.loads(path.read_bytes());assert value['closed'] is True and value['retained_handles_count']==0 and value['errors']==[]
    guards.append(dict(ref=s.pin(path),held_count=len(value['entries']),closed=True,retained_handles_count=0))
decision=dict(schema='researchos.w09-main-router-sequence-independent-source-decision.v1',
    decision='ACCEPTED_SOURCE_ONLY',reviewer_id='codex:/root/full_w09_source_review',
    backend_reviewer_id=s.ACTOR,reviewer_role='INDEPENDENT_NON_AUTHOR',source_author='codex:/root',
    reviewer_thread_id=s.THREAD,Root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',reviewed_utc=now,
    candidate_ref=inventory['candidate_ref'],before_ref=inventory['before_ref'],target_Main_ref=inventory['current_Main_ref'],
    proposal_ref=inventory['proposal_ref'],actual_seed_ref=inventory['seed_ref'],
    single_changed_line=642,change='exact_ids(list(router["FORMAL"][route]), IDS[key], "router formal IDs")',
    diff_ref=s.pin(D/'independent-candidate.diff'),independent_result_ref=s.pin(D/'independent-review-result.json'),
    byte_inverse_complete=True,only_changed_function='_native',all_other_AST_unchanged=True,
    new_checks=result['count'],passed=result['passed'],findings=[],
    candidate_actual_readonly_route_checks=result['actual_candidate_native_rows'],
    existing_Mode_decisions_reissued=False,existing_Native_runs_replayed=False,Native_Source21_changed=False,
    candidate_Main_runtime_only=True,current_Main_qualified_as_candidate=False,
    old_Main_vector_preserved_during_review=True,all_guards_closed=True,retained_handles_count=0,guard_evidence=guards,
    actual_host_pairs=[inspection_host,initial_host,completed_host],
    original1208='FAILED_RETAINED',other_existing_failure_counters_reset=False,new_review_failures=[],
    product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0),
    private_key_reads=0,live_CP_OW_SS_handles=0,Main_writes=0,Canon_writes=0,Scope_writes=0,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
    future_Root_requirements=[
        'Root must perform the separately authorized exact one-target Main adoption CAS against target_Main_ref, retaining the old bytes and actual hostpair.',
        'After actual Main adoption, publish and independently review a fresh BR7 with the new exact trusted profile pin and generation; do not modify sealed BR6.',
        'Rebuild the context seed and formal version vector with the newly adopted Main hash. The old fixed seed remains historical and cannot become current by relabeling.',
        'Reuse the four genuine Native reports and six genuine Mode decisions subject to the unchanged gates: formal_profile_w09.py is outside Native Source21, and this delta changes neither native argv nor owned facts.',
        'Subsequent Root stages still require their own fresh Scope/current4/owner/worker/lease and unchanged TP/CAS, role and six-consumer contracts.'
    ],STOP=True)
decision_ref=s.write('decision.json',decision)
members=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file() and path.name not in ('HDF.json','MF.json')]
assert decision_ref in members
mf_ref=s.write('MF.json',dict(schema='researchos.w09-main-router-sequence-independent-review-MF.v1',members=members))
hdf_ref=s.write('HDF.json',dict(schema='researchos.w09-main-router-sequence-independent-review-HDF.v1',
    status='ACCEPTED_SOURCE_ONLY',review_author=decision['reviewer_id'],backend_reviewer_id=s.ACTOR,
    reviewer_role='INDEPENDENT_NON_AUTHOR',source_author='codex:/root',reviewed_utc=now,
    source_decision_ref=decision_ref,manifest_ref=mf_ref,candidate_ref=inventory['candidate_ref'],
    before_ref=inventory['before_ref'],target_Main_ref=inventory['current_Main_ref'],proposal_ref=inventory['proposal_ref'],
    actual_seed_ref=inventory['seed_ref'],new_checks=result['count'],passed=result['passed'],
    actual_readonly_candidate_routes=6,actual_existing_Native_runs=4,
    guard_evidence=guards,all_guards_closed=True,retained_handles_count=0,
    actual_host_pairs=decision['actual_host_pairs'],new_review_failures=[],
    Native_Source21_changed=False,candidate_only=True,Main_writes=0,Canon_writes=0,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,STOP=True))
print(json.dumps(dict(schema='researchos.w09-main-router-sequence-independent-review-delivery.v1',
    operation='SOURCE_REVIEW_WITNESS',review_author=decision['reviewer_id'],backend_actor_id=s.ACTOR,
    source_author='codex:/root',verdict='ACCEPTED_SOURCE_ONLY',review_refs=[hdf_ref,mf_ref,decision_ref],
    candidate_ref=inventory['candidate_ref'],passed=result['passed'],new_checks=result['count'],
    candidate_only=True,actual_readonly_routes=6,existing_Native_runs=4,Native_Source21_changed=False,
    guards_closed=True,retained_handles_count=0,new_review_failures=[],
    Main_writes=0,Canon_writes=0,execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True),ensure_ascii=False))
