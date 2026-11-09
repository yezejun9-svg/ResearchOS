import { DatabaseSync } from "node:sqlite";
import type { SqliteDatabase, SqliteStatement } from "./database.ts";
import { SqliteStorage } from "./storage.ts";
/** Node SQLite connection settings for a durable storage file. */
export type NodeSqliteStorageOptions = {
    /** SQLite WAL auto-checkpoint threshold. SQLite and this adapter default to 1,000 pages; 0 disables it. */
    readonly walAutoCheckpointPages?: number;
    /** Time SQLite waits for a competing file lock. SQLite defaults to 0; this adapter defaults to 5,000 ms. */
    readonly busyTimeoutMs?: number;
};
/** `SqliteDatabase` adapter backed by Node's built-in `node:sqlite`. */
export declare class NodeSqliteDatabase implements SqliteDatabase {
    private readonly database;
    private closed;
    constructor(database: DatabaseSync);
    exec(sql: string): void;
    prepare(sql: string): SqliteStatement;
    transaction<T>(callback: () => T): T;
    close(): void;
}
/** Open and configure a Node-backed SQLite database facade. */
export declare function openNodeSqliteDatabase(path: string, options?: NodeSqliteStorageOptions): Promise<NodeSqliteDatabase>;
/** Open or create file-backed durable storage using Node's built-in SQLite. */
export declare function openNodeSqliteStorage(path: string, options?: NodeSqliteStorageOptions): Promise<SqliteStorage>;
//# sourceMappingURL=node.d.ts.map