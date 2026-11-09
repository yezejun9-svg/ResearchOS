CREATE TABLE experiment_tasks(project TEXT NOT NULL, experiment TEXT NOT NULL, task TEXT NOT NULL, bound_at TEXT NOT NULL, PRIMARY KEY(project,experiment,task));
CREATE TABLE experiment_runs(project TEXT NOT NULL, experiment TEXT NOT NULL, run TEXT NOT NULL, started_at TEXT NOT NULL, preregistration_hash TEXT NOT NULL, PRIMARY KEY(project,experiment,run));
CREATE TRIGGER experiment_frozen BEFORE UPDATE ON domain_objects
WHEN OLD.kind='Experiment' AND json_extract(OLD.body,'$.status')!='DRAFT' AND (
 json_extract(OLD.body,'$.preregistration_hash') IS NOT json_extract(NEW.body,'$.preregistration_hash') OR
 json_extract(OLD.body,'$.candidate_ref') IS NOT json_extract(NEW.body,'$.candidate_ref') OR
 json_extract(OLD.body,'$.baseline_refs') IS NOT json_extract(NEW.body,'$.baseline_refs') OR
 json_extract(OLD.body,'$.input_refs') IS NOT json_extract(NEW.body,'$.input_refs') OR
 json_extract(OLD.body,'$.metrics') IS NOT json_extract(NEW.body,'$.metrics') OR
 json_extract(OLD.body,'$.acceptance_contract') IS NOT json_extract(NEW.body,'$.acceptance_contract') OR
 json_extract(OLD.body,'$.stop_policy') IS NOT json_extract(NEW.body,'$.stop_policy') OR
 json_extract(OLD.body,'$.budget_policy_id') IS NOT json_extract(NEW.body,'$.budget_policy_id'))
BEGIN SELECT RAISE(ABORT,'experiment preregistration is immutable'); END;
CREATE TRIGGER experiment_terminal BEFORE UPDATE ON domain_objects
WHEN OLD.kind='Experiment' AND json_extract(OLD.body,'$.status') IN ('COMPLETED','INCONCLUSIVE','CANCELLED')
BEGIN SELECT RAISE(ABORT,'experiment terminal result is immutable'); END;
