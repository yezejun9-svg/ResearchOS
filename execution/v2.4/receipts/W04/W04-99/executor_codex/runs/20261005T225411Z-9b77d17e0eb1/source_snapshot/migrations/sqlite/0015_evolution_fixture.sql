-- Additive W16 development evidence. No automatic migration of populated stores.
CREATE TABLE evolution_hosts(project TEXT PRIMARY KEY,body TEXT NOT NULL);
CREATE TRIGGER evolution_hosts_frozen BEFORE UPDATE ON evolution_hosts BEGIN SELECT RAISE(ABORT,'evolution host registration immutable'); END;
CREATE TABLE evolution_builds(project TEXT NOT NULL,artifact TEXT NOT NULL,body TEXT NOT NULL,PRIMARY KEY(project,artifact));
CREATE TRIGGER evolution_builds_frozen BEFORE UPDATE ON evolution_builds BEGIN SELECT RAISE(ABORT,'evolution build immutable'); END;
CREATE TABLE evolution_candidates(project TEXT NOT NULL,candidate TEXT NOT NULL,creator TEXT NOT NULL,plan_hash TEXT NOT NULL,PRIMARY KEY(project,candidate));
CREATE TABLE evolution_tasks(project TEXT NOT NULL,task TEXT NOT NULL,candidate TEXT NOT NULL,phase TEXT NOT NULL CHECK(phase IN ('REGRESSION','CANARY')),PRIMARY KEY(project,task),UNIQUE(project,candidate,phase));
CREATE TRIGGER evolution_tasks_frozen BEFORE UPDATE ON evolution_tasks BEGIN SELECT RAISE(ABORT,'evolution task binding immutable'); END;
CREATE TRIGGER evolution_tasks_nodelete BEFORE DELETE ON evolution_tasks BEGIN SELECT RAISE(ABORT,'evolution task binding immutable'); END;
CREATE TABLE evolution_executions(project TEXT NOT NULL,candidate TEXT NOT NULL,phase TEXT NOT NULL,run TEXT NOT NULL,epoch INTEGER NOT NULL,state TEXT NOT NULL CHECK(state IN ('RESERVED','RECORDED','FAILED')),body TEXT NOT NULL,receipt_hash TEXT,PRIMARY KEY(project,candidate,phase));
CREATE TRIGGER evolution_execution_final BEFORE UPDATE ON evolution_executions WHEN OLD.state!='RESERVED' BEGIN SELECT RAISE(ABORT,'evolution execution immutable'); END;
CREATE TRIGGER evolution_execution_nodelete BEFORE DELETE ON evolution_executions BEGIN SELECT RAISE(ABORT,'evolution execution immutable'); END;
CREATE TABLE evolution_journal(sequence INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT NOT NULL,candidate TEXT NOT NULL,run TEXT NOT NULL,event TEXT NOT NULL,body TEXT NOT NULL,receipt_hash TEXT NOT NULL);
CREATE TRIGGER evolution_journal_noupdate BEFORE UPDATE ON evolution_journal BEGIN SELECT RAISE(ABORT,'evolution journal append only'); END;
CREATE TRIGGER evolution_journal_nodelete BEFORE DELETE ON evolution_journal BEGIN SELECT RAISE(ABORT,'evolution journal append only'); END;
CREATE TABLE evolution_slots(project TEXT PRIMARY KEY,active_hash TEXT NOT NULL,stable_hash TEXT NOT NULL,candidate TEXT,epoch INTEGER NOT NULL,state TEXT NOT NULL CHECK(state IN ('STABLE','CANARY','RECOVERING')));
CREATE TRIGGER evolution_plan_frozen BEFORE UPDATE ON domain_objects WHEN OLD.kind='SystemCandidate' AND (
json_extract(OLD.body,'$.candidate_artifact_ref') IS NOT json_extract(NEW.body,'$.candidate_artifact_ref') OR
json_extract(OLD.body,'$.stable_artifact_ref') IS NOT json_extract(NEW.body,'$.stable_artifact_ref') OR
json_extract(OLD.body,'$.baseline_suite_ref') IS NOT json_extract(NEW.body,'$.baseline_suite_ref') OR
json_extract(OLD.body,'$.baseline_policy_hash') IS NOT json_extract(NEW.body,'$.baseline_policy_hash') OR
json_extract(OLD.body,'$.changed_paths_manifest_ref') IS NOT json_extract(NEW.body,'$.changed_paths_manifest_ref') OR
json_extract(OLD.body,'$.experiment_id') IS NOT json_extract(NEW.body,'$.experiment_id') OR
json_extract(OLD.body,'$.isolated_workspace_id') IS NOT json_extract(NEW.body,'$.isolated_workspace_id') OR
json_extract(OLD.body,'$.independent_supervisor_id') IS NOT json_extract(NEW.body,'$.independent_supervisor_id') OR
json_extract(OLD.body,'$.migration_plan_ref') IS NOT json_extract(NEW.body,'$.migration_plan_ref') OR
json_extract(OLD.body,'$.rollback_plan_ref') IS NOT json_extract(NEW.body,'$.rollback_plan_ref'))
BEGIN SELECT RAISE(ABORT,'system candidate plan frozen; independent new proposal required'); END;
CREATE TRIGGER evolution_terminal BEFORE UPDATE ON domain_objects WHEN OLD.kind='SystemCandidate' AND json_extract(OLD.body,'$.status') IN ('FROZEN','REJECTED','ROLLED_BACK','PROMOTED') BEGIN SELECT RAISE(ABORT,'system candidate terminal; no implicit retry'); END;
CREATE TRIGGER evolution_no_run_rotation BEFORE UPDATE ON domain_objects WHEN OLD.kind='Task' AND json_extract(NEW.body,'$.active_run_id') IS NOT json_extract(OLD.body,'$.active_run_id') AND EXISTS(SELECT 1 FROM evolution_tasks et JOIN evolution_executions ee ON ee.project=et.project AND ee.candidate=et.candidate AND ee.phase=et.phase WHERE et.project=OLD.project AND et.task=OLD.id) BEGIN SELECT RAISE(ABORT,'reserved evolution phase cannot rotate its run'); END;
