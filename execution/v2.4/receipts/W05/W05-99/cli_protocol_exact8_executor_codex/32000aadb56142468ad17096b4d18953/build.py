from pathlib import Path
import os,sys,json,hashlib,subprocess,datetime,uuid
W=Path(__file__).resolve().parents[7]
# Resolve by Git to avoid relying on receipt nesting depth.
W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
MAIN=Path('D:/作品集/ResearchOS/research-os')
N=Path(__file__).resolve().parent
RUN=N/('build-'+uuid.uuid4().hex);RUN.mkdir()
GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe';GOROOT=GO.parent.parent
assert hashlib.sha256(GO.read_bytes()).hexdigest()=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
ENV=os.environ.copy();ENV.update({'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GOROOT),'GOPATH':str(MAIN/'.local/gopath'),'GOCACHE':str(W/'.local/cli-r303/cache'),'GOTMPDIR':str(W/'.local/cli-r303/gotmp'),'GOPROXY':'off','GOSUMDB':'off'})
for key in ['GOCACHE','GOTMPDIR']:Path(ENV[key]).mkdir(parents=True,exist_ok=True)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def invoke(name,argv,timeout=510):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=RUN/(name+'.stdout');err=RUN/(name+'.stderr')
 with out.open('wb') as o,err.open('wb') as e:
  p=subprocess.Popen(argv,cwd=W,env=ENV,stdout=o,stderr=e)
  try:code=p.wait(timeout=timeout);timed=False
  except subprocess.TimeoutExpired:p.kill();code=p.wait();timed=True
 row={'actualargv':argv,'cwd':str(W),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':code,'timeout':timed,'stdout':{'path':str(out.relative_to(W)),'sha256':digest(out)},'stderr':{'path':str(err.relative_to(W)),'sha256':digest(err)},'env':{k:ENV[k] for k in ['GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOCACHE','GOTMPDIR','GOPROXY','GOSUMDB']}}
 (RUN/(name+'.invocation.json')).write_text(json.dumps(row,indent=2),encoding='utf-8');print(name,code,flush=True)
 if code:print(err.read_text(encoding='utf-8',errors='replace')[-4000:],flush=True);raise SystemExit(code)
 return out
paths=json.loads((N/'cli_implementation_scope.json').read_text(encoding='utf-8'))['paths']
invoke('gofmt',[str(GOROOT/'bin/gofmt.exe'),'-w',*paths])
invoke('go-version',[str(GO),'version'])
raw=invoke('go-list',[str(GO),'list','-deps','-test','-json','./apps/cli','./tests/runtime/cli_contract'])
dec=json.JSONDecoder();text=raw.read_text(encoding='utf-8');pkgs=[]
while text.strip():
 text=text.lstrip();obj,end=dec.raw_decode(text);pkgs.append(obj);text=text[end:]
files=set()
for pkg in pkgs:
 d=Path(pkg.get('Dir',''))
 if not d.is_dir():continue
 for q in d.iterdir():
  if q.is_file() and q.suffix.lower() in ['.go','.s','.h','.c','.cc','.cpp','.m','.f','.syso']:files.add(q.resolve())
 for k,v in pkg.items():
  if k.endswith('Files') and isinstance(v,list):
   for rel in v:
    q=d/rel
    if q.is_file():files.add(q.resolve())
for rel in paths+['go.mod','go.sum']:
 files.add((W/rel).resolve())
# Complete public runtime inputs and fixed SDK source; never execute the SDK.
for rel in ['migrations/sqlite','internal/api/contracts','internal/domain/contracts','spec/v2.0/contracts','third_party/mu_runtime']:
 d=W/rel
 if d.is_dir():
  for q in d.rglob('*'):
   if q.is_file():files.add(q.resolve())
for q in (GOROOT/'pkg/tool').rglob('*'):
 if q.is_file():files.add(q.resolve())
files.add(GO.resolve());files.add((GOROOT/'bin/gofmt.exe').resolve())
files.add(Path(__file__).resolve())
def vector():return [{'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(files,key=str)]
before=vector();(RUN/'inputs.before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
print('INPUTS',len(before),'RUN',RUN,flush=True)
try:
 invoke('cli-build',[str(GO),'build','-work','-o',str(RUN/'researchos-cli.exe'),'./apps/cli'])
 invoke('test-build',[str(GO),'test','-c','-work','-o',str(RUN/'cli.test.exe'),'./apps/cli'])
 invoke('harness-build-only',[str(GO),'build','-work','-o',str(RUN/'cli-contract.exe'),'./tests/runtime/cli_contract'])
finally:
 after=vector();(RUN/'inputs.after.json').write_text(json.dumps(after,indent=2),encoding='utf-8');drift=[x for x,y in zip(before,after) if x!=y]
 artifacts=[{'path':str(p.relative_to(W)),'sha256':digest(p),'bytes':p.stat().st_size} for p in RUN.glob('*.exe')]
 (RUN/'build-result.json').write_text(json.dumps({'input_count':len(before),'drift':drift,'artifacts':artifacts,'tests_executed':0},indent=2),encoding='utf-8')
 print('DRIFT',len(drift),flush=True)
