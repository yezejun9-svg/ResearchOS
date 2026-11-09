"""Root caller: retain original launcher bytes, first failure, and actual exit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
SCOPE_SHA = 'edec4df6c5f4fcce632008517adff4c4b2a82f64bc4715d87c8a53e7fd3e19c3'
GRANT_SHA = '26bda302fbb13193918ff58a2fc271f8e013e85cc8df4d98d2b0cc40a82bc010'

def need(ok, why):
    if not ok:
        raise RuntimeError(why)

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

need(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, 'Use -I -S -X utf8')
sys.dont_write_bytecode = True
scope_path = OUT / 'scope_registration.json'
scope_ref = pin(scope_path)
need(scope_ref['sha256'] == SCOPE_SHA, 'Actual reviewed full scope')
scope = json.loads(scope_path.read_bytes().decode('utf-8'))
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
grant_ref = pin(grant_path)
need(grant_ref['sha256'] == GRANT_SHA, 'Actual sealed unique grant')
launcher = scope['launcher_ref']
need(pin(launcher['path']) == launcher and launcher['sha256'] ==
     '0a958ae65c1f3cf5449b4b4f7b09257a515cc17691fd8ae1f99852057a140f11', 'Actual reviewed launcher')
need(Path(sys.executable).resolve() == Path(PYTHON).resolve(), 'Actual pinned Python')
need(pin(PYTHON)['sha256'] == scope['python_ref']['sha256'], 'Actual Python SHA')
env = dict(scope['public_environment'])
need(set(env) <= {'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}, 'Public environment only')
argv = [PYTHON, '-I', '-S', '-X', 'utf8', launcher['path'], str(scope_path), SCOPE_SHA,
        str(grant_path), GRANT_SHA]
save('root-launch.intent.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT),
    'scope_ref': scope_ref, 'grant_ref': grant_ref, 'caller_ref': pin(__file__), 'environment': env,
    'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0,
    'caller_OS_lifecycle_qualification': False,
    'launcher_owned_inner_timeout_seconds': 3600, 'caller_subprocess_timeout_seconds': 3900})
result = None
error = None
secondary = []
try:
    with (OUT / 'root-launch.stdout.raw').open('xb') as stdout, (OUT / 'root-launch.stderr.raw').open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                timeout=3900, check=False)
except BaseException as exc:
    error = {'error': repr(exc), 'traceback': traceback.format_exc()}
finally:
    raw_refs = {}
    for name in ('stdout', 'stderr'):
        try:
            raw_path = OUT / ('root-launch.' + name + '.raw')
            raw_refs[name + '_ref'] = pin(raw_path) if raw_path.is_file() else None
        except BaseException as exc:
            raw_refs[name + '_ref'] = None
            secondary.append({'stage': name + '-raw-reference', 'error': repr(exc)})
    observation = {'actor': 'codex:/root',
        'actual_launcher_native_exit': result.returncode if result else None,
        'caller_error': error, 'actual_outer_tool_exit': None, **raw_refs,
        'scope_ref': scope_ref, 'grant_ref': grant_ref, 'automatic_retry': False,
        'counter_reset': False, 'caller_OS_lifecycle_qualification': False,
        'formal_increment': 0, 'secondary': list(secondary)}
    try:
        save('root-launch.invocation.json', observation)
    except BaseException as exc:
        secondary.append({'stage': 'invocation-receipt', 'error': repr(exc)})
    if error is not None or secondary:
        sys.stderr.write(json.dumps({'first_cause': error,
            'actual_launcher_native_exit': result.returncode if result else None,
            'secondary': secondary, 'raw_refs': raw_refs,
            'automatic_retry': False, 'counter_reset': False}, ensure_ascii=False) + '\n')
print(json.dumps({'actual_launcher_native_exit': result.returncode if result else None,
                  'caller_error': error, 'secondary': secondary,
                  'scope_sha256': SCOPE_SHA, 'grant_sha256': GRANT_SHA}, ensure_ascii=False))
raise SystemExit(result.returncode if result is not None and error is None and not secondary else 1)
