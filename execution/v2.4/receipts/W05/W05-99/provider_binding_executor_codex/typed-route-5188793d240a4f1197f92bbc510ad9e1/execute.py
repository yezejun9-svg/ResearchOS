import pathlib, subprocess, os, json, hashlib, datetime, sys, difflib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[6]
MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
GO = MAIN / '.local/tools/go1.27.1/go/bin/go.exe'
NODE = pathlib.Path('C:/nvm4w/nodejs/node.exe')
BUNDLE = ROOT / '.local/provider-binding/negative-controls-2/mu-worker.mjs'
BIN = HERE / 'domain.test.exe'
REVIEW = MAIN / 'execution/v2.4/receipts/W05/W05-99/provider_binding_zero_model_adjudication_codex/d7f95235-03e1-464f-b3b0-374ca7394fda/attempt3'
SCOPE = MAIN / 'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-typed-route-scope-r285/scope_registration.json'
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

if sha(SCOPE)!='f7cb452f108842e940c21326860e6047554eb41cbf9210f5c54c1219a346de97': raise SystemExit('scope hash mismatch')
if sha(GO)!='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490': raise SystemExit('locked Go hash mismatch')
if sha(NODE)!='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6': raise SystemExit('locked Node hash mismatch')
phase=sys.argv[1]
if phase=='prepare':
    if command('format',[GO.parent/'gofmt.exe','-w','internal/domain/runtime_model_verification.go','internal/domain/runtime_provider_binding_windows_test.go']): raise SystemExit(1)
    previous=HERE.parent/'epoch-correction-69a52b78d491456792bf394b01629e02'
    source_scope=json.loads(SCOPE.read_text(encoding='utf-8'))
    snapshots={}
    nine=['adapters/runtime/mu/worker.mjs','adapters/runtime/mu/worker-provider-binding.test.mjs','internal/domain/runtime_model.go','internal/domain/runtime_broker_windows.go','internal/domain/runtime_model_windows.go','internal/domain/runtime_model_verification.go','internal/domain/runtime_model_stream.go','internal/domain/runtime_provider_binding_test.go','internal/domain/runtime_provider_binding_windows_test.go']
    (HERE/'source-snapshot').mkdir()
    for name in nine:
        p=ROOT/name; target=HERE/'source-snapshot'/name.replace('/','__');target.write_bytes(p.read_bytes());snapshots[name]={'current':ref(p),'snapshot':ref(target)}
        if name in source_scope['source_before']:
            old=previous/(name.replace('/','__')+'.frozen')
            if sha(old)!=source_scope['source_before'][name]['sha256']:raise SystemExit('authorized source-before snapshot mismatch')
            targetold=HERE/'source-snapshot'/(name.replace('/','__')+'.before');targetold.write_bytes(old.read_bytes())
            snapshots[name]['before']=ref(targetold)
            patch=''.join(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),p.read_text(encoding='utf-8').splitlines(True),fromfile='authorized-before/'+name,tofile='author-attempt3/'+name))
            (HERE/'source-snapshot'/(name.replace('/','__')+'.diff')).write_text(patch,encoding='utf-8')
    write('source9.freeze.json',snapshots)
    write('attempt.json',{'scope':ref(SCOPE),'author_attempt':3,'issue_failures_before':3,'model_history_failures_held':5,'automatic_retry':False,'model_calls':0,'worker_starts':0,'HTTP':0,'public_input_only':True,'semantic_vectors':'exact byte-copy before store.Open versus closed output: all schema objects and typed row multisets of every table including stored rowid; no retrospective credit to old case02','precase_diagnostic_errors':[{'command':'rg budget*.go literal path','error':'Windows glob path OS 123','kind':'locator only, no test/model'}, {'command':'rg ... internal/domain/runtime_profile.go','error':'nonexistent path OS 2; actual function found in runtime_qualification.go','kind':'locator only, no test/model'}]})
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
    missing='provider original MODEL dispatch or legacy provenance unavailable'
    unmatched='provider unmatched original MODEL reservation'
    cost='provider original request and complete cost'
    admission='provider original admission provenance'
    cases=[('1','none',''),('red','none',missing),('0','none','')]
    cases += [('0',m,unmatched) for m in ['disguise-model-as-tool','swap-tool-reservation','swap-tool-reservation-rehashed','erase-model-effects']]
    cases += [('1','synthetic-zero-model',''),('1','synthetic-zero-disguise',unmatched),('1','synthetic-shared-route','')]
    cases += [('1',m,'provider ambiguous original typed route') for m in ['synthetic-duplicate-route','synthetic-duplicate-bound']]
    cases += [('0',m,c) for m,c in [('tool-key','provider reservation original effect key'),('tool-epoch','provider original Run epoch unavailable'),('tool-credential','provider ambiguous original typed route'),('tool-request-hash',cost),('tool-cost-event',cost),('tool-cost-time',cost),('tool-cost-basis',cost),('tool-cost-policy','provider reservation original budget policy'),('tool-cost-money',cost)]]
    cases += [(k,'none','') for k in ['2','3','4','5']]
    cases += [(k,m,c) for k in ['1','0','2','3','4','5'] for m,c in [('missing-dispatch-transport',missing),('double-marker',admission)]]
    cases += [('1',m,c) for m,c in [('missing-admission',admission),('missing-profile-ref',admission),('missing-runtime-ref',admission),('missing-binding','provider original MODEL reservation provenance'),('missing-qualification','sql: no rows in result set'),('forged-fixture-deleted-native','provider original MODEL reservation provenance'),('missing-all-run-history','provider original Run epoch unavailable'),('cross-run','immutable dispatch manifest mismatch'),('foreign-runtime-ref',admission),('ambiguous-epoch','provider ambiguous original Run epoch'),('wrong-request-hash',cost),('changed-capability','provider original typed key'),('changed-key-and-capability',unmatched),('sparse-sequence',unmatched),('wrong-epoch','provider original Run epoch unavailable'),('wrong-sql-key','provider effect SQL identity')]]
    cases += [('2','no-prepared',unmatched)]
    synthetic=['sealed-no-policy','later-runtime-revision','generic-missing-ref','missing-binding']
    epoch_modes=['decoded-number','int64','string','fraction','zero','ambiguous']
    if len(cases)+len(synthetic)+len(epoch_modes)>64:raise SystemExit('scope case cap')
    write('case-plan.json',{'archives':cases,'synthetic':synthetic,'epoch_controls':epoch_modes,'public_backup':'NOT_RUN_OPTIONAL','models':0,'held_positives':'NOT_RUN_STILL_HELD'})
    outcomes=[]
    for n,(key,mutation,cause) in enumerate(cases):
        label=f'case-{n:02d}-{key}-{mutation}'
        allowed=[]
        if mutation!='none': allowed=['runtime_dispatches','resource_effects']
        if mutation in ['missing-binding','forged-fixture-deleted-native','missing-all-run-history']: allowed+=['runtime_bindings']
        if mutation in ['missing-qualification','forged-fixture-deleted-native']: allowed+=['runtime_qualification_plans','runtime_qualification_runs']
        if mutation=='forged-fixture-deleted-native': allowed+=['orchestration_fixtures']
        if mutation in ['missing-all-run-history','ambiguous-epoch']: allowed+=['domain_versions']
        if mutation.startswith('tool-cost-'): allowed+=['domain_objects','domain_versions']
        if mutation.startswith('synthetic-'): allowed+=['domain_objects','domain_versions','uploaded_content','runtime_bindings','runtime_qualification_plans','runtime_qualification_runs']
        case={'case':label,'input':originalrefs[key]['copy']['path'],'input_sha256':'sha256:'+originalrefs[key]['copy']['sha256'],'mutation':mutation,'output':str(HERE/(label+'-evidence')),'want_error':bool(cause),'required_cause':cause,'expected_inventory':3 if key=='0' else 1,'allowed_mutation_tables':allowed,'original_effect_key_counts':{'MODEL':3 if key=='0' else 1,'TOOL':1 if key=='0' else 0}}
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
    write('execution-summary.json',{'at':now(),'outcomes':outcomes,'source_drift':source_drift,'input_drift':input_drift,'actual_cases':len(outcomes),'planned_cases':len(cases)+len(synthetic)+len(epoch_modes),'models':0,'workers':0,'HTTP':0,'held_history_count':5,'issue_failures_before':3,'author_repair_attempt_total':3,'status':'STOPPED_FIRST_UNEXPECTED' if any(x['exit']!=0 for x in outcomes) else 'SOURCE_EXECUTION_REPORTED_NOT_ACCEPTED'})
else:raise SystemExit('unknown phase')
