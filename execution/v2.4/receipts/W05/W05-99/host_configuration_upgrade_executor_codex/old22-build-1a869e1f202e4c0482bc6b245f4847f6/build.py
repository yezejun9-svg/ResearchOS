import os,sys,json,subprocess,hashlib,tarfile,io,datetime
from pathlib import Path
out=Path(__file__).resolve().parent;wt=out.parents[6];main=Path('D:/作品集/ResearchOS/research-os');root=out/'frozen_source';root.mkdir()
commit='396287cc5427eb125aaedb8a2b7fadf63e6b9322';go=main/'.local/tools/go1.27.1/go';env=os.environ.copy();env.update(GOROOT=str(go),GOTOOLCHAIN='local',GOENV='off',GOPATH=str(main/'.local/gopath'),GOCACHE=str(main/'.local/gocache'),GOPROXY='off',GOSUMDB='off')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):(out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def invoke(name,argv,cwd):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True);(out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr);save(name+'.invocation.json',dict(actualargv=argv,cwd=str(cwd),exit=p.returncode,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat()));return p
paths=['go.mod','go.sum','internal','adapters','apps/control','ops/backup','migrations','spec/v2.0/contracts']
a=invoke('git-archive',['git','archive','--format=tar',commit,*paths],main);assert a.returncode==0
with tarfile.open(fileobj=io.BytesIO(a.stdout),mode='r:') as tar:
 for member in tar:
  assert member.isfile() or member.isdir();p=root/member.name;assert p.resolve().is_relative_to(root.resolve())
  if member.isdir():p.mkdir(parents=True,exist_ok=True)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tar.extractfile(member).read())
assert len(list((root/'migrations/sqlite').glob('0*.sql')))==22
original={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()};save('git_source.json',dict(commit=commit,archive_sha256=hashlib.sha256(a.stdout).hexdigest(),files=original))
r=invoke('go-list',[str(go/'bin/go.exe'),'list','-deps','-json','./apps/control','./ops/backup'],root);assert r.returncode==0
text=r.stdout.decode();dec=json.JSONDecoder();inputs=set(root.rglob('*.go'))
while text.strip():
 text=text.lstrip();pkg,end=dec.raw_decode(text);text=text[end:];d=Path(pkg['Dir']) if pkg.get('Dir') else None
 if not d:continue
 inputs.update(d.glob('*.go'))
 for key in ['EmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles']:
  inputs.update(d/name for name in pkg.get(key,[]))
 if pkg.get('Module',{}).get('GoMod'):inputs.add(Path(pkg['Module']['GoMod']))
inputs.update(root.rglob('*.json'));inputs.update(root.rglob('*.sql'));inputs.update([root/'go.mod',root/'go.sum',go/'bin/go.exe']);inputs.update(p for p in (go/'pkg/tool').rglob('*') if p.is_file())
def vector():return {str(p):sha(p) for p in sorted(inputs) if p.is_file()}
before=vector();save('source_before.json',before);save('environment.json',{k:env[k] for k in ['GOROOT','GOTOOLCHAIN','GOENV','GOPATH','GOCACHE','GOPROXY','GOSUMDB']})
for package,name in [('./apps/control','old22-control.exe'),('./ops/backup','old22-backup.exe')]:
 r=invoke(name+'.build',[str(go/'bin/go.exe'),'build','-buildvcs=false','-o',str(out/name),package],root)
 if r.returncode:print(str(out));sys.exit(r.returncode)
after=vector();save('source_after.json',after);assert before==after;assert original=={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
save('result.json',dict(status='SOURCE22_BINARY_BUILD_ONLY_NOT_LIVE',commit=commit,source_drift=False,input_count=len(before),programs={name:sha(out/name) for name in ['old22-control.exe','old22-backup.exe']}));print(out);print((out/'result.json').read_text())
