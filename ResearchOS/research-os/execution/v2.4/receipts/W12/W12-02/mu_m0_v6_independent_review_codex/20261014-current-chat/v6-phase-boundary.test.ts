import assert from 'node:assert/strict';
import {test} from 'node:test';
import {EventStream, type AssistantMessage,type AssistantMessageEvent} from '@earendil-works/pi-ai';
import {Type} from 'typebox';
import {Agent} from 'C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012/packages/agent/src/agent.ts';
const model=()=>({id:'initial',name:'fixture',api:'openai-responses',provider:'fixture',baseUrl:'https://invalid.example',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:4096,maxTokens:256});
const assistant=():AssistantMessage=>({role:'assistant',content:[{type:'text',text:'done'}],api:'openai-responses',provider:'fixture',model:'fixture',usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:1});
const message=(text:string):any=>({role:'user',content:[{type:'text',text}],timestamp:1});
const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
function stream(m:AssistantMessage){const s=new EventStream<AssistantMessageEvent,AssistantMessage>(e=>e.type==='done',e=>{if(e.type!=='done')throw Error('event');return e.message;});queueMicrotask(()=>{s.push({type:'done',reason:m.stopReason==='toolUse'?'toolUse':'stop',message:m});s.end(m);});return s;}
function deferred(){let resolve!:()=>void;const promise=new Promise<void>(r=>resolve=r);return{promise,resolve};}

test('V6-P checkpoint after trusted next phase retains new identities and completes tool once',async()=>{
 const gates=[deferred(),deferred()],entered=[deferred(),deferred()];let calls=0,finishes=0,prepares=0;const seen:string[]=[],effects:string[]=[];const initial=model(),next={...model(),id:'next'};
 const tool={name:'next',label:'Next',description:'fixture',pauseVersion:'1',parameters:Type.Object({}),async execute(){effects.push('next');return{content:[{type:'text' as const,text:'ok'}],details:null};}};
 const options:any={sessionId:'repeat-phase',initialState:{model:initial},pauseModels:[{key:'next',version:'1',model:next}],pauseToolRegistry:[tool],prepareNextTurnWithContext:(turn:any)=>{prepares++;return{model:next,context:{...turn.context,tools:[tool]}};},finishTurn:()=>++finishes===1?{action:'continue'}:undefined,streamFn:async(m:any)=>{seen.push(m.id);const n=++calls;if(n<=2){entered[n-1].resolve();await gates[n-1].promise;}return stream(n===2?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'next-call',name:'next',arguments:{}}]}:assistant());}};
 const first=new Agent(options);const running=first.prompt(message('original'));await entered[0].promise;const pause1=first.requestPause();gates[0].resolve();await Promise.all([running,pause1]);
 const second=new Agent(options);second.restorePauseState(copy(first.exportPauseState()),options.sessionId);assert.equal(calls,1);const resuming=second.resumePaused();await entered[1].promise;const pause2=second.requestPause();gates[1].resolve();await Promise.all([resuming,pause2]);assert.equal(calls,2);assert.deepEqual(effects,[]);
 const checkpoint=copy(second.exportPauseState());const third=new Agent(options);third.restorePauseState(checkpoint,options.sessionId);assert.equal(calls,2);assert.deepEqual(effects,[]);await third.resumePaused();
 assert.equal(third.state.errorMessage,undefined);assert.equal(calls,3);assert.deepEqual(seen,['initial','next','next']);assert.deepEqual(effects,['next']);assert.equal(prepares,2);assert.equal(finishes,3);assert.deepEqual(third.state.messages.at(-1),assistant());assert.deepEqual(third.state.messages.filter((m:any)=>m.role==='toolResult').map((m:any)=>m.toolCallId),['next-call']);assert.equal(third.state.messages.filter((m:any)=>m.role==='user').length,1);
 console.log(JSON.stringify({case:'V6-P',calls,seen,effects,prepares,finishes,error:third.state.errorMessage}));
});

test('V6-Q mutated replacement cannot be re-signed by trusted prepareRequest',async()=>{
 const outcomes=[];for(const kind of ['current-model','next-model','next-tool','next-tool-execute']){
  const entered=deferred(),gate=deferred();let calls=0,finishes=0;const initial=model(),next={...model(),id:'next'},effects:string[]=[];const fn=()=>async()=>{effects.push('effect');return{content:[{type:'text' as const,text:'ok'}],details:null};};const tool={name:'next',label:'Next',description:'fixture',parameters:Type.Object({}),execute:fn()};
  const options:any={sessionId:'request-'+kind,initialState:{model:initial},pauseModels:[{key:'next',version:'1',model:next}],pauseToolRegistry:[tool],finishTurn:()=>++finishes===1?{action:'continue'}:undefined,prepareRequest:async(r:any)=>{if(calls===0)return;await Promise.resolve();if(kind==='current-model')initial.baseUrl='https://changed.invalid.example';if(kind==='next-model')next.baseUrl='https://changed.invalid.example';if(kind==='next-tool')tool.description='changed';if(kind==='next-tool-execute'){const replacement=fn();assert.equal(replacement.toString(),tool.execute.toString());tool.execute=replacement;}return{model:next,context:{...r.context,tools:[tool]}};},streamFn:async()=>{calls++;entered.resolve();await gate.promise;return stream(assistant());}};
  const first=new Agent(options);const running=first.prompt(message('original'));await entered.promise;const pause=first.requestPause();gate.resolve();await Promise.all([running,pause]);const target=new Agent(options);target.restorePauseState(copy(first.exportPauseState()),options.sessionId);await target.resumePaused();assert.equal(calls,1);assert.deepEqual(effects,[]);assert.ok(target.state.errorMessage);outcomes.push({kind,calls,effects,error:target.state.errorMessage});
 }console.log(JSON.stringify({case:'V6-Q',outcomes}));
});

test('V6-R async mutation after legitimate phase commit blocks the next dispatch',async()=>{
 const outcomes=[];for(const stage of ['transform','convert','key']){
  const entered=deferred(),gate=deferred();let calls=0,finishes=0,committed=false;const initial=model(),next={...model(),id:'next'};const change=async()=>{await Promise.resolve();next.baseUrl='https://changed.invalid.example';};
  const options:any={sessionId:'new-phase-'+stage,initialState:{model:initial},pauseModels:[{key:'next',version:'1',model:next}],finishTurn:()=>++finishes===1?{action:'continue'}:undefined,prepareNextTurn:()=>{committed=true;return{model:next};},transformContext:async(messages:any)=>{if(committed&&stage==='transform')await change();return messages;},convertToLlm:async(messages:any)=>{if(committed&&stage==='convert')await change();return messages;},getApiKey:async()=>{if(committed&&stage==='key')await change();return undefined;},streamFn:async()=>{calls++;entered.resolve();await gate.promise;return stream(assistant());}};
  const first=new Agent(options);const running=first.prompt(message('original'));await entered.promise;const pause=first.requestPause();gate.resolve();await Promise.all([running,pause]);const target=new Agent(options);target.restorePauseState(copy(first.exportPauseState()),options.sessionId);await target.resumePaused();assert.equal(calls,1);assert.ok(target.state.errorMessage);outcomes.push({stage,calls,error:target.state.errorMessage});
 }console.log(JSON.stringify({case:'V6-R',outcomes}));
});
