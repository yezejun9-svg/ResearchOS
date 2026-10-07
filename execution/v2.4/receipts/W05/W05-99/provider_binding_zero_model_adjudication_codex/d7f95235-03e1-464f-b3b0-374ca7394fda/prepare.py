from pathlib import Path
import os,json,hashlib,subprocess,datetime,sys,shutil
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).parent;L=json.loads((O/'locations.json').read_bytes());R=Path(L['root']);W=Path(L['worktree']);A=R/'.local/worktrees/codex-w0599-provider-binding';S=json.loads((O/'scope.original.json').read_bytes());GO=R/'.local/tools/go1.27.1/go/bin/go.exe'
H=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ref(p):
 b=p.read_bytes();return {'sha256':H(b),'bytes':len(b)}
env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ['TOKEN','SECRET','API_KEY','CREDENTIAL','RESEARCHOS_'])}
env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(GO.parent.parent),GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/gocache'),GOPROXY='off',GOSUMDB='off')
def run(name,argv,cwd=W):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(list(map(str,argv)),cwd=cwd,env=env,capture_output=True)
 (O/(name+'.stdout')).write_bytes(p.stdout);(O/(name+'.stderr')).write_bytes(p.stderr)
 save(name+'.invocation.json',{'argv':list(map(str,argv)),'cwd':str(cwd),'environment':{k:env[k] for k in ['GOROOT','GOPATH','GOCACHE','GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB']},'started_at':start,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'stdout':ref(O/(name+'.stdout')),'stderr':ref(O/(name+'.stderr'))})
 if p.returncode:raise SystemExit('STOP '+name+' exit='+str(p.returncode))
 return p.stdout
originals={};(O/'frozen_originals').mkdir(exist_ok=False)
for i,(n,e) in enumerate(S['original_database_refs'].items()):
 p=A/n;assert ref(p)==e
 dest=O/'frozen_originals'/f'{i}.sqlite';shutil.copyfile(p,dest);assert ref(dest)==e
 originals[str(i)]={'original_path':str(p),'copy':str(dest),**e}
save('original_database_freeze.json',originals)
for e in S['source9']:
 assert ref(W/e['path'])['sha256']==e['sha256']
save('source9.before.json',[{'path':e['path'],**ref(W/e['path'])} for e in S['source9']])
overlay={'Replace':{str(W/'internal/domain/independent_p12_receipt_test.go'):str(O/'p12_overlay_test.go')}};save('overlay.json',overlay)
raw=run('go-list',[GO,'list','-overlay='+str(O/'overlay.json'),'-deps','-test','-json','./internal/domain'])
dec=json.JSONDecoder();txt=raw.decode('utf-8');packages=[];idx=0
while idx<len(txt):
 while idx<len(txt) and txt[idx].isspace():idx+=1
 if idx==len(txt):break
 p,idx=dec.raw_decode(txt,idx);packages.append(p)
files=set([GO,O/'prepare.py',O/'p12_overlay_test.go',O/'overlay.json',O/'scope.original.json',R/'AGENTS.md'])
for p in packages:
 d=Path(p['Dir'])
 for key in ['GoFiles','CgoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','IgnoredGoFiles','SFiles','HFiles','SysoFiles']:
  for n in p.get(key,[]):
   f=d/n
   if str(f) in overlay['Replace']:f=Path(overlay['Replace'][str(f)])
   if f.is_file():files.add(f)
 for f in d.glob('*.go'):files.add(f)
for d in ['spec','migrations','internal/domain/contracts','internal/api/contracts']:
 for f in (W/d).rglob('*'):
  if f.is_file():files.add(f)
for f in (GO.parent.parent/'pkg/tool/windows_amd64').glob('*.exe'):files.add(f)
for n in ['go.mod','go.sum']:files.add(W/n)
files.add(Path(sys.executable));files.add(Path(S['freeze']['old_bundle']['actual']['path']))
for e in S['source9']:files.add(W/e['path'])
save('inputs.before.json',{str(p):ref(p) for p in sorted(files)})
save('packages.json',[{'ImportPath':p.get('ImportPath'),'Dir':p.get('Dir')} for p in packages])
run('compile',[GO,'test','-c','-overlay='+str(O/'overlay.json'),'-o',O/'p12.test.exe','./internal/domain'])
run('buildinfo',[GO,'version','-m',O/'p12.test.exe'])
after={str(p):ref(p) for p in sorted(files)};save('inputs.after_compile.json',after)
before=json.loads((O/'inputs.before.json').read_bytes());assert before==after
save('binary.freeze.json',{'path':str(O/'p12.test.exe'),**ref(O/'p12.test.exe'),'inputs_count':len(files),'packages_count':len(packages),'source9':S['source9'],'no_case_executed':True,'models':0,'worker_starts':0})
print(json.dumps({'ready':True,'input_count':len(files),'binary':ref(O/'p12.test.exe')},ensure_ascii=False))
