from __future__ import annotations
import ast,difflib,hashlib,json,sys,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    inputs=json.loads((Q/'source-inputs.json').read_text(encoding='utf-8'));c=json.loads((Q/'root-calling-contract.source.json').read_text(encoding='utf-8'))
    caller=pin(Q/'old21_root.source.py');assert c['caller_ref']==caller and c['registrar_ref']==caller
    base=Path(inputs['M4_caller_ref']['path']).read_bytes();candidate=(Q/'old21_root.source.py').read_bytes();compile(candidate,str(Q/'old21_root.source.py'),'exec')
    # Four exact inverse layers, validated over their actually retained Source bytes.
    s=json.loads((Q/'Task68-review-pin-revision.inverse.json').read_text(encoding='utf-8'))
    x=candidate.decode().replace(s['inserted_constant'],'').replace(s['inserted_condition'],'').encode();assert x==Path(s['initial_ref']['path']).read_bytes()
    s=json.loads((Q/'numbered-SQL-exact-revision.inverse.json').read_text(encoding='utf-8'));x=x.replace(bytes.fromhex(s['new_hex']),bytes.fromhex(s['old_hex']));assert x==Path(s['initial_ref']['path']).read_bytes()
    s=json.loads((Q/'numbered-SQL-revision.inverse.json').read_text(encoding='utf-8'));x=x.replace(bytes.fromhex(s['new_hex']),bytes.fromhex(s['old_hex']));assert x==Path(s['initial_ref']['path']).read_bytes()
    s=json.loads((Q/'exact-inverse.json').read_text(encoding='utf-8'));restored=bytearray(x)
    for r in reversed(s['spans']):restored[r['candidate_start']:r['candidate_end']]=bytes.fromhex(r['base_hex'])
    assert bytes(restored)==base
    finaldiff=Q/'candidate.sealed.diff'
    with finaldiff.open('xb') as f:f.write(''.join(difflib.unified_diff(base.decode().splitlines(keepends=True),candidate.decode().splitlines(keepends=True),fromfile='accepted-M4/main23_root.source.py',tofile='old21_root.source.py')).encode())
    inverse=save('full-inverse-chain.sealed.json',dict(schema='researchos.old21-caller-full-inverse-chain.v1',base_ref=inputs['M4_caller_ref'],candidate_ref=caller,layer_refs=[pin(Q/n) for n in ('exact-inverse.json','numbered-SQL-revision.inverse.json','numbered-SQL-exact-revision.inverse.json','Task68-review-pin-revision.inverse.json')],restored_full_base_SHA=hashlib.sha256(bytes(restored)).hexdigest(),entire_original_bytes_restored=True))
    tree=ast.parse(candidate);lines=candidate.decode().splitlines();relevant={n.name:dict(line=n.lineno,end_line=n.end_lineno) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('validate_builder_chain','builder_chain','runtime_review_chain','own_review','current_four','future_request','projection','runtime_closure','live_lease','prebuild_authority','LiveScope','execute')}
    report=save('Source-implementation-and-limits.json',dict(schema='researchos.old21-caller-source-implementation.v1',source_author='codex:/root/backup_regression_resources',builder_source_author='codex:/root/native_temp_independent_review',Root_executor_future='codex:/root',caller_ref=caller,contract_ref=pin(Q/'root-calling-contract.source.json'),line_refs=relevant,base_protocol_Source_accepted_by_Root=True,control_evidence=[pin(Q/'finite-delta-controls.json'),pin(Q/'actual-Task68-review-source-binding.json')],passed_control_observations=27,previous25_pre_exact_review_constant=True,previous_M4_37_controls_ref=inputs['M4_controls37_ref'],unchanged_14782_14670_not_reexecuted=True,Source_ref_baseline='historicalCP373full4 only',live_Canon_reads=0,retained_live_Canon_handles=0,actual_builder_called=False,Go_Native_product_SQL_model_TP_calls=0,RootScope_or_grant_created=False,Source_nonauthor_review='PENDING',runtime_qualification=None,programme_qualification=None,formal_acceptance=False,parent_acceptance=False,execution_grant=False,old_original_failures_preserved=[1071,1072,1076,1077,1079],old_failed_guard_status='UNKNOWN_NOT_SERIALIZED; no retroactive closure proof',next_Root='Independent nonauthor Source review of exact new HDF/MF/caller/contract, then Root new distinct Scope and complete actual runtime qualification and captures; build NOTRUN',actual_seal_call_return_obligation='Root captures complete external original header+call+returnedoutput after this script returns; no causal future pair fabricated'))
    gm=types.ModuleType('seal_finite_guard');gm.__file__=str(Q/'read_Task69_basis_revision.py');exec(compile(Path(gm.__file__).read_bytes(),gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        # Finite input and candidate evidence guard; no LIVE canonical handles and no private resources.
        refs=inputs['references']+[pin(p) for p in Q.iterdir() if p.is_file() and p.name not in ('HDF.json','MF.json','Source-final.guard.closed.json')]
        seen=set()
        for ref in refs:
            key=str(Path(ref['path']).resolve(strict=True)).casefold()
            if key in seen:continue
            seen.add(key);guard.read(ref['path'],ref)
        closure=save('Source-final.guard.closed.json',guard.close());closed=True
        members=[pin(p) for p in sorted(Q.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
        mf=save('MF.json',dict(schema='researchos.old21-caller-Source-manifest.v1',source_author='codex:/root/backup_regression_resources',members=members,member_count=len(members),immutable=True,exclusions=['HDF.json self manifest reference','MF.json self digest','External Root seal call-return capture occurs after return and is separate evidence']))
        hdf=save('HDF.json',dict(schema='researchos.old21-root-caller-source-handoff.v1',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',source_author='codex:/root/backup_regression_resources',source_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',builder_source_author='codex:/root/native_temp_independent_review',manifest_ref=mf,caller_ref=caller,registrar_ref=caller,contract_ref=pin(Q/'root-calling-contract.source.json'),source_inputs_ref=pin(Q/'source-inputs.json'),base_caller_ref=inputs['M4_caller_ref'],builder_source_hdf_ref=inputs['builder_source_hdf_ref'],builder_source_mf_ref=inputs['builder_source_mf_ref'],known_builder_Source_review_refs=inputs['known_builder_Source_review_refs'],current_before_archive_refs=inputs['historical_cp373_full4'],inverse_ref=inverse,diff_ref=pin(finaldiff),controls_ref=pin(Q/'finite-delta-controls.json'),actual_Task68_binding_ref=pin(Q/'actual-Task68-review-source-binding.json'),implementation_ref=report,actual_Source_toolpairs_ref=pin(Q/'Source-actual-toolpairs.index.json'),Source_final_guard_ref=closure,success_Source_guard_all_closed=True,retained_handles_count=0,live_Canon_handles=0,Source_old_failed_guard_status='UNKNOWN_NOT_SERIALIZED',old_original_failures=[1071,1072,1076,1077,1079],original_failure_refs=[pin(Q/('failure-origin.'+str(x)+'.json')) for x in (1071,1072,1076,1077,1079)],Source_only=True,actual_RootScope_ref=None,actual_current4=None,actual_runtime_qualification_ref=None,actual_build_hostpair_ref=None,actual_programme_qualification_ref=None,actual_grant=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,source_self_acceptance=False,STOP_after_source_seal=True))
        print(json.dumps(dict(HDF_ref=hdf,MF_ref=mf,caller_ref=caller,contract_ref=pin(Q/'root-calling-contract.source.json'),guard_ref=closure,member_count=len(members),Source_only=True,actual_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('Source-seal-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
