import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r318'
DRAFT = OUT.parent / 'session-list-closedcopy-root-replay-draft'
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
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected, str(path)
    return item


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


assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize and len(sys.argv) == 3
review_path = Path(sys.argv[1]).resolve()
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99')
review_ref = pin(review_path, sys.argv[2])
review = json.loads(read(review_path))
assert review['schema'] == 'researchos.session-list-root-runner-static-review.v1'
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' and review['requested_changes'] == []
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [318, 146, 410]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
git = lock['git']['path']
for key in ['python', 'git']:
    assert hashlib.sha256(Path(lock[key]['path']).read_bytes()).hexdigest() == lock[key]['sha256']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
pins = {'runner_review': review_ref}
for key, path, sha in [
    ('previous_handoff', PREVIOUS / 'handoff-r318-running.json', '7e7cb94b5cbecd1f4c5f378168bf92037a89358100fd9f5f2c249845c1313666'),
    ('previous_manifest', PREVIOUS / 'manifest.json', 'af36b0487b5fa90e6a895e238c388cba9f0e8adc21d70e358eb51d18cee9817e'),
    ('g2_independent_review', ROOT / 'execution/v2.4/receipts/W05/W05-99/provider_g2_bounded29_evidence_independent_review_codex/55a125ea5d084f7bb9a6e9eb4532c2c4/review.final.json', '7d866b4dc6e555bf3a721aeff36aac49ecbff8ff21dc23302798fce86175fef7'),
    ('g2_independent_manifest', ROOT / 'execution/v2.4/receipts/W05/W05-99/provider_g2_bounded29_evidence_independent_review_codex/55a125ea5d084f7bb9a6e9eb4532c2c4/manifest.final.json', '69c9c8ebd00ee41ebd8fbcda78c5258cbe0c2051909e568a862529e4312685ea'),
    ('g2_independent_handoff', ROOT / 'execution/v2.4/receipts/W05/W05-99/provider_g2_bounded29_evidence_independent_review_codex/55a125ea5d084f7bb9a6e9eb4532c2c4/handoff.final.json', '329056f78f16a326d3e8bc0d310b2bd39aeb3db7f25928f0999b8e0a8c0b964a'),
    ('source_desktop_current_handoff', ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-a7f44ed9b4ae4225bd072adcf708e24b/final-audit-2d44db33d4874f8bb806b44137292e08/handoff.json', '53d6d8796982540bf4f6b4b42f9b40047e7633ccaed560bdbd3ef438015e469c')]:
    pins[key] = pin(path, sha)
pins['root_scope'] = pin(DRAFT / 'root_finite14_scope.v3.json', review['scope_sha256'])
scope = json.loads(read(DRAFT / 'root_finite14_scope.v3.json'))
assert scope['expected_registration'] == [319, 147, 413] and scope['python_flags'] == ['-I', '-S', '-X', 'utf8']
assert scope['registration_namespace'] == OUT.relative_to(ROOT).as_posix()
assert scope['source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert scope['state'] == 'DRAFT_V3_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED'
for field, review_key, key in [('runner_ref', 'runner_sha256', 'runner'), ('launcher_ref', 'launcher_sha256', 'launcher'),
    ('authorization_gate_ref', 'gate_sha256', 'gate')]:
    item = scope[field]
    assert item['sha256'] == review[review_key]
    pins[key] = pin(ROOT / item['path'], item['sha256'])
    assert pins[key]['bytes'] == item['bytes']
for key in ['owned_process_helper_ref', 'runtime_resources_ref', 'author14_review_ref', 'author14_handoff_ref', 'author14_manifest_ref',
    'v2_actual_prelaunch_failure_ref', 'v2_original_launcher_failure_ref']:
    item = scope[key]
    pins[key] = pin(ROOT / item['path'], item['sha256'])
    assert pins[key]['bytes'] == item['bytes']
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    path = (ROOT / scope[field]).resolve()
    assert path.is_relative_to(ROOT) and not path.exists(), field
assert json.loads(read(ROOT / pins['author14_review_ref']['path']))['status'] == 'READY_FOR_ROOT_INDEPENDENT_FINITE14'
origin_specs = [
    ('frontier-readonly-package-location-8957bb', 'codex:/root/w05_merge_review', 'READONLY_POWERSHELL_FILE_LOOKUP',
        ROOT / 'execution/v2.4/receipts/W05/W05-99/parent_frontier_readonly_codex/295fa9e085d14e9c886c319eeb69cea6/failure_origin.lookup8957bb.json', '800b42d467c83e337e29ed9fcb1a80476ca2a7036fe21e02e183cdf1942919da'),
    ('r317-source-desktop-revision-evidence-directory-0bbcd5', 'codex:/root/sources_parent_impl', 'OWNED_NODE_FINITE_CONTROL',
        ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-8c81bc59bc444fe2b0c5916e282f04a1/failure-origin-0bbcd5.json', '70295b7b8e7cbc69cffa6320f4305ecff609c07add6efeabcb8dcd17aa693f12'),
    ('root-session-list-finite14-prelaunch-site7783ca', 'codex:/root', 'PINNED_PYTHON_LAUNCHER_PRELAUNCH',
        ROOT / scope['v2_actual_prelaunch_failure_ref']['path'], scope['v2_actual_prelaunch_failure_ref']['sha256'])]
origins = []
for key, actor, kind, path, sha in origin_specs:
    evidence = pin(path, sha)
    raw = json.loads(read(path))
    outer = raw['actual_outer_exit']
    native = raw.get('actual_Node_exit') if kind == 'OWNED_NODE_FINITE_CONTROL' else None
    assert (outer, native) == ((0, 1) if kind == 'OWNED_NODE_FINITE_CONTROL' else (1, None))
    origins.append({'origin_key': key, 'actor': actor, 'event_kind': 'ACTUAL_NONZERO_EXECUTION',
        'actual_outer_exit': outer, 'actual_native_exit': native, 'native_kind': kind,
        'product_cases_run': 1 if native == 1 else 0, 'cause': raw['cause'], 'evidence_ref': evidence,
        'original_payload': raw, 'actual_HTTP_observed': raw.get('HTTP'), 'new_Product_PASS': 0,
        'count_once': True, 'counter_reset': False})
assert len(origins) == len({row['origin_key'] for row in origins}) == 3
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 410, 'after': 413, 'origins': origins,
    'old410_prefix_unchanged': True, 'new_actual_nonzero_origins': 3, 'count_once': True,
    'nullable_native_and_zero_outer_not_rewritten': True, 'counter_reset': False})
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.root-session-list-closedcopy-finite14-execution-registration.v1',
    'state': 'AUTHORIZED_AFTER_ACTUAL_CAS319_AND_SEAL_ONLY_NOT_EXECUTED', 'registration_checkpoint': 319,
    'owner': 'codex:/root', 'author': 'codex:/root/command_queue_impl', 'case_count': 14,
    'root_finite14_scope_ref': pins['root_scope'], 'runner_review_ref': pins['runner_review'],
    'author14_review_ref': pins['author14_review_ref'], 'runner_ref': pins['runner'], 'launcher_ref': pins['launcher'],
    'gate_ref': pins['gate'], 'helper_ref': pins['owned_process_helper_ref'], 'runtime_resources_ref': pins['runtime_resources_ref'],
    'source_only_commit': scope['source_commit'], 'source_parent': scope['actual_candidate_parent_expected'],
    'ordered_cases': scope['ordered_cases'], 'limits': scope['limits'], 'python_flags': scope['python_flags'],
    'new_output_root': scope['new_output_root'], 'new_export_root': scope['new_export_root'],
    'new_authorization_root': scope['new_authorization_root'], 'run_uuid': scope['run_uuid'],
    'actual_grant_required': 'Exact reviewed v3 launcher verifies actual sealed319 registration and creates exclusive grant/raw four canonical copies; inner rechecks before native. Python site startup disabled, runtime guards unchanged.',
    'input_policy': scope['immutable_vector_extension'], 'sidecar_policy': scope['sidecar_rule'],
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'counter_reset': False,
    'Main_product_source_writes': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'old318_prelaunch_failure_preserved': True, 'source_Desktop_current': 'Source06b1 committed and author-current159+7+3 reported; Go3 old OS proof limit preserved. No Go3 extra execution grant here.',
    'G2_independent_bounded29_ref': pins['g2_independent_review'],
    'G2_limits': 'Bounded29 only; bootstrapHTTPUNKNOWN/originalDBstorage&implicitrowidlimits retained; no wholeMain9/provider/current formal acceptance.'})
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[317, 145, 410]', '[318, 146, 410]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 319 and scope['case_count'] == 14
root_scope = json.loads(read(pins['root_scope']['path']))
assert root_scope['python_flags'] == ['-I', '-S', '-X', 'utf8']
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    assert not (ROOT / root_scope[field]).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 3 and len(old_failures) == 410
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys
    assert item['actual_outer_exit'] == 1 or item['actual_native_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0, 'count_once': True,
        'counter_reset': False, 'status': 'ACTUAL_NONZERO_TOOL_OR_NODE_ORIGIN_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:410] == old_failures and len(cp['failure_counters']) == 413
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_root_finite14_scope_ref=pins['root_scope'],
    session_list_closedcopy_root_finite14_execution_scope_ref=pins['scope'],
    session_list_closedcopy_root_runner_review_ref=pins['runner_review'],
    session_list_closedcopy_root_author14_review_ref=pins['author14_review_ref'],
    session_list_closedcopy_root_finite14_state='ROOT_NEW_NON_SITE_INDEPENDENT14_ACTUAL_CAS_BOUND_ONCE_LAUNCH_AFTER_SEAL',
    session_list_closedcopy_root_v2_prelaunch_failure_registered=True,
    r318_preserved_pending_failure_origins_registered_at=319,
    r318_pending_failure_cut='All three pending actual origins registered319; original410 prefix and Root318 failed auth retained.',
    provider_g2_bounded29_independent_review_ref=pins['g2_independent_review'],
    provider_g2_root_execution_state='ACTUAL_NONAUTHOR29_SEALED_AND_INDEPENDENT_EVIDENCE_CLOSED_BOUNDED_ONLY',
    desktop_http_exact15_revised_author_handoff_ref=pins['source_desktop_current_handoff'],
    desktop_http_exact15_revised_author_state='SOURCE06b1_FROZEN_NODE_CURRENT159_PLUS7_PLUS3_REPORTED_Go3_HISTORICAL_OS_LIMIT_RETAINED_NONAUTHOR_REVIEW_PENDING')
cp['failure_chains']['W05-99/r319-three-pending-actual-origins'] = {
    'original410_prefix_unchanged': True, 'new_actual_nonzero_origins': 3,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
desktop = ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']
assert desktop['current_source_writer'] == 'codex:/root/sources_parent_impl'
desktop.update(current_source_writer=None, last_source_writer='codex:/root/sources_parent_impl',
    state='SOURCE06b1_WRITER_STOPPED_CURRENT169_UNITS_REPORTED_Go3_LIMIT_RETAINED_REVIEW_PENDING',
    source_only_revision_commit='06b1fbcb5934cbc70e5d65a46481e60c05c6594b', final_handoff_ref=pins['source_desktop_current_handoff'])
assert ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']['current_source_writer'] is None
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'].update(
    scope_ref=pins['scope'], state='ROOT_V3_NON_SITE_FIXED14_ONCE_AFTER_SEAL', current_source_writer=None,
    source_acceptance=False, formal_increment=0)
cp['next_command'] = 'Root new-v3 non-site fixed14 once after actual319+seal, fresh exclusive grant/export/compile/immutable full vectors/closedcopy proofs. Original410+lookup8957bb+SourceNode0bbcd5+Rootprelaunch7783ca=413 retained. Source06b1 current159+7+3 reported; Go3 exact OS proof limit remains, next minimal extra receipt controller requires separate review/grant. G2 actual29 independent evidence closed bounded only. After accepted14 compose shared38 then CLI43/Desktop58 gates. All22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'ROOT_NON_SITE_FIXED14_NEW_INPUT_SCOPE_AND_THREE_ACTUAL_ORIGINS_REGISTERED',
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 410, 'failure_origins_after': 413, 'new_actual_nonzero_origins': 3,
    'counter_reset': False, 'G2_independent_bounded29_closed': True, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=319, expected_previous_revision=318, updated_at=now, updated_by='codex:/root')
ow.update(revision=147, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r318-running.json'")]
for a, b in [('[317, 318]', '[318, 319]'), ('[145, 146]', '[146, 147]'), ('[410, 410]', '[410, 413]'),
    ('[318, 146, 410]', '[319, 147, 413]'), ("'checkpoint': 318", "'checkpoint': 319"),
    ("'ownership': 146", "'ownership': 147"), ("'failure_origins': 410", "'failure_origins': 413"),
    ('new_Root_independent14_execution_only', 'new_Root_non_site_independent14_execution_only')]:
    tail = once(tail, a, b)
assert tail.count('root318.tmp') == 2
tail = tail.replace('root318.tmp', 'root319.tmp')
handoff_source = '''handoff_ref = save('handoff-r319-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 319, 'failure_origins': 413, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'root_finite14_scope_ref': pins['root_scope'], 'root_finite14_execution_scope_ref': pins['scope'],
    'root_finite14_runner_review_ref': pins['runner_review'], 'G2_independent_bounded29_ref': pins['g2_independent_review'],
    'desktop_source06b1_handoff_ref': pins['source_desktop_current_handoff'],
    'next': 'Root new-v3 non-site14 once after seal; Desktop non-author review and Go3 proof-only proposal; W09 readiness18 complete. All shared source integrations and current formal acceptance still HOLD.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 319, 'ownership': 147, 'failure_origins': 413, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff_source)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r318_readonly_review_codex', 'root_registration_r319_readonly_review_codex')
wrapper = once(wrapper, 'review[\'expected_before\'] == [317, 145, 410] and review[\'expected_after\'] == [318, 146, 410]',
    'review[\'expected_before\'] == [318, 146, 410] and review[\'expected_after\'] == [319, 147, 413]')
wrapper = once(wrapper, "cp['revision'] == 317 and len(cp['failure_counters']) == 410", "cp['revision'] == 318 and len(cp['failure_counters']) == 410")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8', errors='strict')
for a, b in [
    ("PREVIOUS = OUT.parent / 'desktop-targeted-revision-r317'", "PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r318'"),
    ("assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [317, 145, 410]", "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [318, 146, 410]"),
    ("assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [318, 146, 410]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [319, 147, 413]"),
    ("'before': [317, 145, 410], 'after': [318, 146, 410]", "'before': [318, 146, 410], 'after': [319, 147, 413]"),
    ("'new_Root_independent14': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'new_Root_non_site_independent14': 'NOT_STARTED_AT_REGISTRATION_SEAL'"),
    ("'current': [318, 146, 410]", "'current': [319, 147, 413]")]:
    sealer = once(sealer, a, b)
seal = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [318, 146, 410], 'expected_after': [319, 147, 413],
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'new_origins': origins,
    'old410_failure_prefix_unchanged': True, 'three_actual_pending_original_causes_once': True,
    'new_non_site_bootstrap_runtime_guards_unchanged': True, 'Root14_NOT_RUN': True,
    'source06b1_frozen_Node169_reported_Go3_OS_limit_no_extra_test_grant': True,
    'G2_independent_bounded29_not_whole_source_Main_acceptance': True,
    'maximum_active_construction_tasks': 2, 'Main_source_integration': False, 'formal_increment': 0, 'counter_reset': False})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'ROOT_NON_SITE14_EXECUTION_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope'], 'seal': seal}, ensure_ascii=True))
