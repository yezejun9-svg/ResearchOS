import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
DRAFT = OUT.parent / 'closure-and-finite-continuation-r309'


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


assert sys.flags.isolated and not sys.flags.optimize
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
for name in ['checkpoint', 'path_ownership']:
    assert (ROOT / ('execution/v2.4/' + name + '.json')).read_bytes() == (DRAFT / (name + '.desired.json')).read_bytes()
prepared = json.loads((DRAFT / 'prepared_refs.v2.json').read_bytes())
for item in prepared['canonical_before'][2:]:
    assert ref(ROOT / item['path']) == item
cp = json.loads((ROOT / 'execution/v2.4/checkpoint.json').read_bytes())
assert cp['revision'] == 309 and len(cp['failure_counters']) == 379
scope = DRAFT / 'list_independent_scope.v2.json'
scope_ref = ref(scope)
assert scope_ref['sha256'] == '8619aec61da6b0785f54849714e3574ecb3d37389145b7eacb75de2dfb761f93'
assert cp['work_in_progress']['session_list_identity_independent_scope_ref'] == scope_ref
runner = DRAFT / 'list_replay.v2.py'
assert ref(runner)['sha256'] == 'a714295db60586264dd7afdb302b48dfaa18791fd49b66e85455824783c014ad'
git = lock['git']['path']
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == cp['head']
assert hashlib.sha256(subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)).hexdigest() == prepared['git_status_sha256']
argv = [sys.executable, '-X', 'utf8', '-I', str(runner), str(scope), scope_ref['sha256']]
public_names = {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'OS', 'PATHEXT', 'PATH', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE'}
env = {key: value for key, value in os.environ.items() if key.upper() in public_names}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
save('started.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'at': started,
    'scope': scope_ref, 'runner': ref(runner), 'launcher': ref(Path(__file__)),
    'first_unexpected_stop': True, 'automatic_retry': False, 'formal_increment': 0})
child = None
wrapper_error = None
try:
    with (OUT / 'stdout.raw').open('xb') as stdout, (OUT / 'stderr.raw').open('xb') as stderr:
        child = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
except BaseException as error:
    wrapper_error = {'type': type(error).__name__, 'message': str(error)}
finally:
    save('invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'started_at': started,
        'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'actual_exit': child.returncode if child is not None else None, 'wrapper_error': wrapper_error,
        'scope': scope_ref, 'runner': ref(runner), 'launcher': ref(Path(__file__)),
        'stdout': ref(OUT / 'stdout.raw') if (OUT / 'stdout.raw').is_file() else None,
        'stderr': ref(OUT / 'stderr.raw') if (OUT / 'stderr.raw').is_file() else None,
        'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0})
print(json.dumps({'driver_actual_exit': child.returncode if child is not None else None,
    'wrapper_error': wrapper_error, 'stderr_display_only': (OUT / 'stderr.raw').read_text(encoding='utf-8', errors='replace')[-2500:] if (OUT / 'stderr.raw').is_file() else None,
    'stdout_display_only': (OUT / 'stdout.raw').read_text(encoding='utf-8', errors='replace')[-2500:] if (OUT / 'stdout.raw').is_file() else None}, ensure_ascii=True), flush=True)
sys.exit(child.returncode if child is not None else 1)
