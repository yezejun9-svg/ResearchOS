import ast
import copy
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path, PurePosixPath, PureWindowsPath

Q = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
GUARD = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    path = Q / name
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def main():
    basis = json.loads((Q / 'basis.json').read_text(encoding='utf-8'))
    source_path = Q / 'br6_actual_review.source.py'
    source_raw = source_path.read_bytes()
    tree = ast.parse(source_raw)
    compile(source_raw, str(source_path), 'exec')
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    keep = {'need', 'strict', 'shape_ref', 'context_ref', 'route', 'consumer_closure', 'validate_bundle'}
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id in {'SHA', 'ROUTES', 'GLOBAL_TYPES'}
                           for target in node.targets)]
    namespace = {'json': json, 're': __import__('re'), 'PurePosixPath': PurePosixPath,
                 'PureWindowsPath': PureWindowsPath}
    exec(compile(ast.Module(body=assignments + [functions[name] for name in keep], type_ignores=[]),
                 'br6_pure_delta', 'exec'), namespace)
    checks = []
    def check(name, operation, rejected=False):
        try:
            operation()
        except (ValueError, KeyError, TypeError) as exc:
            if not rejected:
                raise
            checks.append({'id': name, 'result': 'EXPECTED_REJECTION', 'type': type(exc).__name__})
        else:
            if rejected:
                raise AssertionError(name + ': expected rejection')
            checks.append({'id': name, 'result': 'PASS'})
    ref2 = {'path': 'execution/v2.4/receipts/W09/W09-99/future/context.json', 'sha256': 'a' * 64}
    check('CONTEXT_EXACT_REPO_POSIX2', lambda: namespace['context_ref'](ref2))
    for name, replacement in [('ABSOLUTE', 'D:/future/context.json'), ('TRAVERSAL', ref2['path'] + '/../x'),
                              ('WINDOWS_SEPARATOR', ref2['path'].replace('/', '\\'))]:
        value = dict(ref2, path=replacement)
        check('CONTEXT_REJECT_' + name, lambda value=value: namespace['context_ref'](value), True)
    check('CONTEXT_REJECT_BYTES3', lambda: namespace['context_ref'](dict(ref2, bytes=0)), True)
    check('JSON_REJECT_DUPLICATE', lambda: namespace['strict']('{"x":1,"x":2}'), True)
    check('JSON_REJECT_TRAILING', lambda: namespace['strict']('{} {}'), True)
    check('JSON_REJECT_NONFINITE', lambda: namespace['strict']('{"x":NaN}'), True)
    public_ref = {'path': 'D:/synthetic/x', 'sha256': 'a' * 64, 'bytes': 0}
    cleanup = {'job_idle_confirmed': True, 'active_processes_last_observed': 0, 'handles_closed': True,
               'primary_exit_confirmed': True, 'assigned_before_resume': True, 'errors': []}
    routes = namespace['ROUTES']
    rows = [dict(zip(('command_key', 'check_id', 'case_id'), item)) for item in routes]
    records = [{'route': list(item), 'actual_exit': 0,
                'observation': {'actual_exit': 0, 'timed_out': False, 'error': None, 'job_cleanup': copy.deepcopy(cleanup)},
                'stdout_ref': public_ref, 'stderr_ref': public_ref} for item in routes]
    consumer = {'schema': 'researchos.w09-bridge-consumers.v1', 'registered_commands': rows,
                'formal_acceptance': False, 'producer_rerun': False, 'c19_policy': 'RUN_CURRENT_CM40',
                'executed_consumer_routes': [list(item) for item in routes], 'processes': records}
    check('SIX_SYNTHETIC_CLOSED_PROCESS_SHAPE', lambda: namespace['consumer_closure'](consumer, {'registered_commands': rows}))
    variants = []
    bad = copy.deepcopy(consumer); bad['processes'][0]['observation']['actual_exit'] = False; variants.append(('BOOL_EXIT', bad))
    bad = copy.deepcopy(consumer); bad['processes'][0]['actual_exit'] = None; variants.append(('UNKNOWN_EXIT', bad))
    bad = copy.deepcopy(consumer); bad['processes'][0]['observation']['job_cleanup']['handles_closed'] = False; variants.append(('LIVE_HANDLE', bad))
    bad = copy.deepcopy(consumer); bad['processes'][0]['observation']['timed_out'] = True; variants.append(('TIMEOUT', bad))
    bad = copy.deepcopy(consumer); bad['processes'][1]['route'] = bad['processes'][0]['route']; variants.append(('DUPLICATE_ROUTE', bad))
    bad = copy.deepcopy(consumer); bad['c19_policy'] = 'REUSE_OLD_C19'; variants.append(('OLD_C19', bad))
    for name, bad in variants:
        check('CONSUMER_REJECT_' + name,
              lambda bad=bad: namespace['consumer_closure'](bad, {'registered_commands': rows}), True)
    future_input = {'schema': 'researchos.w09-br6-formal-actual-review-input.v1', 'context_ref': None,
                    'consumer_result_ref': None, 'root_publication_refs': None, 'current4_refs': None,
                    'resource_refs': None, 'native_mode_qualification_ref': None}
    check('OPEN_FUTURE_INPUT_CANNOT_RUN', lambda: namespace['validate_bundle'](future_input), True)
    forbidden = {'run_owned', 'run_registered_case', 'derive_formal_cases', 'activate', 'consume', 'propose', 'capture'}
    calls = [node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute)
             else '' for node in ast.walk(tree) if isinstance(node, ast.Call)]
    check('NO_PRODUCT_ROOT_STAGE_OR_PROCESS_CALL', lambda: (_ for _ in ()).throw(AssertionError('forbidden call'))
          if forbidden.intersection(calls) else None)
    check('REUSES_MAIN_DISPATCH_GLOBAL_AND_CUTOFF', lambda: None if
          {'_dispatches', '_global', '_review_execution_cutoff', '_role_registry', '_vector'}.issubset(calls)
          else (_ for _ in ()).throw(AssertionError('missing Main gate')))
    source_ref = pin(source_path)
    qualification = next(ref for ref in basis['source_refs'] if Path(ref['path']).name == 'decision.json')
    profile_ref = next(ref for ref in basis['source_refs'] if Path(ref['path']).name == 'formal_profile_w09.py')
    api_ref = next(ref for ref in basis['source_refs'] if Path(ref['path']).name == 'formal_case_index.py')
    contract = {
        'schema': 'researchos.w09-br6-formal-actual-review-preparation-contract.v1',
        'decision': 'PREPARED_SOURCE_ONLY_WAITING_ROOT_ACTUAL_INPUTS',
        'Source_author': 'codex:/root/backup_regression_resources', 'verifier_backend': '/root/backup_regression_resources',
        'product_Source_author': '/root/full_w09_source_review', 'executor': 'codex:/root', 'assembler': 'codex:/root',
        'reviewer_thread': '01a11cee-bf59-7a01-be0e-9f799f9b1084', 'Root_thread': '01a11007-5233-7ca1-b71f-9e9e5ce84c98',
        'caller_ref': source_ref, 'Main_profile_ref': profile_ref, 'Main_api_ref': api_ref,
        'basis_ref': pin(Q / 'basis.json'), 'existing_NF6_qualification_ref': qualification,
        'existing_six_Mode_refs': basis['six_Mode_refs'],
        'input_schema': 'researchos.w09-br6-formal-actual-review-input.v1',
        'input_fields': list(future_input), 'context_reference_fields': ['path', 'sha256'],
        'context_reference_path': 'repository relative POSIX; never absolute or bytes-bearing',
        'metadata_reference_fields': ['path', 'sha256', 'bytes'],
        'Root_publication_fields': ['scope', 'owner', 'roles', 'actual_root_captures'],
        'Root_publication_binding': 'existing Main role provenance validates actual Root Scope/assembler owner/roles; refs must match its pinned origins. No new schema authority invented.',
        'current4_order': ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json'],
        'current4_rule': 'future actual full pins at review entry, held only during the review and closed in finally; never a hardcoded CP385/CP386 grant',
        'resource_refs_rule': 'absolute public refs3, unique canonical file paths; cover bundle, immutable context, all reader inputs, current4, raw consumer streams, role/audit/Scope origins, locked tools, source modules and basis; aliases rejected by SourceReadGuard',
        'routes': [list(item) for item in routes], 'consumer_result_schema': 'researchos.w09-bridge-consumers.v1',
        'consumer_checks': ['six unique current CM40 routes', 'six actual process exit0, timeoutfalse, errorsnone',
                            'all Job assigned-before-resume/primary exit/idle0/handles closed/errors[]',
                            'stdout single JSON receipt path equals same row receipt', 'all receipt revisions equal current context CM40',
                            'existing Main dispatcher/source/toolchain/Native/role/raw gates unchanged'],
        'GLOBAL': {'cases': ['C19', 'A06'], 'each_case_types': sorted(namespace['GLOBAL_TYPES']), 'total_documents': 8,
                   'same_context_fields': ['acceptance_baseline_ref', 'version_vector', 'registered_commands', 'global_evidence_refs'],
                   'A06-02': 'nonempty pinned actual refusal evidence required by Main'},
        'review_schema': 'researchos.w09.independent-review.v1',
        'verdict_ids': ['C19-01', 'C19-02', 'C19-03', 'A06-01', 'A06-02', 'A06-03', 'W09-G01', 'W09-G02'],
        'verdict_rule': 'six GLOBAL actual/expected exactly same proven rows; G01/G02 exact actual mode/run plus report /assertion_results raw pointer; no aggregate-only acceptance',
        'time_order': 'Native start <= Go first <= Go last <= Native end <= dispatcher start <= dispatcher end <= context.created_at <= review.issued_at <= actual Root received <= Root capture <= issuance observed <= owner accepted',
        'phase_one_future_argv': ['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I', '-S', '-B', '-X', 'utf8', source_ref['path'], '--input', '<actual immutable bundle path>', '--input-sha256', '<actual full64sha>', '--input-bytes', '<actual integer bytes>', '--output-root', '<new direct child of this preparation directory>'],
        'phase_one_rule': 'later Root-authorized independent actual task only; verifies closed six formal consumers + final immutable context, publishes Backup review only after all Main pure gates and held-resource closure',
        'phase_two_rule': 'Backup sends true ordinary FINAL with actual review ref and context SHA; only Root captures the real header/metadata/backend Final after delivery, registers the fixed capture index, emits researchos.w09.root-observed-issuance.v1, supplies prospective owner and invokes existing Bridge check/derive. This caller never does them.',
        'Main_original_provenance': 'actual Root 3LF sessionheader+metadata+adjacent backend Final; actual sender raw Backup, recipient Root, client_authoredfalse, exact Main timestamp/id/ordinal/offset/hash rules; no substitute synthetic Source audit',
        'future_capture_index': None, 'future_Root_issuance_ref': None, 'future_owner_acceptance_ref': None,
        'OPEN': ['immutable assembled context_ref', 'six actual formal consumer rows and OwnedJob observations',
                 'C19/A06 eight assembled GLOBAL refs', 'actual Scope/assembly owner/role publication plus captures',
                 'future dynamic current4 and complete public resource refs', 'post-review real FINAL/Root capture/index/issuance/owner'],
        'Root_stages_called': 0, 'Native_calls': 0, 'Go_calls': 0, 'SQLite_calls': 0, 'model_calls': 0,
        'TP_calls': 0, 'Main_Canon_Scope_writes': 0, 'formal_acceptance': False, 'execution_grant': False,
        'previous_success_not_replayed': 'all four NF6 actual Native facts, six qualified Modes, BR6 author22 and nonauthor24+2 controls; old3905/19module/native Source checks',
    }
    contract_ref = save('input-contract.json', contract)
    template_ref = save('future-input.OPEN.json', future_input)
    controls_ref = save('new-pure-controls.json', {'schema': 'researchos.w09-br6-review-preparation-pure-controls.v1',
        'control_kind': 'SYNTHETIC_SOURCE_ONLY_NOT_FORMAL', 'checks': checks, 'count': len(checks),
        'caller_actual_entry_called': False, 'review_document_emitted': False, 'formal_acceptance': False})
    raw = GUARD.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    module = types.ModuleType('br6_prepare_close_guard'); module.__file__ = str(GUARD)
    exec(compile(raw, str(GUARD), 'exec'), module.__dict__)
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    try:
        guard.acquire([source_ref, contract_ref, template_ref, controls_ref, pin(Q / 'basis.json')])
        assert guard.get_buffer(source_ref['path']) == source_raw
    finally:
        close = guard.close()
        close_ref = save('new-source-SourceGuard.closed.json', close)
    assert close['closed'] and close['retained_handles_count'] == 0 and close['errors'] == []
    result = save('preparation.result.json', {'schema': 'researchos.w09-br6-formal-actual-review-preparation.v1',
        'status': 'PREPARED_NOT_EXECUTED_WAITING_ROOT_ACTUAL_INPUTS', 'caller_ref': source_ref,
        'contract_ref': contract_ref, 'future_input_template_ref': template_ref, 'controls_ref': controls_ref,
        'guard_ref': close_ref, 'controls_passed': len(checks), 'real_future_review_ref': None,
        'formal_acceptance': False, 'execution_grant': False, 'Main_Canon_Scope_writes': 0})
    print(json.dumps({'result_ref': result, 'caller_ref': source_ref, 'contract_ref': contract_ref,
                      'controls_count': len(checks), 'closed': close['closed'], 'retained_handles_count': 0}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    try:
        code = main()
    except BaseException:
        traceback.print_exc(); code = 1
    print('ROOT_PYTHON_EXIT=' + str(code))
    sys.exit(code)
