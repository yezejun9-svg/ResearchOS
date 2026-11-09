"""Independent BR8 delta review. Execute only isolated pure Source helpers."""
import ast
import copy
import hashlib
import json
import ntpath
import re
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
SRC = W / 'w09_formal_root_bridge_source_codex/bridge-20261010-08'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
HDF_REF = {'path': str(SRC / 'HDF.json'), 'sha256': '048b118676757dc77f3d1d513ca7a852eb45e483ee2fb8224503b76b050956fc', 'bytes': 12729}
MF_REF = {'path': str(SRC / 'MF.json'), 'sha256': 'c5ac0d882b01ebd15334ab1c2205e1c415f27575b42d0f2f0a47580a018a0e95', 'bytes': 5492}
AUTHOR_REF = {'path': str(W / 'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.bridge08-source-author.actual-audit.root.json'), 'sha256': 'dfb63c737ba4687bc2f86184240a783cfd5e2388b4a44d91df787402d2237d5d', 'bytes': 1112}
ROLE_REF = {'path': str(W / 'w09_br8_role_input_preparation_root/prepare-20261010-01/rebase.prepared.root.json'), 'sha256': '0d4882fe24ced5e17e7773f7596244deea62750617a669edcd7e790901a27941', 'bytes': 1502}
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
PRIOR_REF = {'path': str(W / 'w09_formal_root_bridge_independent_source_review_codex/review-20261010-07-backup/review-decision.json'), 'sha256': 'd9f928885afbfb1211936718ce790ff7e26f3a3381174bbc6d633c1ea55d3852', 'bytes': 2694}
API_REF = {'path': str(R / 'execution/v2.4/formal_case_index.py'), 'sha256': 'e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b', 'bytes': 71844}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def checked(ref):
    raw = Path(ref['path']).read_bytes()
    if len(raw) != ref['bytes'] or sha(raw) != ref['sha256']:
        raise ValueError('fixed independent review input pin differs')
    return raw

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)}

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('new immutable review member exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate Source evidence JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))

def identity(path):
    return ntpath.normcase(ntpath.normpath(str(path)))

def same_ref(left, right):
    return set(left) == set(right) == {'path', 'sha256', 'bytes'} and identity(left['path']) == identity(right['path']) and left['sha256'] == right['sha256'] and type(left['bytes']) is int and type(right['bytes']) is int and left['bytes'] == right['bytes']

def all_refs(value):
    if type(value) is dict:
        if set(value) == {'path', 'sha256', 'bytes'}:
            yield value
        else:
            for item in value.values():
                yield from all_refs(item)
    elif type(value) is list:
        for item in value:
            yield from all_refs(item)

def nodes(tree):
    return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}

def span(raw, node):
    return b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])

checks = []
failure = None
guard = None
closure = None
result = {}
try:
    hdf = strict_json(checked(HDF_REF))
    manifest = strict_json(checked(MF_REF))
    author = strict_json(checked(AUTHOR_REF))
    role = strict_json(checked(ROLE_REF))
    base_hdf = strict_json(checked(hdf['base_hdf_ref']))
    old_role_inputs = strict_json(checked(role['old_inputs_ref']))
    new_role_inputs = strict_json(checked(role['new_inputs_ref']))
    references = [HDF_REF, MF_REF, AUTHOR_REF, author['original_capture_ref'], ROLE_REF, GUARD_REF, PRIOR_REF, API_REF, hdf['base_hdf_ref'], hdf['base_mf_ref'], hdf['base_source_ref'], base_hdf['consumer_launcher_ref'], hdf['Main_required_ref'], hdf['boundary_diagnosis_facts_ref'], role['old_source_ref'], role['new_source_ref'], role['old_inputs_ref'], role['new_inputs_ref']]
    references += manifest['members'] + old_role_inputs['fixed_refs'] + new_role_inputs['fixed_refs']
    inventory = {}
    for item in references:
        key = identity(item['path'])
        if key in inventory and not same_ref(inventory[key], item):
            raise ValueError('conflicting exact public Source reference')
        inventory[key] = item
    guard_module = types.ModuleType('br8_independent_source_guard')
    guard_module.__file__ = GUARD_REF['path']
    sys.modules[guard_module.__name__] = guard_module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), guard_module.__dict__)
    guard = guard_module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire(list(inventory.values()))
    def buffered(reference):
        return bytes(guard.get_buffer(reference['path']))
    def note(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
        if not passed:
            raise AssertionError(name)
    source = buffered(hdf['source_ref'])
    base = buffered(hdf['base_source_ref'])
    source_tree = ast.parse(source.decode('utf-8'))
    base_tree = ast.parse(base.decode('utf-8'))
    newer, older = nodes(source_tree), nodes(base_tree)
    prior = strict_json(buffered(PRIOR_REF))
    note('exact_published_package_and_prior_Source_only_lineage', hdf['source_author'] == 'codex:/root/full_w09_source_review' and hdf['source_author_backend'] == '/root/full_w09_source_review' and prior['decision'] == 'ACCEPTED_SOURCE_ONLY' and same_ref(prior['source_ref'], hdf['base_source_ref']) and same_ref(hdf['manifest_ref'], MF_REF), {'held_public_refs': len(inventory), 'prior_controls_replayed': False})
    helper = 'historical_dependency_refs'
    new_lines = source.splitlines(keepends=True)
    restored = b''.join(new_lines[:newer[helper].lineno-1]) + span(base, older[helper]) + b''.join(new_lines[newer[helper].end_lineno:])
    from_gen = b'BRIDGE_GENERATION = "bridge-20261010-08"'
    to_gen = b'BRIDGE_GENERATION = "bridge-20261010-07"'
    inverse = restored.replace(from_gen, to_gen, 1)
    changed_functions = [name for name in newer if name not in older or ast.dump(newer[name], include_attributes=False) != ast.dump(older[name], include_attributes=False)]
    note('independent_complete_byte_inverse_helper_and_generation_only', restored.count(from_gen) == 1 and inverse == base and set(newer) == set(older) and changed_functions == [helper] and buffered(hdf['consumer_launcher_ref']) == buffered(base_hdf['consumer_launcher_ref']), {'inverse_sha256': sha(inverse), 'changed_functions': changed_functions, 'launcher_byteidentical': True})
    selected = [copy.deepcopy(newer[name]) for name in ['need', 'references', 'validate_persistent_snapshot', helper]]
    canonical_names = ['checkpoint', 'path_ownership', 'step_state', 'commands']
    canon = [identity(R / 'execution/v2.4' / (name + '.json')) for name in canonical_names]
    env = {'copy': copy, 'Path': Path, 're': re, 'CANON': canon, 'canonical_identity': lambda path: identity(Path(path) if Path(path).is_absolute() else R / path)}
    def forbidden_archive(*args):
        raise AssertionError('archive authority function must not be executed by Source-only helper fixture')
    env['proposal_archive_refs'] = forbidden_archive
    exec(compile(ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[])), '<isolated BR8 pure Source helper>', 'exec'), env)
    call = env[helper]
    facts = strict_json(buffered(hdf['boundary_diagnosis_facts_ref']))
    actual_ranges = facts['actual_typed_ranges']
    unchanged = copy.deepcopy(actual_ranges)
    outside = {'path': 'C:/Synthetic-Public-Source-Control/ordinary.log', 'sha256': 'a' * 64, 'bytes': 7}
    fixture = {'dependency_snapshot': {'files': {}, 'inventories': [{'synthetic': True}], 'audit_ranges': actual_ranges + [copy.deepcopy(actual_ranges[0])]}, 'misplaced': {'audit_ranges': [copy.deepcopy(actual_ranges[0])]}, 'ordinary_ref': outside}
    original = copy.deepcopy(fixture)
    emitted = call(fixture, None, None, 'independent_source_only_fixture')
    note('clone_only_13_ranges_original_mixed_spelling_and_misplaced_ref_preserved', fixture == original and actual_ranges == unchanged and len(emitted) == 2 and outside in emitted and any(item['path'] == actual_ranges[0]['path'] for item in emitted), {'synthetic': True, 'range_count': 13, 'misplaced_range_not_exempted': True, 'Root_audit_opened': False, 'whole_file_foreign_physical_failure_replayed': False})
    count_results = []
    for count in [0, 1, 13]:
        snapshot = {'dependency_snapshot': {'files': {}, 'audit_ranges': [copy.deepcopy(actual_ranges[0]) for _ in range(count)]}}
        snapshot_original = copy.deepcopy(snapshot)
        output = call(snapshot, None, None, 'independent_source_only_fixture')
        count_results.append(snapshot == snapshot_original and output == [])
    note('typed_range_count_is_not_a_fixed_Root_log_or_twelve_range_gate', all(count_results), {'synthetic_counts': [0, 1, 13], 'fixed_Root_audit_path_gate_added': False})
    class IntSubclass(int):
        pass
    class StrSubclass(str):
        pass
    class DictSubclass(dict):
        pass
    class ListSubclass(list):
        pass
    cases = []
    for field, replacement in [('offset', IntSubclass(0)), ('bytes', IntSubclass(1)), ('path', StrSubclass(actual_ranges[0]['path'])), ('sha256', StrSubclass('b' * 64))]:
        item = dict(actual_ranges[0])
        item[field] = replacement
        cases.append([item])
    cases += [[DictSubclass(actual_ranges[0])], ListSubclass([dict(actual_ranges[0])])]
    rejected = []
    for ranges in cases:
        try:
            call({'dependency_snapshot': {'files': {}, 'audit_ranges': ranges}}, None, None, 'independent_source_only_fixture')
        except ValueError as error:
            rejected.append(str(error) in {'HISTORICAL_AUDIT_RANGE_SHAPE', 'HISTORICAL_AUDIT_RANGES_REQUIRED'})
        else:
            rejected.append(False)
    note('new_exact_type_subclass_counterexamples_cannot_bypass_typed_branch', all(rejected), {'synthetic': True, 'new_counterexamples': len(cases), 'author14_shape_controls_replayed': False})
    canon_rejections = []
    for name in canonical_names:
        item = dict(actual_ranges[0], path=str(R / 'execution/v2.4/receipts/../' / (name + '.json')))
        try:
            call({'dependency_snapshot': {'files': {}, 'audit_ranges': [item]}}, None, None, 'independent_source_only_fixture')
        except ValueError as error:
            canon_rejections.append(str(error) == 'UNDECLARED_HISTORICAL_CANONICAL_REFERENCE')
        else:
            canon_rejections.append(False)
    note('all_Canon_traversal_identities_rejected_before_clone_omission', all(canon_rejections) and ast.dump(newer['canonical_identity'], include_attributes=False) == ast.dump(older['canonical_identity'], include_attributes=False), {'synthetic_identity_classifier': 'ntpath normpath/normcase only; production classifier byte semantics unchanged', 'Canon_file_bytes_read': False, 'new_counterexamples': len(canon_rejections)})
    api_tree = ast.parse(buffered(API_REF).decode('utf-8'))
    api_nodes = nodes(api_tree)
    audit_call_present = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_audit_range' for node in ast.walk(api_nodes['recheck_inputs']))
    preserved = ['references', 'physical', 'checked', 'snapshot', 'registration', 'publication', 'main']
    actual_preserved = [name for name in preserved if name in newer]
    note('dedicated_actual_range_checks_and_generic_foreign_gate_unchanged', audit_call_present and all(span(source, newer[name]) == span(base, older[name]) for name in actual_preserved), {'API_source_ref': API_REF, 'range_validator_lines': [api_nodes['_audit_range'].lineno, api_nodes['_audit_range'].end_lineno], 'recheck_lines': [api_nodes['recheck_inputs'].lineno, api_nodes['recheck_inputs'].end_lineno], 'other_functions_complete_inverse': True, 'existing_Main_controls_replayed': False, 'dedicated_range_validator_executed': False})
    raw = buffered(author['original_capture_ref'])
    raw_lines = raw.splitlines(keepends=True)
    rows = [strict_json(line) for line in raw_lines]
    prefix = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/full_w09_source_review\nPayload:\n'
    message = rows[2]['payload']
    text = message['content'][0]['text']
    delivery = strict_json(text[len(prefix):]) if text.startswith(prefix) else strict_json(text)
    delivered_refs = list(all_refs(delivery))
    expected = [HDF_REF, MF_REF, hdf['source_ref']]
    actual_author = len(rows) == 3 and rows[0]['type'] == 'session_meta' and rows[0]['payload']['id'] == ROOT_THREAD and rows[1]['type'] == 'inter_agent_communication_metadata' and rows[2]['type'] == 'response_item' and rows[1]['timestamp'] == rows[2]['timestamp'] == '2026-10-10T02:44:52.209Z' and type(rows[1]['ordinal']) is int and rows[2]['ordinal'] == rows[1]['ordinal'] + 1 and message['type'] == 'agent_message' and message['author'] == '/root/full_w09_source_review' and message['recipient'] == '/root' and rows[2]['metadata']['client_authored'] is False and len(message['content']) == 1 and all(any(same_ref(item, candidate) for candidate in delivered_refs) for item in expected) and [sha(line) for line in raw_lines] == author['original_line_sha256'] and author['binding_sha256'] == HDF_REF['sha256']
    note('true_Root_three_LF_author_Final_and_non_author_reviewer_identity', actual_author, {'actor_id': author['actor_id'], 'actual_backend': message['author'], 'recipient': message['recipient'], 'metadata_ordinal': rows[1]['ordinal'], 'Final_ordinal': rows[2]['ordinal'], 'timestamp': rows[2]['timestamp'], 'Root_thread': ROOT_THREAD, 'raw_capture_ref': author['original_capture_ref'], 'Source_author_differs_from_reviewer': True})
    role_old = buffered(role['old_source_ref'])
    role_new = buffered(role['new_source_ref'])
    replacements = [
        ('6d80a6af3b60b6743633f0f6818ff515ba8604d81cd0ec109e9be4871b3db0e1', '50930e0d982b5c7c570280cf2f9e65ad273256176ea3eaf637763e8926244c12'),
        ('bridge-20261010-08', 'bridge-20261010-07'),
        ('BR8_PROPOSAL_CONTEXT', 'BR7_PROPOSAL_CONTEXT'),
        ('w09_br8_role_inputs_root', 'w09_br7_role_inputs_root'),
    ]
    role_inverse = role_new
    replacement_counts = []
    for new, old in replacements:
        replacement_counts.append(role_inverse.count(new.encode('utf-8')))
        role_inverse = role_inverse.replace(new.encode('utf-8'), old.encode('utf-8'))
    note('Root_role_metadata_preparation_four_constant_groups_complete_inverse', role_inverse == role_old and replacement_counts == [1, 2, 1, 1] and role['builder_executed'] is False and role['Root_stage_calls'] == 0, {'replacement_counts': replacement_counts, 'inverse_sha256': sha(role_inverse), 'new_source_ref': role['new_source_ref'], 'metadata_preparation_only': True, 'builder_or_Root_stage_executed': False})
    stable = [key for key in old_role_inputs if key not in {'bridge_source_ref', 'bridge_hdf_ref', 'peer_audits', 'fixed_refs'}]
    role_binding_ok = set(old_role_inputs) == set(new_role_inputs) and all(old_role_inputs[key] == new_role_inputs[key] for key in stable) and same_ref(new_role_inputs['bridge_source_ref'], hdf['source_ref']) and same_ref(new_role_inputs['bridge_hdf_ref'], HDF_REF) and same_ref(new_role_inputs['peer_audits']['SOURCE_AUTHOR'], AUTHOR_REF) and old_role_inputs['peer_audits']['VERIFIER'] == new_role_inputs['peer_audits']['VERIFIER'] and all(any(same_ref(item, candidate) for candidate in new_role_inputs['fixed_refs']) for item in [HDF_REF, MF_REF, hdf['source_ref'], AUTHOR_REF, author['original_capture_ref']])
    note('Root_role_metadata_peer_source_pins_updated_existing_Mode_Main_template_unchanged', role_binding_ok, {'new_inputs_ref': role['new_inputs_ref'], 'mode01_ref': new_role_inputs['mode01_ref'], 'actual_Source_peer_audit_ref': AUTHOR_REF, 'actual_Source_peer_capture_ref': author['original_capture_ref'], 'existing_Mode_verifier_delivery_unchanged': True, 'metadata_preparation_only': True, 'runtime_or_Root_role_issuance_qualification': False})
    result = {'schema': 'researchos.w09-bridge-independent-source-review-report.v1', 'source_hdf_ref': HDF_REF, 'source_mf_ref': MF_REF, 'source_ref': hdf['source_ref'], 'consumer_launcher_ref': hdf['consumer_launcher_ref'], 'root_calling_contract_ref': hdf['root_calling_contract_ref'], 'source_author': hdf['source_author'], 'reviewer_id': '/root/backup_regression_resources', 'actual_source_author_audit_ref': AUTHOR_REF, 'checks': checks, 'new_delta_checks': len(checks), 'findings': [], 'prior_Source_review_ref': PRIOR_REF, 'old_successful_controls_replayed': False, 'existing_Native_and_six_Mode_replayed': False, 'Root_role_metadata_preparation_ref': ROLE_REF, 'role_metadata_preparation_verdict': 'INDEPENDENT_METADATA_PREPARATION_ONLY_NO_RUNTIME_GRANT', 'Root_stage_calls': 0, 'Main_Canon_Scope_Registry_writes': 0, 'Native_Go_SQL_model_TP_dispatcher_calls': 0, 'formal_acceptance': False, 'execution_grant': False}
except BaseException as error:
    failure = {'exception': repr(error), 'traceback': traceback.format_exc(), 'passed_prefix': checks}
finally:
    if guard is not None:
        closure = guard.close()
    else:
        closure = {'attempted': False, 'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('SourceGuard.closed.json', closure)
    if failure is not None:
        publish('review.failure.json', {'failure': failure, 'Source_guard_ref': closure_ref, 'Root_stage_calls': 0, 'Native_Go_SQL_model_TP_dispatcher_calls': 0})

if failure is not None:
    print(json.dumps({'failure': failure, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('independent Source guard closure failed')
result['Source_guard_ref'] = closure_ref
result['all_guards_closed'] = True
result['retained_handles_count'] = 0
result['guard_errors'] = []
report_ref = publish('review-report.json', result)
print(json.dumps({'report_ref': report_ref, 'Source_guard_ref': closure_ref, 'new_delta_checks': len(checks), 'passed': len(checks), 'all_guards_closed': True, 'role_metadata_preparation_verdict': result['role_metadata_preparation_verdict'], 'Root_stage_calls': 0, 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
