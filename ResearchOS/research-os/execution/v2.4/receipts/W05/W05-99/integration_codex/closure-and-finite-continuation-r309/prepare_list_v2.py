import ast
import hashlib
import json
from pathlib import Path

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


def change(code, old, new):
    assert code.count(old) == 1
    return code.replace(old, new, 1)


code = (OUT / 'list_replay.py').read_text(encoding='utf-8')
assert ref(OUT / 'list_replay.py')['sha256'] == '08f37eebc0beb0ea9d173d75958c2bac61fb86362db256edf2b5a1daec792003'
code = change(code, "assert scope_path == DRAFT / 'list_independent_scope.json'", "assert scope_path == DRAFT / 'list_independent_scope.v2.json'")
old = "    paths.update(Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module, '__file__', None) and Path(module.__file__).is_file())"
new = '''    for module in list(sys.modules.values()):
        for attribute in ('__file__', '__cached__'):
            name = getattr(module, attribute, None)
            if name and Path(name).is_file():
                paths.add(Path(name).resolve())'''
code = change(code, old, new)
begin = code.index('def run(name, argv, cwd=EXPORT, timeout=600, stdout_path=None):')
end = code.index('\n\ndef vector(paths):', begin)
new_run = '''def optional_row(path):
    path = Path(path)
    try:
        return {'exists': path.is_file(), 'ref': row(path) if path.is_file() else None}
    except OSError as error:
        return {'exists': None, 'ref': None, 'observation_error': repr(error)}


def run(name, argv, cwd=EXPORT, timeout=600, stdout_path=None):
    STATE['phase'] = name
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    stdout_path = Path(stdout_path) if stdout_path is not None else OUT / (name + '.stdout.raw')
    stderr_path = OUT / (name + '.stderr.raw')
    observed = {'actual_exit': None, 'timed_out': False, 'error': None, 'owned_child_pid': None,
        'creation_time_100ns': None, 'job_cleanup': None, 'resumed': False, 'stage': 'RUNNER_PRECALL'}
    wrapper_error = None
    try:
        with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
            observed = RUN_OWNED(argv, cwd, ENV, stdout, stderr, timeout)
    except BaseException as error:
        wrapper_error = {'error_type': type(error).__name__, 'message': str(error)}
    finally:
        save(name + '.invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(cwd),
            'environment': ENV, 'environment_policy': 'Explicit public allowlist only; no inherited provider/credential/private environment values',
            'started_at': started, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'process_observation': observed, 'wrapper_error': wrapper_error, 'actual_exit': observed['actual_exit'],
            'stdout': optional_row(stdout_path), 'stderr': optional_row(stderr_path), 'automatic_retry': False})
    cleanup = observed.get('job_cleanup') or {}
    if not (wrapper_error is None and observed.get('error') is None and observed.get('actual_exit') == 0
            and observed.get('timed_out') is False and observed.get('resumed') is True
            and all(cleanup.get(key) is True for key in ('kill_on_job_close_configured', 'assigned_before_resume',
                'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed')) and cleanup.get('errors') == []):
        raise RuntimeError(f'{name}: owned process or wrapper failure; first unexpected stop')
    return stdout_path.read_bytes()
'''
code = code[:begin] + new_run + code[end:]
code = change(code, "'GIT_OPTIONAL_LOCKS': '0', 'GOWORK': 'off', 'GOFLAGS': '', 'RESEARCHOS_SESSION_LIST_EVIDENCE': str(OUT / 'cases')}",
    "'GIT_OPTIONAL_LOCKS': '0', 'GOWORK': 'off', 'GOFLAGS': '-buildvcs=false', 'GOAMD64': 'v1', 'GOEXPERIMENT': '', 'GODEBUG': '',\n        'RESEARCHOS_GO': str(go), 'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,\n        'RESEARCHOS_SESSION_LIST_EVIDENCE': str(OUT / 'cases')}")
old_env = "    ENV = {key: value for key, value in os.environ.items() if key not in CLEARED and key.upper() not in {'PYTHONPATH', 'PYTHONOPTIMIZE'}}\n    ENV.update(OVERRIDES)"
new_env = '''    ENV = {key: os.environ[key] for key in ('OS', 'PATHEXT', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
        'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL', 'PROCESSOR_REVISION') if key in os.environ}
    system = Path(os.environ['SystemRoot'])
    ENV.update({'SystemRoot': str(system), 'WINDIR': str(system), 'ComSpec': str(system / 'System32/cmd.exe'),
        'USERPROFILE': str(local / 'temp/profile'), 'LOCALAPPDATA': str(local / 'temp/profile/AppData/Local'),
        'APPDATA': str(local / 'temp/profile/AppData/Roaming'),
        'PATH': os.pathsep.join([str(Path(go).parent), str(Path(git).parent),
            str(system / 'System32/WindowsPowerShell/v1.0'), str(system / 'System32')])})
    ENV.update(OVERRIDES)'''
code = change(code, old_env, new_env)
ast.parse(code)
with (OUT / 'list_replay.v2.py').open('xb') as stream:
    stream.write(code.encode('utf-8'))
scope = json.loads((OUT / 'list_independent_scope.json').read_bytes())
scope.update(runner_ref=ref(OUT / 'list_replay.v2.py'),
    prepared_amendment='Static-only: include actual __cached__ alongside Python source/DLL inputs, explicit public Go/OS env allowlist, finally preserve nullable native/wrapper evidence and require full ownedJob cleanup.',
    prior_draft_scope_ref=ref(OUT / 'list_independent_scope.json'), prior_draft_runner_ref=ref(OUT / 'list_replay.py'),
    environment_policy='Only recorded explicit public allowlist; GOEXPERIMENT empty, GOAMD64v1, GODEBUG empty, no private inherited env values.',
    owned_job_success='Requires resumed and kill_on_job_close_configured/assigned_before_resume/primary_exit_confirmed/job_idle_confirmed/handles_closed true and errors[].',
    Python_runtime_freeze='Actual __file__ and existing __cached__ files plus loaded DLLs. dont_write_bytecode prevents writes only.')
scope_ref = save('list_independent_scope.v2.json', scope)
audit_ref = save('list-v2-static-amendment.json', {'decision': 'STATIC_PREPARATION_AMENDMENT_NOT_ACTUAL_FAILURE',
    'runner': ref(OUT / 'list_replay.v2.py'), 'scope': scope_ref, 'original_drafts_preserved': True,
    'compiler_export_native_cases_SQL_HTTP_SDK_paid_private_calls': 0, 'counter_delta': 0,
    'same14_scope': True, 'same_source_exact2': True, 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'runner': ref(OUT / 'list_replay.v2.py'), 'scope': scope_ref, 'audit': audit_ref}, ensure_ascii=True))
