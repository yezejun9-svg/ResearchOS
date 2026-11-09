"""Retain late origins without changing the live sealed registration cut."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
RECEIPTS = ROOT / 'execution/v2.4/receipts/W05/W05-99'

def pin(path):
    path = Path(path).absolute()
    data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def checked(path, sha):
    ref = pin(path)
    assert ref['sha256'] == sha, ref
    return ref, json.loads(Path(path).read_bytes())

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
peer_ref, peer_doc = checked(RECEIPTS / 'f08_proof_evaluator_independent_source_review_codex/0a0cb85df5dc4e6981dea5fd6a316971/failure-origins.json', 'fe50f0694c1e4b932cfc1eb78d1758a5ef34cba775d5c439af6c5e419f0ac340')
assert peer_doc['new_origin_count'] == 1 and len(peer_doc['origins']) == 1
rows = [{'origin_ref': peer_ref, 'payload_pointer': '/origins/0', 'original_payload': peer_doc['origins'][0]}]
w05_ref, w05_doc = checked(RECEIPTS / 'root_registration_r326_readonly_review_codex/1ab523423a8849b1a2761c055140ad81/failure-origin.4ab1a6.json', '21d4fe9a4ddf9bb773a1a1e40790b9d44cd542bdb920e38271e3d8d9aa4564e6')
rows.append({'origin_ref': w05_ref, 'payload_pointer': '', 'original_payload': w05_doc})
author = RECEIPTS / 'f08_queue_absence_revision_preparation_codex/b9a560ed59c24bef9b9e01d2d91c4b84'
_, handoff = checked(author / 'handoff.json', '1828343f3ff153bf91907307ee7e95ecd4fb9f78b45b9946a31ce87882b10138')
assert len(handoff['new_failure_origin_refs']) == 4
for expected in handoff['new_failure_origin_refs']:
    ref, payload = checked(expected['path'], expected['sha256'])
    assert ref['bytes'] == expected['bytes']
    rows.append({'origin_ref': ref, 'payload_pointer': '', 'original_payload': payload})
for name in ('failure-origin.collaboration-source-map-limit.json', 'failure-origin.a76746.json'):
    path = OUT / name
    rows.append({'origin_ref': pin(path), 'payload_pointer': '', 'original_payload': json.loads(path.read_bytes())})
assert len(rows) == 8
assert len({row['origin_ref']['path'] for row in rows}) == 8
canonical = []
for name, sha in (
    ('checkpoint.json', 'f2cf3ceacdb741bc986e3e535871d28a3adb6faea10022b0b3d824a4a1a2a596'),
    ('path_ownership.json', '6931166b6e23fb42983aae1169b244bfa10394fe630ef19b73d4a89f2bf7b0c8'),
    ('step_state.json', 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'),
    ('commands.json', 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129')):
    ref = pin(ROOT / 'execution/v2.4' / name)
    assert ref['sha256'] == sha, ref
    canonical.append(ref)
result = {
    'schema': 'researchos.late-origin-retention.v1', 'actor': 'codex:/root',
    'registration_revision': 326, 'registered_origin_count': 450,
    'late_pending_origin_count': 8, 'observed_origin_count': 458,
    'canonical_refs_at_capture': canonical, 'origins': rows,
    'current_scope_grant_cut_unchanged': True, 'canonical_written': False,
    'target_invocations': 0, 'SDK_Model_HTTP_Go_SQL_calls': 0,
    'count_each_origin_once': True, 'automatic_retry': False,
    'counter_reset': False, 'formal_increment': 0,
    'future_action': 'Append these eight originals to a new Root registration cut after current execution closure; do not edit current sealed scope, grant or original origin receipts.'
}
with (OUT / 'late-origins.capture.json').open('xb') as stream:
    stream.write((json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps({'ref': pin(OUT / 'late-origins.capture.json'), 'registered': 450, 'late_pending': 8, 'observed': 458}, ensure_ascii=False))
