import pathlib,json,hashlib,subprocess,os,time,datetime
E=pathlib.Path(__file__).parent;OLD=E.parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');S=R/'.local/worktrees/schema24-to25-native-20261014';A=R/'execution/v2.4/receipts/W17/W17-03/schema24_to25_source_codex/20261014-current-chat/revision01';G=R/'.local/tools/go1.27.1/go';T=E/'fixture-temp';T.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));pins={};occurrences=0
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
def pin(p,want=None,size=None,copy=None):
 global occurrences
 p=pathlib.Path(p);raw=p.read_bytes();h=sha(raw)
 if want is not None:assert h==want.removeprefix('sha256:'),(str(p),h,want)
 if size is not None:assert len(raw)==size
 pins[str(p.resolve()).lower()]={'path':str(p),'sha256':h,'bytes':len(raw)};occurrences+=1
 if copy is not None:copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(raw)
 return raw
assert git('rev-parse','HEAD').decode().strip()=='f80955594bdd0373ae1c961cd02ab6be96f2c196';assert git('rev-parse','HEAD^{tree}').decode().strip()=='5bce20214223e8292f16a117a83407f52b4bca4a';assert git('rev-parse','HEAD^').decode().strip()=='1b5ec5d049db7811f6e0d8b143659ea5e2f0836b';assert git('status','--porcelain')==b'';assert git('diff','--check','HEAD^','HEAD')==b''
pin(A/'scope.json','e1447f6b0dd535e16d125adab931a871194c764989d0cc037f50a951a59fcf23',copy=E/'scope.json');pin(A/'SOURCE_REPORT.md','45f2d6a8e931c8c2c2b03ba9d3568ed3af596a65de2dbfec6c0242562d9fd1e1',copy=E/'author-SOURCE_REPORT.md');pin(A/'manifest.json','678eb7697a703cae67a65275507c507ca73c7d07647bfece7e825be7d2bf2686',copy=E/'author-manifest.json')
pin(OLD/'REVIEW.md','1d7e0e4cd2d06c934a4fec21bf7c01ecfccf9d9c320e1bd2b293dd5b3aece392');pin(OLD/'FINAL-report.json','2311db0e64309ebbd6d421464544adea5b3b47b8e260f85d9183036533f17117')
m=read(A/'manifest.json');assert len(m['artifacts'])==109
for x in m['artifacts']:pin(x['path'],x['sha256'],x['bytes'])
old=read(A.parent/'manifest.json');assert len(old['artifacts'])==274
pin(A.parent/'manifest.json','00ff8811feefb3ef2c515470a4b6ed4a6438dc540594d0a743ebba7e265717ff');pin(A.parent/'SOURCE_REPORT.md','91570238b80db2037d15b6b33862ffc7f39d345179ce6443e34ea742f688f4dc')
for x in old['artifacts']:pin(x['path'],x['sha256'],x['bytes'])
scope=read(A/'scope.json');changed=git('diff','--name-only','HEAD^','HEAD').decode().splitlines();assert len(changed)==6 and set(changed)==set(scope['paths']);combined=git('diff','--name-only','60f8c81a7529081eb51d525ab913d63102148a46','HEAD').decode().splitlines();assert len(combined)==22
for name in changed:
 raw=pin(S/name,copy=E/'source'/name);assert raw==git('show','HEAD:'+name)
for x in read(A/'final-freeze/readonly-guards.json'):
 pin(x['path'],x['sha256'],x['bytes']);assert (S/x['relative']).read_bytes()==git('show','HEAD^:'+x['relative'])
for name in set(combined)-set(changed):assert (S/name).read_bytes()==(OLD/'source-snapshot'/name).read_bytes()
(E/'revision.patch').write_bytes(git('diff','--binary','HEAD^','HEAD'));assert (E/'revision.patch').read_bytes()==(A/'final-freeze/source.patch').read_bytes()
cp=read(A/'target25-r4-build-inputs/compiler-inputs.json')
for x in cp['inputs']:pin(x['path'],x['sha256'],x['bytes'])
for x in read(A/'target25-r4-build-inputs/programs.json'):pin(x['path'],x['sha256'],x['bytes'])
config=read(A/'public-handoff04.config.json')
for key,x in config.items():
 if isinstance(x,dict) and {'path','sha256','bytes'}<=x.keys():pin(x['path'],x['sha256'],x['bytes'])
(E/'inputs.before.json').write_text(json.dumps(list(pins.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
env=os.environ.copy();env.update(GOROOT=str(G),GOMODCACHE=str(R/'.local/tools/gopath/pkg/mod'),GOCACHE=str(R/'.local/go-cache/mu-m1-core-20261014'),GOTMPDIR=str(T),TEMP=str(T),TMP=str(T),GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOWORK='off');env.pop('RESEARCHOS_NATIVE_PAUSE_MIGRATION_HARNESS_CONFIG',None)
argv=[str(G/'bin/go.exe'),'test','-mod=readonly','-json','./internal/domain','./internal/recoveryauthority','./apps/control','./ops/backup','./ops/supervisor/recovery_root','./ops/supervisor/recovery_enrollment','-run','TestPause|TestPreparedUpgrade|TestPreparedHandoff|TestBackupHostConfiguration|TestAuthority','-count=1','-timeout=10m'];start=time.time()
with (E/'fresh-regression.stdout.raw').open('xb') as out,(E/'fresh-regression.stderr.raw').open('xb') as err:p=subprocess.run(argv,cwd=S,env=env,stdout=out,stderr=err,timeout=660)
r={'argv':argv,'cwd':str(S),'native_exit':p.returncode,'seconds':time.time()-start,'environment':{k:env[k] for k in ['GOROOT','GOMODCACHE','GOCACHE','GOTMPDIR','TEMP','TMP','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOWORK']},'native_harness_config':'UNSET'};(E/'fresh-regression.process.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');assert p.returncode==0,r
print(json.dumps({'input_files':len(pins),'pin_occurrences':occurrences,'fresh_native_exit':p.returncode,'seconds':r['seconds'],'revised_files':len(changed),'combined_scope':len(combined)}))
