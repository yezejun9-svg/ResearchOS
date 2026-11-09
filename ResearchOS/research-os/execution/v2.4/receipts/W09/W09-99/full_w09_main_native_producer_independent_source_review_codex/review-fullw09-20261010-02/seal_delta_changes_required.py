"""Seal immutable v2 blocker evidence and the original actual reviewer IO."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
S=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-02'
D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
    with (D/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def main():
    reviewed=load(D/'complete-authority-shape-and-real-blockers-v2.json')
    assert reviewed['status']=='CHANGES_REQUIRED' and reviewed['all_Source_guards_closed'] is True and reviewed['retained_handles_count']==0
    c=load(S/'source.choice.json');contract=load(S/'root-calling-contract.json')
    thread=os.environ['CODEX_THREAD_ID'];matches=[]
    for day in ('09','10'):matches.extend(Path('C:/Users/yqyyds/.codex/sessions/2026/10/'+day).glob('rollout-*-'+thread+'.jsonl'))
    assert len(matches)==1
    log=matches[0];size=log.stat().st_size
    with log.open('rb') as f:
        header=f.readline();f.seek(max(len(header),size-64*1024*1024))
        if f.tell()!=len(header):f.readline()
        offset=f.tell();raw=f.read(size-offset)
    assert json.loads(header)['payload']['id']==thread
    calls={};pairs={};diagnostic=None
    wanted={'168ba0','f2df44','11a21f','a13189','6a7a87','6a626f'}
    for line in raw.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):offset+=len(line);continue
        payload=item.get('payload',{});kind=payload.get('type');cid=payload.get('call_id')
        if kind in ('function_call','custom_tool_call') and cid:calls[cid]=(offset,line,item)
        elif kind in ('function_call_output','custom_tool_call_output') and cid in calls:
            output=str(payload.get('output',''))
            for chunk in wanted:
                if chunk in output and chunk not in pairs:pairs[chunk]=(calls[cid],(offset,line,item))
            if diagnostic is None and 'Cannot find path' in output and 'root-actor-map-controls.json' in output and 'root-actor-map-controls.json' in str(calls[cid][2]['payload']):
                diagnostic=(calls[cid],(offset,line,item))
        offset+=len(line)
    assert set(pairs)==wanted and diagnostic is not None
    pairs['original1047-unknown-exit-read-diagnostic']=diagnostic
    archive=[]
    root_ordinals={'168ba0':1051,'f2df44':1052,'11a21f':1053,'original1047-unknown-exit-read-diagnostic':1047}
    for name,(call,result) in sorted(pairs.items()):
        target=D/('actual-'+name+'.raw.jsonl')
        with target.open('xb') as f:f.write(header+call[1]+result[1])
        with log.open('rb') as f:
            for off,original in zip([0,call[0],result[0]],(header,call[1],result[1])):
                f.seek(off);assert f.read(len(original))==original
        py=1 if name in ('168ba0','f2df44','11a21f') else 0 if name in ('a13189','6a7a87') else None
        outer=1 if name in ('168ba0','f2df44','11a21f') else 0 if name in ('a13189','6a626f') else None
        binding=save('actual-'+name+'.binding.json',dict(schema='researchos.independent-source-review.actual-hostpair.v1',actor_id=ACTOR,
            reviewer_thread_id=thread,source_audit_path=str(log),source_prefix_size_observed=size,
            source_line_offsets=[0,call[0],result[0]],source_line_bytes=[len(header),len(call[1]),len(result[1])],
            original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header,call[1],result[1])],
            original_capture_ref=pin(target),actual_call_id=call[2]['payload']['call_id'],actual_chunk_id=name,
            actual_Python_exit=py,actual_outer_exit=outer,Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,
            Root_assigned_original_failure_ordinal=root_ordinals.get(name),self_assigned_Root_ordinal=False))
        archive.append(dict(name=name,binding_ref=binding,raw_ref=pin(target),Root_assigned_original_failure_ordinal=root_ordinals.get(name)))
    failure_ref=save('original-failures-preserved.json',dict(originals=[
        dict(Root_ordinal=1047,diagnostic='Read query used nonexistent root-actor-map-controls.json; actual file inventory preserved.',
             actual_outer_exit=None,Python_exit=None,Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None),
        dict(Root_ordinal=1051,chunk_id='168ba0',actual_outer_exit=1,Python_exit=1,error="SyntaxError: '(' was never closed",line=133,
             original_script_ref=pin(D/'original-failure-168ba0.script.py'),Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None),
        dict(Root_ordinal=1052,chunk_id='f2df44',actual_outer_exit=1,Python_exit=1,error='AssertionError: actual_new_author_delivery_found',line=176,
             original_script_ref=pin(D/'original-failure-f2df44.script.py'),Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None),
        dict(Root_ordinal=root_ordinals['11a21f'],Root_assignment_pending=False,chunk_id='11a21f',actual_outer_exit=1,Python_exit=1,error="NameError: name 'hashlib' is not defined",line=100,
             original_script_ref=pin(D/'authority_shape_continuation.py'),Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None)],
        actual_hostpairs=archive,prior_originals_preserved=[1042,1044,1045],failure_reset=False,
        one_record_per_actual_failure_invocation=True,automatic_retry=False,new_input_corrections_explicit=True))
    for name in ('delta-Source-guard.closed.json','continuation-Source-guard.closed.json','continuation-v2-Source-guard.closed.json'):
        obj=load(D/name);assert obj['closed'] is True and obj['retained_handles_count']==0 and not obj['errors']
    gm=types.ModuleType('delta_final_source_guard');gm.__file__=c['common']['guard_ref']['path']
    assert pin(gm.__file__)==c['common']['guard_ref']
    exec(compile(Path(gm.__file__).read_bytes(),gm.__file__,'exec'),gm.__dict__)
    refs=[pin(S/'HDF.json'),pin(S/'MF.json'),*load(S/'MF.json')['members'],*c['common']['source21'],
          *[pin(p) for p in sorted(D.iterdir()) if p.is_file()]]
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        guard.acquire(refs);assert all(pin(ref['path'])==ref for ref in refs)
    finally:
        closed=guard.close();guard_ref=save('final-delta-Source-guard.closed.json',closed)
    assert closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0
    bound={key:pin(S/name) for key,name in contract['source_file_bindings'].items()}
    decision=dict(schema=contract['review_schema'],decision='CHANGES_REQUIRED',status='CHANGES_REQUIRED',actor_id=ACTOR,
        actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=thread,source_handoff_ref=pin(S/'HDF.json'),source_manifest_ref=pin(S/'MF.json'),
        calling_contract_ref=pin(S/'root-calling-contract.json'),**bound,selectors=c['selectors'],source21=c['common']['source21'],
        findings=reviewed['findings'],complete_authority_controls_ref=pin(D/'complete-authority-shape-and-real-blockers-v2.json'),
        new_peer_controls_reproduced_ref=pin(D/'reproduced-peer-audit-controls.json'),actual_author_peer_ref=reviewed['source_author_real_peer_ref'],
        actual_author_peer_has_full_digest=False,prior_69_and_112_reused_not_rerun=True,new_20_controls_reproduced_once=True,
        complete_Scope_fields_checked=reviewed['complete_Scope_fields_checked'],complete_request_fields_checked=reviewed['complete_request_fields_checked'],
        finite_complete_authority_checks=len(reviewed['checks']),whole_chain_positive='IN_MEMORY_ONLY_THREE_MOCK_AUDITS_AND_PROVEN_PACKAGE_GATE_BYPASS',
        actual_package_refs_rejected='SOURCE_PACKAGE',actual_author_peer_rejected='AUDIT_ARTIFACT_BINDING',
        compiler_blueprint_unchanged=True,source_compiler_package_count=None,new_runs_distinct_and_paths_absent=True,
        original_failure_record_ref=failure_ref,actual_hostpairs=archive,all_Source_guards_closed=True,retained_handles_count=0,final_guard_ref=guard_ref,
        actual_executed=False,actual_prepare_run=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_provider_calls=0,
        execution_grant=False,formal=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,
        Main_written=False,Canon_written=False,current_CanonicalPair_held=False,automatic_retry=False,Root_ordinals_self_assigned=False,
        exact_scope_required_fields=contract['scope_required_fields'],exact_request_fields=contract['request_exact_fields'],
        exact_actual_capture_fields=['schema','actor_id','Root_thread_id','source_audit_path','source_line_offsets','original_line_sha256',
            'source_prefix_size_observed','original_capture_ref','binding_sha256'],
        current_future_argv_interface=contract['future_argv'],
        Root_next_gate='New immutable Source revision: exact Source-only HDF/runtime package status compatibility; real author final delivery full path/SHA256/bytes; non-author Source review; then Root fresh per-selector Scope/lease/Canon/request.',
        no_actualprepare_or_actualrun_request=True,sealed_stop=True)
    dr=save('source-review-decision.json',decision)
    mr=save('MF.json',dict(schema='researchos.w09-three-selector-independent-source-review-manifest.v1',actor_id=ACTOR,
        members=[pin(p) for p in sorted(D.iterdir()) if p.is_file()]))
    hr=save('HDF.json',dict(schema='researchos.w09-three-selector-independent-source-review-handoff.v1',actor_id=ACTOR,
        actor_role='INDEPENDENT_NON_AUTHOR',reviewer_thread_id=thread,status='CHANGES_REQUIRED',manifest_ref=mr,source_decision_ref=dr,
        source_handoff_ref=decision['source_handoff_ref'],source_manifest_ref=decision['source_manifest_ref'],calling_contract_ref=decision['calling_contract_ref'],
        complete_authority_controls_ref=decision['complete_authority_controls_ref'],original_failure_record_ref=failure_ref,final_guard_ref=guard_ref,
        actual_executed=False,execution_grant=False,formal=False,formal_case_accepted_delta=0,formal_acceptance=False,
        all_Source_guards_closed=True,retained_handles_count=0,Main_written=False,Canon_written=False,sealed_stop=True,
        next_gate=decision['Root_next_gate']))
    runtime=types.ModuleType('seal_pair_runtime');runtime.__file__=str(S/'full_w09_runtime.source.py')
    exec(compile(Path(runtime.__file__).read_bytes(),runtime.__file__,'exec'),runtime.__dict__)
    obj,members=runtime.pair(hr,mr);assert obj['source_decision_ref']==dr and dr in members
    print(json.dumps(dict(status='CHANGES_REQUIRED',HDF=hr,MF=mr,decision=dr,
        complete_Scope_fields_checked=decision['complete_Scope_fields_checked'],complete_request_fields_checked=decision['complete_request_fields_checked'],
        finite_complete_authority_checks=decision['finite_complete_authority_checks'],all_Source_guards_closed=True,retained_handles_count=0,
        actual_Go_runs=0,actual_Native_runs=0,formal_case_accepted_delta=0,execution_grant=False,STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
