-- Internal pause authority. Public Run enums and the original queue generation stay unchanged.
CREATE TABLE runtime_pause_intents (
 project TEXT NOT NULL, pause_id TEXT NOT NULL, task TEXT NOT NULL, run TEXT NOT NULL,
 epoch INTEGER NOT NULL CHECK(epoch>0), session_id TEXT NOT NULL, generation TEXT NOT NULL,
 principal TEXT NOT NULL, request_key TEXT NOT NULL, request_hash TEXT NOT NULL,
 runtime TEXT NOT NULL, dispatch_key TEXT NOT NULL, manifest_hash TEXT NOT NULL,
 process_identity_hash TEXT NOT NULL, original_input_hash TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PAUSE_REQUESTED','CHECKPOINT_SEALED','PAUSED_CONFIRMED','RESUME_PREPARED','RESUMED','CANCELLED','RECONCILING')),
 revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>0),
 checkpoint_sequence INTEGER CHECK(checkpoint_sequence>0),
 checkpoint_artifact TEXT, checkpoint_use_receipt_hash TEXT, checkpoint_use_principal TEXT, checkpoint_hash TEXT,
 checkpoint_bytes INTEGER CHECK(checkpoint_bytes>0 AND checkpoint_bytes<=12582912),
 native_session_ref TEXT, sdk_session_id TEXT,
 queue_cut INTEGER CHECK(queue_cut>=0), command_ledger_hash TEXT,
 sdk_watermarks_json TEXT CHECK(sdk_watermarks_json IS NULL OR (json_valid(sdk_watermarks_json) AND json_type(sdk_watermarks_json)='object')),
 model_calls INTEGER CHECK(model_calls>=0), tool_calls INTEGER CHECK(tool_calls>=0),
 journal_checkpoint_hash TEXT, successor_epoch INTEGER CHECK(successor_epoch=epoch+1),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(project,pause_id), UNIQUE(project,run,epoch), UNIQUE(principal,project,request_key),
 FOREIGN KEY(project,run,epoch) REFERENCES runtime_dispatches(project,run,epoch),
 FOREIGN KEY(generation) REFERENCES client_queue_fences(generation),
 CHECK((checkpoint_hash IS NULL AND checkpoint_sequence IS NULL AND checkpoint_artifact IS NULL
  AND checkpoint_use_receipt_hash IS NULL AND checkpoint_use_principal IS NULL AND checkpoint_bytes IS NULL AND native_session_ref IS NULL
  AND sdk_session_id IS NULL AND queue_cut IS NULL AND command_ledger_hash IS NULL
  AND sdk_watermarks_json IS NULL AND model_calls IS NULL AND tool_calls IS NULL AND journal_checkpoint_hash IS NULL)
 OR (checkpoint_hash IS NOT NULL AND checkpoint_sequence IS NOT NULL AND checkpoint_artifact IS NOT NULL
  AND checkpoint_use_receipt_hash IS NOT NULL AND checkpoint_use_principal IS NOT NULL AND checkpoint_bytes IS NOT NULL AND native_session_ref IS NOT NULL
  AND sdk_session_id IS NOT NULL AND queue_cut IS NOT NULL AND command_ledger_hash IS NOT NULL
  AND sdk_watermarks_json IS NOT NULL AND model_calls IS NOT NULL AND tool_calls IS NOT NULL AND journal_checkpoint_hash IS NOT NULL)),
 CHECK(state IN ('PAUSE_REQUESTED','RECONCILING','CANCELLED') OR checkpoint_hash IS NOT NULL),
 CHECK(state NOT IN ('RESUME_PREPARED','RESUMED') OR successor_epoch IS NOT NULL),
 CHECK(successor_epoch IS NULL OR state IN ('RESUME_PREPARED','RESUMED','RECONCILING','CANCELLED'))
);
CREATE INDEX runtime_pause_active ON runtime_pause_intents(project,task,state);
CREATE TRIGGER runtime_pause_identity_frozen BEFORE UPDATE OF project,pause_id,task,run,epoch,session_id,generation,principal,request_key,request_hash,runtime,dispatch_key,manifest_hash,process_identity_hash,original_input_hash,created_at
ON runtime_pause_intents BEGIN SELECT RAISE(ABORT,'pause original identity immutable'); END;
CREATE TRIGGER runtime_pause_revision BEFORE UPDATE ON runtime_pause_intents
WHEN NEW.revision<>OLD.revision+1 BEGIN SELECT RAISE(ABORT,'pause revision must advance once'); END;
CREATE TRIGGER runtime_pause_no_delete BEFORE DELETE ON runtime_pause_intents
BEGIN SELECT RAISE(ABORT,'pause history retained'); END;
CREATE TRIGGER runtime_pause_snapshot_frozen BEFORE UPDATE ON runtime_pause_intents
WHEN OLD.checkpoint_hash IS NOT NULL AND
 (NEW.checkpoint_sequence IS NOT OLD.checkpoint_sequence OR NEW.checkpoint_artifact IS NOT OLD.checkpoint_artifact
 OR NEW.checkpoint_use_receipt_hash IS NOT OLD.checkpoint_use_receipt_hash OR NEW.checkpoint_use_principal IS NOT OLD.checkpoint_use_principal OR NEW.checkpoint_hash IS NOT OLD.checkpoint_hash
 OR NEW.checkpoint_bytes IS NOT OLD.checkpoint_bytes OR NEW.native_session_ref IS NOT OLD.native_session_ref
 OR NEW.sdk_session_id IS NOT OLD.sdk_session_id OR NEW.queue_cut IS NOT OLD.queue_cut
 OR NEW.command_ledger_hash IS NOT OLD.command_ledger_hash OR NEW.sdk_watermarks_json IS NOT OLD.sdk_watermarks_json
 OR NEW.model_calls IS NOT OLD.model_calls OR NEW.tool_calls IS NOT OLD.tool_calls
 OR NEW.journal_checkpoint_hash IS NOT OLD.journal_checkpoint_hash)
BEGIN SELECT RAISE(ABORT,'sealed pause snapshot immutable'); END;
CREATE TRIGGER runtime_pause_successor_frozen BEFORE UPDATE ON runtime_pause_intents
WHEN OLD.successor_epoch IS NOT NULL AND NEW.successor_epoch IS NOT OLD.successor_epoch
BEGIN SELECT RAISE(ABORT,'pause successor immutable'); END;
CREATE TRIGGER runtime_pause_transition BEFORE UPDATE ON runtime_pause_intents
WHEN NOT (NEW.state=OLD.state OR NEW.state='CANCELLED'
 OR (OLD.state='PAUSE_REQUESTED' AND NEW.state IN ('CHECKPOINT_SEALED','RECONCILING'))
 OR (OLD.state='CHECKPOINT_SEALED' AND NEW.state IN ('PAUSED_CONFIRMED','RECONCILING'))
 OR (OLD.state='PAUSED_CONFIRMED' AND NEW.state IN ('RESUME_PREPARED','RECONCILING'))
 OR (OLD.state='RESUME_PREPARED' AND NEW.state IN ('RESUMED','RECONCILING'))
 OR (OLD.state='RECONCILING' AND NEW.state IN ('CHECKPOINT_SEALED','PAUSED_CONFIRMED','RESUME_PREPARED','RESUMED')))
 OR (OLD.state='CANCELLED' AND NEW.state<>'CANCELLED')
BEGIN SELECT RAISE(ABORT,'invalid pause transition'); END;

-- One immutable activation per successor epoch. Later process observations are receipts.
CREATE TABLE runtime_checkpoint_activations (
 project TEXT NOT NULL, run TEXT NOT NULL, epoch INTEGER NOT NULL CHECK(epoch>1),
 previous_epoch INTEGER NOT NULL CHECK(previous_epoch>0 AND epoch=previous_epoch+1),
 pause_id TEXT NOT NULL, task TEXT NOT NULL, session_id TEXT NOT NULL, generation TEXT NOT NULL,
 principal TEXT NOT NULL, request_key TEXT NOT NULL, request_hash TEXT NOT NULL,
 dispatch_key TEXT NOT NULL, manifest_hash TEXT NOT NULL,
 checkpoint_artifact TEXT NOT NULL, checkpoint_hash TEXT NOT NULL, checkpoint_use_receipt_hash TEXT NOT NULL, checkpoint_use_principal TEXT NOT NULL,
 carry_use_receipt_hash TEXT NOT NULL, carry_use_principal TEXT NOT NULL, original_input_hash TEXT NOT NULL,
 native_session_ref TEXT NOT NULL, sdk_session_id TEXT NOT NULL,
 queue_cut INTEGER NOT NULL CHECK(queue_cut>=0), model_calls INTEGER NOT NULL CHECK(model_calls>=0),
 tool_calls INTEGER NOT NULL CHECK(tool_calls>=0), created_at TEXT NOT NULL,
 PRIMARY KEY(project,run,epoch), UNIQUE(project,run,previous_epoch), UNIQUE(principal,project,request_key),
 FOREIGN KEY(project,pause_id) REFERENCES runtime_pause_intents(project,pause_id),
 FOREIGN KEY(project,run,epoch) REFERENCES runtime_dispatches(project,run,epoch),
 FOREIGN KEY(generation) REFERENCES client_queue_fences(generation)
);
CREATE TRIGGER runtime_checkpoint_activation_no_update BEFORE UPDATE ON runtime_checkpoint_activations
BEGIN SELECT RAISE(ABORT,'checkpoint activation immutable'); END;
CREATE TRIGGER runtime_checkpoint_activation_no_delete BEFORE DELETE ON runtime_checkpoint_activations
BEGIN SELECT RAISE(ABORT,'checkpoint activation durable'); END;
CREATE TRIGGER runtime_checkpoint_activation_binding BEFORE INSERT ON runtime_checkpoint_activations
WHEN NOT EXISTS(SELECT 1 FROM runtime_pause_intents p WHERE p.project=NEW.project AND p.pause_id=NEW.pause_id
 AND p.run=NEW.run AND p.epoch=NEW.previous_epoch AND p.successor_epoch=NEW.epoch
 AND p.task=NEW.task AND p.session_id=NEW.session_id AND p.generation=NEW.generation
 AND p.state='RESUME_PREPARED' AND p.checkpoint_artifact=NEW.checkpoint_artifact
 AND p.checkpoint_hash=NEW.checkpoint_hash AND p.checkpoint_use_receipt_hash=NEW.checkpoint_use_receipt_hash
 AND p.checkpoint_use_principal=NEW.checkpoint_use_principal AND p.original_input_hash=NEW.original_input_hash AND p.native_session_ref=NEW.native_session_ref
 AND p.sdk_session_id=NEW.sdk_session_id AND p.queue_cut=NEW.queue_cut
 AND p.model_calls=NEW.model_calls AND p.tool_calls=NEW.tool_calls)
 OR EXISTS(SELECT 1 FROM client_queue_fences f WHERE f.generation=NEW.generation
 AND (f.state<>'OPEN' OR f.restore_fenced<>0))
 OR NOT EXISTS(SELECT 1 FROM domain_objects r WHERE r.project=NEW.project AND r.kind='Run' AND r.id=NEW.run
 AND json_extract(r.body,'$.status') NOT IN ('CANCEL_REQUESTED','CANCELLED','FAILED','SETTLED'))
BEGIN SELECT RAISE(ABORT,'successor activation requires original paused authority'); END;

CREATE TABLE runtime_pause_receipts (
 receipt_id TEXT PRIMARY KEY, project TEXT NOT NULL, pause_id TEXT NOT NULL,
 sequence INTEGER NOT NULL CHECK(sequence>0), kind TEXT NOT NULL,
 body TEXT NOT NULL CHECK(json_valid(body) AND json_type(body)='object'), body_hash TEXT NOT NULL,
 previous_receipt_hash TEXT, created_at TEXT NOT NULL,
 UNIQUE(project,pause_id,sequence), UNIQUE(project,pause_id,body_hash),
 FOREIGN KEY(project,pause_id) REFERENCES runtime_pause_intents(project,pause_id)
);
CREATE TRIGGER runtime_pause_receipt_chain BEFORE INSERT ON runtime_pause_receipts
WHEN (NEW.sequence=1 AND NEW.previous_receipt_hash IS NOT NULL)
 OR (NEW.sequence>1 AND NOT EXISTS(SELECT 1 FROM runtime_pause_receipts p
 WHERE p.project=NEW.project AND p.pause_id=NEW.pause_id AND p.sequence=NEW.sequence-1
 AND p.body_hash=NEW.previous_receipt_hash))
BEGIN SELECT RAISE(ABORT,'pause receipt predecessor required'); END;
CREATE TRIGGER runtime_pause_receipt_no_update BEFORE UPDATE ON runtime_pause_receipts
BEGIN SELECT RAISE(ABORT,'append-only pause receipt'); END;
CREATE TRIGGER runtime_pause_receipt_no_delete BEFORE DELETE ON runtime_pause_receipts
BEGIN SELECT RAISE(ABORT,'durable pause receipt'); END;
