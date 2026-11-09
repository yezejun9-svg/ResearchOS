import type { Context, JsonValue } from "@earendil-works/chord";
import type { ConversationRecord, Cursor, DocumentAddress, DocumentPoint, DocumentQuery, DocumentRecord, EntryQuery, EntryRecord, Id, Page, Seq, Storage, StorageWrite, StoredDocument, SubmissionRecord, TaskQuery, TaskRecord } from "../types.ts";
type StoredTask = TaskRecord<JsonValue, JsonValue, JsonValue>;
/** A fully validated, detached state mutation whose application performs no fallible preparation. */
export interface PreparedMemoryCommit {
    readonly seq: Seq;
    /** Deeply frozen detached writes for persistence. */
    readonly writes: readonly StorageWrite[];
    apply(): Seq;
}
/**
 * Detached in-memory reference implementation of `Storage`.
 *
 * Reads and retained writes are cloned intentionally to match the ownership boundary
 * of serialization-backed stores. This is backend conformance, not validation.
 */
export declare class MemoryStorage implements Storage {
    private readonly state;
    private nextId;
    private nextSeq;
    private closed;
    commit(writes: readonly StorageWrite[], _context: Context): Promise<Seq>;
    /** Validate and detach one commit without changing observable state. */
    prepareCommit(writes: readonly StorageWrite[], seq?: Seq): PreparedMemoryCommit;
    private applyPreparedCommit;
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
    private visibleEntries;
    private checkGlobalIds;
    private prepareDocumentActions;
    private checkDocumentActions;
    private applyDocumentActions;
    private assertOpen;
}
export {};
//# sourceMappingURL=memory.d.ts.map