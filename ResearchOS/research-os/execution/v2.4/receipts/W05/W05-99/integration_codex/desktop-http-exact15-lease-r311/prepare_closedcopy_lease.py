import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
CURRENT = Path(__file__).resolve().parent
OUT = CURRENT.parent / 'session-list-closedcopy-exact1-r312'
assert not OUT.exists()
OUT.mkdir()
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
RECEIPTS = BASE / 'receipts/W05/W05-99'
CAUSE = RECEIPTS / 'session_list_identity_closedcopy_cause_review_codex/18ceca998ff94984aa58fb304e081453'
CLI = RECEIPTS / 'cli_exact8_independent_replay_codex/cli18-r310-audit-dd830b9adb8042619d155cd7fde4b05c'
WT = ROOT / '.local/worktrees/codex-w0599-session-list-proof-r312'
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def pin(path, expected=None):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)


def script(name, source):
    ast.parse(source)
    with (OUT / name).open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return pin(OUT / name)


cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [311, 139, 384]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079' and not WT.exists()
pins = {}
for key, path, expected in [
    ('previous_handoff', CURRENT / 'handoff-r311-running.json', '28412e045eb1a25d38a8a1d4527d67a6f9f4d0c0f090693a40765e1e7eeb3913'),
    ('root_failure', CURRENT.parent / 'root-list14-launch-r310/failure_origin.json', '6503124cc34e7ec26e407030a7b34cd365d8d7c69ad27062cf0eb363915dc757'),
    ('root_failure_manifest', CURRENT.parent / 'root-list14-launch-r310/manifest.json', '91eb5b9d95543a1fa1a5cd621ee463aec4c7c35bba15614169b0e953f3150278'),
    ('cause_review', CAUSE / 'review.json', '0af0ae73aa0d7d33bb051b065f7c56736db88d3db9df97fd34aad846a2b7267e'),
    ('cause_scope', CAUSE / 'scope_proposal.json', 'ad48c547301d64886c55c845c00cab4d2d2247f8b18632d9ae780c70853fb7e5'),
    ('cause_failure', CAUSE / 'failure_origins.json', '36f392ce3cb86beba41aa83e7ae8a893442f0cf01e801403e9a52b4f1d55f08c'),
    ('cause_manifest', CAUSE / 'manifest.json', '5786fe27e5369389e691e86cfc02a889dcc7f082b5460ea8f0255b4b0dc99e85'),
    ('cli221_review', CLI / 'review.json', '02fad7cb55d9e2d191a8de5b4e0935ba6ffcebdf27b03596921e659ede245da8'),
    ('cli221_handoff', CLI / 'handoff.json', '900217ea74d2583826de599163d28c877fa5f924920b15b01efd4b80bf9ba786'),
    ('cli221_manifest', CLI / 'manifest.json', 'b1f8c8af7ac20f26e78c5e8bdba3d3255882aa8e0365ced1948a49e308ddc595')]:
    pins[key] = pin(path, expected)
original = ROOT / '.local/independent-session-list-r310-534857db-public-plan/internal/api/v2_sessions_test.go'
source_before = pin(original, 'e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0')
pins['source_bounds'] = save('source_before.json', {'paths': [{'path': 'internal/api/v2_sessions_test.go',
    'exists_before': True, 'sha256': source_before['sha256'], 'bytes': source_before['bytes']}],
    'source_commit': '534857db99fa5e694987f877af74c322eaa2a0b3', 'actual_exported_file_ref': source_before,
    'protected_domain_sha256': '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3'})
pins['scope'] = save('scope_registration.json', {'schema': 'researchos.session-list-closedcopy-exact1-source-lease.v1',
    'status': 'AUTHORIZED_BY_CAS312_ONLY_NOT_STARTED', 'owner': 'codex:/root/command_queue_impl',
    'root_integrator': 'codex:/root', 'independent_reviewer': 'codex:/root/w05_merge_review',
    'card': 'W05-99', 'registration_checkpoint': 312, 'project_id': cp['project_id'], 'Main_head': head,
    'base_commit': '534857db99fa5e694987f877af74c322eaa2a0b3', 'worktree': str(WT),
    'branch': 'codex/w0599-session-list-proof-r312', 'exact_paths': ['internal/api/v2_sessions_test.go'],
    'path_bounds_ref': pins['source_bounds'], 'independent_cause_review_ref': pins['cause_review'],
    'correction_scope_ref': pins['cause_scope'], 'original_failure_ref': pins['root_failure'],
    'changes': 'Only new appended readonlyCopyOpen and sessionListFixture.closeEvidence: closed original and absent originalsidecars, exclusive fresh copy, correctly escaped mode=ro&immutable=1 copy-only open, actual before/after copy sidecar absence, actual Close/read errors; no delete or relaxed check.',
    'protected': ['Original14633byte test body hash c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1',
        'Original14 selectors/business/command/schema/permission/journal/raw/HTTP controls', 'All mainDB bytes/schema/columns/typedrow multiset checks',
        'internal/domain/client_protocol_sessions.go hash7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3',
        'Root independent check_closed assertions', 'Original raw DB/WAL/SHM/proofs/inputs/failed output'],
    'execution': {'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224,
        'fresh_binary_and_fixtures': True, 'actual_full_compiler_graph_and_generated_WORK_archive_closure': True,
        'SDK_MODEL_Node_external_paid_private_calls': 0},
    'build_outputs': 'Fresh own-worktree cache/WORK/exe and own receipt fixture directories only; no old DB/cache/output overwrites.',
    'receipt_root': str(WT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'),
    'source_commit_rule': 'Commit exactly one test path; receipts separately, product/domain/schema/locks/SDK/Main/registry excluded.',
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'counter_reset': False,
    'maximum_active_construction_tasks': 2, 'other_live_source_writer': 'Source Desktop exact15 dedicated worktree, disjoint paths',
    'Main_product_source_writes': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'scope_limits': 'Test evidence correction only; Main40/CLI composition/held2/fullharness/attach/P02/all22/42 remain unaccepted.'})
rootfailure = json.loads(read(ROOT / pins['root_failure']['path']))
reviewfailure = json.loads(read(CAUSE / 'failure_origins.json'))
assert len(reviewfailure) == 1
row = reviewfailure[0]
origins = [{'origin_key': rootfailure['origin_key'], 'actor': 'codex:/root', 'actual_outer_exit': 1,
    'actual_native_exit': 1, 'actual_native_case_exit': 0, 'product_test_failures': 0,
    'cause': rootfailure['cause'], 'evidence_ref': pins['root_failure']},
    {'origin_key': row['origin_id'], 'actor': row['actor'], 'actual_outer_exit': row['outer_exit'],
     'actual_native_exit': row['native_exit'], 'product_test_failures': 0, 'cause': row['error'],
     'evidence_ref': pins['cause_failure'], 'json_pointer': '/0', 'original_payload': row, 'raw_file_available': False}]
assert not {x['origin_key'] for x in origins}.intersection({x.get('origin_key') for x in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 384, 'after': 386, 'origins': origins,
    'counter_reset': False, 'actual_product_native_test_failures': 0})
old_source = (CURRENT / 'register.py').read_text('utf-8')
header = old_source[:old_source.index("pins = prepared['pins']")]
header = header.replace('[310, 138, 384]', '[311, 139, 384]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 312 and scope['owner'] == 'codex:/root/command_queue_impl'
assert scope['exact_paths'] == ['internal/api/v2_sessions_test.go'] and not Path(scope['worktree']).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 2
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and row['actual_outer_exit'] == 1
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:384] == old_failures and len(cp['failure_counters']) == 386
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_exact1_scope_ref=pins['scope'],
    session_list_closedcopy_exact1_state='TEST_ONLY_SOURCE_LEASE_GRANTED_WORKTREE_CREATION_PENDING',
    session_list_identity_independent_state='STOPPED_FIRST_NATIVE0_CLOSED_COPY_SIDECARS_PRESENT_13_NOTRUN',
    session_list_identity_independent_latest_failure_ref=pins['root_failure'],
    session_list_identity_independent_cause_review_ref=pins['cause_review'],
    cli_current_qualified_unique_leaves=221, cli_exact8_221_finite_review_ref=pins['cli221_review'],
    cli_exact8_221_finite_handoff_ref=pins['cli221_handoff'],
    cli_split_continuation_state='FINITE_UNIQUE_UNION221_COMPLETE_PENDING_MAIN_COMPOSITION_HELD2',
    cli_contract_source_ready=False, session_list_identity_source_ready=False)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert 'session_list_closedcopy_exact1' not in subtasks
subtasks['session_list_closedcopy_exact1'] = {'owner': scope['owner'], 'current_source_writer': scope['owner'],
    'worktree': scope['worktree'], 'base_commit': scope['base_commit'], 'paths': scope['exact_paths'],
    'scope_ref': pins['scope'], 'state': 'SOURCE_LEASE_GRANTED_WORKTREE_CREATION_PENDING',
    'source_ready': False, 'source_acceptance': False, 'Main_product_source_writes': 0, 'formal_increment': 0}
subtasks['session_list_identity_independent_replay'].update(state='STOPPED_FIRST_NATIVE0_CLOSED_COPY_SIDECARS',
    latest_failure_ref=pins['root_failure'], nonauthor_cause_review_ref=pins['cause_review'])
for key in ['cli17_independent_continuation', 'cli_windows4_independent_continuation']:
    subtasks[key].update(state='FINITE_SCOPE_COMPLETED_NO_SOURCE_ACCEPTANCE', finite_review_ref=pins['cli221_review'])
chain = 'W05-99/r310-closed-copy-controller-and-readonly-locator'
assert chain not in cp['failure_chains']
cp['failure_chains'][chain] = {'actual_failed_invocations': 2, 'product_native_test_failures': 0,
    'original384_prefix_unchanged': True, 'counter_reset': False, 'automatic_same_input_retry': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut']}
cp['next_command'] = 'Source Desktop exact15 implementation active. Cmd exact1 closedcopy evidence helper correction/new14 lease registered, fresh own worktree; preserve original native0/controller1 and13NOTRUN. CLI unique221 complete, Main/held2/formal HOLD. G2prepare remains own actual process. Failure384+2=386, no reset; all22/42 current acceptance stillopen.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSED_COPY_EXACT1_TEST_LEASE_AND_CLI221_FINITE_UNION_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 384,
    'failure_origins_after': 386, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=312, expected_previous_revision=311, updated_at=now, updated_by='codex:/root')
ow.update(revision=140, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old_source[old_source.index('for path, raw in before.items():'):old_source.index("handoff_ref = save('handoff-r311-running.json'")]
tail = tail.replace('root311.tmp', 'root312.tmp').replace('[311, 139, 384]', '[312, 140, 386]')
tail = tail.replace('[310, 311]', '[311, 312]').replace('[138, 139]', '[139, 140]').replace('[384, 384]', '[384, 386]')
tail = tail.replace("'checkpoint': 311", "'checkpoint': 312").replace("'ownership': 139", "'ownership': 140").replace("'failure_origins': 384", "'failure_origins': 386")
tail = tail.replace("'new_Desktop_exact15_source_lease_only': True", "'new_closedcopy_exact1_source_lease_and_CLI221_finite_record_only': True")
handoff = '''handoff_ref = save('handoff-r312-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 312, 'failure_origins': 386, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'new_closedcopy_scope_ref': pins['scope'], 'CLI221_review_ref': pins['cli221_review'],
    'next': 'Root creates dedicated closedcopy exact1 worktree; Cmd implements minimal new test evidence correction. Source Desktop exact15 remains independently active. G2 prepare still actual process; no execute29 grant yet.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 312, 'ownership': 140, 'failure_origins': 386, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = (CURRENT / 'run.py').read_text('utf-8').replace('root_registration_r311_readonly_review_codex', 'root_registration_r312_readonly_review_codex')
wrapper = wrapper.replace("review['reviewer'] == 'codex:/root/command_queue_impl'", "review['reviewer'] == 'codex:/root/w05_merge_review'")
wrapper = wrapper.replace("review['expected_before'] == [310, 138, 384] and review['expected_after'] == [311, 139, 384]", "review['expected_before'] == [311, 139, 384] and review['expected_after'] == [312, 140, 386]")
wrapper = wrapper.replace("cp['revision'] == 310 and len(cp['failure_counters']) == 384", "cp['revision'] == 311 and len(cp['failure_counters']) == 384")
wrapped = script('run.py', wrapper)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [311, 139, 384], 'expected_after': [312, 140, 386],
    'scope_ref': pins['scope'], 'cause_ref': pins['cause_review'], 'CLI221_ref': pins['cli221_review'],
    'new_origins': origins, 'counter_reset': False, 'old384_prefix_unchanged': True,
    'Source_Desktop_scope_writer_preserved': True, 'maximum_construction_writers': 2,
    'no_Main_source_integration': True, 'no_product_or_formal_acceptance': True,
    'worktree_creation_after_CAS': True, 'source_path_count': 1, 'fresh_cases': 14})
prepared = {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0}
prepared_ref = save('prepared_refs.json', prepared)
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'CLOSEDCOPY_LEASE_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared_ref, 'audit': pins['audit'], 'scope': pins['scope']}, ensure_ascii=True))
