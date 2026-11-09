"""Desktop58 Root caller: retain launcher bytes, first failure, and actual exit."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = None
REGISTRATION = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-dc00ad52f46c49acacc8058a58500820'
DESKTOP_RECEIPTS = ROOT / 'execution/v2.4/receipts/W13/W13-03'
AUTH_ROOT = DESKTOP_RECEIPTS / 'desktop58_finite_authorization_codex/dc00ad52f46c49acacc8058a58500820'
RUN_UUID = 'dc00ad52f46c49acacc8058a58500820'
PYTHON = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
PYTHON_SHA = 'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
LAUNCHER_SHA = 'a4b5d968cc1829971ada48f55743bb7f6cc790967f76c179ceca1cac978b2bf7'
SCOPE_SHA = None
GRANT_SHA = None

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
need(len(sys.argv) == 4, 'Root must supply actual scope SHA, grant SHA, and a fresh caller output directory')
SCOPE_SHA, GRANT_SHA = sys.argv[1:3]
for name, value in (('scope', SCOPE_SHA), ('grant', GRANT_SHA)):
    need(len(value) == 64 and all(c in '0123456789abcdef' for c in value),
         'Explicit actual ' + name + ' SHA')
OUT = Path(sys.argv[3])
need(OUT.is_absolute() and '..' not in OUT.parts and str(OUT.resolve()) == str(OUT), 'Canonical caller output')
need(OUT.is_relative_to(DESKTOP_RECEIPTS) and OUT != DESKTOP_RECEIPTS, 'Desktop receipt output only')
need(not OUT.is_relative_to(Path(__file__).resolve().parent) and
     not OUT.is_relative_to(REGISTRATION) and
     all(not OUT.is_relative_to(root) and not root.is_relative_to(OUT) for root in
         (AUTH_ROOT,
          DESKTOP_RECEIPTS / ('desktop58_finite_executor_codex/' + RUN_UUID),
          DESKTOP_RECEIPTS / ('desktop58_finite_launcher_codex/' + RUN_UUID),
          DESKTOP_RECEIPTS / ('desktop58_finite_grant_preflight_codex/' + RUN_UUID))),
     'Caller output must be separate from Root execution and preparation leaves')
need(OUT.is_dir() and not any(OUT.iterdir()), 'Root must separately allocate a new empty caller directory')
scope_path = REGISTRATION / 'scope_registration.json' 
scope_ref = pin(scope_path)
need(scope_ref['sha256'] == SCOPE_SHA, 'Actual reviewed full scope')
scope = json.loads(scope_path.read_bytes().decode('utf-8'))
need(scope['source_commit'] == 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'Current58 source only')
need(scope['registration_namespace'] == REGISTRATION.relative_to(ROOT).as_posix(), 'Fixed actual registration namespace')
need(scope['run_uuid'] == RUN_UUID and scope['execution_authorized'] is True and
     scope['preparation_only'] is False and scope['formal_increment'] == 0,
     'Actual registered Desktop58 scope only')
need(scope['inner_seconds'] == 7200 and scope['outer_seconds'] == 7500 and
     scope['cleanup_seconds'] == 5 and
     scope['controller_evidence_reserve_seconds'] == 60 and
     scope['launcher_evidence_reserve_seconds'] == 60,
     'Exact Root Desktop inner/outer/cleanup/evidence allocation')
need(Path(scope['new_authorization_root']) == AUTH_ROOT,
     'Fixed Root authorization allocation')
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
grant_ref = pin(grant_path)
need(grant_ref['sha256'] == GRANT_SHA, 'Actual sealed unique grant')
launcher = scope['launcher_ref']
need(pin(launcher['path']) == launcher and launcher['sha256'] ==
     LAUNCHER_SHA, 'Actual reviewed Desktop launcher')
need(Path(sys.executable).resolve() == Path(PYTHON).resolve(), 'Actual pinned Python')
python_ref = pin(PYTHON)
need(python_ref['sha256'] == PYTHON_SHA, 'Actual pinned Python SHA')
resource_ref = scope['resource_catalog_ref']
need(pin(resource_ref['path']) == resource_ref, 'Actual public resource catalog')
resources = json.loads(Path(resource_ref['path']).read_bytes().decode('utf-8'))
need(resources['tools']['python'] == python_ref, 'Desktop resource Python pin')
env = dict(scope['public_environment'])
need(set(env) <= {'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}, 'Public environment only')
argv = [PYTHON, '-I', '-S', '-X', 'utf8', launcher['path'], str(scope_path), SCOPE_SHA,
        str(grant_path), GRANT_SHA]
save('root-launch.intent.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT),
    'scope_ref': scope_ref, 'grant_ref': grant_ref, 'caller_ref': pin(__file__), 'environment': env,
    'automatic_retry': False, 'counter_reset': False, 'formal_increment': 0,
    'caller_OS_lifecycle_qualification': False,
    'launcher_owned_outer_budget_seconds': 7500, 'controller_inner_budget_seconds': 7200,
    'caller_subprocess_timeout_seconds': 7800})
result = None
error = None
secondary = []
try:
    with (OUT / 'root-launch.stdout.raw').open('xb') as stdout, (OUT / 'root-launch.stderr.raw').open('xb') as stderr:
        result = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                timeout=7800, check=False)
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
