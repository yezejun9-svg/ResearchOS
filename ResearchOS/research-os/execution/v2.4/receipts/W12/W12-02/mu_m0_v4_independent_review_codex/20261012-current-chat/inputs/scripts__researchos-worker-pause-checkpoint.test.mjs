import assert from "node:assert/strict";
import { test } from "node:test";
import { PauseCheckpointProtocol } from "./researchos-worker-pause-checkpoint.mjs";

const binding = { runId: "run-1", sessionId: "session-1", leaseEpoch: 7, inputHash: "a".repeat(64), processId: "fixture-42" };
const safe = { modelStopped: true, toolsStopped: true, streamStopped: true, unknownEffects: false, unknownCost: false };

test("checkpoint is emitted before paused and only matching persisted ACK permits paused", () => {
	const frames = [];
	const protocol = new PauseCheckpointProtocol(binding, (frame) => frames.push(frame));
	const frame = protocol.requestPause({ session: "snapshot" }, safe);
	assert.equal(frames.length, 1);
	assert.equal(frames[0].type, "checkpoint");
	for (const wrong of [
		{ ...binding, leaseEpoch: 8 },
		{ ...binding, runId: "run-2" },
		{ ...binding, inputHash: "b".repeat(64) },
	]) {
		assert.equal(protocol.ack({ type: "checkpoint.ack", binding: wrong, sequence: frame.sequence, hash: frame.hash, persisted: true }, safe), false);
	}
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence + 1, hash: frame.hash, persisted: true }, safe), false);
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: false }, safe), false);
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: true },
		{ ...safe, unknownEffects: true }), false);
	assert.equal(frames.length, 1);
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: true }, safe), true);
	assert.equal(frames[1].type, "turn.paused");
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: true }, safe), false);
});

test("UNKNOWN effects, unknown cost and CANCEL block pause", () => {
	for (const condition of [{ unknownEffects: true }, { unknownCost: true }, { toolsStopped: false }, { streamStopped: false }]) {
		const protocol = new PauseCheckpointProtocol(binding, () => assert.fail("no frame expected"));
		assert.throws(() => protocol.requestPause({}, { ...safe, ...condition }));
	}
	const frames = [];
	const protocol = new PauseCheckpointProtocol(binding, (frame) => frames.push(frame));
	const frame = protocol.requestPause({}, safe);
	protocol.cancel();
	assert.equal(protocol.ack({ type: "checkpoint.ack", binding, sequence: frame.sequence, hash: frame.hash, persisted: true }, safe), false);
	assert.equal(frames.length, 1);
});
