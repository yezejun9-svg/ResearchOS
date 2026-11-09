-- Dedicated source only: not a numbered migration and never automatically installed.
-- Existing canonical domain_objects are required. This schema supplies integrity, not authority.
CREATE TABLE coding_delivery_bindings (
 binding_schema TEXT NOT NULL CHECK(length(trim(binding_schema,char(9)||char(10)||char(13)||' '))>0 AND instr(binding_schema,char(0))=0 AND binding_schema='researchos.coding-delivery-binding.v1'),
 schema_version INTEGER NOT NULL CHECK(typeof(schema_version)='integer' AND schema_version=1),
 project TEXT NOT NULL CHECK(length(trim(project,char(9)||char(10)||char(13)||' '))>0 AND instr(project,char(0))=0),
 goal_id TEXT NOT NULL CHECK(length(trim(goal_id,char(9)||char(10)||char(13)||' '))>0 AND instr(goal_id,char(0))=0),
 task_id TEXT NOT NULL CHECK(length(trim(task_id,char(9)||char(10)||char(13)||' '))>0 AND instr(task_id,char(0))=0),
 approval_issuer_ref TEXT NOT NULL CHECK(length(trim(approval_issuer_ref,char(9)||char(10)||char(13)||' '))>0 AND instr(approval_issuer_ref,char(0))=0),
 approval_ref TEXT NOT NULL CHECK(length(trim(approval_ref,char(9)||char(10)||char(13)||' '))>0 AND instr(approval_ref,char(0))=0),
 lineage_issuer_ref TEXT NOT NULL CHECK(length(trim(lineage_issuer_ref,char(9)||char(10)||char(13)||' '))>0 AND instr(lineage_issuer_ref,char(0))=0),
 business_anchor TEXT NOT NULL CHECK(length(business_anchor)=71 AND substr(business_anchor,1,7)='sha256:' AND substr(business_anchor,8) NOT GLOB '*[^0-9a-f]*' AND instr(business_anchor,char(0))=0),
 owner_principal TEXT NOT NULL CHECK(length(trim(owner_principal,char(9)||char(10)||char(13)||' '))>0 AND instr(owner_principal,char(0))=0),
 owner_root TEXT NOT NULL CHECK(length(trim(owner_root,char(9)||char(10)||char(13)||' '))>0 AND instr(owner_root,char(0))=0),
 owner_host TEXT NOT NULL CHECK(length(trim(owner_host,char(9)||char(10)||char(13)||' '))>0 AND instr(owner_host,char(0))=0),
 task_contract_hash TEXT NOT NULL CHECK(length(task_contract_hash)=71 AND substr(task_contract_hash,1,7)='sha256:' AND substr(task_contract_hash,8) NOT GLOB '*[^0-9a-f]*' AND instr(task_contract_hash,char(0))=0),
 goal_contract_hash TEXT NOT NULL CHECK(length(goal_contract_hash)=71 AND substr(goal_contract_hash,1,7)='sha256:' AND substr(goal_contract_hash,8) NOT GLOB '*[^0-9a-f]*' AND instr(goal_contract_hash,char(0))=0),
 binding_body TEXT NOT NULL CHECK(json_valid(binding_body) AND json_type(binding_body) IS 'object' AND length(CAST(binding_body AS BLOB))<=65536),
 binding_hash TEXT NOT NULL CHECK(length(binding_hash)=71 AND substr(binding_hash,1,7)='sha256:' AND substr(binding_hash,8) NOT GLOB '*[^0-9a-f]*' AND instr(binding_hash,char(0))=0),
 goal_subject_kind TEXT GENERATED ALWAYS AS ('Goal') VIRTUAL,
 task_subject_kind TEXT GENERATED ALWAYS AS ('Task') VIRTUAL,
 PRIMARY KEY(project,task_id),
 FOREIGN KEY(project,goal_subject_kind,goal_id) REFERENCES domain_objects(project,kind,id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 FOREIGN KEY(project,task_subject_kind,task_id) REFERENCES domain_objects(project,kind,id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 CHECK(task_contract_hash<>goal_contract_hash),
 CHECK(json_type(binding_body,'$.binding_schema') IS 'text' AND json_extract(binding_body,'$.binding_schema') IS binding_schema),
 CHECK(json_type(binding_body,'$.schema_version') IS 'integer' AND json_extract(binding_body,'$.schema_version') IS schema_version AND typeof(json_extract(binding_body,'$.schema_version'))='integer'),
 CHECK(json_type(binding_body,'$.project') IS 'text' AND json_extract(binding_body,'$.project') IS project),
 CHECK(json_type(binding_body,'$.goal_id') IS 'text' AND json_extract(binding_body,'$.goal_id') IS goal_id),
 CHECK(json_type(binding_body,'$.task_id') IS 'text' AND json_extract(binding_body,'$.task_id') IS task_id),
 CHECK(json_type(binding_body,'$.approval_issuer_ref') IS 'text' AND json_extract(binding_body,'$.approval_issuer_ref') IS approval_issuer_ref),
 CHECK(json_type(binding_body,'$.approval_ref') IS 'text' AND json_extract(binding_body,'$.approval_ref') IS approval_ref),
 CHECK(json_type(binding_body,'$.lineage_issuer_ref') IS 'text' AND json_extract(binding_body,'$.lineage_issuer_ref') IS lineage_issuer_ref),
 CHECK(json_type(binding_body,'$.business_anchor') IS 'text' AND json_extract(binding_body,'$.business_anchor') IS business_anchor),
 CHECK(json_type(binding_body,'$.owner_principal') IS 'text' AND json_extract(binding_body,'$.owner_principal') IS owner_principal),
 CHECK(json_type(binding_body,'$.owner_root') IS 'text' AND json_extract(binding_body,'$.owner_root') IS owner_root),
 CHECK(json_type(binding_body,'$.owner_host') IS 'text' AND json_extract(binding_body,'$.owner_host') IS owner_host),
 CHECK(json_type(binding_body,'$.task_contract_hash') IS 'text' AND json_extract(binding_body,'$.task_contract_hash') IS task_contract_hash),
 CHECK(json_type(binding_body,'$.goal_contract_hash') IS 'text' AND json_extract(binding_body,'$.goal_contract_hash') IS goal_contract_hash),
 CHECK(json_type(binding_body,'$.parent_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.parent_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.parent_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.parent_confirmation_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.parent_confirmation_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.parent_confirmation_hash'),char(0))=0 AND length(json_extract(binding_body,'$.parent_confirmation_hash'))=71 AND substr(json_extract(binding_body,'$.parent_confirmation_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.parent_confirmation_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.parent_confirmation_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.creation_method') IS 'text' AND length(trim(json_extract(binding_body,'$.creation_method'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.creation_method'),char(0))=0 AND json_extract(binding_body,'$.creation_method')='goal.start'),
 CHECK(json_type(binding_body,'$.client_id') IS 'text' AND length(trim(json_extract(binding_body,'$.client_id'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.client_id'),char(0))=0),
 CHECK(json_type(binding_body,'$.command_id') IS 'text' AND length(trim(json_extract(binding_body,'$.command_id'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.command_id'),char(0))=0),
 CHECK(json_type(binding_body,'$.request_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.request_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.request_hash'),char(0))=0 AND length(json_extract(binding_body,'$.request_hash'))=71 AND substr(json_extract(binding_body,'$.request_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.request_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.request_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.session_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.session_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.session_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.workspace_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.workspace_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.workspace_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.workspace_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.workspace_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.workspace_hash'),char(0))=0 AND length(json_extract(binding_body,'$.workspace_hash'))=71 AND substr(json_extract(binding_body,'$.workspace_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.workspace_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.workspace_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.profile_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.profile_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.profile_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.profile_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.profile_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.profile_hash'),char(0))=0 AND length(json_extract(binding_body,'$.profile_hash'))=71 AND substr(json_extract(binding_body,'$.profile_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.profile_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.profile_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.policy_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.policy_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.policy_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.policy_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.policy_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.policy_hash'),char(0))=0 AND length(json_extract(binding_body,'$.policy_hash'))=71 AND substr(json_extract(binding_body,'$.policy_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.policy_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.policy_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.suite_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.suite_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.suite_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.suite_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.suite_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.suite_hash'),char(0))=0 AND length(json_extract(binding_body,'$.suite_hash'))=71 AND substr(json_extract(binding_body,'$.suite_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.suite_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.suite_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.approved_plan_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.approved_plan_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.approved_plan_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.approved_plan_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.approved_plan_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.approved_plan_hash'),char(0))=0 AND length(json_extract(binding_body,'$.approved_plan_hash'))=71 AND substr(json_extract(binding_body,'$.approved_plan_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.approved_plan_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.approved_plan_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.requirement_refs_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.requirement_refs_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.requirement_refs_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.requirement_refs_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.requirement_refs_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.requirement_refs_hash'),char(0))=0 AND length(json_extract(binding_body,'$.requirement_refs_hash'))=71 AND substr(json_extract(binding_body,'$.requirement_refs_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.requirement_refs_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.requirement_refs_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.input_refs_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.input_refs_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.input_refs_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.input_refs_hash') IS 'text' AND length(trim(json_extract(binding_body,'$.input_refs_hash'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.input_refs_hash'),char(0))=0 AND length(json_extract(binding_body,'$.input_refs_hash'))=71 AND substr(json_extract(binding_body,'$.input_refs_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.input_refs_hash'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.input_refs_hash'),char(0))=0),
 CHECK(json_type(binding_body,'$.origin_problem_id') IS 'text' AND length(trim(json_extract(binding_body,'$.origin_problem_id'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.origin_problem_id'),char(0))=0),
 CHECK(json_type(binding_body,'$.candidate_id') IS 'text' AND length(trim(json_extract(binding_body,'$.candidate_id'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.candidate_id'),char(0))=0),
 CHECK(json_type(binding_body,'$.no_progress_ref') IS 'text' AND length(trim(json_extract(binding_body,'$.no_progress_ref'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.no_progress_ref'),char(0))=0),
 CHECK(json_type(binding_body,'$.no_progress_input_key') IS 'text' AND length(trim(json_extract(binding_body,'$.no_progress_input_key'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.no_progress_input_key'),char(0))=0 AND length(json_extract(binding_body,'$.no_progress_input_key'))=71 AND substr(json_extract(binding_body,'$.no_progress_input_key'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.no_progress_input_key'),8) NOT GLOB '*[^0-9a-f]*' AND instr(json_extract(binding_body,'$.no_progress_input_key'),char(0))=0),
 CHECK(json_type(binding_body,'$.creation_writer_epoch') IS 'text' AND length(trim(json_extract(binding_body,'$.creation_writer_epoch'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.creation_writer_epoch'),char(0))=0 AND length(json_extract(binding_body,'$.creation_writer_epoch')) BETWEEN 1 AND 19 AND substr(json_extract(binding_body,'$.creation_writer_epoch'),1,1) BETWEEN '1' AND '9' AND json_extract(binding_body,'$.creation_writer_epoch') NOT GLOB '*[^0-9]*' AND (length(json_extract(binding_body,'$.creation_writer_epoch'))<19 OR json_extract(binding_body,'$.creation_writer_epoch')<='9223372036854775807' COLLATE BINARY)),
 CHECK(json_type(binding_body,'$.creation_session_revision') IS 'text' AND length(trim(json_extract(binding_body,'$.creation_session_revision'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.creation_session_revision'),char(0))=0 AND length(json_extract(binding_body,'$.creation_session_revision')) BETWEEN 1 AND 19 AND substr(json_extract(binding_body,'$.creation_session_revision'),1,1) BETWEEN '1' AND '9' AND json_extract(binding_body,'$.creation_session_revision') NOT GLOB '*[^0-9]*' AND (length(json_extract(binding_body,'$.creation_session_revision'))<19 OR json_extract(binding_body,'$.creation_session_revision')<='9223372036854775807' COLLATE BINARY))
,
 CHECK(json_type(binding_body,'$.original_problem_anchor') IS 'text' AND length(trim(json_extract(binding_body,'$.original_problem_anchor'),char(9)||char(10)||char(13)||' '))>0 AND instr(json_extract(binding_body,'$.original_problem_anchor'),char(0))=0),
 CHECK(json_type(binding_body,'$.requirement_content_hash') IS 'text' AND length(json_extract(binding_body,'$.requirement_content_hash'))=71 AND substr(json_extract(binding_body,'$.requirement_content_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.requirement_content_hash'),8) NOT GLOB '*[^0-9a-f]*'),
 CHECK(json_type(binding_body,'$.business_input_content_hash') IS 'text' AND length(json_extract(binding_body,'$.business_input_content_hash'))=71 AND substr(json_extract(binding_body,'$.business_input_content_hash'),1,7)='sha256:' AND substr(json_extract(binding_body,'$.business_input_content_hash'),8) NOT GLOB '*[^0-9a-f]*')
) STRICT, WITHOUT ROWID;
CREATE UNIQUE INDEX coding_delivery_goal_unique ON coding_delivery_bindings(project,goal_id);
CREATE UNIQUE INDEX coding_delivery_approval_unique ON coding_delivery_bindings(approval_issuer_ref,approval_ref);
CREATE UNIQUE INDEX coding_delivery_lineage_unique ON coding_delivery_bindings(lineage_issuer_ref,business_anchor);
CREATE TRIGGER coding_delivery_insert_conflict BEFORE INSERT ON coding_delivery_bindings
WHEN EXISTS(SELECT 1 FROM coding_delivery_bindings b WHERE
 (b.project=NEW.project AND (b.task_id=NEW.task_id OR b.goal_id=NEW.goal_id)) OR
 (b.approval_issuer_ref=NEW.approval_issuer_ref AND b.approval_ref=NEW.approval_ref) OR
 (b.lineage_issuer_ref=NEW.lineage_issuer_ref AND b.business_anchor=NEW.business_anchor))
BEGIN SELECT RAISE(ABORT,'immutable binding identity already occupied'); END;
CREATE TRIGGER coding_delivery_closed_body BEFORE INSERT ON coding_delivery_bindings
WHEN (SELECT count(*) FROM json_each(NEW.binding_body))<>44 OR
 EXISTS(SELECT 1 FROM json_each(NEW.binding_body) WHERE key NOT IN ('original_problem_anchor','requirement_content_hash','business_input_content_hash','schema_version','binding_schema','project','goal_id','task_id','approval_issuer_ref','approval_ref','lineage_issuer_ref','business_anchor','owner_principal','owner_root','owner_host','task_contract_hash','goal_contract_hash','parent_ref','parent_confirmation_hash','creation_method','client_id','command_id','request_hash','session_ref','workspace_ref','workspace_hash','profile_ref','profile_hash','policy_ref','policy_hash','suite_ref','suite_hash','approved_plan_ref','approved_plan_hash','requirement_refs_ref','requirement_refs_hash','input_refs_ref','input_refs_hash','origin_problem_id','candidate_id','no_progress_ref','no_progress_input_key','creation_writer_epoch','creation_session_revision')) OR
 EXISTS(SELECT 1 FROM json_each(NEW.binding_body) GROUP BY key HAVING count(*)<>1)
BEGIN SELECT RAISE(ABORT,'closed unique-key coding delivery binding body required'); END;
CREATE TRIGGER coding_delivery_subject_relation BEFORE INSERT ON coding_delivery_bindings
WHEN NOT EXISTS(SELECT 1 FROM domain_objects t JOIN domain_objects g ON g.project=t.project AND g.kind='Goal' AND g.id=NEW.goal_id
 WHERE t.project=NEW.project AND t.kind='Task' AND t.id=NEW.task_id
 AND json_extract(t.body,'$.project_id') IS NEW.project AND json_extract(t.body,'$.id') IS NEW.task_id
 AND json_extract(t.body,'$.goal_id') IS NEW.goal_id
 AND json_extract(g.body,'$.project_id') IS NEW.project AND json_extract(g.body,'$.id') IS NEW.goal_id)
BEGIN SELECT RAISE(ABORT,'canonical Task/Goal relation missing'); END;
CREATE TRIGGER coding_delivery_no_update BEFORE UPDATE ON coding_delivery_bindings
BEGIN SELECT RAISE(ABORT,'coding delivery binding is immutable'); END;
CREATE TRIGGER coding_delivery_no_delete BEFORE DELETE ON coding_delivery_bindings
BEGIN SELECT RAISE(ABORT,'coding delivery binding cannot be deleted'); END;
