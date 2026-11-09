import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v3-r315'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
READS = {}
WT = ROOT / '.local/worktrees/codex-w0599-session-list-proof-r312'
NS = WT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V3 = NS / 'v3-boundary-preparation-cafb9c77a62a4904bb2027ea866ff947'
V4 = NS / 'v4-encoding-preparation-0a6c023f68e849ea8fa73443dfa3b10b'
DESKTOP = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'
AUDITOR = ROOT / 'execution/v2.4/receipts/W05/W05-99/root_registration_r315_readonly_review_codex/9f2550ee1b144f9d91d48da291dff594'


def read(path):
    path = Path(path).resolve()
    assert path.is_relative_to(ROOT)
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


assert sys.flags.isolated and not sys.flags.optimize and len(sys.argv) == 3
review_path = Path(sys.argv[1]).resolve()
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_harness_v4_review_codex')
review = json.loads(read(review_path))
assert pin(review_path)['sha256'] == sys.argv[2]
assert review['decision'] == 'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION' and review['requested_changes'] == []
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [315, 143, 393]
tools = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = tools['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
pins = {'harness_review': pin(review_path, sys.argv[2])}
for key, path, sha in [
    ('previous_handoff', PREVIOUS / 'handoff-r315-running.json', '7890fb2758df00e1fd51f26ec97784d70f7a3007f36197058a53e50816f37a7f'),
    ('previous_manifest', PREVIOUS / 'manifest.json', 'cbc2650dccb51fe2b6d86809370d301f54efd65e7d681364e77a5fa147ffdd0d'),
    ('original_source_scope', OUT.parent / 'session-list-closedcopy-exact1-r312/scope_registration.json', '31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'),
    ('v4_driver', V4 / 'execute.py', 'e52fd10a4dbb6b3fb29850c4fae003c1e502bc629de0c11440a39a21204c8326'),
    ('v4_launcher', V4 / 'launch.py', 'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e'),
    ('v4_manifest', V4 / 'manifest.json', '3bcea5a0002096a6e5acf894035dbc5bfec9de5dd8b1a583b6d0326056c44920'),
    ('v4_handoff', V4 / 'handoff.json', 'a31ad0c9f068ee2d5e3fb631a7d8a426c93198d348131c773b0e8e80b176c28d'),
    ('v4_static_audit', V4 / 'static_audit.json', '1c4b41dd2572277d64f97480fdfafa39f163247426a1e8057c90d2cf592b94f4'),
    ('cmd_stopped_report', V3 / 'stopped_report.v3.json', '5f7ac18865adca3488a71a9a07f87d2ba36af452b774b1ee7f18e5c93af83b96'),
    ('cmd_stopped_handoff', V3 / 'stopped_handoff.v3.json', '31e3abb5b200da0fc90a980ef46fb1bb252c23986819a8647eaff83e5a06f1b6'),
    ('cmd_stopped_manifest', V3 / 'stopped_manifest.v3.json', 'beedab3c9907aebfefd33f4b8602af16b60978ad27dd23a5133df2a4883fc244')]:
    pins[key] = pin(path, sha)
pins['cmd_failure'] = pin(V3 / 'failure_origin.json', '9c28b7c29f52a21452c2e9e3aac23bc7a80e9c84cd583563e96213a34643cbb8')
pins['cmd_source_before_new_execution'] = pin(WT / 'internal/api/v2_sessions_test.go', '9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae')
pins['cmd_domain_unchanged'] = pin(WT / 'internal/domain/client_protocol_sessions.go', '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3')
assert not (V4 / 'started.json').exists()
stopped = json.loads(read(V3 / 'stopped_report.v3.json'))
cmd_raw = json.loads(read(V3 / 'failure_origin.json'))
assert stopped['actual_outer_exit'] == stopped['actual_driver_exit'] == cmd_raw['actual_driver_exit'] == 1
assert stopped['actual_cases'] == 0 and len(stopped['NOT_RUN']) == 14
assert len(cmd_raw['invocations']) == 7 and all(row['actual_exit'] == 0 for row in cmd_raw['invocations'])
origins = [{'origin_key': 'r315-cmd-closedcopy-strictUTF8-30a0d4', 'actor': 'codex:/root/command_queue_impl',
    'event_kind': 'ACTUAL_NONZERO_EXECUTION', 'actual_outer_exit': 1, 'actual_native_exit': 1,
    'native_kind': 'OWNED_PYTHON_DRIVER', 'actual_product_exit': None, 'product_cases_run': 0,
    'product_test_failures': 0, 'actual_compile_exit': 0, 'cause': stopped['cause'],
    'evidence_ref': pins['cmd_failure'], 'stopped_report_ref': pins['cmd_stopped_report'],
    'original_payload': cmd_raw, 'original_stopped_report': stopped}]
for name, sha in [
    ('failure_origin.json', '51dfefc04507240b345364fa29b4cfd9a5a94fc0024a2e407b2d9dad75f0981f'),
    ('failure_origin.eebbe6.json', '28f9c101599911660f22762a98d6a46f3d0a583988fb59315501f042aae11776'),
    ('failure_origin.77e582.json', '1ccb1906455a62dd26a684d2889e86a2512dc9bd36ba39e8de1fc5346c1a0aea')]:
    raw = json.loads(read(AUDITOR / name))
    assert raw['actual_native_exit'] == raw['actual_outer_exit'] == 1 and raw['raw_file'] is None
    evidence = pin(AUDITOR / name, sha)
    pins['auditor_' + name] = evidence
    origins.append({**raw, 'event_kind': 'ACTUAL_NONZERO_EXECUTION', 'evidence_ref': evidence, 'original_payload': raw})
for name, sha, qualification in [
    ('failure-origin-finite-36eb30.json', '9942bed3f0c2a35b81973d713c41ea83ef04bfce990ceddf9dfea61c020bb389', False),
    ('qualification-deviation-aaf4fd.json', '9ecc2d5a08ac5cdd8342dcb138d736ed4e13825b2d0536228f3677306079ae5b', True),
    ('failure-origin-finite-286911.json', '070fc92f2081ea5e37e74975542f64347cad0d9d9c3ed3a94de4fd3ef8a45dca', False),
    ('failure-origin-finite-ae587f.json', 'b982594550e566d77a02ae42dbe23f5d6208d766e0a44151f08f8aaffbbb41d1', False),
    ('failure-origin-finite-2c014c.json', 'e35bb1115580a7670965714fe09d49be7269890acbe7d33eb37cea73c5e2fd0c', False),
    ('qualification-deviation-43ff1b.json', '5c17a23f9e6d250c1c6b2eca497b7b2f8eb1f53194d537399efbba0e4776643f', True),
    ('failure-origin-finite-ce8887.json', 'fabb1bb61c769d18a6fbb3dd13e33999cd2bbbea92b30c5a0afc3633ad1cb0cc', False)]:
    raw = json.loads(read(DESKTOP / name))
    native = raw.get('native_exit', raw.get('native_node_exit'))
    assert raw['wrapper_outer_exit'] == 0 and native == (0 if qualification else 1)
    evidence = pin(DESKTOP / name, sha)
    pins['desktop_' + name] = evidence
    origins.append({'origin_key': raw['origin'], 'actor': 'codex:/root/sources_parent_impl',
        'event_kind': 'QUALIFICATION_DEVIATION' if qualification else 'ACTUAL_NONZERO_EXECUTION',
        'actual_outer_exit': 0, 'actual_native_exit': native, 'native_kind': 'OWNED_NODE_TEST_EXECUTOR',
        'native_failure_count': 0 if qualification else 1, 'qualification_failure_count': 1 if qualification else 0,
        'cause': raw.get('cause', raw.get('actual_cause_boundary')), 'evidence_ref': evidence, 'original_payload': raw})
for name in ['failure_origin.prepare-4410af.json', 'failure_origin.prepare-17e95e.json']:
    raw = json.loads(read(OUT / name))
    evidence = pin(OUT / name)
    pins['root_' + name] = evidence
    origins.append({**raw, 'evidence_ref': evidence, 'original_payload': raw})
assert len(origins) == len({row['origin_key'] for row in origins}) == 13
assert sum(row['event_kind'] == 'QUALIFICATION_DEVIATION' for row in origins) == 2
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 393, 'after': 406, 'origins': origins,
    'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2, 'count_once': True, 'counter_reset': False})
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.closedcopy-targeted-harness-new-input-scope.v1',
    'status': 'AUTHORIZED_AFTER_ACTUAL_CAS316_ONLY_NOT_EXECUTED', 'registration_checkpoint': 316,
    'owner': 'codex:/root/command_queue_impl', 'root_integrator': 'codex:/root',
    'original_source_lease_ref': pins['original_source_scope'], 'harness_review_ref': pins['harness_review'],
    'driver_ref': pins['v4_driver'], 'launcher_ref': pins['v4_launcher'], 'handoff_ref': pins['v4_handoff'],
    'worktree': str(WT), 'source_exact_paths': ['internal/api/v2_sessions_test.go'],
    'source_current_ref': pins['cmd_source_before_new_execution'], 'domain_unchanged_ref': pins['cmd_domain_unchanged'],
    'targeted_change': 'Two Go-generated text reads use strict UTF-8; new exclusive WORK leaf. No fallback, normalization, path repair, guard or scenario change.',
    'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224,
    'SDK_MODEL_Node_external_paid_private_calls': 0, 'native_timeout_seconds': 150, 'owned_timeout_seconds': 180,
    'driver_timeout_seconds': 1800, 'first_unexpected_stop': True, 'automatic_same_input_retry': False,
    'previous_same_chain_actual_failures': 3, 'counter_reset': False,
    'progress_before_this_revision': 'Git/gofmt/full go-list and real compilation succeeded; first archive pin stopped on incorrect system-default decoding. Fourteen product cases remain NOT_RUN.',
    'known_limit': 'Same-user path-validation TOCTOU remains; handle-relative directory safety is not asserted.',
    'execution_grant': 'After actual CAS316 and Root seal, Root sends one precise follow-up to the owner; no pre-CAS launch or old-output retry.',
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0})
old = read(PREVIOUS / 'register.py').decode('utf-8')
header = old[:old.index("pins = prepared['pins']")].replace('[314, 142, 390]', '[315, 143, 393]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 316 and scope['cases'] == 14
assert not (ROOT / pins['v4_driver']['path']).with_name('started.json').exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 13
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys
    if row['event_kind'] == 'QUALIFICATION_DEVIATION':
        assert row['actual_outer_exit'] == row['actual_native_exit'] == row['native_failure_count'] == 0
        assert row['qualification_failure_count'] == 1
        status_value = 'ZERO_EXIT_QUALIFICATION_DEVIATION_PRESERVED_NOT_ACCEPTED'
    else:
        assert row['event_kind'] == 'ACTUAL_NONZERO_EXECUTION'
        assert row['actual_outer_exit'] == 1 or row['actual_native_exit'] == 1
        status_value = 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE'
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': status_value, 'formal_increment': 0})
assert cp['failure_counters'][:393] == old_failures and len(cp['failure_counters']) == 406
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_harness_v4_scope_ref=pins['scope'],
    session_list_closedcopy_harness_v4_review_ref=pins['harness_review'],
    session_list_closedcopy_exact1_latest_failure_ref=pins['cmd_failure'],
    session_list_closedcopy_exact1_state='ACTUAL_UTF8_DECODE_FAILURE_RETAINED_TARGETED_V4_NEW_INPUT_ONCE_AUTHORIZED_NOT_EXECUTED',
    desktop_http_exact15_pending_seven_origins_registered=True,
    r315_independent_review_three_actual_failures_registered=True)
subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
subtask.update(harness_revision_scope_ref=pins['scope'], harness_revision_review_ref=pins['harness_review'],
    state='SOURCE_EXACT1_ACTIVE_NEW_INPUT_HARNESS_V4_ONCE_AUTHORIZED')
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
cp['failure_chains']['W05-99/r315-utf8-and-review-Desktop-finite-origins'] = {
    'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2,
    'original393_prefix_unchanged': True, 'counter_reset': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Cmd exact1 v4 strictUTF8/new WORK execute once after actual316+seal. SourceDesktop15 author reports current159+7 under one frozen cohort; protected ranges/commits/non-author review still required. Root G2 finite29 executes under immutable313 snapshot; original and v2 sealers are unexecuted REQUEST_CHANGES. Old393+11 nonzero+2 qualification deviations=406 preserved with actual exits. Main/all22/all42 HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSEDCOPY_TARGETED_HARNESS_V4_NEW_INPUT_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 393,
    'failure_origins_after': 406, 'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=316, expected_previous_revision=315, updated_at=now, updated_by='codex:/root')
ow.update(revision=144, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r315-running.json'")]
tail = tail.replace('root315.tmp', 'root316.tmp').replace('[315, 143, 393]', '[316, 144, 406]').replace('[:390]', '[:393]').replace('old390_', 'old393_')
tail = tail.replace('[314, 315]', '[315, 316]').replace('[142, 143]', '[143, 144]').replace('[390, 393]', '[393, 406]')
tail = tail.replace("'checkpoint': 315", "'checkpoint': 316").replace("'ownership': 143", "'ownership': 144").replace("'failure_origins': 393", "'failure_origins': 406")
tail = tail.replace("'new_targeted_harness_v3_execution_only': True", "'new_targeted_harness_v4_execution_only': True")
handoff = '''handoff_ref = save('handoff-r316-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 316, 'failure_origins': 406, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'harness_v4_scope_ref': pins['scope'], 'harness_v4_review_ref': pins['harness_review'],
    'next': 'Cmd new-input strictUTF8 closedcopy harness v4 execute once after seal; SourceDesktop15 non-author review preparation and Root G2 finite29 continue.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 316, 'ownership': 144, 'failure_origins': 406, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8').replace('root_registration_r315_readonly_review_codex', 'root_registration_r316_readonly_review_codex')
wrapper = wrapper.replace("review['expected_before'] == [314, 142, 390] and review['expected_after'] == [315, 143, 393]", "review['expected_before'] == [315, 143, 393] and review['expected_after'] == [316, 144, 406]")
wrapper = wrapper.replace("cp['revision'] == 314 and len(cp['failure_counters']) == 390", "cp['revision'] == 315 and len(cp['failure_counters']) == 393")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8').replace("'session-list-closedcopy-harness-v2-r314'", "'session-list-closedcopy-harness-v3-r315'")
sealer = sealer.replace('[315, 143, 393]', '[316, 144, 406]').replace('[314, 142, 390]', '[315, 143, 393]').replace('[:390]', '[:393]').replace('old390_', 'old393_').replace("'new_v3_execution'", "'new_v4_execution'")
seal = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [315, 143, 393], 'expected_after': [316, 144, 406],
    'scope_ref': pins['scope'], 'harness_review_ref': pins['harness_review'], 'new_origins': origins,
    'old393_prefix_unchanged': True, 'new_actual_nonzero_origins': 11, 'new_zero_exit_qualification_deviations': 2,
    'zero_exit_not_rewritten_as_native_failure': True, 'nested_Node_Electron_and_validator_counts_not_conflated': True,
    'maximum_active_construction_tasks': 2, 'both_source_writers_preserved': True,
    'Main_source_integration': False, 'formal_increment': 0, 'execution_after_CAS_and_seal_only': True})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'HARNESS_V4_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope'], 'seal': seal}, ensure_ascii=True))
