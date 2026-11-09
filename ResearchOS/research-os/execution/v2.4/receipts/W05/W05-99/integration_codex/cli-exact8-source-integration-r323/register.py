import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize:
    raise RuntimeError('Optimized Python prohibited')
sys.dont_write_bytecode = True
os.environ['GIT_OPTIONAL_LOCKS'] = '0'
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / name for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}


def read(path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    if path not in READS:
        READS[path] = path.read_bytes()
    return READS[path]


def ref(path, expected=None):
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    path = path.resolve()
    raw = read(path)
    result = {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or result['sha256'] == expected
    return result


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
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
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [322, 150, 425]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert cp['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert head == prepared['head'] == 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
assert hashlib.sha256(status).hexdigest() == prepared['git_status_sha256'] == 'e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
assert len(status.splitlines()) == 13 and sum(row[:2] == b' D' for row in status.splitlines()) == 11
assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
for item in prepared['verified_refs']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
pins = prepared['pins']
scope = json.loads(read(pins['scope']['path']))
review = json.loads(read(pins['integration_controller_review']['path']))
assert scope['expected_before_registration'] == [322, 150, 425]
assert scope['expected_registration'] == [323, 151, 425]
assert scope['base'] == head and scope['exact_paths'] == 8 and scope['union_paths'] == 43
assert review['scope_sha256'] == pins['scope']['sha256']
assert review['controller_sha256'] == scope['controller_ref']['sha256']
assert review['launcher_sha256'] == pins['launcher']['sha256']
assert review['reviewer'] == 'codex:/root/w05_merge_review'
assert review['decision'] == 'READY_FOR_ROOT_EXACT8_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES'
assert review['requested_changes'] == [] and review['actual_integration_executed'] is False
closed = json.loads(read(pins['main38_completed']['path']))
assert closed['actual_head'] == head and closed['unique_paths'] == 38 and closed['merge_attempts'] == 1
assert closed['status'] == 'EXACT38_SOURCE_ONLY_FAST_FORWARD_COMPLETE_PENDING_COMBINED_VALIDATION'
old_failures = json.loads(before[CANON[0]])['failure_counters']
assert len(old_failures) == 425 and prepared['origins'] == []
pending = json.loads(read(pins['postcut_pending_origins']['path']))
assert pending['registered_before'] == [322,150,425] and pending['registration_cut_after'] == [323,151,425]
assert len(pending['origin_refs']) == 2 and pending['origin_refs'] == prepared['pending_origin_refs']
assert pending['observed_lower_bound'] == prepared['observed_actual_tool_origin_lower_bound'] == 427
assert cp['failure_counters'] == old_failures
original_cp = json.loads(before[CANON[0]])
original_ow = json.loads(before[CANON[1]])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress'].update(
    cli_exact8_source_integration_state='ROOT_EXACT8_SOURCE_ONLY_SCOPE_REGISTERED_WAIT_ACTUAL_SEAL_AND_GRANT',
    cli_exact8_source_integration_scope_ref=pins['scope'],
    cli_exact8_source_integration_controller_review_ref=pins['integration_controller_review'],
    cli_exact8_source_integration_launcher_ref=pins['launcher'],
    cli_exact8_source_integration_grant_producer_ref=pins['grant_producer'],
    cli_exact8_fresh43_validation_authorized=False,
    r323_cut_pending_actual_tool_origin_refs=prepared['pending_origin_refs'],
    observed_actual_tool_origin_lower_bound_after_r323_cut=427)
subtasks = ow['card_path_bindings']['W05-99']['subtasks']
assert 'cli_exact8_source_integration' not in subtasks
exact = json.loads(read(scope['exact8_ref']['path']))
assert len(exact) == len({x['path'] for x in exact}) == 8
subtasks['cli_exact8_source_integration'] = {
    'owner': 'codex:/root', 'current_source_writer': 'codex:/root',
    'state': 'ROOT_EXACT8_SOURCE_ONLY_REGISTERED_WAIT_SEAL_AND_GRANT',
    'scope_ref': pins['scope'], 'controller_review_ref': pins['integration_controller_review'],
    'source_paths': [x['path'] for x in exact], 'source_paths_ref': scope['exact8_ref'],
    'candidate': scope['candidate'], 'base': head, 'source_path_cap': 8,
    'apply_cap': 1, 'commit_cap': 1, 'compile_test_SQL_HTTP_model_authorized': False,
    'source_acceptance': False, 'formal_increment': 0}
cp['next_command'] = 'After actual r323 registration, independent review and sealed grant, Root may perform one exact8 source-only indexed import and one commit onto closed Main38 to43. Fresh43 compile/held2, Desktop15 and formal acceptance need separate scopes. Preserve all425 registered failures plus2 explicitly pending postcut origins (observed lower bound427), all existing holds and all22/all42 requirements.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'CLI_EXACT8_SOURCE_ONLY_SCOPE_REGISTERED_AFTER_CLOSED_MAIN38',
    'head_before': head, 'head_after': head, 'scope_ref': pins['scope'],
    'controller_review_ref': pins['integration_controller_review'],
    'failure_origins_before': 425, 'failure_origins_after': 425,
    'pending_origin_refs': prepared['pending_origin_refs'], 'observed_lower_bound': 427,
    'counter_reset': False, 'formal_increment': 0})
cp.update(revision=323, expected_previous_revision=322, updated_at=now, updated_by='codex:/root')
ow.update(revision=151, amended_at=now, amended_by='codex:/root')
for item in pins.values():
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
allowed_cp = {'revision', 'expected_previous_revision', 'updated_at', 'updated_by', 'work_in_progress', 'next_command', 'integrity_events', 'evidence_index'}
assert {k:v for k,v in cp.items() if k not in allowed_cp} == {k:v for k,v in original_cp.items() if k not in allowed_cp}
allowed_wip = {'cli_exact8_source_integration_state', 'cli_exact8_source_integration_scope_ref', 'cli_exact8_source_integration_controller_review_ref', 'cli_exact8_source_integration_launcher_ref', 'cli_exact8_source_integration_grant_producer_ref', 'cli_exact8_fresh43_validation_authorized', 'r323_cut_pending_actual_tool_origin_refs', 'observed_actual_tool_origin_lower_bound_after_r323_cut'}
assert {k:v for k,v in cp['work_in_progress'].items() if k not in allowed_wip} == {k:v for k,v in original_cp['work_in_progress'].items() if k not in allowed_wip}
compare_ow = json.loads(json.dumps(ow))
compare_ow['card_path_bindings']['W05-99']['subtasks'].pop('cli_exact8_source_integration')
for k in ['revision','amended_at','amended_by']:
    if k in original_ow: compare_ow[k] = original_ow[k]
    else: compare_ow.pop(k,None)
assert compare_ow == original_ow
assert cp['head'] == original_cp['head'] == head
assert cp['current_effective_formal_status'] == original_cp['current_effective_formal_status']
for path, raw in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream:
        stream.write(raw)
with (OUT / 'git-status.original.raw').open('xb') as stream:
    stream.write(status)
desired = {path: (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for path, value in zip(CANON[:2], [cp, ow])}
for path, raw in desired.items():
    with (OUT / (path.stem + '.desired.json')).open('xb') as stream:
        stream.write(raw)
intent_ref = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': head,
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)), 'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [322, 323], 'ownership': [150, 151], 'failures': [425, 425]},
    'metadata': [{'path': path.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (path.stem + '.original.json')),
        'desired_ref': ref(OUT / (path.stem + '.desired.json'))} for path in CANON[:2]],
    'unchanged': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[path]).hexdigest()} for path in CANON[2:]],
    'source_acceptance': False, 'Main_integration_authorized': False, 'formal_increment': 0,
    'recovery': 'Forward only against exact own original or desired bytes and unchanged four metadata/HEAD/status; no rollback/reset/automatic rerun.'})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert all(path.read_bytes() == raw for path, raw in READS.items())
for path, raw in desired.items():
    with path.with_name(path.name + '.root323.tmp').open('xb') as stream:
        stream.write(raw)
expected_live = dict(before)
phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for path, raw in desired.items():
        assert all(canonical.read_bytes() == expected_live[canonical] for canonical in CANON)
        assert all(p.read_bytes() == b for p, b in READS.items())
        assert subprocess.check_output([git, 'diff', '--cached', '--name-only'], cwd=ROOT) == b''
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(path.with_name(path.name + '.root323.tmp'), path)
        expected_live[path] = raw
        READS[path] = raw
        assert path.read_bytes() == raw
        phase = path.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + path.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(raw).hexdigest()})
    assert all(path.read_bytes() == raw for path, raw in expected_live.items())
    actual, actual_ow = [json.loads(path.read_bytes()) for path in CANON[:2]]
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [323, 151, 425]
    assert actual['failure_counters'] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 323, 'ownership': 151, 'failure_origins': 425,
        'intent_ref': intent_ref, 'old425_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'Main_exact38_source_only_FF_closed': True,
        'CLI_EXACT8_WAIT_SEAL_AND_EXCLUSIVE_GRANT_NO_PRODUCT_EXECUTION': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r323-running.json', {
    'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE', 'project_id': cp['project_id'], 'Main_head': head,
    'canonical_refs': [ref(path) for path in CANON], 'revision': 323, 'failure_origins': 425,
    'pending_origin_refs': prepared['pending_origin_refs'], 'pending_origin_count': 2,
    'observed_actual_tool_origin_lower_bound': 427, 'registered425_plus_pending2': True,
    'previous_handoff_ref': pins['previous_handoff'], 'counter_reset': False,
    'scope_ref': pins['scope'], 'controller_review_ref': pins['integration_controller_review'],
    'launcher_ref': pins['launcher'], 'grant_producer_ref': pins['grant_producer'],
    'next': cp['next_command'], 'source_acceptance': False, 'formal_increment': 0,
    'actual_source_import': False, 'fresh43_validation_authorized': False,
    'all22_and42_effective_acceptances_required': True})
print(json.dumps({'checkpoint': 323, 'ownership': 151, 'failure_origins': 425, 'handoff_ref': handoff_ref}, ensure_ascii=True))
