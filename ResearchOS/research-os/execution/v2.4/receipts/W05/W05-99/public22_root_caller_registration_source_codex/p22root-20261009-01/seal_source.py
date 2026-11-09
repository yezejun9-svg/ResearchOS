"""Seal immutable Source packet; writes only inside this new namespace."""
import hashlib
import json
from pathlib import Path

N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os')
V=R/'execution/v2.4'
B=V/'receipts/W05/W05-99'
W=V/'receipts/W09/W09-99'
RUN=B/'genuine_schema22_public_upgrade_runner_source_codex/s22public-20261009-01-v2'
RV=B/'public22_runner_independent_source_review_codex/pub22r-20261009-02'
ROOT=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
BEFORE=[('a5429468aefaa383f587e699d90744d437d6e0b4ef70d0df656519a1aa2ec994',4489310),
        ('a612b51f23a5157aff5b99817caa09fb634a67c70879c56430daa4690d1da0bc',208629),
        ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
        ('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]

def ref(path):
    p=Path(path).resolve(strict=True);raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def write(name,value):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return ref(p)

def main():
    canons=[ref(V/(x+'.json')) for x in ('checkpoint','path_ownership','step_state','commands')]
    assert [(x['sha256'],x['bytes']) for x in canons]==BEFORE,'CURRENT_CANON_CHANGED'
    assert (ref(RV/'HDF.json')['sha256'],ref(RV/'HDF.json')['bytes'])==(
        'e5f5611c4ebae96a3fc640fde86543e44b134812904736cf4021edfe60aadd31',3281)
    assert (ref(ROOT/'RESUME.cp370-consumers-qualified.live1013.root.json')['sha256'],
            ref(ROOT/'RESUME.cp370-consumers-qualified.live1013.root.json')['bytes'])==(
        '38e8633ef8796e3f59663d8fa2464b33155d623112fc1fc5e26a8cb6bf3158ac',6145)
    assert (ref(ROOT/'pending-diagnostics.cp370.live1013.root.json')['sha256'],
            ref(ROOT/'pending-diagnostics.cp370.live1013.root.json')['bytes'])==(
        '4013a2f77a6dced4e369159f84afc2d507b88519c7534c0a437c2fb380464005',8152)
    controls=json.loads((N/'source-controls.locked.json').read_bytes())
    assert controls['pass']==controls['count']==14 and controls['fail']==0
    runner_contract=json.loads((RUN/'contract.json').read_bytes())
    refs=[ref(R/'execution/project_identity.json'),ref(R/'execution/toolchains/locked.json'),
          ref(Path(r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe')),
          *canons,ref(ROOT/'RESUME.cp370-consumers-qualified.live1013.root.json'),
          ref(ROOT/'pending-diagnostics.cp370.live1013.root.json'),
          *[ref(RV/x) for x in ('HDF.json','MF.json','source-decision.json')],
          *[ref(RUN/x) for x in ('HDF.json','MF.json','public22_runner.py','contract.json',
                                 'source-inputs.json','source-controls.json')],
          *[ref(runner_contract[x]['path']) for x in
            ('old22_control','old22_backup','source_guard','owned_job')],
          ref(B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py')]
    unique={x['path'].casefold():x for x in refs}
    assert len(unique)==len(refs),'DUPLICATE_SOURCE_INPUT'
    inputs_ref=write('source-inputs.json',{
        'schema':'researchos.root-public22-caller-registration-source-inputs.v1',
        'scope':'SOURCE_ONLY_STATIC_PINS_NO_ACTUAL_RUNTIME',
        'references':refs,'count':len(refs),'canonical_before_refs':canons,
        'pending_original_ordinals':list(range(1005,1013)),
        'unknown_child_exits_remain_null':True,
        'actual_product_processes':0,'actual_database_calls':0,'actual_native_calls':0})
    files=['public22_root_caller.source.py','register_public22.source.py',
           'root-calling-contract.source.json','source_controls.py','seal_source.py',
           'source-controls.json','source-controls.final.json',
           'source-controls.sealed.json','source-controls.locked.json',
           'source-inputs.json']
    members=[ref(N/x) for x in files]
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
        'source_inputs_ref':inputs_ref,'source_controls_ref':ref(N/'source-controls.locked.json'),
        'runner_review_ref':ref(RV/'HDF.json'),
        'source_controls_pass':14,'source_controls_fail':0,
        'canonical_before_refs':canons,'proposed_canonical_revisions':{'checkpoint':371,
            'path_ownership':175,'commands':39},
        'actual_product_processes':0,'actual_SQLite_calls':0,'actual_native_calls':0,
        'root_registration':'NOT_CREATED','first_actual_request':'NOT_CREATED',
        'Root_next_original_failure_ordinal':1013,
        'end_version22':'CALLER_SOURCE_READY_PENDING_REVIEW_AND_ROOT_REGISTRATION',
        'end_version23':'SEPARATE_FRESH_MAIN23_BUILDER_SCOPE_REQUIRED',
        'end_version24':'BLOCKED_MAIN_PUBLIC_23_TO_24_NOT_ADOPTED',
        'schema21':'OPEN','full20to24':'OPEN',
        'formal_acceptance':False,'parent_acceptance':False,
        'Main_Canon_Registry_changed':False,'STOP':True,'FINAL':True})
    print(json.dumps({'handoff_ref':hdf_ref,'manifest_ref':mf_ref,
        'source_inputs_ref':inputs_ref,'members':len(members),
        'static_pins':len(refs)},ensure_ascii=False))

if __name__=='__main__':main()
