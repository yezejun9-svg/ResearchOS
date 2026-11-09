"""Record terminal Root evidence; this does not issue test qualification."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = None
sys.dont_write_bytecode = True
assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode
parser = argparse.ArgumentParser()
parser.add_argument('request_path')
parser.add_argument('request_sha256')
args = parser.parse_args()
READS = {}

def bounded(value):
    p = Path(value)
    assert p.is_absolute() and '..' not in p.parts and p.is_relative_to(ROOT) and p != ROOT
    assert str(p.resolve()) == str(p)
    for ancestor in (p, *p.parents):
        if ancestor.exists():
            assert not ancestor.is_symlink() and not (ancestor.lstat().st_file_attributes & 0x400)
        if ancestor == ROOT:
            break
    return p

def pin(path):
    path = bounded(str(Path(path).absolute()))
    raw = path.read_bytes()
    if str(path) in READS:
        assert READS[str(path)] == raw, 'Input drift'
    READS[str(path)] = raw
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def verified(row):
    assert type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}
    assert type(row['bytes']) is int and row['bytes'] >= 0
    path = Path(row['path'])
    if not path.is_absolute():
        assert path.as_posix() == row['path'] and '..' not in path.parts
        path = ROOT / path
    actual = pin(path)
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
    return READS[actual['path']]

def unique(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, 'Duplicate JSON key'
        result[key] = value
    return result

def decode(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def read(path):
    row = pin(path)
    return decode(READS[row['path']])

def optional_pin(path):
    return pin(path) if Path(path).is_file() else None

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))

def full_manifest(row, directory):
    doc = decode(verified(row))
    rows = doc['files']
    assert type(rows) is list and rows and doc['count'] == len(rows) and doc['excluded_only_self'] is True
    paths = set()
    for entry in rows:
        path = bounded(entry['path'])
        assert path.is_relative_to(directory) and path != directory and str(path) not in paths
        paths.add(str(path))
        verified(entry)
    actual = set()
    for path in directory.rglob('*'):
        bounded(str(path))
        if path.is_file() and path != Path(row['path']):
            actual.add(str(path))
    assert actual == paths, 'Manifest membership mismatch'
    return rows

request_path = bounded(args.request_path)
request_ref = pin(request_path)
assert request_ref['sha256'] == args.request_sha256
q = decode(READS[str(request_path)])
assert q['schema'] == 'researchos.current58-root-terminal-closure-request.v1'
assert q['run_uuid'] == '0e298790cd484ec9ba319a379e7e34ed'
assert q['source_commit'] == 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
assert q['initial_tool_chunk'] == 'ad4547' and q['initial_session_id'] == 78573
assert type(q['known_pending_origins']) is int and q['known_pending_origins'] >= 0
scope = decode(verified(q['scope_ref']))
assert q['scope_ref']['sha256'] == '459f00078d742e754631294d17210329280c2e1fec0cf7925b94fb4333c3bc84'
assert scope['source_commit'] == q['source_commit'] and scope['run_uuid'] == q['run_uuid']
executor, launcher = bounded(scope['new_output_root']), bounded(scope['new_wrapper_root'])
assert Path(q['executor_manifest_ref']['path']).parent == executor
assert Path(q['launcher_manifest_ref']['path']).parent == launcher
caller_root = bounded(q['caller_output_root'])
assert caller_root == ROOT / 'execution/v2.4/receipts/W05/W05-99/cli58_root_launch_once_codex/b9a9db830bf140be90dd2158671e7683'
verified(q['caller_ref'])
assert q['caller_ref']['sha256'] == '766a838c12a641b2c3bf249e648d71706ac45edb027a1b1bfc66261af06b84bb'
grant = decode(verified(q['grant_ref']))
assert Path(q['grant_ref']['path']) == bounded(scope['new_authorization_root']) / 'authorization.execute.json'
assert verified(grant['scope_ref']) == verified(q['scope_ref'])
assert (ROOT / grant['scope_ref']['path']).resolve() == Path(q['scope_ref']['path']).resolve()
assert grant['binding']['run_uuid'] == q['run_uuid'] and grant['binding']['source_commit'] == q['source_commit']
intent = decode(verified(q['caller_intent_ref']))
caller = decode(verified(q['caller_invocation_ref']))
assert Path(q['caller_intent_ref']['path']) == caller_root / 'root-launch.intent.json'
assert Path(q['caller_invocation_ref']['path']) == caller_root / 'root-launch.invocation.json'
for item in (intent, caller):
    assert item['scope_ref'] == q['scope_ref'] and item['grant_ref'] == q['grant_ref']
    assert item['automatic_retry'] is False and item['counter_reset'] is False
    assert item['caller_OS_lifecycle_qualification'] is False
assert intent['caller_ref'] == q['caller_ref'] and Path(intent['cwd']) == ROOT
expected_argv = ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I', '-S', '-X', 'utf8', scope['launcher_ref']['path'],
                 q['scope_ref']['path'], q['scope_ref']['sha256'], q['grant_ref']['path'], q['grant_ref']['sha256']]
assert intent['argv'] == expected_argv
for channel in ('stdout', 'stderr'):
    item = caller[channel + '_ref']
    if item is not None:
        assert Path(item['path']) == caller_root / ('root-launch.' + channel + '.raw')
        verified(item)
tools = decode(verified(q['tool_observation_ref']))
assert tools['initial']['chunk_id'] == q['initial_tool_chunk']
assert tools['initial']['session_id'] == q['initial_session_id']
assert tools['initial_input'] == q['actual_initial_input']
actions = tools['poll_actions']
assert type(actions) is list and actions
for index, action in enumerate(actions):
    assert action['input']['session_id'] == q['initial_session_id'] and action['input'].get('chars', '') == ''
    if index < len(actions) - 1:
        assert action['result'].get('session_id') == q['initial_session_id'] and 'exit_code' not in action['result']
assert tools['final'] == actions[-1]['result']
final = tools['final']
assert type(final['exit_code']) is int and 'session_id' not in final
assert decode(verified(q['terminal_action_input_ref'])) == actions[-1]['input']
assert decode(verified(q['terminal_tool_result_ref'])) == final
assert tools['automatic_retry'] is False and tools['counter_reset'] is False
executor_rows = full_manifest(q['executor_manifest_ref'], executor)
launcher_rows = full_manifest(q['launcher_manifest_ref'], launcher)
markers = re.findall(r'^PythonNativeExit=([0-9]+)\s*$', final['output'], flags=re.MULTILINE)
assert len(markers) <= 1
python_native_exit = int(markers[0]) if markers else None
if python_native_exit is not None:
    assert python_native_exit == final['exit_code']
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
canon = []
for row in grant['canonical_copies']:
    verified(row['ref'])
    canon.append(row['ref'])
registered_count = scope['expected_registration'][2]
assert type(registered_count) is int and registered_count >= 0
local_failure_count = 1 if origin_ref is not None else 0
closed = {
    'schema': 'researchos.root-actual-launch-completion.v2', 'actor': 'codex:/root',
    'actual_initial_tool_chunk': tools['initial']['chunk_id'], 'actual_session_id': tools['initial'].get('session_id'),
    'actual_completion_tool_chunk': final['chunk_id'], 'actual_outer_tool_exit': final['exit_code'],
    'actual_python_caller_exit': python_native_exit, 'actual_launcher_native_exit': caller['actual_launcher_native_exit'],
    'actual_inner_python_native_exit': completed.get('actual_inner_native_exit') if completed is not None else None,
    'caller_error': caller['caller_error'], 'caller_secondary': caller['secondary'],
    'first_cause_original_payload': cause, 'last_child_original_result': child,
    'underlying_local_failure_count': local_failure_count,
    'nested_exit_propagations_are_not_new_origins': True,
    'source_scope_ref': q['scope_ref'], 'grant_ref': q['grant_ref'],
    'caller_ref': q['caller_ref'], 'caller_invocation_ref': q['caller_invocation_ref'],
    'tool_observation_ref': q['tool_observation_ref'],
    'first_origin_ref': origin_ref, 'executor_result_ref': optional_pin(executor / 'result.json'),
    'executor_manifest_ref': optional_pin(executor / 'manifest.json'),
    'launcher_completion_ref': optional_pin(launcher / 'completed.json'),
    'launcher_manifest_ref': optional_pin(launcher / 'manifest.json'),
    'closed_graph_ref': optional_pin(executor / 'go-graph.actual.json'),
    'compiled_closure_ref': optional_pin(executor / 'compiled-closure.json'),
    'test2json_artifact_ref': optional_pin(executor / 'test2json-artifact.finally.json'),
    'compiler_observations': compiler_observations,
    'canonical_refs_at_completion': None, 'canonical_changed': None,
    'authorization_canonical_copy_refs': canon, 'completion_live_canonical_observed': False,
    'actual_result_status': result['status'] if result is not None else None,
    'actual_case_roster_original_payload': result.get('case_roster') if result is not None else None,
    'actual_case_results_original_payload': result['cases'] if result is not None else None,
    'actual_NOT_RUN_original_payload': result['NOT_RUN'] if result is not None else None,
    'native_calls': result['native_calls'] if result is not None else None,
    'SDK_MODEL_external_paid': result['SDK_MODEL_external_paid'] if result is not None else None,
    'registered_origin_count': registered_count, 'known_late_pending_outside_fixed_cut': q['known_pending_origins'],
    'observed_origin_count_at_closure': registered_count + q['known_pending_origins'] + local_failure_count,
    'separately_captured_outer_native_raw': False, 'caller_OS_lifecycle_qualification': False,
    'fresh_compile_qualification': False, 'complete_current43_source_validation': False,
    'independent_qualification': 'PENDING', 'source_acceptance': False,
    'formal_increment': 0, 'automatic_retry': False, 'counter_reset': False
}
closed.update({
    'run_uuid': q['run_uuid'], 'source_commit': q['source_commit'], 'closure_request_ref': request_ref,
    'terminal_action_input_ref': q['terminal_action_input_ref'], 'terminal_tool_result_ref': q['terminal_tool_result_ref'],
    'closure_kind': 'TERMINAL_EVIDENCE_RECORDED_NOT_QUALIFICATION',
    'complete_current58_source_validation': False, 'case_qualification': False,
    'executor_manifest_all_members_verified': True, 'launcher_manifest_all_members_verified': True,
    'actual_initial_input_original_payload': tools['initial_input'],
    'actual_terminal_action_original_payload': actions[-1]
})
assert type(q['additional_sealed_refs']) is list and q['additional_sealed_refs']
for entry in q['additional_sealed_refs']:
    verified(entry)
OUT = bounded(q['new_closure_output_root'])
parent = ROOT / 'execution/v2.4/receipts/W13/W13-03/current58_cli_terminal_closure_codex'
assert OUT.parent == parent and re.fullmatch('[0-9a-f]{32}', OUT.name) and not OUT.exists()
assert parent.is_dir() and not OUT.is_relative_to(Path(__file__).resolve().parent)
for name, original in READS.items():
    assert Path(name).read_bytes() == original, 'Input drift before publication'
OUT.mkdir(exist_ok=False)
save('root-launch.outer-completion.json', closed)
members = [{'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
           for name, raw in sorted(READS.items())]
members.append(pin(__file__))
members.append(pin(OUT / 'root-launch.outer-completion.json'))
by_path = {row['path']: row for row in members}
for name, original in READS.items():
    assert Path(name).read_bytes() == original, 'Input drift during publication'
save('root-launch.closed.manifest.json', {'schema': 'researchos.root-launch-closure-manifest.v2',
    'actor': 'codex:/root', 'members': [by_path[name] for name in sorted(by_path)],
    'original_registration_manifests_unchanged': True, 'source_acceptance': False, 'formal_increment': 0})
print(json.dumps({'completion_ref': pin(OUT / 'root-launch.outer-completion.json'),
    'manifest_ref': pin(OUT / 'root-launch.closed.manifest.json'), 'actual_outer_exit': final['exit_code'],
    'local_underlying_failures': local_failure_count, 'independent_qualification': 'PENDING',
    'formal_increment': 0}, ensure_ascii=False))
