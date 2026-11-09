import assert from "node:assert/strict";
import { test } from "node:test";
import { type AssistantMessage, type AssistantMessageEvent, EventStream, type Model } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { Agent } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012/packages/agent/src/agent.ts";
import type { AgentMessage } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-v2-20261012/packages/agent/src/types.ts";

class MockStream extends EventStream<AssistantMessageEvent, AssistantMessage> {
	constructor(message: AssistantMessage) {
		super(
			(event) => event.type === "done",
			(event) => {
				if (event.type !== "done") throw new Error("unexpected event");
				return event.message;
			},
		);
		queueMicrotask(() => {
			this.push({ type: "done", reason: message.stopReason === "toolUse" ? "toolUse" : "stop", message });
			this.end(message);
		});
	}
}

const model: Model<"openai-responses"> = {
	id: "synthetic",
	name: "synthetic",
	api: "openai-responses",
	provider: "fixture",
	baseUrl: "https://invalid.example",
	reasoning: false,
	input: ["text"],
	cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
	contextWindow: 4096,
	maxTokens: 256,
};
const assistant = (): AssistantMessage => ({
	role: "assistant",
	content: [{ type: "text", text: "done" }],
	api: "openai-responses",
	provider: "fixture",
	model: "synthetic",
	usage: {
		input: 1,
		output: 1,
		cacheRead: 0,
		cacheWrite: 0,
		totalTokens: 2,
		cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
	},
	stopReason: "stop",
	timestamp: 1,
});
const message = (text: string): AgentMessage => ({ role: "user", content: [{ type: "text", text }], timestamp: 1 });

const copy=<T>(x:T):T=>JSON.parse(JSON.stringify(x));
async function idleFixture(registrations:any[]=[]){const options:any={sessionId:'typed',initialState:{model:copy(model),messages:[message('safe')]},pauseDataRegistrations:registrations,streamFn:()=>{throw Error('unexpected dispatch');}};const a=new Agent(options);await a.requestPause();return{options,saved:copy(a.exportPauseState())};}

test('V5-J content discriminants must be strings, with closed per-kind fields',async()=>{
 const f=await idleFixture(),outcomes=[];
 const malformed={type:['text'],unregisteredPayload:{marker:'synthetic-private-data'}};
 for(const role of ['user','assistant','toolResult']){const saved=copy(f.saved);saved.messages.push(role==='user'?{...message('x'),content:[malformed]}:role==='assistant'?{...assistant(),content:[malformed]}:{role:'toolResult',toolCallId:'fixture',toolName:'fixture',content:[malformed],details:null,isError:false,timestamp:1});let rejected=false;const target=new Agent(f.options);try{target.restorePauseState(saved,'typed');}catch{rejected=true;}outcomes.push({role,rejected,unknownRetained:!rejected&&JSON.stringify(target.exportPauseState()).includes('unregisteredPayload')});}
 console.log(JSON.stringify({case:'V5-J',outcomes}));assert.ok(outcomes.every(x=>x.rejected),'array discriminants must not bypass typed content validation');
});

test('V5-K closed trusted custom schema rejects inherited Object.prototype names',async()=>{
 const registration:any={kind:'message',role:'safeCustom',version:'1',schema:{type:'object',properties:{role:{type:'literal',value:'safeCustom'},value:{type:'string'},timestamp:{type:'number'}}}};
 const f=await idleFixture([registration]);const valid={role:'safeCustom',value:'ok',timestamp:1};const good=copy(f.saved);good.messages.push(valid);const control=new Agent(f.options);control.restorePauseState(good,'typed');assert.deepEqual(control.exportPauseState().messages.at(-1),valid);
 const outcomes=[];for(const key of ['unregistered','constructor','__proto__','toString']){const saved=copy(f.saved);const custom=copy(valid) as any;Object.defineProperty(custom,key,{value:{marker:'synthetic-private-data'},enumerable:true,configurable:true,writable:true});saved.messages.push(custom);let rejected=false;const target=new Agent(f.options);try{target.restorePauseState(saved,'typed');}catch{rejected=true;}outcomes.push({key,rejected,unknownRetained:!rejected&&Object.hasOwn(target.exportPauseState().messages.at(-1)!,key)});}
 console.log(JSON.stringify({case:'V5-K',outcomes}));assert.ok(outcomes.every(x=>x.rejected),'closed schema must use own declared properties');
});

for(const update of ['model','tools'] as const){test('V5-L next-turn trusted '+update+' selection preserves uninterrupted behavior',async()=>{
 const runs:any[]=[];
 for(const pause of [false,true]){let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0,finishes=0;const seen:string[]=[],effects:string[]=[];const initial=copy(model),next={...copy(model),id:'next-registered-model'};
 const tool={name:'next_tool',label:'Next',description:'fixture',pauseVersion:'1',parameters:Type.Object({}),async execute(){effects.push('next_tool');return{content:[{type:'text' as const,text:'ok'}],details:null};}};
 const options:any={sessionId:'next-'+update,initialState:{model:initial,tools:[]},pauseModels:[{key:'next',version:'1',model:next}],pauseToolRegistry:[tool],prepareNextTurn:()=>{prepares++;return update==='model'?{model:next}:{context:{messages:[message('new-turn')],tools:[tool]}};},finishTurn:()=>({action:++finishes===1?'continue':'end'}),streamFn:async(m:any)=>{calls++;seen.push(m.id);if(pause&&calls===1){enter();await gate;}return new MockStream(update==='tools'&&calls===2?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'next',name:'next_tool',arguments:{}}]}:assistant());}};
 const first=new Agent(options);const running=first.prompt(message('original'));let target=first;if(pause){await entered;const stopping=first.requestPause();release();await Promise.all([running,stopping]);const saved=copy(first.exportPauseState());target=new Agent(options);target.restorePauseState(saved,options.sessionId);assert.equal(calls,1);await target.resumePaused();}else await running;
 runs.push({pause,calls,prepares,finishes,seen,effects,error:target.state.errorMessage});}
 console.log(JSON.stringify({case:'V5-L-'+update,runs}));assert.deepEqual(runs[1].seen,runs[0].seen);assert.deepEqual(runs[1].effects,runs[0].effects);assert.equal(runs[1].error,undefined);assert.equal(runs[1].prepares,1);
});}

test('V5-M model mutation during async transform conversion key and next-turn preparation blocks next dispatch',async()=>{
 const outcomes=[];for(const stage of ['transform','convert','key','prepareNextTurn']){let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,restored=false,finishes=0;const active=copy(model);const mutate=async()=>{await Promise.resolve();active.baseUrl='https://changed.invalid.example';};
 const options:any={sessionId:'async-'+stage,initialState:{model:active},finishTurn:()=>({action:++finishes===1?'continue':'end'}),prepareNextTurn:async()=>{if(restored&&stage==='prepareNextTurn')await mutate();},transformContext:async(messages:any)=>{if(restored&&stage==='transform')await mutate();return messages;},convertToLlm:async(messages:any)=>{if(restored&&stage==='convert')await mutate();return messages;},getApiKey:async()=>{if(restored&&stage==='key')await mutate();return undefined;},streamFn:async()=>{calls++;if(calls===1){enter();await gate;}return new MockStream(assistant());}};
 const first=new Agent(options);const running=first.prompt(message('safe'));await entered;const stopping=first.requestPause();release();await Promise.all([running,stopping]);const saved=copy(first.exportPauseState());const target=new Agent(options);target.restorePauseState(saved,options.sessionId);assert.equal(calls,1);restored=true;let error:string|undefined;try{await target.resumePaused();}catch(e){error=String(e);}error??=target.state.errorMessage;outcomes.push({stage,calls,rejected:!!error});}
 console.log(JSON.stringify({case:'V5-M',outcomes}));assert.ok(outcomes.every(x=>x.calls===1&&x.rejected));
});

test('V5-N extra registry subset never executes excluded tool after prepared checkpoint',async()=>{
 let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0;const effects:string[]=[];const make=(name:string)=>({name,label:name,description:'fixture',pauseVersion:'1',parameters:Type.Object({}),async execute(){effects.push(name);return{content:[{type:'text' as const,text:'ok'}],details:null};}});const allowed=make('allowed'),excluded=make('excluded');const options:any={sessionId:'extra-excluded',initialState:{model:copy(model),tools:[]},pauseToolRegistry:[allowed,excluded],prepareRequest:async(r:any)=>{enter();await gate;return{context:{...r.context,tools:[allowed]}};},streamFn:()=>new MockStream(++calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'a',name:'allowed',arguments:{}},{type:'toolCall',id:'b',name:'excluded',arguments:{}}]}:assistant())};const first=new Agent(options);const running=first.prompt(message('safe'));await entered;const stopping=first.requestPause();release();await Promise.all([running,stopping]);const target=new Agent(options);target.restorePauseState(copy(first.exportPauseState()),options.sessionId);assert.deepEqual(effects,[]);await target.resumePaused();const results=target.state.messages.filter((m:any)=>m.role==='toolResult').map((m:any)=>({id:m.toolCallId,isError:m.isError}));console.log(JSON.stringify({case:'V5-N',effects,calls,results}));assert.deepEqual(effects,['allowed']);assert.deepEqual(results,[{id:'a',isError:false},{id:'b',isError:true}]);assert.equal(calls,2);
});

