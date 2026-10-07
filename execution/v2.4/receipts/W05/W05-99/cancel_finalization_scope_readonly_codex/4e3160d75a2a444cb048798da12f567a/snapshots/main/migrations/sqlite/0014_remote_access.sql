CREATE TABLE remote_challenges(id TEXT PRIMARY KEY, owner TEXT NOT NULL REFERENCES auth_principals(id), token_hash TEXT NOT NULL UNIQUE, projects TEXT NOT NULL CHECK(json_valid(projects)), expires_at TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE remote_devices(id TEXT PRIMARY KEY REFERENCES auth_principals(id), owner TEXT NOT NULL REFERENCES auth_principals(id), body TEXT NOT NULL CHECK(json_valid(body)));
CREATE TABLE remote_refresh(token_hash TEXT PRIMARY KEY, device TEXT NOT NULL REFERENCES remote_devices(id), expires_at TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE remote_replays(actor TEXT NOT NULL, operation TEXT NOT NULL, key TEXT NOT NULL, request_hash TEXT NOT NULL, target TEXT NOT NULL, response BLOB CHECK(response IS NULL OR operation IN ('updateDeviceGrants','revokeDevice')), expires_at TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(actor,operation,key));
CREATE TABLE remote_audit(id TEXT PRIMARY KEY, actor TEXT NOT NULL, operation TEXT NOT NULL, target TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TRIGGER remote_audit_no_update BEFORE UPDATE ON remote_audit BEGIN SELECT RAISE(ABORT,'immutable remote audit'); END;
CREATE TRIGGER remote_audit_no_delete BEFORE DELETE ON remote_audit BEGIN SELECT RAISE(ABORT,'immutable remote audit'); END;
