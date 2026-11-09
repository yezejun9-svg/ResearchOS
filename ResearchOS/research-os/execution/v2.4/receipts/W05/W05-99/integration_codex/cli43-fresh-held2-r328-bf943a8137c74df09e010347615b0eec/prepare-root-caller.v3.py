"""Prepare the once-only caller using the actual independently reviewed scope and grant."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r327-efa7776ec48e4a7abaa92ce85eb0dace/root-launch-once.v2.py'
OLD_SCOPE = b'320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'
OLD_GRANT = b'4b7ba306f378ef9a736619e36ec70e5a1c5d614481c069dedab01efdad841ac8'
NEW_SCOPE = b'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3'
F08_HANDOFF = ROOT / 'execution/v2.4/receipts/W05/W05-99/f08_sqlite_driver18_independent_source_review_codex/fd09d8ec0d5a4559bcdd338e32a646af/handoff.json'

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
assert scope['expected_registration'] == [328, 156, 469]
assert not any(Path(scope[key]).exists() for key in ('new_output_root', 'new_wrapper_root', 'new_export_root'))
for name in ('root-launch.intent.json', 'root-launch.stdout.raw', 'root-launch.stderr.raw', 'root-launch.invocation.json'):
    assert not (OUT / name).exists(), name
assert pin(OLD)['sha256'] == '665031b99edc5031ebd5e40a80abb1c09bc39a33ab623d8b4d099823240f60dc'
old = OLD.read_bytes()
assert old.count(OLD_SCOPE) == 1 and old.count(OLD_GRANT) == 1
new = old.replace(OLD_SCOPE, NEW_SCOPE).replace(OLD_GRANT, new_grant)
assert new.replace(NEW_SCOPE, OLD_SCOPE).replace(new_grant, OLD_GRANT) == old
ast.parse(new.decode('utf-8'), filename='root-launch-once.v2.py')
assert pin(F08_HANDOFF)['sha256'] == '22fa0484e699ef1e4fa7422dbf94dcddc2d0efc33bd1bf3285bbba75303c2704'
late = json.loads(F08_HANDOFF.read_bytes())['new_reviewer_origins']
assert len(late) == 3
for row in late:
    actual = pin(row['ref']['path'])
    assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
with (OUT / 'root-launch-once.v2.py').open('xb') as stream:
    stream.write(new)
save('root-caller-preparation.json', {
    'actor': 'codex:/root', 'source_only': True,
    'old_caller_ref': pin(OLD), 'new_caller_ref': pin(OUT / 'root-launch-once.v2.py'),
    'scope_ref': pin(scope_path), 'grant_ref': pin(grant_path),
    'changed_constants_only': ['SCOPE_SHA', 'GRANT_SHA'],
    'whole_byte_inverse_equal': True, 'AST_parsed_without_execution': True,
    'executor_launcher_export_absent': True, 'launch_outputs_absent': True,
    'launcher_executed': False, 'Go_SQL_SDK_Model_HTTP_calls': 0,
    'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0,
    'registered_origin_count': 469, 'observed_origin_count_at_preparation': 472,
    'late_origins_outside_sealed_registration_cut': late,
    'late_origins_handoff_ref': pin(F08_HANDOFF),
    'late_origin_note': 'Three independently recorded late origins remain outside the sealed r328 cut. NULL/native/outer facts preserved; register in a later scope. Cleanup remains PENDING_POLICY_REJECTION.'
})
print(json.dumps({'caller_ref': pin(OUT / 'root-launch-once.v2.py'), 'scope_ref': pin(scope_path), 'grant_ref': pin(grant_path)}, ensure_ascii=False))
