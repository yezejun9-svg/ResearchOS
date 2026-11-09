"""Task98: bounded independent AST review; no bridge stage or product entry."""
import ast
import hashlib
import json
import ntpath
import sys
import traceback
import types
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath

Q = Path(__file__).resolve().parent
R = Path('D:/作品集/ResearchOS/research-os')
S = R/'execution/v2.4/receipts/W09/W09-99/w09_formal_root_bridge_source_codex/bridge-20261010-02'
AUTHOR = 'codex:/root/backup_regression_resources'
BACKEND = '/root/backup_regression_resources'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
G = R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
IDENTITY = R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009/w09.public21-source-review-v2.actual-audit.root.json'
TEMP_PARENT = IDENTITY.parent/'physical-C-native-v5-resource-parents.closed.root.json'
EXPECTED = {
    'HDF.json': ('ba17930826a488bbbee9f16ca16371e00de2a1f6e4405b9b18c1aacde6bbe745', 4875),
    'MF.json': ('4a5c1430ce7aeffe58a2d96b4b8790110ee0b324d4bed4f31ce3a103411c43f9', 13031),
    'w09_root_bridge.source.py': ('007dc1ffd8b446cdd164e3f822adf2fb4c41d1c41f18eb568d0d9d18756dfd2d', 40243),
}

def need(ok, code):
    if not ok:
        raise AssertionError(code)

def pin(p):
    p = Path(p)
    raw = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode('utf-8')
    with (Q/name).open('xb') as f:
        f.write(raw)
    return pin(Q/name)

def checked(ref):
    need(type(ref) is dict and set(ref) == {'path', 'sha256', 'bytes'}, 'EXACT_INPUT_REF')
    need(type(ref['sha256']) is str and type(ref['bytes']) is int, 'INPUT_REF_TYPES')
    raw = Path(ref['path']).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == ref['sha256'] and len(raw) == ref['bytes'], 'PIN_CHANGED:'+ref['path'])
    return raw

def const(tree, name):
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return ast.literal_eval(n.value)
    raise AssertionError('ACTUAL_CONSTANT:'+name)

def func(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)

def segment(raw, node):
    return ast.get_source_segment(raw.decode('utf-8'), node)

def calls(node, suffix):
    return [x for x in ast.walk(node) if isinstance(x, ast.Call) and
            ((isinstance(x.func, ast.Attribute) and x.func.attr == suffix) or
             (isinstance(x.func, ast.Name) and x.func.id == suffix))]

def condition(node, label):
    for x in ast.walk(node):
        if isinstance(x, ast.Call) and len(x.args) >= 2 and isinstance(x.args[1], ast.Constant) and x.args[1].value == label:
            return x.args[0]
    raise AssertionError('EXACT_CONDITION:'+label)

def expr(node, values):
    # A single read-only expression from the actual pinned Source, never a Main function/stage.
    return eval(compile(ast.Expression(node), '<pinned-AST-expression>', 'eval'), {'__builtins__': {}}, values)

def main():
    refs = [pin(S/name) for name in EXPECTED]
    for ref in refs:
        need((ref['sha256'], ref['bytes']) == EXPECTED[Path(ref['path']).name], 'ROOT_SUBJECT_PINS')
    hdf = json.loads(checked(refs[0]))
    mf = json.loads(checked(refs[1]))
    need(type(mf.get('members')) is list, 'ACTUAL_MF_SHAPE')
    for ref in mf['members']:
        checked(ref)
    inputs = json.loads(checked(hdf['source_inputs_ref']))
    need(type(inputs.get('references')) is list, 'ACTUAL_SOURCE_INPUTS_SHAPE')
    # Only the source manifest's finite declared public refs; no private-resource traversal.
    input_refs = refs + mf['members'] + inputs['references']
    source_raw = checked(hdf['source_ref'])
    source = ast.parse(source_raw)
    compile(source_raw, hdf['source_ref']['path'], 'exec')
    trusted = const(source, 'TRUSTED')
    main_refs = [dict(path=str(R/k), sha256=v[0], bytes=v[1]) for k,v in trusted.items()]
    for ref in main_refs:
        checked(ref)
    profile_ref = next(ref for ref in main_refs if Path(ref['path']).name == 'formal_profile_w09.py')
    profile_raw = checked(profile_ref)
    profile = ast.parse(profile_raw)
    index_ref = next(ref for ref in main_refs if Path(ref['path']).name == 'formal_case_index.py')
    index_raw = checked(index_ref)
    index = ast.parse(index_raw)
    closure_ref = pin(R/'ops/ci/w09_evidence_closure.py')
    closure_raw = checked(closure_ref)
    closure = ast.parse(closure_raw)
    fixture_ref = hdf['current_Main_fixture_ref']
    checked(fixture_ref)
    identity_ref = pin(IDENTITY)
    need(identity_ref['sha256'] == '775d81746688b95de66cdb101c5caec0d22ebed3bdeffec194afcf31eac782dd' and identity_ref['bytes'] == 1126, 'REAL_PLATFORM_IDENTITY_PIN')
    identity = json.loads(checked(identity_ref))
    identity_raw = checked(identity['original_capture_ref'])
    lines = identity_raw.splitlines(keepends=True)
    need(len(lines) == 3 and all(x.endswith(b'\n') for x in lines), 'REAL_ROOT_IDENTITY_THREE_LINES')
    header, metadata, final = [json.loads(x) for x in lines]
    payload = final['payload']
    need(header['payload']['id'] == ROOT_THREAD and payload['author'] == '/root/attach_restore_independent_review'
         and payload['recipient'] == '/root' and final['metadata']['client_authored'] is False
         and final['ordinal'] == metadata['ordinal']+1 and final['timestamp'] == metadata['timestamp'], 'OBSERVED_ATTACH_BACKEND')
    need(identity['original_line_sha256'] == [hashlib.sha256(x).hexdigest() for x in lines], 'IDENTITY_ORIGINAL_BYTES')
    with Path(identity['source_audit_path']).open('rb') as f:
        for at, line in zip(identity['source_line_offsets'], lines):
            f.seek(at)
            need(f.readline() == line and at+len(line) <= identity['source_prefix_size_observed'], 'REAL_ROOT_SOURCE_RANGE')
    temp_parent_ref = pin(TEMP_PARENT)
    need(temp_parent_ref['sha256'] == 'b85a53b28b489526cf7e7e68acb784ae0661283bea88b5e8c03e152e924ad698' and temp_parent_ref['bytes'] == 2199, 'ACTUAL_C_PARENT_RESOURCE_PIN')
    temp_parent = json.loads(checked(temp_parent_ref))
    need(temp_parent['per_run_scratch_created'] is False and temp_parent['Native_calls'] == 0 and temp_parent['RootScope_issued'] is False
         and temp_parent['resource_scope_only'] is True, 'RESOURCE_PARENT_NOT_NATIVE_AUTHORITY')
    input_refs += main_refs + [closure_ref, fixture_ref, identity_ref, identity['original_capture_ref'],temp_parent_ref]
    unique = {}
    for ref in input_refs:
        key = ntpath.normcase(ntpath.normpath(ref['path'].replace('/', '\\')))
        if key in unique:
            need(unique[key]['sha256'] == ref['sha256'] and unique[key]['bytes'] == ref['bytes'], 'UNIQUE_PIN_STABILITY')
        else:
            unique[key] = ref
    # Never hold the current checkpoint/path_ownership pair or the append-only Root audit.
    forbidden = {ntpath.normcase(str(R/'execution/v2.4'/name)) for name in ('checkpoint.json', 'path_ownership.json')}
    need(not forbidden.intersection(unique), 'NO_LIVE_CP_OW_HANDLES')
    guard_raw = G.read_bytes()
    need(hashlib.sha256(guard_raw).hexdigest() == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and len(guard_raw) == 11404, 'ACTUAL_GUARD_PIN')
    gm = types.ModuleType('task98_readonly_source_guard')
    exec(compile(guard_raw, str(G), 'exec'), gm.__dict__)
    guard = gm.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
    controls = []
    def control(name, passed, fact):
        need(passed, 'REVIEW_CONTROL:'+name)
        controls.append(dict(name=name, observation=bool(passed), fact=fact,
                             synthetic_predicate_only=True, product_execution=False))
    try:
        guard.acquire(list(unique.values()))
        author = const(source, 'AUTHOR')
        control('actual_backend_mapping_not_relabelled', author != payload['author'] and author.removeprefix('codex:') == payload['author'],
                {'canonical_source_author': author, 'actual_peer_backend': payload['author'], 'identity_capture_usage': 'identity only; not Bridge95 approval or a RoleRegistry grant'})
        # The source-author role must use AUTHOR; Main requires the same actor in origin and actual peer author.
        roles_fn = func(source, 'roles')
        roles_condition = condition(roles_fn, 'ACTUAL_VERIFIER_SOURCE_AUTHOR')
        role_values = {'registry': {'roles': {'verifier': const(source, 'VERIFIER'), 'source_authors': [author]}}, 'VERIFIER':const(source, 'VERIFIER'), 'AUTHOR':author}
        control('canonical_author_mandated_by_bridge', expr(roles_condition, role_values), {'line': roles_condition.lineno})
        role_values['registry']['roles']['source_authors'] = [payload['author']]
        control('raw_backend_cannot_satisfy_bridge_author_gate', not expr(roles_condition, role_values), {'line':roles_condition.lineno})
        role_audit = func(profile, '_role_audit')
        author_pred = next(n for n in ast.walk(role_audit) if isinstance(n, ast.Compare) and
                           isinstance(n.left, ast.Call) and isinstance(n.left.func, ast.Attribute) and n.left.func.attr == 'get'
                           and n.left.args and isinstance(n.left.args[0], ast.Constant) and n.left.args[0].value == 'author')
        control('Main_rejects_canonical_actor_for_real_backend', not expr(author_pred, {'payload':payload,'proof':{'actor_id':author}}), {'Main_line':author_pred.lineno})
        control('Main_exact_backend_identity_predicate_allows_observed_actor', expr(author_pred, {'payload':payload,'proof':{'actor_id':payload['author']}}),
                {'Main_line':author_pred.lineno,'this_is_not_full_role_qualification':True})
        control('wrong_peer_remains_rejected', not expr(author_pred, {'payload':payload,'proof':{'actor_id':'/root/other_agent'}}), {'Main_line':author_pred.lineno})
        proposal = func(source, 'propose')
        author_origins = [n for n in ast.walk(proposal) if isinstance(n, ast.Dict) and
                          any(isinstance(k, ast.Constant) and k.value == 'source_actor' for k in n.keys)]
        control('Scope_source_actor_is_same_canonical_AUTHOR', len(author_origins) == 1 and
                any(isinstance(k,ast.Constant) and k.value=='source_actor' and isinstance(v,ast.Name) and v.id=='AUTHOR' for k,v in zip(author_origins[0].keys,author_origins[0].values)), {'line':author_origins[0].lineno})
        physical_pred = condition(func(source, 'physical'), 'REPO_PATH_REQUIRED')
        windows_repo = PureWindowsPath('D:/作品集/ResearchOS/research-os')
        windows_plan = windows_repo.parent/'ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json'
        nf4_parent = PureWindowsPath(temp_parent['exact_parent_paths'][-1])
        paths = {'ROOT':windows_repo, 'PLAN':windows_plan}
        control('repo_temp_allowed_by_existing_path_predicate', expr(physical_pred, dict(paths,result=windows_repo/'.local/bridge-temp')), {'line':physical_pred.lineno})
        control('real_C_resource_parent_rejected_by_existing_path_predicate', not expr(physical_pred, dict(paths,result=nf4_parent)),
                {'line':physical_pred.lineno,'resource_only_root_ref':temp_parent_ref,'per_run_scratch_exists':False,'Native_actual':False})
        control('future_C_child_rejected_by_existing_path_predicate', not expr(physical_pred, dict(paths,result=nf4_parent/'C19-run/temp')), {'line':physical_pred.lineno,'future_fixture_NOT_CREATED_NOT_RUN':True})
        parent_fixture = nf4_parent/'C19-run/temp/fixture'
        control('future_C_fixture_fails_repository_TEMP_containment', not parent_fixture.is_relative_to(windows_repo/'.local/bridge-temp'), {'Main_closure_lines':[605,611],'fixture_NOT_CREATED_NOT_RUN':True})
        control('controlled_common_C_parent_satisfies_pure_containment', parent_fixture.is_relative_to(nf4_parent), {'not_actual_mode_qualification':True,'fixture_NOT_CREATED_NOT_RUN':True})
        consume = func(source, 'consume')
        environment_loop = next(n for n in ast.walk(consume) if isinstance(n, ast.For) and isinstance(n.iter, ast.Tuple)
                                and ast.literal_eval(n.iter)==('TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA'))
        control('TEMP_TMP_both_use_repo_only_physical', bool(calls(environment_loop,'physical')),
                {'line':environment_loop.lineno,'no_fixed_public_C_TEMP_validator_present':True})
        required_stages = ['seed','propose','activate','consume','roles','publish-registration','assemble','capture','check','derive']
        stages_assign = next(n for n in source.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STAGES' for t in n.targets))
        control('all_ten_stage_entries_retained', [ast.literal_eval(k) for k in stages_assign.value.keys] == required_stages, {'entries':required_stages,'executed':[]})
        # No root grant is fabricated: proposals are emitted; Main owns final owner checks and derivation.
        check_fn = func(source,'check')
        derive_fn = func(source,'derive')
        control('owner_precheck_calls_existing_Main_gate', len(calls(check_fn,'verify_owner'))==1 and len(calls(check_fn,'_registered_roots'))==1, {'lines':[x.lineno for x in calls(check_fn,'verify_owner')]})
        derive_call = calls(derive_fn,'derive_formal_cases')[0]
        control('derive_uses_real_SS_not_temporary_path', isinstance(derive_call.args[1],ast.Subscript) and isinstance(derive_call.args[1].value,ast.Name)
                and derive_call.args[1].value.id=='CANON' and isinstance(derive_call.args[1].slice,ast.Constant) and derive_call.args[1].slice.value==2,
                {'line':derive_call.lineno,'existing_Main_source':index_ref})
        routes = const(source,'ROUTES')
        control('six_current_selector_routes_preserved', len(routes)==6 and set(routes)=={('test.retrieval','W09-G01',''),('test.retrieval','W09-G02',''),('test.research.fixture','','C19'),('test.retrieval','','C19'),('test.retrieval','','A06'),('test.security','','A06')}, {'routes':[list(x) for x in routes]})
        proposal_source = segment(source_raw,proposal)
        control('scope_command_keys_and_route_bindings_have_distinct_fields', 'routes=routes, route_bindings=route_bindings' in proposal_source and 'dict.fromkeys(route[0] for route in planned)' in proposal_source,
                {'line':proposal.lineno,'Main_route_membership_requires_command_key_strings':True})
        mode_fn = func(closure,'verify_mode')
        control('current_Main_mode_requires_real_independent_review_and_current_temp', bool(calls(mode_fn,'gettempdir')) and 'INDEPENDENT_NON_AUTHOR' in segment(closure_raw,mode_fn)
                and 'MODE_DECISION_CURRENT_RUN_NOT_CLOSED' in segment(closure_raw,mode_fn), {'line':mode_fn.lineno,'source':closure_ref})
        # Observation is assigned and saved before stdout/stderr hashing can fail.
        observations = [n for n in ast.walk(consume) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.slice,ast.Constant) and t.slice.value=='observation' for t in n.targets)]
        stream_pins = [n for n in ast.walk(consume) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='pin' and n.args and isinstance(n.args[0],ast.Name) and n.args[0].id in {'so','se'}]
        control('OwnedJob_observation_precedes_output_ref_reads', len(observations)==1 and stream_pins and observations[0].lineno < min(n.lineno for n in stream_pins), {'observed_line':observations[0].lineno,'hash_line':min(n.lineno for n in stream_pins)})
        consumer_source = segment(source_raw,consume)
        control('OwnedJob_terminal_cleanup_not_just_exit_zero', all(x in consumer_source for x in ['job_idle_confirmed','active_processes_last_observed','handles_closed','primary_exit_confirmed','assigned_before_resume','FIRST_CHILD_FAILURE_STOP']), {'line':consume.lineno})
        capture_fn = func(source,'capture')
        capture_source = segment(source_raw,capture_fn)
        control('formal_Final_exact_timestamp_and_backend_required', 'meta["timestamp"]==message["timestamp"]' in capture_source and 'payload["author"]==VERIFIER' in capture_source and 'client_authored' in capture_source,
                {'line':capture_fn.lineno,'same_timestamp_not_relaxed':True})
        all_stages_source = {name:segment(source_raw,func(source,fn)) for name,fn in zip(required_stages,['seed','propose','registration','consume','roles','publish_registration','assemble','capture','check','derive'])}
        control('Main_gates_still_required_for_native_and_assemble', '_native' in segment(source_raw,func(source,'native_inputs')) and '_dispatches' in all_stages_source['assemble'] and '_role_registry' in all_stages_source['assemble'], {'no_json_source_only_qualification_shortcut':True})
        control('no_actual_stage_or_Main_entry_called_by_review', True, {'AST_expression_count':8,'Source_runtime_entries_called':0,'Native_Go_SQL_dispatcher_model_TP':0})
    finally:
        closed = guard.close()
        closure_guard_ref = write('source-guard.closed.json',closed)
    need(closed['closed'] is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'], 'SOURCE_GUARD_CLOSED_ZERO')
    control_ref = write('finite-review-controls.json',{'schema':'researchos.w09-bridge-independent-controls.v1','checks':controls,'passed':len(controls),'failed':0,'old_author_18_delta_or_26_guard_controls_rerun':False,'runtime_stages_called':[],'Root_issuance':False,'execution_grant':False})
    source_pin_ref = write('input-source-pins.json',{'schema':'researchos.w09-bridge-review-input-pins.v1','subject_hdf_ref':refs[0],'subject_mf_ref':refs[1],'subject_members':len(mf['members']),'references':list(unique.values()),'Root_actual_identity_ref':identity_ref,'actual_identity_usage':'Only existing Attach backend identity; not Bridge95 source-review, not runtime qualification, not new scope authority.','Root_C_parent_resource_ref':temp_parent_ref,'C_resource_status':'Only existing physical parents; per-run scratch/fixture NOT_CREATED/NOT_RUN, no Native grant or qualification. AppData NF4 candidate was superseded after alias observation original1142.','Root_audit_source_ranges':{'path':identity['source_audit_path'],'offsets':identity['source_line_offsets'],'sha256':identity['original_line_sha256'],'full_live_log_handle_held':False},'live_CP_OW_read_or_guarded':False})
    findings = [
        {'id':'BRIDGE-ROLE-001','severity':'P1','status':'CHANGES_REQUIRED','title':'Canonical Source author cannot satisfy actual Main peer audit',
         'source_ref':hdf['source_ref'],'source_lines':[19,author_origins[0].lineno,roles_condition.lineno], 'Main_ref':profile_ref,'Main_lines':[author_pred.lineno,309,333,366],
         'observed_identity_ref':identity_ref,
         'cause':'Bridge requires canonical AUTHOR in roles.source_authors and pins source_actor=AUTHOR. Main requires origin.source_actor == proof.actor_id, then exact actual backend payload.author == proof.actor_id. Observed genuine backend author is /root/attach_restore_independent_review, not codex:/root/attach_restore_independent_review. A Root capture cannot be relabeled as this author.',
         'minimum_revision':'Keep truthful canonical Source author metadata. Give Source-author RoleRegistry/Scope provenance the exact actual backend actor, validate its fixed canonical-to-backend mapping and genuine Root-thread Final. Do not change Main, pretend Root authored this Source, or relabel old captures.'},
        {'id':'BRIDGE-TEMP-002','severity':'P1','status':'CHANGES_REQUIRED','title':'Repo-only environment paths exclude genuinely physical C resource parent for future Native fixtures',
         'source_ref':hdf['source_ref'],'source_lines':[76,82,416,417,650,663], 'Main_ref':closure_ref,'Main_lines':[565,605,609,611],
         'Root_resource_ref':temp_parent_ref,'Native_fixture_actual':False,
         'cause':'consume passes TEMP/TMP to physical(), which only permits repo or PLAN. Root resource-only receipt confirms genuinely physical C:/Users/yqyyds/.researchos/w09-native-v5 parents, not a run or fixture. NF4 AppData choice was rejected as an alias (original1142) and is not an accepted Native root. Main verify_mode requires actual fixture state roots below current tempfile.gettempdir(). Pure Windows path predicates prove future fixtures at the intended C parent would fail repository TEMP containment, while Bridge also rejects that legitimate C parent before dispatch. Propose/assemble Main-native prechecks plus later check/derive need the same process TEMP context.',
         'minimum_revision':'Add an explicit narrow public environment contract for the genuinely physical C resource parent; validate same canonical TEMP/TMP, nonalias safe parent and subsequently mode-bound real owned roots. Permit this directory only for environment metadata, never general checked/ref paths. Require the bridge Python process (including prechecks/check/derive) and consumer OwnedJob to use the same controlled parent before tempfile caching or verification. Preserve source/data/credential path gates and all actual mode checks. Native fixtures and independent qualifications remain NOT_RUN.'},
    ]
    stage_review = [
        {'stage':'seed','conclusion':'Keeps genuine current Main vector and literal producer Source21; no native startup or artificial acceptance.'},
        {'stage':'propose','conclusion':'Six selector routes and command-key strings are retained; current source gate blocks old Source21 reuse. Role source_actor and in-process TEMP blockers remain.'},
        {'stage':'activate','conclusion':'Uses existing TP pair update with snapshots; SourceGuard intentionally excludes CP/OW. Requires actual Root scope/owner publication; no Scope issued by reviewer.'},
        {'stage':'consume','conclusion':'Locked Python/dispatcher + finite leased routes + CAS and real OwnedJob closure. Known returned observation survives output-ref failure. Current C TEMP is rejected.'},
        {'stage':'roles','conclusion':'Requires real Main role audit, but mandatory canonical Source author contradicts exact backend identity.'},
        {'stage':'publish-registration','conclusion':'Proposal bytes must already be genuinely Root-published at fixed role/index path; registered CP slot has previous-value CAS.'},
        {'stage':'assemble','conclusion':'Main role/native/dispatch/global gates remain, six route consumer outputs required; currentTEMP and source-author blockers prevent closed context.'},
        {'stage':'capture','conclusion':'Only existing real nonauthor Final with Root thread, adjacent metadata, exact timestamp, content hashes and causal times; emits proposals, never future/forged Final.'},
        {'stage':'check','conclusion':'Calls actual Main _registered_roots and verify_owner; dependencies read actual SS; no substitute owner acceptance. Needs controlled currentTEMP.'},
        {'stage':'derive','conclusion':'Calls actual live Main derive_formal_cases on SS and rechecks dependency snapshot; no temporary SS accepted as canonical. Needs controlled currentTEMP.'},
    ]
    decision = {'schema':'researchos.w09-formal-root-bridge-independent-source-review.v1','decision':'CHANGES_REQUIRED',
                'reviewer_id':BACKEND,'reviewer_actor':AUTHOR,'source_author':const(source,'AUTHOR'),'Root_thread_id':ROOT_THREAD,
                'source_ref':hdf['source_ref'],'source_hdf_ref':refs[0],'source_mf_ref':refs[1],
                'findings':findings,'stages':stage_review,'finite_controls_ref':control_ref,'source_guard_ref':closure_guard_ref,
                'input_pins_ref':source_pin_ref,'formal_acceptance':False,'execution_grant':False,'actual_runtime_authority':None,
                'Root_next_step':'No bridge02 activation/consume/formal stage approved. New minimal Source revision for both P1s; nonauthor Source review and then genuine Root scope/runtime resource binding before any actual stage.',
                'prior_failure_counters_reset':False,'Main_Canon_old_Source_writes':0,'RootScope_qualification_created':False,
                'created_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'STOP_after_seal':True}
    decision_ref = write('decision.json',decision)
    print(json.dumps({'decision_ref':decision_ref,'controls_ref':control_ref,'controls':len(controls),'guard_ref':closure_guard_ref,'pins_ref':source_pin_ref,'subject_mf_members':len(mf['members']),'future_execution_authority':False},ensure_ascii=False))
    return 0

if __name__ == '__main__':
    code = 1
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code))
    sys.exit(code)
