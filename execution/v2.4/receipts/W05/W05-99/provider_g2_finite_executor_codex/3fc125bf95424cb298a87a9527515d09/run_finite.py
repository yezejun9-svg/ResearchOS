from pathlib import Path
import os, sys, json, hashlib, subprocess, datetime, uuid, re
N=Path(__file__).resolve().parent
B=Path(sys.argv[1]).resolve()
W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
CASE_CWD=W/'internal/domain'
R=N/('run-'+uuid.uuid4().hex);R.mkdir()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def ref(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
build=json.loads((B/'build-result.json').read_text(encoding='utf-8'))
assert build['status']=='COMPILED_NOT_EXECUTED'
exe=Path(build['test_exe']['path']);assert sha(exe)==build['test_exe']['sha256']
env=json.loads((B/'test-build.invocation.json').read_text(encoding='utf-8'))['environment_allowlist']
plan=json.loads((N/'runner_proposal_ref.json').read_text(encoding='utf-8'))['execution_order']
assert len(plan)==29
start_at=int(sys.argv[2]) if len(sys.argv)>2 else 0
assert 0<=start_at<len(plan)
generated='\n'.join(p.read_text(encoding='utf-8') for p in (B/'compiler-generated').rglob('_testmain.go'))
for s in plan:assert s.split('$/')[0][1:] in generated
inputs=json.loads((B/'inputs.before.json').read_text(encoding='utf-8'))
archives=json.loads((B/'archives.before.json').read_text(encoding='utf-8'))
tracked=inputs+archives+[{'path':str(exe),'sha256':sha(exe)}]
def check(label):
 observed=[];bad=[]
 for x in tracked:
  p=Path(x['path']);h=sha(p) if p.is_file() else None
  observed.append({'path':str(p),'sha256':h})
  if h!=x['sha256']:bad.append({'path':str(p),'expected':x['sha256'],'actual':h})
 save(R/(label+'.json'),{'count':len(observed),'observed':observed,'drift':bad})
 if bad:raise RuntimeError('Immutable input drift '+label)
save(R/'inventory.before.json',{'plan':plan,'start_index':start_at,'generated_testmain_refs':[ref(p) for p in (B/'compiler-generated').rglob('_testmain.go')],'exe':ref(exe),'runner':ref(Path(__file__)),'status':'FROZEN_BEFORE_CASES'})
print('RUN',R,flush=True)
check('inputs.before')
results=[];model_calls=0
for i,s in enumerate(plan):
 if i<start_at:continue
 if i==18:check('component.after.native.before')
 leaf=s.replace('^','').replace('$','');C=R/(f'{i+1:02d}-'+leaf.replace('/','_'));C.mkdir()
 evidence=C/'evidence';evidence.mkdir()
 actualenv=dict(env,RESEARCHOS_PROVIDER_EVIDENCE_DIR=str(evidence))
 argv=[str(exe),'-test.v','-test.count=1','-test.timeout=150s','-test.failfast','-test.run='+s]
 source=[ref(W/x) for x in ['internal/domain/runtime_provider_binding_windows_test.go','internal/domain/runtime_coordinator_windows_test.go']]
 save(C/'inputs.before.json',{'source':source,'exe':ref(exe),'bundle':ref(Path(env['RESEARCHOS_MU_BUNDLE']))})
 started=now()
 with (C/'stdout').open('wb') as out,(C/'stderr').open('wb') as err:
  p=subprocess.Popen(argv,cwd=CASE_CWD,env=actualenv,stdout=out,stderr=err)
  try:code=p.wait(timeout=180);timed=False
  except subprocess.TimeoutExpired:
   timed=True
   if p.poll() is None:subprocess.run(['C:/Windows/System32/taskkill.exe','/PID',str(p.pid),'/T','/F'],stdout=err,stderr=err)
   code=p.wait()
 save(C/'invocation.json',{'argv':argv,'cwd':str(CASE_CWD),'environment_allowlist':actualenv,'started_at':started,'ended_at':now(),'pid':p.pid,'exit_code':code,'timeout':timed})
 raw=(C/'stdout').read_text(encoding='utf-8',errors='replace')
 passes=re.findall(r'^\s*--- PASS: (\S+)',raw,re.M)
 leaves=[x for x in passes if '/' in x]
 failures=re.findall(r'^\s*--- FAIL: (\S+)',raw,re.M)
 skipped=re.findall(r'^\s*--- SKIP: (\S+)',raw,re.M)
 calls=len(list(evidence.rglob('http-*.json')));model_calls+=calls
 after={'source':[ref(W/x) for x in ['internal/domain/runtime_provider_binding_windows_test.go','internal/domain/runtime_coordinator_windows_test.go']],'exe':ref(exe),'bundle':ref(Path(env['RESEARCHOS_MU_BUNDLE']))}
 save(C/'inputs.after.json',after)
 before=json.loads((C/'inputs.before.json').read_text(encoding='utf-8'))
 expected_calls=1 if i>=25 else 0
 valid=code==0 and leaves==[leaf] and not failures and not skipped and before==after and calls==expected_calls and model_calls<=4
 result={'index':i,'selector':s,'leaf':leaf,'exit_code':code,'pass_leaves':leaves,'failure_events':failures,'skip_events':skipped,'model_fixture_http':calls,'model_fixture_http_total':model_calls,'external_paid':0,'status':'PASS' if valid else 'FIRST_UNEXPECTED_STOP','invocation':ref(C/'invocation.json'),'raw_stdout':ref(C/'stdout'),'raw_stderr':ref(C/'stderr'),'evidence':[ref(p) for p in evidence.rglob('*') if p.is_file()]}
 save(C/'result.json',result);results.append(result)
 print(i+1,leaf,result['status'],code,'MODEL',calls,flush=True)
 save(R/'progress.json',results)
 if not valid:break
check('inputs.after')
save(R/'handoff.json',{'status':'FINITE_EXECUTION_REPORTED_NOT_ACCEPTED','build':ref(B/'build-result.json'),'results':results,'not_run':[s for j,s in enumerate(plan) if j>=start_at and j not in [x['index'] for x in results]],'earlier_indices_not_in_this_cohort':list(range(start_at)),'model_fixture_calls':model_calls,'external_paid_calls':0,'source_writer_acceptance':False})
print('FINISHED',R,flush=True)
sys.exit(0 if all(x['status']=='PASS' for x in results) else 1)
