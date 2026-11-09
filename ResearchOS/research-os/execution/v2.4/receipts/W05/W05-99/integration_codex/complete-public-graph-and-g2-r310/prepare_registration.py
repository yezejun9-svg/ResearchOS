import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'closure-and-finite-continuation-r309'
BASE = ROOT / 'execution/v2.4'
RECEIPTS = BASE / 'receipts/W05/W05-99'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
CLI = RECEIPTS / 'cli_exact8_continuation_preparation_codex/cli18-r310-67487c3a'
G2 = RECEIPTS / 'provider_g2_finite_replay_preparation_codex/3ed3a3da52c3471d9ddc524897100842'
DESK = BASE / 'receipts/W13/W13-03/desktop_http_first_branch_scope_independent_review_codex/b0b23bc8d3c24caf8e9763f822f11d89'
READS = {}


def read(path):
    path = Path(path).resolve()
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def pin(path, expected=None, absolute=False):
    path = Path(path).resolve()
    raw = read(path)
    result = {'path': str(path) if absolute else path.relative_to(ROOT).as_posix(),
              'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
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


old = json.loads(read(OLD / 'prepared_refs.v2.json'))
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [309, 137, 379]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == old['git_status_sha256']
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
pins = {key: value for key, value in old['pins'].items() if key in [
    'owned_helper', 'toolchain_lock', 'public_compiler_plan', 'g2_author_handoff',
    'g2_author_manifest', 'g2_nonauthor_review', 'g2_nonauthor_manifest']}
pins['previous_handoff'] = pin(OLD / 'handoff-r309-running.json', '6b36e2f605359991d7e1f3ffb91cb06a136f52531746b353c618117f4ac52d69')
pins['list_scope'] = pin(OUT / 'list_independent_scope.json', '348ebe27058bdae5c3f193a79ada0bd4a6ddc2375bcf196dee29e86900664b7a')
pins['list_runner'] = pin(OUT / 'list_replay.py', 'e26745fa85e6de999b772474fe3f899e2079bc2c8200ebf4193624d3fd89b263')
pins['public_reconciliation'] = pin(OUT / 'public-catalog-reconciliation.json')
pins['g2_runner'] = pin(OUT / 'g2_replay.v3.py', '493c256111796500307295698130ec822b7a70a6f3cc7667f5cdd351eede4427')
pins['g2_amendment'] = pin(OUT / 'g2-controller-static-amendment.json')
for key, name, expected in [
    ('cli_manifest', 'manifest.json', '2fb5aa1d6a84f3fcd5c3a933f99e878d3777d642c61ac48a962564bd2a9367ea'),
    ('cli_spec', 'prepared_execution_spec.json', '0de8c86259c27c42f9c7df543376a3c54a1408c0c432554921192ff51b0f5368'),
    ('cli_handoff', 'handoff.json', '1855b2d2c6c3feeb09a14d9ed59c63b4a6dced61d3823f80dd3644f7587870e7'),
    ('cli_runner', 'runner.v5.py', '4082541964c610258b308c6439d5ea4b37167251729ef03653f1046e06807d9f')]:
    pins[key] = pin(CLI / name, expected)
cli_spec = json.loads(read(CLI / 'prepared_execution_spec.json'))
helper = pin(ROOT / pins['owned_helper']['path'], pins['owned_helper']['sha256'], True)
for lane, key in [('remaining17', 'cli17_scope'), ('windows4', 'cli_windows4_scope')]:
    row = cli_spec['lanes'][lane]
    assert not Path(row['output']).exists()
    grant = {'schema': 'researchos.finite-nonauthor-execution-scope.v1',
        'status': 'AUTHORIZED_BY_CAS310_ONLY_NOT_EXECUTED', 'owner': 'codex:/root/w05_merge_review',
        'source_author': 'codex:/root/sources_parent_impl', 'registration_checkpoint': 310,
        'cli_bounded_continuation': {'lane': lane, 'candidate': cli_spec['source_candidate'],
            'checkout': str(ROOT / '.local/independent-cli-exact8-0dcea526'), 'output': row['output'],
            'prepared_manifest_sha256': pins['cli_manifest']['sha256'], 'owned_process_helper_ref': helper,
            'invocation_limit': row['selector_limit'], 'leaf_limit': row['leaf_limit'],
            'SDK_MODEL_EXTERNAL_PAID_CALLS': 0, 'kernel_resource_ref': cli_spec['kernel'], 'roster_ref': row['roster']},
        'runner_ref': pins['cli_runner'], 'prepared_handoff_ref': pins['cli_handoff'],
        'qualified_original_leaves_retained': 110, 'new_primary_compilation': 0,
        'first_unexpected_stop': True, 'same_input_automatic_retry': False,
        'source_acceptance': False, 'Main_integration_authorized': False, 'Main_product_source_writes': 0,
        'formal_increment': 0, 'original_kernel_loader_cause': None,
        'boundary': 'Read-only candidate and old executable input; new lane output only. Windows test retains its actual temporary CLI build and requires original executable hash. Explicit DLL preload is a resource binding, not qualification.'}
    pins[key] = save(key + '.json', grant)
g2_spec = json.loads(read(G2 / 'execution_spec.json'))
for key, name, expected in [
    ('g2_spec', 'execution_spec.json', '2c871df7ffa78c52470ed08f031be5831ceeab3098947c512d6485c06df8ca0b'),
    ('g2_manifest', 'preparation_manifest.json', '1680e7b2e22d57640f4f6dc3a1e39230ae20c940c4baff464b00e67d38aaff66'),
    ('g2_handoff', 'handoff.json', '144c26efae55bd03afb472c3ff95dd7d1ee1d8ab8e2647ec8b2ddce889732ea0'),
    ('g2_final_manifest', 'manifest.json', 'f2787eb99d1c295b5eed950a1f6ec303d1ee3f638f225ab4a722b66034ce868f')]:
    pins[key] = pin(G2 / name, expected)
assert not Path(g2_spec['output_root']).exists() and not Path(g2_spec['work_root']).exists()
pins['g2_scope'] = save('g2_prepare_scope.json', {
    'schema': 'researchos.provider-g2-root-prepare-scope.v1', 'owner': 'codex:/root',
    'status': 'AUTHORIZED_BY_CAS310_ONLY_NOT_EXECUTED', 'registration_checkpoint': 310,
    'candidate': g2_spec['candidate'], 'spec_ref': pins['g2_spec'], 'runner_ref': pins['g2_runner'],
    'preparation_manifest_ref': pins['g2_manifest'], 'source_handoff_ref': pins['g2_author_handoff'],
    'source_static_review_ref': pins['g2_nonauthor_review'], 'phases': ['prepare'],
    'output_root': g2_spec['output_root'], 'work_root': g2_spec['work_root'],
    'finite_future_roster': [row['selector'] for row in g2_spec['roster']], 'future_cases': 29,
    'prepare_product_test_cases': 0, 'prepare_SDK_MODEL_external_paid_calls': 0,
    'actual_grant_write': 'Root writes actual_registration_completed true only after canonical CAS310 and exact registered scope pin check.',
    'execute_authorization': 'Separate immutable Root scope/grant must bind actual newly completed prepared.json SHA; execute is not granted here.',
    'source_writes': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'same_input_automatic_retry': False, 'first_unexpected_stop': True,
    'bootstrap_HTTP': 'UNKNOWN_NOT_INSTRUMENTED', 'DB_limits': 'Existing author VACUUM INTO snapshots are not original DB byte copies; logical comparison does not assert original storage types or implicit rowid.'})
pins['list_late_failure'] = pin(RECEIPTS / 'integration_codex/root-list14-launch-r309/failure_origin.json', '3a527ff02b61cda533bb7e7d21bd5bca0e401ce83127c2528be290fa4800856b')
pins['cli_late_failure'] = pin(RECEIPTS / 'cli_exact8_independent_replay_codex/cli44-r309-stopped-aecd69f538014b068358ab527e547e53/failure_origins.json', 'f5b99b78f738cf4d298fa1d59c7e6632cdd95f0c05bcf0a1099695e29af82a36')
pins['cli_stopped_review'] = pin(RECEIPTS / 'cli_exact8_independent_replay_codex/cli44-r309-stopped-aecd69f538014b068358ab527e547e53/review.json', '9914862cb5b575f3b3352848c3acbdf450ea0d507989c369558e23ac94bb5800')
pins['desktop_failure'] = pin(DESK / 'failure_origins.json', '6a1ac40972be69463d18728879f66ec1d3ef32ec29d4ceed5e1392b02e669b76')
pins['desktop_review'] = pin(DESK / 'review.json', 'e0e2446d21bf639a1bd26a4367b0e7f9e915f508b597259eca3d17e7957b72f7')
pins['desktop_conditions'] = pin(DESK / 'mandatory_conditions.json', 'da8a81322991a010aef325dbe4e78129c33e0be8242480370712e3947aea7b05')
origins = []
listed = json.loads(read(ROOT / pins['list_late_failure']['path']))
origins.append({'origin_key': listed['origin_key'], 'actor': 'codex:/root', 'actual_outer_exit': 1,
    'actual_native_exit': listed['actual_native_Go_exit'], 'product_test_failures': 0,
    'cause': listed['cause'], 'evidence_ref': pins['list_late_failure']})
cli_failed = json.loads(read(ROOT / pins['cli_late_failure']['path']))
assert isinstance(cli_failed, list) and len(cli_failed) == 1
row = cli_failed[0]
origins.append({'origin_key': row['origin_id'], 'actor': 'codex:/root/w05_merge_review',
    'actual_outer_exit': row['outer_exit'], 'actual_native_exit': row['native_controller_exit'],
    'product_test_failures': row['underlying_case_native_failures'], 'cause': row['kind'],
    'evidence_ref': pins['cli_late_failure'], 'json_pointer': '/0', 'original_payload': row})
desk_failed = json.loads(read(DESK / 'failure_origins.json'))
assert desk_failed['new_total'] == 3 and desk_failed['continued_after_two'] is True and desk_failed['stopped_locator_branch'] is True
for index, row in enumerate(desk_failed['new_readonly_tool_origins']):
    origins.append({'origin_key': 'Desktop-independent-readonly-tool-' + row['tool_ref'],
        'actor': 'codex:/root/command_queue_impl', 'actual_outer_exit': row['actual_outer_exit'],
        'actual_native_exit': row['actual_native_exit'], 'product_test_failures': 0, 'cause': row['cause'],
        'evidence_ref': pins['desktop_failure'], 'json_pointer': '/new_readonly_tool_origins/' + str(index),
        'original_payload': row, 'raw_file_available': False})
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 379, 'after': 384, 'origins': origins,
    'old379_prefix_unchanged': True, 'counter_reset': False, 'actual_product_test_failures': 0,
    'desktop_locator_chain_stopped_after3_with_boundary_violation': True})

# Reuse reviewed CAS guard and forward-only write mechanics; construct the new mutation explicitly.
old_source = read(OLD / 'register.v2.py').decode('utf-8')
header = old_source[:old_source.index('pins = prepared[\'pins\']')]
header = header.replace('prepared_refs.v2.json', 'prepared_refs.json').replace('[308, 136, 371]', '[309, 137, 379]')
mutation = '''pins = prepared['pins']
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
'''
tail = old_source[old_source.index('for path, raw in before.items():'):old_source.index("handoff_ref = save('handoff-r309-running.json'")]
tail = tail.replace('root309.tmp', 'root310.tmp').replace("'register.v2.py'", "'register.py'")
tail = tail.replace('[308, 309]', '[309, 310]').replace('[136, 137]', '[137, 138]').replace('[371, 379]', '[379, 384]')
tail = tail.replace('[309, 137, 379]', '[310, 138, 384]').replace('[:371]', '[:379]').replace('old371_prefix', 'old379_prefix')
tail = tail.replace("'checkpoint': 309", "'checkpoint': 310").replace("'ownership': 137", "'ownership': 138").replace("'failure_origins': 379", "'failure_origins': 384")
tail = tail.replace("'new_independent_CLI44_and_list14_execution_only': True", "'new_CLI17_Windows4_list14_and_G2_prepare_only': True")
handoff = '''handoff_ref = save('handoff-r310-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 310, 'failure_origins': 384, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'current_card': 'W05-99', 'cli17_scope_ref': pins['cli17_scope'], 'cli_windows4_scope_ref': pins['cli_windows4_scope'],
    'list_scope_ref': pins['list_scope'], 'g2_prepare_scope_ref': pins['g2_scope'],
    'Desktop_next': 'Review refined exact15 proposal; no product/source execution lease.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0, 'SDK_MODEL_external_paid_private_calls': 0})
print(json.dumps({'checkpoint': 310, 'ownership': 138, 'failure_origins': 384, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
script('register.py', header + mutation + tail + handoff)
wrapper = read(OLD / 'run.v2.py').decode('utf-8')
wrapper = wrapper.replace('root_registration_r309_readonly_review_codex', 'root_registration_r310_readonly_review_codex')
wrapper = wrapper.replace('prepared_refs.v2.json', 'prepared_refs.json').replace('register.v2.py', 'register.py').replace('audit.v2.json', 'audit.json')
wrapper = wrapper.replace('[308, 136, 371]', '[309, 137, 379]').replace('[309, 137, 379]', '[310, 138, 384]', 1) if False else wrapper
wrapper = wrapper.replace("review['expected_before'] == [308, 136, 371] and review['expected_after'] == [309, 137, 379]", "review['expected_before'] == [309, 137, 379] and review['expected_after'] == [310, 138, 384]")
wrapper = wrapper.replace("cp['revision'] == 308 and len(cp['failure_counters']) == 371", "cp['revision'] == 309 and len(cp['failure_counters']) == 379")
script('run.py', wrapper)
for key, path in [('cli_members', CLI / 'manifest.json'), ('g2_members', G2 / 'manifest.json')]:
    rows = json.loads(read(path))['entries']
    for row in rows:
        p = Path(row['path']); p = p if p.is_absolute() else path.parent / p
        pin(p, row['sha256'])
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1',
    'actor': 'codex:/root', 'state': 'DRAFT_NOT_EXECUTED_PENDING_NONAUTHOR_REVIEW',
    'expected_before': [309, 137, 379], 'expected_after': [310, 138, 384],
    'old_failures_preserved': 379, 'new_origins': origins, 'scopes': {k: pins[k] for k in ['cli17_scope', 'cli_windows4_scope', 'list_scope', 'g2_scope']},
    'scope_boundaries': ['CLI17/107 then separateWindows1/4; protected110 never replayed',
        'list full518 publiccatalog complete beforeGo;713 individually frozen Git source files; only14 selected',
        'G2 prepare0cases; actualgrant only afterCAS; execute29 requires futurepreparedSHA grant',
        'Desktop REQUEST_CHANGES; no productwriter or execution grant',
        'No Source/Main/formal acceptance; no SDK/MODEL/externalpaid/privateaccess in registration'],
    'canonical_write_mechanics': 'All four metadata, HEAD and Git status guards before each replace; original/desired/intent saved first; forward only; no rollback/reset/autoretry.',
    'counter_reset': False, 'Main_source_writes': 0, 'formal_increment': 0})
verified = []
for path, raw in READS.items():
    if path.is_relative_to(ROOT) and path not in CANON:
        verified.append(pin(path))
prepared = {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': verified, 'actual_source_exports_compile_cases': 0,
    'immutable_previous_prepared_refs': pin(OLD / 'prepared_refs.v2.json')}
save('prepared_refs.json', prepared)
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'DRAFT_PREPARED_NOT_EXECUTED', 'canonical': [cp['revision'], ow['revision'], len(cp['failure_counters'])],
    'register': pin(OUT / 'register.py'), 'wrapper': pin(OUT / 'run.py'),
    'prepared': pin(OUT / 'prepared_refs.json'), 'audit': pins['audit'], 'verified_refs': len(verified)}, ensure_ascii=True))
