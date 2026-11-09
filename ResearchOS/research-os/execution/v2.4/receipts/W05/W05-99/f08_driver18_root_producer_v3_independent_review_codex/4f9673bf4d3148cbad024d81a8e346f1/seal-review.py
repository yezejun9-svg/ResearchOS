"""Seal only this independent review's metadata; do not import or run candidate code."""
import hashlib
import json
from pathlib import Path

OWN = Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1')
INVENTORY = json.loads("{\"input\":{\"cmd\":\"rg --files 'execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1'\\nexit $LASTEXITCODE\",\"workdir\":\"D:/作品集/ResearchOS/research-os\",\"max_output_tokens\":1800},\"result\":{\"chunk_id\":\"f8ee6b\",\"wall_time_seconds\":0.6247731,\"exit_code\":0,\"original_token_count\":291,\"output\":\"execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\source-path-analysis.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\REVIEW.md\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\review.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\readonly-IO.original.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\input-pins.before.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\failure-origins.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\counterexamples.NOT_RUN.json\\nexecution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_v3_independent_review_codex/4f9673bf4d3148cbad024d81a8e346f1\\\\byte-AST-inverse.original.json\\n\"}}")

def read_json(path):
    return json.loads(path.read_bytes())

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def write_json(name, value):
    (OWN / name).write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

before = read_json(OWN / 'input-pins.before.json')
checks = []
for expected in before['refs']:
    actual = pin(Path(expected['path']))
    checks.append({'expected': expected, 'actual': actual,
                   'sha_bytes_equal': actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']})
drift = sum(not c['sha_bytes_equal'] for c in checks)
if drift:
    raise RuntimeError('Frozen SHA/bytes changed: ' + str(drift))

review = read_json(OWN / 'review.json')
author = Path(review['source_ref']['path']).parent
inverse_contract = read_json(author / 'whole-inverse.json')
candidate_raw = Path(inverse_contract['candidate_ref']['path']).read_bytes()
base_raw = Path(inverse_contract['base_ref']['path']).read_bytes()
inverse = candidate_raw.decode('utf-8')
hunks = []
for edit in reversed(inverse_contract['edits']):
    count = inverse.count(edit['new'])
    hunks.append({'label': edit['label'], 'new_count': count})
    if count != 1:
        raise RuntimeError('Nonunique inverse hunk: ' + edit['label'])
    inverse = inverse.replace(edit['new'], edit['old'], 1)
inverse_raw = inverse.encode('utf-8')
if inverse_raw != base_raw:
    raise RuntimeError('Whole inverse does not recover original raw bytes')
raw_inverse = {
    'whole_inverse_raw_bytes_equal': True, 'hunks': hunks,
    'inverse_sha256': hashlib.sha256(inverse_raw).hexdigest(),
    'base_sha256': hashlib.sha256(base_raw).hexdigest(),
    'candidate_CRLF_count': candidate_raw.count(b'\r\n'),
    'base_CRLF_count': base_raw.count(b'\r\n'),
    'newline_translation_performed': False,
    'candidate_imported_or_executed': False
}
write_json('input-pins.after.json', {
    'schema': 'researchos.driver18-producer-v3-review-input-pins.after.v1',
    'checks': checks, 'ref_count': len(checks), 'sha_bytes_drift': drift,
    'raw_byte_inverse': raw_inverse, 'comparison': 'SHA256 and bytes; literal path representation is not byte drift'
})

# Correct only an unsealed annotation. Preserve original input/result verbatim.
# The first rg invocation did not explicitly bridge its numeric native exit.
io = read_json(OWN / 'readonly-IO.original.json')
if io['calls'][0]['original_result']['chunk_id'] != '67a400':
    raise RuntimeError('Unexpected original rg evidence')
io['calls'][0]['actual_native_metadata_exit'] = None
io['calls'][0]['native_bridge'] = None
io['calls'][0]['native_exit_note'] = 'Original command has no explicit exit $LASTEXITCODE and result reports only outer exit 0; native numeric exit remains NULL.'
io['calls'].append({
    'tool_name': 'exec_command', 'original_input': INVENTORY['input'],
    'original_result': INVENTORY['result'], 'actual_outer_exit': INVENTORY['result']['exit_code'],
    'actual_native_metadata_exit': INVENTORY['result']['exit_code'],
    'native_bridge': 'explicit exit $LASTEXITCODE'
})
io['annotation_correction_before_seal'] = '67a400: provisional native0 annotation corrected to NULL; raw command/result unchanged, no command retry and no failure origin.'
io['seal_result_location'] = 'External original exec_command response, returned to Root after seal; not fabricated inside this self-excluding manifest.'
write_json('readonly-IO.original.json', io)
handoff = {
    'schema': 'researchos.independent-driver18-producer-v3-source-review-handoff.v1',
    'reviewer': 'codex:/root/f08_whole_scope_review',
    'non_author': True, 'status': 'STOPPED', 'decision': 'REQUEST_CHANGES',
    'critical_count': 0, 'important_count': 1, 'finding_id': 'R01-V3-FRESH_PARENT',
    'review_ref': pin(OWN / 'review.json'),
    'readable_review_ref': pin(OWN / 'REVIEW.md'),
    'source_path_analysis_ref': pin(OWN / 'source-path-analysis.json'),
    'logical_controls_NOT_RUN_ref': pin(OWN / 'counterexamples.NOT_RUN.json'),
    'original_IO_ref': pin(OWN / 'readonly-IO.original.json'),
    'failure_origins_ref': pin(OWN / 'failure-origins.json'),
    'input_pins_before_ref': pin(OWN / 'input-pins.before.json'),
    'input_pins_after_ref': pin(OWN / 'input-pins.after.json'),
    'AST_inverse_original_ref': pin(OWN / 'byte-AST-inverse.original.json'),
    'source_ref': review['source_ref'],
    'author_handoff_ref': review['author_handoff_ref'],
    'author_manifest_ref': review['author_manifest_ref'],
    'prior_REQUEST_ref': review['prior_REQUEST_ref'],
    'prior_REQUEST_unchanged': True,
    'original_three_findings': 'STATIC_CLOSED; earlier REQUEST remains immutable.',
    'remaining_minimum_fix': 'Initial stage-code must require a new empty registration parent before any allocation; bootstrap input and source refs must be outside that parent. Recheck immediately before allocation, without requiring emptiness in later staged actions.',
    'legal_positive_layout_analysis': 'Strict direct sibling layout and staged code/draft/native REF flow can compose; no actual Root path, producer, scope, review, CAS or execution was created.',
    'frozen_ref_count': len(checks), 'sha_bytes_drift': drift,
    'inverse_raw_bytes_equal': True, 'inverse_hunks': len(hunks),
    'unchanged_existing_function_ASTs': 32,
    'build_verified': False, 'candidate_imported_or_executed': False,
    'actual_A01_A07': 'OPEN', 'actual_Root_tuple_catalog_reviews_capture_prepared': 'OPEN',
    'source_acceptance': False, 'actual_registration': False, 'actual_grant': False,
    'actual_driver_execution': False, 'full18': 'OPEN', 'I17': 'OPEN',
    'SQL24': 'OPEN', 'callbacks': 'OPEN', 'formal_increment': 0,
    'candidate_or_helper_target_calls': 0, 'Go_SQL_native_Job_network_model_CAS_Git_calls': 0,
    'canonical_reads_or_writes': 0, 'author_or_other_old_namespace_writes': 0,
    'metadata_read_tools_before_seal': {
        'count': len(io['calls']), 'outer_zero': len(io['calls']),
        'explicit_native_zero': len(io['calls']) - 1, 'native_NULL': 1,
        'original_author_native_facts': 'NULL unchanged'
    },
    'new_failure_origins': [], 'new_Root_unregistered_origins_from_this_review': 0,
    'old_failure_counters_untouched': True,
    'seal_tool_actual_result': 'External original tool response; return exact status and refs to Root, do not append into sealed tree.',
    'next_step': 'Author prepares minimal new immutable candidate; non-author independently checks negative old-parent refusal and positive fresh-parent layout before separate Root actual A01-A07.'
}
write_json('handoff.json', handoff)
members = [pin(p) for p in sorted(OWN.iterdir(), key=lambda p: p.name) if p.is_file() and p.name != 'manifest.json']
write_json('manifest.json', {
    'schema': 'researchos.immutable-independent-driver18-producer-v3-review-manifest.v1',
    'files': members, 'member_count': len(members), 'excluded_only_self': True,
    'status': 'STOPPED', 'decision': 'REQUEST_CHANGES'
})
for expected in members:
    actual = pin(Path(expected['path']))
    if (actual['sha256'], actual['bytes']) != (expected['sha256'], expected['bytes']):
        raise RuntimeError('Own manifest mismatch: ' + expected['path'])
print(json.dumps({
    'status': 'STOPPED', 'decision': 'REQUEST_CHANGES',
    'critical_count': 0, 'important_count': 1,
    'ref_count': len(checks), 'sha_bytes_drift': drift,
    'whole_inverse_raw_bytes_equal': True, 'inverse_hunks': len(hunks),
    'manifest_members': len(members), 'new_failure_origins': [],
    'refs': {name: pin(OWN / name) for name in (
        'review.json', 'REVIEW.md', 'handoff.json', 'manifest.json',
        'failure-origins.json', 'source-path-analysis.json',
        'input-pins.after.json', 'readonly-IO.original.json'
    )}
}, ensure_ascii=False))

