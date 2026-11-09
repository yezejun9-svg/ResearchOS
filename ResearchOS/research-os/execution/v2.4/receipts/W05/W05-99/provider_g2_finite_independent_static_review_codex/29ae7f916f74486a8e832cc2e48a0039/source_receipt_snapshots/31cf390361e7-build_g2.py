from pathlib import Path
import os,sys,json,subprocess,hashlib,uuid,datetime,re
W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
N=Path(__file__).resolve().parent;M=Path('D:/作品集/ResearchOS/research-os')
G=M/'.local/tools/go1.27.1/go/bin/go.exe';GOROOT=G.parent.parent
NODE=Path('C:/nvm4w/nodejs/node.exe')
BUNDLE=M/'.local/worktrees/codex-w0599-provider-binding/.local/provider-whole9-g1-esm-788ce69c409b472799ee1389b778f9da/mu-worker.mjs'
B=N/('build-'+uuid.uuid4().hex);B.mkdir();WORK=W/'.local/provider-g2-finite';(WORK/'cache').mkdir(parents=True,exist_ok=True);(WORK/'tmp').mkdir(exist_ok=True)
ENV={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE']}
ENV.update({'PATH':str(NODE.parent)+';C:/Windows/System32;C:/Windows;C:/Program Files/Git/cmd','GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GOROOT),'GOPATH':str(M/'.local/gopath'),'GOCACHE':str(WORK/'cache'),'GOTMPDIR':str(WORK/'tmp'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_MU_BUNDLE':str(BUNDLE),'RESEARCHOS_GO':str(G)})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,obj):(B/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def run(name,argv,timeout=600):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (B/(name+'.stdout')).open('wb') as out,(B/(name+'.stderr')).open('wb') as err:
  p=subprocess.Popen(argv,cwd=W,env=ENV,stdout=out,stderr=err)
  try:code=p.wait(timeout=timeout);timed=False
  except subprocess.TimeoutExpired:
   timed=True
   if p.poll() is None:subprocess.run(['C:/Windows/System32/taskkill.exe','/PID',str(p.pid),'/T','/F'],stdout=err,stderr=err)
   code=p.wait()
 save(name+'.invocation.json',{'argv':argv,'cwd':str(W),'environment_allowlist':ENV,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'exit_code':code,'timeout':timed})
 print(name,code,flush=True)
 if code:print('FAILED_BUILD',B,flush=True);sys.exit(code)
def rows(paths):return [{'path':str(p),'resolved':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)]
assert sha(G)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
assert sha(NODE)=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
assert sha(BUNDLE)=='497e111b4b0b8d080f2ac20baf78a1d08b132e53866ebf67d851e886a19caade'
source=['internal/domain/runtime_provider_binding_windows_test.go','internal/domain/runtime_coordinator_windows_test.go']
run('gofmt',[str(G.parent/'gofmt.exe'),'-w']+source)
for rel in source:
 p=B/'source-at-build'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((W/rel).read_bytes())
run('go-version',[str(G),'version'])
run('go-list',[str(G),'list','-deps','-test','-json','./internal/domain'])
text=(B/'go-list.stdout').read_text(encoding='utf-8');decoder=json.JSONDecoder();packages=[]
while text.strip():
 value,pos=decoder.raw_decode(text.lstrip());packages.append(value);text=text.lstrip()[pos:]
paths={G,G.parent/'gofmt.exe',NODE,Path(sys.executable),BUNDLE,Path(str(BUNDLE)+'.build.json'),Path(__file__)}
for item in packages:
 if item.get('Dir'):
  d=Path(item['Dir'])
  for p in d.iterdir():
   if p.is_file() and p.suffix.lower() in ['.go','.s','.h','.c','.cc','.cpp','.syso']:paths.add(p)
  for key in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CgoFiles','CFiles','HFiles','SFiles','SysoFiles']:
   for rel in item.get(key,[]):
    p=d/rel
    if p.is_file():paths.add(p)
  mod=item.get('Module',{})
  if mod.get('GoMod'):paths.add(Path(mod['GoMod']))
for rel in ['go.mod','go.sum']+source:paths.add(W/rel)
for rel in ['migrations/sqlite','spec/v2.0/contracts','api','internal/domain/schemas']:
 d=W/rel
 if d.exists():paths.update(p for p in d.rglob('*') if p.is_file())
paths.update(p for p in (GOROOT/'pkg/tool').rglob('*') if p.is_file())
prior=json.loads((M/'execution/v2.4/receipts/W05/W05-99/provider_whole9_g1_root_executor_codex/788ce69c409b472799ee1389b778f9da/inputs.pre-case.json').read_text(encoding='utf-8'))
sdkdirs=set()
for raw,old in prior.items():
 normal=raw.replace('\\','/').lower()
 if '/node_modules/' in normal or '/third_party/' in normal or '/adapters/runtime/mu/' in normal:
  p=Path(raw)
  if not p.is_file():raise RuntimeError('Missing locked SDK input: '+raw)
  if sha(p)!=old['sha256']:raise RuntimeError('Changed locked SDK input: '+raw)
  paths.add(p);sdkdirs.add(p.parent)
for d in sdkdirs:
 paths.update(p for p in d.iterdir() if p.is_file())
before=rows(paths);save('inputs.before.json',before)
run('test-build',[str(G),'test','-c','-work','-x','-o',str(B/'domain.g2.test.exe'),'./internal/domain'])
run('buildinfo',[str(G),'version','-m',str(B/'domain.g2.test.exe')])
raw=(B/'test-build.stderr').read_text(encoding='utf-8');match=re.search(r'^WORK=(.+)$',raw,re.M);assert match,'Actual WORK missing'
work=Path(match.group(1).strip());generated=[];archives=set()
dest=B/'compiler-generated';dest.mkdir()
for p in work.rglob('*'):
 if p.is_file() and (p.suffix=='.go' or p.name.startswith('importcfg')):
  q=dest/p.relative_to(work);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());generated.append({'original_path':str(p),'retained_path':str(q),'sha256':sha(q)})
  if p.name.startswith('importcfg'):
   for line in p.read_text(encoding='utf-8').splitlines():
    if line.startswith('packagefile '):archives.add(Path(line.split('=',1)[1].replace('$WORK',str(work))))
assert any(Path(x['original_path']).name=='_testmain.go' for x in generated)
save('generated.json',generated);save('archives.before.json',rows(archives))
after=rows(paths);save('inputs.after.json',after);assert before==after,'Compiler input drift'
save('build-result.json',{'status':'COMPILED_NOT_EXECUTED','input_count':len(before),'generated_count':len(generated),'archives':len(archives),'source_drift':False,'test_exe':{'path':str(B/'domain.g2.test.exe'),'sha256':sha(B/'domain.g2.test.exe')},'actual_WORK':str(work),'external_paid_model_calls':0})
print('BUILD',B,'INPUTS',len(before),'ARCHIVES',len(archives),flush=True)
