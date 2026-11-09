import pathlib,subprocess,json,hashlib,sys,os,datetime,shutil,concurrent.futures
HERE=pathlib.Path(__file__).resolve().parent;MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os');ROOT=MAIN/'.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c';AUTHOR=MAIN/'.local/worktrees/codex-w0599-provider-binding';AUTH=AUTHOR/'execution/v2.4/receipts/W05/W05-99/provider_binding_executor_codex/typed-route-final-6c47a88a198349b4bd2a3d3d223510b1';SCOPE=MAIN/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-independent-scope-r288/scope_registration.json';GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe';BIN=HERE/'independent.domain.test.exe'
ENV={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','SYSTEMDRIVE','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE','OS']}
ENV.update({'PATH':str(GO.parent)+';'+str(pathlib.Path(shutil.which('git')).parent)+';'+str(pathlib.Path(sys.executable).parent)+';'+os.environ['SYSTEMROOT']+'/System32','TEMP':str(ROOT/'cache-r294/tmp'),'TMP':str(ROOT/'cache-r294/tmp'),'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOCACHE':str(ROOT/'cache-r294/go'),'GOPATH':str(MAIN/'.local/gopath'),'GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','GOFLAGS':'','GOOS':'windows','GOARCH':'amd64','CGO_ENABLED':'0','GIT_NO_REPLACE_OBJECTS':'1'})
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ref(p):p=pathlib.Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(name,obj):
 with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def cmd(label,args,cwd=ROOT,extra=None,timeout=300):
 env=ENV|(extra or {});inv={'argv':list(map(str,args)),'cwd':str(cwd),'environment':env,'started':now(),'timeout_seconds':timeout};write(label+'.invocation.json',inv)
 with (HERE/(label+'.stdout.raw')).open('xb') as out,(HERE/(label+'.stderr.raw')).open('xb') as err:
  try:code=subprocess.run(inv['argv'],cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 result=inv|{'exit':code,'finished':now(),'stdout':ref(HERE/(label+'.stdout.raw')),'stderr':ref(HERE/(label+'.stderr.raw'))};write(label+'.result.json',result);print(label,code,flush=True)
 if code!=0:write('failure-'+label+'.json',{'kind':'actual invocation','result':ref(HERE/(label+'.result.json')),'product_case':label.startswith(('case-','synthetic-','epoch-','public-'))});raise RuntimeError('STOP_FIRST_UNEXPECTED '+label)
 return result

def capture(name,paths):
 unique=sorted(set(str(pathlib.Path(p)) for p in paths));
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:files={r['path']:r for r in pool.map(ref,unique)}
 write(name,{'at':now(),'files':files,'environment':ENV});return files

def basepaths():
 paths=[e['path'] for e in json.loads((HERE/'export.json').read_text(encoding='utf-8'))['files']]
 # All SDK source/lock/resources and installed modules are inventory-only: never invoke Node.
 paths += [str(p) for p in (MAIN/'third_party/mu').rglob('*') if p.is_file()]
 paths += [str(GO),str(GO.parent/'gofmt.exe'),str(pathlib.Path(sys.executable)),shutil.which('git'),str(pathlib.Path('C:/nvm4w/nodejs/node.exe')),str(AUTHOR/'.local/provider-binding/negative-controls-2/mu-worker.mjs'),str(MAIN/'execution/toolchains/locked.json'),str(SCOPE),str(HERE/'amendment-ref.json'),str(pathlib.Path(json.loads((HERE/'amendment-ref.json').read_text(encoding='utf-8'))['path']))]
 paths += [str(p) for p in (GO.parent.parent/'pkg/tool/windows_amd64').iterdir() if p.is_file()]
 paths += [str(p) for p in HERE.glob('*.py')]+[str(p) for p in HERE.glob('*.go')]+[str(p) for p in (HERE/'specs').glob('*.json')]+[str(HERE/'overlay.json'),str(HERE/'synthetic_workspace_evidence.txt')]
 for e in json.loads((HERE/'original7.before.json').read_text(encoding='utf-8')):paths +=[e['original']['path'],e['copy']['path']]
 return paths

def checkevents(label):
 events=[json.loads(l) for l in (HERE/(label+'.stdout.raw')).read_text(encoding='utf-8').splitlines() if l.strip()];runs=[e for e in events if e.get('Action')=='run' and e.get('Test')];passed=[e for e in events if e.get('Action')=='pass' and e.get('Test')];bad=[e for e in events if e.get('Action') in ['skip','fail']]
 if len(runs)!=1 or len(passed)!=1 or bad:write('failure-'+label+'-events.json',{'runs':runs,'passes':passed,'bad':bad});raise RuntimeError('STOP_EVENT_ASSERT '+label)
 return {'tests_run':len(runs),'tests_pass':len(passed),'fail':0,'skip':0}

scope=json.loads(SCOPE.read_text(encoding='utf-8'));phase=sys.argv[1]
try:
 if phase=='prepare':
  assert sha(SCOPE)=='0d6c0121b1a267e124100f63872fc3f8eea3c84456c471ec2d4d11d1c007b277'
  (ROOT/'cache-r294/tmp').mkdir(parents=True);(HERE/'specs').mkdir();plan=[]
  for mode in ['positive','missing-dispatch-transport']:
   for key in ['1','0','2','3','4','5']:
    label='public-'+mode+'-'+key;case={'case':label,'id':key,'mode':mode,'input':str(HERE/'inputs'/(key+'.sqlite')),'input_sha256':'sha256:'+sha(HERE/'inputs'/(key+'.sqlite')),'output':str(HERE/(label+'-evidence')),'expected_inventory':3 if key=='0' else 1};write('specs/'+label+'.json',case);plan.append({'label':label,'selector':'TestIndependentProviderPublicArchiveBoundary','env':{'RESEARCHOS_INDEPENDENT_PUBLIC_SPEC':str(HERE/'specs'/(label+'.json'))},'timeout':180})
  assert len(plan)==12;write('case-plan.json',plan)
  overlay=HERE/'independent_provider_public_boundary_windows_test.go';cmd('gofmt-owned-overlay',[GO.parent/'gofmt.exe','-w',overlay]);write('overlay.json',{'Replace':{str(ROOT/'internal/domain/independent_provider_public_boundary_windows_test.go'):str(overlay)}})
  before=capture('before-compile.json',basepaths()+[HERE/'case-plan.json'])
  cmd('go-list',[GO,'list','-overlay',HERE/'overlay.json','-deps','-test','-json','./internal/domain'])
  text=(HERE/'go-list.stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();i=0;paths=[];packages=[]
  while i<len(text):
   while i<len(text) and text[i].isspace():i+=1
   if i==len(text):break
   p,i=dec.raw_decode(text,i);packages.append(p.get('ImportPath'));d=pathlib.Path(p.get('Dir',''))
   for k in ['GoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','IgnoredGoFiles','IgnoredOtherFiles']:
    for n in p.get(k,[]):
     f=d/n
     if str(f)==str(ROOT/'internal/domain/independent_provider_public_boundary_windows_test.go'):f=overlay
     if f.is_file():paths.append(str(f))
   if d.is_relative_to(ROOT):paths += [str(f) for f in d.glob('*.go')]
  capture('compiled-inputs.json',paths);write('packages.json',packages)
  # Freeze complete dependency closure before compiler invocation.
  full=capture('full-before-compile.json',list(before)+paths)
  cmd('compile',[GO,'test','-overlay',HERE/'overlay.json','-c','-o',BIN,'./internal/domain'])
  cmd('buildinfo',[GO,'version','-m',BIN]);nowfiles=capture('before-first-case.json',list(full)+[BIN]);drift=[p for p,v in full.items() if nowfiles[p]!=v];write('prepare-result.json',{'drift':drift,'count':len(nowfiles),'binary':ref(BIN),'cases_executed':0});assert not drift
 elif phase=='execute':
  before=json.loads((HERE/'before-first-case.json').read_text(encoding='utf-8'))['files'];current=capture('pre-execution-current.json',before);assert current==before
  results=[]
  for c in json.loads((HERE/'case-plan.json').read_text(encoding='utf-8')):
   r=cmd(c['label'],[GO,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',BIN,'-test.v','-test.count=1','-test.timeout='+str(c['timeout'])+'s','-test.run=^'+c['selector']+'$'],ROOT/'internal/domain',c['env']);r=r|checkevents(c['label']);results.append({'label':c['label'],'result':ref(HERE/(c['label']+'.result.json')),'tests':1});write('progress-'+str(len(results))+'.json',{'completed':results})
  after=capture('after-cases.json',before);assert before==after;write('execution-summary.json',{'actual_cases':len(results),'results':results,'inputs':len(before),'drift':[],'model':0,'HTTP':0,'Node':0,'worker':0,'paid':0,'qualification':0,'formal':0,'history_failures_held':5})
 else:raise RuntimeError('unknown phase')
except Exception as e:
 write('STOP-'+phase+'.json',{'at':now(),'error':repr(e),'automatic_retry':False,'model':0,'worker':0,'history_held':5});print(repr(e),flush=True);raise
