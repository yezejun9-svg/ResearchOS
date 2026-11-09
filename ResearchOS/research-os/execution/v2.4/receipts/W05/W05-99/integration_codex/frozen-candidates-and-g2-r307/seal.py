import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


pins = {
    'checkpoint.json': ('1bedd2bc418f5621a08799335cdcd7d609eeb8364e16ade4ca3b9df295551826', 1029825),
    'path_ownership.json': ('4777e3d595b4b1a3c0bb785d030937d8badff40f1076f276ffbd8d6ede07c990', 158787),
    'step_state.json': ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149', 257446),
    'commands.json': ('b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129', 68156),
}
for name, (sha, size) in pins.items():
    item = ref(ROOT / 'execution/v2.4' / name)
    assert (item['sha256'], item['bytes']) == (sha, size)
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
ow = json.loads((ROOT / 'execution/v2.4/path_ownership.json').read_bytes())
old = json.loads((OUT / 'checkpoint.original.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [307, 135, 367]
assert cp['failure_counters'][:362] == old['failure_counters']
assert cp['current_effective_formal_status'] == old['current_effective_formal_status']
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
for key in ['cli_exact8_protocol_repair', 'session_list_identity_exact2']:
    assert subtasks[key]['current_source_writer'] is None and subtasks[key]['source_ready'] is False
assert subtasks['provider_g2_finite_exact2']['current_source_writer'] == 'codex:/root/sources_parent_impl'
assert subtasks['provider_g2_finite_exact2']['paths'] == ['internal/domain/runtime_provider_binding_windows_test.go', 'internal/domain/runtime_coordinator_windows_test.go']
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
invocation = json.loads((OUT / 'invocation.json').read_bytes())
assert invocation['actual_exit'] == 0
assert (OUT / 'stderr.raw').read_bytes() == b''
save('postexecution.audit.json', {'actual_registration_exit': 0, 'checkpoint': 307, 'ownership': 135,
    'failure_origins': 367, 'old362_prefix_preserved': True, 'canonical_refs': [ref(ROOT / 'execution/v2.4' / name) for name in pins],
    'Main_head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(), 'staged_index_empty': True,
    'old11_deletions_preserved': True, 'CLI8_and_list2_source_writers_released': True,
    'G2_new_worktree_exact2_test_source_lease_only': True, 'Main_integration_HOLD': True,
    'formal_increment': 0, 'counter_reset': False, 'registration_invocation_ref': ref(OUT / 'invocation.json'),
    'latest_handoff_ref': ref(OUT / 'handoff-r307-running.json')})
entries = [ref(path) for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'manifest.json']
save('manifest.json', {'entries': entries, 'listed': len(entries), 'formal_increment': 0, 'state': 'CAS307_ACTUAL0_SEALED_NOT_PRODUCT_ACCEPTANCE'})
print(json.dumps({'postexecution': ref(OUT / 'postexecution.audit.json'), 'manifest': ref(OUT / 'manifest.json'), 'listed': len(entries)}, ensure_ascii=True))
