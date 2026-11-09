import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
CANON = ['checkpoint', 'path_ownership', 'step_state', 'commands']
CHAIN = [
    (OUT.parent / 'desktop-http-exact15-lease-r311', [310, 138, 384], [311, 139, 384]),
    (OUT.parent / 'session-list-closedcopy-exact1-r312', [311, 139, 384], [312, 140, 386]),
    (OUT, [312, 140, 386], [313, 141, 388]),
]


def ref(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def verify(item):
    assert ref(ROOT / item['path']) == item


def save(folder, name, value):
    with (folder / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(folder / name)


assert sys.flags.isolated and not sys.flags.optimize
tools = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(tools['python']['path']).resolve()
for name in ['python', 'git']:
    assert hashlib.sha256(Path(tools[name]['path']).read_bytes()).hexdigest() == tools[name]['sha256']
assert subprocess.check_output([tools['git']['path'], 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(subprocess.check_output([tools['git']['path'], 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
previous_desired = None
sealed = []
for folder, expected_before, expected_after in CHAIN:
    invocation = json.loads((folder / 'invocation.json').read_bytes())
    assert invocation['actual_exit'] == 0 and invocation['automatic_retry'] is False and invocation['counter_reset'] is False
    assert invocation['runner_sha256'] == ref(folder / 'register.py')['sha256']
    assert invocation['wrapper_sha256'] == ref(folder / 'run.py')['sha256']
    assert invocation['stdout_sha256'] == ref(folder / 'stdout.raw')['sha256']
    assert invocation['stderr_sha256'] == ref(folder / 'stderr.raw')['sha256']
    verify(invocation['review_ref'])
    intent = json.loads((folder / 'canonical-write.intent.json').read_bytes())
    verified = json.loads((folder / 'canonical-write.verified.json').read_bytes())
    verify(verified['intent_ref'])
    assert intent['transition'] == {'checkpoint': [expected_before[0], expected_after[0]],
                                    'ownership': [expected_before[1], expected_after[1]],
                                    'failures': [expected_before[2], expected_after[2]]}
    original = [(folder / (name + '.original.json')).read_bytes() for name in CANON]
    desired = [(folder / (name + '.desired.json')).read_bytes() for name in CANON[:2]] + original[2:]
    if previous_desired is not None:
        assert original == previous_desired
    previous_desired = desired
    before_cp, before_ow = [json.loads(raw) for raw in original[:2]]
    after_cp, after_ow = [json.loads(raw) for raw in desired[:2]]
    assert [before_cp['revision'], before_ow['revision'], len(before_cp['failure_counters'])] == expected_before
    assert [after_cp['revision'], after_ow['revision'], len(after_cp['failure_counters'])] == expected_after
    assert after_cp['failure_counters'][:expected_before[2]] == before_cp['failure_counters']
    assert after_cp['current_effective_formal_status'] == before_cp['current_effective_formal_status']
    for item in intent['metadata']:
        verify(item['original_ref'])
        verify(item['desired_ref'])
        done = json.loads((folder / ('canonical-write.' + Path(item['path']).stem + '.done.json')).read_bytes())
        assert done['sha256'] == item['desired_ref']['sha256']
    for item, raw in zip(intent['unchanged'], original[2:]):
        assert hashlib.sha256(raw).hexdigest() == item['sha256']
    assert [verified['checkpoint'], verified['ownership'], verified['failure_origins']] == expected_after
    assert verified['formal_increment'] == 0
    worktree_refs = []
    if expected_after[0] in [311, 312]:
        worktree = json.loads((folder / 'worktree-create.invocation.json').read_bytes())
        assert worktree['actual_exit'] == 0 and worktree['wrapper_error'] is None
        verify(worktree['stdout'])
        verify(worktree['stderr'])
        worktree_refs = [ref(folder / name) for name in ['worktree-create.invocation.json', 'worktree-ready.json']]
    audit = save(folder, 'registration-chain-audit.json', {
        'actor': 'codex:/root', 'status': 'ACTUAL_CANONICAL_REGISTRATION_CLOSED_HISTORICAL_CHAIN',
        'before': expected_before, 'after': expected_after,
        'actual_registration_exit': 0, 'invocation_ref': ref(folder / 'invocation.json'),
        'intent_ref': ref(folder / 'canonical-write.intent.json'),
        'verified_ref': ref(folder / 'canonical-write.verified.json'),
        'review_ref': invocation['review_ref'], 'worktree_creation_refs': worktree_refs,
        'old_failure_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
        'scope': 'Historical canonical bytes and actual registration/creation only; current author worktree cleanliness is not asserted.'})
    entries = [ref(path) for path in sorted(folder.rglob('*')) if path.is_file() and path.name != 'manifest.json']
    manifest = save(folder, 'manifest.json', {'entries': entries, 'count': len(entries),
        'self_excluded': True, 'at_seal_only': True, 'future_temporal_append_not_covered': True})
    sealed.append({'after': expected_after, 'audit': audit, 'manifest': manifest})
assert [(ROOT / 'execution/v2.4' / (name + '.json')).read_bytes() for name in CANON] == previous_desired
print(json.dumps({'sealed_registration_chain': sealed, 'current': [313, 141, 388],
                  'product_and_formal_acceptance': False}, ensure_ascii=True))
