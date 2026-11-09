"""Seal v3 Source packet inside its new namespace; no Canon or product writes."""
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
V=R/'execution/v2.4'
B=V/'receipts/W05/W05-99'
ROOT=V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
REVIEW=B/'public22_root_caller_registration_independent_review_codex/review-v2-01a120dd'
OLD=B/'public22_root_caller_registration_source_codex/p22root-20261009-02'
BEFORE=[('a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994',4489310),
        ('a612b51f23a5157aff5b99817caa09fb634a67c70879c56430daa4690d1da0bc',208629),
        ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
        ('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]

def ref(path):
    p=Path(path).resolve(strict=True)
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def write(name,value):
    p=N/name
    assert not p.exists(),name
    with p.open('xb') as f:
        f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
        f.flush()
    return ref(p)

def main():
    canons=[ref(V/(x+'.json')) for x in ('checkpoint','path_ownership','step_state','commands')]
    assert [(x['sha256'],x['bytes']) for x in canons]==BEFORE,'CURRENT_CANON_CHANGED'
    review_pins={
        'HDF.json':('2eaa87c7ebb3f755b4bd79f7b8aaaf15137599abe480776caa9fbebca285ec5e',3395),
        'MF.json':('fdc064846af6fbbc81591e0c8af7d13405b4a8144e6e04aca07a058446a4fcd5',20848),
        'source-decision.json':('6be1e80b64f11d6ee4c4bf5131c7ccaa89181611d58324ed6db5e383f29cbbeb',13258),
    }
    for name,pair in review_pins.items():
        assert (ref(REVIEW/name)['sha256'],ref(REVIEW/name)['bytes'])==pair,name
    pending_ref=ref(ROOT/'pending-diagnostics.cp370.live1016.root.json')
    assert (pending_ref['sha256'],pending_ref['bytes'])==(
        '904233ae7c86c4f59e69f39f9f3dcb6db8355194b57a100ea4d66e3f6b4ceada',11567)
    resume_ref=ref(ROOT/'RESUME.cp370-public22-fixing.live1016.root.json')
    assert (resume_ref['sha256'],resume_ref['bytes'])==(
        '43b61539c9ff9d4cb454ae88b3bf15d7cde978d34deeb851bf169fee6c404e84',8314)
    inputs=json.loads((N/'source-inputs.json').read_bytes())
    assert inputs['count']==len(inputs['references'])==47
    assert all(ref(x['path'])['sha256']==x['sha256'] and
               ref(x['path'])['bytes']==x['bytes'] for x in inputs['references'])
    assert inputs['pending_original_ordinals']==list(range(1005,1016))
    assert inputs['canonical_before_refs']==canons
    controls=json.loads((N/'source-controls.locked.json').read_bytes())
    assert controls['pass']==controls['count']==54 and controls['fail']==0
    assert controls['canonical_before_refs']==canons and controls['canonical_after_refs']==canons
    files=['public22_root_caller.source.py','register_public22.source.py',
           'root-calling-contract.source.json','source-controls.locked.json',
           'source-inputs.json','source-changes.json','source_controls.py',
           'prepare_inputs.py','seal_source.py']
    members=[ref(N/x) for x in files]
    inputs_ref=ref(N/'source-inputs.json')
    mf_ref=write('MF.json',{
        'schema':'researchos.root-public22-caller-registration-source-manifest.v1',
        'members':members,'member_count':len(members),
        'source_inputs_ref':inputs_ref,'excludes':['MF.json','HDF.json']})
    hdf_ref=write('HDF.json',{
        'schema':'researchos.root-public22-caller-registration-source-handoff.v1',
        'status':'SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_AND_ROOT_REGISTRATION',
        'author':'codex:/root/w09_formal_profile_source_impl',
        'manifest_ref':mf_ref,'caller_ref':ref(N/'public22_root_caller.source.py'),
        'registrar_ref':ref(N/'register_public22.source.py'),
        'contract_ref':ref(N/'root-calling-contract.source.json'),
        'source_inputs_ref':inputs_ref,
        'source_controls_ref':ref(N/'source-controls.locked.json'),
        'source_changes_ref':ref(N/'source-changes.json'),
        'runner_review_ref':ref(B/'public22_runner_independent_source_review_codex/pub22r-20261009-02/HDF.json'),
        'superseded_v2_hdf_ref':ref(OLD/'HDF.json'),
        'rejected_v2_review_hdf_ref':ref(REVIEW/'HDF.json'),
        'rejected_v2_review_mf_ref':ref(REVIEW/'MF.json'),
        'rejected_v2_review_decision_ref':ref(REVIEW/'source-decision.json'),
        'repair_pending_ref':pending_ref,'repair_resume_ref':resume_ref,
        'source_controls_pass':54,'source_controls_fail':0,
        'canonical_before_refs':canons,'proposed_canonical_revisions':{
            'checkpoint':371,'path_ownership':175,'commands':39},
        'actual_product_processes':0,'actual_SQLite_calls':0,
        'actual_native_calls':0,'root_registration':'NOT_CREATED',
        'first_actual_request':'NOT_CREATED',
        'Root_next_original_failure_ordinal':1016,
        'first8_pending_originals_preserved':True,
        'new_review_original_failure_ordinals':[1013,1014,1015],
        'end_version22':'CALLER_SOURCE_READY_PENDING_REVIEW_AND_ROOT_REGISTRATION',
        'end_version23':'SEPARATE_FRESH_MAIN23_BUILDER_SCOPE_REQUIRED',
        'end_version24':'BLOCKED_MAIN_PUBLIC_23_TO_24_NOT_ADOPTED',
        'schema21':'OPEN','full20to24':'OPEN',
        'formal_acceptance':False,'parent_acceptance':False,
        'Main_Canon_Registry_changed':False,'STOP':True,'FINAL':True})
    print(json.dumps({'handoff_ref':hdf_ref,'manifest_ref':mf_ref,
        'source_inputs_ref':inputs_ref,'members':len(members),
        'static_pins':len(inputs['references'])},ensure_ascii=False))

if __name__=='__main__':main()
