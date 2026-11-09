import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r319'
CANON = [ROOT / 'execution/v2.4' / (name + '.json') for name in ['checkpoint', 'path_ownership', 'step_state', 'commands']]
READS = {}


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
    assert expected is None or result['sha256'] == expected, str(path)
    return result


def doc(item):
    assert pin(ROOT / item['path']) == item
    return json.loads(read(ROOT / item['path']))


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return pin(OUT / name)


def script(name, source):
    ast.parse(source)
    with (OUT / name).open('xb') as stream:
        stream.write(source.encode('utf-8'))
    return pin(OUT / name)


def once(source, old, new):
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new, 1)


assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and len(sys.argv) == 1
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [319, 147, 413]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
for key in ['python', 'git', 'go']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
pins = {}
for key, path, expected in [
    ('previous_handoff', PREVIOUS / 'handoff-r319-running.json', '25f207a38dda2e717d469471ea85e0843fa65f3af5c76e6d9a8003fb2d5b42a7'),
    ('previous_manifest', PREVIOUS / 'manifest.json', '2078bbcf42a66e6ce8b940babdd37440e9f6858e5a3cadfd04b4ee85b687d9c9'),
    ('root14_scope', OUT.parent / 'session-list-closedcopy-root-replay-draft/root_finite14_scope.v3.json', '55e4c169937d2ecc4bc1aaa98e30538dab8071e9870ffd1c7c3309a636e81eda'),
    ('desktop_revision_review', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_revision_independent_review_codex/874a69212bac4d44be6316a27dc0bf32/review.json', 'ec0db191e493799a7e1623da8c04bc6dff8a320b9a700afc0f2c24e5ed74fa2a'),
    ('desktop_revision_manifest', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_revision_independent_review_codex/874a69212bac4d44be6316a27dc0bf32/manifest.json', '357a7fa265a2ccfb5de186b072f38d8d16174fecd7f09a4d765ca26e556a4e46'),
    ('desktop_revision_handoff', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_revision_independent_review_codex/874a69212bac4d44be6316a27dc0bf32/handoff.json', 'df258454a8436b764251706a981d1f5a30d77ba7f4324e2866f56aa27effbe97'),
    ('go3_spec', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137/spec.v2.json', '858463e5dd1f5570c372de42476c65042d5e3d675085317711fe377323a4db76'),
    ('go3_review', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_v2_static_independent_review_codex/5c67090f25f846ebba8e5d893662c411/review.json', '7af24427796d89c23dba17d6c3d3665ce3bda117355721d34fc2952e51a2a079'),
    ('go3_review_manifest', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_v2_static_independent_review_codex/5c67090f25f846ebba8e5d893662c411/manifest.json', '62c2e13a832eaf12c8a20e6720aba5a0656b5fc29f4dfa3b188b18a9f4f94c33'),
    ('go3_proposal_manifest', ROOT / 'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137/manifest.json', 'cd68a08d19558ae746207e2125320631d96cb3999120da600fbea9f94bfb6958'),
    ('w09_proposal', ROOT / 'execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_proposal_codex/c64f2c8e07794f7183c8ef34325fdcbb/scope_proposal.json', 'a319d215a5216df92daa8d448b181338923502b768989c10a2cc3e960658bdcf'),
    ('w09_roster', ROOT / 'execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_proposal_codex/c64f2c8e07794f7183c8ef34325fdcbb/finite-roster.json', 'b791dcc8572de76bba3269b8640e4311ed232678fdbd9b5749dc8258850dae35'),
    ('w09_manifest', ROOT / 'execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_proposal_codex/c64f2c8e07794f7183c8ef34325fdcbb/manifest.json', 'fcec22f470d50fd5bf31a0c5a09e8199d139e4eb304902bd452ef2d28ceea756'),
    ('w09_review', ROOT / 'execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_independent_review_codex/8b603ab227ee4b179b58458a2ef518ab/scope_review.json', 'e539a910c54627718deaee0cf815470335ecf3eb091220e8196e998a852a31a8'),
    ('w09_diagnostics', ROOT / 'execution/v2.4/receipts/W09/W09-99/test_only_causal_scope_proposal_codex/c64f2c8e07794f7183c8ef34325fdcbb/tool-diagnostics.json', '6a44285d9457be53b0f20409f4d3b1bccd173041f06ddad6cace5f3793bd6acd'),
    ('source_prior_diagnostics', ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/go3-os-capture-proposal-a5d80ce786ac429a862bd5ca8ca4e358/tool-diagnostics.json', 'eb1767eec09cf80fcdbce1d800ea7126d841bfbe751923b74a5b4f39d0c55d4c'),
    ('root_lookup_origin', OUT.parent / 'diagnostic-lookup-536e3d/failure-origin.json', None)]:
    pins[key] = pin(path, expected)
w09 = doc(pins['w09_proposal'])
assert w09['base_commit'] == head and w09['handler_exact_intersection'] == []
assert w09['new_scenarios'] == 41 and w09['core'] == 39 and w09['OS_conditional'] == 2
assert doc(pins['w09_review'])['decision'] == 'READY_FOR_ROOT_EXACT4_SOURCE_IMPLEMENTATION_ONLY'
source_paths = [row['path'] for row in w09['exact_source_paths']]
assert source_paths == ['internal/domain/evidence_w0901_test.go', 'internal/domain/evidence_w0902_test.go', 'internal/domain/retrieval_test.go', 'adapters/retrieval/local_test.go']
for row in w09['exact_source_paths']:
    item = pin(ROOT / row['path'], row['preimage']['sha256'])
    assert item['bytes'] == row['preimage']['bytes']
    pin(row['snapshot_ref']['path'], row['snapshot_ref']['sha256'])
    assert row['base_blob_sha256'] == row['handler_blob_sha256'] == item['sha256']
go3 = doc(pins['go3_spec'])
assert doc(pins['go3_review'])['decision'] == 'READY_FOR_ROOT_REGISTERED_GO3_DEBUG_PROOF_ONCE'
assert go3['python_flags'] == ['-I', '-S', '-X', 'utf8'] and go3['caps']['test_executions'] == 1
assert not Path(go3['new_output_root']).exists()
for key in ['runner_ref', 'debug_helper_ref', 'outer_helper_ref', 'runtime_catalog_ref']:
    pins['go3_' + key] = pin(go3[key]['path'], go3[key]['sha256'])
    assert pins['go3_' + key]['bytes'] == go3[key]['bytes']
assert go3['runner_ref']['sha256'] == 'fe61a605425d17f0ece750e1b843aa3fd88f3d8939db1791055ec0f9125a26e1'
assert go3['debug_helper_ref']['sha256'] == 'b60c8826fb13fc24947965579492b6f4aad76d7d95588fdfe2525daa1941f725'
gofmt_path = Path(lock['go']['path']).parent / 'gofmt.exe'
pins['gofmt'] = pin(gofmt_path)
nonce = uuid.uuid4().hex
worktree = '.local/worktrees/codex-w0999-causal-controls-r320-' + nonce[:12]
assert not (ROOT / worktree).exists()
pins['w09_scope'] = save('w09_source_scope.json', {
    'schema': 'researchos.w09.exact4-source-only-registration.v1', 'registration_checkpoint': 320,
    'state': 'AUTHORIZED_ONLY_AFTER_ACTUAL_CAS320_AND_SEAL', 'owner': 'codex:/root/sources_parent_impl',
    'base_commit': head, 'worktree_root': worktree, 'branch': 'codex/w0999-causal-controls-r320-' + nonce[:12],
    'source_paths': source_paths, 'exact_source_preimages': w09['exact_source_paths'],
    'scope_proposal_ref': pins['w09_proposal'], 'finite_roster_ref': pins['w09_roster'], 'scope_review_ref': pins['w09_review'],
    'source_policy': w09['bounds'], 'original_bodies_comments_assertionIDs_SQL_guards_protected': True,
    'formatting': {'tool_ref': pins['gofmt'], 'maximum_invocations': 3, 'timeout_seconds': 30,
        'argv': ['<pinned-gofmt>', '-w', '<only exact4 files in own worktree>'],
        'owned_process_helper_ref': pins['go3_outer_helper_ref'], 'nonproduct_static_format_only': True},
    'receipt_namespace': 'execution/v2.4/receipts/W09/W09-99/test_only_causal_exact4_executor_codex/' + nonce,
    'main_source_writes': 0, 'Go_compile': 0, 'Go_test': 0, 'SQL': 0, 'API': 0, 'HTTP': 0,
    'native_OS_link_probe': 0, 'SDK_MODEL_external_paid': 0,
    'next_execution_requirement': 'Frozen source-only candidate and actual finite controller/inputs/resources/numeric caps require distinct Root review and grant before compiling or executing tests.',
    'source_acceptance': False, 'formal_increment': 0, 'Main_integration_authorized': False,
    'maximum_active_construction_tasks': 2, 'first_unexpected_stop': True, 'automatic_retry': False, 'counter_reset': False})
pins['go3_scope'] = save('go3_execution_scope.json', {
    'schema': 'researchos.root-go3-debug-component-execution-registration.v1', 'registration_checkpoint': 320,
    'state': 'ROOT_ONCE_GRANT_ONLY_AFTER_ACTUAL_CAS320_SEAL', 'owner': 'codex:/root',
    'spec_ref': pins['go3_spec'], 'review_ref': pins['go3_review'], 'proposal_manifest_ref': pins['go3_proposal_manifest'],
    'review_manifest_ref': pins['go3_review_manifest'], 'source_commit': go3['source_commit'],
    'selectors': go3['selectors'], 'test_exe': go3['test_exe'], 'caps': go3['caps'], 'python_flags': go3['python_flags'],
    'new_output_root': go3['new_output_root'], 'authority': 'Root issues exact immutable grant binding actual sealed320 scope/review/registration refs; false proposal template is never authority.',
    'condition': 'DEBUG_ONLY_THIS_PROCESS new component proof; old normal Go3 OS observation gap remains historical, Python inventory point-in-time only.',
    'Root_shell_walltime_limit': '600+5 bounds owned inner/Go child subtree only; preflight and evidence IO outside that interval explicitly disclosed.',
    'source_edits': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'first_unexpected_stop': True, 'automatic_retry': False, 'counter_reset': False})
origins = []
root_failure = doc(pins['root_lookup_origin'])
origins.append({'origin_key': root_failure['origin_key'], 'actor': 'codex:/root', 'actual_outer_exit': 1,
    'actual_native_exit': None, 'event_kind': 'READONLY_PATH_LOCATOR', 'cause': root_failure['cause'],
    'evidence_ref': pins['root_lookup_origin'], 'original_payload': root_failure, 'product_cases_run': 0})
prior = [row for row in doc(pins['source_prior_diagnostics']) if row['tool_chunk'] == '7ae982']
assert len(prior) == 1 and prior[0]['actual_outer_exit'] == prior[0]['native_exit'] == 1
origins.append({'origin_key': 'source-go3-public-rg-no-match-7ae982', 'actor': 'codex:/root/sources_parent_impl',
    'actual_outer_exit': 1, 'actual_native_exit': 1, 'event_kind': 'READONLY_RG_NO_MATCH',
    'cause': prior[0]['cause'], 'evidence_ref': pins['source_prior_diagnostics'], 'original_payload': prior[0], 'product_cases_run': 0})
rows = [row for row in doc(pins['w09_diagnostics'])['current_origins'] if row['actual_tool_exit'] != 0]
assert [row['tool_chunk'] for row in rows] == ['299018', 'aa4e7c']
for row in rows:
    assert row['actual_tool_exit'] == 1 and row['separate_rg_native_exit'] is None
    origins.append({'origin_key': 'source-w09-readpath-' + row['tool_chunk'], 'actor': 'codex:/root/sources_parent_impl',
        'actual_outer_exit': 1, 'actual_native_exit': None, 'event_kind': 'READONLY_PATH_LOCATOR',
        'cause': row['cause'], 'evidence_ref': pins['w09_diagnostics'], 'original_payload': row, 'product_cases_run': 0})
assert len(origins) == len({row['origin_key'] for row in origins}) == 4
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 413, 'after': 417, 'origins': origins,
    'old413_prefix_unchanged': True, 'count_once': True, 'nullable_native_not_rewritten': True, 'counter_reset': False})
pins['scope'] = save('scope_registration.json', {'schema': 'researchos.root-parallel-source-go3-registration.v1',
    'registration_checkpoint': 320, 'state': 'DRAFT_PENDING_NONAUTHOR_REGISTRATION_REVIEW',
    'w09_source_scope_ref': pins['w09_scope'], 'go3_execution_scope_ref': pins['go3_scope'],
    'root14_existing_actual319_authority_ref': pins['root14_scope'], 'root14_relaunch_granted': False,
    'desktop_revision_review_ref': pins['desktop_revision_review'], 'original_failure_prefix_unchanged': True,
    'main_source_writes': 0, 'source_acceptance': False, 'formal_increment': 0})
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[318, 146, 410]', '[319, 147, 413]')
header = once(header, "ROOT = Path.cwd().resolve()", "sys.dont_write_bytecode = True\nassert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode\nROOT = Path.cwd().resolve()")
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 320
w09_scope = json.loads(read(pins['w09_scope']['path']))
go3_scope = json.loads(read(pins['go3_scope']['path']))
assert w09_scope['Go_compile'] == w09_scope['Go_test'] == w09_scope['SQL'] == w09_scope['HTTP'] == 0
assert not (ROOT / w09_scope['worktree_root']).exists()
assert not Path(go3_scope['new_output_root']).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 4 and len(old_failures) == 413
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_READONLY_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:413] == old_failures and len(cp['failure_counters']) == 417
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(w09_causal_exact4_source_scope_ref=pins['w09_scope'],
    w09_causal_exact4_state='EXACT4_SOURCE_APPEND_AND_STATIC_FORMAT_ONLY_NO_COMPILE_TEST_GRANT',
    desktop_http_exact15_revision_independent_review_ref=pins['desktop_revision_review'],
    desktop_http_exact15_revised_author_state='06b1_CURRENT_NODE169_INDEPENDENTLY_REVIEWED_Go3_HISTORICAL_OS_GAP_RETAINED',
    desktop_go3_debug_component_scope_ref=pins['go3_scope'],
    desktop_go3_debug_component_state='ONCE_PROOF_AUTHORIZED_ONLY_AFTER_ACTUAL320_SEAL_AND_ROOT_GRANT_NO_SOURCE_ACCEPTANCE',
    r319_postcut_actual_diagnostics_registered_at=320)
cp['failure_chains']['W05-99/r320-four-readonly-diagnostics'] = {
    'old413_prefix_unchanged': True, 'new_actual_nonzero_origins': 4,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] is None
assert 'W09-99' not in ow['card_path_bindings']
ow['card_path_bindings']['W09-99'] = {'owner': 'codex:/root',
    'amendment': 'Exact4 isolated test-source-only subtask; parent actual acceptance and registry remain Root serial.',
    'subtasks': {'causal_test_source_exact4': {'owner': 'codex:/root/sources_parent_impl',
        'current_source_writer': 'codex:/root/sources_parent_impl', 'scope_ref': pins['w09_scope'],
        'source_paths': w09_scope['source_paths'], 'worktree_root': w09_scope['worktree_root'],
        'state': 'AUTHOR_SOURCE_IMPLEMENTATION_ONLY_AFTER_SEAL', 'source_acceptance': False, 'formal_increment': 0}}}
ow['card_path_bindings']['W13-03']['subtasks']['go3_debug_component_root_once'] = {
    'owner': 'codex:/root', 'current_source_writer': None, 'scope_ref': pins['go3_scope'],
    'state': 'ROOT_FIXED_COMPONENT_ONCE_AFTER_SEAL_GRANT', 'source_acceptance': False, 'formal_increment': 0}
cp['next_command'] = 'After actual320+seal: Source implement exact4 appended W09 tests/static format only in own2cdb worktree; no compiler/SQL/tests yet. Root creates exact sealed-authority grant and runs Go3 debug-component once. Finish actual319 Root14 proof closure/source review before new shared38 integration scope, fresh CLI43/Desktop58. All417 original failures kept, all22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'W09_EXACT4_SOURCE_ONLY_AND_ROOT_GO3_FIXED_DEBUG_COMPONENT_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'failure_origins_before': 413,
    'failure_origins_after': 417, 'new_actual_nonzero_origins': 4, 'counter_reset': False,
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=320, expected_previous_revision=319, updated_at=now, updated_by='codex:/root')
ow.update(revision=148, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r319-running.json'")]
for a, b in [('[318, 319]', '[319, 320]'), ('[146, 147]', '[147, 148]'), ('[410, 413]', '[413, 417]'),
    ('[319, 147, 413]', '[320, 148, 417]'), ("'checkpoint': 319", "'checkpoint': 320"),
    ("'ownership': 147", "'ownership': 148"), ("'failure_origins': 413", "'failure_origins': 417"),
    ("actual['failure_counters'][:410]", "actual['failure_counters'][:413]"),
    ("'old410_prefix_unchanged'", "'old413_prefix_unchanged'"),
    ('new_Root_non_site_independent14_execution_only', 'W09_source_only_and_Root_Go3_execution_scopes_only')]:
    tail = once(tail, a, b)
assert tail.count('root319.tmp') == 2
tail = tail.replace('root319.tmp', 'root320.tmp')
handoff_source = '''handoff_ref = save('handoff-r320-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 320, 'failure_origins': 417, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'W09_source_only_scope_ref': pins['w09_scope'], 'Go3_component_execution_scope_ref': pins['go3_scope'],
    'Root14_existing319_scope_ref': pins['root14_scope'], 'Root14_relaunch_granted': False,
    'next': 'Source exact4 W09 source-only; Root Go3 once after sealed grant; Root14 actual closure then new shared source integration scope. All22/all42 remain required.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 320, 'ownership': 148, 'failure_origins': 417, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff_source)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r319_readonly_review_codex', 'root_registration_r320_readonly_review_codex')
wrapper = once(wrapper, "review['expected_before'] == [318, 146, 410] and review['expected_after'] == [319, 147, 413]",
    "review['expected_before'] == [319, 147, 413] and review['expected_after'] == [320, 148, 417]")
wrapper = once(wrapper, "cp['revision'] == 318 and len(cp['failure_counters']) == 410", "cp['revision'] == 319 and len(cp['failure_counters']) == 413")
wrapper = once(wrapper, "argv = [sys.executable, '-I', str(runner)]", "argv = [sys.executable, '-I', '-S', '-X', 'utf8', str(runner)]")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8', errors='strict')
for a, b in [
    ("PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r318'", "PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r319'"),
    ("assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [318, 146, 410]", "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [319, 147, 413]"),
    ("assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [319, 147, 413]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [320, 148, 417]"),
    ("cp_after['failure_counters'][:410]", "cp_after['failure_counters'][:413]"),
    ("'before': [318, 146, 410], 'after': [319, 147, 413]", "'before': [319, 147, 413], 'after': [320, 148, 417]"),
    ("'old410_failure_prefix_unchanged'", "'old413_failure_prefix_unchanged'"),
    ("'new_Root_non_site_independent14': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'new_W09_source_and_Go3_component': 'NOT_STARTED_AT_REGISTRATION_SEAL'"),
    ("'current': [319, 147, 413]", "'current': [320, 148, 417]")]:
    sealer = once(sealer, a, b)
seal = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [319, 147, 413], 'expected_after': [320, 148, 417],
    'scope_ref': pins['scope'], 'new_origins': origins, 'original413_prefix_unchanged': True,
    'W09_source_only_no_compile_test_SQL_probe': True, 'Go3_spec_and_exact_static_review_bound_once': True,
    'Root14_original319_authorization_retained_not_relaunched_or_current_cases_accepted': True,
    'maximum_active_construction_tasks': 2, 'Main_source_integration': False, 'formal_increment': 0, 'counter_reset': False})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'source_edits_compile_test_SQL_in_preparation': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'ROOT320_SOURCE_AND_COMPONENT_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope'], 'seal': seal}, ensure_ascii=True))
