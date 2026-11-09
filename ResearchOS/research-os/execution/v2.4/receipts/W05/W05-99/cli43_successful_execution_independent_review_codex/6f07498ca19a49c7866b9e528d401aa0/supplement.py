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

a=read(O/'audit.json');s=read(N/'scope_registration.json');E=Path(s['new_output_root']);X=Path(s['new_export_root']);g=read(Path(s['new_authorization_root'])/'authorization.execute.json');result=read(E/'result.json');closure=read(E/'compiled-closure.json')
ck('only prior false predicate is idempotency statusHTTP200',len(a['failed_checks'])==9 and all(x['check'].startswith('sole durable journal identity ') for x in a['failed_checks']))
source=R/'internal/domain/client_protocol.go';raw=source.read_text(encoding='utf-8');ref(source);ck('actual producer status0', 'hash, 0, string(rb), headers' in raw)
ref(R/'internal/api/v2.go');ck('actual HTTP LF encoder','json.NewEncoder(w).Encode(v)' in (R/'internal/api/v2.go').read_text(encoding='utf-8'))
def typed(d,t):
 cs=[json.loads(x)[1] for x in d['columns'][t]]
 return [dict(zip(cs,[None if k=='null' else int(v) if k=='integer' else base64.b64decode(v).decode() if k=='text' else base64.b64decode(v) for k,v in json.loads(r)])) for r in d['tables'][t]]
journalfacts=[]
for i,leaf in enumerate(s['ordered_cases']):
 req=read(E/f'case-{i:02d}.request.json');F=Path(req['environment']['RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR'])/('TestCLIProtocolInteractiveAuthority_'+leaf);d=read(F/'db-closed-copy.rows.json');js=typed(d,'idempotency');ids=typed(d,'client_command_identities');rq=read(F/'requests.exact.json');rp=read(F/'responses.base64.json')
 for q,p in zip(rq,rp):
  if q['bytes']==0:continue
  env=json.loads(base64.b64decode(q['raw_base64']));jr=[x for x in js if x['key']==env['command_id'] and x['operation']=='v2:'+env['method']];ir=[x for x in ids if x['command_id']==env['command_id']];wire=base64.b64decode(p)
  ck('sole journal status0 plus exact LF framing '+env['command_id'],len(jr)==len(ir)==1 and jr[0]['status']==0 and jr[0]['body'].encode()+b'\n'==wire and jr[0]['request_hash']==ir[0]['request_hash'] and jr[0]['project']==ir[0]['project']==env['project_id'] and ir[0]['method']==env['method'])
  journalfacts.append({'leaf':leaf,'method':env['method'],'command_id':env['command_id'],'journal_internal_status':jr[0]['status'],'wire_http_status':200,'wire_equals_original_journal_body_plus_exact_LF':jr[0]['body'].encode()+b'\n'==wire,'request_hash':jr[0]['request_hash']})
 expected=[closure['test2json']['path'],'-t','-p','researchos.local/research-os/apps/cli',closure['testexe']['path'],'-test.v','-test.count=1','-test.timeout=480s','-test.failfast','-test.run','^TestCLIProtocolInteractiveAuthority$/^'+leaf+'$']
 ck('exact direct test2json argv '+leaf,req['argv']==expected and req['environment']['RESEARCHOS_CLI_PROTOCOL_BINARY']==closure['cli']['path'])
cat=read(verify(s['catalog_ref']));plan=read(verify(s['instrumentation_ref']));inst=read(E/'instrumentation.actual.json');original=R/plan['original_path'];raw=verify(inst['export_test']).read_text(encoding='utf-8')
for old,new in reversed(plan['exact_scoped_inline_edits']):
 ck('inline inverse anchor exact',raw.count(new)==1);raw=raw.replace(new,old,1)
for change in reversed(plan['changes']):
 ck('wholeblock inverse anchor exact',raw.count(change['new'])==1);raw=raw.replace(change['new'],change['old'],1)
ck('instrumentation complete inverse original bytes',raw.encode()==original.read_bytes() and ref(original)['sha256']==plan['original_sha256'])
ck('catalog actual source commit/count',cat['commit']==s['source_commit'] and len(cat['files'])==cat['file_count']==597)
for row in cat['files']:
 original=R/row['path'];current=ref(original);ck('Main source current '+row['path'],current['sha256']==row['sha256'] and current['bytes']==row['bytes']);export=ref(X/row['path']);expected=inst['export_test'] if row['path']==plan['original_path'] else row
 ck('export current source '+row['path'],export['sha256']==expected['sha256'] and export['bytes']==expected['bytes'])
pre=read(verify(g['prelaunch_evidence_ref']));facts=[]
for step in pre['git']:
 verify(step['stdout_ref']);verify(step['stderr_ref']);ck('prelaunch ownedGit '+step['kind'],job(step['result']) and step['wrapper_error'] is None)
 body=path(step['stdout_ref']['path']).read_bytes();facts.append({'kind':step['kind'],'stdout_ref':step['stdout_ref']})
 if step['kind']=='head':ck('prelaunch HEAD',body.decode().strip()==s['source_commit'])
 if step['kind']=='status':ck('prelaunch exact tracked status',hashlib.sha256(body).hexdigest()==s['main_git']['status_sha256'] and len(body)==894 and len(body.splitlines())==13 and sum(x[:2].strip()==b'D' for x in body.splitlines())==11)
 if step['kind']=='index':ck('prelaunch index empty',body==b'')
for row in g['canonical_copies']:ck('live canonical unchanged '+row['canonical_path'],verify(row['ref']).read_bytes()==(R/row['canonical_path']).read_bytes())
# Current direct index bytes are proof only of no reviewer mutation, not a new Git diff invocation.
index_ref=ref(R/'.git/index')
for f in ['build-cli','build-test','build-test2json']:
 q=read(E/(f+'.request.json'));ck('build concurrency and vcs '+f,'-p=1' in q['argv'] and '-buildvcs=false' in q['argv']);ck('compiler network off '+f,q['environment']['GOPROXY']==q['environment']['GOSUMDB']=='off' and q['environment']['GOTOOLCHAIN']=='local')
Ldone=read(L/'completed.json');ck('launcher complete without acceptance',Ldone['actual_outer_tool_exit'] is None and Ldone['actual_inner_native_exit']==0 and Ldone['program_reported_exit']==0 and Ldone['first_cause'] is None and Ldone['secondary']==[] and Ldone['source_acceptance'] is False and Ldone['formal_increment']==0)
for f in sorted(E.glob('buildinfo-*.stdout.raw')):ck('actual buildinfo nonempty '+f.name,len(f.read_bytes())>0);ref(f)
out={'checks':checks,'failed_checks':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'journal_facts':journalfacts,'prior_audit_ref':ref(O/'audit.json'),'prior_audit_false_positive_correction':{'count':9,'old_predicate':'journal status==200','actual_producer':'client_protocol.go INSERT status0; writeJSON Encode adds one LF','prior_audit_native_exit':0,'new_product_failure':False},'current_source_files_hashed':597,'source_export_files_hashed':597,'actual_prelaunch_git_refs':facts,'current_index_bytes_ref':index_ref,'current_status_fresh_Git_executed_by_reviewer':False,'new_target_executions':0}
save('supplement.json',out);print(json.dumps({'checks':len(checks),'failed_checks':out['failed_checks'],'ref':ref(O/'supplement.json')},ensure_ascii=False))
