import type { Context, JsonValue } from "@earendil-works/chord";
import type { FileSystem } from "../../env/index.ts";
import type { Cursor, DocumentAddress, DocumentPoint, DocumentQuery, EntryQuery, Id, Seq, Storage, StorageWrite, TaskQuery } from "../../types.ts";
export type JsonlStorageOptions = {
    /** Flush every affected sidecar before appending the main marker. Defaults to false. */
    readonly fsync?: boolean;
};
export declare class JsonlCorruptionError extends Error {
    constructor(message: string, cause?: Error);
}
export declare class JsonlStoragePoisonedError extends Error {
    constructor(cause: Error);
}
/** Portable JSONL implementation of the storage contract. */
export declare class JsonlStorage implements Storage {
    private readonly fs;
    private readonly directory;
    private readonly mainPath;
    private readonly fsync;
    private readonly memory;
    private readonly currentOnlyDocuments;
    private readonly liveTaskSidecars;
    private closed;
    private poisonError;
    private constructor();
    /** Open or create a JSONL storage directory using the supplied filesystem. */
    static open(directory: string, fs: FileSystem, context: Context, options?: JsonlStorageOptions): Promise<JsonlStorage>;
    commit(writes: readonly StorageWrite[], context: Context): Promise<Seq>;
    mintId(): Promise<number>;
    conversation(id: Id, context: Context): Promise<import("../../types.ts").ConversationRecord | undefined>;
    scanConversations(limit: number, cursor: Cursor | undefined, context: Context): Promise<import("../../types.ts").Page<import("../../types.ts").ConversationRecord, Readonly<Record<string, JsonValue>>>>;
    entry(id: Id, context: Context): ReturnType<Storage["entry"]>;
    entry(conversationId: Id, id: Id, context: Context): ReturnType<Storage["entry"]>;
    findLatestHeadMarker(conversationId: Id, atOrBeforeEntryId: Id | undefined, context: Context): Promise<(import("../../types.ts").EntryRecord & {
        readonly head: number;
    }) | undefined>;
    scanEntries(query: EntryQuery, limit: number, cursor: Cursor | undefined, context: Context): Promise<import("../../types.ts").Page<import("../../types.ts").EntryRecord, Readonly<Record<string, JsonValue>>>>;
    task(id: Id, context: Context): Promise<({
        readonly id: number;
        readonly conversationId: number;
        readonly kind: string;
        readonly version: number;
        readonly input: JsonValue;
        readonly after: readonly number[];
        readonly background: boolean;
        readonly abortRequested: boolean;
    } & ({
        readonly state: {
            readonly status: "pending";
            readonly checkpoint: JsonValue;
            readonly outcome?: undefined;
        } | {
            readonly status: "running";
            readonly checkpoint: JsonValue;
            readonly outcome?: undefined;
        };
        readonly memos?: Readonly<Record<string, JsonValue>> | undefined;
    } | {
        readonly state: {
            readonly status: "terminal";
            readonly checkpoint?: undefined;
            readonly outcome: import("../../types.ts").TaskOutcome<JsonValue>;
        };
        readonly memos?: undefined;
    })) | undefined>;
    scanTasks(query: TaskQuery, limit: number, cursor: Cursor | undefined, context: Context): Promise<import("../../types.ts").Page<{
        readonly id: number;
        readonly conversationId: number;
        readonly kind: string;
        readonly version: number;
        readonly input: JsonValue;
        readonly after: readonly number[];
        readonly background: boolean;
        readonly abortRequested: boolean;
    } & ({
        readonly state: {
            readonly status: "pending";
            readonly checkpoint: JsonValue;
            readonly outcome?: undefined;
        } | {
            readonly status: "running";
            readonly checkpoint: JsonValue;
            readonly outcome?: undefined;
        };
        readonly memos?: Readonly<Record<string, JsonValue>> | undefined;
    } | {
        readonly state: {
            readonly status: "terminal";
            readonly checkpoint?: undefined;
            readonly outcome: import("../../types.ts").TaskOutcome<JsonValue>;
        };
        readonly memos?: undefined;
    }), Readonly<Record<string, JsonValue>>>>;
    submission(id: Id, context: Context): Promise<import("../../types.ts").SubmissionRecord | undefined>;
    submissionByRequest(conversationId: Id, requestId: string, context: Context): Promise<import("../../types.ts").SubmissionRecord | undefined>;
    findDocument(address: DocumentAddress, at: DocumentPoint, context: Context): Promise<import("../../types.ts").DocumentRecord | undefined>;
    document(id: Id, at: DocumentPoint, context: Context): Promise<import("../../types.ts").StoredDocument | undefined>;
    scanDocuments(query: DocumentQuery, limit: number, cursor: Cursor | undefined, context: Context): Promise<import("../../types.ts").Page<import("../../types.ts").DocumentRecord, Readonly<Record<string, JsonValue>>>>;
    close(context: Context): Promise<void>;
    private encodeCommit;
    private planReclamations;
    private adoptSidecarState;
    private reclaimSidecars;
    private replaceSidecar;
    private recover;
    private static confirmRecord;
    private static readLines;
    private resolveFile;
    private get store();
    private poison;
    private assertUsable;
}
//# sourceMappingURL=storage.d.ts.map