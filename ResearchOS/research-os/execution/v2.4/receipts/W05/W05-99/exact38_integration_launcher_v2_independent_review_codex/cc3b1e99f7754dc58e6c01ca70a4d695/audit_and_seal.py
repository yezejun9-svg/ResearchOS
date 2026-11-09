import ast,hashlib,json,difflib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/fresh-handler38-source-integration-r321-v2'
OLD=R/'execution/v2.4/receipts/W05/W05-99/exact38_integration_launcher_independent_review_codex/e274ec2ddcca4ba9ba7095fbc1ca4ef5'
FULL=R/'execution/v2.4/receipts/W05/W05-99/exact38_integration_controller_v2_independent_review_codex/98a6d4c78b3b4aa48abce9426fd44ca8'
reads=[]
def ref(p,pin=None):
 b=p.read_bytes();d={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if pin is not None and d['sha256']!=pin:raise RuntimeError('Hash mismatch: '+str(p))
 reads.append(d);return d
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
new=ref(S/'launcher.v2.py','be5fdfae7c321376dc60f964167a92f06725bfe83e97a826e50a6eae8f2a2bc2')
old=ref(S/'launcher.py','48abd3b7c0a1230b65fdf61c6075691d667e661356e5edaccdbf99f7390af0de')
a=(S/'launcher.py').read_bytes();b=(S/'launcher.v2.py').read_bytes()
needle=b'        out = safe(LOG_PARENT / uuid.uuid4().hex)\n        out.mkdir(exist_ok=False)\n'
replacement=b'        candidate = safe(LOG_PARENT / uuid.uuid4().hex)\n        candidate.mkdir(exist_ok=False)\n        out = candidate\n'
if a.count(needle)!=1 or a.replace(needle,replacement,1)!=b:raise RuntimeError('More than the exact ownership correction changed')
ast.parse(b,filename=str(S/'launcher.v2.py'))
with (O/'launcher.diff').open('xb') as f:f.write(''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='launcher.py',tofile='launcher.v2.py')).encode())
scope=ref(S/'scope_registration.json','254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90')
sd=json.loads((S/'scope_registration.json').read_bytes())
controller=ref(Path(sd['controller_ref']['path']),'e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff')
producer=ref(S/'grant-producer.py','dfbed4a9feb172a46aafa426775605428a1dc1f47d69b3d1c6cf91c50b0d6577')
helper=ref(Path(sd['owned_process_helper_ref']['path']),'6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad')
prior=ref(OLD/'review.json','399ba775df042fb9af555e7e3e7bc9f3ddf1fc0e8908a78fcc585be31669dfb2')
prior_mf=ref(OLD/'manifest.json','1435acc7e47a3a252447b88de539629190b9aff9a805b9bf8e4f6e3a3570c803')
full=ref(FULL/'review.json','ca641a19e3f10d0cda78a49719487987cd02eb396a4197ac33c6d7edd9aca66b')
full_mf=ref(FULL/'manifest.json','b15e2c3629bf033fbd6cc15f6941cc874a358a0d7e28b7855cd1de395e0981ff')
fr=json.loads((FULL/'review.json').read_bytes())
for key in ['checks','reads']:
 row=fr['basis'][key];ref(Path(row['path']),row['sha256'])
copies=[];docs=[]
for name in ['checkpoint','path_ownership','step_state','commands']:
 p=R/'execution/v2.4'/f'{name}.json';raw=p.read_bytes();docs.append(json.loads(raw))
 if raw!=(FULL/f'{name}.before.json').read_bytes():raise RuntimeError('Canonical changed since full static review: '+name)
 with (O/f'{name}.before.json').open('xb') as f:f.write(raw)
 copies.append({'canonical_path':str(p),'ref':ref(O/f'{name}.before.json')})
tuple_now=[docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]
if tuple_now!=[320,148,417]:raise RuntimeError('Unexpected current tuple')
review={'schema':'researchos.exact38-integration-controller-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE','requested_changes':[],
 'controller_sha256':controller['sha256'],'scope_sha256':scope['sha256'],'launcher_sha256':new['sha256'],
 'actual_integration_executed':False,'actual_registration_executed':False,'actual_launcher_executed':False,
 'current_canonical_tuple':tuple_now,'required_future_registration':[321,149,422],
 'refs':{'launcher_v2':new,'preserved_original_launcher':old,'controller':controller,'scope':scope,'grant_producer':producer,'owned_helper':helper,'previous_launcher_REQUEST_CHANGES':prior,'previous_launcher_manifest':prior_mf,'full_controller_v2_review':full,'full_controller_v2_manifest':full_mf},
 'resolved_findings':[
 {'id':'I38-LAUNCH-OWNERSHIP-01','status':'STATIC_RESOLVED','proof':'Exact byte diff changes only candidate creation and delayed out assignment. out remains None until exclusive mkdir succeeds; except/finally cannot write failure or manifest into a pre-existing candidate leaf.'},
 {'id':'I38-V2-PRELAUNCH-01','status':'STATIC_RESOLVED_WITH_REQUIRED_OUTER_V2','proof':'Pinned outer launcher encloses flags/scope/producer and controller pretry failures, preserves raw stdout/stderr and nullable process result, uses two distinct exclusive Jobs and finally seals owned output or explicit stderr fallback.'}],
 'inherited_verified_basis':{'audit_tool_chunk':'576cd2','actual_auditor_exit':0,'checks_passed':78815,'failed':0,'read_files':6467,'candidate_manifest_members':20,'protected_files':5173,'runtime_catalog_files':1211,'unique_source_paths':38,'large_vectors_rehashed_in_this_supplement':False},
 'static_execution_contract':{
 'only_launcher':new,'only_controller':controller,'only_scope':scope,
 'producer_timeout_seconds':600,'controller_timeout_seconds':4500,'each_owned_cleanup_seconds':5,
 'fixed_controller_Git_call_limit':56,'query_seconds':60,'FF_seconds':180,
 'scope_currently_authorized':False,'actual321_seal_and_nonself_registration_review_and_once_grant_required':True,
 'actual_four_canonical_copies_must_equal_grant_and_intent_desired_unchanged':True,
 'grant_operation_UUID_exclusive':True,'source_only_FF_max':1,'automatic_retry':False,'rollback_or_reset':False,
 'old11_deletions_and_empty_index_and_original417_failure_prefix_preserved':True,
 'new_failure_cut':5,'registered_after_cut':422,'two_later_pending_origins_retained_not_folded_into_cut':True,
 'formal_increment':0},
 'conditions':[
 'Root must invoke the exact reviewed launcher.v2.py under pinned Python -I -S -X utf8 from Main only after separately reviewed actual321 registration and successful seal. This review alone is not execution authority.',
 'Use actual321 four canonical immutable copies and actual sealed registration refs. No synthetic/pre-registration grant or reuse of old Root306/controller v1.',
 'Root serialises Main HEAD/index/canonical under integration lease. Fresh output operation UUID must remain absent and all before-source/protected checks must pass.',
 'Record actual outer tool completion separately; process creation may yield nativeNULL. Original stderr is fallback when no safe receipt leaf can be created.',
 'Any failure stops the once chain; after attempted FF do not infer HEAD from exit and do not reset/retry. Require a new forward-only recovery scope.',
 'Future generated register/run/seal scripts still require their own nonauthor registration review; this supplement reviewed only the existing preparation protocol and immutable launcher layer.'
 ],
 'limitations':['Static source/AST/hash review only: no launcher, producer, helper, controller, Git/native/product/SQL/HTTP/model invoked.','Python resource observations are point-in-time, not Git/OS full-lifecycle proof; same-user TOCTOU not excluded.','No fresh Main combined compilation or tests; source-only integration is distinct from acceptance of CLI43/Desktop58/provider/W09/22parents/42formal.'],
 'copied_canonical_before_refs':copies,'new_failure_origins':[],'source_or_formal_acceptance':False}
save('reads.json',reads.copy());rr=save('review.json',review)
mf=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'excluded':['manifest.json','handoff.json']})
handoff=save('handoff.json',{'decision':review['decision'],'review_ref':rr,'manifest_ref':mf,'launcher_ref':new,'controller_ref':controller,'scope_ref':scope,'actual_integration_executed':False,'new_failure_origins':[],'formal_increment':0})
print(json.dumps({'review':rr,'manifest':mf,'handoff':handoff},ensure_ascii=True))
