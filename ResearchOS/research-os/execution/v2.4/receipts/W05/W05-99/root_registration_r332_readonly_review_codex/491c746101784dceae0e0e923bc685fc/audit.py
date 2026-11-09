from pathlib import Path
import ast,copy,hashlib,json,os,traceback
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop15-source-integration-r332-8792799f829a23452ae5d89a59e1b0cf'
T=R/'execution/v2.4/receipts/W13/W13-03/desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060'
checks=[];cache={};observed={}
def ck(v,k,d=None):checks.append({'check':k,'passed':bool(v),'detail':d})
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def digest(p):
 h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b);n+=len(b)
 return h.hexdigest(),n
def pin(v):
 p=path(v);h,n=digest(p);return {'path':str(p),'sha256':h,'bytes':n}
def verify(r):
 p=path(r['path']);k=str(p).casefold()
 if k not in cache:cache[k]=digest(p)
 h,n=cache[k];ck((h,n)==(r['sha256'],r['bytes']),'hash '+str(p));observed[k]={'path':str(p),'sha256':h,'bytes':n};return p
def doc(v):return json.loads(path(v).read_bytes())
def rd(r):return doc(verify(r))
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
def save(n,v):
 with (O/n).open('xb') as f:f.write(enc(v))
 return pin(O/n)
try:
 fixed={'preparation.manifest.json':'6338f3f2ef4b7b0ab11aac2322d187ce51f86f55a44ee1f4e8253aaacaabc18b','prepared_refs.json':'daf3d3bd73285f77e90b5d4ab647a5fd5f6466cffde2e881273142a49654737a','audit.json':'ed240666b374e5af925082d8a18b773a5656865bfad478b9502236d24586d169','register.py':'bb3beccc2a4c2a576b648871dacc0dcab8f8bbff5258e1f0369d1d0af0f13280','run.py':'e05f99eb2d72fbb115bac841054125eb747d4d9ea13dd894872bceb0f069aa6a','seal.py':'6d89836241870e8e3c930a0a70525a01ce59882b26f810d238168e259209fc39','grant-producer.py':'d5b77a96df03a17939f750d5b8cf5a13f58921365cd70fa54f1b123e68ac143a'}
 for name,h in fixed.items():ck(pin(N/name)['sha256']==h,'fixed '+name)
 p=doc(N/'prepared_refs.json');m=doc(N/'preparation.manifest.json');binding=rd(p['binding_ref']); prior=rd(p['controller_review_ref'])
 ck(m['count']==len(m['entries'])==17,'17 complete manifest entries')
 ck(len({str(path(x['path'])).casefold() for x in m['entries']})==17,'manifest unique')
 for x in m['entries']:ck(verify(x).parent==N,'manifest local member')
 for x in p['immutable_inputs']:verify(x)
 for x in p['runtime_files']:verify(x)
 ck(len(p['immutable_inputs'])==8857 and len(p['runtime_files'])==1212,'fixed input cardinality')
 ck(prior['decision']=='READY_FOR_ROOT_EXACT15_SOURCE_COMMIT_ONCE_WITH_OPEN_GATES' and prior['requested_changes']==[] and prior['scope_sha256']==p['future_scope_ref']['sha256'],'prior actual bound review')
 canonical=binding['canonical_before_refs']; originals=[];desired=[];copies=[]
 names=['checkpoint','path_ownership','step_state','commands']
 for i,name in enumerate(names):
  actual=verify(canonical[i]);orig=verify(p['original_refs'][i]);dest=verify(p['desired_refs'][i]);raw=orig.read_bytes()
  ck(actual==R/f'execution/v2.4/{name}.json' and actual.read_bytes()==raw,'ordered live before '+name)
  with (O/(name+'.before.json')).open('xb') as f:f.write(raw)
  copies.append(pin(O/(name+'.before.json')));originals.append(raw);desired.append(dest.read_bytes())
 c0,o0=map(json.loads,originals[:2]);c1,o1=map(json.loads,desired[:2])
 ck(p['before_tuple']==[331,159,509] and p['after_tuple']==[332,160,516],'fixed tuples')
 ck([c0['revision'],o0['revision'],len(c0['failure_counters'])]==p['before_tuple'] and [c1['revision'],o1['revision'],len(c1['failure_counters'])]==p['after_tuple'],'actual desired tuples')
 ck(desired[2:]==originals[2:],'STCM byte identical')
 ck(c1['failure_counters'][:509]==c0['failure_counters'] and c1['failure_counters'][509:]==p['origins']==binding['confirmed_pending_origins'],'all509 prefix + exact7 original rows')
 ck(len(p['origins'])==len({x['origin'] for x in p['origins']})==7,'seven unique origin IDs')
 for row in p['origins']:
  ck(rd(row['evidence_ref'])==row['original_payload'],'full raw origin '+row['origin'])
  ck(row['count_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False,'origin once '+row['origin'])
 cp=copy.deepcopy(c0);ow=copy.deepcopy(o0)
 cp['failure_counters']+=copy.deepcopy(p['origins']);cp.update(revision=332,expected_previous_revision=331,updated_at=p['timestamp'],updated_by='codex:/root')
 additions={'desktop_exact15_source_integration_scope_ref':p['future_scope_ref'],'desktop_exact15_source_integration_controller_review_ref':p['controller_review_ref'],'desktop_exact15_source_integration_state':'ROOT_REGISTERED_WAIT_SEAL_AND_EXCLUSIVE_GRANT','desktop_fresh58_validation_authorized':False,'desktop_GUI_install_NVDA_authorized':False}
 cp['work_in_progress'].update(additions)
 cp['next_command']='Complete Desktop exact15 metadata seal; only the separately generated once-only Root grant may authorize the source-only15 import. No compiler/runtime/GUI qualification.'
 cp['integrity_events'].append({'event':'ROOT_DESKTOP15_SCOPE_REGISTRATION','before':[331,159,509],'after':[332,160,516],'scope_ref':p['future_scope_ref'],'counter_reset':False,'formal_increment':0})
 for x in [p['future_scope_ref'],p['controller_review_ref'],p['binding_ref']]:
  if x['path'] not in cp['evidence_index']:cp['evidence_index'].append(x['path'])
 sub=ow['card_path_bindings']['W13-03'].setdefault('subtasks',{});ck('desktop_exact15_source_integration' not in sub,'new unique lease')
 sub['desktop_exact15_source_integration']={'owner':'codex:/root','current_source_writer':'codex:/root','state':'ROOT_REGISTERED_WAIT_SEAL_AND_EXCLUSIVE_GRANT','scope_ref':p['future_scope_ref'],'controller_review_ref':p['controller_review_ref'],'source_paths':p['source_paths'],'candidate':p['candidate'],'source_path_cap':15,'apply_cap':1,'commit_cap':1,'compile_test_SQL_HTTP_model_authorized':False,'source_acceptance':False,'formal_increment':0}
 ow.update(revision=160,amended_at=p['timestamp'],amended_by='codex:/root')
 ck(cp==c1 and enc(cp)==desired[0],'entire desired CP exact independent reconstruction')
 ck(ow==o1 and enc(ow)==desired[1],'entire desired OW exact independent reconstruction')
 ck(c0['head']==c1['head']==p['head'] and c0['current_effective_formal_status']==c1['current_effective_formal_status'] and c1['current_effective_formal_status']['formal_cases_accepted']==0,'head/full historical formal retained0')
 ck(all(c0.get(k)==c1.get(k) for k in set(c0)|set(c1) if k not in ['revision','expected_previous_revision','updated_at','updated_by','failure_counters','work_in_progress','next_command','integrity_events','evidence_index']),'all protected CP including no_progress unchanged')
 ck(p['source_paths']==rd(rd(p['active_scope_payload_ref'])['scope']['exact15_ref']) if False else len(p['source_paths'])==15,'15 source lease')
 payload=rd(p['active_scope_payload_ref']);active=payload['scope'];scope_raw=enc(active)
 ck(hashlib.sha256(scope_raw).hexdigest()==p['future_scope_ref']['sha256'] and len(scope_raw)==p['future_scope_ref']['bytes'],'future active payload exact hash')
 ck(p['source_paths']==[x['path'] for x in rd(active['exact15_ref'])],'source lease exact15 paths')
 ck(payload['authorized'] is False and payload['future_root_grant'] is None and p['authorized'] is False and p['future_root_grant'] is None,'draft not grant')
 ck(not path(p['future_scope_ref']['path']).exists() and not (N/'canonical-write.intent.json').exists(),'no early active scope/CAS intent')
 ck(not path(active['new_output_root']).exists() and not path(str(active['new_output_root'])+'-outer').exists(),'fresh source outputs')
 grantroot=R/'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_root_grant_codex'/active['operation_uuid'];ck(not grantroot.exists(),'exclusive grant absent')
 template=(T/'metadata-engine.template.py').read_bytes();marker=b"\nMODE = 'register'\n";ck(template.count(marker)==1,'single mode anchor')
 for mode,name in [('register','register.py'),('run','run.py'),('seal','seal.py'),('grant','grant-producer.py')]:
  raw=verify(p['script_refs'][mode]).read_bytes();ck(raw==template.replace(marker,("\nMODE = '"+mode+"'\n").encode(),1),'whole file inverse '+mode);ast.parse(raw)
 ck((R/'.git/HEAD').read_text().strip()=='ref: refs/heads/main' and (R/'.git/refs/heads/main').read_text().strip()==p['head'],'direct Main HEAD without Git')
 ck(all(not os.path.lexists(R/x) for x in p['old_deleted_paths']) and len(p['old_deleted_paths'])==11,'old11D remains')
 ck(verify(p['status_ref']).read_bytes()==(path(binding['scope_ref']['path']).parent/'status.stdout.raw').read_bytes(),'frozen tracked status')
 bindDir=path(binding['scope_ref']['path']).parent
 ck((bindDir/'index.stdout.raw').read_bytes()==b'','saved indexempty; no fresh Git invoked')
 for label in ['head','branch','status','index','config','tree43','tree2cdb','tree06b','desktop-parent','desktop-delta6']:
  j=doc(bindDir/(label+'.invocation.json'));r=j['owned_result'];q=r['job_cleanup'];ck(j['actual_native_exit']==r['actual_exit']==0 and j['error'] is None and r['error'] is None and q['errors']==[] and q['job_idle_confirmed'] is True and q['handles_closed'] is True,'saved actual owned Git '+label)
 started=doc(N/'preparation.started.json');verify(started['input_ref']);done=doc(N/'preparation.completed.json');ck(done['actual_registration_executed'] is False and done['actual_product_execution'] is False and done['future_root_grant'] is None,'actual emitter completed only')
 ck(rd(started['input_ref'])['controller_review_ref']==p['controller_review_ref'],'actual emitter consumed bound review')
 source=template.decode();nodes={x.name:x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef)}
 reg=ast.get_source_segment(source,nodes['register']);reviewok=ast.get_source_segment(source,nodes['review_ok'])
 ck('four canonical completed prefix drift after source guard' in reg and 'four canonical target drift after final source guard' in reg and reg.count('os.replace(')==1 and 'enumerate(CANON[:2])' in reg,'immediate all4 guard and two replace only')
 ck("'copied_canonical_before_refs'" in reviewok and "'codex:/root/w05_merge_review'" in reviewok and "root_registration_r" in reviewok,'review consumer exact schema/actor/namespace')
 for actual in canonical:ck(digest(path(actual['path']))==(actual['sha256'],actual['bytes']),'live canonical after audit '+actual['path'])
 save('observed-inputs.json',list(observed.values()))
 save('canonical-copies.json',{'canonical_before':canonical,'copied_canonical_before_refs':copies})
 save('origin-mapping.json',[{'origin':x['origin'],'evidence_ref':x['evidence_ref'],'actual_outer_exit':x['actual_outer_exit'],'actual_native_exit':x['actual_native_exit'],'original_payload_preserved':True} for x in p['origins']])
 save('audit.json',{'schema':'researchos.root-registration-independent-readonly-audit.v1','checks':checks,'count':len(checks),'failed':[x for x in checks if not x['passed']],'distinct_hashed_refs':len(cache),'candidate_executions':0,'canonical_writes':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'distinct_hashed_refs':len(cache),'output':str(O)},ensure_ascii=False))
except BaseException:
 save('audit.exception.json',{'traceback':traceback.format_exc(),'candidate_executions':0});raise
