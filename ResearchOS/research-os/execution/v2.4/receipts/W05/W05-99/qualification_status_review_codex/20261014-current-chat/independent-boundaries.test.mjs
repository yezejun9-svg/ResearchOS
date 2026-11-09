import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const require=createRequire(import.meta.url), review=path.dirname(fileURLToPath(import.meta.url));
const source=process.env.REVIEW_SOURCE_ROOT;
const {createDesktopManagement}=require(path.join(source,'apps/desktop/main/lib/desktop-management.js'));
const {registerDesktopQualification}=require(path.join(source,'apps/desktop/main/lib/ipc.js'));
const H='sha256:'+'b'.repeat(64), P='researchos-desktop-management/1';
const ctx=(v={})=>JSON.stringify(Object.assign(['p','s','1','1','desktop-shell','2026-10-14T00:00:00Z',2,4],v));
const scope={projectId:'p',sessionId:'s',modelRef:'m',model:{provider_id:'fixture',model_id:'fixture'}};
function fixture(){
 const dir=fs.mkdtempSync(path.join(review,'independent-fixture-')),discovery=path.join(dir,'discovery.json');
 let context=ctx(),suppress=false,mutate=x=>x;const log=[],queue=[];
 const child=new EventEmitter();child.pid=24680;
 const ident=id=>({PID:id,CreatedNS:String(id)+'000000000',ImageSHA256:'a'.repeat(64)});
 const manager=createDesktopManagement({fsImpl:fs,discoveryFile:discovery,dataRoot:dir,context:()=>context,observeProcess:id=>id===child.pid?manager.identity:manager.parentIdentity});
 manager.child=child;manager.identity=ident(child.pid);manager.parentIdentity=ident(process.pid);manager.hostId='host-aaaaaaaaaaaa';manager.state='READY';manager.childExited=false;
 const publish=()=>fs.writeFileSync(discovery,JSON.stringify({url:'http://127.0.0.1:54321/',pid:child.pid,data_dir:manager.options.dataRoot,host_instance_id:manager.hostId}));publish();
 child.stdin={write(bytes,callback){const f=JSON.parse(bytes);log.push(f);let result;
  if(f.operation==='PREPARE')result={state:'AWAITING_CONFIRMATION',request:{request_id:'r',project_id:'p',session_id:'s',model_config_ref:'m',owner_host:manager.hostId,authorize_purpose:'mu_turn',issued_at:new Date(Date.now()-1000).toISOString(),expires_at:new Date(Date.now()+55000).toISOString()},request_hash:H,model_calls:1,tools:[],purpose:'mu_turn',purpose_seconds:600,cost_basis:'UNKNOWN',money:null};
  else if(f.operation==='STATUS')result={request_id:'r',request_hash:H,state:'QUALIFIED_PURPOSE_AUTHORIZED',consumed:true};else result={state:'EXECUTION_SETTLED'};
  const answer={protocol:P,message_id:f.message_id,operation:f.operation,host_id:manager.hostId,kind:'RESULT',result};
  if(suppress)queue.push(answer);else setImmediate(()=>manager.onLine(Buffer.from(JSON.stringify(mutate(answer)))));callback?.();return true;
 }};
 return {manager,log,publish,dir,setContext:v=>context=v,hold:()=>suppress=true,transform:fn=>mutate=fn,release:fn=>{const answer=queue.shift();manager.onLine(Buffer.from(JSON.stringify(fn?fn(answer):answer)))},close(){if(manager.pending?.timer)clearTimeout(manager.pending.timer);assert(fs.realpathSync(dir).startsWith(fs.realpathSync(review)+path.sep));fs.rmSync(dir,{recursive:true,force:true})}};
}
async function settled(f){await f.manager.prepare(scope,ctx());await f.manager.confirm();assert.equal(f.log.filter(x=>x.operation==='CONFIRM').length,1)}
test('independent: historical STATUS ERROR retains consumed barrier and invalidates fresh authority',async()=>{
 const f=fixture();try{await settled(f);const checked=f.manager.intent.checkedAt;f.setContext(ctx({2:'2',7:5}));f.transform(a=>({...a,kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'original Owner unavailable'}}));
 await assert.rejects(f.manager.status(),{code:'STATUS_REJECTED'});assert.equal(f.manager.intent.confirmSent,true);assert.equal(f.manager.intent.checkedAt,checked);assert.equal(f.manager.intent.needsRecheck,true);assert.equal(f.manager.summary().authorized,false);assert.equal(f.manager.summary().original_checked_at,null);await assert.rejects(f.manager.confirm(),{code:'CONFIRM_NOT_AVAILABLE'});assert.equal(f.log.filter(x=>x.operation==='CONFIRM').length,1);
 }finally{f.close()}});
test('independent: history-to-original transition during reply cannot claim authorization',async()=>{
 const f=fixture();try{await settled(f);f.setContext(ctx({2:'2',7:5}));f.hold();const pending=f.manager.status();f.setContext(ctx());f.release();const result=await pending;assert.equal(result.status_scope,'CURRENT_CONTEXT');assert.equal(result.authorized,false);assert.equal(result.checked_at,null);assert.equal(f.manager.intent.checkedContext,null)}finally{f.close()}});
test('independent: returning to same IDs with new selection generation is rejected in flight',async()=>{
 const f=fixture();try{await settled(f);f.hold();const pending=f.manager.status();f.setContext(ctx({1:'other',6:3}));f.setContext(ctx({6:4}));f.release();await assert.rejects(pending,{code:'CONTEXT_CHANGED'});assert.equal(f.manager.intent.needsRecheck,true);assert.equal(f.manager.summary().authorized,false)}finally{f.close()}});
test('independent: host ID, data root, parent and control identity replacements are blocked before and after STATUS',async()=>{
 for(const facet of ['host','root','parent','control'])for(const during of [false,true]){const f=fixture();try{await settled(f);f.setContext(ctx({7:5}));f.hold();const before=f.log.length,pending=during?f.manager.status():null;
 if(facet==='host')f.manager.hostId='host-bbbbbbbbbbbb';if(facet==='root')f.manager.options.dataRoot=path.join(f.dir,'other-root');if(facet==='parent')f.manager.parentIdentity={...f.manager.parentIdentity,CreatedNS:'999999999'};if(facet==='control')f.manager.identity={...f.manager.identity,CreatedNS:'999999999'};f.publish();
 if(during)f.release(a=>({...a,host_id:f.manager.hostId}));await assert.rejects(pending||f.manager.status(),{code:'QUALIFICATION_ORIGIN_CHANGED'},facet);assert.equal(f.log.length,before+Number(during));assert.equal(f.manager.summary().authorized,false);assert.equal(f.manager.intent.confirmSent,true);
 }finally{f.close()}}});
test('independent: actual IPC sender guard refuses renderer supplied request and never dispatches',async()=>{
 const f=fixture();try{await settled(f);const handlers=new Map();registerDesktopQualification({handle:(name,fn)=>handlers.set(name,fn)},{qualifierSenderAllowed:()=>false,desktopManagement:f.manager});const before=f.log.length;const result=await handlers.get('ros:desktop:qualification:status')({}, {request_id:'foreign',request_hash:H});assert.deepEqual(result,{ok:false,reason:'DESKTOP_ORIGIN_REQUIRED'});assert.equal(f.log.length,before)}finally{f.close()}});
test('independent: consumed=false awaiting STATUS cannot restore CONFIRM after consumption',async()=>{
 const f=fixture();try{await settled(f);f.setContext(ctx({4:'other-writer',5:'2000-01-01T00:00:00Z',7:9}));f.transform(a=>({...a,result:{...a.result,state:'AWAITING_CONFIRMATION',consumed:false}}));const out=await f.manager.status();assert.equal(out.consumed,true);assert.equal(out.authorized,false);assert.equal(out.status_scope,'ORIGINAL_REQUEST_HISTORY');assert.equal(f.manager.intent.context,ctx());await assert.rejects(f.manager.confirm(),{code:'CONFIRM_NOT_AVAILABLE'})}finally{f.close()}});
test('independent: truncated or extended contexts cannot relax original writer context',async()=>{
 for(const length of [4,7,9]){const f=fixture();try{await settled(f);const values=JSON.parse(ctx());values[2]='2';values.length=length;f.setContext(JSON.stringify(values));const before=f.log.length;await assert.rejects(f.manager.status(),{code:'CONTEXT_CHANGED'});assert.equal(f.log.length,before)}finally{f.close()}}});
