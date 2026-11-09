"""Prepare the minimal FREV input self-reference correction; no actual review."""
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
SOURCE_REF = {'path': str(BASE / 'br6_actual_review.v3.source.py'), 'sha256': '08cccda8887888b8c82dc8f7fb9e850aacd24871ca327f1a3c1151baa4a3c9da', 'bytes': 19209}
CONTRACT_REF = {'path': str(BASE / 'input-contract.v3.json'), 'sha256': '624916dfa2c7ee401c550fb5a79c71d40c37895089b045f0b651a58bf1359bf6', 'bytes': 19290}
BASIS_REF = {'path': str(BASE / 'basis.json'), 'sha256': '37b0e5a10895881f721ca8867094f915a9b8786ac2334d4599b18961b5d4827e', 'bytes': 31811}
HDF_REF = {'path': str(BASE / 'HDF.json'), 'sha256': '7d2554747b44cb8ef08cb1ba117a503104ed8450ecbdb07d8e51d4749265967b', 'bytes': 15187}
MF_REF = {'path': str(BASE / 'MF.json'), 'sha256': '5ae20878ab3b2bf62ec7aae3505fbb55dd2907b64f1f2e7371cfb230aeb9938a', 'bytes': 4683}
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': digest(raw), 'bytes': len(raw)}

def checked(reference):
    raw = Path(reference['path']).read_bytes()
    if len(raw) != reference['bytes'] or digest(raw) != reference['sha256']:
        raise ValueError('frozen preparation Source pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('new immutable Source preparation member exists: ' + name)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

guard = None
failure = None
checks = []
result = {}
try:
    guard_module = types.ModuleType('frev_selfref_source_guard')
    guard_module.__file__ = GUARD_REF['path']
    sys.modules[guard_module.__name__] = guard_module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), guard_module.__dict__)
    guard = guard_module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    inputs = [SOURCE_REF, CONTRACT_REF, BASIS_REF, HDF_REF, MF_REF, GUARD_REF]
    guard.acquire(inputs)
    old = bytes(guard.get_buffer(SOURCE_REF['path']))
    lines = old.splitlines(keepends=True)
    required = [line for line in lines if b'required = [input_ref, bundle[' in line]
    unique = [line for line in lines if b"need(len(authorized) == len(resources), 'RESOURCE_DUPLICATE_PATH')" in line]
    acquire = [line for line in lines if b'guard.acquire(resources)' in line]
    if len(required) != 1 or len(unique) != 1 or len(acquire) != 1:
        raise ValueError('actual FREV v3 correction byte spans are not unique')
    newline = b'\r\n' if unique[0].endswith(b'\r\n') else b'\n'
    insertion = newline.join([
        b"        input_key = guard_module._canonical(absolute_ref(input_ref)['path'])",
        b"        need(input_key not in authorized, 'BUNDLE_RESOURCE_SELF_REFERENCE')",
        b"        authorized[input_key] = input_ref",
    ]) + newline
    new_required = required[0].replace(b'input_ref, ', b'', 1)
    new_unique = unique[0] + insertion
    new_acquire = acquire[0].replace(b'guard.acquire(resources)', b'guard.acquire([input_ref, *resources])')
    candidate = old.replace(required[0], new_required, 1).replace(unique[0], new_unique, 1).replace(acquire[0], new_acquire, 1)
    inverse = candidate.replace(new_required, required[0], 1).replace(new_unique, unique[0], 1).replace(new_acquire, acquire[0], 1)
    old_tree = ast.parse(old.decode('utf-8'))
    new_tree = ast.parse(candidate.decode('utf-8'))
    compile(new_tree, '<prepared FREV self-reference revision>', 'exec')
    old_nodes = {node.name: node for node in old_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    new_nodes = {node.name: node for node in new_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    changed = [name for name in new_nodes if ast.dump(new_nodes[name], include_attributes=False) != ast.dump(old_nodes[name], include_attributes=False)]
    def note(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
        if not passed:
            raise AssertionError(name)
    note('complete_byte_inverse_one_function_AST_delta', inverse == old and changed == ['review_actual'] and set(old_nodes) == set(new_nodes), {'restored_ref': SOURCE_REF, 'changed_function': 'review_actual', 'byte_changes': 3, 'helpers_schemas_Main_NF6_roles_issuer_unchanged': True})
    caller_ref = publish('br8_actual_review.source.py', candidate)
    basis_ref = publish('basis.json', bytes(guard.get_buffer(BASIS_REF['path'])))
    contract = json.loads(bytes(guard.get_buffer(CONTRACT_REF['path'])))
    contract['caller_ref'] = caller_ref
    contract['basis_ref'] = basis_ref
    contract['phase_one_future_argv'][6] = caller_ref['path']
    contract['resource_refs_rule'] = 'absolute public refs3, unique canonical file paths; cover immutable context, all reader inputs, current4, raw consumer streams, role/audit/Scope origins, locked tools, source modules and basis; aliases rejected by SourceReadGuard. The exact input_ref is separately held by Guard and MUST NOT appear inside bundle.resource_refs, including canonical path aliases or conflicting pins.'
    contract['input_self_reference_revision'] = {
        'schema': 'researchos.w09-formal-review-input-self-reference-revision.v1',
        'base_caller_ref': SOURCE_REF,
        'base_contract_ref': CONTRACT_REF,
        'base_basis_ref': BASIS_REF,
        'base_hdf_ref': HDF_REF,
        'base_mf_ref': MF_REF,
        'Source_author': 'codex:/root/backup_regression_resources',
        'Source_author_backend': '/root/backup_regression_resources',
        'non_author_Source_reviewer_required': True,
        'input_schema_unchanged': 'researchos.w09-br6-formal-actual-review-input.v1',
        'input_ref_verification': 'Caller first verifies exact final bytes/SHA, then independently adds the same input_ref to authorized/Guard. The bundle never encodes its own digest.',
        'resource_refs_self_reference': 'REJECT BUNDLE_RESOURCE_SELF_REFERENCE before Guard.acquire; canonical alias and conflicting pin also rejected.',
        'Guard_actual_set': '[input_ref, *bundle.resource_refs]',
        'all_other_required_publication_resources': 'unchanged and exactly verified; no new Root/Scope/qualification authority created',
        'future_current4': 'actual dynamic pins only',
        'future_actual_review_called': False,
        'formal_acceptance': False,
        'execution_grant': False,
    }
    contract_ref = publish('input-contract.json', contract)
    selected = [copy.deepcopy(new_nodes[name]) for name in ['absolute_ref', 'same_ref', 'need', 'strict', 'shape_ref', 'context_ref', 'validate_bundle']]
    actual_function = new_nodes['review_actual']
    entry_body = []
    for node in actual_function.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'out' for target in node.targets):
            break
        entry_body.append(copy.deepcopy(node))
    entry_body.append(ast.Return(value=ast.Name(id='bundle', ctx=ast.Load())))
    args = ast.arguments(posonlyargs=[], args=[ast.arg(arg='input_ref')], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
    selected.append(ast.FunctionDef(name='actual_entry_pin_prefix', args=args, body=entry_body, decorator_list=[]))
    try_node = next(node for node in actual_function.body if isinstance(node, ast.Try))
    admission_body = []
    for node in try_node.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'context_path' for target in node.targets):
            break
        admission_body.append(copy.deepcopy(node))
    admission_body.append(ast.Return(value=ast.Name(id='authorized', ctx=ast.Load())))
    admission_args = ast.arguments(posonlyargs=[], args=[ast.arg(arg='bundle'), ast.arg(arg='input_ref')], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
    selected.append(ast.FunctionDef(name='actual_resource_admission_prefix', args=admission_args, body=admission_body, decorator_list=[]))
    mock_guard = types.SimpleNamespace(_canonical=lambda value: ntpath.normcase(ntpath.normpath(str(value))))
    environment = {'json': json, 're': re, 'Path': Path, 'PurePosixPath': PurePosixPath, 'PureWindowsPath': PureWindowsPath, 'ROOT': R, 'SHA': re.compile(r'[0-9a-f]{64}'), 'pin': ref, 'guard_module': mock_guard}
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), '<actual AST Source-only admission prefixes>', 'exec'), environment)
    def synthetic_ref(name):
        return {'path': str(HERE / 'synthetic-resources' / name), 'sha256': 'a' * 64, 'bytes': 1}
    consumers, qualification = synthetic_ref('consumers.json'), synthetic_ref('native-qualification.json')
    current4 = [synthetic_ref(name) for name in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]
    publications = {key: synthetic_ref(key + '.json') for key in ['scope', 'owner', 'roles']}
    publications['actual_root_captures'] = [synthetic_ref('actual-root-capture.json')]
    resources = [consumers, qualification, *current4, publications['scope'], publications['owner'], publications['roles'], *publications['actual_root_captures']]
    bundle = {'schema': 'researchos.w09-br6-formal-actual-review-input.v1', 'context_ref': {'path': 'execution/v2.4/receipts/W09/W09-99/synthetic-only/context.json', 'sha256': 'b' * 64}, 'consumer_result_ref': consumers, 'root_publication_refs': publications, 'current4_refs': current4, 'resource_refs': resources, 'native_mode_qualification_ref': qualification}
    synthetic_input_ref = publish('synthetic.bundle.control.json', bundle)
    observed_bundle = environment['actual_entry_pin_prefix'](synthetic_input_ref)
    admitted = environment['actual_resource_admission_prefix'](observed_bundle, synthetic_input_ref)
    input_key = mock_guard._canonical(synthetic_input_ref['path'])
    note('finite_bundle_constructs_once_without_own_digest_and_actual_prefix_holds_input', synthetic_input_ref not in observed_bundle['resource_refs'] and admitted[input_key] == synthetic_input_ref and len(admitted) == len(resources) + 1, {'synthetic': True, 'actual_review_function_called': False, 'input_ref': synthetic_input_ref, 'fake_resources_never_acquired_or_read': True})
    tamper_pass = []
    for bad in [dict(synthetic_input_ref, sha256='0' * 64), dict(synthetic_input_ref, bytes=synthetic_input_ref['bytes'] + 1)]:
        try:
            environment['actual_entry_pin_prefix'](bad)
        except ValueError as error:
            tamper_pass.append(str(error) == 'INPUT_PIN')
        else:
            tamper_pass.append(False)
    note('actual_entry_prefix_refuses_hash_or_byte_tamper', all(tamper_pass), {'synthetic': True, 'new_counterexamples': 2})
    self_pass = []
    for own in [synthetic_input_ref, dict(synthetic_input_ref, path=synthetic_input_ref['path'].replace('\\', '/'), sha256='0' * 64, bytes=0)]:
        bad_bundle = copy.deepcopy(bundle)
        bad_bundle['resource_refs'].append(own)
        try:
            environment['actual_resource_admission_prefix'](bad_bundle, synthetic_input_ref)
        except ValueError as error:
            self_pass.append(str(error) == 'BUNDLE_RESOURCE_SELF_REFERENCE')
        else:
            self_pass.append(False)
    note('self_reference_canonical_alias_and_conflicting_pin_refused', all(self_pass), {'synthetic': True, 'new_counterexamples': 2})
    ordinary_pass = []
    duplicate_bundle = copy.deepcopy(bundle)
    duplicate_bundle['resource_refs'].append(dict(consumers, path=consumers['path'].replace('\\', '/')))
    bad_pin_bundle = copy.deepcopy(bundle)
    bad_pin_bundle['resource_refs'][0]['sha256'] = '0' * 64
    for bad_bundle, expected in [(duplicate_bundle, 'RESOURCE_DUPLICATE_PATH'), (bad_pin_bundle, 'INPUT_NOT_HELD')]:
        try:
            environment['actual_resource_admission_prefix'](bad_bundle, synthetic_input_ref)
        except ValueError as error:
            ordinary_pass.append(str(error) == expected)
        else:
            ordinary_pass.append(False)
    note('existing_duplicate_and_required_resource_pin_gates_preserved', all(ordinary_pass), {'synthetic': True, 'new_counterexamples': 2})
    acquires = [node for node in ast.walk(actual_function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'guard' and node.func.attr == 'acquire']
    expected_list = ast.parse('[input_ref, *resources]', mode='eval').body
    note('actual_full_function_guard_set_and_all_other_functions_unchanged', len(acquires) == 1 and len(acquires[0].args) == 1 and ast.dump(acquires[0].args[0], include_attributes=False) == ast.dump(expected_list, include_attributes=False) and basis_ref['sha256'] == BASIS_REF['sha256'] and contract['input_schema'] == 'researchos.w09-br6-formal-actual-review-input.v1', {'Guard_input_set': '[input_ref, *resources]', 'fixed_Main1e_NF6_six_consumers_roles_Global_issuer_unchanged': True, 'old_successful_controls_replayed': False})
    inverse_ref = publish('exact-inverse.json', {'base_source_ref': SOURCE_REF, 'candidate_source_ref': caller_ref, 'complete_byte_inverse': True, 'restored_sha256': digest(inverse), 'changed_function_AST': changed, 'byte_span_replacements': [{'old_hex': required[0].hex(), 'new_hex': new_required.hex()}, {'old_hex': unique[0].hex(), 'new_hex': new_unique.hex()}, {'old_hex': acquire[0].hex(), 'new_hex': new_acquire.hex()}], 'unchanged_basis_ref': BASIS_REF, 'new_basis_ref': basis_ref})
    result = {'source_author': 'codex:/root/backup_regression_resources', 'source_author_backend': '/root/backup_regression_resources', 'source_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084', 'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98', 'caller_ref': caller_ref, 'input_contract_ref': contract_ref, 'basis_ref': basis_ref, 'exact_inverse_ref': inverse_ref, 'input_refs': inputs, 'checks': checks, 'new_delta_controls': len(checks), 'synthetic_controls_only': True, 'actual_formal_review_called': False, 'Root_stages_Native_Go_SQL_model_TP_dispatcher_calls': 0, 'Main_Canon_Scope_Registry_writes': 0, 'Source_self_acceptance': False, 'independent_Source_review_required': True, 'formal_acceptance': False, 'execution_grant': False}
except BaseException as error:
    failure = {'exception': repr(error), 'traceback': traceback.format_exc(), 'successful_control_prefix': checks}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('SourceGuard.closed.json', closure)
    if failure is not None:
        publish('construction.failure.json', {'failure': failure, 'Source_guard_ref': closure_ref, 'Root_stages_Native_Go_SQL_model_TP_dispatcher_calls': 0})

if failure is not None:
    print(json.dumps({'failure': failure, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('Source construction guard not closed')
result['Source_guard_ref'] = closure_ref
result['all_guards_closed'] = True
metadata_ref = publish('Source-preparation.json', result)
print(json.dumps({'metadata_ref': metadata_ref, 'caller_ref': result['caller_ref'], 'contract_ref': result['input_contract_ref'], 'basis_ref': result['basis_ref'], 'exact_inverse_ref': result['exact_inverse_ref'], 'Source_guard_ref': closure_ref, 'new_delta_controls': len(checks), 'passed': len(checks), 'actual_formal_review_called': False, 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
