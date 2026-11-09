import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {fixture,scope,context,out,registerDesktopCoding} from './fixture.mjs';
const facts=[],review={workspace:{authorized_workspace_ref:'workspace-1',display_name:'Fixture',display_path:'C:/workspace'}};
const scoped=()=>({scope:scope(),context,review});
{
 const f=fixture('privileged-cancel');let prompts=0;const handlers=new Map();
 registerDesktopCoding({handle:(n,fn)=>handlers.set(n,fn)},{desktopManagement:f.manager,codingSenderAllowed:()=>true,prepareCodingScope:async()=>scoped(),recheckCodingScope:async()=>scoped(),privilegedCodingConsent:async()=>{prompts++;return false;}});
 assert.equal((await handlers.get('ros:desktop:coding:prepare')({},{})).state,'AWAITING_CODING_CONFIRMATION');
 const result=await handlers.get('ros:desktop:coding:confirm')({},{});assert.equal(result.reason,'PRIVILEGED_CONFIRM_CANCELLED');assert.equal(prompts,1);assert.equal(f.sent.length,1);
 facts.push({scenario:'privileged-cancel',result,prompts,confirm_frames:0,pass:true});f.save();
}
{
 const f=fixture('expiry-pending-barrier',{ttl:250});await f.manager.prepareCoding(scope(),context,review);await new Promise(r=>setTimeout(r,280));await f.manager.statusCoding();
 const original=f.manager.codingIntent;f.setHold(true);const pending=f.manager.statusCoding();
 await assert.rejects(f.manager.prepareCoding(scope(),context,review),{code:'MANAGEMENT_COMMAND_PENDING'});
 assert.equal(f.manager.codingIntent,original);assert.equal(f.manager.retiredCodingIntents.length,0);f.deliver();await pending;
 facts.push({scenario:'expiry-pending-barrier',pass:true,original_retained:true});f.save();
}
{
 const f=fixture('prepare-context-change-retained');f.setHold(true);const p=f.manager.prepareCoding(scope(),context,review);const id=f.held[0].result.request_id;
 f.setContext(JSON.stringify(['project-1','session-2',1,1]));f.deliver();await p;assert.equal(f.manager.codingIntent.requestId,id);
 f.setContext(context);f.setHold(false);await f.manager.statusCoding();assert.equal(f.sent.filter(x=>x.operation==='PREPARE_CODING').length,1);
 facts.push({scenario:'prepare-context-change-retained',pass:true,request_id:id,status_possible:true});f.save();
}
{
 const f=fixture('prepare-timeout-late-terminal');f.setHold(true);
 // Exercise the unchanged production 45-second PREPARE timer.
 await assert.rejects(f.manager.prepareCoding(scope(),context,review),{code:'MANAGEMENT_REPLY_UNCERTAIN'});
 const original=f.held[0].result;assert.equal(f.manager.pending.timedOut,true);f.deliver();await new Promise(r=>setImmediate(r));
 assert.equal(f.manager.pending,null);assert.equal(f.manager.codingIntent.requestId,undefined);
 await assert.rejects(f.manager.statusCoding(),{code:'CODING_PREPARE_ORIGINAL_UNRESOLVED'});
 await assert.rejects(f.manager.prepareCoding(scope(),context,review),{code:'CODING_ORIGINAL_REQUEST_PENDING'});
 facts.push({scenario:'prepare-timeout-late-terminal',defect_reproduced:true,late_request_id:original.request_id,late_request_hash:original.request_hash,active_intent:f.manager.codingIntent,pending:null,status_error:'CODING_PREPARE_ORIGINAL_UNRESOLVED',new_prepare_error:'CODING_ORIGINAL_REQUEST_PENDING',timeout_ms:45000,production_timeout_ms:45000});f.save();
}
{
 const f=fixture('prepare-authoritative-rejection');f.setHold(true);const p=f.manager.prepareCoding(scope(),context,review);
 Object.assign(f.held[0],{kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'coding source path does not exist'}});
 f.deliver();await assert.rejects(p,{code:'CODING_PREPARE_REJECTED'});assert.equal(f.manager.pending,null);
 await assert.rejects(f.manager.statusCoding(),{code:'CODING_PREPARE_ORIGINAL_UNRESOLVED'});
 await assert.rejects(f.manager.prepareCoding(scope(),context,review),{code:'CODING_ORIGINAL_REQUEST_PENDING'});
 facts.push({scenario:'prepare-authoritative-rejection',defect_reproduced:true,intent:f.manager.codingIntent,status_error:'CODING_PREPARE_ORIGINAL_UNRESOLVED',new_prepare_error:'CODING_ORIGINAL_REQUEST_PENDING'});f.save();
}
{
 const f=fixture('post-consent-await-context-switch');await f.manager.prepareCoding(scope(),context,review);
 let rechecks=0,armed=false,switched=false;const observed=f.manager.observe.bind(f.manager);
 f.manager.observe=id=>{const result=observed(id);if(armed&&!switched){switched=true;queueMicrotask(()=>f.setContext(JSON.stringify(['project-1','session-2',1,1])));}return result;};
 const result=await f.manager.confirmCoding(async()=>true,async()=>{rechecks++;if(rechecks===2)armed=true;return scoped();});
 assert.equal(switched,true);assert.equal(f.manager.sameContext(context),false);assert.equal(f.sent.filter(x=>x.operation==='CONFIRM_CODING').length,1);assert.equal(f.manager.codingIntent.state,'CODING_CONFIGURED');
 facts.push({scenario:'post-consent-await-context-switch',defect_reproduced:true,synthetic_schedule:'During final native observation enqueue selection change microtask; runs after inner guard and before outer await continuation.',rechecks,context_changed_before_send:true,confirm_frames:1,result});f.save();
}
fs.writeFileSync(path.join(out,'review-fixtures-results.json'),JSON.stringify({facts,actual_model_calls:0,actual_tool_calls:0,note:'Defect cases exit zero means reproduced, not product PASS.'},null,2));console.log(JSON.stringify({passed_closures:facts.filter(x=>x.pass).length,reproduced_defects:facts.filter(x=>x.defect_reproduced).length,actual_model_calls:0}));

