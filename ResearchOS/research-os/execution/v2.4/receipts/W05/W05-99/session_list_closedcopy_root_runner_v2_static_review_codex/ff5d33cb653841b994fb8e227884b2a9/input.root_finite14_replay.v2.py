import sys
sys.dont_write_bytecode = True
sys.dont_write_bytecode = True

import base64
from collections import Counter
import datetime
import hashlib
import types
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
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_codex/a452e0211f5846db95514697db075e61'
EXPORT = ROOT / '.local/independent-session-list-closedcopy-root-a452e0211f5846db95514697db075e61'
CANDIDATE = 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
SOURCE_PARENT = '534857db99fa5e694987f877af74c322eaa2a0b3'
BASE = '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
NAMES = ['NullContext', 'OwnedContext', 'ContextNotResultFilter', 'ExactReplayAfterCommit', 'ChangedPayloadConflict', 'ChangedSIDConflict', 'CrossProjectContext', 'ForeignPrincipalContext', 'ForeignPrincipalNullList', 'UnknownContext', 'ProjectGrantDenied', 'CrossProjectCursor', 'CrossPrincipalCursor', 'MalformedRequest']
SOURCES = {
    'internal/domain/client_protocol_sessions.go': '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3',
    'internal/api/v2_sessions_test.go': '9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae',
}
PUBLIC_JEV = {'evaluation/holdout/jev/generate_other.go': {'git_blob': 'a0edc3fd43095520d2b5a77a4d1027e41c5ef147', 'sha256': '2afa6e97311ece753df8af74bd68de7ded3445d8a40bfa988f8ba17baadd5bf4', 'bytes': 186}, 'evaluation/holdout/jev/generate_windows.go': {'git_blob': '46bb72987cddbeeafb296dce03b2f160f5ec8c85', 'sha256': 'c02188ddd6c831ef0dc6b7af97b7667a05fa50e62f074d4b7ff709a0607baab1', 'bytes': 988}, 'evaluation/holdout/jev/generator.go': {'git_blob': '5be93941e7d0b8c3d22c60649f6dfe7689bcedd0', 'sha256': '1dc3d5154fe713155944b9ce761cd0bfc6a1fc4d92f34d0bac7ccd37df8aa523', 'bytes': 12685}, 'evaluation/holdout/jev/rubric.go': {'git_blob': '11bbedbcb5b621d6d0f0f8a2d2dbc38cb577eb8f', 'sha256': '10f3cc145780b4934e005db9bfb5ca7501a152f1caee89aee8732cc5eaf6e2ae', 'bytes': 2916}, 'evaluation/holdout/jev/truth.go': {'git_blob': '43e9c19fbbf98fc0ed790ec77d001b8182e8c9d7', 'sha256': 'b41064e0890811113e249a8fedc3a3ae153a5f71fa868e4763ffa2ad76cc4ca2', 'bytes': 4804}, 'evaluation/evolution/control_current.go': {'git_blob': '23bcb900dff23c0e7c1932afe26348867ce3a893', 'sha256': 'd6d1b6e841057e185baeb0e95e2cd07484a1f31dacc1e01367c469ad57bc527d', 'bytes': 4735}, 'evaluation/evolution/control_protocol.go': {'git_blob': 'e08fe556c18f14428c7c4f122cd1c2b31a7adbbf', 'sha256': 'f7f620372d16584196a7be6aaf72eff310adc7f4f5b0b9a3dd7367ea29a5ae4a', 'bytes': 9930}, 'evaluation/evolution/control_release.go': {'git_blob': '6af5df5d15eed0748757d3d5cba202abbb51e5ea', 'sha256': '1b2a4574b9c5ce3dc6271b1b5b0af9886b876fee10f26d2776606282e670b377', 'bytes': 4089}, 'evaluation/evolution/holdout.go': {'git_blob': 'ce2b7e048854a6a60c5a90b1a9da66ca94a9b04f', 'sha256': 'cf4d6aa3fcc240d163734fa031e0031349867f39811da274c4c173f8cfba1d87', 'bytes': 1796}, 'evaluation/evolution/suite.go': {'git_blob': '11873328e09dd6b3b1bcb28784f0f4d74adc1af5', 'sha256': '9d9d5f3d31e0f7b2a2ae81f730664eb22536e8663fa8162086da9d4337894159', 'bytes': 3387}, 'evaluation/holdout/jev/generator_test.go': {'git_blob': '04059b514f8010e39e47bc1d730d6fc21df7a549', 'sha256': '0dc7901a4114362d46adb21afecef1f9092b5da591203e989bdb644f2ec081d3', 'bytes': 8042}, 'evaluation/skills/compare.go': {'git_blob': '8f359baea3e9d70ffe6d47aa09128f8886ac7d80', 'sha256': 'e079d00b35264a7613e8f9d0a45be8c0363235243e7d17712aa0d5a34af5c06e', 'bytes': 1131}, 'evaluation/skills/rubric.go': {'git_blob': '2398108fade51d7889ad0a378da41676ad6a5feb', 'sha256': '7fb0b6d687068037834da0d447414f4a18fb94a737c28a7e62dfc5bb5291c30a', 'bytes': 1606}, 'evaluation/skills/rubric_test.go': {'git_blob': '39cf7dc3724c772d9ef7e422e60e2b8d1b71876a', 'sha256': '1fcbae0bd2553c43127e111a2bc0e80c4d2abda219b6395817a255da24e8fc1c', 'bytes': 1097}, 'ops/experiment_sandbox/async_windows.go': {'git_blob': '617bec489fc90b71feac6a053d01317786013a4e', 'sha256': '5bd04f17e41b64d9657cdf52d98bde2348b88a8360a3d5aaafe9d351964255a0', 'bytes': 5240}, 'ops/experiment_sandbox/async_windows_test.go': {'git_blob': '2f6b89f7e51419ec381a8a4ad0a19e9d4ddd7c83', 'sha256': '5e566cdf1e37c464e3026d031125a1bf17a6149e1de36e85644ba973c9de68fa', 'bytes': 9889}, 'ops/experiment_sandbox/native_go_windows_test.go': {'git_blob': '750ecf514d8c6061c4a7cd6a5f1bec6b915bf018', 'sha256': '1797280d959c25bad4eae55d9ae0f72e64f152a307a5413258915c8ccc544690', 'bytes': 6653}, 'ops/experiment_sandbox/recovery_windows.go': {'git_blob': 'e4706b2e33667954475dc81110079a92c02964e2', 'sha256': 'ebb188c41263eb7ebd3ac9847b9fb9220764b745963b8855eabe6350f5ff1706', 'bytes': 3033}, 'ops/experiment_sandbox/sandbox_windows.go': {'git_blob': 'd4e1b5621fa26175c60c51e9b38c08e5f868f98e', 'sha256': '8447a67cc2d5e57b244b33574e3eef9940dad4273d8f5ec3e1c1563b430bf258', 'bytes': 16189}, 'ops/experiment_sandbox/sandbox_windows_test.go': {'git_blob': '288270806f3495af0c95761c66e34cf60ede1537', 'sha256': '8f4c82d7f06da2163daffdabedb8444bbb5490f9f1c9e1f03a58d13d4fedba58', 'bytes': 6933}, 'ops/supervisor/control_authority_windows.go': {'git_blob': 'e0b3b646ff2f235d44f02a87fc95b0e781e5a716', 'sha256': 'f0b5d91432bd65adf7e6e9e3947cc9cc38004ea3b2d5f6a65ffab1485c01fca4', 'bytes': 9431}, 'ops/supervisor/control_fixture_windows.go': {'git_blob': '684db6072f2a55587c3c61e0a5d5e81d03da6fd6', 'sha256': 'd896dfdad2da309c08d60d893347bcb1a388556dda9973e5a83c42c2370dbfe6', 'bytes': 16093}, 'ops/supervisor/control_fixture_windows_test.go': {'git_blob': 'ebdddb215f9e71e4918f2d01ae98aa97276cd405', 'sha256': '8a27b208e7da8e7bd457304cce375aaccc5eb0fb627457fba744f85e591bb64c', 'bytes': 16499}, 'ops/supervisor/control_holdout_windows.go': {'git_blob': '50ad7fb494eb7acaf61cf4b4dce2609ced4dbe02', 'sha256': 'a560ee8ce4aba5e6e077080c04a6279aa75a0a6ae25631ee6b651cbe624bf22d', 'bytes': 12744}, 'ops/supervisor/fixture_windows.go': {'git_blob': '9674a74569b8ba91282c4d7c640b70a485df0366', 'sha256': 'f8667df76655297573d57b9ad2f4085ecfd383dd37e34bce66ce870054066b19', 'bytes': 5089}, 'ops/supervisor/holdout_windows.go': {'git_blob': 'b2e0762018add181967ee165a322591b3b657b48', 'sha256': '2659a80b2da2ef657e5c42a88c870a1c486024acc02e9a8045fd0ff247e5e0f5', 'bytes': 8627}, 'ops/supervisor/holdout_windows_test.go': {'git_blob': '67445b0c532c9c81f98589d544263e27bb068c90', 'sha256': '85f80a3693618f39a0376ba6a346bd380e4c935ca0202e4f4571e69f3ad07324', 'bytes': 1058}, 'ops/supervisor/release_drain_windows.go': {'git_blob': 'c1c06535e113288c9cfae7609907d88ed3ae152d', 'sha256': 'e25acfa43a488c6f08c5017bdc6c2b400bfabd00f086b2e47847178c676d5f4c', 'bytes': 11536}, 'ops/supervisor/release_engine_windows.go': {'git_blob': 'cd150e382d9cdbd8df83ed38f61f8b0f0a677b68', 'sha256': '8a2068d8bbbee4118b5a6b1e8f2f6c50257a0856d0a88f80c34acbe9bf4ee8d3', 'bytes': 11491}, 'ops/supervisor/release_engine_windows_test.go': {'git_blob': '7c558f62e8ae91c6dd50a4717a39fc01fc383d37', 'sha256': '7a9ce0c78e2db35bc480e604b2e991453419c1fdae38c87215acccc6c82d47cd', 'bytes': 9968}, 'ops/supervisor/release_journal_windows.go': {'git_blob': '496636afcb65c15f9b7e6a5238cb3a7d6bf3d60d', 'sha256': '3eee9c952a6959837546c818a9893c719a53bb5e7edb14dc249821a0ff2f858d', 'bytes': 21137}, 'ops/supervisor/release_process_windows.go': {'git_blob': '96ced0679bfe9f70eef287ac7987e41db7d9a80d', 'sha256': '052fa936823b29c0e32e6618c637dfd2a0f1cf4d2ee96556a338d122fc4d9b41', 'bytes': 5607}, 'ops/supervisor/release_readiness_windows_test.go': {'git_blob': '901bf55d0f2688a2a3ca801a4fb19f23a79c7ece', 'sha256': '45c98d29aeddc3c829e7a9ef3fbeb820332db1003050562e03070eb0cb0403d6', 'bytes': 4544}, 'ops/supervisor/release_receipt_windows.go': {'git_blob': '8af4add4056d1072359587273acbb972f7319680', 'sha256': '4b86a8a48df1741feed21aca40687b843cb3d8172e327d147bd51c6c32ceb454', 'bytes': 4547}, 'ops/supervisor/release_recovery_windows_test.go': {'git_blob': 'b70ba84cfa2adccf9972cbab36e736a5716196d5', 'sha256': '63721a0d2f4c9fa62099dacc385ae8272eb560295ed2d6ad4f0b8bfc14c251b8', 'bytes': 11867}, 'ops/supervisor/release_sql_windows_test.go': {'git_blob': 'd54c28d091f542e0f4af7131385d34f3b7ac7a66', 'sha256': '3f44824822d5669048c42dc34fbfea872a2c0e93b95d1c2ec0816b485fe2aee3', 'bytes': 4259}}
RESOURCE_PLAN_REF = {'path': 'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json', 'sha256': '598adac08e7c638bda6b783a78dc8541847b8e48054e196dd6da6eb728319bc2', 'bytes': 1573436}
STATE = {'phase': 'NOT_STARTED', 'frozen_inputs': [], 'completed_cases': []}
OWN_OUT_CREATED = False
AUTHORIZATION_PATHS = []


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


def optional_row(path):
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


def vector(paths):
    return [row(path) for path in sorted(set(Path(p).resolve() for p in paths))]


def check_vector(before):
    after = [row(item['path']) for item in before]
    if after != before:
        raise RuntimeError('Frozen source/tool/generated/archive/exe input drift')
    return after


def merge_frozen(*vectors):
    entries = {}
    for frozen in vectors:
        assert len({item['path'] for item in frozen}) == len(frozen)
        for item in frozen:
            if item['path'] in entries:
                assert entries[item['path']] == item, 'Conflicting already-frozen input: ' + item['path']
            else:
                entries[item['path']] = dict(item)
    return [entries[path] for path in sorted(entries)]


def extend_vector(before, paths):
    # Existing rows are immutable. Hash only genuinely new paths; never absorb drift.
    assert len({item['path'] for item in before}) == len(before)
    requested = {str(Path(path).resolve()) for path in paths}
    originals = {item['path']: item for item in before}
    assert set(originals).issubset(requested)
    check_vector(before)
    added = vector(requested.difference(originals))
    extended = merge_frozen(before, added)
    assert all(item == {row['path']: row for row in extended}[item['path']] for item in before)
    check_vector(extended)
    return extended


def runtime_paths():
    paths = {Path(path).resolve() for path in PROCESS_HELPER.runtime_resource_paths()}
    for module in list(sys.modules.values()):
        for attribute in ('__file__', '__cached__'):
            name = getattr(module, attribute, None)
            if name and Path(name).is_file():
                paths.add(Path(name).resolve())
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


def check_python_sidecars(directory, database, stage):
    facts = {}
    for suffix in ('-wal', '-shm'):
        try:
            Path(str(database) + suffix).lstat()
        except FileNotFoundError:
            facts[suffix] = {'exists': False, 'error': None}
        except OSError as error:
            facts[suffix] = {'exists': None, 'error': repr(error)}
        else:
            facts[suffix] = {'exists': True, 'error': None}
    evidence = save((directory / ('independent-python.' + stage + '.sidecars.json')).relative_to(OUT), facts)
    assert all(item['exists'] is False and item['error'] is None for item in facts.values()), facts
    return {'facts': facts, 'evidence': evidence}


def check_closed(directory):
    database = directory / 'closed.sqlite'
    before = row(database)
    go_sidecar_observations = {}
    for name in ['closed-original.sidecars.json', 'closed-copy.before.sidecars.json', 'closed-copy.after.sidecars.json']:
        sidecars = load(directory / name)
        assert set(sidecars) == {'-wal', '-shm'}
        assert all(set(item) == {'exists', 'error'} and item['exists'] is False and item['error'] is None for item in sidecars.values())
        go_sidecar_observations[name] = {'facts': sidecars, 'evidence': row(directory / name)}
    python_before = check_python_sidecars(directory, database, 'before_read')
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
        try:
            connection.close()
        finally:
            python_after = check_python_sidecars(directory, database, 'after_connection_close')
    assert row(database) == before
    proof = load(directory / 'closed-proof.json')
    assert proof['closed_copy_sha256'] == before['sha256']
    assert proof['all_table_schema_multisets_equal'] is True and proof['closed_copy_bytes_unchanged_by_read'] is True
    assert proof['closed_copy_sidecars_absent'] is True
    assert proof['case_failed'] is False and proof['SDK_worker_model_external_paid'] == 0
    return {'database': before, 'independent_python_sqlite_version': sqlite3.sqlite_version,
        'schema_all_columns_all_typed_row_multisets_equal': True, 'table_counts': table_counts,
        'readonly_bytes_unchanged': True, 'rowid_not_separately_exported': True,
        'go_three_closed_sidecar_observations': go_sidecar_observations,
        'python_before_read': python_before, 'python_after_connection_close': python_after}


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
    global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED, PROCESS_HELPER, AUTHORIZATION_PATHS
    assert len(sys.argv) == 5
    scope_path = Path(sys.argv[1]).resolve()
    assert scope_path == DRAFT / 'root_finite14_scope.v2.json' and sha(scope_path) == sys.argv[2]
    scope = load(scope_path)
    assert scope['source_commit'] == CANDIDATE and scope['owner'] == 'codex:/root'
    assert scope['runner_ref']['sha256'] == sha(Path(__file__))
    assert scope['ordered_cases'] == NAMES and scope['source_paths_sha256'] == SOURCES
    gate_path = (ROOT / scope['authorization_gate_ref']['path']).resolve()
    gate_raw = gate_path.read_bytes()
    assert len(gate_raw) == scope['authorization_gate_ref']['bytes']
    assert hashlib.sha256(gate_raw).hexdigest() == scope['authorization_gate_ref']['sha256']
    gate_module = types.ModuleType('researchos_finite14_actual_authorization_gate')
    gate_module.__file__ = str(gate_path)
    exec(compile(gate_raw, str(gate_path), 'exec'), gate_module.__dict__)
    authorization = gate_module.validate_grant(scope_path, sys.argv[2], Path(sys.argv[3]).resolve(), sys.argv[4])
    AUTHORIZATION_PATHS = [Path(path).resolve() for path in authorization['authorization_paths']]
    assert gate_path in AUTHORIZATION_PATHS
    helper_path = (ROOT / scope['owned_process_helper_ref']['path']).resolve()
    assert scope['owned_process_helper_ref']['sha256'] == sha(helper_path)
    helper_raw = helper_path.read_bytes()
    assert hashlib.sha256(helper_raw).hexdigest() == scope['owned_process_helper_ref']['sha256']
    helper_module = types.ModuleType('researchos_root_owned_windows_process')
    helper_module.__file__ = str(helper_path)
    # Compile verified source bytes directly: no SourceFileLoader or existing pyc read.
    exec(compile(helper_raw, str(helper_path), 'exec'), helper_module.__dict__)
    RUN_OWNED = helper_module.run_owned
    PROCESS_HELPER = helper_module
    # Pure local URI conversion loads lazy standard-library modules before any input freeze.
    (ROOT / '__pure_uri_preload_no_file_access__').as_uri()
    # All authority came from the actual sealed registration and its immutable canonical copies.
    # Subsequent Root canonical progress does not alter this registered execution snapshot.
    assert authorization['scope']['source_commit'] == CANDIDATE
    assert authorization['grant']['actual_registration_completed'] is True
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
        'GIT_OPTIONAL_LOCKS': '0', 'GOWORK': 'off', 'GOFLAGS': '-buildvcs=false', 'GOAMD64': 'v1', 'GOEXPERIMENT': '', 'GODEBUG': '',
        'RESEARCHOS_GO': str(go), 'GIT_NO_REPLACE_OBJECTS': '1', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
        'RESEARCHOS_SESSION_LIST_EVIDENCE': str(OUT / 'cases')}
    CLEARED = sorted(key for key in os.environ if key.upper().startswith('RESEARCHOS_'))
    ENV = {key: os.environ[key] for key in ('OS', 'PATHEXT', 'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
        'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL', 'PROCESSOR_REVISION') if key in os.environ}
    system = Path(os.environ['SystemRoot'])
    ENV.update({'SystemRoot': str(system), 'WINDIR': str(system), 'ComSpec': str(system / 'System32/cmd.exe'),
        'USERPROFILE': str(local / 'temp/profile'), 'LOCALAPPDATA': str(local / 'temp/profile/AppData/Local'),
        'APPDATA': str(local / 'temp/profile/AppData/Roaming'),
        'PATH': os.pathsep.join([str(Path(go).parent), str(Path(git).parent),
            str(system / 'System32/WindowsPowerShell/v1.0'), str(system / 'System32')])})
    ENV.update(OVERRIDES)
    save('scope.original.json', scope)
    save('authorization-inputs.original.json', vector(AUTHORIZATION_PATHS))
    delta = run('candidate-source-delta', [git, 'diff-tree', '--no-commit-id', '--name-only', '-r', CANDIDATE], ROOT).decode().splitlines()
    assert delta == ['internal/api/v2_sessions_test.go']
    assert run('candidate-parent', [git, 'rev-parse', CANDIDATE + '^'], ROOT).decode().strip() == SOURCE_PARENT
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
    save('public-JEV-classification.json', {'resources': PUBLIC_JEV, 'classification': 'All36 individually named already approved public Go compiler resources; no private runtime truth/qualification data or dependency test execution', 'plan_ref': RESOURCE_PLAN_REF})
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
    assert len(public_plan['git_resources']) == 518
    assert all((EXPORT / pin['path']).is_file() for pin in public_plan['git_resources']), 'Known approved public compiler catalog export is incomplete'
    for pin in public_plan['external_tools_modules_stdlib']:
        actual = row(pin['path'])
        assert actual['sha256'] == pin['sha256'] and actual['bytes'] == pin['bytes']
        initial_paths.add(Path(pin['path']))
    for directory in [goroot / 'src', goroot / 'pkg/tool', goroot / 'lib']:
        initial_paths.update(path for path in directory.rglob('*') if path.is_file())
    initial_paths.update([Path(lock[key]['path']) for key in ['python', 'git', 'go']])
    initial_paths.update([Path(go).parent / 'gofmt.exe', Path(__file__), helper_path, scope_path, lock_path, plan_path])
    initial_paths.update(runtime_paths())
    initial_paths.update(AUTHORIZATION_PATHS)
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
    before = extend_vector(initial_freeze, inputs)
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
                for line in path.read_text(encoding='utf-8', errors='strict').splitlines():
                    if line.startswith('packagefile '):
                        package, archive = line[len('packagefile '):].split('=', 1)
                        archive_path = Path(archive.replace('$WORK', str(work))).resolve()
                        assert archive_path.is_file()
                        inputs.add(archive_path)
                        importcfg_refs.append({'importcfg': str(path), 'package': package, 'archive': row(archive_path)})
    save('actual-importcfg-packagefile-refs.json', importcfg_refs)
    generated_mains = list((OUT / 'generated').rglob('_testmain.go'))
    assert len(generated_mains) == 1 and 'TestSessionListHTTPOriginalContextIdentity' in generated_mains[0].read_text(encoding='utf-8', errors='strict')
    save('inputs.after_compile.json', check_vector(before))
    work_freeze = vector(artifacts)
    save('compiled_WORK_vector.json', work_freeze)
    archive_freeze = merge_frozen(*[[item['archive']] for item in importcfg_refs])
    compiled_freeze = merge_frozen(before, work_freeze, archive_freeze, vector([executable]))
    check_vector(compiled_freeze)
    run('exe-buildinfo', [go, 'version', '-m', str(executable)])
    inputs.update(artifacts)
    inputs.add(executable)
    inputs.update(runtime_paths())
    check_vector(compiled_freeze)
    freeze = extend_vector(compiled_freeze, inputs)
    final_map = {item['path']: item for item in freeze}
    assert all(final_map[item['path']] == item for item in initial_freeze)
    assert all(final_map[item['path']] == item for item in before)
    assert all(final_map[item['path']] == item for item in work_freeze)
    save('immutable-input-vector-extension-proof.json', {
        'initial_count': len(initial_freeze), 'before_compile_count': len(before),
        'WORK_count': len(work_freeze), 'compiled_count': len(compiled_freeze), 'before_first_count': len(freeze),
        'initial_subset_before_compile_exact': True, 'before_compile_subset_before_first_exact': True,
        'WORK_and_archives_and_exe_after_buildinfo_unchanged': True, 'new_paths_only_appended': True,
        'same_path_new_baseline_prohibited': True})
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
