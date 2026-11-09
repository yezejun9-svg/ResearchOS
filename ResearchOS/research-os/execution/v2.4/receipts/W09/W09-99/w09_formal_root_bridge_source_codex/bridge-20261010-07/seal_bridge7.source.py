"""Seal prepared BR7; source author does not approve or execute this package."""
from pathlib import Path
import json, types
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('receipt_support');s.__file__=str(HELPER)
exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
actual_host=s.capture('c239cb',0,0)
refs=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file()]+[s.pin(HELPER)]
g=s.guard()
try:
    g.acquire(refs)
    metadata=json.loads(g.get_buffer(str(D/'preparation-metadata.json')))
    prefix=json.loads(g.get_buffer(str(D/'delta-controls.json')))
    tail=json.loads(g.get_buffer(str(D/'tail-delta-controls.json')))
    origin=json.loads(g.get_buffer(str(D/'original1218.origin.json')))
    assert prefix['count']==prefix['passed']==2 and tail['count']==tail['passed']==3 and tail['failure'] is None
    assert all(item['passed'] is True for result in (prefix,tail) for item in result['checks'])
    assert origin['original_ordinal']==1218 and origin['outer_exit']==origin['Python_exit']==1
    assert metadata['new_original_failures']==[1218]
    for result in (prefix,tail):
        closed=json.loads(g.get_buffer(result['source_guard_ref']['path']))
        assert closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[]
    assert metadata['source_ref']==s.pin(D/'w09_root_bridge.source.py')
    assert metadata['consumer_launcher_ref']==s.pin(D/'consumer_launch.source.py')
    assert metadata['root_calling_contract_ref']==s.pin(D/'root-calling-contract.source.json')
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
    base_source_contribution=metadata['base_source_contribution'],
    accepted_BR6_review_hdf_ref=s.pin(W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-06-attach/HDF.json'),
    accepted_BR6_review_mf_ref=metadata['base_accepted_review']['manifest_ref'],
    accepted_BR6_review_decision_ref=metadata['base_accepted_review']['decision_ref'],
    exact_inverse_ref=s.pin(D/'exact-inverse.json'),patch_ref=s.pin(D/'bridge07.patch'),
    source_inputs_ref=metadata['source_inputs_ref'],retained_successful_prefix_ref=s.pin(D/'delta-controls.json'),
    delta_controls_ref=s.pin(D/'tail-delta-controls.json'),source_guard_ref=prefix['source_guard_ref'],
    delta_source_guard_ref=tail['source_guard_ref'],seal_source_guard_ref=seal_guard,
    actual_source_build_host=actual_host,original1218_io=origin['original_io'],original1218_origin_ref=s.pin(D/'original1218.origin.json'),
    original1190_io=metadata['original1190_io'],original1185_io_preserved=metadata['original1185_io_preserved'],
    prior_Attach_review_original_diagnostics_preserved=metadata['inherited_BR6_historical_diagnostics'],
    original1208='FAILED_RETAINED_MAIN_TUPLE_TYPE_ARRAY_BOUNDARY',
    Main_root_adoption_closed_ref=metadata['Main_adoption_closed_ref'],
    Main_independent_accepted_review_ref=metadata['Main_independent_review_ref'],Main_required_ref=metadata['Main_required_ref'],
    finite_delta_controls=5,retained_successful_prefix_controls=2,newly_completed_tail_controls=3,
    old_successful_controls_rerun=False,changed_business_functions=[],
    changed_bindings=['BRIDGE_GENERATION','TRUSTED.formal_profile_w09.py'],
    changes=['Rebase generation to bridge-20261010-07.','Rebase only TRUSTED formal_profile_w09.py SHA/bytes to actual Root-adopted 1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087/71403.',
        'All function/class AST, remaining TRUSTED pins, exact Source/Root/peer/role/current4/lease/Guard/TP/TEMP contracts and sealed launcher remain unchanged.'],
    guards_closed_zero=True,retained_handles_count=0,live_Canon_handles_held=0,
    new_package_complete_inventory_held_before_seal=True,independent_source_review_required=True,
    independent_source_review_ref=None,Source_author_self_acceptance=False,new_original_failures=[1218],
    verifier_backend='/root/backup_regression_resources',future_Root_Scope_source_actor=s.ACTOR,
    future_Root_Scope_source_author_canonical='codex:/root/full_w09_source_review',fresh_formal_vector_required=True,
    Native_Source21_changed=False,successful_Native_replayed=False,Mode_decisions_reissued=False,
    future_Root_scope=None,future_Root_request=None,future_execution_grant=None,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,actual_bridge_stages=0,
    actual_Main_module_calls=0,actual_Native_Go_SQL_model_TP_calls=0,Main_Canon_Scope_written=False,
    actual_product_exits=dict(Native=None,Go=None,SQL=None,dispatcher=None,model=None,TP=None,RootStage=None),STOP=True))
print(json.dumps(dict(schema='researchos.w09-formal-root-bridge-source-delivery.v3',operation='SOURCE_PREPARATION',
    source_author='codex:/root/full_w09_source_review',source_author_backend=s.ACTOR,status='SOURCE_PREPARED',
    refs=[hdf_ref,mf_ref,metadata['root_calling_contract_ref']],caller_ref=metadata['source_ref'],
    consumer_launcher_ref=metadata['consumer_launcher_ref'],contract_ref=metadata['contract_ref'],
    finite_delta_controls=5,retained_prefix=2,new_tail=3,guards_closed_zero=True,retained_handles_count=0,
    original1218=origin['original_io'],new_original_failures=[1218],self_acceptance=False,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True),ensure_ascii=False))
