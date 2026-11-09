import pathlib,hashlib,json,sqlite3,shutil,importlib.util,subprocess,sys,datetime
O=pathlib.Path(__file__).resolve().parent;SRC=O/'frozen-source/observe.py';sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('observer_independent',SRC);observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
observer.PROJECT='fixture-project';observer.SESSION='fixture-session';observer.OWNER='fixture-owner'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
F=O/'independent-fixtures';F.mkdir();results=[];oracle=[];real_connect=sqlite3.connect

def mutate_body(c,kind,key,value):
 raw=c.execute('SELECT body FROM domain_objects WHERE kind=?',(kind,)).fetchone()[0];body=json.loads(raw);body[key]=value
 c.execute('UPDATE domain_objects SET body=? WHERE kind=?',(json.dumps(body,ensure_ascii=True,indent=3).encode(),kind))
def consumed_body(c,key,value):
 raw=c.execute("SELECT body FROM idempotency WHERE operation='host:managed-runtime-qualification'").fetchone()[0];body=json.loads(raw);body['run_ref'][key]=value
 c.execute("UPDATE idempotency SET body=? WHERE operation='host:managed-runtime-qualification'",(json.dumps(body).encode(),))
def request_raw(c,changes=None,hash_override=None):
 req=json.loads(c.execute("SELECT body FROM idempotency WHERE operation='host:qualification-confirmation'").fetchone()[0]);req.update(changes or {})
 raw=json.dumps(dict(reversed(list(req.items()))),ensure_ascii=True,indent=4).encode()
 digest=hash_override or observer.qualification_request_digest(req)
 c.execute("UPDATE idempotency SET body=?,request_hash=? WHERE operation='host:qualification-confirmation'",(raw,digest))
 return req,raw,digest

cases=[
 ('valid-reordered-escaped-blob',False,True),('valid-noncanonical-run-blob',True,True),('valid-consumed-goal-cancelled',True,True),('valid-binary-identity-not-dumped',True,True),
 ('wrong-request-raw-hash',False,False),('request-bool-seconds',False,False),('invalid-utf8-body',False,False),('paused-preconfirm',False,False),
 ('run-wrong-id-body',True,False),('run-wrong-project-body',True,False),('run-wrong-task-body',True,False),('run-wrong-runtime-body',True,False),('run-wrong-context-bundle',True,False),('run-wrong-epoch-type',True,False),('run-missing-object',True,False),
 ('ref-wrong-entity',True,False),('ref-wrong-run-id',True,False),('ref-bool-revision',True,False),('ref-future-revision',True,False),('qualification-wrong-profile',True,False),('task-active-run-mismatch',True,False),('goal-wrong-scope',False,False),('budget-cycle',False,False)]
for name,consumed,expected in cases:
 db=F/(name+'.sqlite');shutil.copyfile(O/'author-replay'/('blob-consumed-paused.sqlite' if consumed else 'blob-preconfirm.sqlite'),db)
 with real_connect(db) as c:
  if name=='valid-reordered-escaped-blob':
   request,raw,digest=request_raw(c,{'owner_host':'主机😀<>&\\\n\t\u2028\u2029/组合e\u0301'})
   p=subprocess.run([str(O/'frozen-source/go-jcs-oracle/jcs-oracle.exe')],input=raw,capture_output=True);assert p.returncode==0 and p.stdout.decode().strip()==digest
   (F/(name+'.request.raw')).write_bytes(raw);(F/(name+'.oracle.stdout')).write_bytes(p.stdout);(F/(name+'.oracle.stderr')).write_bytes(p.stderr);oracle.append({'name':name,'exit':p.returncode,'raw_sha256':hashlib.sha256(raw).hexdigest(),'canonical_digest':digest,'raw_is_not_canonical':hashlib.sha256(raw).hexdigest()!=digest.removeprefix('sha256:')})
  elif name=='valid-noncanonical-run-blob':mutate_body(c,'Run','status','SETTLED')
  elif name=='valid-consumed-goal-cancelled':mutate_body(c,'Goal','status','CANCELLED')
  elif name=='valid-binary-identity-not-dumped':c.execute('INSERT INTO runtime_dispatches VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(observer.PROJECT,'fixture-run',3,'key','hash',json.dumps({'fixture':True}).encode(),'SETTLED','worker','locator',json.dumps({'public':'fixture'}).encode(),1,b'\xff\x00BINARY_FIXTURE_SENTINEL'))
  elif name=='wrong-request-raw-hash':
   req,raw,digest=request_raw(c);c.execute("UPDATE idempotency SET request_hash=? WHERE operation='host:qualification-confirmation'",('sha256:'+hashlib.sha256(raw).hexdigest(),))
  elif name=='request-bool-seconds':request_raw(c,{'purpose_seconds':True},hash_override='sha256:'+'a'*64)
  elif name=='invalid-utf8-body':c.execute("UPDATE idempotency SET body=? WHERE operation='host:qualification-confirmation'",(b'\xff',))
  elif name=='paused-preconfirm':mutate_body(c,'Goal','status','PAUSED')
  elif name.startswith('run-wrong-'):
   key,value={'run-wrong-id-body':('id','other-run'),'run-wrong-project-body':('project_id','other-project'),'run-wrong-task-body':('task_id','other-task'),'run-wrong-runtime-body':('runtime_id','other-runtime'),'run-wrong-context-bundle':('context_bundle_id','other-context'),'run-wrong-epoch-type':('lease_epoch','3')}[name];mutate_body(c,'Run',key,value)
  elif name=='run-missing-object':c.execute("DELETE FROM domain_objects WHERE kind='Run'")
  elif name.startswith('ref-'):
   key,value={'ref-wrong-entity':('entity_type','Task'),'ref-wrong-run-id':('id','another-run'),'ref-bool-revision':('revision',True),'ref-future-revision':('revision',3)}[name];consumed_body(c,key,value)
  elif name=='qualification-wrong-profile':c.execute('UPDATE runtime_qualification_runs SET profile_hash=?',('sha256:'+'e'*64,))
  elif name=='task-active-run-mismatch':mutate_body(c,'Task','active_run_id','other-run')
  elif name=='goal-wrong-scope':
   body=json.loads(c.execute("SELECT body FROM domain_objects WHERE kind='BudgetPolicy' AND id='fixture-GOAL'").fetchone()[0]);body['scope_id']='another-goal';c.execute("UPDATE domain_objects SET body=? WHERE kind='BudgetPolicy' AND id='fixture-GOAL'",(json.dumps(body).encode(),))
  elif name=='budget-cycle':
   body=json.loads(c.execute("SELECT body FROM domain_objects WHERE kind='BudgetPolicy' AND id='fixture-GOAL'").fetchone()[0]);body['parent_policy_id']='fixture-GOAL';c.execute("UPDATE domain_objects SET body=? WHERE kind='BudgetPolicy' AND id='fixture-GOAL'",(json.dumps(body).encode(),))
 observer.DATABASE=db;before=sha(db);queries=[];connects=[]
 def guarded(database,*args,**kwargs):
  assert database==db.as_uri()+'?mode=ro' and kwargs.get('uri') is True,(database,kwargs)
  assert db.is_relative_to(F) and db.drive.upper()=='C:';connects.append(str(database));conn=real_connect(database,*args,**kwargs);conn.set_trace_callback(queries.append);return conn
 observer.sqlite3.connect=guarded;result=None;error=None
 try:result=observer.observe('fixture-request','fixture-run' if consumed else None)
 except Exception as e:error={'type':type(e).__name__,'message':str(e)}
 finally:observer.sqlite3.connect=real_connect
 assert sha(db)==before and len(connects)==1
 assert (result is not None)==expected,(name,error)
 assert all(q.strip().split()[0].upper() in ['SELECT','PRAGMA','BEGIN','ROLLBACK'] for q in queries),queries
 if result:
  encoded=json.dumps(result,ensure_ascii=False,indent=2);assert 'EXCLUDED_FIXTURE_SECRET_HASH' not in encoded and 'BINARY_FIXTURE_SENTINEL' not in encoded
  assert result['original_request_hash_matches_canonical_request'] and result['original_task_goal_budget_binding_validated']
  if consumed:assert result['original_request_consume_run_task_binding_validated'] and not result['goal_active_preconfirm_guard_applied']
  else:assert result['goal_active_preconfirm_guard_applied']
  if name=='valid-reordered-escaped-blob':assert result['request_rows'][0]['selected_blob_storage']['body']['raw_sha256']==hashlib.sha256(raw).hexdigest()
  (F/(name+'.observed.json')).write_text(encoded+'\n',encoding='utf-8')
 results.append({'case':name,'expected_accept':expected,'accepted':result is not None,'error':error,'database_sha256_before_after':before,'readonly_uri':connects[0],'sql_trace':queries})
(O/'independent-results.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(SRC),'cases':results,'oracle':oracle,'all_expected_outcomes':True,'original_db_access':False,'launcher_executed':False,'api_calls':0,'model_calls':0,'formal_increment':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(results),'accepted_valid':sum(x['accepted'] for x in results),'rejected_invalid':sum(not x['accepted'] for x in results),'all_expected_outcomes':True,'actual_extra_go_oracle':len(oracle)}))
