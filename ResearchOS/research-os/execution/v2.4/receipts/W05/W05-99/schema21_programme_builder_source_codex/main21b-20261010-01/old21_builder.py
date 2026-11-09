"""Source-only old21 control/backup builder; no entrypoint executes on import.

The separately reviewed live Root scope owns registration, resource qualification,
runtime closure and actual host provenance. A build result is never acceptance.
"""
from __future__ import annotations
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import time
import types

AUTHOR = 'codex:/root/native_temp_independent_review'
COMMIT = 'f6e4a0ed54d697c7214a75743cd1b83dc3685ddb'
TREE = '9696c3a456a4786cbb5518c75ead66e6d8120a83'
REF_KEYS = {'path', 'sha256', 'bytes'}
TARGETS = {'control': 'apps/control', 'backup': 'ops/backup'}
ROOT_METHODS = ('require_registered', 'require_resources', 'require_phase', 'receipt_context')

class BoundaryError(RuntimeError):
    pass

def require(value, code):
    if not value: raise BoundaryError(code)

def observed_ref(path):
    raw = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def load_pinned(ref, name):
    require(isinstance(ref, dict) and set(ref) == REF_KEYS, 'EXACT_REF_REQUIRED')
    require(type(ref['bytes']) is int and 0 < ref['bytes'] <= 1024 * 1024, 'HELPER_SIZE_INVALID')
    require(observed_ref(ref['path']) == ref, 'HELPER_PIN_MISMATCH')
    module = types.ModuleType(name)
    exec(compile(Path(ref['path']).read_bytes(), ref['path'], 'exec'), module.__dict__)
    return module

def require_live_scope(scope):
    require(scope is not None and not isinstance(scope, dict), 'LIVE_ROOT_SCOPE_REQUIRED')
    require(all(callable(getattr(scope, name, None)) for name in ROOT_METHODS), 'ROOT_SCOPE_INTERFACE_REQUIRED')

def compile_request(contract, request, base):
    require(isinstance(request, dict) and set(request) == {'case_id', 'output_root'}, 'REQUEST_FIELDS_INVALID')
    require(type(request['case_id']) is str and re.fullmatch('[0-9a-f]{32}', request['case_id']) is not None, 'CASE_ID_INVALID')
    require(contract['source_author'] == AUTHOR and type(contract['schema_version']) is int and contract['schema_version'] == 21, 'SOURCE_CONTRACT_INVALID')
    require(contract['source_commit'] == COMMIT and contract['source_tree'] == TREE, 'HISTORICAL_COMMIT_TREE_REQUIRED')
    expected = ntpath.join(contract['output_parent'], 'old21-build-' + request['case_id'])
    require(base.regular_absolute(request['output_root']) == base.regular_absolute(expected), 'OUTPUT_SCOPE_ESCAPE')
    root = request['output_root']
    # frozen_main is an inherited helper key, pointing only at the new historical source copy.
    paths = {'root': root, **{n: ntpath.join(root, n) for n in ['frozen_main', 'module_cache', 'gocache', 'gopath', 'tmp', 'raw']}}
    paths['control_program'] = ntpath.join(root, 'old21-control.exe')
    paths['backup_program'] = ntpath.join(root, 'old21-backup.exe')
    go = contract['go_ref']['path']
    phases = [dict(id='go-version', target=None, kind='version', argv=[go, 'version'], timeout=30)]
    for target, package in TARGETS.items():
        for kind, argv, timeout in [
            ('declared', [go, 'list', '-deps', '-compiled', '-json', './' + package], 120),
            ('export', [go, 'list', '-deps', '-compiled', '-export', '-json', './' + package], 600),
            ('build', [go, 'build', '-x', '-work', '-o', paths[target + '_program'], './' + package], 600),
            ('inspect', [go, 'version', '-m', paths[target + '_program']], 30),
        ]:
            phases.append(dict(id=target + '-' + kind, target=target, kind=kind, argv=argv, timeout=timeout))
    return {'paths': paths, 'phases': phases}

def validate_resource_binding(binding, contract, base):
    keys = {'input_manifest_ref', 'source_review_ref', 'resource_qualification_ref', 'runtime_manifest_ref', 'outer_host_binding_ref', 'source_author', 'reviewer_actor'}
    require(isinstance(binding, dict) and set(binding) == keys, 'QUALIFIED_RESOURCE_BINDING_REQUIRED')
    for name in keys - {'source_author', 'reviewer_actor'}: base.exact_ref(binding[name])
    require(binding['input_manifest_ref'] == contract['input_manifest_ref'], 'RESOURCE_MANIFEST_BINDING_MISMATCH')
    require(binding['source_author'] == AUTHOR, 'SOURCE_AUTHOR_BINDING_MISMATCH')
    reviewer = binding['reviewer_actor']
    require(type(reviewer) is str and re.fullmatch(r'codex:/root/[a-z0-9_]+(?:/[a-z0-9_]+)*', reviewer) is not None and reviewer != AUTHOR, 'INDEPENDENT_NONAUTHOR_SOURCE_REVIEW_REQUIRED')
    return binding

def validate_source_manifest(contract, manifest, inventory, base, common):
    require(inventory.get('source_commit') == COMMIT and inventory.get('source_tree') == TREE, 'HISTORICAL_COMMIT_TREE_REQUIRED')
    require(manifest.get('source_commit') == COMMIT and manifest.get('source_tree') == TREE, 'HISTORICAL_COMMIT_TREE_REQUIRED')
    objects = inventory.get('objects')
    require(isinstance(objects, list) and len(objects) == contract['historical_source_file_count'], 'HISTORICAL_SOURCE_COUNT_MISMATCH')
    by_name = {}
    for obj in objects:
        require(isinstance(obj, dict) and set(obj) == {'git_path', 'git_blob', 'sha256', 'bytes', 'mode', 'ref'}, 'SOURCE_OBJECT_FIELDS_INVALID')
        name = common.relative_file(obj['git_path'])
        require(name not in by_name, 'SOURCE_OBJECT_DUPLICATE')
        require(type(obj['git_blob']) is str and re.fullmatch('[0-9a-f]{40}', obj['git_blob']) is not None and obj['mode'] in ('100644', '100755'), 'SOURCE_GIT_OBJECT_INVALID')
        base.exact_ref(obj['ref'])
        require(type(obj['bytes']) is int and obj['bytes'] == obj['ref']['bytes'] and obj['sha256'] == obj['ref']['sha256'], 'SOURCE_BLOB_PIN_MISMATCH')
        expected = ntpath.join(contract['historical_source_root'], *name.split('/'))
        require(base.regular_absolute(obj['ref']['path']) == base.regular_absolute(expected), 'SOURCE_OBJECT_PATH_ESCAPE')
        by_name[name] = obj
    sql = sorted(n for n in by_name if re.fullmatch(r'migrations/sqlite/[0-9]{4}_.+\.sql', n))
    require([int(Path(n).name[:4]) for n in sql] == list(range(1, 22)), 'EXACT_CONTIGUOUS_1_TO_21_REQUIRED')
    require('migrations/sqlite/next_v24_sessions.sql' in by_name, 'ORIGINAL_SESSION_ADDON_REQUIRED')
    runtime_names = sql + ['migrations/sqlite/next_v24_sessions.sql', 'spec/v2.0/contracts/domain.schema.json', 'spec/v2.0/contracts/openapi.json']
    require(len(runtime_names) == 24 and all(n in by_name for n in runtime_names), 'EXACT_RUNTIME_INPUTS_REQUIRED')
    require({n: by_name[n]['ref'] for n in runtime_names} == contract['runtime_source_refs'], 'ORIGINAL_RUNTIME_BYTE_PINS_REQUIRED')
    for name, expected in contract['public_bootstrap_source_refs'].items():
        require(name in by_name and by_name[name]['ref'] == expected, 'PUBLIC_BOOTSTRAP_SOURCE_PIN_MISMATCH')
    items = manifest.get('items')
    require(isinstance(items, list), 'SOURCE_INPUT_ITEMS_REQUIRED')
    found, unique = {}, set()
    for item in items:
        require(isinstance(item, dict) and set(item) == {'kind', 'relative_path', 'ref'}, 'INPUT_ITEM_FIELDS_INVALID')
        require(item['kind'] in ('historical_source', 'module', 'toolchain'), 'INPUT_KIND_INVALID')
        name = common.relative_file(item['relative_path']); base.exact_ref(item['ref'])
        key = (item['kind'], name.casefold())
        require(key not in unique, 'INPUT_PATH_DUPLICATE'); unique.add(key)
        if item['kind'] == 'historical_source':
            found[name] = item['ref']
        else:
            input_root = contract['module_source_root'] if item['kind'] == 'module' else contract['goroot']
            require(base.regular_absolute(item['ref']['path']) == base.regular_absolute(ntpath.join(input_root, *name.split('/'))), 'RESOURCE_INPUT_PATH_ESCAPE')
    require(found == {n: o['ref'] for n, o in by_name.items()}, 'SOURCE_MANIFEST_OBJECT_SET_MISMATCH')
    require(contract['go_ref'] in [x['ref'] for x in items if x['kind'] == 'toolchain'], 'GO_NOT_IN_INPUT_CLOSURE')
    return by_name

def validate_blob_bytes(objects, get_buffer):
    for name, obj in objects.items():
        raw = get_buffer(obj['ref']['path'])
        require(type(raw) is bytes and len(raw) == obj['bytes'] and hashlib.sha256(raw).hexdigest() == obj['sha256'], 'HISTORICAL_BLOB_SHA256_MISMATCH')
        require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == obj['git_blob'], 'HISTORICAL_GIT_BLOB_MISMATCH')
    return True

def source_membership(contract, objects, base):
    root = Path(contract['historical_source_root'])
    require(root.is_dir() and not root.is_symlink() and not root.is_junction(), 'HISTORICAL_SOURCE_ROOT_INVALID')
    actual = []
    for p in root.rglob('*'):
        require(not p.is_symlink() and not p.is_junction(), 'HISTORICAL_SOURCE_REPARSE_PROHIBITED')
        if p.is_file(): actual.append(base.regular_absolute(str(p)))
    expected = [base.regular_absolute(x['ref']['path']) for x in objects.values()]
    require(sorted(actual) == sorted(expected), 'HISTORICAL_SOURCE_MEMBERSHIP_DRIFT')
    return True

def declared_closure(packages, allowed_refs, paths, contract, base, common, target, need_exports):
    require(target in TARGETS, 'BUILD_TARGET_INVALID')
    allowed = {base.regular_absolute(r['path']): r for r in allowed_refs}
    rows, used, exports, names = [], {}, [], set()
    for package in packages:
        require(not package.get('Error') and not package.get('DepsErrors') and not package.get('Incomplete'), 'GO_LIST_INCOMPLETE')
        name = package.get('ImportPath')
        require(type(name) is str and name and name not in names and not package.get('ForTest'), 'PACKAGE_IDENTITY_INVALID'); names.add(name)
        folder = package.get('Dir')
        require(type(folder) is str and any(common.below(folder, r) or base.regular_absolute(folder) == base.regular_absolute(r) for r in [paths['frozen_main'], paths['module_cache'], contract['goroot']]), 'PACKAGE_DIR_OUTSIDE_FROZEN_INPUTS')
        selected = {}
        for field in common.FILE_FIELDS:
            values = package.get(field, []); require(isinstance(values, list), 'PACKAGE_FILES_INVALID'); selected[field] = []
            for value in values:
                require(type(value) is str, 'PACKAGE_FILES_INVALID')
                path = value if ntpath.isabs(value) else ntpath.join(folder, common.relative_file(value.replace('\\', '/')))
                key = base.regular_absolute(path); require(key in allowed, 'DECLARED_BUILD_INPUT_NOT_FROZEN')
                used[key] = allowed[key]; selected[field].append(key)
            selected[field].sort()
        module = package.get('Module') or {}
        require(isinstance(module, dict) and not module.get('Replace'), 'MODULE_REPLACEMENT_PROHIBITED')
        if module:
            modpath = module.get('GoMod')
            require(type(modpath) is str and base.regular_absolute(modpath) in allowed, 'MODULE_GOMOD_NOT_FROZEN')
            used[base.regular_absolute(modpath)] = allowed[base.regular_absolute(modpath)]
            if module.get('Main'):
                require(module.get('Path') == contract['module_path'], 'MAIN_MODULE_IDENTITY_MISMATCH')
            else:
                require(contract['module_versions'].get(module.get('Path')) == module.get('Version'), 'MODULE_VERSION_NOT_PINNED')
        rows.append({'ImportPath': name, 'Dir': base.regular_absolute(folder), 'Name': package.get('Name'), 'Standard': package.get('Standard', False), 'inputs': selected, 'Imports': sorted(package.get('Imports', [])), 'ImportMap': package.get('ImportMap', {}), 'module': {k: module.get(k) for k in ['Path', 'Version', 'Main', 'GoMod', 'Sum', 'GoModSum']}})
        if need_exports and name != 'unsafe':
            export = package.get('Export')
            require(type(export) is str and common.below(export, paths['gocache']) and ntpath.basename(export).endswith('-d'), 'EXPORT_NOT_IN_FRESH_GOCACHE')
            base.regular_absolute(export)
            require(type(package.get('BuildID')) is str and package['BuildID'], 'EXPORT_BUILD_ID_REQUIRED')
            exports.append(dict(ImportPath=name, path=export, BuildID=package['BuildID']))
    wanted = [x for x in rows if x['ImportPath'] == contract['module_path'] + '/' + TARGETS[target]]
    require(len(wanted) == 1 and wanted[0]['Name'] == 'main', 'TARGET_MAIN_PACKAGE_MISSING')
    return {'packages': sorted(rows, key=lambda x: x['ImportPath']), 'input_refs': [used[k] for k in sorted(used)], 'exports': sorted(exports, key=lambda x: x['ImportPath'])}

def verify_binary_metadata(raw, contract, target):
    require(target in TARGETS, 'BUILD_TARGET_INVALID')
    require(type(raw) is bytes and len(raw) <= 1024 * 1024, 'BINARY_METADATA_CAP')
    lines = raw.decode('utf-8').splitlines()
    require(lines and lines[0].endswith(': go1.27.1'), 'BINARY_GO_VERSION_MISMATCH')
    fields = [line.strip().split('\t') for line in lines[1:]]
    require([x for x in fields if x and x[0] == 'path'] == [['path', contract['module_path'] + '/' + TARGETS[target]]], 'BINARY_PACKAGE_IDENTITY_MISMATCH')
    settings = {x[1] for x in fields if len(x) == 2 and x[0] == 'build'}
    require({'CGO_ENABLED=0', 'GOOS=windows', 'GOARCH=amd64', 'GOAMD64=v1', '-trimpath=true'} <= settings, 'BINARY_BUILD_SETTINGS_MISMATCH')
    require(not any(x.startswith('vcs.') for x in settings), 'UNEXPECTED_EMBEDDED_VCS_IDENTITY')
    for field in fields:
        if field and field[0] == 'dep':
            require(len(field) >= 3 and contract['module_versions'].get(field[1]) == field[2], 'BINARY_DEPENDENCY_VERSION_MISMATCH')
    return True

def run_registered_build(contract_ref, request_ref, root_scope):
    """Runtime branch. Never called by author Source controls.

Root must hold this bootstrap and exact helper/contract refs before entry.
The live gate checks actual Root host provenance; serialized flags grant nothing.
"""
    require_live_scope(root_scope)
    root_scope.require_registered(contract_ref, request_ref, source_author=AUTHOR)
    require(observed_ref(contract_ref['path']) == contract_ref, 'CONTRACT_PIN_MISMATCH')
    contract = json.loads(Path(contract_ref['path']).read_bytes())
    base = load_pinned(contract['base_helper_ref'], 'old21_pinned_base')
    common = load_pinned(contract['common_builder_ref'], 'old21_pinned_build_primitives')
    base.exact_ref(contract_ref); base.exact_ref(request_ref)
    request = json.loads(base.read_exact(request_ref)); plan = compile_request(contract, request, base)
    binding = validate_resource_binding(root_scope.require_resources(contract_ref, contract['input_manifest_ref']), contract, base)
    paths = plan['paths']; root = Path(paths['root'])
    state = dict(schema='researchos.old21-build-observation.v1', status='STARTED', phase='prepare', case_id=request['case_id'], contract_ref=contract_ref, request_ref=request_ref, qualified_resource_binding=binding, source_commit=COMMIT, source_tree=TREE, calls=[], target_results={}, first_failure=None, root_created=False, prepared_directories=[], attempted_path=None, formal_acceptance=False, programme_qualification='PENDING_INDEPENDENT_NONAUTHOR', product_program_executions=0, SQL_calls=0, model_calls=0, original_failure_ordinal=None)
    guards, original_refs, copied, exports_all = [], [], [], []
    try:
        root_scope.require_phase('prepare', request_ref, paths['root'])
        state['root_context'] = root_scope.receipt_context()
        base._assert_output_ancestors(paths['root'])
        state['attempted_path'] = str(root); root.mkdir(); state['root_created'] = True; state['prepared_directories'].append(str(root))
        for name in ['frozen_main', 'module_cache', 'gocache', 'gopath', 'tmp', 'raw']:
            state['attempted_path'] = paths[name]; Path(paths[name]).mkdir(); state['prepared_directories'].append(paths[name])
        manifest = json.loads(base.read_exact(contract['input_manifest_ref']))
        inventory = json.loads(base.read_exact(contract['frozen_source_manifest_ref']))
        objects = validate_source_manifest(contract, manifest, inventory, base, common)
        original_refs = [x['ref'] for x in manifest['items']] + [contract_ref, request_ref, contract['builder_ref'], contract['input_manifest_ref'], contract['frozen_source_manifest_ref'], contract['common_builder_ref'], contract['base_helper_ref'], contract['source_guard_ref'], contract['owned_job_ref'], contract['toolchain_lock_ref']]
        original_refs += [binding[k] for k in ['source_review_ref', 'resource_qualification_ref', 'runtime_manifest_ref', 'outer_host_binding_ref']]
        guard_module = load_pinned(contract['source_guard_ref'], 'old21_source_guard')
        original = guard_module.SourceReadGuard(total_cap=512 * 1024 * 1024); guards.append(('original_inputs', original)); original.acquire(original_refs)
        validate_blob_bytes(objects, original.get_buffer); source_membership(contract, objects, base)
        state['source_before_ref'] = base.save_new(root / 'source.before.json', {'refs': original_refs, 'git_commit': COMMIT, 'git_tree': TREE})
        adapted = [{**x, 'kind': 'main' if x['kind'] == 'historical_source' else x['kind']} for x in manifest['items']]
        copied = common.copy_inputs(adapted, paths, original, base)
        frozen = guard_module.SourceReadGuard(total_cap=256 * 1024 * 1024); guards.append(('frozen_inputs', frozen)); frozen.acquire(copied)
        state['frozen_before_ref'] = base.save_new(root / 'frozen.before.json', {'refs': copied})
        require(common.tree_refs(paths['gocache'], base) == [], 'FRESH_EMPTY_GOCACHE_REQUIRED')
        state['gocache_initial'] = {'path': paths['gocache'], 'files': [], 'shared_cache_copied': False}
        env = common.environment(contract, paths); state['environment_ref'] = base.save_new(root / 'environment.json', env)
        job = load_pinned(contract['owned_job_ref'], 'old21_owned_job')
        allowed = copied + [x['ref'] for x in manifest['items'] if x['kind'] == 'toolchain']
        closures, export_closures, caches = {}, {}, {}
        for phase in plan['phases']:
            state['phase'] = phase['id']; target = phase['target']; kind = phase['kind']
            root_scope.require_phase(phase['id'], request_ref, paths['root'])
            require(validate_resource_binding(root_scope.require_resources(contract_ref, contract['input_manifest_ref']), contract, base) == binding, 'RESOURCE_QUALIFICATION_DRIFT')
            common.assert_pins(original_refs + copied, base); source_membership(contract, objects, base); common.verify_frozen_inventory(paths, copied, base)
            invocation = dict(phase=phase['id'], argv=phase['argv'], cwd=paths['frozen_main'], env=env, timeout_seconds=phase['timeout'], started_at_unix_ns=time.time_ns(), actual_exit=None, observation=None, individual_descendant_exit_codes=None, descendant_evidence='TYPED_JOB_AGGREGATE_IDLE_AND_HANDLES_CLOSED')
            state['calls'].append(invocation)
            invocation['before_ref'] = base.save_new(Path(paths['raw']) / (phase['id'] + '.before.json'), dict(invocation))
            stdout = Path(paths['raw']) / (phase['id'] + '.stdout'); stderr = Path(paths['raw']) / (phase['id'] + '.stderr')
            invocation.update(stdout_path=str(stdout), stderr_path=str(stderr))
            try:
                with stdout.open('xb') as out, stderr.open('xb') as err:
                    observation = job.run_owned(phase['argv'], paths['frozen_main'], env, out, err, phase['timeout'], creation_flags=0x08000000)
                invocation.update(observation=observation, actual_exit=observation.get('actual_exit'))
            except BaseException as exc:
                invocation['launch_exception'] = {'type': type(exc).__name__, 'message': str(exc)}
                raise
            finally:
                invocation['ended_at_unix_ns'] = time.time_ns()
                try:
                    for stream_name, stream in [('stdout', stdout), ('stderr', stderr)]:
                        if stream.is_file(): invocation[stream_name + '_ref'] = base.observed_ref(stream)
                    invocation['result_ref'] = base.save_new(Path(paths['raw']) / (phase['id'] + '.result.json'), dict(invocation))
                except BaseException as receipt_exc:
                    invocation['raw_publication_error'] = {'type': type(receipt_exc).__name__, 'message': str(receipt_exc)}
                    if 'launch_exception' not in invocation: raise
            common.validate_owned(observation, base)
            require(stdout.stat().st_size <= 16 * 1024 * 1024 and stderr.stat().st_size <= 16 * 1024 * 1024, 'GO_OUTPUT_SIZE_CAP')
            raw_guard = guard_module.SourceReadGuard(); guards.append(('raw_' + phase['id'], raw_guard)); raw_guard.acquire([invocation['stdout_ref'], invocation['stderr_ref']])
            raw = raw_guard.get_buffer(str(stdout))
            if kind == 'version':
                require(raw.decode().strip() == 'go version go1.27.1 windows/amd64', 'QUALIFIED_GO_VERSION_MISMATCH')
            elif kind in ('declared', 'export'):
                closure = declared_closure(common.parse_json_stream(raw), allowed, paths, contract, base, common, target, kind == 'export')
                state['target_results'].setdefault(target, {})
                if kind == 'declared':
                    closures[target] = closure; state['target_results'][target]['declared_closure_ref'] = base.save_new(root / (target + '.declared-closure.json'), closure)
                else:
                    require(closure['packages'] == closures[target]['packages'] and closure['input_refs'] == closures[target]['input_refs'], 'DECLARED_EXPORT_CLOSURE_DRIFT')
                    export_closures[target] = closure; target_exports = []
                    for item in closure['exports']: item['ref'] = base.observed_ref(item['path']); target_exports.append(item['ref'])
                    exports_all += target_exports
                    export_guard = guard_module.SourceReadGuard(total_cap=512 * 1024 * 1024); guards.append(('exports_' + target, export_guard)); export_guard.acquire(target_exports)
                    state['target_results'][target]['export_closure_ref'] = base.save_new(root / (target + '.export-closure.json'), closure)
                    caches[target] = common.tree_refs(paths['gocache'], base)
                    state['target_results'][target]['cache_before_build_ref'] = base.save_new(root / (target + '.cache.before-build.json'), {'refs': caches[target]})
            elif kind == 'build':
                require(target in closures and target in export_closures, 'DECLARED_EXPORT_CLOSURE_REQUIRED')
                common.assert_pins(caches[target] + exports_all, base)
                require(Path(paths[target + '_program']).is_file(), 'BUILT_PROGRAM_MISSING')
                program = base.observed_ref(paths[target + '_program']); state['target_results'][target]['program_ref'] = program
                state['target_results'][target]['cache_after_build_ref'] = base.save_new(root / (target + '.cache.after-build.json'), {'refs': common.tree_refs(paths['gocache'], base)})
                state['target_results'][target]['build_work_ref'] = base.save_new(root / (target + '.build-work.json'), {'refs': common.tree_refs(paths['tmp'], base), 'retained': True})
                program_guard = guard_module.SourceReadGuard(); guards.append(('program_' + target, program_guard)); program_guard.acquire([program])
            elif kind == 'inspect':
                verify_binary_metadata(raw, contract, target); state['target_results'][target]['binary_metadata_ref'] = invocation['stdout_ref']
        root_scope.require_phase('complete', request_ref, paths['root'])
        require(validate_resource_binding(root_scope.require_resources(contract_ref, contract['input_manifest_ref']), contract, base) == binding, 'RESOURCE_QUALIFICATION_DRIFT')
        common.assert_pins(original_refs + copied + exports_all, base); common.verify_frozen_inventory(paths, copied, base); source_membership(contract, objects, base)
        validate_blob_bytes(objects, original.get_buffer)
        state['source_after_ref'] = base.save_new(root / 'source.after.json', {'refs': [base.observed_ref(r['path']) for r in original_refs]})
        state['frozen_after_ref'] = base.save_new(root / 'frozen.after.json', {'refs': [base.observed_ref(r['path']) for r in copied]})
        state['status'] = 'BUILT_OLD21_CANDIDATES_PENDING_NONAUTHOR_PROGRAMME_REVIEW'
    except BaseException as exc:
        state['status'] = 'STOPPED_AT_FIRST_FAILURE'
        state['first_failure'] = {'phase': state['phase'], 'type': type(exc).__name__, 'message': str(exc), 'original_ordinal': None, 'Root_assignment_required': True, 'last_child_exit': state['calls'][-1]['actual_exit'] if state['calls'] else None}
    finally:
        state['guard_cleanup'] = {}
        for name, guard in reversed(guards):
            try:
                audit = guard.close(); state['guard_cleanup'][name] = audit
                require(audit.get('verification') == 'PASSED' and audit.get('closed') is True and audit.get('retained_handles_count') == 0 and audit.get('errors') == [], 'SOURCE_GUARD_CLOSE_UNCONFIRMED')
            except BaseException as exc:
                error = {'guard': name, 'type': type(exc).__name__, 'message': str(exc)}
                state.setdefault('cleanup_errors', []).append(error); state['status'] = 'STOPPED_GUARD_CLEANUP_UNCONFIRMED'
                if state['first_failure'] is None: state['first_failure'] = {'phase': 'guard_cleanup', **error, 'original_ordinal': None, 'Root_assignment_required': True, 'last_child_exit': state['calls'][-1]['actual_exit'] if state['calls'] else None}
        state['automatic_retry'] = False; state['partial_output_retained'] = state['root_created']; state['Root_full_outer_hostpair_required'] = True
        state['closed_receipt'] = {'status': 'ROOT_MUST_PERSIST_RETURNED_STATE', 'ref': None}
        if state['root_created']:
            try:
                state['closed_receipt']['status'] = 'PUBLICATION_ATTEMPTED_ROOT_MUST_CONFIRM_REF'
                closed = base.save_new(root / 'build.closed.json', state)
                state['closed_receipt'].update(status='PUBLISHED', ref=closed)
            except BaseException as exc:
                state['closed_receipt'].update(status='FAILED_ROOT_MUST_PERSIST_RETURNED_STATE', error={'type': type(exc).__name__, 'message': str(exc)})
                if state['first_failure'] is None: state['first_failure'] = {'phase': 'close_receipt', 'type': type(exc).__name__, 'message': str(exc), 'original_ordinal': None, 'Root_assignment_required': True, 'last_child_exit': state['calls'][-1]['actual_exit'] if state['calls'] else None}
                state['status'] = 'STOPPED_RECEIPT_PUBLICATION_FAILED'
        if state['status'] == 'BUILT_OLD21_CANDIDATES_PENDING_NONAUTHOR_PROGRAMME_REVIEW':
            state['candidate_for_independent_review'] = {'program_refs': {t: state['target_results'][t]['program_ref'] for t in TARGETS}, 'provenance_ref': state['closed_receipt']['ref'], 'source_commit': COMMIT, 'source_tree': TREE, 'frozen_source_manifest_ref': contract['frozen_source_manifest_ref'], 'qualification_ref': None}
    return state
