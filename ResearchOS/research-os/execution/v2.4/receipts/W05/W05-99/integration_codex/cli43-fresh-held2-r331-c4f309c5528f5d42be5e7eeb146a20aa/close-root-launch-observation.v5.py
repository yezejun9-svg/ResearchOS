"""Seal actual completion without converting unobserved facts into successful exits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
parser = argparse.ArgumentParser()
parser.add_argument('--known-pending-origins', type=int, required=True)
args = parser.parse_args()
assert args.known_pending_origins >= 0

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def optional_pin(path):
    return pin(path) if Path(path).is_file() else None

def read(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

scope = read(OUT / 'scope_registration.json')
assert pin(OUT / 'scope_registration.json')['sha256'] == 'f71b60ad316aa3034ff3da5cd79c6aac4c4e5997425d86e7b84d2f9fc02ec89b'
executor, launcher = Path(scope['new_output_root']), Path(scope['new_wrapper_root'])
tools = read(OUT / 'root-launch.tool-observations.json')
final = tools['final']
assert isinstance(final['exit_code'], int) and 'session_id' not in final
markers = re.findall(r'^PythonNativeExit=([0-9]+)\s*$', final['output'], flags=re.MULTILINE)
assert len(markers) == 1 and int(markers[0]) == final['exit_code']
caller = read(OUT / 'root-launch.invocation.json')
result = read(executor / 'result.json') if (executor / 'result.json').is_file() else None
completed = read(launcher / 'completed.json') if (launcher / 'completed.json').is_file() else None
cause = result['first_cause'] if result is not None else None
origin_ref = optional_pin(executor / 'failure.origin.json')
assert (cause is None) == (origin_ref is None) if result is not None else True
if final['exit_code'] == 0:
    assert caller['actual_launcher_native_exit'] == 0 and caller['caller_error'] is None and caller['secondary'] == []
    assert completed is not None and completed['actual_inner_native_exit'] == 0
    assert result is not None and cause is None and result['secondary'] == [] and len(result['cases']) == 2
child = cause.get('last_child_result') if isinstance(cause, dict) else None
compiler_observations = []
for stage in ('build-test2json', 'build-cli', 'build-test'):
    path = executor / (stage + '.invocation.json')
    if not path.is_file():
        compiler_observations.append({'stage': stage, 'invocation_ref': None, 'observed': False})
        continue
    native = read(path)
    owned = native.get('result')
    compiler_observations.append({
        'stage': stage, 'observed': True, 'actual_exit': native.get('actual_exit'),
        'invocation_ref': pin(path), 'stdout_ref': optional_pin(executor / (stage + '.stdout.raw')),
        'stderr_ref': optional_pin(executor / (stage + '.stderr.raw')),
        'owned_result': owned, 'independent_qualification': 'PENDING'
    })
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
grant = read(grant_path)
assert pin(grant_path)['sha256'] == '124f16da796d16dd4a066d3b5ed8a00db8e744f7ca690d614cf46b14b8ac0f81'
canon = []
for row in grant['canonical_copies']:
    actual = pin(ROOT / row['canonical_path'])
    assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
    canon.append(actual)
local_failure_count = 1 if origin_ref is not None else 0
closed = {
    'schema': 'researchos.root-actual-launch-completion.v2', 'actor': 'codex:/root',
    'actual_initial_tool_chunk': tools['initial']['chunk_id'], 'actual_session_id': tools['initial'].get('session_id'),
    'actual_completion_tool_chunk': final['chunk_id'], 'actual_outer_tool_exit': final['exit_code'],
    'actual_python_caller_exit': int(markers[0]), 'actual_launcher_native_exit': caller['actual_launcher_native_exit'],
    'actual_inner_python_native_exit': completed.get('actual_inner_native_exit') if completed is not None else None,
    'caller_error': caller['caller_error'], 'caller_secondary': caller['secondary'],
    'first_cause_original_payload': cause, 'last_child_original_result': child,
    'underlying_local_failure_count': local_failure_count,
    'nested_exit_propagations_are_not_new_origins': True,
    'source_scope_ref': pin(OUT / 'scope_registration.json'), 'grant_ref': pin(grant_path),
    'caller_ref': pin(OUT / 'root-launch-once.v2.py'), 'caller_invocation_ref': pin(OUT / 'root-launch.invocation.json'),
    'tool_observation_ref': pin(OUT / 'root-launch.tool-observations.json'),
    'first_origin_ref': origin_ref, 'executor_result_ref': optional_pin(executor / 'result.json'),
    'executor_manifest_ref': optional_pin(executor / 'manifest.json'),
    'launcher_completion_ref': optional_pin(launcher / 'completed.json'),
    'launcher_manifest_ref': optional_pin(launcher / 'manifest.json'),
    'closed_graph_ref': optional_pin(executor / 'go-graph.actual.json'),
    'compiled_closure_ref': optional_pin(executor / 'compiled-closure.json'),
    'test2json_artifact_ref': optional_pin(executor / 'test2json-artifact.finally.json'),
    'compiler_observations': compiler_observations,
    'canonical_refs_at_completion': canon, 'canonical_changed': False,
    'actual_result_status': result['status'] if result is not None else None,
    'actual_case_roster_original_payload': result.get('case_roster') if result is not None else None,
    'actual_case_results_original_payload': result['cases'] if result is not None else None,
    'actual_NOT_RUN_original_payload': result['NOT_RUN'] if result is not None else None,
    'native_calls': result['native_calls'] if result is not None else None,
    'SDK_MODEL_external_paid': result['SDK_MODEL_external_paid'] if result is not None else None,
    'registered_origin_count': 509, 'known_late_pending_outside_fixed_cut': args.known_pending_origins,
    'observed_origin_count_at_closure': 509 + args.known_pending_origins + local_failure_count,
    'separately_captured_outer_native_raw': False, 'caller_OS_lifecycle_qualification': False,
    'fresh_compile_qualification': False, 'complete_current43_source_validation': False,
    'independent_qualification': 'PENDING', 'source_acceptance': False,
    'formal_increment': 0, 'automatic_retry': False, 'counter_reset': False
}
save('root-launch.outer-completion.json', closed)
members = [pin(path) for path in sorted(OUT.glob('root-launch*')) if path.is_file()]
members += [pin(OUT / name) for name in ('root-caller-preparation.json', 'prepare-root-caller.v6.py',
    'close-root-launch-observation.v5.py', 'root-metadata.tool-observations.after-grant.json')]
save('root-launch.closed.manifest.json', {'schema': 'researchos.root-launch-closure-manifest.v2',
    'actor': 'codex:/root', 'members': members, 'original_registration_manifests_unchanged': True,
    'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'completion_ref': pin(OUT / 'root-launch.outer-completion.json'),
    'manifest_ref': pin(OUT / 'root-launch.closed.manifest.json'),
    'actual_outer_exit': final['exit_code'], 'local_underlying_failures': local_failure_count,
    'independent_qualification': 'PENDING', 'formal_increment': 0}, ensure_ascii=False))
