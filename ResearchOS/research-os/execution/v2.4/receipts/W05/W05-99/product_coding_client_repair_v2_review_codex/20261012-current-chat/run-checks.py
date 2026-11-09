from pathlib import Path
import os,json,subprocess,time,hashlib
O=Path(__file__).resolve().parent; ROOT=O.parents[6]
C=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v2-20261012')
B=C/'.local/builds/product-coding-client-repair-v2-20261012'
node='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'
def run(name,args,extra=None):
 env=os.environ.copy();env.update(extra or {})
 start=time.time();p=subprocess.run([node,*args],cwd=O,env=env,capture_output=True)
 (O/(name+'.stdout')).write_bytes(p.stdout);(O/(name+'.stderr')).write_bytes(p.stderr)
 (O/(name+'.invocation.json')).write_text(json.dumps(dict(argv=[node,*args],cwd=str(O),selected_environment=extra,elapsed_seconds=time.time()-start,exit=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()),indent=2))
 print(name,p.returncode,p.stdout.decode('utf-8')[-1500:],p.stderr.decode('utf-8')[-1500:],flush=True);assert p.returncode==0
run('review-fixtures',[str(O/'review-fixtures.mjs')])
s=(C/'tests/ui/continuity/coding_authorization_driver.mjs').read_text(encoding='utf-8')
s=s.replace("const root = path.resolve(here, '../../..')","const root = process.env.RESEARCHOS_SHARED_ROOT")
s=s.replace("path.join(sharedRoot, '.local', 'vite-coding-authorization-cache')","path.join(here, 'vite-review-cache')")
s=s.replace("console.log(JSON.stringify({ status:","fs.writeFileSync(path.join(here,'status-recovery.dom.html'),await page.content());\n  await page.screenshot({path:path.join(here,'status-recovery.png'),fullPage:true});\n  fs.writeFileSync(path.join(here,'dom-bridge-calls.json'),JSON.stringify(record,null,2));\n  console.log(JSON.stringify({ status:")
s=s.replace("  for (const file of [html, entry]) if (fs.existsSync(file)) fs.unlinkSync(file)","  // Retain generated browser inputs as evidence.")
(O/'status-recovery-dom.mjs').write_text(s,encoding='utf-8')
run('status-recovery-dom',[str(O/'status-recovery-dom.mjs')],dict(RESEARCHOS_SHARED_ROOT=str(ROOT),RESEARCHOS_UI_SOURCE=str(B/'apps/web/src/workbench.jsx'),ROS_STATUS_RECOVERY='1',ROS_REFRESH_FAIL_ONCE='1'))

