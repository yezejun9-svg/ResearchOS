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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [309, 137, 379]
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
listed = json.loads(read(pins['list_scope']['path']))
assert listed['owner'] == 'codex:/root' and listed['source_commit'] == '534857db99fa5e694987f877af74c322eaa2a0b3'
assert len(listed['ordered_cases']) == 14 and len(listed['public_JEV_sources']) == 36
assert listed['maximum_loopback_HTTP_calls_including_setup'] == 224 and listed['SDK_worker_MODEL_external_paid_private'] == 0
g2scope = json.loads(read(pins['g2_scope']['path']))
assert g2scope['phases'] == ['prepare'] and g2scope['prepare_product_test_cases'] == 0
assert g2scope['candidate'] == '8d0921b7c42ecd40300c58192d54af1064947aed'
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
origins = prepared['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
for row in origins:
    assert row['origin_key'] not in old_keys and row['actual_outer_exit'] == 1
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:379] == old_failures and len(cp['failure_counters']) == 384
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(cli44_continuation_state='STOPPED_AFTER27_NATIVE0_WITH26_CLOSED_SELECTORS34_LEAVES_AND_WINDOWS4_UNCLOSED',
    cli44_stopped_review_ref=pins['cli_stopped_review'], cli44_late_failure_ref=pins['cli_late_failure'],
    cli17_continuation_scope_ref=pins['cli17_scope'], cli_windows4_continuation_scope_ref=pins['cli_windows4_scope'],
    cli_split_continuation_state='AUTHORIZED17_107_THEN_SEPARATE_WINDOWS1_4_NOT_EXECUTED',
    cli_split_prepared_handoff_ref=pins['cli_handoff'], cli_current_qualified_unique_leaves=110,
    session_list_identity_independent_scope_ref=pins['list_scope'],
    session_list_identity_second_failure_ref=pins['list_late_failure'],
    session_list_identity_independent_state='COMPLETE518_CATALOG_NEW713_EXPORT_GRAPH_EXE14_AUTHORIZED_NOT_EXECUTED',
    provider_g2_prepare_scope_ref=pins['g2_scope'], provider_g2_replay_preparation_ref=pins['g2_handoff'],
    provider_g2_finite_state='NONAUTHOR_PREPARE_ONLY_AUTHORIZED_EXECUTE29_REQUIRES_ACTUAL_PREPARED_HASH_NEW_GRANT',
    desktop_http_first_scope_review_ref=pins['desktop_review'], desktop_http_first_scope_conditions_ref=pins['desktop_conditions'],
    desktop_http_first_scope_state='REQUEST_CHANGES_NEW15PATH_DESIGN_PENDING_NO_SOURCE_WRITER',
    cli_contract_source_ready=False, session_list_identity_source_ready=False)
chain = 'W05-99/r309-postcut-five-original-tool-origins'
assert chain not in cp['failure_chains']
cp['failure_chains'][chain] = {'actual_failed_invocations': 5, 'counter_reset': False,
    'actual_product_test_failures': 0, 'automatic_same_input_retry': False,
    'list_dependency_tool': 1, 'CLI_controller_closure': 1, 'Desktop_readonly_locator': 3,
    'continued_Desktop_locator_after_two': True, 'Desktop_locator_branch_stopped': True,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut']}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert subtasks['cli44_independent_continuation']['current_source_writer'] is None
subtasks['cli44_independent_continuation'].update(state='STOPPED_NATIVE27_ZERO_26_CLOSED34_LEAVES_WINDOWS4_UNCLOSED',
    stopped_review_ref=pins['cli_stopped_review'], original_failure_ref=pins['cli_late_failure'])
for lane, key, scopekey in [('remaining17', 'cli17_independent_continuation', 'cli17_scope'),
                           ('windows4', 'cli_windows4_independent_continuation', 'cli_windows4_scope')]:
    cli = json.loads(read(pins[scopekey]['path']))
    grant = cli['cli_bounded_continuation']
    assert cli['owner'] == 'codex:/root/w05_merge_review' and cli['registration_checkpoint'] == 310
    assert grant['candidate'] == 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251' and grant['lane'] == lane
    assert grant['prepared_manifest_sha256'] == pins['cli_manifest']['sha256']
    assert grant['invocation_limit'] == (17 if lane == 'remaining17' else 1)
    assert grant['leaf_limit'] == (107 if lane == 'remaining17' else 4)
    assert grant['SDK_MODEL_EXTERNAL_PAID_CALLS'] == 0 and cli['source_acceptance'] is False
    assert key not in subtasks and not Path(grant['output']).exists()
    subtasks[key] = {'owner': cli['owner'], 'current_source_writer': None, 'paths': [],
        'responsibility': 'READONLY_FROZEN_CANDIDATE_INDEPENDENT_EXECUTION_ONLY', 'scope_ref': pins[scopekey],
        'candidate_source_commit': grant['candidate'], 'future_exact_invocations': grant['invocation_limit'],
        'future_unique_leaves': grant['leaf_limit'], 'state': 'AUTHORIZED_NOT_EXECUTED',
        'receipt_namespace': grant['output'], 'source_ready': False, 'source_acceptance': False,
        'Main_product_source_writes': 0, 'SDK_worker_MODEL_external_paid_private': 0, 'formal_increment': 0}
listed_sub = subtasks['session_list_identity_independent_replay']
assert listed_sub['current_source_writer'] is None and not Path(listed['output']).exists()
listed_sub.setdefault('historical_failed_scope_refs', []).append(listed_sub['scope_ref'])
listed_sub.update(scope_ref=pins['list_scope'], latest_failure_ref=pins['list_late_failure'],
    receipt_namespace=listed['output'], state='COMPLETE_PUBLIC_CATALOG_NEW713_GRAPH_EXE14_AUTHORIZED_NOT_EXECUTED')
assert 'provider_g2_independent_prepare' not in subtasks
subtasks['provider_g2_independent_prepare'] = {'owner': 'codex:/root', 'current_source_writer': None, 'paths': [],
    'scope_ref': pins['g2_scope'], 'state': 'PREPARE_ONLY_AUTHORIZED_NOT_EXECUTED',
    'future_execute_cases': 29, 'prepare_cases': 0, 'source_acceptance': False,
    'receipt_namespace': g2scope['output_root'], 'Main_product_source_writes': 0, 'formal_increment': 0}
cp['next_command'] = 'W05-99: CLI separate17/107 thenWindows1/4 scopes; retain110 prior closed unique leaves. Root complete518catalog export713/newgraph/exe list14. G2 nonauthor prepare only; future29 needs actual preparedSHA and new immutable grant. Desktop new15path proposal pending, no sourcewriter. Preserve old379 plus5 actualorigins=384, Main2cdb and all22/42 acceptance HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLI_SPLIT_COMPLETE_PUBLIC_CATALOG_G2_PREPARE_ONLY_REGISTERED',
    'audit_ref': pins['audit'], 'failure_origins_before': 379, 'failure_origins_after': 384,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=310, expected_previous_revision=309, updated_at=now, updated_by='codex:/root')
ow.update(revision=138, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [309, 310], 'ownership': [137, 138], 'failures': [379, 384]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root310.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root310.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [310, 138, 384]
    assert actual['failure_counters'][:379] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 310, 'ownership': 138, 'failure_origins': 384,
        'intent_ref': intent_ref, 'old379_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_CLI17_Windows4_list14_and_G2_prepare_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r310-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 310, 'failure_origins': 384, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'current_card': 'W05-99', 'cli17_scope_ref': pins['cli17_scope'], 'cli_windows4_scope_ref': pins['cli_windows4_scope'],
    'list_scope_ref': pins['list_scope'], 'g2_prepare_scope_ref': pins['g2_scope'],
    'Desktop_next': 'Review refined exact15 proposal; no product/source execution lease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 310, 'ownership': 138, 'failure_origins': 384, 'handoff_ref': handoff_ref}, ensure_ascii=True))
