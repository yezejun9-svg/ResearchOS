"""Publish bounded readonly bundle guidance; do not call any review/stage."""
import ast
import hashlib
import json
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
P = R / 'execution/v2.4/receipts/W09/W09-99/w09_br8_formal_actual_review_codex/prepare-20261010-01'
ATTACH = R / 'execution/v2.4/receipts/W09/W09-99/w09_br8_postactivation_call_preparation_codex/prepare-20261010-01'
CONTRACT_REF = {'path': str(P / 'input-contract.json'), 'sha256': 'f332836db8cfd6cf19e7b6b427cc059843e652820b74d95519085ff9f9811ecb', 'bytes': 22062}
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}

def ref(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(item):
    raw = Path(item['path']).read_bytes()
    if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('readonly guidance source pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('new readonly guidance member exists: ' + name)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

guard = None
error = None
guide = None
try:
    contract = json.loads(checked(CONTRACT_REF))
    known_ref = ref(ATTACH / 'known-inputs.json')
    known = json.loads(checked(known_ref))
    template_ref = ref(ATTACH / 'review-input.template.json')
    inputs = [CONTRACT_REF, contract['caller_ref'], contract['basis_ref'], contract['Main_profile_ref'], contract['Main_api_ref'], template_ref, known_ref, ref(ATTACH / 'FIELD_GUIDE.md'), ref(ATTACH / 'HDF.json'), ref(ATTACH / 'MF.json'), known['bridge'], ref(R / 'ops/ci/w09_evidence_closure.py'), GUARD_REF]
    module = types.ModuleType('br8_bundle_guidance_guard')
    module.__file__ = GUARD_REF['path']
    sys.modules[module.__name__] = module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), module.__dict__)
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire(inputs)
    buffers = {Path(item['path']).name: bytes(guard.get_buffer(item['path'])) for item in inputs}
    template = json.loads(buffers['review-input.template.json'])
    source_tree = ast.parse(buffers['br8_actual_review.source.py'].decode('utf-8'))
    main_tree = ast.parse(buffers['formal_profile_w09.py'].decode('utf-8'))
    api_tree = ast.parse(buffers['formal_case_index.py'].decode('utf-8'))
    bridge_tree = ast.parse(buffers['w09_root_bridge.source.py'].decode('utf-8'))
    def nodes(tree):
        return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    source_nodes, main_nodes, api_nodes, bridge_nodes = map(nodes, (source_tree, main_tree, api_tree, bridge_tree))
    vector = main_nodes['_vector']
    groups = next(ast.literal_eval(node.iter) for node in vector.body if isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == 'group')
    if set(template) != set(contract['input_fields']) or template['schema'] != contract['input_schema'] or tuple(groups) != ('spec_files', 'source_files', 'input_files', 'lock_files', 'tool_files'):
        raise ValueError('observed template or Main vector resource structure differs')
    def cited(item, node):
        return {'source_ref': item, 'line_start': node.lineno, 'line_end': node.end_lineno}
    reader = api_nodes['Reader']
    reader_methods = {node.name: node for node in reader.body if isinstance(node, ast.FunctionDef)}
    refs = {
        'bundle_validation': cited(contract['caller_ref'], source_nodes['validate_bundle']),
        'actual_resource_admission_and_final_reader_closure': cited(contract['caller_ref'], source_nodes['review_actual']),
        'five_vector_arrays': cited(contract['Main_profile_ref'], main_nodes['_vector']),
        'role_provenance_and_current_registry': cited(contract['Main_profile_ref'], main_nodes['_role_registry']),
        'raw_three_lines_and_typed_original_ranges': cited(contract['Main_profile_ref'], main_nodes['_role_audit']),
        'Native_reports_streams_owned_members_Source21_modes': cited(contract['Main_profile_ref'], main_nodes['_native']),
        'six_dispatches_input_versions_and_raw': cited(contract['Main_profile_ref'], main_nodes['_dispatches']),
        'eight_GLOBAL_and_refusal_refs': cited(contract['Main_profile_ref'], main_nodes['_global']),
        'all_reader_hashes_finish': cited(contract['Main_api_ref'], reader_methods['finish']),
        'whole_owned_raw_inventory': cited(contract['Main_api_ref'], api_nodes['_owned_inventory']),
        'typed_audit_range_recheck': cited(contract['Main_api_ref'], api_nodes['_audit_range']),
        'assemble_snapshot_then_new_context': cited(known['bridge'], bridge_nodes['assemble']),
        'snapshot_excludes_Canon_and_preserves_ranges': cited(known['bridge'], bridge_nodes['snapshot']),
    }
    guide = {
        'schema': 'researchos.w09-br8-formal-review-bundle-readonly-guidance.v1',
        'decision': 'READONLY_GUIDANCE_WAITING_ROOT_IMMUTABLE_ACTUAL_BUNDLE_AND_NONAUTHOR_SOURCE_REVIEW',
        'author_id': 'codex:/root/backup_regression_resources',
        'backend_actor': '/root/backup_regression_resources',
        'source_inputs': inputs,
        'source_line_refs': refs,
        'input_schema': contract['input_schema'],
        'exact_top_level_fields': contract['input_fields'],
        'Attach_template_ref': template_ref,
        'Attach_template_matches_current_v4_shape': True,
        'Attach_template_v3_self_reference_notice_is_historical': True,
        'deterministic_fields': {
            'schema': contract['input_schema'],
            'context_ref_shape': {'path': 'final assemble result.context_ref: repository relative POSIX', 'sha256': 'actual complete 64 lowerhex; no bytes key'},
            'consumer_result_ref': 'actual consume result.json: exact absolute path/sha256/bytes; schema researchos.w09-bridge-consumers.v1; six unique current CM40 processes/receipts',
            'root_publication_refs': {'scope': 'actual assembly Scope ref3, not consumer Scope', 'owner': 'actual assembly owner ref3 matching EVIDENCE_ASSEMBLER raw origin', 'roles': 'actual registered fixed roles file ref3 equal context.role_policy.registry_ref', 'actual_root_captures': 'nonempty list of actual existing origin/call/delivery capture refs3; source declarations cannot replace real origin'},
            'current4_refs': 'four actual current refs3 in checkpoint/path_ownership/step_state/commands order, exact canonical live paths at future review entry; archives do not substitute these four',
            'native_mode_qualification_ref': contract['existing_NF6_qualification_ref'],
            'resource_refs': 'nonempty absolute public refs3 with unique canonical physical paths; exact hashes/bytes; excludes final bundle own canonical path',
        },
        'resource_array_sources': [
            'context.version_vector.spec_files/source_files/input_files/lock_files/tool_files; component adapter/policy refs remain pinned to this vector',
            'context.source_coverage and whole declared current Go source inventory; exact Native Source21 pins declared by producer refs',
            'six context.registered_commands receipt/native_report/native_tool_run/mode_decision refs',
            'each dispatcher receipt.input_versions, stdout/stderr, executable tool; six consumer process stdout_ref/stderr_ref files',
            'each Native report.raw_evidence_references two streams, owned_export.members complete .raw inventory, assertion owned exports',
            'each mode independent_review_ref and optional real host_witness/junction_witness; role registry.provenance raw origins and actual_audit_ref plus original_capture_ref',
            'context.global_evidence_refs C19/A06 each four documents in run_receipt/version_manifest/command_receipt/assertion_results insertion order; each assertion raw_evidence_refs and refusal_evidence_refs',
            'locked Go/Python files used by existing Main local_tool, frozen acceptance/spec/plan, trusted router/closure/producer/Main/API sources',
        ],
        'exact_resource_closure_recipe': [
            'Use actual assemble result.dependency_snapshot.files as an observed lower bound: for every path/hash obtain actual integer bytes and verify file pin. This snapshot intentionally excludes Canon and was taken before saving final context.',
            'Add exact final context file ref3, actual consumer result and six process stdout/stderr, Root publication Scope/owner/roles/capture refs3, current4 refs3, existing NF6 qualification, copied v4 basis ref3 and pinned Main/API refs3.',
            'Add all transitive reader documents/tool/raw files from the concrete arrays above and all resources declared in the existing Source calling contract. Include the exact external K-package execution.plan.json read by v4.',
            'Dedupe identical physical paths only if SHA/bytes match; conflicting pins or canonical aliases represented as separate resources reject. Preserve literal source references; metadata resource path is absolute canonical file path.',
            'Do not convert dependency_snapshot.audit_ranges into whole-file resource refs. They have offset/bytes/range SHA and remain separately checked by Main original-range gates; do not hash or hold the whole active Root audit.',
            'Finish immutable bundle first, compute external input_ref from final bytes, pass it via CLI. Do not put input_ref inside resource_refs. Caller holds [input_ref,*resources] and rejects self canonical path even with conflicting hash/bytes.',
            'Final acceptance of resource closure is exact Main Reader.read_hashes -> authorized same canonical path and hash after reader.finish, complete unchanged owned inventory, then SourceGuard.closed=true/retained_handles=0/errors[].',
        ],
        'fixed_refs_available_from_current_contract': {'caller_ref': contract['caller_ref'], 'basis_ref': contract['basis_ref'], 'Main_profile_ref': contract['Main_profile_ref'], 'Main_api_ref': contract['Main_api_ref'], 'plan_ref': contract['plan_ref'], 'existing_NF6_qualification_ref': contract['existing_NF6_qualification_ref'], 'existing_six_Mode_refs': contract['existing_six_Mode_refs']},
        'OPEN_only_actual_inputs_not_invented': [
            'non-author v4 Source decision and actual Root-received delivery before actual use',
            'closed consume result with six real current-CM40 dispatcher receipts/OwnedJob observations and streams',
            'actual registered role policy, assembly Scope/owner and true role origin captures',
            'assembled immutable final context and eight real GLOBAL documents after matching two routes per case',
            'fresh dynamic current4 pins and concrete transitive public resource manifest with bytes',
            'future bundle path/SHA/bytes and new direct child review output root',
            'after review only: Backup true FINAL, actual Root capture/index, issuance and prospective owner; these are not pre-entry bundle prerequisites',
        ],
        'unchanged_environment_boundary': 'Existing Native mode check compares root_path against tempfile.gettempdir(); future verifier process must use already required controlled TEMP/TMP C:/Users/yqyyds/.researchos/w09-native-v5, without moving/reproducing original Native roots.',
        'future_argv': contract['phase_one_future_argv'],
        'input_ref_external_and_independently_guarded': True,
        'Raw_role_actor': '/root/backup_regression_resources',
        'Root_executor_assembler': 'codex:/root',
        'Native_Mode_success_replayed': False,
        'Source_controls_replayed': False,
        'actual_formal_review_called': False,
        'Root_stages_Native_Go_SQL_model_TP_dispatcher_calls': 0,
        'Main_Canon_Scope_writes': 0,
        'live_Canon_or_audit_handles_held': False,
        'formal_acceptance': False,
        'execution_grant': False,
    }
except BaseException as failure:
    error = {'exception': repr(failure), 'traceback': traceback.format_exc()}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('SourceGuard.closed.json', closure)
    if error is not None:
        publish('guidance.failure.json', {'error': error, 'Source_guard_ref': closure_ref})

if error is not None:
    print(json.dumps({'error': error, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('readonly guidance Source guard not closed')
guide['Source_guard_ref'] = closure_ref
guide_ref = publish('bundle-guide.json', guide)
print(json.dumps({'guide_ref': guide_ref, 'Source_guard_ref': closure_ref, 'exact_fields': guide['exact_top_level_fields'], 'formal_acceptance': False, 'execution_grant': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
