import sys
sys.dont_write_bytecode = True

import base64
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
DRAFT = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r309-534857db-public-jev'
EXPORT = ROOT / '.local/independent-session-list-r309-534857db-public-jev'
CANDIDATE = '534857db99fa5e694987f877af74c322eaa2a0b3'
BASE = '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
NAMES = ['NullContext', 'OwnedContext', 'ContextNotResultFilter', 'ExactReplayAfterCommit', 'ChangedPayloadConflict', 'ChangedSIDConflict', 'CrossProjectContext', 'ForeignPrincipalContext', 'ForeignPrincipalNullList', 'UnknownContext', 'ProjectGrantDenied', 'CrossProjectCursor', 'CrossPrincipalCursor', 'MalformedRequest']
SOURCES = {
    'internal/domain/client_protocol_sessions.go': '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3',
    'internal/api/v2_sessions_test.go': 'e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0',
}
PUBLIC_JEV = {'evaluation/holdout/jev/generate_other.go': {'git_blob': 'a0edc3fd43095520d2b5a77a4d1027e41c5ef147', 'sha256': '2afa6e97311ece753df8af74bd68de7ded3445d8a40bfa988f8ba17baadd5bf4', 'bytes': 186}, 'evaluation/holdout/jev/generate_windows.go': {'git_blob': '46bb72987cddbeeafb296dce03b2f160f5ec8c85', 'sha256': 'c02188ddd6c831ef0dc6b7af97b7667a05fa50e62f074d4b7ff709a0607baab1', 'bytes': 988}, 'evaluation/holdout/jev/generator.go': {'git_blob': '5be93941e7d0b8c3d22c60649f6dfe7689bcedd0', 'sha256': '1dc3d5154fe713155944b9ce761cd0bfc6a1fc4d92f34d0bac7ccd37df8aa523', 'bytes': 12685}, 'evaluation/holdout/jev/rubric.go': {'git_blob': '11bbedbcb5b621d6d0f0f8a2d2dbc38cb577eb8f', 'sha256': '10f3cc145780b4934e005db9bfb5ca7501a152f1caee89aee8732cc5eaf6e2ae', 'bytes': 2916}, 'evaluation/holdout/jev/truth.go': {'git_blob': '43e9c19fbbf98fc0ed790ec77d001b8182e8c9d7', 'sha256': 'b41064e0890811113e249a8fedc3a3ae153a5f71fa868e4763ffa2ad76cc4ca2', 'bytes': 4804}}
RESOURCE_PLAN_REF = {'path': 'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json', 'sha256': '598adac08e7c638bda6b783a78dc8541847b8e48054e196dd6da6eb728319bc2', 'bytes': 1573436}
STATE = {'phase': 'NOT_STARTED', 'frozen_inputs': [], 'completed_cases': []}
OWN_OUT_CREATED = False


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def save(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return row(path)


def load(path):
    return json.loads(Path(path).read_bytes())


def run(name, argv, cwd=EXPORT, timeout=600, stdout_path=None):
    STATE['phase'] = name
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    stdout_path = Path(stdout_path) if stdout_path is not None else OUT / (name + '.stdout.raw')
    with stdout_path.open('xb') as stdout, (OUT / (name + '.stderr.raw')).open('xb') as stderr:
        observed = RUN_OWNED(argv, cwd, ENV, stdout, stderr, timeout)
    save(name + '.invocation.json', {'actor': 'codex:/root', 'argv': argv, 'cwd': str(cwd),
        'environment_overrides': OVERRIDES, 'cleared_RESEARCHOS_environment_names': CLEARED,
        'started_at': started, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'process_observation': observed, 'actual_exit': observed['actual_exit'], 'stdout': row(stdout_path),
        'stderr': row(OUT / (name + '.stderr.raw')), 'automatic_retry': False})
    if observed['error'] is not None or observed['timed_out'] or observed['actual_exit'] != 0:
        raise RuntimeError(f'{name}: observed owned process {observed}; first unexpected stop')
    return stdout_path.read_bytes()


def vector(paths):
    return [row(path) for path in sorted(set(Path(p).resolve() for p in paths))]


def check_vector(before):
    after = [row(item['path']) for item in before]
    if after != before:
        raise RuntimeError('Frozen source/tool/generated/archive/exe input drift')
    return after


def runtime_paths():
    paths = {Path(path).resolve() for path in PROCESS_HELPER.runtime_resource_paths()}
    paths.update(Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module, '__file__', None) and Path(module.__file__).is_file())
    paths.update(path.resolve() for path in Path(sys.executable).parent.glob('python*.dll') if path.is_file())
    return paths


def check_stage(stem, stage, freeze):
    frozen = {item['path']: item for item in freeze}
    runtime = vector(runtime_paths())
    save(stem + '.' + stage + '.runtime.json', runtime)
    if any(frozen.get(item['path']) != item for item in runtime):
        raise RuntimeError('Unfrozen runtime input at ' + stem + ':' + stage)
    save(stem + '.' + stage + '.inputs.json', check_vector(freeze))


def typed_cells(values):
    cells = []
    for typ, value in zip(values[::2], values[1::2]):
        if typ == 'null':
            payload = ''
        elif typ == 'integer':
            payload = str(value)
        elif typ == 'real':
            payload = float(value).hex()
        elif typ == 'text':
            payload = base64.b64encode(value.encode('utf-8')).decode()
        elif typ == 'blob':
            payload = base64.b64encode(value).decode()
        else:
            raise RuntimeError('Unknown SQLite storage class')
        cells.append((typ, payload))
    return tuple(cells)


def canonical_saved_cells(serialized):
    pairs = json.loads(serialized)
    return tuple((typ, float(payload).hex() if typ == 'real' else payload) for typ, payload in pairs)


def check_closed(directory):
    database = directory / 'closed.sqlite'
    before = row(database)
    assert not Path(str(database) + '-wal').exists() and not Path(str(database) + '-shm').exists()
    recorded = load(directory / 'closed.rows.json')
    assert recorded == load(directory / 'post-open.rows.json')
    connection = sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        schema = [list(item) for item in connection.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_schema ORDER BY type,name')]
        assert Counter(tuple(item) for item in schema) == Counter(tuple(json.loads(item)) for item in recorded['schema'])
        tables = [item[0] for item in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
        assert set(tables) == set(recorded['tables']) == set(recorded['columns'])
        table_counts = {}
        for name in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            columns = [list(item) for item in connection.execute('PRAGMA table_xinfo(' + quoted + ')')]
            assert Counter(tuple(item) for item in columns) == Counter(tuple(json.loads(item)) for item in recorded['columns'][name])
            names = ['"' + item[1].replace('"', '""') + '"' for item in columns]
            expressions = ','.join(value for name in names for value in ['typeof(' + name + ')', name])
            actual = Counter(typed_cells(values) for values in connection.execute('SELECT ' + expressions + ' FROM ' + quoted))
            expected = Counter(canonical_saved_cells(item) for item in recorded['tables'][name])
            assert actual == expected
            table_counts[name] = sum(actual.values())
    finally:
        connection.close()
    assert row(database) == before
    proof = load(directory / 'closed-proof.json')
    assert proof['closed_copy_sha256'] == before['sha256']
    assert proof['all_table_schema_multisets_equal'] is True and proof['closed_copy_bytes_unchanged_by_read'] is True
    assert proof['case_failed'] is False and proof['SDK_worker_model_external_paid'] == 0
    return {'database': before, 'independent_python_sqlite_version': sqlite3.sqlite_version,
        'schema_all_columns_all_typed_row_multisets_equal': True, 'table_counts': table_counts,
        'readonly_bytes_unchanged': True, 'rowid_not_separately_exported': True}


def check_wire(directory, name):
    count = 0
    for request_meta in sorted(directory.glob('http-*.request.json')):
        stem = request_meta.name.removesuffix('.request.json')
        request = load(request_meta)
        response = load(directory / (stem + '.response.json'))
        for kind, meta in [('request', request), ('response', response)]:
            raw = (directory / (stem + '.' + kind + '.raw')).read_bytes()
            assert meta['bytes'] == len(raw) and meta['sha256'] == hashlib.sha256(raw).hexdigest()
        count += 1
    assertions = load(directory / 'assertions.json')
    assert assertions['case'] == name and assertions['all_assertions_reached'] is True
    proof = load(directory / 'closed-proof.json')
    assert 0 < count == assertions['HTTP_calls_including_setup'] == proof['HTTP_calls_including_setup'] <= 16
    journals = sorted(directory.glob('journal-*.json'))
    for journal_path in journals:
        journal = load(journal_path)
        number = int(journal_path.stem.split('-')[1])
        raw = (directory / f'http-{number:02d}.request.raw').read_bytes()
        response_raw = (directory / f'http-{number:02d}.response.raw').read_bytes()
        envelope = json.loads(raw)
        stored = json.loads(journal['body'])
        header = json.loads(journal['headers'])
        assert base64.b64decode(header['raw_envelope_base64'], validate=True) == raw
        assert stored == json.loads(response_raw)
        assert journal['command_id'] == envelope['command_id'] == stored['command_id']
        assert journal['project'] == envelope['project_id'] and journal['method'] == envelope['method'] == stored['method'] == 'session.list'
        assert stored['session_id'] == envelope['session_id']
        assert stored['protocol_version'] == envelope['protocol_version'] == 'researchos-client/2'
        assert stored['revision'] is None
    if name in ['ProjectGrantDenied', 'MalformedRequest']:
        assert len(journals) == 0
    else:
        assert len(journals) == 1
    return {'HTTP_calls_including_setup': count, 'actual_raw_wire_hashes_checked': True,
        'original_committed_identity_and_replay_journal_checked': True,
        'full_public_Go_schema_and_domain_hash_validation': 'unchanged native assertions, not reimplemented by Python'}


def main():
    global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED, PROCESS_HELPER
    assert len(sys.argv) == 3
    scope_path = Path(sys.argv[1]).resolve()
    assert scope_path == DRAFT / 'list_independent_scope.json' and sha(scope_path) == sys.argv[2]
    scope = load(scope_path)
    assert scope['source_commit'] == CANDIDATE and scope['owner'] == 'codex:/root'
    assert scope['runner_ref']['sha256'] == sha(Path(__file__))
    assert scope['ordered_cases'] == NAMES and scope['source_paths_sha256'] == SOURCES
    helper_path = (ROOT / scope['owned_process_helper_ref']['path']).resolve()
    assert scope['owned_process_helper_ref']['sha256'] == sha(helper_path)
    helper_spec = importlib.util.spec_from_file_location('researchos_root_owned_windows_process', helper_path)
    helper_module = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helper_module)
    RUN_OWNED = helper_module.run_owned
    PROCESS_HELPER = helper_module
    # Pure local URI conversion loads lazy standard-library modules before any input freeze.
    (ROOT / '__pure_uri_preload_no_file_access__').as_uri()
    cp = load(ROOT / 'execution/v2.4/checkpoint.json')
    assert cp['revision'] >= 309
    pin = cp['work_in_progress']['session_list_identity_independent_scope_ref']
    assert (ROOT / pin['path']).resolve() == scope_path and pin['sha256'] == sys.argv[2]
    assert cp['work_in_progress']['session_list_identity_source_ready'] is False
    assert not OUT.exists() and not EXPORT.exists()
    lock_path = ROOT / 'execution/toolchains/locked.json'
    lock = load(lock_path)['tools']
    for key in ['python', 'git', 'go']:
        assert sha(lock[key]['path']) == lock[key]['sha256']
    assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
    go, git = lock['go']['path'], lock['git']['path']
    goroot = Path(go).resolve().parent.parent
    OUT.mkdir(parents=True)
    OWN_OUT_CREATED = True
    EXPORT.mkdir(parents=True)
    local = EXPORT / '.local'
    for name in ['gocache', 'gotmp', 'temp']:
        (local / name).mkdir(parents=True)
    OVERRIDES = {'GOROOT': str(goroot), 'GOPATH': str(ROOT / '.local/gopath'), 'GOMODCACHE': str(ROOT / '.local/gopath/pkg/mod'),
        'GOCACHE': str(local / 'gocache'), 'GOTMPDIR': str(local / 'gotmp'), 'TEMP': str(local / 'temp'), 'TMP': str(local / 'temp'),
        'GOTOOLCHAIN': 'local', 'GOENV': 'off', 'GOPROXY': 'off', 'GOSUMDB': 'off', 'CGO_ENABLED': '0', 'GOOS': 'windows', 'GOARCH': 'amd64',
        'GIT_OPTIONAL_LOCKS': '0', 'GOWORK': 'off', 'GOFLAGS': '', 'RESEARCHOS_SESSION_LIST_EVIDENCE': str(OUT / 'cases')}
    CLEARED = sorted(key for key in os.environ if key.upper().startswith('RESEARCHOS_'))
    ENV = {key: value for key, value in os.environ.items() if key not in CLEARED and key.upper() not in {'PYTHONPATH', 'PYTHONOPTIMIZE'}}
    ENV.update(OVERRIDES)
    save('scope.original.json', scope)
    delta = run('candidate-source-delta', [git, 'diff-tree', '--no-commit-id', '--name-only', '-r', CANDIDATE], ROOT).decode().splitlines()
    assert set(delta) == set(SOURCES) and len(delta) == 2
    assert run('candidate-parent', [git, 'rev-parse', CANDIDATE + '^'], ROOT).decode().strip() == BASE
    tree = run('public-tree', [git, 'ls-tree', '-r', '-z', CANDIDATE], ROOT)
    exports = []
    for item in tree.split(b'\0'):
        if not item:
            continue
        info, name = item.split(b'\t', 1)
        mode, kind, blob = info.decode().split()
        name = name.decode('utf-8')
        if name not in PUBLIC_JEV and name not in ['go.mod', 'go.sum', 'VERSION'] and not name.startswith(('adapters/', 'internal/', 'migrations/', 'spec/', 'apps/cli/', 'tests/', 'contracts/', 'bootstrap/')):
            continue
        assert kind == 'blob' and mode in ['100644', '100755']
        if name in PUBLIC_JEV:
            assert blob == PUBLIC_JEV[name]['git_blob']
        destination = (EXPORT / name).resolve()
        assert destination.is_relative_to(EXPORT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        run(f'git-export-{len(exports) + 1:04d}', [git, 'cat-file', 'blob', blob], ROOT, 30, destination)
        exports.append({'relative_path': name, 'git_blob': blob, 'mode': mode, **row(destination)})
    save('public-source-export.json', exports)
    for name, pin in PUBLIC_JEV.items():
        actual = row(EXPORT / name)
        assert actual['sha256'] == pin['sha256'] and actual['bytes'] == pin['bytes']
    save('public-JEV-classification.json', {'resources': PUBLIC_JEV, 'classification': 'Previously approved generic public Go compiler sources; no private truth/qualification data or test generator execution', 'plan_ref': RESOURCE_PLAN_REF})
    for name, expected in SOURCES.items():
        assert sha(EXPORT / name) == expected
    old_test = run('protected-base-test', [git, 'show', BASE + ':internal/api/v2_sessions_test.go'], ROOT, 30)
    marker = b'// Only the host binding port'
    protected = old_test[old_test.index(marker):]
    assert hashlib.sha256(protected).hexdigest() == 'c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1'
    assert (EXPORT / 'internal/api/v2_sessions_test.go').read_bytes().split(marker, 1)[1].startswith(protected[len(marker):])
    initial_paths = {Path(item['path']) for item in exports}
    plan_path = ROOT / RESOURCE_PLAN_REF['path']
    assert sha(plan_path) == RESOURCE_PLAN_REF['sha256']
    public_plan = load(plan_path)
    for pin in public_plan['external_tools_modules_stdlib']:
        actual = row(pin['path'])
        assert actual['sha256'] == pin['sha256'] and actual['bytes'] == pin['bytes']
        initial_paths.add(Path(pin['path']))
    for directory in [goroot / 'src', goroot / 'pkg/tool', goroot / 'lib']:
        initial_paths.update(path for path in directory.rglob('*') if path.is_file())
    initial_paths.update([Path(lock[key]['path']) for key in ['python', 'git', 'go']])
    initial_paths.update([Path(go).parent / 'gofmt.exe', Path(__file__), helper_path, scope_path, lock_path, plan_path])
    initial_paths.update(runtime_paths())
    initial_freeze = vector(initial_paths)
    STATE['frozen_inputs'] = initial_freeze
    save('inputs.before_Go_tools.json', initial_freeze)
    run('readonly-gofmt', [str(Path(go).parent / 'gofmt.exe'), '-l', *[str(EXPORT / name) for name in SOURCES]])
    assert (OUT / 'readonly-gofmt.stdout.raw').read_bytes() == b''
    run('go-version', [go, 'version'])
    raw = run('go-list', [go, 'list', '-deps', '-test', '-compiled', '-json', './internal/api']).decode('utf-8')
    decoder, position, packages = json.JSONDecoder(), 0, []
    while position < len(raw):
        while position < len(raw) and raw[position].isspace():
            position += 1
        if position == len(raw):
            break
        package, position = decoder.raw_decode(raw, position)
        assert not package.get('Error') and not package.get('DepsErrors')
        packages.append(package)
    save('inputs.after_Go_list.json', check_vector(initial_freeze))
    inputs = set(initial_paths)
    generated_advertised = []
    fields = ['GoFiles', 'CgoFiles', 'CompiledGoFiles', 'CFiles', 'CXXFiles', 'MFiles', 'HFiles', 'FFiles', 'SFiles', 'SwigFiles', 'SwigCXXFiles', 'SysoFiles', 'EmbedFiles', 'TestGoFiles', 'XTestGoFiles', 'TestEmbedFiles', 'XTestEmbedFiles']
    for package in packages:
        for field in fields:
            for name in package.get(field, []):
                path = Path(name)
                if not path.is_absolute():
                    path = Path(package['Dir']) / path
                path = path.resolve()
                if path.is_file():
                    inputs.add(path)
                elif field == 'CompiledGoFiles':
                    assert path.is_relative_to(local)
                    generated_advertised.append(str(path))
                else:
                    raise RuntimeError('Missing actual dependency input: ' + str(path))
        if package.get('Module', {}).get('GoMod'):
            inputs.add(Path(package['Module']['GoMod']))
    for directory in [goroot / 'src', goroot / 'pkg/tool', goroot / 'lib']:
        inputs.update(path for path in directory.rglob('*') if path.is_file())
    inputs.update(Path(lock[key]['path']) for key in ['python', 'git', 'go'])
    inputs.update([Path(go).parent / 'gofmt.exe', Path(__file__), helper_path, scope_path, lock_path])
    # Freeze actual imported Python source/extensions and its interpreter DLLs, without guessed module paths.
    if hasattr(helper_module, 'runtime_resource_paths'):
        inputs.update(Path(path) for path in helper_module.runtime_resource_paths())
    inputs.update(Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module, '__file__', None) and Path(module.__file__).is_file())
    inputs.update(path for path in Path(sys.executable).parent.glob('python*.dll') if path.is_file())
    save('generated-advertised.json', {'paths': generated_advertised, 'classification': 'Own new cache generated testmain/compiledGoFiles; never mislabeled Git source'})
    before = vector(inputs)
    STATE['frozen_inputs'] = before
    save('inputs.before_compile.json', before)
    executable = OUT / 'session-list-api.test.exe'
    run('compile', [go, 'test', '-c', '-work', '-x', '-o', str(executable), './internal/api'])
    match = re.search(r'^WORK=(.+)$', (OUT / 'compile.stderr.raw').read_text(encoding='utf-8'), re.M)
    assert match is not None
    work = Path(match.group(1).strip()).resolve()
    assert work.is_relative_to(local / 'gotmp')
    artifacts = {path.resolve() for path in work.rglob('*') if path.is_file()}
    importcfg_refs = []
    for path in sorted(artifacts):
        if path.name == '_testmain.go' or path.name.startswith('importcfg'):
            copy = OUT / 'generated' / path.relative_to(work)
            copy.parent.mkdir(parents=True, exist_ok=True)
            with copy.open('xb') as stream:
                stream.write(path.read_bytes())
            inputs.add(copy)
            if path.name.startswith('importcfg'):
                for line in path.read_text(encoding='utf-8').splitlines():
                    if line.startswith('packagefile '):
                        package, archive = line[len('packagefile '):].split('=', 1)
                        archive_path = Path(archive.replace('$WORK', str(work))).resolve()
                        assert archive_path.is_file()
                        inputs.add(archive_path)
                        importcfg_refs.append({'importcfg': str(path), 'package': package, 'archive': row(archive_path)})
    save('actual-importcfg-packagefile-refs.json', importcfg_refs)
    generated_mains = list((OUT / 'generated').rglob('_testmain.go'))
    assert len(generated_mains) == 1 and 'TestSessionListHTTPOriginalContextIdentity' in generated_mains[0].read_text(encoding='utf-8')
    save('inputs.after_compile.json', check_vector(before))
    save('compiled_WORK_vector.json', vector(artifacts))
    run('exe-buildinfo', [go, 'version', '-m', str(executable)])
    inputs.update(artifacts)
    inputs.add(executable)
    inputs.update(runtime_paths())
    freeze = vector(inputs)
    STATE['frozen_inputs'] = freeze
    save('inputs.before_first_case.json', freeze)
    results = []
    total_calls = 0
    for index, name in enumerate(NAMES):
        stem = f'case-{index + 1:02d}'
        check_stage(stem, 'before_native', freeze)
        run(stem, [str(executable), '-test.run', '^TestSessionListHTTPOriginalContextIdentity$/^' + name + '$', '-test.v', '-test.failfast', '-test.timeout=150s'], EXPORT / 'internal/api', 180)
        check_stage(stem, 'after_native', freeze)
        stdout = (OUT / (stem + '.stdout.raw')).read_text(encoding='utf-8')
        assert '--- FAIL:' not in stdout and '--- SKIP:' not in stdout
        assert '--- PASS: TestSessionListHTTPOriginalContextIdentity/' + name + ' (' in stdout
        assert '--- PASS: TestSessionListHTTPOriginalContextIdentity (' in stdout
        assert len(re.findall(r'^\s*--- PASS: TestSessionListHTTPOriginalContextIdentity/', stdout, re.M)) == 1
        directory = OUT / 'cases' / ('TestSessionListHTTPOriginalContextIdentity__' + name)
        db_check = check_closed(directory)
        wire_check = check_wire(directory, name)
        check_stage(stem, 'after_fixture_proofs', freeze)
        total_calls += wire_check['HTTP_calls_including_setup']
        assert total_calls <= 224
        result = {'id': f'L{index + 1:02d}', 'leaf': name, 'actual_native_exit': 0,
            'status': 'PASS_DEVELOPMENT_FIXTURE_ONLY', 'database_check': db_check, 'wire_check': wire_check}
        save(stem + '.independent-proof.json', result)
        results.append(result)
        STATE['completed_cases'] = [result['leaf'] for result in results]
        print(json.dumps({'case': name, 'actual_native_exit': 0, 'independent_DB_wire': True}, ensure_ascii=True), flush=True)
    save('inputs.after_cases.json', check_vector(freeze))
    save('result.json', {'candidate': CANDIDATE, 'independent_actor': 'codex:/root', 'cases': results,
        'native_case_invocations': len(results), 'PASS_leaves': len(results), 'SKIP': 0, 'input_count': len(freeze),
        'input_drift': 0, 'actual_HTTP_calls_including_setup': total_calls, 'SDK_worker_model_external_paid_private': 0,
        'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
        'rowid_limit': 'all declared columns and typed row multisets; implicit rowid is not separately exported by these fixtures',
        'new_executable': row(executable), 'whole_compiler_WORK_path': str(work)})
    print(json.dumps({'status': 'NONAUTHOR_FINITE14_COMPLETE_PENDING_ROOT_REGISTRATION', 'leaves': len(results), 'HTTP_calls': total_calls, 'inputs': len(freeze)}, ensure_ascii=True))


try:
    main()
except BaseException as error:
    if OWN_OUT_CREATED:
        observations = []
        for expected in STATE['frozen_inputs']:
            path = Path(expected['path'])
            try:
                actual = row(path)
                observations.append({'before': expected, 'actual': actual, 'equal': actual == expected})
            except OSError as unreadable:
                observations.append({'before': expected, 'actual': None, 'error': repr(unreadable)})
        save('inputs.after_failure.json', {'phase': STATE['phase'], 'observations': observations,
            'already_retained_case_closed_proofs': [row(path) for path in sorted((OUT / 'cases').rglob('closed-proof.json'))],
            'no_failure_case_rerun': True})
        save('driver.exception.json', {'error': repr(error), 'automatic_retry': False, 'counter_reset': False,
            'source_acceptance': False, 'formal_increment': 0, 'remaining_cases': 'NOT_RUN_AFTER_FIRST_UNEXPECTED',
            'phase': STATE['phase'], 'completed_cases': STATE['completed_cases'],
            'native_case_exit_is_recorded_in_each_invocation_never_guessed_from_driver_exception': True})
    raise
