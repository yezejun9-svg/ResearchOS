import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
import assert from 'node:assert/strict'
const OUT=path.dirname(fileURLToPath(import.meta.url))
const ROOT=path.resolve(OUT,'../../../../../../..')
const WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v3-20261012')
const require=createRequire(import.meta.url)
const {chromium}=require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const {createServer}=await import(pathToFileURL(path.join(ROOT,'apps/web/node_modules/vite/dist/node/index.js')))
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
const ipc=require(path.join(WT,'apps/desktop/main/lib/ipc.js'))
process.env.RESEARCHOS_DESKTOP_WIRE_ROOT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v2-20261012/.local/w05-ui-repair-validator-final3/apps/desktop')
const server=await createServer({configFile:false,root:OUT,cacheDir:path.join(OUT,'vite-cache'),server:{host:'127.0.0.1',port:0,hmr:false,watch:{ignored:['**']},fs:{allow:[ROOT]}},resolve:{alias:[{find:/^react\/jsx-dev-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-dev-runtime.js')},{find:/^react\/jsx-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-runtime.js')},{find:/^react$/,replacement:path.join(ROOT,'apps/web/node_modules/react/index.js')},{find:/^react-dom\/client$/,replacement:path.join(ROOT,'apps/web/node_modules/react-dom/client.js')}]}})
await server.listen()
const browser=await chromium.launch({headless:true})
const facts=[]
async function scenario(name,run){
 process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'raw-http',name)
 let mode='COMPLETE',sequence=0,record=null,release=null
 const calls=[],replies=[]
 const state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}
 const h=await harness(async raw=>{
  const env=JSON.parse(raw);calls.push(env)
  const reply=pair(env.method,env.method==='host.configure'&&mode==='ACK'?'ACKNOWLEDGED':'COMPLETED').response
  reply.command_id=env.command_id;reply.session_id=env.session_id;reply.revision=env.session_id?env.expected_revision:null
  if(env.method==='host.status'){reply.result.config_revision=record?.config_revision||0;reply.result.model_configurations=record?[record]:[]}
  if(env.method==='host.configure'&&mode!=='ACK'){
    if(mode==='HELD'||mode==='HELD_NO_RECORD')await new Promise(resolve=>release=resolve)
    if(mode==='HELD_NO_RECORD')reply.result={...reply.result,...env.payload}
    else {record={...reply.result,...env.payload};reply.result=record}
  }
  return {body:reply}
 },{state})
 h.deps.commandIdFor=method=>'review-'+(++sequence)+'-'+method
 const handlers={};ipc.registerDesktopReview({handle:(name,fn)=>handlers[name]=fn},h.deps)
 const page=await browser.newPage();page.setDefaultTimeout(12000)
 const errors=[];page.on('pageerror',e=>errors.push(e.message))
 await page.exposeFunction('bridge',async(method,payload)=>{
   const reply=method==='selectProject'?await handlers['ros:desktop:selectProject'](null,payload):await ipc.callV2(h.deps,method,payload)
   replies.push({method,payload,reply});return reply
 })
 const waitFor=async(pred)=>{const end=Date.now()+12000;while(!pred()){if(Date.now()>end)throw Error('review condition timeout');await new Promise(r=>setTimeout(r,30))}}
 try{
  await page.goto(server.resolvedUrls.local[0]);await page.getByText('当前配置修订 0',{exact:false}).waitFor()
  await run({page,h,state,calls,replies,waitFor,setMode:v=>mode=v,release:()=>{assert(release);release()}})
  assert.deepEqual(errors,[])
  fs.writeFileSync(path.join(OUT,name+'.dom.html'),await page.content())
  facts.push({name,status:'CHECK_COMPLETED',http_requests:calls.length,configuration_requests:calls.filter(x=>x.method==='host.configure'),bridge_replies:replies,model_calls:0,page_errors:errors})
 }finally{if(release)release();await page.close();await h.close()}
}
async function fill(page,provider='ollama',model='qwen3:4b-instruct'){
 await page.getByLabel('提供方 ID').fill(provider);await page.getByLabel('模型 ID').fill(model);await page.getByLabel('API 基础地址').fill('http://127.0.0.1:11434/v1')
}
try{
 await scenario('whitespace-recovery',async({page,calls})=>{
  await fill(page,' ');await page.getByRole('button',{name:'保存模型配置',exact:true}).click()
  await page.getByRole('alert').waitFor();assert.equal(calls.filter(x=>x.method==='host.configure').length,0);assert.equal(await page.getByLabel('提供方 ID').isDisabled(),false)
  await page.getByLabel('提供方 ID').fill('ollama');await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByText('配置已保存（修订 1）',{exact:false}).waitFor()
  assert.equal(calls.filter(x=>x.method==='host.configure').length,1)
 })
 await scenario('ack-remount-exact-replay',async({page,calls,setMode})=>{
  setMode('ACK');await fill(page);await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByRole('button',{name:'继续同一配置命令'}).waitFor()
  await page.evaluate(()=>window.remount());await page.getByText('当前配置修订 0',{exact:false}).waitFor()
  assert.equal(await page.getByLabel('模型 ID').inputValue(),'qwen3:4b-instruct');assert.equal(await page.getByLabel('模型 ID').isDisabled(),true)
  setMode('COMPLETE');await page.getByRole('button',{name:'继续同一配置命令'}).click();await page.getByText('配置已保存（修订 1）',{exact:false}).waitFor()
  const sent=calls.filter(x=>x.method==='host.configure');assert.equal(sent.length,2);assert.deepEqual(sent[0],sent[1])
 })
 await scenario('project-switch-preserves-origin',async({page,calls,setMode})=>{
  setMode('ACK');await fill(page);await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByRole('button',{name:'继续同一配置命令'}).waitFor()
  await page.evaluate(()=>window.remount('other_project'));await page.getByText('当前配置修订 0',{exact:false}).waitFor();await fill(page,'ollama','other-model')
  await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByRole('alert').waitFor();assert.match(await page.getByRole('alert').innerText(),/COMMAND_PENDING/)
  assert.equal(await page.getByLabel('模型 ID').isDisabled(),false);assert.equal(calls.filter(x=>x.method==='host.configure').length,1)
  await page.evaluate(()=>window.remount('fixture_project'));await page.getByText('当前配置修订 0',{exact:false}).waitFor();setMode('COMPLETE')
  await page.getByRole('button',{name:'继续同一配置命令'}).click();await page.getByText('配置已保存（修订 1）',{exact:false}).waitFor()
  const sent=calls.filter(x=>x.method==='host.configure');assert.equal(sent.length,2);assert.deepEqual(sent[0],sent[1])
 })
 await scenario('inflight-remount-completion-observed',async({page,calls,replies,waitFor,setMode,release})=>{
  setMode('HELD');await fill(page);await page.getByRole('button',{name:'保存模型配置',exact:true}).click()
  await waitFor(()=>calls.some(x=>x.method==='host.configure'))
  await page.evaluate(()=>window.remount());await page.getByRole('button',{name:'继续同一配置命令'}).waitFor()
  release();await waitFor(()=>replies.some(x=>x.method==='host.configure'))
  await page.getByText('配置已保存（修订 1）',{exact:false}).waitFor()
  assert.equal(await page.getByLabel('模型 ID').isDisabled(),false)
  assert.equal(calls.filter(x=>x.method==='host.configure').length,1)
  fs.writeFileSync(path.join(OUT,'inflight-remount-completion-observed.dom.html'),await page.content())
  facts.push({finding:'OLD_COMPONENT_COMPLETION_OBSERVED_BY_NEW_COMPONENT',repaired:true,configuration_requests:1})
 })
 await scenario('stale-outcome-unproven-stays-locked',async({page,calls,replies,waitFor,setMode,release})=>{
  setMode('HELD_NO_RECORD');await fill(page);await page.getByRole('button',{name:'保存模型配置',exact:true}).click()
  await waitFor(()=>calls.some(x=>x.method==='host.configure'))
  await page.evaluate(()=>window.remount());await page.getByRole('button',{name:'继续同一配置命令'}).waitFor()
  release();await waitFor(()=>replies.some(x=>x.method==='host.configure'))
  await page.waitForTimeout(1000)
  fs.writeFileSync(path.join(OUT,'stale-debug.dom.html'),await page.content())
  fs.writeFileSync(path.join(OUT,'stale-debug.replies.json'),JSON.stringify(replies,null,2))
  await page.getByRole('alert').waitFor()
  assert.equal(await page.getByLabel('模型 ID').isDisabled(),true)
  await page.getByRole('button',{name:'核对原配置结果'}).click()
  await page.getByRole('alert').waitFor()
  assert.equal(calls.filter(x=>x.method==='host.configure').length,1)
  fs.writeFileSync(path.join(OUT,'stale-outcome-unproven-stays-locked.dom.html'),await page.content())
 })
 fs.writeFileSync(path.join(OUT,'reviewer-dom-results.json'),JSON.stringify({evidence_kind:'ACTUAL_CHROMIUM_DOM_REAL_IPC_BOUND_GO_VALIDATOR_SYNTHETIC_HTTP',facts,model_calls:0,external_calls:0},null,2)+'\n')
 console.log(JSON.stringify(facts.map(({bridge_replies,...f})=>f)))
}finally{await browser.close();await server.close()}


