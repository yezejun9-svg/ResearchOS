from pathlib import Path
import json,hashlib,base64,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='246c20b781664b0e80fae7fd29b9b2b4';O=Path(__file__).parent;N=P/'integration_codex'/('cli43-fresh-held2-r329-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U
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
 s=read(N/'scope_registration.json');g=read(Path(s['new_authorization_root'])/'authorization.execute.json');result=read(E/'result.json');origin=read(E/'failure.origin.json');completion=read(N/'root-launch.outer-completion.json')
 ck('Root completion supplied SHA',ref(N/'root-launch.outer-completion.json')['sha256']=='ea3c614362df659939c8508d51d518e7a200a428568b8e90a80e7bfb4a1d0ae5')
 manifest_counts={}
 for folder,name,key in [(E,'manifest.json','files'),(L,'manifest.json','files'),(N,'root-launch.closed.manifest.json','members')]:
  mf=read(folder/name);manifest_counts[str(folder)]=len(mf[key]);ck('unique MF '+str(folder),len({path(x['path']) for x in mf[key]})==len(mf[key]))
  for x in mf[key]:verify(x)
 for k,v in completion.items():
  if k.endswith('_ref') and isinstance(v,dict) and all(y in v for y in ['path','sha256','bytes']):verify(v)
 ck('single underlying propagated1',completion['underlying_local_failure_count']==1 and completion['nested_exit_propagations_are_not_new_origins'] is True and [completion[k] for k in ['actual_outer_tool_exit','actual_python_caller_exit','actual_launcher_native_exit','actual_inner_python_native_exit']]==[1,1,1,1])
 ck('firstcause raw nullable preserved',origin==result['first_cause'] and origin['actual_stage_native_exit'] is None and origin['last_child_result']['actual_exit']==1 and origin['error']=="RuntimeError('Owned process failed')")
 ck('14 calls first13 succeed one qualified',result['native_calls']==14 and len(result['stages'])==13 and len(result['cases'])==1 and result['cases'][0]['status']=='PASS' and result['product_acceptance'] is False)
 roster=result['case_roster'];ck('first QUALIFIED second EXECUTED_FAILED',roster[0]['state']=='QUALIFIED' and roster[0]['qualified'] is True and roster[0]['fixture_observation']=='OBSERVED' and roster[1]['state']=='EXECUTED_FAILED' and roster[1]['launch_attempted'] is True and roster[1]['test_leaf_started'] is True and roster[1]['actual_native_exit']==1 and roster[1]['fixture_observation']=='NOT_STARTED')
 stagefacts=[]
 for stage in result['stages']:
  inv=read(verify(stage['result_ref']));rr=inv['result'];ck('native0 complete job '+stage['label'],inv['actual_exit']==0 and job(rr));d=rr.get('debug_capture');fact={'label':stage['label'],'actual_exit':rr['actual_exit'],'debug':d is not None}
  if d is not None:
   ck('complete debug '+stage['label'],d['complete'] is True and d['create_process_count']==d['exit_process_count'] and d['rejected_load_facts']==[])
   ck('all actual hFile unchanged '+stage['label'],all(x['before']==x['after'] for x in d['modules']))
   ck('all generation independent0 '+stage['label'],all(x['independent_exit']==0 and x['exit_continued'] is True for x in d['process_generations']))
   fact.update(generations=len(d['process_generations']),modules=len(d['modules']),create=d['create_process_count'],exit=d['exit_process_count'],closed=rr['job_cleanup']['explicit_owned_handle_close_successes'],remaining=rr['job_cleanup']['explicit_owned_handles_remaining'])
  stagefacts.append(fact)
 ck('SDK model external paid0',result['SDK_MODEL_external_paid']==0)
 ledgers={};previous={}
 for f in sorted(E.glob('ledger-add-*.json')):
  d=read(f);full=rowmap(d['full_members']);added=rowmap(d['added']);ck('ledger append immutable '+f.name,all(full.get(k)==v for k,v in previous.items()) and all(full.get(k)==v for k,v in added.items()) and set(full)==set(previous)|set(added));ledgers[d['revision']]=full;previous=full
 vectorfacts=[]
 for f in sorted(E.glob('*.vector.json')):
  d=read(f);expected=rowmap(d['expected_members']);observed=rowmap(d['observed_members']);ck('closed vector '+f.name,d['drift']==[] and len(expected)==len(d['expected_members'])==d['file_count'] and expected==observed==ledgers[d['revision']]);vectorfacts.append({'name':f.name,'revision':d['revision'],'files':d['file_count']})
 final=read(E/'after-finally.vector.json');fm=rowmap(final['expected_members']);ck('final compiled rev6 30207',final['revision']==6 and final['file_count']==30207)
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
 inv=read(E/'case-01.invocation.json');rr=inv['result'];d=rr['debug_capture'];j=rr['job_cleanup']
 ck('failed case native1 healthy closed capture',inv['actual_exit']==rr['actual_exit']==1 and rr['error'] is None and rr['timed_out'] is False and d['complete'] is True and d['rejected_load_facts']==[] and d['create_process_count']==d['exit_process_count']==3 and j['errors']==[] and j['job_idle_confirmed'] is True and j['explicit_owned_handles_remaining']==0 and j['explicit_owned_handle_close_successes']==45 and j['termination_requested'] is False)
 ck('three actual exits 1 1 3',[x['independent_exit'] for x in d['process_generations']]==[1,1,3] and all(x['before']==x['after'] for x in d['modules']))
 stagefacts.append({'label':'case-01','actual_exit':1,'generation_exits':[x['independent_exit'] for x in d['process_generations']],'complete':d['complete'],'cleanup':j})
 fixturefacts=[];cause={}
 for ci,leaf in enumerate(['real-existing-open-readonly','real-existing-self-send']):
  req=read(E/f'case-{ci:02d}.request.json');evidence=Path(req['environment']['RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR'])/('TestCLIProtocolInteractiveAuthority_'+leaf)
  files=sorted(evidence.iterdir())
  for f in files:
   if f.is_file():ref(f)
   if f.suffix=='.json':rawscan(read(f),'',f)
  proof=read(evidence/'closed-proof.json');firstrows=read(evidence/'db-post-open.rows.json');lastrows=read(evidence/'db-closed-copy.rows.json')
  ck('saved full typed rows equal '+leaf,firstrows==lastrows and proof['all_schema_column_typed_row_multisets_equal'] is True)
  ck('closed DB actual bytes '+leaf,all(ref(evidence/name)['sha256']==proof['original_after_close_sha256'] for name in ['session.sqlite','closed-copy.sqlite']) and proof['closed_bytes_equal'] is True and proof['original_reopened'] is False and proof['case_failed']==bool(ci))
  ck('four sidecars absent '+leaf,all(not Path(str(evidence/name)+suffix).exists() for name in ['session.sqlite','closed-copy.sqlite'] for suffix in ['-wal','-shm']))
  summary=read(evidence/'http-summary.json');expected=(5,2,7) if ci==0 else (12,9,21)
  ck('HTTP counters complete '+leaf,(summary['upstream']['dispatched'],summary['proxy']['admitted'],summary['actual_received_HTTP_legs'])==expected and summary['first_overflow'] is None and summary['pending']=={} and summary['stopped'] is False)
  cli=read(evidence/'invocation.json');ck('CLI native expected '+leaf,cli['exit_code']==(0 if ci==0 else 3) and cli['timeout'] is False)
  fixturefacts.append({'leaf':leaf,'files_hashed':len(files),'proof_ref':ref(evidence/'closed-proof.json'),'HTTP':expected,'CLI_invocation_ref':ref(evidence/'invocation.json'),'original_DB_ref':ref(evidence/'session.sqlite'),'copied_DB_ref':ref(evidence/'closed-copy.sqlite'),'typed_rows_ref':ref(evidence/'db-closed-copy.rows.json')})
  if ci==0:
   business=read(evidence/'business-counts.json');ident=read(evidence/'identity-proof.json');ck('qualified original business/identity',business=={'cli_exit':0,'read_only_attach':1,'send_journal':0,'sends':0,'tasks':0} and ident['before_sid']==ident['after_sid']==ident['db_sid'] and ident['epoch']==1)
   ck('case00 qualified three stages',read(E/'case-00.verified.json')==result['cases'][0] and (E/'case-00-fixture-after.vector.json').exists())
  else:
   rq=read(evidence/'requests.exact.json');rp=read(evidence/'responses.base64.json');presentation=read(evidence/'requests.json')
   ck('9 paired requests 7 commands 2 empty GET',len(rq)==len(rp)==len(presentation)==9 and [i for i,x in enumerate(rq) if x['bytes']==0]==[5,7])
   proxy=sorted([v for v in summary['records'].values() if v['layer']=='proxy'],key=lambda x:x['sequence']);pairs=[]
   for i,(q,b,rec) in enumerate(zip(rq,rp,proxy)):
    raw=b'' if q['raw_base64'] is None else base64.b64decode(q['raw_base64'],validate=True);reply=base64.b64decode(b,validate=True)
    ck('proxy paired exact request '+str(i),q==rec['request'])
    ck('proxy paired exact response '+str(i),reply==base64.b64decode(rec['accepted_body']['raw_base64'],validate=True))
    pairs.append({'index':i,'method':rec['request_method'],'uri':rec['request_uri'],'request_bytes':len(raw),'request_sha256':hashlib.sha256(raw).hexdigest(),'response_bytes':len(reply),'response_sha256':hashlib.sha256(reply).hexdigest(),'status':rec['status'],'sequence':rec['sequence']})
    if raw:
     env=json.loads(raw);res=json.loads(reply);ck('CommandResponse original identities '+str(i),all(env[k]==res[k] for k in ['command_id','method','session_id']) and res['status']=='COMPLETED')
    else:
     body=json.loads(reply);ck('known empty GET business scope '+str(i),rec['request_method']=='GET' and rec['status']==200 and body['project_id']==json.loads(base64.b64decode(rq[0]['raw_base64']))['project_id'])
   lines=(evidence/'stdout.jsonl').read_text(encoding='utf-8').splitlines();lines=[json.loads(x) for x in lines if x.strip()];terminal=lines[-1];task=read(evidence/'task.original.json')
   ck('CLI expected durable BLOCKED exit3',len(lines)==5 and terminal['reason']=='TASK_BLOCKED' and terminal['exit_code']==3 and terminal['execution']['status']=='UNRESOLVED' and terminal['execution']['task_id']==task['id'] and task['status']=='BLOCKED' and (evidence/'stderr.txt').stat().st_size==0)
   ck('no case01 qualification artifacts',(E/'case-01.verified.json').exists() is False and (E/'case-01-fixture-after.vector.json').exists() is False and (evidence/'business-counts.json').exists() is False)
   cause={'pairing':pairs,'first_invalid_command_JSON_input_index':5,'raw_input_bytes':0,'test_error':'unexpected end of JSON input','test_source_ref':ref(Path(req['cwd'])/'cli_sessions_test.go'),'helper_ref':s['instrumentation_helper_ref'],'CLI_stdout_ref':ref(evidence/'stdout.jsonl'),'CLI_stderr_ref':ref(evidence/'stderr.txt'),'CLI_terminal':terminal,'task_ref':ref(evidence/'task.original.json'),'fixture_observation_NOT_STARTED_means':'controller verifier not entered; actual HTTP occurred','fix_boundary':'transport-aware command-vs-GET audit classification; never blanket-skip empty requests; preserve full raw records and strict command schema/identity for POST /v2/command; validate exact Goal/Task GET method/path/status/JSON/resource linkage separately'}
 ck('all raw byte digests now consistent',mismatches==[])
 for x in g['canonical_copies']:ck('live grant canonical '+x['canonical_path'],verify(x['ref']).read_bytes()==(R/x['canonical_path']).read_bytes());ref(R/x['canonical_path'])
 cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');ck('current329157481',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[329,157,481])
 head=(R/'.git/HEAD').read_text().strip();hp=R/'.git'/head[5:] if head.startswith('ref: ') else None;ck('direct HEAD unchanged',(hp.read_text().strip() if hp else head)==s['source_commit'])
 helper=verify(s['instrumentation_helper_ref']);runner=verify(s['runner_ref']);hraw=helper.read_text(encoding='utf-8');ck('clone and unconditional command parser source', 'b=bytes.Clone(b);' in hraw and 'for i,raw:=range requests{' in hraw and 'canonicalRequest,e:=canonical.JSON(raw)' in hraw)
 save('cause.json',cause)
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'manifest_member_counts':manifest_counts,'native_stages':stagefacts,'vectors':vectorfacts,'graph_counts':graphfacts,'compiled_artifact_refs':{k:closure[k] for k in ['cli','testexe','test2json']},'compiled_current_files_hashed':len(compiled_refs),'fixture_facts':fixturefacts,'raw_records_scanned':raw_count,'HTTP_mismatches':mismatches,'DB_sqlite_opened_by_reviewer':False,'full_backing_resource_tree_rehashed':False,'qualification':'SECOND_CASE_WITHHELD','target_executions':0})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json'),'cause_ref':ref(O/'cause.json'),'raw_count':raw_count,'compiled_current_files_hashed':len(compiled_refs)},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
