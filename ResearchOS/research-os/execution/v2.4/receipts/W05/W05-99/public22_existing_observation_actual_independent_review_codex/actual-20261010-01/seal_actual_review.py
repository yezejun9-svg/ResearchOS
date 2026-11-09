"""Seal Task64 actual component review and original1065 once."""
import hashlib
import json
import os
from pathlib import Path
import types

D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,obj):
    with (D/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def main():
    e=doc(D/'actual-independent-checks-v2.json');thread=os.environ['CODEX_THREAD_ID'];matches=[]
    for day in ('09','10'):matches.extend(Path('C:/Users/yqyyds/.codex/sessions/2026/10/'+day).glob('rollout-*-'+thread+'.jsonl'))
    assert len(matches)==1;log=matches[0];size=log.stat().st_size
    with log.open('rb') as f:
        head=f.readline();f.seek(max(len(head),size-16*1024*1024))
        if f.tell()!=len(head):f.readline()
        offset=f.tell();raw=f.read(size-offset)
    assert json.loads(head)['payload']['id']==thread
    calls={};pairs={};wanted={'0604fe','420c4b','f11baa'}
    for line in raw.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):offset+=len(line);continue
        payload=item.get('payload',{});cid=payload.get('call_id')
        if payload.get('type') in ('custom_tool_call','function_call') and cid:calls[cid]=(offset,line,item)
        elif payload.get('type') in ('custom_tool_call_output','function_call_output') and cid in calls:
            for chunk in wanted:
                if chunk not in pairs and chunk in str(payload.get('output','')):pairs[chunk]=(calls[cid],(offset,line,item))
        offset+=len(line)
    assert set(pairs)==wanted;archives=[]
    for chunk,(call,result) in sorted(pairs.items()):
        path=D/('actual-review-'+chunk+'.raw.jsonl')
        with path.open('xb') as f:f.write(head+call[1]+result[1])
        with log.open('rb') as f:
            for off,line in ((0,head),(call[0],call[1]),(result[0],result[1])):f.seek(off);assert f.read(len(line))==line
        binding=save('actual-review-'+chunk+'.binding.json',dict(schema='researchos.independent-actual-review-hostpair.v1',
            actor_id=ACTOR,reviewer_thread_id=thread,source_audit_path=str(log),source_prefix_size_observed=size,
            source_line_offsets=[0,call[0],result[0]],source_line_bytes=[len(head),len(call[1]),len(result[1])],
            original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (head,call[1],result[1])],
            original_capture_ref=pin(path),actual_call_id=call[2]['payload']['call_id'],actual_chunk_id=chunk,
            actual_outer_exit=1 if chunk=='420c4b' else 0,actual_Python_exit=1 if chunk=='420c4b' else 0,
            Root_assigned_original_ordinal=1065 if chunk=='420c4b' else None,Root_ordinal_self_assigned=False,
            Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None))
        archives.append(dict(chunk_id=chunk,raw_ref=pin(path),binding_ref=binding))
    for name in ('independent-Source-guard.closed.json','continuation-Source-guard.closed.json'):
        g=doc(D/name);assert g['closed'] is True and g['retained_handles_count']==0 and not g['errors']
    gp=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py')
    assert pin(gp)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm=types.ModuleType('public22_final_independent_Source_guard');gm.__file__=str(gp)
    exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
    refs=[pin(p) for p in sorted(D.iterdir()) if p.is_file()]+[e['input_bundle_ref']]
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    try:
        guard.acquire(refs);assert all(pin(r['path'])==r for r in refs)
    finally:
        closed=guard.close();gr=save('final-Source-guard.closed.json',closed)
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    decision=save('decision.json',dict(schema='researchos.public22-existing-artifacts-actual-independent-decision.v1',
        actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',reviewer_thread_id=thread,
        status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',decision='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',
        input_bundle_ref=e['input_bundle_ref'],actual_checks_ref=pin(D/'actual-independent-checks-v2.json'),
        original1065_prefix_ref=pin(D/'original1065-reused-prefix.json'),actual_review_hostpairs=archives,
        original1065=dict(Root_assigned_ordinal=1065,actual_chunk_id='420c4b',outer_exit=1,Python_exit=1,
            original_script_ref=pin(D/'review_actual.py'),original_guard_closed_ref=pin(D/'independent-Source-guard.closed.json'),
            issue="Review parser called .get on a list returned by structured_values; dict-filter-only continuation saved separately.",
            Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,reset=False),
        actual_original8_hostpairs_verified=True,actual_Root_build_check_activate_readonly_outer_Python_exits=[0,0,0,0],
        CP_OW_transition=[371,175,372,176],complete_inverse=True,TP_actual_committed=True,SS_CM39_unchanged=True,
        actual_scope_owner_worker_lease_valid_at_execution=True,actual_original_request_fields=3,actual_original_evidence_fields=9,
        actual_loaded_runtime_refs=149,actual_Source_guard_entries=933,actual_guard_closed0=True,
        old4_owned_children_FILETIME_exact_Python_decimal=e['old4_exact_FILETIME'],original1025_result='FAILED_RETAINED',
        readonly83_oracle_source_ref=e['readonly83_oracle_source_ref'],oracle_lines=e['oracle_lines'],
        oracle_qualification_basis='Exact successful actual pinned leaf call, immutable DB/backup baseline pins and all83 table predicates; no duplicate SQL query.',
        actual_reviewer_remaining_checks=len(e['checks']),already_verified_prefix_reused=True,unchanged_large_resources_not_rehashed=True,
        all_Source_guards_closed=True,retained_handles_count=0,final_guard_ref=gr,live_CP_OW_held=False,
        historical_Canon_refs_recursed=False,private_owner_or_recovery_key_read=False,Source_Canon_Main_written=False,
        SQL_queries_by_reviewer=0,new_Native_children_by_reviewer=0,Go_runs_by_reviewer=0,dispatcher_runs=0,model_calls=0,
        original_failure_ledger_reset=False,Root_ordinals_self_assigned=False,formal=False,formal_acceptance=False,parent_acceptance=False,
        execution_grant=False,Root_formal_acceptance_required=True,Root_current_dynamic_CAS_required=True,
        unresolved_product_paths=e['unresolved'],sealed_stop=True))
    manifest=save('MF.json',dict(schema='researchos.public22-existing-artifacts-actual-independent-manifest.v1',actor_id=ACTOR,
        members=[pin(p) for p in sorted(D.iterdir()) if p.is_file()]))
    handoff=save('HDF.json',dict(schema='researchos.public22-existing-artifacts-actual-independent-handoff.v1',actor_id=ACTOR,
        actor_role='INDEPENDENT_NON_AUTHOR_NON_EXECUTOR',reviewer_thread_id=thread,status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',
        manifest_ref=manifest,decision_ref=decision,input_bundle_ref=e['input_bundle_ref'],actual_checks_ref=pin(D/'actual-independent-checks-v2.json'),
        actual_review_hostpairs=archives,original1065_preserved=True,original1025_result='FAILED_RETAINED',
        all_Source_guards_closed=True,retained_handles_count=0,Source_guard_ref=gr,formal=False,formal_acceptance=False,parent_acceptance=False,
        execution_grant=False,unresolved_product_paths=e['unresolved'],sealed_stop=True))
    assert decision in doc(D/'MF.json')['members'] and doc(D/'HDF.json')['decision_ref']==decision
    print(json.dumps(dict(status='COMPONENT_EXISTING_ARTIFACTS_INTEGRATION_QUALIFIED',HDF=handoff,MF=manifest,decision=decision,
        all_Source_guards_closed=True,retained_handles_count=0,SQL_queries_by_reviewer=0,new_Native_children_by_reviewer=0,
        original1025_result='FAILED_RETAINED',original1065_preserved=True,STOP_TASK64=True),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
