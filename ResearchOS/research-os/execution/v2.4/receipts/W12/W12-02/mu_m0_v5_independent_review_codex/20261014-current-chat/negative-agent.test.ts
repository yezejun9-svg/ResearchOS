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
