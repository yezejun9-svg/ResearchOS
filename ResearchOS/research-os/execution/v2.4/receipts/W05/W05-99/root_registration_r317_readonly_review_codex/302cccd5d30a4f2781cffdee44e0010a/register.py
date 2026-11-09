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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [316, 144, 406]
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
assert scope['registration_checkpoint'] == 317 and scope['root_full159_replay_on_old840'] == 'HOLD_NOT_GRANTED'
desktop_worktree = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311'
assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=desktop_worktree).decode().strip() == scope['evidence_head_before_revision']
assert subprocess.check_output([git, 'status', '--porcelain=v1'], cwd=desktop_worktree) == b''
for item in scope['all_original15_source_before'].values():
    assert ref(item['path'], item['sha256']) == item
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 4
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and row['event_kind'] == 'ACTUAL_NONZERO_EXECUTION'
    assert row['actual_outer_exit'] == 1 and row['actual_native_exit'] is None
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:406] == old_failures and len(cp['failure_counters']) == 410
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(desktop_http_exact15_source_review_ref=pins['source_review'],
    desktop_http_exact15_source_review_state='REQUEST_CHANGES_TWO_FINDINGS_THREE_SUPPLEMENTAL_CONTROLS_NOT_RUN',
    desktop_http_exact15_targeted_revision_scope_ref=pins['scope'],
    desktop_http_exact15_root_replay_on_old840_state='HOLD_NOT_GRANTED',
    desktop_http_exact15_receipt_sealer_failure_registered=True,
    session_list_closedcopy_exact1_final_handoff_ref=pins['cmd_final_handoff'],
    session_list_closedcopy_exact1_state='AUTHOR_EXECUTION_REPORTED_SOURCE_AND_EVIDENCE_COMMITTED_14PASS_78HTTP_NONAUTHOR_REVIEW_PENDING',
    integration_composition_handoff_ref=pins['composition_handoff'],
    integration_composition_unique_paths={'handler_list_helper': 38, 'plus_cli': 43, 'plus_desktop_after_acceptance': 58})
desktop = ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']
assert desktop['current_source_writer'] == 'codex:/root/sources_parent_impl'
desktop.update(targeted_revision_scope_ref=pins['scope'], source_review_ref=pins['source_review'],
    state='SOURCE_TARGETED_REVISION_AUTHORIZED_AFTER_SEAL', source_ready=False, source_acceptance=False)
cmd_subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert cmd_subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
cmd_subtask.update(current_source_writer=None, last_source_writer='codex:/root/command_queue_impl',
    state='WRITER_STOPPED_AUTHOR14_REPORTED_NONAUTHOR_REVIEW_PENDING', final_handoff_ref=pins['cmd_final_handoff'],
    source_only_commit='a5d6d16ffaf129de0361470c3a1570228bd259a2',
    receipt_only_commit='fa73a24f4dd5a9d3246650551aa54b98043fb8fd', source_ready=False, source_acceptance=False)
cp['failure_chains']['W13-03/r317-targeted-source-review-and-receipt-tool-origins'] = {
    'new_actual_nonzero_tool_origins': 4, 'new_static_review_findings_counted_as_native_failures': 0,
    'original406_prefix_unchanged': True, 'counter_reset': False, 'audit_ref': pins['audit'],
    'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Source completes independent Cmd14 closure review, then revised Desktop ACK/strict packet fixes plus original159+7 and3 supplemental controls under new bounded revised-source cohort after actual317+seal. Root14 new runner awaits static review and separate actual grant; old840 full Desktop replay HOLD. Root G2 finite29 continues under immutable313 snapshot with reviewed v3 post-execution sealer. Shared Main source/composed38-43-58/all22/all42 remain HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'DESKTOP_TWO_FINDINGS_TARGETED_REVISION_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'source_review_ref': pins['source_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 406, 'failure_origins_after': 410, 'new_actual_nonzero_tool_origins': 4,
    'static_findings_are_NOT_RUN_not_native_failure': True, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=317, expected_previous_revision=316, updated_at=now, updated_by='codex:/root')
ow.update(revision=145, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [316, 317], 'ownership': [144, 145], 'failures': [406, 410]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root317.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root317.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [317, 145, 410]
    assert actual['failure_counters'][:406] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 317, 'ownership': 145, 'failure_origins': 410,
        'intent_ref': intent_ref, 'old406_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_targeted_Desktop_revision_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r317-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 317, 'failure_origins': 410, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'desktop_targeted_revision_scope_ref': pins['scope'], 'desktop_source_review_ref': pins['source_review'],
    'cmd_author14_final_handoff_ref': pins['cmd_final_handoff'],
    'next': 'Source targeted Desktop revision after exact grant; Cmd14 non-author review and Root independent14 scope preparation; immutable313 G2 continues. No Main composition or current formal acceptance.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 317, 'ownership': 145, 'failure_origins': 410, 'handoff_ref': handoff_ref}, ensure_ascii=True))
