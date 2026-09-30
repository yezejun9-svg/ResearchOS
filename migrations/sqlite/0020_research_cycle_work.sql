-- Private monitor and stage relations. Task/Run/Experiment remain the state machines.
ALTER TABLE intent_plan_bindings ADD COLUMN plan_kind TEXT NOT NULL DEFAULT 'DELIVERY'
 CHECK(plan_kind IN ('DELIVERY','MONITOR'));
ALTER TABLE intent_plan_bindings ADD COLUMN monitor_current INTEGER NOT NULL DEFAULT 0
 CHECK(typeof(monitor_current)='integer' AND monitor_current IN (0,1));
ALTER TABLE intent_plan_bindings ADD COLUMN monitor_started_at TEXT;
ALTER TABLE intent_plan_bindings ADD COLUMN monitor_progress_id TEXT;
CREATE UNIQUE INDEX research_one_current_monitor ON intent_plan_bindings(project) WHERE monitor_current=1;

CREATE TRIGGER research_monitor_insert BEFORE INSERT ON intent_plan_bindings BEGIN
 SELECT CASE WHEN NEW.plan_kind!='DELIVERY' OR NEW.monitor_current!=0 OR NEW.monitor_started_at IS NOT NULL OR NEW.monitor_progress_id IS NOT NULL
 THEN RAISE(ABORT,'monitor requires accepted plan transition') END;
 SELECT CASE WHEN EXISTS(SELECT 1 FROM intent_plan_bindings WHERE project=NEW.project AND (requirement=NEW.requirement OR submission=NEW.submission))
 THEN RAISE(ABORT,'intent binding cannot be replaced') END;
END;
CREATE TRIGGER research_monitor_update BEFORE UPDATE ON intent_plan_bindings BEGIN
 SELECT CASE WHEN NEW.project IS NOT OLD.project OR NEW.requirement IS NOT OLD.requirement OR NEW.submission IS NOT OLD.submission OR NEW.actor IS NOT OLD.actor OR NEW.raw_hash IS NOT OLD.raw_hash
 THEN RAISE(ABORT,'immutable intent identity') END;
 SELECT CASE WHEN OLD.monitor_started_at IS NOT NULL AND (NEW.plan_kind IS NOT OLD.plan_kind OR NEW.monitor_started_at IS NOT OLD.monitor_started_at OR NEW.monitor_progress_id IS NOT OLD.monitor_progress_id OR NEW.compiled_goal IS NOT OLD.compiled_goal OR NEW.brief_ref IS NOT OLD.brief_ref OR NEW.acceptance_ref IS NOT OLD.acceptance_ref OR NEW.accepted_revision IS NOT OLD.accepted_revision OR NEW.planning_goal IS NOT OLD.planning_goal OR NEW.planning_task IS NOT OLD.planning_task OR NEW.monitor_current>OLD.monitor_current)
 THEN RAISE(ABORT,'immutable monitor authorization') END;
 SELECT CASE WHEN NEW.plan_kind='MONITOR' AND (NEW.monitor_started_at IS NULL OR NEW.monitor_progress_id IS NULL OR NEW.compiled_goal IS NULL OR NEW.brief_ref IS NULL OR NEW.acceptance_ref IS NULL OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='Goal' AND id=NEW.compiled_goal) OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='NoProgressRecord' AND id=NEW.monitor_progress_id))
 THEN RAISE(ABORT,'monitor needs goal, accepted plan and progress binding') END;
 SELECT CASE WHEN NEW.plan_kind='DELIVERY' AND (NEW.monitor_current!=0 OR NEW.monitor_started_at IS NOT NULL OR NEW.monitor_progress_id IS NOT NULL)
 THEN RAISE(ABORT,'delivery cannot act as monitor') END;
END;
CREATE TRIGGER research_monitor_no_delete BEFORE DELETE ON intent_plan_bindings
BEGIN SELECT RAISE(ABORT,'durable intent binding'); END;

CREATE TABLE research_cycle_work (
 project TEXT NOT NULL,
 cycle TEXT NOT NULL,
 logical_key TEXT NOT NULL CHECK(length(logical_key)>0),
 plan_ref TEXT NOT NULL CHECK(json_valid(plan_ref) AND json_type(plan_ref)='object'),
 stage TEXT NOT NULL CHECK(stage IN ('discovery','verification','experiment','review','delivery','follow_up')),
 task TEXT NOT NULL,
 experiment TEXT,
 source_id TEXT,
 evidence_id TEXT,
 input_refs TEXT NOT NULL CHECK(json_valid(input_refs) AND json_type(input_refs)='array'),
 input_hash TEXT NOT NULL CHECK(length(input_hash)>0),
	parameters TEXT NOT NULL CHECK(json_valid(parameters) AND json_type(parameters)='object'),
 window_from TEXT,
 window_to TEXT,
 progress_record_id TEXT,
 source_receipt TEXT CHECK(source_receipt IS NULL OR (json_valid(source_receipt) AND json_type(source_receipt)='object')),
 created_at TEXT NOT NULL,
 PRIMARY KEY(project,cycle,logical_key),
 UNIQUE(project,cycle,task),
 CHECK((window_from IS NULL)=(window_to IS NULL)),
 CHECK(stage='discovery' OR source_receipt IS NULL)
);
CREATE INDEX research_work_task ON research_cycle_work(project,task);
CREATE TRIGGER research_work_insert BEFORE INSERT ON research_cycle_work BEGIN
 SELECT CASE WHEN EXISTS(SELECT 1 FROM research_cycle_work WHERE project=NEW.project AND cycle=NEW.cycle AND (logical_key=NEW.logical_key OR task=NEW.task))
 THEN RAISE(ABORT,'research work cannot be replaced') END;
 SELECT CASE WHEN NEW.source_receipt IS NOT NULL THEN RAISE(ABORT,'source receipt must follow real capture') END;
 SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='ResearchCycle' AND id=NEW.cycle)
 OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='Task' AND id=NEW.task)
 OR (NEW.experiment IS NOT NULL AND NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='Experiment' AND id=NEW.experiment))
 OR (NEW.progress_record_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='NoProgressRecord' AND id=NEW.progress_record_id))
 THEN RAISE(ABORT,'research work needs existing domain objects') END;
END;
CREATE TRIGGER research_work_update BEFORE UPDATE ON research_cycle_work BEGIN
 SELECT CASE WHEN NEW.project IS NOT OLD.project OR NEW.cycle IS NOT OLD.cycle OR NEW.logical_key IS NOT OLD.logical_key OR NEW.plan_ref IS NOT OLD.plan_ref OR NEW.stage IS NOT OLD.stage OR NEW.task IS NOT OLD.task OR NEW.experiment IS NOT OLD.experiment OR NEW.source_id IS NOT OLD.source_id OR NEW.evidence_id IS NOT OLD.evidence_id OR NEW.input_refs IS NOT OLD.input_refs OR NEW.input_hash IS NOT OLD.input_hash OR NEW.parameters IS NOT OLD.parameters OR NEW.window_from IS NOT OLD.window_from OR NEW.window_to IS NOT OLD.window_to OR NEW.progress_record_id IS NOT OLD.progress_record_id OR NEW.created_at IS NOT OLD.created_at
 THEN RAISE(ABORT,'immutable research work mapping') END;
 SELECT CASE WHEN OLD.source_receipt IS NOT NULL AND NEW.source_receipt IS NOT OLD.source_receipt
 THEN RAISE(ABORT,'immutable source receipt') END;
 SELECT CASE WHEN NEW.source_receipt IS NOT NULL AND (
 json_type(NEW.source_receipt,'$.epoch') IS NOT 'integer' OR json_extract(NEW.source_receipt,'$.epoch')<1
 OR json_extract(NEW.source_receipt,'$.project_id') IS NOT NEW.project
 OR json_extract(NEW.source_receipt,'$.task_id') IS NOT NEW.task
 OR json_type(NEW.source_receipt,'$.effect_key') IS NOT 'text'
 OR json_type(NEW.source_receipt,'$.request_hash') IS NOT 'text'
 OR json_type(NEW.source_receipt,'$.reservation_id') IS NOT 'text'
 OR json_type(NEW.source_receipt,'$.manifest_ref') IS NOT 'object'
 OR json_type(NEW.source_receipt,'$.cursor_before_ref') IS NOT 'object'
 OR json_type(NEW.source_receipt,'$.cursor_after_ref') IS NOT 'object'
 OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='Run' AND id=json_extract(NEW.source_receipt,'$.run_id') AND json_extract(body,'$.task_id')=NEW.task)
 OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='BudgetLedgerEntry' AND id=json_extract(NEW.source_receipt,'$.reservation_id')))
 THEN RAISE(ABORT,'bound source receipt required') END;
END;
CREATE TRIGGER research_work_no_delete BEFORE DELETE ON research_cycle_work
BEGIN SELECT RAISE(ABORT,'durable research work'); END;

ALTER TABLE research_candidate_reviews ADD COLUMN reviewer_id TEXT;
ALTER TABLE research_candidate_reviews ADD COLUMN review_task_ref TEXT;
ALTER TABLE research_candidate_reviews ADD COLUMN acceptance_ref TEXT;
-- Existing manual reviews stay legacy annotations. New driver completion requires
-- all three bindings and rechecks their current authority, inputs and receipts.
CREATE TRIGGER research_review_no_replace BEFORE INSERT ON research_candidate_reviews
WHEN EXISTS(SELECT 1 FROM research_candidate_reviews WHERE project=NEW.project AND cycle_id=NEW.cycle_id AND evidence_id=NEW.evidence_id)
BEGIN SELECT RAISE(ABORT,'candidate review cannot be replaced'); END;
CREATE TRIGGER research_review_bound_insert BEFORE INSERT ON research_candidate_reviews
WHEN NEW.reviewer_id IS NOT NULL OR NEW.review_task_ref IS NOT NULL OR NEW.acceptance_ref IS NOT NULL BEGIN
 SELECT CASE WHEN NEW.reviewer_id IS NULL OR NEW.review_task_ref IS NULL OR NEW.acceptance_ref IS NULL
 OR NOT json_valid(NEW.review_task_ref) OR NOT json_valid(NEW.acceptance_ref)
 OR json_type(NEW.review_task_ref,'$.revision') IS NOT 'integer'
 OR json_type(NEW.acceptance_ref,'$.revision') IS NOT 'integer'
 OR json_extract(NEW.review_task_ref,'$.entity_type') IS NOT 'Task'
 OR json_extract(NEW.acceptance_ref,'$.entity_type') IS NOT 'AcceptanceReceipt'
 OR NOT EXISTS(SELECT 1 FROM research_cycle_work w WHERE w.project=NEW.project AND w.cycle=NEW.cycle_id AND w.stage='review' AND w.evidence_id=NEW.evidence_id AND w.task=json_extract(NEW.review_task_ref,'$.id'))
 OR NOT EXISTS(SELECT 1 FROM domain_objects WHERE project=NEW.project AND kind='AcceptanceReceipt' AND id=json_extract(NEW.acceptance_ref,'$.id') AND json_extract(body,'$.verifier_principal_id')=NEW.reviewer_id)
 THEN RAISE(ABORT,'bound current review required') END;
END;
CREATE TRIGGER research_review_immutable BEFORE UPDATE ON research_candidate_reviews
BEGIN SELECT RAISE(ABORT,'immutable candidate review'); END;
CREATE TRIGGER research_review_no_delete BEFORE DELETE ON research_candidate_reviews
BEGIN SELECT RAISE(ABORT,'durable candidate review'); END;
