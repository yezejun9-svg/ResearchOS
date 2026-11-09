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
DRAFT = OUT.parent / 'provider-g2-finite29-execute-r313'


def ref(path, absolute=False):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path) if absolute else path.relative_to(ROOT).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


assert sys.flags.isolated and not sys.flags.optimize
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for name in ['python', 'git']:
    assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
for name in ['checkpoint', 'path_ownership']:
    assert (ROOT / ('execution/v2.4/' + name + '.json')).read_bytes() == (DRAFT / (name + '.desired.json')).read_bytes()
prepared = json.loads((DRAFT / 'prepared_refs.json').read_bytes())
for item in prepared['canonical_before'][2:]:
    assert ref(ROOT / item['path']) == item
cp_raw = (ROOT / 'execution/v2.4/checkpoint.json').read_bytes()
cp = json.loads(cp_raw)
assert cp['revision'] == 313 and len(cp['failure_counters']) == 388
scope = DRAFT / 'scope_registration.json'
scope_ref = ref(scope)
assert cp['work_in_progress']['provider_g2_execute_scope_ref'] == scope_ref == prepared['pins']['scope']
value = json.loads(scope.read_bytes())
assert value['phases'] == ['execute'] and value['case_count'] == 29
runner = ROOT / value['runner_ref']['path']
assert ref(runner) == prepared['pins']['g2_runner']
assert ref(runner)['sha256'] == 'e687bd35560d4c34b4e939609b617a5d4770b4a45d51c3b132fca60a4bfa39f5'
spec_pin = value['spec_ref']
spec_path = ROOT / spec_pin['path']
assert ref(spec_path) == spec_pin
spec = json.loads(spec_path.read_bytes())
assert spec['candidate'] == value['candidate'] == '8d0921b7c42ecd40300c58192d54af1064947aed'
assert spec['output_root'] == value['output_root'] and spec['work_root'] == value['work_root']
assert [row['selector'] for row in spec['roster']] == value['finite_future_roster']
assert ref(ROOT / value['prepared_ref']['path']) == value['prepared_ref']
assert value['prepared_ref']['sha256'] == 'fe01bef395b10c5308d28ce006bc42fca6a7465d6847ddc1711586f449ab60ec'
assert not (Path(spec['output_root']) / 'execute').exists()
git = lock['git']['path']
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == cp['head']
assert hashlib.sha256(subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)).hexdigest() == prepared['git_status_sha256']
with (OUT / 'authorized-checkpoint.raw').open('xb') as stream:
    stream.write(cp_raw)
grant = {'status': 'ROOT_REGISTERED_EXECUTION_AUTHORIZED', 'actual_registration_completed': True,
    'executor': 'codex:/root', 'registration_checkpoint': 313, 'candidate': spec['candidate'],
    'spec_sha256': spec_pin['sha256'], 'runner_sha256': ref(runner)['sha256'],
    'output_root': spec['output_root'], 'work_root': spec['work_root'],
    'roster': value['finite_future_roster'], 'phases': ['execute'], 'prepared_sha256': value['prepared_ref']['sha256'],
    'scope_refs': [ref(scope, True), ref(OUT / 'authorized-checkpoint.raw', True)],
    'controller_refs': [ref(Path(__file__), True), ref(runner, True)],
    'product_test_cases_authorized_now': 29, 'MODEL_loopback_maximum': 4, 'external_paid_calls_authorized_now': 0,
    'source_acceptance': False, 'formal_increment': 0,
    'actual_prepared_SHA_bound': True}
grant_ref = save('authorization.execute.json', grant)
argv = [sys.executable, '-X', 'utf8', '-I', str(runner), '--phase', 'execute',
        '--authorization', str(OUT / 'authorization.execute.json'), '--authorization-sha256', grant_ref['sha256']]
public_names = {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'OS', 'PATHEXT', 'PATH', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE'}
env = {key: value for key, value in os.environ.items() if key.upper() in public_names}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
save('started.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'at': started,
    'scope': scope_ref, 'runner': ref(runner), 'launcher': ref(Path(__file__)), 'grant': grant_ref,
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
        'scope': scope_ref, 'runner': ref(runner), 'launcher': ref(Path(__file__)), 'grant': grant_ref,
        'stdout': ref(OUT / 'stdout.raw') if (OUT / 'stdout.raw').is_file() else None,
        'stderr': ref(OUT / 'stderr.raw') if (OUT / 'stderr.raw').is_file() else None,
        'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0})
print(json.dumps({'driver_actual_exit': child.returncode if child is not None else None,
    'wrapper_error': wrapper_error,
    'stderr_display_only': (OUT / 'stderr.raw').read_text(encoding='utf-8', errors='replace')[-2500:] if (OUT / 'stderr.raw').is_file() else None,
    'stdout_display_only': (OUT / 'stdout.raw').read_text(encoding='utf-8', errors='replace')[-2500:] if (OUT / 'stdout.raw').is_file() else None}, ensure_ascii=True), flush=True)
sys.exit(child.returncode if child is not None else 1)
