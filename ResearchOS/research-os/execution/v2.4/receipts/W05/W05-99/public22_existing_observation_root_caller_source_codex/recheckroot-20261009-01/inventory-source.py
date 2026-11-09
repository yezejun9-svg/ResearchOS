"""Pin existing Source and artifact bytes; never query SQLite or run a child."""
import hashlib,json,sqlite3,_sqlite3,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
L=B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v3'
Q=B/'public22_leaf_v3_independent_source_review_codex/review-01a12145'
def main():
    m=types.ModuleType('recheck_source_inventory');m.__file__=str(N/'public22_recheck_root.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    h=m.pin(L/'HDF.json');mf=m.pin(L/'MF.json');rh=m.pin(Q/'HDF.json');rm=m.pin(Q/'MF.json');rd=m.pin(Q/'decision.json');req=m.pin(Q/'next-root-recheck-contract.json')
    for ref,sha,size in [(h,'986c86da716c5be2c26922f0aa64200a4f925037bc6a84aa7135383a985346f5',4181),
        (mf,'e791329078879c06624741ef81d3b26726f94820c8b83f6eedd9e083f39c3afe',8082),
        (rh,'4108d1dc659877a09929abb973d11c93c3559706c82112621f9ffe2da540c796',3566),
        (rm,'322255995bffca280a4a2f3b1c053ffdccececa715012c207beb27a196b4ef22',296315),
        (rd,'54847862ebf19412c145873c1f2b5e176dcb77e86e4787dbbb954ed568ba9338',2863),
        (req,'b8a605a8ba171b285786e3082b45a9295a9cf84894974cfca5dad96cd05e3772',7917)]:m.need(ref['sha256']==sha and ref['bytes']==size,'PINNED_INPUT')
    leaf,lmf,lrefs=m.pair(h,mf);review,reviewmf,rrefs=m.pair(rh,rm);requirements=m.doc(req);contract=m.doc(leaf['contract_ref'])
    source_inputs=m.doc(leaf['source_inputs_ref']);resource_refs=lrefs+rrefs+[rd,req,*source_inputs['references'],m.GUARD_REF,m.TP_REF]
    i=dict(schema='researchos.public22-existing-root-source-inputs.v1',leaf_hdf_ref=h,leaf_mf_ref=mf,leaf_review_hdf_ref=rh,leaf_review_mf_ref=rm,
        leaf_review_decision_ref=rd,recheck_contract_ref=req,leaf_contract_ref=leaf['contract_ref'],leaf_runner_ref=leaf['runner_ref'],
        case_request_ref=requirements['request_ref'],evidence=requirements['evidence'],owned_job_ref=contract['owned_job'],
        toolchain_lock_ref=m.pin(R/'execution/toolchains/locked.json'))
    # No SQLite observation here: only old serialized metadata, file hashes and attributes.
    original=m.original_evidence(i)
    resource_refs.extend(original['refs']);resource_refs.extend([contract[k] for k in ('old22_recovery_source','old22_backup_source','old22_canonical_source','owned_job','source_guard')])
    leafmodule=m.load(leaf['runner_ref'],'preload_accepted_leaf_no_calls')
    tp=m.load(m.TP_REF,'preload_existing_TP_no_transaction')
    guardmodule=m.load(m.GUARD_REF,'preload_existing_SourceGuard')
    helper=m.load(contract['owned_job'],'enumeration_only_no_owned_job')
    runtime=[m.pin(sys.executable),m.pin(_sqlite3.__file__)]+[m.pin(p) for p in helper.runtime_resource_paths()]
    for mod in tuple(sys.modules.values()):
        for field in ('__file__','__cached__'):
            path=getattr(mod,field,None)
            if path and Path(path).is_file() and not Path(path).is_relative_to(N):runtime.append(m.pin(path))
    runtime=m.refs_unique(runtime)
    runtime_ref=m.save(N,'runtime-resources.json',dict(schema='researchos.public22-existing-root-runtime-resources.v1',resource_refs=runtime,
        python_ref=m.pin(sys.executable),sqlite_extension_ref=m.pin(_sqlite3.__file__),sqlite_runtime_version=sqlite3.sqlite_version,
        collected_after_sqlite_import=True,sqlite_queries_performed=0,Job_started=False,source_only=True,requires_non_author_Source_review=True))
    i['runtime_resources_ref']=runtime_ref;i['source_resource_refs']=m.refs_unique(resource_refs)
    input_ref=m.save(N,'source-inputs.json',i)
    held=guardmodule.SourceReadGuard(per_file_cap=m.MAX,total_cap=2*1024*1024*1024)
    try:
        held.acquire(m.refs_unique(i['source_resource_refs']+runtime+[input_ref,runtime_ref]))
        for ref in i['source_resource_refs']+runtime:m.checked(ref)
    finally:
        closed=held.close();m.save(N,'source-inventory-guard.closed.json',closed)
        m.need(closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0,'SOURCE_GUARD_CLOSED')
    m.save(N,'source-inventory-observation.json',dict(status='PINNED_SOURCE_AND_OLD_METADATA_ONLY',source_refs=len(i['source_resource_refs']),runtime_refs=len(runtime),
        original_native_children=4,new_native_children=0,SQLite_queries=0,current_Canon_read=False,current_Canon_held=False,
        original1025_result='FAILED_RETAINED',private_key_or_owner_file_read=False,formal_acceptance=False))
    print(json.dumps(dict(status='SOURCE_INPUTS_PINNED',source_refs=len(i['source_resource_refs']),runtime_refs=len(runtime),original_children=4,SQL_queries=0)))
if __name__=='__main__':main()
