"""Seal the independent Source-only verdict. Writes exclusively to this review directory."""
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
S=N.parent.parent/'genuine_schema22_public_upgrade_runner_source_codex'/'s22public-20261009-01-v2'
P=N.parent/'pub22r-20261009-01'

def ref(path):
    path=Path(path).resolve(strict=True)
    raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def read(path): return json.loads(Path(path).read_bytes())

def write(name,value):
    path=N/name
    with path.open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return ref(path)

def main():
    for name,sha in [('HDF.json','6f2ec5e3eeb6c06a343ab9fc2fdfb1462e0e740da72986f5c8b7639fab31187e'),
                     ('MF.json','cca5a67720a616832d8503158c2c7b2c2933638bcdfc5da2b3eb69dcd1e78ca5'),
                     ('public22_runner.py','c157e0a213406267d56d3f24ee07092413c26bb3c6bafaf9ac5469fbf4829da7'),
                     ('contract.json','24d24cf6535b79355ad0a4e9a9ef518b93039f4c67bd01ad74cae5d66a127976')]:
        assert ref(S/name)['sha256']==sha, 'SOURCE_CHANGED_'+name
    controls=read(N/'independent-controls.json')
    assert controls['passed']==22 and controls['failed']==0 and controls['read_pins']==583
    assert controls['guard_closed'] is True and controls['product_processes']==controls['product_database_calls']==0
    author=read(S/'HDF.json')
    assert author['source_controls_pass']==85 and author['source_controls_fail']==0
    assert author['actual_runtime_executed'] is False and author['root_registration']=='NOT_CREATED'
    old_decision=read(P/'source-decision.json')
    assert old_decision['decision']=='REQUEST_CHANGES_SOURCE_ONLY' and old_decision['blocking_findings']==['F1','F2']
    findings={
        'schema':'researchos.w05-public22-independent-source-findings.v2',
        'source_author_id':'codex:/root/native_temp_independent_review',
        'reviewer_id':'codex:/root/w09_formal_profile_source_impl',
        'prior_review_ref':ref(P/'source-decision.json'),
        'resolution':[{'id':'F1','verdict':'RESOLVED_IN_SOURCE',
            'evidence':'Independent calls accepted exact sealed/restored22 and rejected dropped Owner, changed Owner/domain rows, changed or absent schema digest, missing or added table; AST confirms verify22 invokes validate_restore22.'},
            {'id':'F2','verdict':'RESOLVED_IN_SOURCE',
            'evidence':'Independent in-memory Path fault injection covered mkdir failure for root/private/raw/tmp/work22 and case.closed publication failure. Original prepare failure remained in returned state, partial directories were observable, no child/retry ran, and a case.closed payload was emitted whenever root existed and save succeeded.'}],
        'reviewer_adapter_error_ref':ref(N/'review-first-run-error.json'),
        'reviewer_adapter_error_disposition':'REVIEW_SCRIPT_SCHEMA_ASSUMPTION_CORRECTED; NO_SOURCE_OR_PRODUCT_FAILURE',
        'blocking_source_findings':[],
        'limits':{'actual_product_runtime':'NOT_EXECUTED','Root_public22_scope_owner_worker_lease':'ABSENT_AT_REVIEW_PIN',
                  'end_version23':'PENDING_ROOT_FRESH_CURRENT_MAIN23_PROGRAMME_BINDING',
                  'end_version24':'BLOCKED_MAIN_PUBLIC_23_TO_24_NOT_ADOPTED',
                  'schema21':'OPEN','full20to24':'OPEN','formal_acceptance':False}
    }
    findings_ref=write('findings.json',findings)
    decision={
        'schema':'researchos.w05-public22-runner-independent-source-decision.v2',
        'decision':'ACCEPTED_SOURCE_ONLY',
        'actor_id':'codex:/root/w09_formal_profile_source_impl','actor_role':'INDEPENDENT_NON_AUTHOR',
        'source_author_id':'codex:/root/native_temp_independent_review',
        'source_hdf_ref':ref(S/'HDF.json'),'source_mf_ref':ref(S/'MF.json'),
        'runner_ref':ref(S/'public22_runner.py'),'contract_ref':ref(S/'contract.json'),
        'source_inputs_ref':ref(S/'source-inputs.json'),'source_controls_ref':ref(S/'source-controls.json'),
        'review_controls_ref':ref(N/'independent-controls.json'),
        'review_guard_ref':ref(N/'sourceguard.closed.json'),
        'findings_ref':findings_ref,
        'prior_review_decision_ref':ref(P/'source-decision.json'),
        'blocking_source_findings':[], 'resolved_prior_findings':['F1','F2'],
        'source_controls_pass':85,'independent_checks_pass':22,'held_read_refs':583,
        'first_actual_request':'NOT_CREATED',
        'current_canon_public22_root_scope_owner_worker_lease':'ABSENT_AT_REVIEW_PIN',
        'current_main23_programme_binding':'NOT_QUALIFIED_FOR_ACTUAL',
        'main23to24':'BLOCKED_MAIN_NOT_ADOPTED','schema21':'OPEN','full20to24':'OPEN',
        'actual_product_processes':0,'actual_product_database_calls':0,
        'actual_registration':False,'execution_grant':False,'formal_acceptance':False,
        'Main_or_Canon_written':False,'STOP':True,'FINAL':True
    }
    decision_ref=write('source-decision.json',decision)
    members=[ref(N/name) for name in ['review.py','seal_review.py','review-first-run-error.json',
        'independent-controls.json','sourceguard.closed.json','findings.json','source-decision.json']]
    members += [ref(S/name) for name in ['HDF.json','MF.json','public22_runner.py','contract.json',
        'source-inputs.json','source-controls.json','source-delivery.json','revision-changes.json']]
    mf_ref=write('MF.json',{'schema':'researchos.w05-public22-runner-independent-source-review-manifest.v2',
         'source_hdf_ref':ref(S/'HDF.json'),'source_mf_ref':ref(S/'MF.json'),
         'members':members,'member_count':len(members),'excludes':['MF.json','HDF.json']})
    hdf_ref=write('HDF.json',{'schema':'researchos.w05-public22-runner-independent-source-review-handoff.v2',
        'decision':'ACCEPTED_SOURCE_ONLY','actor_id':'codex:/root/w09_formal_profile_source_impl',
        'actor_role':'INDEPENDENT_NON_AUTHOR','manifest_ref':mf_ref,
        'source_decision_ref':decision_ref,'findings_ref':findings_ref,
        'review_controls_ref':ref(N/'independent-controls.json'),
        'review_guard_ref':ref(N/'sourceguard.closed.json'),
        'source_hdf_ref':ref(S/'HDF.json'),'source_mf_ref':ref(S/'MF.json'),
        'runner_ref':ref(S/'public22_runner.py'),'contract_ref':ref(S/'contract.json'),
        'blocking_source_findings':0,'held_read_refs':583,'guard_closed':True,
        'product_processes_executed':0,'product_database_calls':0,
        'Root_actual_registration':False,'formal_acceptance':False,'STOP':True,'FINAL':True})
    print(json.dumps({'handoff_ref':hdf_ref,'manifest_ref':mf_ref,'decision_ref':decision_ref,
        'findings_ref':findings_ref},ensure_ascii=False))

if __name__=='__main__':main()
