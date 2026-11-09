# C57 directory contract

- `internal/qualificationmaintenancejournal/`: pure immutable journal grammar and Windows native reader/writer. Production code is restricted to frozen scope paths; files are named for the responsibility (`contract`, `journal_windows`, `replacement_windows`, `journal_other`). Do not store fixture or authoritative acceptance data here.
- `internal/recoveryboundary/`: boot boundary contract and Windows native identity/ACL checks. `ops/qualification_recovery_boundary/` is its phase CLI, with platform-specific entry points.
- `execution/.../qualification_maintenance_c57_codex/20261025-current-chat/`: append-only command recipes, raw outputs, diagnostic ledger, manifests and final report for this card. Never overwrite failed raw captures; new attempts get new sequence numbers. Preserve permanently as evidence.
- `.local/qualification-maintenance-c57-20261025-tmp/`: reproducible local scratch, removed after final use; no unique evidence.
- `C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-20261025/`: ASCII-path task-owned disposable native fixtures and large outputs. Remove disposable fixtures after recording evidence; keep retained proof binaries only when referenced by manifest.
