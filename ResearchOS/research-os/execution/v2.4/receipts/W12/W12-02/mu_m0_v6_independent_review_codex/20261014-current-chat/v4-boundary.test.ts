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

async function preparedFixture(extra:any={}) {
 let enter!:()=>void,release!:()=>void; const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);const effects:any[]=[];
 const selected={...model,id:'selected'};let prepares=0;
 const options:any={sessionId:'boundary',initialState:{model:{...model}},pauseModels:[{key:'selected',version:'v1',model:selected}],...extra,prepareRequest:async(request:any)=>{prepares++;enter();await gate;return{model:selected,...(extra.prepared?.(request)??{})};},streamFn:(m:any)=>{effects.push({kind:'model',id:m.id,url:m.baseUrl});return new MockStream(assistant());}};
 const first=new Agent(options);const running=first.prompt(message('safe'));await entered;const stopping=first.requestPause();release();await Promise.all([running,stopping]);const saved=JSON.parse(JSON.stringify(first.exportPauseState()));assert.equal(saved.continuation.phase,'request');assert.equal(saved.continuation.stage,'afterRequest');assert.deepEqual(effects,[]);return{options,saved,effects,selected,prepares:()=>prepares};
}

test('V4-E registered tool outside state.tools remains recoverable at prepared-request boundary',async()=>{
 const tool={name:'registered_only',label:'Registered',description:'safe fixture',pauseVersion:'v1',parameters:Type.Object({}),async execute(){throw Error('not expected');}};
 const f=await preparedFixture({pauseToolRegistry:[tool],prepared:(r:any)=>({context:{messages:r.context.messages,tools:[tool]}})});
 assert.deepEqual(f.saved.toolNames,[]);assert.deepEqual(f.saved.runtime.toolNames,['registered_only']);const target=new Agent(f.options);let error:string|undefined;try{target.restorePauseState(f.saved,'boundary');}catch(e){error=String(e);}
 console.log(JSON.stringify({case:'V4-E',error,modelCalls:f.effects.length,rootTools:f.saved.toolNames,runtimeTools:f.saved.runtime.toolNames}));assert.equal(error,undefined);assert.deepEqual(f.effects,[]);await target.resumePaused();assert.equal(f.effects.length,1);assert.equal(f.prepares(),1);
});

test('V4-F model registration drift between restore and resume fails closed',async()=>{
 const f=await preparedFixture();const target=new Agent(f.options);target.restorePauseState(f.saved,'boundary');assert.deepEqual(f.effects,[]);f.selected.baseUrl='https://changed.invalid.example';let error:string|undefined;try{await target.resumePaused();}catch(e){error=String(e);}
 console.log(JSON.stringify({case:'V4-F',error,effects:f.effects}));assert.equal(f.effects.length,0,'changed model must not dispatch');assert.ok(error);
});

test('V4-G unallowlisted extension payload and refresh token are not serialized as message metadata',async()=>{
 const options={sessionId:'metadata',initialState:{model,messages:[{...message('safe'),extensionState:{refreshToken:'fixture-private-token',internalHandle:'fixture-private-handle'}} as AgentMessage]},streamFn:()=>{throw Error('no calls');}};
 const first=new Agent(options);await first.requestPause();let saved:any,error:string|undefined;try{saved=first.exportPauseState();}catch(e){error=String(e);}
 console.log(JSON.stringify({case:'V4-G',rejected:!!error,extensionSaved:!!saved?.messages[0]?.extensionState,tokenSaved:JSON.stringify(saved??{}).includes('fixture-private-token')}));assert.ok(error||!JSON.stringify(saved).includes('fixture-private-token'),'undeclared extension data must not be serialized');
});

test('V4-H unsafe version phase size depth ordinal and model/tool bindings reject without effects or mutation',async()=>{
 const tool={name:'safe',label:'Safe',description:'safe fixture',pauseVersion:'v1',parameters:Type.Object({}),async execute(){return{content:[{type:'text' as const,text:'ok'}],details:null};}};
 const f=await preparedFixture({initialState:{model:{...model},tools:[tool]}});
 const changes:Array<[string,(s:any)=>void]>=[['version',s=>s.version=9],['phase',s=>s.continuation.phase='unknown'],['stage',s=>s.continuation.stage='unknown'],['size',s=>s.messages[0].padding='x'.repeat(12*1024*1024)],['depth',s=>{let p:any=s.messages[0];for(let i=0;i<45;i++)p=p.deep={};}],['ordinal',s=>s.nextSequence=0],['duplicate ordinal',s=>{s.nextSequence=3;s.steering.pending=[{sequence:1,message:message('a')},{sequence:1,message:message('b')}];}],['model signature',s=>s.runtime.modelBinding.signature='0'.repeat(64)],['model version',s=>s.runtime.modelBinding.version='v2'],['model provider',s=>s.runtime.modelBinding.provider='foreign'],['tool signature',s=>s.runtime.toolSignature='0'.repeat(64)],['unknown runtime key',s=>s.runtime.unexpected=1],['headers',s=>s.messages[0].headers={Authorization:'fixture'}],['function',s=>s.messages[0].callback=()=>{}],['instance',s=>s.messages[0].extension=new Date()]];
 const outcomes=[];for(const[name,change]of changes){const saved=structuredClone(f.saved);change(saved);const target=new Agent(f.options),before=JSON.stringify(target.state.messages);let error:string|undefined;try{target.restorePauseState(saved,'boundary');}catch(e){error=String(e);}outcomes.push({name,rejected:!!error,unchanged:before===JSON.stringify(target.state.messages)});}
 for(const [name,options]of [['tool version',{...f.options,initialState:{...f.options.initialState,tools:[{...tool,pauseVersion:'v2'}]}}],['config version',{...f.options,pauseBindingVersion:'v2'}]] as const){let rejected=false;try{new Agent(options).restorePauseState(f.saved,'boundary');}catch{rejected=true;}outcomes.push({name,rejected,unchanged:true});}
 console.log(JSON.stringify({case:'V4-H',outcomes,effects:f.effects}));assert.ok(outcomes.every(o=>o.rejected&&o.unchanged));assert.deepEqual(f.effects,[]);
});

test('V4-I invalid message types and thinking enum are rejected at restore',async()=>{
 let calls=0;const options={sessionId:'invalid-shape',initialState:{model},streamFn:()=>{calls++;return new MockStream(assistant());}};const first=new Agent(options);await first.requestPause();const saved=first.exportPauseState();const outcomes=[];
 for(const[name,mutate]of [['thinking enum',(s:any)=>s.thinkingLevel='unsafe-level'],['user content',(s:any)=>s.messages=[{role:'user',content:42,timestamp:1}]],['unknown role',(s:any)=>s.messages=[{role:'undeclared-extension',data:{value:1}}]],['queued message',(s:any)=>{s.nextSequence=2;s.steering.pending=[{sequence:1,message:{role:42,content:null}}];}]] as const){const snapshot=structuredClone(saved);mutate(snapshot);let rejected=false;try{new Agent(options).restorePauseState(snapshot,'invalid-shape');}catch{rejected=true;}outcomes.push({name,rejected});}
 console.log(JSON.stringify({case:'V4-I',outcomes,calls}));assert.ok(outcomes.every(o=>o.rejected));assert.equal(calls,0);
});


