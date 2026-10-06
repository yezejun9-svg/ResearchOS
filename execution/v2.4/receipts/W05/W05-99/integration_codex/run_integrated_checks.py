"""Fresh source-wave regressions; never a provider LIVE or parent acceptance."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys, uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}

# Run only after separately reviewed slices have actually been integrated.
integrations = [HERE/name for name in ('cli_slice_integrated_codex.json','tool_slice_integrated_codex.json','goal_slice_integrated_codex.json','s4_cli_goal_integrated_codex.json')]
for p in integrations: assert p.is_file(), f'reviewed integration required: {p.name}'
locked = read(ROOT/'execution/toolchains/locked.json')
for name in ('go','node','python'):
    tool = locked['tools'][name]
    assert sha(Path(tool['path'])) == tool['sha256']
bundle = ROOT/'.local/w1401-mu-worker/mu-worker.mjs'
assert bundle.is_file()
scopes = [HERE/name for name in ('cli_source_scope_codex.json','goal_source_scope_codex.json','tools_source_scope_codex.json','tool_recovery_test_source_scope_codex.json','s4_cli_goal_source_scope_codex.json')]
owned = sorted({p for scope in scopes for p in read(scope)['exact_paths']})
run = HERE/'integrated_runs'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10])
run.mkdir(parents=True)
(run/'runner_snapshot.py.txt').write_bytes(Path(__file__).read_bytes())
tracked = subprocess.check_output(['git','ls-files','apps/cli','apps/control','internal','adapters','migrations','contracts','evaluation','ops','tests','spec/v2.0/contracts','go.mod','go.sum'],cwd=ROOT,text=True).splitlines()
inputs = [ref(ROOT/p) for p in sorted(set(tracked)) if (ROOT/p).is_file()]
for p in owned:
    target = run/'source_snapshot'/p
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((ROOT/p).read_bytes())
env = dict(os.environ)
go,node = locked['tools']['go'],locked['tools']['node']
env.update(GOTOOLCHAIN='local',GOENV='off',GOPROXY='off',GOSUMDB='off',GOPATH=str(ROOT/'.local/gopath'),GOCACHE=str(ROOT/'.local/gocache'),
    GOROOT=str(Path(go['path']).parents[1]),RESEARCHOS_GO=go['path'],RESEARCHOS_MU_BUNDLE=str(bundle))
env['PATH'] = str(Path(node['path']).parent)+os.pathsep+env['PATH']
selector = '^(TestClient|TestRuntimeMu|TestRuntimeOriginalToolPermission|TestRuntimePermission|TestPermissionProducer|TestPermissionRespond|TestW14Session|TestW05RuntimeEvent|TestRuntimeCoordinatorEffectCrashRecovery)'
commands = [('cli',[go['path'],'test','-json','-count=1','./apps/cli','-run','^Test','-timeout','300s']),
    ('domain',[go['path'],'test','-json','-count=1','./internal/domain','-run',selector,'-timeout','300s']),
    ('api',[go['path'],'test','-json','-count=1','./internal/api','-timeout','300s'])]
manifest = {'schema':'researchos.w05.integrated-wave-test-input.v1','mode':'FIXTURE_AND_REAL_CURRENT_MU_WITH_LOCAL_FIXTURE_PORTS_NOT_LIVE',
    'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'integration_refs':[ref(p) for p in integrations],'scope_refs':[ref(p) for p in scopes],
    'source_inputs':inputs,'owned_source_snapshots':[{'path':p,'sha256':sha(ROOT/p)} for p in owned],
    'runner_sha256':sha(Path(__file__)),'tools':{name:locked['tools'][name] for name in ('go','node','python')},
    'bundle':{'path':str(bundle),'sha256':sha(bundle),'bytes':bundle.stat().st_size},
    'environment':{name:env[name] for name in ('GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','GOPATH','GOCACHE','GOROOT','RESEARCHOS_GO','RESEARCHOS_MU_BUNDLE')},
    'commands':[{'name':name,'argv':args,'cwd':str(ROOT)} for name,args in commands],
    'external_provider_calls':0,'formal_case_count_delta':0}
(run/'inputs.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
results=[]
for name,args in commands:
    with (run/f'{name}.stdout.jsonl').open('wb') as out,(run/f'{name}.stderr.txt').open('wb') as err:
        try: code=subprocess.run(args,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=330).returncode
        except subprocess.TimeoutExpired: code=124
    rows=[json.loads(line) for line in (run/f'{name}.stdout.jsonl').read_text(encoding='utf8').splitlines()]
    counts={a:[r['Test'] for r in rows if r.get('Action')==a and r.get('Test')] for a in ('pass','fail','skip')}
    outcome={'package':name,'exit_code':code,'stdout':ref(run/f'{name}.stdout.jsonl'),'stderr':ref(run/f'{name}.stderr.txt'),
        'test_pass':counts['pass'],'test_fail':counts['fail'],'test_skip':counts['skip'],
        'package_pass':any(r.get('Action')=='pass' and not r.get('Test') for r in rows)}
    results.append(outcome)
    print(json.dumps({'package':name,'exit_code':code,'pass':len(counts['pass']),'fail':counts['fail'],'skip':counts['skip']},ensure_ascii=True),flush=True)
    if code or not outcome['package_pass'] or counts['fail'] or counts['skip']: break
result={'schema':'researchos.w05.integrated-wave-test-result.v1','mode':manifest['mode'],
    'started_at':manifest['started_at'],'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'inputs':ref(run/'inputs.json'),'runner_snapshot':ref(run/'runner_snapshot.py.txt'),'packages':results,
    'source_changed_during_run':[r['path'] for r in inputs if sha(ROOT/r['path'])!=r['sha256']],
    'external_provider_calls':0,'formal_case_count_delta':0,'product_or_parent_acceptance_issued':False}
result['status']='PASS' if len(results)==3 and all(r['exit_code']==0 and r['package_pass'] and not r['test_fail'] and not r['test_skip'] for r in results) and not result['source_changed_during_run'] else 'FAIL'
(run/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':result['status'],'result':ref(run/'result.json')},ensure_ascii=True),flush=True)
sys.exit(0 if result['status']=='PASS' else 1)
