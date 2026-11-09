from pathlib import Path
import hashlib,json,subprocess
BASE=Path(__file__).resolve().parent
WT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-core-system-drive-20261104')
SCOPE=Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/core-system-drive/scope.json')
NODE=Path('C:/nvm4w/nodejs/node.exe');GIT='C:/Program Files/Git/cmd/git.exe'
assert hashlib.sha256(NODE.read_bytes()).hexdigest()=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
directory=BASE/'checks-01';directory.mkdir(exist_ok=False)
tests=['tests/ui/desktop/managed-environment.test.mjs','tests/ui/desktop/desktop-management-boundary.test.mjs','tests/ui/desktop/development-smoke.test.mjs']
for rel in tests:assert (WT/rel).exists(),rel
commands=[
 ('focused-node-tests',[str(NODE),'--test','--test-reporter=tap',*tests]),
 ('management-syntax',[str(NODE),'--check','apps/desktop/main/lib/desktop-management.js']),
 ('test-syntax',[str(NODE),'--check','tests/ui/desktop/managed-environment.test.mjs']),
 ('git-diff-check',[GIT,'-C',str(WT),'diff','--check']),
 ('git-status',[GIT,'-C',str(WT),'status','--porcelain=v1','--untracked-files=all']),
 ('git-diff',[GIT,'-C',str(WT),'diff','--','apps/desktop/main/lib/desktop-management.js','tests/ui/desktop/managed-environment.test.mjs']),
 ('git-head',[GIT,'-C',str(WT),'rev-parse','HEAD'])
]
results=[]
for name,argv in commands:
    (directory/(name+'.command.json')).write_text(json.dumps({'argv':argv,'cwd':str(WT),'timeout_seconds':60,'runtime':'Pure environment functions, fake management streams/identity/observe and owned temporary fixture files only. No real app/native/model/auth/user DB/cache DB.'},indent=2),encoding='utf-8')
    r=subprocess.run(argv,cwd=WT,capture_output=True,timeout=60)
    (directory/(name+'.stdout.raw')).write_bytes(r.stdout);(directory/(name+'.stderr.raw')).write_bytes(r.stderr)
    row={'name':name,'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    results.append(row);(directory/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(row),flush=True)
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
status=(directory/'git-status.stdout.raw').read_text(encoding='utf-8')
paths={line[3:] for line in status.splitlines() if line}
head=(directory/'git-head.stdout.raw').read_text().strip()
check={'paths_exact':paths==set(scope['baseline_sha256']),'paths':sorted(paths),'base_matches':head==scope['base_head']}
(directory/'scope-check.json').write_text(json.dumps(check,indent=2),encoding='utf-8');print(json.dumps(check),flush=True)
raise SystemExit(0 if all(row['exit_code']==0 for row in results) and check['paths_exact'] and check['base_matches'] else 1)
