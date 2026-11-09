import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
const OUT=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.resolve(OUT,'../../../../../../..');
const WT=path.join(ROOT,'.local/worktrees/w05-normal-model-ui-20261012');
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const {createServer}=await import(pathToFileURL(path.join(ROOT,'apps/web/node_modules/vite/dist/node/index.js')));
const {pair,harness}=await import(pathToFileURL(path.join(WT,'tests/ui/desktop/http-wire-boundary.test.mjs')));
const ipc=require(path.join(WT,'apps/desktop/main/lib/ipc.js'));
process.env.RESEARCHOS_DESKTOP_WIRE_ROOT=path.join(WT,'.local/w05-validator-final/apps/desktop');
process.env.RESEARCHOS_DESKTOP_CASE_RECEIPT=path.join(OUT,'raw-http');
const server=await createServer({configFile:false,root:OUT,cacheDir:path.join(OUT,'vite-cache'),server:{host:'127.0.0.1',port:0,hmr:false,watch:{ignored:['**']},fs:{allow:[ROOT]}},resolve:{alias:[{find:/^react\/jsx-dev-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-dev-runtime.js')},{find:/^react\/jsx-runtime$/,replacement:path.join(ROOT,'apps/web/node_modules/react/jsx-runtime.js')},{find:/^react$/,replacement:path.join(ROOT,'apps/web/node_modules/react/index.js')},{find:/^react-dom\/client$/,replacement:path.join(ROOT,'apps/web/node_modules/react-dom/client.js')}]}});
await server.listen();const url=server.resolvedUrls.local[0];
const browser=await chromium.launch({headless:true});
const facts=[];
async function scenario(name,run){
 let ack=false,sequence=0;const calls=[];
 const state={projectId:'fixture_project',sessionId:null,expectedRevision:null,writerEpoch:null};
 const h=await harness((raw)=>{
  const env=JSON.parse(raw);calls.push(env);const p=pair(env.method,env.method==='host.configure'&&ack?'ACKNOWLEDGED':'COMPLETED');
  p.response.command_id=env.command_id;p.response.session_id=env.session_id;p.response.revision=env.session_id?env.expected_revision:null;
  if(env.method==='host.status'){p.response.result.config_revision=0;p.response.result.model_configurations=[];}
  if(env.method==='host.configure'&&!ack){Object.assign(p.response.result,env.payload);}
  return {body:p.response};
 },{state});
 h.deps.commandIdFor=method=>'review-'+(++sequence)+'-'+method;
 const handlers={};ipc.registerDesktopReview({handle:(name,fn)=>handlers[name]=fn},h.deps);
 const page=await browser.newPage();page.setDefaultTimeout(10000);const pageErrors=[];page.on('pageerror',e=>pageErrors.push(e.message));
 await page.exposeFunction('bridge',async(method,payload)=>method==='selectProject'?handlers['ros:desktop:selectProject'](null,payload):ipc.callV2(h.deps,method,payload));
 try{
  await page.goto(url);await page.getByRole('heading',{name:'模型配置'}).waitFor();await page.getByText('当前配置修订 0',{exact:false}).waitFor();
  await run({page,h,state,calls,setAck:v=>ack=v});
  assert.deepEqual(pageErrors,[]);facts.push({name,status:'REPRODUCED',http_requests:calls.length,model_calls:0,page_errors:pageErrors});
  fs.writeFileSync(path.join(OUT,name+'.dom.html'),await page.content());
 }finally{await page.close();await h.close();}
}
async function fill(page,provider='ollama',model='qwen3:4b-instruct'){
 await page.getByLabel('提供方 ID').fill(provider);await page.getByLabel('模型 ID').fill(model);await page.getByLabel('API 基础地址').fill('http://127.0.0.1:11434/v1');
}
try{
 await scenario('local-refusal-locks-form',async({page,calls})=>{
  await fill(page,' ');await page.getByRole('button',{name:'保存模型配置',exact:true}).click();
  await page.getByRole('alert').waitFor();assert.equal(calls.filter(x=>x.method==='host.configure').length,0);
  assert.equal(await page.getByLabel('提供方 ID').isDisabled(),true);
  await page.getByRole('button',{name:'继续同一配置命令'}).click();await page.getByRole('alert').waitFor();
  assert.equal(calls.filter(x=>x.method==='host.configure').length,0);assert.equal(await page.getByLabel('提供方 ID').isDisabled(),true);
  facts.push({finding:'local refusal with zero configure HTTP calls locks malformed input',alert:await page.getByRole('alert').innerText()});
 });
 await scenario('pending-command-lost-on-remount',async({page,h,calls,setAck})=>{
  setAck(true);await fill(page);await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByRole('button',{name:'继续同一配置命令'}).waitFor();
  const first=calls.find(x=>x.method==='host.configure');assert(first);
  await page.evaluate(()=>window.remount());await page.getByRole('button',{name:'保存模型配置',exact:true}).waitFor();await page.getByText('当前配置修订 0',{exact:false}).waitFor();
  await fill(page,'ollama','different-model');await page.getByRole('button',{name:'保存模型配置',exact:true}).click();await page.getByRole('alert').waitFor();
  assert.match(await page.getByRole('alert').innerText(),/COMMAND_PENDING/);assert.equal(await page.getByLabel('模型 ID').isDisabled(),true);
  await page.getByRole('button',{name:'继续同一配置命令'}).click();assert.equal(calls.filter(x=>x.method==='host.configure').length,1);
  facts.push({finding:'remount loses original payload while IPC still holds original command',original_command_id:first.command_id,new_input:await page.getByLabel('模型 ID').inputValue()});
  setAck(false);const settled=await ipc.callV2(h.deps,'host.configure',first.payload);assert.equal(settled.completed,true);
  const sent=calls.filter(x=>x.method==='host.configure');assert.deepEqual(sent[0],sent[1]);
  facts.push({check:'direct IPC same-payload replay retains full original envelope and command_id',passed:true,command_id:sent[0].command_id});
 });
 fs.writeFileSync(path.join(OUT,'reviewer-test-results.json'),JSON.stringify({kind:'ACTUAL_CHROMIUM_DOM_REAL_IPC_SOURCE_BOUND_VALIDATOR_SYNTHETIC_HTTP',facts,model_calls:0,external_calls:0},null,2));
 console.log(JSON.stringify({facts,model_calls:0}));
}finally{await browser.close();await server.close();}
