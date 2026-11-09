"""Prepare current once-only caller by replacing only two reviewed pins."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
OLD = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-fresh-held2-r326-477e329b79944cb0b33f9ead24811760/root-launch-once.v2.py'
OLD_SCOPE = b'68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566'
OLD_GRANT = b'93329e2cd46e334043ded2000cf196c2fd0273be6454954720cae830063eac62'
NEW_SCOPE = b'320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'
NEW_GRANT = b'4b7ba306f378ef9a736619e36ec70e5a1c5d614481c069dedab01efdad841ac8'

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
scope_path = OUT / 'scope_registration.json'
assert pin(scope_path)['sha256'] == NEW_SCOPE.decode('ascii')
scope = json.loads(scope_path.read_bytes())
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
assert pin(grant_path)['sha256'] == NEW_GRANT.decode('ascii')
grant = json.loads(grant_path.read_bytes())
assert grant['actual_registration_completed'] is True
assert grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED'
assert grant['scope_ref']['sha256'] == NEW_SCOPE.decode('ascii')
assert scope['expected_registration'] == [327, 155, 459]
assert not any(Path(scope[key]).exists() for key in ('new_output_root', 'new_wrapper_root', 'new_export_root'))
for name in ('root-launch.intent.json', 'root-launch.stdout.raw', 'root-launch.stderr.raw', 'root-launch.invocation.json'):
    assert not (OUT / name).exists(), name
assert pin(OLD)['sha256'] == '0d2813b929540476206feaabc51f497e35de4dc991fa84cf6018a86b4a7adc63'
old = OLD.read_bytes()
assert old.count(OLD_SCOPE) == 1 and old.count(OLD_GRANT) == 1
new = old.replace(OLD_SCOPE, NEW_SCOPE).replace(OLD_GRANT, NEW_GRANT)
assert new.replace(NEW_SCOPE, OLD_SCOPE).replace(NEW_GRANT, OLD_GRANT) == old
ast.parse(new.decode('utf-8'), filename='root-launch-once.v2.py')
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
    'late_origins_outside_sealed_registration_cut': 3,
    'registered_origin_count': 459, 'observed_origin_count': 462,
    'late_origin_note': 'F08 peer 4ddd35, Source fork 4024a7, Cmd communication thread-limit retained outside fixed cut; register later without changing this sealed scope.'
})
print(json.dumps({'caller_ref': pin(OUT / 'root-launch-once.v2.py'), 'scope_ref': pin(scope_path), 'grant_ref': pin(grant_path)}, ensure_ascii=False))
