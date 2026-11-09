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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [315, 143, 393]
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
assert scope['registration_checkpoint'] == 316 and scope['cases'] == 14
assert not (ROOT / pins['v4_driver']['path']).with_name('started.json').exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 13
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys
    if row['event_kind'] == 'QUALIFICATION_DEVIATION':
        assert row['actual_outer_exit'] == row['actual_native_exit'] == row['native_failure_count'] == 0
        assert row['qualification_failure_count'] == 1
        status_value = 'ZERO_EXIT_QUALIFICATION_DEVIATION_PRESERVED_NOT_ACCEPTED'
    else:
        assert row['event_kind'] == 'ACTUAL_NONZERO_EXECUTION'
        assert row['actual_outer_exit'] == 1 or row['actual_native_exit'] == 1
        status_value = 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE'
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': status_value, 'formal_increment': 0})
assert cp['failure_counters'][:393] == old_failures and len(cp['failure_counters']) == 406
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_harness_v4_scope_ref=pins['scope'],
    session_list_closedcopy_harness_v4_review_ref=pins['harness_review'],
    session_list_closedcopy_exact1_latest_failure_ref=pins['cmd_failure'],
    session_list_closedcopy_exact1_state='ACTUAL_UTF8_DECODE_FAILURE_RETAINED_TARGETED_V4_NEW_INPUT_ONCE_AUTHORIZED_NOT_EXECUTED',
    desktop_http_exact15_pending_seven_origins_registered=True,
    r315_independent_review_three_actual_failures_registered=True)
subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
subtask.update(harness_revision_scope_ref=pins['scope'], harness_revision_review_ref=pins['harness_review'],
    state='SOURCE_EXACT1_ACTIVE_NEW_INPUT_HARNESS_V4_ONCE_AUTHORIZED')
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
cp['failure_chains']['W05-99/r315-utf8-and-review-Desktop-finite-origins'] = {
    'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2,
    'original393_prefix_unchanged': True, 'counter_reset': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Cmd exact1 v4 strictUTF8/new WORK execute once after actual316+seal. SourceDesktop15 author reports current159+7 under one frozen cohort; protected ranges/commits/non-author review still required. Root G2 finite29 executes under immutable313 snapshot; original and v2 sealers are unexecuted REQUEST_CHANGES. Old393+11 nonzero+2 qualification deviations=406 preserved with actual exits. Main/all22/all42 HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSEDCOPY_TARGETED_HARNESS_V4_NEW_INPUT_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 393,
    'failure_origins_after': 406, 'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=316, expected_previous_revision=315, updated_at=now, updated_by='codex:/root')
ow.update(revision=144, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [315, 316], 'ownership': [143, 144], 'failures': [393, 406]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root316.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root316.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [316, 144, 406]
    assert actual['failure_counters'][:393] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 316, 'ownership': 144, 'failure_origins': 406,
        'intent_ref': intent_ref, 'old393_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_targeted_harness_v4_execution_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r316-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 316, 'failure_origins': 406, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'harness_v4_scope_ref': pins['scope'], 'harness_v4_review_ref': pins['harness_review'],
    'next': 'Cmd new-input strictUTF8 closedcopy harness v4 execute once after seal; SourceDesktop15 non-author review preparation and Root G2 finite29 continue.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 316, 'ownership': 144, 'failure_origins': 406, 'handoff_ref': handoff_ref}, ensure_ascii=True))
