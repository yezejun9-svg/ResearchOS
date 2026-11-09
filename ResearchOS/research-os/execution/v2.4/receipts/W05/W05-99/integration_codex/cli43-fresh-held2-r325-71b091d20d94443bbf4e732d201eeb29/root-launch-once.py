"""Root caller: retain original launcher bytes and actual exit, with no retry."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
SCOPE_SHA = 'c942ced8bc4e34668e74997a1950150816ee819298e54a448b588e0e3ea2eb20'
GRANT_SHA = '4358b6b1c494e33104aff066e4e07f12cec0b3029a95ed56f1be940500df9f7a'

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
try:
    with (OUT / 'root-launch.stdout.raw').open('xb') as stdout, (OUT / 'root-launch.stderr.raw').open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                timeout=3900, check=False)
except BaseException as exc:
    error = repr(exc)
    raise
finally:
    save('root-launch.invocation.json', {'actor': 'codex:/root',
        'actual_launcher_native_exit': result.returncode if result else None,
        'caller_error': error, 'actual_outer_tool_exit': None,
        'stdout_ref': pin(OUT / 'root-launch.stdout.raw'),
        'stderr_ref': pin(OUT / 'root-launch.stderr.raw'),
        'scope_ref': scope_ref, 'grant_ref': grant_ref, 'automatic_retry': False,
        'counter_reset': False, 'caller_OS_lifecycle_qualification': False, 'formal_increment': 0})
print(json.dumps({'actual_launcher_native_exit': result.returncode,
                  'invocation_ref': pin(OUT / 'root-launch.invocation.json'),
                  'scope_sha256': SCOPE_SHA, 'grant_sha256': GRANT_SHA}, ensure_ascii=False))
raise SystemExit(result.returncode)
