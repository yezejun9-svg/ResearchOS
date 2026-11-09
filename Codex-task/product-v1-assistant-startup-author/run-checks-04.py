import hashlib, json, subprocess
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104')
NODE='C:/nvm4w/nodejs/node.exe'
GIT='C:/Program Files/Git/cmd/git.exe'
directory=BASE/'checks-04-final'
directory.mkdir(exist_ok=False)
commands=[
 ('startup-and-compatibility',[NODE,'--test','--test-reporter=tap','tests/ui/desktop/assistant-startup.test.mjs','tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs']),
 ('main-syntax',[NODE,'--check','apps/desktop/main/main.js']),
 ('startup-syntax',[NODE,'--check','apps/web/src/startup.js']),
 ('new-test-syntax',[NODE,'--check','tests/ui/desktop/assistant-startup.test.mjs']),
 ('git-diff-check',[GIT,'-C',str(ROOT),'diff','--check']),
 ('git-status',[GIT,'-C',str(ROOT),'status','--porcelain=v1','--untracked-files=all']),
 ('git-diff-stat',[GIT,'-C',str(ROOT),'diff','--stat']),
 ('git-head',[GIT,'-C',str(ROOT),'rev-parse','HEAD'])
]
results=[]
for name,argv in commands:
    (directory/(name+'.command.json')).write_text(json.dumps({'argv':argv,'cwd':str(ROOT),'timeout_seconds':60},ensure_ascii=True,indent=2),encoding='utf-8')
    r=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60)
    (directory/(name+'.stdout.raw')).write_bytes(r.stdout)
    (directory/(name+'.stderr.raw')).write_bytes(r.stderr)
    row={'name':name,'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    results.append(row)
    (directory/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(row),flush=True)
status=(directory/'git-status.stdout.raw').read_text(encoding='utf-8')
expected=set(json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/assistant-home/scope.json').read_text(encoding='utf-8'))['baseline_sha256'])
actual={line[3:] for line in status.splitlines() if line}
head=(directory/'git-head.stdout.raw').read_text().strip()
scope_check={'paths_exact':actual==expected,'actual_paths':sorted(actual),'base_matches':head=='d9d7e2477c0b1de27cec28e0d76dcba55e7a9e81'}
(directory/'scope-check.json').write_text(json.dumps(scope_check,indent=2),encoding='utf-8')
print(json.dumps(scope_check),flush=True)
raise SystemExit(0 if all(row['exit_code']==0 for row in results) and scope_check['paths_exact'] and scope_check['base_matches'] else 1)
