"""Author the minimal Bridge04 Source delta; no stage or product invocation."""
from pathlib import Path
from datetime import datetime, timezone
import ast, copy, difflib, hashlib, json, re, traceback, types, uuid

R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99'
D=Path(__file__).resolve().parent
OLD=W/'w09_formal_root_bridge_source_codex/bridge-20261010-03'
READY=W/'nf6_bridge_reviewer_actor_readiness_source_codex/review-20261010-01'
sp=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py'
s=types.ModuleType('review_support');s.__file__=str(sp)
exec(compile(sp.read_bytes(),str(sp),'exec'),s.__dict__);s.D=D
AUTHOR='codex:/root/full_w09_source_review';BACKEND='/root/full_w09_source_review'
VERIFIER='/root/backup_regression_resources';GENERATION='bridge-20261010-04'

def exact(path,sha,size):return {'path':str(path),'sha256':sha,'bytes':size}
refs={
 'old_hdf':exact(OLD/'HDF.json','1f85ead2fffdd5400270c3d0f1078bb661df91fbd8ff94bfd1dd05992e45aa0f',7862),
 'old_mf':exact(OLD/'MF.json','225bb69692fde3fb0d54afa017a93248db968ef9e0a24cdd2c9a81b3ad0119d1',6046),
 'old_source':exact(OLD/'w09_root_bridge.source.py','327b0e886b58008ad33dcbcfaaaa2c44bc10d4076d3d3c717b2ce6e96914cbfb',49240),
 'old_launcher':exact(OLD/'consumer_launch.source.py','c64deb904e746fd2d5df6775e0b96375ce36741315109d47ab86408360de5011',1493),
 'old_contract':exact(OLD/'ROOT_CALL_CONTRACT.md','756b10ab0a4e7f798d9e4a0f7c994e23dc9e50fddddbaa560a8dcae9c0c21ea6',4147),
 'readiness_hdf':exact(READY/'HDF.json','9933572b41df21ebbda6563ef40b7ba2e7caf67618bc8da8ea0fbd4c100251b5',7756),
 'readiness_mf':exact(READY/'MF.json','8d4ad106580fb3de4dc80d07127378b0db19a827a95521f9fe7fb709f2843b34',2298),
 'readiness_decision':exact(READY/'readiness-decision.json','dd4f548764e40eb8f787c9145edad058eb9e59368559515139cd4bac66a14681',71243),
 'Main_profile':exact(R/'execution/v2.4/formal_profile_w09.py','d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f',71397),
 'Main_index':exact(R/'execution/v2.4/formal_case_index.py','e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b',71844),
}

def raw_write(name,raw):
    with (D/name).open('xb') as f:f.write(raw)
    return s.pin(D/name)

def top_nodes(raw):return {n.name:n for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def assignments(tree):
    return {n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
def need_predicate(node,code):
    hits=[n.args[0] for n in ast.walk(node) if isinstance(n,ast.Call) and ((isinstance(n.func,ast.Name) and n.func.id in ('need','require')) or (isinstance(n.func,ast.Attribute) and n.func.attr=='require')) and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value==code]
    if len(hits)!=1:raise ValueError('UNIQUE_PURE_SOURCE_PREDICATE:'+code)
    return hits[0]
def expression(node,env):return eval(compile(ast.Expression(body=copy.deepcopy(node)),'<Source-only-predicate>','eval'),{'__builtins__':{},'type':type,'set':set,'len':len},env)
def controls_fixture(label,kind,env,expected,node):
    observed=bool(expression(node,env));check(label,observed is expected,{'fixture_kind':kind,'actual_stage_called':False,'observed':observed,'expected':expected})

g=s.guard();checks=[];failure=None;built={};inverse=[];source_uuid=uuid.uuid4().hex
def check(name,ok,detail=None):
    checks.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise ValueError(name)

try:
    old_members=json.loads(Path(refs['old_mf']['path']).read_bytes())['members']
    for index,ref in enumerate(old_members):refs['old_member_'+str(index)]=ref
    g.acquire(list({ref['path']:ref for ref in refs.values()}.values()))
    old_hdf=json.loads(g.get_buffer(refs['old_hdf']['path']))
    before=g.get_buffer(refs['old_source']['path']);after=before
    changes=[
      ('AUTHOR = "codex:/root/attach_restore_independent_review"','AUTHOR = "codex:/root/full_w09_source_review"'),
      ('AUTHOR_BACKEND = "/root/attach_restore_independent_review"','AUTHOR_BACKEND = "/root/full_w09_source_review"'),
      ('BRIDGE_GENERATION = "bridge-20261010-03"','BRIDGE_GENERATION = "bridge-20261010-04"'),
      ('VERIFIER = "/root/full_w09_source_review"','VERIFIER = "/root/backup_regression_resources"'),
    ]
    for old,new in changes:
        if after.count(old.encode())!=1:raise ValueError('EXACT_SINGLE_ASSIGNMENT_REQUIRED')
        after=after.replace(old.encode(),new.encode(),1)
        inverse.append({'before_text':old,'after_text':new,'count':1})
    restored=after
    for row in reversed(inverse):
        if restored.count(row['after_text'].encode())!=1:raise ValueError('EXACT_SINGLE_INVERSE_REQUIRED')
        restored=restored.replace(row['after_text'].encode(),row['before_text'].encode(),1)
    check('four_assignment_exact_original_byte_inverse',restored==before,{'business_assignment':'VERIFIER','metadata_assignments':['AUTHOR','AUTHOR_BACKEND','BRIDGE_GENERATION']})
    old_tree=ast.parse(before);new_tree=ast.parse(after)
    old_assign=assignments(old_tree);new_assign=assignments(new_tree)
    changed=[key for key in old_assign if ast.dump(old_assign[key],include_attributes=False)!=ast.dump(new_assign[key],include_attributes=False)]
    check('only_four_expected_top_level_AST_assignments_change',set(changed)=={'AUTHOR','AUTHOR_BACKEND','BRIDGE_GENERATION','VERIFIER'},changed)
    normalized=copy.deepcopy(new_tree);na=assignments(normalized)
    for key in changed:na[key].value=copy.deepcopy(old_assign[key].value)
    check('whole_Source_AST_equals_BR3_after_inverse',ast.dump(normalized,include_attributes=False)==ast.dump(old_tree,include_attributes=False))
    old_funcs=top_nodes(before);new_funcs=top_nodes(after)
    check('all_ten_Root_stage_and_all_other_function_bodies_unchanged',set(old_funcs)==set(new_funcs) and all(ast.dump(old_funcs[key],include_attributes=False)==ast.dump(new_funcs[key],include_attributes=False) for key in old_funcs),{'stage_methods_invoked':0,'function_count':len(new_funcs)})
    check('STAGES_exact_ten_entries_and_TRUSTED_resources_unchanged',ast.dump(old_assign['STAGES'],include_attributes=False)==ast.dump(new_assign['STAGES'],include_attributes=False) and len(new_assign['STAGES'].value.keys)==10 and ast.dump(old_assign['TRUSTED'],include_attributes=False)==ast.dump(new_assign['TRUSTED'],include_attributes=False))
    check('six_routes_new_C19_policy_TEMP_and_offsets_gates_unchanged',all(ast.dump(old_assign[key],include_attributes=False)==ast.dump(new_assign[key],include_attributes=False) for key in ('ROUTES','NEW','PUBLIC_TEMP','RESOURCE_PARENT_REF','RESOURCE_AUDIT_REF','RESOURCE_OWNER_REF','ROOT_RESOURCE_AUDIT_PATH','ROOT_ACTOR','THREAD','ROLE_PATH','INDEX_PATH')))
    built['source_ref']=raw_write('w09_root_bridge.source.py',after)
    launcher=g.get_buffer(refs['old_launcher']['path'])
    built['consumer_launcher_ref']=raw_write('consumer_launch.source.py',launcher)
    check('consumer_launcher_actual_bytes_unchanged',built['consumer_launcher_ref']['sha256']==refs['old_launcher']['sha256'] and built['consumer_launcher_ref']['bytes']==refs['old_launcher']['bytes'])
    base={'AUTHOR':AUTHOR,'AUTHOR_BACKEND':BACKEND,'VERIFIER':VERIFIER,'ROOT_ACTOR':'codex:/root'}
    own_review=need_predicate(new_funcs['source_review'],'SOURCE_REVIEW_BINDING')
    ref_fixture={'path':str(D/'w09_root_bridge.source.py'),'sha256':built['source_ref']['sha256'],'bytes':built['source_ref']['bytes']}
    for actor in (AUTHOR,BACKEND,'codex:/root','/root'):
        env=dict(base,review={'reviewer_id':actor,'source_ref':ref_fixture},req={'bridge_source_ref':ref_fixture})
        controls_fixture('self_review_or_Root_rejected_'+actor,'Source-only independent-review expression',env,False,own_review)
    for actor in (VERIFIER,'/root/attach_restore_independent_review'):
        env=dict(base,review={'reviewer_id':actor,'source_ref':ref_fixture},req={'bridge_source_ref':ref_fixture})
        controls_fixture('non_author_review_identity_allowed_'+actor,'Source-only expression; no actual review or grant',env,True,own_review)
    role_pred=need_predicate(new_funcs['roles'],'ACTUAL_VERIFIER_SOURCE_AUTHOR')
    for label,verifier,authors,expected in (
      ('new_Backup_with_Full_backend',VERIFIER,[BACKEND],True),
      ('old_Full_verifier',BACKEND,[BACKEND],False),
      ('canonical_Backup_verifier','codex:'+VERIFIER,[BACKEND],False),
      ('canonical_Full_Source_author',VERIFIER,[AUTHOR],False),
      ('missing_current_Full_Source_author',VERIFIER,['/root/attach_restore_independent_review'],False),
    ):
        controls_fixture('roles_'+label,'Source-only role expression; no registered roles',dict(base,registry={'roles':{'verifier':verifier,'source_authors':authors}}),expected,role_pred)
    pnodes=top_nodes(g.get_buffer(refs['Main_profile']['path']))
    independent=need_predicate(pnodes['_role_registry'],'INDEPENDENT_ACTOR')
    for label,authors,verifier,expected in (
      ('Full_author_Backup_verifier',[BACKEND],VERIFIER,True),
      ('Full_author_Full_verifier',[BACKEND],BACKEND,False),
      ('Backup_author_Backup_verifier',[BACKEND,VERIFIER],VERIFIER,False),
    ):
        roles={'executor':'codex:/root','assembler':'codex:/root','root_observer':'codex:/root','verifier':verifier}
        controls_fixture('Main_independence_'+label,'Source-only Main predicate; no Main module/stage invocation',{'roles':roles,'authors':authors,'context':{'executor_id':'codex:/root'}},expected,independent)
    common=next(n for n in ast.walk(new_funcs['propose']) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='common').value
    common_values={ast.literal_eval(k):v for k,v in zip(common.keys,common.values)}
    check('future_Root_Source_actor_uses_new_true_Backend_and_canonical_metadata',expression(common_values['source_actor'],base)==BACKEND and expression(common_values['source_author_canonical'],base)==AUTHOR,{'actual_Scope_issued':False,'old_Scope_reused':False})
    formal_pred=need_predicate(new_funcs['capture'],'REAL_FORMAL_REVIEW')
    ref2=lambda ref:{key:ref[key] for key in ('path','sha256')}
    context_fixture={'path':'execution/v2.4/receipts/W09/W09-99/Source-only-never-issued-context.json','sha256':'0'*64}
    for actor,expected in ((VERIFIER,True),(BACKEND,False),('codex:'+VERIFIER,False)):
        controls_fixture('capture_reviewer_issuer_'+actor,'Source-only formal identity expression; no review emitted',dict(base,review={'reviewer_id':actor,'issuer_id':actor,'context_ref':context_fixture},req={'context_ref':context_fixture},ref2=ref2),expected,formal_pred)
    peer_author=next(n for n in ast.walk(new_funcs['capture']) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Subscript) and isinstance(n.left.value,ast.Name) and n.left.value.id=='payload' and isinstance(n.left.slice,ast.Constant) and n.left.slice.value=='author' and any(isinstance(k,ast.Name) and k.id=='VERIFIER' for k in ast.walk(n)))
    for actor,expected in ((VERIFIER,True),(BACKEND,False),('codex:'+VERIFIER,False)):
        controls_fixture('capture_actual_backend_author_'+actor,'Source-only actual peer author comparison; no raw audit fabricated',dict(base,payload={'author':actor}),expected,peer_author)
    check('Source_revision_UUID_is_new_package_only',re.fullmatch('[0-9a-f]{32}',source_uuid) is not None,{'source_revision_uuid':source_uuid,'future_Root_run_id_or_Scope_not_selected':True})

    diff=''.join(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True),after.decode('utf-8').splitlines(keepends=True),fromfile=str(OLD/'w09_root_bridge.source.py'),tofile=str(D/'w09_root_bridge.source.py')))
    built['patch_ref']=raw_write('bridge04.patch',diff.encode('utf-8'))
    built['exact_inverse_ref']=s.write('exact-inverse.json',{'schema':'researchos.w09-bridge04-exact-source-inverse.v1','before_ref':refs['old_source'],'after_ref':built['source_ref'],'replacements':inverse,'exact_byte_inverse':True,'all_function_bodies_and_stage_table_unchanged':True,'consumer_launcher_before_ref':refs['old_launcher'],'consumer_launcher_after_ref':built['consumer_launcher_ref'],'launcher_exact_bytes_unchanged':True})
    contract_text='''# Bridge04：真实 Full 作者与 Backup verifier

本包只替换 Bridge03 的 VERIFIER 业务常量；新作者 canonical 为 codex:/root/full_w09_source_review，backend 为 /root/full_w09_source_review，独立 verifier 必须为 /root/backup_regression_resources。原 Attach 作者的 Bridge03 HDF/MF/source/launcher/合同作为原始贡献精确引用，原包不修改。

十个 Root stage 的全部函数字节/AST 保持：seed、propose、activate、consume、roles、publish-registration、assemble、capture、check、derive。ROOT 仍为唯一 Main/Canon/Scope writer。新请求必须绑定本包实际 source_hdf_ref、source_mf_ref、bridge_source_ref、consumer_launcher_ref 和新的独立 source_review_ref/source_review_audit；Source 接受不构成运行授权。拒绝当前作者的 canonical/backend 自审以及 Root 自审。完整 Root request/grant actual toolpair、有限时序、current4 CAS、原始 offset/SHA/bytes 和资源审计门不变。

未来 Root 真正发行的新 consumers/assembly Scope.source_actor 必须为 /root/full_w09_source_review，source_author_canonical 必须为 codex:/root/full_w09_source_review，generation 为 bridge-20261010-04。不能借 Bridge03 Scope、旧 Source review 或预造 peer/lease。当前 Source_revision_uuid 仅是包身份，不是 Root 未来 run_id。

所有 Main 验证及六 consumer 真实进程仍必须使用 C:\\Users\\yqyyds\\.researchos\\w09-native-v5 作为精确 TEMP/TMP；通用 physical/checked 未放宽。相同 launcher 先核实际 TEMP/cache、资源来源和 locked Python/dispatcher，再在同一进程执行原 Main dispatcher。所有 C marker/父目录资源及 OwnedJob/guard 清理逻辑保持原样。

NF6 四个实际 current Source21 Native 成功闭合及独立 Mode 均是未来输入；Source 不生成 Mode 或资格。producer_id 为 codex:/root；Mode reviewer_id、independent review.actor_id 和 formal review reviewer_id/issuer_id 使用真实 backend /root/backup_regression_resources。五角色必须有完整真实 typed origins、独立 verifier 与真实作者/执行者/assembler/Root observer 分离；旧 actor、canonical relabel、未观察 peer 和未来时间不得通过。

NF6 使用 RUN_CURRENT_CM40 执行原六路：test.retrieval/W09-G01；test.retrieval/W09-G02；test.research.fixture/C19；test.retrieval/C19；test.retrieval/A06；test.security/A06。不能复用旧 Source21 的 Native/consumer 作为当前资格。六路 mode/schema/SHA/actualraw/W11 junction/current Source 门完全保留，未增加 route。

调用保持 locked Python -I -S -B -X utf8 w09_root_bridge.source.py <stage> --request <absolute-json> --sha256 <sha256> --bytes <bytes>。consumer_launch.source.py 的 argv 仍为 <bridge-sha256> <bridge-bytes> <command-key> <check-id> <case-id>，launcher 原字节不变，HERE 自动定位本包新 bridge。

所有新增 controls 均为 Source AST/纯条件 fixture；不是实际 Root grant、真实审计、产品 PASS、Mode qualification 或 formal acceptance。独立非作者审查及后续 Root 实际 Scope/registration/consumer/assembler/capture/Verifier 工作仍待进行。
'''
    built['contract_ref']=raw_write('ROOT_CALL_CONTRACT.md',contract_text.encode('utf-8'))
    built['root_calling_contract_ref']=s.write('root-calling-contract.source.json',{
      'schema':'researchos.w09-formal-root-bridge-source-calling-contract.v1','generation':GENERATION,
      'source_revision_uuid':source_uuid,'source_author':AUTHOR,'source_author_backend':BACKEND,'source_thread_id':s.THREAD,
      'Root_actor':'codex:/root','Root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','verifier_backend':VERIFIER,
      'source_ref':built['source_ref'],'consumer_launcher_ref':built['consumer_launcher_ref'],'contract_ref':built['contract_ref'],
      'request_schema':'researchos.w09-root-bridge-request.v1','stages':['seed','propose','activate','consume','roles','publish-registration','assemble','capture','check','derive'],
      'Source_review_decision':'ACCEPTED_SOURCE_ONLY',
      'Source_review_binding_fields':['source_ref','consumer_launcher_ref','source_hdf_ref','source_mf_ref'],
      'Source_review_actual_peer_proof_required':True,'Source_reviewer_must_not_be_author_or_Root':True,
      'Root_actual_request_and_grant_toolpairs_required':True,'dynamic_current4_CAS_and_finite_lease_required':True,
      'future_Scope_source_actor':BACKEND,'future_Scope_source_author_canonical':AUTHOR,
      'six_routes':[list(ast.literal_eval(r)) for r in new_assign['ROUTES'].value.elts],
      'NF6_C19_policy':'RUN_CURRENT_CM40','TEMP_TMP':r'C:\Users\yqyyds\.researchos\w09-native-v5',
      'CLI_prefix':[r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe','-I','-S','-B','-X','utf8',str(D/'w09_root_bridge.source.py')],
      'no_new_Source_acceptance_or_Mode_here':True,'future_Root_request_scope_grant_lease_refs':None,
      'execution_grant':False,'formal_acceptance':False,'actual_executed':False,
    })
    built['source_inputs_ref']=s.write('source-inputs.json',{'schema':'researchos.w09-bridge04-source-inputs.v1','refs':refs,'readiness_decision_ref':refs['readiness_decision'],'prior_BR3_Author':{'canonical':old_hdf['source_author'],'backend':old_hdf['source_author_backend'],'thread_id':old_hdf['actual_source_thread']},'old_44_and_BR3_22_controls_rerun':False,'new_delta_only':True})
except BaseException as exc:failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    closed=g.close();guard_ref=s.write('source-guard.closed.json',closed)
    controls_ref=s.write('delta-controls.json',{'schema':'researchos.w09-bridge04-source-delta-controls.v1','source_author':AUTHOR,'backend_author':BACKEND,'source_thread_id':s.THREAD,'source_revision_uuid':source_uuid,'checks':checks,'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'failure':failure,'guard_ref':guard_ref,'built_refs':built,'old_successful_controls_rerun':False,'pure_Source_only':True,'Root_stages_or_Main_modules_called':False,'actual_Native_Go_SQL_model_dispatcher_TP_calls':0,'Main_Canon_Scope_written':False,'execution_grant':False,'formal_acceptance':False})
print(json.dumps({'status':'SOURCE_FILES_BUILT_PENDING_SEAL' if failure is None else 'FAILED_SOURCE_BUILD','passed':sum(c['passed'] for c in checks),'failure':failure,'controls_ref':controls_ref,'guard_ref':guard_ref,'built_refs':built,'all_guards_closed':closed['closed'],'retained_handles_count':closed['retained_handles_count'],'execution_grant':False,'formal_acceptance':False},ensure_ascii=False))
if failure or not closed['closed'] or closed['retained_handles_count'] or closed['errors']:raise SystemExit(1)
