-- R2 private release effect ledger. The supervisor-owned journal, not this
-- candidate-writable domain database, is the mechanical slot authority.
CREATE TABLE evolution_release_operations (
  project TEXT NOT NULL,
  candidate TEXT NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('START_CANARY','ROLLBACK','PROMOTE')),
  operation_id TEXT NOT NULL UNIQUE,
  expected_epoch INTEGER NOT NULL CHECK (typeof(expected_epoch)='integer' AND expected_epoch > 0),
  admission_hash TEXT NOT NULL CHECK (length(admission_hash)=64 AND admission_hash NOT GLOB '*[^0-9a-f]*'),
  effect_key TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL CHECK (status IN ('PREPARED','DISPATCHED','OBSERVED','FAILED','PROJECTED')),
  receipt_digest TEXT,
  projection_revision INTEGER NOT NULL DEFAULT 0 CHECK (typeof(projection_revision)='integer' AND projection_revision >= 0),
  PRIMARY KEY (project,candidate,action),
  CHECK ((status IN ('OBSERVED','PROJECTED') AND receipt_digest IS NOT NULL AND length(receipt_digest)=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*') OR
         (status IN ('PREPARED','DISPATCHED','FAILED') AND receipt_digest IS NULL)),
  CHECK ((status='PROJECTED' AND projection_revision>0) OR (status!='PROJECTED' AND projection_revision=0))
);
CREATE TRIGGER evolution_release_operation_insert_guard BEFORE INSERT ON evolution_release_operations
WHEN NEW.status!='PREPARED' OR
     EXISTS(SELECT 1 FROM evolution_release_operations WHERE project=NEW.project AND candidate=NEW.candidate AND action=NEW.action) OR
     EXISTS(SELECT 1 FROM evolution_release_operations WHERE operation_id=NEW.operation_id) OR
     EXISTS(SELECT 1 FROM evolution_release_operations WHERE effect_key=NEW.effect_key)
BEGIN SELECT RAISE(ABORT,'release operation must begin prepared and cannot replace identity'); END;
CREATE TRIGGER evolution_release_operation_guard BEFORE UPDATE ON evolution_release_operations
WHEN OLD.project IS NOT NEW.project OR OLD.candidate IS NOT NEW.candidate OR OLD.action IS NOT NEW.action OR
     OLD.operation_id IS NOT NEW.operation_id OR OLD.expected_epoch IS NOT NEW.expected_epoch OR
     OLD.admission_hash IS NOT NEW.admission_hash OR OLD.effect_key IS NOT NEW.effect_key OR
     (OLD.receipt_digest IS NOT NULL AND OLD.receipt_digest IS NOT NEW.receipt_digest) OR
     (OLD.status=NEW.status AND (OLD.receipt_digest IS NOT NEW.receipt_digest OR OLD.projection_revision IS NOT NEW.projection_revision)) OR
     (OLD.status!=NEW.status AND NOT (
       (OLD.status='PREPARED' AND NEW.status IN ('DISPATCHED','FAILED')) OR
       (OLD.status='DISPATCHED' AND NEW.status='OBSERVED') OR
       (OLD.status='OBSERVED' AND NEW.status='PROJECTED')))
BEGIN SELECT RAISE(ABORT,'release operation is immutable or transition invalid'); END;
CREATE TRIGGER evolution_release_operation_nodelete BEFORE DELETE ON evolution_release_operations
BEGIN SELECT RAISE(ABORT,'release operation is append-only'); END;
