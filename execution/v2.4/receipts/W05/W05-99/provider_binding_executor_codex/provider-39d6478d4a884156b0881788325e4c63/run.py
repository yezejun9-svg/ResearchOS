import pathlib, subprocess, os, json, hashlib, datetime, uuid, sys
ROOT=pathlib.Path(__file__).resolve().parents[7]
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
HERE=pathlib.Path(__file__).resolve().parent
GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe'
NODE=pathlib.Path('C:/nvm4w/nodejs/node.exe')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(argv,label,env):
    d=HERE/(label+'-'+uuid.uuid4().hex); d.mkdir()
    env=dict(env); env['RESEARCHOS_PROVIDER_EVIDENCE_DIR']=str(d/'native'); (d/'native').mkdir()
    doc={'argv':list(map(str,argv)),'cwd':str(ROOT),'environment':env,'start':now(),'lane':'LOCAL_FIXTURE_ONLY'}
    write(d/'invocation.json',doc)
    with (d/'stdout.raw').open('wb') as out,(d/'stderr.raw').open('wb') as err:
        p=subprocess.run(doc['argv'],cwd=ROOT,env=os.environ|env,stdout=out,stderr=err)
    doc.update(end=now(),exit=p.returncode,stdout_sha256=sha(d/'stdout.raw'),stderr_sha256=sha(d/'stderr.raw'))
    write(d/'result.json',doc); print(str(d),p.returncode,flush=True)
    return p.returncode
env={'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOCACHE':str(MAIN/'.local/gocache'),'GOPATH':str(MAIN/'.local/gopath'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_GO':str(GO),'PATH':str(NODE.parent)+';'+os.environ['PATH']}
stage=sys.argv[1]
bundle=ROOT/'.local/provider-binding'/stage/'mu-worker.mjs'
env.update(RESEARCHOS_NODE=str(NODE),RESEARCHOS_MU_BUNDLE=str(bundle),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(bundle),RESEARCHOS_STREAM_SDK_ROOT=str(MAIN/'third_party/mu'))
if stage=='baseline-cli-env-fix':
    env['RESEARCHOS_MU_BUNDLE']=str(ROOT/'.local/provider-binding/baseline/mu-worker.mjs')
    sys.exit(run([GO,'test','-json','-count=1','./apps/cli'],stage,env))
if stage=='baseline-control-name-fix':
    env['RESEARCHOS_QUEUE_WORKER_BUNDLE']=str(ROOT/'.local/provider-binding/baseline/mu-worker.mjs')
    sys.exit(run([NODE,'--test','adapters/runtime/mu/worker-control.test.mjs'],stage,env))
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
files={p:sha(ROOT/p) for p in paths if p and (p.endswith(('.go','.mjs','.sql')) or p in ['go.mod','go.sum','execution/toolchains/locked.json','execution/v2.4/component_lock.json','third_party/mu.MANIFEST.json']) and (ROOT/p).is_file()}
write(HERE/(stage+'-source.json'),{'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'files':files,'tools':{str(GO):sha(GO),str(NODE):sha(NODE)},'at':now()})
if run([NODE,'adapters/runtime/mu/build.mjs',bundle],stage+'-build',env): sys.exit(1)
if stage=='baseline':
    for args,label in [([NODE,'--test','adapters/runtime/mu/worker-queue.test.mjs','adapters/runtime/mu/worker-stream.test.mjs'],'js'),([GO,'test','-json','-count=1','-run','TestRuntimeMu|TestRuntimeClientQueueActual|TestModelStream|TestModelSSE','./internal/domain'],'domain'),([GO,'test','-json','-count=1','./apps/cli'],'cli')]:
        run(args,stage+'-'+label,env)
else:
    run([NODE,'--test','adapters/runtime/mu/worker-provider-binding.test.mjs'],stage+'-js',env)
    pattern=sys.argv[2] if len(sys.argv)>2 else 'TestProviderBinding(Config|Reasoning|Wire|Preflight|Archived)'
    run([GO,'test','-json','-count=1','-timeout=480s','-run',pattern,'./internal/domain'],stage+'-domain',env)
