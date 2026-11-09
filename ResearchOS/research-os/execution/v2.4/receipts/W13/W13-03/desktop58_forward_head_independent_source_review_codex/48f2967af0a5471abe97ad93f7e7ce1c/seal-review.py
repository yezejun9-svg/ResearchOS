"""Seal only independent old-template review metadata. Do not import/execute engine or builder."""
import hashlib
import json
from pathlib import Path

OWN = Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_forward_head_independent_source_review_codex/48f2967af0a5471abe97ad93f7e7ce1c')
AUTHOR_MANIFEST = json.loads("{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W13\\\\W13-03\\\\desktop58_forward_head_metadata_preparation_codex\\\\503ef47ea65144029c73a4d7bf19409a\\\\manifest.json\",\"sha256\":\"150f52178b664ae3e019b5c28dab445c0827ea9c6be84bd5b70204212f3e4240\",\"bytes\":9897}")
AUTHOR_HANDOFF = json.loads("{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W13\\\\W13-03\\\\desktop58_forward_head_metadata_preparation_codex\\\\503ef47ea65144029c73a4d7bf19409a\\\\handoff.json\",\"sha256\":\"66ed76d859c4e92668cc0d222b5ae378eb4ef279ae9d90ddf955f020b4cac006\",\"bytes\":3772}")
RUNTIME_CATALOG = json.loads("{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W13\\\\W13-03\\\\desktop15_root_parameters_codex\\\\8792799f829a23452ae5d89a59e1b0cf\\\\runtime.with-locked-git.json\",\"sha256\":\"c75ee385bdca56de3582f78695af8fc1b31fb67da0ecffa22cd1e4b4aca4b9b5\",\"bytes\":282833}")
CUT = json.loads("{\"path\":\"D:\\\\作品集\\\\ResearchOS\\\\research-os\\\\execution\\\\v2.4\\\\receipts\\\\W13\\\\W13-03\\\\desktop58_forward_head_root_parameters_codex\\\\6cd1a3bb23fb45e1bcb26091d2b0a031\\\\origin-cut.actual.json\",\"sha256\":\"47dae6378442ce7ddab9ba1849c5e85b4514c20091621fdf30b5ae18cda54904\",\"bytes\":52221}")

def doc(p):
    return json.loads(p.read_bytes())

def pin(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def save(name, value):
    with (OWN / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

ns = Path(AUTHOR_MANIFEST['path']).parent
declared = doc(Path(AUTHOR_MANIFEST['path']))['entries']
old_inputs = doc(ns / 'inputs.final-before.json')['files']
refs = [*declared, *old_inputs, AUTHOR_MANIFEST, CUT, RUNTIME_CATALOG]
unique = {}
for r in refs:
    key = str(Path(r['path']).resolve()).casefold()
    if key in unique and (unique[key]['sha256'], unique[key]['bytes']) != (r['sha256'], r['bytes']):
        raise RuntimeError('Conflicting declared immutable pin')
    unique[key] = r
checks = []
for expected in unique.values():
    actual = pin(Path(expected['path']))
    checks.append({'expected': expected, 'actual': actual,
                   'sha_bytes_equal': (actual['sha256'], actual['bytes']) == (expected['sha256'], expected['bytes'])})
drift = sum(not x['sha_bytes_equal'] for x in checks)
if drift:
    raise RuntimeError('Frozen input drift: ' + str(drift))
save('input-pins.before.json', {
    'schema': 'researchos.desktop58-independent-old-template-review-pins.v1',
    'refs': list(unique.values()), 'unique_count': len(unique),
    'initial_source_IO_checks': '30 declared members and12 original inputs were independently hashed earlier with zero SHA/bytes drift; detailed tool response preserved.',
    'comparison': 'SHA256 and bytes; path representation alone is not byte drift'
})
save('input-pins.after.json', {
    'schema': 'researchos.desktop58-independent-old-template-review-pins.after.v1',
    'checks': checks, 'unique_count': len(checks), 'sha_bytes_drift': drift
})
runtime = doc(Path(RUNTIME_CATALOG['path']))
runtime_facts = {'catalog_ref': RUNTIME_CATALOG, 'type': type(runtime).__name__,
                 'keys': list(runtime) if isinstance(runtime, dict) else None,
                 'files_count': len(runtime['files']) if isinstance(runtime, dict) and isinstance(runtime.get('files'), list) else None}
review = doc(OWN / 'review.json')
handoff = {
    'schema': 'researchos.desktop58-forward-head-independent-source-review-handoff.v1',
    'reviewer': 'codex:/root/f08_whole_scope_review', 'non_author': True,
    'status': 'STOPPED', 'decision': 'REQUEST_CHANGES',
    'critical_count': 1, 'important_count': 1,
    'critical_id': 'DFH-R01-MODE-ANCHOR', 'important_id': 'DFH-R02-RUNTIME-SCOPE-BINDING',
    'review_ref': pin(OWN / 'review.json'),
    'readable_review_ref': pin(OWN / 'REVIEW.md'),
    'composition_ref': pin(OWN / 'composition.NOT_RUN.json'),
    'inverse_and_anchor_ref': pin(OWN / 'source-inverse-and-anchor-facts.json'),
    'original_IO_ref': pin(OWN / 'readonly-IO.original.json'),
    'original_failure_origin_ref': pin(OWN / 'failure-origin.v8-af2be6.json'),
    'failure_origins_index_ref': pin(OWN / 'failure-origins.json'),
    'input_pins_before_ref': pin(OWN / 'input-pins.before.json'),
    'input_pins_after_ref': pin(OWN / 'input-pins.after.json'),
    'source_ref': review['source_ref'], 'builder_ref': review['builder_ref'],
    'author_handoff_ref': AUTHOR_HANDOFF, 'author_manifest_ref': AUTHOR_MANIFEST,
    'base_engine_ref': review['base_engine_ref'],
    'runtime_catalog_actual_facts': runtime_facts,
    'all_frozen_unique_inputs': len(checks), 'sha_bytes_drift': drift,
    'source_lines': 662, 'engine_functions': 27, 'builder_lines': 25,
    'whole_inverse_hunks': 29, 'whole_inverse_bytes_equal': True,
    'unchanged_existing_functions': 14,
    'mode_anchor_count_in_actual_source': 4,
    'mode_anchor_whole_line_count_in_actual_source': 1,
    'all_future_runtime_controls': 'NOT_RUN', 'build_verified': False,
    'actual_final_Root_request_ref': None, 'actual_draft_generated': False,
    'actual_metadata_registration': False, 'actual_lease_closed': False,
    'actual_Root_grant': False, 'source_acceptance': False,
    'fresh58_GUI_NVDA_SQL24_formal': 'OPEN', 'formal_increment': 0,
    'all_candidate_import_execution_native_Job_Git_Go_SQL_network_model_CAS_calls': 0,
    'canonical_reads_or_writes': 0, 'author_or_old_namespace_writes': 0,
    'frozen_cut_ref': CUT, 'frozen_cut_before': [332, 160, 516],
    'frozen_cut_after': [333, 161, 524], 'frozen_cut_origins': 8,
    'frozen_cut_unchanged': True,
    'new_failure_origin_occurrences': 1,
    'V8_orchestration_outer_native_exits': [None, None],
    'underlying_af2be6_outer_native_exits': [0, 0],
    'underlying_af2be6_not_another_origin': True,
    'author09b17d_already_fixed_cut_not_recounted': True,
    'old_failure_counters_untouched': True,
    'Root_future_count_or_request_inferred': False,
    'seal_original_tool_result': 'External actual exec_command response; deliver after seal without appending to immutable review.',
    'next_step': 'Author seals minimal revision for same physical-line mode anchors and historical scope runtime REF binding, referencing this immutable REQUEST. Root final immutable request composition remains separate and does not run targets in review.'
}
save('handoff.json', handoff)
entries = [pin(p) for p in sorted(OWN.iterdir(), key=lambda p: p.name) if p.is_file() and p.name != 'manifest.json']
save('manifest.json', {
    'schema': 'researchos.immutable-independent-desktop58-forward-head-source-review.v1',
    'count': len(entries), 'entries': entries, 'self_excluded': True,
    'status': 'STOPPED', 'decision': 'REQUEST_CHANGES'
})
for r in entries:
    actual = pin(Path(r['path']))
    if (actual['sha256'], actual['bytes']) != (r['sha256'], r['bytes']):
        raise RuntimeError('Own manifest drift')
print(json.dumps({
    'status': 'STOPPED', 'decision': 'REQUEST_CHANGES',
    'critical': 1, 'important': 1, 'unique_frozen_inputs': len(checks),
    'sha_bytes_drift': drift, 'manifest_members': len(entries),
    'new_failure_origins': 1, 'runtime_facts': runtime_facts,
    'refs': {name: pin(OWN / name) for name in (
        'review.json', 'handoff.json', 'manifest.json', 'REVIEW.md',
        'failure-origin.v8-af2be6.json', 'input-pins.after.json'
    )}
}, ensure_ascii=False))

