"""Capture twelve distinct pending origins while preserving opaque original rows and NULLs."""
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

def save(p, value):
    with Path(p).open('xb') as f:
        f.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

def verified(p, digest):
    ref = pin(p)
    assert ref['sha256'] == digest
    return ref

specs = [
    (BASE / 'f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/failure-origin.3c0cfb.json', '1e4e3c0b62cc772e10e04d70bd1910f082ce780307ecf471deeb76cf0802f6e7', 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO'),
    (BASE / 'f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/failure-origin.4d42b8.json', '599d19509dee1686d5e8158b6355057f55242f34a31d3792c5a431c695ff9667', 'METADATA_ACTUAL_TOOL_PYTHON_NONZERO'),
    (BASE / 'f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/failure-origin.cleanup-rejected.json', '94f39c7e46a2bf0c282c1dbc93bbe948b0e038071ade1318c97f458d276611b1', 'AUTO_REVIEW_TOOL_REJECTION_NO_PROCESS_NATIVE_OUTER_NULL'),
    (OUT / 'failure-origin.exec-textencoder.json', 'c65ca8f2ee2fa47d79d9b2b09e65a10cbd6b8ea9b68e26292b99616964c931ca', 'TOOL_V8_REFERENCE_ERROR_NO_NESTED_PROCESS_NATIVE_OUTER_NULL'),
    (BASE / 'cli43_fresh_compiler_executor_codex/bf943a8137c74df09e010347615b0eec/failure.origin.json', 'd919eebc43a94728711319efd7b08fd251f352ae2890814872736ba51450349c', 'HTTP_RAW_SHA_QUALIFICATION_FAILURE_NATIVE_CASE_ZERO_ORIGIN_NULL'),
    (BASE / 'cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09/failure-origin.cb7175.json', 'a6ebf436321f6e8e26d9133c428dedf5565a9a56bcf36c455b9b899f12741d84', 'READONLY_TOOL_NONZERO_NATIVE_NULL'),
    (BASE / 'cli43_failed_execution_independent_review_codex/684f0c8b739541fe8da3b2f06ca78d09/failure-origin.ad3e4f.json', 'b457d79fb2152cd0da171f0abf1de24ec9cf8da750a1c201b7fed6dab892f380', 'READONLY_TOOL_NONZERO_NATIVE_NULL'),
    (OUT / 'failure-origin.79e033.json', '81d691aec806f2bbe8ed1ea1191f7582cfb1018b3d2442292f8102a5de0016ca', 'READONLY_TOOL_NONZERO_NATIVE_NULL'),
    (OUT / 'failure-origin.36d659.json', '0c4c8ad65d32ee921cf5fea0b5c3f5ea1cb14a3edab65ac7af438ab72bd9458c', 'READONLY_TOOL_NONZERO_NATIVE_NULL')
]
origins = []
for p, digest, kind in specs:
    origins.append({'evidence_ref': verified(p, digest), 'original_payload': doc(p),
        'classification': kind, 'counter_reset': False, 'automatic_same_input_retry': False})
container = BASE / 'f08_i17_binding_source_mapping_codex/83077264f7f748daa7c9452e22c5c2d0/origins.json'
container_ref = verified(container, '0ee0bf01989b0a341a3f19e6e726709645886690a7d74845aafaa20c28b97e96')
payload = doc(container)
assert [row['id'] for row in payload['new_origins']] == ['b9d4f8', 'bafc93', '427f1a']
leaf_dir = OUT / 'mapped-origin-leaves.for-r329'
leaf_dir.mkdir(exist_ok=False)
for index, row in enumerate(payload['new_origins']):
    leaf = leaf_dir / ('original-row.' + row['id'] + '.json')
    save(leaf, row)
    assert doc(leaf) == row
    origins.append({'evidence_ref': pin(leaf), 'original_payload': row,
        'original_container_ref': container_ref, 'original_container_payload': payload,
        'original_origin_row': row, 'original_origin_index': index,
        'leaf_extraction_only_not_new_execution': True,
        'classification': 'INDEPENDENT_READONLY_METADATA_NONZERO_ORIGINAL_NATIVE_NULL_OR_ONE_PRESERVED',
        'counter_reset': False, 'automatic_same_input_retry': False})
assert len(origins) == 12 and len({row['evidence_ref']['sha256'] for row in origins}) == 12
closed = doc(OUT / 'root-launch.outer-completion.json')
for row in closed['canonical_refs_at_completion']:
    actual = pin(Path(row['path']))
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
cp = doc(ROOT / 'execution/v2.4/checkpoint.json')
ow = doc(ROOT / 'execution/v2.4/path_ownership.json')
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [328,156,469]
assert all(all(old.get('evidence_ref', {}).get('sha256') != row['evidence_ref']['sha256'] for old in cp['failure_counters']) for row in origins)
for row in origins:
    assert pin(ROOT / row['evidence_ref']['path']) == row['evidence_ref']
cut = {'schema': 'researchos.root-late-origin-cut.v1', 'actor': 'codex:/root',
    'before': [328,156,469], 'after': [329,157,481], 'registered_origin_count': 469,
    'captured_late_origin_count': 12, 'fixed_cut_observed_origin_count': 481,
    'observed_including_later_pending_at_capture': 481, 'origins': origins,
    'native_NULL_and_original_payloads_preserved': True, 'nested_exit_propagations_counted_once': True,
    'mapped_three_container_rows_extracted_exactly_not_reexecuted': True,
    'canonical_writes': 0, 'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0}
save(OUT / 'late-origins.capture.for-r329.json', cut)
print(json.dumps({'capture_ref': pin(OUT / 'late-origins.capture.for-r329.json'),
    'captured_late_origins': 12, 'canonical_unchanged': True}, ensure_ascii=False))
