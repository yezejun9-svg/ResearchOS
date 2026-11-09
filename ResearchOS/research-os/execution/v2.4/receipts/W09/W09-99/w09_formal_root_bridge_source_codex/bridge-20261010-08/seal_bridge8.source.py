"""Seal BR8 Source preparation only; independent review and actual Root authority are future inputs."""
from pathlib import Path
import json, types
R=Path(r'D:/作品集/ResearchOS/research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
original_io=s.capture('f5ac7c',1,None,1229)
actual_host=s.capture('39f676',0,0)
origin_ref=s.write('original1229.origin.json',dict(schema='researchos.original-source-failure.v1',
    original_ordinal=1229,Root_assigned=True,actual_chunk_id='f5ac7c',outer_exit=1,Python_exit=None,
    Native_exit=None,Go_exit=None,SQL_exit=None,dispatcher_exit=None,model_exit=None,TP_exit=None,RootStage_exit=None,
    original_io=original_io,reason='Read-only command successfully read Main audit range methods and diagnosis HDF; final Get-Content used an incorrect W09 Guard path instead of the existing W05 path.',
    successful_prefix_preserved=True,successful_reads_replayed=False,SourceGuard_acquire_attempted=False,
    product_calls=0,Main_Canon_Scope_writes=0,failure_count_reset=False))
refs=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file()]+[s.pin(HELPER),s.GREF]
g=s.guard()
try:
    g.acquire(refs)
    metadata=json.loads(g.get_buffer(str(D/'preparation-metadata.json')))
    controls=json.loads(g.get_buffer(str(D/'delta-controls.json')))
    closed=json.loads(g.get_buffer(controls['source_guard_ref']['path']))
    assert controls['count']==controls['passed']==8 and controls['failure'] is None
    assert all(item['passed'] is True for item in controls['checks'])
    assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    assert metadata['source_ref']==s.pin(D/'w09_root_bridge.source.py')
    assert metadata['consumer_launcher_ref']==s.pin(D/'consumer_launch.source.py')
    assert metadata['root_calling_contract_ref']==s.pin(D/'root-calling-contract.source.json')
    inverse=json.loads(g.get_buffer(str(D/'exact-inverse.json')))
    assert inverse['complete_byte_inverse'] is True
    assert inverse['changed_business_functions']==['historical_dependency_refs']
    assert inverse['other_functions_classes_AST_unchanged'] is True
finally:
    seal_guard=s.write('seal-source-guard.closed.json',g.close())
members=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file() and path.name not in ('HDF.json','MF.json')]
mf_ref=s.write('MF.json',dict(schema='researchos.w09-formal-root-bridge-source-manifest.v3',members=members,
    exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf_ref=s.write('HDF.json',dict(schema='researchos.w09-formal-root-bridge-source-handoff.v3',
    source_author='codex:/root/full_w09_source_review',source_author_backend=s.ACTOR,
    actual_source_thread=s.THREAD,actual_parent_thread='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    status='SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW',generation=metadata['generation'],
    created_utc=metadata['created_utc'],source_revision_uuid=metadata['source_revision_uuid'],
    source_ref=metadata['source_ref'],consumer_launcher_ref=metadata['consumer_launcher_ref'],
    contract_ref=metadata['contract_ref'],root_calling_contract_ref=metadata['root_calling_contract_ref'],manifest_ref=mf_ref,
    base_hdf_ref=metadata['base_hdf_ref'],base_mf_ref=metadata['base_mf_ref'],base_source_ref=metadata['base_source_ref'],
    base_source_contribution=metadata['retained_original_author_contribution'],
    boundary_diagnosis_hdf_ref=metadata['diagnosis_hdf_ref'],boundary_diagnosis_mf_ref=metadata['diagnosis_mf_ref'],
    boundary_diagnosis_decision_ref=metadata['independent_boundary_diagnosis_ref'],
    boundary_diagnosis_facts_ref=metadata['diagnosis_facts_ref'],
    exact_inverse_ref=s.pin(D/'exact-inverse.json'),patch_ref=s.pin(D/'bridge08.patch'),
    source_inputs_ref=metadata['source_inputs_ref'],delta_controls_ref=s.pin(D/'delta-controls.json'),
    source_guard_ref=controls['source_guard_ref'],seal_source_guard_ref=seal_guard,
    actual_source_build_host=actual_host,original1229_io=original_io,original1229_origin_ref=origin_ref,
    original1224=metadata['original1224'],original1225_origin_ref=metadata['original1225_origin_ref'],
    historical_original1218_io=metadata['historical_original1218_io'],failure_count_reset=False,
    Main_required_ref=metadata['Main_required_ref'],Native_Source21_changed=False,
    finite_delta_controls=8,old_successful_controls_rerun=False,
    changed_business_functions=['historical_dependency_refs'],changed_bindings=['BRIDGE_GENERATION'],
    typed_audit_range_branch='dependency_snapshot.audit_ranges',clone_only_omission=True,
    original_snapshot_and_ranges_preserved=True,normalized_Canon_range_alias_refusal_preserved=True,
    dedicated_Main_range_rechecks_preserved=True,general_foreign_C_path_exception=False,
    physical_checked_references_resource_owner_unchanged=True,other_functions_classes_AST_unchanged=True,
    complete_byte_inverse_to_BR7=True,consumer_launcher_unchanged=True,
    guards_closed_zero=True,retained_handles_count=0,guard_errors=[],live_Canon_handles_held=0,
    live_audit_log_handles_held=0,new_package_complete_inventory_held_before_seal=True,
    independent_source_review_required=True,independent_source_review_ref=None,
    Source_author_self_acceptance=False,new_original_failures=[1229],
    verifier_backend='/root/backup_regression_resources',future_Root_Scope_source_actor=s.ACTOR,
    future_Root_Scope_source_author_canonical='codex:/root/full_w09_source_review',fresh_formal_vector_required=True,
    successful_Native_replayed=False,Mode_decisions_reissued=False,
    future_Root_scope=None,future_Root_request=None,future_execution_grant=None,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,actual_bridge_stages=0,
    actual_Main_module_calls=0,actual_Native_Go_SQL_model_TP_calls=0,Main_Canon_Scope_Registry_written=False,
    actual_product_exits=dict(Native=None,Go=None,SQL=None,dispatcher=None,model=None,TP=None,RootStage=None),STOP=True))
print(json.dumps(dict(schema='researchos.w09-formal-root-bridge-source-delivery.v3',operation='SOURCE_PREPARATION',
    source_author='codex:/root/full_w09_source_review',source_author_backend=s.ACTOR,status='SOURCE_PREPARED',
    refs=[hdf_ref,mf_ref,metadata['root_calling_contract_ref']],caller_ref=metadata['source_ref'],
    consumer_launcher_ref=metadata['consumer_launcher_ref'],contract_ref=metadata['contract_ref'],
    exact_inverse_ref=s.pin(D/'exact-inverse.json'),delta_controls_ref=s.pin(D/'delta-controls.json'),
    source_guard_ref=controls['source_guard_ref'],seal_source_guard_ref=seal_guard,
    finite_delta_controls=8,changed_business_functions=['historical_dependency_refs'],
    original1229=original_io,new_original_failures=[1229],guards_closed_zero=True,retained_handles_count=0,
    old_successful_controls_replayed=False,self_acceptance=False,execution_grant=False,
    formal_acceptance=False,parent_acceptance=False,STOP=True),ensure_ascii=False))
