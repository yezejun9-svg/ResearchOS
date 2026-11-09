import { apply } from "@earendil-works/chord/delta";
import { applySqliteMigrations } from "./migrations.js";
const parseJson = (value) => JSON.parse(value);
const encodeJson = (value) => JSON.stringify(value);
// Some SQLite bindings replace lone UTF-16 surrogates. JSON encoding keeps indexed identities lossless.
const encodeIndexedString = (value) => JSON.stringify(value);
const getRow = (statement, ...params) => statement.get(...params);
const allRows = (statement, ...params) => statement.all(...params);
const cursorId = (cursor) => cursor?.after;
const page = (values, limit) => {
    const items = values.slice(0, limit);
    if (values.length <= limit)
        return { items };
    return { items, next: { after: items.at(-1).id } };
};
const scopeColumns = (scope) => {
    switch (scope.kind) {
        case "session":
            return { scopeKind: "session", ownerId: 0 };
        case "conversation":
            return { scopeKind: "conversation", ownerId: scope.conversationId };
        case "task":
            return { scopeKind: "task", ownerId: scope.taskId };
    }
};
const addressParts = (address) => {
    const scope = scopeColumns(address.scope);
    return {
        kind: encodeIndexedString(address.kind),
        ...scope,
        family: address.key === undefined ? 0 : 1,
        keyValue: encodeIndexedString(address.key ?? ""),
    };
};
const addressKey = (address) => {
    const parts = addressParts(address);
    return JSON.stringify([parts.kind, parts.scopeKind, parts.ownerId, parts.family, parts.keyValue]);
};
const isAliveAt = (record, at) => {
    if (at === "current")
        return record.retiredAt === undefined;
    return record.createdAt <= at && (record.retiredAt === undefined || at < record.retiredAt);
};
const isCurrentOnly = (record) => record.scope.kind !== "conversation" || record.history === "latest";
const writeId = (write) => {
    switch (write.type) {
        case "conversation":
        case "entry":
        case "task":
        case "submission":
            return write.value.id;
        case "document.create":
            return write.record.id;
        case "document.change":
        case "document.retire":
            return undefined;
    }
};
class StatementCachingDatabase {
    database;
    statements = new Map();
    constructor(database) {
        this.database = database;
    }
    exec(sql) {
        this.database.exec(sql);
    }
    prepare(sql) {
        let statement = this.statements.get(sql);
        if (statement === undefined) {
            statement = this.database.prepare(sql);
            this.statements.set(sql, statement);
        }
        return statement;
    }
    transaction(callback) {
        return this.database.transaction(callback);
    }
    close() {
        this.statements.clear();
        return this.database.close();
    }
}
/** Portable SQLite implementation of the Pico storage contract. */
export class SqliteStorage {
    db;
    nextId;
    closed = false;
    constructor(db, nextId) {
        this.db = new StatementCachingDatabase(db);
        this.nextId = nextId;
    }
    /** Initialize storage over an owned SQLite database facade. */
    static async open(db) {
        try {
            await applySqliteMigrations(db);
            const metadata = getRow(db.prepare("SELECT next_id, next_seq FROM durable_metadata WHERE singleton = 1"));
            if (metadata === undefined)
                throw new Error("Durable SQLite metadata is missing");
            return new SqliteStorage(db, Number(metadata.next_id));
        }
        catch (error) {
            try {
                await db.close();
            }
            catch {
                // Preserve the initialization failure.
            }
            throw error;
        }
    }
    async commit(writes, _context) {
        this.assertOpen();
        const documentActions = this.prepareDocumentActions(writes);
        const candidateNextId = this.candidateNextId(writes);
        const seq = await this.db.transaction(() => {
            const metadata = getRow(this.db.prepare("SELECT next_id, next_seq FROM durable_metadata WHERE singleton = 1"));
            if (metadata === undefined)
                throw new Error("Durable SQLite metadata is missing");
            const committedSeq = metadata.next_seq;
            this.checkGlobalIds(writes);
            this.checkDocumentActions(documentActions);
            for (const write of writes)
                this.applyTableWrite(write, committedSeq);
            this.applyDocumentActions(documentActions, committedSeq);
            this.db
                .prepare("UPDATE durable_metadata SET next_id = ?, next_seq = ? WHERE singleton = 1")
                .run(String(Math.max(Number(metadata.next_id), candidateNextId)), committedSeq + 1);
            return committedSeq;
        });
        this.nextId = Math.max(this.nextId, candidateNextId);
        return seq;
    }
    async mintId() {
        this.assertOpen();
        if (!Number.isSafeInteger(this.nextId))
            throw new Error("ID space is exhausted");
        return this.nextId++;
    }
    async conversation(id, _context) {
        this.assertOpen();
        const row = getRow(this.db.prepare("SELECT record FROM conversations WHERE id = ?"), id);
        return row === undefined ? undefined : parseJson(row.record);
    }
    async scanConversations(limit, cursor, _context) {
        this.assertOpen();
        const after = cursorId(cursor) ?? -1;
        const rows = allRows(this.db.prepare("SELECT record FROM conversations WHERE id > ? ORDER BY id LIMIT ?"), after, limit + 1);
        return page(rows.map((row) => parseJson(row.record)), limit);
    }
    async entry(idOrConversationId, idOrContext, context) {
        this.assertOpen();
        let conversation = context === undefined ? undefined : this.readConversation(idOrConversationId);
        if (context !== undefined && conversation === undefined) {
            throw new Error(`Unknown conversation: ${idOrConversationId}`);
        }
        const id = context === undefined ? idOrConversationId : idOrContext;
        const row = getRow(this.db.prepare("SELECT record, commit_seq FROM entries WHERE id = ?"), id);
        if (row === undefined)
            return undefined;
        const entry = parseJson(row.record);
        if (conversation !== undefined) {
            let upperEntryId = Number.POSITIVE_INFINITY;
            while (conversation.id !== entry.conversationId) {
                if (conversation.parent === undefined)
                    return undefined;
                upperEntryId = Math.min(upperEntryId, conversation.parent.at);
                conversation = this.readConversation(conversation.parent.conversationId);
            }
            if (entry.id > upperEntryId)
                return undefined;
        }
        return { entry, commitSeq: row.commit_seq };
    }
    async findLatestHeadMarker(conversationId, atOrBeforeEntryId, _context) {
        this.assertOpen();
        let conversation = this.readConversation(conversationId);
        if (conversation === undefined)
            throw new Error(`Unknown conversation: ${conversationId}`);
        let upper = atOrBeforeEntryId;
        while (true) {
            const row = upper === undefined
                ? getRow(this.db.prepare("SELECT record FROM entries WHERE conversation_id = ? AND head IS NOT NULL ORDER BY id DESC LIMIT 1"), conversation.id)
                : getRow(this.db.prepare("SELECT record FROM entries WHERE conversation_id = ? AND head IS NOT NULL AND id <= ? ORDER BY id DESC LIMIT 1"), conversation.id, upper);
            if (row !== undefined)
                return parseJson(row.record);
            if (conversation.parent === undefined)
                return undefined;
            upper = upper === undefined ? conversation.parent.at : Math.min(upper, conversation.parent.at);
            conversation = this.readConversation(conversation.parent.conversationId);
        }
    }
    async scanEntries(query, limit, cursor, _context) {
        this.assertOpen();
        let conversation = this.readConversation(query.conversationId);
        if (conversation === undefined)
            throw new Error(`Unknown conversation: ${query.conversationId}`);
        const after = cursorId(cursor);
        let upper = query.maxEntryId;
        if (after !== undefined)
            upper = Math.min(upper ?? Number.MAX_SAFE_INTEGER, after - 1);
        const values = [];
        while (true) {
            const clauses = ["conversation_id = ?"];
            const params = [conversation.id];
            if (query.minEntryId !== undefined) {
                clauses.push("id >= ?");
                params.push(query.minEntryId);
            }
            if (upper !== undefined) {
                clauses.push("id <= ?");
                params.push(upper);
            }
            params.push(limit + 1 - values.length);
            const rows = allRows(this.db.prepare(`SELECT record FROM entries WHERE ${clauses.join(" AND ")} ORDER BY id DESC LIMIT ?`), ...params);
            values.push(...rows.map((row) => parseJson(row.record)));
            if (values.length > limit || conversation.parent === undefined)
                break;
            upper = upper === undefined ? conversation.parent.at : Math.min(upper, conversation.parent.at);
            if (query.minEntryId !== undefined && upper < query.minEntryId)
                break;
            conversation = this.readConversation(conversation.parent.conversationId);
        }
        return page(values, limit);
    }
    async task(id, _context) {
        this.assertOpen();
        const row = getRow(this.db.prepare("SELECT record FROM tasks WHERE id = ?"), id);
        return row === undefined ? undefined : parseJson(row.record);
    }
    async scanTasks(query, limit, cursor, _context) {
        this.assertOpen();
        const clauses = ["id > ?"];
        const params = [cursorId(cursor) ?? -1];
        if (query.conversationId !== undefined) {
            clauses.push("conversation_id = ?");
            params.push(query.conversationId);
        }
        if (query.kind !== undefined) {
            clauses.push("kind = ?");
            params.push(encodeIndexedString(query.kind));
        }
        if (query.status !== undefined) {
            clauses.push("status = ?");
            params.push(query.status);
        }
        if (query.abortRequested !== undefined) {
            clauses.push("abort_requested = ?");
            params.push(query.abortRequested ? 1 : 0);
        }
        if (query.background !== undefined) {
            clauses.push("background = ?");
            params.push(query.background ? 1 : 0);
        }
        params.push(limit + 1);
        const rows = allRows(this.db.prepare(`SELECT record FROM tasks WHERE ${clauses.join(" AND ")} ORDER BY id LIMIT ?`), ...params);
        return page(rows.map((row) => parseJson(row.record)), limit);
    }
    async submission(id, _context) {
        this.assertOpen();
        const row = getRow(this.db.prepare("SELECT record FROM submissions WHERE id = ?"), id);
        return row === undefined ? undefined : parseJson(row.record);
    }
    async submissionByRequest(conversationId, requestId, _context) {
        this.assertOpen();
        const row = getRow(this.db.prepare("SELECT record FROM submissions WHERE conversation_id = ? AND request_id = ?"), conversationId, encodeIndexedString(requestId));
        return row === undefined ? undefined : parseJson(row.record);
    }
    async findDocument(address, at, _context) {
        this.assertOpen();
        const parts = addressParts(address);
        const statement = at === "current"
            ? this.db.prepare(`SELECT record FROM documents
					WHERE kind = ? AND scope_kind = ? AND owner_id = ? AND family = ? AND key_value = ?
					AND retired_at IS NULL ORDER BY created_at DESC LIMIT 1`)
            : this.db.prepare(`SELECT record FROM documents
					WHERE kind = ? AND scope_kind = ? AND owner_id = ? AND family = ? AND key_value = ?
					AND created_at <= ? AND (retired_at IS NULL OR retired_at > ?)
					ORDER BY created_at DESC LIMIT 1`);
        const params = [parts.kind, parts.scopeKind, parts.ownerId, parts.family, parts.keyValue];
        if (at !== "current")
            params.push(at, at);
        const row = getRow(statement, ...params);
        return row === undefined ? undefined : parseJson(row.record);
    }
    async document(id, at, _context) {
        this.assertOpen();
        const row = getRow(this.db.prepare("SELECT record FROM documents WHERE id = ?"), id);
        if (row === undefined)
            return undefined;
        const record = parseJson(row.record);
        if (at !== "current" && isCurrentOnly(record)) {
            throw new Error(`Document ${id} does not retain historical content`);
        }
        if (!isAliveAt(record, at))
            return undefined;
        const upper = at === "current" ? Number.MAX_SAFE_INTEGER : at;
        const base = getRow(this.db.prepare(`SELECT seq, kind, version, content FROM document_revisions
				WHERE document_id = ? AND kind = 'base' AND seq <= ? ORDER BY seq DESC LIMIT 1`), id, upper);
        if (base === undefined)
            throw new Error(`Document ${id} is missing a required base`);
        let value = parseJson(base.content);
        const tail = allRows(this.db.prepare(`SELECT seq, kind, version, content FROM document_revisions
				WHERE document_id = ? AND seq > ? AND seq <= ? ORDER BY seq`), id, base.seq, upper);
        for (const revision of tail) {
            if (revision.kind !== "delta" || revision.version !== base.version) {
                throw new Error(`Document ${id} crosses a stored version boundary without a base`);
            }
            value = apply(value, parseJson(revision.content));
        }
        return { record, version: base.version, value };
    }
    async scanDocuments(query, limit, cursor, _context) {
        this.assertOpen();
        const scope = scopeColumns(query.scope);
        const clauses = ["scope_kind = ?", "owner_id = ?", "id > ?"];
        const params = [scope.scopeKind, scope.ownerId, cursorId(cursor) ?? -1];
        if (query.kind !== undefined) {
            clauses.push("kind = ?");
            params.push(encodeIndexedString(query.kind));
        }
        if (query.at === "current") {
            clauses.push("retired_at IS NULL");
        }
        else {
            clauses.push("created_at <= ?", "(retired_at IS NULL OR retired_at > ?)");
            params.push(query.at, query.at);
        }
        params.push(limit + 1);
        const rows = allRows(this.db.prepare(`SELECT record FROM documents WHERE ${clauses.join(" AND ")} ORDER BY id LIMIT ?`), ...params);
        return page(rows.map((row) => parseJson(row.record)), limit);
    }
    async close(_context) {
        if (this.closed)
            return;
        this.closed = true;
        await this.db.close();
    }
    readConversation(id) {
        const row = getRow(this.db.prepare("SELECT record FROM conversations WHERE id = ?"), id);
        return row === undefined ? undefined : parseJson(row.record);
    }
    candidateNextId(writes) {
        let nextId = this.nextId;
        for (const write of writes) {
            const id = writeId(write);
            if (id !== undefined)
                nextId = Math.max(nextId, id + 1);
        }
        return nextId;
    }
    checkGlobalIds(writes) {
        const claimed = new Map();
        const lookup = this.db.prepare("SELECT record_type FROM record_ids WHERE id = ?");
        for (const write of writes) {
            if (write.type === "document.change" || write.type === "document.retire")
                continue;
            const table = write.type === "document.create" ? "document" : write.type;
            const id = write.type === "document.create" ? write.record.id : write.value.id;
            const existing = getRow(lookup, id)?.record_type;
            const earlier = claimed.get(id);
            if (table === "conversation" || table === "entry" || table === "document") {
                if (existing !== undefined)
                    throw new Error(`ID ${id} already belongs to ${existing}`);
                if (earlier !== undefined)
                    throw new Error(`ID ${id} is written more than once`);
            }
            else {
                if (existing !== undefined && existing !== table)
                    throw new Error(`ID ${id} already belongs to ${existing}`);
                if (earlier !== undefined && earlier !== table)
                    throw new Error(`ID ${id} is written as two record types`);
            }
            claimed.set(id, table);
        }
    }
    prepareDocumentActions(writes) {
        const actions = new Map();
        for (const write of writes) {
            if (write.type !== "document.create" && write.type !== "document.change" && write.type !== "document.retire") {
                continue;
            }
            const id = write.type === "document.create" ? write.record.id : write.id;
            let action = actions.get(id);
            if (action === undefined) {
                action = { retire: false };
                actions.set(id, action);
            }
            switch (write.type) {
                case "document.create":
                    if (action.create !== undefined || action.content !== undefined) {
                        throw new Error(`Document ${id} has more than one content command`);
                    }
                    action.create = write.record;
                    action.content = write.content;
                    break;
                case "document.change":
                    if (action.content !== undefined)
                        throw new Error(`Document ${id} has more than one content command`);
                    action.content = write.content;
                    break;
                case "document.retire":
                    if (action.retire)
                        throw new Error(`Document ${id} is retired more than once`);
                    action.retire = true;
                    break;
            }
        }
        return actions;
    }
    checkDocumentActions(actions) {
        const liveCounts = new Map();
        for (const [id, action] of actions) {
            const row = getRow(this.db.prepare("SELECT record FROM documents WHERE id = ?"), id);
            const existing = row === undefined ? undefined : parseJson(row.record);
            if (action.create === undefined && existing === undefined)
                throw new Error(`Unknown document: ${id}`);
            if (action.create !== undefined && existing !== undefined)
                throw new Error(`Document ${id} already exists`);
            if (existing?.retiredAt !== undefined)
                throw new Error(`Document ${id} is retired`);
            if (action.content?.kind === "delta") {
                const previous = getRow(this.db.prepare("SELECT version FROM document_revisions WHERE document_id = ? ORDER BY seq DESC LIMIT 1"), id);
                if (previous === undefined)
                    throw new Error(`Document ${id} delta has no base`);
                if (previous.version !== action.content.version) {
                    throw new Error(`Document ${id} version transition requires a base`);
                }
            }
            const record = action.create ?? existing;
            const key = addressKey(record);
            let live = liveCounts.get(key);
            if (live === undefined)
                live = this.currentDocumentId(record) === undefined ? 0 : 1;
            if (action.retire && existing !== undefined)
                live--;
            if (action.create !== undefined && !action.retire)
                live++;
            liveCounts.set(key, live);
        }
        for (const live of liveCounts.values()) {
            if (live > 1)
                throw new Error("Document address already has a current incarnation");
        }
    }
    currentDocumentId(address) {
        const parts = addressParts(address);
        return getRow(this.db.prepare(`SELECT id FROM documents
				WHERE kind = ? AND scope_kind = ? AND owner_id = ? AND family = ? AND key_value = ? AND retired_at IS NULL
				LIMIT 1`), parts.kind, parts.scopeKind, parts.ownerId, parts.family, parts.keyValue)?.id;
    }
    applyTableWrite(write, seq) {
        switch (write.type) {
            case "conversation":
                this.claimId(write.value.id, "conversation");
                this.db
                    .prepare("INSERT INTO conversations (id, record) VALUES (?, ?)")
                    .run(write.value.id, encodeJson(write.value));
                break;
            case "entry":
                this.claimId(write.value.id, "entry");
                this.db
                    .prepare("INSERT INTO entries (id, conversation_id, head, commit_seq, record) VALUES (?, ?, ?, ?, ?)")
                    .run(write.value.id, write.value.conversationId, write.value.head ?? null, seq, encodeJson(write.value));
                break;
            case "task":
                this.claimId(write.value.id, "task");
                this.db
                    .prepare(`INSERT INTO tasks (id, conversation_id, kind, status, abort_requested, background, record)
						VALUES (?, ?, ?, ?, ?, ?, ?)
						ON CONFLICT(id) DO UPDATE SET conversation_id = excluded.conversation_id, kind = excluded.kind,
						status = excluded.status, abort_requested = excluded.abort_requested,
						background = excluded.background, record = excluded.record`)
                    .run(write.value.id, write.value.conversationId, encodeIndexedString(write.value.kind), write.value.state.status, write.value.abortRequested ? 1 : 0, write.value.background ? 1 : 0, encodeJson(write.value));
                break;
            case "submission":
                this.claimId(write.value.id, "submission");
                this.db
                    .prepare(`INSERT INTO submissions (id, conversation_id, request_id, record) VALUES (?, ?, ?, ?)
						ON CONFLICT(id) DO UPDATE SET conversation_id = excluded.conversation_id,
						request_id = excluded.request_id, record = excluded.record`)
                    .run(write.value.id, write.value.conversationId, write.value.requestId === undefined ? null : encodeIndexedString(write.value.requestId), encodeJson(write.value));
                break;
            case "document.create":
            case "document.change":
            case "document.retire":
                break;
        }
    }
    claimId(id, table) {
        this.db.prepare("INSERT OR IGNORE INTO record_ids (id, record_type) VALUES (?, ?)").run(id, table);
    }
    applyDocumentActions(actions, seq) {
        for (const [id, action] of actions) {
            let record;
            if (action.create !== undefined) {
                record = {
                    ...action.create,
                    createdAt: seq,
                    ...(action.retire ? { retiredAt: seq } : {}),
                };
                const parts = addressParts(record);
                this.claimId(id, "document");
                this.db
                    .prepare(`INSERT INTO documents
						(id, kind, family, key_value, scope_kind, owner_id, created_at, retired_at, record)
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`)
                    .run(id, parts.kind, parts.family, parts.keyValue, parts.scopeKind, parts.ownerId, seq, action.retire ? seq : null, encodeJson(record));
            }
            else {
                const row = getRow(this.db.prepare("SELECT record FROM documents WHERE id = ?"), id);
                record = parseJson(row.record);
            }
            if (action.content !== undefined) {
                if (action.content.kind === "base" && isCurrentOnly(record)) {
                    this.db.prepare("DELETE FROM document_revisions WHERE document_id = ?").run(id);
                }
                const encodedContent = action.content.kind === "base" ? encodeJson(action.content.value) : encodeJson(action.content.ops);
                this.db
                    .prepare("INSERT INTO document_revisions (document_id, seq, kind, version, content) VALUES (?, ?, ?, ?, ?)")
                    .run(id, seq, action.content.kind, action.content.version, encodedContent);
            }
            if (action.retire) {
                if (action.create === undefined) {
                    record = { ...record, retiredAt: seq };
                    this.db
                        .prepare("UPDATE documents SET retired_at = ?, record = ? WHERE id = ?")
                        .run(seq, encodeJson(record), id);
                }
                if (isCurrentOnly(record))
                    this.db.prepare("DELETE FROM document_revisions WHERE document_id = ?").run(id);
            }
        }
    }
    assertOpen() {
        if (this.closed)
            throw new Error("SqliteStorage is closed");
    }
}
//# sourceMappingURL=storage.js.map