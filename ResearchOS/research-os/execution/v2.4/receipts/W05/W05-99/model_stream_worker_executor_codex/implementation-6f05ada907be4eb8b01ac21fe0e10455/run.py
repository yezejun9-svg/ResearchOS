import hashlib, json, os, pathlib, subprocess, sys, time, uuid
sys.stdout.reconfigure(encoding='utf8')
ROOT = pathlib.Path(__file__).resolve().parents[7]
MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
NODE = pathlib.Path('C:/nvm4w/nodejs/node.exe')
OUT = pathlib.Path(__file__).parent / ('run-' + uuid.uuid4().hex)
OUT.mkdir()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def vector():
    paths=[ROOT/'adapters/runtime/mu'/name for name in ('worker.mjs','worker-stream.test.mjs','worker-control.test.mjs','build.mjs','package.json')]
    paths += [MAIN/'execution/v2.4/component_lock.json', MAIN/'third_party/mu.MANIFEST.json', MAIN/'third_party/VENDORED_FROM.md', NODE, pathlib.Path(__file__)]
    paths += [MAIN/'third_party/mu/package.json', MAIN/'third_party/mu/package-lock.json']
    for base in (MAIN/'third_party/mu/packages/ai', MAIN/'third_party/mu/packages/agent', MAIN/'third_party/mu/packages/coding-agent'):
        paths += [base/'package.json']
        for folder in ('src','dist'):
            paths += [p for p in (base/folder).rglob('*') if p.is_file()]
    # Freeze installed build/runtime dependencies too, rather than assuming
    # package-lock alone proves the bytes resolved by the existing builder.
    for directory, _, names in os.walk(MAIN/'third_party/mu/node_modules'):
        paths += [pathlib.Path(directory)/name for name in names]
    return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(paths))]
def run(name,argv,env,timeout):
    began=time.time_ns(); p=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    timedout=False
    try: stdout,stderr=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timedout=True
        killed=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True)
        (OUT/(name+'.termination.stdout')).write_bytes(killed.stdout);(OUT/(name+'.termination.stderr')).write_bytes(killed.stderr)
        stdout,stderr=p.communicate(timeout=10)
    (OUT/(name+'.stdout')).write_bytes(stdout); (OUT/(name+'.stderr')).write_bytes(stderr)
    save(name+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'environment':{k:env.get(k) for k in ('RESEARCHOS_QUEUE_WORKER_BUNDLE','RESEARCHOS_STREAM_SDK_ROOT','NODE_OPTIONS')},'started_ns':began,'finished_ns':time.time_ns(),'exit_code':p.returncode,'timeout':timedout,'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()})
    print(name,p.returncode,stdout.decode('utf8','replace'),stderr.decode('utf8','replace'),flush=True)
    return p.returncode
if sha(NODE) != '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6': raise RuntimeError('locked Node drift')
before=vector();save('source.before.json',before)
for name in ('worker.mjs','worker-stream.test.mjs','worker-control.test.mjs'):
    (OUT/name).write_bytes((ROOT/'adapters/runtime/mu'/name).read_bytes())
env=dict(os.environ);env.pop('NODE_OPTIONS',None)
bundle=ROOT/'.local/model-stream/mu-worker.mjs'
env['RESEARCHOS_QUEUE_WORKER_BUNDLE']=str(bundle)
env['RESEARCHOS_STREAM_SDK_ROOT']=str(MAIN/'third_party/mu')
build=run('build',[str(NODE),'adapters/runtime/mu/build.mjs',str(bundle)],env,60)
result=build
if not build:
    (OUT/'bundle.build.json').write_bytes(pathlib.Path(str(bundle)+'.build.json').read_bytes())
    result=run('test',[str(NODE),'--test','--test-timeout=20000','adapters/runtime/mu/worker-stream.test.mjs','adapters/runtime/mu/worker-control.test.mjs'],env,45)
after=vector();save('source.after.json',after)
save('result.json',{'measurement_mode':'FIXTURE','exit_code':result,'source_drift':before!=after,'canonical_registration_executed':False,'network_provider_calls':0})
print('RECEIPT',OUT,flush=True)
sys.exit(result or (1 if before!=after else 0))
