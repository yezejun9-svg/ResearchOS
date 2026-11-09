-- Private configuration foundation only. No dependency on the later additive
-- session schema. Runtime qualification and public configure wiring are separate.
-- The redundant unique index permits an exact deferred request-hash foreign key
-- without rewriting any existing replay row or changing its logical uniqueness.
CREATE UNIQUE INDEX client_identity_receipt_request
 ON idempotency(principal,project,operation,key,request_hash);

CREATE TABLE client_command_identities (
 principal TEXT NOT NULL REFERENCES auth_principals(id),
 command_id TEXT NOT NULL CHECK(length(command_id)>0),
 protocol TEXT NOT NULL CHECK(protocol='researchos-client/2'),
 project TEXT NOT NULL,
 method TEXT NOT NULL CHECK(length(method)>0),
 operation TEXT NOT NULL CHECK(operation='v2:'||method),
 request_hash TEXT NOT NULL CHECK(length(request_hash)=71 AND substr(request_hash,1,7)='sha256:' AND substr(request_hash,8) NOT GLOB '*[^0-9a-f]*'),
 created_at TEXT NOT NULL CHECK(length(created_at)>0),
 PRIMARY KEY(principal,command_id),
 UNIQUE(principal,command_id,request_hash),
 FOREIGN KEY(principal,project,operation,command_id,request_hash)
  REFERENCES idempotency(principal,project,operation,key,request_hash)
  DEFERRABLE INITIALLY DEFERRED
);
CREATE TRIGGER client_identity_no_update BEFORE UPDATE ON client_command_identities BEGIN SELECT RAISE(ABORT,'immutable command identity'); END;
CREATE TRIGGER client_identity_no_delete BEFORE DELETE ON client_command_identities BEGIN SELECT RAISE(ABORT,'immutable command identity'); END;
CREATE TRIGGER client_identity_no_replace BEFORE INSERT ON client_command_identities WHEN EXISTS(SELECT 1 FROM client_command_identities WHERE principal=NEW.principal AND command_id=NEW.command_id) BEGIN SELECT RAISE(ABORT,'immutable command identity'); END;

CREATE TABLE host_model_configurations (
 model_config_ref TEXT PRIMARY KEY CHECK(length(model_config_ref)>0),
 owner_host_ref TEXT NOT NULL CHECK(length(owner_host_ref)=17 AND substr(owner_host_ref,1,5)='host-' AND substr(owner_host_ref,6) NOT GLOB '*[^0-9a-f]*'),
 principal TEXT NOT NULL,
 config_revision INTEGER NOT NULL CHECK(typeof(config_revision)='integer' AND config_revision BETWEEN 1 AND 9007199254740991),
 canonical_config_json TEXT NOT NULL CHECK(json_valid(canonical_config_json) AND json_type(canonical_config_json)='object'),
 config_hash TEXT NOT NULL CHECK(length(config_hash)=71 AND substr(config_hash,1,7)='sha256:' AND substr(config_hash,8) NOT GLOB '*[^0-9a-f]*'),
 command_id TEXT NOT NULL,
 request_hash TEXT NOT NULL,
 operation_scope_json TEXT NOT NULL CHECK(json_valid(operation_scope_json) AND json_type(operation_scope_json)='object'),
 scope_hash TEXT NOT NULL CHECK(length(scope_hash)=71 AND substr(scope_hash,1,7)='sha256:' AND substr(scope_hash,8) NOT GLOB '*[^0-9a-f]*'),
 created_at TEXT NOT NULL CHECK(length(created_at)>0),
 CHECK(json_extract(canonical_config_json,'$.config_revision')=config_revision),
 UNIQUE(owner_host_ref,principal,config_revision),
 UNIQUE(owner_host_ref,principal,config_revision,model_config_ref),
 UNIQUE(principal,command_id),
 FOREIGN KEY(principal,command_id,request_hash)
  REFERENCES client_command_identities(principal,command_id,request_hash)
  DEFERRABLE INITIALLY DEFERRED
);
CREATE TRIGGER host_config_no_update BEFORE UPDATE ON host_model_configurations BEGIN SELECT RAISE(ABORT,'immutable model configuration'); END;
CREATE TRIGGER host_config_no_delete BEFORE DELETE ON host_model_configurations BEGIN SELECT RAISE(ABORT,'immutable model configuration'); END;
CREATE TRIGGER host_config_no_replace BEFORE INSERT ON host_model_configurations WHEN EXISTS(SELECT 1 FROM host_model_configurations WHERE model_config_ref=NEW.model_config_ref OR (owner_host_ref=NEW.owner_host_ref AND principal=NEW.principal AND config_revision=NEW.config_revision) OR (principal=NEW.principal AND command_id=NEW.command_id)) BEGIN SELECT RAISE(ABORT,'immutable model configuration'); END;

CREATE TABLE host_model_config_heads (
 owner_host_ref TEXT NOT NULL,
 principal TEXT NOT NULL,
 current_revision INTEGER NOT NULL CHECK(typeof(current_revision)='integer' AND current_revision BETWEEN 1 AND 9007199254740991),
 default_model_config_ref TEXT NOT NULL,
 PRIMARY KEY(owner_host_ref,principal),
 FOREIGN KEY(owner_host_ref,principal,current_revision,default_model_config_ref)
  REFERENCES host_model_configurations(owner_host_ref,principal,config_revision,model_config_ref)
  DEFERRABLE INITIALLY DEFERRED
);
CREATE TRIGGER host_config_head_first BEFORE INSERT ON host_model_config_heads WHEN NEW.current_revision<>1 BEGIN SELECT RAISE(ABORT,'configuration head must begin at one'); END;
CREATE TRIGGER host_config_head_monotonic BEFORE UPDATE ON host_model_config_heads WHEN NEW.owner_host_ref<>OLD.owner_host_ref OR NEW.principal<>OLD.principal OR NEW.current_revision<>OLD.current_revision+1 OR NEW.default_model_config_ref=OLD.default_model_config_ref BEGIN SELECT RAISE(ABORT,'configuration head CAS must advance one'); END;
CREATE TRIGGER host_config_head_no_delete BEFORE DELETE ON host_model_config_heads BEGIN SELECT RAISE(ABORT,'configuration head cannot be deleted'); END;
CREATE TRIGGER host_config_head_no_replace BEFORE INSERT ON host_model_config_heads WHEN EXISTS(SELECT 1 FROM host_model_config_heads WHERE owner_host_ref=NEW.owner_host_ref AND principal=NEW.principal) BEGIN SELECT RAISE(ABORT,'configuration head cannot be replaced'); END;
