"""Seal Task58 independent narrow Source conclusions, with original real IO."""
import hashlib
import json
import ntpath
import os
from pathlib import Path
import types

D=Path(__file__).resolve().parent
ACTOR='codex:/root/full_w09_source_review'
W=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def main():
    result=doc(D/'finite-source-checks.json'); evidence=doc(D/'exact-source-time-and-format.json')
    assert result['status']=='CHANGES_REQUIRED_SOURCE_ONLY' and result['model_only_no_qualification_created'] is True
    closed=doc(D/'Source-guard.closed.json')
    assert closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    thread=os.environ['CODEX_THREAD_ID'];logs=[]
    for day in ('09','10'):logs.extend(Path('C:/Users/yqyyds/.codex/sessions/2026/10/'+day).glob('rollout-*-'+thread+'.jsonl'))
    assert len(logs)==1
    log=logs[0];prefix=log.stat().st_size
    with log.open('rb') as f:
        head=f.readline();f.seek(max(len(head),prefix-32*1024*1024))
        if f.tell()!=len(head):f.readline()
        offset=f.tell();tail=f.read(prefix-offset)
    assert json.loads(head)['payload']['id']==thread
    calls={};pair=None
    for line in tail.splitlines(keepends=True):
        try:item=json.loads(line)
        except (ValueError,UnicodeDecodeError):offset+=len(line);continue
        payload=item.get('payload',{});cid=payload.get('call_id')
        if payload.get('type') in ('custom_tool_call','function_call') and cid:calls[cid]=(offset,line,item)
        elif payload.get('type') in ('custom_tool_call_output','function_call_output') and cid in calls:
            if pair is None and 'cd37e8' in str(payload.get('output','')):pair=(calls[cid],(offset,line,item))
        offset+=len(line)
    assert pair is not None
    first,last=pair
    raw=head+first[1]+last[1]
    raw_path=D/'actual-finite-review-cd37e8.raw.jsonl'
    with raw_path.open('xb') as f:f.write(raw)
    raw_ref=pin(raw_path)
    with log.open('rb') as f:
        for off,line in ((0,head),(first[0],first[1]),(last[0],last[1])):
            assert off+len(line)<=prefix;f.seek(off);assert f.read(len(line))==line
    own_binding_ref=save('actual-finite-review-cd37e8.binding.json',dict(
        schema='researchos.independent-source-review.actual-hostpair.v1',actor_id=ACTOR,reviewer_thread_id=thread,
        source_audit_path=str(log),source_prefix_size_observed=prefix,source_line_offsets=[0,first[0],last[0]],
        source_line_bytes=[len(head),len(first[1]),len(last[1])],
        original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (head,first[1],last[1])],
        original_capture_ref=raw_ref,actual_call_id=first[2]['payload']['call_id'],actual_chunk_id='cd37e8',
        actual_outer_exit=0,actual_Python_exit=0,Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,
        actual_qualification_created=False,formal_acceptance=False,execution_grant=False))
    refs=evidence['input_refs']+[pin(p) for p in sorted(D.iterdir()) if p.is_file()]
    for observation in result['actual_peer_observations']:refs.extend(observation['observed_delivered_refs'])
    unique={}
    for ref in refs:
        key=ntpath.normcase(ntpath.normpath(ref['path']))
        if key in unique:assert unique[key]['sha256']==ref['sha256'] and unique[key]['bytes']==ref['bytes']
        else:unique[key]=ref
    assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    gm=types.ModuleType('task58_final_source_guard');gm.__file__=str(G)
    exec(compile(G.read_bytes(),str(G),'exec'),gm.__dict__)
    guard=gm.SourceReadGuard()
    try:
        guard.acquire(list(unique.values()))
        for ref in unique.values():
            actual=pin(ref['path']);assert actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes']
    finally:
        final_closed=guard.close();final_guard_ref=save('final-Source-guard.closed.json',final_closed)
    assert final_closed['closed'] is True and final_closed['retained_handles_count']==0 and not final_closed['errors']
    source_ref=evidence['input_refs'][2];contract_ref=evidence['input_refs'][3]
    observations=result['actual_peer_observations']
    decision=save('decision.json',dict(schema='researchos.main23-time-and-peer-format-independent-source-decision.v1',
        review_author=ACTOR,reviewer_thread_id=thread,independent_non_author=True,verdict='CHANGES_REQUIRED',status='CHANGES_REQUIRED_SOURCE_ONLY',
        scope='TASK58_M3_TIME_CONTRACT_AND_NORMAL_FINAL_ENVELOPE_ONLY',source_caller_ref=source_ref,source_contract_ref=contract_ref,
        exact_source_evidence_ref=pin(D/'exact-source-time-and-format.json'),finite_checks_ref=pin(D/'finite-source-checks.json'),
        Task55_hdf_ref=evidence['input_refs'][4],Task55_mf_ref=evidence['input_refs'][5],Task55_decision_ref=evidence['input_refs'][6],
        Task55_verdict_preserved=evidence['Task55_verdict'],Task55_resources_not_requalified=True,
        findings=[
            dict(id='M3-TIME-01',priority='BLOCKER',source_ref=source_ref,lines=[320,322,365,367],contract_ref=contract_ref,
                conclusion='Honest distinct sequential payload and wrapper creation times cannot satisfy the exact M3 projection plus time order.',
                proof='Exact projection forces P=Q; an immutable payload exists before Root call C and actual return R, so P<C<R. M3 requires R<=Q=P, yielding P<C<R<=P.',
                nuance='The <= numeric predicates alone allow equality or a preselected future payload timestamp. Neither is evidence of actual causal creation.',
                minimum_revision=dict(wrapper_only_field='created_utc',exactly_bound_payload_field='payload_created_utc',
                    payload_fields='Replace payload.created_utc with payload_created_utc; include payload_created_utc in wrapper projection.',
                    wrapper_projection_exclusions=['schema','payload_ref','root_issuance_binding_ref','created_utc'],
                    exact_payload_rule='All payload fields except schema equal projected wrapper exactly, including payload_created_utc and all identity/ref/resource fields.',
                    required_order='scope.created <= review.reviewed <= actual peer receipt <= payload_created_utc <= actual Root call <= actual Root output <= wrapper.created_utc <= validating current UTC',
                    creation_rule='Use actual creation times at each step; never prefill a future timestamp to pass M3.',
                    contract_update='Publish a fresh immutable Source revision with the matching payload rule, field semantics and time order.')),
            dict(id='M3-PEER-FINAL-02',priority='BLOCKER',source_ref=source_ref,lines=[183,204,263,270],contract_ref=contract_ref,
                actual_peer_observations=observations,M3_rejection='PEER_TYPED_DELIVERY_REQUIRED',
                conclusion='Both normal backend FINAL bodies contain a fixed envelope before a complete multiline typed JSON; exact M3 structured_documents finds zero deliveries.',
                minimum_revision=dict(target='validate_peer_delivery only; keep Root tool stdout structured_documents semantics',
                    envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: <validated exact backend peer author>\nPayload:\n',
                    parsing='At the start only, require the exact FINAL envelope derived from the already validated peer actor and /root recipient. Strip that exact prefix and strict-decode exactly one entire JSON dictionary. Preserve exact complete plain JSON compatibility.',
                    reject='Wrong sender/recipient/message type, unanchored envelope, duplicate keys, extra JSON document or arbitrary digest-containing text.',
                    keep='Canonical actor and nonauthor exclusions; fixed Root thread/log; metadata adjacency/timestamps/client_authored=false; message id; original offset/byte/hash capture; typed operation/verdict/false grants; exact full ref sets.'))],
        finite_checks_count=len(result['checks']),actual_peer_capture_count=2,
        actual_review_toolpair=dict(raw_ref=raw_ref,binding_ref=own_binding_ref),
        Root_reported_original_1057_preserved=dict(ordinal=1057,chunk_id='599b63',outer_exit=1,Python_exit=1,
            source='Root actual message; existing Root record unchanged, no duplicate failure invocation',
            Go_exit=None,Native_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None),
        all_Source_guards_closed=True,retained_handles_count=0,final_guard_ref=final_guard_ref,
        actual_qualification_created=False,actual_registration=False,actual_prepare_run=False,
        actual_Go_runs=0,actual_Native_jobs=0,actual_SQL_runs=0,actual_dispatcher_runs=0,actual_model_calls=0,
        Source_written=False,Canon_written=False,Main_written=False,formal=False,formal_acceptance=False,execution_grant=False,
        original_failure_reset=False,Root_ordinals_self_assigned=False,old_20_and_14782_controls_not_rerun=True,sealed_stop=True))
    manifest=save('MF.json',dict(schema='researchos.main23-time-and-peer-format-independent-source-manifest.v1',
        review_author=ACTOR,members=[pin(p) for p in sorted(D.iterdir()) if p.is_file()]))
    handoff=save('HDF.json',dict(schema='researchos.main23-time-and-peer-format-independent-source-hdf.v1',
        review_author=ACTOR,reviewer_thread_id=thread,independent_non_author=True,status='CHANGES_REQUIRED_SOURCE_ONLY',
        manifest_ref=manifest,decision_ref=decision,source_caller_ref=source_ref,source_contract_ref=contract_ref,
        exact_source_evidence_ref=pin(D/'exact-source-time-and-format.json'),finite_checks_ref=pin(D/'finite-source-checks.json'),
        actual_review_toolpair=dict(raw_ref=raw_ref,binding_ref=own_binding_ref),
        actual_peer_captures=[dict(raw_ref=x['raw_ref'],binding_ref=x['binding_ref']) for x in observations],
        Source_guard_ref=final_guard_ref,all_Source_guards_closed=True,retained_handles_count=0,
        actual_qualification_created=False,formal=False,formal_acceptance=False,execution_grant=False,sealed_stop=True))
    assert doc(D/'HDF.json')['decision_ref']==decision and decision in doc(D/'MF.json')['members']
    for ref in doc(D/'MF.json')['members']:assert pin(ref['path'])==ref
    print(json.dumps(dict(status='CHANGES_REQUIRED_SOURCE_ONLY',HDF=handoff,MF=manifest,decision=decision,
        finite_checks_count=len(result['checks']),actual_peer_captures=[dict(raw_ref=x['raw_ref'],binding_ref=x['binding_ref']) for x in observations],
        actual_review_toolpair=dict(raw_ref=raw_ref,binding_ref=own_binding_ref),
        all_Source_guards_closed=True,retained_handles_count=0,qualification_created=False,products_started=0,STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
