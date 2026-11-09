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
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
prepared = json.loads(read(OUT / 'prepared_refs.json'))
before = {path: path.read_bytes() for path in CANON}
for path, pin in zip(CANON, prepared['canonical_before']):
    assert path == ROOT / pin['path'] and ref(path) == pin
assert len(prepared['canonical_before']) == 4
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [307, 135, 367]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == prepared['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
for item in prepared['verified_refs']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
pins = prepared['pins']
cli = json.loads(read(pins['cli_scope']['path']))
listed = json.loads(read(pins['list_scope']['path']))
assert cli['owner'] == 'codex:/root/w05_merge_review'
assert cli['cli47_execution']['candidate'] == 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
assert cli['cli47_execution']['invocation_limit'] == 47 and cli['cli47_execution']['leaf_limit'] == 221
assert cli['cli47_execution']['SDK_MODEL_EXTERNAL_PAID_CALLS'] == 0
assert listed['owner'] == 'codex:/root' and listed['source_commit'] == '534857db99fa5e694987f877af74c322eaa2a0b3'
assert len(listed['ordered_cases']) == 14 and listed['maximum_loopback_HTTP_calls_including_setup'] == 224
assert listed['SDK_worker_MODEL_external_paid_private'] == 0
assert cli['Main_product_source_writes'] == listed['Main_product_source_writes'] == 0
assert cli['source_acceptance'] is False and listed['source_acceptance'] is False
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
origins = prepared['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 4
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:367] == old_failures and len(cp['failure_counters']) == 371
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(cli_exact8_independent_source_static_review_ref=pins['cli_static_review'],
    cli_exact8_independent_scope_ref=pins['cli_scope'],
    cli_exact8_independent_prepared_handoff_ref=pins['cli_prepared_handoff'],
    cli_exact8_independent_prepared_manifest_ref=pins['cli_prepared_manifest'],
    cli_exact8_independent_state='NONAUTHOR_FINITE47_AUTHORIZED_NEW_GRAPH_NEW_EXE_NOT_YET_EXECUTED',
    session_list_identity_independent_scope_ref=pins['list_scope'],
    session_list_identity_independent_state='NONAUTHOR_ROOT_FINITE14_AUTHORIZED_NEW_GRAPH_NEW_EXE_NOT_YET_EXECUTED',
    cli_contract_source_ready=False, session_list_identity_source_ready=False)
chain = 'W05-99/r307-postcut-four-readonly-tool-origins'
assert chain not in cp['failure_chains']
cp['failure_chains'][chain] = {'actual_failed_invocations': 4, 'distinct_actual_causes': 4,
    'actual_native_product_test_failures': 0, 'unknown_native_outer_nonzero_locator_origins': 2,
    'actual_native_readonly_python_failures': 2, 'counter_reset': False,
    'automatic_same_input_retry': False, 'audit_ref': pins['audit']}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert subtasks['cli_exact8_protocol_repair']['current_source_writer'] is None
assert subtasks['session_list_identity_exact2']['current_source_writer'] is None
for key, scope, scope_ref, owner in [
    ('cli_exact8_independent_replay', cli, pins['cli_scope'], cli['owner']),
    ('session_list_identity_independent_replay', listed, pins['list_scope'], listed['owner']),
]:
    assert key not in subtasks
    subtasks[key] = {'owner': owner, 'current_source_writer': None, 'responsibility': 'READONLY_FROZEN_CANDIDATE_INDEPENDENT_EXECUTION_ONLY',
        'source_paths': [], 'scope_ref': scope_ref, 'candidate_source_commit': scope.get('source_commit', scope.get('cli47_execution', {}).get('candidate')),
        'future_exact_invocations': 47 if key.startswith('cli_') else 14, 'state': 'AUTHORIZED_NOT_EXECUTED',
        'receipt_namespace': scope['output'], 'source_ready': False, 'source_acceptance': False,
        'Main_product_source_writes': 0, 'SDK_worker_MODEL_external_paid_private': 0, 'formal_increment': 0,
        'model': 'gpt-6-astra', 'reasoning_effort': 'high',
        'model_selection_reason': 'Inherited existing verifier, exact typed source and native evidence validation. ResearchOS external preference deepseek-v4.1-flash retained; no paid model request.'}
cp['next_command'] = 'W05-99: Source G2 new6fb exact2 test-only construction continues under307 scope. W05 nonauthor CLI8 b987 finite47/new fullgraph/newexe and Root nonauthor list2 534 finite14/API<=224/newfullgraph/newexe authorized afterCAS308. No author selfacceptance/MainFF/SDKpaid/privatecall; old Main public-list HOLD remains until new independent source evidence reviewed. Old367 failureprefix preserved plus4 readonly origins; later339800 G2 locator pending nextCAS. Lease6/24/Mu pause restore18/Desktop strict wire remain future bounded branches. all22+42 effectiveaccept required; formal0/42.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'NONAUTHOR_CLI47_LIST14_FINITE_EXECUTION_SCOPES_REGISTERED_NO_SOURCE_ACCEPTANCE',
    'audit_ref': pins['audit'], 'cli_scope_ref': pins['cli_scope'], 'list_scope_ref': pins['list_scope'],
    'failure_origins_before': 367, 'failure_origins_after': 371, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=308, expected_previous_revision=307, updated_at=now, updated_by='codex:/root')
ow.update(revision=136, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [307, 308], 'ownership': [135, 136], 'failures': [367, 371]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root308.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root308.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [308, 136, 371]
    assert actual['failure_counters'][:367] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 308, 'ownership': 136, 'failure_origins': 371,
        'intent_ref': intent_ref, 'old367_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'new_independent_CLI47_and_list14_execution_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r308-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 308, 'failure_origins': 371, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'current_card': 'W05-99', 'cli_scope_ref': pins['cli_scope'], 'list_scope_ref': pins['list_scope'],
    'G2': 'Independent Source G2 test2 construction under307 continues; no other source writer granted.',
    'CLI': 'Frozenb987 exact8, nonauthor47 invocation221expectedleaf authorized. Actual results not claimed. Existing2 list500/P01-03 realAPI/trueattach/P02/fullharness HOLD.',
    'list': 'Frozen534 exact2, nonauthorRoot14 publicHTTP<=224/newGoGraph/newexe/closedSQLite typed multiset and wire checks authorized. Actual results not claimed; Main old22752 integration remains HOLD.',
    'pending_after_cut': 'Source G2 readonly locator339800 pending nextCAS; no repeated original causes or reset.',
    'current_effective_formal_status': cp['current_effective_formal_status'], 'all22_and42_effective_acceptances_required': True,
    'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 308, 'ownership': 136, 'failure_origins': 371, 'handoff_ref': handoff_ref}, ensure_ascii=True))
