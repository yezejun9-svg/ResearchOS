import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
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
    sha = hashlib.sha256(raw).hexdigest()
    assert expected is None or sha == expected, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}


def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)


lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
before = {path: path.read_bytes() for path in CANON}
prepared = json.loads(read(OUT / 'prepared_refs.json'))
assert len(prepared['canonical_before']) == 4
for path, pin in zip(CANON, prepared['canonical_before']):
    assert path == ROOT / pin['path']
    assert hashlib.sha256(before[path]).hexdigest() == pin['sha256'] and len(before[path]) == pin['bytes']
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [306, 134, 362]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == prepared['head'] == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
for item in prepared['all_verified_refs']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
refs = prepared['pins']
audit_ref = prepared['audit_ref']
assert audit_ref['sha256'] == '5a7e79f05fed9ca3e99ffea84b8972a48ee7d8d5d5df81a4abbf73c3bf914de7'
assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 5 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:362] == old_failures and len(cp['failure_counters']) == 367
scope = json.loads(read(refs['g2_finite_execution_scope']['path']))
assert scope['status'] == 'AUTHORIZED_BY_CAS307_ONLY_NOT_EXECUTED'
assert scope['owner'] == 'codex:/root/sources_parent_impl'
assert scope['source_paths'] == ['internal/domain/runtime_provider_binding_windows_test.go', 'internal/domain/runtime_coordinator_windows_test.go']
assert scope['component_cases'] == 18 and scope['native_cases'] == 11 and len(scope['ordered_cases']) == 29
assert scope['loopback_MODEL_max'] == 4 and scope['external_paid_private_calls'] == 0
assert scope['frozen_CLI8_list2_Main_SQL_SDK_lock_production_source_writes'] == 0
assert scope['source_ready'] is False and scope['formal_increment'] == 0
cli = json.loads(read(refs['cli_final_handoff']['path']))
list_candidate = json.loads(read(refs['list_candidate_handoff']['path']))
assert cli['source_commit'] == 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
assert cli['current_source_writer'] == 'STOPPED_AND_FROZEN_PENDING_NONAUTHOR_REVIEW'
assert list_candidate['source_commit'] == '534857db99fa5e694987f877af74c322eaa2a0b3'
assert list_candidate['source_acceptance'] is False and list_candidate['Main_HOLD'] is True
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(cli_exact8_frozen_candidate_source_commit=cli['source_commit'],
    cli_exact8_frozen_candidate_evidence_commit='60b9c00c648ec3110b31e6f5c6740cc105fc4c16',
    cli_exact8_frozen_candidate_handoff_ref=refs['cli_final_handoff'],
    cli_exact8_frozen_candidate_source_manifest_ref=refs['cli_source_manifest'],
    cli_exact8_frozen_candidate_scenario_coverage_ref=refs['cli_scenario_coverage'],
    cli_exact8_frozen_candidate_current_leaf_coverage_ref=refs['cli_current_leaf_coverage'],
    cli_exact8_frozen_candidate_namespace_manifest_ref=refs['cli_manifest'],
    cli_exact8_frozen_candidate_closure_ref=refs['cli_closure'],
    cli_contract_diagnostic_state='FROZEN_AUTHOR_SOURCE8_99_NEW_PLUS122_REGRESSION_REPORTED_EXISTING2_LAYER_GAP_ATTACH_P02_FULLHARNESS_HOLD_NONAUTHOR_PENDING',
    cli_contract_source_ready=False,
    session_list_identity_candidate_source_commit=list_candidate['source_commit'],
    session_list_identity_candidate_handoff_ref=refs['list_candidate_handoff'],
    session_list_identity_candidate_report_ref=refs['list_candidate_report'],
    session_list_identity_candidate_manifest_ref=refs['list_candidate_manifest'],
    session_list_identity_state='FROZEN_AUTHOR_SOURCE2_14_ACTUAL_PASS_REPORTED_NONAUTHOR_PENDING_MAIN_HOLD',
    session_list_identity_source_ready=False,
    provider_g2_finite_execution_scope_ref=refs['g2_finite_execution_scope'],
    provider_g2_finite_new_executor='codex:/root/sources_parent_impl',
    provider_g2_finite_state='SOURCE_EXACT2_TEST_ONLY_NEW_EXECUTOR_AUTHORIZED_29_FUTURE_CASES_NOT_RUN',
    attach_lease_synchronous_scope_proposal_ref=refs['lease_sync_proposal'],
    attach_lease_synchronous_finite24_ref=refs['lease_sync_cases'],
    attach_lease_source_edit_execution_authorized=False,
    mu_pause_checkpoint_sdk_readonly_review_ref=refs['mu_sdk_readonly_review'],
    mu_pause_checkpoint_sdk_readonly_handoff_ref=refs['mu_sdk_readonly_handoff'],
    mu_pause_checkpoint_closed_source_scope=False,
    desktop_response_boundary_readonly_findings_ref=refs['desktop_response_findings'])
chain_key = 'W05-99/r305-postcut-cli3-and-readonly2'
assert chain_key not in cp['failure_chains']
cp['failure_chains'][chain_key] = {'actual_failed_invocations': 5, 'distinct_actual_causes': 5,
    'native_cli_test_batch_failures': 3, 'native_readonly_python_failure': 1,
    'outer_nonzero_unknown_native_locator': 1, 'counter_reset': False,
    'automatic_same_input_retry': False, 'audit_ref': audit_ref,
    'state': 'FIVE_ORIGINAL_ORIGINS_IMPORTED_ONCE_OLD362PREFIX_PRESERVED'}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
subtasks['cli_exact8_protocol_repair'].update(current_source_writer=None,
    source_writer_state='STOPPED_FROZEN_PENDING_NONAUTHOR_REVIEW',
    candidate_source_commit=cli['source_commit'],
    candidate_handoff_ref=refs['cli_final_handoff'],
    candidate_manifest_ref=refs['cli_manifest'], state=work['cli_contract_diagnostic_state'], source_ready=False)
subtasks['session_list_identity_exact2'].update(current_source_writer=None,
    source_writer_state='STOPPED_FROZEN_PENDING_NONAUTHOR_REVIEW',
    candidate_source_commit=list_candidate['source_commit'],
    candidate_handoff_ref=refs['list_candidate_handoff'],
    candidate_manifest_ref=refs['list_candidate_manifest'], state=work['session_list_identity_state'], source_ready=False)
assert 'provider_g2_finite_exact2' not in subtasks
subtasks['provider_g2_finite_exact2'] = {
    'owner': scope['owner'], 'current_source_writer': scope['owner'], 'integrator': 'codex:/root',
    'verifier': 'NONAUTHOR_REVIEW_REQUIRED_NO_SELF_ACCEPTANCE', 'worktree': scope['worktree'],
    'branch': scope['branch'], 'base_commit': scope['base_commit'], 'paths': scope['source_paths'],
    'scope_ref': refs['g2_finite_execution_scope'],
    'proposal_ref': refs['provider_g2_finite_proposal_ref'],
    'nonauthor_scope_review_ref': refs['provider_g2_finite_nonauthor_root_scope_review_ref'],
    'conditions_ref': refs['provider_g2_finite_nonauthor_root_conditions_ref'],
    'selectors_ref': refs['provider_g2_finite_selectors_ref'],
    'state': work['provider_g2_finite_state'], 'source_ready': False,
    'future_cases': 29, 'component_cases': 18, 'native_cases': 11, 'loopback_MODEL_max': 4,
    'API_loopback_setup_HTTP_separately_counted': True, 'external_paid_private_calls': 0,
    'formal_increment': 0, 'receipt_namespace': scope['new_receipt_namespace'],
    'frozen_CLI8_list2_Main_SQL_SDK_lock_production_source_writes': 0,
    'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_selection_reason': 'Inherited existing agent handles typed budget/effect/transaction sensitive finite controls. External ResearchOS model preference deepseek-v4.1-flash retained; no external or paid model request.'}
cp['next_command'] = 'W05-99: frozen CLI8 b987 and list2 534 candidates await independent current source/finite replay, neither author evidence selfaccepts or removes Main public-list500 HOLD. Source released CLI writer and now owns isolated6fb G2 exact2 test-only newWT:18 component then11native precise selectors, new wholegraph/compiler/generated testmain/importcfg/NEWexe, readonly bundle497e,4MODEL loopback max with API setup separate, externalpaid0, original cause/budget UNKNOWN intact, firstunexpected stop/no autoretry. Lease6/24, MuSDK finishTurn/transcript18 and Desktop response boundary remain readonly future proposals; true attach/P02/fullharness/fullprovider/live/parent/formal OPEN. Old362prefix plus5postcut origins retained; later independent CLI locator dc40e0 pending nextCAS. all22+42 accepted required, formal0/42.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'CLI8_LIST2_FROZEN_NOT_ACCEPTED_AND_G2_TEST2_NEW_WRITER_AUTHORIZED',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'g2_scope_ref': refs['g2_finite_execution_scope'],
    'cli_candidate_handoff_ref': refs['cli_final_handoff'],
    'list_candidate_handoff_ref': refs['list_candidate_handoff'],
    'failure_origins_before': 362, 'failure_origins_after': 367,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=307, expected_previous_revision=306, updated_at=now, updated_by='codex:/root')
ow.update(revision=135, amended_at=now, amended_by='codex:/root')
for row in [audit_ref, prepared['root_review_ref'], *refs.values()]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
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
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)),
    'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [306, 307], 'ownership': [134, 135], 'failures': [362, 367]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'main_integration_authorized': False, 'g2_test_exact2_candidate_only': True,
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root307.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root307.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [307, 135, 367]
    assert actual['failure_counters'][:362] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 307, 'ownership': 135, 'failure_origins': 367,
        'intent_ref': intent_ref, 'old362_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'g2_testsource2_candidate_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r307-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 307, 'failure_origins': 367,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'g2_testsource2_scope_ref': refs['g2_finite_execution_scope'],
    'CLI_candidate_handoff_ref': refs['cli_final_handoff'], 'list_candidate_handoff_ref': refs['list_candidate_handoff'],
    'CLI': 'Frozen8 source b987/evidence60b9 clean writer stopped; author current99 newleaf+122 regressionleaf21groups reported. Existing2 public-list500, P01-03 realAPI layer gap, trueattach/P02/fullharness held. Independent static/replay pending, no self acceptance.',
    'list': 'Frozen2 source534 reported14 actualPASS/78loopbackHTTP/newexe/frozen15461/0drift, newfailure0. Pending nonauthor review; Main old22752 integration still HOLD.',
    'G2': 'New Source owner isolated6fb test2 lease: exact18 component then11native, beforeTask actualGoal budget, typed Fault and original MODEL cause/budget chain,4MODEL loopback max,0external/paid, fresh fullgraph/generatedfiles/newexe.29allNOT_RUN/no source acceptance.',
    'future': 'Lease sync6/24 readonly, Mu SDK actualfinishTurn+transcript restore static18 NOTRUN/no closed edit scope, Desktop response boundary readonly/no editlease. Preserve all oldRun/effects/budgets/failures and no fake ACK completion.',
    'pending_after_cut': 'Independent CLI readonly dc40e0 single actualPython1 origin sealed, nextCAS; sixcc diagnostic outer0 not fabricated nativefailure.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 307, 'ownership': 135, 'failure_origins': 367, 'handoff_ref': handoff_ref}, ensure_ascii=True))
