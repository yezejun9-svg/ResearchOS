import pathlib,json,hashlib,subprocess,os,time,datetime
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');S=R/'.local/worktrees/bridge-checkpoint-compat-20261014';A=E.parents[1]/'bridge_checkpoint_compat_source_codex'/'20261014-current-chat';C=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp475/bridge-checkpoint-compat-source-scope.json';G=R/'.local/tools/go1.27.1/go';T=E/'fixture-temp';T.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));pins={}
def git(*args):return subprocess.check_output(['git','-C',str(S),*args])
def pin(p,want=None,size=None,copy=None):
 p=pathlib.Path(p);raw=p.read_bytes();h=sha(raw)
 if want is not None:assert h==want.removeprefix('sha256:'),(str(p),h,want)
 if size is not None:assert len(raw)==size
 pins[str(p.resolve()).lower()]={'path':str(p),'sha256':h,'bytes':len(raw)}
 if copy is not None:copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(raw)
 return raw
assert git('rev-parse','HEAD').decode().strip()=='0f9a870aed72785297a9999396fc8c760b296e13';assert git('rev-parse','HEAD^{tree}').decode().strip()=='fa071c9be7e39628c0b86ad43f77d5c50be63c7c';assert git('rev-parse','HEAD^').decode().strip()=='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';assert git('status','--porcelain')==b'';assert git('diff','--check','HEAD^','HEAD')==b''
pin(C,'b6af6ed6677b524673885a7b290022880045398b93c92420d28c620b21f25504',copy=E/'scope.json')
pin(A/'evidence-manifest.json','e6f11bbf42a5f605106720dbdfba63a5873714ee98d1d5c58cf201f8e9194d35',copy=E/'author/evidence-manifest.json')
pin(A/'report.json','046e800454d9085a0c71302a1afca221d5e57cb08a4044c60611c3748604d4da')
m=read(A/'evidence-manifest.json');assert len(m['files'])==12
for x in m['files']:pin(A/x['file'],x['sha256'],x['bytes'],copy=E/'author'/x['file'])
sm=read(A/'source-manifest.json');assert set(git('diff','--name-only','HEAD^','HEAD').decode().splitlines())==set(read(C)['paths'])
for x in sm['source']:
 raw=pin(S/x['path'],x['sha256'],x['bytes'],copy=E/'source'/x['path']);assert raw==git('show','HEAD:'+x['path'])
for x in sm['unchanged_dependencies']:
 raw=pin(S/x['path'],x['working_file_sha256'],copy=E/'dependencies'/x['path']);assert raw==git('show','HEAD:'+x['path'])==git('show','HEAD^:'+x['path'])
for x in sm['native_assets']:pin(x['path'],x['sha256'],x['bytes'])
for name in ['AGENTS.md','adapters/runtime/bridge_windows.go','internal/domain/runtime_coordinator_windows.go','ops/experiment_sandbox/sandbox_windows.go','ops/experiment_sandbox/async_windows.go']:
 pin(S/name,copy=E/'dependencies'/name)
(E/'source.patch').write_bytes(git('diff','--binary','HEAD^','HEAD'));assert (E/'source.patch').read_bytes()==(A/'source.patch').read_bytes()
env=os.environ.copy();env.update(GOROOT=str(G),GOMODCACHE=str(R/'.local/tools/gopath/pkg/mod'),GOCACHE=str(R/'.local/go-cache/mu-m1-core-20261014'),GOTMPDIR=str(T),TEMP=str(T),TMP=str(T),GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOWORK='off')
def run(name,args,timeout=300):
 start=time.time()
 with (E/(name+'.stdout.raw')).open('xb') as out,(E/(name+'.stderr.raw')).open('xb') as err:p=subprocess.run([str(G/'bin/go.exe'),*args],cwd=S,env=env,stdout=out,stderr=err,timeout=timeout)
 result={'argv':[str(G/'bin/go.exe'),*args],'cwd':str(S),'started':datetime.datetime.fromtimestamp(start,datetime.timezone.utc).isoformat(),'seconds':time.time()-start,'native_exit':p.returncode,'environment':{k:env[k] for k in ['GOROOT','GOMODCACHE','GOCACHE','GOTMPDIR','TEMP','TMP','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOWORK']}};(E/(name+'.process.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');assert p.returncode==0,result
run('compiler-list',['list','-mod=readonly','-deps','-test','-json','./adapters/runtime','./internal/domain'])
raw=(E/'compiler-list.stdout.raw').read_text(encoding='utf8');decoder=json.JSONDecoder();offset=0;packages=[]
while raw[offset:].strip():
 offset+=len(raw[offset:])-len(raw[offset:].lstrip());p,offset=decoder.raw_decode(raw,offset);packages.append(p)
for p in packages:
 for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles','TestGoFiles','XTestGoFiles','TestEmbedFiles','XTestEmbedFiles']:
  for name in p.get(key,[]):
   path=pathlib.Path(p['Dir'])/name
   if path.is_file():pin(path)
for p in [S/'go.mod',S/'go.sum',G/'bin/go.exe',*sorted((G/'pkg/tool/windows_amd64').glob('*.exe'))]:pin(p)
(E/'inputs.before.json').write_text(json.dumps(list(pins.values()),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Observe original native test at its existing checkpoints only; all original assertions remain intact.
source=(S/'adapters/runtime/bridge_control_windows_test.go').read_text(encoding='utf8')
source=source.replace('t.Logf("NATIVE_SYNTHETIC production worker+bridge,','reviewCaptureBridge(t, "pause", w.Directory())\n\tt.Logf("NATIVE_SYNTHETIC production worker+bridge,').replace('t.Logf("NATIVE_SYNTHETIC same Run epoch 1 -> 2,','reviewCaptureBridge(t, "resume", w2.Directory())\n\tt.Logf("NATIVE_SYNTHETIC same Run epoch 1 -> 2,')
assert source.count('reviewCaptureBridge(t,')==2
capture_dir=E/'native-capture'
source+='\nfunc reviewCaptureBridge(t *testing.T, label, directory string) {\n t.Helper()\n target := filepath.Join('+json.dumps(str(capture_dir))+', label)\n if e := os.MkdirAll(target,0700); e != nil {t.Fatal(e)}\n names := []string{"bridge.json","stdout.raw","stderr.raw","input/request.json","checkpoint.sealed.json","output/result.json"}\n extra,_ := filepath.Glob(filepath.Join(directory,"checkpoint-*.json"));for _,p := range extra {names=append(names,filepath.Base(p))}\n for _,name := range names {raw,e := os.ReadFile(filepath.Join(directory,filepath.FromSlash(name)));if os.IsNotExist(e) {continue};if e != nil {t.Fatal(e)};out:=filepath.Join(target,filepath.FromSlash(name));if e=os.MkdirAll(filepath.Dir(out),0700);e!=nil {t.Fatal(e)};if e=os.WriteFile(out,raw,0600);e!=nil {t.Fatal(e)}}\n}\n'
overlayFile=E/'bridge_control_observation_windows_test.go';overlayFile.write_text(source,encoding='utf8');overlay={'Replace':{str(S/'adapters/runtime/bridge_control_windows_test.go'):str(overlayFile)}};(E/'native-observation-overlay.json').write_text(json.dumps(overlay,ensure_ascii=False,indent=2),encoding='utf8')
assets=sm['native_assets'];run('fresh-runtime',['test','-mod=readonly','-overlay',str(E/'native-observation-overlay.json'),'-json','./adapters/runtime','-run','^(TestBridgeCheckpoint|TestPauseCheckpointFile|TestBridgeControlIdentityRejectsForeignProcessAndEpoch|TestBridgeProductionPauseCheckpointNative)$','-count=1','-timeout=4m','-pause-worker-node',assets[0]['path'],'-pause-worker-bundle',assets[1]['path']])
run('fresh-legacy-core',['test','-mod=readonly','-json','./internal/domain','-run','^TestRuntimeCoordinatorCheckpoint(Resume|CrashRecovery)$','-count=1','-timeout=4m'])
for x in pins.values():assert sha(pathlib.Path(x['path']).read_bytes())==x['sha256']
assert git('status','--porcelain')==b'';(E/'git-status.after.raw').write_bytes(git('status','--short'))
print(json.dumps({'input_files':len(pins),'compiler_packages':len(packages),'runtime_exit':0,'legacy_exit':0,'author_artifacts':12},ensure_ascii=True))
