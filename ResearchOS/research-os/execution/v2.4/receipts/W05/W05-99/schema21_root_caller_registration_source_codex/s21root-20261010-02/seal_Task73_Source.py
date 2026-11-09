from __future__ import annotations
import ast,hashlib,json,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    b=json.loads((Q/'source-inputs.basis.json').read_bytes());c=json.loads((Q/'root-calling-contract.source.json').read_bytes());inputs=json.loads((Q/'source-inputs.json').read_bytes());inv=json.loads((Q/'Task73-exact-inverse.json').read_bytes())
    candidate=(Q/'old21_root.source.py').read_bytes();caller=pin(Q/'old21_root.source.py');assert caller==inv['candidate_ref']==c['caller_ref']==c['registrar_ref']
    restored=candidate
    for layer in reversed(inv['layers']):
        old,new=bytes.fromhex(layer['old_hex']),bytes.fromhex(layer['new_hex']);assert restored.count(new)==1;restored=restored.replace(new,old)
    assert restored==Path(b['base_caller_ref']['path']).read_bytes() and hashlib.sha256(restored).hexdigest()==b['base_caller_ref']['sha256']
    before=ast.parse(restored);after=ast.parse(candidate)
    bm={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};am={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};changed=sorted(k for k in bm if bm[k]!=am[k]);assert changed==['failure_rows','projection','validate_peer_delivery']
    oldh=json.loads(Path(b['base_hdf_ref']['path']).read_bytes());line_refs={n.name:dict(line=n.lineno,end_line=n.end_lineno) for n in after.body if isinstance(n,ast.FunctionDef) and n.name in changed}
    report=save('Task73-Source-implementation-and-limits.json',dict(schema='researchos.old21-caller-Task73-Source-implementation.v1',caller_ref=caller,base_ref=b['base_caller_ref'],changed_functions=changed,line_refs=line_refs,full_inverse_reconstructs_original_Source=True,original_multi_layer_inverse_ref=b['base_inverse_ref'],new_inverse_ref=pin(Q/'Task73-exact-inverse.json'),prior39_controls_ref=pin(Q/'Task73-delta-controls.json'),original25_853_14782_controls_not_reexecuted=True,Task70_CHANGES_REQUIRED_refs=b['Task70_review_refs'],legacy_component='OLD21_PROGRAMME_BUILDER_SOURCE',legacy_original_decoder_boundary='Only the actual Full original Task68 message id/time/raw sha bytes and canonical actual actor/root thread/exact3 known Builder review refs; old21 Caller SOURCE_REVIEW_WITNESS unchanged',Root_issuer_original_gate='Preserved Source bytes and not executed in Source decode controls',old_original_failure_refs=b['original_failure_refs'],old_failed_guard_status=b['old_failed_guard_status'],new_original_failures=[],Main_Canon_oldSources_writes=0,live_Canon_reads=0,Go_Native_SQL_TP_model_actual_branches=0,actual_RootScope_ref=None,actual_runtime_manifest_ref=None,actual_runtime_qualification_ref=None,actual_programme_qualification_ref=None,execution_grant=False,formal_acceptance=False,parent_acceptance=False,Source_self_acceptance=False,Root_seal_full_original_return_capture='Root must externally capture complete actual sealing call+returnedoutput after return; cannot place future return inside this HDF'))
    mf=json.loads(Path(b['base_mf_ref']['path']).read_bytes());gr=next(r for r in mf['members'] if Path(r['path']).name=='read_Task69_basis_revision.py');gm=types.ModuleType('Task73_seal_finite_guard');gm.__file__=gr['path'];exec(compile(Path(gr['path']).read_bytes(),gm.__file__,'exec'),gm.__dict__);guard=gm.Guard();closed=False
    try:
        refs=inputs['references']+[pin(p) for p in Q.iterdir() if p.is_file() and p.name not in ('HDF.json','MF.json','Source-final.guard.closed.json')]
        seen=set()
        for r in refs:
            key=str(Path(r['path']).resolve(strict=True)).casefold()
            if key in seen:continue
            seen.add(key);guard.read(r['path'],r)
        closure=save('Source-final.guard.closed.json',guard.close());closed=True
        members=[pin(p) for p in sorted(Q.iterdir(),key=lambda p:p.name) if p.is_file() and p.name not in ('HDF.json','MF.json')]
        mref=save('MF.json',dict(schema='researchos.old21-caller-Source-manifest.v1',source_author='codex:/root/backup_regression_resources',members=members,member_count=len(members),immutable=True,exclusions=['HDF.json self-reference','MF.json own digest','Root future full Source-seal hostpair capture is separate post-return evidence']))
        h=save('HDF.json',dict(schema='researchos.old21-root-caller-source-handoff.v1',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',source_author='codex:/root/backup_regression_resources',source_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',builder_source_author='codex:/root/native_temp_independent_review',manifest_ref=mref,caller_ref=caller,registrar_ref=caller,contract_ref=pin(Q/'root-calling-contract.source.json'),source_inputs_ref=pin(Q/'source-inputs.json'),base_Source_hdf_ref=b['base_hdf_ref'],base_Source_mf_ref=b['base_mf_ref'],base_Caller_ref=b['base_caller_ref'],prior_complete_inverse_ref=b['base_inverse_ref'],inverse_ref=pin(Q/'Task73-exact-inverse.json'),diff_ref=pin(Q/'candidate.diff'),Task70_CHANGES_REQUIRED_refs=b['Task70_review_refs'],controls_ref=pin(Q/'Task73-delta-controls.json'),controls39_Source_only=True,controls_guard_ref=pin(Q/'Task73-delta-controls.guard.closed.json'),implementation_ref=report,actual_Source_toolpairs_ref=pin(Q/'Source-actual-toolpairs.index.json'),Source_final_guard_ref=closure,successful_Source_guards_closed=True,retained_handles_count=0,live_Canon_handles=0,original_failure_refs=b['original_failure_refs'],old_failed_guard_status=b['old_failed_guard_status'],new_original_failures=[],builder_source_hdf_ref=oldh['builder_source_hdf_ref'],builder_source_mf_ref=oldh['builder_source_mf_ref'],known_builder_Source_review_refs=b['known_builder_Source_review_refs'],current_before_archive_refs=b['current_before_archive_refs'],actual_Task68_observation_ref=b['actual_Task68_observation_ref'],actual_Task68_raw_ref=b['actual_Task68_raw_ref'],Source_only=True,actual_RootScope_ref=None,actual_current4=None,actual_runtime_manifest_ref=None,actual_runtime_qualification_ref=None,actual_build_hostpair_ref=None,actual_programme_qualification_ref=None,actual_grant=False,execution_grant=False,formal_acceptance=False,parent_acceptance=False,source_self_acceptance=False,STOP_after_source_seal=True))
        print(json.dumps(dict(HDF_ref=h,MF_ref=mref,caller_ref=caller,contract_ref=pin(Q/'root-calling-contract.source.json'),Source_guard_ref=closure,member_count=len(members),new_original_failures=[],actual_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False))
    finally:
        if not closed and any(not s.closed for s,_,_ in guard.held):save('Task73-seal-attempt-failure.guard.closed.json',guard.close())
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
