-- W08-02: one durable coalesced trigger per project. The active cycle's frozen
-- window is unchanged; a later cycle consumes this pending window atomically.
-- This is private scheduling state, not an extension of ResearchCycle's schema.
CREATE TABLE research_pending_windows (
  project TEXT PRIMARY KEY,
  active_cycle TEXT NOT NULL,
  profile_revision INTEGER NOT NULL CHECK (profile_revision >= 1),
  trigger TEXT NOT NULL CHECK (trigger IN ('USER', 'SCHEDULE')),
  window_from TEXT NOT NULL,
  window_to TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
