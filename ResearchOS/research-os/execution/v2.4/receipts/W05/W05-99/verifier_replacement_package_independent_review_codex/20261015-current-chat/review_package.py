import pathlib, os, subprocess, json, hashlib, datetime, sys
R=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
W=R/'.local/worktrees/verifier-replacement-20261014'
E=pathlib.Path(__file__).resolve().parent
A=R/'execution/v2.4/receipts/W05/W05-99/verifier_replacement_package_codex/20261015-current-chat'
P=pathlib.Path(r'C:\Users\yqyyds\.codex\researchos-resource-cache\normal-verifier-replacement-4f4023-20261015')
B=P.parent/'normal-coding-profile-c8b7adab-20261014'
G=R/'.local/tools/go1.27.1/go/bin/go.exe'
T=R/'.local/tmp/vr-package-independent-20261015'
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp491/verifier-normal-package-scope.json'
def pin(p):
 raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(n,v):
 with (E/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(cwd,*args):return subprocess.check_output(['git','--no-optional-locks','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd=cwd)
def inventory(root):return {p.relative_to(root).as_posix():pin(p) for p in sorted(root.rglob('*')) if p.is_file()}
def sourceguards():return [pin(W/os.fsdecode(p)) for p in git(W,'ls-files','-z').split(b'\0') if p and (W/os.fsdecode(p)).is_file()]
def checkref(v):
 q=pathlib.Path(v['path']);q=q if q.is_absolute() else R/q
 got=pin(q);assert got['sha256']==v['sha256'] and got['bytes']==v['bytes'],(got,v)
 return got
if sys.argv[1]=='baseline':
 assert pin(S)['sha256']=='491def288f03df983b227f1b647f74f77a98362187c9dc99f444d6fdc34dd4ad'
 assert pin(A/'FINAL-manifest.json')['sha256']=='97e828ce312b7ddcf76c2cef32b5c4848c860e85208bdc99bc18e1c101865396'
 assert pin(A/'SUPPLEMENT-manifest.json')['sha256'].startswith('a1ecd71f')
 for repo in [R,W]:
  assert git(repo,'rev-parse','HEAD').strip()==b'4f4023c956f84d65743f39ce77d6c8899a21ada1'
  assert git(repo,'rev-parse','HEAD^{tree}').strip()==b'3db13a15cc52b2b0bd75cae3452c66509a9f55c9'
 assert not git(W,'status','--porcelain')
 declared=read(A/'package-inventory.json');now=inventory(P);old=inventory(B)
 assert len(now)==58 and set(now)==set(old)=={x['path'] for x in declared['files']}
 for f in declared['files']:
  actual=now[f['path']];assert actual['sha256']==f['sha256'] and actual['bytes']==f['bytes']
  raw=(P/f['path']).read_bytes()
  if 'line_endings' in f:assert f['line_endings']=={'crlf':raw.count(b'\r\n'),'lf':raw.count(b'\n'),'nul':raw.count(b'\0')}
 changed=[p for p in now if now[p]['sha256']!=old[p]['sha256']]
 assert sorted(changed)==sorted(['apps/desktop/resources/control/researchos-control.exe','apps/desktop/resources/control/runtime-verifier.exe','apps/desktop/resources/control/runtime-verifier-installation.json'])
 assert sorted(declared['unchanged_paths'])==sorted(set(now)-set(changed))
 m=read(P/'apps/desktop/resources/control/runtime-verifier-installation.json');previous=read(B/'apps/desktop/resources/control/runtime-verifier-installation.json')
 assert m['executable']==str(P/'apps/desktop/resources/control/runtime-verifier.exe')
 assert m['executable_hash']=='sha256:'+now['apps/desktop/resources/control/runtime-verifier.exe']['sha256']
 assert m['source_commit']=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
 allowed={'executable','executable_hash','source_commit'}
 assert {k:v for k,v in m.items() if k not in allowed}=={k:v for k,v in previous.items() if k not in allowed}
 fm=read(A/'FINAL-manifest.json');refs=[]
 for f in fm['evidence_files']:
  got=pin(A/f['relative_path']);assert got['sha256']==f['sha256'] and got['bytes']==f['bytes'];refs.append(got)
 for obj in [fm,read(A/'SUPPLEMENT-manifest.json'),read(A/'native-source-read.json'),read(A/'composition.json'),read(S)]:
  for v in obj.values():
   if isinstance(v,dict) and {'path','sha256','bytes'}<=v.keys():refs.append(checkref(v))
 assert len(fm['evidence_files'])==fm['evidence_file_count']==2231
 wire=read(A/'package-wire-summary.json');assert wire['counts']=={'tests':214,'pass':214,'fail':0,'skipped':0,'cancelled':0};checkref(wire['source_test'])
 save('01-baseline.json',{'scope':pin(S),'author_final':pin(A/'FINAL-manifest.json'),'author_supplement':pin(A/'SUPPLEMENT-manifest.json'),'new_inventory':now,'old_inventory':old,'changed':changed,'unchanged':55,'source_guards':sourceguards(),'checked_author_refs':refs,'go':pin(G),'formal_increment':0})
 save('reviewer-diagnostics.json',{'preserved_read_only_diagnostics':['First scope lookup used 20261014 parent; corrected to canonical 20261015 path from composition.','Literal wildcard mu* passed as rg path; corrected with rg -g.','Sparse worktree does not materialize Desktop main/lib/host.js; inspected packaged immutable Desktop files.','Guessed apps/runtimeverifier/main.go absent; rg located apps/runtime-verifier/main_windows.go.'],'test_attempts_failed':0,'source_or_package_writes':False})
 save('overlay.json',{'Replace':{str(W/'internal/host/independent_package_read_windows_test.go'):str(E/'package_probe_windows_test.go')}})
 print('baseline verified:58 members,55 unchanged,2231 author evidence files; source clean');sys.exit(0)
if sys.argv[1]=='after':
 b=read(E/'01-baseline.json');assert b['new_inventory']==inventory(P);assert b['old_inventory']==inventory(B);assert b['source_guards']==sourceguards()
 for ref in b['checked_author_refs']:checkref(ref)
 assert not git(W,'status','--porcelain')
 save('07-guards-after.json',{'new_inventory':inventory(P),'old_inventory':inventory(B),'source_guards_unchanged':len(b['source_guards']),'author_refs_unchanged':len(b['checked_author_refs']),'source_status':git(W,'status','--porcelain').decode(),'product_access':False,'formal_increment':0});print('all guards unchanged');sys.exit(0)
T.mkdir(parents=True,exist_ok=True)
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','HOMEDRIVE','HOMEPATH'}}
env.update(TEMP=str(T),TMP=str(T),GOCACHE=str(R/'.local/go-cache/verifier-replacement-20261014'),GOMODCACHE=str(R/'.local/tools/gopath/pkg/mod'),GOTOOLCHAIN='local',GOENV='off',GOPROXY='off',GOSUMDB='off',GOFLAGS='-buildvcs=true',REVIEW_PACKAGE_ROOT=str(P))
label=sys.argv[1];argv=sys.argv[2:];cwd=W
if argv[0]=='GO':argv[0]=str(G)
else:cwd=T;env={k:v for k,v in env.items() if k.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP'}}
record={'label':label,'argv':argv,'cwd':str(cwd),'environment_allowlist':env,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (E/(label+'.stdout')).open('xb') as out,(E/(label+'.stderr')).open('xb') as err:
 result=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
record.update(native_exit=result.returncode,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout=pin(E/(label+'.stdout')),stderr=pin(E/(label+'.stderr')))
save(label+'.json',record)
with (E/'attempt-ledger.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
print(json.dumps({'label':label,'exit':result.returncode},ensure_ascii=False));print((E/(label+'.stdout')).read_text(encoding='utf-8',errors='replace')[-3000:]);print((E/(label+'.stderr')).read_text(encoding='utf-8',errors='replace')[-500:])
