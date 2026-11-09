import datetime,json,os,sys
from pathlib import Path
from preserve_main_baseline import verify,read,ref,git,R,N
from verify_cp554_main_preflight import BASE,CANDIDATE,TREE,FILES

def new(p,v):
 with p.open('x',encoding='utf8')as s:json.dump(v,s,ensure_ascii=False,indent=2);s.write('\n')
def swap(p,b,v):
 assert p.read_bytes()==b;q=p.with_name(p.name+'.cp555.pending')
 with q.open('xb')as s:s.write(v)
 assert p.read_bytes()==b;os.replace(q,p)

review_path=Path(sys.argv[1]);review_sha=sys.argv[2]
assert ref(review_path)['sha256']==review_sha
seal=read(review_path);assert seal['verdict']=='PASS_FOR_EXACT_SEVEN_PATH_LOCAL_FAST_FORWARD'and seal['blocking_findings']==0 and seal['candidate_commit']==CANDIDATE and seal['expected_tree_after']==TREE
review_root=review_path.parent;review_manifest=review_root/'PREFLIGHT-MANIFEST.json'
assert ref(review_manifest)['sha256']==seal['manifest_sha256'];review_refs=[]
for x in read(review_manifest)['files']:
 a=ref(review_root/x['path']);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];review_refs.append(a)
assert len(review_refs)==seal['reference_count']==73
assert ref(review_root/'DIAGNOSTICS.json')['sha256']==seal['diagnostics_sha256']
cp_p,ow_p,hp,sp=[R/('execution/v2.4/'+x)for x in ['checkpoint.json','path_ownership.json','HANDOFF_RESUME_PACK.md','step_state.json']]
raw={p:p.read_bytes()for p in [cp_p,ow_p,hp,sp]};cp=read(cp_p);ow=read(ow_p)
assert cp['revision']==554 and ow['revision']==340 and len(cp['failure_counters'])==2244
before=verify();prior=read(N/'continuation-cp554/RESUME.current.json')
assert git(R,'branch','--show-current').decode().strip()=='main'
assert git(R,'rev-parse',CANDIDATE+'^').decode().strip()==BASE
assert git(R,'rev-parse',CANDIDATE+'^{tree}').decode().strip()==TREE
assert sorted(git(R,'diff','--name-only',BASE,CANDIDATE).decode().splitlines())==FILES
V=N.parent.parent/'desktop_main7d_independent_review_codex/20261025-current-chat'
bound=[ref(review_path),ref(review_manifest),ref(N/'CP554-live-Main-integration-preflight.json'),ref(N/'088-cp554-main-preflight.recipe.result.json'),ref(V/'complete-tree/R3-REVIEW-SEAL.json'),ref(V/'native-proof/NATIVE-PROOF-REVIEW-SEAL.json'),ref(N/'continuation-cp554/Owned-native-Desktop-limited-adopted.json')]
O=N/'continuation-cp555';O.mkdir();now=datetime.datetime.now(datetime.timezone.utc).isoformat()
scope={'schema':'researchos.desktop-main-integration-scope.v1','at':now,'owner':'codex:/root','source_task_count':1,'operation':'LOCAL_FAST_FORWARD_ONLY','base':BASE,'candidate':CANDIDATE,'tree':TREE,'allowed_paths':FILES,'runner_ref':ref(N/'integrate_desktop_main_ecc28.py'),'post_gate_ref':ref(N/'preserve_desktop_main_ecc28.py'),'bound_evidence':bound,'precondition':'Exact direct child; empty index; original20dirty and48protectedrefs preserved; six new paths absent; main.js unchanged from Main base','postcondition':'Main HEAD/tree and seven on-disk files identical to reviewed candidate; index empty; all original dirty bytes/existence and protectedrefs retained','rollback_policy':'Do not reset/clean. Stop and retain raw if unexpected state; no automatic rollback','original_data_action':False,'C57_merge':False,'installer_claim':False,'formal_increment':0,'evidence_reuse':'Existing source/build/owned native evidence remains bound to the same candidate bytes and original isolated bundle/state; no claim of Main-root native rerun'}
new(O/'Desktop-Main-integration-scope.json',scope);new(O/'preservation.before-scope.json',before)
new(O/'Root-independent-preflight-ref-verification.json',{'verified_refs':review_refs,'review_seal_ref':ref(review_path),'blocking_findings':0})
records=[{'origin_key':'20261025|root-main-preflight-wait-aborted','attempts':1,'status':'TOOL_PROTOCOL_DIAGNOSTIC_PRESERVED','detail':'collaboration.wait_agent timeout40000 aborted before dispatch adjacent to reviewer preflight completion message; tool transcript only, no native operation','native_exit':None,'counter_reset':False},{'origin_key':'20261025|root-main-preflight-diagnostics-name-lookup','attempts':1,'status':'READONLY_PATH_LOOKUP_DIAGNOSTIC_PRESERVED','detail':'Guessed PREFLIGHT-DIAGNOSTICS.json after directory listing; actual file DIAGNOSTICS.json subsequently read and SHA verified. Outer command exit1; tool transcript only; no source/product effect','native_exit':1,'counter_reset':False}]
for d in read(review_root/'DIAGNOSTICS.json')['read_nonzero_results']:
 records.append({'origin_key':'20261025|desktop-main-preflight-review|'+d['read_step'],'attempts':1,'status':'READONLY_REVIEW_DIAGNOSTIC_PRESERVED','detail':d,'evidence_ref':ref(review_root/'DIAGNOSTICS.json'),'product_failure':False,'counter_reset':False})
assert len(records)==6 and not({x['origin_key']for x in records}&{x.get('origin_key')for x in cp['failure_counters']})
old_counters=list(cp['failure_counters']);cp['failure_counters'].extend(records);assert cp['failure_counters'][:2244]==old_counters and len(cp['failure_counters'])==2250
new(O/'new-records-ledger.json',{'records':records,'mixed_record_increment':6,'source_failures':0,'tests_executed':0,'counter_reset':False})
resume=prior.copy();resume.update(schema='researchos.current-chat-resume.v133',at=now,checkpoint_revision=555,ownership_revision=341,Desktop_Main_integration_scope_ref=ref(O/'Desktop-Main-integration-scope.json'),active_source_cards=[{'owner':'codex:/root','task':'Desktop exact seven-path local Main integration','scope_ref':ref(O/'Desktop-Main-integration-scope.json')}])
resume['failure_records_preserved']=2250
resume['next_command']='Root execute preregistered local fast-forward Main7d to independently reviewed Desktop ecc28 exact7, preserve original20dirty and48refs, then independent post-integration review. No C57 merge/original-data/native rerun. Admin USER_PREPARING_NOT_VERIFIED. Mixed2250;formal0/42/all22open.'
new(O/'RESUME.current.json',resume);rr=ref(O/'RESUME.current.json')
cp.update(revision=555,expected_previous_revision=554,updated_at=now,updated_by='codex:/root',next_command=resume['next_command']);cp['work_in_progress'].update(current_chat_continuation_cp555=rr,Desktop_Main_integration_scope_ref=ref(O/'Desktop-Main-integration-scope.json'));cp['evidence_index'].append({'kind':'DESKTOP_EXACT_SEVEN_MAIN_INTEGRATION_SCOPED_NOT_EXECUTED','ref':rr,'formal_increment':0})
ow.update(revision=341,expected_previous_revision=340,updated_at=now,updated_by='codex:/root');ow['special_paths']['Desktop_Main_integration']={'owner':'codex:/root','state':'EXACT_SEVEN_FAST_FORWARD_REGISTERED_NOT_EXECUTED','source_edit_authority':'EXACT_REVIEWED_BLOBS_ONLY','scope_ref':ref(O/'Desktop-Main-integration-scope.json'),'allowed_source_paths':FILES}
for p,name in [(cp_p,'checkpoint.before.raw.json'),(ow_p,'ownership.before.raw.json'),(hp,'handoff.before.raw.md')]:
 with(O/name).open('xb')as s:s.write(raw[p])
for p,b in raw.items():assert p.read_bytes()==b
swap(ow_p,raw[ow_p],(json.dumps(ow,ensure_ascii=False,indent=2)+'\n').encode());swap(cp_p,raw[cp_p],(json.dumps(cp,ensure_ascii=False,indent=2)+'\n').encode());swap(hp,raw[hp],('# Current verified continuation CP555\n\nRead '+rr['path']+' first. Root exact7 Main local fast-forward scope registered, not yet executed. Original20dirty/48refs protected; candidate ecc28 independently source/build/owned native limited accepted. C57 frozen; administrator preparation not verification. Mixed2250;formal0/42/all22open.\n\n').encode()+raw[hp]);assert sp.read_bytes()==raw[sp]
print(json.dumps({'checkpoint':555,'ownership':341,'mixed_records':2250,'scope':ref(O/'Desktop-Main-integration-scope.json'),'resume':rr,'formal_increment':0},ensure_ascii=False))
