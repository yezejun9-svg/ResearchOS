from pathlib import Path
from collections import defaultdict
import json,hashlib,zlib,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W13/W13-03';E=P/'desktop_exact15_integration_executor_codex/8792799f829a23452ae5d89a59e1b0cf';L=E.with_name(E.name+'-outer');A=P/'desktop15_root_parameters_codex/8792799f829a23452ae5d89a59e1b0cf';checks=[]
def load(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def ck(v,n):checks.append({'check':n,'passed':bool(v)})
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(O/n)
c=load(E/'completed.json');s=load(c['scope_ref']['path']);g=load(c['grant_ref']['path']);pa=load(O/'audit.partial.json')
ck(pa['failed']==[{'check':'vector paths unique outer','passed':False}],'sole previous false predicate preserved')
b=load(L/'immutable-inputs.before.json');a=load(L/'immutable-inputs.after.json');groups=defaultdict(list)
for row in b:groups[str(Path(row['path'])).casefold()].append(row)
duplicates={k:v for k,v in groups.items() if len(v)>1}
ck(a==b and all(all(x['sha256']==v[0]['sha256'] and x['bytes']==v[0]['bytes'] for x in v) for v in groups.values()),'outer complete multiset byte-identical; repeated canonicalpaths equal pins')
launcher=Path(s['launcher_ref']['path']).read_bytes();ck(b"immutable=[pin(scopepath),pin(grantpath),s['launcher_ref'],s['controller_ref'],s['toolchain_lock_ref'],s['runtime_resources_ref'],hr,*controller.READS.values()]" in launcher,'producer intentional concatenation exact source line114')
catalog=load(s['runtime_resources_ref']['path']);allowed={str(Path(x['path'])).casefold():x for x in catalog['files']}
for k in ['controller_ref','launcher_ref','owned_process_helper_ref']:allowed[str(Path(s[k]['path'])).casefold()]=s[k]
runtime=[]
for root in [E,L]:
 for p in sorted(root.glob('runtime.*.json')):
  d=load(p);ck(d['kind']=='ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE','runtime honest boundary '+str(p));seen=set()
  for row in d['files']:
   k=str(Path(row['path'])).casefold();ref=allowed.get(k);ck(ref is not None and ref['sha256']==row['sha256'] and ref['bytes']==row['bytes'],'runtime prepin '+k);seen.add(k)
  ck(len(seen)==len(d['files']),'runtime unique '+str(p));runtime.append({'ref':pin(p),'observed_files':len(d['files'])})
obs_path=A/'owned-source-launch.tool-observations.closed.json';obs=load(obs_path);ck(pin(obs_path)['sha256']=='d009ad4619273fd5b74b30d5ce232f5dee81d9ed67387ecb3a93b093906d18df','Root actual toolobjects pin');ck(obs['closed'] is True and obs['actual_outer_tool_exit']==obs['actual_python_exit']==0 and obs['terminal_result']['exit_code']==0 and obs['terminal_result']['output']=='ACTUAL_PYTHON_EXIT=0\r\n','explicit outerPython nativebridge0')
launchreview=load(obs['final_launch_review_ref']['path']);ck(obs['initial_input']==load(launchreview['launch_request_ref']['path'])['exact_exec_command_input'],'actual exec input exactly reviewed packet')
ck(obs['actual_scope_ref']==c['scope_ref'] and obs['actual_grant_ref']['sha256']==c['grant_ref']['sha256'] and Path(obs['actual_grant_ref']['path'])==Path(c['grant_ref']['path']),'actual scope/grant semantic identical ref spelling')
head=c['actual_new_commit'];obj=R/'.git/objects'/head[:2]/head[2:];objfacts={'loose_commit_exists':obj.is_file()}
if obj.is_file():
 raw=zlib.decompress(obj.read_bytes());ck(hashlib.sha1(raw).hexdigest()==head,'direct commit object hash');header,body=raw.split(b'\0',1);ck(header==b'commit '+str(len(body)).encode(),'direct commit object type/size');parents=[x[7:].decode() for x in body.splitlines() if x.startswith(b'parent ')];ck(parents==[c['parent']],'direct commit single parent');objfacts.update({'commit_raw_sha256':hashlib.sha256(raw).hexdigest(),'parents':parents,'tree':body.splitlines()[0][5:].decode()})
for row in g['canonical_copies']:ck((R/row['canonical_path']).read_bytes()==Path(row['ref']['path']).read_bytes(),'final live canonical stable '+row['canonical_path'])
ck((R/'.git/refs/heads/main').read_text().strip()==head,'final direct HEAD remains imported source')
cp=load(R/'execution/v2.4/checkpoint.json');ow=load(R/'execution/v2.4/path_ownership.json');ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==[332,160,516] and cp['head']==c['parent'] and cp['current_effective_formal_status']['formal_cases_accepted']==0,'pending forward-head registration intentional; current516 formal0')
origins=[pin(x) for x in sorted(O.glob('failure-origin.*.json'))]
ar=save('completion-audit.json',{'checks':checks,'failed':[x for x in checks if not x['passed']],'prior_audit_ref':pin(O/'audit.partial.json'),'prior_checks':pa['checks'].__len__(),'superseded_predicate':{'check':'vector paths unique outer','reason':'Not a producer requirement; launcher concat explicitly repeats already verified refs. Full before/after multiset and all repeated pins are checked instead.'},'outer_repeated_paths':len(duplicates),'outer_duplicate_excess':len(b)-len(groups),'runtime_observations':runtime,'direct_commit_facts':objfacts,'new_failure_origins':origins})
ok=all(x['passed'] for x in checks)
review=save('review.json',{'schema':'researchos.desktop58-source-execution-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'SOURCE_COMMIT_EVIDENCE_CLOSED' if ok else 'REQUEST_CHANGES','requested_changes':[x for x in checks if not x['passed']],'actual_integration_executed_by_reviewer':False,'actual_source_integration_evidence_closed':ok,'completed_ref':pin(E/'completed.json'),'manifest_ref':pin(E/'manifest.json'),'outer_manifest_ref':pin(L/'manifest.json'),'outer_invocation_ref':pin(L/'invocation.final.json'),'source_intent_ref':pin(E/'source-transaction.intent.json'),'root_tool_observations_ref':pin(obs_path),'scope_ref':c['scope_ref'],'grant_ref':c['grant_ref'],'prelaunch_review_ref':obs['final_launch_review_ref'],'audit_refs':[pin(O/'audit.partial.json'),ar],'actual_parent':c['parent'],'actual_new_head':head,'source_candidate':c['source_candidate'],'source_paths':c['source_paths'],'source_path_count':15,'unique_combined_paths':58,'actual_git_invocations':43,'actual_git_native_nonzero':0,'apply_attempts':1,'commit_attempts':1,'controller_owned_native_exit':0,'outer_tool_exit':0,'outer_explicit_python_exit':0,'root_tool_observations_are_original_native_streams':False,'protected_paths_current_hash_verified':6983,'actual_unique_input_files_hash_verified':pa['verified_unique_files'],'immutable_vectors':pa['vectors'],'runtime_observations':runtime,'runtime_qualification':'POINT_IN_TIME_NOT_LIFECYCLE','canonical_tuple':[332,160,516],'canonical_writes_by_source_integration':0,'canonical_head_forward_registration':'PENDING_ROOT_REGISTRATION; no invented future tuple','source_acceptance':False,'fresh58_qualified':False,'author169_inherited_as_independent_current':False,'formal_increment':0,'formal_cases_accepted':0,'product_native_compile_SQL_HTTP_model_calls':0,'open_gates':['Root forward-head metadata registration after this independent review','Fresh combined58 build and independent Desktop169 validation','Installed GUI, NVDA, native frame, BrowserContinuity, P02/SDK/full formal42 remain OPEN'],'new_failure_origins':origins,'status':'STOPPED'})
hdf=save('handoff.json',{'review_ref':review,'decision':'SOURCE_COMMIT_EVIDENCE_CLOSED' if ok else 'REQUEST_CHANGES','manifest_path':str(O/'manifest.json'),'new_failure_origins':origins,'registered_failure_count':516,'new_review_tool_failure_count':len(origins),'status':'STOPPED'})
rows=[pin(p) for p in sorted(O.iterdir()) if p.is_file()];mf=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(rows),'entries':rows,'self_excluded':True})
print(json.dumps({'review':review,'handoff':hdf,'manifest':mf,'supplement_checks':len(checks),'failed':[x for x in checks if not x['passed']],'new_failure_origins':origins},ensure_ascii=False))
