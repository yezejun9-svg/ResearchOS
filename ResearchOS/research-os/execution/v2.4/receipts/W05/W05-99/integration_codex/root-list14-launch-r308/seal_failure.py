import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
CASES = ROOT / 'execution/v2.4/receipts/W05/W05-99/session_list_identity_independent_replay_codex/root-r308-534857db'


def ref(path):
    raw = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


outer = json.loads((OUT / 'invocation.json').read_bytes())
native = json.loads((CASES / 'go-list.invocation.json').read_bytes())
assert outer['actual_exit'] == native['actual_exit'] == 1
assert native['process_observation']['timed_out'] is False
assert native['process_observation']['job_cleanup']['job_idle_confirmed'] is True
assert native['process_observation']['job_cleanup']['handles_closed'] is True
assert not (CASES / 'inputs.before_compile.json').exists() and not (CASES / 'result.json').exists()
assert list((CASES / 'cases').glob('*')) == []
save('failure_origin.json', {'actor': 'codex:/root', 'origin_key': 'r308-list-independent-public-export-missing-JEV-go-list',
    'actual_outer_exit': 1, 'actual_native_Go_exit': 1, 'origin_count': 1,
    'cause': 'Independent public Git export omitted the public generic evaluation/holdout/jev Go package imported by adapters/protectedstore/frozen_development.go. go-list stopped before compile/cases.',
    'native_invocation_ref': ref(CASES / 'go-list.invocation.json'), 'native_stderr_ref': ref(CASES / 'go-list.stderr.raw'),
    'outer_invocation_ref': ref(OUT / 'invocation.json'), 'driver_exception_ref': ref(CASES / 'driver.exception.json'),
    'after_failure_ref': ref(CASES / 'inputs.after_failure.json'), 'public_export_ref': ref(CASES / 'public-source-export.json'),
    'native_product_test_cases': 0, 'SDK_worker_MODEL_external_paid_private': 0, 'compile_commands': 0,
    'closed_DB_cases': 0, 'scope_limited_Job_cleanup_confirmed': True,
    'source_acceptance': False, 'formal_increment': 0, 'automatic_same_input_retry': False, 'counter_reset': False,
    'initial_failure_vector_limit': 'Before graph completion the runner had not yet frozen expected source/tool inputs; its after_failure observations are explicitly empty. Exported Git blobs and each tool raw/invocation are retained; no complete precompile closure claimed.'})
save('manifest.json', {'entries': [ref(path) for base in [OUT, CASES] for path in sorted(base.rglob('*')) if path.is_file() and path.name != 'manifest.json'],
    'state': 'ACTUAL_GO_LIST1_BEFORE_COMPILE_CASES0_SINGLE_CAUSE_PRESERVED', 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'failure_origin': ref(OUT / 'failure_origin.json'), 'manifest': ref(OUT / 'manifest.json')}, ensure_ascii=True))
