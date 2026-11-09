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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [305, 133, 348]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == prepared['head'] == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
for item in prepared['all_verified_refs']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
refs = prepared['pins']
audit_ref = prepared['audit_ref']
assert audit_ref['sha256'] == '8ca871571432b8b6d8d5f63768421621f492b63baaf5bec78cd70249be484ad5'
assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 6 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 14
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:348] == old_failures and len(cp['failure_counters']) == 362
scope = json.loads(read(refs['list_identity_fix_execution_scope']['path']))
hold = json.loads(read(refs['main_integration_hold']['path']))
assert scope['status'] == 'AUTHORIZED_BY_CAS306_ONLY_NOT_EXECUTED'
assert scope['source_paths'] == ['internal/domain/client_protocol_sessions.go', 'internal/api/v2_sessions_test.go']
assert scope['owner'] == 'codex:/root/command_queue_impl'
assert scope['cases'] == 14 and scope['maximum_loopback_HTTP'] == 224
assert scope['SDK_worker_model_external_paid_calls'] == 0 and scope['Source_cli8_frozen_handler_author_Main_canonical_writes'] == 0
assert scope['source_ready'] is False and scope['formal_increment'] == 0
assert hold['status'] == 'HOLD_CONFIRMED_PUBLIC_SESSION_LIST_IDENTITY500' and hold['Main_source_writes_authorized'] is False
assert json.loads(read(refs['handler_final_review']['path']))['decision'] == 'SOURCE_READY_HANDLER38_WITH_DECLARED_OPEN_PRODUCT_GATES'
assert json.loads(read(refs['list_adverse_nonauthor_review']['path']))['decision'] == 'CONFIRMED_RESPONSE_IDENTITY_BOUNDARY_DEFECT_MAIN_INTEGRATION_HOLD'
assert json.loads(read(refs['list_fix_scope_review']['path']))['decision'] == 'SOURCE_SCOPE_READY_WITH_MANDATORY_WIRE_CLASSIFICATION'
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(configuration_handler_historical_final_positive_ref=refs['handler_final_review'],
    configuration_handler_historical_final_manifest_ref=refs['handler_manifest'],
    configuration_handler_historical_final_handoff_ref=refs['handler_handoff'],
    configuration_handler_final_source_ready=False,
    configuration_handler_scope_state='HISTORICAL_AE_C09_POSITIVES_PRESERVED_CURRENT_MAIN_INTEGRATION_HOLD_PUBLIC_SESSION_LIST_IDENTITY500',
    configuration_handler_main_integration_hold_ref=refs['main_integration_hold'],
    configuration_handler_current_adverse_nonauthor_ref=refs['list_adverse_nonauthor_review'],
    session_list_identity_exact2_scope_ref=refs['list_identity_fix_execution_scope'],
    session_list_identity_scope_nonauthor_ref=refs['list_fix_scope_review'],
    session_list_identity_wire_conditions_ref=refs['list_fix_conditions'],
    session_list_identity_state='EXACT2_CANDIDATE_WRITER_AUTHORIZED_14_FUTURE_CASES_NOT_RUN_MAIN_HOLD',
    session_list_identity_source_ready=False,
    cli_exact8_development_failure_handoff_refs=[refs['CLI_' + name] for name in [
        'r305-first-failure', 'r305-second-failure', 'r305-read-atomic-failure',
        'r305-read-config-failure', 'r305-admitted-disconnect-failure']],
    cli_exact8_pending_postcut_cursor_ref=refs['pending_postcut_cursor_failure'],
    cli_contract_source_ready=False,
    attach_lease_original_proposal_ref=refs['lease_original_proposal'],
    attach_lease_revision_correction_ref=refs['lease_revision_correction'],
    attach_lease_source_edit_execution_authorized=False,
    cli_real_resume_producer_continuation_ref=refs['root_resume_findings'],
    handler_main_protected_resource_vector_ref=refs['protected_resources'])
chain_key = 'W05-99/r305-fixedcut14-cli-and-readonly-origins'
assert chain_key not in cp['failure_chains']
cp['failure_chains'][chain_key] = {'actual_failed_invocations': 14, 'distinct_actual_causes': 14,
    'native_test_batch_failures': 5, 'unknown_native_outer_nonzero_diagnostics': 8,
    'native_git128_outer0_locator_failure': 1, 'counter_reset': False,
    'automatic_same_input_retry': False, 'audit_ref': audit_ref,
    'pending_postcut_cursor_ref': refs['pending_postcut_cursor_failure'],
    'state': 'SEALED14_IMPORTED_ONCE_OLD348PREFIX_PRESERVED_PENDING_LATER_ORIGINS_NEXT_CAS'}
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert 'session_list_identity_exact2' not in subtasks
subtasks['session_list_identity_exact2'] = {
    'owner': scope['owner'], 'current_source_writer': scope['owner'], 'integrator': 'codex:/root',
    'verifier': 'NONAUTHOR_REVIEW_REQUIRED_NO_SELF_ACCEPTANCE', 'worktree': scope['worktree'],
    'branch': scope['branch'], 'base_commit': scope['base_commit'], 'paths': scope['source_paths'],
    'scope_ref': refs['list_identity_fix_execution_scope'], 'proposal_ref': refs['list_fix_proposal'],
    'nonauthor_scope_review_ref': refs['list_fix_scope_review'], 'wire_conditions_ref': refs['list_fix_conditions'],
    'state': work['session_list_identity_state'], 'source_ready': False, 'future_cases': 14,
    'maximum_loopback_HTTP': 224, 'SDK_worker_model_external_paid_calls': 0,
    'Main_integration_hold_ref': refs['main_integration_hold'], 'formal_increment': 0,
    'receipt_namespace': 'execution/v2.4/receipts/W05/W05-99/session_list_identity_exact2_executor_codex/**',
    'Main_frozen_handler_AuthorWT_SourceCLI_SQL_schema_globalidentity_writes': 0,
    'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_selection_reason': 'Inherited current agent writes the two-file public list identity fix; DeepSeek-v4.1-flash preference retained for ResearchOS external provider resources, no new paid model call.'}
subtasks['cli_exact8_protocol_repair'].update(current_public_nonnull_session_list='HOLD_PUBLIC_PRODUCER500_NO_SID_CLEAR_BYPASS',
    development_failure_handoff_refs=work['cli_exact8_development_failure_handoff_refs'],
    pending_postcut_cursor_ref=refs['pending_postcut_cursor_failure'], source_ready=False)
cp['next_command'] = 'W05-99: Cmd exact2 from22752 mirrors list response context SID only after existing project/principal/session owner checks, preserves globalidentity/schema/SQL and old tests, follows nonauthor wire conditions L02 shared-principal readonly and L05/L06/L14 actual short409/400. Freeze14 finite leaves/new full compiler/testmain/importcfg/NEW executable/alltableDB before cases; stop first unexpected. Source CLI exact8 continues scoped affected and unrun regressions, preserves old failures/strong terminal semantics and raw-beforeDecode; existing nonnull-list interactions HOLD pending producer. Main source integration remains HOLD despite historical handler A-E+C09 green. Attach lease revision correction readonly/no executionlease; P02/F08/G2/live gates OPEN. Old348prefix+14actualorigins preserved, later cursor/Goal failure origins nextCAS, formal0/42/all22 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'PUBLIC_LIST_IDENTITY500_MAIN_HOLD_AND_NONAUTHOR_BOUND_EXACT2_REPAIR_AUTHORIZED',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'list_scope_ref': refs['list_identity_fix_execution_scope'],
    'historical_handler_positive_ref': refs['handler_final_review'],
    'current_adverse_review_ref': refs['list_adverse_nonauthor_review'],
    'main_integration_hold_ref': refs['main_integration_hold'],
    'failure_origins_before': 348, 'failure_origins_after': 362, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=306, expected_previous_revision=305, updated_at=now, updated_by='codex:/root')
ow.update(revision=134, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [305, 306], 'ownership': [133, 134], 'failures': [348, 362]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'main_integration_authorized': False, 'list_exact2_candidate_only': True,
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root306.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root306.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [306, 134, 362]
    assert actual['failure_counters'][:348] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 306, 'ownership': 134, 'failure_origins': 362,
        'intent_ref': intent_ref, 'old348_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_source_integration_HOLD': True,
        'list_source2_candidate_only': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r306-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 306, 'failure_origins': 362,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'list_exact2_scope_ref': refs['list_identity_fix_execution_scope'],
    'main_integration_hold_ref': refs['main_integration_hold'],
    'handler': 'Original A-E and corrected C09 six copiedDB controls green preserved; public session.list nonnullSID500 confirmed independently, current Main integration suspended; never execute old draft integrate_main.py.',
    'CLI': 'Exact8 scoped development continues; legal new-created-owned send actual durable BLOCKED3 permitted; existing nonnull-list interactions HOLD. No source/formal acceptance. Later cursor and Goal batch origins preserved pending nextCAS.',
    'producer_list': 'Exact2 new isolated22752 worktree with strict context ownership checks and SID mirror;14 future finite cases allNOT_RUN; wire L02 readonly same principal/differentwriter and L05/L06/L14 short409/400 conditions mandatory; fresh full compile/new exe/alltable guards;0SDK/external/paid.',
    'attach_lease_P02_provider_F08': 'Lease original proposal corrected renewal revision unchanged only readonly, no product/edit/executionlease. P02 realMu pause/resume gap remains. G2 finite29/F0821 future scopes no executionlease; full asynchronous attach stillOPEN.',
    'pending_postcut_cursor_ref': refs['pending_postcut_cursor_failure'],
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 306, 'ownership': 134, 'failure_origins': 362, 'handoff_ref': handoff_ref}, ensure_ascii=True))
