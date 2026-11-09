import assert from "node:assert/strict";
import { test } from "node:test";
import { type AssistantMessage, type AssistantMessageEvent, EventStream, type Model } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import { Agent } from "../src/agent.ts";
import type { AgentMessage } from "../src/types.ts";

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

test("both raw queues and consumption watermarks survive restore; only explicit continue calls model", async () => {
	let calls = 0;
	const options = {
		sessionId: "session-1",
		initialState: { model, messages: [message("original"), assistant()] },
		streamFn: () => {
			calls++;
			return new MockStream(assistant());
		},
	};
	const first = new Agent(options);
	first.steer(message("steer-1"));
	first.followUp(message("follow-1"));
	await first.requestPause();
	const snapshot = first.exportPauseState();
	assert.equal(snapshot.steering.pending[0].message.role, "user");
	assert.equal(snapshot.followUp.pending[0].message.role, "user");
	assert.notEqual(snapshot.steering.pending[0].sequence, snapshot.followUp.pending[0].sequence);
	const restored = new Agent(options);
	restored.restorePauseState(snapshot, "session-1");
	assert.equal(calls, 0);
	await restored.resumePaused();
	assert.equal(calls, 2);
	assert.equal(restored.hasQueuedMessages(), false);
	await restored.requestPause();
	const after = restored.exportPauseState();
	assert.ok(after.steering.lastConsumedSequence > 0);
	assert.ok(after.followUp.lastConsumedSequence > 0);
	assert.equal(after.messages.filter((item) => item.role === "user").length, 3);
});

test("restore rejects cross-session and consumed watermark corruption without mutating target", async () => {
	const options = {
		sessionId: "session-1",
		initialState: { model, messages: [message("original"), assistant()] },
		streamFn: () => new MockStream(assistant()),
	};
	const first = new Agent(options);
	first.steer(message("pending"));
	await first.requestPause();
	const checkpoint = first.exportPauseState();
	const target = new Agent(options);
	assert.throws(() => target.restorePauseState(checkpoint, "another-session"));
	checkpoint.steering.pending[0].sequence = checkpoint.steering.lastConsumedSequence;
	assert.throws(() => target.restorePauseState(checkpoint, "session-1"));
	assert.equal(target.hasQueuedMessages(), false);
});

test("pause during a sequential tool settles the active effect and resumes only the missing call", async () => {
	let modelCalls = 0;
	const effects: string[] = [];
	let firstStarted!: () => void;
	let releaseFirst!: () => void;
	const started = new Promise<void>((resolve) => {
		firstStarted = resolve;
	});
	const release = new Promise<void>((resolve) => {
		releaseFirst = resolve;
	});
	const tool = {
		name: "write",
		label: "Write",
		description: "synthetic effect",
		parameters: Type.Object({ id: Type.String() }),
		async execute(_toolCallId: string, params: unknown) {
			const args = params as { id: string };
			if (args.id === "one") {
				firstStarted();
				await release;
			}
			effects.push(args.id);
			return { content: [{ type: "text" as const, text: args.id }], details: { id: args.id } };
		},
	};
	const streamFn = () => {
		modelCalls++;
		return new MockStream(
			modelCalls === 1
				? {
						...assistant(),
						stopReason: "toolUse",
						content: [
							{ type: "toolCall", id: "call-one", name: "write", arguments: { id: "one" } },
							{ type: "toolCall", id: "call-two", name: "write", arguments: { id: "two" } },
						],
					}
				: assistant(),
		);
	};
	const options = {
		sessionId: "session-tools",
		initialState: { model, tools: [tool] },
		toolExecution: "sequential" as const,
		streamFn,
	};
	const first = new Agent(options);
	const running = first.prompt(message("go"));
	await started;
	const pausing = first.requestPause();
	releaseFirst();
	await Promise.all([running, pausing]);
	assert.deepEqual(effects, ["one"]);
	assert.equal(modelCalls, 1);
	const checkpoint = first.exportPauseState();
	assert.deepEqual(
		checkpoint.messages.filter((item) => item.role === "toolResult").map((item) => item.toolCallId),
		["call-one"],
	);
	const restored = new Agent(options);
	restored.restorePauseState(checkpoint, "session-tools");
	assert.deepEqual(effects, ["one"]);
	await restored.resumePaused();
	assert.deepEqual(effects, ["one", "two"]);
	assert.equal(modelCalls, 2);
	assert.deepEqual(
		restored.state.messages.filter((item) => item.role === "toolResult").map((item) => item.toolCallId),
		["call-one", "call-two"],
	);
});

test("pause during a parallel batch settles every launched effect before checkpoint", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	const effects: string[] = [];
	let calls = 0;
	const tool = {
		name: "parallel-effect",
		label: "Parallel effect",
		description: "synthetic",
		parameters: Type.Object({ id: Type.String() }),
		async execute(_id: string, params: unknown) {
			const id = (params as { id: string }).id;
			if (id === "one") {
				entered();
				await gate;
			}
			effects.push(id);
			return { content: [{ type: "text" as const, text: id }], details: null };
		},
	};
	const streamFn = () => {
		calls++;
		return new MockStream(
			calls === 1
				? {
						...assistant(),
						stopReason: "toolUse",
						content: [
							{ type: "toolCall", id: "parallel-one", name: "parallel-effect", arguments: { id: "one" } },
							{ type: "toolCall", id: "parallel-two", name: "parallel-effect", arguments: { id: "two" } },
						],
					}
				: assistant(),
		);
	};
	const options = {
		sessionId: "parallel-session",
		initialState: { model, tools: [tool] },
		toolExecution: "parallel" as const,
		streamFn,
	};
	const running = new Agent(options);
	const prompt = running.prompt(message("go"));
	await started;
	const pausing = running.requestPause();
	release();
	await Promise.all([prompt, pausing]);
	const snapshot = running.exportPauseState();
	assert.deepEqual(new Set(effects), new Set(["one", "two"]));
	assert.equal(calls, 1);
	assert.deepEqual(
		snapshot.messages.filter((item) => item.role === "toolResult").map((item) => item.toolCallId),
		["parallel-one", "parallel-two"],
	);
	const restored = new Agent(options);
	restored.restorePauseState(snapshot, "parallel-session");
	await restored.resumePaused();
	assert.equal(calls, 2);
	assert.deepEqual(new Set(effects), new Set(["one", "two"]));
});

test("cooperative tool settles on pause request without cancellation", async () => {
	let entered!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	let releaseTool!: () => void;
	const stop = new Promise<void>((resolve) => {
		releaseTool = resolve;
	});
	let pauseSeen = false;
	let cancelled = false;
	let modelCalls = 0;
	const tool = {
		name: "cooperative",
		label: "Cooperative",
		description: "synthetic",
		parameters: Type.Object({}),
		requestPause() {
			pauseSeen = true;
			releaseTool();
		},
		async execute(_id: string, _params: unknown, cancelSignal?: AbortSignal) {
			entered();
			await stop;
			cancelled = cancelSignal?.aborted ?? false;
			return { content: [{ type: "text" as const, text: "known-stopped" }], details: null };
		},
	};
	const streamFn = () => {
		modelCalls++;
		return new MockStream(
			modelCalls === 1
				? {
						...assistant(),
						stopReason: "toolUse",
						content: [{ type: "toolCall", id: "cooperative-1", name: "cooperative", arguments: {} }],
					}
				: assistant(),
		);
	};
	const agent = new Agent({ sessionId: "session-cooperative", initialState: { model, tools: [tool] }, streamFn });
	const running = agent.prompt(message("go"));
	await started;
	await Promise.all([running, agent.requestPause()]);
	assert.equal(pauseSeen, true);
	assert.equal(cancelled, false);
	assert.equal(modelCalls, 1);
	assert.equal(agent.exportPauseState().messages.filter((item) => item.role === "toolResult").length, 1);
});

test("pause during model stream waits for its final message and fences the next tool", async () => {
	let modelCalls = 0;
	let effects = 0;
	let releaseModel!: () => void;
	let modelStarted!: () => void;
	const started = new Promise<void>((resolve) => {
		modelStarted = resolve;
	});
	const modelRelease = new Promise<void>((resolve) => {
		releaseModel = resolve;
	});
	const tool = {
		name: "effect",
		label: "Effect",
		description: "synthetic",
		parameters: Type.Object({}),
		async execute() {
			effects++;
			return { content: [{ type: "text" as const, text: "ok" }], details: null };
		},
	};
	const toolMessage = {
		...assistant(),
		stopReason: "toolUse" as const,
		content: [{ type: "toolCall" as const, id: "effect-1", name: "effect", arguments: {} }],
	};
	const streamFn = () => {
		modelCalls++;
		if (modelCalls > 1) return new MockStream(assistant());
		const stream = new EventStream<AssistantMessageEvent, AssistantMessage>(
			(event) => event.type === "done",
			(event) => {
				if (event.type !== "done") throw new Error("unexpected event");
				return event.message;
			},
		);
		modelStarted();
		void modelRelease.then(() => {
			stream.push({ type: "done", reason: "toolUse", message: toolMessage });
			stream.end(toolMessage);
		});
		return stream;
	};
	const options = { sessionId: "session-stream", initialState: { model, tools: [tool] }, streamFn };
	const running = new Agent(options);
	const prompt = running.prompt(message("go"));
	await started;
	const pausing = running.requestPause();
	releaseModel();
	await Promise.all([prompt, pausing]);
	assert.equal(effects, 0);
	assert.equal(modelCalls, 1);
	const snapshot = running.exportPauseState();
	const resumed = new Agent(options);
	resumed.restorePauseState(snapshot, "session-stream");
	assert.equal(effects, 0);
	await resumed.resumePaused();
	assert.equal(effects, 1);
	assert.equal(modelCalls, 2);
});

test("turn-end pause leaves completed output intact and explicit resume performs no duplicate request", async () => {
	let calls = 0;
	let modelStarted!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		modelStarted = resolve;
	});
	const wait = new Promise<void>((resolve) => {
		release = resolve;
	});
	const response = assistant();
	const streamFn = () => {
		calls++;
		const stream = new EventStream<AssistantMessageEvent, AssistantMessage>(
			(event) => event.type === "done",
			(event) => {
				if (event.type !== "done") throw new Error("unexpected event");
				return event.message;
			},
		);
		modelStarted();
		void wait.then(() => {
			stream.push({ type: "done", reason: "stop", message: response });
			stream.end(response);
		});
		return stream;
	};
	const first = new Agent({ sessionId: "session-end", initialState: { model }, streamFn });
	const running = first.prompt(message("go"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const snapshot = first.exportPauseState();
	assert.equal(snapshot.messages.filter((item) => item.role === "assistant").length, 1);
	const restored = new Agent({ sessionId: "session-end", initialState: { model }, streamFn });
	restored.restorePauseState(snapshot, "session-end");
	await restored.resumePaused();
	assert.equal(calls, 1);
});

test("abort supersedes a pending pause without producing a checkpoint", async () => {
	let started!: () => void;
	let release!: () => void;
	const entered = new Promise<void>((resolve) => {
		started = resolve;
	});
	const wait = new Promise<void>((resolve) => {
		release = resolve;
	});
	const streamFn = () => {
		const stream = new EventStream<AssistantMessageEvent, AssistantMessage>(
			(event) => event.type === "done",
			(event) => {
				if (event.type !== "done") throw new Error("unexpected event");
				return event.message;
			},
		);
		started();
		void wait.then(() => {
			stream.push({ type: "done", reason: "stop", message: assistant() });
			stream.end(assistant());
		});
		return stream;
	};
	const agent = new Agent({ sessionId: "session-cancel", initialState: { model }, streamFn });
	const running = agent.prompt(message("go"));
	await entered;
	const pausing = agent.requestPause();
	const rejected = assert.rejects(pausing, /superseded by abort/);
	agent.abort();
	release();
	await Promise.all([running, rejected]);
	assert.equal(agent.isPaused, false);
	assert.throws(() => agent.exportPauseState());
});

test("pause inside completed next-turn preparation resumes without preparing twice", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	let calls = 0;
	let prepares = 0;
	const modelIds: string[] = [];
	const tool = {
		name: "effect",
		label: "Effect",
		description: "fixture",
		parameters: Type.Object({}),
		async execute() {
			return { content: [{ type: "text" as const, text: "ok" }], details: null };
		},
	};
	const options = {
		sessionId: "prepare-inside",
		initialState: { model, tools: [tool] },
		prepareNextTurn: async () => {
			prepares++;
			if (prepares === 1) {
				entered();
				await gate;
			}
			return { messages: [message("prepared-context")], model: { ...model, id: "prepared" } };
		},
		streamFn: (activeModel: Model<any>) => {
			modelIds.push(activeModel.id);
			return new MockStream(
				++calls === 1
					? {
							...assistant(),
							stopReason: "toolUse",
							content: [{ type: "toolCall", id: "one", name: "effect", arguments: {} }],
						}
					: assistant(),
			);
		},
	};
	const first = new Agent(options);
	const running = first.prompt(message("original"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const restored = new Agent(options);
	restored.restorePauseState(first.exportPauseState(), "prepare-inside");
	await restored.resumePaused();
	assert.equal(prepares, 1);
	assert.equal(calls, 2);
	assert.deepEqual(modelIds, ["synthetic", "prepared"]);
	assert.equal(restored.state.messages.filter((item) => item.role === "user").length, 2);
});

test("a prepared steering request resumes even when its trigger was already consumed", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	let calls = 0;
	let preparations = 0;
	const options = {
		sessionId: "prepared-steering",
		initialState: { model },
		prepareRequest: async () => {
			if (++preparations === 2) {
				entered();
				await gate;
			}
			return undefined;
		},
		streamFn: () => {
			calls++;
			return new MockStream(assistant());
		},
	};
	const first = new Agent(options);
	first.subscribe((event) => {
		if (event.type === "turn_end" && calls === 1) first.steer(message("steered"));
	});
	const running = first.prompt(message("original"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const restored = new Agent(options);
	restored.restorePauseState(first.exportPauseState(), "prepared-steering");
	await restored.resumePaused();
	assert.equal(calls, 2);
	assert.equal(preparations, 2);
	assert.equal(restored.state.messages.filter((item) => item.role === "user").length, 2);
});

test("pause after a plain response still runs finishTurn and its continuation once", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	let calls = 0;
	let finishes = 0;
	const options = {
		sessionId: "plain-finish",
		initialState: { model },
		finishTurn: () => ({ action: ++finishes === 1 ? ("continue" as const) : ("end" as const) }),
		streamFn: async () => {
			if (++calls === 1) {
				entered();
				await gate;
			}
			return new MockStream(assistant());
		},
	};
	const first = new Agent(options);
	const running = first.prompt(message("original"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const restored = new Agent(options);
	restored.restorePauseState(first.exportPauseState(), "plain-finish");
	await restored.resumePaused();
	assert.equal(finishes, 2);
	assert.equal(calls, 2);
});

test("pause while finishTurn settles retains its completed decision", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	let calls = 0;
	let finishes = 0;
	const options = {
		sessionId: "finish-inside",
		initialState: { model },
		finishTurn: async () => {
			finishes++;
			if (finishes === 1) {
				entered();
				await gate;
				return { action: "continue" as const };
			}
			return { action: "end" as const };
		},
		streamFn: () => {
			calls++;
			return new MockStream(assistant());
		},
	};
	const first = new Agent(options);
	const running = first.prompt(message("original"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const restored = new Agent(options);
	restored.restorePauseState(first.exportPauseState(), "finish-inside");
	await restored.resumePaused();
	assert.equal(finishes, 2);
	assert.equal(calls, 2);
});

test("an error response settled during pause does not repeat its finish callback", async () => {
	let entered!: () => void;
	let release!: () => void;
	const started = new Promise<void>((resolve) => {
		entered = resolve;
	});
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	let calls = 0;
	let finishes = 0;
	const options = {
		sessionId: "error-finish",
		initialState: { model },
		finishTurn: () => {
			finishes++;
		},
		streamFn: async () => {
			calls++;
			entered();
			await gate;
			return new MockStream({ ...assistant(), stopReason: "error", errorMessage: "fixture error" });
		},
	};
	const first = new Agent(options);
	const running = first.prompt(message("original"));
	await started;
	const pausing = first.requestPause();
	release();
	await Promise.all([running, pausing]);
	const restored = new Agent(options);
	restored.restorePauseState(first.exportPauseState(), "error-finish");
	await restored.resumePaused();
	assert.equal(finishes, 1);
	assert.equal(calls, 1);
});
