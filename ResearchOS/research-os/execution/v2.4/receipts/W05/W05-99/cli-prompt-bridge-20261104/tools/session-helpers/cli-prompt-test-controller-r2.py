import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/cli-prompt-bridge-20261104')
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=MAIN/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/author'
SOURCE=['apps/cli/main.go','apps/cli/cli_contract.go','apps/cli/cli_run_contract.go','apps/cli/cli_verbs.go','apps/cli/cli_stream.go','apps/cli/cli_prompt.go','apps/cli/cli_prompt_test.go']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock= json.loads((MAIN/'execution/toolchains/locked.json').read_bytes())
for key in ['go','python']:
    item=lock['tools'][key]
    if not Path(item['path']).is_absolute() or sha(item['path'])!=item['sha256']:raise SystemExit('tool mismatch: '+key)
run=OUT/'checks-02';run.mkdir(parents=True,exist_ok=False)
cache=ROOT/'.local/cli-prompt-author-tests-20261104'
for part in ['gocache','gotmp','tmp']:(cache/part).mkdir(parents=True,exist_ok=True)
env=dict(os.environ,GOPROXY='off',GOSUMDB='off',GOTOOLCHAIN='local',GOENV='off',
   GOMODCACHE=str(MAIN/'.local/tools/gopath/pkg/mod'),GOCACHE=str(cache/'gocache'),GOTMPDIR=str(cache/'gotmp'),TEMP=str(cache/'tmp'),TMP=str(cache/'tmp'))
pattern='^(TestCLIPrompt.*|TestW05CLIFollowActualPagesAndDelayedAdmission|TestW05CLIFollowRefusesIncompleteExecution|TestW05CLICancelRequiresHostSettlement|TestW05CLIGoalAdoptionAndAliases|TestW14CLICommandsUseRealSessionHTTP|TestRefusedWriterLeavesTheFileUntouched)$'
argv=[lock['tools']['go']['path'],'test','./apps/cli','-run',pattern,'-count=1','-v']
inputs={'scope_id':'CLI_PROMPT_BRIDGE_20261104','attempt_index':2,'failure_origin':'cli-prompt-sparse-module-closure-20261104','previous_attempt':'checks-01','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'base_head':'fc2b1a50662580b1a0fca92559ca26be6e959f01','cwd':str(ROOT),'argv':argv,
    'tools':{key:lock['tools'][key] for key in ['go','python']},'tool_lock_path':str(MAIN/'execution/toolchains/locked.json'),'tool_lock_sha256':sha(MAIN/'execution/toolchains/locked.json'),
    'environment_overrides':{key:env[key] for key in ['GOPROXY','GOSUMDB','GOTOOLCHAIN','GOENV','GOMODCACHE','GOCACHE','GOTMPDIR','TEMP','TMP']},
    'source_sha256':{name:sha(ROOT/name) for name in SOURCE},'scope_sha256':sha(OUT.parent/'scope.json'),
    'measurement_mode':'DEVELOPMENT_FIXTURE','formal_increment':0,
    'exclusions':['No real native credential bridge','No provider/model','No legacy cascade process','No old task checker','No registry/checkpoint mutation']}
dump(run/'inputs.json',inputs)
begin=time.monotonic()
with (run/'stdout.txt').open('wb') as out,(run/'stderr.txt').open('wb') as err:
    result=subprocess.run(argv,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=300)
summary={'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-begin,3),'terminal':True,'expected_exit':0,'matched_expected_exit':result.returncode==0}
dump(run/'result.json',summary)
for name in ['cli-prompt-author.py','cli-prompt-tests-author.py','cli-prompt-metadata.py','cli-prompt-pretest.py','cli-prompt-int64-fix.py','cli-prompt-retry-prepare.py','cli-prompt-test-controller.py','cli-prompt-test-controller-r2.py']:
    shutil.copyfile(Path(__file__).parent/name,run/name)
print(json.dumps(summary),flush=True)
raise SystemExit(result.returncode)
