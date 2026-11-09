"""Prepare a new once-only caller from immutable r328 bytes and the actual r329 grant."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r328-bf943a8137c74df09e010347615b0eec/root-launch-once.v2.py'
OLD_SCOPE = b'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3'
OLD_GRANT = b'26bda302fbb13193918ff58a2fc271f8e013e85cc8df4d98d2b0cc40a82bc010'
NEW_SCOPE = b'90aec754f429ee9f946ac6943685848b358a33e28ea2f4e7484b03235c6673e0'

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
parser = argparse.ArgumentParser()
parser.add_argument('--grant-sha256', required=True)
args = parser.parse_args()
assert len(args.grant_sha256) == 64 and all(c in '0123456789abcdef' for c in args.grant_sha256)
new_grant = args.grant_sha256.encode('ascii')
scope_path = OUT / 'scope_registration.json'
assert pin(scope_path)['sha256'] == NEW_SCOPE.decode('ascii')
scope = json.loads(scope_path.read_bytes())
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
assert pin(grant_path)['sha256'] == args.grant_sha256
grant = json.loads(grant_path.read_bytes())
assert grant['actual_registration_completed'] is True
assert grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED'
assert grant['scope_ref']['sha256'] == NEW_SCOPE.decode('ascii')
assert scope['expected_registration'] == [329, 157, 481]
assert not any(Path(scope[key]).exists() for key in ('new_output_root', 'new_wrapper_root', 'new_export_root'))
for name in ('root-launch.intent.json', 'root-launch.stdout.raw', 'root-launch.stderr.raw', 'root-launch.invocation.json'):
    assert not (OUT / name).exists(), name
assert pin(OLD)['sha256'] == 'aad28f3f72605af1195637ec262f1a8b84f8ebeda1066f13467793cb0a7979f8'
old = OLD.read_bytes()
assert old.count(OLD_SCOPE) == 1 and old.count(OLD_GRANT) == 1
new = old.replace(OLD_SCOPE, NEW_SCOPE).replace(OLD_GRANT, new_grant)
assert new.replace(NEW_SCOPE, OLD_SCOPE).replace(new_grant, OLD_GRANT) == old
ast.parse(new.decode('utf-8'), filename='root-launch-once.v2.py')
snapshot_path = OUT / 'RESUME.prepare.snapshot.json'
assert pin(snapshot_path)['sha256'] == '6e47a26a6091d935994580d531a8342f235f18bac93207f6b58c3dc37e8b2fa3'
snapshot = json.loads(snapshot_path.read_bytes())
late = snapshot['outside_fixed_cut']
assert len(late) == 3
for row in late:
    if row.get('ref') is not None:
        actual = pin(row['ref']['path'])
        assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
canon = []
for row in grant['canonical_copies']:
    actual = pin(ROOT / row['canonical_path'])
    assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
    canon.append(actual)
with (OUT / 'root-launch-once.v2.py').open('xb') as stream:
    stream.write(new)
save('root-caller-preparation.json', {
    'actor': 'codex:/root', 'source_only': True,
    'old_caller_ref': pin(OLD), 'new_caller_ref': pin(OUT / 'root-launch-once.v2.py'),
    'preparer_ref': pin(__file__), 'scope_ref': pin(scope_path), 'grant_ref': pin(grant_path),
    'changed_constants_only': ['SCOPE_SHA', 'GRANT_SHA'],
    'whole_byte_inverse_equal': True, 'AST_parsed_without_execution': True,
    'executor_launcher_export_absent': True, 'launch_outputs_absent': True,
    'canonical_refs_equal_actual_grant_copies': canon,
    'launcher_executed': False, 'Go_SQL_SDK_Model_HTTP_calls': 0,
    'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0,
    'registered_origin_count': 481, 'observed_origin_count_at_snapshot': 484,
    'late_origins_outside_sealed_registration_cut_at_snapshot': late,
    'late_origins_snapshot_ref': pin(snapshot_path),
    'late_origin_note': 'Three known late origins remain outside fixed r329 cut. Exact sealed metadata for the third remains pending in this immutable snapshot; later receipts must retain original NULL/native/outer facts. No failure count reset. Cleanup remains PENDING_POLICY_REJECTION.'
})
print(json.dumps({'caller_ref': pin(OUT / 'root-launch-once.v2.py'),
    'preparation_ref': pin(OUT / 'root-caller-preparation.json'),
    'scope_ref': pin(scope_path), 'grant_ref': pin(grant_path)}, ensure_ascii=False))
