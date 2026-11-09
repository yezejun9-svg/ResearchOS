import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
R = BASE / 'receipts/W05/W05-99'
SR = ROOT / '.local/worktrees/codex-w0599-cli-contract-repair-r303'
SN = SR / 'execution/v2.4/receipts/W05/W05-99/cli_protocol_exact8_executor_codex/32000aadb56142468ad17096b4d18953'
READS = {}
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert expected is None or sha == expected, str(path)
    if path in READS:
        assert READS[path] == raw
    READS[path] = raw
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(raw)}


def read(path):
    row = ref(path)
    return READS[ROOT / row['path']]


def save(name, obj):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode())
    return ref(OUT / name)


def collect(obj, base=ROOT):
    if isinstance(obj, dict):
        if isinstance(obj.get('path'), str) and isinstance(obj.get('sha256'), str) and len(obj['sha256']) == 64:
            path = Path(obj['path'])
            path = path if path.is_absolute() else base / path
            row = ref(path, obj['sha256'])
            assert 'bytes' not in obj or row['bytes'] == obj['bytes']
        else:
            for value in obj.values():
                collect(value, base)
    elif isinstance(obj, list):
        for value in obj:
            collect(value, base)


lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
before = [ref(path) for path in CANON]
assert [row['sha256'] for row in before] == [
    '2a003a2f717334e123219873cbd7af903be5d434ff2d970b6d86cf14d45e92c1',
    '43eb41b3e80a259ed5750616aa6c70cf7b6234db65a9bae61c0104cac36c44a9',
    'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',
    'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129']
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [306, 134, 362]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
P = R / 'session_list_identity_exact2_executor_codex/dd80342f72a442a09551b80022198dd3'
SDK = R / 'mu_pause_checkpoint_interface_independent_review_codex/fb993615c8f34f9c8752bb8c1e93c6c8'
LEASE = R / 'attach_lease_synchronous_scope_independent_review_codex/c7994ea630534db2b85b1235ce441900'
DESKTOP = ROOT / 'execution/v2.4/receipts/W13/W13-03/integration_codex/desktop-response-boundary-readonly-r306'
pins = {
    'previous_handoff': ref(R / 'integration_codex/handler38-final-and-main-scope-r306/handoff-r306-running.json', 'f9a4e5b65c5a668644c35f13bbd837eb62470ee79f6af515730660b5e549e179'),
    'cli_final_handoff': ref(SN / 'final-freeze/handoff.final.json', '882891dc0e5c416844615099a286b7287c07727b2361cbc4ebd399bab144c509'),
    'cli_source_manifest': ref(SN / 'final-freeze/source-manifest.json', '7fb395eeae08666dc92822ce3482e0518be2ecebe1abb028caafaf948599fab0'),
    'cli_scenario_coverage': ref(SN / 'final-freeze/scenario-coverage.json', '39dc6313e7291071f8a66c81c541956c738957f8ac5e637fb6592594059e2c31'),
    'cli_current_leaf_coverage': ref(SN / 'final-freeze/current-leaf-coverage.json', '1ed5d076b0716d602cf887cda7cb978268618d67fcb0dc63b378be99f4209c31'),
    'cli_closure': ref(SN / 'final-freeze/closure.json', 'bd8f9737d762cf21339e27e671bb3bd4669e0e76d9510e17f8a614fe91acada4'),
    'cli_manifest': ref(SN / 'final-freeze/manifest.json', '421b384c08aa5ee89882c78e813f5a83ec4c4ed7ca70605c429f996ff95f33a1'),
    'cli_final_index': ref(SN / 'final-freeze/final-index.json', '754967345e47d96da59ab1a6492771fbb359b3464c0ac769df34f531413e350e'),
    'cli_cursor_failure': ref(SN / 'r305-cursor-failure/handoff.json', '2d30e7c118ed497c989faddac761eb411d0a25a8cb9ee96d5bb954a215ff0f94'),
    'cli_goal_failures': ref(SN / 'r305-goal-failure-supplement/handoff.json', '7ede61561933bfdd723bfb09973d9f01069c1808c5173dac9b53680d51749729'),
    'list_candidate_handoff': ref(P / 'handoff.json', '4f51254012fa9132fe0683424b0aaceffe7e4318a129b48ca422f3d68987dcaa'),
    'list_candidate_report': ref(P / 'execution_report.json', 'eec009b22028451b5c57602da78ae91d75ff58c65ce7bfe41b92bae31944fe4e'),
    'list_candidate_manifest': ref(P / 'manifest.json', '83b9237047426804006b50a6e890bd22344b204dd9c787b5d7ca231012efe556'),
    'lease_sync_proposal': ref(LEASE / 'scope_proposal.json', '1ce11956825a91646e30d7f2edcda2a5585149f9c9356d0df329f404cd4f948f'),
    'lease_sync_cases': ref(LEASE / 'finite_scenarios24.json', '5e306223b901b061c7d3f8fae302f9153167cffa9071ce6bbe2075bf19f343d2'),
    'lease_sync_manifest': ref(LEASE / 'manifest.json', 'e3d89f1bd8b53f6b279a1d82ab3bd2551348a8ef000d8be8ea8b4df719d26947'),
    'lease_sync_handoff': ref(LEASE / 'handoff.json', '008e861a6f55881235c230e5e4e5d254c64c79a860cd297c9de6f15fff8ea4fa'),
    'mu_sdk_readonly_review': ref(SDK / 'review.json', '7d8bb7f4b4d9050e3b2e191350d1ba03a0d35309fa6121f7975a648596f51f78'),
    'mu_sdk_readonly_manifest': ref(SDK / 'manifest.json', '72ee113bd98063cec0e638ec5078c1a75d801b314d97384a58335752b947e2bb'),
    'mu_sdk_readonly_handoff': ref(SDK / 'handoff.json', '91f1bd960a6e2665b8dd4169664e8269235460be34a8158d5ab1f4821a8a5134'),
    'mu_sdk_readonly_failure': ref(SDK / 'failure_origin.json', '413e4caf7359f15a1f85e8a59d0c1f3a16bd0b84a2b3650fbad1d1c930db9f57'),
    'root_readonly_failure': ref(R / 'integration_codex/root-readonly-locator-origin-r306/failure_origin.json', '7566f1fd34dc499541777ad1008c2b41b1ae05d92f10e2e1ee913cc2dadefc07'),
    'desktop_response_findings': ref(DESKTOP / 'findings.json', '3094bea974f7a04361c1f41091b3181c7a90116b446203a491d4c4ea6bb10207'),
    'desktop_response_manifest': ref(DESKTOP / 'manifest.json', '8b9941d25724029f5f55093d15d2761c24b1fd744efa01528a80722e7f322f8b')}
for key in ['provider_g2_finite_proposal_ref', 'provider_g2_finite_selectors_ref', 'provider_g2_finite_runner_ref',
            'provider_g2_finite_nonauthor_root_scope_review_ref', 'provider_g2_finite_nonauthor_root_conditions_ref']:
    row = cp['work_in_progress'][key]
    pins[key] = ref(row['path'], row['sha256'])
manifest_audit = []
for key, base, expected_count in [
    ('cli_manifest', SR, 2428), ('list_candidate_manifest', ROOT, 951),
    ('lease_sync_manifest', ROOT, 70), ('mu_sdk_readonly_manifest', ROOT, 36),
    ('desktop_response_manifest', DESKTOP, 8)]:
    manifest = json.loads(read(pins[key]['path']))
    rows = manifest['entries']
    assert len(rows) == expected_count
    for row in rows:
        path = Path(row['path'])
        path = path if path.is_absolute() else base / path
        actual = ref(path, row['sha256'])
        assert actual['bytes'] == row['bytes']
    manifest_audit.append({'name': key, 'listed': len(rows), 'bad': 0, 'ref': pins[key]})
cli = json.loads(read(pins['cli_final_handoff']['path']))
assert cli['source_commit'] == 'b98738ac093ea55bb8700cfa724ddd9e6b2a1251'
assert cli['current_source_writer'] == 'STOPPED_AND_FROZEN_PENDING_NONAUTHOR_REVIEW'
assert cli['new_tests'] == {'inventory': 101, 'pass': 99, 'held': 2, 'skip': 0}
assert cli['regressions'] == {'groups': 21, 'leaf_pass': 122, 'skip': 0}
collect(cli, SR)
cli_source = json.loads(read(pins['cli_source_manifest']['path']))
assert len(cli_source['paths']) == 8
assert subprocess.check_output([git, 'diff-tree', '--no-commit-id', '--name-only', '-r', cli['source_commit']], cwd=ROOT).decode().splitlines() == [row['path'] for row in cli_source['paths']]
for row in cli_source['paths']:
    raw = read(SR / row['path'])
    assert hashlib.sha256(raw).hexdigest() == row['sha256']
    assert subprocess.check_output([git, 'show', cli['source_commit'] + ':' + row['path']], cwd=ROOT) == raw
list_handoff = json.loads(read(pins['list_candidate_handoff']['path']))
assert list_handoff['source_commit'] == '534857db99fa5e694987f877af74c322eaa2a0b3'
assert [list_handoff[key] for key in ['case_count', 'leaf_pass', 'fail', 'skip', 'loopback_HTTP', 'input_count', 'input_drift']] == [14, 14, 0, 0, 78, 15461, 0]
assert list_handoff['source_acceptance'] is False and list_handoff['Main_HOLD'] is True
for path, sha in list_handoff['source_sha256'].items():
    raw = subprocess.check_output([git, 'show', list_handoff['source_commit'] + ':' + path], cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest() == sha
assert subprocess.check_output([git, 'diff-tree', '--no-commit-id', '--name-only', '-r', list_handoff['source_commit']], cwd=ROOT).decode().splitlines() == sorted(list_handoff['source_paths'])
origins = []
for key in ['cli_cursor_failure', 'cli_goal_failures']:
    obj = json.loads(read(pins[key]['path']))
    collect(obj, SR)
    for row in obj.get('origins', [obj]):
        assert [row['outer_exit'], row['native_exit']] == [1, 1]
        origins.append({'origin_key': 'cli-r305-' + row['tool_chunk'], 'actor': 'codex:/root/sources_parent_impl',
            'actual_outer_exit_code': 1, 'actual_native_exit_code': 1, 'kind': 'TEST_BATCH',
            'reason': row['cause'], 'evidence_ref': pins[key], 'source_origin': row})
row = json.loads(read(pins['root_readonly_failure']['path']))
origins.append({key: row[key] for key in ['origin_key', 'actor', 'actual_outer_exit_code', 'actual_native_exit_code', 'kind', 'reason']})
origins[-1].update(evidence_ref=pins['root_readonly_failure'], source_origin=row)
row = json.loads(read(pins['mu_sdk_readonly_failure']['path']))
assert [row['outer_exit_code'], row['native_python_exit_code']] == [1, 1]
origins.append({'origin_key': 'mu-sdk-readonly-' + row['origin'], 'actor': 'codex:/root/w05_merge_review',
    'actual_outer_exit_code': 1, 'actual_native_exit_code': 1, 'kind': 'READONLY_SNIPPET_BOUND',
    'reason': row['cause'], 'evidence_ref': pins['mu_sdk_readonly_failure'], 'source_origin': row})
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
assert not ({row['origin_key'] for row in origins} & {row.get('origin_key') for row in cp['failure_counters']})
proposal = json.loads(read(pins['provider_g2_finite_proposal_ref']['path']))
runner = json.loads(read(pins['provider_g2_finite_runner_ref']['path']))
conditions = json.loads(read(pins['provider_g2_finite_nonauthor_root_conditions_ref']['path']))
assert len(runner['execution_order']) == 29 and len(conditions) == 8
assert proposal['candidate_head'] == '6fb5263681c17f0e50920c354dc07ed440a23714'
assert runner['bundle_pin'] == '497e111b4b0b8d080f2ac20baf78a1d08b132e53866ebf67d851e886a19caade'
bundle = ref(runner['env']['RESEARCHOS_MU_BUNDLE'], runner['bundle_pin'])
pins['g2_readonly_bundle'] = bundle
scope = {'status': 'AUTHORIZED_BY_CAS307_ONLY_NOT_EXECUTED', 'owner': 'codex:/root/sources_parent_impl',
    'worktree': '.local/worktrees/codex-w0599-provider-g2-finite-r307',
    'branch': 'work/codex-w0599-provider-g2-finite-r307', 'base_commit': proposal['candidate_head'],
    'source_paths': [row['path'] for row in proposal['exact_mutations']],
    'source_proposal_ref': pins['provider_g2_finite_proposal_ref'], 'mandatory_source_proposal': proposal,
    'nonauthor_root_scope_review_ref': pins['provider_g2_finite_nonauthor_root_scope_review_ref'],
    'mandatory_conditions_ref': pins['provider_g2_finite_nonauthor_root_conditions_ref'],
    'mandatory_conditions': conditions, 'selectors_ref': pins['provider_g2_finite_selectors_ref'],
    'runner_proposal_ref': pins['provider_g2_finite_runner_ref'], 'mandatory_runner_proposal': runner,
    'executor_cwd_override': '.local/worktrees/codex-w0599-provider-g2-finite-r307',
    'new_receipt_namespace': 'execution/v2.4/receipts/W05/W05-99/provider_g2_finite_executor_codex/**',
    'new_cache_work_tmp_must_be_inside_new_worktree': True,
    'readonly_bundle_original_ref': bundle, 'original_provider_authorWT_writes': 0,
    'frozen_CLI8_list2_Main_SQL_SDK_lock_production_source_writes': 0,
    'original9_production_JS_source_paths_unchanged': True, 'ordered_cases': runner['execution_order'],
    'component_cases': 18, 'native_cases': 11, 'loopback_MODEL_max': 4,
    'API_readiness_loopback_HTTP_separately_counted': True, 'external_paid_private_calls': 0,
    'new_actual_full_Go_graph_testmain_importcfg_archives_tool_SDK_input_closure_and_NEW_exe_before_cases': True,
    'maximum_active_construction': 2, 'first_unexpected_stop': True, 'automatic_retries': 0,
    'source_ready': False, 'formal_increment': 0,
    'Main_list_integration_HOLD_unchanged': True, 'full_provider_G3_G4_G5_G6_parent_formal_OPEN': True,
    'current_C09_note': 'Old R08 pending C09 concern is historical: corrected six public controls passed; public session.list adverse suspended current Main integration. No green source/formal inheritance.'}
pins['g2_finite_execution_scope'] = save('g2_finite_execution_scope.json', scope)
root_review = save('root_scope_review.json', {'decision': 'FROZEN_AUTHOR_CANDIDATES_NOT_ACCEPTED_G2_EXACT2_NEW_OWNER_BOUND_FINITE29_AUTHORIZED',
    'cli_source8_commit': cli['source_commit'], 'cli_evidence_commit': '60b9c00c648ec3110b31e6f5c6740cc105fc4c16',
    'cli_current_actual99_plus122_reported_not_selfacceptance': True, 'cli_existing2_and_P01_03_layer_gap_and_trueattach_P02_fullharness_HOLD': True,
    'list_source2_commit': list_handoff['source_commit'], 'list_actual14_reported_not_nonauthor_source_acceptance': True,
    'source_writer_CLI8_and_list2_stopped': True, 'g2_future29_all_NOT_RUN': True,
    'Main_integration_HOLD': True, 'lease6_24_and_Mu18_and_Desktop_only_readonly_future_designs': True,
    'new_actual_origins': 5, 'old362_prefix_preserved': True, 'counter_reset': False, 'formal_increment': 0})
audit = save('audit.json', {'canonical_before': before, 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'refs': pins,
    'manifests': manifest_audit, 'origins': origins, 'old_failure_count': 362,
    'new_origin_count': 5, 'after': 367, 'main_integration_authorized': False,
    'g2_source_test2_only_authorized': True, 'source_candidate_acceptance': False,
    'formal_increment': 0, 'counter_reset': False})
assert all(path.read_bytes() == raw for path, raw in READS.items())
prepared = save('prepared_refs.json', {'pins': pins, 'audit_ref': audit,
    'root_review_ref': root_review,
    'all_verified_refs': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
        for path, raw in sorted(READS.items(), key=lambda item: str(item[0]))],
    'canonical_before': before, 'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(),
    'new_origin_count': 5})
print(json.dumps({'prepared': prepared, 'audit': audit, 'scope': pins['g2_finite_execution_scope'],
    'verified_ref_count': len(READS), 'registration_executed': False}, ensure_ascii=True))
