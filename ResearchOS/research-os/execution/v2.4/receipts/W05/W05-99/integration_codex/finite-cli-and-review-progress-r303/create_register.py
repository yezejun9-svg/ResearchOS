import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
source = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/handler-resource-and-diagnostics-r302/register.py'
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '6b5d004b5e046ec6ca7de40bf9d283317c48ca13f4b635f96c4f5edb9caedf6e'
original = raw.decode('utf-8')
header_end = original.index("g1 = json.loads(read(refs['g1_result']['path']))")
tail_start = original.index('for path, raw in before.items():')
tail_end = original.index("handoff_ref = save('handoff-r302-running.json'")
header = original[:header_end]
replacements = {
    '[301, 129, 322]': '[302, 130, 330]',
    "08bfa673a21a32c8ec4f0b79b888c22210999bea35be6b5dea9f7c7cb8aa69d5": 'e5ee549d9dc5401ee755ea25bad804d1e8ae3d49f560dbe7cd88858c04d62bc0',
    "assert prepared['root_review_ref']['sha256'] == '008b5dc2cce224f566430ea03d502b2cd475c398ee8638ab544d3d4a559bbe93'": "assert ref(prepared['root_review_ref']['path'], prepared['root_review_ref']['sha256']) == prepared['root_review_ref']",
    'len(audit[\'manifests\']) == 5': 'len(audit[\'manifests\']) == 8',
    'assert cp[\'failure_counters\'][:322] == old_failures and len(cp[\'failure_counters\']) == 330': 'assert cp[\'failure_counters\'][:330] == old_failures and len(cp[\'failure_counters\']) == 338',
}
for old, new in replacements.items():
    assert old in header, old
    header = header.replace(old, new)
business = '''scope = json.loads(read(refs['cli_implementation_scope']['path']))
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
'''
tail = original[tail_start:tail_end]
replacements = {
    '.root302.tmp': '.root303.tmp',
    "'checkpoint': [301, 302], 'ownership': [129, 130], 'failures': [322, 330]": "'checkpoint': [302, 303], 'ownership': [130, 131], 'failures': [330, 338]",
    '[302, 130, 330]': '[303, 131, 338]',
    "actual['failure_counters'][:322]": "actual['failure_counters'][:330]",
    "'checkpoint': 302, 'ownership': 130, 'failure_origins': 330": "'checkpoint': 303, 'ownership': 131, 'failure_origins': 338",
    "'old322_prefix_unchanged'": "'old330_prefix_unchanged'",
}
for old, new in replacements.items():
    assert old in tail, old
    tail = tail.replace(old, new)
handoff = '''handoff_ref = save('handoff-r303-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
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
'''
generated = (header + business + tail + handoff).encode('utf-8')
compile(generated, str(OUT / 'register.py'), 'exec')
with (OUT / 'register.py').open('xb') as stream:
    stream.write(generated)
print('register.py ' + hashlib.sha256(generated).hexdigest() + ' bytes=' + str(len(generated)))
