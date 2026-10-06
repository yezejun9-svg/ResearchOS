import pathlib,subprocess,os,json,hashlib,datetime,uuid,sys
ROOT=pathlib.Path(__file__).resolve().parents[7];MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os');HERE=pathlib.Path(__file__).resolve().parent
RUN=HERE/('closure-'+uuid.uuid4().hex);RUN.mkdir()
GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe';NODE=pathlib.Path('C:/nvm4w/nodejs/node.exe')
BUNDLE=ROOT/'.local/provider-binding/negative-controls-2/mu-worker.mjs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
env={'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOCACHE':str(MAIN/'.local/gocache'),'GOPATH':str(MAIN/'.local/gopath'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_GO':str(GO),'RESEARCHOS_NODE':str(NODE),'RESEARCHOS_MU_BUNDLE':str(BUNDLE),'RESEARCHOS_QUEUE_WORKER_BUNDLE':str(BUNDLE),'RESEARCHOS_STREAM_SDK_ROOT':str(MAIN/'third_party/mu'),'RESEARCHOS_PROVIDER_EVIDENCE_DIR':str(RUN/'native'),'PATH':str(NODE.parent)+';'+os.environ['PATH']}
(RUN/'native').mkdir()
results=[]
def run(label,argv):
 doc={'argv':list(map(str,argv)),'cwd':str(ROOT),'environment':env,'start':now(),'outer_timeout_seconds':600,'lane':'LOCAL_FIXTURE_ONLY'};write(RUN/(label+'.invocation.json'),doc)
 with (RUN/(label+'.stdout')).open('wb') as out,(RUN/(label+'.stderr')).open('wb') as err:
  try:p=subprocess.run(doc['argv'],cwd=ROOT,env=os.environ|env,stdout=out,stderr=err,timeout=600);code=p.returncode
  except subprocess.TimeoutExpired:code='OUTER_TIMEOUT'
 doc.update(end=now(),exit=code,stdout_sha256=sha(RUN/(label+'.stdout')),stderr_sha256=sha(RUN/(label+'.stderr')));write(RUN/(label+'.result.json'),doc);results.append({'label':label,'exit':code});print(label,code,flush=True)
 return code
def capture(label):
 names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
 paths=[p for p in names if p and not p.startswith('execution/v2.4/receipts/') and (ROOT/p).is_file()]
 files={p:{'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size} for p in paths}
 sdk={}
 for base in [MAIN/'third_party/mu/packages',MAIN/'third_party/mu/node_modules']:
  for p in base.rglob('*'):
   if p.is_file() and p.suffix in ['.js','.mjs','.cjs','.json','.node','.wasm']:
    sdk[str(p.relative_to(MAIN))]={'sha256':sha(p),'bytes':p.stat().st_size}
 doc={'at':now(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'source':files,'actual_main_sdk_and_dependencies':sdk,'bundle':{'path':str(BUNDLE),'sha256':sha(BUNDLE)},'tools':{str(GO):sha(GO),str(NODE):sha(NODE)}};write(RUN/(label+'.json'),doc);return doc
closure={}
before=capture('inputs-before')
if run('go-list',[GO,'list','-deps','-test','-json','./internal/domain','./adapters/runtime','./apps/cli'])==0:
 text=(RUN/'go-list.stdout').read_text(encoding='utf-8');decoder=json.JSONDecoder();index=0;closure={};packages=[]
 while index<len(text):
  while index<len(text) and text[index].isspace():index+=1
  if index==len(text):break
  package,index=decoder.raw_decode(text,index);packages.append(package.get('ImportPath'))
  directory=pathlib.Path(package.get('Dir',''))
  for key in ['GoFiles','CgoFiles','CFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
   for name in package.get(key,[]):
    p=directory/name
    if p.is_file():closure[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
 write(RUN/'compiled-inputs.json',{'packages':packages,'files':closure})
run('js',[NODE,'--test','adapters/runtime/mu/worker-control.test.mjs','adapters/runtime/mu/worker-stream.test.mjs','adapters/runtime/mu/worker-provider-binding.test.mjs'])
out=ROOT/'.local/provider-binding/final';out.mkdir(parents=True,exist_ok=True)
for package,name,pattern in [('./internal/domain','domain','TestRuntimeMu|TestRuntimeClientQueue|TestRuntimeModel|TestModelStream|TestModelSSE|TestClientQueue|TestQueueUpgrade|TestW180[12]|TestProviderBinding(Config|Reasoning|Wire|Preflight|Archived|Quarantine)'),('./adapters/runtime','bridge','.'),('./apps/cli','cli','.')]:
 binary=out/(name+'.test.exe')
 if run(name+'-compile',[GO,'test','-c','-o',binary,package])==0:
  run(name+'-buildinfo',[GO,'version','-m',binary]);write(RUN/(name+'-binary.json'),{'path':str(binary),'sha256':sha(binary),'bytes':binary.stat().st_size})
  # go test uses each package directory as cwd; the compiled binary needs it too.
  oldroot=ROOT;ROOT=ROOT/package[2:]
  run(name+'-test',[GO,'tool','test2json','-t','-p',package,binary,'-test.v','-test.count=1','-test.timeout=480s','-test.run='+pattern]);ROOT=oldroot
after=capture('inputs-after')
compiled_after={p:{'sha256':sha(pathlib.Path(p)),'bytes':pathlib.Path(p).stat().st_size} for p in closure}
write(RUN/'compiled-inputs-after.json',compiled_after)
write(RUN/'compiled-input-drift.json',[p for p in closure if closure[p]!=compiled_after[p]])
write(RUN/'summary.json',{'results':results,'source_equal':before['source']==after['source'],'sdk_equal':before['actual_main_sdk_and_dependencies']==after['actual_main_sdk_and_dependencies'],'blocked_chain_excluded':'TestProviderBindingActualSameRunToolHistory and TestProviderBindingAllOriginalStatesPortable; no new execution of held qualification chain','status':'EXECUTION_REPORTED_NOT_ACCEPTED'})
print(str(RUN),flush=True)
