import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {fixture,scope,context,out,registerDesktopCoding} from './fixture.mjs';
const facts=[],review=(generation=0)=>({resource_generation:generation,workspace:{authorized_workspace_ref:'workspace-1',display_name:'Fixture',display_path:'C:/workspace'}});
const scoped=(generation=0)=>({scope:scope(),context,review:review(generation)});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function done(f,name,extra={}){f.save();facts.push({scenario:name,pass:true,...extra});console.log(JSON.stringify({scenario:name,pass:true}));}
{
 const f=fixture('privileged-cancel');let prompts=0;const handlers=new Map();
 registerDesktopCoding({handle:(n,fn)=>handlers.set(n,fn)},{desktopManagement:f.manager,codingSenderAllowed:()=>true,prepareCodingScope:async()=>scoped(),recheckCodingScope:async()=>scoped(),privilegedCodingConsent:async()=>{prompts++;return false;}});
 assert.equal((await handlers.get('ros:desktop:coding:prepare')({},{})).state,'AWAITING_CODING_CONFIRMATION');
 assert.equal((await handlers.get('ros:desktop:coding:confirm')({},{})).reason,'PRIVILEGED_CONFIRM_CANCELLED');
 assert.equal(prompts,1);assert.equal(f.sent.length,1);assert.equal(f.manager.codingIntent.confirmSent,false);
 done(f,'privileged-cancel',{prompts,confirm_frames:0});
}
{
 const f=fixture('expiry-pending-barrier',{ttl:250});await f.manager.prepareCoding(scope(),context,review());await sleep(280);await f.manager.statusCoding();
 const original=f.manager.codingIntent;f.setHold(true);const pending=f.manager.statusCoding();
 await assert.rejects(f.manager.prepareCoding(scope(),context,review()),{code:'MANAGEMENT_COMMAND_PENDING'});
 assert.equal(f.manager.codingIntent,original);assert.equal(f.manager.retiredCodingIntents.length,0);f.deliver();await pending;
 done(f,'expiry-pending-barrier',{original_retained:true});
}
{
 const f=fixture('prepare-context-change-retained');f.setHold(true);const p=f.manager.prepareCoding(scope(),context,review());const id=f.held[0].result.request_id;
 f.setContext(JSON.stringify(['project-1','session-2',1,1]));f.deliver();await p;assert.equal(f.manager.codingIntent.requestId,id);
 f.setContext(context);f.setHold(false);await f.manager.statusCoding();assert.equal(f.sent.filter(x=>x.operation==='PREPARE_CODING').length,1);
 done(f,'prepare-context-change-retained',{request_id:id,status_possible:true});
}
{
 const f=fixture('explicit-rejection-go-resource-reselection');f.setHold(true);const p=f.manager.prepareCoding(scope(),context,review());
 Object.assign(f.held[0],{kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'coding source path does not exist'}});
 f.deliver();await assert.rejects(p,{code:'CODING_PREPARE_REJECTED'});
 const rejected=f.manager.codingIntent;assert.equal(rejected.state,'PREPARE_REJECTED');assert.equal(f.manager.codingSummary().available,true);
 f.setGeneration(1);const corrected=scope();corrected.coding.checks[0].toolchain_root='C:/corrected-go';
 f.setHold(false);await f.manager.prepareCoding(corrected,context,review(1));
 assert.equal(f.sent[1].coding.checks[0].toolchain_root,'C:/corrected-go');assert.equal(f.manager.retiredCodingIntents.length,1);
 assert.equal(f.manager.retiredCodingIntents[0].prepareRejection.messageId,f.sent[0].message_id);
 assert.equal(f.manager.retiredCodingIntents[0].retireReason,'AUTHORITATIVE_PREPARE_REJECTION');
 done(f,'explicit-rejection-go-resource-reselection',{prepare_frames:2,confirm_frames:0,retired_audit:rejected.prepareRejection});
}
for(const kind of ['session','resource']){
 const f=fixture('post-consent-await-'+kind+'-switch');await f.manager.prepareCoding(scope(),context,review());
 let rechecks=0,armed=false,switched=false;const observed=f.manager.observe.bind(f.manager);
 f.manager.observe=id=>{const result=observed(id);if(armed&&!switched){switched=true;queueMicrotask(()=>{if(kind==='session')f.setContext(JSON.stringify(['project-1','session-2',1,1]));else f.setGeneration(1);});}return result;};
 await assert.rejects(f.manager.confirmCoding(async()=>true,async()=>{rechecks++;if(rechecks===2)armed=true;return scoped();}),{code:'CODING_CONSENT_CONTEXT_CHANGED'});
 assert.equal(switched,true);assert.equal(f.sent.filter(x=>x.operation==='CONFIRM_CODING').length,0);
 assert.equal(f.manager.codingIntent.confirmSent,false);assert.equal(f.manager.pending,null);assert.equal(f.manager.consentPending,false);
 done(f,'post-consent-await-'+kind+'-switch',{rechecks,confirm_frames:0,original_unconsumed:true});
}
{
 const f=fixture('valid-explicit-confirm-exactly-once');await f.manager.prepareCoding(scope(),context,review());
 const result=await f.manager.confirmCoding(async()=>true,async()=>scoped());assert.equal(result.state,'CODING_CONFIGURED');
 await assert.rejects(f.manager.confirmCoding(async()=>true,async()=>scoped()),{code:'CODING_CONFIRM_NOT_AVAILABLE'});
 assert.equal(f.sent.filter(x=>x.operation==='CONFIRM_CODING').length,1);assert.equal((await f.manager.statusCoding()).state,'CODING_CONFIGURED');
 done(f,'valid-explicit-confirm-exactly-once',{confirm_frames:1,status_original:true});
}
for(const kind of ['wrong-host','bad-frozen-check','ambiguous-error']){
 const f=fixture('quarantine-'+kind);f.setHold(true);const p=f.manager.prepareCoding(scope(),context,review());
 let code;if(kind==='wrong-host'){f.held[0].host_id='host-bbbbbbbbbbbb';code='PRIVATE_REPLY_MISMATCH';}
 else if(kind==='bad-frozen-check'){f.held[0].result.frozen_checks[0].id='other-check';code='CODING_FROZEN_CHECK_INVALID';}
 else {f.held[0].kind='ERROR';f.held[0].error={code:'MANAGEMENT_REJECTED',message:'ambiguous result'};code='CODING_PREPARE_REJECTION_AMBIGUOUS';}
 f.deliver();await assert.rejects(p,{code});assert.equal(f.manager.state,'BROKEN');assert.equal(f.manager.codingIntent.state,'PREPARE_UNRESOLVED');
 await assert.rejects(f.manager.prepareCoding(scope(),context,review()),{code:'CODING_ORIGINAL_REQUEST_PENDING'});
 assert.equal(f.sent.length,1);done(f,'quarantine-'+kind,{error:code,prepare_frames:1,confirm_frames:0,original_retained:true});
}
// Independent managers let the three real production timers run together.
// No timer fields, pending records, clock values or candidate methods are patched.
await Promise.all(['valid-result','expired-result','terminal-error'].map(async kind=>{
 const name='production-45000ms-timeout-late-'+kind,f=fixture(name,{ttl:kind==='expired-result'?60000:55000});
 f.setHold(true);const started=Date.now();const pending=f.manager.prepareCoding(scope(),context,review());const id=f.held[0].result.request_id;
 if(kind==='terminal-error')Object.assign(f.held[0],{kind:'ERROR',result:null,error:{code:'MANAGEMENT_REJECTED',message:'explicit late rejection'}});
 await assert.rejects(pending,{code:'MANAGEMENT_REPLY_UNCERTAIN'});assert.equal(f.manager.pending.timedOut,true);
 await assert.rejects(f.manager.prepareCoding(scope(),context,review()),{code:'MANAGEMENT_COMMAND_PENDING'});
 assert.equal(f.sent.length,1);assert.equal(f.manager.retiredCodingIntents.length,0);
 if(kind==='expired-result')await sleep(Math.max(0,61000-(Date.now()-started)));
 f.deliver();assert.equal(f.manager.pending,null);f.setHold(false);
 if(kind==='terminal-error'){
  assert.equal(f.manager.codingIntent.state,'PREPARE_REJECTED');
  const rejected=f.manager.codingIntent;f.setGeneration(1);const corrected=scope();corrected.coding.checks[0].toolchain_root='C:/new-trusted-go';
  await f.manager.prepareCoding(corrected,context,review(1));assert.equal(f.manager.retiredCodingIntents[0].prepareRejection.messageId,f.sent[0].message_id);
  done(f,name,{elapsed_ms:Date.now()-started,production_timeout_ms:45000,prepare_frames:2,confirm_frames:0,rejection:rejected.prepareRejection});
 }else{
  assert.equal(f.manager.codingIntent.requestId,id);assert.equal(f.manager.codingIntent.prepareTerminal,'RESULT');
  const result=await f.manager.statusCoding();assert.equal(result.state,kind==='expired-result'?'EXPIRED':'AWAITING_CODING_CONFIRMATION');
  assert.deepEqual(f.sent.map(x=>x.operation),['PREPARE_CODING','STATUS_CODING']);
  done(f,name,{elapsed_ms:Date.now()-started,production_timeout_ms:45000,fixture_ttl_ms:kind==='expired-result'?60000:55000,request_id:id,retained_hash:f.manager.codingIntent.requestHash,final_state:result.state,prepare_frames:1,confirm_frames:0});
 }
}));
fs.writeFileSync(path.join(out,'review-fixtures-results.json'),JSON.stringify({facts,all_passed:true,actual_model_calls:0,actual_tool_calls:0},null,2));
console.log(JSON.stringify({independent_scenarios:facts.length,all_passed:true,actual_model_calls:0,actual_tool_calls:0}));

