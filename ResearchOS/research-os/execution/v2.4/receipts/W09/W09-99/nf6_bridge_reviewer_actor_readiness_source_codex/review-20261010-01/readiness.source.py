"""Finite, guarded, read-only actor compatibility review; never invoke Main stages."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, traceback, types

R = Path(r'D:\作品集\ResearchOS\research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
D = Path(__file__).resolve().parent
BR = W / 'w09_formal_root_bridge_source_codex/bridge-20261010-03'
NF = W / 'full_w09_main_native_producer_source_codex/fullw09-20261010-06'
RG = W / 'w09_nf6_root_registration_source_codex/register-20261010-01'
sp = W / 'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s = types.ModuleType('review_support'); s.__file__ = str(sp)
exec(compile(sp.read_bytes(), str(sp), 'exec'), s.__dict__); s.D = D
AUTHOR = 'codex:/root/full_w09_source_review'
FULL = '/root/full_w09_source_review'
BACKUP = '/root/backup_regression_resources'
ATTACH = '/root/attach_restore_independent_review'

def exact(path, sha, size):
    return {'path': str(path), 'sha256': sha, 'bytes': size}

refs = {
 'BR3_hdf': exact(BR/'HDF.json', '1f85ead2fffdd5400270c3d0f1078bb661df91fbd8ff94bfd1dd05992e45aa0f', 7862),
 'BR3_mf': exact(BR/'MF.json', '225bb69692fde3fb0d54afa017a93248db968ef9e0a24cdd2c9a81b3ad0119d1', 6046),
 'BR3_source': exact(BR/'w09_root_bridge.source.py', '327b0e886b58008ad33dcbcfaaaa2c44bc10d4076d3d3c717b2ce6e96914cbfb', 49240),
 'BR3_launcher': exact(BR/'consumer_launch.source.py', 'c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011', 1493),
 'BR3_contract': exact(BR/'ROOT_CALL_CONTRACT.md', '756b10ab0a4e7f798d9e4a0f7c994e23dc9e50fddddbaa560a8dcae9c0c21ea6', 4147),
 'Main_profile': exact(R/'execution/v2.4/formal_profile_w09.py', 'd44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f', 71397),
 'Main_index': exact(R/'execution/v2.4/formal_case_index.py', 'e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b', 71844),
 'Main_closure': s.pin(R/'ops/ci/w09_evidence_closure.py'),
 'Main_router': s.pin(R/'ops/ci/w09_formal_router.py'),
 'Main_retrieval': exact(R/'ops/ci/retrieval.py', 'b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11', 14545),
 'NF6_hdf': exact(NF/'HDF.json', '8d5109e4105567c2d6a3aa1d300c81b5d9d6ee88dd392834c8c2985f225c2af6', 23159),
 'NF6_mf': exact(NF/'MF.json', '902ff6b68a318d45333e4fe6abb3d050d3fe9f0d46f2e6a0dbc77be7c70854d2', 4758),
 'NF6_contract': exact(NF/'root-calling-contract.json', 'd5ab18c0e8eac613819221708815ed5d7079944c54ea53f529dc8e5a3b44ebb3', 9701),
 'REG6_hdf': exact(RG/'HDF.json', 'a1b50d275b748e4c9be4dab7c8f330fa1265ba10502cb42111570e77c76f7db7', 13078),
 'REG6_mf': exact(RG/'MF.json', '2b966f7b983245e0289d5d4a84630a007c2ba25f2f69aabbc1d5a1bf6d791eb9', 4418),
 'REG6_contract': exact(RG/'root-calling-contract.source.json', '5e67a4491ac8a4602fca85be83e3ab68862a3ace794b2025a3cc8ec902384c8d', 10835),
}
g = s.guard(); checks = []; failure = None; result = None
def check(name, ok, detail=None):
    checks.append({'name': name, 'passed': bool(ok), 'detail': detail})
    if not ok: raise ValueError(name)

def function_nodes(raw):
    return {n.name:n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

def references(node, name):
    return [n.lineno for n in ast.walk(node) if isinstance(n,ast.Name) and n.id == name]

def string_keys(node, base):
    keys = set()
    for n in ast.walk(node):
        if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id == base and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str):
            keys.add(n.slice.value)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id==base and n.func.attr=='get' and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str):
            keys.add(n.args[0].value)
    return sorted(keys)

try:
    g.acquire(list(refs.values()))
    raw = {k:g.get_buffer(ref['path']) for k,ref in refs.items()}
    bridge_tree = ast.parse(raw['BR3_source']); bnodes = function_nodes(raw['BR3_source'])
    pnodes = function_nodes(raw['Main_profile']); cnodes = function_nodes(raw['Main_closure'])
    constants = {}
    for node in bridge_tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try: constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError): pass
    old_hdf = json.loads(raw['BR3_hdf']); nf_hdf = json.loads(raw['NF6_hdf'])
    nf_contract = json.loads(raw['NF6_contract']); reg_contract = json.loads(raw['REG6_contract'])
    check('BR3_current_VERIFIER_is_Full_and_Backup_is_rejected_by_literal', constants['VERIFIER']==FULL and constants['VERIFIER']!=BACKUP)
    uses = {name:references(node,'VERIFIER') for name,node in bnodes.items() if references(node,'VERIFIER')}
    check('BR3_literal_reaches_roles_assemble_capture_issuance', {'roles','assemble','capture'}<=set(uses), uses)
    check('BR3_Attach_AUTHOR_is_true_bridge_identity_not_NF6_author', constants['AUTHOR']=='codex:'+ATTACH and constants['AUTHOR_BACKEND']==ATTACH and old_hdf['source_author']==constants['AUTHOR'] and old_hdf['source_author_backend']==ATTACH)
    check('NF6_current_package_author_is_Full_and_contract_keeps_real_review_gate', nf_hdf['actor_id']==AUTHOR and nf_contract['author']==AUTHOR and nf_contract['review_decision']=='SOURCE_ACCEPTED_FOR_ROOT_FOUR_SELECTOR_NATIVE' and reg_contract['review_decision']=='SOURCE_ACCEPTED_FOR_ROOT_NF4_REGISTRATION')
    identities = [FULL,BACKUP,ATTACH,'codex:'+FULL,'codex:'+BACKUP,'codex:'+ATTACH]
    current_hardcodes = {k:[n.lineno for n in ast.walk(ast.parse(raw[k])) if isinstance(n,ast.Constant) and n.value in identities] for k in ('Main_profile','Main_index','Main_closure','Main_router','BR3_launcher')}
    check('Main_and_launcher_have_no_Full_Backup_Attach_literal_reviewer_selection', all(not values for values in current_hardcodes.values()),current_hardcodes)
    def disjoint(authors,executor,assembler,observer,verifier):
        return verifier.casefold() not in {actor.casefold() for actor in [*authors,executor,assembler,observer]}
    role_fixture = {'source_authors':[FULL], 'executor':'codex:/root','assembler':'codex:/root','root_observer':'codex:/root','verifier':BACKUP}
    check('new_Bridge_Full_author_Backup_verifier_satisfies_Main_independence_predicate',disjoint(role_fixture['source_authors'],role_fixture['executor'],role_fixture['assembler'],role_fixture['root_observer'],role_fixture['verifier']),{'Source_only_predicate_fixture_not_registered_role_or_audit':True,'roles':role_fixture})
    check('Full_self_verifier_canonical_Backup_relabel_and_Backup_author_are_rejected',not disjoint([FULL],'codex:/root','codex:/root','codex:/root',FULL) and not disjoint([BACKUP],'codex:/root','codex:/root','codex:/root',BACKUP) and ('codex:'+BACKUP)!=BACKUP,{'canonical_Backup_fails_actual_peer_author_equality':True})
    routes = constants['ROUTES']
    new_assignment=next(n for n in bridge_tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='NEW')
    expected_new=ast.parse('tuple(r for r in ROUTES if r[2] != "C19")',mode='eval').body
    check('exact_six_existing_routes_no_new_route_or_old_Current_source_reuse',len(routes)==6 and len(set(routes))==6 and ast.dump(new_assignment.value,include_attributes=False)==ast.dump(expected_new,include_attributes=False))
    check('current_Main_single_line_adoption_matches_conditional_NF6_pin', refs['Main_retrieval']==nf_hdf['conditional_Main_after_ref'] and nf_hdf['current_Source21_qualification'] is False,{'Root_Main_adoption_now_observed':True,'future_Native_Mode_qualification_not_claimed':True})
    check('source_and_mode_actor_gates_are_separate_dynamic_actual_origins',bool(references(pnodes['_role_registry'],'roles')) and bool(references(pnodes['_role_audit'],'proof')) and string_keys(cnodes['verify_mode'],'review') and 'reviewer_id' in string_keys(cnodes['verify_mode'],'decision'))
    evidence = {
      'BR3':s.code_evidence(raw['BR3_source'],refs['BR3_source']['path'],('source_review','native_inputs','consumer_plan','roles','assemble','capture')),
      'Main_profile':s.code_evidence(raw['Main_profile'],refs['Main_profile']['path'],('_role_audit','_role_registry','_route_execution_actor','_independent','_native','verify_owner')),
      'Main_closure':s.code_evidence(raw['Main_closure'],refs['Main_closure']['path'],('verify_mode',)),
      'consumer_launcher':s.code_evidence(raw['BR3_launcher'],refs['BR3_launcher']['path'],('main',)),
    }
    mode_rows = []
    for command,check_id,case_id in routes:
        mode_rows.append({'bridge_route':[command,check_id,case_id], 'mode_decision_route':[command,'W09',check_id,case_id], 'selector':check_id or case_id, 'mode':'LIVE_WINDOWS' if check_id=='W09-G02' else 'FIXTURE', 'producer_id':'codex:/root','reviewer_id':BACKUP,'issuer_id':BACKUP,'independent_review_actor_id':BACKUP,'state':'PENDING_ACTUAL_NF6_CLOSED_FACTS_AND_BACKUP_REVIEW'})
    result = {
      'schema':'researchos.w09-nf6-bridge-reviewer-actor-readiness.v1',
      'actor_id':AUTHOR,'backend_actor_id':FULL,'created_utc':datetime.now(timezone.utc).isoformat(),
      'decision':'BR3_VERIFIER_REPIN_REQUIRED',
      'finding':{'id':'NF6-BR3-VERIFIER-001','severity':'P1','source_ref':refs['BR3_source'],'line':29,'literal_current_verifier':FULL,'required_actual_verifier':BACKUP,'blocked_functions':uses,'effect':'roles/assemble/capture refuse actual Backup; Full is now the NF6 author and cannot be the independent verifier.'},
      'minimal_new_BR4_source_changes':[
        {'location':'w09_root_bridge.source.py:29','change':'VERIFIER = "/root/backup_regression_resources"; retain all uses and exact Main/audit gates.'},
        {'location':'w09_root_bridge.source.py:19,21,22','change':'As a new Source authored by Full, set AUTHOR="codex:/root/full_w09_source_review", AUTHOR_BACKEND="/root/full_w09_source_review", and the new bridge generation. Preserve original Attach HDF/MF/source refs as ancestry.'},
        {'location':'new BR4 HDF/MF/ROOT_CALL_CONTRACT.md and exact Source bindings','change':'Publish truthful new author/thread and selfrefs. Fresh Root Scope.source_actor must be Full backend and source_author_canonical Full canonical; no old Scope or old review/witness substitution.'},
      ],
      'no_Main_NF6_producer_or_consumer_launcher_business_change_required':True,
      'BR3_original_Attach_author_must_remain_immutable':True,
      'prospective_BR4_roles':role_fixture,
      'role_origin_requirements':{
        'roles_exact_fields':['source_authors','executor','assembler','verifier','root_observer'],
        'additional_actual_source_authors':'Include only truthful actual author identities and one typed, audited provenance entry per claimed actor; any additional current source author requires its own actual origin. Do not omit a current author merely to pass verifier independence.',
        'SOURCE_AUTHOR':{'origin_kind':'ROOT_SCOPE_REGISTRATION','locator':'/source_actor','actual_backend':FULL,'requirements':'New genuine Root-issued BR4 scope, accepted researchos.w09[-.]*scope.v1 schema, correct new source_hdf/source_mf/source_review bindings and exact Root-thread actual Full peer delivery.'},
        'EXECUTOR':{'origin_kind':'ACTUAL_MODE_DECISION','locator':'/producer_id','actor':'codex:/root'},
        'EVIDENCE_ASSEMBLER':{'origin_kind':'ROOT_OWNER_REGISTRATION','locator':'/selected_worker_id','requirements':'Real owner registration, scope_ref under W09 Source prefix, Root-issued W09_FULL_FORMAL_ASSEMBLY scope, ACTIVE finite lease covering context.created_at.'},
        'VERIFIER':{'origin_kind':'ACTUAL_MODE_DECISION','locator':'/reviewer_id','actor':BACKUP},
        'ROOT_OBSERVER':{'origin_kind':'ROOT_SCOPE_REGISTRATION','locator':'/issued_by','actor':'codex:/root'},
        'proof_exact_fields':['role','actor_id','origin_kind','raw_ref','actual_audit_ref'],
        'audit_required_fields':['schema','actor_id','role','Root_thread_id','source_audit_path','source_line_offsets','original_line_sha256','source_prefix_size_observed','original_capture_ref','binding_sha256'],
        'audit_schema':'researchos.w09.actual-role-audit.v1',
        'actual_peer_gate':'Original Root header + adjacent metadata/agent_message; exact author backend, recipient /root, client_authored=false, one input_text; unchanged strict metadata/result timestamp equality; exact offset/original bytes and bound full artifact digest. Never predict future timestamps or relabel actor.',
        'route_execution_refs':'Six exact command/check/case rows; genuine per-route scope_ref and owner_ref; all actors and registrations rechecked by Main.',
      },
      'mode_input_shape':{
        'mode_decision_schema':'researchos.w09-mode-decision.v2',
        'mode_decision_required_keys_from_Main':string_keys(cnodes['verify_mode'],'decision'),
        'independent_review_schema':'researchos.w09-independent-mode-review.v1',
        'independent_review_required_keys_from_Main':string_keys(cnodes['verify_mode'],'review'),
        'decision_QUALIFIED_only_after_actual_facts':True,
        'native_report_and_tool_row_refs':'Main registered_commands row native_report_ref/native_tool_run_ref/mode_decision_ref uses repository-relative two-key path/sha256 refs; fixed Native source/report/raw/Go pins must remain actual current NF6 bytes.',
        'independent_review_ref':'Exactly path/sha256/bytes, within repository and outside producer report parent.',
        'actor_literals':'producer_id codex:/root; reviewer_id and independent_review.actor_id actual backend /root/backup_regression_resources. Mode issuer_id may match Backup; the existing closure does not separately require issuer_id, while final formal review/issuance requires it exactly equal to verifier.',
        'FIXTURE':'OWNED_TEMP_DIR; actual IN_PROCESS_HTTptest_RECORDER exchanges; actual state root underneath the current process fixed physical C TEMP/TMP.',
        'LIVE_WINDOWS':'W09-G02 only: actual Windows11 x64, locked Go SHA, distinct exact host/junction three-key witness refs and frozen two-witness allowlist, current run/report/source/go bindings, actual successful mklink /J command/output/root/target matching owned event.',
        'six_rows':mode_rows,
        'two_route_selectors':'C19 and A06 each reuse their same current selector report/tool bundle, but require separate route-specific Mode decision documents. An independent current-run review can be shared where every bound actual run fact agrees.',
        'current_Source_requirement':'All four actual NF6 reports must bind the newly adopted current Source21; all six CM40 consumers run under RUN_CURRENT_CM40. Old NF5/C19 success remains historical.',
      },
      'Main_formal_entry':{'entry':'formal_profile_w09.verify_owner(api, reader, owner, roots, plan_path)','requires':'Actual ACCEPTED prospective owner, registered context/review/issuance roots, current role registry pinned in context/current checkpoint, dependency state, Main _native/_dispatches/_global/_independent replay, current complete Source/owned raw and audit ranges; Source readiness is no qualification.'},
      'inputs':refs,'source_evidence':evidence,
      'old_44_or_3905_controls_rerun':False,'Rootstages_or_product_called':False,
      'future_roles_scopes_Mode_qualification_refs':None,
      'Mode_signed':False,'execution_grant':False,'formal_acceptance':False,
    }
except BaseException as exc:
    failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed=g.close();guard_ref=s.write('source-guard.closed.json',closed)
    controls_ref=s.write('delta-controls.json',{'schema':'researchos.w09-nf6-bridge-reviewer-actor-readiness-controls.v1','checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'failure':failure,'guard_ref':guard_ref,'old_controls_rerun':False,'actual_product_calls':0,'execution_grant':False,'formal_acceptance':False})
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:
    print(json.dumps({'status':'READONLY_REVIEW_FAILED','failure':failure,'controls_ref':controls_ref,'guard_ref':guard_ref},ensure_ascii=False));raise SystemExit(1)
decision_ref=s.write('readiness-decision.json',dict(result,source_guard_ref=guard_ref,finite_controls_ref=controls_ref))
print(json.dumps({'status':'READONLY_REVIEW_COMPLETE_BR3_REPIN_REQUIRED','decision_ref':decision_ref,'controls_ref':controls_ref,'guard_ref':guard_ref,'passed':sum(c['passed'] for c in checks),'all_guards_closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'failure':None,'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
