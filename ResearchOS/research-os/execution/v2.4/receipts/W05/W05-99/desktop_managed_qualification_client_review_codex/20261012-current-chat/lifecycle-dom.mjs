import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
import {fixture} from './fixture-support.mjs'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),require=createRequire(import.meta.url)
const WT=path.join(ROOT,'.local/worktrees/w05-desktop-managed-qualification-client-20261012'),BUILD=path.join(WT,'.local/managed-client-bound-final3')
const {registerDesktopQualification}=require(path.join(BUILD,'apps/desktop/main/lib/ipc.js'))
const {chromium}=require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const {createServer}=await import(pathToFileURL(path.join(ROOT,'apps/web/node_modules/vite/dist/node/index.js')))
const server=await createServer({configFile:false,root:OUT,cacheDir:path.join(OUT,'vite-qualification-cache'),server:{host:'127.0.0.1',port:0,hmr:false,watch:{ignored:['**']},fs:{allow:[ROOT]}},resolve:{alias:[{find:/^react\/jsx-dev-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-dev-runtime.js')},{find:/^react\/jsx-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-runtime.js')},{find:/^react$/,replacement:path.join(ROOT,'apps/web/node_modules/react/index.js')},{find:/^react-dom\/client$/,replacement:path.join(ROOT,'apps/web/node_modules/react-dom/client.js')}]}})
await server.listen();const browser=await chromium.launch({headless:true}),facts=[]
try{
 for(const name of ['expired-context','summary-host-change']){
  const f=fixture('dom-'+name,{expiresSoon:name==='expired-context'}),handlers={},calls=[]
  let scope=f.scope
  registerDesktopQualification({handle:(channel,fn)=>handlers[channel]=fn},{qualifierSenderAllowed:()=>true,prepareQualificationScope:async()=>({scope,context:f.context()}),desktopManagement:f.manager})
  const page=await browser.newPage({viewport:{width:1100,height:900}});page.setDefaultTimeout(12000)
  await page.exposeFunction('managedBridge',async method=>{const suffix={qualificationCurrent:'current',qualificationPrepare:'prepare',qualificationConfirm:'confirm',qualificationStatus:'status'}[method];const result=await handlers['ros:desktop:qualification:'+suffix]({});calls.push({method,result});return result})
  await page.addInitScript(()=>{window.researchos={desktop:Object.fromEntries(['qualificationCurrent','qualificationPrepare','qualificationConfirm','qualificationStatus'].map(method=>[method,()=>window.managedBridge(method)]))}})
  try{
   if(name==='summary-host-change'){
    await f.manager.prepare(scope,f.context());await f.manager.confirm()
    fs.writeFileSync(f.discoveryFile,JSON.stringify({...f.discovery,host_instance_id:'host-bbbbbbbbbbbb',data_dir:path.join(f.dir,'different-root')}))
   }
   await page.goto(server.resolvedUrls.local[0]+'qualification-entry.html')
   if(name==='expired-context'){
    await page.getByRole('button',{name:'准备当前会话',exact:true}).click()
    await page.getByText('准备完成；模型调用尚未开始',{exact:false}).waitFor()
    f.setContext('["project-1","session-2",7,2,2]');scope={...scope,sessionId:'session-2'}
    await page.evaluate(()=>window.remount('session-2'))
    await new Promise(resolve=>setTimeout(resolve,300))
    assert(Date.parse(f.manager.intent.expiresAt)<Date.now())
    await page.getByText('项目或会话已变更，原请求保留',{exact:false}).waitFor()
    await page.getByRole('button',{name:'准备当前会话',exact:true}).click()
    await page.getByText('QUALIFICATION_INTENT_PENDING',{exact:false}).waitFor()
    assert.equal(await page.getByRole('button',{name:'明确确认一次调用',exact:true}).isDisabled(),true)
    assert.equal(await page.getByRole('button',{name:'复核原请求',exact:true}).isDisabled(),true)
    assert.equal(f.frames.filter(x=>x.direction==='desktop_to_fixture').length,1)
   }else{
    await page.getByText('最近一次复核显示用途授权',{exact:false}).waitFor()
    const current=calls.find(x=>x.method==='qualificationCurrent').result
    assert.equal(current.authorized,true);assert.equal(current.available,true)
    await page.getByRole('button',{name:'复核原请求',exact:true}).click()
    await page.getByText('HOST_CHANGED',{exact:false}).waitFor()
    assert.equal(await page.getByText('最近一次复核显示用途授权',{exact:false}).count(),1)
   }
   fs.writeFileSync(path.join(OUT,name+'.dom.html'),await page.content());await page.screenshot({path:path.join(OUT,name+'.png'),fullPage:true})
   facts.push({name,defect_reproduced:true,summary:f.manager.summary(),calls,frames:f.frames})
  }finally{await page.close()}
 }
}finally{await browser.close();await server.close();fs.writeFileSync(path.join(OUT,'lifecycle-dom-results.json'),JSON.stringify({evidence_class:'ACTUAL_CHROMIUM_BOUND_REACT_SOURCE_AND_IPC_MANAGER_SYNTHETIC_PRIVATE_FRAMES',actual_model_calls:0,external_calls:0,facts},null,2)+'\n')}
console.log(JSON.stringify({counterexamples:facts.length,cases:facts.map(x=>x.name)}))
