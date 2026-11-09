import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {fileURLToPath} from 'node:url'
import {createRequire} from 'node:module'
import {fixture} from './fixture-support.mjs'
const OUT=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.resolve(OUT,'../../../../../../..'),require=createRequire(import.meta.url)
const BUILD=path.join(ROOT,'.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012/.local/managed-client-repair-v2-bound-final')
const {registerDesktopQualification}=require(path.join(BUILD,'apps/desktop/main/lib/ipc.js'))
const facts=[],sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))
const record=(name,f,extra={})=>facts.push({name,passed:true,summary:f.manager.summary(),frames:f.frames,...extra})
const operations=f=>f.frames.filter(x=>x.direction==='desktop_to_fixture').map(x=>JSON.parse(x.raw).operation)
function handlers(f,overrides={}){
 const h={};registerDesktopQualification({handle:(name,fn)=>h[name]=fn},{qualifierSenderAllowed:()=>true,desktopManagement:overrides.manager||f.manager,prepareQualificationScope:async()=>({scope:f.scope,context:f.context()})});return h
}
const switched=f=>fs.writeFileSync(f.discoveryFile,JSON.stringify({...f.discovery,host_instance_id:'host-bbbbbbbbbbbb',data_dir:path.join(f.dir,'different-root')}))
const restored=f=>fs.writeFileSync(f.discoveryFile,JSON.stringify(f.discovery))

{
 const f=fixture('expired-context',{expiresSoon:true});await f.manager.prepare(f.scope,f.context())
 const original={...f.manager.intent};f.setContext('["project-1","session-2",7,2,2]');await sleep(300)
 assert(Date.parse(original.expiresAt)<Date.now());await assert.rejects(f.manager.status(),{code:'CONTEXT_CHANGED'});await assert.rejects(f.manager.confirm(),{code:'CONTEXT_CHANGED'})
 assert.equal(f.manager.summary().state,'EXPIRED');assert.equal(f.manager.summary().request_id,original.requestId)
 const next=await f.manager.prepare({...f.scope,sessionId:'session-2'},f.context())
 assert.notEqual(next.request_id,original.requestId);assert.equal(next.previous_request_id,original.requestId)
 assert.equal(f.manager.retiredIntents[0].requestHash,original.requestHash);assert.equal(Object.isFrozen(f.manager.retiredIntents[0]),true)
 assert.deepEqual(operations(f),['PREPARE','PREPARE']);record('original-P2-001-real-expiry-context-recovery',f,{original,next})
}
{
 const f=fixture('summary-host-change');await f.manager.prepare(f.scope,f.context());await f.manager.confirm()
 assert.equal(f.manager.summary().authorized,true);const original=f.manager.intent.requestId,h=handlers(f)
 switched(f);const current=await h['ros:desktop:qualification:current']({});assert.equal(current.authorized,false);assert.equal(current.available,false);assert.equal(current.state,'HOST_UNAVAILABLE');assert.equal(current.request_id,original)
 await assert.rejects(f.manager.status(),{code:'HOST_CHANGED'});restored(f);assert.equal(f.manager.summary().authorized,false)
 assert.equal((await f.manager.status()).authorized,true);assert.equal(operations(f).filter(x=>x==='CONFIRM').length,1)
 record('original-P2-002-host-switch-current-recheck',f,{blocked:current})
}
{
 const f=fixture('uncertain-status',{expiresSoon:true});await f.manager.prepare(f.scope,f.context());f.hold('STATUS')
 const pending=f.manager.exchange('STATUS',{project_id:'project-1',request_id:f.manager.intent.requestId,request_hash:f.manager.intent.requestHash},15)
 await assert.rejects(pending,{code:'MANAGEMENT_REPLY_UNCERTAIN'});await sleep(250);const original=f.manager.intent.requestId
 assert.equal(f.manager.summary().state,'PRIVATE_COMMAND_UNCERTAIN');await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'QUALIFICATION_INTENT_PENDING'})
 assert.equal(f.manager.intent.requestId,original);assert.equal(f.manager.retiredIntents.length,0)
 f.release();await sleep(0);assert.equal(f.manager.pending,null)
 const next=await f.manager.prepare(f.scope,f.context());assert.notEqual(next.request_id,original);assert.equal(next.previous_request_id,original)
 assert.deepEqual(operations(f),['PREPARE','STATUS','PREPARE']);record('real-read-timeout-blocks-expiry-until-original-terminal',f)
}
{
 const f=fixture('uncertain-confirm',{expiresSoon:true});await f.manager.prepare(f.scope,f.context());f.hold('CONFIRM')
 const originalExchange=f.manager.exchange.bind(f.manager)
 f.manager.exchange=(op,scope,timeout)=>originalExchange(op,scope,op==='CONFIRM'?15:timeout)
 await assert.rejects(f.manager.confirm(),{code:'MANAGEMENT_REPLY_UNCERTAIN'});await sleep(250)
 const original=f.manager.intent.requestId;await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'QUALIFICATION_INTENT_PENDING'})
 f.release();await sleep(0);assert.equal(f.manager.pending,null);await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'QUALIFICATION_INTENT_PENDING'})
 f.setStatus('EXPIRED',false);await f.manager.status();assert.equal(f.manager.intent.confirmSent,true)
 await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'QUALIFICATION_INTENT_PENDING'});await assert.rejects(f.manager.confirm(),{code:'CONFIRM_NOT_AVAILABLE'})
 assert.equal(f.manager.intent.requestId,original);assert.equal(f.manager.retiredIntents.length,0);assert.equal(operations(f).filter(x=>x==='CONFIRM').length,1)
 record('consumed-confirm-monotonic-after-real-timeout-late-terminal-and-expiry',f)
}
{
 const f=fixture('retire-host-change',{expiresSoon:true});await f.manager.prepare(f.scope,f.context());await sleep(300)
 switched(f);await assert.rejects(f.manager.prepare(f.scope,f.context()),{code:'HOST_CHANGED'});assert.equal(f.manager.retiredIntents.length,0)
 restored(f);await f.manager.prepare(f.scope,f.context());assert.equal(f.manager.retiredIntents.length,1);record('expiry-cannot-retire-on-other-host',f)
}
{
 const f=fixture('current-microtask');await f.manager.prepare(f.scope,f.context());await f.manager.confirm();const h=handlers(f)
 const reply=h['ros:desktop:qualification:current']({});switched(f)
 const current=await reply;assert.equal(current.authorized,false);assert.equal(current.state,'HOST_UNAVAILABLE');record('current-IPC-native-switch-during-await-microtask',f,{current})
}
{
 const f=fixture('status-microtask');await f.manager.prepare(f.scope,f.context());await f.manager.confirm()
 const h=handlers(f,{manager:{summary:()=>f.manager.summary(),status:async()=>{const result=await f.manager.status();assert.equal(result.authorized,true);queueMicrotask(()=>switched(f));return result}}})
 const reply=await h['ros:desktop:qualification:status']({});assert.equal(reply.authorized,false);assert.equal(reply.state,'HOST_UNAVAILABLE');record('STATUS-IPC-switch-after-action-before-reply',f,{reply})
}
fs.writeFileSync(path.join(OUT,'lifecycle-edge-results.json'),JSON.stringify({evidence_class:'BOUND_CLIENT_MODULE_PUBLIC_IN_PROCESS_FRAMES_NOT_CORE_OR_MODEL',actual_model_calls:0,external_calls:0,facts},null,2)+'\n')
console.log(JSON.stringify({passed:facts.length,cases:facts.map(x=>x.name)}))
