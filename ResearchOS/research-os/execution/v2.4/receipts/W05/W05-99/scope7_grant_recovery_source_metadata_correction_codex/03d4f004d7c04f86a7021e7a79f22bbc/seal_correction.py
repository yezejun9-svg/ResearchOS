"""Additive correction of the original Source packet member claim."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OLD = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
              'scope7_grant_recovery_source_preparation_codex/'
              '8821517157754457be7645afa51c5177')
HERE = ROOT / ('execution/v2.4/receipts/W05/W05-99/'
               'scope7_grant_recovery_source_metadata_correction_codex/'
               '03d4f004d7c04f86a7021e7a79f22bbc')
NAMES = {
    'scope7_grant_recover.proposed.py',
    'scope7_grant_recover.v2.proposed.py',
    'precheck_scope7.py', 'precheck.scope7.v5.json',
    'tool-io.selected.json', 'tool-io.final.json', 'tool-io.v2.json',
    'source.inverse.json', 'future-inputs.template.json',
    'failure-origin-001.json', 'report.json', 'manifest.json',
    'handoff.json', 'seal_scope7.py'}


def pin(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def put(name, value):
    target = HERE / name
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False,
                      indent=2, allow_nan=False) + '\n').encode('utf-8')
    with target.open('xb') as output:
        output.write(raw)
    return pin(target)


actual = {path.name for path in OLD.iterdir() if path.is_file()}
assert actual == NAMES, {'unexpected': sorted(actual - NAMES),
                         'missing': sorted(NAMES - actual)}
old_mf = pin(OLD / 'manifest.json')
old_hdf = pin(OLD / 'handoff.json')
assert old_mf['sha256'] == 'cfa6a809d7d847a46a7198574c75c18650e84c8a0695f66f9e4c314039cdbf49'
assert old_hdf['sha256'] == 'e6612f97a16cd79f766caca1fcef2dccc9a5db3e4c7c6185f77106fec6d41760'
old_doc = json.loads((OLD / 'manifest.json').read_text(encoding='utf-8'))
assert len(old_doc['members']) == old_doc['count'] == 11
missing = NAMES - {Path(ref['path']).name for ref in old_doc['members']}
assert missing == {'manifest.json', 'handoff.json', 'seal_scope7.py'}
inventory_ref = put('original-namespace-complete-inventory.json', {
    'schema': 'researchos.scope7-source-complete-inventory.v1',
    'original_namespace': OLD.relative_to(ROOT).as_posix(),
    'all_existing_files': [pin(OLD / name) for name in sorted(NAMES)],
    'count': 14, 'actual_not_in_original_MF': sorted(missing),
    'original_MF_ref': old_mf, 'original_HDF_ref': old_hdf})
report_ref = put('correction.json', {
    'schema': 'researchos.scope7-source-metadata-correction.v1',
    'status': 'ADDITIVE_CORRECTION_ONLY',
    'original_MF_ref': old_mf, 'original_HDF_ref': old_hdf,
    'old_claim_excluded_only_self': True,
    'old_claim_valid': False,
    'old_member_count': 11, 'actual_existing_file_count': 14,
    'missing_from_old_MF': sorted(missing),
    'complete_inventory_ref': inventory_ref,
    'source_candidate_unchanged': True,
    'gate_executions': 0, 'product_executions': 0,
    'grant_tail_writes': 0, 'formal_increment': 0})
mf_ref = put('manifest.json', {
    'schema': 'researchos.scope7-source-correction-manifest.v1',
    'members': [pin(HERE / name) for name in
                ('seal_correction.py', 'original-namespace-complete-inventory.json',
                 'correction.json')],
    'count': 3, 'excluded_names': ['manifest.json', 'handoff.json']})
hdf_ref = put('handoff.json', {
    'schema': 'researchos.scope7-source-correction-handoff.v1',
    'status': 'STOPPED_METADATA_CORRECTION',
    'inventory_ref': inventory_ref, 'correction_ref': report_ref,
    'manifest_ref': mf_ref, 'supersedes_original_MF_completeness_claim': old_mf,
    'source_candidate_unchanged': True, 'formal_increment': 0})
print(json.dumps({'inventory': inventory_ref, 'correction': report_ref,
                  'manifest': mf_ref, 'handoff': hdf_ref},
                 ensure_ascii=False, separators=(',', ':')))
