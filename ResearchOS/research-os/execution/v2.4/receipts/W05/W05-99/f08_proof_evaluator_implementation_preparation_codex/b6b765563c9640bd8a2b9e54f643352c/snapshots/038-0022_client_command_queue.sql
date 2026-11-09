-- Internal operational evidence. No dependency on the later additive session schema.
CREATE TABLE client_queue_fences (
 project TEXT NOT NULL, task_id TEXT NOT NULL, session_id TEXT NOT NULL,
 generation TEXT NOT NULL UNIQUE, state TEXT NOT NULL CHECK(state IN ('OPEN','SEALING','SEALED','CANCEL_FENCED','RECONCILING')),
 accepted_through INTEGER NOT NULL DEFAULT 0, sealed_through INTEGER NOT NULL DEFAULT 0,
 run_id TEXT, runtime_epoch INTEGER, dispatch_key TEXT, manifest_hash TEXT, process_identity TEXT,
 restore_fenced INTEGER NOT NULL DEFAULT 0 CHECK(restore_fenced IN (0,1)),
 revision INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(project,task_id)
);
CREATE TABLE client_command_queue (
 principal TEXT NOT NULL, project TEXT NOT NULL, command_id TEXT NOT NULL,
 session_id TEXT NOT NULL, task_id TEXT NOT NULL, goal_id TEXT NOT NULL,
 generation TEXT NOT NULL REFERENCES client_queue_fences(generation), queue_sequence INTEGER NOT NULL,
 request_hash TEXT NOT NULL, message_id TEXT NOT NULL UNIQUE, accepted_writer_epoch INTEGER NOT NULL,
 delivery TEXT NOT NULL CHECK(delivery IN ('STEER','FOLLOW_UP')), content TEXT NOT NULL, content_hash TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('ENQUEUED','SENDING','SDK_ACCEPTED','CONSUMED','DROP_REQUESTED','DROPPED','UNKNOWN')),
 revision INTEGER NOT NULL DEFAULT 1, last_receipt_id TEXT, created_at TEXT NOT NULL,
 PRIMARY KEY(principal,project,command_id), UNIQUE(generation,queue_sequence)
);
CREATE INDEX client_queue_pending ON client_command_queue(project,session_id,state);
CREATE TABLE client_control_requests (
 principal TEXT NOT NULL, project TEXT NOT NULL, command_id TEXT NOT NULL,
 session_id TEXT NOT NULL, control_request_id TEXT NOT NULL UNIQUE, request_hash TEXT NOT NULL,
 target_id TEXT NOT NULL, task_ids TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('REQUESTED','RECONCILING','CONFIRMED')),
 original_response TEXT, final_response TEXT, created_at TEXT NOT NULL,
 PRIMARY KEY(principal,project,command_id)
);
CREATE TABLE client_control_receipts (
 receipt_id TEXT PRIMARY KEY, project TEXT NOT NULL, generation TEXT NOT NULL,
 command_id TEXT, kind TEXT NOT NULL, body TEXT NOT NULL, body_hash TEXT NOT NULL,
 previous_receipt_id TEXT, created_at TEXT NOT NULL
);
CREATE TRIGGER client_receipt_no_update BEFORE UPDATE ON client_control_receipts BEGIN SELECT RAISE(ABORT,'append-only control receipt'); END;
CREATE TRIGGER client_receipt_no_delete BEFORE DELETE ON client_control_receipts BEGIN SELECT RAISE(ABORT,'append-only control receipt'); END;
