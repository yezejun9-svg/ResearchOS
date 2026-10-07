"""Independent, read-only audit of the supplied W13 raw execution evidence."""
from pathlib import Path
import collections
import hashlib
import io
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def checkhash(path, expected):
    assert digest(path) == expected.removeprefix('sha256:'), str(path)

def frozen_manifest(manifest, revision):
    paths = list(manifest)
    batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                           input=''.join(f'{revision}:{p}\n' for p in paths).encode(), capture_output=True, check=True)
    stream = io.BytesIO(batch.stdout)
    for path in paths:
        header = stream.readline().split()
        assert len(header) == 3 and header[1] == b'blob', (path, header)
        data = stream.read(int(header[2])); assert stream.read(1) == b'\n'
        assert hashlib.sha256(data).hexdigest() == manifest[path].removeprefix('sha256:'), path
    return len(paths)

def invocation(id):
    folder = ROOT / 'execution/invocations' / id
    value = read(folder / 'receipt.json')
    assert value['status'] == 'PASS' and value['exit_code'] == 0 and value['assertion_ids']
    for name in ['stdout', 'stderr']:
        checkhash(ROOT / value[name]['path'], value[name]['sha256'])
    output = json.loads((folder / 'stdout.txt').read_text(encoding='utf-8').splitlines()[-1])
    return value, output

result = {'status': 'PASS_INPUT_AUDIT_ONLY', 'formal_receipt_signed': False, 'browser': [], 'backend': [],
          'limits': ['Physical OS sleep not executed; C26 and W13 stage acceptance remain false.',
                     'No new browser or business test executed by this audit; actual raw evidence independently checked.']}
ids = ['0a70d300-8432-4971-805e-afc74dbaa3ad', 'f9378174-6a6c-47cd-b43a-82d470b651c0',
       'cdae0833-2b55-4be7-a2b7-b082a5ade22f', 'fa55ec06-24d5-472f-b49a-a283d5297243']
children = {}
for id in ids:
    inv, stdout = invocation(id)
    report_path = Path(stdout['receipt']); report = read(report_path); before = read(report_path.parent / 'before.json')
    assert before['code_revision'] == inv['code_revision'] == 'be8f6a7266fc11fb58afeb724cda4883323d41fb'
    assert report['status'] == 'PASS' and report['source_drift'] == []
    assert report['expected_checks'] == report['actual_checks'] and report['assertion_ids'] == inv['assertion_ids']
    assert all(row['status'] == 'PASS' and row['actual'] == row['expected'] for row in report['assertions'])
    for name, sha in report['raw_evidence_hashes'].items(): checkhash(report_path.parent / name, sha)
    child_path = ROOT / report['child_report']; checkhash(child_path, report['child_report_hash']); child = read(child_path)
    assert child['status'] == 'PASS' and child['phase'] == report['phase'] and child['checks'] == report['actual_checks']
    assert set(child['screenshots']) == set(child['screenshot_hashes'])
    dimensions = {}
    for name, sha in child['screenshot_hashes'].items():
        png = child_path.parent / name; checkhash(png, sha)
        dimensions[name] = list(struct.unpack('>II', png.read_bytes()[16:24]))
    source_count = frozen_manifest(before['source_manifest'], before['code_revision'])
    for row in child.get('responsive_matrix', []):
        assert row['no_overflow'] and (row['width'] >= 768 or row['mobile_targets_44px'])
        if row['width'] in [320, 390, 768, 1024, 1440]:
            name = f"{row['screen']}-{row['theme']}-{row['width']}.png"
            assert dimensions[name][0] == row['width'], name
            # Reviewed runner deliberately captures full document on >=768px.
            assert dimensions[name][1] >= row['height'], name
            if row['width'] < 768: assert dimensions[name][1] == row['height'], name
    row = {'invocation': id, 'phase': report['phase'], 'assertions': len(report['assertions']),
           'manifest_files_verified_against_git': source_count, 'screenshots_verified': len(dimensions),
           'responsive_cases': len(child.get('responsive_matrix', [])), 'child_report': report['child_report'],
           'child_report_sha256': digest(child_path)}
    result['browser'].append(row); children[report['phase']] = child

n = children['contracts']['notification_contract']; ids = n['replay_event_ids']; count = n['reversed_old_events']
assert count > 0 and len(ids) == n['replay_frame_count'] == 6 * count
assert len(set(ids)) == count and set(collections.Counter(ids).values()) == {6}
assert n['stream_last_event_ids'] and not n['writes_from_replay'] and n['offline_delivery_recovered'] and n['read_twice_same_logical_notification']
chain = children['contracts']['sidebar_chain']
assert all(chain[key] == n[key] for key in ['release_id', 'artifact_ref', 'acceptance_id'])
assert all(chain[key] for key in ['clicked_actual_sidebar_link', 'expanded_full_receipt', 'hash_checked_content_rendered'])
assert children['contracts']['browser_freeze']['physical_os_sleep'] is False
result['notification_replay'] = {'nonempty_events': count, 'frames_fulfilled_to_browser': len(ids), 'copies_per_event': 6,
                                 'duplicate_cards_or_writes': False, 'sidebar_exact_full_chain': True}

for id in ['a96b94e9-3b4a-497b-bd1e-f95337e4dbe8', 'dd249fca-899f-42a7-a3ac-1f719584c2fb']:
    inv, stdout = invocation(id); path = Path(stdout['receipt']); report = read(path); before = read(path.parent / 'before.json')
    assert report['backend_status'] == 'PASS' and not report['missing'] and not report['malformed'] and not report['changed_during_run']
    assert report['assertion_ids'] == inv['assertion_ids']
    for name, sha in report['raw_evidence_hashes'].items(): checkhash(path.parent / name, sha)
    for row in report['assertions']:
        assert row['status'] == 'PASS' and row['actual'] == row['expected'], row['assertion_id']
        raw = row['raw_evidence']; raw_path = path.parent / raw['path']; checkhash(raw_path, raw['sha256'])
        line = raw_path.read_text(encoding='utf-8').splitlines()[raw['line'] - 1]
        payload = json.loads(line[line.index('{'):]); expected = {k: v for k, v in row.items() if k != 'raw_evidence'}
        assert payload == expected, row['assertion_id']
    result['backend'].append({'invocation': id, 'assertions': len(report['assertions']),
                              'manifest_files_verified_against_git': frozen_manifest(before['source_manifest'], before['code_revision']),
                              'report': str(path.relative_to(ROOT)).replace('\\', '/'), 'sha256': digest(path)})
inv, stdout = invocation('4bf521a5-6257-4898-a053-3acb5f62c77e')
assert stdout['status'] == 'PASS' and stdout['assertion_ids'] == inv['assertion_ids'] and len(inv['assertion_ids']) == 5
result['contracts_assertions'] = 5
result['fixture_diff_review'] = {'3a79574': 'Only positive/redirect native transport budget1s->5s; explicit timeout/cancel10ms and expected outcomes retained.',
                                  '6238e81': 'Reserved204 readiness is checked before URL exposure; max3 fresh listeners. Handler bypassed only on readiness path, foreignHits/business call counters not modified; business assertions not retried or weakened.'}
(OUT / 'input-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
