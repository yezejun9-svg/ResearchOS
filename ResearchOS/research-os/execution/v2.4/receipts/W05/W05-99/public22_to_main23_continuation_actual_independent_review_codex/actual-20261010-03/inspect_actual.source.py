from pathlib import Path
import ast,json,types
R=Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
A2=B/'public22_to_main23_continuation_actual_independent_review_codex/actual-20261010-02'
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
bundle_ref=s.pin(S/'w05.gen02.seven-actual-input.root.json')
assert bundle_ref['sha256']=='4838d3b0ecce99c69a0975643cc2116d15d33e4c7b5256ddf91a22c0c14ea829' and bundle_ref['bytes']==2419
bundle=json.loads((S/'w05.gen02.seven-actual-input.root.json').read_bytes())
source_hdf=json.loads((N/'HDF.json').read_bytes())
refs=[bundle_ref,*bundle.values(),s.pin(A2/'actual-input-contract.json'),s.pin(N/'HDF.json'),s.pin(N/'MF.json'),
    source_hdf['caller_ref'] if 'caller_ref' in source_hdf else s.pin(N/'public22_to23_root.source.py'),
    s.pin(N/'root-calling-contract.source.json'),s.pin(N/'source-inputs.json'),s.pin(__file__),s.pin(HELPER),s.GREF]
refs=list({str(Path(x['path']).resolve(strict=True)):s.pin(x['path']) for x in refs}.values())
g=s.guard();result=None
try:
    g.acquire(refs)
    data={key:json.loads(g.get_buffer(str(Path(ref['path'])))) for key,ref in bundle.items()}
    case=data['case_closed_ref'];facts=data['registration_facts_ref'];request=data['actual_request_ref']
    result=dict(schema='researchos.public22-gen02-actual-shape-inventory.v1',bundle_ref=bundle_ref,
        held_refs=refs,document_keys={key:list(value) for key,value in data.items()},
        case_scalars={k:v for k,v in case.items() if v is None or type(v) in (str,int,bool)},
        facts=facts,actual_request=request,registration_result=data['registration_result_ref'],
        preentry=data['execute_preentry_audit_ref'],initial_host=data['execute_initial_host_capture_ref'],
        completed_host=data['execute_completed_host_capture_ref'],
        calls=case.get('calls'),observation_shapes={k:s.shape(v) for k,v in case.get('observations',{}).items()},
        case_top_refs={k:v for k,v in case.items() if type(v) is dict and set(v)=={'path','sha256','bytes'}},
        cleanup_shape=s.shape(case.get('source_guard_cleanup')),recoverability=case.get('recoverability'),
        publication=case.get('publication'),new_Native_SQL_TP_Go_RootStage_model_calls=0,
        actual_component_accepted=False,execution_grant=False,formal_acceptance=False)
finally:
    guard_ref=s.write('inventory-guard.closed.json',g.close())
    if result is not None:
        result['inventory_guard_ref']=guard_ref
        result_ref=s.write('actual-shape-inventory.json',result)
        print(json.dumps(dict(result_ref=result_ref,case_keys=result['document_keys']['case_closed_ref'],
            facts_keys=list(result['facts']),scope_ref=result['facts'].get('scope_ref'),
            call_phases=[v.get('phase') for v in result['calls']],call_keys=[list(v) for v in result['calls']],
            observation_keys=list(result['observation_shapes']),cleanup=result['cleanup_shape'],
            registration_result=result['registration_result'],preentry=result['preentry'],
            initial_host=result['initial_host'],completed_host=result['completed_host'],
            guard_ref=guard_ref,products=0,formal_acceptance=False),ensure_ascii=False))
