import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { decimal, applyHarnessPage, validateTaskIdentity, createHarnessController, cancelIntent, canSubmitHarness } from './stage01/apps/web/src/harness.js'
import { composerSubmitKey, harnessActivityRows } from './stage01/apps/web/src/activity.js'

const taskRef = { project_id:'qa-project',task_id:'qa-task' }
const task = patch => ({ task_ref:taskRef,request_id:'qa-original',harness_id:'codex',workspace_ref:'qa-workspace',prompt:'inspect source',scope:'workspace-read',ephemeral:true,status:'QUEUED',terminal:false,task_revision:'1',run:null,created_at:'2026-11-04T00:00:00Z',updated_at:'2026-11-04T00:00:00Z',result:null,failure:null,...patch })
const capabilities = { harness_id:'codex',can_submit:true,capabilities:{readonly_turn:true,event_stream:true,cancel:true,task_history:true,request_lookup:true,token_delta:false,write:false,resume:false,pause:false,per_tool_approval:false,file_diff:false,file_list:false,file_artifacts:false,attachments:false} }
const ok=data=>({ok:true,data})
const deferred=()=>{let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b});return {promise,resolve,reject}}
const bridge = overrides => ({capabilities:async()=>ok(capabilities),pending:async()=>ok(null),list:async()=>ok({items:[],next_cursor:'0',has_more:false,lookup:null}),get:async()=>ok(task()),...overrides})
const event=(sequence,patch)=>({event_id:'qa-event-'+sequence,task_ref:taskRef,run:null,sequence,timestamp:'2026-11-04T00:00:00Z',kind:'RUN_STATE',payload:{status:'RUNNING',text:null,tool:null,task:null,error:null},...patch})
const state=()=>({task:task(),events:[],cursor:'0',end:false})
const page=(events,patch)=>({task_ref:taskRef,events,next_cursor:events.at(-1)?.sequence||'0',has_more:false,end:false,reset:false,snapshot:null,...patch})

test('Q03 canonical exact int64 values do not coerce to JS numbers',()=>{
 for(const x of ['0','9007199254740993','9223372036854775807'])assert.equal(decimal(x),true)
 for(const x of [0,9007199254740992,'9223372036854775808','01','-1','1e3','1.0','+1'])assert.equal(decimal(x),false)
 assert.equal(decimal('0',true),false)
 const s=applyHarnessPage(state(),page([event('9007199254740993'),event('9223372036854775807')]),taskRef)
 assert.equal(s.cursor,'9223372036854775807');assert.equal(s.events[0].sequence,'9007199254740993')
})
test('Q04 Q05 reset is the only path that may replace buffer and move cursor backwards',()=>{
 const s={...state(),cursor:'9007199254740993',events:[event('9007199254740993')]}
 assert.throws(()=>applyHarnessPage(s,page([],{next_cursor:'1'}),taskRef))
 const out=applyHarnessPage(s,page([],{reset:true,snapshot:task(),next_cursor:'1'}),taskRef)
 assert.deepEqual(out.events,[]);assert.equal(out.cursor,'1');assert.equal(out.task.status,'QUEUED')
 for(const bad of [{has_more:true},{events:[event('2')]},{snapshot:null},{end:true}])assert.throws(()=>applyHarnessPage(s,page([],{reset:true,snapshot:task(),next_cursor:'1',...bad}),taskRef))
 assert.throws(()=>applyHarnessPage(state(),{...page([]),task_ref:{...taskRef,task_id:'foreign'}},taskRef))
})
test('Q06 run changes retain history and duplicate events are exact',()=>{
 const first=event('2'),s=applyHarnessPage(state(),page([first]),taskRef)
 const run={run_id:'qa-run-next',epoch:'9007199254740993'}
 const second=event('3',{kind:'RUN_STARTED',run})
 const out=applyHarnessPage(s,page([first,second]),taskRef)
 assert.deepEqual(out.events,[first,second]);assert.equal(out.cursor,'3')
 assert.throws(()=>applyHarnessPage(s,page([{...first,payload:{...first.payload,text:'changed'}}]),taskRef))
})
test('Q06 terminal task may still have additional durable pages',()=>{
 const terminal=task({status:'COMPLETED',terminal:true})
 const p=page([event('3',{kind:'TASK_TERMINAL',payload:{status:'COMPLETED',text:null,tool:null,task:terminal,error:null}})],{has_more:true})
 const out=applyHarnessPage(state(),p,taskRef);assert.equal(out.task.terminal,true);assert.equal(out.end,false)
 assert.throws(()=>applyHarnessPage(out,page([],{next_cursor:'3',end:true,has_more:true}),taskRef))
})
test('Q01 Q17 can_submit does not require fabricated verification and queued ACK stays nonterminal',async()=>{
 assert.equal(canSubmitHarness(capabilities),true)
 let submits=0
 const c=createHarnessController(bridge({submit:async()=>{submits++;return ok({task_ref:taskRef,request_id:'qa-original',task_revision:'1',status:'QUEUED',run:null})}}),taskRef.project_id)
 await c.load();assert.equal(await c.submit({workspace_ref:'qa-workspace',prompt:'inspect source'}),true)
 assert.equal(submits,1);assert.equal(c.getSnapshot().task.run,null);assert.equal(c.getSnapshot().task.terminal,false)
 c.dispose()
})
test('Q07 stale event page cannot overwrite newly selected task',async()=>{
 const old=deferred();let selected='qa-task'
 const c=createHarnessController(bridge({get:async b=>ok(task({task_ref:{...taskRef,task_id:b.task_id}})),events:()=>old.promise}),taskRef.project_id)
 await c.load();await c.select(selected);const pending=c.tick();selected='qa-other';await c.select(selected)
 old.resolve(ok(page([event('7')])));await pending
 assert.equal(c.getSnapshot().task.task_ref.task_id,'qa-other');assert.deepEqual(c.getSnapshot().events,[]);assert.equal(c.getSnapshot().cursor,'0')
 c.dispose()
})
test('Q07 disposed controller ignores delayed metadata',async()=>{
 const d=deferred();const c=createHarnessController(bridge({capabilities:()=>d.promise}),taskRef.project_id)
 const before=c.getSnapshot();const pending=c.load();c.dispose();d.resolve(ok(capabilities));await pending
 assert.equal(c.getSnapshot().capabilities,null);assert.equal(before.capabilities,null)
})
test('Q09 Q10 UNKNOWN recovery remains read-only after NOT_FOUND',async()=>{
 let submits=0,reads=0
 const unknown={kind:'submit',request_id:'qa-original',state:'UNKNOWN',task_ref:null,workspace_ref:'qa-workspace',prompt:'inspect source'}
 const c=createHarnessController(bridge({pending:async()=>ok(unknown),submit:async()=>{submits++;throw Error('POST forbidden')},reconcile:async()=>{reads++;return ok({pending:unknown,task:null})}}),taskRef.project_id)
 await c.load();assert.equal(await c.submit({workspace_ref:'qa-workspace',prompt:'different'}),false)
 await c.reconcile();await c.reconcile();assert.equal(reads,2);assert.equal(submits,0);assert.equal(c.getSnapshot().pending.request_id,'qa-original')
 c.dispose()
})
test('Q13 stale cancel refreshes once but never cancels the newer Run automatically',async()=>{
 let cancels=0,gets=0
 const c=createHarnessController(bridge({get:async()=>ok(task({run:{run_id:++gets>1?'new-run':'old-run',epoch:String(gets)},status:'RUNNING'})),cancel:async()=>{cancels++;return {ok:false,reason:'STATE_CONFLICT',outcome:'REPLIED'}}}),taskRef.project_id)
 await c.load();await c.select('qa-task');await c.cancel();assert.equal(cancels,1);assert.equal(c.getSnapshot().task.run.run_id,'new-run')
 assert.deepEqual(cancelIntent(task()),{task_id:'qa-task',expected_task_revision:'1',expected_run_id:null,expected_epoch:null})
 c.dispose()
})
test('Q18 unsupported submission and blank UTF8 overflow never reach bridge',async()=>{
 let posts=0
 const c=createHarnessController(bridge({submit:async()=>{posts++;throw Error('should not send')}}),taskRef.project_id)
 await c.load();for(const prompt of ['','  \n','中'.repeat(22000)])assert.equal(await c.submit({workspace_ref:'qa-workspace',prompt}),false)
 assert.equal(posts,0);c.dispose()
})
test('Q19 keyboard helper guards composition and multiline without claiming real IME evidence',()=>{
 for(const x of [{key:'Enter',isComposing:true},{key:'Enter',keyCode:229},{key:'Enter',shiftKey:true}])assert.equal(composerSubmitKey(x),false)
 assert.equal(composerSubmitKey({key:'Enter'}),true)
})
test('Q02 Q23 failed tools and UNKNOWN are not rendered as accepted results',()=>{
 validateTaskIdentity(task({status:'UNKNOWN',terminal:true}),taskRef)
 assert.throws(()=>cancelIntent(task({status:'UNKNOWN',terminal:true})))
 const rows=harnessActivityRows([event('2',{kind:'TOOL_EVENT',payload:{status:null,text:null,tool:{id:'t1',name:'read',phase:'FAILED',summary:'denied'},task:null,error:null}})],taskRef)
 assert.ok(JSON.stringify(rows).includes('denied'));assert.ok(!JSON.stringify(rows).includes('ACCEPTED'))
})

// Execute the exact frozen send function, not a hand-written simulation of it.
const source=fs.readFileSync(new URL('./stage01/apps/web/src/workbench.jsx',import.meta.url),'utf8')
const block=source.slice(source.indexOf('function NativeHarnessWorkbench('),source.indexOf('function NativeMuWorkbench('))
const match=/async function send\(event\) \{[\s\S]*?\n  \}/.exec(block)
assert.ok(match,'actual send function can be isolated without JSX')
for(const editedBack of [false,true])test('Q20 original frozen send preserves unsent typing during pending success; editBack='+editedBack,async()=>{
 const accepted=deferred();let currentDraft='submitted text';let notices=[]
 const setDraft=value=>{currentDraft=typeof value==='function'?value(currentDraft):value}
 const send=vm.runInNewContext('('+match[0]+')',{canSend:true,draft:'submitted text',workspace:'qa-workspace',setDraft,setNotice:v=>notices.push(v),controller:{current:{submit:()=>accepted.promise}}})
 const pending=send({preventDefault(){}})
 setDraft('new unsent text');if(editedBack)setDraft('submitted text')
 const expected=currentDraft;accepted.resolve(true);await pending
 assert.equal(currentDraft,expected,'Late ACK/GET must preserve the current user draft (including edit-back-to-original).')
})
