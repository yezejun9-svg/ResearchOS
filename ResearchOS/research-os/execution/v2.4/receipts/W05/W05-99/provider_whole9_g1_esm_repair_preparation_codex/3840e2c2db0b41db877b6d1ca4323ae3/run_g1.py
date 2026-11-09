"""UNEXECUTED Root-only G1 candidate driver. No source writes or SDK compilation.
Review this source and register exact authorization before invoking --execute.
"""
import argparse, datetime, hashlib, json, os, pathlib, queue, re, subprocess, threading, time, traceback
P = pathlib.Path(__file__).resolve().parent
L = json.loads((P/'layout.json').read_bytes())
M = pathlib.Path(L['sdk_shared']).parents[1]
W = pathlib.Path(L['candidate'])
SDK = pathlib.Path(L['sdk_shared'])
WORK = pathlib.Path(L['future_work_dir'])
OUT = pathlib.Path(L['future_receipt_dir'])
GO3 = ['TestProviderBindingConfigAndBody','TestProviderBindingReasoningExactHistory','TestProviderBindingWireSignatureWhitespaceAndBlocks']
JS3 = ['worker-provider-binding.test.mjs','worker-stream.test.mjs','worker-control.test.mjs']
protected = []

def digest(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,v):
    b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    with (OUT/n).open('xb') as f: f.write(b)
def check(ok,why):
    if not ok: raise RuntimeError(why)
def vector(paths):
    return {str(p):{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(set(paths)) if p.is_file()}
def tree(root):
    # Do not follow aliases recursively; record them separately. Main Mu aliases
    # all resolve inside the explicitly hashed packages tree.
    out=[]
    for current,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if d!='.git' and not pathlib.Path(current,d).is_junction()]
        out.extend(pathlib.Path(current,f) for f in files)
    return out

def command(name,argv,cwd,limit,mode=None):
    start=now(); q=queue.Queue(); seen=[]; forced=None
    with (OUT/(name+'.stdout.raw')).open('xb') as so,(OUT/(name+'.stderr.raw')).open('xb') as se:
        proc=subprocess.Popen(argv,cwd=cwd,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        def read(stream,target,isout):
            for line in iter(stream.readline,b''):
                target.write(line);target.flush()
                if isout:q.put(line)
            stream.close()
        threads=[threading.Thread(target=read,args=(proc.stdout,so,True)),threading.Thread(target=read,args=(proc.stderr,se,False))]
        for t in threads:t.start()
        deadline=time.monotonic()+limit
        while proc.poll() is None:
            try:line=q.get(timeout=.05)
            except queue.Empty:line=b''
            if mode=='go' and line:
                try:
                    event=json.loads(line);seen.append(event)
                    if event.get('Action') in ('fail','skip'):forced='first unexpected Go '+event['Action']
                except (ValueError,TypeError):forced='invalid test2json event'
            if mode=='node' and (re.match(rb'\s*not ok\b',line) or re.search(rb'#\s*(SKIP|TODO)\b',line,re.I)):
                forced='first unexpected Node failure/skip'
            if time.monotonic()>deadline:forced='outer timeout'
            if forced:
                killed=subprocess.run([TASKKILL,'/PID',str(proc.pid),'/T','/F'],capture_output=True,env=ENV)
                save(name+'.termination.json',{'reason':forced,'actualargv':[TASKKILL,'/PID',str(proc.pid),'/T','/F'],'actual_exit':killed.returncode,'stdout':killed.stdout.decode('utf8','replace'),'stderr':killed.stderr.decode('utf8','replace')})
                break
        code=proc.wait()
        for t in threads:t.join()
    raw=(OUT/(name+'.stdout.raw')).read_bytes();err=(OUT/(name+'.stderr.raw')).read_bytes()
    save(name+'.invocation.json',{'actualargv':argv,'cwd':str(cwd),'actor':'codex:/root','started_at':start,'ended_at':now(),'actual_exit':code,'forced_stop':forced,'stdout_sha256':digest(raw),'stderr_sha256':digest(err),'timeout_seconds':limit})
    check(code==0 and forced is None,name+' failed; no automatic retry')
    return raw

def json_stream(raw):
    text=raw.decode();dec=json.JSONDecoder();i=0;out=[]
    while i<len(text):
        while i<len(text) and text[i].isspace():i+=1
        if i==len(text):break
        obj,end=dec.raw_decode(text,i);out.append(obj);i=end
    return out

def main(args):
    global ENV,TASKKILL,protected
    check(args.actor=='codex:/root','author cannot execute independent G1')
    auth=pathlib.Path(args.authorization).read_bytes()
    check(digest(auth)==args.authorization_sha,'authorization bytes changed')
    check(not WORK.exists() and not OUT.exists(),'single attempt outputs already exist; no overwrite/retry')
    check(WORK.parent==W/'.local','work path outside exact local root')
    WORK.mkdir(parents=True);OUT.mkdir(parents=True)
    (OUT/'authorization.original.json').write_bytes(auth)
    (OUT/'counter_state.original.json').write_bytes(pathlib.Path(args.counter_state).read_bytes())
    (OUT/'runner.original.py').write_bytes(pathlib.Path(__file__).read_bytes())
    lock=json.loads((M/'execution/toolchains/locked.json').read_bytes())['tools']
    for name in ['python','node','go','git']:
        check(digest(pathlib.Path(lock[name]['path']).read_bytes())==lock[name]['sha256'],'tool mismatch '+name)
    node=lock['node']['path'];go=lock['go']['path'];git=lock['git']['path'];goroot=pathlib.Path(go).parent.parent
    TASKKILL=str(pathlib.Path(os.environ['SystemRoot'])/'System32/taskkill.exe')
    ENV={k:v for k,v in os.environ.items() if k.upper() not in {'NODE_OPTIONS','NODE_PATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','GOFLAGS','GOEXPERIMENT','GOWORK','GOTOOLCHAIN','GOENV','GODEBUG'} and not k.upper().startswith('RESEARCHOS_')}
    ENV.update({'GOROOT':str(goroot),'GOPATH':str(M/'.local/gopath'),'GOCACHE':str(WORK/'gocache'),'GOTMPDIR':str(WORK/'gotmp'),'TMP':str(WORK/'tmp'),'TEMP':str(WORK/'tmp'),'GOENV':'off','GOTOOLCHAIN':'local','GOFLAGS':'-mod=readonly','GOWORK':'off','GOPROXY':'off','GOSUMDB':'off','GOOS':'windows','GOARCH':'amd64','CGO_ENABLED':'0','NODE_PATH':str(SDK/'node_modules'),'NO_PROXY':'*'})
    ENV['PATH']=str(pathlib.Path(git).parent)+os.pathsep+str(pathlib.Path(node).parent)+os.pathsep+os.environ.get('PATH','')
    for p in ['gocache','gotmp','tmp']: (WORK/p).mkdir()
    save('environment.json',{k:ENV[k] for k in ['GOROOT','GOPATH','GOCACHE','GOTMPDIR','TMP','TEMP','GOENV','GOTOOLCHAIN','GOFLAGS','GOWORK','GOPROXY','GOSUMDB','GOOS','GOARCH','CGO_ENABLED','NODE_PATH','NO_PROXY','PATH']})
    check(command('head',[git,'rev-parse','HEAD'],W,30).decode().strip()=='6fb5263681c17f0e50920c354dc07ed440a23714','candidate HEAD mismatch')
    expected=json.loads((P/'inputs.json').read_bytes())['inputs']
    for f in expected:check(digest(pathlib.Path(f['source']).read_bytes())==f['sha256'],'preparation input drift '+f['source'])
    vendor=json.loads((M/'third_party/mu.MANIFEST.json').read_bytes())
    check(vendor['files']==5083 and len(vendor['entries'])==5083,'fixed Mu manifest count')
    for p,v in vendor['entries'].items():
        check(p.startswith('third_party/mu/') and '..' not in pathlib.PurePosixPath(p).parts,'bad vendor path')
        b=(M/p).read_bytes();check(digest(b)==v['sha256'] and len(b)==v['size'],'fixed SDK drift '+p)
    aliases=json.loads((P/'resources.json').read_bytes())['aliases']
    for a in aliases:check(str(pathlib.Path(a['alias']).resolve())==a['resolved'] and a['within_mu'],'alias drift')
    protected=[pathlib.Path(f['source']) for f in expected]+[pathlib.Path(TASKKILL)]
    for d in ['internal','apps','adapters','migrations','contracts']:protected+=tree(W/d)
    protected+=tree(SDK/'packages')+tree(SDK/'node_modules')+[M/p for p in vendor['entries']]+tree(goroot)
    for name in ['python','node','go','git']:protected.append(pathlib.Path(lock[name]['path']))
    before=vector(protected);save('inputs.before.json',before)
    # Actual ESM resolution only; no SDK import or module execution.
    code = (P/'esm_probe.mjs.txt').read_text(encoding='utf-8')
    command('node-resolve-alias',[node,'--experimental-import-meta-resolve','--input-type=module','-e',code,str(SDK)],W,30)
    bundle=WORK/'mu-worker.mjs'
    metadata=json.loads(command('bundle',[node,str(W/'adapters/runtime/mu/build.mjs'),str(bundle)],W,120))
    check(metadata['source_sha256']==digest((W/'adapters/runtime/mu/worker.mjs').read_bytes()),'wrong worker source')
    check(metadata['bundle_sha256']==digest(bundle.read_bytes()) and metadata['vendored_files_verified']==5083,'wrong bundle metadata')
    (OUT/'bundle.original.mjs').write_bytes(bundle.read_bytes());(OUT/'bundle.build.original.json').write_bytes((pathlib.Path(str(bundle)+'.build.json')).read_bytes())
    deps=json_stream(command('go-list',[go,'list','-deps','-test','-json','./internal/domain'],W,180))
    dependency=[];generated=[]
    fields=['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']
    for pkg in deps:
        check(not pkg.get('Error') and not pkg.get('DepsErrors'),'go list package error')
        for field in fields:
            for f in pkg.get(field,[]):
                p=pathlib.Path(f) if pathlib.Path(f).is_absolute() else pathlib.Path(pkg['Dir'])/f
                if not p.exists():
                    check(pkg.get('ImportPath','').endswith('.test') and p.name=='_testmain.go','missing compiler input '+str(p));generated.append(str(p));continue
                check(any(p.resolve().is_relative_to(x.resolve()) for x in [W,goroot,M/'.local/gopath']), 'dependency outside registered public roots '+str(p))
                dependency.append(p)
        if pkg.get('Module',{}).get('GoMod'):dependency.append(pathlib.Path(pkg['Module']['GoMod']))
    protected+=dependency;before=vector(protected);save('compiled-dependencies.before.json',before);save('generated-testmain.expected.json',generated)
    exe=WORK/'domain.g1.test.exe'
    command('go-compile',[go,'test','-c','-work','-x','-o',str(exe),'./internal/domain'],W,240)
    command('go-buildinfo',[go,'version','-m',str(exe)],W,30)
    save('artifacts.before-case.json',vector(tree(WORK)))
    check(before==vector(protected),'compiled inputs changed before first case')
    save('inputs.pre-case.json',vector(protected))
    ENV['RESEARCHOS_QUEUE_WORKER_BUNDLE']=str(bundle);ENV['RESEARCHOS_STREAM_SDK_ROOT']=str(SDK)
    save('test-environment.json',{'RESEARCHOS_QUEUE_WORKER_BUNDLE':str(bundle),'RESEARCHOS_STREAM_SDK_ROOT':str(SDK),'ordinary_Go_MODEL_calls':0,'Go_SQL_calls':0,'JS_transport':'custom Response plus synthetic child frames; local process only, no real provider HTTP'})
    raw=command('go3',[go,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',str(exe),'-test.v','-test.count=1','-test.timeout=60s','-test.run=^('+'|'.join(GO3)+')$'],W/'internal/domain',90,'go')
    events=[json.loads(line) for line in raw.splitlines() if line];check(not any(x.get('Action') in ['fail','skip'] for x in events),'Go failure/skip')
    check({x.get('Test') for x in events if x.get('Action')=='pass' and x.get('Test') in GO3}==set(GO3),'missing Go3 actual pass events')
    check(before==vector(protected),'input changed after Go3')
    raw=command('js3',[node,'--test','--test-concurrency=1','--test-reporter=tap']+[str(W/'adapters/runtime/mu'/f) for f in JS3],W,180,'node')
    text=raw.decode('utf8');counts={k:int(v) for k,v in re.findall(r'^# (tests|pass|fail|cancelled|skipped|todo) (\d+)\r?$',text,re.M)}
    save('js3.actual-counts.json',{'counts':counts,'expected_author_tests':26})
    check(counts.get('tests')==26 and counts.get('pass')==26 and all(counts.get(k)==0 for k in ['fail','cancelled','skipped','todo']),'JS actual count/failure/skip mismatch')
    check(before==vector(protected),'input changed after JS3')
    save('inputs.after-current.json',vector(protected));save('artifacts.after.json',vector([exe,bundle]))
    save('result.json',{'status':'ROOT_G1_EXECUTION_REPORTED_NOT_WHOLE9_ACCEPTANCE','Go_top_level':3,'Go_actual_test_pass_events':sum(x.get('Action')=='pass' and 'Test' in x for x in events),'JS':counts,'held_positives_executed':0,'old64_plus12_repeated':0,'paid':0,'external_model_HTTP':0,'source_mutations':0,'chain_reset':False})

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');a.add_argument('--actor');a.add_argument('--authorization');a.add_argument('--authorization-sha');a.add_argument('--counter-state');args=a.parse_args()
    if not args.execute:a.error('Preparation only: Root must review and explicitly authorize execution; no default action.')
    try: main(args)
    except BaseException as error:
        if OUT.exists():
            save('inputs.failure.current.json',vector(protected))
            save('failure.origin.json',{'at':now(),'error':repr(error),'traceback':traceback.format_exc(),'counter_reset':False,'stop':'First unexpected stops dependent lane. No repair/retry/source write authorized.','candidate9_current':vector([W/x['path'] for x in json.loads((P/'snapshot/main/execution/v2.4/receipts/W05/W05-99/provider_binding_whole_scope_gap_mapping_codex/80512d54-a478-4291-9760-8e5a4b77e49f/mapping.json').read_bytes())['candidate_source9']])})
        raise
