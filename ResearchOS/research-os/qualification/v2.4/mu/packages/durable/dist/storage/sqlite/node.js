import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { SqliteStorage } from "./storage.js";
const DEFAULT_WAL_AUTO_CHECKPOINT_PAGES = 1_000;
const DEFAULT_BUSY_TIMEOUT_MS = 5_000;
class NodeSqliteStatement {
    statement;
    constructor(statement) {
        this.statement = statement;
    }
    run(...params) {
        this.statement.run(...params);
    }
    get(...params) {
        return this.statement.get(...params);
    }
    all(...params) {
        return this.statement.all(...params);
    }
}
/** `SqliteDatabase` adapter backed by Node's built-in `node:sqlite`. */
export class NodeSqliteDatabase {
    database;
    closed = false;
    constructor(database) {
        this.database = database;
    }
    exec(sql) {
        this.database.exec(sql);
    }
    prepare(sql) {
        return new NodeSqliteStatement(this.database.prepare(sql));
    }
    transaction(callback) {
        this.database.exec("BEGIN IMMEDIATE");
        try {
            const result = callback();
            if (result !== null &&
                (typeof result === "object" || typeof result === "function") &&
                typeof Reflect.get(result, "then") === "function") {
                throw new TypeError("SQLite transaction callbacks must be synchronous");
            }
            this.database.exec("COMMIT");
            return result;
        }
        catch (error) {
            try {
                this.database.exec("ROLLBACK");
            }
            catch {
                // Preserve the error that caused the transaction to fail.
            }
            throw error;
        }
    }
    close() {
        if (this.closed)
            return;
        this.closed = true;
        try {
            this.database.exec("PRAGMA wal_checkpoint(TRUNCATE)");
        }
        finally {
            this.database.close();
        }
    }
}
/** Open and configure a Node-backed SQLite database facade. */
export async function openNodeSqliteDatabase(path, options = {}) {
    const checkpointPages = options.walAutoCheckpointPages ?? DEFAULT_WAL_AUTO_CHECKPOINT_PAGES;
    const timeout = options.busyTimeoutMs ?? DEFAULT_BUSY_TIMEOUT_MS;
    if (path !== ":memory:")
        await mkdir(dirname(path), { recursive: true });
    const database = new DatabaseSync(path, { timeout });
    const adapter = new NodeSqliteDatabase(database);
    try {
        adapter.exec("PRAGMA journal_mode = WAL");
        adapter.exec("PRAGMA synchronous = NORMAL");
        adapter.exec(`PRAGMA wal_autocheckpoint = ${checkpointPages}`);
        return adapter;
    }
    catch (error) {
        try {
            adapter.close();
        }
        catch {
            // Preserve the configuration failure.
        }
        throw error;
    }
}
/** Open or create file-backed durable storage using Node's built-in SQLite. */
export async function openNodeSqliteStorage(path, options = {}) {
    return SqliteStorage.open(await openNodeSqliteDatabase(path, options));
}
//# sourceMappingURL=node.js.map