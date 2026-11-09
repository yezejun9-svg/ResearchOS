"""Seal own source-mapping metadata only; no candidate import or target execution."""
import hashlib
import json
from pathlib import Path

OWN = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_contract_mapping_codex/172e0c45ad4a4b25b19e1da1822804f2')
ACTOR = 'codex:/root/f08_whole_scope_review'

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    target = OWN/name
    with target.open('xb') as output:
        output.write(encoded(value))
    return pin(target)

freeze = json.loads((OWN/'input-pins.after.json').read_bytes())
before_paths = {row['before_ref']['path'].replace('\\','/').casefold() for row in freeze['after']}
late_unique = []
duplicate_reverification = []
for row in freeze['late_metadata_pins']:
    key = row['actual_late_ref']['path'].replace('\\','/').casefold()
    if key in before_paths:
        duplicate_reverification.append(row)
    else:
        late_unique.append(row)
classification_ref = save('input-freeze-classification.json', {
    'schema': 'researchos.driver18-mapping-unique-input-freeze.v1',
    'previously_pinned_unique_files': len(before_paths),
    'previously_pinned_drift': freeze['drift'],
    'additional_late_pinned_files': late_unique,
    'already_pinned_duplicate_reverification': duplicate_reverification,
    'correction_ref': pin(OWN/'pin-classification-correction.json'),
    'original_freeze_ref': pin(OWN/'input-pins.after.json'),
    'original_successful_tool_result_preserved': True,
    'canonical_live_reads': 0,
    'target_calls': 0,
})
mapping = json.loads((OWN/'contract-map.json').read_bytes())
mapping_ref = pin(OWN/'contract-map.json')
read_io = json.loads((OWN/'readonly-commands-and-results.json').read_bytes())
freeze_io = json.loads((OWN/'freeze-io-record.json').read_bytes())
failed = [row for row in read_io['actions'] if row['actual_outer_exit'] not in (None,0)]
if freeze_io['actual_outer_exit'] not in (None,0):
    failed.append(freeze_io)
ready = not freeze['drift'] and all(row['prior_parsed_document_equal'] for row in late_unique) and not failed
hdf = save('handoff.json', {
    'schema': 'researchos.driver18-root-producer-contract-mapping-handoff.v1',
    'actor': ACTOR,
    'non_author': True,
    'writer': 'STOPPED',
    'status': 'SEALED_METADATA_ONLY',
    'decision': 'MAPPING_READY_ACTUAL_PRODUCTION_OPEN' if ready else 'REQUEST_CHANGES_LISTED_INPUT_DRIFT_OR_IO_FAILURE',
    'contract_map_ref': mapping_ref,
    'readable_map_ref': pin(OWN/'contract-map.md'),
    'consumer_refs': mapping['consumer_refs'],
    'actual_cli_pipeline_ref': mapping['actual_cli_pipeline_ref'],
    'prior_independent_source_review_ref': mapping['prior_independent_review_ref'],
    'input_freeze_ref': classification_ref,
    'original_read_command_and_result_ref': pin(OWN/'readonly-commands-and-results.json'),
    'original_freeze_command_and_result_ref': pin(OWN/'freeze-io-record.json'),
    'pin_classification_correction_ref': pin(OWN/'pin-classification-correction.json'),
    'failure_origins_ref': pin(OWN/'failure-origins.json'),
    'new_failure_origins': [],
    'new_origin_count': 0,
    'listed_previously_pinned_files': len(before_paths),
    'listed_input_drift_count': len(freeze['drift']),
    'additional_late_pinned_files': len(late_unique),
    'earlier_duplicate_reverification': len(duplicate_reverification),
    'additional_late_semantic_equality': [row['prior_parsed_document_equal'] for row in late_unique],
    'original_metadata_read_io_calls': len(read_io['actions']),
    'additional_metadata_freeze_io_calls': 1,
    'final_seal_result': 'Returned by original external tool result; not substituted into target-native authority evidence.',
    'gates': {row['id']: row['status'] for row in mapping['gates']},
    'minimum_implementation_groups': ['G1 finite resources and explicit phase inputs', 'G2 current draft register/wrapper/sealer', 'G3 actual source guard and phase grant', 'G4 prospective tool input-response capture and complete prepare sealer', 'G5 separate execute registration/grant and independent native qualification'],
    'caps_unchanged': mapping['caps'],
    'I17': 'OPEN_NOT_AUTHORIZED',
    'full18': 'NOT_QUALIFIED',
    'SQL24_adoption': False,
    'full_callbacks': 'OPEN',
    'formal_increment': 0,
    'source_acceptance': False,
    'actual_new_scope_or_tuple_or_lease': False,
    'actual_registration': False,
    'actual_grant': False,
    'canonical_live_reads': 0,
    'canonical_writes': 0,
    'Git_Go_SQL_helper_driver_HTTP_Node_SDK_model_target_calls': 0,
    'manifest_path': str(OWN/'manifest.json'),
    'manifest_self_excluded': True,
    'original_public_sources_and_old_receipts_untouched': True,
})
members = [pin(path) for path in sorted(OWN.iterdir()) if path.is_file() and path.name != 'manifest.json']
manifest_ref = save('manifest.json', {
    'schema': 'researchos.driver18-root-producer-contract-mapping-manifest.v1',
    'actor': ACTOR, 'members': members, 'member_count': len(members), 'excluded_only_self': True,
})
for row in members:
    actual = pin(Path(row['path']))
    if actual != row:
        raise RuntimeError('owned metadata drift after manifest')
print(json.dumps({
    'writer': 'STOPPED', 'decision': 'MAPPING_READY_ACTUAL_PRODUCTION_OPEN' if ready else 'REQUEST_CHANGES',
    'handoff_ref': hdf, 'manifest_ref': manifest_ref, 'manifest_members': len(members),
    'contract_map_ref': mapping_ref, 'readable_map_ref': pin(OWN/'contract-map.md'),
    'input_freeze_ref': classification_ref, 'failure_origins_ref': pin(OWN/'failure-origins.json'),
    'input_drift': len(freeze['drift']), 'previously_pinned_unique_files': len(before_paths),
    'additional_late_metadata_files': len(late_unique), 'duplicate_reverification': len(duplicate_reverification),
    'new_origin_count': 0, 'target_calls': 0, 'canonical_writes': 0
}, ensure_ascii=False))
