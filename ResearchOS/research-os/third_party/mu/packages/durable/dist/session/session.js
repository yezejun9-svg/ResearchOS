import { awaitWithContext, withoutAbortSignal } from "@earendil-works/chord/context";
import { track } from "@earendil-works/chord/delta";
import { checkRecordScope, checkRecordVersion, materializeDocument, resolveAddress, } from "../documents.js";
import { Transaction } from "./transaction.js";
/** Open a Session kernel over one storage backend. */
export function createSession(storage) {
    return new SessionKernel(storage);
}
/**
 * Session kernel: one mutation line, the loaded document tracker cache, and committed publication.
 *
 * Only committed state is observable. Every commit callback, preparation, Storage settlement, adoption, and
 * publication enqueue runs while the line is held; listeners run later.
 */
export class SessionKernel {
    #storage;
    #documents = new Map();
    #listeners = new Set();
    #host;
    #tail = Promise.resolve();
    #closing;
    #poison;
    constructor(storage) {
        this.#storage = storage;
        this.#host = {
            storage,
            cached: (id) => this.#documents.get(id),
            load: (definition, addressId, address, context) => this.#load(definition, addressId, address, context),
            install: (document) => {
                this.#documents.set(document.addressId, document);
            },
            evict: (id, recordId) => {
                if (this.#documents.get(id)?.record.id === recordId)
                    this.#documents.delete(id);
            },
        };
    }
    commit(change, context) {
        try {
            this.#assertUsable();
        }
        catch (error) {
            return Promise.reject(error);
        }
        return this.#enqueue(() => this.#runCommit(change, context));
    }
    async snapshot(token, ...args) {
        this.#assertUsable();
        const definition = token.definition;
        const resolved = resolveAddress(definition, args);
        const context = args[resolved.nextArgument];
        const loaded = this.#documents.get(resolved.id) ??
            (await this.#enqueue(async () => {
                this.#assertHealthy();
                return this.#load(definition, resolved.id, resolved.address, context);
            }));
        if (loaded === undefined)
            return undefined;
        checkRecordScope(definition, loaded.record);
        checkRecordVersion(definition, loaded.record, loaded.storedVersion);
        return loaded.tracker.value;
    }
    async snapshotAsOf(token, ...args) {
        this.#assertUsable();
        const definition = token.definition;
        const resolved = resolveAddress(definition, args);
        if (resolved.address.scope.kind !== "conversation") {
            throw new TypeError("Session.snapshotAsOf() requires a conversation document");
        }
        const conversationId = resolved.address.scope.conversationId;
        const at = args[resolved.nextArgument];
        const context = args[resolved.nextArgument + 1];
        return this.#enqueue(async () => {
            this.#assertHealthy();
            const storedEntry = await this.#storage.entry(conversationId, at, context);
            if (storedEntry === undefined) {
                throw new Error(`Entry ${at} is not visible from conversation ${conversationId}`);
            }
            const address = {
                ...resolved.address,
                scope: { kind: "conversation", conversationId: storedEntry.entry.conversationId },
            };
            const record = await this.#storage.findDocument(address, storedEntry.commitSeq, context);
            if (record === undefined)
                return undefined;
            const stored = await this.#storage.document(record.id, storedEntry.commitSeq, context);
            if (stored === undefined) {
                throw new Error(`Historical document ${record.id} (${record.kind}) cannot be read`);
            }
            return materializeDocument(definition, stored);
        });
    }
    close(context) {
        if (this.#closing === undefined) {
            const cleanup = withoutAbortSignal(context);
            this.#closing = this.#enqueue(async () => {
                this.#documents.clear();
                await this.#storage.close(cleanup);
            });
        }
        return awaitWithContext(this.#closing, context);
    }
    /** Register an internal commit listener. Callbacks run later in commit order and must not throw. */
    subscribeCommits(listener) {
        this.#listeners.add(listener);
        return () => {
            this.#listeners.delete(listener);
        };
    }
    /** Drop every loaded tracker on the mutation line; later access cold-loads from Storage. */
    unloadDocuments() {
        return this.#enqueue(async () => {
            this.#documents.clear();
        });
    }
    async #runCommit(change, context) {
        this.#assertHealthy();
        context.abortSignal?.throwIfAborted();
        const tx = new Transaction(this.#host, context);
        let result;
        try {
            result = await change(tx);
        }
        catch (error) {
            await tx.settleFailure();
            throw error;
        }
        const writes = await tx.settleSuccess();
        if (writes.length === 0) {
            tx.discard();
            return result;
        }
        let seq;
        try {
            // Once admitted, caller cancellation does not interrupt Storage settlement.
            seq = await this.#storage.commit(writes, withoutAbortSignal(context));
        }
        catch (error) {
            tx.discard();
            this.#poison = { error };
            throw error;
        }
        let documents;
        try {
            documents = tx.adopt(seq);
        }
        catch (error) {
            // Storage already committed; a failed adoption leaves memory behind durable state.
            this.#poison = { error };
            throw error;
        }
        this.#publish(seq, writes, documents, context);
        return result;
    }
    #publish(seq, writes, documents, context) {
        if (this.#listeners.size === 0)
            return;
        const changes = [];
        for (const write of writes) {
            switch (write.type) {
                case "conversation":
                case "entry":
                case "task":
                case "submission":
                    changes.push(write);
            }
        }
        for (const document of documents)
            changes.push(document);
        const publication = { seq, changes };
        const listeners = [...this.#listeners];
        queueMicrotask(() => {
            for (const listener of listeners)
                listener(publication, context);
        });
    }
    async #load(definition, addressId, address, context) {
        const cached = this.#documents.get(addressId);
        if (cached !== undefined)
            return cached;
        const record = await this.#storage.findDocument(address, "current", context);
        if (record === undefined)
            return undefined;
        const stored = await this.#storage.document(record.id, "current", context);
        if (stored === undefined)
            throw new Error(`Current document ${record.id} (${record.kind}) cannot be read`);
        const value = materializeDocument(definition, stored);
        const loaded = {
            addressId,
            record: stored.record,
            storedVersion: stored.version,
            tracker: track(value),
        };
        this.#documents.set(addressId, loaded);
        return loaded;
    }
    #enqueue(job) {
        const run = this.#tail.then(job);
        this.#tail = run.then(() => undefined, () => undefined);
        return run;
    }
    #assertUsable() {
        if (this.#closing !== undefined)
            throw new Error("Session is closed");
        this.#assertHealthy();
    }
    #assertHealthy() {
        if (this.#poison !== undefined) {
            throw new Error("Session is poisoned by a failed commit after storage admission; reopen it", {
                cause: this.#poison.error,
            });
        }
    }
}
//# sourceMappingURL=session.js.map