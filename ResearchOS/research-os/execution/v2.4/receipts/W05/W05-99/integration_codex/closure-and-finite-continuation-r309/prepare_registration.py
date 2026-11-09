import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'independent-cli-list-scopes-r308'
BASE = ROOT / 'execution/v2.4'
RECEIPTS = BASE / 'receipts/W05/W05-99'


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


def write(name, value):
    ast.parse(value)
    with (OUT / name).open('xb') as stream:
        stream.write(value.encode('utf-8'))
    return ref(OUT / name)


cli_dir = RECEIPTS / 'cli_exact8_continuation_preparation_codex/cli44-r309-c927f880'
cli_stopped = RECEIPTS / 'cli_exact8_independent_replay_codex/cli47-r308-stopped-audit-3f62f862'
g2_dir = ROOT / '.local/worktrees/codex-w0599-provider-g2-finite-r307/execution/v2.4/receipts/W05/W05-99/provider_g2_finite_executor_codex/3fc125bf95424cb298a87a9527515d09'
g2_final = g2_dir / 'final-audit-97b53059b7284a5294781a90f7ab64a1'
g2_review = RECEIPTS / 'provider_g2_finite_independent_static_review_codex/29ae7f916f74486a8e832cc2e48a0039'
desktop_dir = BASE / 'receipts/W13/W13-03/desktop_wire_scope_readonly_codex/d85840371d3b4ba2a8f012c884fc8a75'
pins = {
    'owned_helper': ref(OLD / 'windows_owned_process.py', '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad'),
    'toolchain_lock': ref(ROOT / 'execution/toolchains/locked.json', '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663'),
    'public_compiler_plan': ref(RECEIPTS / 'cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'),
    'previous_handoff': ref(OLD / 'handoff-r308-running.json', '89c003651678e9a2c85980384c99778b6d03b9cd363035ec93e94b46b92f42d6'),
    'list_scope': ref(OUT / 'list_independent_scope.json'),
    'list_runner': ref(OUT / 'list_replay.py'),
    'list_old_failure': ref(OUT.parent / 'root-list14-launch-r308/failure_origin.json', '17448057f0888b3bf60683f859f0538b13b4ec1bca28e0a3bd483c5ee349bfad'),
    'list_old_manifest': ref(OUT.parent / 'root-list14-launch-r308/manifest.json', '3230abdae5ddb64b59dd317d91e23d7516584b35c706df45f990aea5f6c8991f'),
    'cli_scope': ref(OUT / 'cli_continuation_scope.json'),
    'cli_prepared_handoff': ref(cli_dir / 'handoff.v3.json', 'd195f61fb1d46b0c95367710adf15f7c67ac054b84e080c55967cfbe74d58b92'),
    'cli_prepared_manifest': ref(cli_dir / 'manifest.v3.json', '584dbb16c4e9d6661b973a2c991d6b8dd28b9ab00f3fe70b2b8fd59d900cf572'),
    'cli_prepared_spec': ref(cli_dir / 'prepared_execution_spec.v3.json', '34e40f3fd952ec6a54362ca9d9b391f1eaa9e88ff7d59aa0eaaec587bcb04967'),
    'cli_roster': ref(cli_dir / 'finite_selectors.v3.json', 'ec1c0eee674dc9a4567bab23ea5d089e6e6d31e006e16d01b2e27cbc73301e29'),
    'cli_old_review': ref(cli_stopped / 'review.json', '8e5fac6cca5167a25fd978f69db7a6c3f57c49efc3ca0674befb0658d5115f63'),
    'cli_old_failure': ref(cli_stopped / 'failure_origins.json', 'b5b0d7a1d95a88fef7e2ff634fbb4063cd24b166b9f52c296b951b09f014b034'),
    'cli_old_manifest': ref(cli_stopped / 'manifest.json', '6d84834b4ee745f681f97e937362921289a41eebe7ad6a395cc1010218e6b3d5'),
    'g2_author_handoff': ref(g2_final / 'handoff.json', '618ce28c1888e573240bba9534116d07132aacd0c57f63b388d23c9a81204d98'),
    'g2_author_manifest': ref(g2_final / 'manifest.json', 'b4300d9db50848d1a7ee393d5047293a8b8cdc34931cbe4569011d376caa1ba9'),
    'g2_nonauthor_review': ref(g2_review / 'review.json', '734c90dfe21aea4ad4343d4bc26f41e785fdee926dea84e4665c1d1e98cfead3'),
    'g2_nonauthor_handoff': ref(g2_review / 'handoff.json', '603aad495cfde00d449dfa98a7f8661f2ad332b9c115d6423013761838113379'),
    'g2_nonauthor_manifest': ref(g2_review / 'manifest.json', '7b8d986145c9367a93351c656b8bd3148bc5f29f3ad5b16babf7b374d6f0c622'),
    'g2_future_scope': ref(g2_review / 'future_replay_scope.json', '294b199e9353989cb9bacb1429327f1a83184af911759cf399e42e5f2f137128'),
    'desktop_proposal': ref(desktop_dir / 'proposal.final.json', 'f8d91daa73ad240c4cce0c32e2db152238875607a0f46b4207cfc0f639477531'),
    'desktop_handoff': ref(desktop_dir / 'handoff.json', '033e0a67756ff6df381c8a5b44caf5ee6a1ded9fb5da00b87975e26e493f689a'),
    'desktop_manifest': ref(desktop_dir / 'manifest.json', 'e837dd5505b97a20ce062bdb613ef6610a5d210783bf7af1775e80da26691510'),
    'runner_preparation_audit': ref(OUT / 'runner-preparation.audit.json'),
}
origins = []
for chunk, filename, expected, native in [
    ('339800', 'tool-origin-339800.json', '7257ad23fc3098e8897732b4fa02ceee050e104d3bbd6b764195eb87e544b08c', 1),
    ('798239', 'tool-origin-798239.json', '43f68e44cf6541b1e23cbe2232a7e30ba09342930c4d9fc70b3a0099c3ab8f3a', None),
    ('62f172', 'tool-origin-62f172.json', 'b5a0c8c88c367b27c512a720edf8267e765e65346aec69f157710b45cbff82ec', None),
]:
    evidence = ref(g2_dir / filename, expected)
    original = json.loads((ROOT / evidence['path']).read_bytes())
    assert original.get('outer_exit', original.get('actual_exit')) == 1
    origins.append({'origin_key': 'G2-readonly-tool-' + chunk, 'actor': 'codex:/root/sources_parent_impl',
        'actual_outer_exit': 1, 'actual_native_exit': native, 'product_test_failures': 0, 'evidence_ref': evidence,
        'cause': original['cause'] if 'cause' in original else original['kind'], 'original_payload': original})
cmd_origin = json.loads((g2_review / 'failure_origin.json').read_bytes())
assert cmd_origin['actual_outer_exit'] == cmd_origin['actual_native_python_exit'] == 1
origins.append({'origin_key': cmd_origin['origin_key'], 'actor': cmd_origin['actor'], 'actual_outer_exit': 1,
    'actual_native_exit': 1, 'product_test_failures': 0, 'cause': cmd_origin['cause'],
    'evidence_ref': ref(g2_review / 'failure_origin.json', '8c9e20a65a5dc0e9f4c43ab2e30ebed7b7546eb046bdcdf77cd0ae90758b8e2e')})
root_origin = json.loads((ROOT / pins['list_old_failure']['path']).read_bytes())
assert root_origin['actual_outer_exit'] == root_origin['actual_native_Go_exit'] == 1 and root_origin['native_product_test_cases'] == 0
origins.append({'origin_key': root_origin['origin_key'], 'actor': 'codex:/root', 'actual_outer_exit': 1,
    'actual_native_exit': 1, 'product_test_failures': 0, 'cause': root_origin['cause'], 'evidence_ref': pins['list_old_failure']})
cli_origin = json.loads((cli_stopped / 'failure_origins.json').read_bytes())['origins']
assert len(cli_origin) == 1 and cli_origin[0]['outer_native_exit'] == 1 and cli_origin[0]['underlying_case_native_failures'] == 0
origins.append({'origin_key': cli_origin[0]['origin_id'], 'actor': 'codex:/root/w05_merge_review', 'actual_outer_exit': 1,
    'actual_native_exit': 1, 'product_test_failures': 0, 'cause': cli_origin[0]['reason'], 'evidence_ref': pins['cli_old_failure']})
diagnostic_ref = ref(desktop_dir / 'tool-diagnostics.json', '6f79024e106c9a87de47f49d1e0ee488c7670be6dce2c52b6b423de584f66ce0')
diagnostic = json.loads((ROOT / diagnostic_ref['path']).read_bytes())
for index, row in enumerate(diagnostic['actual_nonzero_outer_origins']):
    assert row['actual_outer_exit'] == 1 and row['origin'] in ['9429cc', 'a25d00']
    origins.append({'origin_key': 'Desktop-readonly-tool-' + row['origin'], 'actor': 'codex:/root/sources_parent_impl',
        'actual_outer_exit': 1, 'actual_native_exit': None, 'product_test_failures': 0, 'cause': row['kind'],
        'evidence_ref': diagnostic_ref, 'json_pointer': '/actual_nonzero_outer_origins/' + str(index),
        'original_payload': row, 'raw_file_available': False})
assert len(origins) == len({item['origin_key'] for item in origins}) == 8
assert diagnostic['zero_outer_with_diagnostic'][0]['actual_outer_exit'] == 0
failure_ref = save('failure-origins.cut.json', {'origins': origins, 'count': 8, 'product_test_failures': 0,
    'zero_outer_diagnostics_not_counted': diagnostic['zero_outer_with_diagnostic'], 'counter_reset': False})
pins['failure_cut'] = failure_ref
canon = [ref(BASE / name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
cp = json.loads((BASE / 'checkpoint.json').read_bytes())
ow = json.loads((BASE / 'path_ownership.json').read_bytes())
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [308, 136, 371]
git = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
audit_ref = save('audit.json', {'decision': 'CAS309_DRAFT_PENDING_INDEPENDENT_REVIEW', 'expected_before': [308, 136, 371],
    'expected_after': [309, 137, 379], 'source_acceptance': False, 'Main_integration_authorized': False,
    'G2_source_writer_release': 'Frozen8d092 exact2, Source writer stopped;755 author evidence and734 nonauthor static review bound at actual WT root. finite29 future not authorized by this registration.',
    'CLI': 'Original76 complete cohort retained, two unresolved closure controls plus42 NOT_RUN authorized under new44 input scope; no original failure reset or full acceptance.',
    'list': 'Original go-list native1 preserved with zero cases. Public5 compiler resources added, new export/cache/WORK/exe and URI preload+per-case closure checks; finite14 only.',
    'Desktop': '23path/141case readonly design registered NON_READY; no product lease or execution.',
    'origins': origins, 'zero_outer_diagnostics_not_counted': diagnostic['zero_outer_with_diagnostic'],
    'step_state_commands_Main_old11D_formal_unchanged': True, 'formal_increment': 0, 'SDK_MODEL_external_paid_private': 0})
pins['audit'] = audit_ref
old_code = (OLD / 'register.v2.py').read_text(encoding='utf-8')
prefix = old_code[:old_code.index("lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']")]
body = '''lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
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
'''
tail = old_code[old_code.index('for path, raw in before.items():'):old_code.index("handoff_ref = save('handoff-r308-running.json'")]
tail = tail.replace('root308.tmp', 'root309.tmp').replace("[307, 308]", "[308, 309]").replace("[135, 136]", "[136, 137]").replace("[367, 371]", "[371, 379]")
tail = tail.replace('[308, 136, 371]', '[309, 137, 379]').replace('[:367]', '[:371]').replace("'checkpoint': 308", "'checkpoint': 309").replace("'ownership': 136", "'ownership': 137").replace("'failure_origins': 371", "'failure_origins': 379").replace('old367_prefix_unchanged', 'old371_prefix_unchanged').replace('new_independent_CLI47_and_list14_execution_only', 'new_independent_CLI44_and_list14_execution_only')
ending = '''handoff_ref = save('handoff-r309-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
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
'''
register_ref = write('register.py', prefix + body + tail + ending)
wrapper = (OLD / 'run.v2.py').read_text(encoding='utf-8')
wrapper = wrapper.replace('root_registration_r308_readonly_review_codex', 'root_registration_r309_readonly_review_codex')
wrapper = wrapper.replace('prepared_refs.v2.json', 'prepared_refs.json').replace('register.v2.py', 'register.py').replace('audit.v2.json', 'audit.json')
wrapper = wrapper.replace("codex:/root/command_queue_impl", "codex:/root/w05_merge_review")
wrapper = wrapper.replace('[308, 136, 371]', '[309, 137, 379]').replace('[307, 135, 367]', '[308, 136, 371]')
wrapper = wrapper.replace("cp['revision'] == 307 and len(cp['failure_counters']) == 367", "cp['revision'] == 308 and len(cp['failure_counters']) == 371")
wrapper_ref = write('run.py', wrapper)
verified = list(pins.values()) + [register_ref, wrapper_ref, ref(Path(__file__)), ref(OUT / 'prepare.py')]
for entry in json.loads((cli_dir / 'manifest.v3.json').read_bytes())['entries']:
    actual = ref(cli_dir / entry['path'], entry['sha256'])
    assert actual['bytes'] == entry['bytes']
    verified.append(actual)
for origin in origins:
    verified.append(origin['evidence_ref'])
for obj in [root_origin, cli_origin[0]]:
    for pin in obj.values():
        if isinstance(pin, dict) and {'path', 'sha256', 'bytes'} <= set(pin):
            actual = ref(pin['path'], pin['sha256'])
            assert actual['bytes'] == pin['bytes']
            verified.append(actual)
unique = {item['path']: item for item in verified}
prepared_ref = save('prepared_refs.json', {'canonical_before': canon, 'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(),
    'pins': pins, 'origins': origins, 'verified_refs': list(unique.values()), 'actual_source_exports_compile_cases': 0})
assert ref(BASE / 'checkpoint.json') == canon[0] and ref(BASE / 'path_ownership.json') == canon[1]
print(json.dumps({'prepared_refs': prepared_ref, 'register': register_ref, 'wrapper': wrapper_ref,
    'audit': audit_ref, 'closure_ref_count': len(unique), 'before': [308, 136, 371], 'after': [309, 137, 379]}, ensure_ascii=True))
