"""Seal v3 Source packet inside its new namespace; no Canon or product writes."""
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
V=R/'execution/v2.4'
B=V/'receipts/W05/W05-99'
ROOT=V/'receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
REVIEW=B/'public22_root_caller_registration_independent_review_codex/review-v3-01a1210b'
OLD=B/'public22_root_caller_registration_source_codex/p22root-20261009-03'
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
        'HDF.json':('11d1e317758d0c1213b871aba43a0358fb7370fc510eb91443510fc135abb573',3398),
        'MF.json':('1dc20b70eda56e86795bcc615d86b89c9e5c68681df005f19973883c0c8ba9b1',218989),
        'source-decision.json':('e9968c0f8bfd0c9ec056fcac767a7a4eed7be8b39c0d01d37a3564edc737a91a',3615),
    }
    for name,pair in review_pins.items():
        assert (ref(REVIEW/name)['sha256'],ref(REVIEW/name)['bytes'])==pair,name
    pending_ref=ref(ROOT/'pending-diagnostics.cp370.live1018.root.json')
    assert (pending_ref['sha256'],pending_ref['bytes'])==(
        'ab22f3b0ee01b4002dfbbc97e219f08e99e371315839248fd4fac4e3e503d3b0',13226)
    resume_ref=ref(ROOT/'RESUME.cp370-public22-v4-pending.live1018.root.json')
    assert (resume_ref['sha256'],resume_ref['bytes'])==(
        '8e08f0fc150de49033ac875e6776951b8ef39169752c97385bf749921a0a3c58',8415)
    inputs=json.loads((N/'source-inputs.json').read_bytes())
    assert inputs['count']==len(inputs['references'])==56
    assert all(ref(x['path'])['sha256']==x['sha256'] and
               ref(x['path'])['bytes']==x['bytes'] for x in inputs['references'])
    assert inputs['pending_original_ordinals']==list(range(1005,1018))
    assert inputs['canonical_before_refs']==canons
    controls=json.loads((N/'source-controls.locked.json').read_bytes())
    assert controls['pass']==controls['count']==56 and controls['fail']==0
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
        'superseded_v3_hdf_ref':ref(OLD/'HDF.json'),
        'rejected_v3_review_hdf_ref':ref(REVIEW/'HDF.json'),
        'rejected_v3_review_mf_ref':ref(REVIEW/'MF.json'),
        'rejected_v3_review_decision_ref':ref(REVIEW/'source-decision.json'),
        'repair_pending_ref':pending_ref,'repair_resume_ref':resume_ref,
        'source_controls_pass':56,'source_controls_fail':0,
        'canonical_before_refs':canons,'proposed_canonical_revisions':{
            'checkpoint':371,'path_ownership':175,'commands':39},
        'actual_product_processes':0,'actual_SQLite_calls':0,
        'actual_native_calls':0,'root_registration':'NOT_CREATED',
        'first_actual_request':'NOT_CREATED',
        'Root_next_original_failure_ordinal':1018,
        'first8_pending_originals_preserved':True,
        'new_review_original_failure_ordinals':[],
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
