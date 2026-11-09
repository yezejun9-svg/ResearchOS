import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'desktop-targeted-revision-r317'
ROOT_DRAFT = OUT.parent / 'session-list-closedcopy-root-replay-draft'
G2 = OUT.parent / 'root-g2-execute29-launch-r313'
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


assert sys.flags.isolated and not sys.flags.optimize and len(sys.argv) == 3
review_path = Path(sys.argv[1]).resolve()
assert review_path.is_relative_to(ROOT / 'execution/v2.4/receipts/W05/W05-99')
review_ref = pin(review_path, sys.argv[2])
review = json.loads(read(review_path))
assert review['schema'] == 'researchos.session-list-root-runner-static-review.v1'
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' and review['requested_changes'] == []
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [317, 145, 410]
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
    ('previous_handoff', PREVIOUS / 'handoff-r317-running.json', 'f8cb9cafb933b90545dd2ab59aff0f06812522920a31b5cc51f8382edd86eebc'),
    ('previous_manifest', PREVIOUS / 'manifest.json', '0899adc85b2edaab6dcf91ddd31c9fa83544389d47e34f0bd7815e03b36995f8'),
    ('g2_execution_audit', G2 / 'execution-audit.json', '56832030b32ad62d494007cf55542c93ed742fbbcfa5007ccd2d2e3f90cd072e'),
    ('g2_execution_manifest', G2 / 'manifest.json', '7839b708640f215320a2d62d1e44914ec739575123deed98f1ad0de0504ad26b'),
    ('pending_frontier_lookup_origin', ROOT / 'execution/v2.4/receipts/W05/W05-99/parent_frontier_readonly_codex/295fa9e085d14e9c886c319eeb69cea6/failure_origin.lookup8957bb.json', '800b42d467c83e337e29ed9fcb1a80476ca2a7036fe21e02e183cdf1942919da'),
    ('pending_desktop_revision_Node_origin', ROOT / '.local/worktrees/codex-w1303-desktop-http-r311/execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-8c81bc59bc444fe2b0c5916e282f04a1/failure-origin-0bbcd5.json', '70295b7b8e7cbc69cffa6320f4305ecff609c07add6efeabcb8dcd17aa693f12')]:
    pins[key] = pin(path, sha)
pins['root_scope'] = pin(ROOT_DRAFT / 'root_finite14_scope.v2.json', review['scope_sha256'])
scope = json.loads(read(ROOT_DRAFT / 'root_finite14_scope.v2.json'))
assert scope['expected_registration'] == [318, 146, 410]
assert scope['registration_namespace'] == OUT.relative_to(ROOT).as_posix()
assert scope['source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert scope['state'] == 'DRAFT_V2_NOT_REGISTERED_NOT_AUTHORIZED_NOT_EXECUTED'
for field, review_key, key in [('runner_ref', 'runner_sha256', 'runner'), ('launcher_ref', 'launcher_sha256', 'launcher'),
    ('authorization_gate_ref', 'gate_sha256', 'gate')]:
    item = scope[field]
    assert item['sha256'] == review[review_key]
    pins[key] = pin(ROOT / item['path'], item['sha256'])
    assert pins[key]['bytes'] == item['bytes']
for key in ['owned_process_helper_ref', 'runtime_resources_ref', 'author14_review_ref',
    'author14_review_handoff_ref', 'author14_review_manifest_ref']:
    item = scope[key]
    pins[key] = pin(ROOT / item['path'], item['sha256'])
    assert pins[key]['bytes'] == item['bytes']
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    path = (ROOT / scope[field]).resolve()
    assert path.is_relative_to(ROOT) and not path.exists(), field
assert json.loads(read(ROOT / pins['author14_review_ref']['path']))['status'] == 'READY_FOR_ROOT_INDEPENDENT_FINITE14'
g2 = json.loads(read(G2 / 'execution-audit.json'))
assert g2['actual_outer_exit'] == g2['actual_controller_exit'] == 0
assert len(g2['qualified_finite_leaves']) == len(g2['processes']) == 29
assert g2['MODEL_loopback'] == 4 and g2['snapshot_count'] == 13
assert g2['actual_execution_inputs'] == 41963 and g2['bootstrap_HTTP'] == 'UNKNOWN_NOT_INSTRUMENTED'
assert g2['source_acceptance'] is False and g2['formal_increment'] == 0
pins['scope'] = save('scope_registration.json', {
    'schema': 'researchos.root-session-list-closedcopy-finite14-execution-registration.v1',
    'state': 'AUTHORIZED_AFTER_ACTUAL_CAS318_AND_SEAL_ONLY_NOT_EXECUTED', 'registration_checkpoint': 318,
    'owner': 'codex:/root', 'author': 'codex:/root/command_queue_impl', 'case_count': 14,
    'root_finite14_scope_ref': pins['root_scope'], 'runner_review_ref': pins['runner_review'],
    'author14_review_ref': pins['author14_review_ref'], 'runner_ref': pins['runner'], 'launcher_ref': pins['launcher'],
    'gate_ref': pins['gate'], 'helper_ref': pins['owned_process_helper_ref'], 'runtime_resources_ref': pins['runtime_resources_ref'],
    'source_only_commit': scope['source_commit'], 'source_parent': scope['actual_candidate_parent_expected'],
    'ordered_cases': scope['ordered_cases'], 'limits': scope['limits'],
    'new_output_root': scope['new_output_root'], 'new_export_root': scope['new_export_root'],
    'new_authorization_root': scope['new_authorization_root'], 'run_uuid': scope['run_uuid'],
    'actual_grant_required': 'Exact one-shot reviewed launcher verifies actual sealed registration and creates exclusive authorization raw four canonical copies; inner rechecks entire grant before DLL/Git/Go/native.',
    'input_policy': scope['immutable_vector_extension'], 'sidecar_policy': scope['sidecar_rule'],
    'first_unexpected_stop': True, 'same_input_automatic_retry': False, 'counter_reset': False,
    'Main_product_source_writes': 0, 'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'desktop_writer_and_scope': 'Source targeted Desktop revision from317 remains independent and authorized; do not read/hash its changing worktree into this frozen Root lane.',
    'G2_actual_finite29_sealed_refs': [pins['g2_execution_audit'], pins['g2_execution_manifest']],
    'G2_limits': 'Bounded29 only; bootstrapHTTPUNKNOWN/originalDBstorage&implicitrowidlimits retained; wholeMain9/provider/current formal acceptance not inferred.'})
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[316, 144, 406]', '[317, 145, 410]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 318 and scope['case_count'] == 14
root_scope = json.loads(read(pins['root_scope']['path']))
for field in ['new_output_root', 'new_export_root', 'new_authorization_root']:
    assert not (ROOT / root_scope[field]).exists()
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert prepared['origins'] == [] and len(old_failures) == 410
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(session_list_closedcopy_root_finite14_scope_ref=pins['root_scope'],
    session_list_closedcopy_root_finite14_execution_scope_ref=pins['scope'],
    session_list_closedcopy_root_runner_review_ref=pins['runner_review'],
    session_list_closedcopy_root_author14_review_ref=pins['author14_review_ref'],
    session_list_closedcopy_root_finite14_state='ROOT_INDEPENDENT14_ACTUAL_CAS_BOUND_ONCE_LAUNCH_AFTER_SEAL',
    session_list_closedcopy_exact1_state='AUTHOR14_NONAUTHOR_SOURCE_EVIDENCE_REVIEW_READY_ROOT_INDEPENDENT14_NOT_STARTED',
    provider_g2_root_execution_audit_ref=pins['g2_execution_audit'],
    provider_g2_root_execution_manifest_ref=pins['g2_execution_manifest'],
    provider_g2_root_execution_state='ACTUAL_NONAUTHOR29_SEALED_4LOOPBACK_MODEL_13SNAPSHOTS_NOT_MAIN_FORMAL_ACCEPTANCE',
    r318_preserved_pending_failure_origin_refs=[pins['pending_frontier_lookup_origin'], pins['pending_desktop_revision_Node_origin']],
    r318_pending_failure_cut='Two actual origins preserved for immediate next serialized cut319; registered410 prefix unchanged, total observed at least412. Unrelated318 fixed execution snapshot is not a counter reset.')
assert cp['work_in_progress']['session_list_identity_source_ready'] is False
assert ow['card_path_bindings']['W13-03']['subtasks']['desktop_http_exact15']['current_source_writer'] == 'codex:/root/sources_parent_impl'
assert ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1']['current_source_writer'] is None
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'] = {
    'owner': 'codex:/root', 'current_source_writer': None, 'scope_ref': pins['scope'],
    'state': 'ROOT_NONAUTHOR_FIXED14_RUNTIME_ONCE_AFTER_SEAL', 'Main_product_source_writes': 0,
    'source_acceptance': False, 'formal_increment': 0}
cp['next_command'] = 'Root once-only actual sealed318 grant/independent fixed14 new source export+fresh compile+immutable full vectors+closed-copy/sidecars/wire proofs. Immediately next serialized319 cut preserves actual pending lookup8957bb and Desktop Node0bbcd5 as two separate original causes; 410 registered plus2 pending, no reset. Source317 targeted Desktop revision continues independently. G2 root29 actually sealed; source/wholeprovider/Main9/current formal remains unaccepted. After accepted list14 compose shared38 unique delta, then CLI43 fresh held2, Desktop58 after separate non-author readiness. All22/all42 still required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'ROOT_CLOSED_COPY_NONAUTHOR_FINITE14_ONCE_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'audit_ref': pins['audit'],
    'failure_origins_before': 410, 'failure_origins_after': 410, 'new_actual_nonzero_origins': 0,
    'counter_reset': False, 'G2_actual_non_author29_sealed_not_main': True, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=318, expected_previous_revision=317, updated_at=now, updated_by='codex:/root')
ow.update(revision=146, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r317-running.json'")]
for a, b in [('[316, 317]', '[317, 318]'), ('[144, 145]', '[145, 146]'), ('[406, 410]', '[410, 410]'),
    ('[317, 145, 410]', '[318, 146, 410]'), ('[:406]', '[:410]'),
    ("'checkpoint': 317", "'checkpoint': 318"), ("'ownership': 145", "'ownership': 146"),
    ('old406_prefix_unchanged', 'old410_prefix_unchanged'), ('new_targeted_Desktop_revision_only', 'new_Root_independent14_execution_only')]:
    tail = once(tail, a, b)
assert tail.count('root317.tmp') == 2
tail = tail.replace('root317.tmp', 'root318.tmp')
handoff = '''handoff_ref = save('handoff-r318-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'canonical_refs': [ref(path) for path in CANON],
    'revision': 318, 'failure_origins': 410, 'counter_reset': False, 'previous_handoff_ref': pins['previous_handoff'],
    'registered_failure_prefix': 410, 'preserved_pending_origin_refs': [pins['pending_frontier_lookup_origin'], pins['pending_desktop_revision_Node_origin']],
    'known_total_observed_failures_lower_bound': 412,
    'root_finite14_scope_ref': pins['root_scope'], 'root_finite14_execution_scope_ref': pins['scope'],
    'root_finite14_runner_review_ref': pins['runner_review'], 'G2_sealed29_ref': pins['g2_execution_audit'],
    'next': 'Root fixed14 once-only launch after registration seal; Source Desktop317 narrow revision continues. G2 actual29 sealed. Shared38/CLI43/Desktop58 source-only composition after respective acceptance gates.',
    'all22_and42_effective_acceptances_required': True, 'source_acceptance': False,
    'Main_integration_authorized': False, 'formal_increment': 0})
print(json.dumps({'checkpoint': 318, 'ownership': 146, 'failure_origins': 410, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
register = script('register.py', header + mutation + tail + handoff)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r317_readonly_review_codex', 'root_registration_r318_readonly_review_codex')
wrapper = once(wrapper, 'review[\'expected_before\'] == [316, 144, 406] and review[\'expected_after\'] == [317, 145, 410]',
    'review[\'expected_before\'] == [317, 145, 410] and review[\'expected_after\'] == [318, 146, 410]')
wrapper = once(wrapper, "cp['revision'] == 316 and len(cp['failure_counters']) == 406", "cp['revision'] == 317 and len(cp['failure_counters']) == 410")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8', errors='strict')
for a, b in [
    ("PREVIOUS = OUT.parent / 'session-list-closedcopy-harness-v4-r316'", "PREVIOUS = OUT.parent / 'desktop-targeted-revision-r317'"),
    ("assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [316, 144, 406]", "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [317, 145, 410]"),
    ("assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [317, 145, 410]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [318, 146, 410]"),
    ('[:406]', '[:410]'), ("'before': [316, 144, 406], 'after': [317, 145, 410]", "'before': [317, 145, 410], 'after': [318, 146, 410]"),
    ('old406_failure_prefix_unchanged', 'old410_failure_prefix_unchanged'),
    ("'source_review_ref': prepared['pins']['source_review']", "'runner_review_ref': prepared['pins']['runner_review']"),
    ("'new_targeted_Desktop_revision': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'new_Root_independent14': 'NOT_STARTED_AT_REGISTRATION_SEAL'"),
    ("'current': [317, 145, 410]", "'current': [318, 146, 410]")]:
    sealer = once(sealer, a, b)
seal = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [317, 145, 410], 'expected_after': [318, 146, 410],
    'scope_ref': pins['scope'], 'runner_review_ref': pins['runner_review'], 'new_origins': [],
    'registered_failure_prefix': 410, 'pending_origin_refs': [pins['pending_frontier_lookup_origin'], pins['pending_desktop_revision_Node_origin']],
    'known_total_observed_failures_lower_bound': 412, 'pending_cut_319_required': True,
    'old410_failure_prefix_unchanged': True, 'four_canonical_CAS_and_seal_then_unique_actual_grant_required': True,
    'Root14_NOT_RUN': True, 'SourceDesktop317_revision_preserved': True, 'G2_sealed29_not_Source_Main_acceptance': True,
    'maximum_active_construction_tasks': 2, 'Main_source_integration': False, 'formal_increment': 0, 'counter_reset': False})
prepared = save('prepared_refs.json', {'canonical_before': [pin(path) for path in CANON], 'head': head,
    'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': [],
    'verified_refs': [pin(path) for path in READS if path not in CANON], 'actual_source_exports_compile_cases': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'state': 'ROOT14_EXECUTION_DRAFT_NOT_EXECUTED', 'register': register, 'wrapper': wrapped,
    'prepared': prepared, 'audit': pins['audit'], 'scope': pins['scope'], 'seal': seal}, ensure_ascii=True))
