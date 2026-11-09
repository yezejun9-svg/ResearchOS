import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
REPLAY = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r310-534857db-public-plan'


def ref(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


outer = json.loads((OUT / 'invocation.json').read_bytes())
native = json.loads((REPLAY / 'case-01.invocation.json').read_bytes())
exception = json.loads((REPLAY / 'driver.exception.json').read_bytes())
assert outer['actual_exit'] == 1 and outer['wrapper_error'] is None
assert native['actual_exit'] == 0 and native['process_observation']['actual_exit'] == 0
assert exception['phase'] == 'case-01' and exception['completed_cases'] == []
cleanup = native['process_observation']['job_cleanup']
assert all(cleanup[name] is True for name in ['kill_on_job_close_configured', 'assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed']) and cleanup['errors'] == []
before = json.loads((REPLAY / 'inputs.before_first_case.json').read_bytes())
after_native = json.loads((REPLAY / 'case-01.after_native.inputs.json').read_bytes())
after_failure = json.loads((REPLAY / 'inputs.after_failure.json').read_bytes())
assert before == after_native and len(before) == 17185
assert len(after_failure['observations']) == len(before)
assert all(row['equal'] is True for row in after_failure['observations'])
current = []
for row in before:
    path = Path(row['path'])
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    actual = {'path': row['path'], 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}
    current.append({'expected': row, 'actual': actual, 'equal': actual == row})
assert all(row['equal'] for row in current)
current_ref = save('inputs.current-after-stop.json', current)
case = REPLAY / 'cases/TestSessionListHTTPOriginalContextIdentity__NullContext'
sidecars = [ref(case / name) for name in ['closed.sqlite', 'closed.sqlite-wal', 'closed.sqlite-shm']]
assert sidecars[1]['bytes'] == 0 and sidecars[2]['bytes'] == 32768
failure_ref = save('failure_origin.json', {
    'actor': 'codex:/root', 'origin_key': 'r310-list-independent-closed-copy-sidecars-0f9faf-d7304c',
    'actual_outer_exit': 1, 'actual_native_controller_exit': 1, 'actual_native_case_exit': 0,
    'origin_count': 1, 'actual_product_native_test_failures': 0, 'native_cases_run': 1,
    'fully_closed_cases': 0, 'later13_cases': 'NOT_RUN_AFTER_FIRST_UNEXPECTED',
    'cause': 'Independent check_closed refused closed.sqlite because WAL and SHM existed before independent Python SQL read. No sidecar deletion or relaxed check performed.',
    'sidecar_loader_or_creator_cause': None, 'sidecar_files': sidecars,
    'outer_invocation_ref': ref(OUT / 'invocation.json'), 'native_invocation_ref': ref(REPLAY / 'case-01.invocation.json'),
    'driver_exception_ref': ref(REPLAY / 'driver.exception.json'),
    'original_closed_proof_ref': ref(case / 'closed-proof.json'),
    'known_inputs': 17185, 'before_after_native_after_failure_current_drift': 0,
    'current_inputs_ref': current_ref, 'owned_job_cleanup_confirmed': True,
    'same_input_automatic_retry': False, 'counter_reset': False, 'source_acceptance': False,
    'formal_increment': 0, 'SDK_MODEL_external_paid_private': 0})
entries = [ref(p) for root in [OUT, REPLAY] for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'manifest.json']
manifest_ref = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True,
    'original_stopped_output_and_sidecars_preserved': True, 'product_acceptance': False})
print(json.dumps({'failure': failure_ref, 'manifest': manifest_ref, 'listed': len(entries)}, ensure_ascii=True))
