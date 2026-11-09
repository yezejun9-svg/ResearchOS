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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [318, 146, 410]
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
assert scope['registration_checkpoint'] == 319 and scope['case_count'] == 14
root_scope = json.loads(read(pins['root_scope']['path']))
assert root_scope['python_flags'] == ['-I', '-S', '-X', 'utf8']
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    assert not (ROOT / root_scope[field]).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 3 and len(old_failures) == 410
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys
    assert item['actual_outer_exit'] == 1 or item['actual_native_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_OR_NODE_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:410] == old_failures and len(cp['failure_counters']) == 413
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_root_finite14_scope_ref=pins['root_scope'],
    session_list_closedcopy_root_finite14_execution_scope_ref=pins['scope'],
    session_list_closedcopy_root_runner_review_ref=pins['runner_review'],
    session_list_closedcopy_root_author14_review_ref=pins['author14_review_ref'],
    session_list_closedcopy_root_finite14_state='ROOT_NEW_NON_SITE_INDEPENDENT14_ACTUAL_CAS_BOUND_ONCE_LAUNCH_AFTER_SEAL',
    session_list_closedcopy_root_v2_prelaunch_failure_registered=True,
    r318_preserved_pending_failure_origins_registered_at=319,
    r318_pending_failure_cut='All three pending actual origins registered319; original410 prefix and Root318 failed auth retained.',
    provider_g2_bounded29_independent_review_ref=pins['g2_independent_review'],
    provider_g2_root_execution_state='ACTUAL_NONAUTHOR29_SEALED_AND_INDEPENDENT_EVIDENCE_CLOSED_BOUNDED_ONLY',
    desktop_http_exact15_revised_author_handoff_ref=pins['source_desktop_current_handoff'],
    desktop_http_exact15_revised_author_state='SOURCE06b1_FROZEN_NODE_CURRENT159_PLUS7_PLUS3_REPORTED_Go3_HISTORICAL_OS_LIMIT_RETAINED_NONAUTHOR_REVIEW_PENDING')
cp['failure_chains']['W05-99/r319-three-pending-actual-origins'] = {
    'original410_prefix_unchanged': True, 'new_actual_nonzero_origins': 3,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
desktop = ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']
assert desktop['current_source_writer'] == 'codex:/root/sources_parent_impl'
desktop.update(current_source_writer=None, last_source_writer='codex:/root/sources_parent_impl',
    state='SOURCE06b1_WRITER_STOPPED_CURRENT169_UNITS_REPORTED_Go3_LIMIT_RETAINED_REVIEW_PENDING',
    source_only_revision_commit='06b1fbcb5934cbc70e5d65a46481e60c05c6594b', final_handoff_ref=pins['source_desktop_current_handoff'])
assert ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']['current_source_writer'] is None
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'].update(
    scope_ref=pins['scope'], state='ROOT_V3_NON_SITE_FIXED14_ONCE_AFTER_SEAL', current_source_writer=None,
    source_acceptance=False, formal_increment=0)
cp['next_command'] = 'Root new-v3 non-site fixed14 once after actual319+seal, fresh exclusive grant/export/compile/immutable full vectors/closedcopy proofs. Original410+lookup8957bb+SourceNode0bbcd5+Rootprelaunch7783ca=413 retained. Source06b1 current159+7+3 reported; Go3 exact OS proof limit remains, next minimal extra receipt controller requires separate review/grant. G2 actual29 independent evidence closed bounded only. After accepted14 compose shared38 then CLI43/Desktop58 gates. All22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'ROOT_NON_SITE_FIXED14_NEW_INPUT_SCOPE_AND_THREE_ACTUAL_ORIGINS_REGISTERED',
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 410, 'failure_origins_after': 413, 'new_actual_nonzero_origins': 3,
    'counter_reset': False, 'G2_independent_bounded29_closed': True, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=319, expected_previous_revision=318, updated_at=now, updated_by='codex:/root')
ow.update(revision=147, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [318, 319], 'ownership': [146, 147], 'failures': [410, 413]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root319.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root319.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [319, 147, 413]
    assert actual['failure_counters'][:410] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 319, 'ownership': 147, 'failure_origins': 413,
        'intent_ref': intent_ref, 'old410_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_Root_non_site_independent14_execution_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r319-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 319, 'failure_origins': 413, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'root_finite14_scope_ref': pins['root_scope'], 'root_finite14_execution_scope_ref': pins['scope'],
    'root_finite14_runner_review_ref': pins['runner_review'], 'G2_independent_bounded29_ref': pins['g2_independent_review'],
    'desktop_source06b1_handoff_ref': pins['source_desktop_current_handoff'],
    'next': 'Root new-v3 non-site14 once after seal; Desktop non-author review and Go3 proof-only proposal; W09 readiness18 complete. All shared source integrations and current formal acceptance still HOLD.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 319, 'ownership': 147, 'failure_origins': 413, 'handoff_ref': handoff_ref}, ensure_ascii=True))
