"""Seal independent v4 review metadata only; candidate code is never imported or executed."""
import hashlib
import json
from pathlib import Path

OWN = Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v4_independent_review_codex/188de814eb44453ba0c192ccec7cb2ea')

def doc(path):
    return json.loads(path.read_bytes())

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (OWN / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

before = doc(OWN / 'input-pins.before.json')
checks = []
for expected in before['refs']:
    actual = pin(Path(expected['path']))
    checks.append({'expected': expected, 'actual': actual,
                   'sha_bytes_equal': actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']})
drift = sum(not row['sha_bytes_equal'] for row in checks)
if drift:
    raise RuntimeError('Frozen input SHA/bytes changed: ' + str(drift))
save('input-pins.after.json', {
    'schema': 'researchos.driver18-v4-independent-review-pins.after.v1',
    'checks': checks, 'unique_count': len(checks), 'sha_bytes_drift': drift,
    'candidate_imported_or_executed': False
})
review = doc(OWN / 'review.json')
handoff = {
    'schema': 'researchos.independent-driver18-v4-narrow-review-handoff.v1',
    'reviewer': 'codex:/root/f08_whole_scope_review', 'non_author': True,
    'status': 'STOPPED', 'decision': 'READY_SOURCE_PREPARATION_ONLY',
    'finding': 'R01-V3-FRESH_PARENT', 'finding_state': 'CLOSED_SOURCE_ONLY',
    'critical_count': 0, 'important_count': 0,
    'review_ref': pin(OWN / 'review.json'),
    'readable_review_ref': pin(OWN / 'REVIEW.md'),
    'source_ref': review['source_ref'],
    'author_handoff_ref': review['author_handoff_ref'],
    'author_manifest_ref': review['author_manifest_ref'],
    'prior_REQUEST_ref': review['prior_REQUEST_ref'], 'prior_REQUEST_unchanged': True,
    'AST_inverse_ref': pin(OWN / 'AST-inverse.original.json'),
    'path_control_analysis_ref': pin(OWN / 'path-analysis.NOT_RUN.json'),
    'original_tool_IO_ref': pin(OWN / 'readonly-IO.original.json'),
    'input_pins_before_ref': pin(OWN / 'input-pins.before.json'),
    'input_pins_after_ref': pin(OWN / 'input-pins.after.json'),
    'failure_origins_index_ref': pin(OWN / 'failure-origins.json'),
    'stopped_locator_original_failure_refs': [
        pin(OWN / 'failure-origin.516943.json'), pin(OWN / 'failure-origin.04c0fb.json')
    ],
    'stopped_locator_failure_occurrences': 2,
    'stopped_locator_outer_native_exits': {'516943': [2, 2], '04c0fb': [2, 2]},
    'stopped_locator_failure_count_semantics': 'Already reported to Root as two underlying occurrences; refs only preserve them, not another increment. No failed input rerun.',
    'v4_review_new_failure_origins': [],
    'unique_frozen_refs': len(checks), 'sha_bytes_drift': drift,
    'whole_inverse_raw_bytes_equal': True, 'inverse_hunks': 2,
    'unchanged_function_ASTs': 40, 'changed_functions': ['preallocate', 'entry'],
    'total_functions': 42, 'source_lines': 523, 'original_inputs': 9,
    'input_before_after_bytes_equal': True, 'all_four_controls': 'NOT_RUN',
    'build_verified': False, 'candidate_imported_or_executed': False,
    'all_candidate_native_Job_Go_SQL_Git_network_model_CAS_calls': 0,
    'canonical_reads_or_writes': 0, 'author_or_old_namespace_writes': 0,
    'actual_A01_A07': 'OPEN', 'actual_Root_tuple_catalog_review_capture_prepared': 'OPEN',
    'actual_registration': False, 'actual_grant': False, 'actual_driver_execution': False,
    'I17': 'OPEN', 'full18': 'OPEN', 'callbacks': 'OPEN', 'SQL24': 'OPEN',
    'source_acceptance': False, 'formal_increment': 0, 'old_failure_counters_untouched': True,
    'Root_future_tuple_or_failure_count': None,
    'seal_actual_exit_evidence': 'External original exec_command response; deliver actual status to Root after seal and do not append to this closed namespace.',
    'next_step': 'Root independently produces real catalog/scope/draft review/CAS/grant/capture/prepare facts in a new authorized scope; source-only review supplies no authority.'
}
save('handoff.json', handoff)
members = [pin(p) for p in sorted(OWN.iterdir(), key=lambda p: p.name) if p.is_file() and p.name != 'manifest.json']
save('manifest.json', {
    'schema': 'researchos.immutable-independent-driver18-v4-review-manifest.v1',
    'files': members, 'member_count': len(members), 'excluded_only_self': True,
    'status': 'STOPPED', 'decision': 'READY_SOURCE_PREPARATION_ONLY'
})
for expected in members:
    actual = pin(Path(expected['path']))
    if (actual['sha256'], actual['bytes']) != (expected['sha256'], expected['bytes']):
        raise RuntimeError('Own immutable manifest mismatch: ' + expected['path'])
print(json.dumps({
    'status': 'STOPPED', 'decision': 'READY_SOURCE_PREPARATION_ONLY',
    'finding': 'R01-V3-FRESH_PARENT', 'finding_state': 'CLOSED_SOURCE_ONLY',
    'unique_frozen_refs': len(checks), 'sha_bytes_drift': drift,
    'whole_inverse_hunks': 2, 'unchanged_function_ASTs': 40,
    'manifest_members': len(members), 'v4_review_new_failure_origins': [],
    'earlier_locator_origins_preserved_once': ['516943', '04c0fb'],
    'refs': {name: pin(OWN / name) for name in (
        'review.json', 'REVIEW.md', 'handoff.json', 'manifest.json',
        'failure-origin.516943.json', 'failure-origin.04c0fb.json',
        'failure-origins.json', 'input-pins.after.json', 'readonly-IO.original.json'
    )}
}, ensure_ascii=False))

