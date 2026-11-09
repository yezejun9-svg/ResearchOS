from pathlib import Path
import datetime, json, types

D=Path(__file__).resolve().parent
B=D.parent.parent
N=B/'public22_to_main23_continuation_caller_source_codex/continue-20261010-02'
W=B.parents[1]/'W09/W09-99'
S=W/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
P=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(P)
exec(compile(P.read_bytes(),str(P),'exec'),s.__dict__);s.D=D
def read(p):return json.loads(Path(p).read_bytes())
c=s.inert(N/'public22_to23_root.source.py')
h=read(N/'HDF.json');i=read(N/'source-inputs.json');prefix=read(N/'historical-review-prefix.json')
result=read(D/'independent-delta-result.json');runtime=read(D/'runtime-public-closure.json')
assert result['all_passed'] and result['passed_count']==result['check_count']
assert runtime['missing']==[] and runtime['complete_exact_loaded_public_closure']
guards=[runtime['guard_closed_ref'],result['guard_closed_ref']]
guard_counts=[]
for ref in guards:
    g=read(ref['path']);assert g['closed'] and g['retained_handles_count']==0 and g['errors']==[]
    guard_counts.append(dict(ref=ref,held_count=len(g['entries']),closed=True,retained_handles_count=0))
delta_pair=s.capture('9bf11a',0,0)
s.write('actual-independent-delta-hostpair.json',delta_pair)
reviewed=datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')
bindings=dict(source_hdf_ref=s.pin(N/'HDF.json'),source_mf_ref=s.pin(N/'MF.json'),caller_ref=h['caller_ref'],
    source_inputs_ref=h['source_inputs_ref'],calling_contract_ref=h['calling_contract_ref'],
    runtime_resources_ref=i['runtime_resources_ref'],main23_bound_ref=i['main23_bound_ref'],existing22_decision_ref=i['existing22_decision_ref'])
decision=dict(schema='researchos.public22-continuation-root-independent-source-decision.v1',
    decision='ACCEPTED_SOURCE_ONLY',actor_id='codex:/root/full_w09_source_review',actor_role='INDEPENDENT_NON_AUTHOR',
    backend_actor_id='/root/full_w09_source_review',reviewer_thread_id=s.THREAD,Root_thread_id=c.ROOT_THREAD,
    source_author=c.AUTHOR,reviewed_utc=reviewed,**bindings,
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
    original1025_result='FAILED_RETAINED',continuation_only=True,runtime_closure_reviewed=True,
    runtime_closure_evidence_ref=s.pin(D/'runtime-public-closure.json'),
    independent_delta_evidence_ref=s.pin(D/'independent-delta-result.json'),
    prior_changes_required_decision_ref=prefix['independent_changes_required_refs'][2],
    closed_finding=dict(id='P22C-OBSERVATION-CLOSE-001',status='RESOLVED_SOURCE_ONLY',
        evidence='Returned observations are retained inside the output contexts. Inner/outer close faults and pre-existing primary failures preserve known exit, integer/decimal FILETIME and Job cleanup; absent observation remains NULL.'),
    findings=[],new_independent_checks=result['check_count'],
    reused=dict(author_close_controls=3,prior_Source_controls=14,prior_resource_guard_count=781,
        rerun=False,prefix_ref=h['historical_review_prefix_ref']),
    runtime_review_boundary=dict(manifest_resource_count=runtime['runtime_manifest_resource_count'],
        actual_public_required_count=runtime['required_count'],missing_resources=[],
        actual_inert_source_loading=True,actual_loaded_DLL_inventory=True,
        reviewer_instrumentation_entry_excluded_explicitly=runtime['excluded_instrumentation_refs'],
        Caller_exact_entry_ref_included=h['caller_ref'],SQL_import_only=True,SQL_connections=0,
        future_Root_runtime_qualification_issued=False,
        future_Root_must_reobserve_current_exact_runtime_before_guard_and_execution=True),
    actual_Source_author_audit_ref=s.pin(S/'w09.public22-main23-continuation-source02.actual-audit.root.json'),
    original_source_failure_ordinals_preserved=h['original_failure_ordinals'],new_review_failures=[],
    all_acquired_source_guards_closed=True,retained_handles_count=0,guard_evidence=guard_counts,
    product_calls=dict(Native=0,Go=0,SQL=0,TP=0,RootStage=0,model=0),
    future_Root_requirements=['Actual review Final capture with fixed parent/backend identity, original offsets and full typed refs; no precreated witness.',
        'Fresh finite Root owner/worker/lease and continuation Scope with current4 dynamic CAS; existing evidence and original1025 remain unchanged.',
        'Actual Caller __main__ loaded resource closure and original runtime manifest pins must pass before Root registration/execution.',
        'Only three new public children in unused output root; complete real hostpair and independent component review afterward.'],
    remaining_OPEN=['new independent negative public child','schema23to24','original-data cutover','full20to24'],STOP=True)
decision_ref=s.write('decision.json',decision)
members=[s.pin(p) for p in sorted(D.iterdir(),key=lambda x:x.name) if p.is_file()]
mf_ref=s.write('MF.json',dict(schema='researchos.public22-continuation-independent-source-MF.v1',members=members,
    exclusions=['HDF.json','MF.json','postseal.actual-tool-io.json'],source_only=True))
review_hdf=dict(schema='researchos.public22-continuation-independent-source-HDF.v1',
    actor_id=decision['actor_id'],actor_role=decision['actor_role'],backend_actor_id=decision['backend_actor_id'],
    source_author=c.AUTHOR,reviewed_utc=reviewed,status='ACCEPTED_SOURCE_ONLY',source_decision_ref=decision_ref,
    manifest_ref=mf_ref,**bindings,
    runtime_closure_reviewed=True,runtime_closure_evidence_ref=decision['runtime_closure_evidence_ref'],
    new_independent_checks=result['check_count'],reused=decision['reused'],
    original1025_result='FAILED_RETAINED',original_source_failure_ordinals_preserved=h['original_failure_ordinals'],
    new_review_failures=[],all_acquired_source_guards_closed=True,retained_handles_count=0,guard_evidence=guard_counts,
    actual_source_tool_pairs=[read(D/'actual-runtime-probe-hostpair.json'),delta_pair],
    formal_acceptance=False,parent_acceptance=False,execution_grant=False,
    future_Root_runtime_qualification_issued=False,formal_case_accepted_delta=0,STOP=True)
hdf_ref=s.write('HDF.json',review_hdf)
# Check only the published own-review interface and its own exact refs; no Root request/Scope fixture.
assert decision['schema']=='researchos.public22-continuation-root-independent-source-decision.v1'
assert decision['decision']=='ACCEPTED_SOURCE_ONLY' and decision['actor_id']==review_hdf['actor_id']
assert decision['actor_id'] not in (c.ROOT,c.AUTHOR,c.LEAF_AUTHOR) and decision['actor_role']=='INDEPENDENT_NON_AUTHOR'
assert c.same(review_hdf['source_decision_ref'],decision_ref) and decision_ref in members
assert all(c.same(decision[k],v) for k,v in bindings.items())
assert decision['runtime_closure_reviewed'] and decision['continuation_only'] and decision['original1025_result']=='FAILED_RETAINED'
assert not decision['formal_acceptance'] and not decision['execution_grant']
print(json.dumps(dict(schema='researchos.public22-continuation-peer-review-delivery.v1',operation='SOURCE_REVIEW_WITNESS',
    review_author=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],source_author=c.AUTHOR,
    Root_thread_id=c.ROOT_THREAD,verdict='ACCEPTED_SOURCE_ONLY',review_refs=[hdf_ref,mf_ref,decision_ref],
    new_independent_checks=result['check_count'],runtime_manifest_resources=runtime['runtime_manifest_resource_count'],
    actual_loaded_required_resources=runtime['required_count'],runtime_closure_reviewed=True,
    reused_controls=dict(author_delta=3,old_Source=14,old_resource_guard=781,rerun=False),
    all_source_guards_closed=True,retained_handles_count=0,new_failures=[],
    original1025_result='FAILED_RETAINED',original_source_failure_ordinals_preserved=h['original_failure_ordinals'],
    execution_grant=False,formal_acceptance=False,future_Root_runtime_qualification_issued=False,STOP=True),ensure_ascii=False))
