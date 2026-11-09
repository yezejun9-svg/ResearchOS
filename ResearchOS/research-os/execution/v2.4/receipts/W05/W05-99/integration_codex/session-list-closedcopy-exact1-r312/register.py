import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}


def read(path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
prepared = json.loads(read(OUT / 'prepared_refs.json'))
before = {path: path.read_bytes() for path in CANON}
assert len(prepared['canonical_before']) == 4
for path, pin in zip(CANON, prepared['canonical_before']):
    assert path == ROOT / pin['path'] and ref(path) == pin
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [311, 139, 384]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == prepared['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
for item in prepared['verified_refs']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
g2_worktree = ROOT / '.local/worktrees/codex-w0599-provider-g2-finite-r307'
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=g2_worktree).decode().strip() == '9a34aacbaeb775566e524f5af3518ea86a5d41b9'
assert subprocess.check_output([git, 'status', '--porcelain=v1'], cwd=g2_worktree) == b''
assert ref(g2_worktree / 'internal/domain/runtime_coordinator_windows_test.go')['sha256'] == 'a3f6ccfa16a3ea5d3770802eeb376789988bfcbd7b0b9b745e01c2821c4cacd8'
assert ref(g2_worktree / 'internal/domain/runtime_provider_binding_windows_test.go')['sha256'] == 'df176f5252e1b7eb6ac6f997052844b3af3f98997f7c2ac232eddb5307eaa8c4'
pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 312 and scope['owner'] == 'codex:/root/command_queue_impl'
assert scope['exact_paths'] == ['internal/api/v2_sessions_test.go'] and not Path(scope['worktree']).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 2
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and row['actual_outer_exit'] == 1
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:384] == old_failures and len(cp['failure_counters']) == 386
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_exact1_scope_ref=pins['scope'],
    session_list_closedcopy_exact1_state='TEST_ONLY_SOURCE_LEASE_GRANTED_WORKTREE_CREATION_PENDING',
    session_list_identity_independent_state='STOPPED_FIRST_NATIVE0_CLOSED_COPY_SIDECARS_PRESENT_13_NOTRUN',
    session_list_identity_independent_latest_failure_ref=pins['root_failure'],
    session_list_identity_independent_cause_review_ref=pins['cause_review'],
    cli_current_qualified_unique_leaves=221, cli_exact8_221_finite_review_ref=pins['cli221_review'],
    cli_exact8_221_finite_handoff_ref=pins['cli221_handoff'],
    cli_split_continuation_state='FINITE_UNIQUE_UNION221_COMPLETE_PENDING_MAIN_COMPOSITION_HELD2',
    cli_contract_source_ready=False, session_list_identity_source_ready=False)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert 'session_list_closedcopy_exact1' not in subtasks
subtasks['session_list_closedcopy_exact1'] = {'owner': scope['owner'], 'current_source_writer': scope['owner'],
    'worktree': scope['worktree'], 'base_commit': scope['base_commit'], 'paths': scope['exact_paths'],
    'scope_ref': pins['scope'], 'state': 'SOURCE_LEASE_GRANTED_WORKTREE_CREATION_PENDING',
    'source_ready': False, 'source_acceptance': False, 'Main_product_source_writes': 0, 'formal_increment': 0}
subtasks['session_list_identity_independent_replay'].update(state='STOPPED_FIRST_NATIVE0_CLOSED_COPY_SIDECARS',
    latest_failure_ref=pins['root_failure'], nonauthor_cause_review_ref=pins['cause_review'])
for key in ['cli17_independent_continuation', 'cli_windows4_independent_continuation']:
    subtasks[key].update(state='FINITE_SCOPE_COMPLETED_NO_SOURCE_ACCEPTANCE', finite_review_ref=pins['cli221_review'])
chain = 'W05-99/r310-closed-copy-controller-and-readonly-locator'
assert chain not in cp['failure_chains']
cp['failure_chains'][chain] = {'actual_failed_invocations': 2, 'product_native_test_failures': 0,
    'original384_prefix_unchanged': True, 'counter_reset': False, 'automatic_same_input_retry': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut']}
cp['next_command'] = 'Source Desktop exact15 implementation active. Cmd exact1 closedcopy evidence helper correction/new14 lease registered, fresh own worktree; preserve original native0/controller1 and13NOTRUN. CLI unique221 complete, Main/held2/formal HOLD. G2prepare remains own actual process. Failure384+2=386, no reset; all22/42 current acceptance stillopen.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSED_COPY_EXACT1_TEST_LEASE_AND_CLI221_FINITE_UNION_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 384,
    'failure_origins_after': 386, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=312, expected_previous_revision=311, updated_at=now, updated_by='codex:/root')
ow.update(revision=140, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
for path, raw in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream:
        stream.write(raw)
with (OUT / 'git-status.original.raw').open('xb') as stream:
    stream.write(status)
desired = {path: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for path, value in zip(CANON[:2], [cp, ow])}
for path, raw in desired.items():
    with (OUT / (path.stem + '.desired.json')).open('xb') as stream:
        stream.write(raw)
intent_ref = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': head,
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)), 'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [311, 312], 'ownership': [139, 140], 'failures': [384, 386]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root312.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root312.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [312, 140, 386]
    assert actual['failure_counters'][:384] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 312, 'ownership': 140, 'failure_origins': 386,
        'intent_ref': intent_ref, 'old384_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_closedcopy_exact1_source_lease_and_CLI221_finite_record_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r312-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 312, 'failure_origins': 386, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'new_closedcopy_scope_ref': pins['scope'], 'CLI221_review_ref': pins['cli221_review'],
    'next': 'Root creates dedicated closedcopy exact1 worktree; Cmd implements minimal new test evidence correction. Source Desktop exact15 remains independently active. G2 prepare still actual process; no execute29 grant yet.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 312, 'ownership': 140, 'failure_origins': 386, 'handoff_ref': handoff_ref}, ensure_ascii=True))
