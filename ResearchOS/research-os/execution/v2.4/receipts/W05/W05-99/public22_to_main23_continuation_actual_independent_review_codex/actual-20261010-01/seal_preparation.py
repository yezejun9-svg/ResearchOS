"""Seal the future component-review input map, not an actual result or authority."""
from pathlib import Path
from datetime import datetime, timezone
import json, types

R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
B = R / 'execution/v2.4/receipts/W05/W05-99'
D = Path(__file__).resolve().parent
REVIEW = B / 'public22_to_main23_continuation_independent_review_codex/review-20261010-02-full'
HELPER = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('receipt_support'); s.__file__ = str(HELPER)
exec(compile(HELPER.read_bytes(), str(HELPER), 'exec'), s.__dict__); s.D = D
def read(path): return json.loads(Path(path).read_bytes())
result = read(D / 'preparation-result.json'); refs = result['refs']
assert result['status'] == 'PREPARED_PENDING_ACTUAL' and result['failure'] is None
closed = read(refs['guard_ref']['path'])
assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
hostpair = s.capture('bfd534', 0, 0)
s.write('actual-preparation-hostpair.json', hostpair)
review = read(REVIEW / 'HDF.json')
now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
decision = s.write('preparation-decision.json', dict(
    schema='researchos.public22-continuation-component-review-preparation-decision.v1',
    actor_id='codex:/root/full_w09_source_review', backend_actor_id='/root/full_w09_source_review',
    actor_role='INDEPENDENT_NON_AUTHOR', Source_author='codex:/root/attach_restore_independent_review',
    status='PREPARED_PENDING_ACTUAL', prepared_utc=now, input_contract_ref=refs['input_contract_ref'],
    source_interface_evidence_ref=refs['source_evidence_ref'], input_refs_ref=refs['input_refs_ref'],
    source_guard_ref=refs['guard_ref'], actual_preparation_hostpair=hostpair,
    accepted_Source_review_refs=[s.pin(REVIEW / 'HDF.json'), review['manifest_ref'], review['source_decision_ref']],
    future_actual_bundle=None, future_actual_verdict=None, actual_component_review_performed=False,
    actual_component_accepted=False, actual_children=0, no_new_product_requirements=True,
    prior_Source_resource_checks_reused_without_rerun=True,
    original1025_result='FAILED_RETAINED', original_four_children_replayed=False,
    automatic_retry=False, full20to24='OPEN',
    formal_acceptance=False, parent_acceptance=False, execution_grant=False,
    formal_case_accepted_delta=0, Main_Canon_Scope_written=False,
    actual_product_exits=dict(Native=None, Go=None, SQL=None, TP=None, dispatcher=None, model=None), STOP=True))
g = s.guard(); held = [s.pin(path) for path in sorted(D.iterdir(), key=lambda p:p.name) if path.is_file()]
try:
    g.acquire(held)
finally:
    seal_guard = s.write('seal-preparation-guard.closed.json', g.close())
closed = read(seal_guard['path'])
assert closed['closed'] and closed['retained_handles_count'] == 0 and closed['errors'] == []
mf = s.write('MF.json', dict(schema='researchos.public22-continuation-review-preparation-manifest.v1',
    members=[s.pin(path) for path in sorted(D.iterdir(), key=lambda p:p.name) if path.is_file()],
    exclusions=['HDF.json','MF.json','postseal-tool-io.json']))
hdf = s.write('HDF.json', dict(schema='researchos.public22-continuation-actual-review-preparation-handoff.v1',
    actor_id='codex:/root/full_w09_source_review', backend_actor_id='/root/full_w09_source_review',
    actor_thread_id=s.THREAD, root_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',
    status='PREPARED_PENDING_ACTUAL', prepared_utc=now, decision_ref=decision, manifest_ref=mf,
    input_contract_ref=refs['input_contract_ref'], source_interface_evidence_ref=refs['source_evidence_ref'],
    source_guard_ref=refs['guard_ref'], seal_guard_ref=seal_guard, actual_preparation_hostpair=hostpair,
    accepted_Source_HDF_ref=review['source_hdf_ref'], accepted_Source_MF_ref=review['source_mf_ref'],
    accepted_Source_review_refs=[s.pin(REVIEW / 'HDF.json'), review['manifest_ref'], review['source_decision_ref']],
    reused_existing22_decision_ref=review['existing22_decision_ref'],
    reused_Main23_bound_ref=review['main23_bound_ref'], reused_runtime_resources_ref=review['runtime_resources_ref'],
    prior_144_149_resource_checks_rerun=False, prior_Source_controls_rerun=False,
    future_actual_bundle=None, actual_component_review_performed=False, actual_component_accepted=False,
    actual_children=0, new_review_failures=[], all_guards_closed_zero=True, retained_handles_count=0,
    live_Canon_handles_held=0, current_Native_outputs_read=False, private_material_read_or_hashed=False,
    original1025_result='FAILED_RETAINED', old_four_children_replayed=False,
    full20to24='OPEN', execution_grant=False, formal_acceptance=False, parent_acceptance=False,
    formal_case_accepted_delta=0, actual_Root_stages=0, actual_Native_Go_SQL_TP_model_calls=0,
    Main_Canon_Scope_written=False, STOP=True))
print(json.dumps(dict(schema='researchos.public22-continuation-actual-review-preparation-delivery.v1',
    operation='PREPARED_PENDING_ACTUAL', reviewer='codex:/root/full_w09_source_review',
    backend_actor='/root/full_w09_source_review', preparation_refs=[hdf,mf,decision],
    input_contract_ref=refs['input_contract_ref'],
    actual_preparation_hostpair=hostpair, guards=[refs['guard_ref'],seal_guard],
    all_guards_closed_zero=True, retained_handles_count=0, actual_children=0,
    actual_component_accepted=False, future_actual_bundle=None, new_failures=[],
    execution_grant=False, formal_acceptance=False, parent_acceptance=False,
    original1025_result='FAILED_RETAINED', full20to24='OPEN', STOP=True), ensure_ascii=False))
