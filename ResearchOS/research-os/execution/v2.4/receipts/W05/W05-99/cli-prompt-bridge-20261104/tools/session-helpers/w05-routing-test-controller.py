"""Capture W05 author-only development checks; never updates global counters/acceptance."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-routing-20261104')
RECEIPT=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/routing-author')
SPEC=Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
NAMES=['tests/runtime/check/legacy.go','tests/runtime/check/routing_test.go','tests/runtime/check/w0501.go','tests/runtime/check/w0502.go','ops/ci/runtime_v24.py','tests/runtime/runtime_v24_test.py']
STAMP=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock=json.loads((ROOT/'execution/toolchains/locked.json').read_bytes())
for key in ['python','go']:
    tool=lock['tools'][key]
    if not Path(tool['path']).is_absolute() or sha(tool['path'])!=tool['sha256']:raise SystemExit('locked tool mismatch '+key)
python=lock['tools']['python']['path'];go=lock['tools']['go']['path']
RECEIPT.mkdir(parents=True,exist_ok=True)
run=RECEIPT/'checks-01'
run.mkdir(exist_ok=False)
cache=ROOT/'.local/w05-routing-author-20261104'
for folder in ['gocache','gotmp','tmp']:(cache/folder).mkdir(parents=True,exist_ok=True)
env=dict(os.environ,RESEARCHOS_V24_SPEC_ROOT=str(SPEC),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',
         GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOENV='off',
         GOCACHE=str(cache/'gocache'),GOTMPDIR=str(cache/'gotmp'),
         GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',TEMP=str(cache/'tmp'),TMP=str(cache/'tmp'))
commands=[
    ('python-unit',[python,'-X','utf8','tests/runtime/runtime_v24_test.py'],0,{}),
    ('go-unit',[go,'test','./tests/runtime/check','-run','^TestRuntime(ExactRoutes|LockedPython)$','-count=1','-v'],0,{}),
    ('a04-live-gap',[python,'-X','utf8','ops/ci/runtime_v24.py','--mode','live'],1,{'RESEARCHOS_TASK_ID':'W05','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'A04'}),
    ('a04-fixture-refusal',[python,'-X','utf8','ops/ci/runtime_v24.py','--mode','fixture'],2,{'RESEARCHOS_TASK_ID':'W05','RESEARCHOS_CHECK_ID':'','RESEARCHOS_CASE_ID':'A04'}),
]
dump(run/'inputs.json',{'started':STAMP,'cwd':str(ROOT),'source_head':'3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5',
   'tools':{key:lock['tools'][key] for key in ['python','go']},'spec_root':str(SPEC),'environment_overrides':{key:env[key] for key in ['RESEARCHOS_V24_SPEC_ROOT','GOPROXY','GOSUMDB','GOTOOLCHAIN','GOENV','GOCACHE','GOTMPDIR','GOMODCACHE','TEMP','TMP']},
   'source_sha256':{name:sha(ROOT/name) for name in NAMES},'note':'Development checks only, no formal acceptance; old native suites not called.'})
results=[]
for name,argv,expected,extra in commands:
    directory=run/name;directory.mkdir()
    dump(directory/'command.json',{'argv':argv,'cwd':str(ROOT),'environment_overrides':extra,'expected_exit':expected})
    begin=time.monotonic()
    with (directory/'stdout.txt').open('wb') as out,(directory/'stderr.txt').open('wb') as err:
        p=subprocess.run(argv,cwd=ROOT,env=dict(env,**extra),stdout=out,stderr=err,timeout=300)
    result={'name':name,'exit_code':p.returncode,'expected_exit':expected,'matched_expected_exit':p.returncode==expected,'elapsed_seconds':round(time.monotonic()-begin,3)}
    dump(directory/'result.json',result);results.append(result)
    print(json.dumps(result),flush=True)
dump(run/'results.json',results)
for script in ['w05-routing-author.py','w05-routing-refine.py','w05-routing-test-controller.py']:
    shutil.copyfile(Path(__file__).parent/script,run/script)
raise SystemExit(0 if all(r['matched_expected_exit'] for r in results) else 1)
