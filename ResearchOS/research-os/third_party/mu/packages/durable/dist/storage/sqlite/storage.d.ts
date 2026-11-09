import type { Context, JsonValue } from "@earendil-works/chord";
import type { ConversationRecord, Cursor, DocumentAddress, DocumentPoint, DocumentQuery, DocumentRecord, EntryQuery, EntryRecord, Id, Page, Seq, Storage, StorageWrite, StoredDocument, SubmissionRecord, TaskQuery, TaskRecord } from "../../types.ts";
import type { SqliteDatabase } from "./database.ts";
type StoredTask = TaskRecord<JsonValue, JsonValue, JsonValue>;
/** Portable SQLite implementation of the Pico storage contract. */
export declare class SqliteStorage implements Storage {
    private readonly db;
    private nextId;
    private closed;
    private constructor();
    /** Initialize storage over an owned SQLite database facade. */
    static open(db: SqliteDatabase): Promise<SqliteStorage>;
    commit(writes: readonly StorageWrite[], _context: Context): Promise<Seq>;
    mintId(): Promise<Id>;
    conversation(id: Id, _context: Context): Promise<ConversationRecord | undefined>;
    scanConversations(limit: number, cursor: Cursor | undefined, _context: Context): Promise<Page<ConversationRecord, Cursor>>;
    entry(id: Id, context: Context): Promise<{
        readonly entry: EntryRecord;
        readonly commitSeq: Seq;
    } | undefined>;
    entry(conversationId: Id, id: Id, context: Context): Promise<{
        readonly entry: EntryRecord;
        readonly commitSeq: Seq;
    } | undefined>;
    findLatestHeadMarker(conversationId: Id, atOrBeforeEntryId: Id | undefined, _context: Context): Promise<(EntryRecord & {
        readonly head: Id;
    }) | undefined>;
    scanEntries(query: EntryQuery, limit: number, cursor: Cursor | undefined, _context: Context): Promise<Page<EntryRecord, Cursor>>;
    task(id: Id, _context: Context): Promise<StoredTask | undefined>;
    scanTasks(query: TaskQuery, limit: number, cursor: Cursor | undefined, _context: Context): Promise<Page<StoredTask, Cursor>>;
    submission(id: Id, _context: Context): Promise<SubmissionRecord | undefined>;
    submissionByRequest(conversationId: Id, requestId: string, _context: Context): Promise<SubmissionRecord | undefined>;
    findDocument(address: DocumentAddress, at: DocumentPoint, _context: Context): Promise<DocumentRecord | undefined>;
    document(id: Id, at: DocumentPoint, _context: Context): Promise<StoredDocument | undefined>;
    scanDocuments(query: DocumentQuery, limit: number, cursor: Cursor | undefined, _context: Context): Promise<Page<DocumentRecord, Cursor>>;
    close(_context: Context): Promise<void>;
    private readConversation;
    private candidateNextId;
    private checkGlobalIds;
    private prepareDocumentActions;
    private checkDocumentActions;
    private currentDocumentId;
    private applyTableWrite;
    private claimId;
    private applyDocumentActions;
    private assertOpen;
}
export {};
//# sourceMappingURL=storage.d.ts.map