import { BACKGROUND_CONTEXT } from "../context/index.js";
import { applyImmutable, isBase, track } from "../delta/index.js";
import { JsonRevisionValidator } from "../delta/revision-validator.js";
import { registerReplicatedStateInternals } from "./state-internals.js";
/** Maintains local publication order independently of how revisions are produced. */
class ReplicatedStatePublisher {
    #listeners = new Map();
    #sourceListeners = new Set();
    #publications = [];
    #value;
    #sequence = 0;
    #delivering = false;
    constructor(initial) {
        this.#value = initial;
    }
    get value() {
        return this.#value;
    }
    snapshot() {
        return { value: this.#value, sequence: this.#sequence };
    }
    subscribe(listener) {
        const { value, sequence } = this.snapshot();
        this.#listeners.set(listener, sequence);
        try {
            listener(value, serviceDeliveryContext(), { kind: "hydrate", sequence });
        }
        catch (error) {
            this.#listeners.delete(listener);
            throw error;
        }
        return () => this.#listeners.delete(listener);
    }
    subscribeSource(listener) {
        this.#sourceListeners.add(listener);
        return () => this.#sourceListeners.delete(listener);
    }
    /** Publish an already-prepared immutable revision and return isolated listener failures. */
    publish(value, ops, context) {
        this.#value = value;
        this.#sequence += 1;
        this.#publications.push({ value, ops, sequence: this.#sequence, context });
        if (this.#delivering)
            return [];
        this.#delivering = true;
        const errors = [];
        try {
            for (let publication = this.#publications.shift(); publication !== undefined; publication = this.#publications.shift()) {
                for (const listener of [...this.#sourceListeners]) {
                    try {
                        listener(publication.ops, publication.sequence, publication.context);
                    }
                    catch (error) {
                        errors.push(error);
                    }
                }
                const delivery = { kind: "update", sequence: publication.sequence };
                for (const [listener, hydratedSequence] of [...this.#listeners]) {
                    if (publication.sequence <= hydratedSequence)
                        continue;
                    try {
                        listener(publication.value, publication.context, delivery);
                    }
                    catch (error) {
                        errors.push(error);
                    }
                }
            }
        }
        finally {
            this.#delivering = false;
        }
        return errors;
    }
}
export class MutableReplicatedStateImpl {
    #tracker;
    #publisher;
    #changing = false;
    constructor(initial) {
        this.#tracker = track(initial);
        this.#publisher = new ReplicatedStatePublisher(this.#tracker.value);
        registerReplicatedStateInternals(this, {
            snapshot: () => this.#publisher.snapshot(),
            subscribe: (listener) => this.#publisher.subscribeSource(listener),
        });
    }
    get value() {
        return this.#tracker.value;
    }
    change(context, mutate) {
        if (this.#changing)
            throw new Error("Replicated state cannot be changed reentrantly from a change callback");
        this.#changing = true;
        let prepared;
        try {
            const change = this.#tracker.beginChange();
            try {
                const outcome = mutate(change.state);
                if (isPromiseLike(outcome)) {
                    void Promise.resolve(outcome).catch(() => undefined);
                    throw new TypeError("Replicated state change callbacks must be synchronous");
                }
                prepared = change.prepare();
            }
            catch (error) {
                change.abort();
                throw error;
            }
        }
        finally {
            this.#changing = false;
        }
        this.#tracker.adopt(prepared);
        if (prepared.ops.length === 0)
            return;
        throwCollectedErrors(this.#publisher.publish(prepared.value, prepared.ops, context), "Replicated state listeners failed");
    }
    replace(context, value) {
        if (this.#changing)
            throw new Error("Replicated state cannot be replaced from a change callback");
        const prepared = this.#tracker.prepareReplace(value);
        this.#tracker.adopt(prepared);
        if (prepared.ops.length === 0)
            return;
        throwCollectedErrors(this.#publisher.publish(prepared.value, prepared.ops, context), "Replicated state listeners failed");
    }
    subscribe(listener) {
        return this.#publisher.subscribe(listener);
    }
}
class AttachedReplicatedStateImpl {
    #publisher;
    #attachment;
    #reportError;
    #cursor;
    #disposed = false;
    constructor(attachment, options) {
        const { snapshot } = attachment;
        assertCursor(snapshot.cursor, "snapshot");
        this.#attachment = attachment;
        this.#cursor = snapshot.cursor;
        this.#publisher = new ReplicatedStatePublisher(snapshot.value);
        this.#reportError = options.onError ?? reportErrorAsync;
        registerReplicatedStateInternals(this, {
            snapshot: () => this.#publisher.snapshot(),
            subscribe: (listener) => this.#publisher.subscribeSource(listener),
        });
    }
    get value() {
        return this.#publisher.value;
    }
    subscribe(listener) {
        return this.#publisher.subscribe(listener);
    }
    activate() {
        this.#attachment.activate((frame) => this.#receive(frame));
    }
    dispose() {
        if (this.#disposed)
            return;
        this.#disposed = true;
        this.#attachment.dispose();
    }
    #receive(frame) {
        if (this.#disposed)
            return;
        try {
            assertCursor(frame.cursor, "frame");
            const expected = this.#cursor + 1;
            if (frame.cursor !== expected) {
                throw new Error(`Replicated state source cursor has a gap: expected ${expected}, received ${frame.cursor}`);
            }
            this.#cursor = frame.cursor;
            const errors = this.#publisher.publish(frame.value, frame.ops, frame.context);
            if (errors.length === 1)
                this.#report(errors[0]);
            else if (errors.length > 1)
                this.#report(new AggregateError(errors, "Replicated state listeners failed"));
        }
        catch (error) {
            this.#fail(toError(error));
        }
    }
    #fail(error) {
        if (this.#disposed)
            return;
        this.#disposed = true;
        try {
            this.#attachment.dispose();
        }
        catch (disposeError) {
            this.#report(new AggregateError([error, disposeError], "Replicated state source contract failed"));
            return;
        }
        this.#report(error);
    }
    #report(error) {
        try {
            this.#reportError(toError(error));
        }
        catch (reportError) {
            reportErrorAsync(toError(reportError));
        }
    }
}
/** Attach a publication-only replicated state to one authoritative immutable source stream. */
export function attachReplicatedStateSource(source, options = {}) {
    const attachment = source.attach();
    try {
        const state = new AttachedReplicatedStateImpl(attachment, options);
        state.activate();
        return state;
    }
    catch (error) {
        try {
            attachment.dispose();
        }
        catch (disposeError) {
            throw new AggregateError([error, disposeError], "Failed to attach replicated state source");
        }
        throw error;
    }
}
/** A cold read-only state used by service consumers until a complete snapshot arrives. */
export class ReplicatedStateReplica {
    #listeners = new Set();
    #reportError;
    #validator = new JsonRevisionValidator();
    #value;
    #sequence;
    constructor(reportError) {
        this.#reportError = reportError;
    }
    get value() {
        return this.#value;
    }
    subscribe(listener) {
        this.#listeners.add(listener);
        if (this.#value !== undefined) {
            this.#deliver(listener, this.#value, serviceDeliveryContext(), {
                kind: "hydrate",
                sequence: this.#sequence,
            });
        }
        return () => this.#listeners.delete(listener);
    }
    hydrate(sequence, ops, context) {
        let next;
        try {
            if (!isBase(ops))
                throw new Error("Replicated state snapshot is not a base operation batch");
            next = this.#validator.validate(applyImmutable(undefined, ops));
        }
        catch (error) {
            this.clear();
            throw error;
        }
        this.#sequence = sequence;
        this.#value = next;
        this.#deliverAll(context, { kind: "hydrate", sequence });
    }
    update(sequence, ops, context) {
        if (this.#sequence === undefined || this.#value === undefined) {
            throw new Error("Replicated state received an update before hydration");
        }
        if (sequence !== this.#sequence + 1) {
            this.clear();
            throw new Error("Replicated state update sequence has a gap");
        }
        let next;
        try {
            next = this.#validator.validate(applyImmutable(this.#value, ops));
        }
        catch (error) {
            this.clear();
            throw error;
        }
        this.#sequence = sequence;
        this.#value = next;
        this.#deliverAll(context, { kind: "update", sequence });
    }
    clear() {
        this.#value = undefined;
        this.#sequence = undefined;
    }
    #deliverAll(context, delivery) {
        if (this.#value === undefined)
            return;
        for (const listener of this.#listeners)
            this.#deliver(listener, this.#value, context, delivery);
    }
    #deliver(listener, value, context, delivery) {
        try {
            listener(value, context, delivery);
        }
        catch (error) {
            this.#reportError(toError(error));
        }
    }
}
/** @internal Context for synthetic service deliveries without a caller. */
export function serviceDeliveryContext() {
    // TODO: Add delivery-scoped cancellation or metadata if deliveries gain an owned lifecycle.
    return BACKGROUND_CONTEXT;
}
function assertCursor(cursor, kind) {
    if (!Number.isSafeInteger(cursor))
        throw new TypeError(`Replicated state source ${kind} cursor must be a safe integer`);
}
function isPromiseLike(value) {
    return (((typeof value === "object" && value !== null) || typeof value === "function") &&
        typeof value.then === "function");
}
function throwCollectedErrors(errors, message) {
    if (errors.length === 1)
        throw errors[0];
    if (errors.length > 1)
        throw new AggregateError(errors, message);
}
function reportErrorAsync(error) {
    queueMicrotask(() => {
        throw error;
    });
}
function toError(error) {
    return error instanceof Error ? error : new Error(String(error));
}
//# sourceMappingURL=state.js.map