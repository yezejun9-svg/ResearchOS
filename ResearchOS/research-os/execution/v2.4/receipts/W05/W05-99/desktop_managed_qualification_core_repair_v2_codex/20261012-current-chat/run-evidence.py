import datetime, hashlib, json, os, pathlib, subprocess, sys
out=pathlib.Path(__file__).resolve().parent
repo=out.parents[6]
wt=repo/'.local/worktrees/w05-desktop-managed-qualification-core-repair-v2-20261012'
review=repo/'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_core_review_codex/20261012-current-chat'
baseline=json.loads((review/'domain.invocation.json').read_text(encoding='utf-8'))
env=dict(os.environ);env.update(baseline['environment'])
for key,folder in [('GOTMPDIR','go-tmp'),('TEMP','test-temp'),('TMP','test-temp')]:
    target=out/'cache'/folder;target.mkdir(parents=True,exist_ok=True);env[key]=str(target)
go=str(repo/'.local/tools/go1.27.1/go/bin/go.exe')
build=repo/'.local/builds/desktop-managed-qualification-core-repair-v2-20261012'
build.mkdir(parents=True,exist_ok=True)
env['RESEARCHOS_CONTROL_EXE']=str(build/'researchos-control.exe')
env['RESEARCHOS_RUNTIME_VERIFIER_EXE']=str(build/'runtime-verifier.exe')
phase=sys.argv[1]
if phase=='format':
    argv=[str(pathlib.Path(go).with_name('gofmt.exe')),'-w',*[str(wt/'internal/domain'/p) for p in ['runtime_coordinator_windows.go','runtime_drain_windows.go','runtime_qualification_confirmation_windows.go','runtime_qualification_fence_windows_test.go']]]
elif phase.startswith('build-'):
    target=phase[len('build-'):]; name='researchos-control' if target=='control' else 'runtime-verifier'
    argv=[go,'build','-mod=readonly','-o',str(build/(name+'.exe')),'./apps/'+target]
else:
    argv=[go,'test','-mod=readonly','-count=1','-json','-timeout=300s']
    if phase=='targeted':argv+=['./internal/domain','-run','^(TestManagedFence|TestRuntimeDrainLeaseAndScanFence)']
    elif phase=='review-overlay':
        original=review/'reviewer_shutdown_fence_windows_test.go'
        overlay={'Replace':{str(wt/'internal/domain/reviewer_shutdown_fence_windows_test.go'):str(original)}}
        (out/'review-overlay.json').write_text(json.dumps(overlay),encoding='utf-8')
        argv+=['-overlay='+str(out/'review-overlay.json'),'./internal/domain','-run','^TestReviewer']
    elif phase=='domain':argv+=['./internal/domain','-run',baseline['argv'][-1][:-2]+'|TestManagedFence.*|TestRuntimeDrainLeaseAndScanFence)$']
    elif phase=='host':
        host=json.loads((review/'host.invocation.json').read_text(encoding='utf-8'))
        for k,v in host['environment'].items():
            if k.startswith('RESEARCHOS_'):env[k]=v
        env['RESEARCHOS_CONTROL_EXE']=str(build/'researchos-control.exe')
        env['RESEARCHOS_RUNTIME_VERIFIER_EXE']=str(build/'runtime-verifier.exe')
        argv+=['./internal/host','-run',host['argv'][host['argv'].index('-run')+1],'-args','-local-runtime-assets-dir='+str(repo/'.local/builds/current-chat-runtime-assets-20261012'),'-local-runtime-verifier-executable='+str(build/'runtime-verifier.exe'),'-local-runtime-control-executable='+str(build/'researchos-control.exe')]
    elif phase=='verifier':argv+=['./internal/verifier']
    else:raise ValueError(phase)
prefix=sys.argv[2] if len(sys.argv)>2 else phase
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=wt,env=env,capture_output=True,timeout=420)
(out/(prefix+'.stdout')).write_bytes(r.stdout);(out/(prefix+'.stderr')).write_bytes(r.stderr)
record={'argv':argv,'cwd':str(wt),'started':started,'ended':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'environment':{k:v for k,v in env.items() if k in baseline['environment'] or k.startswith('RESEARCHOS_')},'real_model_calls':0}
(out/(prefix+'.invocation.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
events=[]
for line in r.stdout.splitlines():
    try: events.append(json.loads(line))
    except ValueError:pass
terminal=[{k:e[k] for k in ['Action','Package','Test','Elapsed'] if k in e} for e in events if e.get('Action') in ['pass','fail','skip']]
(out/(prefix+'.summary.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'phase':phase,'exit':r.returncode,'passed':sum(e['Action']=='pass' and 'Test' in e for e in terminal),'failed':[e for e in terminal if e['Action']=='fail'],'skipped':[e for e in terminal if e['Action']=='skip']}))
if r.returncode:print(r.stderr.decode('utf-8',errors='replace'));print(r.stdout.decode('utf-8',errors='replace')[-10000:])
raise SystemExit(r.returncode)
