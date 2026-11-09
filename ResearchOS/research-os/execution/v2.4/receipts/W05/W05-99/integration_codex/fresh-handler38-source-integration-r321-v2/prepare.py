import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
from pathlib import Path
import subprocess

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'parallel-source-and-go3-r320'
CANON = [ROOT / 'execution/v2.4' / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}

def read(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    assert p.is_relative_to(ROOT)
    raw = p.read_bytes()
    assert p not in READS or READS[p] == raw
    READS[p] = raw
    return raw

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    raw = read(p)
    item = {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item

def doc(item):
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
    return json.loads(read(item['path']))

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)

def script(name, text):
    ast.parse(text, filename=name)
    with (OUT / name).open('xb') as stream:
        stream.write(text.encode('utf-8'))
    return ref(OUT / name)

def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

assert len(sys.argv) == 2
pin_bundle = json.loads(read(sys.argv[1]))
assert pin_bundle['expected_before'] == [320, 148, 417]
assert pin_bundle['expected_after'] == [321, 149, 422]
pins = pin_bundle['pins']
for item in pins.values():
    doc(item) if item['path'].endswith('.json') else ref(item['path'], item['sha256'])
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [320, 148, 417]
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
for name in ['python', 'git']:
    assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
assert doc(pins['root14_review'])['decision'] == 'READY_FOR_ROOT_REGISTERING_BOUNDED14_LIST_FIX_SOURCE_WITH_DECLARED_OPEN_GATES'
assert doc(pins['go3_review'])['decision'] == pin_bundle['go3_review_decision']
assert doc(pins['integration_controller_review'])['decision'] == pin_bundle['integration_controller_review_decision']
assert doc(pins['w09_handoff'])['source_commit'] == 'cd0d818baa703fbc59a6f7c8187d467d41570094'
assert doc(pins['w09_review'])['decision'] == 'SOURCE_IMPLEMENTED_STATIC_REVIEWED_WITH_EXPLICIT_UNRUN_GATES'
origins = []
for item in pin_bundle['origin_refs']:
    original = doc(item)
    assert original['actual_outer_exit'] == 1
    chunk = original.get('tool_trace') or original.get('tool_chunk') or original['unique_original_invocation'].split('/')[-1]
    key = original.get('origin_key') or ('w05-integration-static-map-audit-828f8b' if chunk == '828f8b' else 'w05-root14-readonly-' + chunk)
    native = original.get('actual_python_auditor_exit') if chunk == '61f965' else original.get('actual_python_exit') if chunk == '828f8b' else None
    assert 'actor' in original or chunk == '828f8b'
    origins.append({'origin_key': key, 'actor': original.get('actor', 'codex:/root/w05_merge_review'), 'actual_outer_exit': 1,
        'actual_native_exit': native, 'actual_native_product_exit': None,
        'event_kind': original.get('event_kind', 'READONLY_AUDITOR_OR_PATH_LOCATOR'),
        'cause': original['cause'], 'evidence_ref': ref(item['path'], item['sha256']),
        'original_payload': original, 'product_cases_run': 0})
assert len(origins) == len({row['origin_key'] for row in origins}) == 5
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 417, 'after': 422, 'origins': origins,
    'old417_prefix_unchanged': True, 'count_once': True, 'counter_reset': False})
scope = pin_bundle['root_scope']
assert scope['registration_checkpoint'] == 321 and scope['expected_registration'] == [321, 149, 422]
assert scope['owner'] == 'codex:/root' and scope['max_source_FF_operations'] == 1
assert scope['target_source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert scope['base_commit'] == head and scope['unique_source_paths'] == 38
assert scope['Go_compile'] == scope['Go_test'] == scope['SQL'] == scope['HTTP'] == scope['SDK_MODEL_external_paid'] == 0
assert (OUT / 'scope_registration.json').is_file()
pins['scope'] = ref(OUT / 'scope_registration.json')
assert doc(pins['scope']) == scope
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[319, 147, 413]', '[320, 148, 417]')
mutation = '''pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
assert scope['registration_checkpoint'] == 321 and scope['expected_registration'] == [321, 149, 422]
assert scope['owner'] == 'codex:/root' and scope['max_source_FF_operations'] == 1
assert scope['target_source_commit'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {row.get('origin_key') for row in old_failures}
assert len(prepared['origins']) == 5 and len(old_failures) == 417
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0,
        'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_READONLY_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:417] == old_failures and len(cp['failure_counters']) == 422
assert len(prepared['pending_origin_refs']) == 2
for item in prepared['pending_origin_refs']:
    ref(item['path'], item['sha256'])
cp['work_in_progress']['r321_cut_pending_actual_tool_origin_refs'] = prepared['pending_origin_refs']
cp['work_in_progress']['observed_actual_tool_origin_lower_bound_after_r321_cut'] = 424
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(
    session_list_identity_source_ready=True,
    session_list_identity_state='BOUNDED14_LIST_FIX_INDEPENDENTLY_VERIFIED_DECLARED_OPEN_PRODUCT_GATES_RETAINED',
    session_list_closedcopy_exact1_state='AUTHOR14_AND_ROOT14_CLOSED_WITH_NONAUTHOR_BOUNDED_REVIEW',
    session_list_closedcopy_root_finite14_state='ROOT14_CLOSED_14_NATIVE_PASS_0SKIP_78HTTP_NO_INPUT_DRIFT_NO_RERUN',
    session_list_closedcopy_root_finite14_evidence_review_ref=pins['root14_review'],
    session_list_closedcopy_root_finite14_sealed_audit_ref=pins['root14_audit'],
    handler38_source_integration_scope_ref=pins['scope'],
    handler38_source_integration_controller_review_ref=pins['integration_controller_review'],
    handler38_source_integration_state='REGISTERED_EXACT38_SOURCE_ONLY_FF_AFTER_SEAL_AND_ROOT_ONCE_GRANT',
    handler38_source_integration_target=scope['target_source_commit'],
    desktop_go3_debug_component_state='CLOSED_NEW_DEBUG_COMPONENT_INDEPENDENTLY_REVIEWED_OLD_NORMAL_MODE_GAP_RETAINED',
    desktop_go3_debug_component_closed_audit_ref=pins['go3_audit'],
    desktop_go3_debug_component_evidence_review_ref=pins['go3_review'],
    w09_causal_exact4_state='SOURCE4_INDEPENDENT_STATIC_REVIEWED_WRITER_STOPPED_NO_COMPILE_OR_TEST_GRANT',
    w09_causal_exact4_source_commit='cd0d818baa703fbc59a6f7c8187d467d41570094',
    w09_causal_exact4_author_handoff_ref=pins['w09_handoff'],
    w09_causal_exact4_static_source_review_ref=pins['w09_review'])
cp['failure_chains']['W05-99/r321-five-readonly-diagnostics'] = {
    'old417_prefix_unchanged': True, 'new_actual_nonzero_origins': 5,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
w09_source = ow['card_path_bindings']['W09-99']['subtasks']['causal_test_source_exact4']
assert w09_source['current_source_writer'] == 'codex:/root/sources_parent_impl'
w09_source.update(current_source_writer=None, state='SOURCE4_INDEPENDENT_STATIC_REVIEWED_NOT_COMPILED',
    source_only_commit='cd0d818baa703fbc59a6f7c8187d467d41570094', author_handoff_ref=pins['w09_handoff'],
    static_source_review_ref=pins['w09_review'])
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_root_finite14'].update(
    state='CLOSED_ROOT14_NONAUTHOR_BOUNDED_EVIDENCE_REVIEW_READY', evidence_review_ref=pins['root14_review'])
ow['card_path_bindings']['W05-99']['subtasks']['session_list_closedcopy_exact1'].update(
    state='BOUNDED14_SOURCE_FIX_READY_WITH_OPEN_PRODUCT_GATES', source_ready=True,
    root_evidence_review_ref=pins['root14_review'])
ow['card_path_bindings']['W05-99']['subtasks']['handler38_main_source_integration'] = {
    'owner': 'codex:/root', 'current_source_writer': 'codex:/root',
    'scope_ref': pins['scope'], 'controller_review_ref': pins['integration_controller_review'],
    'state': 'ROOT_SOURCE_ONLY_FF38_AFTER_SEAL_AND_EXACT_GRANT',
    'target_source_commit': scope['target_source_commit'], 'source_paths_ref': scope['source_paths_ref'],
    'source_acceptance': False, 'formal_increment': 0}
ow['card_path_bindings']['W13-03']['subtasks']['go3_debug_component_root_once'].update(
    state='CLOSED_NEW_DEBUG_COMPONENT_NONAUTHOR_EVIDENCE_REVIEW_READY', evidence_review_ref=pins['go3_review'])
cp['next_command'] = 'After actual321+seal, Root issue exact once source-only38 FF grant and execute reviewed controller to a5d6. Preserve old11D and empty index. Forward-only metadata follow-up then fresh combined43 CLI and58 Desktop compilation/replays under distinct scopes. W09 source4 frozen NOT_RUN, controller preparation only. All422 registered origins plus2pending aftercut and all22/all42 required.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'BOUNDED_ROOT14_GO3_CLOSED_AND_FRESH_EXACT38_SOURCE_ONLY_SCOPE_REGISTERED',
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'],
    'failure_origins_before': 417, 'failure_origins_after': 422,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=321, expected_previous_revision=320, updated_at=now, updated_by='codex:/root')
ow.update(revision=149, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r320-running.json'")]
for previous, updated in [('[319, 320]', '[320, 321]'), ('[147, 148]', '[148, 149]'),
    ('[413, 417]', '[417, 422]'), ('[320, 148, 417]', '[321, 149, 422]'),
    ("'checkpoint': 320", "'checkpoint': 321"), ("'ownership': 148", "'ownership': 149"),
    ("'failure_origins': 417", "'failure_origins': 422"),
    ("actual['failure_counters'][:413]", "actual['failure_counters'][:417]"),
    ("'old413_prefix_unchanged'", "'old417_prefix_unchanged'"),
    ("'Main_source_integration_HOLD': True", "'Main_exact38_FF_scope_registered_only': True"),
    ("'Main_integration_authorized': False", "'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT'"),
    ('W09_source_only_and_Root_Go3_execution_scopes_only', 'BOUNDED14_GO3_CLOSED_W09_STOPPED_FRESH_SOURCE_ONLY38_SCOPE')]:
    tail = once(tail, previous, updated)
assert tail.count('root320.tmp') == 2
tail = tail.replace('root320.tmp', 'root321.tmp')
ending = '''handoff_ref = save('handoff-r321-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'project_id': cp['project_id'], 'Main_head': head,
    'canonical_refs': [ref(path) for path in CANON], 'revision': 321, 'failure_origins': 422,
    'previous_handoff_ref': pins['previous_handoff'], 'counter_reset': False,
    'source_only38_scope_ref': pins['scope'], 'root14_review_ref': pins['root14_review'],
    'go3_review_ref': pins['go3_review'], 'w09_author_handoff_ref': pins['w09_handoff'],
    'next': cp['next_command'], 'source_acceptance': False,
    'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT',
    'all22_and42_effective_acceptances_required': True, 'formal_increment': 0})
print(json.dumps({'checkpoint': 321, 'ownership': 149, 'failure_origins': 422, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
runner = script('register.py', header + mutation + tail + ending)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r320_readonly_review_codex', 'root_registration_r321_readonly_review_codex')
wrapper = once(wrapper, "review['expected_before'] == [319, 147, 413] and review['expected_after'] == [320, 148, 417]",
    "review['expected_before'] == [320, 148, 417] and review['expected_after'] == [321, 149, 422]")
wrapper = once(wrapper, "cp['revision'] == 319 and len(cp['failure_counters']) == 413", "cp['revision'] == 320 and len(cp['failure_counters']) == 417")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.v2.py').decode('utf-8', errors='strict')
for previous, updated in [
    ("PREVIOUS = OUT.parent / 'session-list-closedcopy-root-r319'", "PREVIOUS = OUT.parent / 'parallel-source-and-go3-r320'"),
    ('[319, 147, 413]', '[320, 148, 417]'), ('[320, 148, 417]', '[321, 149, 422]')]:
    if previous == '[320, 148, 417]':
        # The previous substitution is confined to the cp_before expression to avoid cascade.
        continue
    if previous.startswith('['):
        sealer = once(sealer, "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == " + previous,
            "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == " + updated)
    else:
        sealer = once(sealer, previous, updated)
for previous, updated in [
    ("assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [320, 148, 417]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [321, 149, 422]"),
    ("cp_after['failure_counters'][:413]", "cp_after['failure_counters'][:417]"),
    ("'before': [319, 147, 413], 'after': [320, 148, 417]", "'before': [320, 148, 417], 'after': [321, 149, 422]"),
    ("'old413_failure_prefix_unchanged'", "'old417_failure_prefix_unchanged'"),
    ("'go3_runner_review_ref': prepared['pins']['go3_review']", "'Go3_actual_evidence_review_ref': prepared['pins']['go3_review']"),
    ("'w09_source_review_ref': prepared['pins']['w09_review']", "'fresh38_controller_review_ref': prepared['pins']['integration_controller_review']"),
    ("'new_W09_source_and_Go3_component': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'source_only38_actual_merge': 'NOT_STARTED_AT_REGISTRATION_SEAL'"),
    ("'Main_integration_authorized': False", "'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT'"),
    ("'current': [320, 148, 417]", "'current': [321, 149, 422]")]:
    sealer = once(sealer, previous, updated)
sealed = script('seal.py', sealer)
pins['audit'] = save('audit.json', {
    'schema': 'researchos.root-registration-draft-audit.v1', 'actor': 'codex:/root',
    'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW', 'expected_before': [320, 148, 417], 'expected_after': [321, 149, 422],
    'scope_ref': pins['scope'], 'new_origins': origins, 'original417_prefix_unchanged': True,
    'bounded_Root14_evidence_closed': True, 'new_Go3_debug_component_evidence_closed': True,
    'W09_source4_author_frozen_NOT_RUN': True, 'maximum_active_construction_tasks': 2,
    'Main_source_integration': 'EXACT38_ONLY_AFTER_ACTUAL321_SEAL_AND_NEW_GRANT',
    'formal_increment': 0, 'counter_reset': False})
prepared = save('prepared_refs.json', {'canonical_before': [ref(path) for path in CANON],
    'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins, 'origins': origins,
    'pending_origin_refs': pin_bundle['pending_origin_refs'],
    'verified_refs': [ref(path) for path in sorted(READS, key=str) if path not in CANON],
    'source_edits_compile_test_SQL_in_preparation': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'register_ref': runner, 'run_ref': wrapped, 'prepared_ref': prepared,
    'scope_ref': pins['scope'], 'audit_ref': pins['audit'], 'seal_ref': sealed}, ensure_ascii=True))
