-- Private S1 authority; populated stores are never migrated implicitly.
CREATE TABLE runtime_bindings (
    project TEXT NOT NULL, runtime TEXT NOT NULL,
    profile_ref TEXT NOT NULL, profile_hash TEXT NOT NULL,
    technical_hash TEXT NOT NULL, owner TEXT NOT NULL,
    PRIMARY KEY(project,runtime)
);
CREATE TRIGGER runtime_bindings_frozen BEFORE UPDATE ON runtime_bindings BEGIN SELECT RAISE(ABORT,'runtime binding immutable'); END;
CREATE TABLE runtime_qualification_plans (
    project TEXT NOT NULL, task TEXT NOT NULL, runtime TEXT NOT NULL,
    plan TEXT NOT NULL, plan_hash TEXT NOT NULL,
    author TEXT NOT NULL, author_root TEXT NOT NULL,
    PRIMARY KEY(project,task)
);
CREATE TRIGGER runtime_qualification_plans_frozen BEFORE UPDATE ON runtime_qualification_plans BEGIN SELECT RAISE(ABORT,'runtime plan immutable'); END;
CREATE TABLE runtime_qualification_runs (
    project TEXT NOT NULL, task TEXT NOT NULL, run TEXT NOT NULL,
    runtime TEXT NOT NULL, epoch INTEGER NOT NULL,
    plan_hash TEXT NOT NULL, profile_hash TEXT NOT NULL,
    contract_hash TEXT NOT NULL, input_hash TEXT NOT NULL,
    context_bundle TEXT NOT NULL, owner_root TEXT NOT NULL,
    PRIMARY KEY(project,task), UNIQUE(project,run)
);
CREATE TRIGGER runtime_qualification_runs_frozen BEFORE UPDATE ON runtime_qualification_runs BEGIN SELECT RAISE(ABORT,'runtime qualification marker immutable'); END;
CREATE TABLE runtime_qualification_approvals (
    project TEXT NOT NULL, runtime TEXT NOT NULL, revision INTEGER NOT NULL,
    qualification_hash TEXT NOT NULL, run TEXT NOT NULL,
    receipt_ref TEXT NOT NULL, approved_at TEXT NOT NULL,
    PRIMARY KEY(project,runtime,revision)
);
CREATE TRIGGER runtime_qualification_approvals_frozen BEFORE UPDATE ON runtime_qualification_approvals BEGIN SELECT RAISE(ABORT,'runtime approval immutable'); END;
