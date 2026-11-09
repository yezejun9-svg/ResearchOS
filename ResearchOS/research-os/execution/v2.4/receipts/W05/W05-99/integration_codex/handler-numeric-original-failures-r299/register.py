import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
READS = {}

def read(path):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    if path not in READS: READS[path] = path.read_bytes()
    return READS[path]

def ref(path, expected=None):
    path = Path(path)
    if not path.is_absolute(): path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT)
    data = read(path); sha = hashlib.sha256(data).hexdigest()
    assert expected is None or sha == expected
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha, 'bytes': len(data)}

def save(name, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream: stream.write(data)
    return ref(OUT / name)

lock = json.loads(read(ROOT / 'execution/toolchains/locked.json'))['tools']
git = lock['git']['path']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest() == lock['git']['sha256']
before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert [cp['revision'], ow['revision'], len(cp['failure_counters'])] == [298, 126, 313]
head = subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
status = subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
assert len(status.splitlines()) == 13 and sum(r[:2] == b' D' for r in status.splitlines()) == 11
audit_path = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/handler-numeric-and-settlement-originals-audit-r298/audit.json'
audit_ref = ref(audit_path, '6b679d26d6b1f7dae61d8188e97680e8dac1266929c667e117c7c47aca80e9e1')
audit = json.loads(read(audit_path))
for row in audit['copies']:
    actual = ref(row['path'], row['sha256']); assert actual['bytes'] == row['bytes']
supplement_ref = audit['supplement_ref']; ref(supplement_ref['path'], supplement_ref['sha256'])
supplement = json.loads(read(ROOT / supplement_ref['path']))
assert len(supplement['new_batch_origins']) == 1 and len(supplement['tool_origins']) == 2
origins = []
batch = supplement['new_batch_origins'][0]
result_ref = next(r for r in batch['refs'] if r['path'].endswith('/result.json'))
invocation_ref = next(r for r in batch['refs'] if r['path'].endswith('/command.invocation.json'))
result = json.loads(read(ROOT / result_ref['path']))
invocation = json.loads(read(ROOT / invocation_ref['path']))
assert result['exit'] == invocation['exit'] == 1 and not result['source_drift'] and result['input_count'] == 39071
assert result['test_events'] == {'pass': 54, 'fail': 1, 'skip': 0}
origins.append((batch['origin'], {'actual_exit': 1, 'cause': batch['cause'], 'result_ref': result_ref,
    'events': result['test_events'], 'count_once_per_batch': True}))
for row in supplement['tool_origins']:
    assert row['actual_outer_exit'] == 1
    origins.append(('tool-' + row['chunk_id'], row))
old_failures = json.loads(before[CANON[0]])['failure_counters']
old_keys = {r.get('origin_key') for r in old_failures}
for origin, detail in origins:
    key = 'W05-99/handler-numeric-settlement/' + origin
    assert key not in old_keys
    cp['failure_counters'].append({'origin_key': key, 'evidence_ref': supplement_ref, 'detail': detail,
        'attempts': 1, 'retries_used': 0, 'count_once': True, 'counter_reset': False,
        'status': 'ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE', 'formal_increment': 0})
assert cp['failure_counters'][:313] == old_failures and len(cp['failure_counters']) == 316
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
cp['work_in_progress']['configuration_handler_numeric_original_failures_ref'] = audit_ref
cp['work_in_progress']['configuration_handler_unknown_native_exit_origins_preserved'] = {
    'origins': supplement['unknown_original_outer_exits'], 'evidence_ref': supplement_ref,
    'actual_exit': None, 'failure_counter_increment': 0, 'no_native_exit_fabricated': True}
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'HANDLER_NUMERIC_SETTLEMENT_ORIGINAL_FAILURES_REGISTERED',
    'audit_ref': audit_ref, 'failure_origins_before': 313, 'failure_origins_after': 316,
    'counter_reset': False, 'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=299, expected_previous_revision=298, updated_at=now, updated_by='codex:/root')
ow.update(revision=127, amended_at=now, amended_by='codex:/root')
ow['card_path_bindings']['W05-99']['subtasks']['host_configuration_public_handlers']['numeric_original_failure_audit_ref'] = audit_ref
for row in [audit_ref, supplement_ref]:
    if row['path'] not in cp['evidence_index']: cp['evidence_index'].append(row['path'])
for p, data in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as stream: stream.write(data)
with (OUT / 'git-status.original.raw').open('xb') as stream: stream.write(status)
desired = {p: (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8') for p, v in zip(CANON[:2], [cp, ow])}
for p, data in desired.items():
    with (OUT / (p.stem + '.desired.json')).open('xb') as stream: stream.write(data)
intent_ref = save('canonical-write.intent.json', {'actor': 'codex:/root', 'Main_head': head,
    'status_ref': ref(OUT / 'git-status.original.raw'), 'register_ref': ref(Path(__file__)),
    'toolchain_lock_ref': ref(ROOT / 'execution/toolchains/locked.json'),
    'transition': {'checkpoint': [298, 299], 'ownership': [126, 127], 'failures': [313, 316]},
    'metadata': [{'path': p.relative_to(ROOT).as_posix(), 'original_ref': ref(OUT / (p.stem + '.original.json')),
        'desired_ref': ref(OUT / (p.stem + '.desired.json'))} for p in CANON[:2]],
    'unchanged': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(before[p]).hexdigest()} for p in CANON[2:]],
    'recovery': 'Root forward only against exact own original or desired bytes, unchanged remaining metadata, HEAD and saved status; external differences stop; no rollback/reset/automatic rerun.'})
assert all(p.read_bytes() == data for p, data in before.items())
assert all(p.read_bytes() == data for p, data in READS.items())
for p, data in desired.items():
    with p.with_name(p.name + '.root299.tmp').open('xb') as stream: stream.write(data)
expected_live = dict(before); phase = 'ALL_DESIRED_TEMP_FILES_PREPARED'
try:
    for p, data in desired.items():
        assert all(c.read_bytes() == expected_live[c] for c in CANON)
        assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
        assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
        os.replace(p.with_name(p.name + '.root299.tmp'), p); expected_live[p] = data
        assert p.read_bytes() == data
        phase = p.name + '_REPLACED_AND_VERIFIED'
        save('canonical-write.' + p.stem + '.done.json', {'phase': phase, 'sha256': hashlib.sha256(data).hexdigest()})
    assert all(p.read_bytes() == data for p, data in expected_live.items())
    actual = json.loads(CANON[0].read_bytes()); actual_ow = json.loads(CANON[1].read_bytes())
    assert [actual['revision'], actual_ow['revision'], len(actual['failure_counters'])] == [299, 127, 316]
    assert actual['failure_counters'][:313] == old_failures
    assert actual['current_effective_formal_status'] == json.loads(before[CANON[0]])['current_effective_formal_status']
    assert subprocess.check_output([git, 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == head
    assert subprocess.check_output([git, 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
    save('canonical-write.verified.json', {'checkpoint': 299, 'ownership': 127, 'failure_origins': 316,
        'intent_ref': intent_ref, 'old313_prefix_unchanged': True, 'step_state_commands_unchanged': True,
        'old11_git_deletions_preserved': True, 'formal_increment': 0})
except BaseException as error:
    save('canonical-write.exception.json', {'phase': phase, 'error': repr(error), 'intent_ref': intent_ref,
        'current_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in CANON},
        'automatic_retry': False, 'rollback_or_external_overwrite': False})
    raise
handoff_ref = save('handoff-r299-running.json', {'state': 'ACTIVE_IMPLEMENTATION_NOT_COMPLETE',
    'project_id': cp['project_id'], 'Main_head': head, 'checkpoint': ref(CANON[0]), 'ownership': ref(CANON[1]),
    'step_state': ref(CANON[2]), 'commands': ref(CANON[3]), 'revision': 299, 'failure_origins': 316,
    'counter_reset': False, 'source_failure_audit_ref': audit_ref,
    'previous_handoff_ref': ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-g1-registration-final-r298/handoff-r298-running.json', 'c7d0f225a4d7d71c2e4085cfe33f2e4b283e05088286f9e487cfdd82c2188d4d'),
    'current_card': 'W05-99', 'handler': 'Candidate38 temporarily frozen; actual CLI/TLS cohorts and full closure in progress. Final commit, current whole-scope matrix and NONAUTHOR acceptance still required.',
    'provider': 'Root first G1 preparation failure retained, author readonly ESM repair preparation active. No automatic retry.',
    'F08': 'Readonly v5 correction authorized; whole20 final review and SQL24 source lease remain open.',
    'current_effective_formal_status': cp['current_effective_formal_status'],
    'all22_and42_effective_acceptances_required': True, 'paid_calls': 0, 'formal_increment': 0})
print(json.dumps({'checkpoint': 299, 'ownership': 127, 'failure_origins': 316, 'handoff_ref': handoff_ref}, ensure_ascii=True))
