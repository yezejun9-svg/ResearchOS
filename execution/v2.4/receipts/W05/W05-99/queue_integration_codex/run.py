"""Main-source integration evidence; no product-source writes or formal acceptance."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode('utf-8').strip()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}

locked=read(ROOT/'execution/toolchains/locked.json')['tools']
for tool in ('go','node','python'):assert sha(Path(locked[tool]['path']))==locked[tool]['sha256'],tool
go,node=locked['go']['path'],locked['node']['path']
bundle=ROOT/'.local/w0599-queue-integration/mu-worker.mjs'
control=ROOT/'.local/w0599-queue-integration/control.exe'
package=ROOT/'execution/v2.4/receipts/W05/W05-99/queue_executor_codex/frozen-package-input'
assert sha(package/'PACKAGE_MANIFEST.json')=='4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'
package_files=read(package/'PACKAGE_MANIFEST.json')['files']
assert len(package_files)==147
for entry in package_files:
    path=package/entry['path']
    assert sha(path)==entry['sha256'] and path.stat().st_size==entry['size_bytes'],entry['path']
assert {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}=={e['path'] for e in package_files}|{'PACKAGE_MANIFEST.json'}
source_scopes=['apps','internal','adapters','migrations','contracts','evaluation','ops','tests','bootstrap','spec/v2.0/contracts','go.mod','go.sum','execution/toolchains/locked.json','execution/v2.4/component_lock.json','third_party/VENDORED_FROM.md','third_party/mu.MANIFEST.json','third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu/pnpm-lock.yaml','third_party/mu/yarn.lock','third_party/mu/bun.lock']
def vector():
    paths=set(git('ls-files','--',*source_scopes).splitlines())
    paths.update(git('ls-files','--others','--exclude-standard','--',*source_scopes).splitlines())
    paths.update(p.relative_to(ROOT).as_posix() for p in package.rglob('*') if p.is_file())
    return [ref(ROOT/p) for p in sorted(paths) if p and (ROOT/p).is_file()]
env=dict(os.environ)
env.update(GOTOOLCHAIN='local',GOENV='off',GOPROXY='off',GOSUMDB='off',GOROOT=str(Path(go).parents[1]),GOCACHE=str(ROOT/'.local/gocache'),GOPATH=str(ROOT/'.local/gopath'),RESEARCHOS_GO=go,RESEARCHOS_NODE=node,RESEARCHOS_MU_BUNDLE=str(bundle),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(bundle),RESEARCHOS_W04_PACKAGE_INPUT=str(package))
env['PATH']=str(Path(node).parent)+os.pathsep+env['PATH']
envkeys=['GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','GOROOT','GOCACHE','GOPATH','RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_QUEUE_WORKER_BUNDLE','RESEARCHOS_W04_PACKAGE_INPUT','RESEARCHOS_QUEUE_FAILURE_DIR','RUNTIME_CONTROL_BINARY']
selector='^TestClientQueue|^TestRuntimeClientQueue|^TestQueueUpgrade|^TestBridge|^TestRuntimeMuToolRefusal|^TestW18FinalSchema|^TestW04CurrentA01|^TestW07Health'
commands=[('sdk-build',[node,'adapters/runtime/mu/build.mjs',str(bundle)]),('cli',[go,'test','-json','./apps/cli','-count=1','-timeout=240s']),('matrix',[go,'test','-json','./internal/domain','./adapters/runtime','-run',selector,'-count=1','-timeout=300s']),('sdk',[node,'--test','adapters/runtime/mu/worker-control.test.mjs']),('control-build',[go,'build','-o',str(control),'./apps/control']),('control-startup',[go,'test','-json','./internal/domain','-run','^TestRuntimeCoordinatorControlStartup$','-count=1','-timeout=90s'])]
results=[]
for name,argv in commands:
    run=HERE/name
    run.mkdir(exist_ok=False)
    before=vector();write(run/'inputs-before.json',before)
    env['RESEARCHOS_QUEUE_FAILURE_DIR']=str(run/'failed-fixture')
    if name=='control-startup':env['RUNTIME_CONTROL_BINARY']=str(control)
    command={'argv':argv,'cwd':str(ROOT),'head':git('rev-parse','HEAD'),'started':now(),'exe_sha256':sha(Path(argv[0])),'environment':{k:env[k] for k in envkeys if k in env},'runner':ref(Path(__file__)),'tools':{k:locked[k] for k in ('go','node','python')},'bundle':ref(bundle) if bundle.exists() else None,'control':ref(control) if name=='control-startup' else None}
    write(run/'command.json',command)
    with (run/'stdout.raw').open('wb') as out,(run/'stderr.raw').open('wb') as err:
        code=subprocess.run(argv,cwd=ROOT,env=env,stdout=out,stderr=err).returncode
    after=vector();write(run/'inputs-after.json',after)
    stdout=(run/'stdout.raw').read_text(encoding='utf-8-sig',errors='replace')
    events=[]
    for line in stdout.splitlines():
        try:
            v=json.loads(line)
            if isinstance(v,dict) and 'Action' in v:events.append(v)
        except ValueError:pass
    counts={a:[e['Test'] for e in events if e.get('Action')==a and e.get('Test')] for a in ('pass','fail','skip')}
    nodecounts={k:int(m.group(1)) for k in ('tests','pass','fail','skipped') if (m:=re.search('ℹ '+k+r' (\d+)',stdout))}
    result={'name':name,'exit_code':code,'ended':now(),'head_after':git('rev-parse','HEAD'),'input_count':len(before),'source_vector_equal':before==after,'test_events':counts,'node_counts':nodecounts,'stdout':ref(run/'stdout.raw'),'stderr':ref(run/'stderr.raw'),'bundle_after':ref(bundle) if bundle.exists() else None,'classification':'CURRENT_MAIN_INTEGRATION_FIXTURE_NOT_FORMAL_ACCEPTANCE'}
    write(run/'result.json',result);results.append(result)
    print(json.dumps({'name':name,'exit':code,'pass_events':len(counts['pass']),'fail':counts['fail'],'skip':counts['skip'],'node':nodecounts,'drift':before!=after}),flush=True)
    if code or before!=after or counts['fail'] or counts['skip']:
        break
write(HERE/'results.json',{'runs':results,'completed_commands':len(results),'expected_commands':len(commands),'formal_case_count_delta':0,'parent_acceptance':False,'external_provider_live':False})
sys.exit(0 if len(results)==len(commands) and all(r['exit_code']==0 and r['source_vector_equal'] and not r['test_events']['fail'] and not r['test_events']['skip'] for r in results) else 1)
