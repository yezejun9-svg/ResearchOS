import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent


def ref(path, expected=None):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(path)
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new, 1)


assert sys.flags.isolated and not sys.flags.optimize and len(sys.argv) == 2
runtime_path = Path(sys.argv[1]).resolve()
assert runtime_path.is_relative_to(OUT)
runtime_ref = ref(runtime_path)
gate_ref = ref(OUT / 'authorization_gate.v2.py')
launcher_ref = ref(OUT / 'launch.v2.py')
source_ref = ref(OUT / 'root_finite14_replay.py', '612794633a1674bf788282db482265b3fd156e2a16f4ad10a44706aac06fe44d')
scope_before_ref = ref(OUT / 'root_finite14_scope.draft.json', '7f5e4e8dafa73fb1b74176f36610e0c33099619eb220bc1d74fb050650c71362')
source = (OUT / 'root_finite14_replay.py').read_text(encoding='utf-8', errors='strict')
scope = json.loads((OUT / 'root_finite14_scope.draft.json').read_bytes())
run_id = uuid.uuid4().hex
old_id = scope['new_output_root'].split('/')[-1]
assert source.count(old_id) == 2
source = source.replace(old_id, run_id)
source = once(source, 'OWN_OUT_CREATED = False', 'OWN_OUT_CREATED = False\nAUTHORIZATION_PATHS = []')
source = once(source, 'import sys', 'import sys\nsys.dont_write_bytecode = True')
vector_extension = '''def merge_frozen(*vectors):
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


'''
source = once(source, 'def runtime_paths():', vector_extension + 'def runtime_paths():')
sidecar_helper = '''def check_python_sidecars(directory, database, stage):
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


'''
source = once(source, 'def check_closed(directory):', sidecar_helper + 'def check_closed(directory):')
source = once(source, "    assert not Path(str(database) + '-wal').exists() and not Path(str(database) + '-shm').exists()", '''    go_sidecar_observations = {}
    for name in ['closed-original.sidecars.json', 'closed-copy.before.sidecars.json', 'closed-copy.after.sidecars.json']:
        sidecars = load(directory / name)
        assert set(sidecars) == {'-wal', '-shm'}
        assert all(set(item) == {'exists', 'error'} and item['exists'] is False and item['error'] is None for item in sidecars.values())
        go_sidecar_observations[name] = {'facts': sidecars, 'evidence': row(directory / name)}
    python_before = check_python_sidecars(directory, database, 'before_read')''')
source = once(source, '        connection.close()', "        try:\n            connection.close()\n        finally:\n            python_after = check_python_sidecars(directory, database, 'after_connection_close')")
source = once(source, "    assert proof['case_failed'] is False and proof['SDK_worker_model_external_paid'] == 0", "    assert proof['closed_copy_sidecars_absent'] is True\n    assert proof['case_failed'] is False and proof['SDK_worker_model_external_paid'] == 0")
source = once(source, "        'readonly_bytes_unchanged': True, 'rowid_not_separately_exported': True}", "        'readonly_bytes_unchanged': True, 'rowid_not_separately_exported': True,\n        'go_three_closed_sidecar_observations': go_sidecar_observations,\n        'python_before_read': python_before, 'python_after_connection_close': python_after}")
source = once(source, 'global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED, PROCESS_HELPER', 'global ENV, OVERRIDES, CLEARED, RUN_OWNED, OWN_OUT_CREATED, PROCESS_HELPER, AUTHORIZATION_PATHS')
source = once(source, '    assert len(sys.argv) == 3', '    assert len(sys.argv) == 5')
source = once(source, "DRAFT / 'root_finite14_scope.draft.json'", "DRAFT / 'root_finite14_scope.v2.json'")
source = once(source, "    helper_path = (ROOT / scope['owned_process_helper_ref']['path']).resolve()", '''    gate_path = (ROOT / scope['authorization_gate_ref']['path']).resolve()
    gate_raw = gate_path.read_bytes()
    assert len(gate_raw) == scope['authorization_gate_ref']['bytes']
    assert hashlib.sha256(gate_raw).hexdigest() == scope['authorization_gate_ref']['sha256']
    gate_module = types.ModuleType('researchos_finite14_actual_authorization_gate')
    gate_module.__file__ = str(gate_path)
    exec(compile(gate_raw, str(gate_path), 'exec'), gate_module.__dict__)
    authorization = gate_module.validate_grant(scope_path, sys.argv[2], Path(sys.argv[3]).resolve(), sys.argv[4])
    AUTHORIZATION_PATHS = [Path(path).resolve() for path in authorization['authorization_paths']]
    assert gate_path in AUTHORIZATION_PATHS
    helper_path = (ROOT / scope['owned_process_helper_ref']['path']).resolve()''')
source = once(source, "    cp = load(ROOT / 'execution/v2.4/checkpoint.json')\n    assert cp['revision'] >= 317\n    pin = cp['work_in_progress']['session_list_closedcopy_root_finite14_scope_ref']\n    assert (ROOT / pin['path']).resolve() == scope_path and pin['sha256'] == sys.argv[2]\n    assert cp['work_in_progress']['session_list_identity_source_ready'] is False", '''    # All authority came from the actual sealed registration and its immutable canonical copies.
    # Subsequent Root canonical progress does not alter this registered execution snapshot.
    assert authorization['scope']['source_commit'] == CANDIDATE
    assert authorization['grant']['actual_registration_completed'] is True''')
source = once(source, "    save('scope.original.json', scope)", "    save('scope.original.json', scope)\n    save('authorization-inputs.original.json', vector(AUTHORIZATION_PATHS))")
source = once(source, '    initial_paths.update(runtime_paths())', '    initial_paths.update(runtime_paths())\n    initial_paths.update(AUTHORIZATION_PATHS)')
source = once(source, '    before = vector(inputs)', '    before = extend_vector(initial_freeze, inputs)')
source = once(source, "    save('compiled_WORK_vector.json', vector(artifacts))", '''    work_freeze = vector(artifacts)
    save('compiled_WORK_vector.json', work_freeze)
    archive_freeze = merge_frozen(*[[item['archive']] for item in importcfg_refs])
    compiled_freeze = merge_frozen(before, work_freeze, archive_freeze, vector([executable]))
    check_vector(compiled_freeze)''')
source = once(source, '    freeze = vector(inputs)', '''    check_vector(compiled_freeze)
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
        'same_path_new_baseline_prohibited': True})''')
ast.parse(source)
old_shas = set(re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])', (OUT / 'root_finite14_replay.py').read_text(encoding='utf-8')))
assert old_shas.issubset(set(re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])', source)))
with (OUT / 'root_finite14_replay.v2.py').open('xb') as stream:
    stream.write(source.encode('utf-8'))
review_dir = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_author14_closure_review_codex/85a603d2d1be48f89a501f6068aee16f'
author14_review_ref = ref(review_dir / 'source_review.json', '6596e8aecf36bd25e92b34bf35548b77bcea66ec2c7481972bdeafcb9b6f818a')
assert json.loads((review_dir / 'source_review.json').read_bytes())['status'] == 'READY_FOR_ROOT_INDEPENDENT_FINITE14'
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
status = subprocess.check_output([lock['git']['path'], 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
scope.update(state='DRAFT_V2_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED', uuid=run_id, run_uuid=run_id,
    runner_ref=ref(OUT / 'root_finite14_replay.v2.py'), launcher_ref=launcher_ref, authorization_gate_ref=gate_ref,
    author14_review_ref=author14_review_ref,
    author14_review_handoff_ref=ref(review_dir / 'handoff.complete.json', 'b0268c53d7fd3d1c8fed8b5a365fc2b5bba365a8ae170cc72b0edacc7250ddda'),
    author14_review_manifest_ref=ref(review_dir / 'manifest.complete.json', 'c0c754bc7995a356c8cbfe7c325b7a280038426b865352bc37a5a496be81fab3'),
    previous_runner_draft_ref=source_ref, previous_scope_draft_ref=scope_before_ref,
    previous_static_REQUEST_CHANGES_ref=ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_root_runner_static_review_codex/02c6cdcbd85f4c6eb93a76f36a0f350b/review.json', '3991d47ae3139ad6221638667cb101e4f74a31fd255068971a4d44bb8cb191ee'),
    new_output_root='execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_codex/' + run_id,
    new_export_root='.local/independent-session-list-closedcopy-root-' + run_id,
    new_authorization_root='execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_root_replay_authorization_codex/' + run_id,
    registration_namespace='execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-r318',
    expected_registration=[318, 146, 410],
    launch_limits={'timeout_seconds': 3600}, runtime_resources_ref=runtime_ref,
    main_git={'head': '2cdb0d43d5a600eef13c8f1735946a9adf52d079', 'status_sha256': hashlib.sha256(status).hexdigest(),
        'status_bytes': len(status), 'status_rows': 13, 'deleted_rows': 11, 'index_empty': True},
    authority_rule='Draft alone grants nothing. Exact actual sealed Root318 registration, source and runner independent reviews, four actual canonical raw copies and one unique prelaunch grant are mandatory before native calls.',
    immutable_vector_extension='Retain original path/hash/bytes rows; only new paths appended; compiler WORK/archive/exe records checked again after exe-buildinfo; initial/before_compile/before_first exact subsets.',
    sidecar_rule='Consume all three actual Go closed sidecar observations and closed_copy_sidecars_absent=true; independently lstat -wal/-shm before SQLite read and after connection.close; error/symlink/existence refuses. Never delete sidecar.')
scope['author14_handoff_ref'] = scope['author14_review_handoff_ref']
scope['author14_manifest_ref'] = scope['author14_review_manifest_ref']
authorization_parent = (ROOT / scope['new_authorization_root']).parent
assert authorization_parent.resolve().is_relative_to(ROOT)
authorization_parent.mkdir(parents=True, exist_ok=True)
scope_ref = save('root_finite14_scope.v2.json', scope)
save('runner_revision.v2.audit.json', {'previous_runner_ref': source_ref, 'previous_scope_ref': scope_before_ref,
    'runner_ref': scope['runner_ref'], 'scope_ref': scope_ref, 'gate_ref': gate_ref, 'launcher_ref': launcher_ref,
    'runtime_resources_ref': runtime_ref, 'R14_01_actual_sealed_grant_consumed_and_frozen': True,
    'R14_02_existing_vector_rows_immutable': True, 'R14_03_pre_and_post_closed_sidecars_checked': True,
    'all_old64hex_literals_unchanged': True, 'actual_export_build_SQL_HTTP_MODEL': 0,
    'state': 'DRAFT_STATIC_REVIEW_REQUIRED', 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'runner': scope['runner_ref'], 'scope': scope_ref, 'gate': gate_ref, 'launcher': launcher_ref,
    'actual_export_compile_tests': 0}, ensure_ascii=True))
