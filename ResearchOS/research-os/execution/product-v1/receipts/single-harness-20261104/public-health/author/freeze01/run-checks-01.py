from pathlib import Path
import hashlib,json,subprocess
BASE=Path(__file__).resolve().parent
ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-public-health-20261104')
NODE=Path('C:/nvm4w/nodejs/node.exe'); GIT='C:/Program Files/Git/cmd/git.exe'
assert hashlib.sha256(NODE.read_bytes()).hexdigest()=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
directory=BASE/'checks-01';directory.mkdir(exist_ok=False)
tests=['tests/ui/desktop/public-health-bridge.test.mjs','tests/ui/desktop/assistant-startup.test.mjs','tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs']
for rel in tests:assert (ROOT/rel).exists(),rel
commands=[
 ('pure-tests',[str(NODE),'--test','--test-reporter=tap',*tests]),
 ('ipc-syntax',[str(NODE),'--check','apps/desktop/main/lib/ipc.js']),
 ('test-syntax',[str(NODE),'--check','tests/ui/desktop/public-health-bridge.test.mjs']),
 ('git-diff-check',[GIT,'-C',str(ROOT),'diff','--check']),
 ('git-status',[GIT,'-C',str(ROOT),'status','--porcelain=v1','--untracked-files=all']),
 ('git-diff',[GIT,'-C',str(ROOT),'diff','--','apps/desktop/main/lib/ipc.js']),
 ('git-head',[GIT,'-C',str(ROOT),'rev-parse','HEAD'])
]
results=[]
for name,argv in commands:
    (directory/(name+'.command.json')).write_text(json.dumps({'argv':argv,'cwd':str(ROOT),'timeout_seconds':60,'runtime':'In-memory fake filesystem, fake HTTP events and transport only; no real socket/native/model/auth/DB.'},ensure_ascii=True,indent=2),encoding='utf-8')
    r=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60)
    (directory/(name+'.stdout.raw')).write_bytes(r.stdout);(directory/(name+'.stderr.raw')).write_bytes(r.stderr)
    row={'name':name,'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    results.append(row);(directory/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(row),flush=True)
scope=json.loads(Path('D:/作品集/ResearchOS/research-os/execution/product-v1/receipts/single-harness-20261104/public-health/scope.json').read_text(encoding='utf-8'))
status=(directory/'git-status.stdout.raw').read_text(encoding='utf-8')
paths={line[3:] for line in status.splitlines() if line}
head=(directory/'git-head.stdout.raw').read_text().strip()
check={'paths_exact':paths==set(scope['baseline_sha256']),'paths':sorted(paths),'base_matches':head==scope['base_head']}
(directory/'scope-check.json').write_text(json.dumps(check,indent=2),encoding='utf-8');print(json.dumps(check),flush=True)
raise SystemExit(0 if all(row['exit_code']==0 for row in results) and check['paths_exact'] and check['base_matches'] else 1)
