"""Prepare forward-only metadata after actual Main38 success; never merge or test."""
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
PREVIOUS = OUT.parent / 'fresh-handler38-source-integration-r321-v2'
CANON = [ROOT / 'execution/v2.4' / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
BASE = '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
TARGET = 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
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

def ref(path, digest=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    raw = read(p)
    item = {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert digest is None or item['sha256'] == digest
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

assert len(sys.argv) == 3
outer_ref = ref(sys.argv[1], sys.argv[2])
outer = doc(outer_ref)
assert outer['schema'] == 'researchos.main38-root-launch-outer-completion.v1'
assert outer['actual_outer_exit'] == 0 and outer['automatic_retry'] is False
assert outer['reported_root_launcher_exit'] == 0 and outer['source_acceptance'] is False
launcher_out = (ROOT / outer['launcher_output_root']).resolve()
assert launcher_out.parent == ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_root_launcher_codex'
launcher_mf_ref = ref(launcher_out / 'manifest.json')
launcher_mf = doc(launcher_mf_ref)
assert launcher_mf['first_failure'] is None
for item in launcher_mf['entries']:
    assert (ROOT / item['path']).resolve().is_relative_to(launcher_out)
    doc(item) if item['path'].endswith('.json') else ref(item['path'], item['sha256'])
for name in ['grant-preflight', 'source-only-integration']:
    observed = json.loads(read(launcher_out / (name + '.owned-result.json')))
    result = observed['result']
    assert observed['wrapper_error'] is None and observed['actual_native_exit'] == result['actual_exit'] == 0
    assert result['error'] is None and result['timed_out'] is False and result['resumed'] is True
    cleanup = result['job_cleanup']
    assert cleanup['errors'] == [] and all(cleanup[k] is True for k in [
        'unnamed_exclusive_job', 'assigned_before_resume', 'kill_on_job_close_configured',
        'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'])
launcher_completed_ref = ref(launcher_out / 'completed.json')
launcher_completed = doc(launcher_completed_ref)
assert launcher_completed['actual_controller_native_exit'] == 0 and launcher_completed['formal_increment'] == 0
previous_prepared = json.loads(read(PREVIOUS / 'prepared_refs.json'))
ref(PREVIOUS / 'prepared_refs.json', '1d10ff495924f1c3b9b6a6a9fe927ff5c6c5bde99a61f189ea4d741ff434efcf')
ref(PREVIOUS / 'register.py', '199e46d1db99b7c18053759d69a920330df92b1bf901637beb675aef06c82dcd')
ref(PREVIOUS / 'run.py', 'dcff04204ca0461eefadb763ef2cec68826b2e6b7dabad4c9dd770b29c342b3a')
ref(PREVIOUS / 'seal.py', 'd55bd1cce6fe1a0a76e7dc8f8966b0d499ead0d5a4d7cc2383e30ffacebf0b77')
ref(PREVIOUS / 'manifest.json', '568ff537ee996a384dfe42cb12d352cb6d9607a821ba9fbc2b216ba98b3d3018')
scope_ref = previous_prepared['pins']['scope']
scope = doc(scope_ref)
assert scope['expected_registration'] == [321, 149, 422] and scope['target_source_commit'] == TARGET
executor_out = Path(scope['new_output_root'])
if not executor_out.is_absolute():
    executor_out = ROOT / executor_out
executor_out = executor_out.resolve()
assert executor_out.parent == ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_executor_codex'
assert executor_out.name == scope['operation_uuid']
completed_ref = ref(executor_out / 'completed.json')
manifest_ref = ref(executor_out / 'manifest.json')
completed = doc(completed_ref)
assert completed['status'] == 'EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION'
assert completed['actual_head'] == TARGET and completed['unique_paths'] == 38 and completed['merge_attempts'] == 1
assert completed['canonical_writes'] == completed['product_tests_HTTP_SQL_models'] == completed['formal_increment'] == 0
assert completed['whole_W05_acceptance'] is False and not (executor_out / 'failure.origin.json').exists()
assert completed['scope_ref'] == scope_ref
for authority in [completed['grant_ref'], launcher_completed['grant_ref']]:
    assert ref(authority['path'], authority['sha256'])['bytes'] == authority['bytes']
assert ref(completed['grant_ref']['path']) == ref(launcher_completed['grant_ref']['path'])
manifest = doc(manifest_ref)
assert manifest['count'] == len(manifest['entries'])
listed = {}
for item in manifest['entries']:
    p = Path(item['path']).resolve()
    assert p.is_relative_to(executor_out) and p not in listed
    assert ref(p, item['sha256'])['bytes'] == item['bytes']
    listed[p] = item
assert listed[executor_out / 'completed.json']['sha256'] == completed_ref['sha256']
git_invocations = [p for p in listed if p.name.endswith('.invocation.json')]
assert len(git_invocations) == 56
for p in git_invocations:
    invocation = json.loads(read(p))
    result = invocation['process_observation']
    assert invocation['actual_native_exit'] == 0 and invocation['wrapper_error'] is None
    assert result['actual_exit'] == 0 and result['error'] is None and not result['timed_out'] and result['resumed'] is True
    cleanup = result['job_cleanup']
    assert cleanup['errors'] == [] and all(cleanup[k] is True for k in [
        'unnamed_exclusive_job', 'assigned_before_resume', 'kill_on_job_close_configured',
        'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'])
cp, ow = [json.loads(read(path)) for path in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [321, 149, 422]
assert cp['head'] == BASE and cp['work_in_progress']['handler38_source_integration_scope_ref'] == scope_ref
lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
for name in ['python', 'git']:
    assert hashlib.sha256(Path(lock[name]['path']).read_bytes()).hexdigest() == lock[name]['sha256']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
git = lock['git']['path']
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == TARGET and hashlib.sha256(status).hexdigest() == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
source_after_ref = ref(executor_out / 'source.after.json')
after_rows = doc(source_after_ref)
assert len(after_rows) == 38 and len({row['path'] for row in after_rows}) == 38
for row in after_rows:
    assert ref(row['path'], row['sha256'])['bytes'] == row['bytes']
pins = dict(previous_prepared['pins'])
pins.update(previous_handoff=ref(PREVIOUS / 'handoff-r321-running.json'),
    previous_manifest=ref(PREVIOUS / 'manifest.json'),
    main38_outer_completion=outer_ref, main38_launcher_manifest=launcher_mf_ref,
    main38_launcher_completed=launcher_completed_ref, main38_completed=completed_ref,
    main38_manifest=manifest_ref, main38_source_after=source_after_ref)
origins = []
pending = previous_prepared['pending_origin_refs']
assert pending == cp['work_in_progress']['r321_cut_pending_actual_tool_origin_refs'] and len(pending) == 2
for item in pending:
    original = doc(item)
    chunk = original.get('tool_chunk_id') or original['tool_chunk']
    assert chunk in ['eeed61', 'df6aba']
    assert (original.get('actual_exec_command_exit') if chunk == 'eeed61' else original['actual_outer_exit']) == 1
    origins.append({'origin_key': 'r321-postcut-preparation-' + chunk,
        'actor': 'codex:/root/sources_parent_impl' if chunk == 'eeed61' else 'codex:/root/command_queue_impl',
        'actual_outer_exit': 1,
        'actual_native_exit': original['nested_native_exit'] if chunk == 'eeed61' else original['actual_native_python_exit'],
        'actual_native_product_exit': None, 'event_kind': 'PREPARATION_ONLY_ACTUAL_NONZERO',
        'cause': original['cause'] if chunk == 'eeed61' else original['error'],
        'evidence_ref': item, 'original_payload': original, 'product_cases_run': 0})
root_origin_ref = ref(OUT / 'failure-origin.d6c6f9.json', 'f3b914c3ca9ba9483c93d46a820f5c53fc93fca2fad12b3d89bb099477746f24')
root_origin = doc(root_origin_ref)
assert root_origin['actual_outer_exit'] == root_origin['actual_native_python_exit'] == 1
origins.append({'origin_key': 'root-after-main38-preparation-d6c6f9', 'actor': 'codex:/root',
    'actual_outer_exit': 1, 'actual_native_exit': 1, 'actual_native_product_exit': None,
    'event_kind': 'PREPARATION_ONLY_ACTUAL_NONZERO', 'cause': root_origin['cause'],
    'evidence_ref': root_origin_ref, 'original_payload': root_origin, 'product_cases_run': 0})
pins['root_post_integration_preparation_origin'] = root_origin_ref
assert len({row['origin_key'] for row in origins}) == 3
assert not {row['origin_key'] for row in origins}.intersection({row.get('origin_key') for row in cp['failure_counters']})
pins['failure_cut'] = save('failure-origins.cut.json', {'before': 422, 'after': 425, 'origins': origins,
    'old422_prefix_unchanged': True, 'count_once': True, 'counter_reset': False})
old = read(PREVIOUS / 'register.py').decode('utf-8', errors='strict')
header = once(old[:old.index("pins = prepared['pins']")], '[320, 148, 417]', '[321, 149, 422]')
header = once(header, "assert head == cp['head'] == prepared['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'",
    "assert cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'\nassert head == prepared['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'")
mutation = '''pins = prepared['pins']
closed = json.loads(read(pins['main38_completed']['path']))
assert closed['actual_head'] == head and closed['unique_paths'] == 38 and closed['merge_attempts'] == 1
assert closed['status'] == 'EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION'
assert closed['whole_W05_acceptance'] is False
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert len(old_failures) == 422 and len(prepared['origins']) == 3
old_keys = {row.get('origin_key') for row in old_failures}
for item in prepared['origins']:
    assert item['origin_key'] not in old_keys and item['actual_outer_exit'] == 1
    ref(item['evidence_ref']['path'], item['evidence_ref']['sha256'])
    cp['failure_counters'].append({**item, 'attempts': 1, 'retries_used': 0,
        'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_PREPARATION_TOOL_NONZERO_ORIGIN_PRESERVED', 'formal_increment': 0})
assert cp['failure_counters'][:422] == old_failures and len(cp['failure_counters']) == 425
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['head'] = head
cp['work_in_progress'].update(
    handler38_source_integration_state='ACTUAL_MAIN_SOURCE_ONLY_FF38_CLOSED_PENDING_FRESH_COMBINED_VALIDATION',
    handler38_source_integration_completed_ref=pins['main38_completed'],
    handler38_source_integration_manifest_ref=pins['main38_manifest'],
    handler38_source_integration_outer_completion_ref=pins['main38_outer_completion'],
    handler38_source_integration_source_after_ref=pins['main38_source_after'],
    r322_r321_pending_origins_registered_refs=prepared['pending_origin_refs'],
    handler38_fresh_combined_validation_authorized=False,
    cli_exact8_source_integration_state='FUTURE_NEW_SCOPE_REQUIRED_AFTER_MAIN38_FORWARD_HEAD_REGISTRATION_AND_EVIDENCE_REVIEW',
    desktop_exact15_source_integration_state='PREPARATION_ONLY_FUTURE_ACTUAL_MAIN43_SCOPE_REQUIRED')
cp['failure_chains']['W05-99/r322-two-postcut-preparation-diagnostics'] = {
    'old422_prefix_unchanged': True, 'new_actual_nonzero_origins': 3,
    'failure_cut_ref': pins['failure_cut'], 'audit_ref': pins['audit'], 'counter_reset': False}
integration = ow['card_path_bindings']['W05-99']['subtasks']['handler38_main_source_integration']
assert integration['current_source_writer'] == 'codex:/root'
integration.update(current_source_writer=None, state='SOURCE_ONLY_FF38_CLOSED_PENDING_FRESH_COMBINED_VALIDATION',
    completed_ref=pins['main38_completed'], manifest_ref=pins['main38_manifest'], source_acceptance=False)
cp['next_command'] = 'Main38 actual source-only FF and forward head metadata are closed. Non-author review this closed evidence and actual post-registration audit; then new explicit CLI8 source import scope/register/grant to reach43, fresh combined43 compile and held2 CLI replays, Desktop15 import to58 and fresh169 Root replay under their own scopes. W09 finite-controller revision preparation only. Preserve all425 failures and require all22/all42 actual effective acceptances.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'ACTUAL_SOURCE_ONLY_MAIN38_FORWARD_HEAD_REGISTERED_AND_TWO_PENDING_AND_ONE_ROOT_PREPARATION_DIAGNOSTICS_APPENDED',
    'head_before': '2cdb0d43d5a600eef13c8f1735946a9adf52d079', 'head_after': head,
    'completed_ref': pins['main38_completed'], 'manifest_ref': pins['main38_manifest'],
    'failure_origins_before': 422, 'failure_origins_after': 425,
    'counter_reset': False, 'formal_increment': 0})
cp.update(revision=322, expected_previous_revision=321, updated_at=now, updated_by='codex:/root')
ow.update(revision=150, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
'''
tail = old[old.index('for path, raw in before.items():'):old.index("handoff_ref = save('handoff-r321-running.json'")]
for previous, updated in [('[320, 321]', '[321, 322]'), ('[148, 149]', '[149, 150]'),
    ('[417, 422]', '[422, 425]'), ('[321, 149, 422]', '[322, 150, 425]'),
    ("'checkpoint': 321", "'checkpoint': 322"), ("'ownership': 149", "'ownership': 150"),
    ("'failure_origins': 422", "'failure_origins': 425"),
    ("actual['failure_counters'][:417]", "actual['failure_counters'][:422]"),
    ("'old417_prefix_unchanged'", "'old422_prefix_unchanged'"),
    ("'Main_exact38_FF_scope_registered_only': True", "'Main_exact38_source_only_FF_closed': True"),
    ("'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT'", "'Main_integration_authorized': False"),
    ('BOUNDED14_GO3_CLOSED_W09_STOPPED_FRESH_SOURCE_ONLY38_SCOPE', 'MAIN38_SOURCE_ONLY_CLOSED_NO_FURTHER_SOURCE_OR_PRODUCT_EXECUTION_GRANT')]:
    tail = once(tail, previous, updated)
assert tail.count('root321.tmp') == 2
tail = tail.replace('root321.tmp', 'root322.tmp')
ending = '''handoff_ref = save('handoff-r322-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'project_id': cp['project_id'], 'Main_head': head,
    'canonical_refs': [ref(path) for path in CANON], 'revision': 322, 'failure_origins': 425,
    'previous_handoff_ref': pins['previous_handoff'], 'counter_reset': False,
    'completed_ref': pins['main38_completed'], 'manifest_ref': pins['main38_manifest'],
    'next': cp['next_command'], 'source_acceptance': False, 'formal_increment': 0,
    'all22_and42_effective_acceptances_required': True})
print(json.dumps({'checkpoint': 322, 'ownership': 150, 'failure_origins': 425, 'handoff_ref': handoff_ref}, ensure_ascii=True))
'''
runner = script('register.py', header + mutation + tail + ending)
wrapper = read(PREVIOUS / 'run.py').decode('utf-8', errors='strict')
wrapper = once(wrapper, 'root_registration_r321_readonly_review_codex', 'root_registration_r322_readonly_review_codex')
wrapper = once(wrapper, "review['expected_before'] == [320, 148, 417] and review['expected_after'] == [321, 149, 422]",
    "review['expected_before'] == [321, 149, 422] and review['expected_after'] == [322, 150, 425]")
wrapper = once(wrapper, "cp['revision'] == 320 and len(cp['failure_counters']) == 417", "cp['revision'] == 321 and len(cp['failure_counters']) == 422")
wrapped = script('run.py', wrapper)
sealer = read(PREVIOUS / 'seal.py').decode('utf-8', errors='strict')
sealer = once(sealer, "PREVIOUS = OUT.parent / 'parallel-source-and-go3-r320'", "PREVIOUS = OUT.parent / 'fresh-handler38-source-integration-r321-v2'")
for previous, updated in [
    ("assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [320, 148, 417]", "assert [cp_before['revision'], ow_before['revision'], len(cp_before['failure_counters'])] == [321, 149, 422]"),
    ("assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [321, 149, 422]", "assert [cp_after['revision'], ow_after['revision'], len(cp_after['failure_counters'])] == [322, 150, 425]"),
    ("cp_after['failure_counters'][:417]", "cp_after['failure_counters'][:422]"),
    ("'before': [320, 148, 417], 'after': [321, 149, 422]", "'before': [321, 149, 422], 'after': [322, 150, 425]"),
    ("'old417_failure_prefix_unchanged'", "'old422_failure_prefix_unchanged'"),
    ("'source_only38_actual_merge': 'NOT_STARTED_AT_REGISTRATION_SEAL'", "'source_only38_actual_merge': 'ACTUAL_ONCE_SOURCE_ONLY_FF_CLOSED_NO_COMBINED_PRODUCT_VALIDATION'"),
    ("'Main_integration_authorized': 'ONLY_FRESH_SCOPE_AFTER_SEAL_AND_GRANT'", "'Main_integration_authorized': False"),
    ("'current': [321, 149, 422]", "'current': [322, 150, 425]")]:
    sealer = once(sealer, previous, updated)
sealer = once(sealer, "audit = save('registration-audit.json', {", "audit = save('registration-audit.json', {\n    'schema': 'researchos.main38-post-integration-registration-audit.v1',\n    'completed_ref': prepared['pins']['main38_completed'],\n    'manifest_ref': prepared['pins']['main38_manifest'],\n    'registered_head': cp_after['head'],")
sealer = once(sealer, "assert cp_after['current_effective_formal_status'] == cp_before['current_effective_formal_status']", "assert cp_after['current_effective_formal_status'] == cp_before['current_effective_formal_status']\nassert cp_before['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'\nassert cp_after['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'")
sealed = script('seal.py', sealer)
pins['audit'] = save('audit.json', {'schema': 'researchos.root-registration-draft-audit.v1',
    'actor': 'codex:/root', 'state': 'DRAFT_PENDING_NONAUTHOR_REVIEW',
    'expected_before': [321, 149, 422], 'expected_after': [322, 150, 425],
    'head_before': BASE, 'registered_head_after': TARGET, 'completed_ref': completed_ref,
    'manifest_ref': manifest_ref, 'new_origins': origins, 'old422_prefix_unchanged': True,
    'no_additional_source_product_compile_test_SQL_HTTP_model_authority': True,
    'counter_reset': False, 'formal_increment': 0})
prepared = save('prepared_refs.json', {'canonical_before': [ref(path) for path in CANON],
    'head': head, 'git_status_sha256': hashlib.sha256(status).hexdigest(), 'pins': pins,
    'origins': origins, 'pending_origin_refs': pending,
    'verified_refs': [ref(path) for path in sorted(READS, key=str) if path not in CANON],
    'source_edits_compile_test_SQL_in_preparation': 0})
assert all(path.read_bytes() == raw for path, raw in READS.items())
print(json.dumps({'register_ref': runner, 'run_ref': wrapped, 'prepared_ref': prepared,
    'audit_ref': pins['audit'], 'seal_ref': sealed}, ensure_ascii=True))
