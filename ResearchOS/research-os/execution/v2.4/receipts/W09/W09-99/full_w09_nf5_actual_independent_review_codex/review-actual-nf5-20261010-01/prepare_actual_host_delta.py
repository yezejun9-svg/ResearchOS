import hashlib,json,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def main():
    raw=(Q/'review_actual_nf5.py').read_bytes();namespace={'__file__':str(Q/'review_actual_nf5.py'),'__name__':'Source_delta_only'}
    exec(compile(raw,'nf5_review_Source','exec'),namespace)
    shapes=json.loads((Q/'actual-input-shapes.json').read_bytes());ready=namespace['decode'](namespace['read_ref'](shapes['G02_prepare_ref']))
    c=namespace['decode'](namespace['read_ref'](shapes['choice_ref']))['selectors']['W09-G02']
    initial=pin(S/'nf5-G02-prepare-initial.host-pair.root.json');completed=pin(S/'nf5-G02-prepare-completed.host-pair.root.json')
    pair=namespace['root_prepare_pair'](initial,completed,ready,c,ready['request_ref'])
    result=dict(schema='researchos.nf5-reviewer-host-delta-controls.v1',controls=[dict(name='actual-prepare-header-call-session-completion-ready',status='PASS'),dict(name='initial-yield-is-not-completion',status='PASS',initial_exit=pair[0]['actual_host_result'].get('exit_code'),actual_session=pair[0]['actual_host_result']['session_id'])],
        original_immutable_host_refs=[initial,completed],Native_called=False,Root_stage_called=False,qualification_issued=False,formal_acceptance=False)
    with(Q/'prepare-host-delta-controls.json').open('xb')as f:f.write((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    contract=json.loads((Q/'input-contract.json').read_bytes());contract['previous_contract_ref']=pin(Q/'input-contract.json')
    contract['reviewer_program_ref']=pin(Q/'review_actual_nf5.py')
    contract['group_exact_fields']=['prepare_ref','producer_closed_ref','prepare_initial_Root_capture_ref','prepare_completed_Root_capture_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref']
    contract['Root_prepare_contract']='consume existing Root host-pair initial+completed and original header/call/output; same actual session; completed outer/Python0; parsed producer progress publication joins real prepare.ready; no extra observation artifact exists or is synthesized'
    contract['new_host_delta_controls_ref']=pin(Q/'prepare-host-delta-controls.json')
    with(Q/'input-contract.v2.json').open('xb')as f:f.write((json.dumps(contract,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status='HOST_CONTRACT_DELTA_READY_WAITING_FOR_FOUR_ACTUAL',delta_controls=2,input_contract_ref=pin(Q/'input-contract.v2.json'),program_ref=pin(Q/'review_actual_nf5.py'),Native_called=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
