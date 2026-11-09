from pathlib import Path
import hashlib,json,subprocess
BASE=Path(__file__).resolve().parent
WT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-public-health-20261104')
BASE_HEAD='c4029c0b57599e1aafed6d01ea4034b0cf465ccd'
GIT='C:/Program Files/Git/cmd/git.exe';NODE='C:/nvm4w/nodejs/node.exe'
directory=BASE/'checks-02-c-overlay';directory.mkdir(exist_ok=False)
stage=directory/'source'
def git(*args):
    r=subprocess.run([GIT,'-C',str(WT),*args],capture_output=True,timeout=30)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))
    return r.stdout
paths=git('ls-tree','-r','--name-only',BASE_HEAD,'--','apps/web/src','apps/desktop/main/lib').decode('utf-8').splitlines()
paths=[p for p in paths if Path(p).suffix in ['.js','.jsx','.mjs','.json','.css']]
tests=['tests/ui/desktop/public-health-bridge.test.mjs','tests/ui/desktop/assistant-startup.test.mjs','tests/ui/desktop/harness-workbench.test.mjs','tests/ui/desktop/activity-projection.test.mjs','tests/ui/desktop/development-smoke.test.mjs']
paths+=['apps/web/package.json','apps/desktop/main/main.js',*tests]
inventory=[]
for rel in sorted(set(paths)):
    own=rel in ['apps/desktop/main/lib/ipc.js','tests/ui/desktop/public-health-bridge.test.mjs']
    payload=(WT/rel).read_bytes() if own else git('show',BASE_HEAD+':'+rel)
    target=stage/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(payload)
    inventory.append({'path':rel,'origin':'CURRENT_SCOPE_EXACT2' if own else 'GIT_BASE_READONLY_PUBLIC_SOURCE','base_head':None if own else BASE_HEAD,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
(directory/'input-manifest.json').write_text(json.dumps({'base_head':BASE_HEAD,'files':inventory,'note':'Only public source dependencies plus exact2 overlay; no full Git baseline, runtime data, credentials, DB or model.'},indent=2),encoding='utf-8')
argv=[NODE,'--test','--test-reporter=tap',*tests]
(directory/'command.json').write_text(json.dumps({'argv':argv,'cwd':str(stage),'timeout_seconds':60,'source_dependencies_from_git_base':True,'exact_same_five_test_selections_as_attempt01':True},indent=2),encoding='utf-8')
r=subprocess.run(argv,cwd=stage,capture_output=True,timeout=60)
(directory/'stdout.raw').write_bytes(r.stdout);(directory/'stderr.raw').write_bytes(r.stderr)
report={'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),'input_files':len(inventory),'all_overlay_live_unchanged':all(hashlib.sha256((WT/row['path']).read_bytes()).hexdigest()==row['sha256'] for row in inventory if row['origin']=='CURRENT_SCOPE_EXACT2')}
(directory/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
print(r.stdout.decode('utf-8',errors='replace')[-700:],flush=True)
raise SystemExit(r.returncode)
