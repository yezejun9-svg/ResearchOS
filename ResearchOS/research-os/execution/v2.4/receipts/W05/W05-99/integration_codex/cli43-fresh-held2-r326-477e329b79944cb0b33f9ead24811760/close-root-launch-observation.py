"""Close the actual outer observation without qualifying a failed execution."""
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def read(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
scope = read(OUT / 'scope_registration.json')
assert pin(OUT / 'scope_registration.json')['sha256'] == '68a0986a0bfcf39948ab2f696e33ef9ec05b39bb5a23f8787f92bf0129fe3566'
e = Path(scope['new_output_root'])
l = Path(scope['new_wrapper_root'])
tool = read(OUT / 'root-launch.tool-observations.json')
final = tool['final']
assert final['chunk_id'] == '69d9dc' and final['exit_code'] == 1
markers = re.findall(r'^PythonNativeExit=([0-9]+)\s*$', final['output'], flags=re.MULTILINE)
assert markers == ['1'], markers
caller = read(OUT / 'root-launch.invocation.json')
assert caller['actual_launcher_native_exit'] == 1 and caller['caller_error'] is None and not caller['secondary']
result = read(e / 'result.json')
assert result['status'] == 'STOPPED' and result['first_cause']['stage'] == 'build-cli'
native = read(e / 'build-cli.invocation.json')
assert native['actual_exit'] == 1 and native['result']['actual_exit'] == 1
child = native['result']
assert child['error'] is None and child['timed_out'] is False
assert child['debug_capture']['complete'] is True
cleanup = child['job_cleanup']
assert cleanup['job_idle_confirmed'] is True and cleanup['active_processes_last_observed'] == 0
assert cleanup['explicit_owned_handle_count'] == 284 and cleanup['explicit_owned_handles_remaining'] == 0
assert cleanup['errors'] == []
assert result['native_calls'] == 6 and result['cases'] == [] and len(result['NOT_RUN']) == 2
assert read(e / 'go-list.invocation.json')['actual_exit'] == 0
canon = []
grant = read(Path(scope['new_authorization_root']) / 'authorization.execute.json')
for row in grant['canonical_copies']:
    actual = pin(ROOT / row['canonical_path'])
    assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
    canon.append(actual)
closed = {
    'schema': 'researchos.root-actual-launch-completion.v1', 'actor': 'codex:/root',
    'actual_initial_tool_chunk': tool['initial']['chunk_id'], 'actual_session_id': tool['initial']['session_id'],
    'actual_completion_tool_chunk': final['chunk_id'], 'actual_outer_tool_exit': final['exit_code'],
    'actual_python_caller_exit': int(markers[0]), 'actual_launcher_native_exit': 1,
    'actual_inner_python_native_exit': read(l / 'completed.json')['actual_inner_native_exit'],
    'actual_go_build_exit': child['actual_exit'],
    'origin_recorded_actual_stage_native_exit': result['first_cause']['actual_stage_native_exit'],
    'origin_null_preserved': result['first_cause']['actual_stage_native_exit'] is None,
    'first_underlying_stage': 'build-cli', 'primary_diagnostic_cause': None,
    'underlying_failure_count': 1, 'nested_exit_propagations_are_not_new_origins': True,
    'source_scope_ref': pin(OUT / 'scope_registration.json'),
    'caller_ref': pin(OUT / 'root-launch-once.v2.py'),
    'caller_invocation_ref': pin(OUT / 'root-launch.invocation.json'),
    'tool_observation_ref': pin(OUT / 'root-launch.tool-observations.json'),
    'first_origin_ref': pin(e / 'failure.origin.json'),
    'executor_result_ref': pin(e / 'result.json'), 'executor_manifest_ref': pin(e / 'manifest.json'),
    'launcher_completion_ref': pin(l / 'completed.json'), 'launcher_manifest_ref': pin(l / 'manifest.json'),
    'build_invocation_ref': pin(e / 'build-cli.invocation.json'),
    'build_stdout_ref': pin(e / 'build-cli.stdout.raw'), 'build_stderr_ref': pin(e / 'build-cli.stderr.raw'),
    'closed_graph_ref': pin(e / 'go-graph.actual.json'),
    'go_list_exit': 0, 'debug_capture_complete': True, 'job_idle_confirmed': True,
    'actual_owned_handles_closed': 284, 'actual_owned_handles_remaining': 0,
    'canonical_refs_at_completion': canon, 'canonical_changed': False,
    'cases': [{'case_id': name, 'launch_attempted': False, 'status': 'NOT_STARTED', 'qualification': 'NOT_RUN'} for name in result['NOT_RUN']],
    'native_calls': 6, 'SDK_Model_Node_external_paid_calls': 0,
    'registered_origin_count': 450, 'late_pending_before_execution_failure': 8,
    'observed_origin_count_after_single_execution_failure': 459,
    'separately_captured_outer_native_raw': False,
    'caller_OS_lifecycle_qualification': False, 'fresh_compile_qualification': False,
    'source_acceptance': False, 'formal_increment': 0, 'automatic_retry': False, 'counter_reset': False
}
save('root-launch.outer-completion.json', closed)
members = [pin(path) for path in sorted(OUT.glob('root-launch*')) if path.is_file()]
members += [pin(OUT / name) for name in ('root-caller-preparation.json', 'prepare-root-caller.py', 'retain-late-origins.py', 'late-origins.capture.json', 'failure-origin.collaboration-source-map-limit.json', 'failure-origin.a76746.json', 'close-root-launch-observation.py')]
save('root-launch.closed.manifest.json', {'schema': 'researchos.root-launch-closure-manifest.v1', 'actor': 'codex:/root', 'members': members, 'original_registration_manifest_unchanged': True, 'case_acceptance': 0, 'formal_increment': 0})
print(json.dumps({'completion_ref': pin(OUT / 'root-launch.outer-completion.json'), 'manifest_ref': pin(OUT / 'root-launch.closed.manifest.json'), 'observed_origin_count': 459, 'case_acceptance': 0}, ensure_ascii=False))
