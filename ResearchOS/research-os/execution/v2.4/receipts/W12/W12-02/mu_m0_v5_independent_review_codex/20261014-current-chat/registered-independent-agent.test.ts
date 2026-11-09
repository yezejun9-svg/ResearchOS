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

test('pause during async transform does not start a new provider request', async () => {
 let enter!:()=>void, release!:()=>void; const started=new Promise<void>(r=>enter=r), gate=new Promise<void>(r=>release=r); let calls=0;
 const agent=new Agent({sessionId:'transform-pause',initialState:{model},streamFn:()=>{calls++;return new MockStream(assistant());},transformContext:async messages=>{enter();await gate;return messages;}});
 const running=agent.prompt(message('original')); await started; const pause=agent.requestPause(); release(); await Promise.all([running,pause]);
 assert.equal(calls,0,'pause arrived before provider dispatch, but provider was called');
});

test('resume preserves completed non-terminating result when remaining result terminates',async()=>{
 let enter!:()=>void, release!:()=>void; const started=new Promise<void>(r=>enter=r), gate=new Promise<void>(r=>release=r); let calls=0; const effects:string[]=[];
 const tool={name:'effect',label:'Effect',description:'synthetic',parameters:Type.Object({id:Type.String()}),async execute(_id:string,p:any){if(p.id==='one'){enter();await gate;}effects.push(p.id);return{content:[{type:'text' as const,text:p.id}],details:null,terminate:p.id==='two'};}};
 const streamFn=()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'effect',arguments:{id:'one'}},{type:'toolCall',id:'two',name:'effect',arguments:{id:'two'}}]}:assistant());};
 const options={sessionId:'termination',initialState:{model,tools:[tool]},toolExecution:'sequential' as const,streamFn};
 const first=new Agent(options);const running=first.prompt(message('original'));await started;const pause=first.requestPause();release();await Promise.all([running,pause]);
 const state=first.exportPauseState();const restored=new Agent(options);restored.restorePauseState(state,'termination');await restored.resumePaused();
 assert.deepEqual(effects,['one','two']);assert.equal(calls,2,'original batch has a non-terminating result, so continuation must run');
});

test('resume remaining tools invokes prepareNextTurn before the next model',async()=>{
 let enter!:()=>void,release!:()=>void;const started=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0;let prepares=0;
 const tool={name:'effect',label:'Effect',description:'synthetic',parameters:Type.Object({id:Type.String()}),async execute(_id:string,p:any){if(p.id==='one'){enter();await gate;}return{content:[{type:'text' as const,text:p.id}],details:null};}};
 const streamFn=()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'effect',arguments:{id:'one'}},{type:'toolCall',id:'two',name:'effect',arguments:{id:'two'}}]}:assistant());};
 const options={sessionId:'prepare',initialState:{model,tools:[tool]},toolExecution:'sequential' as const,streamFn,prepareNextTurn:()=>{prepares++;return {messages:[message('required-context')]};}};
 const first=new Agent(options);const running=first.prompt(message('original'));await started;const pause=first.requestPause();release();await Promise.all([running,pause]);
 const restored=new Agent(options);restored.restorePauseState(first.exportPauseState(),'prepare');await restored.resumePaused();
 assert.equal(calls,2);assert.equal(prepares,1,'completed resumed tool turn must prepare the next request');
});

test('pause after fully terminating tool batch does not add model work on resume',async()=>{
 let enter!:()=>void,release!:()=>void;const started=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0;
 const tool={name:'stop',label:'Stop',description:'synthetic',parameters:Type.Object({}),async execute(){enter();await gate;return{content:[{type:'text' as const,text:'stop'}],details:null,terminate:true};}};
 const streamFn=()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'stop',name:'stop',arguments:{}}]}:assistant());};
 const options={sessionId:'stop',initialState:{model,tools:[tool]},streamFn};const first=new Agent(options);const running=first.prompt(message('original'));await started;const pause=first.requestPause();release();await Promise.all([running,pause]);
 const restored=new Agent(options);restored.restorePauseState(first.exportPauseState(),'stop');await restored.resumePaused();assert.equal(calls,1,'terminated batch must not dispatch another model');
});

test('custom raw queues preserve all fields and monotone watermarks',async()=>{
 const options={sessionId:'custom',initialState:{model,messages:[message('original'),assistant()]},streamFn:()=>new MockStream(assistant()),pauseDataRegistrations:[{kind:'message' as const,role:'custom',customType:'review',version:'1',schema:{type:'object' as const,properties:{role:{type:'literal' as const,value:'custom'},customType:{type:'literal' as const,value:'review'},content:{type:'array' as const,items:{type:'object' as const,properties:{type:{type:'literal' as const,value:'text'},text:{type:'string' as const}}}},display:{type:'boolean' as const},details:{type:'object' as const,properties:{id:{type:'string' as const},nested:{type:'object' as const,properties:{retained:{type:'boolean' as const}}}}},timestamp:{type:'number' as const}}}}]};
 const first=new Agent(options);first.steeringMode='all';first.followUpMode='all';
 const custom=(id:string)=>({role:'custom',customType:'review',content:[{type:'text',text:id}],display:true,details:{id,nested:{retained:true}},timestamp:22} as any);
 first.steer(custom('s1'));first.steer(custom('s2'));first.followUp(custom('f1'));first.followUp(custom('f2'));await first.requestPause();const snapshot=first.exportPauseState();
 const restored=new Agent(options);restored.restorePauseState(snapshot,'custom');assert.deepEqual(restored.exportPauseState(),snapshot);await restored.resumePaused();await restored.requestPause();const after=restored.exportPauseState();assert.equal(after.steering.pending.length,0);assert.equal(after.followUp.pending.length,0);assert.equal(after.steering.lastConsumedSequence,2);assert.equal(after.followUp.lastConsumedSequence,4);
});

test('unpaused controls retain complete-batch termination and next-turn preparation',async()=>{
 for(const terminateAll of [false,true]){
  let calls=0,prepares=0;const effects:string[]=[];
  const tool={name:'effect',label:'Effect',description:'synthetic',parameters:Type.Object({id:Type.String()}),async execute(_id:string,p:any){effects.push(p.id);return{content:[{type:'text' as const,text:p.id}],details:null,terminate:terminateAll||p.id==='two'};}};
  const agent=new Agent({sessionId:'control',initialState:{model,tools:[tool]},toolExecution:'sequential',prepareNextTurn:()=>{prepares++;return{messages:[message('required-context')]};},streamFn:()=>{calls++;return new MockStream(calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'effect',arguments:{id:'one'}},{type:'toolCall',id:'two',name:'effect',arguments:{id:'two'}}]}:assistant());}});
  await agent.prompt(message('original'));assert.deepEqual(effects,['one','two']);assert.equal(calls,terminateAll?1:2);assert.equal(prepares,terminateAll?0:1);
 }
});

test('restore rejects watermark greater than next sequence even with empty pending queue',async()=>{
 const options={sessionId:'watermark',initialState:{model},streamFn:()=>new MockStream(assistant())};const first=new Agent(options);await first.requestPause();const snapshot=first.exportPauseState();snapshot.steering.lastConsumedSequence=99;
 const target=new Agent(options);assert.throws(()=>target.restorePauseState(snapshot,'watermark'));
});

