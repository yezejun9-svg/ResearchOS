import pathlib,subprocess,os,json,datetime
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[6];WT=ROOT/'.local/worktrees/w05-normal-runtime-host-20261012'
ASSETS=ROOT/'.local/builds/current-chat-runtime-assets-20261012';GO=ROOT/'.local/tools/go1.27.1/go/bin/go.exe'
env=dict(os.environ)
for name in ['go-cache','go-tmp','test-temp']:(OUT/'cache'/name).mkdir(parents=True,exist_ok=True)
settings={'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOPATH':str(ROOT/'.local/tools/gopath'),'GOMODCACHE':str(ROOT/'.local/tools/gopath/pkg/mod'),'GOCACHE':str(OUT/'cache/go-cache'),'GOTMPDIR':str(OUT/'cache/go-tmp'),'TEMP':str(OUT/'cache/test-temp'),'TMP':str(OUT/'cache/test-temp'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_MU_BUNDLE':str(ASSETS/'mu-worker.mjs'),'PATH':str(ASSETS)+os.pathsep+env.get('PATH','')}
env.update(settings)
cases=[('domain',['./internal/domain','-run','^(TestLocalRuntimeSetup.*|TestHandlerRuntimeStored(Local)?ProfileExactMapping|TestRuntimeMuUnknownNeverRetries|TestRuntimeMuLocalModelDoesNotForwardSDKOrBrokerHeaders|TestRuntimeCoordinatorPurposeRevocation|TestRuntimeCoordinatorTypedBroker)$']),('host',['./internal/host','-run','^TestLocalRuntime(Assets.*|Host.*)$','-args','-local-runtime-assets-dir='+str(ASSETS)])]
for name,args in cases:
 argv=[str(GO),'test','-mod=readonly','-count=1','-json','-timeout=180s']+args;start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 result=subprocess.run(argv,cwd=WT,env=env,capture_output=True,timeout=240)
 (OUT/(name+'.stdout')).write_bytes(result.stdout);(OUT/(name+'.stderr')).write_bytes(result.stderr)
 (OUT/(name+'.invocation.json')).write_text(json.dumps({'argv':argv,'cwd':str(WT),'started':start,'ended':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':result.returncode,'environment':settings,'real_model_calls':0},indent=2)+'\n',encoding='utf-8')
 events=[]
 for line in result.stdout.splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 terminal=[{k:e[k] for k in ['Action','Package','Test','Elapsed'] if k in e} for e in events if e.get('Action') in ['pass','fail','skip']]
 (OUT/(name+'.summary.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8');print(json.dumps({'case':name,'exit':result.returncode,'terminal':terminal}),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
