import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
REPLAY = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r309-534857db-public-jev'


def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
    return ref(OUT / name)


outer = json.loads((OUT / 'invocation.json').read_bytes())
native = json.loads((REPLAY / 'go-list.invocation.json').read_bytes())
after = json.loads((REPLAY / 'inputs.after_failure.json').read_bytes())
before = json.loads((REPLAY / 'inputs.before_Go_tools.json').read_bytes())
assert outer['actual_exit'] == native['actual_exit'] == 1
assert not (REPLAY / 'compile.invocation.json').exists() and not list(REPLAY.glob('case-*.invocation.json'))
assert len(before) == len(after['observations']) == 14913 and all(row['equal'] for row in after['observations'])
process = native['process_observation']
cleanup = process['job_cleanup']
assert process['resumed'] and process['error'] is None and not process['timed_out']
assert all(cleanup[key] is True for key in ['assigned_before_resume', 'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'])
assert cleanup['errors'] == []
failure = save('failure_origin.json', {'actor': 'codex:/root',
    'origin_key': 'r309-list-independent-public-export-missing-ops-experiment-sandbox-go-list',
    'actual_outer_exit': 1, 'actual_native_Go_exit': 1, 'origin_count': 1,
    'cause': 'Public exporter added the five JEV files but omitted existing public ops/experiment_sandbox imported by bridge_windows.go. Full known518 public compiler catalog now has31 other missing resources; no package download or case retry performed.',
    'native_invocation_ref': ref(REPLAY / 'go-list.invocation.json'), 'native_stderr_ref': ref(REPLAY / 'go-list.stderr.raw'),
    'outer_invocation_ref': ref(OUT / 'invocation.json'), 'driver_exception_ref': ref(REPLAY / 'driver.exception.json'),
    'before_Go_ref': ref(REPLAY / 'inputs.before_Go_tools.json'), 'after_failure_ref': ref(REPLAY / 'inputs.after_failure.json'),
    'public_export_ref': ref(REPLAY / 'public-source-export.json'), 'known_inputs': 14913, 'known_input_drift': 0,
    'native_product_test_cases': 0, 'compile_commands': 0, 'SDK_worker_MODEL_external_paid_private': 0,
    'owned_Job_cleanup_confirmed': True, 'source_acceptance': False, 'formal_increment': 0,
    'automatic_same_input_retry': False, 'counter_reset': False,
    'related_previous_failure': 'r308-list-independent-public-export-missing-JEV-go-list preserved separately. Broad export omission chain now2 actual failed go-list invocations, original input cohorts distinct; counts never reset.'})
entries = [ref(path) for base in [OUT, REPLAY] for path in sorted(base.rglob('*')) if path.is_file() and path.name != 'manifest.json']
manifest = save('manifest.json', {'entries': entries, 'count': len(entries), 'self_excluded': True, 'no_compile_or_case': True})
print(json.dumps({'failure': failure, 'manifest': manifest, 'listed': len(entries)}, ensure_ascii=True))
