"""Bounded GEN02 review intake. No product calls or automatic actual acceptance."""
from pathlib import Path
import hashlib,json,re,sys
ACTOR='codex:/root/full_w09_source_review'
BACKEND='/root/full_w09_source_review'
FIELDS=('actual_request_ref','registration_facts_ref','registration_result_ref','execute_preentry_audit_ref',
    'execute_initial_host_capture_ref','execute_completed_host_capture_ref','case_closed_ref')
CONTRACT_SCHEMA='researchos.public22-continuation-actual-component-review-input-contract.v1'
def strict(raw):
    def pairs(items):
        value={}
        for key,item in items:
            if key in value:raise ValueError('DUPLICATE_JSON_KEY')
            value[key]=item
        return value
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
def ref_shape(ref):
    if type(ref) is not dict or set(ref)!={'path','sha256','bytes'}:raise ValueError('EXACT_REF_SHAPE')
    if type(ref['path']) is not str or not Path(ref['path']).is_absolute():raise ValueError('ABSOLUTE_REF_PATH')
    if type(ref['sha256']) is not str or re.fullmatch('[0-9a-f]{64}',ref['sha256']) is None:raise ValueError('FULL_SHA256')
    if type(ref['bytes']) is not int or ref['bytes']<0:raise ValueError('INTEGER_BYTES')
    return ref
def checked(ref):
    ref_shape(ref);raw=Path(ref['path']).read_bytes()
    if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('PIN_CHANGED')
    return raw
def prepare(contract):
    if contract['schema']!=CONTRACT_SCHEMA or contract['status']!='PREPARED_PENDING_ACTUAL':raise ValueError('PREPARATION_CONTRACT')
    generation=contract['generation']
    if generation['key']!='public22_to_main23_continuation_gen02' or generation['slice_id']!='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02':raise ValueError('EXACT_GEN02')
    if any(contract['future_delivery'][key] is not None for key in FIELDS):raise ValueError('ACTUAL_FACTS_REQUIRE_SEPARATE_REVIEW')
    if contract['current_preparation']['actual_component_accepted'] is not False:raise ValueError('NO_PREACCEPTANCE')
    return dict(status='PREPARED_PENDING_ACTUAL',actor_id=ACTOR,backend_actor_id=BACKEND,
        future_inputs={key:None for key in FIELDS},actual_component_review_performed=False,actual_children=0,
        execution_grant=False,formal_acceptance=False,parent_acceptance=False)
def intake_shape(bundle):
    """Pure layout check for later explicit review; this does not read or qualify artifacts."""
    if type(bundle) is not dict or set(bundle)!=set(FIELDS):raise ValueError('SEVEN_ACTUAL_REFS')
    for key in FIELDS:ref_shape(bundle[key])
    return dict(status='INPUT_LAYOUT_ONLY_PENDING_ACTUAL_REVIEW',actual_component_accepted=False,
        execution_grant=False,formal_acceptance=False,parent_acceptance=False)
def main(args):
    if len(args)!=4 or args[0]!='prepare':raise ValueError('PREPARE_MODE_ONLY')
    contract_ref=dict(path=args[1],sha256=args[2],bytes=int(args[3]))
    result=prepare(strict(checked(contract_ref)));result['input_contract_ref']=contract_ref
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))
    return 0
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
