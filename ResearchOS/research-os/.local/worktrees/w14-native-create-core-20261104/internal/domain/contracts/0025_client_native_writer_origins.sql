-- Prepared fresh-fixture addon only. Not a live migration; no schema_migrations bump.
DROP TRIGGER idempotency_immutable;

-- object: client_native_writer_origins
CREATE TABLE client_native_writer_origins (
 origin_schema TEXT NOT NULL CHECK(typeof(origin_schema)='text' AND length(origin_schema)>0 AND origin_schema='researchos.client-native-writer-origin.v1'),
 schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version=1),
 attestation_ref TEXT NOT NULL CHECK(typeof(attestation_ref)='text' AND length(attestation_ref)>0 AND length(attestation_ref)=69 AND substr(attestation_ref,1,5)='natt-' AND substr(attestation_ref,6) NOT GLOB '*[^0-9a-f]*'),
 witness_hash TEXT NOT NULL CHECK(typeof(witness_hash)='text' AND length(witness_hash)>0 AND length(witness_hash)=71 AND substr(witness_hash,1,7)='sha256:' AND substr(witness_hash,8) NOT GLOB '*[^0-9a-f]*'),
 principal TEXT NOT NULL CHECK(typeof(principal)='text' AND length(principal)>0),
 authority_root TEXT NOT NULL CHECK(typeof(authority_root)='text' AND length(authority_root)>0),
 command_id TEXT NOT NULL CHECK(typeof(command_id)='text' AND length(command_id)>0),
 request_hash TEXT NOT NULL CHECK(typeof(request_hash)='text' AND length(request_hash)>0 AND length(request_hash)=71 AND substr(request_hash,1,7)='sha256:' AND substr(request_hash,8) NOT GLOB '*[^0-9a-f]*'),
 request_wire_hash TEXT NOT NULL CHECK(typeof(request_wire_hash)='text' AND length(request_wire_hash)>0 AND length(request_wire_hash)=71 AND substr(request_wire_hash,1,7)='sha256:' AND substr(request_wire_hash,8) NOT GLOB '*[^0-9a-f]*'),
 response_hash TEXT NOT NULL CHECK(typeof(response_hash)='text' AND length(response_hash)>0 AND length(response_hash)=71 AND substr(response_hash,1,7)='sha256:' AND substr(response_hash,8) NOT GLOB '*[^0-9a-f]*'),
 project TEXT NOT NULL CHECK(typeof(project)='text' AND length(project)>0),
 session_id TEXT NOT NULL CHECK(typeof(session_id)='text' AND length(session_id)>0),
 writer_epoch INTEGER NOT NULL CHECK(typeof(writer_epoch)='integer' AND writer_epoch=1),
 writer_client_id TEXT NOT NULL CHECK(typeof(writer_client_id)='text' AND length(writer_client_id)>0),
 host_instance_ref TEXT NOT NULL CHECK(typeof(host_instance_ref)='text' AND length(host_instance_ref)>0 AND length(host_instance_ref)=17 AND substr(host_instance_ref,1,5)='host-' AND substr(host_instance_ref,6) NOT GLOB '*[^0-9a-f]*'),
 host_generation_ref TEXT NOT NULL CHECK(typeof(host_generation_ref)='text' AND length(host_generation_ref)>0 AND length(host_generation_ref)=71 AND substr(host_generation_ref,1,7)='sha256:' AND substr(host_generation_ref,8) NOT GLOB '*[^0-9a-f]*'),
 connection_instance_ref TEXT NOT NULL CHECK(typeof(connection_instance_ref)='text' AND length(connection_instance_ref)>0 AND length(connection_instance_ref)=36 AND substr(connection_instance_ref,1,4)='nci-' AND substr(connection_instance_ref,5) NOT GLOB '*[^0-9a-f]*'),
 os_subject_ref TEXT NOT NULL CHECK(typeof(os_subject_ref)='text' AND length(os_subject_ref)>0),
 credential_hash TEXT NOT NULL CHECK(typeof(credential_hash)='text' AND length(credential_hash)>0 AND length(credential_hash)=71 AND substr(credential_hash,1,7)='sha256:' AND substr(credential_hash,8) NOT GLOB '*[^0-9a-f]*'),
 attested_at TEXT NOT NULL CHECK(typeof(attested_at)='text' AND length(attested_at)>0),
 attestation_expires_at TEXT NOT NULL CHECK(typeof(attestation_expires_at)='text' AND length(attestation_expires_at)>0),
 created_at TEXT NOT NULL CHECK(typeof(created_at)='text' AND length(created_at)>0),
 origin_body TEXT NOT NULL CHECK(json_valid(origin_body) AND json_type(origin_body)='object'),
 origin_hash TEXT NOT NULL CHECK(length(origin_hash)=71 AND substr(origin_hash,1,7)='sha256:' AND substr(origin_hash,8) NOT GLOB '*[^0-9a-f]*'),
 CHECK(COALESCE(json_type(origin_body,'$.origin_schema')='text' AND json_extract(origin_body,'$.origin_schema')=origin_schema,0)),
 CHECK(COALESCE(json_type(origin_body,'$.schema_version')='integer' AND json_extract(origin_body,'$.schema_version')=schema_version,0)),
 CHECK(COALESCE(json_type(origin_body,'$.attestation_ref')='text' AND json_extract(origin_body,'$.attestation_ref')=attestation_ref,0)),
 CHECK(COALESCE(json_type(origin_body,'$.witness_hash')='text' AND json_extract(origin_body,'$.witness_hash')=witness_hash,0)),
 CHECK(COALESCE(json_type(origin_body,'$.principal')='text' AND json_extract(origin_body,'$.principal')=principal,0)),
 CHECK(COALESCE(json_type(origin_body,'$.authority_root')='text' AND json_extract(origin_body,'$.authority_root')=authority_root,0)),
 CHECK(COALESCE(json_type(origin_body,'$.command_id')='text' AND json_extract(origin_body,'$.command_id')=command_id,0)),
 CHECK(COALESCE(json_type(origin_body,'$.request_hash')='text' AND json_extract(origin_body,'$.request_hash')=request_hash,0)),
 CHECK(COALESCE(json_type(origin_body,'$.request_wire_hash')='text' AND json_extract(origin_body,'$.request_wire_hash')=request_wire_hash,0)),
 CHECK(COALESCE(json_type(origin_body,'$.response_hash')='text' AND json_extract(origin_body,'$.response_hash')=response_hash,0)),
 CHECK(COALESCE(json_type(origin_body,'$.project')='text' AND json_extract(origin_body,'$.project')=project,0)),
 CHECK(COALESCE(json_type(origin_body,'$.session_id')='text' AND json_extract(origin_body,'$.session_id')=session_id,0)),
 CHECK(COALESCE(json_type(origin_body,'$.writer_epoch')='integer' AND json_extract(origin_body,'$.writer_epoch')=writer_epoch,0)),
 CHECK(COALESCE(json_type(origin_body,'$.writer_client_id')='text' AND json_extract(origin_body,'$.writer_client_id')=writer_client_id,0)),
 CHECK(COALESCE(json_type(origin_body,'$.host_instance_ref')='text' AND json_extract(origin_body,'$.host_instance_ref')=host_instance_ref,0)),
 CHECK(COALESCE(json_type(origin_body,'$.host_generation_ref')='text' AND json_extract(origin_body,'$.host_generation_ref')=host_generation_ref,0)),
 CHECK(COALESCE(json_type(origin_body,'$.connection_instance_ref')='text' AND json_extract(origin_body,'$.connection_instance_ref')=connection_instance_ref,0)),
 CHECK(COALESCE(json_type(origin_body,'$.os_subject_ref')='text' AND json_extract(origin_body,'$.os_subject_ref')=os_subject_ref,0)),
 CHECK(COALESCE(json_type(origin_body,'$.credential_hash')='text' AND json_extract(origin_body,'$.credential_hash')=credential_hash,0)),
 CHECK(COALESCE(json_type(origin_body,'$.attested_at')='text' AND json_extract(origin_body,'$.attested_at')=attested_at,0)),
 CHECK(COALESCE(json_type(origin_body,'$.attestation_expires_at')='text' AND json_extract(origin_body,'$.attestation_expires_at')=attestation_expires_at,0)),
 CHECK(COALESCE(json_type(origin_body,'$.created_at')='text' AND json_extract(origin_body,'$.created_at')=created_at,0)),
 PRIMARY KEY(attestation_ref),
 UNIQUE(principal,command_id),
 UNIQUE(project,session_id,writer_epoch),
 FOREIGN KEY(principal,command_id,request_hash) REFERENCES client_command_identities(principal,command_id,request_hash) DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY(session_id) REFERENCES client_sessions(id) DEFERRABLE INITIALLY DEFERRED
);

-- object: native_origin_no_update
CREATE TRIGGER native_origin_no_update BEFORE UPDATE ON client_native_writer_origins BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;

-- object: native_origin_no_delete
CREATE TRIGGER native_origin_no_delete BEFORE DELETE ON client_native_writer_origins BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;

-- object: native_origin_no_replace
CREATE TRIGGER native_origin_no_replace BEFORE INSERT ON client_native_writer_origins WHEN EXISTS(SELECT 1 FROM client_native_writer_origins WHERE attestation_ref=NEW.attestation_ref OR (principal=NEW.principal AND command_id=NEW.command_id) OR (project=NEW.project AND session_id=NEW.session_id AND writer_epoch=NEW.writer_epoch)) BEGIN SELECT RAISE(ABORT,'immutable native writer origin'); END;

-- object: native_origin_receipt_no_insert
CREATE TRIGGER native_origin_receipt_no_insert BEFORE INSERT ON idempotency WHEN CASE WHEN json_valid(NEW.headers) THEN json_extract(NEW.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' OR json_type(NEW.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END BEGIN SELECT RAISE(ABORT,'native receipt must seal existing response'); END;

-- object: native_origin_receipt_no_update
CREATE TRIGGER native_origin_receipt_no_update BEFORE UPDATE ON idempotency WHEN CASE WHEN json_valid(OLD.headers) THEN json_extract(OLD.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' OR json_type(OLD.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;

-- object: native_origin_receipt_no_delete
CREATE TRIGGER native_origin_receipt_no_delete BEFORE DELETE ON idempotency WHEN CASE WHEN json_valid(OLD.headers) THEN json_extract(OLD.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' OR json_type(OLD.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;

-- object: native_origin_receipt_no_replace
CREATE TRIGGER native_origin_receipt_no_replace BEFORE INSERT ON idempotency WHEN EXISTS(SELECT 1 FROM idempotency old WHERE old.principal=NEW.principal AND old.project=NEW.project AND old.operation=NEW.operation AND old.key=NEW.key AND (CASE WHEN json_valid(old.headers) THEN json_extract(old.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' OR json_type(old.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END)) BEGIN SELECT RAISE(ABORT,'immutable native receipt'); END;

-- object: native_origin_receipt_seal
CREATE TRIGGER native_origin_receipt_seal BEFORE UPDATE ON idempotency WHEN CASE WHEN json_valid(NEW.headers) THEN json_extract(NEW.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' OR json_type(NEW.headers,'$.native_create_origin') IS NOT NULL ELSE 0 END BEGIN
 SELECT CASE WHEN NOT COALESCE((COALESCE(json_extract(OLD.headers,'$.schema')='researchos.private-command-envelope.v1',0) AND NEW.principal IS OLD.principal AND NEW.project IS OLD.project AND NEW.operation IS OLD.operation AND NEW.key IS OLD.key AND NEW.request_hash IS OLD.request_hash AND NEW.status IS OLD.status AND NEW.body IS OLD.body AND NEW.created_at IS OLD.created_at AND json_extract(NEW.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' AND json_extract(NEW.headers,'$.encoding')='base64' AND json_extract(NEW.headers,'$.raw_envelope_base64')=json_extract(OLD.headers,'$.raw_envelope_base64') AND json_extract(NEW.headers,'$.native_create_origin.schema_version')=1 AND OLD.operation='v2:session.create' AND json_extract(OLD.body,'$.status')='COMPLETED' AND EXISTS(SELECT 1 FROM client_native_writer_origins o WHERE o.principal=OLD.principal AND o.project=OLD.project AND o.command_id=OLD.key AND o.request_hash=OLD.request_hash AND o.session_id=json_extract(OLD.body,'$.session_id') AND o.session_id=json_extract(OLD.body,'$.result.session_id') AND o.attestation_ref=json_extract(NEW.headers,'$.native_create_origin.attestation_ref') AND o.witness_hash=json_extract(NEW.headers,'$.native_create_origin.witness_hash') AND o.origin_hash=json_extract(NEW.headers,'$.native_create_origin.origin_hash')) AND json_object('schema','researchos.private-command-envelope.v1','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64')) IS OLD.headers AND json_object('schema','researchos.private-command-envelope.native-create.v2','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64'),'native_create_origin',json_object('schema_version',1,'attestation_ref',json_extract(NEW.headers,'$.native_create_origin.attestation_ref'),'witness_hash',json_extract(NEW.headers,'$.native_create_origin.witness_hash'),'origin_hash',json_extract(NEW.headers,'$.native_create_origin.origin_hash'))) IS NEW.headers)  ,0) THEN RAISE(ABORT,'invalid native receipt seal') END;
END;

-- object: idempotency_immutable
CREATE TRIGGER idempotency_immutable BEFORE UPDATE ON idempotency WHEN NOT COALESCE((COALESCE(json_extract(OLD.headers,'$.schema')='researchos.private-command-envelope.v1',0) AND NEW.principal IS OLD.principal AND NEW.project IS OLD.project AND NEW.operation IS OLD.operation AND NEW.key IS OLD.key AND NEW.request_hash IS OLD.request_hash AND NEW.status IS OLD.status AND NEW.body IS OLD.body AND NEW.created_at IS OLD.created_at AND json_extract(NEW.headers,'$.schema')='researchos.private-command-envelope.native-create.v2' AND json_extract(NEW.headers,'$.encoding')='base64' AND json_extract(NEW.headers,'$.raw_envelope_base64')=json_extract(OLD.headers,'$.raw_envelope_base64') AND json_extract(NEW.headers,'$.native_create_origin.schema_version')=1 AND OLD.operation='v2:session.create' AND json_extract(OLD.body,'$.status')='COMPLETED' AND EXISTS(SELECT 1 FROM client_native_writer_origins o WHERE o.principal=OLD.principal AND o.project=OLD.project AND o.command_id=OLD.key AND o.request_hash=OLD.request_hash AND o.session_id=json_extract(OLD.body,'$.session_id') AND o.session_id=json_extract(OLD.body,'$.result.session_id') AND o.attestation_ref=json_extract(NEW.headers,'$.native_create_origin.attestation_ref') AND o.witness_hash=json_extract(NEW.headers,'$.native_create_origin.witness_hash') AND o.origin_hash=json_extract(NEW.headers,'$.native_create_origin.origin_hash')) AND json_object('schema','researchos.private-command-envelope.v1','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64')) IS OLD.headers AND json_object('schema','researchos.private-command-envelope.native-create.v2','encoding','base64','raw_envelope_base64',json_extract(OLD.headers,'$.raw_envelope_base64'),'native_create_origin',json_object('schema_version',1,'attestation_ref',json_extract(NEW.headers,'$.native_create_origin.attestation_ref'),'witness_hash',json_extract(NEW.headers,'$.native_create_origin.witness_hash'),'origin_hash',json_extract(NEW.headers,'$.native_create_origin.origin_hash'))) IS NEW.headers),0) BEGIN SELECT RAISE(ABORT,'immutable replay'); END;
