import ast,hashlib,json,pathlib,sys,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os'); O=pathlib.Path(sys.argv[1]); N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli43-post-integration-r324'
checks=[]; cache={}
def check(ok,label):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok: raise ValueError(label)
def read(p):
 p=pathlib.Path(p); p=p if p.is_absolute() else R/p
 if p not in cache: cache[p]=p.read_bytes()
 return cache[p]
def ref(p):
 p=pathlib.Path(p); p=p if p.is_absolute() else R/p; b=read(p)
 return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else p.as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def verify(v):
 a=ref(v['path']); check(a['sha256']==v['sha256'] and a['bytes']==v['bytes'],'ref:'+v['path']); return a
def obj(p): return json.loads(read(p))
def save(n,v):
 p=O/n; p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')); return ref(p)
pins={'register.py':'1b8f837711f66ab46bcf7ef8eb6783fdf5444bd60f170b70bfe70537808a3518','run.py':'f14820feac6b1383527cc20949b16407158341b536e220b15fd82d98b3145d06','seal.py':'495b7e5c573c0db19d0d915b6208cef339641b577db66ccaba1e26b99cc1fbab','prepared_refs.json':'3afe8d1a034d4825509b104f450235dd24b6c3fe43694faed5bdc6537c380f66','audit.json':'fa36677670debdc45325033de6740937a23d860d57c5192334a8eacf9429023e'}
try:
 for n,h in pins.items(): check(ref(N/n)['sha256']==h,'suppliedpin:'+n)
 trees=[]
 for n in ['register.py','run.py','seal.py']:
  t=ast.parse(read(N/n).decode('utf8')); t.body=[x for x in t.body if not (isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='MODE' for z in x.targets))]; trees.append(ast.dump(t))
 check(len(set(trees))==1,'three scripts identical except dispatch MODE')
 p=obj(N/'prepared_refs.json'); a=obj(N/'audit.json')
 check(a['expected_before']==[323,151,425] and a['expected_after']==[324,152,430],'tuples')
 for v in p['verified_refs']: verify(v)
 for v in list(p['scripts'].values())+p['original_refs']+p['desired_refs']+list(p['pins'].values()): verify(v)
 verify(p['audit_ref'])
 before=[]; after=[]; copies=[]
 for i,(live,old,new) in enumerate(zip(p['canonical_before'],p['original_refs'],p['desired_refs'])):
  verify(live); verify(old); verify(new); b=read(live['path']); check(b==read(old['path']),'live equals original '+str(i)); before.append(json.loads(b));after.append(obj(new['path']))
  cp=O/(str(i)+'-'+pathlib.Path(live['path']).name); cp.write_bytes(b);copies.append(ref(cp))
 check(len(copies)==4,'ordered canonical4')
 check([before[0]['revision'],before[1]['revision'],len(before[0]['failure_counters'])]==[323,151,425],'before tuple')
 check([after[0]['revision'],after[1]['revision'],len(after[0]['failure_counters'])]==[324,152,430],'after tuple')
 check(after[0]['failure_counters'][:425]==before[0]['failure_counters'],'old425 exact prefix')
 check(after[0]['failure_counters'][425:]==p['origins'] and len(p['origins'])==5,'exact5 append')
 for i,row in enumerate(p['origins']):
  check(row['original_payload']==obj(row['evidence_ref']['path']),'original payload '+str(i));check(row['count_once'] and row['attempts']==1 and row['retries_used']==0,'count once '+str(i))
 check([x['actual_native_exit'] for x in p['origins']]==[None,1,None,None,None],'nullable native mapping')
 check([x['actual_outer_exit'] for x in p['origins']]==[1,1,1,None,1],'outer mapping')
 check(before[2:]==after[2:] and all(read(p['original_refs'][i]['path'])==read(p['desired_refs'][i]['path']) for i in [2,3]),'ST CM byte unchanged')
 check(before[0]['current_effective_formal_status']==after[0]['current_effective_formal_status'],'formal unchanged')
 check(after[0]['head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856' and before[0]['head']=='a5d6d16ffaf129de0361470c3a1570228bd259a2','forward head')
 allowed={'head','revision','expected_previous_revision','updated_at','updated_by','failure_counters','work_in_progress','next_command','integrity_events','evidence_index'}
 check({k:v for k,v in before[0].items() if k not in allowed}=={k:v for k,v in after[0].items() if k not in allowed},'other checkpoint fields unchanged')
 check(after[0]['integrity_events'][:-1]==before[0]['integrity_events'],'integrity append only')
 check(after[0]['evidence_index'][:len(before[0]['evidence_index'])]==before[0]['evidence_index'],'evidence prefix')
 ow=json.loads(json.dumps(after[1]));ow['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']=before[1]['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration']
 for k in ['revision','amended_at','amended_by']:
  if k in before[1]:ow[k]=before[1][k]
  else:ow.pop(k,None)
 check(ow==before[1],'other ownership unchanged')
 sub=after[1]['card_path_bindings']['W05-99']['subtasks']['cli_exact8_source_integration'];check(sub['current_source_writer'] is None and sub['compile_test_SQL_HTTP_model_authorized'] is False,'writer closed no execution grant')
 check(after[0]['work_in_progress']['observed_actual_tool_origin_lower_bound_after_r324_cut']==431,'postcut lowerbound431')
 check(a['postcut_pending_origin_refs']==[p['pins']['aftercut_pending_origin']],'e1bbac pending separate')
 check(obj(p['pins']['cli_pre_registration_review']['path'])['post_registration_audit_ref'] is None,'no cyclic future audit')
 check(ref(N/'prepare-head.stdout.raw')['sha256'] and read(N/'prepare-head.stdout.raw').decode().strip()==after[0]['head'],'actual prepare head')
 check(read(N/'prepare-index.stdout.raw')==b'','actual prepare index empty')
 status=read(N/'prepare-status.stdout.raw');check(hashlib.sha256(status).hexdigest()==p['git_status_sha256'] and len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11,'13 status11oldD')
 for label in ['head','index','status','tree','parent','union']:
  j=obj(N/('prepare-'+label+'.invocation.json'));check(j['actual_native_exit']==0 and j['wrapper_error'] is None,'prepare readonlyGit '+label);verify(j['stdout_ref']);verify(j['stderr_ref'])
 # Recheck cached input bytes, no new source or product operations.
 for path,b in list(cache.items()):check(path.read_bytes()==b,'after unchanged:'+str(path))
 result={'checks':checks,'passed':len(checks),'failed':0,'actual_target_import_or_execution':False,'input_refs':[ref(x) for x in list(cache) if not x.is_relative_to(O)],'canonical_before':p['canonical_before'],'copied_canonical_before_refs':copies,'scripts':{n:ref(N/n) for n in pins}}
 save('read-audit.json',result); print(json.dumps({'output':str(O),'checks':len(checks),'inputs':len(result['input_refs']),'audit':ref(O/'read-audit.json')},ensure_ascii=True))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'checks':checks,'input_refs':[ref(x) for x in list(cache)]});raise