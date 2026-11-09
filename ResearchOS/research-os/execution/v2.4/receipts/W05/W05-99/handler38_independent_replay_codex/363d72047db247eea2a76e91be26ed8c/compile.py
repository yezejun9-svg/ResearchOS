import os,sys,json,hashlib,subprocess,datetime
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');W=R/'.local/independent-handler38-a639cfcf';N=Path(__file__).resolve().parent;L=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools'];G=Path(L['go']['path']);GR=G.parent.parent;cache=R/'.local/independent-handler38-cache-a639cfcf';cache.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(n,o):(N/n).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
env=os.environ.copy();scopeenv={'GOROOT':str(GR),'GOTOOLCHAIN':'local','GOENV':'off','GOPATH':str(R/'.local/gopath'),'GOCACHE':str(cache),'GOPROXY':'off','GOSUMDB':'off','GOFLAGS':'','CGO_ENABLED':'0','GOWORK':'off','GOTELEMETRY':'off','RESEARCHOS_GO':str(G),'RESEARCHOS_NODE':L['node']['path'],'RESEARCHOS_MU_BUNDLE':str(R/'.local/w0599-main-stream-integration-r268/mu-worker.mjs'),'RESEARCHOS_QUEUE_WORKER_BUNDLE':str(R/'.local/w0599-main-stream-integration-r268/mu-worker.mjs'),'RESEARCHOS_STREAM_SDK_ROOT':str(R/'third_party/mu'),'RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR':str(N/'public-fixtures'),'PATH':str(Path(L['git']['path']).parent)+';'+str(G.parent)+';'+os.environ.get('PATH','')};env.update(scopeenv)
for k in list(env):
 if k.upper() in ['OPENAI_API_KEY','ANTHROPIC_API_KEY','AZURE_OPENAI_API_KEY']:env.pop(k,None)
save('environment.json',scopeenv)
def invoke(label,args,cwd=W,timeout=600):
 st=now()
 with (N/(label+'.stdout.raw')).open('xb') as out,(N/(label+'.stderr.raw')).open('xb') as err:
  try:q=subprocess.run(args,cwd=cwd,env=env,stdout=out,stderr=err,timeout=timeout);code=q.returncode
  except subprocess.TimeoutExpired:code=124
 save(label+'.invocation.json',{'argv':args,'cwd':str(cwd),'started_at':st,'ended_at':now(),'exit':code})
 if code:
  save('stopped.json',{'stage':label,'exit':code,'product_cases':0,'automatic_retry':False});print(json.dumps({'stage':label,'exit':code}));sys.exit(code)
 return code
for name in ['go','python','node','git']:assert sha(Path(L[name]['path']))==L[name]['sha256']
assert sha(Path(scopeenv['RESEARCHOS_MU_BUNDLE']))=='2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441'
freeze=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/candidate-review-2174dd5f0df043cd9f523945cc135cc2/source.freeze.json';f=json.loads(freeze.read_bytes());source=[]
for row in f['files']:
 actual=sha(W/row['path']);assert actual==row['sha256'];source.append({'path':row['path'],'actual_sha256':actual,'git_blob':row['git_blob']})
save('source38.current.json',source)
invoke('go-list',[str(G),'list','-deps','-test','-compiled','-json','./internal/domain','./internal/api','./internal/host','./apps/control','./ops/backup','./apps/cli'])
raw=(N/'go-list.stdout.raw').read_text(encoding='utf8');packages=[];d=json.JSONDecoder()
while raw.strip():
 raw=raw.lstrip();o,i=d.raw_decode(raw);packages.append(o);raw=raw[i:]
paths=set()
for p in packages:
 if not p.get('Dir'):continue
 folder=Path(p['Dir']);paths.update(x for x in folder.glob('*.go') if x.is_file())
 for key in ['GoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','CgoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','CFiles','CXXFiles','SysoFiles']:
  for name in p.get(key,[]):
   path=Path(name) if Path(name).is_absolute() else folder/name
   if not path.is_file():raise RuntimeError('missing compiler input '+str(path))
   paths.add(path)
 if p.get('Module',{}).get('GoMod'):paths.add(Path(p['Module']['GoMod']))
# All exported candidate files are public frozen inputs, including test-runtime assets.
for x in json.loads((N/'export_manifest.json').read_bytes())['files']:paths.add(W/x['path'])
for x in (GR/'pkg/tool').rglob('*'):
 if x.is_file():paths.add(x)
for x in (R/'third_party/mu').rglob('*'):
 if x.is_file() and '.git' not in x.parts:paths.add(x)
for rel in ['third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json','execution/toolchains/locked.json']:
 p=R/rel
 if p.is_file():paths.add(p)
paths.update(Path(L[n]['path']) for n in ['go','node','git','python']);paths.update([Path(scopeenv['RESEARCHOS_MU_BUNDLE']),Path(__file__).resolve(),N/'environment.json',N/'resource_amendment.byte-exact.json',N/'export_manifest.json'])
# Freeze physical paths and resolved junction targets. No canonical mutable metadata.
paths=sorted(paths);save('input_paths.json',[{'path':str(p),'resolved':str(p.resolve())} for p in paths])
def vector():return {str(p):sha(p) for p in paths}
before=vector();save('source.before.json',before);print(json.dumps({'stage':'SOURCE_FROZEN_BEFORE_COMPILE','inputs':len(before),'packages':len(packages)}),flush=True)
exe=[]
for name,pkg in [('domain','./internal/domain'),('api','./internal/api'),('host','./internal/host'),('cli','./apps/cli')]:
 target=N/(name+'.test.exe');invoke('build-'+name,[str(G),'test','-c','-o',str(target),pkg]);exe.append({'package':pkg,'path':str(target),'sha256':sha(target),'bytes':target.stat().st_size});print(json.dumps({'stage':'COMPILED','package':pkg,'sha256':exe[-1]['sha256']}),flush=True)
invoke('build-cli-product',[str(G),'build','-o',str(N/'researchos-cli.exe'),'./apps/cli']);exe.append({'package':'./apps/cli PRODUCT','path':str(N/'researchos-cli.exe'),'sha256':sha(N/'researchos-cli.exe')})
after=vector();save('source.after_compile.json',after);save('executables.before_cases.json',exe);save('compile_result.json',{'exit':0,'inputs':len(before),'source_drift':before!=after,'testcases':0,'executables':exe});assert before==after;print(json.dumps({'stage':'COMPILE_COMPLETE_NO_CASES','inputs':len(before),'source_drift':False}),flush=True)
