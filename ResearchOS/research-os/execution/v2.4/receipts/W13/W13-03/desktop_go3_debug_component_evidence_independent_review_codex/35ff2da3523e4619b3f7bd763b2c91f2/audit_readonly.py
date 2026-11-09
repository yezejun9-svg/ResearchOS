import ast, collections, concurrent.futures, hashlib, json, os, re, time
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
H=Path(__file__).resolve().parent
N=R/'execution/v2.4/receipts/W13/W13-03/desktop_go3_os_capture_revision_codex/01fc890602df43b89935fdbef4424137'
O=N/'actual-once'
M=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/root-continuation-after320'
G=R/'execution/v2.4/receipts/W13/W13-03/desktop_go3_root_once_authorization_codex/5b5e8bafa4fc41f18ccb058193b490d0/grant.json'
checks=[];readrefs={};tohash={}
def norm(p):
 p=str(p)
 if p.startswith('\\\\?\\'):p=p[4:]
 p=Path(p);p=p if p.is_absolute() else R/p
 return os.path.normcase(str(p.absolute()))
def read(p):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();readrefs[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def load(p):return json.loads(read(p))
def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
def save(name,x):
 with (H/name).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def add(ref):
 k=norm(ref['path']);v=(ref['sha256'],ref['bytes'])
 if k in tohash:check('same_path_expected_hash_consistent',v==(tohash[k]['sha256'],tohash[k]['bytes']),ref['path'])
 else:tohash[k]={'path':str(Path(k)),'sha256':v[0],'bytes':v[1]}
def walk(x):
 if isinstance(x,dict):
  if {'path','sha256','bytes'}<=x.keys():yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def mapping(rows):
 out={norm(x['path']):(x['sha256'],x['bytes']) for x in rows}
 check('unique_vector_paths',len(out)==len(rows),len(rows));return out
def subset(a,b):return all(b.get(k)==v for k,v in a.items())
started=time.time()
try:
 pins=[(M/'handoff.json','a5df55ccb16015ec37b3ef9f33e79a5b9360fe745ec486f15cd795f411e87a95'),(M/'manifest.json','175c020bee79da6350c50c3554e759fb75e6f3169fb75b26ef91fdffde0b4c1b'),(M/'audit.json','16562b88cade459e8185b09a5827a7cb49634a9690ae6b764876742da377cf0b'),(G,'0b0b7230ff78213178c6fa82e5b324d682644d0470459014feedd227cde89956'),(N/'spec.v2.json','858463e5dd1f5570c372de42476c65042d5e3d675085317711fe377323a4db76')]
 for p,sha in pins:check('fixed_pin_'+p.name,hashlib.sha256(read(p)).hexdigest()==sha)
 spec=load(N/'spec.v2.json');grant=load(G)
 for obj in [spec,grant,load(M/'audit.json'),load(M/'handoff.json')]:
  for x in walk(obj):add(x)
 manifest_counts={}
 for p in [M/'manifest.json',O/'outer.manifest.json',O/'inner.manifest.json']:
  mf=load(p);entries=mf['entries'];manifest_counts[str(p)]=len(entries)
  for x in entries:add(x)
 save('manifest-rosters.json',manifest_counts)
 check('actual_root_authorization',grant['authorized'] is True and grant['issuer']=='codex:/root' and grant['actual_registration_completed'] is True and grant['registration']==[320,148,417] and grant['max_executions']==1 and len(grant['authority_refs'])==15)
 for field in ['source_commit','test_exe','selectors','caps','python_flags','new_output_root','runner_ref','debug_helper_ref','outer_helper_ref','python_ref','runtime_catalog_ref']:
  check('grant_exact_'+field,grant[field]==spec[field])
 check('pure_component_caps',all(spec['caps'][k]==0 for k in ['http','sdk_model','external','paid','source_edits','new_selectors']) and spec['caps']['test_processes']==spec['caps']['test_executions']==1)
 for field in ['runner_ref','debug_helper_ref','outer_helper_ref']:
  source=read(spec[field]['path']);ast.parse(source);check('actual_source_AST_'+field,hashlib.sha256(source).hexdigest()==spec[field]['sha256'])
 compiled=load(spec['input_vector_ref']['path']);cv=mapping(compiled)
 check('actual_8577_original_compiled',len(compiled)==8577)
 for x in compiled:add(x)
 catalog=load(spec['runtime_catalog_ref']['path']);catalogmap=mapping(catalog['files'])
 check('fixed_public_runtime_catalog1211',len(catalog['files'])==1211)
 # Full catalog is public static resource inventory, not all-loaded claim.
 for x in catalog['files']:add(x)
 approved=dict(catalogmap)
 for f in ['runner_ref','debug_helper_ref','outer_helper_ref']:
  x=spec[f];approved[norm(x['path'])]=(x['sha256'],x['bytes'])
 phases={};phasevectors={}
 for phase in ['outer','inner']:
  summary=load(O/(phase+'.summary.json'));inv=load(O/(phase+'.invocation.json'));owned=load(O/(phase+'.owned-result.json'));rr=owned['result'];job=rr['job_cleanup']
  check(phase+'_completed_native0',summary['status']=='COMPONENT_EVIDENCE_RECORDED' and summary['first_failure'] is None and summary['diagnostics']==[] and summary['actual_native_exit']==owned['actual_native_exit']==rr['actual_exit']==0 and rr['error'] is None and rr['timed_out'] is False and rr['resumed'] is True)
  check(phase+'_Job_complete',all(job[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and job['errors']==[] and job['active_processes_last_observed']==0 and job['termination_requested'] is False)
  check(phase+'_closed_raw_files',owned['stdout_closed'] is True and owned['stderr_closed'] is True and owned['stdio']=='EXPLICIT_FILE_HANDLES_NOT_PIPES' and (O/(phase+'.stdout.raw')).is_file() and (O/(phase+'.stderr.raw')).is_file())
  check(phase+'_invocation_preexecution_exit_preserved',inv['actual_exit'] is None and inv['result_record']==phase+'.owned-result.json' and inv['cwd']==spec['cwd'])
  before=load(O/(phase+'.inputs.before.json'));after=load(O/(phase+'.inputs.after.json'));bm=mapping(before)
  check(phase+'_compiled_subset_frozen',subset(cv,bm))
  check(phase+'_after_all_match',all(x['match'] is True and x['error'] is None and x['actual']==x['expected'] for x in after) and mapping([x['expected'] for x in after])==bm)
  for x in before:add(x)
  runtime=[]
  for stage in ['before','after']:
   rt=load(O/(phase+'.runtime.'+stage+'.json'));rm=mapping(rt['files']);runtime.append(rm)
   check(phase+'_runtime_'+stage+'_explicit_pointtime',rt['measurement']=='POINT_IN_TIME_NOT_LIFECYCLE' and rt['transient_load_absence_proven'] is False and subset(rm,approved) and subset(rm,bm))
   check(phase+'_runtime_'+stage+'_no_site',not any('site-packages' in k for k in rm))
  check(phase+'_runtime_no_new_paths_or_drift',runtime[0]==runtime[1])
  phasevectors[phase]=bm
  phases[phase]={'inputs':len(before),'runtime_observed':len(runtime[0]),'actual_native_exit':rr['actual_exit'],'pid':rr['owned_child_pid'],'creation_time_100ns':rr['creation_time_100ns'],'elapsed_seconds':rr['elapsed_seconds']}
  if phase=='outer':
   check('actual_inner_controller_argv',inv['argv'][1:5]==['-I','-S','-X','utf8'] and '--inner' in inv['argv'] and inv['argv'][-2:] == ['--grant-sha256','0b0b7230ff78213178c6fa82e5b324d682644d0470459014feedd227cde89956'] and inv['timeout_seconds']==600)
  else:
   check('actual_Go_exact_argv',inv['argv']==[spec['test_exe']['path'],'-test.run',spec['anchored_selector'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s'] and inv['timeout_seconds']==150)
   debug=rr['debug_capture'];events=debug['events'];mods=debug['modules'];pid=rr['owned_child_pid']
   check('debug_primary_unique_complete',debug['complete'] is True and debug['mode']=='CREATE_OWN_CHILD_DEBUG_ONLY_THIS_PROCESS' and debug['create_process_count']==debug['exit_process_count']==debug['initial_breakpoint_count']==debug['total_processes_last_observed']==1 and debug['exit_event_code']==rr['actual_exit']==0)
   check('debug_actual_event_causal_order',events[0]['code']==3 and events[-1]['code']==5 and sum(x['code']==3 for x in events)==sum(x['code']==5 for x in events)==1 and all(x['pid']==pid and x['code'] in range(1,9) and not x.get('capture_omitted_during_failure_cleanup',False) for x in events) and events[-1]['actual_exit_event_code']==0)
   exceptions=[x for x in events if x['code']==1]
   check('only_explicit_loader_breakpoint',len(exceptions)==1 and exceptions[0]['initial_breakpoint'] is True and exceptions[0]['exception_code']==0x80000003 and exceptions[0]['first_chance']==1 and exceptions[0]['tid']==events[0]['tid'])
   check('debug_events_modules_within_bounds',len(events)<=4096 and len(mods)==10==sum(x['code'] in [3,6] for x in events) and len(mods)<=256 and sum(x['before']['bytes'] for x in mods)<=1024*1024*1024)
   for index,m in enumerate(mods):
    check('module_'+str(index)+'_held_handle_before_after',m['before']==m['after'] and 0<m['before']['bytes']<=256*1024*1024)
    p=norm(m['path_from_actual_file_handle']);ref={'path':p,**m['before']};add(ref)
    check('module_'+str(index)+'_actual_image_or_catalog', (p==norm(spec['test_exe']['path']) and m['event_code']==3 and m['before']=={'sha256':spec['test_exe']['sha256'],'bytes':spec['test_exe']['bytes']}) if index==0 else m['event_code']==6 and catalogmap.get(p)==(m['before']['sha256'],m['before']['bytes']))
   phases['debug']={'events':len(events),'module_records':len(mods),'create':1,'exit':1,'TotalProcesses':1,'module_paths':[x['path_from_actual_file_handle'] for x in mods],'failure_injection_test_executed':False}
 check('outer_inner_exact_frozen_vector',phasevectors['outer']==phasevectors['inner'])
 stdout=read(O/'inner.stdout.raw');text=stdout.decode('utf-8');passes=re.findall(r'^\s*--- PASS: ([^ ]+)',text,re.M);fail_or_skip=re.findall(r'^\s*--- (?:FAIL|SKIP): ([^ ]+)',text,re.M);record=load(O/'inner.test-events.json')
 check('actual_raw64_exact_spec_and_aggregate',collections.Counter(passes)==collections.Counter(spec['expected_pass_records']) and len(passes)==64 and not fail_or_skip and record['passes']==passes and record['failure_or_skip']==[] and record['stdout_sha256']==hashlib.sha256(stdout).hexdigest() and text.rstrip().endswith('PASS'))
 tops=[x for x in passes if '/' not in x];leaves=[x for x in passes if not any(y.startswith(x+'/') for y in passes)]
 check('actual3top63leaf',set(tops)==set(spec['selectors']) and len(tops)==3 and len(leaves)==63)
 save('actual-case-and-process-summary.json',{'phases':phases,'PASS_records':passes,'top_functions':tops,'leaf_count':len(leaves),'failure_or_skip':fail_or_skip})
 for f in [M/'go3.outer-tool-completion.json',M/'record.py']:
  read(f)
 def hashone(x):
  try:
   h=hashlib.sha256();size=0
   with Path(x['path']).open('rb') as f:
    while b:=f.read(4*1024*1024):size+=len(b);h.update(b)
   return {'path':x['path'],'sha256':h.hexdigest(),'bytes':size,'match':size==x['bytes'] and h.hexdigest()==x['sha256']}
  except OSError as e:return {'path':x['path'],'match':False,'error':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:current=list(pool.map(hashone,tohash.values()))
 save('current-content-hash-audit.json',current)
 check('all_manifest_authority_compiled_runtime_current',all(x['match'] for x in current),{'unique_paths':len(current),'mismatches':[x for x in current if not x['match']]})
 print(json.dumps({'checks':len(checks),'hashed_paths':len(current),'failed':[x for x in checks if not x['passed']]},ensure_ascii=False))
except Exception as e:
 save('audit.exception.json',{'type':type(e).__name__,'message':str(e),'product_executions':0});raise
finally:
 save('read-refs.json',list(readrefs.values()));save('checks.json',checks);save('audit-summary.json',{'checks':len(checks),'failed':[x for x in checks if not x['passed']],'elapsed_seconds':time.time()-started,'product_executions':0,'SQL_connections':0,'reviewed_controller_imports':0})
