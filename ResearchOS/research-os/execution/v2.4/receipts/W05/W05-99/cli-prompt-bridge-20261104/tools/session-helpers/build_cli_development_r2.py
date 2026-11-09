import hashlib,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
main=Path('D:/作品集/ResearchOS/research-os')
source=main/'.local/worktrees/workbench-experience-20261104'
out=main/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104'
receipt=out/'cli-development-build';bundle=source/'.local/development-cli-20261104-r1'
expected=sys.argv[1];assert len(expected)==40 and all(c in '0123456789abcdef' for c in expected)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,doc):path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=source).decode().strip()
assert not receipt.exists() and not bundle.exists(),'Inspect prior artifacts, do not replay uncertain build'
assert git('rev-parse','HEAD')==expected and not git('status','--porcelain=v1','-uno')
desktop=json.loads((out/'development-build/controller-02/final.json').read_bytes());assert desktop['head']==expected
lock=json.loads((main/'execution/toolchains/locked.json').read_bytes())['tools']
go=Path(lock['go']['path']);assert sha(go)==lock['go']['sha256']
receipt.mkdir();bundle.mkdir()
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PROGRAMDATA','PROGRAMFILES','PROGRAMFILES(X86)','PATH'}}
env.update({'GOTOOLCHAIN':'local','GOENV':'off','CGO_ENABLED':'0','GOPROXY':'off','GOSUMDB':'off','GOPATH':str(main/'.local/tools/gopath'),'GOMODCACHE':str(main/'.local/tools/gopath/pkg/mod'),'GOCACHE':str(source/'.local/development-ui-20261104-r4-go-cache')})
rows=json.loads((out/'author/source-manifest.json').read_bytes())['files']
for row in rows:assert sha(source/row['path'])==row['sha256']
def run(name,argv,cwd=source,child_env=env):
    start=datetime.now(timezone.utc).isoformat()
    result=subprocess.run([str(x) for x in argv],cwd=cwd,env=child_env,capture_output=True,timeout=300)
    (receipt/(name+'.stdout.txt')).write_bytes(result.stdout);(receipt/(name+'.stderr.txt')).write_bytes(result.stderr)
    put(receipt/(name+'.json'),{'argv':[str(x) for x in argv],'cwd':str(cwd),'started_at':start,'exit_code':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()})
    assert result.returncode==0,f'{name} failed; original evidence retained'
    return result.stdout
binary=bundle/'researchos.exe'
run('go-build',[go,'build','-mod=readonly','-trimpath','-buildvcs=true','-o',binary,'./apps/cli'])
version=run('go-binary-metadata',[go,'version','-m',binary]).decode('utf-8')
assert 'vcs.revision='+expected in version and 'vcs.modified=false' in version
state=source/'.local/development-cli-20261104-r1-probe-state';assert not state.exists()
probe_env=env.copy();probe_env.update({'LOCALAPPDATA':str(state/'LocalAppData'),'APPDATA':str(state/'AppData'),'RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED':'1','RESEARCHOS_CLI_DISCOVERY':str(state/'absent-discovery.json')})
commands=json.loads(run('standalone-command-surface',[binary,'commands'],bundle,probe_env))
assert commands['command']=='commands' and commands['status']=='COMPLETED' and commands['exit_code']==0
for name in ['task','run']:
    command=next(item for item in commands['commands'] if item['command']==name)
    mode=command['explicit_prompt_mode']
    assert mode['state']=='IMPLEMENTED' and mode['qualification']=='DEVELOPMENT_ONLY' and mode['independent_acceptance']=='NOT_EVALUATED'
assert not state.exists(),'Metadata-only command unexpectedly created state'
put(receipt/'command-surface.json',commands)
for row in rows:assert sha(source/row['path'])==row['sha256']
assert git('rev-parse','HEAD')==expected and not git('status','--porcelain=v1','-uno')
manifest={'schema':'researchos.cli-development-binary/1','mode':'DEVELOPMENT_BUILD_COMMAND_SURFACE_CHECKED_NOT_LIVE_QUALIFIED','source_head':expected,'source_tree':git('rev-parse','HEAD^{tree}'),'source_files':rows,'binary':{'path':str(binary),'sha256':sha(binary),'bytes':binary.stat().st_size},'go_tool':{'path':str(go),'sha256':sha(go)},'go_mod_sha256':sha(source/'go.mod'),'go_sum_sha256':sha(source/'go.sum'),'standalone_commands_exit':0,'probe_state_created':False,'network_or_native_or_provider_started':False,'formal_increment':0,'limitations':['CLI commands metadata only; no authenticated business task or native qualification was run.','Normal task/run prompt requires a reachable authorized shared Host and current session/model configuration.','Existing W14 baseline writer takeover test and ordinary LIVE business acceptance design remain blocked.']}
put(bundle/'development-cli-manifest.json',manifest);put(receipt/'result.json',manifest)
(bundle/'README.txt').write_text('ResearchOS CLI development build\n\nresearchos.exe task --prompt "your task"\nresearchos.exe run --prompt-file goal.txt\n\nRequires an authorized running Host and configured project/model. Source development checks do not constitute independent business or formal acceptance. The Desktop development launcher deliberately isolates its state and disables the global locator. Use an explicitly selected discovery path for that isolated instance; never copy credentials or merge roots.\n',encoding='utf-8')
print(json.dumps({'status':manifest['mode'],'binary':str(binary),'sha256':sha(binary),'bytes':binary.stat().st_size,'source_head':expected,'formal_increment':0}))
