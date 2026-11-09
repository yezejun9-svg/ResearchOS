from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\workbench-experience-20261104')
MAIN = Path(r'D:\作品集\ResearchOS\research-os')
RECEIPT = MAIN / 'execution/v2.4/receipts/W13/W13-03/workbench-experience-20261104/desktop-build'
CONTROL = RECEIPT / 'controller-02'
BUILD_RECEIPT = RECEIPT / 'build-02'
OUTPUT = ROOT / '.local/development-ui-20261104-r2'
STATE = ROOT / '.local/development-ui-20261104-r2-dryrun-state'
HEAD = '3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5'
PYTHON = Path(r'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe')
NODE = Path(r'C:\nvm4w\nodejs\node.exe')
env = os.environ.copy()
env.update({'PYTHONDONTWRITEBYTECODE':'1','GOPROXY':'off','GOSUMDB':'off'})

def now(): return datetime.now(timezone.utc).isoformat()
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def run(name, argv):
    folder=CONTROL/name
    folder.mkdir(exist_ok=False)
    put(folder/'invocation.json',{'argv':[str(x) for x in argv],'cwd':str(ROOT),'environment':{k:env.get(k) for k in ['PYTHONDONTWRITEBYTECODE','GOPROXY','GOSUMDB']}})
    start=now()
    with (folder/'stdout.raw').open('xb') as out,(folder/'stderr.raw').open('xb') as err:
        p=subprocess.Popen([str(x) for x in argv],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        code=p.wait()
    put(folder/'result.json',{'started_at':start,'ended_at':now(),'pid':p.pid,'native_exit':code,'stdout_sha256':digest(folder/'stdout.raw'),'stderr_sha256':digest(folder/'stderr.raw')})
    if code:
        raise RuntimeError(f'{name} exited {code}; original raw retained')
    return (folder/'stdout.raw').read_bytes()

def source_seven():
    report=json.loads((ROOT/'.local/workbench-experience-author-report.json').read_bytes())
    rows=[]
    for row in report['source_manifest']:
        current=digest(ROOT/row['path'])
        if current!=row['sha256']: raise RuntimeError('frozen UI source changed: '+row['path'])
        rows.append({**row,'current_sha256':current})
    return rows

def main():
    if OUTPUT.exists() or BUILD_RECEIPT.exists() or STATE.exists() or CONTROL.exists():
        raise RuntimeError('new output, controller, build receipt and dry-run state must not exist')
    for suffix in ['-go-cache','-go-tmp','-temp','-mu-stage','-client-stage','-client-receipts']:
        if OUTPUT.with_name(OUTPUT.name+suffix).exists(): raise RuntimeError('scratch collision '+suffix)
    CONTROL.mkdir(parents=True,exist_ok=False)
    put(CONTROL/'scope.json',{'at':now(),'owner':'codex:/root/workbench_builder','authorization':'Parent explicitly authorized complete development bundle build and dry-run on 2026-11-04; no installation, Core, product GUI, original state or old bundle actions','failure_origin':'desktop-build/sparse-module-closure','attempt_index':2,'prior_attempt_retained':True,'counters_reset':False,'expected_source_head':HEAD,'output':str(OUTPUT),'builder_receipts':str(BUILD_RECEIPT),'scratch':[str(OUTPUT.with_name(OUTPUT.name+x)) for x in ['-go-cache','-go-tmp','-temp','-mu-stage','-client-stage','-client-receipts']],'dryrun_nonexistent_state':str(STATE),'formal_acceptance':False})
    current=run('head-before',['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD']).decode('ascii').strip()
    if current!=HEAD: raise RuntimeError('candidate HEAD changed')
    before=source_seven();put(CONTROL/'frozen-ui.before.json',before)
    run('sparse-before',['git','-c','gc.auto=0','-c','maintenance.auto=false','sparse-checkout','list'])
    run('materialize-source',['git','-c','gc.auto=0','-c','maintenance.auto=false','sparse-checkout','add','adapters','internal','migrations/sqlite','execution/toolchains','docs/installation','tests/contracts','evaluation/development/jev-v2','evaluation/evolution','evaluation/holdout/jev','evaluation/skills','ops/experiment_sandbox','ops/supervisor'])
    status=run('source-status-before',['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','status','--porcelain=v1','-uno'])
    if status.strip(): raise RuntimeError('candidate tracked source dirty after materialization')
    if source_seven()!=before: raise RuntimeError('UI changed during materialization')
    argv=[PYTHON,'-B','-X','utf8','apps/desktop/build-development.py','--go',MAIN/'.local/tools/go1.27.1/go/bin/go.exe','--node',NODE,'--electron-dist',MAIN/'apps/desktop/node_modules/electron/dist','--module-cache',MAIN/'.local/tools/gopath/pkg/mod','--web-modules',MAIN/'apps/web/node_modules','--mu-common',MAIN,'--output',OUTPUT,'--receipts',BUILD_RECEIPT]
    print('Source closure materialized and seven frozen UI files unchanged; starting offline development build.',flush=True)
    run('complete-development-build',argv)
    put(CONTROL/'frozen-ui.after.json',source_seven())
    result=json.loads((BUILD_RECEIPT/'result.json').read_bytes())
    manifest=json.loads((OUTPUT/'development-manifest.json').read_bytes())
    if result.get('status')!='BUILT_NOT_NATIVE_TESTED' or manifest['source']['head']!=HEAD: raise RuntimeError('build completion/head mismatch')
    print('Complete source-bound development build finished; validating without Core/GUI launch.',flush=True)
    run('launcher-dryrun',[NODE,OUTPUT/'launch-development.mjs','--bundle',OUTPUT,'--state',STATE,'--dry-run'])
    if STATE.exists(): raise RuntimeError('dry-run unexpectedly created runtime state')
    after=run('source-status-after',['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks','status','--porcelain=v1','-uno'])
    if after.strip() or source_seven()!=before: raise RuntimeError('source changed during build')
    put(CONTROL/'final.json',{'at':now(),'status':'DEVELOPMENT_BUILT_AND_DRYRUN_VALIDATED_NO_NATIVE_START','head':HEAD,'bundle':str(OUTPUT),'manifest_sha256':digest(OUTPUT/'development-manifest.json'),'files':result['files'],'bytes':sum(row['bytes'] for row in manifest['files']),'dryrun_state_created':False,'source_seven_unchanged':True,'source_tracked_clean':True,'formal_acceptance':False,'limits':['Build and dry-run only; no installer, provider call, product Core/GUI, installation lifecycle, original data or formal acceptance tested.']})
    print(json.dumps({'status':'DEVELOPMENT_BUILT_AND_DRYRUN_VALIDATED_NO_NATIVE_START','bundle':str(OUTPUT),'manifest_sha256':digest(OUTPUT/'development-manifest.json'),'files':result['files']},ensure_ascii=True),flush=True)

try:
    main()
except Exception as error:
    if CONTROL.is_dir() and not (CONTROL/'controller-failed.json').exists():
        put(CONTROL/'controller-failed.json',{'at':now(),'error_type':type(error).__name__,'error':str(error),'status':'FIRST_FAILURE_RETAINED_NO_RETRY'})
    print(str(error),file=sys.stderr)
    raise SystemExit(1)
