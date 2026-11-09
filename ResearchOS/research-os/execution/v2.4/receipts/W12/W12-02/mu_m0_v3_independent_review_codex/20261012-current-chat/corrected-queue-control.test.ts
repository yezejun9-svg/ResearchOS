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


test('V3-C JSON roundtrip keeps consumed one-at-a-time steering and pending ordinal distinct',async()=>{
 let enter!:()=>void,release!:()=>void;const entered=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);let calls=0,prepares=0;const seen:any[]=[];
 const opts={sessionId:'json-steering',initialState:{model},prepareNextTurn:async()=>{prepares++;if(prepares===1){enter();await gate;}return{messages:[message('prepared-'+prepares)]};},streamFn:(_m:any,context:any)=>{calls++;seen.push(context.messages.filter((m:any)=>m.role==='user').map((m:any)=>m.content[0].text));return new MockStream(assistant());}};
 const first=new Agent(opts);first.subscribe(e=>{if(e.type==='turn_end'&&calls===1){first.steer(message('s1'));first.steer(message('s2'));}});const running=first.prompt(message('original'));await entered;const pausing=first.requestPause();release();await Promise.all([running,pausing]);const saved=JSON.parse(JSON.stringify(first.exportPauseState()));
 assert.equal(saved.steering.lastConsumedSequence,1);assert.equal(saved.steering.pending[0].sequence,2);assert.equal(saved.continuation.stage,'beforeRequest');assert.equal(saved.messages.filter((m:any)=>m.role==='user'&&m.content[0].text==='s1').length,1);
 const restored=new Agent(opts);restored.restorePauseState(saved,'json-steering');assert.deepEqual(JSON.parse(JSON.stringify(restored.exportPauseState())),saved);await restored.resumePaused();assert.equal(calls,3);assert.equal(prepares,2);assert.equal(restored.state.messages.filter((m:any)=>m.role==='user'&&m.content[0].text==='s1').length,1);assert.equal(restored.state.messages.filter((m:any)=>m.role==='user'&&m.content[0].text==='s2').length,1);await restored.requestPause();const after=restored.exportPauseState();assert.equal(after.steering.lastConsumedSequence,2);assert.equal(after.steering.pending.length,0);
});
