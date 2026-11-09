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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [317, 145, 410]
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
assert scope['registration_checkpoint'] == 318 and scope['case_count'] == 14
root_scope = json.loads(read(pins['root_scope']['path']))
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    assert not (ROOT / root_scope[field]).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert prepared['origins'] == [] and len(old_failures) == 410
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_root_finite14_scope_ref=pins['root_scope'],
    session_list_closedcopy_root_finite14_execution_scope_ref=pins['scope'],
    session_list_closedcopy_root_runner_review_ref=pins['runner_review'],
    session_list_closedcopy_root_author14_review_ref=pins['author14_review_ref'],
    session_list_closedcopy_root_finite14_state='ROOT_INDEPENDENT14_ACTUAL_CAS_BOUND_ONCE_LAUNCH_AFTER_SEAL',
    session_list_closedcopy_exact1_state='AUTHOR14_NONAUTHOR_SOURCE_EVIDENCE_REVIEW_READY_ROOT_INDEPENDENT14_NOT_STARTED',
    provider_g2_root_execution_audit_ref=pins['g2_execution_audit'],
    provider_g2_root_execution_manifest_ref=pins['g2_execution_manifest'],
    provider_g2_root_execution_state='ACTUAL_NONAUTHOR29_SEALED_4LOOPBACK_MODEL_13SNAPSHOTS_NOT_MAIN_FORMAL_ACCEPTANCE',
    r318_preserved_pending_failure_origin_refs=[pins['pending_frontier_lookup_origin'], pins['pending_desktop_revision_Node_origin']],
    r318_pending_failure_cut='Two actual origins preserved for immediate next serialized cut319; registered410 prefix unchanged, total observed at least412. Unrelated318 fixed execution snapshot is not a counter reset.')
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
assert ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']['current_source_writer'] is None
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'] = {
    'owner': 'codex:/root', 'current_source_writer': None, 'scope_ref': pins['scope'],
    'state': 'ROOT_NONAUTHOR_FIXED14_RUNTIME_ONCE_AFTER_SEAL', 'Main_product_source_writes': 0,
    'source_acceptance': False, 'formal_increment': 0}
cp['next_command'] = 'Root once-only actual sealed318 grant/independent fixed14 new source export+fresh compile+immutable full vectors+closed-copy/sidecars/wire proofs. Immediately next serialized319 cut preserves actual pending lookup8957bb and Desktop Node0bbcd5 as two separate original causes; 410 registered plus2 pending, no reset. Source317 targeted Desktop revision continues independently. G2 root29 actually sealed; source/wholeprovider/Main9/current formal remains unaccepted. After accepted list14 compose shared38 unique delta, then CLI43 fresh held2, Desktop58 after separate non-author readiness. All22/all42 still required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'ROOT_CLOSED_COPY_NONAUTHOR_FINITE14_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 410, 'failure_origins_after': 410, 'new_actual_nonzero_origins': 0,
    'counter_reset': False, 'G2_actual_non_author29_sealed_not_main': True, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=318, expected_previous_revision=317, updated_at=now, updated_by='codex:/root')
ow.update(revision=146, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [317, 318], 'ownership': [145, 146], 'failures': [410, 410]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root318.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root318.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [318, 146, 410]
    assert actual['failure_counters'][:410] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 318, 'ownership': 146, 'failure_origins': 410,
        'intent_ref': intent_ref, 'old410_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_Root_independent14_execution_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r318-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 318, 'failure_origins': 410, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'registered_failure_prefix': 410, 'preserved_pending_origin_refs': [pins['pending_frontier_lookup_origin'], pins['pending_desktop_revision_Node_origin']],
    'known_total_observed_failures_lower_bound': 412,
    'root_finite14_scope_ref': pins['root_scope'], 'root_finite14_execution_scope_ref': pins['scope'],
    'root_finite14_runner_review_ref': pins['runner_review'], 'G2_sealed29_ref': pins['g2_execution_audit'],
    'next': 'Root fixed14 once-only launch after registration seal; Source Desktop317 narrow revision continues. G2 actual29 sealed. Shared38/CLI43/Desktop58 source-only composition after respective acceptance gates.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 318, 'ownership': 146, 'failure_origins': 410, 'handoff_ref': handoff_ref}, ensure_ascii=True))
