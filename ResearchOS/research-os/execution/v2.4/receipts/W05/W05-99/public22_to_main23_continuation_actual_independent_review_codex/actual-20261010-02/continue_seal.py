"""Finish only unreached sealing after retained original1223; no check/resource replay."""
from pathlib import Path
import datetime,json,types
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('support');s.__file__=str(HELPER);exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
ctx=json.loads((D/'preparation-context.json').read_bytes());result=json.loads((D/'preparation-result.json').read_bytes())
guard=json.loads(Path(result['source_guard_ref']['path']).read_bytes())
assert result['count']==result['passed']==4 and result['failure'] is None
assert guard['closed'] is True and guard['retained_handles_count']==0 and not guard['errors']
pair=json.loads((D/'preparation-hostpair.json').read_bytes())
assert s.pin(pair['raw_ref']['path'])==pair['raw_ref'] and s.pin(pair['binding_ref']['path'])==pair['binding_ref']
failed_pair=s.capture('2018ec',1,1,1223)
failure=dict(original_ordinal=1223,actual_chunk_id='2018ec',original_io=failed_pair,original_script_ref=s.pin(D/'seal_preparation.py'),
    retained_preparation_result_ref=s.pin(D/'preparation-result.json'),retained_guard_ref=result['source_guard_ref'],successful_retained_checks=4,
    actual_outer_exit=1,actual_Python_exit=1,actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,actual_TP_exit=None,
    actual_dispatcher_exit=None,actual_RootStage_exit=None,actual_model_exit=None,product_failure=False,
    reason='Reviewer sealer passed a context field and explicit same field twice to dict(). No decision/HDF/MF was written by the failed invocation.',
    status='FAILED_RETAINED_REVIEWER_INSTRUMENTATION_ONLY',successful_checks_replayed=False)
origin_ref=s.write('sealer-failure.origin.json',failure)
created=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
bindings={key:value for key,value in ctx.items() if key not in ('actual_component_review_performed','actual_component_accepted','product_calls')}
decision=dict(schema='researchos.public22-continuation-actual-review-preparation-decision.v1',status='PREPARED_PENDING_ACTUAL',
    actor_id='codex:/root/full_w09_source_review',backend_actor_id='/root/full_w09_source_review',
    prepared_utc=created,**bindings,actual_preparation_hostpair=pair,source_guard_ref=result['source_guard_ref'],
    new_schema_pin_checks=4,prior_controls_replayed=False,prior_runtime149_144_replayed=False,
    future_actual_inputs=None,actual_component_review_performed=False,actual_component_accepted=False,actual_native_children=0,
    fresh_GEN02_registration_required=True,old_original1201_case_usable_for_new_acceptance=False,
    complete_case_closed_and_real_hostpairs_required=True,stdout_truncation_cannot_create_returned_state=True,
    runtime_resource_review_reused_only=True,future_Root_runtime_observation_required=True,
    old_Source04_review_unchanged=True,Root_reported_original1222_peer_capture_failure_retained=True,
    new_review_failures=[failure],failure_origin_ref=origin_ref,all_guards_closed_zero=True,retained_handles_count=0,live_Canon_handles_held=0,
    private_material_read_or_hashed=False,product_calls=0,Main_Canon_Scope_Registry_written=False,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,STOP=True)
dref=s.write('preparation-decision.json',decision)
members=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file() and path.name not in ('HDF.json','MF.json')]
mref=s.write('MF.json',dict(schema='researchos.public22-continuation-review-preparation-manifest.v1',members=members,
    exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
href=s.write('HDF.json',dict(schema='researchos.public22-continuation-actual-review-preparation-handoff.v1',
    actor_id=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],actor_thread_id=s.THREAD,
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',status='PREPARED_PENDING_ACTUAL',prepared_utc=created,
    decision_ref=dref,manifest_ref=mref,**bindings,source_guard_ref=result['source_guard_ref'],actual_preparation_hostpair=pair,
    new_schema_pin_checks=4,prior_controls_replayed=False,prior_runtime149_144_replayed=False,
    future_actual_bundle=None,actual_component_review_performed=False,actual_component_accepted=False,actual_children=0,
    new_review_failures=[failure],failure_origin_ref=origin_ref,all_guards_closed_zero=True,retained_handles_count=0,live_Canon_handles_held=0,
    private_material_read_or_hashed=False,product_calls=0,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
    formal_case_accepted_delta=0,STOP=True))
manifest=json.loads(Path(mref['path']).read_bytes());assert dref in manifest['members']
assert all(s.pin(ref['path'])==ref for ref in manifest['members'])
print(json.dumps(dict(schema='researchos.public22-continuation-actual-review-preparation-delivery.v1',
    operation='ACTUAL_REVIEW_PREPARATION',review_author=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],
    root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',status='PREPARED_PENDING_ACTUAL',
    preparation_refs=[href,mref,dref],calling_contract_ref=ctx['calling_contract_ref'],caller_ref=ctx['caller_ref'],
    input_contract_ref=ctx['input_contract_ref'],new_schema_pin_checks=4,
    accepted_Source04_review_redelivery=dict(operation='SOURCE_REVIEW_WITNESS',verdict='ACCEPTED_SOURCE_ONLY',
        review_author=decision['actor_id'],source_author='codex:/root/attach_restore_independent_review',review_refs=ctx['Source04_review_refs'],
        original_review_unchanged=True,execution_grant=False,formal_acceptance=False),
    future_actual_bundle=None,actual_component_review_performed=False,actual_component_accepted=False,actual_children=0,
    all_guards_closed_zero=True,retained_handles_count=0,new_review_failures=[failure],
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True),ensure_ascii=False,indent=2))
