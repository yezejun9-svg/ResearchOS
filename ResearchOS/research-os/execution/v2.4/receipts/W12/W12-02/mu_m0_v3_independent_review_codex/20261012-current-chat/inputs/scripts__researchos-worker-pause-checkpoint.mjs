import { createHash } from "node:crypto";

/** Isolated protocol fixture. Its send callback is a synthetic host, not durable storage. */
export class PauseCheckpointProtocol {
	constructor(binding, send) {
		if (!binding || !binding.runId || !binding.sessionId || !Number.isSafeInteger(binding.leaseEpoch) ||
			binding.leaseEpoch < 0 || !/^[a-f0-9]{64}$/.test(binding.inputHash) || !binding.processId ||
			typeof send !== "function") throw new Error("Invalid pause binding");
		this.binding = structuredClone(binding);
		this.send = send;
		this.sequence = 0;
		this.pending = null;
		this.cancelled = false;
	}

	/** Exercise the real candidate AgentSession without installing a production worker. */
	async requestPauseFromSession(session, safety) {
		if (session?.sessionManager?.getSessionId() !== this.binding.sessionId) {
			throw new Error("Pause session binding mismatch");
		}
		await session.requestPause();
		const checkpoint = session.exportPauseCheckpoint({
			leaseEpoch: this.binding.leaseEpoch,
			inputHash: this.binding.inputHash,
		});
		return this.requestPause(checkpoint, safety);
	}

	requestPause(checkpoint, safety) {
		if (this.cancelled || this.pending) throw new Error("Pause unavailable");
		if (!safety?.modelStopped || !safety?.toolsStopped || !safety?.streamStopped ||
			safety?.unknownEffects || safety?.unknownCost) throw new Error("Pause safety evidence incomplete");
		const bytes = JSON.stringify(checkpoint);
		if (Buffer.byteLength(bytes, "utf8") > 12 * 1024 * 1024) throw new Error("Checkpoint exceeds 12 MiB");
		const hash = createHash("sha256").update(bytes).digest("hex");
		const sequence = ++this.sequence;
		const frame = { type: "checkpoint", binding: this.binding, sequence, hash, bytes };
		this.pending = { sequence, hash, bytes, safety: structuredClone(safety) };
		this.send(frame);
		return frame;
	}

	ack(ack, currentSafety) {
		const pending = this.pending;
		if (this.cancelled || !pending || ack?.type !== "checkpoint.ack" ||
			ack.sequence !== pending.sequence || ack.hash !== pending.hash ||
			JSON.stringify(ack.binding) !== JSON.stringify(this.binding) || ack.persisted !== true ||
			!currentSafety?.modelStopped || !currentSafety?.toolsStopped || !currentSafety?.streamStopped ||
			currentSafety?.unknownEffects || currentSafety?.unknownCost) {
			return false;
		}
		this.pending = null;
		this.send({ type: "turn.paused", binding: this.binding, sequence: pending.sequence, checkpointHash: pending.hash });
		return true;
	}

	cancel() {
		this.cancelled = true;
		this.pending = null;
	}
}
