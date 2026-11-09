"""Read-only diagnosis of the already failed BR7 activation; no replay."""
import ast
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
RUN = ROOT / 'execution/v2.4/receipts/W09/W09-99/w09_br7_actual_root/actual-20261010-01'
SOURCE = ROOT / 'execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-07/w09_root_bridge.source.py'
RESOURCE = ROOT / 'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/physical-C-native-v5-resource-parents.closed.root.json'
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable diagnosis member already exists: ' + name)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8')
    path.write_bytes(raw)
    return ref(path)

def reference_walk(value, pointer=''):
    if type(value) is dict:
        if {'path', 'sha256'} <= set(value):
            yield pointer, {key: value[key] for key in ['path', 'sha256', 'bytes'] if key in value}
        else:
            for key, item in value.items():
                escaped = key.replace('~', '~0').replace('/', '~1')
                yield from reference_walk(item, pointer + '/' + escaped)
    elif type(value) is list:
        for index, item in enumerate(value):
            yield from reference_walk(item, pointer + '/' + str(index))

def main():
    proposal_ref = ref(RUN / 'propose-1bc4180305d244f39897ef1220628d70/result.json')
    failure_ref = ref(RUN / 'activate-1d84acd485ae49938818f41964d60779/failure.json')
    root_guard_ref = ref(RUN / 'activate-1d84acd485ae49938818f41964d60779/source-guard.closed.json')
    source_ref = ref(SOURCE)
    resource_ref = ref(RESOURCE)
    guard_ref = ref(GUARD)
    if not proposal_ref['sha256'].startswith('e740') or proposal_ref['bytes'] != 2047990:
        raise ValueError('actual proposal differs from Root supplied observation')
    if source_ref['sha256'] != '16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668' or source_ref['bytes'] != 54832:
        raise ValueError('actual BR7 Source pin differs')
    if resource_ref['sha256'] != 'b85a53b28b489526cf7e7e68acb784ae0661283bea88b5e8c03e152e924ad698' or resource_ref['bytes'] != 2199:
        raise ValueError('fixed Root resource receipt differs')
    if guard_ref['sha256'] != 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' or guard_ref['bytes'] != 11404:
        raise ValueError('fixed guard pin differs')
    spec = importlib.util.spec_from_file_location('br7_readonly_activation_diagnosis_guard', GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    guard = module.SourceReadGuard(per_file_cap=128*1024*1024, total_cap=512*1024*1024)
    refs = [proposal_ref, failure_ref, root_guard_ref, source_ref, resource_ref, guard_ref]
    facts = None
    closure = None
    try:
        guard.acquire(refs)
        get = lambda r: guard.get_buffer(r['path'])
        proposal = json.loads(get(proposal_ref))
        failure = json.loads(get(failure_ref))
        root_guard = json.loads(get(root_guard_ref))
        resource = json.loads(get(resource_ref))
        source_text = get(source_ref).decode('utf-8')
        tree = ast.parse(source_text)
        owner_assign = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'RESOURCE_OWNER_REF' for t in n.targets))
        owner_ref = ast.literal_eval(owner_assign.value)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        cleaned = copy.deepcopy(proposal)
        del cleaned['current4']
        del cleaned['historical_current4']
        ordered_refs = list(reference_walk(cleaned))
        root = PureWindowsPath(str(ROOT))
        plan = PureWindowsPath(str(ROOT.parent / 'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'))
        outside = []
        for index, (pointer, item) in enumerate(ordered_refs):
            path = PureWindowsPath(item['path'])
            if not path.is_absolute():
                path = root / path
            if not path.is_relative_to(root) and path != plan:
                outside.append({'ordered_reference_index': index, 'json_pointer': pointer, 'ref': item, 'lexical_absolute_identity': str(path)})
        if not outside:
            raise ValueError('no actual outside-repository dependency was found')
        if failure['stage'] != 'activate' or failure['error'] != "ValueError('REPO_PATH_REQUIRED')" or failure['formal_acceptance'] is not False:
            raise ValueError('actual Root failure does not match scoped diagnosis')
        if root_guard['attempted'] is not False or root_guard['verification'] != 'NOT_RUN' or root_guard['closed'] is not True or root_guard['retained_handles_count'] != 0 or root_guard['errors']:
            raise ValueError('actual failed activation guard state differs')
        if resource['resource_owner_marker_ref'] != owner_ref or resource['resource_scope_only'] is not True or resource['execution_grant'] is not False:
            raise ValueError('fixed resource-only owner marker binding differs')
        first = outside[0]
        excerpts = {}
        source_lines = source_text.splitlines()
        for name in ['physical', 'resource_environment', 'historical_dependency_refs']:
            node = functions[name]
            excerpts[name] = {'source_ref': source_ref, 'start_line': node.lineno, 'end_line': node.end_lineno, 'text': '\n'.join(source_lines[node.lineno-1:node.end_lineno])}
        excerpts['main_historical_dependency_loop'] = {'source_ref': source_ref, 'start_line': 870, 'end_line': 892, 'text': '\n'.join(source_lines[869:892])}
        facts = {
            'schema': 'researchos.w09-br7-activation-resource-readonly-diagnosis.v1',
            'reviewer_id': '/root/backup_regression_resources',
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'original_ordinal': 1224,
            'failure_ref': failure_ref, 'Root_failure': failure,
            'proposal_ref': proposal_ref, 'Root_guard_ref': root_guard_ref,
            'Root_guard_attempted': False, 'Root_guard_closed': True,
            'source_ref': source_ref, 'fixed_resource_receipt_ref': resource_ref,
            'fixed_resource_owner_ref': owner_ref,
            'first_outside_dependency': first,
            'first_is_exact_fixed_resource_owner_ref': first['ref'] == owner_ref,
            'all_outside_dependencies': outside,
            'ordered_reference_count': len(ordered_refs),
            'method': 'Exact Source references traversal and proposal field removal order; PureWindowsPath lexical containment only. No physical()/stage failure replay and no C marker content was opened.',
            'source_excerpt_refs': excerpts,
            'minimum_revision': {
                'location': 'main() historical dependency loop immediately before physical(ref["path"]) at Source line885',
                'fixed_owner_handling': 'For only exact RESOURCE_OWNER_REF path, require the complete path/sha256/bytes ref equality and the same already resource_environment-validated entry in refs, then reuse that existing held-resource registration instead of passing this C marker through general repository physical()/checked().',
                'no_general_C_exception': True,
                'unrelated_C_refs': 'Remain refused or explicitly diagnosed as separate blockers; never grant generic C parents/children/audit ranges through this marker exception.',
                'resource_environment': 'All existing physical C parent/noalias/reparse/project-owner/SHA/Root resource-only receipt/actual Root provenance gates remain unchanged and execute before historical dependencies.',
                'gates_unchanged': 'Current4 historical archives, Canon conflict checks, Source/peer/Root lease/CAS, roles, OwnedJob, six current CM40 routes and Native Mode pins remain strict.',
            },
            'necessary_delta_controls': [
                'Exact fixed marker from valid historical proposal reuses already validated resource entry.',
                'Same marker path with changed SHA or bytes or unexpected fields is rejected.',
                'Missing prevalidated fixed marker entry is rejected.',
                'Other C file, marker sibling/descendant, alternate resource generation or alias path remains outside the general repository gate.',
                'General repository dependencies and undeclared historical Canon rejection remain unchanged.',
                'Full byte inverse excludes only this fixed-ref handling and new generation/self refs; old controls/Native/Mode evidence is reused without replay.',
            ],
            'all_original_failures_preserved': True,
            'physical_failure_replayed': False,
            'Root_stages_Native_Go_SQL_model_TP_calls': 0,
            'Main_Canon_Scope_Registry_writes': 0,
            'source_candidate_created': False,
            'formal_acceptance': False, 'execution_grant': False,
            'held_input_refs': refs,
        }
    finally:
        closure = guard.close()
        publish('SourceGuard.closed.json', closure)
    if closure['closed'] is not True or closure['retained_handles_count'] != 0 or closure['errors']:
        raise ValueError('readonly diagnosis guard did not fully close')
    facts['Source_guard_ref'] = ref(HERE / 'SourceGuard.closed.json')
    facts['Source_guard_closed'] = True
    facts_ref = publish('diagnosis-facts.json', facts)
    print(json.dumps({'status': 'READONLY_ACTIVATION_BOUNDARY_DIAGNOSED_PENDING_SEAL', 'facts_ref': facts_ref, 'first_outside_dependency': facts['first_outside_dependency'], 'first_is_exact_fixed_marker': facts['first_is_exact_fixed_resource_owner_ref'], 'outside_ref_count': len(facts['all_outside_dependencies']), 'guard_closed': True}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
