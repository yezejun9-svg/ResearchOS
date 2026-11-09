import hashlib, json, subprocess, time
from pathlib import Path
ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-assistant-home-20261104')
BASE = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-assistant-startup-author')
NODE = Path('C:/nvm4w/nodejs/node.exe')
assert hashlib.sha256(NODE.read_bytes()).hexdigest() == '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
attempt = BASE / 'checks-01'
attempt.mkdir(exist_ok=False)
test_source = BASE / 'assistant-startup.test.mjs'
target = ROOT / 'tests/ui/desktop/assistant-startup.test.mjs'
assert not target.exists()
target.write_bytes(test_source.read_bytes())
commands = [
 ('startup-and-compatibility', [str(NODE), '--test', '--test-reporter=tap', 'tests/ui/desktop/assistant-startup.test.mjs', 'tests/ui/desktop/harness-workbench.test.mjs', 'tests/ui/desktop/activity-projection.test.mjs', 'tests/ui/desktop/development-smoke.test.mjs']),
 ('mu-first-use', [str(NODE), '--test', '--test-reporter=tap', '--test-name-pattern=^first use consumes native choice', 'tests/ui/desktop/w13-react.test.js']),
 ('main-syntax', [str(NODE), '--check', 'apps/desktop/main/main.js']),
 ('startup-syntax', [str(NODE), '--check', 'apps/web/src/startup.js']),
]
results=[]
for name, argv in commands:
    (attempt / (name + '.command.json')).write_text(json.dumps({'argv':argv,'cwd':str(ROOT),'timeout_seconds':60},ensure_ascii=True,indent=2),encoding='utf-8')
    t=time.monotonic()
    try:
        r=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60)
        (attempt/(name+'.stdout.raw')).write_bytes(r.stdout)
        (attempt/(name+'.stderr.raw')).write_bytes(r.stderr)
        row={'name':name,'exit_code':r.returncode,'elapsed_seconds':round(time.monotonic()-t,3),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    except subprocess.TimeoutExpired as e:
        (attempt/(name+'.stdout.raw')).write_bytes(e.stdout or b'')
        (attempt/(name+'.stderr.raw')).write_bytes(e.stderr or b'')
        row={'name':name,'exit_code':None,'status':'TIMEOUT','elapsed_seconds':round(time.monotonic()-t,3)}
    results.append(row)
    (attempt/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(row),flush=True)
print('CHECKS_TERMINAL',flush=True)
raise SystemExit(0 if all(row['exit_code']==0 for row in results) else 1)
