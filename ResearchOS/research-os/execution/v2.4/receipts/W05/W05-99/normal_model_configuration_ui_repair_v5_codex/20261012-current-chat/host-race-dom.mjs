import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {fileURLToPath,pathToFileURL} from 'node:url'
import {createRequire} from 'node:module'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..')
const WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-repair-v5-20261012'),require=createRequire(import.meta.url)
const {chromium}=require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package')
const {createServer}=await import(pathToFileURL(path.join(ROOT,'apps/web/node_modules/vite/dist/node/index.js')))
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')))
const ipc=require(path.join(WT,'apps/desktop/main/lib/ipc.js'))
const server=await createServer({configFile:false,root:OUT,cacheDir:path.join(OUT,'vite-cache'),server:{host:'127.0.0.1',port:0,hmr:false,watch:{ignored:['**']},fs:{allow:[ROOT]}},resolve:{alias:[{find:/^react\/jsx-dev-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-dev-runtime.js')},{find:/^react\/jsx-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-runtime.js')},{find:/^react$/,replacement:path.join(ROOT,'apps/web/node_modules/react/index.js')},{find:/^react-dom\/client$/,replacement:path.join(ROOT,'apps/web/node_modules/react-dom/client.js')}]}})
await server.listen();const browser=await chromium.launch({headless:true});const facts=[]
try {
for(const variant of [
 {name:'stale-before-reply-different-ref',remount:true,sameRef:false,afterReply:false},
 {name:'completed-before-reply-same-ref',remount:false,sameRef:true,afterReply:false},
 {name:'stale-before-reply-same-ref',remount:true,sameRef:true,afterReply:false},
 {name:'completed-before-reply-different-ref',remount:false,sameRef:false,afterReply:false},
 {name:'stale-after-reply-different-ref',remount:true,sameRef:false,afterReply:true},
 {name:'completed-after-reply-same-ref',remount:false,sameRef:true,afterReply:true},
]){
 const {name,remount,sameRef,afterReply}=variant
 process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'host-race-http',name)
 let sequence=0,release,originalPayload,discovery,recordA=null
 const calls=[],replies=[],state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null}
 const payload={config_revision:1,provider_id:'ollama',base_url:'http://127.0.0.1:11434/v1',model_id:'qwen3:4b-instruct',credential_ref:null}
 const recordB={...pair('host.configure').response.result,...payload,model_config_ref:sameRef?'fixture_config_1':'different_host_config'}
 const makeReply=(env)=>{const reply=pair(env.method).response;reply.command_id=env.command_id;reply.session_id=env.session_id;reply.revision=env.session_id?env.expected_revision:null;return reply}
 const a=await harness(async raw=>{
  const env=JSON.parse(raw);calls.push({host:'A',env});const reply=makeReply(env)
  if(env.method==='host.configure'){originalPayload=env.payload;await new Promise(resolve=>release=resolve);recordA={...reply.result,...env.payload};reply.result=recordA}
  else{reply.result.host_instance_id='host-aaaaaaaaaaaa';reply.result.config_revision=recordA?.config_revision||0;reply.result.model_configurations=recordA?[recordA]:[]}
  return {body:reply}
 },{state})
 const b=await harness(async raw=>{
  const env=JSON.parse(raw);calls.push({host:'B',env});assert.equal(env.method,'host.status','new host must not receive original configure')
  const reply=makeReply(env);Object.assign(reply.result,{host_instance_id:'host-bbbbbbbbbbbb',config_revision:1,model_configurations:[recordB]});return {body:reply}
 },{state})
 discovery={url:a.url,pid:1234,data_dir:'fixture-data-A',host_instance_id:'host-aaaaaaaaaaaa'}
 const switchToB=()=>{discovery={url:b.url,pid:2222,data_dir:'fixture-data-B',host_instance_id:'host-bbbbbbbbbbbb'}}
 a.deps.fsImpl.readFileSync=()=>JSON.stringify(discovery);a.deps.commandIdFor=method=>'host-race-'+(++sequence)+'-'+method
 const handlers={};ipc.registerDesktopReview({handle:(name,fn)=>handlers[name]=fn},a.deps)
 const page=await browser.newPage();page.setDefaultTimeout(10000)
 await page.exposeFunction('bridge',async(method,payload)=>{const reply=method==='selectProject'?await handlers['ros:desktop:selectProject'](null,payload):await ipc.callV2(a.deps,method,payload);if(method==='host.configure'&&afterReply)switchToB();replies.push({method,payload,reply});return reply})
 const wait=async f=>{const end=Date.now()+10000;while(!f()){if(Date.now()>end)throw Error('condition timeout');await new Promise(r=>setTimeout(r,25))}}
 try{
  await page.goto(server.resolvedUrls.local[0]);await page.getByText('当前配置修订 0',{exact:false}).waitFor()
  await page.getByLabel('提供方 ID').fill(payload.provider_id);await page.getByLabel('模型 ID').fill(payload.model_id);await page.getByLabel('API 基础地址').fill(payload.base_url)
  await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await wait(()=>release)
  if(!afterReply)switchToB()
  if(remount){await page.evaluate(()=>window.remount());await page.getByRole('button',{name:'继续同一配置命令'}).waitFor();await wait(()=>ipc.callV2.sequences.get(state)>3)}
  release();await page.getByRole('alert').waitFor()
  assert.equal(await page.getByLabel('模型 ID').isDisabled(),true)
  assert.equal(await page.getByRole('button',{name:'核对原配置结果'}).count(),1)
  assert.equal(calls.filter(x=>x.env.method==='host.configure').length,1)
  assert(calls.some(x=>x.host==='B'&&x.env.method==='host.status'))
  const configureReply=replies.find(x=>x.method==='host.configure').reply
  assert.equal(remount?configureReply.reason:configureReply.protocol_status,remount?'STALE_RESPONSE':'COMPLETED')
  fs.writeFileSync(path.join(OUT,name+'-blocked-on-B.dom.html'),await page.content())
  discovery={url:a.url,pid:9999,data_dir:'fixture-data-A',host_instance_id:'host-aaaaaaaaaaaa'}
  await page.getByRole('button',{name:'核对原配置结果'}).click()
  await page.getByText('配置已保存（修订 1）',{exact:false}).waitFor()
  assert.equal(await page.getByLabel('模型 ID').isDisabled(),false)
  assert.equal(calls.filter(x=>x.env.method==='host.configure').length,1)
  facts.push({name,repaired:true,variant,original_host:'host-aaaaaaaaaaaa',new_host:'host-bbbbbbbbbbbb',originalPayload,recordA,recordB,configureReply,calls,replies})
  fs.writeFileSync(path.join(OUT,name+'-reconciled-on-A.dom.html'),await page.content())
 }finally{if(release)release();await page.close();await a.close();await b.close()}
}
fs.writeFileSync(path.join(OUT,'host-race-results.json'),JSON.stringify({evidence_class:'V5_IPC_AND_ACTUAL_DOM_WITH_FROZEN_V2_GO_VALIDATOR_SYNTHETIC_HTTP',current_v5_full_build_binding:true,model_calls:0,external_calls:0,facts},null,2)+'\n')
console.log(JSON.stringify(facts.map(({calls,replies,...f})=>f)))
}finally{await browser.close();await server.close()}
