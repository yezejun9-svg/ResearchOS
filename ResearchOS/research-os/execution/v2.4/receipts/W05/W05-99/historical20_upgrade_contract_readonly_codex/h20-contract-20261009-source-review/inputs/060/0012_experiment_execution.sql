CREATE TABLE experiment_executions(project TEXT NOT NULL, experiment TEXT NOT NULL, run TEXT NOT NULL, epoch INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('RESERVED','RECORDED','FAILED')), body TEXT NOT NULL, receipt_hash TEXT, PRIMARY KEY(project,experiment,run,epoch));
CREATE TRIGGER experiment_execution_final BEFORE UPDATE ON experiment_executions WHEN OLD.state!='RESERVED' BEGIN SELECT RAISE(ABORT,'experiment execution evidence immutable'); END;
CREATE TRIGGER experiment_execution_no_delete BEFORE DELETE ON experiment_executions BEGIN SELECT RAISE(ABORT,'experiment execution evidence immutable'); END;
CREATE UNIQUE INDEX experiment_task_single ON experiment_tasks(project,task);
CREATE TABLE evaluation_native_tools(project TEXT NOT NULL, content_hash TEXT NOT NULL, registered_at TEXT NOT NULL, PRIMARY KEY(project,content_hash));
