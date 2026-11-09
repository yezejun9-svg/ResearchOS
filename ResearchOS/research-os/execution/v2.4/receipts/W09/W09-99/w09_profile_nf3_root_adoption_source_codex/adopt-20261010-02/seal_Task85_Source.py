"""Seal the minimal Task85 revision and real Source-process evidence only."""
import ast, base64, hashlib, json, types
from pathlib import Path

Q = Path(__file__).resolve().parent
AUTHOR = 'codex:/root/backup_regression_resources'
THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'
LOG = Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    path=Path(path); raw=path.read_bytes()
    return dict(path=str(path),sha256=sha(raw),bytes=len(raw))
def encoded(value): return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save_raw(name,raw):
    path=Q/name
    with path.open('xb') as handle: handle.write(raw)
    return pin(path)
def save(name,value): return save_raw(name,encoded(value))

def capture_source():
    prefix=LOG.stat().st_size; calls={}; pairs=[]; offset=0
    with LOG.open('rb') as handle:
        hraw=handle.readline(); header=json.loads(hraw)
        assert header['payload']['id']==THREAD
        offset=len(hraw)
        while offset<prefix:
            raw=handle.readline()
            if not raw or offset+len(raw)>prefix: break
            row=json.loads(raw); payload=row.get('payload',{}); kind=payload.get('type'); cid=payload.get('call_id')
            if kind in ('function_call','custom_tool_call') and cid:
                source=str(payload.get('input',payload.get('arguments','')))
                if 'task85_' in source: calls[cid]=(offset,raw,row)
            if kind in ('function_call_output','custom_tool_call_output') and cid in calls:
                pairs.append((calls[cid],(offset,raw,row)))
            offset+=len(raw)
    assert pairs
    result=[]
    for call,returned in pairs:
        cid=call[2]['payload']['call_id']; token=sha(cid.encode())[:24]
        chosen=[(0,hraw,header),call,returned]
        rawref=save_raw('actual-source-'+token+'.raw.jsonl',b''.join(row[1] for row in chosen))
        binding=save('actual-source-'+token+'.binding.json',dict(
            schema='researchos.actual-Source-tool-capture-binding.v1',source_actor=AUTHOR,source_thread_id=THREAD,
            parent_thread_id=header['payload'].get('parent_thread_id'),source_audit_path=str(LOG),
            source_prefix_size_observed=prefix,source_line_offsets=[row[0] for row in chosen],
            source_line_bytes=[len(row[1]) for row in chosen],original_line_sha256=[sha(row[1]) for row in chosen],
            actual_tool_name=call[2]['payload'].get('name'),original_call_id=cid,original_capture_ref=rawref,
            tool_call_timestamp=call[2]['timestamp'],tool_result_timestamp=returned[2]['timestamp'],
            representation='Exact original current Source author header/call/returnedoutput bytes; not a Root Scope, issuer or formal peer witness.',
            product_execution=False,execution_grant=False,formal_acceptance=False))
        result.append(dict(original_call_id=cid,raw_ref=rawref,binding_ref=binding))
    return save('actual-source-host-pairs.json',dict(schema='researchos.w09-adoption-revision-actual-source-host-pairs.v1',
        actual_source_author=AUTHOR,source_thread_id=THREAD,parent_thread_id=header['payload'].get('parent_thread_id'),
        captures=result,complete_returned_pairs=len(result),observed_prefix_size=prefix,
        current_seal_full_call_return='Root captures the actual seal return and final peer delivery externally after completion; this Source does not manufacture its future complete pair.',
        old_control_suites_rerun=False,Root_issuer_called=False,actual_stage_called=False,execution_grant=False,formal_acceptance=False))

def main():
    basis=json.loads((Q/'revision-basis.json').read_bytes())
    controls=json.loads((Q/'delta-source-controls.result.json').read_bytes())
    contract=json.loads((Q/'root-calling-contract.source.json').read_bytes())
    inverse=json.loads((Q/'precise-byte-inverse.json').read_bytes())
    assert controls['passed']==25 and controls['failed']==0 and controls['runtime_stage_called'] is False
    assert controls['Root_issuer_called'] is False and controls['Main_written'] is False and controls['Canon_written'] is False
    assert contract['source_author']==AUTHOR and contract['own_independent_source_review_required']['source_author_id']==AUTHOR
    assert contract['revision_provenance']['old_68_controls_rerun'] is False
    for item in inverse['members']:
        raw=Path(item['candidate_ref']['path']).read_bytes(); restored=raw
        assert pin(item['candidate_ref']['path'])==item['candidate_ref']
        for span in reversed(item['byte_spans']):
            new=base64.b64decode(span['candidate_bytes_b64']); old=base64.b64decode(span['base_bytes_b64'])
            assert restored[span['candidate_start']:span['candidate_end']]==new
            restored=restored[:span['candidate_start']]+old+restored[span['candidate_end']:]
        assert restored==Path(item['original_ref']['path']).read_bytes()
        assert sha(restored)==item['upstream_ref']['sha256'] and len(restored)==item['upstream_ref']['bytes']
        ast.parse(raw); compile(raw,item['candidate_ref']['path'],'exec')
    hostref=capture_source()
    inputs=json.loads((Q/'input-pins.json').read_bytes()); gref=inputs['refs']['guard']
    assert pin(gref['path'])==gref
    gm=types.ModuleType('task85_seal_guard'); exec(compile(Path(gref['path']).read_bytes(),gref['path'],'exec'),gm.__dict__)
    members=[pin(path) for path in sorted(Q.rglob('*')) if path.is_file()]
    guard=gm.SourceReadGuard(total_cap=128*1024*1024)
    try:
        guard.acquire(members)
        for key,ref in contract['source_bindings'].items(): assert pin(ref['path'])==ref and ref in members
        audit=json.loads(guard.get_buffer(str(Q/'construct.source-guard.closed.json')))
        assert audit['closed'] is True and audit['retained_handles_count']==0 and audit['errors']==[]
        assert basis['main_pair_ref']['sha256']=='8b17646980d38d5c16f60f6c1b530f9ed237e45b7ebe146404269458d586be5c'
    finally:
        closed=guard.close(); closedref=save('seal.source-guard.closed.json',closed)
        assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    contractref=pin(Q/'root-calling-contract.source.json')
    priorguard=pin(Q/'construct.source-guard.closed.json')
    limits=dict(actual_branch_called=False,actual_TP_called=False,actual_Main_exclusive_write_called=False,
        actual_NF3_prepare_run_called=False,Main_written=False,Canon_written=False,
        Root_request_scope_or_lease_created=False,Root_issuer_called=False,Go_Native_SQL_model_called=False,
        execution_grant=False,programme_qualification=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0)
    delivery=save('Source-delivery.json',dict(schema='researchos.w09-root-adoption-source-delivery.v1',
        source_author=AUTHOR,source_thread_id=THREAD,original_contributor='codex:/root/native_temp_independent_review',
        status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ADOPTION',source_refs=contract['source_bindings'],
        contract_ref=contractref,input_pins_ref=pin(Q/'input-pins.json'),base_hdf_ref=basis['base_hdf_ref'],base_manifest_ref=basis['base_manifest_ref'],
        controls_ref=pin(Q/'delta-source-controls.result.json'),controls_passed=25,controls_failed=0,
        reused_old_68_controls_ref=basis['base_controls_ref'],old_68_controls_rerun=False,Q_NF3_suites_rerun=False,
        actual_source_host_pairs_ref=hostref,precise_byte_inverse_ref=pin(Q/'precise-byte-inverse.json'),
        minimal_diff_ref=pin(Q/'minimal-source.diff'),source_guard_refs=[priorguard,closedref],
        all_Source_guards_closed=True,retained_handles_count=0,original_failure_refs=basis['original_failure_refs'],
        Root_reported_AD01_failure_ordinal_1109_retained=True,new_original_failures=[],
        business_delta_one_path_predicate=True,identity_delta_truthful_Backup_author=True,STOP=True,**limits))
    finalmembers=[pin(path) for path in sorted(Q.rglob('*')) if path.is_file()]
    mf=save('MF.json',dict(schema='researchos.w09-root-adoption-source-manifest.v1',members=finalmembers,
        excludes=['MF.json','HDF.json'],source_author=AUTHOR,source_thread_id=THREAD,
        original_contributor='codex:/root/native_temp_independent_review',sealed_immutable=True))
    hdf=save('HDF.json',dict(schema='researchos.w09-root-adoption-source-handoff.v1',actor_id=AUTHOR,
        source_thread_id=THREAD,status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_ADOPTION',manifest_ref=mf,
        source_delivery_ref=delivery,**contract['source_bindings'],contract_ref=contractref,input_pins_ref=pin(Q/'input-pins.json'),
        controls_ref=pin(Q/'delta-source-controls.result.json'),controls_passed=25,controls_failed=0,
        source_guard_refs=[priorguard,closedref],all_Source_guards_closed=True,retained_handles_count=0,
        actual_source_host_pairs_ref=hostref,base_hdf_ref=basis['base_hdf_ref'],base_manifest_ref=basis['base_manifest_ref'],
        original_contributor='codex:/root/native_temp_independent_review',reused_old_68_controls_ref=basis['base_controls_ref'],
        old_68_controls_rerun=False,precise_byte_inverse_ref=pin(Q/'precise-byte-inverse.json'),minimal_diff_ref=pin(Q/'minimal-source.diff'),
        original_failure_refs=basis['original_failure_refs'],Root_reported_AD01_original1109_retained=True,new_original_failures=[],
        required_next='Fresh non-author AD02 Source review with exact HDF/MF/decision and actual Backup/peer audit; Root issues a new current NATIVE_SCOPES request and bounded lease. Old failed input is not retried, and this package runs no actual stages.',**limits))
    for ref in finalmembers: assert pin(ref['path'])==ref
    print(json.dumps(dict(HDF=hdf,MF=mf,caller=contract['source_bindings']['caller_ref'],core=contract['source_bindings']['core_ref'],
        main_pair=contract['source_bindings']['main_pair_ref'],contract=contractref,Source_author=AUTHOR,
        controls_passed=25,controls_failed=0,members=len(finalmembers),all_Source_guards_closed=True,retained_handles_count=0,
        original_Source_failure_1090_preserved=True,Root_original1109_preserved=True,new_original_failures=[],execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))

if __name__ == '__main__':
    try: main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1'); raise
    print('ROOT_PYTHON_EXIT=0')
