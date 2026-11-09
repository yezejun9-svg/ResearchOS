"""Continue only the unreached FREV Source tail; never execute review_actual."""
import ast
import copy
import hashlib
import json
import ntpath
import re
import sys
import traceback
import types
from pathlib import Path, PurePosixPath, PureWindowsPath

HERE = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
BASE = R / 'execution/v2.4/receipts/W09/W09-99/w09_br6_formal_actual_review_codex/prepare-20261010-02'
S = R / 'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
BASE_SOURCE = {'path': str(BASE / 'br6_actual_review.v3.source.py'), 'sha256': '08cccda8887888b8c82dc8f7fb9e850aacd24871ca327f1a3c1151baa4a3c9da', 'bytes': 19209}
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
BINDING_REF = {'path': str(S / 'original1235.fixed-actual.binding.root.json'), 'sha256': '96f279e4b9bf5165456156511d5d04fc754061064b4b78b37e08d4b5ce659cb9', 'bytes': 1617}
RAW_REF = {'path': str(S / 'original1235.fixed-actual.raw.root.jsonl'), 'sha256': 'a6e48da5ad536fdf78e3d16d843fbeb06b578f59f9442e3cc63e1368c889c885', 'bytes': 28223}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw)}

def checked(reference):
    raw = Path(reference['path']).read_bytes()
    if len(raw) != reference['bytes'] or digest(raw) != reference['sha256']:
        raise ValueError('Source tail input pin differs')
    return raw

def publish(name, obj):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable new Source member exists: ' + name)
    raw = obj if isinstance(obj, bytes) else (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

guard = None
failure = None
result = {}
tail_checks = []
try:
    contract_ref = ref(HERE / 'input-contract.json')
    contract = json.loads(checked(contract_ref))
    candidate_ref = contract['caller_ref']
    basis_ref = contract['basis_ref']
    old_failure_ref = ref(HERE / 'construction.failure.json')
    old_constructor_ref = ref(HERE / 'construct_source_revision.py')
    synthetic_ref = ref(HERE / 'synthetic.bundle.control.json')
    old_guard_ref = ref(HERE / 'SourceGuard.closed.json')
    original_io_ref = ref(HERE / 'original-dde746.actual-tools.reencoded.json')
    inputs = [contract_ref, candidate_ref, basis_ref, BASE_SOURCE, old_failure_ref, old_constructor_ref, synthetic_ref, old_guard_ref, original_io_ref, BINDING_REF, RAW_REF, GUARD_REF]
    guard_module = types.ModuleType('frev_selfref_tail_guard')
    guard_module.__file__ = GUARD_REF['path']
    sys.modules[guard_module.__name__] = guard_module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), guard_module.__dict__)
    guard = guard_module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire(inputs)
    def held(reference):
        return bytes(guard.get_buffer(reference['path']))
    failed = json.loads(held(old_failure_ref))
    previous = failed['failure']['successful_control_prefix']
    successful_prefix = previous[:4]
    if len(previous) != 5 or not all(item['passed'] is True for item in successful_prefix) or previous[4]['passed'] is not False:
        raise ValueError('existing original1235 control prefix differs')
    source = held(candidate_ref)
    old = held(BASE_SOURCE)
    new_tree = ast.parse(source.decode('utf-8'))
    old_tree = ast.parse(old.decode('utf-8'))
    nodes = {node.name: node for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    old_nodes = {node.name: node for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    actual = nodes['review_actual']
    try_node = next(node for node in actual.body if isinstance(node, ast.Try))
    admission_body = []
    for node in try_node.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'context_path' for target in node.targets):
            break
        admission_body.append(copy.deepcopy(node))
    admission_body.append(ast.Return(value=ast.Name(id='authorized', ctx=ast.Load())))
    selected = [copy.deepcopy(nodes[name]) for name in ['absolute_ref', 'same_ref', 'need']]
    args = ast.arguments(posonlyargs=[], args=[ast.arg(arg='bundle'), ast.arg(arg='input_ref')], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
    selected.append(ast.FunctionDef(name='actual_resource_admission_prefix', args=args, body=admission_body, decorator_list=[]))
    mock_guard = types.SimpleNamespace(_canonical=lambda value: ntpath.normcase(ntpath.normpath(str(value))))
    environment = {'Path': Path, 'ROOT': R, 'guard_module': mock_guard}
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), '<actual Source AST finite admission tail>', 'exec'), environment)
    bundle = json.loads(held(synthetic_ref))
    duplicate = copy.deepcopy(bundle)
    duplicate['resource_refs'].append(dict(bundle['consumer_result_ref'], path=bundle['consumer_result_ref']['path'].replace('\\', '/')))
    bad_pin = copy.deepcopy(bundle)
    bad_pin['resource_refs'][0] = dict(bad_pin['resource_refs'][0], sha256='0' * 64)
    if bad_pin['consumer_result_ref']['sha256'] == bad_pin['resource_refs'][0]['sha256']:
        raise ValueError('revised counterexample did not independently replace the resource dict')
    outcomes = []
    for item, expected in [(duplicate, 'RESOURCE_DUPLICATE_PATH'), (bad_pin, 'INPUT_NOT_HELD')]:
        try:
            environment['actual_resource_admission_prefix'](item, synthetic_ref)
        except ValueError as error:
            outcomes.append({'expected': expected, 'observed': str(error), 'passed': str(error) == expected})
        else:
            outcomes.append({'expected': expected, 'observed': 'ACCEPTED', 'passed': False})
    tail_checks.append({'name': 'existing_duplicate_and_required_resource_pin_gates_preserved_revised_fixture', 'passed': all(item['passed'] for item in outcomes), 'outcomes': outcomes, 'synthetic': True, 'actual_review_called': False})
    if not tail_checks[-1]['passed']:
        raise AssertionError(tail_checks[-1]['name'])
    acquires = [node for node in ast.walk(actual) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'guard' and node.func.attr == 'acquire']
    expected = ast.parse('[input_ref, *resources]', mode='eval').body
    passed = len(acquires) == 1 and len(acquires[0].args) == 1 and ast.dump(acquires[0].args[0], include_attributes=False) == ast.dump(expected, include_attributes=False) and basis_ref['sha256'] == '37b0e5a10895881f721ca8867094f915a9b8786ac2334d4599b18961b5d4827e' and contract['input_schema'] == 'researchos.w09-br6-formal-actual-review-input.v1'
    tail_checks.append({'name': 'actual_full_function_guard_set_and_fixed_basis_schema_unchanged', 'passed': passed, 'Guard_input_set': '[input_ref, *resources]', 'actual_review_called': False})
    if not passed:
        raise AssertionError(tail_checks[-1]['name'])
    # Serialize the original successful inverse spans; do not replay prefix controls.
    old_lines = old.splitlines(keepends=True)
    required = next(line for line in old_lines if b'required = [input_ref, bundle[' in line)
    unique = next(line for line in old_lines if b"need(len(authorized) == len(resources), 'RESOURCE_DUPLICATE_PATH')" in line)
    acquire = next(line for line in old_lines if b'guard.acquire(resources)' in line)
    newline = b'\r\n' if unique.endswith(b'\r\n') else b'\n'
    insert = newline.join([b"        input_key = guard_module._canonical(absolute_ref(input_ref)['path'])", b"        need(input_key not in authorized, 'BUNDLE_RESOURCE_SELF_REFERENCE')", b"        authorized[input_key] = input_ref"]) + newline
    spans = [(required, required.replace(b'input_ref, ', b'', 1)), (unique, unique + insert), (acquire, acquire.replace(b'guard.acquire(resources)', b'guard.acquire([input_ref, *resources])'))]
    inverse_ref = publish('exact-inverse.json', {'base_source_ref': BASE_SOURCE, 'candidate_source_ref': candidate_ref, 'complete_byte_inverse': True, 'restored_sha256': BASE_SOURCE['sha256'], 'changed_function_AST': ['review_actual'], 'byte_span_replacements': [{'old_hex': left.hex(), 'new_hex': right.hex()} for left, right in spans], 'proof_is_original_successful_prefix_not_replayed': successful_prefix[0], 'proof_failure_artifact_ref': old_failure_ref, 'unchanged_basis_sha256': basis_ref['sha256']})
    binding = json.loads(held(BINDING_REF))
    raw_lines = held(RAW_REF).splitlines(keepends=True)
    if len(raw_lines) != 3 or [len(line) for line in raw_lines] != binding['source_line_bytes'] or [digest(line) for line in raw_lines] != binding['original_line_sha256']:
        raise ValueError('Root original1235 actual three-line capture differs')
    if binding['original_ordinal'] != 1235 or binding['actual_host_chunk_id'] != 'dde746' or binding['actual_outer_exit'] != 1 or binding['actual_python_exit'] != 1 or binding['actor_id'] != 'codex:/root/backup_regression_resources':
        raise ValueError('Root original1235 identity or observed exits differs')
    origin_ref = publish('failure-origin.1235.json', {'schema': 'researchos.source-original-failure-origin.v1', 'ordinal': 1235, 'actual_host_chunk_id': 'dde746', 'actual_outer_exit': 1, 'actual_python_exit': 1, 'actual_native_exit': None, 'actual_Go_exit': None, 'actual_SQLite_exit': None, 'actual_TP_exit': None, 'actual_dispatcher_exit': None, 'actual_model_exit': None, 'actual_binding_ref': BINDING_REF, 'actual_raw_three_lines_ref': RAW_REF, 'complete_tools_IO_reencoded_ref': original_io_ref, 'failed_constructor_ref': old_constructor_ref, 'failure_ref': old_failure_ref, 'failed_attempt_guard_ref': old_guard_ref, 'cause': 'Source-only negative fixture mutated a deepcopy-preserved shared dict and also changed the expected consumer pin; candidate unchanged', 'original_failure_preserved': True, 'counter_reset': False, 'exact_failed_input_replayed': False, 'product_failure': False})
    result = {'schema': 'researchos.w09-formal-review-self-reference-source-preparation.v1', 'Source_author': 'codex:/root/backup_regression_resources', 'Source_author_backend': '/root/backup_regression_resources', 'author_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084', 'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98', 'caller_ref': candidate_ref, 'contract_ref': contract_ref, 'basis_ref': basis_ref, 'exact_inverse_ref': inverse_ref, 'source_inputs': inputs, 'original1235_ref': origin_ref, 'prior_successful_control_prefix': successful_prefix, 'prior_prefix_not_replayed': True, 'tail_checks': tail_checks, 'new_tail_checks': len(tail_checks), 'total_distinct_passed_controls': len(successful_prefix) + len(tail_checks), 'failed_original_control_retained': previous[4], 'actual_formal_review_called': False, 'Root_stages_Native_Go_SQL_model_TP_dispatcher_calls': 0, 'Main_Canon_Scope_Registry_writes': 0, 'Source_self_acceptance': False, 'independent_Source_review_required': True, 'formal_acceptance': False, 'execution_grant': False}
except BaseException as error:
    failure = {'exception': repr(error), 'traceback': traceback.format_exc(), 'actual_tail_checks': tail_checks}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('tail-SourceGuard.closed.json', closure)
    if failure is not None:
        publish('tail.failure.json', {'failure': failure, 'Source_guard_ref': closure_ref})

if failure is not None:
    print(json.dumps({'failure': failure, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('Source tail guard not closed')
result['Source_guard_ref'] = closure_ref
result['all_guards_closed'] = True
metadata_ref = publish('Source-preparation.json', result)
print(json.dumps({'metadata_ref': metadata_ref, 'caller_ref': result['caller_ref'], 'contract_ref': result['contract_ref'], 'basis_ref': result['basis_ref'], 'exact_inverse_ref': result['exact_inverse_ref'], 'original1235_ref': result['original1235_ref'], 'Source_guard_ref': closure_ref, 'tail_checks_passed': len(tail_checks), 'successful_prefix_not_replayed': 4, 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
