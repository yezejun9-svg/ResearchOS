"""Complete the read-only diagnosis with the actual typed audit-range cause."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
API = ROOT / 'execution/v2.4/formal_case_index.py'
GUARD = ROOT / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable diagnosis member exists: ' + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8'))
    return ref(path)

def main():
    facts_ref = ref(HERE / 'diagnosis-facts.json')
    facts = json.loads((HERE / 'diagnosis-facts.json').read_text(encoding='utf-8'))
    api_ref = {'path': str(API), 'sha256': 'e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b', 'bytes': 71844}
    guard_ref = ref(GUARD)
    if guard_ref['sha256'] != 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85':
        raise ValueError('fixed guard differs')
    spec = importlib.util.spec_from_file_location('typed_range_readonly_completion_guard', GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    guard = module.SourceReadGuard(per_file_cap=128*1024*1024, total_cap=512*1024*1024)
    refs = [facts_ref, facts['proposal_ref'], api_ref, facts['source_ref'], guard_ref]
    closed = None
    result = None
    try:
        guard.acquire(refs)
        proposal = json.loads(guard.get_buffer(facts['proposal_ref']['path']))
        ranges = proposal['dependency_snapshot']['audit_ranges']
        root_audit = facts['first_outside_dependency']['ref']['path']
        if len(ranges) != 12 or any(set(item) != {'path', 'offset', 'bytes', 'sha256'} or item['path'] != root_audit or type(item['offset']) is not int or item['offset'] < 0 or type(item['bytes']) is not int or item['bytes'] <= 0 for item in ranges):
            raise ValueError('actual typed Root range list differs from observed first cause')
        first = ranges[0]
        if {k: first[k] for k in ['path', 'sha256', 'bytes']} != facts['first_outside_dependency']['ref']:
            raise ValueError('actual first range does not match ordered scan')
        api_text = guard.get_buffer(api_ref['path']).decode('utf-8')
        api_tree = ast.parse(api_text)
        api_functions = {n.name: n for n in api_tree.body if isinstance(n, ast.FunctionDef)}
        api_lines = api_text.splitlines()
        excerpt = {}
        for name in ['_audit_range', 'recheck_inputs']:
            node = api_functions[name]
            excerpt[name] = {'source_ref': api_ref, 'start_line': node.lineno, 'end_line': node.end_lineno, 'text': '\n'.join(api_lines[node.lineno-1:node.end_lineno])}
        result = copy.deepcopy(facts)
        result['decision'] = 'SOURCE_REVISION_REQUIRED_TYPED_AUDIT_RANGES_PROMOTED_TO_WHOLE_FILE_REFS'
        result['exploratory_facts_ref'] = facts_ref
        result['exploratory_minimum_revision_superseded'] = True
        result['first_rejected_reference'] = dict(facts['first_outside_dependency'], original_typed_range=first)
        result['actual_typed_ranges'] = ranges
        result['all12_outside_refs_are_fixed_Root_audit_ranges'] = True
        result['marker_is_not_the_first_or_any_current_outside_ref'] = True
        result['Main_api_ref'] = api_ref
        result['Main_api_excerpt_refs'] = excerpt
        result['actual_call_chain'] = [
            {'source_line': 881, 'action': 'main reads exact immutable proposal_ref'},
            {'source_line': 381, 'action': 'historical_dependency_refs clones proposal and removes archive-covered current4 fields'},
            {'source_line': 391, 'action': 'references(cleaned) scans dependency_snapshot.audit_ranges and drops each offset'},
            {'source_line': 885, 'action': 'main passes first projected C Root-audit range to general repository-only physical()'},
            {'source_line': 90, 'action': 'REPO_PATH_REQUIRED rejects C audit file before Guard.acquire at909 and before registration at912'},
        ]
        result['minimum_revision'] = {
            'location': 'historical_dependency_refs at381..394, only the deep-copied dependency_snapshot used for generic references scanning',
            'typed_range_handling': 'Preserve original snapshot and its audit_ranges exactly. Validate the declared list and exact path/offset/bytes/sha256 item schema, then omit only that typed audit_ranges branch from generic whole-file ref enumeration in the clone.',
            'retained_validation': 'Original snapshot must still pass existing api.recheck_inputs(snapshot)/_audit_range; registration539 and publication715 must retain actual range hashing before TP, and proposal snapshot314 remains strict.',
            'range_is_not_file_ref': '22732 is the header range length, with offset0, and sha85ee... is that range digest. They are not the size/hash of the growing whole audit file.',
            'Root_audit_boundary': 'Use the existing exact Root audit path and nonnegative integer offset/positive integer bytes/full SHA/provenance gates; no alias/other audit/source/private/project path exception.',
            'physical_checked_unchanged': True,
            'general_references_unchanged': True,
            'fixed_RESOURCE_OWNER_boundary_unchanged': 'Current main872..879 already registers this one fully validated fixed marker separately; no marker-specific change is needed for this actual first failure.',
            'Canon_and_authority_unchanged': 'Archive coverage and undeclared Canon conflict rejection remain strict; preserve current4/SS/CM/Root owner/lease/role/Source proof/OwnedJob/finite Scope gates.',
        }
        result['necessary_delta_controls'] = [
            'Valid exact typed Root audit range remains in original snapshot and is not returned as a whole-file dependency.',
            'Ordinary repository ref and undeclared historical Canon checks retain their existing behavior.',
            'Malformed range keys, bool/negative offset, bool/nonpositive bytes, invalid SHA, wrong Root audit path or alias are rejected.',
            'Actual changed bytes in a declared range are still refused by existing api.recheck_inputs/_audit_range; do not remove or replace the dedicated range check.',
            'Unrelated C ref under another branch, marker sibling and arbitrary parent/descendant remain subject to repository physical() refusal.',
            'Complete inverse confines changes to this typed-branch enumeration plus new generation/self refs, preserving prior controls and Native/Mode artifacts without replay.',
        ]
        result['Root_original1224_unchanged'] = True
        result['new_original_failures'] = []
        result['future_Source_candidate_ref'] = None
        result['future_Source_independent_review_ref'] = None
        result['diagnostic_entry_executions'] = 0
        result['source_files_written'] = 0
        result['Main_Canon_Scope_Registry_writes'] = 0
        result['Root_stages_Native_Go_SQL_model_TP_calls'] = 0
        result['formal_acceptance'] = False
        result['execution_grant'] = False
    finally:
        closed = guard.close()
        publish('completion-SourceGuard.closed.json', closed)
    if closed['closed'] is not True or closed['retained_handles_count'] != 0 or closed['errors']:
        raise ValueError('readonly completion guard did not fully close')
    result['completion_Source_guard_ref'] = ref(HERE / 'completion-SourceGuard.closed.json')
    result['all_diagnostic_guards_closed'] = True
    report_ref = publish('diagnosis-facts.v2.json', result)
    print(json.dumps({'decision': result['decision'], 'report_ref': report_ref, 'first_rejected_reference': result['first_rejected_reference'], 'all_guards_closed': True, 'no_original1224_replay': True}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        print('ROOT_PYTHON_EXIT=1', flush=True)
        raise
    else:
        print('ROOT_PYTHON_EXIT=0', flush=True)
