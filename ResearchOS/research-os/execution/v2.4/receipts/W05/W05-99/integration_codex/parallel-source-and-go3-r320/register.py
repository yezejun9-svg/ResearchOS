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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [319, 147, 413]
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
assert scope['registration_checkpoint'] == 320
w09_scope = json.loads(read(pins['w09_scope']['path']))
go3_scope = json.loads(read(pins['go3_scope']['path']))
assert w09_scope['Go_compile'] == w09_scope['Go_test'] == w09_scope['SQL'] == w09_scope['HTTP'] == 0
assert not (ROOT / w09_scope['worktree_root']).exists()
assert not Path(go3_scope['new_output_root']).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 4 and len(old_failures) == 413
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_READONLY_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:413] == old_failures and len(cp['failure_counters']) == 417
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(w09_causal_exact4_source_scope_ref=pins['w09_scope'],
    w09_causal_exact4_state='EXACT4_SOURCE_APPEND_AND_STATIC_FORMAT_ONLY_NO_COMPILE_TEST_GRANT',
    desktop_http_exact15_revision_independent_review_ref=pins['desktop_revision_review'],
    desktop_http_exact15_revised_author_state='06b1_CURRENT_NODE169_INDEPENDENTLY_REVIEWED_Go3_HISTORICAL_OS_GAP_RETAINED',
    desktop_go3_debug_component_scope_ref=pins['go3_scope'],
    desktop_go3_debug_component_state='ONCE_PROOF_AUTHORIZED_ONLY_AFTER_ACTUAL320_SEAL_AND_ROOT_GRANT_NO_SOURCE_ACCEPTANCE',
    r319_postcut_actual_diagnostics_registered_at=320)
cp['failure_chains']['W05-99/r320-four-readonly-diagnostics'] = {
    'old413_prefix_unchanged': True, 'new_actual_nonzero_origins': 4,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] is None
assert 'W09-99' not in ow['card_path_bindings']
ow['card_path_bindings']['W09-99'] = {'owner': 'codex:/root',
    'amendment': 'Exact4 isolated test-source-only subtask; parent actual acceptance and registry remain Root serial.',
    'subtasks': {'causal_test_source_exact4': {'owner': 'codex:/root/sources_parent_impl',
        'current_source_writer': 'codex:/root/sources_parent_impl', 'scope_ref': pins['w09_scope'],
        'source_paths': w09_scope['source_paths'], 'worktree_root': w09_scope['worktree_root'],
        'state': 'AUTHOR_SOURCE_IMPLEMENTATION_ONLY_AFTER_SEAL', 'source_acceptance': False, 'formal_increment': 0}}}
ow['card_path_bindings']['W13-03']['subtasks']['go3_debug_component_root_once'] = {
    'owner': 'codex:/root', 'current_source_writer': None, 'scope_ref': pins['go3_scope'],
    'state': 'ROOT_FIXED_COMPONENT_ONCE_AFTER_SEAL_GRANT', 'source_acceptance': False, 'formal_increment': 0}
cp['next_command'] = 'After actual320+seal: Source implement exact4 appended W09 tests/static format only in own2cdb worktree; no compiler/SQL/tests yet. Root creates exact sealed-authority grant and runs Go3 debug-component once. Finish actual319 Root14 proof closure/source review before new shared38 integration scope, fresh CLI43/Desktop58. All417 original failures kept, all22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'W09_EXACT4_SOURCE_ONLY_AND_ROOT_GO3_FIXED_DEBUG_COMPONENT_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 413,
    'failure_origins_after': 417, 'new_actual_nonzero_origins': 4, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=320, expected_previous_revision=319, updated_at=now, updated_by='codex:/root')
ow.update(revision=148, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [319, 320], 'ownership': [147, 148], 'failures': [413, 417]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root320.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root320.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [320, 148, 417]
    assert actual['failure_counters'][:413] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 320, 'ownership': 148, 'failure_origins': 417,
        'intent_ref': intent_ref, 'old413_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'W09_source_only_and_Root_Go3_execution_scopes_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r320-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 320, 'failure_origins': 417, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'W09_source_only_scope_ref': pins['w09_scope'], 'Go3_component_execution_scope_ref': pins['go3_scope'],
    'Root14_existing319_scope_ref': pins['root14_scope'], 'Root14_relaunch_granted': False,
    'next': 'Source exact4 W09 source-only; Root Go3 once after sealed grant; Root14 actual closure then new shared source integration scope. All22/all42 remain required.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 320, 'ownership': 148, 'failure_origins': 417, 'handoff_ref': handoff_ref}, ensure_ascii=True))
