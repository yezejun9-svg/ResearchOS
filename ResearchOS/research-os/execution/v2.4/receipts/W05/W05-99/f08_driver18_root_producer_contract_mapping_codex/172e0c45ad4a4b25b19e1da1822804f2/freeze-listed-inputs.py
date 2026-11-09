"""Review metadata IO only: pin the already listed immutable inputs, never execute source."""
import hashlib
import json
from pathlib import Path

OWN = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_contract_mapping_codex/172e0c45ad4a4b25b19e1da1822804f2')

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}, raw

before = json.loads((OWN/'input-pins.before.json').read_bytes())
after = []
drift = []
for row in before['refs']:
    actual, raw = pin(row['ref']['path'])
    equal = actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
    result = {'before_ref': row['ref'], 'after_ref': actual, 'bytes_and_sha_equal': equal, 'category': row['category'], 'pin_phase': row['pin_phase']}
    after.append(result)
    if not equal:
        drift.append(result)

late = []
for prior in json.loads((OWN/'late-metadata-read-records.json').read_bytes())['documents']:
    actual, raw = pin(prior['path'])
    value = json.loads(raw)
    late.append({'actual_late_ref': actual, 'prior_parsed_document_equal': value == prior['original_parsed_document'], 'firstread_raw_hash_recorded': False})
document = {
    'schema': 'researchos.driver18-mapping-input-freeze.v1',
    'listed_previously_pinned_files': len(after),
    'after': after,
    'drift': drift,
    'late_metadata_pins': late,
    'not_recursive_tree_or_resource_verification': True,
    'canonical_live_reads': 0,
    'target_executions': 0,
    'source_acceptance': False,
}
with (OWN/'input-pins.after.json').open('xb') as output:
    output.write(encoded(document))
print(json.dumps({'listed_previously_pinned_files': len(after), 'drift_count': len(drift), 'late_metadata_files': len(late), 'late_semantic_equal': [row['prior_parsed_document_equal'] for row in late], 'after_ref': pin(OWN/'input-pins.after.json')[0], 'target_calls': 0}, ensure_ascii=False))
