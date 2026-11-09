import os,sys,json,hashlib,subprocess,datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/independent-handler38-a639cfcf';N=Path(__file__).resolve().parent
A=R/'execution/v2.4/receipts/W05/W05-99/handler38_independent_replay_codex/363d72047db247eea2a76e91be26ed8c'
L=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools'];G=Path(L['go']['path'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save(name,value):
 with (N/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
env=os.environ.copy();frozen_env=json.loads((A/'environment.json').read_bytes());frozen_env['RESEARCHOS_C09_ROOT']=str(N);frozen_env['RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']=str(N/'unused-model-evidence');env.update(frozen_env)
for key in list(env):
 if key.upper() in ['OPENAI_API_KEY','ANTHROPIC_API_KEY','AZURE_OPENAI_API_KEY']:env.pop(key,None)
save('environment.json',frozen_env)
def invoke(name,argv,cwd=W,timeout=600):
 st=now()
 with (N/(name+'.stdout.raw')).open('xb') as out,(N/(name+'.stderr.raw')).open('xb') as err:
  try:code=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout).returncode
  except subprocess.TimeoutExpired:code=124
 save(name+'.invocation.json',{'argv':argv,'cwd':str(cwd),'started_at':st,'ended_at':now(),'actual_exit':code})
 print(json.dumps({'stage':name,'actual_exit':code}),flush=True)
 return code
def stop(stage,code):
 save('stopped.json',{'stage':stage,'actual_exit':code,'automatic_retry':False,'source_writes':0,'external_HTTP':0,'models':0,'Node':0,'formal_increment':0});sys.exit(code or 1)
assert json.loads((A/'AE.result.json').read_bytes())['source_drift'] is False
for name in ['go','python','node','git']:assert sha(Path(L[name]['path']))==L[name]['sha256']
for row in json.loads((A/'source38.current.json').read_bytes()):assert sha(W/row['path'])==row['actual_sha256']
source=R/'.local/worktrees/codex-w0599-host-configuration-handler/execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/tls-runner-compiled-41b2091700e248b9a7e9f1b05ff5d727/run-82ea516f44c24025b35e6467fbf56c50/public-fixtures/TestHandlerTLSActualSDKConfiguredSession/handler-typed-tls-sdk.sqlite'
assert sha(source)=='16a69152e10889815d686f1d91387e3dfd4d0086d6fca6b109698b9b2b33a3d1'
names=['permission-resolved-positive','all-runs-settled-positive','permission-open','permission-acknowledged','older-run-unknown-hidden-by-later-settled-run','older-run-running-hidden-by-later-settled-run']
fixtures=[]
for name in names:
 folder=N/'cases'/name;folder.mkdir(parents=True,exist_ok=False);target=folder/'input.sqlite'
 with target.open('xb') as f:f.write(source.read_bytes())
 assert sha(target)==sha(source);fixtures.append({'case':name,'input':str(target),'sha256':sha(target),'original':str(source)})
save('fixtures.json',fixtures)
physical=N/'overlay/handler_configuration_independent_review_test.go';virtual=W/'internal/domain/handler_configuration_independent_review_test.go';assert not virtual.exists()
mapping=N/'overlay/overlay.json';save('overlay/overlay.json',{'Replace':{str(virtual):str(physical)}})
save('execution_spec.json',{'candidate':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','case_order':names,'selector':'^TestIndependentHandlerConfigurationC09$','scope_sha256':'2705297ee492cf72a6d01e70612fa45f05b9bcc6499abb159e0ec6f37d9fb02a','scope_original':str(N/'approved-originals/scope.json'),'AE_cohort_separate':str(A),'old_failed_cohort_preserved':str(N.parent/'c09-a0163b5c32ed44f7aca7730f3834e009'),'changes':['takeover writer_epoch=null','after_sequence actual nonnegative current watermark','exact raw persisted before Decode','strict ACK PendingResult/actual lease/journal/sole identity and exact ACK replay all-row equality'],'first_unexpected_stop':True,'C09_models_HTTP_Node_worker_paid':0,'formal_increment':0})
code=invoke('gofmt',[str(G.parent/'gofmt.exe'),'-w',str(physical)]); 
if code:stop('gofmt',code)
code=invoke('go-list',[str(G),'list','-overlay='+str(mapping),'-deps','-test','-compiled','-json','./internal/domain'])
if code:stop('go-list',code)
raw=(N/'go-list.stdout.raw').read_text(encoding='utf8');packages=[];dec=json.JSONDecoder()
while raw.strip():
 raw=raw.lstrip();obj,index=dec.raw_decode(raw);packages.append(obj);raw=raw[index:]
paths=set(Path(p) for p in json.loads((A/'source.before_first_case.json').read_bytes()))
for package in packages:
 if not package.get('Dir'):continue
 folder=Path(package['Dir']);paths.update(p for p in folder.glob('*.go') if p.is_file())
 for key in ['GoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','CgoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','CFiles','CXXFiles','SysoFiles']:
  for name in package.get(key,[]):
   p=Path(name) if Path(name).is_absolute() else folder/name
   if p==virtual:p=physical
   if not p.is_file():raise RuntimeError('missing actual compiler input '+str(p))
   paths.add(p)
 if package.get('Module',{}).get('GoMod'):paths.add(Path(package['Module']['GoMod']))
paths.update(p for p in (R/'third_party/mu').rglob('*') if p.is_file() and '.git' not in p.parts)
paths.update(p for p in (N/'approved-originals').rglob('*') if p.is_file());paths.update([N/'prepare_corrected.py',N/'overlay.pre-gofmt.diff',N/'preparation.json'])
paths.update([physical,mapping,N/'execution_spec.json',N/'fixtures.json',N/'environment.json',Path(__file__).resolve(),G.parent/'gofmt.exe',source]);paths.update(Path(row['input']) for row in fixtures)
paths=sorted(paths);save('input_paths.json',[{'path':str(p),'resolved':str(p.resolve())} for p in paths])
def vector():return {str(p):sha(p) for p in paths}
before=vector();save('source.before_compile.json',before)
assert before[str(physical)]==sha(physical) and json.loads(mapping.read_bytes())['Replace']=={str(virtual):str(physical)}
print(json.dumps({'stage':'C09_INPUTS_FROZEN','inputs':len(before),'packages':len(packages),'overlay_sha256':sha(physical)}),flush=True)
binary=N/'domain-c09-corrected.test.exe';code=invoke('compile',[str(G),'test','-overlay='+str(mapping),'-c','-o',str(binary),'./internal/domain'])
after=vector();save('source.after_compile.json',after)
if code:stop('compile',code)
if before!=after:stop('compile-drift',1)
save('testexe.json',{'path':str(binary),'sha256':sha(binary),'bytes':binary.stat().st_size,'cohort':'C09_ONLY_NOT_AE'})
paths.extend([binary,N/'testexe.json']);frozen=vector();save('source.before_first_case.json',frozen)
argv=[str(G),'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',str(binary),'-test.v','-test.failfast','-test.timeout=240s','-test.run=^TestIndependentHandlerConfigurationC09$']
code=invoke('cases',argv,W/'internal/domain',300)
events=[]
for line in (N/'cases.stdout.raw').read_bytes().splitlines():
 try:obj=json.loads(line)
 except ValueError:continue
 if obj.get('Test') and obj.get('Action') in ['pass','fail','skip']:events.append(obj)
leaf={obj['Test'].split('/',1)[1]:obj['Action'] for obj in events if '/' in obj['Test']}
final=vector();save('source.after_cases.json',final)
result={'actual_exit':code,'events':events,'case_results':leaf,'not_run':[name for name in names if name not in leaf],'source_drift':final!=frozen,'original_DB_sha256':sha(source),'testexe_sha256':sha(binary),'inputs':len(frozen),'formal_increment':0,'AE_separate_cohort':True}
save('result.json',result);print(json.dumps({'stage':'C09_FINISHED','actual_exit':code,'case_results':leaf,'not_run':result['not_run'],'source_drift':result['source_drift']}),flush=True)
if code or final!=frozen or set(leaf)!=set(names) or any(v!='pass' for v in leaf.values()):stop('C09-first-unexpected',code or 1)
