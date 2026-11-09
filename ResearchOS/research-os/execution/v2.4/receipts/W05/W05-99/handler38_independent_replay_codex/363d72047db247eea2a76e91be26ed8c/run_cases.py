import json,os,subprocess,sys,hashlib,datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/independent-handler38-a639cfcf';N=Path(__file__).resolve().parent;P=R/'execution/v2.4/receipts/W05/W05-99/handler38_final_source_review_codex/a639cfcf998f4c7fb182db19c6788c3b/execution_plan.json';plan=json.loads(P.read_bytes());env=os.environ.copy();env.update(json.loads((N/'environment.json').read_bytes()));G=env['RESEARCHOS_GO'];lock=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(p,o):p.write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
inputs=json.loads((N/'source.before.json').read_bytes());assert inputs==json.loads((N/'source.after_compile.json').read_bytes());assert json.loads((N/'compile_result.json').read_bytes())['exit']==0
inputs[str(Path(__file__).resolve())]=sha(Path(__file__).resolve());inputs[str(P)]=sha(P)
for x in json.loads((N/'executables.before_cases.json').read_bytes()):inputs[x['path']]=x['sha256']
def vector():return {p:sha(Path(p)) for p in sorted(inputs)}
current=vector();save(N/'source.before_cases.json',current);assert current==inputs
save(N/'AE_execution_spec.json',{'batches':plan['batches'],'failfast':True,'candidate':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','C09_in_this_cohort':False,'source_qualification':False,'Root_scope':'456a3a93e9e0d458206af572038cf530a7eefcab332ab484444b68620e8e5fff'})
inputs[str(N/'AE_execution_spec.json')]=sha(N/'AE_execution_spec.json');save(N/'source.before_first_case.json',inputs)
results=[]
for batch in plan['batches']:
 name=batch['id'];out=N/'batches'/name;out.mkdir(parents=True,exist_ok=False);ev=out/'public-fixtures';ev.mkdir();runenv=env.copy();runenv['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']=str(ev)
 for key in list(runenv):
  if key.upper() in ['OPENAI_API_KEY','ANTHROPIC_API_KEY','AZURE_OPENAI_API_KEY']:runenv.pop(key,None)
 package=batch['package'];short={'./internal/domain':'domain','./internal/api':'api','./internal/host':'host','./apps/cli':'cli'}[package];binary=N/(short+'.test.exe');argv=[G,'tool','test2json','-t','-p','researchos.local/research-os/'+package[2:],str(binary),'-test.v','-test.failfast','-test.timeout='+batch['test_timeout'],'-test.run='+batch['run_regex']];cwd=W/package[2:];start=now();save(out/'environment.json',{k:runenv[k] for k in json.loads((N/'environment.json').read_bytes())});print(json.dumps({'stage':'CASE_BATCH_START','batch':name,'binary_sha256':sha(binary),'time':start}),flush=True)
 with (out/'stdout.raw').open('xb') as stdout,(out/'stderr.raw').open('xb') as stderr:
  try:q=subprocess.run(argv,cwd=cwd,env=runenv,stdout=stdout,stderr=stderr,timeout=int(batch['outer_timeout'][:-1]));exitcode=q.returncode
  except subprocess.TimeoutExpired:exitcode=124
 save(out/'invocation.json',{'argv':argv,'cwd':str(cwd),'started_at':start,'ended_at':now(),'exit':exitcode,'binary_sha256':sha(binary),'fixture_only':True})
 events=[]
 for line in (out/'stdout.raw').read_bytes().splitlines():
  try:o=json.loads(line)
  except (ValueError,UnicodeDecodeError):continue
  if o.get('Test') and o.get('Action') in ['pass','fail','skip']:events.append(o)
 counts={k:sum(x['Action']==k for x in events) for k in ['pass','fail','skip']};tops={k:sum(x['Action']==k and '/' not in x['Test'] for x in events) for k in counts};res={'batch':name,'exit':exitcode,'test_events':counts,'top_events':tops,'source_cohort':'AE_NO_OVERLAY','binary_sha256':sha(binary),'closed_fixture_files':[{'path':str(p.relative_to(out)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(ev.rglob('*')) if p.is_file()]};save(out/'result.json',res);results.append(res);save(N/'AE.results.partial.json',results);print(json.dumps({'stage':'CASE_BATCH_FINISHED',**{k:res[k] for k in ['batch','exit','test_events','top_events']}}),flush=True)
 if exitcode or counts['fail'] or counts['skip'] or counts['pass']==0:
  after=vector();save(N/'source.after_stopped.json',after);save(N/'AE.stopped.json',{'batch':name,'result':res,'source_drift':after!=inputs,'remaining_batches':[b['id'] for b in plan['batches'] if b['id']>name],'C09':'NOT_RUN','retry':0});sys.exit(exitcode or 1)
after=vector();save(N/'source.after_AE.json',after);save(N/'AE.result.json',{'batches':results,'source_drift':after!=inputs,'inputs':len(inputs),'C09':'NOT_RUN_SEPARATE_COHORT','formal_increment':0});assert after==inputs;print(json.dumps({'stage':'AE_COMPLETE','batches':len(results),'inputs':len(inputs),'source_drift':False}),flush=True)
