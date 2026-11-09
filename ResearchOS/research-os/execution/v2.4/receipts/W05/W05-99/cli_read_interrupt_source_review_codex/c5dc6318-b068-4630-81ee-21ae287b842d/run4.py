from pathlib import Path
import os,sys,subprocess,json,hashlib,datetime,re,shutil
sys.stdout.reconfigure(encoding='utf-8')
R=Path.cwd();O=R/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_source_review_codex/c5dc6318-b068-4630-81ee-21ae287b842d';(O/'attempt4').mkdir(exist_ok=False);O=O/'attempt4';W=R/'.local/worktrees/independent-l02-c5dc6318';G=R/'.local/tools/go1.27.1/go';N=Path('C:/nvm4w/nodejs/node.exe');B=R/'.local/w0599-main-stream-integration-r268/mu-worker.mjs'
E={k:v for k,v in os.environ.items() if not k.startswith('GIT_') and not k.startswith('RESEARCHOS_')};E.update(GIT_NO_REPLACE_OBJECTS='1',GOROOT=str(G),GOENV='off',GOTOOLCHAIN='local',GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE=str(N),RESEARCHOS_MU_BUNDLE=str(B),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(B),RESEARCHOS_STREAM_SDK_ROOT=str(R/'third_party/mu'),RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(O/'actual-fixtures'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(n,a):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (O/(n+'.stdout.raw')).open('xb') as so,(O/(n+'.stderr.raw')).open('xb') as se:
  p=subprocess.run(a,cwd=W,env=E,stdout=so,stderr=se,timeout=600)
 save(n+'.invocation.json',{'argv':a,'cwd':str(W),'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'stdout_sha256':sha(O/(n+'.stdout.raw')),'stderr_sha256':sha(O/(n+'.stderr.raw'))});print(n,p.returncode,flush=True);return p.returncode
assert sha(B)=='2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441'
save('environment.json',{k:v for k,v in E.items() if k.startswith(('GO','RESEARCHOS_','GIT_'))})
assert run('go-list-before',[str(G/'bin/go.exe'),'list','-deps','-test','-json','./apps/cli','./internal/domain','./adapters/runtime'])==0
raw=(O/'go-list-before.stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();packages=[]
while raw.strip():
 raw=raw.lstrip();p,i=dec.raw_decode(raw);packages.append(p);raw=raw[i:]
paths=set()
for p in packages:
 if not p.get('Dir'):continue
 d=Path(p['Dir']);paths.update(q for q in d.glob('*.go') if q.is_file())
 for k in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles']:
  paths.update(d/n for n in p.get(k,[]))
 if p.get('Module',{}).get('GoMod'):paths.add(Path(p['Module']['GoMod']))
for folder in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
 paths.update(p for p in (W/folder).rglob('*') if p.is_file() and p.suffix in ['.go','.mjs','.json','.sql'])
for folder in ['internal','adapters','tests']:
 for d in (W/folder).rglob('testdata'):paths.update(p for p in d.rglob('*') if p.is_file())
for folder in ['packages','node_modules']:paths.update(p for p in (R/'third_party/mu'/folder).rglob('*') if p.is_file() and '.git' not in p.parts)
for n in ['third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json']:paths.add(R/n)
paths.update([W/'go.mod',W/'go.sum',G/'bin/go.exe',N,B,Path(__file__).resolve(),Path(sys.executable)])
paths.update(p for p in (G/'pkg/tool').rglob('*') if p.is_file())
ps=Path(shutil.which('powershell.exe'));paths.add(ps);paths.update(p for p in ps.parent.glob('*.dll') if p.is_file())
for n in ['csc.exe','csc.exe.config','Microsoft.CSharp.dll','mscorlib.dll','System.dll','System.Core.dll']:
 p=Path(E['SYSTEMROOT'])/'Microsoft.NET/Framework64/v4.0.30319'/n
 if p.is_file():paths.add(p)
probe=R/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_source_precheck_codex/fbc5e37c-b117-4717-b249-0e9e44309775/probe_test.go';paths.add(probe)
save('overlay.json',{'Replace':{str(W/'apps/cli/independent_original_oversize_test.go'):str(probe)}});paths.add(O/'overlay.json')
locked=W/'execution/toolchains/locked.json';paths.add(locked);locked_doc=json.loads(locked.read_bytes());gittool=Path(locked_doc['tools']['git']['path']);assert sha(gittool)==locked_doc['tools']['git']['sha256'];paths.add(gittool);paths=sorted(paths)
def snap():return {('repo:'+p.relative_to(W).as_posix() if p.is_relative_to(W) else 'main:'+p.relative_to(R).as_posix() if p.is_relative_to(R) else 'absolute:'+p.as_posix()):sha(p) for p in paths}
before=snap();save('source_before.json',before);print('inputs',len(before),flush=True)
full=run('full-cli',[str(G/'bin/go.exe'),'test','-json','-count=1','-timeout=480s','./apps/cli'])
probe_exit=run('original-oversize-probe',[str(G/'bin/go.exe'),'test','-json','-count=1','-timeout=60s','-overlay',str(O/'overlay.json'),'-run','^TestIndependentOversizeCannotBecomeSignalFailure$','./apps/cli'])
after=snap();save('source_after.json',after)
assert run('go-list-after',[str(G/'bin/go.exe'),'list','-deps','-test','-json','./apps/cli','./internal/domain','./adapters/runtime'])==0
counts={}
for n in ['full-cli','original-oversize-probe']:
 c={'pass':0,'fail':0,'skip':0,'top_pass':0}
 for l in (O/(n+'.stdout.raw')).read_bytes().splitlines():
  try:x=json.loads(l)
  except:continue
  if x.get('Test') and x.get('Action') in c:
   c[x['Action']]+=1
   if x['Action']=='pass' and '/' not in x['Test']:c['top_pass']+=1
 counts[n]=c
result={'full_exit':full,'original_probe_exit':probe_exit,'counts':counts,'input_count':len(before),'drift':before!=after,'source_before_sha256':sha(O/'source_before.json'),'source_after_sha256':sha(O/'source_after.json'),'bundle_sha256':sha(B)};save('result.json',result);print(json.dumps(result),flush=True)

