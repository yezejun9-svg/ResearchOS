import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {fixture,scope,context,out,registerDesktopCoding} from './fixture.mjs';
const facts=[];
{
 const f=fixture('renderer-confirm-without-privileged-consent');let privilegedPrompts=0;
 const handlers=new Map();registerDesktopCoding({handle:(name,fn)=>handlers.set(name,fn)},{desktopManagement:f.manager,codingSenderAllowed:event=>event.sender.getURL()==='ros-app://desktop/',prepareCodingScope:async()=>({scope:scope(),context}),pickCodingDirectory:async()=>({selected:true}),requestPrivilegedConfirmation:()=>{privilegedPrompts++;return false;}});
 const event={sender:{getURL:()=> 'ros-app://desktop/'}};
 assert.equal((await handlers.get('ros:desktop:coding:prepare')(event,{})).state,'AWAITING_CODING_CONFIRMATION');
 // Invoke exposed IPC directly: no DOM click, window.confirm, native dialog or user gesture.
 const result=await handlers.get('ros:desktop:coding:confirm')(event,{});
 assert.equal(result.state,'CODING_CONFIGURED');assert.equal(result.ok,true);assert.equal(privilegedPrompts,0);
 assert.equal(f.sent.filter(x=>x.operation==='CONFIRM_CODING').length,1);
 facts.push({scenario:'renderer-confirm-without-privileged-consent',defect_reproduced:true,result,privileged_prompts:privilegedPrompts,confirm_frames:1});f.save();
}
{
 const f=fixture('expiry-retires-during-pending-status',{ttl:400});
 await f.manager.prepareCoding(scope(),context);const original={requestId:f.manager.codingIntent.requestId,requestHash:f.manager.codingIntent.requestHash};
 await new Promise(r=>setTimeout(r,450));assert.equal((await f.manager.statusCoding()).state,'EXPIRED');
 f.setHold(true);const pendingStatus=f.manager.statusCoding();assert.equal(f.manager.pending.operation,'STATUS_CODING');
 await assert.rejects(f.manager.prepareCoding(scope(),context),{code:'MANAGEMENT_COMMAND_PENDING'});
 assert.equal(f.manager.codingIntent,null);assert.equal(f.manager.retiredCodingIntents.length,1);assert.equal(f.manager.pending.operation,'STATUS_CODING');
 const beforeLate={activeIntent:f.manager.codingIntent,retired:f.manager.retiredCodingIntents.map(x=>({requestId:x.requestId,state:x.state})),pending:f.manager.pending.operation};
 f.deliver();await pendingStatus;await assert.rejects(f.manager.statusCoding(),{code:'CODING_ORIGINAL_REQUEST_REQUIRED'});
 facts.push({scenario:'expiry-retires-during-pending-status',defect_reproduced:true,original,before_late:beforeLate,after_late:f.manager.codingSummary(),status_after_late:'CODING_ORIGINAL_REQUEST_REQUIRED',confirm_frames:0});f.save();
}
{
 const f=fixture('prepare-response-context-change-drops-original');f.setHold(true);
 const preparing=f.manager.prepareCoding(scope(),context);const frozen=f.held[0].result;
 f.setContext(JSON.stringify(['project-1','session-2',1,1]));f.deliver();
 await assert.rejects(preparing,{code:'CONTEXT_CHANGED'});assert.equal(f.manager.codingIntent,null);
 assert.equal(f.manager.retiredCodingIntents.length,0);assert.equal(f.manager.pending,null);
 f.setContext(context);await assert.rejects(f.manager.statusCoding(),{code:'CODING_ORIGINAL_REQUEST_REQUIRED'});
 f.setHold(false);await f.manager.prepareCoding(scope(),context);assert.equal(f.sent.filter(x=>x.operation==='PREPARE_CODING').length,2);
 facts.push({scenario:'prepare-response-context-change-drops-original',defect_reproduced:true,first_request_id:frozen.request_id,first_request_hash:frozen.request_hash,current_request_id:f.manager.codingIntent.requestId,first_request_retained:false,prepare_frames:2,confirm_frames:0});f.save();
}
fs.writeFileSync(path.join(out,'counterexample-results.json'),JSON.stringify({facts,actual_model_calls:0,actual_tool_calls:0,source_modules:'final bound build',note:'Exit zero means all asserted defects reproduced, not product PASS.'},null,2));
console.log(JSON.stringify({defects_reproduced:facts.length,actual_model_calls:0,actual_tool_calls:0}));
