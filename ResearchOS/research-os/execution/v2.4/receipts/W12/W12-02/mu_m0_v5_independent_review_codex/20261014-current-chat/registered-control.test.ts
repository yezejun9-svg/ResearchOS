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

test('V4-E corrected control registered-only tool executes once without pause',async()=>{
 const effects:string[]=[];let calls=0;const tool={name:'registered_only',label:'Registered',description:'safe fixture',pauseVersion:'v1',parameters:Type.Object({}),async execute(){effects.push('registered_only');return{content:[{type:'text' as const,text:'ok'}],details:null};}};
 const first=new Agent({sessionId:'unpaused',initialState:{model},pauseToolRegistry:[tool],prepareRequest:r=>({context:{messages:r.context.messages,tools:[tool]}}),streamFn:()=>new MockStream(++calls===1?{...assistant(),stopReason:'toolUse',content:[{type:'toolCall',id:'one',name:'registered_only',arguments:{}}]}:assistant())});await first.prompt(message('safe'));assert.equal(first.state.errorMessage,undefined);assert.equal(calls,2);assert.deepEqual(effects,['registered_only']);console.log(JSON.stringify({case:'V4-E-corrected-control',calls,effects}));
});

