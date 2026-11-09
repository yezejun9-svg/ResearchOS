from pathlib import Path
import os,json,subprocess,time,hashlib,concurrent.futures
O=Path(__file__).resolve().parent;ROOT=O.parents[6]
C=Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-client-v3-20261012')
B=C/'.local/builds/product-coding-client-repair-v3-20261012'
node='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'
def run(name,args,extra=None):
 env=os.environ.copy();env.update(extra or {})
 started=time.time();p=subprocess.run([node,*args],cwd=O,env=env,capture_output=True,timeout=100)
 (O/(name+'.stdout')).write_bytes(p.stdout);(O/(name+'.stderr')).write_bytes(p.stderr)
 (O/(name+'.invocation.json')).write_text(json.dumps(dict(argv=[node,*args],cwd=str(O),selected_environment=extra,elapsed_seconds=time.time()-started,exit=p.returncode,stdout_sha256=hashlib.sha256(p.stdout).hexdigest(),stderr_sha256=hashlib.sha256(p.stderr).hexdigest()),indent=2),encoding='utf-8')
 print(name,p.returncode,p.stdout.decode('utf-8')[-2500:],p.stderr.decode('utf-8')[-2000:],flush=True)
 assert p.returncode==0
s=(C/'tests/ui/continuity/coding_authorization_driver.mjs').read_text(encoding='utf-8')
s=s.replace("const root = path.resolve(here, '../../..')","const root = process.env.RESEARCHOS_SHARED_ROOT")
s=s.replace("path.join(sharedRoot, '.local', 'vite-coding-authorization-cache')","path.join(here, 'vite-review-cache')")
s=s.replace("  for (const file of [html, entry]) if (fs.existsSync(file)) fs.unlinkSync(file)","  // Generated inputs retained as independent evidence.")
s=s.replace("console.log(JSON.stringify({ status:", "fs.writeFileSync(path.join(here,'status-recovery.dom.html'),await page.content());\n  await page.screenshot({path:path.join(here,'status-recovery.png'),fullPage:true});\n  fs.writeFileSync(path.join(here,'status-dom-bridge-calls.json'),JSON.stringify(record,null,2));\n  console.log(JSON.stringify({ status:")
(O/'status-recovery-dom.mjs').write_text(s,encoding='utf-8')
native=s.replace("import fs from 'node:fs'", "import {fixture as makeFixture,scope as originalScope,context as originalContext,registerDesktopCoding} from './fixture.mjs';\nimport fs from 'node:fs'")
native=native.replace('const record = []',"""const record = []
const nativeFixture=makeFixture('dom-explicit-error-go-reselection')
let resourceGeneration=0, selectedToolchain=null, privilegedPrompts=0
const ipcHandlers=new Map()
const trustedReview=()=>({resource_generation:resourceGeneration,workspace:{authorized_workspace_ref:'workspace-1',display_name:'Fixture',display_path:'C:/workspace'}})
let lastInput=null
const scopedInput=body=>({context:originalContext,review:trustedReview(),scope:{...originalScope(),coding:{...originalScope().coding,...body,checks:body.checks.map(check=>({...check,toolchain_root:selectedToolchain}))}}})
registerDesktopCoding({handle:(name,fn)=>ipcHandlers.set(name,fn)},{
 desktopManagement:nativeFixture.manager,codingSenderAllowed:()=>true,
 prepareCodingScope:async body=>{lastInput=body;return scopedInput(body)},
 recheckCodingScope:async()=>scopedInput(lastInput),
 privilegedCodingConsent:async()=>{privilegedPrompts++;return true},
 pickCodingDirectory:async()=>{nativeFixture.manager.commandIdle();selectedToolchain='C:/trusted-go-'+(++resourceGeneration);nativeFixture.setGeneration(resourceGeneration);return {selected:true,name:'go-toolchain'}}
})""")
start=native.index("  await page.exposeFunction('codingBridge'")
end=native.index("  await page.addInitScript",start)
native=native[:start]+"""  await page.exposeFunction('codingBridge', async (method,args)=>{
    record.push({method,args})
    if(method==='codingCurrent')return {ok:true,...nativeFixture.manager.codingSummary()}
    const channel={codingPickToolchain:'pickToolchain',codingPickVendor:'pickVendor',codingPrepare:'prepare',codingConfirm:'confirm',codingStatus:'status'}[method]
    if(!channel)throw new Error('unexpected '+method)
    if(method==='codingPrepare'){
      prepares++
      if(prepares===1){
        nativeFixture.setHold(true)
        const result=ipcHandlers.get('ros:desktop:coding:prepare')({},args[0])
        await new Promise(resolve=>setImmediate(resolve))
        assert.equal(nativeFixture.held.length,1)
        Object.assign(nativeFixture.held[0],{kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'first resource unavailable'}})
        nativeFixture.deliver();nativeFixture.setHold(false)
        return await result
      }
    }
    if(method==='codingConfirm')confirms++
    return await ipcHandlers.get('ros:desktop:coding:'+channel)({},args[0])
  })
"""+native[end:]
native=native.replace("assert.deepEqual(errors, [])","""assert.deepEqual(errors, [])
  assert.equal(resourceGeneration,2)
  assert.equal(privilegedPrompts,1)
  assert.equal(nativeFixture.sent[0].coding.checks[0].toolchain_root,'C:/trusted-go-1')
  assert.equal(nativeFixture.sent[1].coding.checks[0].toolchain_root,'C:/trusted-go-2')
  assert.equal(nativeFixture.manager.retiredCodingIntents[0].retireReason,'AUTHORITATIVE_PREPARE_REJECTION')
  nativeFixture.save()
  fs.writeFileSync(path.join(here,'native-repick-results.json'),JSON.stringify({pass:true,resourceGeneration,privilegedPrompts,prepares,confirms,refreshes,retired:nativeFixture.manager.retiredCodingIntents,actual_model_calls:0,actual_tool_calls:0,page_errors:errors},null,2))
""")
native=native.replace('status-recovery.dom.html','native-repick.dom.html').replace('status-recovery.png','native-repick.png').replace('status-dom-bridge-calls.json','native-dom-bridge-calls.json')
(O/'native-repick-dom.mjs').write_text(native,encoding='utf-8')
env=dict(RESEARCHOS_SHARED_ROOT=str(ROOT),RESEARCHOS_UI_SOURCE=str(B/'apps/web/src/workbench.jsx'))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 timed=pool.submit(run,'review-fixtures',[str(O/'review-fixtures.mjs')])
 run('status-recovery-dom',[str(O/'status-recovery-dom.mjs')],dict(env,ROS_STATUS_RECOVERY='1',ROS_REFRESH_FAIL_ONCE='1'))
 run('native-repick-dom',[str(O/'native-repick-dom.mjs')],dict(env,ROS_PREPARE_ERROR_REPICK='1'))
 timed.result()

