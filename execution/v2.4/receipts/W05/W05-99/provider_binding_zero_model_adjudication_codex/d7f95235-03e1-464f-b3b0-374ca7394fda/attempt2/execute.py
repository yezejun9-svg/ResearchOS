from pathlib import Path
import os,json,subprocess,hashlib,datetime,sys,shutil
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).parent;L=json.loads((O/'locations.json').read_bytes());R=Path(L['root']);W=Path(L['worktree']);S=json.loads((O/'scope.original.json').read_bytes())
H=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'sha256':H(b),'bytes':len(b)}
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
binary=json.loads((O/'binary.freeze.json').read_bytes());assert ref(Path(binary['path']))['sha256']==binary['sha256']
inputs=json.loads((O/'inputs.before.json').read_bytes())
for n,e in inputs.items():assert ref(Path(n))==e
dbs=json.loads((O/'original_database_freeze.json').read_bytes())
for e in dbs.values():assert ref(Path(e['original_path']))=={'sha256':e['sha256'],'bytes':e['bytes']}
# PREPARED first is the predeclared highest-risk zero-observation case.
order=['1','2','3','4','5','0'];plan=[]
for i in order:
 for mode in ['baseline','missing_dispatch_and_transport','removed_profile_policy_and_transport','public_positive']:
  d=O/'cases'/(i+'-'+mode);d.mkdir(parents=True,exist_ok=False)
  c={'Database':str(d/'fixture.sqlite'),'Output':str(d),'Mode':mode,'ExpectedSHA':dbs[i]['sha256']}
  save(str((d/'case.json').relative_to(O)),c)
  plan.append({'database_id':i,'mode':mode,'case_file':str(d/'case.json'),'frozen_source':dbs[i]})
save('execution.plan.json',{'cases':plan,'max_internal':18,'max_public_positive':6,'extra_public_corruption':0,'model_calls':0,'automatic_retries':0,'stop_on_first_nonzero_or_unexpected_accept':True})
full=dict(inputs)
for p in [O/'execute.py',O/'binary.freeze.json',Path(binary['path']),O/'execution.plan.json',O/'dependency_recovery.json']+list((O/'cases').rglob('case.json'))+list((O/'frozen_originals').glob('*.sqlite')):full[str(p)]=ref(p)
save('before_first_case.freeze.json',full)
env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['TOKEN','SECRET','API_KEY','CREDENTIAL','RESEARCHOS_'])}
env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(R/'.local/tools/go1.27.1/go'),GOPATH=str(R/'.local/gopath'),GOCACHE=str(W/'.local/p12-gocache'),GOPROXY='off',GOSUMDB='off')
results=[]
for case in plan:
 c=json.loads(Path(case['case_file']).read_bytes());d=Path(c['Output']);shutil.copyfile(case['frozen_source']['copy'],c['Database']);assert ref(Path(c['Database']))['sha256']==c['ExpectedSHA']
 cmd=[binary['path'],'-test.v','-test.count=1','-test.timeout=60s','-test.run=^TestIndependentP12Offline$'];env['P12_CASE_FILE']=case['case_file'];start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (d/'stdout.raw').open('wb') as out,(d/'stderr.raw').open('wb') as err:
  proc=subprocess.Popen(cmd,cwd=W/'internal/domain',env=env,stdout=out,stderr=err)
  pid=proc.pid
  try:code=proc.wait(timeout=90)
  except subprocess.TimeoutExpired:
   proc.kill();code=proc.wait();(d/'outer_timeout.txt').write_text('Outer timeout; process killed; no retry',encoding='utf-8')
 info={'argv':cmd,'cwd':str(W/'internal/domain'),'pid':pid,'executable_sha256':binary['sha256'],'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':code,'environment_overrides':{'P12_CASE_FILE':case['case_file'],'GOENV':'off','GOPROXY':'off','GOSUMDB':'off'},'stdin':'not supplied','stdout':ref(d/'stdout.raw'),'stderr':ref(d/'stderr.raw'),'actual':ref(d/'actual.json') if (d/'actual.json').exists() else None}
 (d/'invocation.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');results.append({'case':case,'invocation':info})
 print(case['database_id'],case['mode'],code,flush=True)
 if code!=0:break
after={n:ref(Path(n)) for n in full};save('inputs.after_cases.json',after);drift=[n for n,e in full.items() if after[n]!=e]
original_drift=[e['original_path'] for e in dbs.values() if ref(Path(e['original_path']))!={'sha256':e['sha256'],'bytes':e['bytes']}]
save('execution.result.json',{'results':results,'executed_case_count':len(results),'planned_case_count':len(plan),'stopped_on_first_nonzero':bool(results and results[-1]['invocation']['exit']),'unexecuted_cases':plan[len(results):],'input_count':len(full),'input_drift':drift,'original_database_drift':original_drift,'worker_starts':0,'model_calls':0,'paid_calls':0,'history_counter_remains':5,'qualification_increment':0,'no_product_source_changes':True})
assert not drift and not original_drift
print(json.dumps({'cases':len(results),'stopped':bool(results and results[-1]['invocation']['exit']),'input_count':len(full),'drift':drift,'original_database_drift':original_drift}))
