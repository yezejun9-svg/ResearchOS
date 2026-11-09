import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { Agent } from "@earendil-works/pi-agent-core";
import { type AssistantMessage, type AssistantMessageEvent, EventStream, type Model } from "@earendil-works/pi-ai";
// @ts-expect-error Candidate-only MJS worker fixture has no declaration file in the nine-file scope.
import { PauseCheckpointProtocol } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/scripts/researchos-worker-pause-checkpoint.mjs";
import { AgentSession } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/agent-session.ts";
import { AuthStorage } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/auth-storage.ts";
import { createExtensionRuntime } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/extensions/loader.ts";
import type { ResourceLoader } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/resource-loader.ts";
import { SessionManager } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/session-manager.ts";
import { SettingsManager } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/src/core/settings-manager.ts";
import { createInMemoryModelRegistry, getModelRuntime } from "C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-pause-checkpoint-m0-20261012/packages/coding-agent/test/model-runtime-test-utils.ts";

const model: Model<"openai-responses"> = {
	id: "fixture",
	name: "fixture",
	api: "openai-responses",
	provider: "fixture",
	baseUrl: "https://invalid.example",
	reasoning: false,
	input: ["text"],
	cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
	contextWindow: 4096,
	maxTokens: 256,
};
const loader: ResourceLoader = {
	getExtensions: () => ({ extensions: [], errors: [], runtime: createExtensionRuntime() }),
	getSkills: () => ({ skills: [], diagnostics: [] }),
	getPrompts: () => ({ prompts: [], diagnostics: [] }),
	getThemes: () => ({ themes: [], diagnostics: [] }),
	getAgentsFiles: () => ({ agentsFiles: [] }),
	getSystemPrompt: () => undefined,
	getSystemPromptSource: () => undefined,
	getAppendSystemPrompt: () => [],
	getAppendSystemPromptSources: () => [],
	extendResources: () => {},
	reload: async () => {},
};

async function createSession(manager: SessionManager, calls: { count: number }): Promise<AgentSession> {
	const authStorage = AuthStorage.inMemory();
	const registry = await createInMemoryModelRegistry(authStorage);
	const streamFn = () => {
		calls.count++;
		const message: AssistantMessage = {
			role: "assistant",
			content: [{ type: "text", text: "fixture" }],
			api: "openai-responses",
			provider: "fixture",
			model: "fixture",
			stopReason: "stop",
			timestamp: 1,
			usage: {
				input: 1,
				output: 1,
				cacheRead: 0,
				cacheWrite: 0,
				totalTokens: 2,
				cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
			},
		};
		const stream = new EventStream<AssistantMessageEvent, AssistantMessage>(
			(event) => event.type === "done",
			(event) => {
				if (event.type !== "done") throw new Error("unexpected event");
				return event.message;
			},
		);
		queueMicrotask(() => {
			stream.push({ type: "done", reason: "stop", message });
			stream.end(message);
		});
		return stream;
	};
	return new AgentSession({
		agent: new Agent({ sessionId: manager.getSessionId(), initialState: { model, tools: [] }, streamFn }),
		sessionManager: manager,
		settingsManager: SettingsManager.inMemory(),
		cwd: process.cwd(),
		modelRuntime: getModelRuntime(registry),
		resourceLoader: loader,
		baseToolsOverride: {},
	});
}

test('session pause keeps deferred custom message out of incomplete tool batch',async()=>{
 for(const pauseEnabled of [false,true]){
  const id='session-custom-'+pauseEnabled;const manager=SessionManager.inMemory(process.cwd(),{id});const calls={count:0};const session=await createSession(manager,calls);
  let enter!:()=>void,release!:()=>void;const started=new Promise<void>(r=>enter=r),gate=new Promise<void>(r=>release=r);const effects:string[]=[];
  const tool:any={name:'effect',label:'Effect',description:'synthetic',parameters:{type:'object',properties:{id:{type:'string'}},required:['id'],additionalProperties:false},async execute(_id:string,p:any){if(p.id==='one'){enter();await gate;}effects.push(p.id);return{content:[{type:'text',text:p.id}],details:null};}};
  session.agent.state.tools=[tool];session.agent.toolExecution='sequential';
  session.agent.streamFunction=()=>{calls.count++;const response:AssistantMessage={role:'assistant',content:calls.count===1?[{type:'toolCall',id:'one',name:'effect',arguments:{id:'one'}},{type:'toolCall',id:'two',name:'effect',arguments:{id:'two'}}]:[{type:'text',text:'done'}],api:'openai-responses',provider:'fixture',model:'fixture',stopReason:calls.count===1?'toolUse':'stop',timestamp:1,usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}}};const stream=new EventStream<AssistantMessageEvent,AssistantMessage>(e=>e.type==='done',e=>{if(e.type!=='done')throw Error('unexpected');return e.message;});queueMicrotask(()=>{stream.push({type:'done',reason:response.stopReason==='toolUse'?'toolUse':'stop',message:response});stream.end(response);});return stream;};
  const running=session.sendCustomMessage({customType:'start',content:'original',display:true},{triggerTurn:true});await started;
  await session.sendCustomMessage({customType:'context',content:'deferred',display:true,details:{retain:true}},{triggerTurn:false});
  const pausing=pauseEnabled?session.requestPause():Promise.resolve();release();await Promise.all([running,pausing]);
  if(!pauseEnabled){assert.deepEqual(effects,['one','two']);assert.equal(calls.count,2);session.dispose();continue;}
  const checkpoint=session.exportPauseCheckpoint({leaseEpoch:1,inputHash:'a'.repeat(64)});
  console.log(JSON.stringify({case:'deferred-custom-pause',pendingCustom:checkpoint.payload.pendingCustom.length,roles:checkpoint.payload.agent.messages.map(m=>m.role),effects,calls:calls.count}));
  await session.resumePause();
  console.log(JSON.stringify({case:'deferred-custom-resume',error:session.agent.state.errorMessage,effects,calls:calls.count}));
  session.dispose();assert.deepEqual(effects,['one','two'],'deferred custom context must not make unfinished batch unresumable');
 }
});

test('session bounded restore retains retry counters and rejects corrupt hash or oversized payload',async()=>{
 const manager=SessionManager.inMemory(process.cwd(),{id:'boundaries'});const calls={count:0};const session=await createSession(manager,calls);await session.requestPause();const binding={leaseEpoch:8,inputHash:'b'.repeat(64)};const snapshot=session.exportPauseCheckpoint(binding);const expected={sessionId:'boundaries',...binding};
 snapshot.payload.retryAttempt=3;snapshot.payload.overflowRecoveryAttempted=true;snapshot.sha256=createHash('sha256').update(JSON.stringify(snapshot.payload)).digest('hex');session.restorePauseCheckpoint(snapshot,expected);assert.equal(session.exportPauseCheckpoint(binding).payload.retryAttempt,3);assert.equal(session.exportPauseCheckpoint(binding).payload.overflowRecoveryAttempted,true);assert.equal(calls.count,0);
 assert.throws(()=>session.restorePauseCheckpoint({...snapshot,sha256:'0'.repeat(64)},expected));const oversized=structuredClone(snapshot);oversized.payload.uiSteering=['x'.repeat(12*1024*1024)];oversized.sha256=createHash('sha256').update(JSON.stringify(oversized.payload)).digest('hex');assert.throws(()=>session.restorePauseCheckpoint(oversized,expected));session.dispose();
});
