from pathlib import Path
import hashlib,json,os,subprocess,sys,datetime
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-native-create-core-20261104')
AUTHOR=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/core/author')
scope=json.loads((AUTHOR.parent/'scope.json').read_text(encoding='utf-8-sig'))
lock=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))
go=Path(lock['tools']['go']['path']);assert hashlib.sha256(go.read_bytes()).hexdigest()==lock['tools']['go']['sha256']
git=Path(lock['tools']['git']['path']);assert hashlib.sha256(git.read_bytes()).hexdigest()==lock['tools']['git']['sha256']
out=AUTHOR/sys.argv[1];out.mkdir(exist_ok=False)
mode=sys.argv[2]
private=HERE/'runtime'
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('RESEARCHOS_','MU_'))}
settings={'GOCACHE':str(private/'cache'),'GOPATH':str(private/'gopath'),'GOTMPDIR':str(private/'tmp'),'TMP':str(private/'tmp'),'TEMP':str(private/'tmp'),'USERPROFILE':str(private/'profile'),'APPDATA':str(private/'profile/roaming'),'LOCALAPPDATA':str(private/'profile/local'),'GOMODCACHE':'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod','GOTOOLCHAIN':'local','GOENV':'off','GOWORK':'off','GOTELEMETRY':'off','GOPROXY':'off','GOSUMDB':'off','CGO_ENABLED':'0','GOMAXPROCS':'2','GOFLAGS':'-mod=readonly -p=1 -buildvcs=false'}
for k in ['GOCACHE','GOPATH','GOTMPDIR','TMP','USERPROFILE','APPDATA','LOCALAPPDATA']:Path(settings[k]).mkdir(parents=True,exist_ok=True)
env.update(settings)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):
 with (out/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
names=scope['production_paths']+scope['test_paths']
save('input.json',{'scope':scope['scope_id'],'mode':mode,'cwd':str(ROOT),'env_overrides':settings,'tools':{'go':lock['tools']['go'],'gofmt_sha256':sha(go.with_name('gofmt.exe'))},'source':{n:sha(ROOT/n) if (ROOT/n).exists() else 'ABSENT' for n in names}})
gofiles=[n for n in names if n.endswith('.go') and (ROOT/n).exists()]
commands=[('format',[str(go.with_name('gofmt.exe')),'-w',*gofiles])]
if mode=='compile':commands.append(('compile',[str(go),'test','./internal/domain','./internal/host','./internal/api','./apps/control','-run','^$','-count=1','-timeout=60s','-json']))
elif mode=='focused':commands.append(('focused',[str(go),'test','./internal/domain','./internal/host','./internal/api','-run','^(TestNativeCreate|TestNativeWriterOrigin|TestNativeOrigin|TestPreparedNativeOrigin)','-count=1','-timeout=90s','-json']))
elif mode=='domain-focused':commands.append(('domain-focused',[str(go),'test','./internal/domain','-run','^(TestNativeWriterOrigin|TestNativeOrigin|TestPreparedNativeOrigin)','-count=1','-timeout=90s','-json']))
elif mode=='regression':commands.append(('regression',[str(go),'test','./internal/domain','./internal/api','./internal/host','-run','^(TestCommandAuthContext.*|TestCommandAuthHTTP.*|TestNativePeerCapability.*|TestHostBootEntropyFailurePrecedesMutableInitialization|TestClientTypedRejectionRollsBackBusinessWrites|TestAttachGrantFaultRollsBackEpochAndIdentity|TestW14SessionHTTPCreateSendEventsAndReplay|TestW14SessionWriterLeaseHandoff|TestAttachHTTPRawReplayAndDefaultLease)$','-count=1','-timeout=90s','-json']))
else:raise ValueError(mode)
commands += [('diff-check',[str(git),'-c','gc.auto=0','-c','maintenance.auto=false','diff','--check']),('scope-status',[str(git),'-c','gc.auto=0','-c','maintenance.auto=false','status','--short','--untracked-files=all'])]
results=[]
for name,argv in commands:
 print(json.dumps({'phase':name,'status':'STARTED'}),flush=True)
 try:r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,timeout=300);code,stdout,stderr=r.returncode,r.stdout,r.stderr
 except subprocess.TimeoutExpired as e:code,stdout,stderr=124,e.stdout or b'',e.stderr or b''
 (out/(name+'.stdout.raw')).write_bytes(stdout);(out/(name+'.stderr.raw')).write_bytes(stderr)
 row={'phase':name,'argv':argv,'cwd':str(ROOT),'exit_code':code,'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest(),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save(name+'.command.json',row);results.append(row)
 print(json.dumps({'phase':name,'exit_code':code,'stderr_preview':stderr.decode('utf-8',errors='replace')[:1400]}),flush=True)
 if name=='format' and code:break
save('results.json',{'status':'DEVELOPMENT_CHECKS_PASS' if all(r['exit_code']==0 for r in results) else 'DEVELOPMENT_CHECKS_FAILED','commands':results,'sources':{n:sha(ROOT/n) if (ROOT/n).exists() else 'ABSENT' for n in names},'formal_increment':0})
sys.exit(0 if all(r['exit_code']==0 for r in results) else 1)
