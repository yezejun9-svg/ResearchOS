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

test('V4-E control preparation-selected registered-only tool works without pause',async()=>{
 const seen:any[]=[];const tool={name:'registered_only',label:'Registered',description:'safe fixture',pauseVersion:'v1',parameters:Type.Object({}),async execute(){throw Error('not expected');}};
 const first=new Agent({sessionId:'unpaused',initialState:{model},pauseToolRegistry:[tool],prepareRequest:r=>({context:{messages:r.context.messages,tools:[tool]}}),streamFn:(_model,context)=>{seen.push(context.tools?.map(t=>t.name));return new MockStream(assistant());}});await first.prompt(message('safe'));assert.equal(first.state.errorMessage,undefined);assert.deepEqual(seen,[['registered_only']]);console.log(JSON.stringify({case:'V4-E-control',seen}));
});

test('V4-F control registration changed before restore is rejected without dispatch',async()=>{
 const f=await preparedFixture();f.selected.baseUrl='https://changed.invalid.example';let error:string|undefined;try{new Agent(f.options).restorePauseState(f.saved,'boundary');}catch(e){error=String(e);}assert.match(error??'',/registration changed/);assert.deepEqual(f.effects,[]);console.log(JSON.stringify({case:'V4-F-control',error,effects:f.effects}));
});

test('V4-G control valid built-in message has no credential or executable checkpoint payload',async()=>{
 const f=await preparedFixture();const saved=JSON.stringify(f.saved);assert.ok(!saved.includes('baseUrl'));assert.ok(!saved.includes('execute'));assert.ok(!saved.includes('getApiKey'));assert.ok(!saved.includes('headers'));const target=new Agent(f.options);target.restorePauseState(f.saved,'boundary');assert.deepEqual(f.effects,[]);await target.resumePaused();assert.equal(f.effects.length,1);assert.equal(f.prepares(),1);console.log(JSON.stringify({case:'V4-G-control',passiveRestore:true,resumeCalls:f.effects.length,prepares:f.prepares()}));
});

