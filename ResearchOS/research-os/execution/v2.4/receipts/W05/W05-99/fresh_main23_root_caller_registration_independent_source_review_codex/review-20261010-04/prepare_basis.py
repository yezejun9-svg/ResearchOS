"""Pin prior evidence only; M4 inputs and verdict remain unavailable."""
import hashlib
import json
import os
from pathlib import Path
import types

W=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99')
D=Path(__file__).resolve().parent
M=W/'fresh_main23_root_caller_registration_independent_source_review_codex/review-20261010-03'
T=W/'main23_qualification_time_contract_independent_review_codex/review-20261010-01'
G=W/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
def pin(p):
    raw=Path(p).read_bytes()
    return dict(path=str(Path(p)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    with (D/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(D/name)
def main():
    h=doc(M/'HDF.json');t=doc(T/'HDF.json');refs=[pin(M/'HDF.json'),h['manifest_ref'],h['source_decision_ref'],
        h['finitechecks_ref'],h['Source_guard_ref'],pin(M/'published-contract-check.json'),
        pin(T/'HDF.json'),t['manifest_ref'],t['decision_ref'],t['finite_checks_ref'],t['Source_guard_ref'],pin(G)]
    assert refs[0]['sha256']=='2c834ce12d8c6845ebd42724254f59e8834bc8cff3fc48bff5973c8000c76cb1' and refs[0]['bytes']==3587
    assert refs[6]['sha256']=='c7c85652c49efd0e178dedbd7ee367af0748c4765aee8c885d0999353a017cc9' and refs[6]['bytes']==4972
    assert refs[-1]['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    module=types.ModuleType('M4_prior_only_guard');module.__file__=str(G)
    exec(compile(G.read_bytes(),str(G),'exec'),module.__dict__)
    guard=module.SourceReadGuard()
    try:
        guard.acquire(refs)
        for ref in refs:
            observed=pin(ref['path']);assert observed['sha256']==ref['sha256'] and observed['bytes']==ref['bytes']
        checks=doc(h['finitechecks_ref']['path'])
        assert len(checks['checks'])==14782 and checks['failed']==[]
        assert doc(M/'decision.json')['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION'
        assert doc(M/'published-contract-check.json')['actual_final_HDF_MF_decision_validate_by_unmodified_own_review_prefix'] is True
        assert doc(T/'decision.json')['verdict']=='CHANGES_REQUIRED'
        basis=save('prepared-basis.json',dict(status='PREPARED_AWAITING_ROOT_M4_REFS',review_author='codex:/root/full_w09_source_review',
            reviewer_thread_id=os.environ['CODEX_THREAD_ID'],prior_evidence_refs=refs,
            M3_review_checks_reusable=14782,M3_checks_rerun=0,unchanged_14670_pins_await_actual_M4_delta_comparison=True,
            M3_review_hdf_schema=h['schema'],M3_decision_schema=doc(M/'decision.json')['schema'],
            required_delta=['independent actual payload/wrapper creation times and complete order with no future timestamp',
                'anchored exact backend FINAL envelope and strict one complete typed peer JSON'],
            required_unchanged_gates=['Root tool decoder','canonical actors and exclusions','fixed Root audit and actual offset bytes',
                'complete resource/source binding','TP and Job rules','original failure ledger'],
            actual_peer_samples=[60922,60970],final_own_review_prefix_required=True,future_witness_not_synthesized=True,
            new_Source_read=False,new_Source_refs=None,new_Source_verdict=None,qualification_created=False,
            execution_grant=False,formal_acceptance=False,Go_Native_SQL_dispatcher_model_runs=0,Canon_Main_Source_written=False))
    finally:
        closed=guard.close();closed_ref=save('prepared-basis.Source-guard.closed.json',closed)
    assert closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0
    print(json.dumps(dict(status='PREPARED_AWAITING_ROOT_M4_REFS',basis_ref=basis,closed_guard_ref=closed_ref,
        prior_14782_checks_not_rerun=True,new_Source_read=False,new_Source_verdict=None,retained_handles_count=0),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
