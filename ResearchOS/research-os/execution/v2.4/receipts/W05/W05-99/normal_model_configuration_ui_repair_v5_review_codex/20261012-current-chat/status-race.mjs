import fs from 'node:fs'
import path from 'node:path'
import http from 'node:http'
import crypto from 'node:crypto'
import assert from 'node:assert/strict'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..')
const WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v5-20261012'),BUILD=path.join(WT,'.local/v5-bound-build-1'),require=createRequire(import.meta.url)
const {chromium}=require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
// Use the modules inside the verified full-bound build, not an edited implementation.
const ipc=require(path.join(BUILD,'apps/desktop/main/lib/ipc.js'))
const {createServer}=await import(pathToFileURL(path.join(ROOT,'apps/web/node_modules/vite/dist/node/index.js')))
const dev=await createServer({configFile:false,root:OUT,cacheDir:path.join(OUT,'status-race-cache'),server:{host:'127.0.0.1',port:0,hmr:false,watch:{ignored:['**']},fs:{allow:[ROOT]}},resolve:{alias:[{find:/^react\/jsx-dev-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-dev-runtime.js')},{find:/^react\/jsx-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-runtime.js')},{find:/^react$/,replacement:path.join(ROOT,'apps/web/node_modules/react/index.js')},{find:/^react-dom\/client$/,replacement:path.join(ROOT,'apps/web/node_modules/react-dom/client.js')}]}})
await dev.listen()
const dist=path.join(BUILD,'apps/web/dist'),servedAssets=[]
const built=http.createServer((req,res)=>{
 const name=new URL(req.url,'http://localhost').pathname
 if(name.startsWith('/api/')||name.startsWith('/v1/')){res.writeHead(404,{'Content-Type':'application/json'});res.end(JSON.stringify({code:'UNIMPLEMENTED_FIXTURE_READ',message:'Public fixture has no ancillary REST data'}));return}
 const p=name.startsWith('/assets/')?path.join(dist,path.basename(path.dirname(name)),path.basename(name)):path.join(dist,'index.html')
 const bytes=fs.readFileSync(p);servedAssets.push({path:p,sha256:crypto.createHash('sha256').update(bytes).digest('hex')})
 res.writeHead(200,{'Content-Type':p.endsWith('.js')?'application/javascript':p.endsWith('.css')?'text/css':'text/html'});res.end(bytes)
})
await new Promise(resolve=>built.listen(0,'127.0.0.1',resolve))
const browser=await chromium.launch({headless:true}),facts=[]
const wait=async pred=>{const end=Date.now()+15000;while(!pred()){if(Date.now()>end)throw Error('condition timeout');await new Promise(r=>setTimeout(r,25))}}
try{
 for(const variant of [{name:'component-status-response-switch',built:false,credential:false},{name:'component-status-credential-switch',built:false,credential:true},{name:'compiled-ui-status-response-switch',built:true,credential:false}]){
  const {name}=variant
  process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'status-race-http',name)
  let discovery,recordA=null,releaseStatus,sequence=0,statusSwitchDone=false
  const state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null},calls=[],replies=[]
  const makeReply=env=>{const reply=pair(env.method).response;reply.command_id=env.command_id;reply.session_id=env.session_id;reply.revision=env.session_id?env.expected_revision:null;return reply}
  const a=await harness(async raw=>{
   const env=JSON.parse(raw);calls.push({host:'A',env});const reply=makeReply(env)
   if(env.method==='host.configure'){recordA={...reply.result,...env.payload};reply.result=recordA}
   else if(env.method==='host.status'){
    Object.assign(reply.result,{host_instance_id:'host-aaaaaaaaaaaa',config_revision:recordA?.config_revision||0,model_configurations:recordA?[recordA]:[]})
    if(recordA&&!variant.credential&&!statusSwitchDone){await new Promise(resolve=>releaseStatus=resolve);statusSwitchDone=true}
   }else if(env.method==='session.list'){reply.result.items=[]}
   return {body:reply}
  },{state})
  const b=await harness(async raw=>{const env=JSON.parse(raw);calls.push({host:'B',env});assert.equal(env.method,'host.status');const reply=makeReply(env);Object.assign(reply.result,{host_instance_id:'host-bbbbbbbbbbbb',config_revision:0,model_configurations:[]});return {body:reply}},{state})
  discovery={url:a.url,pid:1111,data_dir:'fixture-data-A',host_instance_id:'host-aaaaaaaaaaaa'}
  const switchB=()=>{discovery={url:b.url,pid:2222,data_dir:'fixture-data-B',host_instance_id:'host-bbbbbbbbbbbb'}}
  a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);a.deps.commandIdFor=method=>'status-race-'+(++sequence)+'-'+method
  if(variant.credential)a.deps.credentialFor=async()=>{if(recordA&&!statusSwitchDone){switchB();statusSwitchDone=true}return 'public-fixture-only'}
  const handlers={};ipc.registerDesktopReview({handle:(channel,fn)=>handlers[channel]=fn},a.deps)
  const page=await browser.newPage();page.setDefaultTimeout(15000);const pageErrors=[];page.on('pageerror',e=>pageErrors.push(e.message))
  await page.route('**/*',route=>{const url=new URL(route.request().url());if(url.hostname!=='127.0.0.1')throw Error('external request prohibited');return route.continue()})
  await page.exposeFunction('bridge',async(method,payload)=>{
   const reply=method==='selectProject'?await handlers['ros:desktop:selectProject'](null,payload):method==='context'?await handlers['ros:desktop:context']():await ipc.callV2(a.deps,method,payload)
   replies.push({method,payload,reply,discoveryAtReturn:{...discovery}});return reply
  })
  if(variant.built)await page.addInitScript(()=>{window.researchos={desktop:{context:()=>window.bridge('context'),selectProject:project_id=>window.bridge('selectProject',{project_id})},v2:new Proxy({}, {get:(_target,method)=>payload=>window.bridge(method,payload)})}})
  try{
   await page.goto(variant.built?'http://127.0.0.1:'+built.address().port+'/p/fixture_project':dev.resolvedUrls.local[0])
   await page.getByLabel('提供方 ID').waitFor()
   await page.getByLabel('提供方 ID').fill('ollama');await page.getByLabel('模型 ID').fill('qwen3:4b-instruct');await page.getByLabel('API 基础地址').fill('http://127.0.0.1:11434/v1')
   await page.getByRole('button',{name:'保存模型配置',exact:true}).click()
   if(!variant.credential){await wait(()=>releaseStatus);switchB();releaseStatus()}
   await page.getByRole('button',{name:'核对原配置结果',exact:true}).waitFor()
   await wait(()=>replies.some(x=>x.method==='host.status'&&['HOST_CHANGED_BEFORE_SEND','HOST_CHANGED_DURING_STATUS'].includes(x.reply.reason)))
   assert.equal(discovery.host_instance_id,'host-bbbbbbbbbbbb')
   assert.equal(calls.filter(x=>x.env.method==='host.configure').length,1)
   assert.equal(calls.filter(x=>x.host==='B').length,0)
   assert.equal(await page.getByText('配置已保存（修订 1）',{exact:false}).count(),0)
   assert.equal(await page.getByLabel('模型 ID').isDisabled(),true)
   assert.equal(await page.getByLabel('模型 ID').inputValue(),'qwen3:4b-instruct')
   const lastStatus=replies.filter(x=>x.method==='host.status').at(-1)
   assert.equal(lastStatus.discoveryAtReturn.host_instance_id,'host-bbbbbbbbbbbb')
   assert.equal(lastStatus.reply.local_host_origin,replies.find(x=>x.method==='host.configure').reply.local_host_origin)
   assert.equal(lastStatus.reply.ok,false)
   assert.equal(lastStatus.reply.reason,variant.credential?'HOST_CHANGED_BEFORE_SEND':'HOST_CHANGED_DURING_STATUS')
   assert.equal(lastStatus.reply.result,undefined)
   fs.writeFileSync(path.join(OUT,name+'-blocked-on-B.dom.html'),await page.content())
   await page.screenshot({path:path.join(OUT,name+'-blocked-on-B.png'),fullPage:true})
   // Explicit recheck on B must retain the original terminal intent as well.
   await page.getByRole('button',{name:'核对原配置结果',exact:true}).click()
   await wait(()=>calls.some(x=>x.host==='B'))
   await page.getByText('主机已切换；原配置只能在原主机核对',{exact:false}).waitFor()
   assert.equal(await page.getByLabel('模型 ID').isDisabled(),true)
   const currentOnB={...discovery}
   discovery={url:a.url,pid:9999,data_dir:'fixture-data-A',host_instance_id:'host-aaaaaaaaaaaa'}
   await page.getByRole('button',{name:'核对原配置结果',exact:true}).click()
   await page.getByText('配置已保存（修订 1）',{exact:false}).first().waitFor()
   assert.equal(calls.filter(x=>x.env.method==='host.configure').length,1)
   if(!variant.built)assert.equal(await page.getByLabel('模型 ID').isDisabled(),false)
   else assert.equal(await page.getByLabel('提供方 ID').count(),0,'compiled parent accepts configuration only after returning to A')
   const fact={name,repaired:true,variant,recordA,blockedDiscovery:currentOnB,recoveredDiscovery:discovery,configurationRequests:calls.filter(x=>x.env.method==='host.configure'),calls,replies,pageErrors}
   facts.push(fact)
   fs.writeFileSync(path.join(OUT,name+'.dom.html'),await page.content())
   await page.screenshot({path:path.join(OUT,name+'.png'),fullPage:true})
  }finally{if(releaseStatus)releaseStatus();await page.close();await a.close();await b.close()}
 }
}finally{
 fs.writeFileSync(path.join(OUT,'status-race-results.json'),JSON.stringify({evidence_class:'ACTUAL_CHROMIUM_DOM_BOUND_V5_IPC_AND_GO_VALIDATOR_SYNTHETIC_HTTP',compiled_ui_exercised:facts.some(x=>x.variant.built),model_calls:0,external_calls:0,servedAssets,facts},null,2)+'\n')
 await browser.close();await dev.close();await new Promise(resolve=>built.close(resolve))
}
console.log(JSON.stringify({repaired:facts.length,cases:facts.map(x=>x.name)}))
