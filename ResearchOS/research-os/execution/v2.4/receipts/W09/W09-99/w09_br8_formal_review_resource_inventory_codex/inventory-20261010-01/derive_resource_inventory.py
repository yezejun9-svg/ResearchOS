"""Derive public refs from closed actual documents; no Main/review execution."""
import hashlib
import json
import re
import sys
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
GUARD_REF = {'path': str(R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'), 'sha256': 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85', 'bytes': 11404}
SHA = re.compile(r'[0-9a-f]{64}')

def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(ref):
    raw = Path(ref['path']).read_bytes()
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('closed actual input pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable inventory member exists: ' + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

guard = None
failure = None
result = {}
try:
    shape = json.loads((HERE / 'actual-input-shapes.json').read_bytes())
    inputs = shape['input_refs']
    docs = {key: json.loads(checked(ref)) for key, ref in inputs.items()}
    assemble, consumer, contract = docs['assemble'], docs['consume'], docs['v4_contract']
    module = types.ModuleType('br8_actual_inventory_guard')
    module.__file__ = GUARD_REF['path']
    sys.modules[module.__name__] = module
    exec(compile(checked(GUARD_REF), GUARD_REF['path'], 'exec'), module.__dict__)
    canonical = module._canonical
    canon_slots = {canonical(str(R / 'execution/v2.4' / name)) for name in ('checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json')}
    ranges = assemble['dependency_snapshot']['audit_ranges']
    range_paths = {canonical(item['path']) for item in ranges}
    resources, origins, deferred = {}, {}, []
    def absolute(value):
        path = Path(value)
        return path if path.is_absolute() else R / path
    def resource(ref, origin):
        path = absolute(ref['path'])
        key = canonical(str(path))
        if key in canon_slots:
            deferred.append({'source': origin, 'path': str(path), 'reason': 'ROOT_LATER_DYNAMIC_CURRENT4_SLOT_NO_READ_OR_STAT'})
            return None
        if key in range_paths:
            raise ValueError('typed original audit path appeared as a whole-file resource')
        if type(ref.get('sha256')) is not str or SHA.fullmatch(ref['sha256']) is None:
            raise ValueError('resource expected complete lowerhex SHA')
        info = path.stat()
        if not path.is_file():
            raise ValueError('public inventory resource is not a regular file')
        value = {'path': str(path), 'sha256': ref['sha256'], 'bytes': info.st_size}
        if 'bytes' in ref and (type(ref['bytes']) is not int or ref['bytes'] != info.st_size):
            raise ValueError('declared public resource bytes differs from file metadata')
        if key in resources and (resources[key]['sha256'], resources[key]['bytes']) != (value['sha256'], value['bytes']):
            raise ValueError('actual public inventory pin conflict')
        resources.setdefault(key, value)
        origins.setdefault(key, []).append(origin)
        return resources[key]
    for path, digest in assemble['dependency_snapshot']['files'].items():
        resource({'path': path, 'sha256': digest}, 'assemble.dependency_snapshot.files')
    context_ref = resource(assemble['context_ref'], 'assemble.final_context_ref')
    context = json.loads(checked(context_ref))
    roles_ref = resource(context['role_policy']['registry_ref'], 'context.role_policy.registry_ref')
    if roles_ref['sha256'] != '47eb31c89aa2177dd8c12285783399fa711d87bc21a37af0642e8d4ededb0f22' or roles_ref['bytes'] != 8291:
        raise ValueError('Root published registry pin differs')
    registry = json.loads(checked(roles_ref))
    assembler = next(proof for proof in registry['provenance'] if proof['role'] == 'EVIDENCE_ASSEMBLER')
    owner_ref = resource(assembler['raw_ref'], 'registry.EVIDENCE_ASSEMBLER.raw_ref')
    owner = json.loads(checked(owner_ref))
    scope_ref = resource(owner['scope_ref'], 'assembly.owner.scope_ref')
    checked(scope_ref)
    finite_guard_refs = [*inputs.values(), context_ref, roles_ref, owner_ref, scope_ref, GUARD_REF]
    captures, global_refs = [], []
    for index, proof in enumerate(registry['provenance']):
        audit_ref = resource(proof['actual_audit_ref'], 'roles.provenance.actual_audit_ref')
        audit = json.loads(checked(audit_ref))
        raw_ref = resource(audit['original_capture_ref'], 'roles.provenance.actual_audit.original_capture_ref')
        checked(raw_ref)
        finite_guard_refs.extend([audit_ref, raw_ref])
        captures.extend([audit_ref, raw_ref])
        resource(proof['raw_ref'], 'roles.provenance.raw_ref')
    for case, documents in context['global_evidence_refs'].items():
        for name, raw_ref in documents.items():
            global_ref = resource(raw_ref, 'context.global_evidence_refs.' + case + '.' + name)
            checked(global_ref)
            finite_guard_refs.append(global_ref)
            global_refs.append({'case_id': case, 'type': name, 'ref': global_ref})
    consumer_ref = resource(inputs['consume'], 'bundle.consumer_result_ref')
    for index, process in enumerate(consumer['processes']):
        for channel in ('stdout_ref', 'stderr_ref'):
            stream_ref = resource(process[channel], 'consumer.processes.' + str(index) + '.' + channel)
            checked(stream_ref)
            finite_guard_refs.append(stream_ref)
    for key in ('caller_ref', 'basis_ref', 'Main_profile_ref', 'Main_api_ref', 'plan_ref', 'existing_NF6_qualification_ref'):
        resource(contract[key], 'v4_contract.' + key)
    resource(inputs['v4_contract'], 'v4.input-contract')
    resource(inputs['assemble'], 'Root.closed_assemble_result')
    resource(inputs['proposal'], 'Root.original_proposal_result')
    resource(GUARD_REF, 'v4.SourceReadGuard')
    # This finite Guard validates only new parent/stream pins. Previous 2080-file
    # hashes/Native checks are inherited from closed Root snapshot, not replayed.
    unique_finite = {canonical(ref['path']): ref for ref in finite_guard_refs}
    guard = module.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    guard.acquire(list(unique_finite.values()))
    capture_refs = list({canonical(ref['path']): ref for ref in captures}.values())
    ordered = [resources[key] for key in sorted(resources)]
    result = {
        'schema': 'researchos.w09-br8-formal-review-public-resource-inventory.v1',
        'decision': 'PREPARED_PUBLIC_REFS_WITH_ROOT_DYNAMIC_CURRENT4_PENDING_NOT_ACTUAL_REVIEW',
        'author_id': 'codex:/root/backup_regression_resources',
        'backend_actor': '/root/backup_regression_resources',
        'source_input_refs': inputs,
        'context_ref2': assemble['context_ref'],
        'context_resource_ref3': context_ref,
        'consumer_result_ref': consumer_ref,
        'root_publication_refs': {'scope': scope_ref, 'owner': owner_ref, 'roles': roles_ref, 'actual_root_captures': capture_refs},
        'native_mode_qualification_ref': contract['existing_NF6_qualification_ref'],
        'resource_refs': ordered,
        'resource_count': len(ordered),
        'resource_origin_rows': [{'ref': resources[key], 'origins': origins[key]} for key in sorted(resources)],
        'snapshot_files_count': len(assemble['dependency_snapshot']['files']),
        'snapshot_inventory_count': len(assemble['dependency_snapshot']['inventories']),
        'original_typed_audit_range_count': len(ranges),
        'typed_audit_range_whole_file_refs_added': 0,
        'GLOBAL_actual_refs': global_refs,
        'deferred_current4_source_refs': deferred,
        'later_Root_current4_refs': None,
        'current4_rule': 'Root supplies four actual fresh refs3 after its pending diagnostic registration; append exactly those to resource_refs before final immutable bundle bytes/pin. Never substitute historical archives or their old hashes.',
        'snapshot_hash_validation': 'Inherited exact hashes from closed actual Root snapshot; current file size/path metadata observed. No blanket replay of prior snapshot full-file hashes; future v4 SourceReadGuard independently checks every resource.',
        'new_finite_guard_input_count': len(unique_finite),
        'input_bundle_self_ref': None,
        'Root_future_input_ref_rule': 'Compute final bundle SHA/bytes externally; exclude its canonical path from resource_refs; caller independently holds input_ref.',
        'Raw_uint64_FILETIME_copied_via_Python_no_JS_number': True,
        'Private_OWNER_or_credentials_read_or_hashed': False,
        'live_Canon_or_whole_audit_read_or_held': False,
        'actual_review_called': False,
        'Root_stages_Main_functions_Native_Go_SQL_TP_dispatcher_model_calls': 0,
        'Main_Canon_Rootbundle_writes': 0,
        'formal_acceptance': False,
        'execution_grant': False,
    }
except BaseException as error:
    failure = {'exception': repr(error), 'traceback': traceback.format_exc()}
finally:
    closure = guard.close() if guard is not None else {'closed': None, 'retained_handles_count': None, 'errors': [], 'status': 'NOT_ACQUIRED'}
    closure_ref = publish('inventory-SourceGuard.closed.json', closure)
    if failure is not None:
        publish('inventory.failure.json', {'error': failure, 'Source_guard_ref': closure_ref})

if failure is not None:
    print(json.dumps({'error': failure, 'Source_guard_ref': closure_ref}, ensure_ascii=False))
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit(1)
if closure.get('closed') is not True or closure.get('retained_handles_count') != 0 or closure.get('errors'):
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise SystemExit('public inventory finite Source guard not closed')
result['Source_guard_ref'] = closure_ref
inventory_ref = publish('resource-inventory.json', result)
print(json.dumps({'inventory_ref': inventory_ref, 'Source_guard_ref': closure_ref, 'resource_count': result['resource_count'], 'snapshot_files_count': result['snapshot_files_count'], 'typed_audit_ranges': result['original_typed_audit_range_count'], 'GLOBAL_refs': len(result['GLOBAL_actual_refs']), 'root_publication_refs': result['root_publication_refs'], 'context_ref': result['context_ref2'], 'current4_refs': None, 'formal_acceptance': False}, ensure_ascii=False))
print('ROOT_PYTHON_EXIT=0', flush=True)
