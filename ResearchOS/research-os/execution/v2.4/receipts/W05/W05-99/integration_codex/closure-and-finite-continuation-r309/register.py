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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [308, 136, 371]
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
cli = json.loads(read(pins['cli_scope']['path']))
listed = json.loads(read(pins['list_scope']['path']))
assert cli['owner'] == 'codex:/root/w05_merge_review'
assert cli['cli44_continuation']['candidate'] == 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
assert cli['cli44_continuation']['invocation_limit'] == 44 and cli['cli44_continuation']['leaf_limit'] == 145
assert cli['cli44_continuation']['prepared_manifest_v3_sha256'] == pins['cli_prepared_manifest']['sha256']
assert cli['cli44_continuation']['SDK_MODEL_EXTERNAL_PAID_CALLS'] == 0
assert listed['owner'] == 'codex:/root' and listed['source_commit'] == '534857db99fa5e694987f877af74c322eaa2a0b3'
assert len(listed['ordered_cases']) == 14 and len(listed['public_JEV_sources']) == 5
assert listed['maximum_loopback_HTTP_calls_including_setup'] == 224 and listed['SDK_worker_MODEL_external_paid_private'] == 0
assert cli['Main_product_source_writes'] == listed['Main_product_source_writes'] == 0
assert cli['source_acceptance'] is False and listed['source_acceptance'] is False
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
origins = prepared['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 8
for row in origins:
    assert row['origin_key'] not in old_keys and row['actual_outer_exit'] == 1
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:371] == old_failures and len(cp['failure_counters']) == 379
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(cli_exact8_independent_original_stopped_review_ref=pins['cli_old_review'],
    cli_exact8_independent_original_failure_ref=pins['cli_old_failure'],
    cli44_continuation_scope_ref=pins['cli_scope'], cli44_continuation_handoff_ref=pins['cli_prepared_handoff'],
    cli44_continuation_state='NONAUTHOR_NEW44_CLOSURE_SUPPLEMENT_AND_NOTRUN_AUTHORIZED',
    cli_exact8_independent_state='ORIGINAL47_STOPPED_CONTROLLER_CLOSURE_1_WITH5_NATIVE0_78LEAF_76COMPLETE',
    session_list_identity_independent_original_failure_ref=pins['list_old_failure'],
    session_list_identity_independent_scope_ref=pins['list_scope'],
    session_list_identity_independent_state='NONAUTHOR_NEW14_PUBLIC_JEV_EXPORT_AND_NEW_GRAPH_EXE_AUTHORIZED',
    provider_g2_finite_candidate_source_commit='8d0921b7c42ecd40300c58192d54af1064947aed',
    provider_g2_finite_candidate_evidence_commit='9a34aacbaeb775566e524f5af3518ea86a5d41b9',
    provider_g2_finite_candidate_handoff_ref=pins['g2_author_handoff'],
    provider_g2_finite_candidate_manifest_ref=pins['g2_author_manifest'],
    provider_g2_finite_nonauthor_static_review_ref=pins['g2_nonauthor_review'],
    provider_g2_finite_future_replay_scope_ref=pins['g2_future_scope'],
    provider_g2_finite_state='AUTHOR_FROZEN_STATIC_EXACT2_REVIEWED_NONAUTHOR_FINITE29_PENDING_NEW_GRANT',
    desktop_wire_scope_readonly_proposal_ref=pins['desktop_proposal'],
    desktop_wire_scope_readonly_handoff_ref=pins['desktop_handoff'],
    desktop_wire_scope_state='DESIGN_PROPOSAL_NON_READY_NO_SOURCE_EXECUTION_LEASE',
    cli_contract_source_ready=False, session_list_identity_source_ready=False)
chain = 'W05-99/r308-postcut-eight-original-tool-origins'
assert chain not in cp['failure_chains']
cp['failure_chains'][chain] = {'actual_failed_invocations': 8, 'distinct_actual_causes': 8,
    'actual_native_product_test_failures': 0, 'counter_reset': False, 'automatic_same_input_retry': False,
    'list_Go_dependency_tool_failure': 1, 'CLI_independent_controller_closure_failure': 1,
    'readonly_tool_failure_origins': 6, 'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut']}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
g2 = subtasks['provider_g2_finite_exact2']
assert g2['current_source_writer'] == 'codex:/root/sources_parent_impl'
g2.update(current_source_writer=None, source_commit='8d0921b7c42ecd40300c58192d54af1064947aed',
    receipt_commit='9a34aacbaeb775566e524f5af3518ea86a5d41b9', state='SOURCE_FROZEN_STOPPED_PENDING_NONAUTHOR_FINITE29',
    candidate_handoff_ref=pins['g2_author_handoff'], candidate_manifest_ref=pins['g2_author_manifest'],
    nonauthor_static_review_ref=pins['g2_nonauthor_review'], future_replay_scope_ref=pins['g2_future_scope'], source_ready=False)
original_cli = subtasks['cli_exact8_independent_replay']
assert original_cli['current_source_writer'] is None
original_cli.update(state='STOPPED_ORIGINAL_CONTROLLER_CLOSURE_FAILURE_NATIVE5_ZERO_76COMPLETE',
    stopped_review_ref=pins['cli_old_review'], original_failure_ref=pins['cli_old_failure'])
key = 'cli44_independent_continuation'
assert key not in subtasks
subtasks[key] = {'owner': cli['owner'], 'current_source_writer': None, 'paths': [],
    'responsibility': 'READONLY_FROZEN_CANDIDATE_INDEPENDENT_EXECUTION_ONLY', 'scope_ref': pins['cli_scope'],
    'candidate_source_commit': cli['cli44_continuation']['candidate'], 'future_exact_invocations': 44,
    'future_unique_leaves': 145, 'state': 'AUTHORIZED_NOT_EXECUTED', 'receipt_namespace': cli['cli44_continuation']['output'],
    'source_ready': False, 'source_acceptance': False, 'Main_product_source_writes': 0,
    'SDK_worker_MODEL_external_paid_private': 0, 'formal_increment': 0,
    'model': 'gpt-6-astra', 'reasoning_effort': 'high', 'model_selection_reason': 'Existing nonauthor verifier; no external model requests.'}
listed_sub = subtasks['session_list_identity_independent_replay']
assert listed_sub['current_source_writer'] is None
listed_sub['historical_failed_scope_ref'] = listed_sub['scope_ref']
listed_sub.update(scope_ref=pins['list_scope'], original_failure_ref=pins['list_old_failure'],
    receipt_namespace=listed['output'], state='NEW_PUBLIC5_COHORT_AUTHORIZED_NOT_EXECUTED')
cp['next_command'] = 'W05-99: W05 newCLI44 continuation145 expected plus original complete76 retained; Root newlist14 with five approved publicGo compiler sources/newgraph/newexe authorized afterCAS309. G2 Source8d092 writer released after freeze/static734, nonauthor29 newdriver preparation pending separate grant. Desktop23/141 design NON_READY, no sourcelease. Old371failureprefix+8actualtoolorigins=379, no reset. Main2cdb/allparents/formal0of42 remain unaccepted.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLI44_LIST14_NEW_INPUT_SCOPES_G2_FROZEN_DESKTOP_DESIGN_REGISTERED',
    'audit_ref': pins['audit'], 'cli_scope_ref': pins['cli_scope'], 'list_scope_ref': pins['list_scope'],
    'failure_origins_before': 371, 'failure_origins_after': 379, 'counter_reset': False,
    'G2_current_source_writer_released': True, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=309, expected_previous_revision=308, updated_at=now, updated_by='codex:/root')
ow.update(revision=137, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [308, 309], 'ownership': [136, 137], 'failures': [371, 379]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root309.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root309.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [309, 137, 379]
    assert actual['failure_counters'][:371] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 309, 'ownership': 137, 'failure_origins': 379,
        'intent_ref': intent_ref, 'old371_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_independent_CLI44_and_list14_execution_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r309-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 309, 'failure_origins': 379, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'current_card': 'W05-99', 'cli_scope_ref': pins['cli_scope'], 'list_scope_ref': pins['list_scope'],
    'G2_source_frozen_ref': pins['g2_author_handoff'], 'G2_nonauthor_static_ref': pins['g2_nonauthor_review'],
    'G2_next': 'New nonauthor29 prepare only; actual execution requires separate complete Root scope.',
    'CLI_next': '44 continuation145 expected unique leaves; original complete76 retained at original cohort. No full acceptance.',
    'list_next': 'New14 with publicJEV5 resources and freshcompiler; original zero-case go-list failure preserved.',
    'Desktop_next': 'Readonly23path141case design remainsNON_READY/no sourcelease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False, 'Main_integration_authorized': False,
    'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 309, 'ownership': 137, 'failure_origins': 379, 'handoff_ref': handoff_ref}, ensure_ascii=True))
