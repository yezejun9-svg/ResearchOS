from pathlib import Path
import json,hashlib,base64,traceback
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';U='bf943a8137c74df09e010347615b0eec';O=Path(__file__).parent;N=P/'integration_codex'/('cli43-fresh-held2-r328-'+U);E=P/'cli43_fresh_compiler_executor_codex'/U;L=P/'cli43_fresh_compiler_launcher_codex'/U
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
 ck('Root completion supplied SHA',ref(N/'root-launch.outer-completion.json')['sha256']=='c5eb2ea279af775aef428ab309754dc3dcd04e81f20a6d6018b404a51adfa0f5')
 manifest_counts={}
 for folder,name,key in [(E,'manifest.json','files'),(L,'manifest.json','files'),(N,'root-launch.closed.manifest.json','members')]:
  mf=read(folder/name);manifest_counts[str(folder)]=len(mf[key]);ck('unique MF '+str(folder),len({path(x['path']) for x in mf[key]})==len(mf[key]))
  for x in mf[key]:verify(x)
 for k,v in completion.items():
  if k.endswith('_ref') and isinstance(v,dict) and all(y in v for y in ['path','sha256','bytes']):verify(v)
 ck('single underlying propagated1',completion['underlying_local_failure_count']==1 and completion['nested_exit_propagations_are_not_new_origins'] is True and [completion[k] for k in ['actual_outer_tool_exit','actual_python_caller_exit','actual_launcher_native_exit','actual_inner_python_native_exit']]==[1,1,1,1])
 ck('firstcause raw nullable preserved',origin==result['first_cause'] and origin['actual_stage_native_exit'] is None and origin['last_child_result']['actual_exit']==0 and origin['error']=="RuntimeError('Actual body bytes/SHA')")
 ck('13native no accepted cases',result['native_calls']==13 and len(result['stages'])==13 and result['cases']==[] and result['NOT_RUN']==['real-existing-self-send'] and result['product_acceptance'] is False)
 roster=result['case_roster'];ck('first executed unqualified second notstarted',roster[0]['state']=='EXECUTED_UNQUALIFIED' and roster[0]['launch_attempted'] is True and roster[0]['test_leaf_started'] is True and roster[0]['actual_native_exit']==0 and roster[0]['qualified'] is False and roster[1]['launch_attempted'] is False and roster[1]['actual_native_exit'] is None)
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
 request=read(E/'case-00.request.json');evidence=Path(request['environment']['RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR'])/'TestCLIProtocolInteractiveAuthority_real-existing-open-readonly'
 fixture_files=list(sorted(evidence.iterdir()))
 for f in fixture_files:
  if f.is_file():ref(f)
  if f.suffix=='.json':rawscan(read(f),'',f)
 proof=read(evidence/'closed-proof.json');firstrows=read(evidence/'db-post-open.rows.json');lastrows=read(evidence/'db-closed-copy.rows.json')
 ck('saved typed full rows equal',firstrows==lastrows and proof['all_schema_column_typed_row_multisets_equal'] is True)
 ck('actual closed DB hashes',all(ref(evidence/name)['sha256']==proof['original_after_close_sha256'] for name in ['session.sqlite','closed-copy.sqlite']) and proof['closed_bytes_equal'] is True and proof['original_reopened'] is False and proof['case_failed'] is False)
 ck('original and copy four sidecars absent',all(not Path(str(evidence/name)+suffix).exists() for name in ['session.sqlite','closed-copy.sqlite'] for suffix in ['-wal','-shm']))
 business=read(evidence/'business-counts.json');ident=read(evidence/'identity-proof.json');summary=read(evidence/'http-summary.json')
 ck('preserved business observation',business=={'cli_exit':0,'read_only_attach':1,'send_journal':0,'sends':0,'tasks':0} and ident['before_sid']==ident['after_sid']==ident['db_sid'] and ident['epoch']==1)
 ck('HTTP recorded5up2proxy7',summary['actual_received_HTTP_legs']==7 and summary['upstream']['dispatched']==5 and summary['proxy']['admitted']==2 and summary['first_overflow'] is None and summary['pending']=={} and summary['stopped'] is False)
 ck('exact four nonempty requested discrepancies',len(mismatches)==4 and [Path(x['file_ref']['path']).name for x in mismatches]==['upstream-handler-0002.json','upstream-handler-0003.json','upstream-handler-0004.json','upstream-handler-0005.json'] and all(x['json_pointer']=='/write_calls/0/requested' and x['derived_bytes']==x['recorded_bytes']>0 and not x['raw_base64_is_null'] for x in mismatches))
 relations=[]
 for name in ['upstream-handler-0002.json','upstream-handler-0003.json','upstream-handler-0004.json','upstream-handler-0005.json']:
  d=read(evidence/name);w=d['write_calls'][0];accepted=base64.b64decode(w['accepted']['raw_base64']);expected=w['requested']['sha256'];same=hashlib.sha256(accepted).hexdigest()==expected
  ck('accepted owned copy matches originally recorded requested hash '+name,same);relations.append({'file_ref':ref(evidence/name),'accepted_SHA_equals_original_requested_SHA':same})
 events=read(E/'case-00.test-events.observed.json');ck('actual test leaf ran',events['test_leaf_started'] is True)
 for x in g['canonical_copies']:ck('live grant canonical '+x['canonical_path'],verify(x['ref']).read_bytes()==(R/x['canonical_path']).read_bytes());ref(R/x['canonical_path'])
 cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json');ck('current328156469',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[328,156,469])
 head=(R/'.git/HEAD').read_text().strip();hp=R/'.git'/head[5:] if head.startswith('ref: ') else None;ck('direct HEAD unchanged',(hp.read_text().strip() if hp else head)==s['source_commit'])
 helper=verify(s['instrumentation_helper_ref']);runner=verify(s['runner_ref']);hraw=helper.read_text(encoding='utf-8');ck('actual alias producer source', '"raw_base64":b,"bytes":len(b)' in hraw and '"requested":cli43Bytes(p)' in hraw)
 ck('fixture-after qualification absent',not (E/'case-00-fixture-after.vector.json').exists() and not (E/'case-00.verified.json').exists())
 save('audit.json',{'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'manifest_member_counts':manifest_counts,'native_stages':stagefacts,'vectors':vectorfacts,'graph_counts':graphfacts,'compiled_artifact_refs':{k:closure[k] for k in ['cli','testexe','test2json']},'compiled_current_files_hashed':len(compiled_refs),'fixture_files_hashed':len(fixture_files),'raw_records_scanned':raw_count,'HTTP_mismatches':mismatches,'accepted_relationships':relations,'business':business,'identity':ident,'http_counters':{k:summary[k] for k in ['actual_received_HTTP_legs','upstream','proxy']},'DB_sqlite_opened_by_reviewer':False,'full_backing_resource_tree_rehashed':False,'qualification':'WITHHELD','target_executions':0})
 print(json.dumps({'checks':len(checks),'failed_checks':[x for x in checks if not x['passed']],'audit_ref':ref(O/'audit.json'),'mismatch_count':len(mismatches),'compiled_current_files_hashed':len(compiled_refs)},ensure_ascii=False))
except BaseException as e:
 save('audit.failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':checks,'input_refs':list(refs.values()),'target_executions':0});raise
