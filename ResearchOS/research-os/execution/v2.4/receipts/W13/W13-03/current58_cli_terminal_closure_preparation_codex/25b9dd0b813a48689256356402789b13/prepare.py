"""Pure IO/AST preparation; never imports or executes the candidate."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
P05 = ROOT / 'execution/v2.4/receipts/W05/W05-99'
OLD = P05 / 'integration_codex/cli43-fresh-held2-r331-c4f309c5528f5d42be5e7eeb146a20aa'
QUAL = P05 / 'cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/qualification.json'
CALLER = ROOT / 'execution/v2.4/receipts/W13/W13-03/current58_cli2_root_caller_preparation_codex/b8e3c81d266b43a89ca6810f044acb04/root-launch-once.current58.proposed.py'
INPUTS = [OLD / n for n in ('close-root-launch-observation.v5.py', 'root-launch.closed.manifest.json', 'completion-reader-preparation.json', 'root-launch.tool-observations.json', 'root-launch.invocation.json')] + [QUAL, CALLER]

def ref(p):
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    with (OUT / name).open('xb') as f:
        f.write(raw)

before = [ref(p) for p in INPUTS]
old = INPUTS[0].read_bytes()
assert hashlib.sha256(old).hexdigest() == '9746d725c5441a410fd7d4b737c190c13542d9ffd5001c890a4739d9165c9c69'
text = old.decode('utf-8')
prefix_end = text.index('child = cause.get(')
prefix = r'''"""Record terminal Root evidence; this does not issue test qualification."""
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
    assert pin(row['path']) == row
    return READS[row['path']]

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
executor_rows = full_manifest(q['executor_manifest_ref'], executor)
launcher_rows = full_manifest(q['launcher_manifest_ref'], launcher)
caller_root = bounded(q['caller_output_root'])
assert caller_root == ROOT / 'execution/v2.4/receipts/W05/W05-99/cli58_root_launch_once_codex/b9a9db830bf140be90dd2158671e7683'
verified(q['caller_ref'])
assert q['caller_ref']['sha256'] == '766a838c12a641b2c3bf249e648d71706ac45edb027a1b1bfc66261af06b84bb'
grant = decode(verified(q['grant_ref']))
assert Path(q['grant_ref']['path']) == bounded(scope['new_authorization_root']) / 'authorization.execute.json'
assert grant['scope_ref'] == q['scope_ref']
intent = decode(verified(q['caller_intent_ref']))
caller = decode(verified(q['caller_invocation_ref']))
assert Path(q['caller_intent_ref']['path']) == caller_root / 'root-launch.intent.json'
assert Path(q['caller_invocation_ref']['path']) == caller_root / 'root-launch.invocation.json'
for item in (intent, caller):
    assert item['scope_ref'] == q['scope_ref'] and item['grant_ref'] == q['grant_ref']
    assert item['automatic_retry'] is False and item['counter_reset'] is False
    assert item['caller_OS_lifecycle_qualification'] is False
assert intent['caller_ref'] == q['caller_ref'] and Path(intent['cwd']) == ROOT
expected_argv = [scope['python_ref']['path'], '-I', '-S', '-X', 'utf8', scope['launcher_ref']['path'],
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
'''
candidate = prefix + text[prefix_end:]
start = candidate.index("grant_path = Path(scope['new_authorization_root'])")
end = candidate.index('local_failure_count =', start)
candidate = candidate[:start] + """canon = []
for row in grant['canonical_copies']:
    verified(row['ref'])
    canon.append(row['ref'])
registered_count = scope['expected_registration'][2]
assert type(registered_count) is int and registered_count >= 0
""" + candidate[end:]
for old_s, new_s in [
    ("'actual_python_caller_exit': int(markers[0])", "'actual_python_caller_exit': python_native_exit"),
    ("pin(OUT / 'scope_registration.json')", "q['scope_ref']"),
    ("'grant_ref': pin(grant_path)", "'grant_ref': q['grant_ref']"),
    ("pin(OUT / 'root-launch-once.v2.py')", "q['caller_ref']"),
    ("pin(OUT / 'root-launch.invocation.json')", "q['caller_invocation_ref']"),
    ("pin(OUT / 'root-launch.tool-observations.json')", "q['tool_observation_ref']"),
    ("'canonical_refs_at_completion': canon, 'canonical_changed': False", "'canonical_refs_at_completion': None, 'canonical_changed': None,\n    'authorization_canonical_copy_refs': canon, 'completion_live_canonical_observed': False"),
    ("'registered_origin_count': 509", "'registered_origin_count': registered_count"),
    ("args.known_pending_origins", "q['known_pending_origins']"),
    ("'observed_origin_count_at_closure': 509 +", "'observed_origin_count_at_closure': registered_count +"),
]:
    assert old_s in candidate, old_s
    candidate = candidate.replace(old_s, new_s)
end = candidate.index("save('root-launch.outer-completion.json', closed)")
candidate = candidate[:end] + r'''closed.update({
    'run_uuid': q['run_uuid'], 'source_commit': q['source_commit'], 'closure_request_ref': request_ref,
    'terminal_action_input_ref': q['terminal_action_input_ref'], 'terminal_tool_result_ref': q['terminal_tool_result_ref'],
    'closure_kind': 'TERMINAL_EVIDENCE_RECORDED_NOT_QUALIFICATION',
    'complete_current58_source_validation': False, 'case_qualification': False,
    'executor_manifest_all_members_verified': True, 'launcher_manifest_all_members_verified': True,
    'actual_initial_input_original_payload': tools['initial_input'],
    'actual_terminal_action_original_payload': actions[-1]
})
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
'''
new = candidate.encode('utf-8')
ast.parse(new)
save('close-root-launch.current58.proposed.py', new)
old_tree, new_tree = ast.parse(old), ast.parse(new)
preserved = []
for node in old_tree.body:
    if isinstance(node, ast.FunctionDef):
        matches = [x for x in new_tree.body if isinstance(x, ast.FunctionDef) and x.name == node.name]
        if matches and ast.dump(node, include_attributes=False) == ast.dump(matches[0], include_attributes=False):
            preserved.append(node.name)
save('source.diff', ''.join(difflib.unified_diff(text.splitlines(True), candidate.splitlines(True), fromfile='old.v5.py', tofile='current58.proposed.py')).encode())
edits = []
for op, a, b, c, d in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if op != 'equal':
        edits.append({'old_start': a, 'old_end': b, 'new_start': c, 'new_end': d, 'old_hex': old[a:b].hex(), 'new_hex': new[c:d].hex()})
inverse = new
for e in reversed(edits):
    assert inverse[e['new_start']:e['new_end']] == bytes.fromhex(e['new_hex'])
    inverse = inverse[:e['new_start']] + bytes.fromhex(e['old_hex']) + inverse[e['new_end']:]
assert inverse == old
save('whole-inverse.json', {'old_ref': before[0], 'new_ref': ref(OUT/'close-root-launch.current58.proposed.py'), 'edits': edits, 'whole_byte_inverse_equal': True})
save('inputs.before.json', before)
after = [ref(p) for p in INPUTS]
assert before == after
save('inputs.after.json', after)
save('static-audit.json', {'AST_parse': True, 'candidate_imported_or_executed': False, 'whole_byte_inverse_equal': True, 'unchanged_function_AST': preserved, 'input_count': len(before), 'input_drift_count': 0, 'native_product_calls': 0, 'new_failure_origins': []})
save('request.proposed.json', {'schema': 'researchos.current58-root-terminal-closure-request.v1', 'run_uuid': '0e298790cd484ec9ba319a379e7e34ed', 'source_commit': 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7', 'initial_tool_chunk': 'ad4547', 'initial_session_id': 78573, 'known_pending_origins': None, 'scope_ref': None, 'grant_ref': None, 'caller_ref': None, 'caller_output_root': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/cli58_root_launch_once_codex/b9a9db830bf140be90dd2158671e7683', 'caller_intent_ref': None, 'caller_invocation_ref': None, 'tool_observation_ref': None, 'terminal_action_input_ref': None, 'terminal_tool_result_ref': None, 'actual_initial_input': None, 'executor_manifest_ref': None, 'launcher_manifest_ref': None, 'additional_sealed_refs': None, 'new_closure_output_root': None})
save('contract.json', {'status': 'SOURCE_PREPARATION_ONLY_NOT_RUN', 'old_producer_ref': before[0], 'old_wire': {'completion_schema': 'researchos.root-actual-launch-completion.v2', 'manifest_schema': 'researchos.root-launch-closure-manifest.v2', 'members_field': 'members', 'old_member_count': 11, 'new_count': 'actual verified union, never fixed11'}, 'invocation': 'PINNED_PYTHON -I -S -X utf8 NEW_PRODUCER ABS_ROOT_REQUEST REQUEST_SHA', 'Root_required': ['Actual ended tool session: initial input/result, each poll input/result, last action input and result independent raw refs; do not fabricate raw or markers.', 'Actual scope/grant/caller pins, request SHA, complete E/L files manifests after closure, Root original caller intent/invocation/stdout/stderr.', 'additional_sealed_refs must include actual current controller source review, caller source review, Root registration/stage-before-launch closed refs and any supplemental original captures; Root fixes this set before using producer.', 'Root must create only the shared closure parent after review; producer owns exclusive UUID leaf.', 'Root separately retains any metadata-producer exception/raw traceback; this script never retries or writes running input directories.'], 'boundaries': ['No live canonical reads or changes; authorization copies preserved and current canonical status explicitly NULL.', 'No qualification from exit0. Actual test/case/Go/OS evidence remains independently reviewed by W05.', 'Actual Python native exit derives only from captured explicit marker; absent marker is NULL.', 'Underlying failure payload retained; nested propagation not new origin; pending count supplied by Root and does not update canonical.', 'caller_OS_lifecycle_qualification remains false.', 'Tool input-response linkage is evidence binding, not cryptographic platform attestation. Root must provide authentic raw captures.', 'Failure without complete sealed E/L manifests remains OPEN; no successful closure synthesized.'], 'future_controls_NOT_RUN': ['complete actual terminal evidence', 'terminal session mismatch', 'unrelated exit0 response', 'missing marker retains NULL', 'manifest member drift/missing/extra', 'failed launcher preserves original cause', 'old a510 scope rejected', 'existing output rejected'], 'current_dynamic_outputs_read': False})
print(json.dumps({'namespace': str(OUT), 'candidate_ref': ref(OUT/'close-root-launch.current58.proposed.py'), 'AST_only': True, 'target_calls': 0}, ensure_ascii=False))
