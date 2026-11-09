import fs from 'node:fs';
import path from 'node:path';
const out=path.dirname(new URL(import.meta.url).pathname.slice(1));
const base=fs.readFileSync(out+'/independent-agent.test.ts','utf8').split("test('pause during")[0];
fs.writeFileSync(out+'/negative-agent.test.ts',base+`
test('N1 pause during prepareNextTurn must not repeat committed preparation on resume',async()=>{
 let enter!:()=>void, release!:()=>void;const started=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0;
 const tool={name:'effect',label:'Effect',description:'fixture',parameters:Type.Object({}),async execute(){return{content:[{type:'text' as const,text:'ok'}],details:null};}};
 const options={sessionId:'prepare-inside',initialState:{model,tools:[tool]},prepareNextTurn:async()=>{prepares++;if(prepares===1){enter();await gate;}return{};},streamFn:()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'effect',arguments:{}}]}:assistant());}};
 const first=new Agent(options);const running=first.prompt(message('original'));await started;const pausing=first.requestPause();release();await Promise.all([running,pausing]);
 const snapshot=first.exportPauseState();const restored=new Agent(options);restored.restorePauseState(snapshot,'prepare-inside');await restored.resumePaused();
 console.log(JSON.stringify({case:'N1',calls,prepares,error:restored.state.errorMessage}));assert.equal(calls,2);assert.equal(prepares,1);
});
test('N2 pause during plain assistant response must preserve finishTurn decision',async()=>{
 let enter!:()=>void,release!:()=>void;const started=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,finishes=0;
 const options={sessionId:'plain-finish',initialState:{model},finishTurn:()=>{finishes++;return finishes===1?{action:'continue' as const}:{action:'end' as const};},streamFn:async()=>{calls++;if(calls===1){enter();await gate;}return new MockStream(assistant());}};
 const first=new Agent(options);const running=first.prompt(message('original'));await started;const pausing=first.requestPause();release();await Promise.all([running,pausing]);const snapshot=first.exportPauseState();
 const restored=new Agent(options);restored.restorePauseState(snapshot,'plain-finish');await restored.resumePaused();console.log(JSON.stringify({case:'N2',calls,finishes,error:restored.state.errorMessage}));assert.equal(finishes,2);assert.equal(calls,2);
});
test('N3 both queues reject invalid empty watermark and failed restore is atomic',async()=>{
 const opts={sessionId:'negative-watermark',initialState:{model},streamFn:()=>new MockStream(assistant())};const agent=new Agent(opts);await agent.requestPause();const snapshot=agent.exportPauseState();
 for(const queue of ['steering','followUp'] as const){for(const value of [-1,1,99,Number.MAX_SAFE_INTEGER+1]){const bad=structuredClone(snapshot);bad[queue].lastConsumedSequence=value;assert.throws(()=>agent.restorePauseState(bad,'negative-watermark'));assert.deepEqual(agent.exportPauseState(),snapshot);}}
});
test('N4 default no-pause prepare and finish controls',async()=>{
 let calls=0,finishes=0,prepares=0;const a=new Agent({sessionId:'default-control',initialState:{model},prepareNextTurn:()=>{prepares++;return{};},finishTurn:()=>{finishes++;return finishes===1?{action:'continue'}:{action:'end'};},streamFn:()=>{calls++;return new MockStream(assistant());}});await a.prompt(message('original'));assert.equal(calls,2);assert.equal(finishes,2);assert.equal(prepares,1);
});
`);
const session=fs.readFileSync(out+'/independent-session.test.ts','utf8');
const prefix=session.split("test('session pause")[0];
let existing=session.slice(session.indexOf("test('session pause"),session.indexOf("test('session bounded"));
existing=existing.replace("session pause keeps deferred custom message out of incomplete tool batch","N5 custom message arriving after pause cannot break unfinished tool batch");
existing=existing.replace("  await session.sendCustomMessage({customType:'context',content:'deferred',display:true,details:{retain:true}},{triggerTurn:false});",'');
existing=existing.replace("  const checkpoint=session.exportPauseCheckpoint", "  await session.sendCustomMessage({customType:'context',content:'arrived-after-pause',display:true,details:{retain:true}},{triggerTurn:false});\n  const checkpoint=session.exportPauseCheckpoint");
fs.writeFileSync(out+'/negative-session.test.ts',prefix+existing);
