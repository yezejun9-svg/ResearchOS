# Root coordinator v3 narrow Source repair

Status: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_DELTA_REVIEW.

R01: provider-free prepare creates or validates the real isolated data_root/trial-once directory, refuses symlink/junction/canonical-path drift, and checks the UUID-specific file is absent. C7 once_path is data_root/trial-once/<run_uuid>.json. The coordinator does not create, delete, overwrite, or reset that file; pinned v9 exclusively consumes it.

R02: C7 qualification_profile_hash is engine.go_hash(actual profile_entity_ref). Before GO the actual read-only registration, current ArtifactRef, runtime binding, and admitted qualification marker are checked for matching project/runtime/task/run/epoch/ref digest and technical registration hash. Host profile_hash and all GO content-hash fields retain their existing Artifact content-digest meaning. This Source contains future read-only DB queries but none were executed for this repair.

Two isolated delta controls passed, including synthetic digest mismatch/registration/ref-drift cases. Original 24 role pins and 40+1 prior controls are reused, not rerun. Forward/inverse full-byte restoration is verified; other Source behavior is unchanged. No actual native/SQL/provider calls or canonical/Main edits were made. This does not create bootstrap or qualification facts. Successful bootstrap is still unavailable, and the separate normal-Host draft/runtime issue remains outside this repair. No API or source Head changes, execution grant, READY, or formal acceptance are issued.
