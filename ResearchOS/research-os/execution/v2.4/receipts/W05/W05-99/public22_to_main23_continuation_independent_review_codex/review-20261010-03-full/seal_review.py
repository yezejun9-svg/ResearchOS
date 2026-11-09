"""Seal retained Source03 delta evidence; no product invocation or prior checks replay."""
from pathlib import Path
import datetime, json, types

R = Path(r'D:\作品集\ResearchOS\research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
N = B / 'public22_to_main23_continuation_caller_source_codex/continue-20261010-03'
PRIOR = B / 'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D

def read(path): return json.loads(Path(path).read_bytes())

# This binds a completed real tail call, not a future Root witness.
tail_host = s.capture('eeca9f', 0, 0)
refs = [s.pin(path) for path in sorted(D.iterdir()) if path.is_file()]
refs += [s.pin(HELPER), s.pin(N/'HDF.json'), s.pin(PRIOR/'HDF.json'), s.pin(PRIOR/'decision.json')]
g = s.guard(); failure = None
try:
    g.acquire(refs)
    def held(path): return json.loads(g.get_buffer(str(path)))
    prefix = held(D/'independent-delta-result.json')
    tail = held(D/'independent-tail-result.json')
    origin = held(D/'original-review-failure.origin.json')
    source = held(N/'HDF.json')
    old_hdf = held(PRIOR/'HDF.json'); old_decision = held(PRIOR/'decision.json')
    for result in (prefix, tail):
        assert result['count'] == len(result['checks']) == result['passed']
        assert all(item['passed'] is True for item in result['checks'])
        closed = held(Path(result['source_guard_ref']['path']))
        assert closed['closed'] is True and closed['retained_handles_count'] == 0 and closed['errors'] == []
    assert prefix['failure']['type'] == 'NameError'
    assert prefix['failure']['message'] == "name 'BoundaryError' is not defined"
    assert tail['failure'] is None and tail['original_ordinal'] == 1206
    assert origin['original_ordinal'] == 1206 and origin['product_failure'] is False
    assert origin['original_io'] == tail['original_review_failure']
    assert source['source_author'] == 'codex:/root/attach_restore_independent_review'
    assert source['runtime_resources_ref'] == old_decision['runtime_resources_ref']
    assert old_decision['runtime_closure_reviewed'] is True
    total = prefix['count'] + tail['count']
    assert total == 26
finally:
    seal_guard_ref = s.write('seal-source-guard.closed.json', g.close())

now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
bindings = dict(source_hdf_ref=next(ref for ref in refs if ref['path'] == str(N/'HDF.json')),
    source_mf_ref=source['manifest_ref'],
    **{key:source[key] for key in ('caller_ref','source_inputs_ref','calling_contract_ref',
        'runtime_resources_ref','main23_bound_ref','existing22_decision_ref')})
guard_evidence = []
for path in (D/'source-guard.closed.json', D/'tail-source-guard.closed.json', D/'seal-source-guard.closed.json'):
    closed = read(path)
    assert closed['closed'] is True and closed['retained_handles_count'] == 0 and closed['errors'] == []
    guard_evidence.append(dict(ref=s.pin(path), held_count=len(closed['entries']), closed=True, retained_handles_count=0))
runtime_boundary = dict(old_decision['runtime_review_boundary'])
runtime_boundary['Caller_exact_entry_ref_included'] = bindings['caller_ref']
runtime_boundary['Source03_entry_binding'] = 'New exact Source03 Caller held in delta Guard; other function AST/imports and external resource manifest unchanged.'
runtime_boundary['prior_runtime_checks_replayed'] = False
runtime_boundary['future_Root_runtime_qualification_issued'] = False
runtime_boundary['future_Root_must_reobserve_current_exact_runtime_before_guard_and_execution'] = True
reused = dict(Source02_review_hdf_ref=s.pin(PRIOR/'HDF.json'),
    Source02_review_decision_ref=s.pin(PRIOR/'decision.json'),
    Source02_independent_delta_checks=old_decision['new_independent_checks'],
    runtime_manifest_resources=149, runtime_actual_public_required=144,
    prior_Source_controls=14, author_close_controls=3, author_Source03_delta_controls=12,
    author_Source03_delta_controls_ref=source['source_controls_ref'],
    protected_Source02_files=15, rerun=False)
new_failure = dict(origin)
new_failure['status'] = 'FAILED_RETAINED_REVIEWER_INSTRUMENTATION_ONLY'
new_failure['actual_RootStage_exit'] = None
decision = dict(schema='researchos.public22-continuation-root-independent-source-decision.v1',
    decision='ACCEPTED_SOURCE_ONLY', actor_id='codex:/root/full_w09_source_review',
    actor_role='INDEPENDENT_NON_AUTHOR', backend_actor_id='/root/full_w09_source_review',
    reviewer_thread_id=s.THREAD, Root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    source_author=source['source_author'], reviewed_utc=now, **bindings,
    execution_grant=False, formal_acceptance=False, parent_acceptance=False, formal_case_accepted_delta=0,
    original1025_result='FAILED_RETAINED', original1201_result='FAILED_RETAINED', continuation_only=True,
    runtime_closure_reviewed=True,
    runtime_closure_evidence_ref=tail['observations']['runtime_closure_evidence_ref'],
    runtime_review_boundary=runtime_boundary,
    retained_prefix_evidence_ref=s.pin(D/'independent-delta-result.json'),
    tail_evidence_ref=s.pin(D/'independent-tail-result.json'),
    independent_delta_evidence_ref=s.pin(D/'source-delta-evidence.json'),
    prior_accepted_Source02_decision_ref=s.pin(PRIOR/'decision.json'),
    actual_Source_author_audit_ref=tail['observations']['actual_source_author_audit_ref'],
    revision_inverse_ref=source['revision_inverse_ref'], working22_probe_ref=source['working22_difference_probe_ref'],
    closed_finding=dict(id='P22C-WORKING22-SCHEMA-PROJECTION-001',status='RESOLVED_SOURCE_ONLY',
        evidence='All 83 tables and binary identity remain bound. Ledger1..22, retained legacy schema projection and complete Native schema digest are simultaneously required. Working22 observation is retained before the compatibility check can fail.'),
    findings=[], new_independent_checks=total, successful_retained_prefix=prefix['count'],
    newly_completed_tail=tail['count'], reused=reused,
    original_source_failure_ordinals_preserved=[1170,1171,1174,1175,1201,1205],
    original1201_preserved_ref=source['original1201_preserved_ref'],
    original1205_preserved_ref=source['original1205_preserved_ref'],
    new_review_failures=[new_failure], actual_source_tool_pairs=[origin['original_io'],tail_host],
    all_acquired_source_guards_closed=True, retained_handles_count=0, guard_evidence=guard_evidence,
    product_calls=dict(Native=0,Go=0,SQL=0,TP=0,RootStage=0,model=0),
    future_Root_requirements=[
        'Capture this actual independent Final with exact backend identity, original offsets and complete three review refs; no precreated witness.',
        'Issue a fresh finite owner/worker/lease and continuation Scope bound to Source03 and actual current4, then register through the unchanged TP/CAS gate. The consumed original1201 Scope is unusable.',
        'Reobserve the actual Source03 Caller __main__ runtime and exact pinned resources before registration/execution; this review issues no future Root runtime qualification.',
        'Execute only upgrade22to23, backup23 and verify23 in an unused output root; retain complete real hostpairs and closed artifacts for subsequent independent component review.'
    ],
    remaining_OPEN=['actual Source03 three-phase continuation','new independent negative public child','schema23to24','original-data cutover','full20to24'],
    STOP=True)
decision_ref = s.write('decision.json', decision)
members = [s.pin(path) for path in sorted(D.iterdir()) if path.is_file() and path.name not in ('HDF.json','MF.json')]
assert decision_ref in members
manifest_ref = s.write('MF.json', dict(schema='researchos.public22-continuation-independent-source-MF.v1', members=members))
hdf = dict(schema='researchos.public22-continuation-independent-source-HDF.v1',
    actor_id=decision['actor_id'], actor_role=decision['actor_role'], backend_actor_id=decision['backend_actor_id'],
    source_author=source['source_author'], reviewed_utc=now, status='ACCEPTED_SOURCE_ONLY',
    source_decision_ref=decision_ref, manifest_ref=manifest_ref, **bindings,
    runtime_closure_reviewed=True, runtime_closure_evidence_ref=decision['runtime_closure_evidence_ref'],
    new_independent_checks=total, successful_retained_prefix=prefix['count'], newly_completed_tail=tail['count'],
    reused=reused, original1025_result='FAILED_RETAINED', original1201_result='FAILED_RETAINED',
    original_source_failure_ordinals_preserved=decision['original_source_failure_ordinals_preserved'],
    new_review_failures=[new_failure], actual_source_tool_pairs=decision['actual_source_tool_pairs'],
    all_acquired_source_guards_closed=True, retained_handles_count=0, guard_evidence=guard_evidence,
    execution_grant=False, formal_acceptance=False, parent_acceptance=False, formal_case_accepted_delta=0,
    future_Root_runtime_qualification_issued=False, STOP=True)
hdf_ref = s.write('HDF.json', hdf)
print(json.dumps(dict(schema='researchos.public22-continuation-source-review-delivery.v1',operation='SOURCE_REVIEW_WITNESS',
    review_author=decision['actor_id'],backend_actor_id=decision['backend_actor_id'],
    root_thread_id=decision['Root_thread_id'],source_author=source['source_author'],verdict='ACCEPTED_SOURCE_ONLY',
    review_refs=[hdf_ref,manifest_ref,decision_ref],new_independent_checks=total,
    source_hdf_ref=bindings['source_hdf_ref'], runtime_closure_reviewed=True,
    retained_handles_count=0,original1206=origin['original_io'],
    execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True),ensure_ascii=False))
