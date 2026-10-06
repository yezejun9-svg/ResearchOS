import os,sys,json,uuid,subprocess,datetime,hashlib
from pathlib import Path
root=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-host-configuration-handler');main=Path('D:/作品集/ResearchOS/research-os')
out=Path(__file__).resolve().parent/('run-'+uuid.uuid4().hex);out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):
 with (out/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
go=main/'.local/tools/go1.27.1/go';node=Path('C:/nvm4w/nodejs/node.exe');bundle=main/'.local/independent-main-stream/c22da050-5fd2-4394-932c-5a5534360295/mu-worker.mjs'
assert sha(go/'bin/go.exe')=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
env=os.environ.copy();names=dict(GOROOT=str(go),GOTOOLCHAIN='local',GOENV='off',GOPATH=str(main/'.local/gopath'),GOCACHE=str(main/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(go/'bin/go.exe'),RESEARCHOS_NODE=str(node),RESEARCHOS_MU_BUNDLE=str(bundle),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(bundle),RESEARCHOS_STREAM_SDK_ROOT=str(main/'third_party/mu'),RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(out/'public-fixtures'))
env.update(names);save('environment.json',names)
def invoke(label,argv,cwd=root):
 start=now()
 with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:r=subprocess.run(argv,cwd=cwd,env=env,stdout=stdout,stderr=stderr)
 save(label+'.invocation.json',dict(actualargv=argv,cwd=str(cwd),started_at=start,ended_at=now(),exit=r.returncode))
 return r.returncode
code=invoke('go-list',[str(go/'bin/go.exe'),'list','-deps','-test','-json','./internal/domain','./internal/api','./internal/host','./apps/control','./ops/backup','./apps/cli'])
if code:print(out);sys.exit(code)
text=(out/'go-list.stdout').read_text(encoding='utf8');packages=[];decoder=json.JSONDecoder()
while text.strip():text=text.lstrip();p,n=decoder.raw_decode(text);packages.append(p);text=text[n:]
paths=set()
for p in packages:
 if not p.get('Dir'):continue
 d=Path(p['Dir']);paths.update(f for f in d.glob('*.go') if f.is_file())
 for key in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles','CgoFiles']:
  paths.update(d/n for n in p.get(key,[]) if (d/n).is_file())
 if p.get('Module',{}).get('GoMod'):paths.add(Path(p['Module']['GoMod']))
for folder in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
 paths.update(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ['.go','.mjs','.json','.sql'])
for folder in ['packages','node_modules']:
 paths.update(p for p in (main/'third_party/mu'/folder).rglob('*') if p.is_file() and '.git' not in p.parts)
for name in ['go.mod','go.sum','third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json']:
 p=(root/name) if name in ['go.mod','go.sum'] else main/name
 if p.is_file():paths.add(p)
paths.update(p for p in (go/'pkg/tool').rglob('*') if p.is_file());paths.update([go/'bin/go.exe',node,bundle,Path(__file__).resolve()])
for folder in ['internal','adapters','tests']:
 for d in (root/folder).rglob('testdata'):paths.update(p for p in d.rglob('*') if p.is_file())
def inputs():
 return {('repo:'+p.relative_to(root).as_posix() if p.is_relative_to(root) else 'main:'+p.relative_to(main).as_posix() if p.is_relative_to(main) else 'absolute:'+p.as_posix()):sha(p) for p in sorted(paths)}
invoke('git-status',['git','status','--short','--untracked-files=no']);invoke('go-version',[str(go/'bin/go.exe'),'version']);invoke('node-version',[str(node),'--version'])
before=inputs();save('source.before.json',before)
args=sys.argv[1:];mode=args[0]
if mode=='build':argv=[str(go/'bin/go.exe'),'test','-c','-o',str(out/'domain.test.exe'),'./internal/domain']
elif mode=='test':argv=[str(go/'bin/go.exe'),'test','-json','-count=1','-timeout','180s','-run',args[2],*args[1].split(',')]
else:raise ValueError('only explicit build/test modes')
code=invoke('command',argv);after=inputs();save('source.after.json',after)
binary=out/'domain.test.exe'
result=dict(measurement_mode='LOCAL_FIXTURE_NOT_LIVE_NOT_ACCEPTANCE',kind=mode,exit=code,input_count=len(before),source_drift=before!=after,bundle_sha256=sha(bundle),binary_sha256=sha(binary) if binary.exists() else None)
if mode=='test':
 events=[]
 for line in (out/'command.stdout').read_text(encoding='utf8',errors='replace').splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 result['test_events']={a:sum(1 for e in events if e.get('Test') and e.get('Action')==a) for a in ['pass','fail','skip']}
save('result.json',result);print(out);print(json.dumps(result));print((out/'command.stdout').read_text(encoding='utf8',errors='replace')[-1800:]);print((out/'command.stderr').read_text(encoding='utf8',errors='replace')[-5000:]);sys.exit(code or int(before!=after))
