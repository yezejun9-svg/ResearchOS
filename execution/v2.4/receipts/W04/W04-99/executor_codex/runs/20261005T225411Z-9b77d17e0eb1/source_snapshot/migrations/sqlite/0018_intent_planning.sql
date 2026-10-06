CREATE TABLE intent_plan_bindings (
 project TEXT NOT NULL,
 requirement TEXT NOT NULL,
 submission TEXT NOT NULL,
 actor TEXT NOT NULL,
 raw_hash TEXT NOT NULL,
 accepted_revision INTEGER,
 planning_goal TEXT,
 planning_task TEXT,
 brief_ref TEXT,
 acceptance_ref TEXT,
 compiled_goal TEXT,
 node_mapping TEXT,
 PRIMARY KEY(project, requirement),
 UNIQUE(project, submission),
 UNIQUE(project, requirement, accepted_revision)
);
