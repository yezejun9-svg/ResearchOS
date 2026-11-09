"""Preserve ten distinct late origins as opaque payloads; no canonical writes."""
import hashlib
import json
from pathlib import Path
import sys

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
BASE = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OUT = Path(__file__).absolute().parent

def pin(p):
    p = Path(p).absolute()
    raw = p.read_bytes()
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def doc(p):
    return json.loads(Path(p).read_bytes())

def verified(p, digest):
    ref = pin(p)
    assert ref['sha256'] == digest
    return ref

specs = [
    ('f08_initial_profile_journal_independent_source_review_codex/c9d3ae02dc1048138094771b6cb809e9/failure-origin.4ddd35.json', 'b6d165636c79256e7895acca1b110d4a312606cc6252a88a7cb99605361bb506', 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO'),
    ('f08_sqlite_complete_fork_resource_codex/29646a104712459fb211fc6f80545bf0/failure-origin.4024a7.json', 'caf96d1a14cfa2a3dd6a4f14cc118e79a8fa47489a472f1a17763a295ebaa457', 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO'),
    ('f08_sqlite_complete_fork_resource_independent_review_codex/dd62b57442844767ac22716ffefe5061/failure-origin.send-message-thread-limit.json', '236f4101c7754acd0144bc417ac9019e449ff33d6fb7da18ac772aaadb915ef8', 'COORDINATION_TOOL_DIAGNOSTIC_NATIVE_OUTER_NULL'),
    ('f08_fence_semantics_revision_preparation_codex/65c17a2368284d90beec9526fba58a44/failure-origin.17042a.json', 'b7195b6022fbbe0b10dd153c6cb60c27bb66517429f2f4b880b3d37da7a5fef5', 'READONLY_TOOL_NONZERO_NATIVE_NULL'),
    ('cli43_root_caller_static_independent_review_codex/e44826e7328e412f9d22ae5dbcb16ceb/failure-origin.3dbc41.json', '1925e818d3443434c2a0204f3df7a1536785d7836646aa056cc8767dd9f5871c', 'READONLY_TOOL_NONZERO_NATIVE_NULL'),
    ('f08_fence_semantics_independent_source_review_codex/9dbd54518abc4d18ba53261413b8cba5/failure-origin.9d9d3e.json', 'd8305e8fe11385e441adab312abf7dcf58a2e9a808740edac0888523a9744715', 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO'),
    ('cli43_fresh_compiler_executor_codex/efa7776ec48e4a7abaa92ce85eb0dace/failure.origin.json', 'a079d11193f27a3d8a4b0909c7865ae43230a4d83044f40e37bd4101bcb7e1e8', 'SINGLE_CASE_CAPTURE_UNKNOWN_MODULE_REQUESTED_TERMINATION_QUALIFICATION_WITHHELD')
]
origins = []
for relative, digest, kind in specs:
    p = BASE / relative
    origins.append({'evidence_ref': verified(p, digest), 'original_payload': doc(p), 'classification': kind,
        'counter_reset': False, 'automatic_same_input_retry': False})
desktop = ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop15_next_scope_reference_mapping_codex/e5b678298b1b435c81d7d7f7f37a798c/failure-origin.0319e9.json'
origins.append({'evidence_ref': verified(desktop, '941aefb17910ddfaee76c04c8985e02897337ca967a730200f564991c4d609a4'),
    'original_payload': doc(desktop), 'classification': 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO',
    'counter_reset': False, 'automatic_same_input_retry': False})
container = BASE / 'f08_sqlite_upstream_zip_resource_codex/8c2f06c01895426ea1e31317664a7748/failure-origins.json'
container_ref = verified(container, '575a1ad39cf8542ad293293a5353ecb3ca560fa84968c8847350a057e8339aed')
resource = doc(container)
assert len(resource['origins']) == 2 and resource['network_or_web_failures'] == 2 and resource['new_native_nonzero_count'] == 0
for index, row in enumerate(resource['origins']):
    ref = row['evidence_ref']
    p = Path(ref['path'])
    actual = pin(p)
    assert actual['sha256'] == ref['sha256'] and actual['bytes'] == ref['bytes']
    assert row['actual_native_exit'] is None
    origins.append({'evidence_ref': actual, 'original_payload': doc(p),
        'original_container_ref': container_ref, 'original_container_payload': resource,
        'original_origin_row': row, 'original_origin_index': index,
        'classification': 'PUBLIC_RESOURCE_NETWORK_OR_WEB_FAILURE_NO_NATIVE_NONZERO_INFERENCE',
        'counter_reset': False, 'automatic_same_input_retry': False})
assert len(origins) == 10 and len({r['evidence_ref']['sha256'] for r in origins}) == 10
closure = doc(OUT / 'root-launch.outer-completion.json')
for row in closure['canonical_refs_at_completion']:
    actual = pin(Path(row['path']))
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
cp = doc(ROOT / 'execution/v2.4/checkpoint.json')
assert cp['revision'] == 327 and len(cp['failure_counters']) == 459
assert all(all(old.get('evidence_ref', {}).get('sha256') != row['evidence_ref']['sha256'] for old in cp['failure_counters']) for row in origins)
for row in origins:
    assert pin(ROOT / row['evidence_ref']['path']) == row['evidence_ref']
payload = {'schema': 'researchos.root-late-origin-cut.v1', 'actor': 'codex:/root',
    'before': [327,155,459], 'after': [328,156,469], 'registered_origin_count': 459,
    'captured_late_origin_count': 10, 'fixed_cut_observed_origin_count': 469,
    'later_peer_origins_not_in_fixed_cut': ['3c0cfb', 'cleanup-auto-review-rejection', '4d42b8'],
    'observed_including_later_pending_at_capture': 472, 'origins': origins,
    'native_NULL_and_original_payloads_preserved': True, 'nested_exit_propagations_counted_once': True,
    'canonical_writes': 0, 'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0}
with (OUT / 'late-origins.capture.for-r328.json').open('xb') as stream:
    stream.write((json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps({'capture_ref': pin(OUT / 'late-origins.capture.for-r328.json'),
    'captured_late_origins': 10, 'canonical_unchanged': True}, ensure_ascii=False))
