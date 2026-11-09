"""Read base via Git and use a Go build overlay; no source file is replaced."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import time

ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=MAIN/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/author'
BASE='fc2b1a50662580b1a0fca92559ca26be6e959f01'
EXISTING=['apps/cli/main.go','apps/cli/cli_contract.go','apps/cli/cli_run_contract.go','apps/cli/cli_verbs.go','apps/cli/cli_stream.go']
NEW=['apps/cli/cli_prompt.go','apps/cli/cli_prompt_test.go']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock=json.loads((MAIN/'execution/toolchains/locked.json').read_bytes())
for key in ['go','git']:
    item=lock['tools'][key]
    if not Path(item['path']).is_absolute() or sha(item['path'])!=item['sha256']:raise SystemExit('locked tool mismatch '+key)
run=OUT/'baseline-w14-01';run.mkdir(parents=True,exist_ok=False)
snapshots=run/'base-sources';snapshots.mkdir()
replacements={};source_hashes={};commands=[]
for name in EXISTING:
    argv=[lock['tools']['git']['path'],'-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+name]
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=30)
    commands.append({'argv':argv,'cwd':str(ROOT),'exit_code':result.returncode})
    if result.returncode!=0:
        (run/'git-stderr.txt').write_bytes(result.stderr);dump(run/'git-commands.json',commands);raise SystemExit(result.returncode)
    target=snapshots/Path(name).name
    target.write_bytes(result.stdout)
    replacements[str(ROOT/name)]=str(target);source_hashes[name]=sha(target)
for name in NEW:replacements[str(ROOT/name)]=''
overlay=run/'overlay.json';dump(overlay,{'Replace':replacements})
cache=ROOT/'.local/cli-prompt-author-tests-20261104'
env=dict(os.environ,GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOENV='off',GOFLAGS='-overlay='+str(overlay),GOMODCACHE=str(MAIN/'.local/tools/gopath/pkg/mod'),GOCACHE=str(cache/'gocache'),GOTMPDIR=str(cache/'gotmp'),TEMP=str(cache/'tmp'),TMP=str(cache/'tmp'))
argv=[lock['tools']['go']['path'],'test','-overlay',str(overlay),'./apps/cli','-run','^TestW14CLICommandsUseRealSessionHTTP$','-count=1','-v']
dump(run/'inputs.json',{'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_head':BASE,'argv':argv,'cwd':str(ROOT),'environment_overrides':{'GOFLAGS':env['GOFLAGS'],'GOPROXY':'off','GOSUMDB':'off','GOTOOLCHAIN':'local','GOENV':'off'},'base_source_sha256':source_hashes,'overlay_sha256':sha(overlay),'new_files_removed_from_build':NEW,'candidate_source_before':{name:sha(ROOT/name) for name in EXISTING+NEW},'mode':'BASELINE_DEVELOPMENT_FIXTURE','failure_origin':'cli-prompt-existing-w14-writer-busy-20261104','origin_attempt_index':2,'previous_observation':'checks-02','note':'Exact old sources via read-only build overlay; inherited GOFLAGS keeps any child Go build on the same overlay. No check weakened or source restored.'})
dump(run/'git-commands.json',commands)
begin=time.monotonic()
with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err:
    result=subprocess.run(argv,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=180)
summary={'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-begin,3),'terminal':True,'candidate_source_after':{name:sha(ROOT/name) for name in EXISTING+NEW},'interpretation':'Baseline observation only; nonzero is not converted into PASS.'}
dump(run/'result.json',summary)
shutil.copyfile(Path(__file__),run/Path(__file__).name)
print(json.dumps(summary),flush=True)
raise SystemExit(result.returncode)
