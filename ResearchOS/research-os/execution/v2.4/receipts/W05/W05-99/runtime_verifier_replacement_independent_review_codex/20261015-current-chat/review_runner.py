import pathlib, subprocess, os, sys, json, hashlib, datetime
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/verifier-replacement-20261014'
E=pathlib.Path(__file__).resolve().parent
OLD=E.parent/'20261014-current-chat'
A=R/'execution/v2.4/receipts/W05/W05-99/runtime_verifier_replacement_source_codex/20261014-current-chat/revision01'
G=R/'.local/tools/go1.27.1/go/bin/go.exe'
T=R/'.local/tmp/vr-independent-20261015'
def pin(p):
 b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(name,obj):
 with (E/name).open('x',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
def git(*args):
 return subprocess.check_output(['git','--no-optional-locks','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd=W)
def guards():
 paths=[W/os.fsdecode(p) for p in git('ls-files','-z').split(b'\0') if p]
 paths=[p for p in paths if p.is_file()]
 paths += [p for p in OLD.rglob('*') if p.is_file()]
 paths += [p for p in A.rglob('*') if p.is_file()]
 return [pin(p) for p in sorted(set(paths))]
if sys.argv[1]=='baseline':
 assert git('rev-parse','HEAD').strip()==b'4f4023c956f84d65743f39ce77d6c8899a21ada1'
 assert git('rev-parse','HEAD^{tree}').strip()==b'3db13a15cc52b2b0bd75cae3452c66509a9f55c9'
 assert not git('status','--porcelain')
 m=json.loads((A/'12-FINAL-manifest.json').read_text(encoding='utf-8-sig'))
 checked=[]
 def walk(v):
  if isinstance(v,dict):
   if set(['path','sha256','bytes'])<=v.keys():
    q=pin(pathlib.Path(v['path'])); assert q==v,(q,v); checked.append(q)
   else:
    for x in v.values():walk(x)
  elif isinstance(v,list):
   for x in v:walk(x)
 walk(m)
 assert pin(A/'12-FINAL-manifest.json')['sha256']=='b3928cb7289d207b20e3f140ddfb12221fa7a2a6bfc01af269ed126a2e695c78'
 rev=git('diff','--binary','--full-index','c5ea30829800a75badc07cfc25b01c0822e787c9','HEAD','--')
 assert rev==(A/'12-revision.patch').read_bytes()
 cumulative=git('diff','--binary','--full-index','c8b7adab9f0c15eb33f235f8d0d9eb205794e376','HEAD','--')
 assert cumulative==(A/'12-exact8.patch').read_bytes()
 save('inputs.before.json',guards())
 save('manifest-verification.json',{'checked':checked,'revision':pin(A/'12-revision.patch'),'cumulative':pin(A/'12-exact8.patch'),'head':git('rev-parse','HEAD').decode().strip(),'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'status':git('status','--porcelain').decode(),'actual_model':'gpt-6-astra','reasoning_effort':'high','formal_increment':0})
 probe=OLD/'independent_probe_windows_test.go'
 save('overlay.json',{'Replace':{str(W/'internal/host/revision_review_probe_windows_test.go'):str(probe)}})
 print('baseline verified',len(checked),'manifest refs');sys.exit(0)
if sys.argv[1]=='after':
 before=json.loads((E/'inputs.before.json').read_text(encoding='utf-8'))
 after=guards(); save('inputs.after.json',after); assert before==after
 assert not git('status','--porcelain')
 print('all source and historical evidence guards unchanged',len(after));sys.exit(0)
T.mkdir(parents=True,exist_ok=True)
label=sys.argv[1];argv=[str(G)]+sys.argv[2:]
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','HOMEDRIVE','HOMEPATH'}}
env.update(TEMP=str(T),TMP=str(T),GOCACHE=str(R/'.local/go-cache/verifier-replacement-20261014'),GOMODCACHE=str(R/'.local/tools/gopath/pkg/mod'),GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off',GOFLAGS='-buildvcs=true')
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
log=E/(label+'.log')
with log.open('xb') as f: result=subprocess.run(argv,cwd=W,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
record={'label':label,'argv':argv,'cwd':str(W),'environment_allowlist':env,'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':result.returncode,'log':pin(log)}
save(label+'.json',record)
with (E/'attempt-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
print(json.dumps(record['log'],ensure_ascii=False));print(log.read_text(encoding='utf-8',errors='replace')[-2000:]);sys.exit(result.returncode)
