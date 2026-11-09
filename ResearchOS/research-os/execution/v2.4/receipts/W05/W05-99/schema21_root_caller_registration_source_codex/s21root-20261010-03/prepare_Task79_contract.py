import copy,hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    r=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    b=json.loads((Q/'source-inputs.basis.json').read_bytes());inputs=json.loads(Path(b['base_source_inputs_ref']['path']).read_bytes());c=json.loads(Path(b['base_contract_ref']['path']).read_bytes());caller=pin(Q/'old21_root.source.py')
    inputs=copy.deepcopy(inputs);inputs.update(schema='researchos.old21-caller-source-inputs.Task79.v1',caller_ref=caller,Task79_base_hdf_ref=b['base_hdf_ref'],Task79_base_mf_ref=b['base_mf_ref'],Task79_base_caller_ref=b['base_caller_ref'],Task79_base_inverse_ref=b['base_inverse_ref'],Task79_basis_ref=pin(Q/'source-inputs.basis.json'),actual_Task76_observation_ref=b['actual_Task76_observation_ref'],actual_Task76_raw_ref=b['actual_Task76_raw_ref'],Root_original1091_preservation='Root-owned immutable original; not read, altered, reset or recategorized here',future_RootScope_ref=None,future_runtime_manifest_ref=None,future_runtime_qualification_ref=None,future_programme_qualification_ref=None,execution_grant=False,formal_acceptance=False)
    inputs['references']+=b['references']+[b['actual_Task76_observation_ref'],b['actual_Task76_raw_ref']]
    iref=save('source-inputs.json',inputs)
    c.update(caller_ref=caller,registrar_ref=caller,source_inputs_ref=iref,actual_grant=False,source_self_acceptance=False,formal_acceptance=False,parent_acceptance=False)
    c['Task79_minimum_revision']=dict(base_Source_hdf_ref=b['base_hdf_ref'],base_Source_mf_ref=b['base_mf_ref'],base_Caller_ref=b['base_caller_ref'],base_contract_ref=b['base_contract_ref'],only_changed_function='validate_peer_delivery',time_policy='Complete actual adjacent metadata then backend Final; metadata timestamp <= Final timestamp and interval <=1 second. Ordinal, actor/root thread/recipient/client_authored, original source offsets/bytes and strict JSON gates remain unchanged.',exact_inverse_ref=pin(Q/'Task79-exact-inverse.json'),controls_ref=pin(Q/'Task79-time-delta-controls.json'),actual_platform_observation_ref=b['actual_Task76_observation_ref'],actual_platform_raw_ref=b['actual_Task76_raw_ref'],counter_and_legacy_Source_guards_unchanged=True,old39_59_853_14782_not_reexecuted=True)
    c['peer_metadata_final_time_policy']=dict(minimum_interval_seconds=0,maximum_interval_seconds=1,adjacent_ordinal_required=True,original_source_bytes_required=True,Source_observation_is_Root_witness=False,Task76_real_interval_ms=1,Task68_legacy_exact_raw_message_time_binding_unchanged=True)
    c['Task79_resource_qualification_policy']='Source03 is a new exact resource and requires its own nonauthor Source review and future Root runtime manifest/Scope/qualification binding. Source03 does not borrow Source02, old21 resource-only Scope, Main23 lease, or actual execution authority.'
    c['previous_controls_policy']='Only10 necessary time delta/AST/compatibility Source observations executed in Task79. Old39/59/853/14782 inputs not repeated. Decode units explicitly bypass Root issuer binding and create no Root witness/Scope/qualification; real original bytes observed separately.'
    ref=save('root-calling-contract.source.json',c)
    print(json.dumps(dict(contract_ref=ref,source_inputs_ref=iref,actual_grant=False),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
