import hashlib,json,os,subprocess,datetime,traceback
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler38-post-integration-r322'
PRE=S.parent/'fresh-handler38-source-integration-r321-v2'
OLD=R/'execution/v2.4/receipts/W05/W05-99/root_registration_r322_readonly_review_codex/bc313de20bda4233bcb5001d0d9815a8'
L=R/'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_root_launcher_codex/9f028224a18f4d0fb49f854014ace6d0'
checks=[];reads={};queries=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check(n,v):checks.append({'check':n,'pass':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();x={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 if str(p) in reads:check('same-read:'+str(p),reads[str(p)]==x)
 reads[str(p)]=x;return b
def ref(p):read(p);d=reads[str(path(p))].copy();d['path']=path(p).relative_to(R).as_posix();return d
def verify(x):
 b=read(x['path']);check('ref:'+x['path'],hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']);return b
def doc(p):return json.loads(read(p))
def save(n,d):
 with (O/n).open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(O/n)
def job(n,x):
 j=x['job_cleanup'];check(n,x['actual_exit']==0 and x['error'] is None and x['timed_out'] is False and x['resumed'] is True and x['owned_child_pid']>0 and x['creation_time_100ns']>0 and j['errors']==[] and all(j[k] is True for k in ['unnamed_exclusive_job','assigned_before_resume','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']))
try:
 audit_ref=ref(S/'registration-audit.json');check('post-audit-pin',audit_ref['sha256']=='d3bd87694dc7e61a3601e2bb4db77e2cb48356e90690458eac3adea4e64b1383')
 a=doc(S/'registration-audit.json');check('post-audit-schema',a['schema']=='researchos.main38-post-integration-registration-audit.v1' and a['actual_registration_exit']==0 and a['after']==[322,150,425])
 mf=doc(S/'manifest.json');check('post-manifest-pin',ref(S/'manifest.json')['sha256']=='8cfbec158ee1add86a4b6efc1042938268aa9b4987340ab95c48a5b8f2e9fd73');check('post-mf-count',mf['count']==len(mf['entries']))
 for x in mf['entries']:verify(x)
 p=doc(S/'prepared_refs.json');oldreview=doc(OLD/'review.json');check('reuse-reviewed1536',ref(OLD/'review.json')['sha256']=='b4eaf34a8fda33998cf50f31fc38c1a0a88e6510f73563aa555cfff625178b5f' and oldreview['evidence']['checks_passed']==1536)
 verify(oldreview['evidence']['checks_ref']);verify(oldreview['evidence']['reads_ref'])
 check('original-relative-dictionaries',a['completed_ref']==p['pins']['main38_completed'] and a['manifest_ref']==p['pins']['main38_manifest'])
 completed=json.loads(verify(a['completed_ref']));em=json.loads(verify(a['manifest_ref']));E=path(a['completed_ref']['path']).parent
 check('source-only-done',completed['actual_head']==a['registered_head']=='a5d6d16ffaf129de0361470c3a1570228bd259a2' and completed['unique_paths']==38 and completed['merge_attempts']==1 and completed['formal_increment']==0 and completed['whole_W05_acceptance'] is False)
 check('executor-179',em['count']==len(em['entries'])==179)
 invrows=[x for x in em['entries'] if x['path'].endswith('.invocation.json')];check('saved56',len(invrows)==56)
 for x in invrows:
  d=json.loads(verify(x));job('git-owned:'+Path(x['path']).name,d['process_observation']);check('git-wrapper:'+Path(x['path']).name,d['actual_native_exit']==0 and d['wrapper_error'] is None and d['automatic_retry'] is False)
  verify(d['stdout_ref']);verify(d['stderr_ref'])
 ff=doc(E/'fast-forward.invocation.json');check('once-exact-FF',ff['argv'][-5:]==['merge','--ff-only','--no-autostash','--no-edit',a['registered_head']])
 lm=doc(L/'manifest.json')
 for x in lm['entries']:verify(x)
 check('launcher-no-failure',lm['first_failure'] is None)
 for n in ['grant-preflight','source-only-integration']:
  z=doc(L/(n+'.owned-result.json'));job('python-owned:'+n,z['result']);check('python-wrapper:'+n,z['actual_native_exit']==0 and z['wrapper_error'] is None)
  d=doc(L/(n+'.invocation.json'));check('python-sanitized-flags:'+n,d['argv'][1:5]==['-I','-S','-X','utf8'])
  read(L/(n+'.stdout.raw'));read(L/(n+'.stderr.raw'))
 outer=json.loads(verify(p['pins']['main38_outer_completion']));check('outer-observation',outer['initial_tool_chunk']=='c822f3' and outer['actual_tool_session']==65537 and outer['completion_tool_chunk']=='eab84b' and outer['actual_outer_exit']==0 and outer['actual_root_launcher_native_exit_separately_observed'] is None and outer['this_record_is_not_original_native_stdout_or_stderr'] is True)
 grant=json.loads(verify(completed['grant_ref']));check('actual-grant321',grant['actual_registration_completed'] is True and grant['operation_uuid']==E.name and grant['automatic_retry'] is False)
 for item in grant['canonical_copies']:
  b=verify(item['ref']);n=Path(item['canonical_path']).stem;check('321-grant-original-in322:'+n,b==read(S/(n+'.original.json')))
 for k in ['manifest','audit','invocation','intent','verified']:verify(grant['registration_refs'][k])
 ga=json.loads(verify(grant['registration_refs']['audit']));check('actual321beforeFF',ga['actual_registration_exit']==0 and ga['after']==[321,149,422])
 rootinv=json.loads(verify(a['invocation_ref']));intent=json.loads(verify(a['intent_ref']));verified=json.loads(verify(a['verified_ref']));rr=json.loads(verify(rootinv['review_ref']))
 check('actual-post322-invocation',rootinv['actual_exit']==0 and rootinv['automatic_retry'] is False and rootinv['counter_reset'] is False and rr['decision']=='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION')
 for field,n in [('register_sha256','register.py'),('wrapper_sha256','run.py'),('prepared_refs_sha256','prepared_refs.json'),('audit_sha256','audit.json')]:check('actual-reviewed:'+n,rr[field]==ref(S/n)['sha256'])
 for stream in ['stdout','stderr']:check('actual-registration-raw:'+stream,rootinv[stream+'_sha256']==ref(S/(stream+'.raw'))['sha256'])
 docs=[];originaldocs=[]
 for n in ['checkpoint','path_ownership','step_state','commands']:
  current=read(R/'execution/v2.4'/f'{n}.json');original=read(S/(n+'.original.json'));expected=read(S/(n+('.desired.json' if n in ['checkpoint','path_ownership'] else '.original.json')))
  check('current322-byte:'+n,current==expected);docs.append(json.loads(current));originaldocs.append(json.loads(original))
  with (O/(n+'.current322.json')).open('xb') as f:f.write(current)
 cp,ow=docs[:2];beforecp=originaldocs[0]
 check('tuple322150425',[cp['revision'],ow['revision'],len(cp['failure_counters'])]==[322,150,425])
 check('422-prefix',cp['failure_counters'][:422]==beforecp['failure_counters'])
 check('head-forward',beforecp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079' and cp['head']==a['registered_head'])
 check('formal-unchanged',cp['current_effective_formal_status']==beforecp['current_effective_formal_status'])
 for got,expected in zip(cp['failure_counters'][422:],p['origins']):check('3-origins-preserved:'+got['origin_key'],all(got[k]==v for k,v in expected.items()))
 for x in intent['metadata']:
  verify(x['original_ref']);verify(x['desired_ref']);d=doc(S/('canonical-write.'+Path(x['path']).stem+'.done.json'));check('commit-done:'+x['path'],d['sha256']==x['desired_ref']['sha256'])
 check('verified-actual-tuple',[verified['checkpoint'],verified['ownership'],verified['failure_origins']]==[322,150,425] and verified['intent_ref']==a['intent_ref'])
 check('no-fresh-validation-grant',cp['work_in_progress']['handler38_fresh_combined_validation_authorized'] is False and ow['card_path_bindings']['W05-99']['subtasks']['handler38_main_source_integration']['current_source_writer'] is None)
 rows=doc(E/'source.after.json');check('38-current-count',len(rows)==38)
 for x in rows:verify(x)
 check('protected-vector-original-equal',read(E/'protected.before.json')==read(E/'protected.after.json'))
 for n in ['runtime.before.json','runtime.precommit.json','runtime.after.json']:doc(E/n)
 for n in ['runtime.before.json','runtime.after.json']:
  z=doc(L/n);check('pointtime-only:'+n,z['measurement']=='POINT_IN_TIME_NOT_LIFECYCLE' and z['transient_load_absence_proven'] is False)
 lock=doc(R/'execution/toolchains/locked.json')['tools'];git=lock['git']['path'];check('locked-Git-current',hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['git']['sha256'])
 env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']};env.update(PATH='C:/Windows/System32;C:/Windows',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0')
 prefix=[git,'--no-optional-locks','-c','core.fsmonitor=false','-c','core.untrackedCache=false']
 for name,args,expected in [('head',['rev-parse','HEAD'],(a['registered_head']+'\n').encode()),('status',['status','--porcelain=v1','--untracked-files=no'],read(E/'after-status.stdout.raw')),('index',['diff','--cached','--name-only'],b'')]:
  argv=prefix+args;start=now();result=None;error=None
  try:
   with (O/(name+'.stdout.raw')).open('xb') as so,(O/(name+'.stderr.raw')).open('xb') as se:result=subprocess.run(argv,cwd=R,env=env,stdout=so,stderr=se,timeout=60)
  except BaseException as exc:error=repr(exc);raise
  finally:
   inv={'argv':argv,'cwd':str(R),'environment':env,'started_at':start,'ended_at':now(),'actual_exit':None if result is None else result.returncode,'error':error,'scope':'BOUNDED_READONLY_GIT_QUERY','optional_locks':False,'stdout_ref':ref(O/(name+'.stdout.raw')) if (O/(name+'.stdout.raw')).exists() else None,'stderr_ref':ref(O/(name+'.stderr.raw')) if (O/(name+'.stderr.raw')).exists() else None};queries.append(inv);save(name+'.invocation.json',inv)
  if result.returncode!=0:raise RuntimeError('Readonly Git failed: '+name)
  check('fresh-'+name,read(O/(name+'.stdout.raw'))==expected)
 status=read(O/'status.stdout.raw');check('13status11D',len(status.splitlines())==13 and sum(x[:2]==b' D' for x in status.splitlines())==11)
 for n in ['checkpoint','path_ownership','step_state','commands']:check('canonical-stable-after-query:'+n,read(R/'execution/v2.4'/f'{n}.json')==read(O/(n+'.current322.json')))
except BaseException as exc:
 save('failure.origin.json',{'error':repr(exc),'traceback':traceback.format_exc(),'actual_product_exit':None,'readonly_queries':queries,'no_retry':True});raise
finally:
 save('checks.json',{'checks':checks,'failed':[x for x in checks if not x['pass']],'queries':queries,'product_executions':0})
 save('reads.json',list(reads.values()))
print(json.dumps({'checks':len(checks),'failed':sum(not x['pass'] for x in checks),'read_files':len(reads),'readonly_git_exits':[x['actual_exit'] for x in queries]},ensure_ascii=True))
