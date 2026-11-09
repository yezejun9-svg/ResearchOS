from pathlib import Path
import json,hashlib,base64,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='c4f309c5528f5d42be5e7eeb146a20aa';O=Path(__file__).parent;N=P/'integration_codex'/('cli43-fresh-held2-r331-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U
checks=[];refs={}; mismatches=[];raw_count=0
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def ref(x):
 p=path(x);h=hashlib.sha256();length=0
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b);length+=len(b)
 a={'path':p.as_posix(),'sha256':h.hexdigest(),'bytes':length};refs[a['path']]=a;return a
def ck(n,v):checks.append({'check':n,'passed':bool(v)})
def verify(x):
 p=path(x['path']);a=refs.get(p.as_posix()) or ref(p);ck('pin '+str(p),a['sha256']==x['sha256'] and a['bytes']==x['bytes']);return p
def read(x):ref(x);return json.loads(path(x).read_bytes())
def save(n,x):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def rowmap(rows):return {path(x['path']):(x['sha256'],x['bytes']) for x in rows}
def job(rr):
 j=rr['job_cleanup'];return rr['actual_exit']==0 and rr['error'] is None and rr['timed_out'] is False and all(j[k] is True for k in ['assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[]
def rawscan(value,pointer,file):
 global raw_count
 if isinstance(value,dict):
  if all(k in value for k in ['raw_base64','bytes','sha256']):
   actual=b'' if value['raw_base64'] is None and value['bytes']==0 else base64.b64decode(value['raw_base64'],validate=True);raw_count+=1;dh=hashlib.sha256(actual).hexdigest()
   if len(actual)!=value['bytes'] or dh!=value['sha256']:mismatches.append({'file_ref':ref(file),'json_pointer':pointer,'recorded_bytes':value['bytes'],'recorded_sha256':value['sha256'],'derived_bytes':len(actual),'derived_sha256':dh,'raw_base64_is_null':value['raw_base64'] is None,'decoded_prefix_utf8':actual[:100].decode('utf-8',errors='replace')})
  for k,v in value.items():rawscan(v,pointer+'/'+k,file)
 elif isinstance(value,list):
  for i,v in enumerate(value):rawscan(v,pointer+'/'+str(i),file)
try:
 s=read(N/'scope_registration.json');g=read(Path(s['new_authorization_root'])/'authorization.execute.json');result=read(E/'result.json');completion=read(N/'root-launch.outer-completion.json')
 ck('Root completion supplied SHA',ref(N/'root-launch.outer-completion.json')['sha256']=='8d2b7c842836ded1bdc50b34feb4a74acfa62364040ffe51ceff3acaf6f75f06')
 manifest_counts={}
 for folder,name,key in [(E,'manifest.json','files'),(L,'manifest.json','files'),(N,'root-launch.closed.manifest.json','members')]:
  mf=read(folder/name);manifest_counts[str(folder)]=len(mf[key]);ck('unique MF '+str(folder),len({path(x['path']) for x in mf[key]})==len(mf[key]))
  for x in mf[key]:verify(x)
 for k,v in completion.items():
  if k.endswith('_ref') and isinstance(v,dict) and all(y in v for y in ['path','sha256','bytes']):verify(v)
 ck('actual success no firstcause',result['first_cause'] is None and result['secondary']==[] and not (E/'failure.origin.json').exists() and completion['underlying_local_failure_count']==0 and [completion[k] for k in ['actual_outer_tool_exit','actual_python_caller_exit','actual_launcher_native_exit','actual_inner_python_native_exit']]==[0,0,0,0])
 ck('14 native and two qualified',result['native_calls']==len(result['stages'])==14 and len(result['cases'])==2 and all(x['status']=='PASS' for x in result['cases']) and result['NOT_RUN']==[] and result['product_acceptance'] is False)
 roster=result['case_roster'];ck('actual complete roster',len(roster)==2 and all(x['state']=='QUALIFIED' and x['launch_attempted'] and x['resumed'] and x['test_leaf_started'] and x['actual_native_exit']==0 and x['fixture_observation']=='OBSERVED' and x['qualified'] and x['failure'] is None for x in roster))
 stagefacts=[]
 for stage in result['stages']:
  inv=read(verify(stage['result_ref']));rr=inv['result'];ck('native0 complete job '+stage['label'],inv['actual_exit']==0 and job(rr));d=rr.get('debug_capture');fact={'label':stage['label'],'actual_exit':rr['actual_exit'],'debug':d is not None}
  if d is not None:
   ck('complete debug '+stage['label'],d['complete'] is True and d['create_process_count']==d['exit_process_count'] and d['rejected_load_facts']==[])
   ck('all actual hFile unchanged '+stage['label'],all(x['before']==x['after'] for x in d['modules']))
   ck('all generation independent0 '+stage['label'],[x['independent_exit'] for x in d['process_generations']]==([0,0,3] if stage['label']=='case-01' else [0]*len(d['process_generations'])) and all(x['exit_continued'] is True for x in d['process_generations']))
   fact.update(generations=len(d['process_generations']),modules=len(d['modules']),create=d['create_process_count'],exit=d['exit_process_count'],closed=rr['job_cleanup']['explicit_owned_handle_close_successes'],remaining=rr['job_cleanup']['explicit_owned_handles_remaining'])
  stagefacts.append(fact)
 ck('SDK model external paid0',result['SDK_MODEL_external_paid']==0)
 ledgers={};previous={}
 for f in sorted(E.glob('ledger-add-*.json')):
  d=read(f);full=rowmap(d['full_members']);added=rowmap(d['added']);ck('ledger append immutable '+f.name,all(full.get(k)==v for k,v in previous.items()) and all(full.get(k)==v for k,v in added.items()) and set(full)==set(previous)|set(added));ledgers[d['revision']]=full;previous=full
 vectorfacts=[]
 for f in sorted(E.glob('*.vector.json')):
  d=read(f);expected=rowmap(d['expected_members']);observed=rowmap(d['observed_members']);ck('closed vector '+f.name,d['drift']==[] and len(expected)==len(d['expected_members'])==d['file_count'] and expected==observed==ledgers[d['revision']]);vectorfacts.append({'name':f.name,'revision':d['revision'],'files':d['file_count']})
 final=read(E/'after-finally.vector.json');fm=rowmap(final['expected_members']);ck('final compiled rev6 30204',final['revision']==6 and final['file_count']==30204)
 closure=read(E/'compiled-closure.json');compiled_refs={}
 for k in ['WORK','cache','importcfg','archives']:
  for x in closure[k]:compiled_refs[path(x['path'])]=x;ck('compiled row in beforecase '+str(path(x['path'])),fm.get(path(x['path']))==(x['sha256'],x['bytes']))
 for k in ['cli','testexe','test2json']:compiled_refs[path(closure[k]['path'])]=closure[k]
 for x in compiled_refs.values():verify(x)
 graphfacts={}
 for name in ['go-graph.actual.json','test2json-graph.actual.json']:
  d=read(E/name);graphfacts[name]={'packages':len(d['packages']),'referenced_files':len(d['all_referenced_files'])}
  ck('graph all refs in frozen vector '+name,all(fm.get(path(x['path']))==(x['sha256'],x['bytes']) for x in d['all_referenced_files']))
  ck('graph no errors '+name,all(not x.get('Error') and not x.get('DepsErrors') for x in d['packages']))

 def decodebody(x):return b'' if x['raw_base64'] is None and x['bytes']==0 else base64.b64decode(x['raw_base64'],validate=True)
 def typed(rows,table):
  columns=[json.loads(v)[1] for v in rows['columns'][table]];out=[]
  for text in rows['tables'][table]:
   cells=json.loads(text);item={}
   for k,(kind,val) in zip(columns,cells):item[k]=None if kind=='null' else int(val) if kind=='integer' else float(val) if kind=='real' else base64.b64decode(val).decode('utf-8') if kind=='text' else base64.b64decode(val)
   out.append(item)
  return out
 modulecount=0
 for stage in result['stages']:
  inv=read(verify(stage['result_ref']));dbg=inv['result'].get('debug_capture')
  if dbg:
   for mod in dbg['modules']:
    actual=mod['path_from_actual_file_handle'].removeprefix(chr(92)*2+'?'+chr(92));q=Path(actual)
    ck('actual hFile pin '+stage['label']+' '+actual,fm.get(q)==(mod['before']['sha256'],mod['before']['bytes']) and mod['before']==mod['after']);modulecount+=1
 fixturefacts=[];pairfacts=[]
 for ci,leaf in enumerate(['real-existing-open-readonly','real-existing-self-send']):
  req=read(E/f'case-{ci:02d}.request.json');evidence=Path(req['environment']['RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR'])/('TestCLIProtocolInteractiveAuthority_'+leaf)
  for file in sorted(evidence.iterdir()):
   if file.is_file():ref(file)
   if file.suffix=='.json':rawscan(read(file),'',file)
  proof=read(evidence/'closed-proof.json');rows=read(evidence/'db-closed-copy.rows.json')
  ck('full schema columns typed multiset equality '+leaf,rows==read(evidence/'db-post-open.rows.json') and proof['all_schema_column_typed_row_multisets_equal'] is True and proof['case_failed'] is False)
  ck('DB bytes original and immutablecopy '+leaf,all(ref(evidence/name)['sha256']==proof['original_after_close_sha256'] for name in ['session.sqlite','closed-copy.sqlite']) and len({proof[k] for k in ['copy_after_sha256','copy_before_sha256','original_after_close_sha256','original_after_read_sha256']})==1 and proof['original_reopened'] is False)
  for name in ['db-closed-original.files.json','db-copy-before-read.files.json','db-copy-after-close.files.json','db-original-after-copy.files.json']:
   f=read(evidence/name);ck('stored absent sidecars '+leaf+name,f['-wal'] is None and f['-shm'] is None and f['']['sha256']==proof['original_after_close_sha256'])
  ck('current sidecars absent '+leaf,all(not Path(str(evidence/name)+suffix).exists() for name in ['session.sqlite','closed-copy.sqlite'] for suffix in ['-wal','-shm']))
  cr=read(evidence/'db-copy-read-result.json');cl=read(evidence/'db-close-result.json');ck('actual DB close and immutable URI '+leaf,cr['close_error']==cr['read_error']==cl['original_close_error']==cl['snapshot_error']=='<nil>' and 'immutable=1&mode=ro' in cr['uri'] and cr['original_reopened'] is False)
  summary=read(evidence/'http-summary.json');expected=(5,2,7) if ci==0 else (12,9,21)
  ck('HTTP complete counts '+leaf,(summary['upstream']['dispatched'],summary['proxy']['admitted'],summary['actual_received_HTTP_legs'])==expected and summary['first_overflow'] is None and summary['pending']=={} and summary['stopped'] is False and summary['unobserved_client_outbound_attempts'] is None)
  for rec in summary['records'].values():
   ck('HTTP completed admission '+leaf+str(rec['sequence']),rec['completed'] is True and rec['admitted'] is True)
   if rec['layer']=='upstream':ck('upstream full read close '+leaf+str(rec['sequence']),rec['response_observed'] is True and rec['read_EOF_observed'] is True and rec['response_close_error'] is None and rec['whole_response_transmitted_to_CLI_claim'] is False)
   else:
    ck('proxy no fabricated socket observation '+leaf+str(rec['sequence']),rec['actual_client_received_body'] is None and rec['actual_client_received_headers'] is None and rec['unobserved_socket_delivery'] is True)
    for w in rec['write_calls']:ck('write accepted exact '+leaf+str(rec['sequence']),w['error'] is None and w['actual_n']==w['requested']['bytes']==w['accepted']['bytes'] and decodebody(w['requested'])==decodebody(w['accepted']))
  cfgb=read(evidence/'config.before.json');cfga=read(evidence/'config.after.json');before=read(evidence/'session-before.json');after=read(evidence/'session-after.json');ident=read(evidence/'identity-proof.json');business=read(evidence/'business-counts.json')
  sessions=typed(rows,'client_sessions');ck('one actual Session sameSID epoch1 '+leaf,len(sessions)==1 and sessions[0]['id']==before['session_id']==after['session_id']==ident['before_sid']==ident['after_sid']==ident['db_sid'] and sessions[0]['writer_epoch']==before['writer_epoch']==after['writer_epoch']==ident['epoch']==1)
  cli=read(evidence/'invocation.json');ck('CLI exact current executable '+leaf,cli['exit_code']==(0 if ci==0 else 3) and cli['timeout'] is False and path(cli['actualargv'][0])==path(closure['cli']['path']) and (evidence/'stderr.txt').stat().st_size==0)
  ck('business exact '+leaf,business=={'cli_exit':0 if ci==0 else 3,'read_only_attach':1,'send_journal':ci,'sends':ci,'tasks':ci})
  rq=read(evidence/'requests.exact.json');rp=read(evidence/'responses.base64.json');transport=read(evidence/'transport.exact.json');proxy=sorted([v for v in summary['records'].values() if v['layer']=='proxy'],key=lambda x:x['sequence']);posts=[];getentities=[];pairs=[]
  ck('exact arrays '+leaf,len(rq)==len(rp)==len(transport)==len(proxy)==(2 if ci==0 else 9))
  for i,(q,encoded,tr,rec) in enumerate(zip(rq,rp,transport,proxy)):
   request=decodebody(q);response=base64.b64decode(encoded,validate=True);body=json.loads(response)
   ck('transport exact pair '+leaf+str(i),tr['request_index']==tr['response_index']==i and tr['status']==rec['status']==200 and tr['method']==rec['request_method'] and tr['request_uri']==rec['request_uri'] and request==decodebody(rec['request']) and response==decodebody(rec['accepted_body']))
   if tr['method']=='POST':
    env=json.loads(request);posts.append((env,body,response));ck('POST full identity SID project '+leaf+str(i),tr['request_uri']=='/v2/command' and env['method']!='session.create' and env['session_id']==sessions[0]['id'] and env['project_id']==sessions[0]['project_id'] and all(env[k]==body[k] for k in ['command_id','method','session_id']) and body['status']=='COMPLETED' and body['error'] is None and body['error_code'] is None)
    if env['method']=='session.attach':ck('actual read-only attach '+leaf,env['payload']['request_write_owner'] is False and body['result']['write_owner_acquired'] is False)
    if env['method'] in ['session.attach','session.send','session.get']:
     snap=body['result'] if env['method']=='session.get' else body['result']['snapshot'];ck('nested snapshot SID/project/epoch '+leaf+str(i),snap['session_id']==sessions[0]['id'] and snap['project_id']==sessions[0]['project_id'] and snap['writer']['epoch']==1)
   else:
    ck('strict GET exact route '+leaf+str(i),tr['method']=='GET' and request==b'' and tr['request_uri'] in ['/v1/projects/'+sessions[0]['project_id']+'/goals/'+body['id'],'/v1/projects/'+sessions[0]['project_id']+'/tasks/'+body['id']] and body['binding']['route']=='THIN_CORE' and body['project_id']==sessions[0]['project_id']);getentities.append(body)
   pairs.append({'index':i,**tr,'request_sha256':hashlib.sha256(request).hexdigest(),'response_sha256':hashlib.sha256(response).hexdigest()})
  ck('one attach zero create bounded send '+leaf,sum(e['method']=='session.attach' for e,_,_ in posts)==1 and sum(e['method']=='session.send' for e,_,_ in posts)==ci)
  journal=typed(rows,'idempotency');ids=typed(rows,'client_command_identities');objects=typed(rows,'domain_objects')
  for env,body,response in posts:
   js=[v for v in journal if v['key']==env['command_id'] and v['operation']=='v2:'+env['method']];identrows=[v for v in ids if v['command_id']==env['command_id']]
   ck('sole durable journal identity '+leaf+env['command_id'],len(js)==len(identrows)==1 and js[0]['status']==200 and (js[0]['body'].encode() if isinstance(js[0]['body'],str) else js[0]['body'])+b'\n'==response and identrows[0]['request_hash']==js[0]['request_hash'])
  ck('actual task count '+leaf,sum(x['kind']=='Task' for x in objects)==ci)
  if ci:
   goal,task=getentities;send=[v for v in posts if v[0]['method']=='session.send'][0];snap=send[1]['result']['snapshot'];savedtask=read(evidence/'task.original.json');terminal=json.loads((evidence/'stdout.jsonl').read_text(encoding='utf-8').splitlines()[-1])
   ck('send Goal Task DB full link',snap['goal_id']==goal['id']==task['goal_id']==sessions[0]['goal_id']==ident['completed_send_goal_id'] and goal['task_ids'].count(task['id'])==1 and task['id']==sessions[0]['task_id']==savedtask['id']==terminal['execution']['task_id'] and task==savedtask and task['status']=='BLOCKED' and terminal['reason']=='TASK_BLOCKED' and terminal['exit_code']==3)
   ck('REST exact domain DB objects',all(len([v for v in objects if v['kind']==kind and v['id']==body['id'] and json.loads(v['body'])==body])==1 for kind,body in [('Goal',goal),('Task',task)]))
   ck('native identity proof passed',ident['REST_goal_count']==ident['REST_task_count']==1 and ident['REST_send_goal_task_links_validated'] is True)
  else:ck('read-only no REST entity',getentities==[] and ident['REST_goal_count']==ident['REST_task_count']==0)
  events=[json.loads(v) for v in (E/f'case-{ci:02d}.stdout.raw').read_text(encoding='utf-8').splitlines() if v.strip()];test='TestCLIProtocolInteractiveAuthority/'+leaf
  ck('actual leaf pass no failure or skip '+leaf,any(x.get('Action')=='run' and x.get('Test')==test for x in events) and any(x.get('Action')=='pass' and x.get('Test')==test for x in events) and not any(x.get('Action') in ['fail','skip'] for x in events) and (E/f'case-{ci:02d}.stderr.raw').stat().st_size==0)
  ck('qualified fixture-stage artifact '+leaf,read(E/f'case-{ci:02d}.verified.json')==result['cases'][ci] and (E/f'case-{ci:02d}-fixture-after.vector.json').is_file())
  fixturefacts.append({'leaf':leaf,'HTTP':expected,'proof_ref':ref(evidence/'closed-proof.json'),'identity_ref':ref(evidence/'identity-proof.json'),'business_ref':ref(evidence/'business-counts.json'),'CLI_invocation_ref':ref(evidence/'invocation.json'),'typed_rows_ref':ref(evidence/'db-closed-copy.rows.json'),'original_DB_ref':ref(evidence/'session.sqlite'),'copy_DB_ref':ref(evidence/'closed-copy.sqlite'),'tables':len(rows['tables']),'CLI_exit':cli['exit_code'],'Go_test_exit':0});pairfacts.append({'leaf':leaf,'pairs':pairs})
 ck('all captured HTTP digests consistent',mismatches==[])
 for x in g['canonical_copies']:ck('current canonical equals grant '+x['canonical_path'],verify(x['ref']).read_bytes()==(R/x['canonical_path']).read_bytes());ref(R/x['canonical_path'])
 cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');ck('current331159509',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[331,159,509])
 head=(R/'.git/HEAD').read_text().strip();hp=R/'.git'/head[5:] if head.startswith('ref: ') else None;ck('direct HEAD',(hp.read_text().strip() if hp else head)==s['source_commit'])
 X=Path(s['new_export_root']);instrument=read(E/'instrumentation.actual.json');verify(instrument['export_test']);verify(instrument['helper']);ck('actual instrumented inputs match reviewed',instrument['export_test']['sha256']==s['instrumented_source_ref']['sha256'] and instrument['helper']['sha256']==s['instrumentation_helper_ref']['sha256'] and instrument['unmodified_Main_testexe'] is False)
 legacy=X/'spec/v2.0/contracts/domain.schema.json';lr=ref(legacy);ld=read(legacy);hraw=verify(s['instrumentation_helper_ref']).read_text(encoding='utf-8');ts=(X/'apps/cli/cli_sessions_test.go').read_text(encoding='utf-8')
 ck('exact legacy fixture/helper schema origin',lr['sha256']=='b11439c80d15c9481d7940c98eb6517b5156470f871c839e505a8dce40e0b847' and lr['sha256'] in hraw and 'filepath.Join("..","..","spec","v2.0","contracts","domain.schema.json")' in hraw and 'svc, err := domain.New(db, "../../spec/v2.0/contracts", "../../migrations/sqlite/0002_domain.sql")' in ts and ld['$defs']['ProjectBinding']['properties']['route']['enum']==['PAPERCLIP','THIN_CORE'])
 ck('legacy schema in actual vector',fm.get(legacy)==(lr['sha256'],lr['bytes']))
 for file in E.glob('*.python-os.*.json'):
  d=read(file);ck('Python pointtime honest '+file.name,d['point_in_time_only'] is True and d['Python_lifecycle_proof'] is False and all(fm.get(path(x['path']))==(x['sha256'],x['bytes']) for x in d['files']))
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'manifest_member_counts':manifest_counts,'native_stages':stagefacts,'vectors':vectorfacts,'graph_counts':graphfacts,'compiled_artifact_refs':{k:closure[k] for k in ['cli','testexe','test2json']},'compiled_current_files_hashed':len(compiled_refs),'actual_module_records_compared':modulecount,'fixture_facts':fixturefacts,'raw_records_scanned':raw_count,'HTTP_mismatches':mismatches,'transport_pairings':pairfacts,'DB_sqlite_opened_by_reviewer':False,'full_backing_resource_tree_rehashed':False,'qualification':'BOUNDED2_PENDING_REVIEW','target_executions':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json'),'raw_records':raw_count,'compiled_files_hashed':len(compiled_refs)},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
