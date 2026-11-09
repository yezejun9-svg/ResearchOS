"""Finish only the unsealed report tail; reuse both actual closed guards."""
import ast
import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath

HERE = Path(__file__).resolve().parent
API = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/formal_case_index.py')

def ref(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def checked(reference):
    raw = Path(reference['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['sha256'] or len(raw) != reference['bytes']:
        raise ValueError('immutable report-tail pin differs')
    return raw

def publish(name, value):
    path = HERE / name
    if path.exists():
        raise FileExistsError('immutable report-tail member exists: ' + name)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').replace('\n', '\r\n').encode('utf-8'))
    return ref(path)

try:
    facts = json.loads((HERE / 'diagnosis-facts.json').read_text(encoding='utf-8'))
    observed = json.loads(checked({'path': str(HERE / 'actual-range-shape.observation.json'), 'sha256': 'a5606813279f9cae2b0239b534201822d5081394cee6a08ee815366a2b328c2a', 'bytes': 2066}))
    proposal = json.loads(checked(facts['proposal_ref']))
    ranges = proposal['dependency_snapshot']['audit_ranges']
    identity = PureWindowsPath(facts['first_outside_dependency']['ref']['path'])
    if len(ranges) != observed['actual_total_audit_ranges'] or any(set(item) != {'path', 'offset', 'bytes', 'sha256'} or PureWindowsPath(item['path']) != identity for item in ranges):
        raise ValueError('typed range tail differs from actual observation')
    api_ref = {'path': str(API), 'sha256': 'e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b', 'bytes': 71844}
    api_text = checked(api_ref).decode('utf-8')
    tree = ast.parse(api_text)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    lines = api_text.splitlines()
    excerpts = {}
    for name in ['_audit_range', 'recheck_inputs']:
        node = functions[name]
        excerpts[name] = {'source_ref': api_ref, 'start_line': node.lineno, 'end_line': node.end_lineno, 'text': '\n'.join(lines[node.lineno-1:node.end_lineno])}
    guards = [facts['Source_guard_ref'], ref(HERE / 'completion-SourceGuard.closed.json')]
    for guard_ref in guards:
        guard = json.loads(checked(guard_ref))
        if guard['closed'] is not True or guard['retained_handles_count'] != 0 or guard['errors']:
            raise ValueError('previous actual diagnosis Guard is not closed')
    result = copy.deepcopy(facts)
    result['decision'] = 'SOURCE_REVISION_REQUIRED_TYPED_AUDIT_RANGES_PROMOTED_TO_WHOLE_FILE_REFS'
    result['exploratory_facts_ref'] = ref(HERE / 'diagnosis-facts.json')
    result['exploratory_owner_marker_minimum_revision_superseded'] = True
    result['first_rejected_reference'] = dict(facts['first_outside_dependency'], original_typed_range=ranges[0])
    result['actual_total_audit_ranges'] = len(ranges)
    result['actual_outside_generic_ref_count'] = len(facts['all_outside_dependencies'])
    result['actual_typed_ranges'] = ranges
    result['actual_range_path_spellings'] = observed['path_counts']
    result['all12_outside_refs_same_fixed_Root_audit_physical_identity'] = True
    result['marker_is_not_the_first_or_any_current_outside_ref'] = True
    result['Main_api_ref'] = api_ref
    result['Main_api_excerpt_refs'] = excerpts
    result['actual_call_chain'] = [
        {'source_line': 881, 'action': 'main reads immutable proposal_ref'},
        {'source_line': 381, 'action': 'historical_dependency_refs clones proposal and removes archive-covered current4'},
        {'source_line': 391, 'action': 'references(cleaned) drops audit_ranges offset and emits each range as whole-file ref'},
        {'source_line': 885, 'action': 'main passes first projected C Root-audit range to repository-only physical()'},
        {'source_line': 90, 'action': 'REPO_PATH_REQUIRED before Guard.acquire909 and before registration912'},
    ]
    result['minimum_revision'] = {
        'location': 'historical_dependency_refs381..394, only cloned dependency_snapshot used for generic reference scanning',
        'typed_branch': 'Validate declared audit_ranges list and exact path/offset/bytes/sha256 schema; omit only this typed branch from cloned whole-file enumeration. Preserve original snapshot and range objects completely.',
        'retained_hash_checks': 'Existing api._audit_range1047..1065 and recheck_inputs1068..1087 stay unchanged; original proposal is rechecked by registration539 before TP, publication snapshot715 before TP, and snapshot314 before publication.',
        'Canon_defense': 'Before omitting the typed branch, keep original canonical_identity range.path not in CANON refusal, including aliases/traversal identity. No new omission of historical Canon dependency.',
        'path_spelling': 'Support the same regular physical C Root audit identity expressed with C:\\ or C:/; retain each original string/object and exact offset/bytes/SHA. Do not rewrite historical refs.',
        'no_generic_C_exception': 'physical()/checked()/general references() remain unchanged. Unrelated C whole-file refs under other branches remain refused.',
        'resource_owner': 'Existing main872..879 already registers only fixed resource_environment-validated marker; no marker-specific change is required by this failure.',
        'all_existing_authority_gates': 'Keep current4 archives/SS/CM, nonauthor Source proof, Root owner/lease/CAS, finite Scope, roles, six routes, OwnedJobs and Native Mode refs unchanged.',
    }
    result['necessary_delta_controls'] = [
        'Exact typed Root ranges remain in original snapshot; clone whole-file refs omit only audit_ranges.',
        'Both actual C:\\ and C:/ spellings resolve to same allowed identity while original objects stay unchanged.',
        'Wrong keys, bool/negative offset, bool/nonpositive bytes and malformed SHA fail strict range shape.',
        'Range path resolving to Canon, including alias/traversal, still fails UNDECLARED_HISTORICAL_CANONICAL_REFERENCE.',
        'Actual range byte/hash mutation still fails existing _audit_range/recheck_inputs; preserve calls before TP.',
        'Other C ordinary refs and marker siblings/children remain rejected by unchanged repository gate.',
        'Full inverse limits delta to cloned typed-branch enumeration plus generation/self refs; no old controls/Native/Mode replay.',
    ]
    result['original1225_origin_ref'] = ref(HERE / 'original1225.origin.json')
    result['original1225_cause_correction'] = 'Actual total is12; failure was raw-string path equality, because6 range paths use backslashes and6 use forward slashes for the same physical Root audit file. Initial quantity explanation is superseded; original IO/script remains unchanged.'
    result['guard_refs'] = guards
    result['all_diagnostic_guards_closed'] = True
    result['old_six_and_five_input_guards_replayed'] = False
    result['report_tail_reads'] = 'Exact immutable proposal and pinned API Source text only; no new Guard.acquire or Rootaudit handle.'
    result['Root_original1224_unchanged'] = True
    result['new_original_failures'] = [1225]
    result['future_Source_candidate_ref'] = None
    result['future_Source_independent_review_ref'] = None
    result['Root_stages_Native_Go_SQL_model_TP_calls'] = 0
    result['physical_failure_replayed'] = False
    result['Main_Canon_Scope_Registry_writes'] = 0
    result['formal_acceptance'] = False
    result['execution_grant'] = False
    report_ref = publish('diagnosis-facts.v2.json', result)
    print(json.dumps({'decision': result['decision'], 'report_ref': report_ref, 'actual_total_audit_ranges': len(ranges), 'actual_outside_ref_count': len(facts['all_outside_dependencies']), 'original1225_ref': result['original1225_origin_ref'], 'all_previous_guards_closed': True, 'failure_replayed': False}, ensure_ascii=False))
except BaseException:
    print('ROOT_PYTHON_EXIT=1', flush=True)
    raise
else:
    print('ROOT_PYTHON_EXIT=0', flush=True)
