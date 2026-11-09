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
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [302, 130, 330]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == prepared['head'] == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
for item in prepared['all_verified_refs']:
    actual = ref(item['path'], item['sha256'])
    assert actual['bytes'] == item['bytes']
refs = prepared['pins']
audit_ref = prepared['audit_ref']
assert audit_ref['sha256'] == 'e5ee549d9dc5401ee755ea25bad804d1e8ae3d49f560dbe7cd88858c04d62bc0'
assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']
audit = json.loads(read(audit_ref['path']))
assert audit['refs'] == refs and audit['canonical_before'] == prepared['canonical_before']
assert len(audit['manifests']) == 8 and all(row['bad'] == 0 for row in audit['manifests'])
origins = audit['origins']
assert len(origins) == len({row['origin_key'] for row in origins}) == 8
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
for row in origins:
    assert row['origin_key'] not in old_keys
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:330] == old_failures and len(cp['failure_counters']) == 338
scope = json.loads(read(refs['cli_implementation_scope']['path']))
assert scope['status'] == 'AUTHORIZED_BY_CAS303_ONLY_NOT_EXECUTED'
assert scope['base_commit'] == '22752a6a41732c8c158d7d7e1b8932ec958f8cb8'
assert len(scope['paths']) == len(set(scope['paths'])) == 8
assert len(scope['approved_exact_regression_selectors']) == 21
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
work = cp['work_in_progress']
work.update(provider_whole9_g1_readonly_nonauthor_review_ref=refs['g1_review'],
    provider_whole9_g1_state='LIMITED_ORIGINAL_NATIVE_EVIDENCE_NONSELF_REVIEWED_ORIGINAL_HARNESS_FAILURES_PRESERVED',
    provider_independent_whole9_source_ready=False,
    f08_type_boundary_nonauthor_review_ref=refs['f08_type_review'],
    f08_startup_caller21_proposal_ref=refs['f08_caller_proposal'],
    f08_startup_caller21_nonauthor_review_ref=refs['f08_caller_review'],
    f08_startup_caller21_conditions_ref=refs['f08_conditions'],
    f08_type_boundary_state='EXACT21_SCOPE_READY_WITH_IMPLEMENTATION_CONDITIONS_NO_SQL24_LEASE',
    cli_exact8_proposal_ref=refs['cli_proposal'], cli_exact8_nonauthor_review_ref=refs['cli_review'],
    cli_exact8_implementation_scope_ref=refs['cli_implementation_scope'],
    cli_contract_diagnostic_state='EXACT8_AUTHOR_IMPLEMENTATION_AUTHORIZED_P01_P03_P04_ONLY_P02_HELD',
    cli_real_resume_producer_gap_ref=refs['resume_gap'],
    provider_g2_finite_proposal_ref=refs['g2_proposal'], provider_g2_finite_selectors_ref=refs['g2_selectors'],
    provider_g2_finite_runner_ref=refs['g2_runner'],
    provider_g2_causal_state='FINITE18_COMPONENT_PLUS11_NATIVE_PLAN_REGISTERED_NO_SOURCE_EDIT_OR_EXECUTION_LEASE')
chain = cp['failure_chains']['W05-99/provider-whole9-g1-alias-preparation']
assert chain['actual_failed_invocations'] == 2 and chain['same_cause_failures'] == 1
chain.update(state='LIMITED_ORIGINAL_NATIVE_EVIDENCE_NONSELF_REVIEWED_BOTH_HARNESS_FAILURES_PRESERVED',
    readonly_nonauthor_review_ref=refs['g1_review'], counter_reset=False, automatic_retry=False)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert 'cli_exact8_protocol_repair' not in subtasks
subtasks['cli_exact8_protocol_repair'] = {'owner': 'codex:/root/sources_parent_impl', 'integrator': 'codex:/root',
    'verifier': 'NONAUTHOR_REVIEW_REQUIRED_NO_SELF_ACCEPTANCE', 'worktree': scope['worktree'],
    'branch': scope['branch'], 'base_commit': scope['base_commit'], 'paths': scope['paths'],
    'scope_ref': refs['cli_implementation_scope'], 'proposal_ref': refs['cli_proposal'],
    'nonauthor_scope_review_ref': refs['cli_review'],
    'state': 'EXACT8_ISOLATED_AUTHOR_IMPLEMENTATION_AND_FINITE_TESTS_AUTHORIZED_NOT_ACCEPTED',
    'current_source_writer': 'codex:/root/sources_parent_impl',
    'receipt_namespace': 'execution/v2.4/receipts/W05/W05-99/cli_protocol_exact8_executor_codex/**',
    'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_selection_reason': 'Current inherited agent implements schema/authority/transaction-sensitive CLI repair; external preference DeepSeek-v4.1-flash retained for ResearchOS model resources, no new paid model call.',
    'Main_or_frozen_handler_authorWT_writes': 0, 'P02_SQL_provider_frozen_contract_writes': 0,
    'formal_increment': 0, 'source_ready': False}
subtasks['provider_whole9_g1_independent'].update(state=work['provider_whole9_g1_state'], source_ready=False,
    readonly_nonauthor_review_ref=refs['g1_review'])
subtasks['f08_whole_scope_readonly_review'].update(state=work['f08_type_boundary_state'],
    type_boundary_nonauthor_review_ref=refs['f08_type_review'], startup_caller21_proposal_ref=refs['f08_caller_proposal'],
    startup_caller21_nonauthor_review_ref=refs['f08_caller_review'], mandatory_conditions_ref=refs['f08_conditions'],
    SQL24_implementation_lease=False, SQL24_source_lease=False)
ow['path_lease_transfers'].append({'at': now, 'actor': 'codex:/root',
    'new_subtask': 'W05-99/cli_exact8_protocol_repair', 'new_owner': 'codex:/root/sources_parent_impl',
    'new_worktree': scope['worktree'], 'paths': scope['paths'], 'scope_ref': refs['cli_implementation_scope'],
    'kind': 'ISOLATED_NEW_WORKTREE_CURRENT_WRITER_LEASE_OLD_MAIN_AND_FROZEN38_HISTORY_PRESERVED',
    'old_worktrees_and_receipts_unchanged': True})
cp['next_command'] = 'W05-99: Source implement isolated exact8 CLI P01/P03/P04 with full frozen-schema/authority gates,37 scenario rows and exact21 original regressions; actual leaf roster must freeze before cases, -failfast, independent cache/closedDB. P02 real Goal/Run pause/resume and fullformalCLI held. W05 frozen handler38 independent A-E/C09 continues under unchanged scope, first unexpected stops. F08 exact21 source scope ready with12 implementation conditions but SQL24 lease false. G2 finite29 test-only proposal registered awaiting free construction slot/new lease. All original failures and0/42formal retained.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'CLI_EXACT8_NONSELF_SCOPE_LEASE_AND_G1_F08_G2_BOUNDED_PROGRESS_REGISTERED',
    'audit_ref': audit_ref, 'root_review_ref': prepared['root_review_ref'],
    'CLI_scope_ref': refs['cli_implementation_scope'], 'CLI_nonauthor_scope_review_ref': refs['cli_review'],
    'G1_nonauthor_limited_review_ref': refs['g1_review'], 'F08_caller21_scope_review_ref': refs['f08_caller_review'],
    'failure_origins_before': 330, 'failure_origins_after': 338, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=303, expected_previous_revision=302, updated_at=now, updated_by='codex:/root')
ow.update(revision=131, amended_at=now, amended_by='codex:/root')
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
    'transition': {'checkpoint': [302, 303], 'ownership': [130, 131], 'failures': [330, 338]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root303.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root303.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual = json.loads(CANON[0].read_bytes())
    actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [303, 131, 338]
    assert actual['failure_counters'][:330] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 303, 'ownership': 131, 'failure_origins': 338,
        'intent_ref': intent_ref, 'old330_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r303-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 303, 'failure_origins': 338,
    'counter_reset': False, 'audit_ref': audit_ref, 'previous_handoff_ref': refs['previous_handoff'],
    'current_card': 'W05-99', 'CLI_implementation_scope_ref': refs['cli_implementation_scope'],
    'CLI': 'Source authorized on new isolated exact22752 branch to fix exact8/P01/P03/P04.37scenario NOT_RUN+4HOLD, exact21 original regression roster, before-case actual leaves freeze/failfast/independent cache. Original69IDs/26failures remain. P02/fullformal held; no source acceptance.',
    'handler': 'Frozen38 A-E/C09 independent execution running under unchanged CAS301 scope+CAS302 corrected15pathspec12resource. Preparation/compile progress does not constitute source acceptance; actual final outcome to register separately.',
    'provider': 'Original G1 limited native3Go/13pass and26JS child0 independently adjudicated, originalouter1/taskkill128/chain2 retained. G2 finite18helper+11native plan recorded; no test2 edits/execution yet, construction slot/new scope lease required. No whole9 acceptance.',
    'F08': 'Exact21 scope now nonauthor SOURCE_SCOPE_READY_WITH_MANDATORY_IMPLEMENTATION_CONDITIONS. OriginalSQL34/281/14 unchanged. Source/SQL24 implementation lease false; installed engine fingerprint and future40+12 controls not yet executed.',
    'resume_gap_ref': refs['resume_gap'], 'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 303, 'ownership': 131, 'failure_origins': 338, 'handoff_ref': handoff_ref}, ensure_ascii=True))
