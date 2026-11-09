import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'


def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


for name in ['checkpoint.json', 'path_ownership.json']:
    assert (BASE / name).read_bytes() == (OUT / (Path(name).stem + '.desired.json')).read_bytes()
for name in ['step_state.json', 'commands.json']:
    assert (BASE / name).read_bytes() == (OUT / (Path(name).stem + '.original.json')).read_bytes()
cp = json.loads((BASE / 'checkpoint.json').read_bytes())
ow = json.loads((BASE / 'path_ownership.json').read_bytes())
old = json.loads((OUT / 'checkpoint.original.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [308, 136, 371]
assert cp['failure_counters'][:367] == old['failure_counters']
assert cp['current_effective_formal_status'] == old['current_effective_formal_status']
old_ow = json.loads((OUT / 'path_ownership.original.json').read_bytes())
assert ow['card_path_bindings']['W05-99']['subtasks']['provider_g2_finite_exact2'] == old_ow['card_path_bindings']['W05-99']['subtasks']['provider_g2_finite_exact2']
assert json.loads((OUT / 'invocation.json').read_bytes())['actual_exit'] == 0
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
head = subprocess.check_output([lock['git']['path'], 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([lock['git']['path'], 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([lock['git']['path'], 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
save('postexecution.audit.json', {'actual_registration_exit': 0, 'checkpoint': 308, 'ownership': 136, 'failure_origins': 371,
    'old367_prefix_preserved': True, 'canonical_refs': [ref(BASE / name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']],
    'Main_head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(), 'old11_deletions_preserved': True,
    'staged_index_empty': True, 'Source_G2_existing_exact2_lease_unchanged': True, 'Main_integration_HOLD': True,
    'new_independent_CLI47_and_list14_execution_only': True, 'source_acceptance': False, 'formal_increment': 0})
entries = [ref(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'manifest.json']
save('manifest.json', {'entries': entries, 'listed': len(entries), 'formal_increment': 0, 'state': 'CAS308_ACTUAL0_SEALED_NOT_PRODUCT_ACCEPTANCE'})
print(json.dumps({'postexecution': ref(OUT / 'postexecution.audit.json'), 'manifest': ref(OUT / 'manifest.json'), 'listed': len(entries)}, ensure_ascii=True))
