from pathlib import Path
import json,os,subprocess,hashlib,datetime,time,sys
sys.stdout.reconfigure(encoding='utf-8')
R=Path('D:/作品集/ResearchOS/research-os');O=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_source_review_codex/9673a59f-c9e7-43bb-8f98-4972c1b553ec';D=R/'.local/independent-configuration-9673a59f'
E=json.loads((O/'environment.json').read_text(encoding='utf-8'));env=os.environ.copy();env.update(E);go=E['RESEARCHOS_GO']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def run(name,argv,cwd,timeout):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (O/(name+'.stdout.raw')).open('wb') as out,(O/(name+'.stderr.raw')).open('wb') as err:
  p=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout)
 save(name+'.invocation.json',{'argv':argv,'cwd':str(cwd),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'stdout_sha256':sha(O/(name+'.stdout.raw')),'stderr_sha256':sha(O/(name+'.stderr.raw'))})
 if p.returncode:print(name+' FAILED '+str(p.returncode),flush=True);sys.exit(p.returncode)
 print(name+' PASS',flush=True)
run('go-list',[go,'list','-deps','-test','-json','./internal/domain'],D,180)
s=(O/'go-list.stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();packages=[]
while s.strip():
 s=s.lstrip();p,n=dec.raw_decode(s);packages.append(p);s=s[n:]
files=set()
for p in packages:
 d=Path(p.get('Dir',''));files.update(x for x in d.glob('*') if x.is_file() and x.suffix in ['.go','.s','.h','.c','.syso'])
 for k in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
  for n in p.get(k,[]):
   x=d/n
   if x.is_file():files.add(x)
 for k in ['GoMod']:
  if p.get('Module',{}).get(k):files.add(Path(p['Module'][k]))
files.update(x for x in D.rglob('*') if x.is_file())
files.update(x for x in Path(E['GOROOT']).joinpath('pkg/tool/windows_amd64').glob('*') if x.is_file())
files.add(Path(go));files.add(Path(sys.executable));files.add(O/'environment.json')
for k in ['RESEARCHOS_CONFIGURATION_OLD_CONTROL','RESEARCHOS_CONFIGURATION_TARGET_PROGRAM'] :files.add(Path(E[k]))
files.update(x for x in Path(E['RESEARCHOS_CONFIGURATION_OLD_ROOT']).rglob('*') if x.is_file())
def vector():return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files,key=lambda x:str(x))]
before=vector();save('inputs.before.json',before);print('frozen inputs '+str(len(before)),flush=True)
run('compile',[go,'test','-c','-o',str(O/'domain.test.exe'),'./internal/domain'],D,300)
after=vector();save('inputs.after_compile.json',after)
if before!=after:save('drift.json',{'phase':'compile'});sys.exit(91)
save('binary.freeze.json',{'path':str(O/'domain.test.exe'),'sha256':sha(O/'domain.test.exe'),'bytes':(O/'domain.test.exe').stat().st_size,'inputs_sha256':sha(O/'inputs.before.json')})
selector='^Test(ClientQueueFreshNumberedSchema|ClientQueueHistorical22NumberedSchema|ClientQueueBackup|ConfigurationUpgrade|BackupHostConfiguration|ClientConfiguration|ClientCommandIdentity|QueueUpgrade)'
run('test',[go,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',str(O/'domain.test.exe'),'-test.v=test2json','-test.run='+selector,'-test.timeout=300s'],D/'internal/domain',360)
end=vector();save('inputs.after_test.json',end);counts={'pass':0,'fail':0,'skip':0};tests=[]
for line in (O/'test.stdout.raw').read_text(encoding='utf-8').splitlines():
 x=json.loads(line)
 if x.get('Test') and x.get('Action') in counts:counts[x['Action']]+=1;tests.append({'test':x['Test'],'action':x['Action']})
save('test.result.json',{'counts':counts,'tests':tests,'input_count':len(before),'all_inputs_equal':before==after==end,'binary_sha256':sha(O/'domain.test.exe'),'models':0,'paid':0,'worker':0})
print(json.dumps({'counts':counts,'inputs':len(before),'stable':before==after==end}),flush=True)
