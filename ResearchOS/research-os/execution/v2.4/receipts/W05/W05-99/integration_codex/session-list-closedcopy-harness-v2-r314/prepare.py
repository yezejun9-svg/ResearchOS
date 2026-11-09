import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'provider-g2-finite29-execute-r313'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
READS = {}
WT = ROOT / '.local/worktrees/codex-w0599-session-list-proof-r312'
NS = WT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V1 = NS / '907592b8e03d433da7de947435274481'
V2 = NS / 'v2-preparation-48a141cf916944aabe60ea42f6bd6dbe'
DESKTOP_FAILURE = ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/98552188a0014da3a6d73be7cdb3f9bd/failure-origin-tool-ad9051.json'


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
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_harness_v2_review_codex')
review = json.loads(read(review_path))
assert pin(review_path)['sha256'] == sys.argv[2]
assert review['decision'] == 'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION'
assert review['requested_changes'] == []
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [313, 141, 388]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
pins = {'harness_review': pin(review_path, sys.argv[2])}
for key, path, sha in [
    ('previous_handoff', PREVIOUS / 'handoff-r313-running.json', '005372be25b1fc78f4dd66b7f4730d2277d28b3a2bd39005ff91972822386e3e'),
    ('previous_manifest', PREVIOUS / 'manifest.json', 'b58f902dd61206e6564d59cedc2670d9fc0eff9210e4b90b9231e6c327dde36f'),
    ('original_source_scope', OUT.parent / 'session-list-closedcopy-exact1-r312/scope_registration.json', '31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c'),
    ('v2_driver', V2 / 'execute.py', 'b0610c0dc587dc138a5282660fe98841ab3cc41f98dc4607eadd2be9f6315782'),
    ('v2_launcher', V2 / 'launch.py', 'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e'),
    ('v2_manifest', V2 / 'manifest.json', 'da2d92526ee41ce99db469d67c5a6e53bf28e3f592e5cd9672f4f8654fcfd38e'),
    ('v2_handoff', V2 / 'handoff.json', '84801a82f0ff4a67a54a9f439ce2f544131512b9029ee023528fe26e42d7e6d9'),
    ('v2_static_audit', V2 / 'static_audit.json', 'af6860c21dec419dd0e6c237797433b61e988deb1c18e0761567068888996986'),
    ('cmd_failure', V1 / 'failure_origin.json', 'cba15c0ca93c9987be389fc7e0ac67049bfc0e9bbfc12fbb03fff87995288850'),
    ('cmd_stopped_report', V1 / 'stopped_report.json', '1a8e651ccbbdbf2adcbd423708596b643e846e7f273c19a23119879da266b652'),
    ('cmd_stopped_handoff', V1 / 'stopped_handoff.json', '213e3a68bf3b524dd133d1072ace223a669521755a0b49c5cdb5652c4ca365e4'),
    ('desktop_locator_failure', DESKTOP_FAILURE, '74294eeb3e2987c247427977c190527b2e71d35a69249e6ba46aae70bc52dd8b')]:
    pins[key] = pin(path, sha)
pins['cmd_source_before_new_execution'] = pin(WT / 'internal/api/v2_sessions_test.go', '54abc44af9e12181a1c19a07c0f1d192bd8e295626a825d79e6d1b93d824f320')
pins['cmd_domain_unchanged'] = pin(WT / 'internal/domain/client_protocol_sessions.go', '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3')
assert not (V2 / 'started.json').exists()
stopped = json.loads(read(V1 / 'stopped_report.json'))
desktop = json.loads(read(DESKTOP_FAILURE))
assert stopped['actual_outer_exit'] == stopped['actual_driver_exit'] == 1 and stopped['Go_invocations'] == stopped['cases_executed'] == 0
assert stopped['actual_Go_exit'] is None and len(stopped['cases_NOT_RUN']) == 14
assert desktop['actual_outer_exit'] == 1 and desktop['product_tests_executed'] == 0
origins = [
    {'origin_key': 'r312-cmd-closedcopy-directory-precondition-aa7b24', 'actor': 'codex:/root/command_queue_impl',
     'actual_outer_exit': 1, 'actual_native_exit': 1, 'native_kind': 'OWNED_PYTHON_DRIVER', 'actual_product_exit': None,
     'product_test_failures': 0, 'product_cases_run': 0, 'cause': stopped['cause'],
     'evidence_ref': pins['cmd_failure'], 'stopped_report_ref': pins['cmd_stopped_report'], 'original_payload': stopped},
    {'origin_key': 'desktop-readonly-locator-ad9051', 'actor': 'codex:/root/sources_parent_impl',
     'actual_outer_exit': 1, 'actual_native_exit': None, 'product_test_failures': 0, 'product_cases_run': 0,
     'cause': desktop['cause'], 'evidence_ref': pins['desktop_locator_failure'], 'original_payload': desktop},
]
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 388, 'after': 390, 'origins': origins, 'count_once': True, 'counter_reset': False})
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.closedcopy-targeted-harness-new-input-scope.v1',
    'status': 'AUTHORIZED_AFTER_ACTUAL_CAS314_ONLY_NOT_EXECUTED', 'registration_checkpoint': 314,
    'owner': 'codex:/root/command_queue_impl', 'root_integrator': 'codex:/root',
    'original_source_lease_ref': pins['original_source_scope'], 'harness_review_ref': pins['harness_review'],
    'driver_ref': pins['v2_driver'], 'launcher_ref': pins['v2_launcher'], 'handoff_ref': pins['v2_handoff'],
    'worktree': str(WT), 'source_exact_paths': ['internal/api/v2_sessions_test.go'],
    'source_current_ref': pins['cmd_source_before_new_execution'], 'domain_unchanged_ref': pins['cmd_domain_unchanged'],
    'targeted_change': 'Only validate/create exact owned .local parent and use new exclusive leaf; immutable v1/raw/source snapshots unchanged.',
    'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224,
    'SDK_MODEL_Node_external_paid_private_calls': 0, 'native_timeout_seconds': 150, 'owned_timeout_seconds': 180,
    'driver_timeout_seconds': 1800, 'first_unexpected_stop': True, 'automatic_same_input_retry': False,
    'previous_same_chain_actual_failures': 1, 'counter_reset': False,
    'known_limit': 'Same-user path-validation TOCTOU remains; handle-relative directory safety is not asserted.',
    'execution_grant': 'After actual CAS314 Root sends one precise follow-up to the owner; no pre-CAS launch or old-output retry.',
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0})
old = read(PREVIOUS / 'register.py').decode('utf-8')
header = old[:old.index("pins = prepared['pins']")].replace('[312, 140, 386]', '[313, 141, 388]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 314 and scope['cases'] == 14
assert not (ROOT / pins['v2_driver']['path']).with_name('started.json').exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 2
for row in prepared['origins']:
    assert row['origin_key'] not in old_keys and row['actual_outer_exit'] == 1
    ref(row['evidence_ref']['path'], row['evidence_ref']['sha256'])
    cp['failure_counters'].append({**row, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:388] == old_failures and len(cp['failure_counters']) == 390
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_harness_v2_scope_ref=pins['scope'],
    session_list_closedcopy_harness_v2_review_ref=pins['harness_review'],
    session_list_closedcopy_exact1_latest_failure_ref=pins['cmd_failure'],
    session_list_closedcopy_exact1_state='ACTUAL_DIRECTORY_PRECONDITION_FAILURE_RETAINED_TARGETED_V2_NEW_INPUT_ONCE_AUTHORIZED_NOT_EXECUTED',
    desktop_http_exact15_latest_locator_failure_ref=pins['desktop_locator_failure'])
subtask = ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']
assert subtask['current_source_writer'] == 'codex:/root/command_queue_impl'
subtask.update(harness_revision_scope_ref=pins['scope'], harness_revision_review_ref=pins['harness_review'],
    state='SOURCE_EXACT1_ACTIVE_NEW_INPUT_HARNESS_V2_ONCE_AUTHORIZED')
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
cp['failure_chains']['W05-99/r312-directory-precondition-and-Desktop-readonly-locator'] = {
    'actual_failed_invocations': 2, 'original388_prefix_unchanged': True, 'counter_reset': False,
    'audit_ref': pins['audit'], 'failure_cut_ref': pins['failure_cut'], 'automatic_same_input_retry': False}
cp['next_command'] = 'Cmd exact1 test-evidence source new-input harness v2 execute once after actual314; all14 and full compiler/input/DB/HTTP/Job assertions unchanged. Source Desktop15 implementation active. Root G2 exact29 finite replay already dispatched under313 immutable snapshot; await actual result. Old388+2=390 prefix preserved; Main and all22/42 acceptance HOLD.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'CLOSEDCOPY_TARGETED_HARNESS_V2_NEW_INPUT_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 388,
    'failure_origins_after': 390, 'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=314, expected_previous_revision=313, updated_at=now, updated_by='codex:/root')
ow.update(revision=142, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r313-running.json'")]
tail = tail.replace('root313.tmp', 'root314.tmp').replace('[313, 141, 388]', '[314, 142, 390]').replace('[:386]', '[:388]').replace('old386_', 'old388_')
tail = tail.replace('[312, 313]', '[313, 314]').replace('[140, 141]', '[141, 142]').replace('[386, 388]', '[388, 390]')
tail = tail.replace("'checkpoint': 313", "'checkpoint': 314").replace("'ownership': 141", "'ownership': 142").replace("'failure_origins': 388", "'failure_origins': 390")
tail = tail.replace("'new_actual_prepared_G2_finite29_execution_only': True", "'new_targeted_harness_v2_execution_only': True")
handoff = '''handoff_ref = save('handoff-r314-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 314, 'failure_origins': 390, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'harness_v2_scope_ref': pins['scope'], 'harness_v2_review_ref': pins['harness_review'],
    'next': 'Cmd new-input closedcopy harness v2 execute once; SourceDesktop15 and Root G2 finite29 continue.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 314, 'ownership': 142, 'failure_origins': 390, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8').replace('root_registration_r313_readonly_review_codex', 'root_registration_r314_readonly_review_codex')
wrapper = wrapper.replace("review['expected_before'] == [312, 140, 386] and review['expected_after'] == [313, 141, 388]", "review['expected_before'] == [313, 141, 388] and review['expected_after'] == [314, 142, 390]")
wrapper = wrapper.replace("cp['revision'] == 312 and len(cp['failure_counters']) == 386", "cp['revision'] == 313 and len(cp['failure_counters']) == 388")
wrapped = script('run.py', wrapper)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [313, 141, 388], 'expected_after': [314, 142, 390],
    'scope_ref': pins['scope'], 'harness_review_ref': pins['harness_review'], 'new_origins': origins,
    'old388_prefix_unchanged': True, 'maximum_active_construction_tasks': 2, 'both_source_writers_preserved': True,
    'Main_source_integration': False, 'formal_increment': 0, 'execution_after_CAS_only': True})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'HARNESS_V2_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
                  'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope']}, ensure_ascii=True))
