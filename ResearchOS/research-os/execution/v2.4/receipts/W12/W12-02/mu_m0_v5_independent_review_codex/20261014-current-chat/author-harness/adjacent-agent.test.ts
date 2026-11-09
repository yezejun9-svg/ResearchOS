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


for(const pauseAt of ['response','finish'] as const){
 test('V3-A runtime model and replacement context survive '+pauseAt+' pause',async()=>{
  const runs:any[]=[];
  for(const enabled of [false,true]){
   let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0,finishes=0;const models:string[]=[],contexts:any[]=[],finishContexts:any[]=[];
   const selectedModel={...model,id:'selected-runtime-model'}; const opts={sessionId:'runtime-state-'+pauseAt,initialState:{model},pauseModels:[{key:'selected',version:'1',model:selectedModel}],prepareRequest:()=>{prepares++;return prepares===1?{model:selectedModel,context:{messages:[message('compacted-context')],tools:[]}}:undefined;},finishTurn:async(turn:any)=>{finishes++;finishContexts.push(turn.context.messages.filter((m:any)=>m.role==='user').map((m:any)=>m.content[0].text));if(finishes===1&&pauseAt==='finish'&&enabled){enter();await gate;}return{action:finishes===1?'continue' as const:'end' as const};},streamFn:async(activeModel:any,context:any)=>{calls++;models.push(activeModel.id);contexts.push(context.messages.filter((m:any)=>m.role==='user').map((m:any)=>m.content[0].text));if(calls===1&&pauseAt==='response'&&enabled){enter();await gate;}return new MockStream(assistant());}};
   const first=new Agent(opts);const running=first.prompt(message('original-context'));
   if(enabled){await entered;const pausing=first.requestPause();release();await Promise.all([running,pausing]);const snapshot=JSON.parse(JSON.stringify(first.exportPauseState()));const restored=new Agent(opts);restored.restorePauseState(snapshot,opts.sessionId);assert.equal(calls,1);await restored.resumePaused();assert.equal(restored.state.errorMessage,undefined);}else await running;
   runs.push({enabled,calls,prepares,finishes,models,contexts,finishContexts});
  }
  console.log(JSON.stringify({case:'V3-A-'+pauseAt,runs}));assert.deepEqual(runs[1].models,runs[0].models);assert.deepEqual(runs[1].contexts,runs[0].contexts);assert.deepEqual(runs[1].finishContexts,runs[0].finishContexts);assert.equal(runs[1].prepares,2);assert.equal(runs[1].finishes,2);
 });
}
test('V3-B restored tool batch retains per-request restricted tool loadout',async()=>{
 const runs:any[]=[];
 for(const enabled of [false,true]){
  let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0;const effects:string[]=[];
  const firstTool={name:'allowed',label:'Allowed',description:'fixture',parameters:Type.Object({}),async execute(){if(enabled){enter();await gate;}effects.push('allowed');return{content:[{type:'text' as const,text:'ok'}],details:null};}};
  const excludedTool={name:'excluded',label:'Excluded',description:'not in this turn loadout',parameters:Type.Object({}),async execute(){effects.push('excluded');return{content:[{type:'text' as const,text:'unexpected'}],details:null};}};
  const opts={sessionId:'restricted-tools',initialState:{model,tools:[firstTool,excludedTool]},toolExecution:'sequential' as const,prepareRequest:(request:any)=>({context:{...request.context,tools:[firstTool]}}),streamFn:()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'allowed',arguments:{}},{type:'toolCall',id:'two',name:'excluded',arguments:{}}]}:assistant());}};
  const first=new Agent(opts);const running=first.prompt(message('original'));let final=first;
  if(enabled){await entered;const pausing=first.requestPause();release();await Promise.all([running,pausing]);const saved=JSON.parse(JSON.stringify(first.exportPauseState()));final=new Agent(opts);final.restorePauseState(saved,opts.sessionId);await final.resumePaused();}else await running;
  runs.push({enabled,effects,calls,resultErrors:final.state.messages.filter((m:any)=>m.role==='toolResult').map((m:any)=>({id:m.toolCallId,isError:m.isError})),error:final.state.errorMessage});
 }
 console.log(JSON.stringify({case:'V3-B',runs}));assert.deepEqual(runs[1].effects,runs[0].effects);assert.deepEqual(runs[1].resultErrors,runs[0].resultErrors);assert.deepEqual(runs[0].effects,['allowed']);
});
test('V3-C JSON roundtrip keeps consumed one-at-a-time steering and pending ordinal distinct',async()=>{
 let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0;const seen:any[]=[];
 const opts={sessionId:'json-steering',initialState:{model},prepareNextTurn:async()=>{prepares++;if(prepares===1){enter();await gate;}return{messages:[message('prepared-'+prepares)]};},streamFn:(_m:any,context:any)=>{calls++;seen.push(context.messages.filter((m:any)=>m.role==='user').map((m:any)=>m.content[0].text));return new MockStream(assistant());}};
 const first=new Agent(opts);first.subscribe(e=>{if(e.type==='turn_end'&&calls===1){first.steer(message('s1'));first.steer(message('s2'));}});const running=first.prompt(message('original'));await entered;const pausing=first.requestPause();release();await Promise.all([running,pausing]);const saved=JSON.parse(JSON.stringify(first.exportPauseState()));
 assert.equal(saved.steering.lastConsumedSequence,1);assert.equal(saved.steering.pending[0].sequence,2);assert.equal(saved.continuation.pendingMessages[0].content[0].text,'s1');
 const restored=new Agent(opts);restored.restorePauseState(saved,'json-steering');assert.deepEqual(JSON.parse(JSON.stringify(restored.exportPauseState())),saved);await restored.resumePaused();assert.equal(calls,3);assert.equal(prepares,2);assert.equal(restored.state.messages.filter((m:any)=>m.role==='user'&&m.content[0].text==='s1').length,1);assert.equal(restored.state.messages.filter((m:any)=>m.role==='user'&&m.content[0].text==='s2').length,1);await restored.requestPause();const after=restored.exportPauseState();assert.equal(after.steering.lastConsumedSequence,2);assert.equal(after.steering.pending.length,0);
});
test('V3-D prepared-request JSON survives repeated pause without another prepareRequest',async()=>{
 let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0;
 const preparedModel={...model,id:'prepared'}; const opts={sessionId:'repeat-pause',initialState:{model},pauseModels:[{key:'prepared',version:'1',model:preparedModel}],prepareRequest:async()=>{prepares++;enter();await gate;return{model:preparedModel};},streamFn:()=>{calls++;return new MockStream(assistant());}};
 const first=new Agent(opts);const running=first.prompt(message('original'));await entered;const pausing=first.requestPause();release();await Promise.all([running,pausing]);let saved=JSON.parse(JSON.stringify(first.exportPauseState()));const middle=new Agent(opts);middle.restorePauseState(saved,'repeat-pause');let secondPause:Promise<void>|undefined;middle.subscribe(e=>{if(e.type==='agent_start')secondPause=middle.requestPause();});await middle.resumePaused();await secondPause;assert.equal(calls,0);assert.equal(prepares,1);saved=JSON.parse(JSON.stringify(middle.exportPauseState()));const final=new Agent(opts);final.restorePauseState(saved,'repeat-pause');await final.resumePaused();assert.equal(calls,1);assert.equal(prepares,1);
});
