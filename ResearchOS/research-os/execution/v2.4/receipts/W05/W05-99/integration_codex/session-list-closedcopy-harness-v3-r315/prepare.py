import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v2-r314'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
READS = {}
WT = ROOT / '.local/worktrees/codex-w0599-session-list-proof-r312'
NS = WT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V2 = NS / 'v2-preparation-48a141cf916944aabe60ea42f6bd6dbe'
V3 = NS / 'v3-boundary-preparation-cafb9c77a62a4904bb2027ea866ff947'
DESKTOP = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd'


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
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_harness_v3_review_codex')
review = json.loads(read(review_path))
assert pin(review_path)['sha256'] == sys.argv[2]
assert review['decision'] == 'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION' and review['requested_changes'] == []
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [314, 142, 390]
tools = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = tools['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
pins = {'harness_review': pin(review_path, sys.argv[2])}
for key, path, sha in [
    ('previous_handoff', PREVIOUS / 'handoff-r314-running.json', '9da9c11800e60c0c31d317ae2774be2d484ebd2e886bfea1afbd98c7fcdc4d28'),
    ('previous_manifest', PREVIOUS / 'manifest.json', 'b37b6dd186471dcd4aa727c2912939375993dfcf72c0ba54b783983bb18a5e92'),
    ('original_source_scope', OUT.parent / 'session-list-closedcopy-exact1-r312/scope_registration.json', '31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'),
    ('v3_driver', V3 / 'execute.py', 'ad5a3513eca16c31ae4a4c72b054aabcaf7069e698aac77cc12901ad225bb8ea'),
    ('v3_launcher', V3 / 'launch.py', 'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e'),
    ('v3_manifest', V3 / 'manifest.json', '39cdfc243462449f271bc8c1599449142c28431367a377cdfa0d06549e1f27b5'),
    ('v3_handoff', V3 / 'handoff.json', 'c18ca148dbd368252b97df1ba0a330d7148a4b98ca73dba693fbb2f3c9b58c21'),
    ('v3_static_audit', V3 / 'static_audit.json', 'e415084c51f000f2f823dfbf336c4dcb382387252266874f4d13cb52a90ac33e'),
    ('cmd_stopped_report', V2 / 'stopped_report.v2.json', '6e1f0c9dbda5568b4ff0cf456665649c80258dca47670044d785d919357de6a1'),
    ('cmd_stopped_handoff', V2 / 'stopped_handoff.v2.json', '96d46071c26f6721cf7d3f62ea4a3abdfd9c47933815097ac6b9cb85709741b9'),
    ('cmd_stopped_manifest', V2 / 'stopped_manifest.v2.json', 'cf503c211b2c5b8cfdffc6f1609bc4e94b88ed1c673ba615c45e2e6063dc33b6'),
    ('desktop_import_failure', DESKTOP / 'failure-origin-finite-e0b034.json', '979f4b45f5fa2f7e9e93446d45539424eaa0ad603d7d6777486d6d955fad1e69'),
    ('desktop_diagnostic_failure', DESKTOP / 'failure-origin-finite-56b97d.json', 'c4c1d015715b8a6c015eba2dc8ef1e416254b953cdf239ae6c685090c9af05a4')]:
    pins[key] = pin(path, sha)
pins['cmd_failure'] = pin(V2 / 'failure_origin.json')
pins['cmd_source_before_new_execution'] = pin(WT / 'internal/api/v2_sessions_test.go', '9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae')
pins['cmd_domain_unchanged'] = pin(WT / 'internal/domain/client_protocol_sessions.go', '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3')
assert not (V3 / 'started.json').exists()
stopped = json.loads(read(V2 / 'stopped_report.v2.json'))
assert stopped['actual_outer_exit'] == stopped['actual_driver_exit'] == 1
assert stopped['Go_compiles'] == stopped['cases_executed'] == 0 and len(stopped['NOT_RUN']) == 14
assert stopped['same_chain_actual_failures'] == 2 and stopped['causal_difference']['exactly_one_new_separator_newline'] is True
origins = [{'origin_key': 'r314-cmd-closedcopy-prefix-single-LF-18e863', 'actor': 'codex:/root/command_queue_impl',
    'actual_outer_exit': 1, 'actual_native_exit': 1, 'native_kind': 'OWNED_PYTHON_DRIVER', 'actual_product_exit': None,
    'product_test_failures': 0, 'product_cases_run': 0, 'cause': stopped['cause'], 'evidence_ref': pins['cmd_failure'],
    'stopped_report_ref': pins['cmd_stopped_report'], 'original_payload': stopped}]
for key in ['desktop_import_failure', 'desktop_diagnostic_failure']:
    raw = json.loads(read(ROOT / pins[key]['path']))
    assert raw['native_exit'] == 1 and raw['wrapper_outer_exit'] == 0
    origins.append({'origin_key': raw['origin'], 'actor': 'codex:/root/sources_parent_impl',
        'actual_outer_exit': 0, 'actual_native_exit': 1, 'native_kind': 'OWNED_NODE_TEST_EXECUTOR',
        'product_test_failures': raw.get('batch_fail', 0),
        'actual_completed_product_leaf_pass': raw.get('actual_leaf_pass', raw.get('batch_pass', 0)),
        'source_behavior_conclusion': 'Selected diagnostic leaf failure is retained; numeric behavior is not certified by the diagnostic exception.',
        'cause': raw['cause'], 'evidence_ref': pins[key], 'original_payload': raw})
assert len(origins) == len({row['origin_key'] for row in origins}) == 3
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 390, 'after': 393, 'origins': origins, 'count_once': True, 'counter_reset': False})
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.closedcopy-targeted-harness-new-input-scope.v1',
    'status': 'AUTHORIZED_AFTER_ACTUAL_CAS315_ONLY_NOT_EXECUTED', 'registration_checkpoint': 315,
    'owner': 'codex:/root/command_queue_impl', 'root_integrator': 'codex:/root',
    'original_source_lease_ref': pins['original_source_scope'], 'harness_review_ref': pins['harness_review'],
    'driver_ref': pins['v3_driver'], 'launcher_ref': pins['v3_launcher'], 'handoff_ref': pins['v3_handoff'],
    'worktree': str(WT), 'source_exact_paths': ['internal/api/v2_sessions_test.go'],
    'source_current_ref': pins['cmd_source_before_new_execution'], 'domain_unchanged_ref': pins['cmd_domain_unchanged'],
    'targeted_change': 'Exact old prefix plus one LF belonging to the new helper; no normalization and all original body/suffix guards unchanged. New exclusive WORK leaf.',
    'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224,
    'SDK_MODEL_Node_external_paid_private_calls': 0, 'native_timeout_seconds': 150, 'owned_timeout_seconds': 180,
    'driver_timeout_seconds': 1800, 'first_unexpected_stop': True, 'automatic_same_input_retry': False,
    'previous_same_chain_actual_failures': 2, 'counter_reset': False,
    'progress_before_this_revision': 'Owned parent creation, Git HEAD/status and gofmt actually succeeded; original body/suffix now independently proven unchanged.',
    'known_limit': 'Same-user path-validation TOCTOU remains; handle-relative directory safety is not asserted.',
    'execution_grant': 'After actual CAS315 Root sends one precise follow-up to the owner; no pre-CAS launch or old-output retry.',
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0})
old = read(PREVIOUS / 'register.py').decode('utf-8')
header = old[:old.index("pins = prepared['pins']")].replace('[313, 141, 388]', '[314, 142, 390]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 315 and scope['cases'] == 14
assert not (ROOT / pins['v3_driver']['path']).with_name('started.json').exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 3
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and (row['actual_outer_exit'] == 1 or row['actual_native_exit'] == 1)
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:390] == old_failures and len(cp['failure_counters']) == 393
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_harness_v3_scope_ref=pins['scope'],
    session_list_closedcopy_harness_v3_review_ref=pins['harness_review'],
    session_list_closedcopy_exact1_latest_failure_ref=pins['cmd_failure'],
    session_list_closedcopy_exact1_state='ACTUAL_PREFIX_SINGLE_LF_BOUNDARY_ORIGIN_RETAINED_TARGETED_V3_NEW_INPUT_ONCE_AUTHORIZED_NOT_EXECUTED',
    desktop_http_exact15_latest_import_failure_ref=pins['desktop_import_failure'],
    desktop_http_exact15_latest_diagnostic_failure_ref=pins['desktop_diagnostic_failure'])
subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
subtask.update(harness_revision_scope_ref=pins['scope'], harness_revision_review_ref=pins['harness_review'],
    state='SOURCE_EXACT1_ACTIVE_NEW_INPUT_HARNESS_V3_ONCE_AUTHORIZED')
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
cp['failure_chains']['W05-99/r314-prefix-boundary-and-Desktop-finite-executor'] = {
    'actual_failed_invocations': 3, 'original390_prefix_unchanged': True, 'counter_reset': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Cmd exact1 evidence source new-input harness v3 execute once after actual315, preserving exact old prefix+1LF/all14/fullclosure/DB/HTTP/Job guards. Source Desktop15 keeps 69+9 historical positive leaves and retained module/diagnostic stops; final current159+7 not accepted. Root G2 finite29 running under immutable313 snapshot. Old390+3=393 preserved; Main and all22/42 HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSEDCOPY_TARGETED_HARNESS_V3_NEW_INPUT_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 390,
    'failure_origins_after': 393, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=315, expected_previous_revision=314, updated_at=now, updated_by='codex:/root')
ow.update(revision=143, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r314-running.json'")]
tail = tail.replace('root314.tmp', 'root315.tmp').replace('[314, 142, 390]', '[315, 143, 393]').replace('[:388]', '[:390]').replace('old388_', 'old390_')
tail = tail.replace('[313, 314]', '[314, 315]').replace('[141, 142]', '[142, 143]').replace('[388, 390]', '[390, 393]')
tail = tail.replace("'checkpoint': 314", "'checkpoint': 315").replace("'ownership': 142", "'ownership': 143").replace("'failure_origins': 390", "'failure_origins': 393")
tail = tail.replace("'new_targeted_harness_v2_execution_only': True", "'new_targeted_harness_v3_execution_only': True")
handoff = '''handoff_ref = save('handoff-r315-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 315, 'failure_origins': 393, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'harness_v3_scope_ref': pins['scope'], 'harness_v3_review_ref': pins['harness_review'],
    'next': 'Cmd new-input closedcopy harness v3 execute once; SourceDesktop15 and Root G2 finite29 continue.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 315, 'ownership': 143, 'failure_origins': 393, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8').replace('root_registration_r314_readonly_review_codex', 'root_registration_r315_readonly_review_codex')
wrapper = wrapper.replace("review['expected_before'] == [313, 141, 388] and review['expected_after'] == [314, 142, 390]", "review['expected_before'] == [314, 142, 390] and review['expected_after'] == [315, 143, 393]")
wrapper = wrapper.replace("cp['revision'] == 313 and len(cp['failure_counters']) == 388", "cp['revision'] == 314 and len(cp['failure_counters']) == 390")
wrapped = script('run.py', wrapper)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [314, 142, 390], 'expected_after': [315, 143, 393],
    'scope_ref': pins['scope'], 'harness_review_ref': pins['harness_review'], 'new_origins': origins,
    'old390_prefix_unchanged': True, 'Desktop_native1_outer0_origins_distinct': True,
    'maximum_active_construction_tasks': 2, 'both_source_writers_preserved': True,
    'Main_source_integration': False, 'formal_increment': 0, 'execution_after_CAS_only': True})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'HARNESS_V3_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
                  'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope']}, ensure_ascii=True))
