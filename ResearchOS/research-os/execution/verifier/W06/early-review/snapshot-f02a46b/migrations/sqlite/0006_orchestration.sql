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
