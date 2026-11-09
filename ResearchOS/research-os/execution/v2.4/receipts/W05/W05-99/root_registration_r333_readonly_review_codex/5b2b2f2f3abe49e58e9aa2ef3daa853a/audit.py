from pathlib import Path
import json,hashlib,copy,ast,os
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts';N=P/'W05/W05-99/integration_codex/desktop58-post-integration-r333-6cd1a3bb23fb45e1bcb26091d2b0a031'
checks=[];cache={};reused={};fresh={}
def ck(v,n):checks.append({'check':n,'passed':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def load(p):return json.loads(path(p).read_bytes())
def pin(p):
 p=path(p);h=hashlib.sha256();sz=0
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);sz+=len(b)
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':sz}
def key(p):return str(path(p)).casefold()
def verify(x,allow_reuse=True):
 k=key(x['path']);p=path(x['path'])
 if allow_reuse and k in reused:
  y=reused[k];ck((x['sha256'],x['bytes'])==(y['sha256'],y['bytes']),'prior protected pin exact '+str(p));return p
 if k not in cache:cache[k]=pin(p)
 y=cache[k];ck((x['sha256'],x['bytes'])==(y['sha256'],y['bytes']),'actual hash '+str(p));fresh[k]=y;return p
def doc(x):return load(verify(x))
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return pin(O/n)
pins={'prepared_refs.json':'6b420134f5f612166c8205df3213421716d6878a89bc4d18f233b60c2274ecf4','audit.json':'ec19061f15856910db2215930066597de60dd66bf3d76502a35f38ebf84c040e','preparation.manifest.json':'6a92ead81c5119708e8cc3127605635f35d09c6cd88f5c717d195e2bee71ed63','register.py':'1a8596d923d4fee0f3cde0b69cc2f4e74d62c370f4dc90e48704dc5bab348955','run.py':'133497733c55cf90d7cf229e7861f2fcab1ae314a6f3ff43058a332fc6ae972f','seal.py':'48164bf1cd3ef3939b20255d260c8885f63fed17d5885575453dfd0af6e2c0a2'}
for n,h in pins.items():ck(pin(N/n)['sha256']==h,'Root announced '+n)
p=load(N/'prepared_refs.json');q=doc(p['request_ref']);a=load(N/'audit.json');pm=load(N/'preparation.manifest.json')
for row in pm['entries']:verify(row)
ck(len({key(x['path']) for x in pm['entries']})==len(pm['entries']) and pm['self_excluded'] is True,'preparation MF exact unique entries')
srpath=P/'W13/W13-03/desktop58_forward_head_revision_independent_review_codex/335dbe67cc9a4ab39d2ff274e3c6f26a/review.json';sr=load(srpath);ck(pin(srpath)['sha256']=='777bb89972a963f7c6383252c3b28aa2c14a61769660655dbe34c666f98f993c' and sr['decision']=='READY_SOURCE_PREPARATION_ONLY' and sr['requested_changes']==[],'independent source review reused')
engine=verify(q['code_refs']['engine']).read_bytes();ck(engine==(N/'register.py').read_bytes(),'register selected engine exact')
for mode in ['register','run','seal']:
 b=(N/(mode+'.py')).read_bytes();ck(b==engine.replace(b"\nMODE = 'register'\n",("\nMODE = '"+mode+"'\n").encode(),1),'only MODE wholebyte delta '+mode);t=ast.parse(b);assigns=[n.value.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='MODE' for v in n.targets) and isinstance(n.value,ast.Constant)];ck(assigns==[mode],'single MODE AST '+mode)
ck(set(p['script_refs'])=={'engine','builder','register','run','seal'},'only three emitted modes no grant')
for x in p['script_refs'].values():verify(x)
closure=doc(p['source_closure_review_ref']);ck(closure['decision']=='SOURCE_COMMIT_EVIDENCE_CLOSED' and closure['reviewer']=='codex:/root/w05_merge_review','actual source closure review identity')
intent=doc(closure['source_intent_ref']);protected=doc(intent['protected_vector_ref']);ck(len(protected)==6983 and closure['protected_paths_current_hash_verified']==6983,'reuse prior actual6983 protected source proof')
reused={key(x['path']):x for x in protected}
ck(len(p['immutable_inputs'])==9148 and len({key(x['path']) for x in p['immutable_inputs']})==9148,'9148 unique prepared closure')
imm={key(x['path']):x for x in p['immutable_inputs']}
for x in p['immutable_inputs']:verify(x)
for x in q['immutable_inputs']:ck(key(x['path']) in imm and imm[key(x['path'])]['sha256']==x['sha256'] and imm[key(x['path'])]['bytes']==x['bytes'],'request closure is exact subset')
ck(key(p['request_ref']['path']) in imm,'explicit actual request frozen in prepared closure')
canon=q['canonical_before'];ck(len(canon)==len(q['original_copy_refs'])==len(p['original_refs'])==len(p['desired_refs'])==4,'four canonical shape')
copied=[];before=[];desired=[]
for i,(ca,orig,reqcopy,de) in enumerate(zip(canon,p['original_refs'],q['original_copy_refs'],p['desired_refs'])):
 b=verify(orig).read_bytes();ck(verify(reqcopy).read_bytes()==b and verify(ca,False).read_bytes()==b,'current4 equals both original copies '+str(i));before.append(b);desired.append(verify(de).read_bytes());ck(key(ca['path']) not in imm,'live canon excluded from immutable '+str(i))
 target=O/('canonical-before-'+str(i)+'.json')
 with target.open('xb') as f:f.write(b)
 copied.append(pin(target))
ck([path(x['path']).name for x in canon]==['checkpoint.json','path_ownership.json','step_state.json','commands.json'],'canonical order exact')
cp,ow=[json.loads(x) for x in before[:2]];origcp=copy.deepcopy(cp);origow=copy.deepcopy(ow);newcp,newow=[json.loads(x) for x in desired[:2]]
ck(p['before_tuple']==q['before_tuple']==[332,160,516] and p['after_tuple']==q['after_tuple']==[333,161,524],'fixed before/after tuple')
ck([cp['revision'],ow['revision'],len(cp['failure_counters'])]==p['before_tuple'] and cp['head']==p['head_before'],'actual canonical tuple / intentionally oldhead')
cut=doc(p['origin_cut_ref']);ck(cut['origins']==p['origins'] and cut['before_tuple']==p['before_tuple'] and cut['after_tuple']==p['after_tuple'] and cut['counter_reset'] is False,'fixed cut exact')
def allrefs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}<=set(v):yield v
  for x in v.values():yield from allrefs(x)
 elif isinstance(v,list):
  for x in v:yield from allrefs(x)
oldhashes={x['sha256'] for x in allrefs(cp['failure_counters'])};seen=set();originrows=[]
for row in p['origins']:
 raw=doc(row['evidence_ref']);ck(raw==row['original_payload'],'origin complete original payload '+row['origin_key']);ck(row['evidence_ref']['sha256'] not in oldhashes|seen and row['count_once'] and not row['counter_reset'],'origin append exactly once '+row['origin_key']);seen.add(row['evidence_ref']['sha256']);originrows.append({'origin_key':row['origin_key'],'actual_outer_exit':row['actual_outer_exit'],'actual_native_exit':row['actual_native_exit'],'evidence_ref':row['evidence_ref']})
ck(len(seen)==8,'eight exact original events')
cp['failure_counters']+=copy.deepcopy(p['origins']);cp.update(head=p['head'],revision=333,expected_previous_revision=332,updated_at=p['timestamp'],updated_by='codex:/root')
add={'desktop_exact15_source_integration_state':'CLOSED_PENDING_FRESH58_VALIDATION','desktop_exact15_source_integration_completed_ref':p['completed_ref'],'desktop_exact15_source_integration_manifest_ref':p['source_manifest_ref'],'desktop_exact15_source_integration_outer_manifest_ref':p['outer_manifest_ref'],'desktop_exact15_source_integration_grant_ref':p['source_grant_ref'],'desktop_exact15_source_integration_execution_review_ref':p['source_closure_review_ref'],'desktop_exact15_actual58_head':p['head'],'desktop_exact15_actual_combined_source_paths':58,'desktop_fresh58_validation_authorized':False,'desktop_GUI_install_NVDA_authorized':False}
cp['work_in_progress'].update(add)
cp['next_command']='Desktop source15/combined58 source commit closed; prepare separately reviewed fresh58 validation. No fresh compiler, runtime, GUI, SQL24 or formal acceptance is authorized by this head-forward registration.'
cp['integrity_events'].append({'event':'ROOT_DESKTOP58_FORWARD_HEAD_REGISTRATION','actor':'codex:/root','at':p['timestamp'],'before':p['before_tuple'],'after':p['after_tuple'],'head_before':p['head_before'],'head_after':p['head'],'completed_ref':p['completed_ref'],'execution_review_ref':p['source_closure_review_ref'],'origin_refs':[x['evidence_ref'] for x in p['origins']],'counter_reset':False,'formal_increment':0})
for k in ['request_ref','completed_ref','source_manifest_ref','outer_manifest_ref','source_grant_ref','source_closure_review_ref','source_closure_manifest_ref','origin_cut_ref']:
 if p[k]['path'] not in cp['evidence_index']:cp['evidence_index'].append(p[k]['path'])
sub=ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration'];ck(sub['owner']==sub['current_source_writer']=='codex:/root' and sub['source_paths']==p['source_paths'],'close only exact current Root source15 lease')
sub.update(current_source_writer=None,state='CLOSED_PENDING_FRESH58_VALIDATION',actual_head=p['head'],actual_unique_source_paths=58,actual_source_paths=15,completed_ref=p['completed_ref'],manifest_ref=p['source_manifest_ref'],outer_manifest_ref=p['outer_manifest_ref'],grant_ref=p['source_grant_ref'],execution_review_ref=p['source_closure_review_ref'],source_acceptance=False,formal_increment=0,compile_test_SQL_HTTP_model_authorized=False,GUI_authorized=False)
ow.update(revision=161,amended_at=p['timestamp'],amended_by='codex:/root')
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
ck(enc(cp)==desired[0] and cp==newcp,'CP entire independently reconstructed exact bytes');ck(enc(ow)==desired[1] and ow==newow,'OW entire independently reconstructed exact bytes');ck(desired[2:]==before[2:],'ST/CM unchanged bytes')
ck(newcp['failure_counters'][:516]==origcp['failure_counters'] and newcp['failure_counters'][516:]==p['origins'],'all old516 prefix exact')
ck(newcp['current_effective_formal_status']==origcp['current_effective_formal_status'] and newcp['current_effective_formal_status']['formal_cases_accepted']==0,'formal unchanged0')
runtime=doc(q['runtime_resources_ref']);ck(len(runtime['files'])==1212 and p['runtime_files']==runtime['files'],'exact source-scope runtime1212 reused')
runtimepins={key(x['path']):x for x in runtime['files']};runtimepins.update({key(x['path']):x for x in p['script_refs'].values()})
for x in a['observed_runtime']:
 y=runtimepins.get(key(x['path']));ck(y is not None and x['sha256']==y['sha256'] and x['bytes']==y['bytes'],'observed prepare pointtime fully prepinned '+x['path'])
ck(a['before']==p['before_tuple'] and a['after']==p['after_tuple'] and a['canonical_before']==canon and a['canonical_writes']==0 and a['Git_helper_DLL_product_calls']==0,'actual prepare audit metadata-only')
ck((R/'.git/refs/heads/main').read_text().strip()==p['head'] and p['head']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7','direct Main new HEAD')
ck(all(not os.path.lexists(R/x) for x in p['old_deleted_paths']) and len(p['old_deleted_paths'])==11,'old11D remain absent')
status=verify(p['status_ref']).read_bytes();source=doc(p['source_closure_review_ref']);E=path(source['completed_ref']['path']).parent;ck((E/'status-after.stdout.raw').read_bytes()==status and (E/'index-after.stdout.raw').read_bytes()==b'','latest saved source Job status13/indexempty')
src=engine.decode();ck("source_guard(p, lock, helper, 'register-pre-' + str(i))\n        need(all(raw(x) == b for x, b in zip(CANON, live)), 'four canonical completed prefix drift after source guard')\n        os.replace" in src,'immediate fourguard after sourceguard before each replace')
ck("source_guard(p, lock, helper, 'register-after')\n    need(all(raw(q) == b for q, b in zip(CANON, target))" in src and "source_guard(p, lock, helper, 'seal-current')\n    need(all(raw(q) == b for q, b in zip(CANON, target))" in src,'post longguards current4 rechecked')
ck(src.index("intent = save('canonical-write.intent.json'")<src.index("os.replace(q.with_name") and "recovery': 'Forward-only" in src,'persistent intent/forward-only prefix')
ck(p['authorized'] is False and p['future_root_grant'] is None and q['new_execution_grant'] is None and p['source_acceptance'] is False and p['formal_increment']==0,'no new execution scope/grant/acceptance')
for ca,b in zip(canon,before):ck(path(ca['path']).read_bytes()==b,'final live4 still same '+ca['path'])
ar=save('audit.json',{'checks':checks,'count':len(checks),'failed':[x for x in checks if not x['passed']],'actual_current_hash_unique_files':len(fresh),'prepared_closure_members':9148,'prior6983_source_hash_reuse':True,'origin_rows':originrows,'candidate_imports_or_executions':0,'new_failure_origins':[]})
save('fresh-verified-inputs.json',list(fresh.values()))
decision='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES'
review=save('review.json',{'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':decision,'requested_changes':[x for x in checks if not x['passed']],'actual_registration_executed':False,'expected_before':[332,160,516],'expected_after':[333,161,524],'register_sha256':pins['register.py'],'wrapper_sha256':pins['run.py'],'prepared_refs_sha256':pins['prepared_refs.json'],'audit_sha256':pins['audit.json'],'sealer_sha256':pins['seal.py'],'canonical_before':canon,'copied_canonical_before_refs':copied,'request_ref':p['request_ref'],'preparation_manifest_ref':pin(N/'preparation.manifest.json'),'source_preparation_review_ref':pin(srpath),'source_execution_closure_ref':p['source_closure_review_ref'],'independent_audit_ref':ar,'source_review_reuse':'Selected engine/builder exact bytes checked against source-preparation review; previous6983 protected source and closed58 proof reused by exact pins, not relabelled as new product execution. Other prepared refs actual-hashed.','runtime_boundary':'Python point-in-time metadata observation only; future owned Git/registration execution still pending.','root_run_argv_suffix':[p['request_ref']['path'],p['request_ref']['sha256'],str(O/'review.json'),'<actual review SHA>'],'root_seal_argv_suffix':[p['request_ref']['path'],p['request_ref']['sha256']],'future_scope_or_grant_authorized':False,'fresh58_qualified':False,'source_acceptance':False,'formal_increment':0,'fixed_origin_count':8,'outside_cut_origins':'Preserved externally by Root; not appended here or used to change fixed524.','new_failure_origins':[],'status':'STOPPED'})
hdf=save('handoff.json',{'review_ref':review,'decision':decision,'manifest_path':str(O/'manifest.json'),'new_failure_origins':[],'status':'STOPPED'})
members=[pin(x) for x in sorted(O.iterdir()) if x.is_file()];mf=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','count':len(members),'entries':members,'self_excluded':True})
print(json.dumps({'review':review,'manifest':mf,'handoff':hdf,'checks':len(checks),'failed':[x for x in checks if not x['passed']],'fresh_unique_files':len(fresh)},ensure_ascii=False))
