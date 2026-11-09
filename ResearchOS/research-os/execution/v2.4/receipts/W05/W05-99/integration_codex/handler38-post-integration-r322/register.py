import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
sys.dont_write_bytecode = True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [321, 149, 422]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert head == prepared['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
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
closed = json.loads(read(pins['main38_completed']['path']))
assert closed['actual_head'] == head and closed['unique_paths'] == 38 and closed['merge_attempts'] == 1
assert closed['status'] == 'EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION'
assert closed['whole_W05_acceptance'] is False
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert len(old_failures) == 422 and len(prepared['origins']) == 3
old_keys = {row.get('origin_key') for row in old_failures}
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0,
        'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_PREPARATION_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:422] == old_failures and len(cp['failure_counters']) == 425
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['head'] = head
cp['work_in_progress'].update(
    handler38_source_integration_state='ACTUAL_MAIN_SOURCE_ONLY_FF38_CLOSED_PENDING_FRESH_COMBINED_VALIDATION',
    handler38_source_integration_completed_ref=pins['main38_completed'],
    handler38_source_integration_manifest_ref=pins['main38_manifest'],
    handler38_source_integration_outer_completion_ref=pins['main38_outer_completion'],
    handler38_source_integration_source_after_ref=pins['main38_source_after'],
    r322_r321_pending_origins_registered_refs=prepared['pending_origin_refs'],
    handler38_fresh_combined_validation_authorized=False,
    cli_exact8_source_integration_state='FUTURE_NEW_SCOPE_REQUIRED_AFTER_MAIN38_FORWARD_HEAD_REGISTRATION_AND_EVIDENCE_REVIEW',
    desktop_exact15_source_integration_state='PREPARATION_ONLY_FUTURE_ACTUAL_MAIN43_SCOPE_REQUIRED')
cp['failure_chains']['W05-99/r322-two-postcut-preparation-diagnostics'] = {
    'old422_prefix_unchanged': True, 'new_actual_nonzero_origins': 3,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
integration = ow['card_path_bindings']['W05-99']['subtasks']['handler38_main_source_integration']
assert integration['current_source_writer'] == 'codex:/root'
integration.update(current_source_writer=None, state='SOURCE_ONLY_FF38_CLOSED_PENDING_FRESH_COMBINED_VALIDATION',
    completed_ref=pins['main38_completed'], manifest_ref=pins['main38_manifest'], source_acceptance=False)
cp['next_command'] = 'Main38 actual source-only FF and forward head metadata are closed. Non-author review this closed evidence and actual post-registration audit; then new explicit CLI8 source import scope/register/grant to reach43, fresh combined43 compile and held2 CLI replays, Desktop15 import to58 and fresh169 Root replay under their own scopes. W09 finite-controller revision preparation only. Preserve all425 failures and require all22/all42 actual effective acceptances.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'ACTUAL_SOURCE_ONLY_MAIN38_FORWARD_HEAD_REGISTERED_AND_TWO_PENDING_AND_ONE_ROOT_PREPARATION_DIAGNOSTICS_APPENDED',
    'head_before': '2cdb0d43d5a600eef13c8f1735946a9adf52d079', 'head_after': head,
    'completed_ref': pins['main38_completed'], 'manifest_ref': pins['main38_manifest'],
    'failure_origins_before': 422, 'failure_origins_after': 425,
    'counter_reset': False, 'formal_increment': 0})
cp.update(revision=322, expected_previous_revision=321, updated_at=now, updated_by='codex:/root')
ow.update(revision=150, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [321, 322], 'ownership': [149, 150], 'failures': [422, 425]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root322.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root322.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [322, 150, 425]
    assert actual['failure_counters'][:422] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 322, 'ownership': 150, 'failure_origins': 425,
        'intent_ref': intent_ref, 'old422_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_exact38_source_only_FF_closed': True,
        'MAIN38_SOURCE_ONLY_CLOSED_NO_FURTHER_SOURCE_OR_PRODUCT_EXECUTION_GRANT': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r322-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'project_id': cp['project_id'], 'Main_head': head,
    'canonical_refs': [ref(path) for path in CANON], 'revision': 322, 'failure_origins': 425,
    'previous_handoff_ref': pins['previous_handoff'], 'counter_reset': False,
    'completed_ref': pins['main38_completed'], 'manifest_ref': pins['main38_manifest'],
    'next': cp['next_command'], 'source_acceptance': False, 'formal_increment': 0,
    'all22_and42_effective_acceptances_required': True})
print(json.dumps({'checkpoint': 322, 'ownership': 150, 'failure_origins': 425, 'handoff_ref': handoff_ref}, ensure_ascii=True))
