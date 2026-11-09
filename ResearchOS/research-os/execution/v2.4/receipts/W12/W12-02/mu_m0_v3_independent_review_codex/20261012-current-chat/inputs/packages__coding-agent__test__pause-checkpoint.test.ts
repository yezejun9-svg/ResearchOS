import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { Agent } from "@earendil-works/pi-agent-core";
import { type AssistantMessage, type AssistantMessageEvent, EventStream, type Model } from "@earendil-works/pi-ai";
// @ts-expect-error Candidate-only MJS worker fixture has no declaration file in the nine-file scope.
import { PauseCheckpointProtocol } from "../../../scripts/researchos-worker-pause-checkpoint.mjs";
import { AgentSession } from "../src/core/agent-session.ts";
import { AuthStorage } from "../src/core/auth-storage.ts";
import { createExtensionRuntime } from "../src/core/extensions/loader.ts";
import type { ResourceLoader } from "../src/core/resource-loader.ts";
import { SessionManager } from "../src/core/session-manager.ts";
import { SettingsManager } from "../src/core/settings-manager.ts";
import { createInMemoryModelRegistry, getModelRuntime } from "./model-runtime-test-utils.ts";

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

test("complete session header, entries and selected leaf survive restore without work", () => {
	const cwd = process.cwd();
	const session = SessionManager.inMemory(cwd, { id: "pause-session-1" });
	const first = session.appendMessage({ role: "user", content: "original", timestamp: 1 });
	const second = session.appendMessage({
		role: "assistant",
		content: [{ type: "text", text: "done" }],
		api: "openai-responses",
		provider: "fixture",
		model: "synthetic",
		stopReason: "stop",
		timestamp: 2,
		usage: {
			input: 1,
			output: 1,
			cacheRead: 0,
			cacheWrite: 0,
			totalTokens: 2,
			cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
		},
	});
	assert.notEqual(first, second);
	session.branch(first);
	const checkpoint = session.exportPauseCheckpoint();
	const restored = SessionManager.fromPauseCheckpoint(cwd, checkpoint, "pause-session-1");
	assert.deepEqual(restored.getHeader(), session.getHeader());
	assert.deepEqual(restored.getEntries(), session.getEntries());
	assert.equal(restored.getLeafId(), first);
	assert.equal(restored.getEntries().length, 2);
});

test("corrupt, cross-session, cross-context and invalid leaf checkpoints fail closed", () => {
	const cwd = process.cwd();
	const session = SessionManager.inMemory(cwd, { id: "pause-session-2" });
	session.appendMessage({ role: "user", content: "x", timestamp: 1 });
	const checkpoint = session.exportPauseCheckpoint();
	assert.throws(() => SessionManager.fromPauseCheckpoint(cwd, checkpoint, "other-session"));
	assert.throws(() => SessionManager.fromPauseCheckpoint(`${cwd}/other`, checkpoint, "pause-session-2"));
	const broken = structuredClone(checkpoint);
	broken.payload.entries[0].id = "changed";
	assert.throws(() => SessionManager.fromPauseCheckpoint(cwd, broken, "pause-session-2"));
	const badLeaf = structuredClone(checkpoint);
	badLeaf.payload.leafId = "missing";
	badLeaf.sha256 = createHash("sha256").update(JSON.stringify(badLeaf.payload)).digest("hex");
	assert.throws(() => SessionManager.fromPauseCheckpoint(cwd, badLeaf, "pause-session-2"));
});

test("AgentSession restore is passive, bound to session/epoch/input, and explicit resume consumes queued input", async () => {
	const cwd = process.cwd();
	const manager = SessionManager.inMemory(cwd, { id: "session-agent-1" });
	const calls = { count: 0 };
	const first = await createSession(manager, calls);
	first.agent.followUp({ role: "user", content: "queued", timestamp: 1 });
	await first.requestPause();
	const binding = { leaseEpoch: 4, inputHash: "b".repeat(64) };
	const checkpoint = first.exportPauseCheckpoint(binding);
	const restoredManager = SessionManager.fromPauseCheckpoint(cwd, checkpoint.payload.session, "session-agent-1");
	const resumed = await createSession(restoredManager, calls);
	const expected = { sessionId: "session-agent-1", ...binding };
	assert.throws(() => resumed.restorePauseCheckpoint(checkpoint, { ...expected, leaseEpoch: 5 }));
	assert.equal(calls.count, 0);
	resumed.restorePauseCheckpoint(checkpoint, expected);
	assert.equal(calls.count, 0);
	await resumed.resumePause();
	assert.equal(calls.count, 1);
	first.dispose();
	resumed.dispose();
});

test("uninstalled worker asks real candidate session to pause, then waits for matching ACK", async () => {
	const manager = SessionManager.inMemory(process.cwd(), { id: "session-worker-1" });
	const calls = { count: 0 };
	const session = await createSession(manager, calls);
	const binding = {
		runId: "run-1",
		sessionId: "session-worker-1",
		leaseEpoch: 6,
		inputHash: "c".repeat(64),
		processId: "fixture-process",
	};
	const safety = {
		modelStopped: true,
		toolsStopped: true,
		streamStopped: true,
		unknownEffects: false,
		unknownCost: false,
	};
	const frames: Array<{ type: string }> = [];
	const protocol = new PauseCheckpointProtocol(binding, (frame: { type: string }) => frames.push(frame));
	const frame = await protocol.requestPauseFromSession(session, safety);
	assert.equal(session.agent.isPaused, true);
	assert.equal(calls.count, 0);
	assert.deepEqual(
		frames.map((item) => item.type),
		["checkpoint"],
	);
	assert.equal(
		protocol.ack(
			{ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: true },
			safety,
		),
		true,
	);
	assert.deepEqual(
		frames.map((item) => item.type),
		["checkpoint", "turn.paused"],
	);
	session.dispose();
});

test("custom context arriving after pause waits for the unfinished tool batch", async () => {
	for (const restore of [false, true]) {
		const id = `paused-custom-${restore}`;
		const manager = SessionManager.inMemory(process.cwd(), { id });
		const calls = { count: 0 };
		const first = await createSession(manager, calls);
		let entered!: () => void;
		let release!: () => void;
		const started = new Promise<void>((resolve) => {
			entered = resolve;
		});
		const gate = new Promise<void>((resolve) => {
			release = resolve;
		});
		const effects: string[] = [];
		const tool: any = {
			name: "effect",
			label: "Effect",
			description: "fixture",
			parameters: {
				type: "object",
				properties: { id: { type: "string" } },
				required: ["id"],
				additionalProperties: false,
			},
			async execute(_callId: string, args: { id: string }) {
				if (args.id === "one") {
					entered();
					await gate;
				}
				effects.push(args.id);
				return { content: [{ type: "text", text: args.id }], details: null };
			},
		};
		const streamFn = () => {
			const response: AssistantMessage = {
				role: "assistant",
				api: "openai-responses",
				provider: "fixture",
				model: "fixture",
				content:
					++calls.count === 1
						? [
								{ type: "toolCall", id: "one", name: "effect", arguments: { id: "one" } },
								{ type: "toolCall", id: "two", name: "effect", arguments: { id: "two" } },
							]
						: [{ type: "text", text: "done" }],
				stopReason: calls.count === 1 ? "toolUse" : "stop",
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
				stream.push({
					type: "done",
					reason: response.stopReason === "toolUse" ? "toolUse" : "stop",
					message: response,
				});
				stream.end(response);
			});
			return stream;
		};
		first.agent.state.tools = [tool];
		first.agent.toolExecution = "sequential";
		first.agent.streamFunction = streamFn;
		const running = first.sendCustomMessage(
			{ customType: "start", content: "original", display: true },
			{ triggerTurn: true },
		);
		await started;
		const pausing = first.requestPause();
		release();
		await Promise.all([running, pausing]);
		let resumed = first;
		if (restore) {
			const before = first.exportPauseCheckpoint({ leaseEpoch: 1, inputHash: "a".repeat(64) });
			const restoredManager = SessionManager.fromPauseCheckpoint(process.cwd(), before.payload.session, id);
			resumed = await createSession(restoredManager, calls);
			resumed.agent.state.tools = [tool];
			resumed.agent.toolExecution = "sequential";
			resumed.agent.streamFunction = streamFn;
			resumed.restorePauseCheckpoint(before, { sessionId: id, leaseEpoch: 1, inputHash: "a".repeat(64) });
		}
		await resumed.sendCustomMessage(
			{ customType: "context", content: "arrived-after-pause", display: true, details: { retain: true } },
			{ triggerTurn: false },
		);
		const pending = resumed.exportPauseCheckpoint({ leaseEpoch: 1, inputHash: "a".repeat(64) });
		assert.equal(pending.payload.pendingCustom.length, 1);
		await resumed.resumePause();
		assert.deepEqual(effects, ["one", "two"]);
		first.dispose();
		if (restore) resumed.dispose();
	}
});
