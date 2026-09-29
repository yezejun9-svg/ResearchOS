CREATE TABLE orchestration_contracts (
 project TEXT NOT NULL, task TEXT NOT NULL, contract TEXT NOT NULL CHECK(json_valid(contract)),
 frozen_at TEXT NOT NULL, PRIMARY KEY(project,task)
);
CREATE TRIGGER orchestration_contract_immutable BEFORE UPDATE ON orchestration_contracts BEGIN SELECT RAISE(ABORT,'frozen acceptance contract'); END;
CREATE TRIGGER orchestration_contract_durable BEFORE DELETE ON orchestration_contracts BEGIN SELECT RAISE(ABORT,'frozen acceptance contract'); END;
-- Local test registration is never runtime qualification or LIVE admission.
CREATE TABLE orchestration_fixtures (project TEXT NOT NULL,runtime TEXT NOT NULL, PRIMARY KEY(project,runtime));
CREATE TABLE orchestration_identity (
 principal TEXT PRIMARY KEY REFERENCES auth_principals(id),
 root TEXT NOT NULL REFERENCES auth_principals(id), parent TEXT REFERENCES auth_principals(id)
);
CREATE TRIGGER orchestration_identity_immutable BEFORE UPDATE ON orchestration_identity BEGIN SELECT RAISE(ABORT,'immutable identity'); END;
CREATE TRIGGER orchestration_identity_durable BEFORE DELETE ON orchestration_identity BEGIN SELECT RAISE(ABORT,'durable identity'); END;
CREATE TABLE orchestration_failures (
 project TEXT NOT NULL, key_hash TEXT NOT NULL, reason_hash TEXT NOT NULL, count INTEGER NOT NULL,
 PRIMARY KEY(project,key_hash,reason_hash)
);
CREATE TABLE orchestration_task_controls (
 project TEXT NOT NULL, task TEXT NOT NULL, action TEXT NOT NULL,
 reason TEXT NOT NULL, requested_at TEXT NOT NULL, PRIMARY KEY(project,task)
);
CREATE TABLE orchestration_goal_contracts (
 project TEXT NOT NULL, goal TEXT NOT NULL, contract TEXT NOT NULL CHECK(json_valid(contract)),
 PRIMARY KEY(project,goal)
);
CREATE TRIGGER orchestration_goal_contract_immutable BEFORE UPDATE ON orchestration_goal_contracts BEGIN SELECT RAISE(ABORT,'frozen goal contract'); END;
CREATE TRIGGER orchestration_goal_contract_durable BEFORE DELETE ON orchestration_goal_contracts BEGIN SELECT RAISE(ABORT,'durable goal contract'); END;
CREATE TABLE orchestration_run_dependencies (
 project TEXT NOT NULL, run TEXT NOT NULL, snapshot TEXT NOT NULL CHECK(json_valid(snapshot)),
 PRIMARY KEY(project,run)
);
CREATE TRIGGER orchestration_run_dependencies_immutable BEFORE UPDATE ON orchestration_run_dependencies BEGIN SELECT RAISE(ABORT,'frozen run dependencies'); END;
CREATE TRIGGER orchestration_run_dependencies_durable BEFORE DELETE ON orchestration_run_dependencies BEGIN SELECT RAISE(ABORT,'durable run dependencies'); END;

CREATE TABLE orchestration_rejections (
 correlation_id TEXT PRIMARY KEY, project TEXT NOT NULL, operation TEXT NOT NULL,
 principal TEXT, status INTEGER NOT NULL CHECK(status>=400), code TEXT NOT NULL,
 body_hash TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE TRIGGER orchestration_rejections_immutable BEFORE UPDATE ON orchestration_rejections BEGIN SELECT RAISE(ABORT,'immutable rejected gate audit'); END;
CREATE TRIGGER orchestration_rejections_durable BEFORE DELETE ON orchestration_rejections BEGIN SELECT RAISE(ABORT,'durable rejected gate audit'); END;
