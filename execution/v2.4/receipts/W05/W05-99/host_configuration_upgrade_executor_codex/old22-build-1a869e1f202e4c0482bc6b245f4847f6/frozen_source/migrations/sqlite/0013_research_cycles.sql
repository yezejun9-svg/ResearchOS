CREATE UNIQUE INDEX IF NOT EXISTS research_one_active_cycle
ON domain_objects(project)
WHERE kind='ResearchCycle' AND json_extract(body,'$.status') IN ('PLANNED','RUNNING');

CREATE TABLE IF NOT EXISTS research_candidate_reviews (
  project TEXT NOT NULL,
  cycle_id TEXT NOT NULL,
  evidence_id TEXT NOT NULL,
  profile_revision INTEGER NOT NULL,
  context_target TEXT NOT NULL,
  outcome TEXT NOT NULL CHECK(outcome IN ('REJECT','WATCH','INCONCLUSIVE','ADOPT')),
  reason TEXT NOT NULL CHECK(length(reason)>0),
  missing_evidence TEXT,
  revisit_trigger TEXT,
  origin_summary_json TEXT NOT NULL CHECK(json_valid(origin_summary_json)),
  created_at TEXT NOT NULL,
  PRIMARY KEY(project,cycle_id,evidence_id),
  CHECK(outcome NOT IN ('WATCH','INCONCLUSIVE') OR
    (length(missing_evidence)>0 AND length(revisit_trigger)>0))
);
