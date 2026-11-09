import copy,hashlib,json
from pathlib import Path
Q=Path(__file__).resolve().parent
def pin(p):
    raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(n,v):
    p=Q/n
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def main():
    b=json.loads((Q/'source-inputs.basis.json').read_bytes());old=json.loads(Path(b['base_source_inputs_ref']['path']).read_bytes());c=json.loads(Path(b['base_contract_ref']['path']).read_bytes());caller=pin(Q/'old21_root.source.py')
    inputs=copy.deepcopy(old);inputs.update(schema='researchos.old21-caller-source-inputs.Task73.v1',caller_ref=caller,Task73_base_hdf_ref=b['base_hdf_ref'],Task73_base_mf_ref=b['base_mf_ref'],Task73_base_caller_ref=b['base_caller_ref'],Task73_base_inverse_ref=b['base_inverse_ref'],Task70_rejected_Source_review_refs=b['Task70_review_refs'],Task73_basis_ref=pin(Q/'source-inputs.basis.json'),actual_Task68_observation_ref=b['actual_Task68_observation_ref'],actual_Task68_raw_ref=b['actual_Task68_raw_ref'],future_RootScope_ref=None,future_runtime_manifest_ref=None,future_runtime_qualification_ref=None,actual_qualification_ref=None,execution_grant=False,formal_acceptance=False)
    inputs['references']+=b['references']
    iref=save('source-inputs.json',inputs)
    c.update(caller_ref=caller,registrar_ref=caller,source_inputs_ref=iref,source_author='codex:/root/backup_regression_resources',source_self_acceptance=False,actual_grant=False,formal_acceptance=False,parent_acceptance=False)
    c['Task73_minimum_revision']=dict(base_Source_hdf_ref=b['base_hdf_ref'],base_Source_mf_ref=b['base_mf_ref'],base_Caller_ref=b['base_caller_ref'],base_contract_ref=b['base_contract_ref'],Task70_independent_CHANGES_REQUIRED_refs=b['Task70_review_refs'],changed_functions=['failure_rows','projection','validate_peer_delivery'],counter_policy='In both pending validator and pure projection, type(next) is int, next >= actual current start, every ordinal is exact int, and the sequence equals range(start,next). Empty equal-start is allowed; no backwards/negative/bool/string counter, bool ordinals or gap/duplicate. Existing history, unique Origin keys, unknown NULL, and full inverse preserved.',inverse_ref=pin(Q/'Task73-exact-inverse.json'),delta_controls_ref=pin(Q/'Task73-delta-controls.json'),old_controls_reexecuted=False)
    c['builder_Source_review_contract']['legacy_actual_delivery']=dict(schema='researchos.main23-peer-review-delivery.v2',operation='SOURCE_REVIEW_WITNESS',accepted_only_for_caller_operation='BUILDER_SOURCE_REVIEW_WITNESS',component='OLD21_PROGRAMME_BUILDER_SOURCE',peer_actor='codex:/root/full_w09_source_review',root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',message_id='amsg_01a121d5-f9cd-7c73-a691-bd9060ad2d77',received_at='2026-10-09T18:03:53.678Z',original_capture_sha256='797f80403540a5f9da512f47d8698498c40bf36869fb5b4b4f64600e8d57e083',original_capture_bytes=27173,review_refs=b['known_builder_Source_review_refs'],wholeJSON_or_anchored_exact_FINAL=True,formal_acceptance=False,execution_grant=False,Root_issuer_and_actual_original_backend_metadata_gates_unchanged=True,independent_observation_is_Root_witness=False)
    c['Caller_peer_delivery_policy']=dict(schema='researchos.old21-peer-review-delivery.v2',operation='SOURCE_REVIEW_WITNESS',legacy_main23_builder_fallback_for_Caller=False,whole_JSON_strict=True,Root_source_witness_and_real_non_author_delivery_required=True)
    c['Task73_resource_qualification_policy']='Original s21root-01 was CHANGES_REQUIRED. This new Caller requires its own exact nonauthor Source review and a new real Root runtime qualification Scope/manifest/refs. Task73 creates none; prior old21 resource observations and Main23 lease do not grant execution.'
    c['previous_controls_policy']='Do not rerun original853, M4/14782/14670 or prior25 unchanged Source controls. Task73 executes only39 finite delta Source units; actual legacy body/source offsets are observationally verified, decoder tested under explicit pure stub. No Root issuer witness, Scope, runtime qualification, Go/Native/SQL/TP/model branch executes.'
    ref=save('root-calling-contract.source.json',c)
    print(json.dumps(dict(contract_ref=ref,source_inputs_ref=iref,actual_grant=False),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1');raise
    print('ROOT_PYTHON_EXIT=0')
