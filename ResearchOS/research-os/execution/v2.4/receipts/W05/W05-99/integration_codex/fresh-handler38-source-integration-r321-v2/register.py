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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [320, 148, 417]
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
assert scope['registration_checkpoint'] == 321 and scope['expected_registration'] == [321, 149, 422]
assert scope['owner'] == 'codex:/root' and scope['max_source_FF_operations'] == 1
assert scope['target_source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 5 and len(old_failures) == 417
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0,
        'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_READONLY_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:417] == old_failures and len(cp['failure_counters']) == 422
assert len(prepared['pending_origin_refs']) == 2
for item in prepared['pending_origin_refs']:
    ref(item['path'], item['sha256'])
cp['work_in_progress']['r321_cut_pending_actual_tool_origin_refs'] = prepared['pending_origin_refs']
cp['work_in_progress']['observed_actual_tool_origin_lower_bound_after_r321_cut'] = 424
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(
    session_list_identity_source_ready=True,
    session_list_identity_state='BOUNDED14_LIST_FIX_INDEPENDENTLY_VERIFIED_DECLARED_OPEN_PRODUCT_GATES_RETAINED',
    session_list_closedcopy_exact1_state='AUTHOR14_AND_ROOT14_CLOSED_WITH_NONAUTHOR_BOUNDED_REVIEW',
    session_list_closedcopy_root_finite14_state='ROOT14_CLOSED_14_NATIVE_PASS_0SKIP_78HTTP_NO_INPUT_DRIFT_NO_RERUN',
    session_list_closedcopy_root_finite14_evidence_review_ref=pins['root14_review'],
    session_list_closedcopy_root_finite14_sealed_audit_ref=pins['root14_audit'],
    handler38_source_integration_scope_ref=pins['scope'],
    handler38_source_integration_controller_review_ref=pins['integration_controller_review'],
    handler38_source_integration_state='REGISTERED_EXACT38_SOURCE_ONLY_FF_AFTER_SEAL_AND_ROOT_ONCE_GRANT',
    handler38_source_integration_target=scope['target_source_commit'],
    desktop_go3_debug_component_state='CLOSED_NEW_DEBUG_COMPONENT_INDEPENDENTLY_REVIEWED_OLD_NORMAL_MODE_GAP_RETAINED',
    desktop_go3_debug_component_closed_audit_ref=pins['go3_audit'],
    desktop_go3_debug_component_evidence_review_ref=pins['go3_review'],
    w09_causal_exact4_state='SOURCE4_INDEPENDENT_STATIC_REVIEWED_WRITER_STOPPED_NO_COMPILE_OR_TEST_GRANT',
    w09_causal_exact4_source_commit='cd0d818baa703fbc59a6f7c8187d467d41570094',
    w09_causal_exact4_author_handoff_ref=pins['w09_handoff'],
    w09_causal_exact4_static_source_review_ref=pins['w09_review'])
cp['failure_chains']['W05-99/r321-five-readonly-diagnostics'] = {
    'old417_prefix_unchanged': True, 'new_actual_nonzero_origins': 5,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
w09_source = ow['card_path_bindings']['W09-99']['subtasks']['causal_test_source_exact4']
assert w09_source['current_source_writer'] == 'codex:/root/sources_parent_impl'
w09_source.update(current_source_writer=None, state='SOURCE4_INDEPENDENT_STATIC_REVIEWED_NOT_COMPILED',
    source_only_commit='cd0d818baa703fbc59a6f7c8187d467d41570094', author_handoff_ref=pins['w09_handoff'],
    static_source_review_ref=pins['w09_review'])
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'].update(
    state='CLOSED_ROOT14_NONAUTHOR_BOUNDED_EVIDENCE_REVIEW_READY', evidence_review_ref=pins['root14_review'])
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1'].update(
    state='BOUNDED14_SOURCE_FIX_READY_WITH_OPEN_PRODUCT_GATES', source_ready=True,
    root_evidence_review_ref=pins['root14_review'])
ow['card_path_bindings']['W05-99']['subtasks']['handler38_main_source_integration'] = {
    'owner': 'codex:/root', 'current_source_writer': 'codex:/root',
    'scope_ref': pins['scope'], 'controller_review_ref': pins['integration_controller_review'],
    'state': 'ROOT_SOURCE_ONLY_FF38_AFTER_SEAL_AND_EXACT_GRANT',
    'target_source_commit': scope['target_source_commit'], 'source_paths_ref': scope['source_paths_ref'],
    'source_acceptance': False, 'formal_increment': 0}
ow['card_path_bindings']['W13-03']['subtasks']['go3_debug_component_root_once'].update(
    state='CLOSED_NEW_DEBUG_COMPONENT_NONAUTHOR_EVIDENCE_REVIEW_READY', evidence_review_ref=pins['go3_review'])
cp['next_command'] = 'After actual321+seal, Root issue exact once source-only38 FF grant and execute reviewed controller to a5d6. Preserve old11D and empty index. Forward-only metadata follow-up then fresh combined43 CLI and58 Desktop compilation/replays under distinct scopes. W09 source4 frozen NOT_RUN, controller preparation only. All422 registered origins plus2pending aftercut and all22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'BOUNDED_ROOT14_GO3_CLOSED_AND_FRESH_EXACT38_SOURCE_ONLY_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'],
    'failure_origins_before': 417, 'failure_origins_after': 422,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=321, expected_previous_revision=320, updated_at=now, updated_by='codex:/root')
ow.update(revision=149, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [320, 321], 'ownership': [148, 149], 'failures': [417, 422]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT', 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root321.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root321.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [321, 149, 422]
    assert actual['failure_counters'][:417] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 321, 'ownership': 149, 'failure_origins': 422,
        'intent_ref': intent_ref, 'old417_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_exact38_FF_scope_registered_only': True,
        'BOUNDED14_GO3_CLOSED_W09_STOPPED_FRESH_SOURCE_ONLY38_SCOPE': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r321-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'project_id': cp['project_id'], 'Main_head': head,
    'canonical_refs': [ref(path) for path in CANON], 'revision': 321, 'failure_origins': 422,
    'previous_handoff_ref': pins['previous_handoff'], 'counter_reset': False,
    'source_only38_scope_ref': pins['scope'], 'root14_review_ref': pins['root14_review'],
    'go3_review_ref': pins['go3_review'], 'w09_author_handoff_ref': pins['w09_handoff'],
    'next': cp['next_command'], 'source_acceptance': False,
    'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT',
    'all22_and42_effective_acceptances_required': True, 'formal_increment': 0})
print(json.dumps({'checkpoint': 321, 'ownership': 149, 'failure_origins': 422, 'handoff_ref': handoff_ref}, ensure_ascii=True))
