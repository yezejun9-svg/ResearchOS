import pathlib, subprocess, os, json, hashlib, datetime, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[6]
MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
GO = MAIN / '.local/tools/go1.27.1/go/bin/go.exe'
NODE = pathlib.Path('C:/nvm4w/nodejs/node.exe')
BUNDLE = ROOT / '.local/provider-binding/negative-controls-2/mu-worker.mjs'
BIN = HERE / 'domain.test.exe'
REVIEW = MAIN / 'execution/v2.4/receipts/W05/W05-99/provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda/attempt3'
SCOPE = MAIN / 'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-epoch-causal-correction-r283/attempt3/scope_registration.json'
env = {'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(GO.parent.parent),'GOCACHE':str(MAIN/'.local/gocache'),'GOPATH':str(MAIN/'.local/gopath'),'GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','GOFLAGS':'','GOOS':'windows','GOARCH':'amd64','CGO_ENABLED':'0'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name, obj):
    p=HERE/name
    with p.open('x',encoding='utf-8') as f: json.dump(obj,f,indent=2,ensure_ascii=False);f.write('\n')
def ref(p): return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def command(label, argv, cwd=ROOT, extra=None):
    effective=env | (extra or {})
    invocation={'argv':[str(v) for v in argv],'cwd':str(cwd),'environment':effective,'started':now(),'timeout_seconds':300,'lane':'ZERO_MODEL_NO_HTTP_NO_WORKER'}
    write(label+'.invocation.json',invocation)
    with (HERE/(label+'.stdout.raw')).open('xb') as out,(HERE/(label+'.stderr.raw')).open('xb') as err:
        try: code=subprocess.run(invocation['argv'],cwd=cwd,env=os.environ|effective,stdout=out,stderr=err,timeout=300).returncode
        except subprocess.TimeoutExpired: code='TIMEOUT'
    write(label+'.result.json',invocation|{'finished':now(),'exit':code,'stdout':ref(HERE/(label+'.stdout.raw')),'stderr':ref(HERE/(label+'.stderr.raw'))})
    print(label,code,flush=True)
    return code
def capture(name, dependencies=None):
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    paths={str(ROOT/n) for n in names if n and not n.startswith('execution/') and (ROOT/n).is_file()}
    for base in [MAIN/'third_party/mu/packages',MAIN/'third_party/mu/node_modules']:
        paths.update(str(p) for p in base.rglob('*') if p.is_file() and p.suffix in ['.js','.mjs','.cjs','.json','.node','.wasm'])
    paths.update([str(GO),str(GO.parent/'gofmt.exe'),str(NODE),str(BUNDLE),str(SCOPE),str(HERE/'execute.py')])
    paths.update(str(f) for f in (GO.parent.parent/'pkg/tool/windows_amd64').glob('*') if f.is_file())
    paths.update(str(f) for pattern in ['*.json','*lock*'] for f in (MAIN/'third_party/mu').glob(pattern) if f.is_file())
    paths.update([str(MAIN/'execution/toolchains/locked.json')])
    if dependencies: paths.update(dependencies)
    if BIN.exists(): paths.add(str(BIN))
    data={p:ref(pathlib.Path(p)) for p in sorted(paths)}
    write(name+'.json',{'at':now(),'files':data,'environment':env,'overlay':None})
    return data

if sha(SCOPE)!='c7849f608ea93e97010b919414b905c902005c3031efc903a7d69047a28d2f7b': raise SystemExit('scope hash mismatch')
if sha(GO)!='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490': raise SystemExit('locked Go hash mismatch')
if sha(NODE)!='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6': raise SystemExit('locked Node hash mismatch')
phase=sys.argv[1]
if phase=='prepare':
    if command('format',[GO.parent/'gofmt.exe','-w','internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']): raise SystemExit(1)
    capture('source-before-compile')
    if command('go-list',[GO,'list','-deps','-test','-json','./internal/domain']): raise SystemExit(1)
    text=(HERE/'go-list.stdout.raw').read_text(encoding='utf-8');decoder=json.JSONDecoder();i=0;deps={};packages=[]
    while i<len(text):
        while i<len(text) and text[i].isspace():i+=1
        if i==len(text):break
        p,i=decoder.raw_decode(text,i);packages.append(p.get('ImportPath'));d=pathlib.Path(p.get('Dir',''))
        for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']:
            for name in p.get(key,[]):
                f=d/name
                if f.is_file():deps[str(f)]=ref(f)
    write('compiled-inputs.before.json',{'packages':packages,'files':deps})
    if command('compile',[GO,'test','-c','-o',BIN,'./internal/domain']):raise SystemExit(1)
    if command('buildinfo',[GO,'version','-m',BIN]):raise SystemExit(1)
    capture('before-first-case',deps)
    write('prepared.json',{'binary':ref(BIN),'scope':ref(SCOPE),'models':0,'tests_executed':0})
elif phase=='execute':
    before=json.loads((HERE/'before-first-case.json').read_text(encoding='utf-8'))['files']
    drift=[p for p,v in before.items() if ref(pathlib.Path(p))!=v]
    if drift:raise SystemExit('pre-case drift '+str(drift))
    # All original inputs are sealed before the first control. No DB is opened
    # by Python, only byte copies; Go opens only a new case copy.
    originals=json.loads((REVIEW/'original_database_freeze.json').read_text(encoding='utf-8'))
    originalrefs={}
    (HERE/'inputs').mkdir()
    for key,v in originals.items():
        src=pathlib.Path(v['original_path'])
        if sha(src)!=v['sha256']:raise SystemExit('original archive drift')
        target=HERE/'inputs'/(key+'.sqlite');target.write_bytes(src.read_bytes())
        originalrefs[key]={'original':ref(src),'copy':ref(target)}
    red=REVIEW/'cases/1-missing_dispatch_and_transport/fixture.sqlite'
    if sha(red)!='0c9b4fce3653119d277593f39f9079abeb6e65a9b7a441a76f3bdd7977abd121':raise SystemExit('independent red drift')
    target=HERE/'inputs/red.sqlite';target.write_bytes(red.read_bytes());originalrefs['red']={'original':ref(red),'copy':ref(target)}
    write('original-inputs.before.json',originalrefs)
    cases=[('1','none',False),('red','none',True)]
    cases += [(k,'none',False) for k in ['0','2','3','4','5']]
    cases += [(k,m,True) for k in ['1','0','2','3','4','5'] for m in ['missing-dispatch-transport','double-marker']]
    cases += [('1',m,True) for m in ['missing-admission','missing-profile-ref','missing-runtime-ref','missing-binding','missing-qualification','forged-fixture-deleted-native','missing-all-run-history','cross-run','foreign-runtime-ref','ambiguous-epoch','wrong-request-hash','changed-capability','changed-key-and-capability','sparse-sequence','wrong-epoch','wrong-sql-key']]
    cases += [('2','no-prepared',True)]
    synthetic=['sealed-no-policy','later-runtime-revision','generic-missing-ref','missing-binding']
    epoch_modes=['decoded-number','int64','missing','string','fraction','zero','negative','overflow','no-match','ambiguous']
    if len(cases)+len(synthetic)+len(epoch_modes)>64:raise SystemExit('scope case cap')
    write('case-plan.json',{'archives':cases,'synthetic':synthetic,'epoch_controls':epoch_modes,'public_backup':'NOT_RUN_OPTIONAL','models':0,'held_positives':'NOT_RUN_STILL_HELD'})
    outcomes=[]
    for n,(key,mutation,want) in enumerate(cases):
        label=f'case-{n:02d}-{key}-{mutation}';case={'case':label,'input':originalrefs[key]['copy']['path'],'input_sha256':'sha256:'+originalrefs[key]['copy']['sha256'],'mutation':mutation,'output':str(HERE/(label+'-evidence')),'want_error':want}
        if key=='red' or mutation=='missing-dispatch-transport':case['required_cause']='provider original MODEL dispatch or legacy provenance unavailable'
        write(label+'.json',case)
        code=command(label,[GO,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',BIN,'-test.v','-test.count=1','-test.timeout=90s','-test.run=^TestProviderBindingInventoryCausalControl$'],ROOT/'internal/domain',{'RESEARCHOS_PROVIDER_CAUSAL_CASE':str(HERE/(label+'.json'))})
        outcomes.append({'case':label,'exit':code})
        if code!=0:break
    if outcomes and outcomes[-1]['exit']==0:
        for mode in synthetic:
            label='synthetic-'+mode
            code=command(label,[GO,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',BIN,'-test.v','-test.count=1','-test.timeout=90s','-test.run=^TestProviderBindingInventorySyntheticProvenance$'],ROOT/'internal/domain',{'RESEARCHOS_PROVIDER_SYNTHETIC_DIR':str(HERE/(label+'-evidence')),'RESEARCHOS_PROVIDER_SYNTHETIC_MODE':mode})
            outcomes.append({'case':label,'exit':code})
            if code!=0:break
    if outcomes and outcomes[-1]['exit']==0:
        for mode in epoch_modes:
            label='epoch-'+mode
            code=command(label,[GO,'tool','test2json','-t','-p','researchos.local/research-os/internal/domain',BIN,'-test.v','-test.count=1','-test.timeout=90s','-test.run=^TestProviderBindingOriginalEpochCausalControl$'],ROOT/'internal/domain',{'RESEARCHOS_PROVIDER_EPOCH_DIR':str(HERE/(label+'-evidence')),'RESEARCHOS_PROVIDER_EPOCH_MODE':mode})
            outcomes.append({'case':label,'exit':code})
            if code!=0:break
    after=capture('after-cases',before)
    source_drift=[p for p,v in before.items() if after.get(p)!=v]
    input_drift=[k for k,v in originalrefs.items() if ref(pathlib.Path(v['original']['path']))!=v['original'] or ref(pathlib.Path(v['copy']['path']))!=v['copy']]
    write('execution-summary.json',{'at':now(),'outcomes':outcomes,'source_drift':source_drift,'input_drift':input_drift,'actual_cases':len(outcomes),'planned_cases':len(cases)+len(synthetic)+len(epoch_modes),'models':0,'workers':0,'HTTP':0,'held_history_count':5,'issue_failures_before':2,'author_repair_attempt_total':2,'status':'STOPPED_FIRST_UNEXPECTED' if any(x['exit']!=0 for x in outcomes) else 'SOURCE_EXECUTION_REPORTED_NOT_ACCEPTED'})
else:raise SystemExit('unknown phase')
