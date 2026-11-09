"""Seal the prepared FREV Source and observed IO, without formal execution."""
import difflib
import hashlib
import json
import sys
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUTHOR = 'codex:/root/backup_regression_resources'
GUARD_REF = {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py', 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(reference):
    raw = Path(reference['path']).read_bytes()
    if len(raw) != reference['bytes'] or hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('sealed Source input pin differs')
    return raw

def read(name):
    return json.loads((HERE / name).read_bytes())

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable Source seal member exists: ' + name)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

guard = None
error = None
result = {}
try:
    preparation = read('Source-preparation.json')
    contract = read('input-contract.json')
    inverse = read('exact-inverse.json')
    origin = read('failure-origin.1235.json')
    caller_ref = preparation['caller_ref']
    contract_ref = preparation['contract_ref']
    basis_ref = preparation['basis_ref']
    candidate = checked(caller_ref)
    checked(contract_ref)
    checked(basis_ref)
    base_source_ref = inverse['base_source_ref']
    before = checked(base_source_ref)
    diff = ''.join(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True), candidate.decode('utf-8').splitlines(keepends=True), fromfile=base_source_ref['path'], tofile=caller_ref['path'])).encode('utf-8')
    diff_ref = publish('caller.exact.diff', diff)
    closed_refs = [ref(HERE / 'SourceGuard.closed.json'), ref(HERE / 'tail-SourceGuard.closed.json')]
    for item in closed_refs:
        closure = json.loads(checked(item))
        if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
            raise ValueError('observed earlier Source guard was not closed')
    if preparation['total_distinct_passed_controls'] != 6 or preparation['new_tail_checks'] != 2 or preparation['prior_prefix_not_replayed'] is not True or any(item['passed'] is not True for item in preparation['tail_checks']):
        raise ValueError('existing finite Source control observations differ')
    if contract['input_schema'] != 'researchos.w09-br6-formal-actual-review-input.v1' or preparation['actual_formal_review_called'] is not False:
        raise ValueError('Source preparation execution or schema boundary differs')
    decision = {
        'schema': 'researchos.w09-br8-formal-review-source-preparation-decision.v1',
        'decision': 'PREPARED_SOURCE_ONLY_SELF_REFERENCE_FIXED_WAITING_NONAUTHOR_REVIEW_AND_ACTUAL_INPUTS',
        'author_id': AUTHOR,
        'backend_actor': '/root/backup_regression_resources',
        'author_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084',
        'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'created_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'caller_ref': caller_ref,
        'contract_ref': contract_ref,
        'basis_ref': basis_ref,
        'base_source_ref': base_source_ref,
        'base_hdf_ref': contract['input_self_reference_revision']['base_hdf_ref'],
        'base_mf_ref': contract['input_self_reference_revision']['base_mf_ref'],
        'preparation_ref': ref(HERE / 'Source-preparation.json'),
        'exact_inverse_ref': ref(HERE / 'exact-inverse.json'),
        'exact_diff_ref': diff_ref,
        'business_delta': 'Only review_actual: remove input_ref from required bundle resources, reject canonical self-reference and independently authorize/hold exact input_ref with resource_refs.',
        'changed_function': 'review_actual',
        'byte_span_replacements': 3,
        'input_schema_unchanged': contract['input_schema'],
        'basis_bytes_unchanged': True,
        'Main1e_NF6_sixConsumer_roles_8GLOBAL_issuer_executor_rules_unchanged': True,
        'six_distinct_controls_passed': 6,
        'four_successful_prefix_controls_not_replayed': True,
        'two_unreached_tail_controls_executed': True,
        'new_controls_are_synthetic_Source_only': True,
        'original_failure_refs': [ref(HERE / 'failure-origin.1235.json')],
        'original1235_true_Root_capture_ref': origin['actual_binding_ref'],
        'original1235_true_raw_three_lines_ref': origin['actual_raw_three_lines_ref'],
        'complete_public_tools_IO_ref': ref(HERE / 'Source-public-tool-IO.reencoded.json'),
        'complete_public_tools_IO_kind': 'ACTUAL_TOOL_REQUEST_RESULT_REENCODED_NOT_RAW_AUDIT',
        'all_previous_failures_preserved': True,
        'failure_counter_reset': False,
        'current4_rule': 'Future exact dynamic Root publication; no live Canon read or held handle in this task.',
        'independent_Source_review_required_before_actual_use': True,
        'future_actual_review_inputs': 'OPEN: immutable context, six actual consumer results, Root publication/scope/owner/roles/current4, 8 GLOBAL evidence and all exact resources.',
        'future_input_resource_rule': 'Compute bundle bytes and input_ref externally; resource_refs excludes the bundle own canonical path. Caller independently validates and holds input_ref. All other original resources stay mandatory.',
        'future_actual_review_called': False,
        'Root_stage_Native_Go_SQL_model_TP_dispatcher_calls': 0,
        'Main_Canon_Scope_Registry_writes': 0,
        'Root_issuance_created': False,
        'Source_self_acceptance': False,
        'formal_acceptance': False,
        'execution_grant': False,
        'stop_after_delivery': True,
    }
    decision_ref = publish('preparation-decision.json', decision)
    paths = sorted(path for path in HERE.iterdir() if path.is_file())
    local_refs = [ref(path) for path in paths]
    # Necessary publication pin closure only; no successful control or old runtime replay.
    external_refs = preparation['source_inputs']
    unique = {}
    module = types.ModuleType('frev_source_publication_guard')
    module.__file__ = GUARD_REF['path']
    sys.modules[module.__name__] = module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), module.__dict__)
    for item in [*local_refs, *external_refs, GUARD_REF]:
        key = module._canonical(item['path'])
        if key in unique and (unique[key]['sha256'], unique[key]['bytes']) != (item['sha256'], item['bytes']):
            raise ValueError('Source publication resource pin conflict')
        unique[key] = item
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire(list(unique.values()))
    result = {'local_refs': local_refs, 'decision_ref': decision_ref, 'caller_ref': caller_ref, 'contract_ref': contract_ref, 'basis_ref': basis_ref, 'external_refs': external_refs, 'closed_refs': closed_refs, 'diff_ref': diff_ref}
except BaseException as failure:
    error = {'exception': repr(failure), 'traceback': traceback.format_exc()}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    publication_guard_ref = publish('publication-SourceGuard.closed.json', closure)
    if error is not None:
        publish('publication.failure.json', {'error': error, 'Source_guard_ref': publication_guard_ref})

if error is not None:
    print(json.dumps({'error': error, 'Source_guard_ref': publication_guard_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('publication Source guard not closed')
members = [*result['local_refs'], publication_guard_ref]
for item in members:
    checked(item)
manifest_ref = publish('MF.json', {'schema': 'researchos.w09-br8-formal-review-preparation-manifest.v1', 'author_id': AUTHOR, 'members': members, 'member_count': len(members), 'exclusions': ['HDF.json', 'MF.json', 'publication-seal.actual-tool-io.reencoded.json'], 'exclusion_reason': 'Handoff/manifest avoid self-reference; final seal call and output are captured afterward as explicitly external IO.', 'formal_acceptance': False, 'execution_grant': False})
handoff_ref = publish('HDF.json', {'schema': 'researchos.w09-br8-formal-review-preparation-handoff.v1', 'decision': decision['decision'], 'author_id': AUTHOR, 'backend_actor': '/root/backup_regression_resources', 'author_thread': decision['author_thread'], 'Root_thread': decision['Root_thread'], 'manifest_ref': manifest_ref, 'decision_ref': result['decision_ref'], 'caller_ref': result['caller_ref'], 'contract_ref': result['contract_ref'], 'basis_ref': result['basis_ref'], 'exact_inverse_ref': decision['exact_inverse_ref'], 'exact_diff_ref': result['diff_ref'], 'source_inputs': result['external_refs'], 'guard_refs': [*result['closed_refs'], publication_guard_ref], 'all_guards_closed': True, 'new_tail_controls_passed': 2, 'previous_successful_prefix_preserved_not_replayed': 4, 'original_failure_refs': decision['original_failure_refs'], 'original1235_actual_binding_ref': origin['actual_binding_ref'], 'original1235_actual_raw_ref': origin['actual_raw_three_lines_ref'], 'existing_NF6_qualification_ref': contract['existing_NF6_qualification_ref'], 'existing_six_Mode_refs': contract['existing_six_Mode_refs'], 'new_Main_profile_ref': contract['Main_profile_ref'], 'input_schema': contract['input_schema'], 'runtime_resource_rule': decision['future_input_resource_rule'], 'future_current4_dynamic': True, 'future_actual_review_called': False, 'independent_Source_review_required': True, 'Source_self_acceptance': False, 'Root_stage_Native_Go_SQL_model_TP_dispatcher_calls': 0, 'Main_Canon_Scope_Registry_writes': 0, 'formal_acceptance': False, 'execution_grant': False, 'stop_after_delivery': True})
print(json.dumps({'hdf_ref': handoff_ref, 'mf_ref': manifest_ref, 'decision_ref': result['decision_ref'], 'caller_ref': result['caller_ref'], 'contract_ref': result['contract_ref'], 'basis_ref': result['basis_ref'], 'publication_guard_ref': publication_guard_ref, 'members': len(members), 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
