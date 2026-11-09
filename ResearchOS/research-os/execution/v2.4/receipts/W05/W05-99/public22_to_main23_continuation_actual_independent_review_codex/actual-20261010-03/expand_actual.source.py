from pathlib import Path
import json,types
R=Path(r'D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-04'
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
inventory=json.loads((D/'actual-shape-inventory.json').read_bytes())
facts=inventory['facts'];actual=inventory['actual_request'];result=inventory['registration_result']
inputs=json.loads((N/'source-inputs.json').read_bytes())
refs=[s.pin(D/'actual-shape-inventory.json'),s.pin(N/'source-inputs.json'),s.pin(__file__),s.pin(HELPER),
    *[facts[k] for k in ('request_ref','scope_ref','owner_ref','worker_ref')],
    inputs['leaf_runner_ref'],inputs['leaf_contract_ref'],inputs['main23_bound_ref'],
    s.pin(Path(result['transaction']['transaction_journal'])/'committed.json')]
refs=list({str(Path(x['path']).resolve(strict=True)):s.pin(x['path']) for x in refs}.values())
g=s.guard();value=None
try:
    g.acquire(refs)
    docs={key:json.loads(g.get_buffer(str(Path(facts[key]['path'])))) for key in ('request_ref','scope_ref','owner_ref','worker_ref')}
    leafcontract=json.loads(g.get_buffer(str(Path(inputs['leaf_contract_ref']['path']))))
    bound=json.loads(g.get_buffer(str(Path(inputs['main23_bound_ref']['path']))))
    committed=json.loads(g.get_buffer(str(Path(result['transaction']['transaction_journal'])/'committed.json')))
    value=dict(schema='researchos.public22-gen02-actual-expansion.v1',held_refs=refs,registration=docs,
        Source_inputs_ref=s.pin(N/'source-inputs.json'),Source_input_keys=list(inputs),leaf_contract=leafcontract,
        Main23_bound=bound,committed=committed,component_accepted=False,products=0,formal_acceptance=False)
finally:
    guard_ref=s.write('expansion-guard.closed.json',g.close())
    if value is not None:
        value['expansion_guard_ref']=guard_ref
        result_ref=s.write('actual-expansion.json',value)
        print(json.dumps(dict(result_ref=result_ref,registration=docs,Source_input_keys=list(inputs),
            Source_refs={k:v for k,v in inputs.items() if type(v) is dict and set(v)=={'path','sha256','bytes'}},
            evidence_keys=list(inputs['evidence']),leafcontract_keys=list(leafcontract),
            Main23_bound=bound,committed=committed,guard_ref=guard_ref,products=0),ensure_ascii=False))
