import hashlib, importlib.util, json, ntpath, sys, traceback
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
Q = Path(__file__).resolve().parent
C = R / 'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
G = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
W = R / 'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public22-main23-continuation-source.actual-audit.root.json'

def pin(p):
    raw = Path(p).read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, obj):
    path = Q / name
    with path.open('xb') as f: f.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def norm(path): return ntpath.normcase(ntpath.normpath(str(path)))

def load(ref, name):
    spec = importlib.util.spec_from_file_location(name, ref['path'])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def walk(value, path=''):
    yield path, value
    if type(value) is dict:
        for key, child in value.items(): yield from walk(child, path + '/' + key)
    elif type(value) is list:
        for key, child in enumerate(value): yield from walk(child, path + '/' + str(key))

def main():
    h = json.loads((C / 'HDF.json').read_bytes())
    i = json.loads(Path(h['source_inputs_ref']['path']).read_bytes())
    manifest = json.loads(Path(i['runtime_resources_ref']['path']).read_bytes())
    witness = json.loads(W.read_bytes())
    refs = [pin(C / 'HDF.json'), pin(C / 'MF.json'), h['caller_ref'], h['source_inputs_ref'], h['calling_contract_ref'],
            *i['source_resource_refs'], *manifest['resource_refs'], pin(G), pin(W), witness['original_capture_ref']]
    refs.extend(v for v in i.values() if type(v) is dict and set(v) == {'path', 'sha256', 'bytes'})
    # No private key/database operation, live Canon observation or live Root audit access is authorized here.
    forbidden = {norm(R / ('execution/v2.4/' + name + '.json')) for name in ('checkpoint', 'path_ownership', 'step_state', 'commands')}
    forbidden.add(norm(R / 'ops/ci/retrieval.py'))
    unique = {}
    for ref in refs:
        key = norm(ref['path'])
        if key in forbidden or '\\private\\' in key or '\\.codex\\sessions\\' in key or key.endswith(('.key', 'owner.token')):
            raise ValueError('FORBIDDEN_RESOURCE_PREACQUIRE')
        if key in unique and (unique[key]['sha256'], unique[key]['bytes']) != (ref['sha256'], ref['bytes']):
            raise ValueError('CONFLICTING_PUBLIC_PIN')
        unique[key] = ref
    guard_mod = load(pin(G), 'p22c_runtime_resource_guard')
    guard = guard_mod.SourceReadGuard(per_file_cap=128 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    result = dict(schema='researchos.public22-continuation-source-runtime-resource-closure.v1',
                  source_resource_refs=i['source_resource_refs'], runtime_resources_ref=i['runtime_resources_ref'],
                  requested_unique_resources=len(unique), current_canonical_observed=False,
                  non_W05_adopted_Main_target_held=False, private_owner_file_read=False,
                  SQL_connection_opened=False, product_process_created=False, future_execution_grant=False)
    primary = None
    try:
        guard.acquire(list(unique.values()))
        import sqlite3, _sqlite3
        owned = load(i['owned_job_ref'], 'p22c_passive_loaded_runtime')
        loaded = owned.runtime_resource_paths()
        runtime = {norm(r['path']): r for r in manifest['resource_refs']}
        observed_paths = {norm(p): str(p) for p in loaded}
        observed_paths[norm(sys.executable)] = sys.executable
        observed_paths[norm(_sqlite3.__file__)] = _sqlite3.__file__
        instrumentation = {norm(__file__), norm(G), norm(i['owned_job_ref']['path'])}
        for mod in tuple(sys.modules.values()):
            for attr in ('__file__', '__cached__'):
                p = getattr(mod, attr, None)
                if type(p) is str and Path(p).is_file() and norm(p) not in instrumentation:
                    observed_paths[norm(p)] = p
        covered = [runtime[key] for key in sorted(observed_paths) if key in runtime]
        missing = [observed_paths[key] for key in sorted(observed_paths) if key not in runtime]
        result['loaded_resource_refs_from_exact_runtime_manifest'] = covered
        result['loaded_resources_missing_from_runtime_manifest'] = missing
        result['review_instrumentation_only_refs'] = [pin(__file__), pin(G), i['owned_job_ref']]
        result['locked_runtime_flags'] = dict(isolated=sys.flags.isolated, no_site=sys.flags.no_site, dont_write_bytecode=sys.dont_write_bytecode, utf8=sys.flags.utf8_mode)
        result['locked_python_ref'] = pin(sys.executable)
        result['resource_qualification_status'] = 'PUBLIC_STATIC_AND_CURRENT_LOADED_RUNTIME_CLOSURE_VERIFIED' if not missing else 'PUBLIC_STATIC_CLOSURE_VERIFIED_LOADED_RUNTIME_NOT_COMPLETE'
        raw = guard.get_buffer(witness['original_capture_ref']['path'])
        lines = raw.splitlines(keepends=True)
        if len(lines) != 3: raise ValueError('EXACT_AUTHOR_THREE_LF_REQUIRED')
        if [hashlib.sha256(line).hexdigest() for line in lines] != witness['original_line_sha256']:
            raise ValueError('AUTHOR_RAW_LINE_HASH_BINDING')
        parsed = [json.loads(line) for line in lines]
        result['author_witness_ref'] = pin(W)
        result['author_raw_ref'] = witness['original_capture_ref']
        result['author_raw_field_shapes'] = [{p: list(v) for p, v in walk(line) if type(v) is dict} for line in parsed]
        result['author_raw_selected_identity_values'] = [{p: v for p, v in walk(line) if p.rsplit('/', 1)[-1] in
            ('type', 'author', 'sender', 'recipient', 'thread_id', 'id', 'client_authored', 'timestamp')} for line in parsed]
        result['author_witness_exact_bindings'] = dict(actor_id=witness['actor_id'], Root_thread_id=witness['Root_thread_id'], binding_sha256=witness['binding_sha256'])
    except BaseException as exc:
        primary = dict(type=type(exc).__name__, message=str(exc))
        traceback.print_exc()
    finally:
        cleanup = guard.close()
        close_ref = save('complete-resource-sourceguard.closed.json', cleanup)
        result['guard_cleanup_ref'] = close_ref
        result['guard_cleanup'] = cleanup
        result['primary_error'] = primary
        result_ref = save('complete-resource-closure.json', result)
        print(json.dumps(dict(resource_closure_ref=result_ref, guard_cleanup_ref=close_ref,
                             verified_resources=sum(x['verified'] for x in cleanup['entries']),
                             resource_qualification_status=result.get('resource_qualification_status'),
                             loaded_missing=result.get('loaded_resources_missing_from_runtime_manifest'),
                             author_fields=result.get('author_raw_selected_identity_values'),
                             primary_error=primary, closed=cleanup['closed'], retained_handles=cleanup['retained_handles_count']), ensure_ascii=False))
    return 1 if primary is not None or not cleanup['closed'] or cleanup['errors'] else 0

if __name__ == '__main__':
    rc = 1
    try: rc = main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT=' + str(rc))
    sys.exit(rc)
