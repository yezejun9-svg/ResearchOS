import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def run(name, argv, cwd):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    child = None
    error = None
    try:
        with (OUT / (name + '.stdout.raw')).open('xb') as stdout, (OUT / (name + '.stderr.raw')).open('xb') as stderr:
            child = subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    except BaseException as exc:
        error = repr(exc)
    finally:
        save(name + '.invocation.json', {'argv': argv, 'cwd': str(cwd), 'started_at': started,
            'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'actual_exit': child.returncode if child is not None else None, 'wrapper_error': error,
            'stdout': ref(OUT / (name + '.stdout.raw')) if (OUT / (name + '.stdout.raw')).is_file() else None,
            'stderr': ref(OUT / (name + '.stderr.raw')) if (OUT / (name + '.stderr.raw')).is_file() else None,
            'automatic_retry': False})
    assert child is not None and child.returncode == 0 and error is None
    return (OUT / (name + '.stdout.raw')).read_bytes()


assert sys.flags.isolated and not sys.flags.optimize
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 312 and len(cp['failure_counters']) == 386
scope_path = OUT / 'scope_registration.json'
scope_pin = ref(scope_path)
assert scope_pin == cp['work_in_progress']['session_list_closedcopy_exact1_scope_ref']
assert scope_pin['sha256'] == '31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'
scope = json.loads(scope_path.read_bytes())
wt = Path(scope['worktree']).resolve()
assert wt.is_relative_to(ROOT / '.local/worktrees') and not wt.exists()
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
git = lock['git']['path']
for name in ['git', 'python']:
    assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
original = {path: path.read_bytes() for path in [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]}
head = run('worktree-before-head', [git, 'rev-parse', 'HEAD'], ROOT).decode().strip()
assert head == cp['head'] == scope['Main_head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert run('worktree-before-branch', [git, 'for-each-ref', '--format=%(refname)', 'refs/heads/' + scope['branch']], ROOT) == b''
save('worktree-create.intent.json', {'scope_ref': scope_pin, 'target': str(wt), 'branch': scope['branch'],
    'base_commit': scope['base_commit'], 'Main_head': head, 'canonical_refs': [ref(path) for path in original],
    'actor': 'codex:/root', 'source_writer': scope['owner'], 'automatic_retry': False, 'formal_increment': 0})
run('worktree-create', [git, 'worktree', 'add', '-b', scope['branch'], str(wt), scope['base_commit']], ROOT)
assert run('worktree-after-head', [git, 'rev-parse', 'HEAD'], wt).decode().strip() == scope['base_commit']
assert run('worktree-after-status', [git, 'status', '--porcelain=v1'], wt) == b''
source_scope = json.loads((ROOT / scope['path_bounds_ref']['path']).read_bytes())
for row in source_scope['paths']:
    path = wt / row['path']
    if row['exists_before']:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'] and path.stat().st_size == row['bytes']
    else:
        assert not path.exists()
identity = json.loads((wt / 'execution/project_identity.json').read_bytes())
assert identity['project_id'] == cp['project_id']
assert all(path.read_bytes() == raw for path, raw in original.items())
result = save('worktree-ready.json', {'status': 'ACTUAL_DEDICATED_WORKTREE_READY_FOR_EXACT1_TEST_EVIDENCE_CORRECTION',
    'scope_ref': scope_pin, 'worktree': str(wt), 'branch': scope['branch'], 'base_commit': scope['base_commit'], 'Main_head': head,
    'owner': scope['owner'], 'existing1_hash_matches': True, 'new0_extra_paths': True, 'git_clean': True,
    'project_id': cp['project_id'], 'canonical_unchanged': True, 'Main_source_writes': 0, 'formal_increment': 0})
print(json.dumps({'worktree_ready_ref': result, 'worktree': str(wt)}, ensure_ascii=True))
