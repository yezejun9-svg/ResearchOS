"""Seal blocked Source review; actual IO, inverse and original offset proofs."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import types

D = Path(__file__).resolve().parent
B = D.parent.parent
Q = B / 'schema21_root_caller_registration_source_codex/s21root-20261010-01'
AUDIT = Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T23-50-03-01a1215b-7210-7613-b033-756b9d553b83.jsonl')
ACTOR = 'codex:/root/full_w09_source_review'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(path):
    path = Path(path); raw = path.read_bytes()
    return dict(path=path.as_posix(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def doc(path): return json.loads(Path(path).read_bytes())

def save(name, value):
    with (D/name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
    return pin(D/name)

def module(path, name):
    value = types.ModuleType(name); value.__file__ = str(path)
    exec(compile(Path(path).read_bytes(), str(path), 'exec'), value.__dict__)
    return value

def check_hash(raw, ref):
    assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'], ref

def actual_finite_pair(m):
    size = AUDIT.stat().st_size; lower = max(0,size-64*1024*1024); calls={}; found=[]
    with AUDIT.open('rb') as stream:
        header = stream.readline(); stream.seek(lower)
        if lower: stream.readline()
        while stream.tell()<size:
            offset=stream.tell(); line=stream.readline()
            if offset+len(line)>size: break
            row=json.loads(line); payload=row.get('payload')
            if row.get('type')!='response_item' or type(payload) is not dict: continue
            if payload.get('type') in ('custom_tool_call','function_call'):
                calls[payload['call_id']]=(offset,line,row)
            elif payload.get('type') in ('custom_tool_call_output','function_call_output'):
                hosts=[x for x in m.structured_documents(payload.get('output')) if type(x) is dict and x.get('chunk_id')=='0e9134']
                if hosts: found.append((calls[payload['call_id']],(offset,line,row),hosts))
    assert len(found)==1 and len(found[0][2])==1
    first,last,hosts=found[0]; host=hosts[0]
    identity=json.loads(header)['payload']
    assert identity['id']==os.environ['CODEX_THREAD_ID']=='01a1215b-7210-7613-b033-756b9d553b83'
    assert identity['agent_path']==ACTOR.removeprefix('codex:') and identity['parent_thread_id']==ROOT_THREAD
    rows=[(0,header),(first[0],first[1]),(last[0],last[1])]
    with AUDIT.open('rb') as stream:
        for offset,line in rows:
            stream.seek(offset); assert stream.readline()==line
    with (D/'actual-finite-review-0e9134.raw.jsonl').open('xb') as stream:
        stream.write(b''.join(line for offset,line in rows))
    assert host['exit_code']==0 and 'Python_exit=0' in host['output']
    raw_ref=pin(D/'actual-finite-review-0e9134.raw.jsonl')
    binding_ref=save('actual-finite-review-0e9134.binding.json',dict(
        schema='researchos.old21-independent-caller-actual-review-host-binding.v1',review_author=ACTOR,
        reviewer_thread_id=identity['id'],parent_root_thread_id=ROOT_THREAD,source_audit_path=AUDIT.as_posix(),
        source_prefix_size_observed=size,source_line_offsets=[offset for offset,line in rows],
        source_line_bytes=[len(line) for offset,line in rows],original_line_sha256=[hashlib.sha256(line).hexdigest() for offset,line in rows],
        original_capture_ref=raw_ref,original_call_id=first[2]['payload']['call_id'],
        tool_call_timestamp=first[2]['timestamp'],tool_result_timestamp=last[2]['timestamp'],
        chunk_id='0e9134',actual_outer_exit=0,actual_python_exit=0,
        actual_native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
        original_failed_invocation=False,Root_assigned_original_ordinal=None,synthetic_control_results_are_not_product_results=True,
        counter_reset=False,execution_grant=False,formal_acceptance=False))
    return raw_ref,binding_ref

def inverse(m, source):
    chain=doc(source['inverse_ref']['path']); layers=[doc(x['path']) for x in chain['layer_refs']]
    raw=Path(source['caller_ref']['path']).read_bytes(); check_hash(raw,chain['candidate_ref']); outcomes=[]
    for layer in reversed(layers[1:]):
        check_hash(raw,layer['candidate_ref'])
        if 'inserted_constant' in layer:
            for field in ('inserted_condition','inserted_constant'):
                token=layer[field].replace('\\n','\n').encode()
                if raw.count(token)!=1 and raw.count(token.replace(b'\n',b'\r\n'))==1:
                    token=token.replace(b'\n',b'\r\n')
                assert raw.count(token)==1,field
                raw=raw.replace(token,b'',1)
        else:
            new,old=bytes.fromhex(layer['new_hex']),bytes.fromhex(layer['old_hex'])
            assert raw.count(new)==1
            raw=raw.replace(new,old,1)
        check_hash(raw,layer['initial_ref']); outcomes.append(dict(restored_ref=layer['initial_ref'],restored_exact_bytes=True))
    base_layer=layers[0]; check_hash(raw,base_layer['candidate_ref'])
    for span in reversed(base_layer['spans']):
        a,b=span['candidate_start'],span['candidate_end']
        assert raw[a:b]==bytes.fromhex(span['candidate_hex'])
        raw=raw[:a]+bytes.fromhex(span['base_hex'])+raw[b:]
    check_hash(raw,chain['base_ref'])
    assert raw==Path(source['base_caller_ref']['path']).read_bytes()
    return save('independent-full-Source-inverse.json',dict(schema='researchos.old21-independent-caller-full-inverse.v1',
        source_chain_ref=source['inverse_ref'],layer_refs=chain['layer_refs'],candidate_ref=source['caller_ref'],base_ref=source['base_caller_ref'],
        intermediate_restorations=outcomes,byte_spans=len(base_layer['spans']),entire_original_bytes_restored=True,
        inverse_in_memory_only=True,Source_only=True,actual_TP_called=False))

def original_Source_hosts(m, source):
    index=doc(source['actual_Source_toolpairs_ref']['path']); results=[]
    for pair in index['complete_returned_toolpairs']:
        binding=doc(pair['binding_ref']['path']); raw=Path(pair['raw_ref']['path']).read_bytes(); check_hash(raw,pair['raw_ref'])
        lines=raw.splitlines(keepends=True); assert len(lines)==3
        assert [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']
        assert [len(x) for x in lines]==binding['source_line_bytes']
        with Path(binding['source_audit_path']).open('rb') as stream:
            for offset,line in zip(binding['source_line_offsets'],lines):
                assert type(offset) is int and offset>=0 and offset+len(line)<=binding['source_prefix_size_observed']
                stream.seek(offset); assert stream.readline()==line
        header,first,last=[json.loads(x) for x in lines]
        assert header['type']=='session_meta' and header['payload']['id']==source['source_thread_id']
        assert header['payload']['agent_path']==source['source_author'].removeprefix('codex:') and header['payload']['parent_thread_id']==ROOT_THREAD
        assert first['payload']['call_id']==last['payload']['call_id']==binding['original_call_id']==pair['call_id']
        assert first['timestamp']==binding['tool_call_timestamp'] and last['timestamp']==binding['tool_result_timestamp']
        hosts=[x for x in m.structured_documents(last['payload']['output']) if type(x) is dict and type(x.get('chunk_id')) is str and type(x.get('output')) is str]
        results.append(dict(call_id=pair['call_id'],raw_ref=pair['raw_ref'],binding_ref=pair['binding_ref'],original_bytes_and_offsets_verified=True,
            hosts=[dict(chunk_id=x['chunk_id'],actual_outer_exit=x.get('exit_code')) for x in hosts]))
    return save('actual-Source-author-toolpair-offsets-verified.json',dict(schema='researchos.old21-independent-Source-author-host-audit.v1',
        Source_index_ref=source['actual_Source_toolpairs_ref'],source_author=source['source_author'],source_thread_id=source['source_thread_id'],
        root_parent_thread_id=ROOT_THREAD,complete_pairs=results,pair_count=len(results),
        old_original_failures=source['old_original_failures'],old_failed_guard_status=source['Source_old_failed_guard_status'],
        unknown_exits_not_inferred=True,old_originals_retained=True,actual_Root_review_witness_created=False))

def main():
    source=doc(Q/'HDF.json'); m=module(Q/'old21_root.source.py','old21_seal_inert')
    finite=doc(D/'finite-Source-review.json'); assert finite['unexpected_check_failures']==0 and finite['check_count']==32 and len(finite['blocking_findings'])==2
    closed=doc(D/'independent-Source-guard.closed.json'); assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
    audit_raw,audit_binding=actual_finite_pair(m)
    guard_module=module(m.GUARD_REF['path'],'old21_seal_source_guard')
    guard=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    source_mf=doc(Q/'MF.json')
    initial_refs=[pin(Q/'HDF.json'),pin(Q/'MF.json'),pin(D/'finite-Source-review.json'),pin(D/'independent-Source-guard.closed.json'),audit_raw,audit_binding]+source_mf['members']
    try:
        guard.acquire(m.local_refs(initial_refs,m.CANON))
        inv=inverse(m,source)
        author_hosts=original_Source_hosts(m,source)
    finally:
        c=guard.close(); metadata_guard=save('metadata-and-inverse-Source-guard.closed.json',c)
    assert c['closed'] and c['retained_handles_count']==0 and not c['errors']
    when=datetime.now(timezone.utc).isoformat()
    bindings=dict(source_hdf_ref=pin(Q/'HDF.json'),source_mf_ref=pin(Q/'MF.json'),caller_ref=source['caller_ref'],registrar_ref=source['registrar_ref'],calling_contract_ref=source['contract_ref'])
    decision=save('decision.json',dict(schema='researchos.old21-caller-independent-source-decision.v1',status='CHANGES_REQUIRED',verdict='CHANGES_REQUIRED',
        review_author=ACTOR,source_author=source['source_author'],builder_source_author=source['builder_source_author'],root_thread_id=ROOT_THREAD,
        reviewer_thread_id=os.environ['CODEX_THREAD_ID'],independent_non_author=True,reviewed_utc=when,**bindings,
        blocking_findings=finite['blocking_findings'],finitechecks_ref=pin(D/'finite-Source-review.json'),Source_guard_ref=pin(D/'independent-Source-guard.closed.json'),
        metadata_and_inverse_guard_ref=metadata_guard,actual_review_raw_ref=audit_raw,actual_review_binding_ref=audit_binding,
        actual_Task68_Root_peer_observation_ref=finite['actual_Task68_peer_observation_ref'],Source_author_original_host_audit_ref=author_hosts,full_Source_inverse_ref=inv,
        new_failed_invocations=[],original_Source_failures_retained=source['old_original_failures'],original_failed_guard_status=source['Source_old_failed_guard_status'],
        historical_guard_unknown_not_inferred_closed=True,current_review_guards_closed=True,retained_handles_count=0,
        reused_builder_review_refs=finite['reused_builder_review_refs'],builder853_controls_reexecuted=False,
        current4_policy='Read only archived CP373/OW177/SS/CM39; Root must refresh dynamic live refs for a future corrected Source.',
        Root_operation_correction=dict(final_schema='researchos.old21-peer-review-delivery.v2',final_operation='SOURCE_REVIEW_WITNESS',
            prior_CALLER_SOURCE_REVIEW_WITNESS_dispatch_was_Root_error=True,Source_blocker=False),
        retained_gates=dict(full_legacy_SQL21_and_session_addon='Pinned accepted Builder Source retained; no compiler rerun',
            Canon='Dynamic current4/CAS complete inverse/lease gates retained except confirmed pending counter rollback',
            Owned_Job_FILETIME='Accepted Builder source unchanged; exact integer proof reused, no Native call',
            runtime='Independent resource Scope + full runtime manifest + real peer/root pair causality remain required',
            peer='Exact original sender/recipient/metadata/message ID/offsets and whole anchored JSON remain required'),
        actual_paths_still_OPEN=['Root revised Caller Source independent acceptance','Root new old21 resource-only Scope and independent runtime closure','Root real external review/current4/prerequisite captures','Root separate owner/worker/lease registration TP','Actual old21 offline dual control/backup build and external returned hostpair','Independent candidate programme qualification and formal acceptance'],
        source_only=True,synthetic_conditions_are_not_Root_grants=True,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
        formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,actual_runtime_qualification_created=False,
        actual_Go_Native_SQL_model_dispatcher_TP_calls=0,live_Canon_held=0,STOP=True))
    local=[pin(p) for p in sorted(D.iterdir()) if p.is_file() and p.name not in ('HDF.json','MF.json')]
    mf=save('MF.json',dict(schema='researchos.old21-caller-independent-source-manifest.v1',review_author=ACTOR,source_author=source['source_author'],members=local,
        excluded=['HDF.json','MF.json','postpublication guard, negative admission and seal outputs'],formal_acceptance=False,execution_grant=False))
    hdf=save('HDF.json',dict(schema='researchos.old21-caller-independent-source-handoff.v1',status='CHANGES_REQUIRED',review_author=ACTOR,source_author=source['source_author'],
        builder_source_author=source['builder_source_author'],root_thread_id=ROOT_THREAD,reviewer_thread_id=os.environ['CODEX_THREAD_ID'],independent_non_author=True,
        reviewed_utc=when,**bindings,manifest_ref=mf,source_decision_ref=decision,decision_ref=decision,
        finitechecks_ref=pin(D/'finite-Source-review.json'),Source_guard_ref=pin(D/'independent-Source-guard.closed.json'),metadata_and_inverse_guard_ref=metadata_guard,
        actual_review_raw_ref=audit_raw,actual_review_binding_ref=audit_binding,blocking_findings_count=2,Source_checks_expected_observations=32,
        Source_checks_unexpected_failures=0,old_original_Source_failures_retained=source['old_original_failures'],original_failed_guard_status=source['Source_old_failed_guard_status'],
        current_review_guards_closed=True,retained_handles_count=0,Source_only=True,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
        formal_programme_qualification=False,candidate_program_ref=None,qualification_ref=None,STOP=True))
    published=guard_module.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:
        published.acquire(m.local_refs([hdf,mf,decision]+local+[pin(Q/'HDF.json'),pin(Q/'MF.json'),source['caller_ref'],source['contract_ref']]))
        request=dict(source_hdf_ref=bindings['source_hdf_ref'],source_mf_ref=bindings['source_mf_ref'],review_hdf_ref=hdf,review_mf_ref=mf,review_decision_ref=decision,
            Source_only_interface_check=True)
        try:
            m.own_review(request)
        except ValueError as exc:
            assert str(exc)=='CALLER_NONAUTHOR_REVIEW_REQUIRED'; blocked=str(exc)
        else:
            raise ValueError('BLOCKED_REVIEW_MUST_NOT_ADMIT_ROOT_EXECUTION')
        assert all(pin(ref['path'])['sha256']==ref['sha256'] and pin(ref['path'])['bytes']==ref['bytes'] for ref in (hdf,mf,decision))
    finally:
        c=published.close(); published_guard=save('published-review-Source-guard.closed.json',c)
    assert c['closed'] and c['retained_handles_count']==0 and not c['errors']
    admission=save('published-negative-admission.json',dict(schema='researchos.old21-independent-published-Source-review-admission.v1',
        review_refs=[hdf,mf,decision],production_own_review_rejection=blocked,Root_witness_never_loaded=True,
        Source_only_in_memory_request=True,Root_request_or_grant_created=False,Source_guard_ref=published_guard,
        execution_grant=False,formal_acceptance=False))
    seal=save('complete-independent-Source-review-seal.json',dict(status='CHANGES_REQUIRED',review_refs=[hdf,mf,decision],
        published_negative_admission_ref=admission,published_guard_ref=published_guard,actual_review_raw_ref=audit_raw,actual_review_binding_ref=audit_binding,
        all_current_review_guards_closed=True,retained_handles_count=0,old_failed_guards_remain_unknown=True,
        original_Source_failures_retained=source['old_original_failures'],new_failed_invocations=[],execution_grant=False,formal_acceptance=False,STOP=True))
    print(json.dumps(dict(status='CHANGES_REQUIRED',review_refs=[hdf,mf,decision],seal_ref=seal,guard_ref=published_guard,actual_review_raw_ref=audit_raw,
        actual_review_binding_ref=audit_binding,checks=32,blockers=2,closed0=True,execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))

if __name__=='__main__': main()
