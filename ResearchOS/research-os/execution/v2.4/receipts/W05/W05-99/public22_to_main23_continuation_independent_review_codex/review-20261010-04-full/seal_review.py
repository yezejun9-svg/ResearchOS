"""Seal retained true host records and Source04 review without another resource acquisition."""
from pathlib import Path
import copy,datetime,json,types
R=Path(r'D:\作品集\ResearchOS\research-os');B=R/'execution/v2.4/receipts/W05/W05-99';W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent;HELPER=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('support');s.__file__=str(HELPER);exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),s.__dict__);s.D=D
prefix=json.loads((D/'independent-delta-result.json').read_bytes());tail=json.loads((D/'tail-delta-result.json').read_bytes())
last=json.loads((D/'author-tail-result.json').read_bytes());ctx=json.loads((D/'review-preparation-context.json').read_bytes())
assert prefix['count']==prefix['passed']==7 and tail['passed']==12 and last['count']==last['passed']==5 and last['failure'] is None
guards=[]
for result in (prefix,tail,last):
    ref=result['source_guard_ref'];closed=json.loads(Path(ref['path']).read_bytes())
    assert s.pin(ref['path'])==ref and closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
    guards.append(dict(ref=ref,held_count=result['held_count'],closed=True,retained_handles_count=0))
captures=[s.capture('01dd30',1,1,1219),s.capture('4879c7',1,1,1220),s.capture('92da0d',0,0)]
failures=[]
for ordinal,chunk,script,result,reason,cap in [
    (1219,'01dd30','review_generation.py',prefix,'Reviewer future-counter memory fixture treated the actual list as dict; seven successful prefix predicates retained.',captures[0]),
    (1220,'4879c7','continue_generation.py',tail,'Reviewer misapplied Caller typed-review-ref predicate to the real author Markdown publication; twelve successful tail predicates retained. Caller typed FINAL gate unchanged.',captures[1])]:
    failures.append(dict(original_ordinal=ordinal,actual_chunk_id=chunk,original_io=cap,original_script_ref=s.pin(D/script),
        original_result_ref=s.pin(D/('independent-delta-result.json' if ordinal==1219 else 'tail-delta-result.json')),
        original_guard_ref=result['source_guard_ref'],successful_retained_checks=result['passed'],
        actual_outer_exit=1,actual_Python_exit=1,actual_Native_exit=None,actual_Go_exit=None,actual_SQL_exit=None,
        actual_TP_exit=None,actual_RootStage_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,
        reason=reason,product_failure=False,status='FAILED_RETAINED_REVIEWER_INSTRUMENTATION_ONLY',no_successful_control_replay=True))
failure_ref=s.write('review-failures.origin.json',dict(original_failures=failures,counter_reset=False,Root_ordinals_only=True))
bindings={key:ctx[key] for key in ('source_hdf_ref','source_mf_ref','caller_ref','source_inputs_ref','calling_contract_ref','runtime_resources_ref','main23_bound_ref','existing22_decision_ref')}
runtime=copy.deepcopy(ctx['runtime_boundary']);runtime['Caller_exact_entry_ref_included']=ctx['caller_ref']
runtime['Source04_entry_binding']='Exact Source04 entry was held by Source delta Guards; all prior imports/functions except pure projection generation precondition are unchanged.'
runtime['Source04_resource_reinspection']='Inherited sealed 149-resource/144-actual-public-runtime closure; no replay or fresh Root runtime qualification issued.'
created=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
checks=prefix['checks']+[x for x in tail['checks'] if x['passed']]+last['checks']
assert len(checks)==24 and all(x['passed'] for x in checks)
reused=dict(Source03_review_decision_ref=ctx['inherited_review_ref'],Source03_independent_checks=26,
    Source03_author_controls=12,Source02_runtime_manifest_resources=149,Source02_runtime_actual_public_required=144,
    Source04_author_controls=19,author_controls_replayed=False,prior_checks_replayed=False)
decision=dict(schema='researchos.public22-continuation-root-independent-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',
    actor_id='codex:/root/full_w09_source_review',backend_actor_id='/root/full_w09_source_review',actor_role='INDEPENDENT_NON_AUTHOR',
    source_author=ctx['source_author'],reviewed_utc=created,**bindings,
    original1025_result='FAILED_RETAINED',original1201_result='FAILED_RETAINED',continuation_only=True,
    runtime_closure_reviewed=True,runtime_closure_evidence_ref=ctx['runtime_closure_evidence_ref'],runtime_review_boundary=runtime,
    new_independent_checks=24,successful_retained_prefix=7,successful_retained_generation_tail=12,newly_completed_author_runtime_tail=5,
    checks=checks,reused=reused,predecessor_lineage_ref=ctx['lineage_ref'],actual_source_author_audit_ref=ctx['actual_source_author_audit_ref'],
    source_observations=ctx['observations'],new_review_failures=failures,original_failure_evidence_ref=failure_ref,
    original_source_failure_ordinals_preserved=[1170,1171,1174,1175,1201,1205,1206],
    actual_source_tool_pairs=captures,guard_evidence=guards,all_acquired_source_guards_closed=True,retained_handles_count=0,
    future_Root_constraints=dict(new_generation='GEN02',fresh_registration_required=True,new_scope_and_lease_required=True,
        current_four_must_be_observed_by_Root=True,old_CP386_OW190_archives_supply_only_predecessor_closed_proof=True,
        old_failed_consumed_scope_must_not_be_reused=True,Root_actual_review_typed_Final_capture_required=True,
        future_runtime_qualification_and_actual_three_phases_required=True,full20_to24='OPEN'),
    product_calls=dict(Native=0,Go=0,SQL=0,dispatcher=0,TP=0,RootStage=0,model=0),
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
    future_Root_runtime_qualification_issued=False,STOP=True)
dref=s.write('decision.json',decision)
members=[s.pin(path) for path in sorted(D.iterdir()) if path.is_file() and path.name not in ('HDF.json','MF.json')]
mref=s.write('MF.json',dict(schema='researchos.public22-continuation-independent-source-MF.v1',members=members))
href=s.write('HDF.json',dict(schema='researchos.public22-continuation-independent-source-HDF.v1',
    actor_id=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],actor_role=decision['actor_role'],source_author=ctx['source_author'],
    reviewed_utc=created,status='ACCEPTED_SOURCE_ONLY',source_decision_ref=dref,manifest_ref=mref,**bindings,
    runtime_closure_reviewed=True,runtime_closure_evidence_ref=ctx['runtime_closure_evidence_ref'],new_independent_checks=24,
    successful_retained_prefix=7,successful_retained_generation_tail=12,newly_completed_author_runtime_tail=5,reused=reused,
    predecessor_lineage_ref=ctx['lineage_ref'],actual_source_author_audit_ref=ctx['actual_source_author_audit_ref'],
    original1025_result='FAILED_RETAINED',original1201_result='FAILED_RETAINED',original_source_failure_ordinals_preserved=decision['original_source_failure_ordinals_preserved'],
    new_review_failures=failures,actual_source_tool_pairs=captures,all_acquired_source_guards_closed=True,
    retained_handles_count=0,guard_evidence=guards,execution_grant=False,formal_acceptance=False,parent_acceptance=False,
    formal_case_accepted_delta=0,future_Root_runtime_qualification_issued=False,STOP=True))
manifest=json.loads(Path(mref['path']).read_bytes())
assert dref in manifest['members'] and all(s.pin(ref['path'])==ref for ref in manifest['members'])
assert all(decision[key]==ctx[key] for key in bindings) and s.pin(href['path'])==href
delivery=dict(schema='researchos.public22-continuation-source-review-delivery.v1',operation='SOURCE_REVIEW_WITNESS',
    review_author=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    source_author=ctx['source_author'],verdict='ACCEPTED_SOURCE_ONLY',review_refs=[href,mref,dref],
    new_independent_checks=24,reused=reused,new_review_failures=failures,all_guards_closed=True,retained_handles_count=0,
    runtime_closure_reviewed=True,future_Root_runtime_qualification_issued=False,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True)
print(json.dumps(delivery,ensure_ascii=False,indent=2))
