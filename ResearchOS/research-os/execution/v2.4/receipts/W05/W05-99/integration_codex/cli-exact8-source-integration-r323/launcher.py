"""One Root launch with sealed first-failure and raw child exits, never a retry."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
from pathlib import Path
import traceback
import types
import uuid

ROOT = Path('D:/作品集/ResearchOS/research-os')
REG = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-exact8-source-integration-r323'
SCOPE_SHA = '52d8f686f07a606afaeb64eccca26f53edb2872bf93fa595132fd6afc067da71'
PRODUCER_SHA = '7c6b8877e523ad727cb8773651452e13cae2ac940ef28086639890f0bf829f6a'
CONTROLLER_SHA = 'f3301a8fad305ce207afa0595d0071c91842f9258ad3b2e58ddb709e1562922b'
HELPER_SHA = '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'
LOCK_SHA = '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663'
LOG_PARENT = ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_root_launcher_codex'
FLAGS = ['-I', '-S', '-X', 'utf8']

def check(value, message):
    if not value:
        raise RuntimeError(message)

def safe(p):
    p = Path(p)
    check(p.is_absolute() and '..' not in p.parts and p.resolve() == p.absolute(), 'Absolute no-alias path')
    for q in [p] + list(p.parents):
        if os.path.lexists(q):
            st = os.lstat(q)
            check(not q.is_symlink() and not getattr(st, 'st_file_attributes', 0) & 0x400, 'Reparse/symlink path')
    return p

def file_ref(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    p = safe(p)
    raw = p.read_bytes()
    ref = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    check(expected is None or ref['sha256'] == expected, 'Input hash mismatch ' + str(p))
    return ref

def save(out, name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (out / name).open('xb') as stream:
        stream.write(raw)
    return file_ref(out / name)

def complete(result):
    check(isinstance(result, dict) and result.get('actual_exit') == 0 and result.get('error') is None and
        result.get('timed_out') is False and result.get('resumed') is True, 'Owned child failed')
    cleanup = result.get('job_cleanup', {})
    check(cleanup.get('errors') == [] and all(cleanup.get(key) is True for key in [
        'unnamed_exclusive_job', 'assigned_before_resume', 'kill_on_job_close_configured',
        'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed']), 'Owned Job incomplete')

def main():
    out = None
    stage = 'SAFE_LOG_INITIALIZATION'
    first = None
    last_result = None
    helper = None
    runtime_spec = None
    try:
        # Before a safe log exists, an OS/path failure falls back to original tool stderr.
        safe(LOG_PARENT)
        LOG_PARENT.mkdir(exist_ok=True)
        candidate = safe(LOG_PARENT / uuid.uuid4().hex)
        candidate.mkdir(exist_ok=False)
        out = candidate
        save(out, 'started.json', {'actual_argv': sys.argv, 'actual_interpreter': sys.executable,
            'source_writes': 0, 'automatic_retry': False})
        stage = 'FLAGS_AND_FIXED_INPUTS'
        check(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize, 'Python flags')
        check(Path.cwd().resolve() == ROOT.resolve(), 'Main cwd')
        scope_ref = file_ref(REG / 'scope_registration.json', SCOPE_SHA)
        scope = json.loads(Path(scope_ref['path']).read_bytes())
        check(scope['expected_registration'] == [323, 151, 425], 'Fixed registration')
        lock_ref = file_ref(ROOT / 'execution/toolchains/locked.json', LOCK_SHA)
        tools = json.loads(Path(lock_ref['path']).read_bytes())['tools']
        check(Path(sys.executable).resolve() == Path(tools['python']['path']).resolve(), 'Pinned actual Python')
        python_ref = file_ref(sys.executable, tools['python']['sha256'])
        producer_ref = file_ref(REG / 'grant-producer.py', PRODUCER_SHA)
        controller_ref = file_ref(scope['controller_ref']['path'], CONTROLLER_SHA)
        helper_ref = file_ref(scope['owned_process_helper_ref']['path'], HELPER_SHA)
        catalog_ref = file_ref(scope['runtime_resources_ref']['path'], scope['runtime_resources_ref']['sha256'])
        helper = types.ModuleType('main38_root_launcher_owned_job')
        helper.__file__ = helper_ref['path']
        exec(compile(Path(helper_ref['path']).read_bytes(), helper_ref['path'], 'exec'), helper.__dict__)
        # Prime lazy URI support before the point-in-time before measurement.
        Path(__file__).resolve().as_uri()
        catalog = json.loads(Path(catalog_ref['path']).read_bytes())['files']
        runtime_spec = {os.path.normcase(str(Path(row['path']).absolute())): row for row in catalog}
        for row in [file_ref(Path(__file__)), helper_ref]:
            runtime_spec[os.path.normcase(str(Path(row['path']).absolute()))] = row

        def runtime(name):
            paths = set(helper.runtime_resource_paths()) | {sys.executable}
            for module in list(sys.modules.values()):
                for key in ['__file__', '__cached__']:
                    p = getattr(module, key, None)
                    if isinstance(p, str) and Path(p).is_file():
                        paths.add(p)
            rows = []
            for p in sorted(paths):
                expected = runtime_spec.get(os.path.normcase(str(Path(p).absolute())))
                check(expected is not None, 'Unpinned actual launcher runtime')
                actual = file_ref(p, expected['sha256'])
                check(actual['bytes'] == expected['bytes'], 'Actual runtime size')
                rows.append(actual)
            save(out, name + '.json', {'files': rows, 'measurement': 'POINT_IN_TIME_NOT_LIFECYCLE',
                'transient_load_absence_proven': False})

        env = {key: value for key, value in os.environ.items() if key.upper() in
            ['SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'COMSPEC', 'PATHEXT', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE']}
        env.update(PATH='C:/Windows/System32;C:/Windows', PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
        runtime('runtime.before')
        save(out, 'inputs.before.json', [scope_ref, lock_ref, python_ref, producer_ref, controller_ref, helper_ref, catalog_ref])

        def owned(name, argv, timeout):
            nonlocal last_result, stage
            stage = name
            last_result = None
            error = None
            save(out, name + '.invocation.json', {'argv': argv, 'cwd': str(ROOT), 'environment': env,
                'timeout_seconds': timeout, 'owned_cleanup_seconds': 5, 'automatic_retry': False})
            try:
                with (out / (name + '.stdout.raw')).open('xb') as stdout, (out / (name + '.stderr.raw')).open('xb') as stderr:
                    last_result = helper.run_owned(argv, str(ROOT), env, stdout, stderr, timeout)
            except BaseException as exc:
                error = repr(exc)
                raise
            finally:
                save(out, name + '.owned-result.json', {'result': last_result, 'wrapper_error': error,
                    'actual_native_exit': last_result.get('actual_exit') if isinstance(last_result, dict) else None})
            complete(last_result)

        owned('grant-preflight', [sys.executable] + FLAGS + [producer_ref['path']], 600)
        returned = json.loads((out / 'grant-preflight.stdout.raw').read_bytes())
        grant = returned['grant_ref']
        grant_path = safe(ROOT / grant['path']) if not Path(grant['path']).is_absolute() else safe(grant['path'])
        check(grant_path.parent.name == scope['operation_uuid'] and grant_path.name == 'grant.json', 'Exact once grant path')
        check(grant_path.parent.parent == ROOT / 'execution/v2.4/receipts/W05/W05-99/cli_exact8_integration_root_grant_codex', 'Grant namespace')
        check(file_ref(grant_path, grant['sha256'])['bytes'] == grant['bytes'], 'Returned grant bytes')
        stage = 'PRE_CONTROLLER_INPUT_RECHECK'
        for expected in [scope_ref, lock_ref, python_ref, producer_ref, controller_ref, helper_ref, catalog_ref]:
            check(file_ref(expected['path'], expected['sha256'])['bytes'] == expected['bytes'], 'Pre-controller input drift')
        owned('source-only-integration', [sys.executable] + FLAGS + [controller_ref['path'],
            '--scope', scope_ref['path'], '--scope-sha256', scope_ref['sha256'],
            '--grant', str(grant_path), '--grant-sha256', grant['sha256']], 1200)
        runtime('runtime.after')
        save(out, 'completed.json', {'state': 'ROOT_ONCE_LAUNCH_FINISHED_PENDING_INDEPENDENT_EVIDENCE_REVIEW',
            'scope_ref': scope_ref, 'grant_ref': grant, 'actual_controller_native_exit': 0,
            'source_apply_attempts_max': 1, 'source_commit_attempts_max': 1, 'Go_compile_test_SQL_HTTP_models': 0, 'formal_increment': 0})
    except BaseException as exc:
        first = {'stage': stage, 'error': repr(exc), 'traceback': traceback.format_exc(),
            'actual_native_exit': last_result.get('actual_exit') if isinstance(last_result, dict) else None,
            'controller_outer_exit': 1, 'automatic_retry': False, 'counter_reset': False,
            'rollback_or_reset': False, 'formal_increment': 0}
        if out is not None:
            try:
                save(out, 'failure.origin.json', first)
            except BaseException as save_error:
                print(json.dumps({'first_failure': first, 'save_error': repr(save_error)}, ensure_ascii=True), file=sys.stderr)
        else:
            print(json.dumps({'first_failure': first, 'file_capture_unavailable': 'Safe log initialization failed; original tool stderr is the retained record.'}, ensure_ascii=True), file=sys.stderr)
    finally:
        if out is not None:
            try:
                entries = [file_ref(p) for p in sorted(out.iterdir()) if p.is_file()]
                save(out, 'manifest.json', {'entries': entries, 'self_excluded': True, 'first_failure': first})
            except BaseException as exc:
                print(json.dumps({'stage': 'SAVE_MANIFEST', 'error': repr(exc)}, ensure_ascii=True), file=sys.stderr)
                first = first or {'stage': 'SAVE_MANIFEST', 'error': repr(exc)}
        print(json.dumps({'output_root': str(out) if out is not None else None,
            'actual_outer_exit': 0 if first is None else 1, 'first_failure': first}, ensure_ascii=True))
    return 0 if first is None else 1

if __name__ == '__main__':
    raise SystemExit(main())
