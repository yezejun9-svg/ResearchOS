"""Seal actual failed once-only execution; retain compile successes separately."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).absolute().parent
sys.dont_write_bytecode = True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode

def pin(path):
    path = Path(path).absolute()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def read(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

scope = read(OUT / 'scope_registration.json')
assert pin(OUT / 'scope_registration.json')['sha256'] == '320fef447b526c1696075c9ae11fe8439d582d893239ed659c486b21562f5137'
executor, launcher = Path(scope['new_output_root']), Path(scope['new_wrapper_root'])
tools = read(OUT / 'root-launch.tool-observations.json')
final = tools['final']
assert final['chunk_id'] == '257165' and final['exit_code'] == 1
markers = re.findall(r'^PythonNativeExit=([0-9]+)\s*$', final['output'], flags=re.MULTILINE)
assert markers == ['1']
caller = read(OUT / 'root-launch.invocation.json')
assert caller['actual_launcher_native_exit'] == 1 and caller['caller_error'] is None and caller['secondary'] == []
result = read(executor / 'result.json')
cause = result['first_cause']
assert result['status'] == 'STOPPED' and cause['stage'] == 'case-00'
assert cause['actual_stage_native_exit'] is None
assert result['cases'] == [] and result['NOT_RUN'] == ['real-existing-self-send'] and result['native_calls'] == 10
child = cause['last_child_result']
assert child['actual_exit'] == 3758097160 and child['debug_capture']['complete'] is False
cleanup = child['job_cleanup']
assert cleanup['termination_requested'] is True and cleanup['termination_code_requested'] == child['actual_exit']
assert cleanup['job_idle_confirmed'] is True and cleanup['explicit_owned_handles_remaining'] == 0
compilers = []
for stage in ('build-cli', 'build-test'):
    native = read(executor / (stage + '.invocation.json'))
    owned = native['result']
    assert native['actual_exit'] == 0 and owned['actual_exit'] == 0 and owned['error'] is None
    assert owned['timed_out'] is False and owned['debug_capture']['complete'] is True
    assert owned['job_cleanup']['job_idle_confirmed'] is True
    assert owned['job_cleanup']['explicit_owned_handles_remaining'] == 0 and owned['job_cleanup']['errors'] == []
    compilers.append({'stage': stage, 'actual_exit': native['actual_exit'],
        'invocation_ref': pin(executor / (stage + '.invocation.json')),
        'stdout_ref': pin(executor / (stage + '.stdout.raw')),
        'stderr_ref': pin(executor / (stage + '.stderr.raw')),
        'debug_capture_complete': True, 'job_idle_confirmed': True,
        'owned_handles_remaining': 0, 'independent_qualification': 'PENDING'})
grant_path = Path(scope['new_authorization_root']) / 'authorization.execute.json'
grant = read(grant_path)
assert pin(grant_path)['sha256'] == '4b7ba306f378ef9a736619e36ec70e5a1c5d614481c069dedab01efdad841ac8'
canon = []
for row in grant['canonical_copies']:
    actual = pin(ROOT / row['canonical_path'])
    assert actual['sha256'] == row['ref']['sha256'] and actual['bytes'] == row['ref']['bytes']
    canon.append(actual)
closed = {
    'schema': 'researchos.root-actual-launch-completion.v1', 'actor': 'codex:/root',
    'actual_initial_tool_chunk': tools['initial']['chunk_id'], 'actual_session_id': tools['initial']['session_id'],
    'actual_completion_tool_chunk': final['chunk_id'], 'actual_outer_tool_exit': final['exit_code'],
    'actual_python_caller_exit': int(markers[0]), 'actual_launcher_native_exit': caller['actual_launcher_native_exit'],
    'actual_inner_python_native_exit': read(launcher / 'completed.json')['actual_inner_native_exit'],
    'first_underlying_stage': cause['stage'], 'primary_diagnostic_cause': child['error'],
    'actual_case_primary_exit': child['actual_exit'], 'actual_case_exit_was_requested_termination': True,
    'origin_recorded_actual_stage_native_exit': cause['actual_stage_native_exit'], 'origin_null_preserved': True,
    'underlying_failure_count': 1, 'nested_exit_propagations_are_not_new_origins': True,
    'source_scope_ref': pin(OUT / 'scope_registration.json'), 'caller_ref': pin(OUT / 'root-launch-once.v2.py'),
    'caller_invocation_ref': pin(OUT / 'root-launch.invocation.json'),
    'tool_observation_ref': pin(OUT / 'root-launch.tool-observations.json'),
    'first_origin_ref': pin(executor / 'failure.origin.json'),
    'executor_result_ref': pin(executor / 'result.json'), 'executor_manifest_ref': pin(executor / 'manifest.json'),
    'launcher_completion_ref': pin(launcher / 'completed.json'), 'launcher_manifest_ref': pin(launcher / 'manifest.json'),
    'case_invocation_ref': pin(executor / 'case-00.invocation.json'),
    'case_stdout_ref': pin(executor / 'case-00.stdout.raw'), 'case_stderr_ref': pin(executor / 'case-00.stderr.raw'),
    'closed_graph_ref': pin(executor / 'go-graph.actual.json'), 'compiler_observations': compilers,
    'case_debug_capture_complete': False, 'case_job_idle_confirmed': cleanup['job_idle_confirmed'],
    'actual_case_owned_handles_closed': cleanup['explicit_owned_handle_close_successes'],
    'actual_case_owned_handles_remaining': cleanup['explicit_owned_handles_remaining'],
    'actual_case_cleanup_errors': cleanup['errors'], 'canonical_refs_at_completion': canon,
    'canonical_changed': False, 'cases': [
        {'case_id': 'real-existing-open-readonly', 'launch_attempted': True, 'status': 'STOPPED_DURING_NATIVE_CAPTURE', 'qualification': 'WITHHELD'},
        {'case_id': 'real-existing-self-send', 'launch_attempted': False, 'status': 'NOT_STARTED', 'qualification': 'NOT_RUN'}],
    'native_calls': result['native_calls'], 'SDK_MODEL_external_paid': result['SDK_MODEL_external_paid'],
    'registered_origin_count': 459, 'known_late_pending_before_execution_failure': 9,
    'observed_origin_count_after_single_execution_failure_at_closure': 469,
    'separately_captured_outer_native_raw': False, 'caller_OS_lifecycle_qualification': False,
    'fresh_compile_qualification': False, 'complete_current43_source_validation': False,
    'source_acceptance': False, 'formal_increment': 0, 'automatic_retry': False, 'counter_reset': False
}
save('root-launch.outer-completion.json', closed)
members = [pin(path) for path in sorted(OUT.glob('root-launch*')) if path.is_file()]
members += [pin(OUT / name) for name in ('root-caller-preparation.json', 'prepare-root-caller.py',
    'close-root-launch-observation.py', 'root-metadata.tool-observations.after-grant.json')]
save('root-launch.closed.manifest.json', {'schema': 'researchos.root-launch-closure-manifest.v1',
    'actor': 'codex:/root', 'members': members, 'original_registration_manifest_unchanged': True,
    'case_acceptance': 0, 'formal_increment': 0})
print(json.dumps({'completion_ref': pin(OUT / 'root-launch.outer-completion.json'),
    'manifest_ref': pin(OUT / 'root-launch.closed.manifest.json'), 'case_acceptance': 0}, ensure_ascii=False))
